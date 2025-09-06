#!/usr/bin/env python3
"""
Simplified Resume Keyword Analyzer for JobQst
Focuses on extracting keywords and skills from resumes to enhance user profiles.

Core Features:
- Parse PDF and DOCX resume files
- Extract technical skills using keyword matching
- Suggest new keywords for user profiles
- Simple skill gap analysis
"""

import re
import logging
from typing import Dict, List, Set, Any
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

logger = logging.getLogger(__name__)


class SimpleResumeAnalyzer:
    """Simplified resume analyzer focused on keyword extraction."""
    
    def __init__(self):
        self.tech_skills = self._get_tech_skills()
        self.soft_skills = self._get_soft_skills()
        
    def _get_tech_skills(self) -> Set[str]:
        """Get list of common technical skills to look for."""
        return {
            # Programming Languages
            'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go',
            'typescript', 'swift', 'kotlin', 'scala', 'r',
            
            # Web Technologies
            'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express',
            'django', 'flask', 'spring', 'jquery', 'bootstrap',
            
            # Databases
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite',
            
            # Cloud & Tools
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'github',
            'jenkins', 'terraform', 'linux',
            
            # Data & ML
            'machine learning', 'pandas', 'numpy', 'tensorflow', 'pytorch',
            'tableau', 'powerbi', 'excel',
            
            # Other
            'api', 'rest', 'graphql', 'json', 'agile', 'scrum'
        }
    
    def _get_soft_skills(self) -> Set[str]:
        """Get list of soft skills to look for."""
        return {
            'leadership', 'communication', 'teamwork', 'problem solving',
            'project management', 'analytical', 'creative', 'detail oriented',
            'time management', 'adaptable', 'collaborative'
        }
    
    def analyze_resume_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a resume file and extract keywords.
        
        Args:
            file_path: Path to resume file (PDF or DOCX)
            
        Returns:
            Dictionary with extracted skills and suggestions
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {'error': f'File not found: {file_path}'}
        
        try:
            # Extract text
            text = self._extract_text(file_path)
            if not text:
                return {'error': 'Could not extract text from file'}
            
            # Analyze text
            analysis = self._analyze_text(text)
            analysis['file_analyzed'] = str(file_path)
            analysis['file_type'] = file_path.suffix
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing resume: {e}")
            return {'error': str(e)}
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text from PDF or DOCX file."""
        text = ""
        
        if file_path.suffix.lower() == '.pdf':
            if not PDF_AVAILABLE:
                raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")
            text = self._extract_from_pdf(file_path)
            
        elif file_path.suffix.lower() == '.docx':
            if not DOCX_AVAILABLE:
                raise ImportError("python-docx not installed. Run: pip install python-docx")
            text = self._extract_from_docx(file_path)
            
        elif file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        return text
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF."""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting from PDF: {e}")
        return text
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX."""
        text = ""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error extracting from DOCX: {e}")
        return text
    
    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze resume text and extract skills."""
        text_lower = text.lower()
        
        # Find technical skills
        found_tech_skills = set()
        for skill in self.tech_skills:
            if self._skill_exists_in_text(skill, text_lower):
                found_tech_skills.add(skill)
        
        # Find soft skills
        found_soft_skills = set()
        for skill in self.soft_skills:
            if self._skill_exists_in_text(skill, text_lower):
                found_soft_skills.add(skill)
        
        # Extract contact info
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        
        # Determine experience level
        experience_level = self._get_experience_level(text_lower)
        
        return {
            'tech_skills': sorted(list(found_tech_skills)),
            'soft_skills': sorted(list(found_soft_skills)),
            'total_skills': len(found_tech_skills) + len(found_soft_skills),
            'email': email,
            'phone': phone,
            'experience_level': experience_level,
            'text_length': len(text),
            'analysis_successful': True
        }
    
    def _skill_exists_in_text(self, skill: str, text: str) -> bool:
        """Check if skill exists in text using word boundaries."""
        if ' ' in skill:
            # Multi-word skill - exact match
            return skill in text
        else:
            # Single word - use word boundaries
            pattern = r'\b' + re.escape(skill) + r'\b'
            return bool(re.search(pattern, text, re.IGNORECASE))
    
    def _extract_email(self, text: str) -> str:
        """Extract email address from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else ""
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from text."""
        phone_pattern = r'(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        matches = re.findall(phone_pattern, text)
        return ''.join(matches[0]) if matches else ""
    
    def _get_experience_level(self, text: str) -> str:
        """Determine experience level from resume text."""
        senior_words = ['senior', 'lead', 'principal', 'manager', 'director', 'architect']
        junior_words = ['junior', 'entry', 'intern', 'graduate', 'associate']
        
        senior_count = sum(1 for word in senior_words if word in text)
        junior_count = sum(1 for word in junior_words if word in text)
        
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
            return 'Mid Level'
    
    def suggest_profile_keywords(self, resume_analysis: Dict[str, Any], 
                                current_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest improvements to user profile based on resume analysis.
        
        Args:
            resume_analysis: Results from analyze_resume_file()
            current_profile: Current user profile data
            
        Returns:
            Dictionary with suggestions
        """
        if 'error' in resume_analysis:
            return {'error': resume_analysis['error']}
        
        current_keywords = set(k.lower() for k in current_profile.get('keywords', []))
        current_skills = set(s.lower() for s in current_profile.get('skills', []))
        
        resume_tech_skills = set(s.lower() for s in resume_analysis.get('tech_skills', []))
        resume_soft_skills = set(s.lower() for s in resume_analysis.get('soft_skills', []))
        
        suggestions = {
            'new_keywords_from_resume': list(resume_tech_skills - current_keywords),
            'new_skills_from_resume': list(resume_tech_skills - current_skills),
            'new_soft_skills': list(resume_soft_skills - current_skills),
            'profile_has_but_resume_missing': list(current_skills - resume_tech_skills),
            'recommended_additions': []
        }
        
        # Suggest related technologies
        related_suggestions = self._get_related_technologies(resume_tech_skills)
        suggestions['recommended_additions'] = list(related_suggestions - current_keywords)[:5]
        
        # Contact info suggestions
        if resume_analysis.get('email') and not current_profile.get('email'):
            suggestions['contact_updates'] = {'email': resume_analysis['email']}
        
        # Experience level suggestion
        resume_level = resume_analysis.get('experience_level', '')
        current_level = current_profile.get('experience_level', '')
        if resume_level and resume_level != current_level:
            suggestions['experience_level_update'] = resume_level
        
        return suggestions
    
    def _get_related_technologies(self, skills: Set[str]) -> Set[str]:
        """Suggest related technologies based on current skills."""
        related = set()
        
        # Technology relationships
        relationships = {
            'python': ['django', 'flask', 'pandas', 'fastapi'],
            'javascript': ['react', 'node.js', 'typescript', 'vue'],
            'react': ['redux', 'next.js', 'typescript'],
            'java': ['spring', 'hibernate', 'maven'],
            'aws': ['ec2', 's3', 'lambda', 'cloudformation'],
            'docker': ['kubernetes', 'docker-compose'],
            'sql': ['postgresql', 'mysql', 'database design']
        }
        
        for skill in skills:
            if skill in relationships:
                related.update(relationships[skill])
        
        return related
    
    def analyze_profile_resume_match(self, profile_path: str) -> Dict[str, Any]:
        """
        Analyze how well the resume matches the profile.
        
        Args:
            profile_path: Path to the profile directory
            
        Returns:
            Analysis results and suggestions
        """
        profile_dir = Path(profile_path)
        
        # Load profile
        profile_file = None
        for file_pattern in ['*.json']:
            profile_files = list(profile_dir.glob(file_pattern))
            if profile_files:
                profile_file = profile_files[0]
                break
        
        if not profile_file:
            return {'error': 'No profile file found'}
        
        try:
            with open(profile_file, 'r') as f:
                profile_data = json.load(f)
        except Exception as e:
            return {'error': f'Error loading profile: {e}'}
        
        # Find resume file
        resume_file = None
        for ext in ['.pdf', '.docx', '.txt']:
            resume_files = list(profile_dir.glob(f'*resume*{ext}'))
            if not resume_files:
                resume_files = list(profile_dir.glob(f'*Resume*{ext}'))
            if resume_files:
                resume_file = resume_files[0]
                break
        
        if not resume_file:
            return {'error': 'No resume file found in profile directory'}
        
        # Analyze resume
        resume_analysis = self.analyze_resume_file(str(resume_file))
        if 'error' in resume_analysis:
            return resume_analysis
        
        # Generate suggestions
        suggestions = self.suggest_profile_keywords(resume_analysis, profile_data)
        
        return {
            'profile_analyzed': str(profile_file),
            'resume_analyzed': str(resume_file),
            'resume_analysis': resume_analysis,
            'suggestions': suggestions,
            'match_summary': {
                'total_resume_skills': len(resume_analysis.get('tech_skills', [])),
                'skills_in_profile': len(set(s.lower() for s in profile_data.get('skills', []))),
                'new_skills_found': len(suggestions.get('new_skills_from_resume', [])),
                'skills_to_add': len(suggestions.get('recommended_additions', []))
            }
        }

