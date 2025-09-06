#!/usr/bin/env python3
"""
Resume and Keyword Analyzer Service for JobQst
Extracts skills, keywords, and relevant terms from resumes and suggests 
improvements to user profiles for better job matching.

Features:
- Resume parsing (PDF, DOCX, TXT)
- Skill extraction using NLP and keyword matching
- Keyword suggestions based on industry standards
- Profile enhancement recommendations
- Skills gap analysis
"""

import re
import logging
from typing import Dict, List, Set, Any, Tuple
from pathlib import Path
import json

# PDF and DOCX parsing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# NLP processing
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

logger = logging.getLogger(__name__)


class ResumeKeywordAnalyzer:
    """Service for analyzing resumes and extracting keywords/skills."""
    
    def __init__(self):
        self.tech_skills = self._load_tech_skills()
        self.soft_skills = self._load_soft_skills()
        self.industry_keywords = self._load_industry_keywords()
        self.nlp = self._load_nlp_model()
        
    def _load_tech_skills(self) -> Set[str]:
        """Load comprehensive list of technical skills."""
        return {
            # Programming Languages
            'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go',
            'rust', 'swift', 'kotlin', 'typescript', 'scala', 'r', 'matlab',
            'perl', 'shell', 'bash', 'powershell',
            
            # Web Technologies
            'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express',
            'django', 'flask', 'spring', 'laravel', 'jquery', 'bootstrap',
            'sass', 'less', 'webpack', 'babel', 'npm', 'yarn',
            
            # Databases
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'cassandra', 'oracle', 'sqlite', 'dynamodb', 'neo4j',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
            'github', 'gitlab', 'bitbucket', 'terraform', 'ansible', 'chef',
            'puppet', 'vagrant', 'linux', 'unix', 'ci/cd', 'microservices',
            
            # Data Science & ML
            'machine learning', 'deep learning', 'tensorflow', 'pytorch',
            'scikit-learn', 'pandas', 'numpy', 'jupyter', 'tableau', 'powerbi',
            'spark', 'hadoop', 'kafka', 'airflow', 'mlops',
            
            # Mobile Development
            'ios', 'android', 'react native', 'flutter', 'xamarin', 'ionic',
            
            # Testing & Quality
            'unit testing', 'integration testing', 'selenium', 'jest', 'pytest',
            'junit', 'tdd', 'bdd', 'agile', 'scrum', 'kanban',
            
            # Other Technologies
            'api', 'rest', 'graphql', 'soap', 'json', 'xml', 'oauth', 'jwt',
            'blockchain', 'ethereum', 'solidity', 'iot', 'embedded systems'
        }
    
    def _load_soft_skills(self) -> Set[str]:
        """Load comprehensive list of soft skills."""
        return {
            'communication', 'leadership', 'teamwork', 'problem solving',
            'critical thinking', 'creativity', 'adaptability', 'time management',
            'project management', 'collaboration', 'analytical thinking',
            'decision making', 'conflict resolution', 'mentoring', 'coaching',
            'presentation skills', 'negotiation', 'customer service',
            'organizational skills', 'attention to detail', 'multitasking',
            'stress management', 'emotional intelligence', 'work ethic',
            'reliability', 'flexibility', 'initiative', 'self-motivation'
        }
    
    def _load_industry_keywords(self) -> Dict[str, Set[str]]:
        """Load industry-specific keywords."""
        return {
            'software_development': {
                'software engineer', 'full stack', 'backend', 'frontend',
                'devops', 'site reliability', 'software architect',
                'technical lead', 'senior developer', 'junior developer'
            },
            'data_science': {
                'data scientist', 'data analyst', 'machine learning engineer',
                'ai engineer', 'data engineer', 'business intelligence',
                'quantitative analyst', 'research scientist'
            },
            'product_management': {
                'product manager', 'product owner', 'product marketing',
                'product strategy', 'roadmap', 'user research', 'analytics'
            },
            'design': {
                'ux designer', 'ui designer', 'graphic designer', 'web designer',
                'product designer', 'design systems', 'prototyping', 'wireframes'
            },
            'marketing': {
                'digital marketing', 'content marketing', 'seo', 'sem',
                'social media marketing', 'email marketing', 'growth hacking'
            }
        }
    
    def _load_nlp_model(self):
        """Load spaCy NLP model if available."""
        if SPACY_AVAILABLE:
            try:
                return spacy.load("en_core_web_sm")
            except IOError:
                logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
        return None
    
    def analyze_resume(self, resume_path: str) -> Dict[str, Any]:
        """
        Analyze a resume file and extract skills, keywords, and suggestions.
        
        Args:
            resume_path: Path to the resume file (PDF, DOCX, or TXT)
            
        Returns:
            Dictionary with analysis results
        """
        resume_path = Path(resume_path)
        
        if not resume_path.exists():
            raise FileNotFoundError(f"Resume file not found: {resume_path}")
        
        # Extract text from resume
        text = self._extract_text_from_file(resume_path)
        
        if not text:
            raise ValueError("Could not extract text from resume file")
        
        # Perform analysis
        analysis = {
            'file_path': str(resume_path),
            'file_type': resume_path.suffix.lower(),
            'text_length': len(text),
            'extraction_successful': True,
            **self._analyze_text(text)
        }
        
        logger.info(f"Resume analysis complete: {len(analysis['tech_skills'])} tech skills, "
                   f"{len(analysis['soft_skills'])} soft skills found")
        
        return analysis
    
    def _extract_text_from_file(self, file_path: Path) -> str:
        """Extract text content from various file formats."""
        text = ""
        
        try:
            if file_path.suffix.lower() == '.pdf':
                text = self._extract_from_pdf(file_path)
            elif file_path.suffix.lower() == '.docx':
                text = self._extract_from_docx(file_path)
            elif file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
        
        return text
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 not available. Install with: pip install PyPDF2")
        
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        return text
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file."""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not available. Install with: pip install python-docx")
        
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        return text
    
    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze extracted text for skills and keywords."""
        text_lower = text.lower()
        
        # Extract skills
        tech_skills = self._extract_skills(text_lower, self.tech_skills)
        soft_skills = self._extract_skills(text_lower, self.soft_skills)
        
        # Extract contact information
        contact_info = self._extract_contact_info(text)
        
        # Extract experience level indicators
        experience_level = self._determine_experience_level(text_lower)
        
        # Extract industry focus
        industry_focus = self._determine_industry_focus(text_lower)
        
        # Generate keyword suggestions
        suggested_keywords = self._generate_keyword_suggestions(tech_skills, industry_focus)
        
        # Analyze skill gaps
        skill_gaps = self._analyze_skill_gaps(tech_skills, industry_focus)
        
        return {
            'tech_skills': list(tech_skills),
            'soft_skills': list(soft_skills),
            'contact_info': contact_info,
            'experience_level': experience_level,
            'industry_focus': industry_focus,
            'suggested_keywords': suggested_keywords,
            'skill_gaps': skill_gaps,
            'total_skills_found': len(tech_skills) + len(soft_skills),
            'skill_categories': self._categorize_skills(tech_skills)
        }
    
    def _extract_skills(self, text: str, skill_set: Set[str]) -> Set[str]:
        """Extract skills from text using keyword matching."""
        found_skills = set()
        
        for skill in skill_set:
            # Handle multi-word skills
            if ' ' in skill:
                if skill in text:
                    found_skills.add(skill)
            else:
                # Use word boundaries for single words
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    found_skills.add(skill)
        
        return found_skills
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from resume text."""
        contact_info = {}
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        # Phone pattern (various formats)
        phone_pattern = r'(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact_info['phone'] = ''.join(phones[0]) if isinstance(phones[0], tuple) else phones[0]
        
        # LinkedIn pattern
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin:
            contact_info['linkedin'] = 'https://' + linkedin.group()
        
        # GitHub pattern
        github_pattern = r'github\.com/[\w-]+'
        github = re.search(github_pattern, text, re.IGNORECASE)
        if github:
            contact_info['github'] = 'https://' + github.group()
        
        return contact_info
    
    def _determine_experience_level(self, text: str) -> str:
        """Determine experience level based on resume content."""
        # Look for experience indicators
        senior_indicators = ['senior', 'lead', 'principal', 'architect', 'manager', 'director']
        junior_indicators = ['junior', 'entry', 'intern', 'associate', 'graduate']
        
        senior_count = sum(1 for indicator in senior_indicators if indicator in text)
        junior_count = sum(1 for indicator in junior_indicators if indicator in text)
        
        # Look for years of experience
        years_pattern = r'(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)'
        years_match = re.search(years_pattern, text, re.IGNORECASE)
        
        if years_match:
            years = int(years_match.group(1))
            if years >= 7:
                return 'Senior Level'
            elif years >= 3:
                return 'Mid Level'
            else:
                return 'Entry Level'
        
        if senior_count > junior_count:
            return 'Senior Level'
        elif junior_count > 0:
            return 'Entry Level'
        else:
            return 'Mid Level'  # Default
    
    def _determine_industry_focus(self, text: str) -> List[str]:
        """Determine industry focus based on keywords."""
        industry_scores = {}
        
        for industry, keywords in self.industry_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                industry_scores[industry] = score
        
        # Return industries sorted by relevance
        sorted_industries = sorted(industry_scores.items(), key=lambda x: x[1], reverse=True)
        return [industry.replace('_', ' ').title() for industry, _ in sorted_industries[:3]]
    
    def _generate_keyword_suggestions(self, current_skills: Set[str], industry_focus: List[str]) -> List[str]:
        """Generate keyword suggestions based on current skills and industry."""
        suggestions = set()
        
        # Suggest related technologies
        skill_relationships = {
            'python': ['django', 'flask', 'pandas', 'numpy', 'tensorflow'],
            'javascript': ['react', 'node.js', 'vue', 'angular', 'typescript'],
            'java': ['spring', 'hibernate', 'maven', 'gradle', 'junit'],
            'react': ['redux', 'jsx', 'typescript', 'next.js', 'gatsby'],
            'aws': ['ec2', 's3', 'lambda', 'cloudformation', 'vpc'],
            'machine learning': ['tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy']
        }
        
        for skill in current_skills:
            if skill in skill_relationships:
                suggestions.update(skill_relationships[skill])
        
        # Remove skills already present
        suggestions -= current_skills
        
        return list(suggestions)[:10]  # Limit to top 10 suggestions
    
    def _analyze_skill_gaps(self, current_skills: Set[str], industry_focus: List[str]) -> Dict[str, List[str]]:
        """Analyze skill gaps based on industry standards."""
        skill_gaps = {}
        
        # Define required skills for different roles/industries
        role_requirements = {
            'Software Development': {
                'essential': ['git', 'sql', 'api', 'testing'],
                'preferred': ['docker', 'ci/cd', 'cloud', 'microservices']
            },
            'Data Science': {
                'essential': ['python', 'sql', 'pandas', 'machine learning'],
                'preferred': ['tensorflow', 'pytorch', 'spark', 'tableau']
            },
            'Web Development': {
                'essential': ['html', 'css', 'javascript', 'git'],
                'preferred': ['react', 'node.js', 'webpack', 'testing']
            }
        }
        
        for industry in industry_focus:
            if industry in role_requirements:
                requirements = role_requirements[industry]
                
                missing_essential = [skill for skill in requirements['essential'] 
                                   if skill not in current_skills]
                missing_preferred = [skill for skill in requirements['preferred'] 
                                   if skill not in current_skills]
                
                if missing_essential or missing_preferred:
                    skill_gaps[industry] = {
                        'essential_gaps': missing_essential,
                        'preferred_gaps': missing_preferred
                    }
        
        return skill_gaps
    
    def _categorize_skills(self, skills: Set[str]) -> Dict[str, List[str]]:
        """Categorize technical skills into groups."""
        categories = {
            'Programming Languages': [],
            'Web Technologies': [],
            'Databases': [],
            'Cloud & DevOps': [],
            'Data Science & ML': [],
            'Mobile Development': [],
            'Other': []
        }
        
        categorization_map = {
            'Programming Languages': ['python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go'],
            'Web Technologies': ['html', 'css', 'react', 'angular', 'vue', 'node.js', 'express'],
            'Databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch'],
            'Cloud & DevOps': ['aws', 'azure', 'docker', 'kubernetes', 'jenkins', 'git'],
            'Data Science & ML': ['machine learning', 'tensorflow', 'pandas', 'numpy', 'tableau'],
            'Mobile Development': ['ios', 'android', 'react native', 'flutter']
        }
        
        for skill in skills:
            categorized = False
            for category, category_skills in categorization_map.items():
                if skill in category_skills:
                    categories[category].append(skill)
                    categorized = True
                    break
            
            if not categorized:
                categories['Other'].append(skill)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def suggest_profile_improvements(self, current_profile: Dict[str, Any], 
                                   resume_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest improvements to user profile based on resume analysis."""
        suggestions = {
            'new_keywords': [],
            'new_skills': [],
            'experience_level_update': None,
            'contact_info_updates': {},
            'missing_from_resume': []
        }
        
        current_keywords = set(kw.lower() for kw in current_profile.get('keywords', []))
        current_skills = set(skill.lower() for skill in current_profile.get('skills', []))
        
        # Suggest new keywords from resume
        resume_skills = set(skill.lower() for skill in resume_analysis['tech_skills'])
        suggestions['new_keywords'] = list(resume_skills - current_keywords)
        
        # Suggest new skills
        suggestions['new_skills'] = list(resume_skills - current_skills)
        
        # Suggest experience level update
        resume_level = resume_analysis['experience_level']
        current_level = current_profile.get('experience_level', '')
        if resume_level != current_level:
            suggestions['experience_level_update'] = resume_level
        
        # Suggest contact info updates
        resume_contact = resume_analysis['contact_info']
        for field, value in resume_contact.items():
            current_value = current_profile.get(field, '')
            if not current_value or current_value != value:
                suggestions['contact_info_updates'][field] = value
        
        # Find skills in profile but not in resume
        suggestions['missing_from_resume'] = list(current_skills - resume_skills)
        
        return suggestions

