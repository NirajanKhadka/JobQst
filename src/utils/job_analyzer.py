"""
Enhanced Job Analysis Module
Extracts detailed requirements, keywords, experience levels, and other metadata from job postings
to improve auto-application targeting and efficiency.
"""

import re
import json
import time
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
from dataclasses import dataclass
from playwright.sync_api import Page, Browser
from rich.console import Console

# Handle ollama import gracefully
try:
    import ollama
    OLLAMA_AVAILABLE = True
except Exception as e:
    OLLAMA_AVAILABLE = False
    print(f"⚠️ Ollama not available: {e}")

console = Console()

@dataclass
class JobRequirements:
    """Structured job requirements data"""
    required_skills: List[str]
    preferred_skills: List[str]
    experience_level: str  # entry, mid, senior, executive
    years_experience: Optional[int]
    education_level: str  # high_school, bachelor, master, phd, none_specified
    certifications: List[str]
    salary_range: Optional[Tuple[int, int]]  # (min, max) in CAD
    remote_options: str  # remote, hybrid, onsite, flexible
    employment_type: str  # full_time, part_time, contract, internship
    industry: str
    company_size: str  # startup, small, medium, large, enterprise
    benefits: List[str]
    application_deadline: Optional[datetime]
    urgency_level: str  # low, medium, high, urgent

class JobAnalyzer:
    """Enhanced job analyzer for extracting detailed requirements and metadata"""
    
    def __init__(self, use_ai: bool = True, profile_name: str = "default"):
        self.use_ai = use_ai
        self.profile_name = profile_name
        self.console = Console()
        
        # Skill categories for better organization
        self.skill_categories = {
            "programming_languages": [
                "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "php", "ruby",
                "swift", "kotlin", "scala", "r", "matlab", "sql", "html", "css"
            ],
            "frameworks_libraries": [
                "react", "angular", "vue", "django", "flask", "spring", "express", "node.js", "pandas",
                "numpy", "tensorflow", "pytorch", "scikit-learn", "bootstrap", "jquery", "laravel"
            ],
            "databases": [
                "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "oracle", "sql server",
                "sqlite", "cassandra", "dynamodb", "firebase"
            ],
            "cloud_platforms": [
                "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform", "ansible"
            ],
            "data_tools": [
                "tableau", "power bi", "excel", "powerpoint", "looker", "qlik", "sas", "spss",
                "jupyter", "databricks", "snowflake", "spark", "hadoop"
            ],
            "methodologies": [
                "agile", "scrum", "kanban", "devops", "ci/cd", "tdd", "machine learning", "data science",
                "etl", "api", "microservices", "rest", "graphql"
            ]
        }
        
        # Experience level indicators
        self.experience_indicators = {
            "entry": ["entry", "junior", "associate", "graduate", "new grad", "0-2 years", "1-2 years"],
            "mid": ["mid", "intermediate", "2-5 years", "3-5 years", "4-6 years"],
            "senior": ["senior", "sr.", "lead", "5+ years", "7+ years", "8+ years", "principal"],
            "executive": ["director", "vp", "vice president", "chief", "head of", "manager", "10+ years"]
        }
        
        # Salary patterns (CAD)
        self.salary_patterns = [
            r'\$(\d{2,3}),?(\d{3})\s*-\s*\$(\d{2,3}),?(\d{3})',  # $80,000 - $120,000
            r'\$(\d{2,3})k\s*-\s*\$(\d{2,3})k',  # $80k - $120k
            r'(\d{2,3}),?(\d{3})\s*-\s*(\d{2,3}),?(\d{3})',  # 80,000 - 120,000
        ]

    def analyze_job_deep(self, job: Dict, page: Optional[Page] = None) -> Dict:
        """
        Perform deep analysis of a job posting to extract detailed requirements.
        
        Args:
            job: Basic job data from scraper
            page: Optional Playwright page for additional scraping
            
        Returns:
            Enhanced job data with detailed requirements analysis
        """
        console.print(f"[cyan]🔍 Analyzing job: {job.get('title', 'Unknown')}[/cyan]")
        
        # Get full job description if page is provided
        full_description = self._get_full_description(job, page)
        
        # Extract requirements
        requirements = self._extract_requirements(full_description)
        
        # Analyze with AI if available
        if self.use_ai:
            ai_analysis = self._analyze_with_ai(full_description)
            requirements = self._merge_analysis(requirements, ai_analysis)
        
        # Add analysis to job data
        enhanced_job = job.copy()
        enhanced_job.update({
            "full_description": full_description,
            "requirements": requirements.__dict__,
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_version": "1.0"
        })
        
        console.print(f"[green]✅ Analysis complete: {requirements.experience_level} level, {len(requirements.required_skills)} skills[/green]")
        return enhanced_job

    def _get_full_description(self, job: Dict, page: Optional[Page]) -> str:
        """Extract full job description from the job page"""
        if not page:
            return job.get("summary", job.get("description", ""))
        
        try:
            # Try to find job description on the page
            description_selectors = [
                ".job-description",
                ".job-details",
                ".job-content",
                "[data-testid='job-description']",
                ".description",
                ".content"
            ]
            
            for selector in description_selectors:
                element = page.query_selector(selector)
                if element:
                    return element.inner_text()
            
            # Fallback to page text
            return page.inner_text()
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not extract full description: {e}[/yellow]")
            return job.get("summary", job.get("description", ""))

    def _extract_requirements(self, description: str) -> JobRequirements:
        """Extract structured requirements from job description"""
        text = description.lower()
        
        # Extract skills
        required_skills, preferred_skills = self._extract_skills(text)
        
        # Extract experience level and years
        experience_level, years_experience = self._extract_experience(text)
        
        # Extract education
        education_level = self._extract_education(text)
        
        # Extract certifications
        certifications = self._extract_certifications(text)
        
        # Extract salary
        salary_range = self._extract_salary(description)
        
        # Extract work arrangement
        remote_options = self._extract_remote_options(text)
        
        # Extract employment type
        employment_type = self._extract_employment_type(text)
        
        # Extract other metadata
        industry = self._extract_industry(text)
        company_size = self._extract_company_size(text)
        benefits = self._extract_benefits(text)
        urgency_level = self._extract_urgency(text)
        
        return JobRequirements(
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_level=experience_level,
            years_experience=years_experience,
            education_level=education_level,
            certifications=certifications,
            salary_range=salary_range,
            remote_options=remote_options,
            employment_type=employment_type,
            industry=industry,
            company_size=company_size,
            benefits=benefits,
            application_deadline=None,  # TODO: Extract deadline
            urgency_level=urgency_level
        )

    def _extract_skills(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract required and preferred skills"""
        required_skills = []
        preferred_skills = []
        
        # Check all skill categories
        for category, skills in self.skill_categories.items():
            for skill in skills:
                if skill in text:
                    # Determine if required or preferred based on context
                    if self._is_required_skill(text, skill):
                        required_skills.append(skill)
                    else:
                        preferred_skills.append(skill)
        
        return list(set(required_skills)), list(set(preferred_skills))

    def _is_required_skill(self, text: str, skill: str) -> bool:
        """Determine if a skill is required or preferred based on context"""
        skill_index = text.find(skill)
        if skill_index == -1:
            return False
        
        # Look for context around the skill
        context_start = max(0, skill_index - 100)
        context_end = min(len(text), skill_index + 100)
        context = text[context_start:context_end]
        
        required_indicators = ["required", "must", "essential", "mandatory", "need"]
        preferred_indicators = ["preferred", "nice to have", "bonus", "plus", "advantage"]
        
        required_score = sum(1 for indicator in required_indicators if indicator in context)
        preferred_score = sum(1 for indicator in preferred_indicators if indicator in context)
        
        return required_score > preferred_score

    def _extract_experience(self, text: str) -> Tuple[str, Optional[int]]:
        """Extract experience level and years"""
        # Check for explicit years
        years_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)-(\d+)\s*years?\s*(?:of\s*)?experience',
            r'minimum\s*(\d+)\s*years?',
            r'at least\s*(\d+)\s*years?'
        ]
        
        years_experience = None
        for pattern in years_patterns:
            match = re.search(pattern, text)
            if match:
                years_experience = int(match.group(1))
                break
        
        # Determine experience level
        experience_level = "mid"  # default
        for level, indicators in self.experience_indicators.items():
            if any(indicator in text for indicator in indicators):
                experience_level = level
                break
        
        return experience_level, years_experience

    def _extract_education(self, text: str) -> str:
        """Extract education requirements"""
        education_patterns = {
            "phd": ["phd", "ph.d", "doctorate", "doctoral"],
            "master": ["master", "msc", "mba", "m.s.", "m.a."],
            "bachelor": ["bachelor", "degree", "bsc", "ba", "b.s.", "b.a.", "undergraduate"],
            "high_school": ["high school", "diploma", "secondary"]
        }
        
        for level, patterns in education_patterns.items():
            if any(pattern in text for pattern in patterns):
                return level
        
        return "none_specified"

    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certification requirements"""
        cert_patterns = [
            "aws certified", "azure certified", "google cloud certified",
            "pmp", "cissp", "cisa", "cism", "comptia", "cisco",
            "microsoft certified", "oracle certified", "salesforce certified"
        ]
        
        certifications = []
        for cert in cert_patterns:
            if cert in text:
                certifications.append(cert)
        
        return certifications

    def _extract_salary(self, text: str) -> Optional[Tuple[int, int]]:
        """Extract salary range"""
        for pattern in self.salary_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 4:  # $80,000 - $120,000
                        min_sal = int(match.group(1) + match.group(2))
                        max_sal = int(match.group(3) + match.group(4))
                    elif len(match.groups()) == 2:  # $80k - $120k
                        min_sal = int(match.group(1)) * 1000
                        max_sal = int(match.group(2)) * 1000
                    else:
                        continue
                    
                    return (min_sal, max_sal)
                except ValueError:
                    continue
        
        return None

    def _extract_remote_options(self, text: str) -> str:
        """Extract remote work options"""
        if any(term in text for term in ["remote", "work from home", "wfh"]):
            if any(term in text for term in ["hybrid", "flexible"]):
                return "hybrid"
            return "remote"
        elif any(term in text for term in ["hybrid", "flexible"]):
            return "hybrid"
        elif any(term in text for term in ["on-site", "onsite", "office"]):
            return "onsite"
        return "flexible"

    def _extract_employment_type(self, text: str) -> str:
        """Extract employment type"""
        if any(term in text for term in ["contract", "contractor", "freelance"]):
            return "contract"
        elif any(term in text for term in ["part-time", "part time"]):
            return "part_time"
        elif any(term in text for term in ["intern", "internship"]):
            return "internship"
        return "full_time"

    def _extract_industry(self, text: str) -> str:
        """Extract industry information"""
        industries = {
            "technology": ["tech", "software", "it", "computer", "digital"],
            "finance": ["finance", "banking", "investment", "fintech"],
            "healthcare": ["health", "medical", "hospital", "pharmaceutical"],
            "consulting": ["consulting", "advisory", "professional services"],
            "retail": ["retail", "ecommerce", "consumer"],
            "manufacturing": ["manufacturing", "industrial", "automotive"],
            "government": ["government", "public sector", "municipal"]
        }
        
        for industry, keywords in industries.items():
            if any(keyword in text for keyword in keywords):
                return industry
        
        return "other"

    def _extract_company_size(self, text: str) -> str:
        """Extract company size indicators"""
        if any(term in text for term in ["startup", "early stage"]):
            return "startup"
        elif any(term in text for term in ["fortune 500", "enterprise", "multinational"]):
            return "enterprise"
        elif any(term in text for term in ["small business", "small company"]):
            return "small"
        return "medium"

    def _extract_benefits(self, text: str) -> List[str]:
        """Extract benefits and perks"""
        benefit_keywords = [
            "health insurance", "dental", "vision", "401k", "pension",
            "vacation", "pto", "flexible hours", "stock options",
            "bonus", "training", "professional development"
        ]
        
        benefits = []
        for benefit in benefit_keywords:
            if benefit in text:
                benefits.append(benefit)
        
        return benefits

    def _extract_urgency(self, text: str) -> str:
        """Extract urgency level"""
        urgent_indicators = ["urgent", "immediate", "asap", "start immediately"]
        high_indicators = ["soon", "quickly", "fast-paced"]
        
        if any(indicator in text for indicator in urgent_indicators):
            return "urgent"
        elif any(indicator in text for indicator in high_indicators):
            return "high"
        return "medium"

    def _analyze_with_ai(self, description: str) -> Dict:
        """Use AI to analyze job description for additional insights"""
        if not OLLAMA_AVAILABLE:
            console.print("[yellow]⚠️ AI analysis skipped - Ollama not available[/yellow]")
            return {}

        try:
            prompt = f"""
            Analyze this job description and extract key information in JSON format:

            Job Description:
            {description[:2000]}  # Limit to avoid token limits

            Please extract:
            1. Required technical skills (list)
            2. Preferred skills (list)
            3. Experience level (entry/mid/senior/executive)
            4. Years of experience required (number or null)
            5. Education level required
            6. Key responsibilities (list)
            7. Company culture indicators
            8. Growth opportunities mentioned

            Return ONLY valid JSON in this exact format:
            {{
                "required_skills": ["skill1", "skill2"],
                "preferred_skills": ["skill1", "skill2"],
                "experience_level": "entry",
                "years_required": 2,
                "education_level": "Bachelor's",
                "responsibilities": ["task1", "task2"],
                "culture_indicators": ["indicator1"],
                "growth_opportunities": ["opportunity1"]
            }}
            """

            response = ollama.generate(model="mistral", prompt=prompt)
            response_text = response.get("response", "{}")

            # Clean up the response text to ensure valid JSON
            response_text = response_text.strip()

            # Remove any text before the first { and after the last }
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')

            if start_idx != -1 and end_idx != -1:
                response_text = response_text[start_idx:end_idx+1]
            else:
                # If no valid JSON structure found, return empty dict
                console.print(f"[yellow]⚠️ AI response doesn't contain valid JSON structure[/yellow]")
                return {}

            # Try to parse the cleaned JSON
            try:
                parsed_data = json.loads(response_text)
                return parsed_data
            except json.JSONDecodeError as json_error:
                console.print(f"[yellow]⚠️ JSON parsing failed: {json_error}[/yellow]")
                console.print(f"[yellow]Raw response: {response_text[:200]}...[/yellow]")

                # Try to fix common JSON issues
                fixed_text = response_text
                # Fix common issues like trailing commas, unescaped quotes, etc.
                fixed_text = re.sub(r',\s*}', '}', fixed_text)  # Remove trailing commas before }
                fixed_text = re.sub(r',\s*]', ']', fixed_text)  # Remove trailing commas before ]

                try:
                    return json.loads(fixed_text)
                except json.JSONDecodeError:
                    console.print(f"[yellow]⚠️ Could not fix JSON, returning empty analysis[/yellow]")
                    return {}

        except Exception as e:
            console.print(f"[yellow]⚠️ AI analysis failed: {e}[/yellow]")
            return {}

    def _merge_analysis(self, requirements: JobRequirements, ai_analysis: Dict) -> JobRequirements:
        """Merge AI analysis with rule-based analysis"""
        if not ai_analysis:
            return requirements
        
        # Merge skills
        ai_required = ai_analysis.get("required_skills", [])
        ai_preferred = ai_analysis.get("preferred_skills", [])
        
        requirements.required_skills.extend([skill.lower() for skill in ai_required])
        requirements.preferred_skills.extend([skill.lower() for skill in ai_preferred])
        
        # Remove duplicates
        requirements.required_skills = list(set(requirements.required_skills))
        requirements.preferred_skills = list(set(requirements.preferred_skills))
        
        return requirements

    def calculate_job_match_score(self, job_requirements: JobRequirements, user_profile: Dict) -> float:
        """
        Calculate how well a user matches a job based on requirements.
        
        Returns:
            Match score from 0.0 to 1.0
        """
        user_skills = set(skill.lower() for skill in user_profile.get("keywords", []))
        required_skills = set(job_requirements.required_skills)
        preferred_skills = set(job_requirements.preferred_skills)
        
        # Calculate skill match
        required_match = len(user_skills & required_skills) / max(len(required_skills), 1)
        preferred_match = len(user_skills & preferred_skills) / max(len(preferred_skills), 1)
        
        # Weight required skills more heavily
        skill_score = (required_match * 0.7) + (preferred_match * 0.3)
        
        # Experience level penalty/bonus
        user_experience = user_profile.get("experience_level", "mid")
        experience_score = self._calculate_experience_match(user_experience, job_requirements.experience_level)
        
        # Final score
        final_score = (skill_score * 0.8) + (experience_score * 0.2)
        
        return min(1.0, max(0.0, final_score))

    def _calculate_experience_match(self, user_level: str, job_level: str) -> float:
        """Calculate experience level match score"""
        level_scores = {"entry": 1, "mid": 2, "senior": 3, "executive": 4}
        user_score = level_scores.get(user_level, 2)
        job_score = level_scores.get(job_level, 2)
        
        # Perfect match
        if user_score == job_score:
            return 1.0
        # Close match (within 1 level)
        elif abs(user_score - job_score) <= 1:
            return 0.8
        # Moderate match (within 2 levels)
        elif abs(user_score - job_score) <= 2:
            return 0.5
        # Poor match
        else:
            return 0.2

    def analyze_job(self, job: Dict) -> Dict:
        """
        Analyze a job posting to extract key information.
        
        Args:
            job: Job dictionary with title, description, etc.
            
        Returns:
            Analysis results dictionary
        """
        description = job.get('description', job.get('summary', ''))
        
        analysis = {
            'skills': self.extract_skills(description),
            'experience_level': self.detect_experience_level(description),
            'education_level': self.detect_education_level(description),
            'remote_options': self.detect_remote_options(description),
            'salary_range': self.extract_salary_range(description),
            'language': self.detect_language(description),
            'sentiment': self.analyze_sentiment(description),
            'requirements': self._extract_requirements(description).__dict__
        }
        
        return analysis

    def extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from job description text.
        
        Args:
            text: Job description text
            
        Returns:
            List of detected skills
        """
        text_lower = text.lower()
        skills = []
        
        # Check all skill categories
        for category, skill_list in self.skill_categories.items():
            for skill in skill_list:
                if skill.lower() in text_lower:
                    skills.append(skill)
        
        # Remove duplicates and return
        return list(set(skills))

    def detect_experience_level(self, text: str) -> str:
        """
        Detect experience level from job description.
        
        Args:
            text: Job description text
            
        Returns:
            Experience level (entry, mid, senior, executive)
        """
        text_lower = text.lower()
        
        for level, indicators in self.experience_indicators.items():
            for indicator in indicators:
                if indicator.lower() in text_lower:
                    return level
        
        # Default to mid-level if no clear indicators
        return "mid"

    def detect_education_level(self, text: str) -> str:
        """
        Detect required education level from job description.
        
        Args:
            text: Job description text
            
        Returns:
            Education level (high_school, bachelor, master, phd, none_specified)
        """
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['phd', 'doctorate', 'doctoral']):
            return 'phd'
        elif any(term in text_lower for term in ['master', 'mba', 'ms', 'ma']):
            return 'master'
        elif any(term in text_lower for term in ['bachelor', 'ba', 'bs', 'b.s.', 'degree']):
            return 'bachelor'
        elif any(term in text_lower for term in ['high school', 'diploma']):
            return 'high_school'
        else:
            return 'none_specified'

    def detect_remote_options(self, text: str) -> str:
        """
        Detect remote work options from job description.
        
        Args:
            text: Job description text
            
        Returns:
            Remote options (remote, hybrid, onsite, flexible)
        """
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['remote', 'work from home', 'wfh', 'telecommute']):
            return 'remote'
        elif any(term in text_lower for term in ['hybrid', 'partially remote', 'flexible']):
            return 'hybrid'
        elif any(term in text_lower for term in ['onsite', 'in-office', 'in person']):
            return 'onsite'
        else:
            return 'flexible'

    def extract_salary_range(self, text: str) -> Optional[Tuple[int, int]]:
        """
        Extract salary range from job description.
        
        Args:
            text: Job description text
            
        Returns:
            Tuple of (min_salary, max_salary) or None if not found
        """
        for pattern in self.salary_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 4:  # $80,000 - $120,000 format
                    min_sal = int(match.group(1) + match.group(2))
                    max_sal = int(match.group(3) + match.group(4))
                    return (min_sal, max_sal)
                elif len(match.groups()) == 2:  # $80k - $120k format
                    min_sal = int(match.group(1)) * 1000
                    max_sal = int(match.group(2)) * 1000
                    return (min_sal, max_sal)
        
        return None

    def detect_language(self, text: str) -> str:
        """
        Detect the primary language of the job description.
        
        Args:
            text: Job description text
            
        Returns:
            Language code (en, fr, etc.)
        """
        # Simple language detection based on common words
        text_lower = text.lower()
        
        # French indicators
        french_words = ['le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'pour', 'avec', 'sur', 'dans']
        french_count = sum(1 for word in french_words if word in text_lower)
        
        # English indicators
        english_words = ['the', 'and', 'or', 'for', 'with', 'in', 'on', 'at', 'to', 'of', 'a', 'an']
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if french_count > english_count:
            return 'fr'
        else:
            return 'en'

    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of job description.
        
        Args:
            text: Job description text
            
        Returns:
            Sentiment analysis results
        """
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = ['exciting', 'innovative', 'dynamic', 'growth', 'opportunity', 'challenging', 'rewarding', 'flexible', 'competitive', 'excellent']
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        # Negative indicators
        negative_words = ['stressful', 'demanding', 'difficult', 'challenging', 'fast-paced', 'high-pressure', 'deadline', 'overtime']
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Neutral indicators
        neutral_words = ['responsible', 'required', 'must', 'should', 'will', 'experience', 'skills', 'knowledge']
        neutral_count = sum(1 for word in neutral_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return {'sentiment': 'neutral', 'confidence': 0.0, 'scores': {'positive': 0, 'negative': 0, 'neutral': 0}}
        
        positive_score = positive_count / total_words
        negative_score = negative_count / total_words
        neutral_score = neutral_count / total_words
        
        # Determine overall sentiment
        if positive_score > negative_score and positive_score > neutral_score:
            sentiment = 'positive'
            confidence = positive_score
        elif negative_score > positive_score and negative_score > neutral_score:
            sentiment = 'negative'
            confidence = negative_score
        else:
            sentiment = 'neutral'
            confidence = neutral_score
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'scores': {
                'positive': positive_score,
                'negative': negative_score,
                'neutral': neutral_score
            }
        }
