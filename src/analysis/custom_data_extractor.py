"""
Custom Data Extraction Engine for Enhanced Job Processing
Handles structured data extraction using custom logic and regex patterns.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Result of custom data extraction."""
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None
    skills: List[str] = None
    requirements: List[str] = None
    benefits: List[str] = None
    confidence: float = 0.0
    extraction_method: str = "custom_logic"
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.requirements is None:
            self.requirements = []
        if self.benefits is None:
            self.benefits = []

class CustomDataExtractor:
    """
    Handles structured data extraction using custom logic, regex patterns, and parsing rules.
    
    This extractor focuses on reliable extraction of structured information that can be
    consistently parsed without requiring AI analysis.
    """
    
    def __init__(self):
        """Initialize the custom data extractor with patterns and rules."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize extraction patterns
        self._init_title_patterns()
        self._init_company_patterns()
        self._init_location_patterns()
        self._init_salary_patterns()
        self._init_experience_patterns()
        self._init_employment_type_patterns()
        self._init_skills_patterns()
        self._init_requirements_patterns()
        self._init_benefits_patterns()
    
    def _init_title_patterns(self):
        """Initialize job title extraction patterns."""
        self.title_patterns = [
            # Direct title indicators
            r'(?i)job\s*title[:\s]+([^\n\r]{1,100})',
            r'(?i)position[:\s]+([^\n\r]{1,100})',
            r'(?i)role[:\s]+([^\n\r]{1,100})',
            
            # Common job title formats
            r'(?i)^([A-Z][a-zA-Z\s\-,&()]+(?:Engineer|Developer|Manager|Analyst|Specialist|Coordinator|Assistant|Director|Lead|Senior|Junior))\s*$',
            r'(?i)(Senior|Junior|Lead|Principal|Staff)\s+([A-Za-z\s]+(?:Engineer|Developer|Manager|Analyst))',
            
            # HTML title extraction
            r'<title>([^<]+(?:Engineer|Developer|Manager|Analyst|Specialist)[^<]*)</title>',
            r'<h1[^>]*>([^<]+(?:Engineer|Developer|Manager|Analyst|Specialist)[^<]*)</h1>',
        ]
    
    def _init_company_patterns(self):
        """Initialize company name extraction patterns."""
        self.company_patterns = [
            # Direct company indicators
            r'(?i)company[:\s]+([^\n\r]{1,80})',
            r'(?i)employer[:\s]+([^\n\r]{1,80})',
            r'(?i)organization[:\s]+([^\n\r]{1,80})',
            r'(?i)at\s+([A-Z][a-zA-Z\s&.,\-()]{2,50})\s*(?:\n|$)',
            
            # Common company formats
            r'([A-Z][a-zA-Z\s&.,\-()]{2,50})\s+(?:Inc|LLC|Corp|Corporation|Ltd|Limited|Company|Co\.)',
            r'([A-Z][a-zA-Z\s&.,\-()]{2,50})\s+(?:Technologies|Technology|Tech|Solutions|Systems|Services)',
            
            # HTML company extraction
            r'<span[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)</span>',
            r'data-testid="company"[^>]*>([^<]+)<',
        ]
        
        # Company name cleanup patterns
        self.company_cleanup_patterns = [
            r'\s*-\s*.*$',  # Remove everything after dash
            r'\s*\|.*$',    # Remove everything after pipe
            r'\s*\(.*\)$',  # Remove parenthetical content
            r'^\s*at\s+',   # Remove "at" prefix
        ]
    
    def _init_location_patterns(self):
        """Initialize location extraction patterns."""
        self.location_patterns = [
            # Direct location indicators
            r'(?i)location[:\s]+([^\n\r]{1,80})',
            r'(?i)where[:\s]+([^\n\r]{1,80})',
            r'(?i)based\s+in[:\s]+([^\n\r]{1,80})',
            
            # Common location formats
            r'([A-Z][a-zA-Z\s\-,]+),\s*([A-Z]{2})\s*(?:\d{5})?',  # City, State ZIP
            r'([A-Z][a-zA-Z\s\-,]+),\s*([A-Z][a-zA-Z\s]+)',       # City, Country/Province
            r'(?i)(Remote|Hybrid|On-site|Work from home)',
            
            # HTML location extraction
            r'<span[^>]*class="[^"]*location[^"]*"[^>]*>([^<]+)</span>',
            r'data-testid=".*location.*"[^>]*>([^<]+)<',
        ]
    
    def _init_salary_patterns(self):
        """Initialize salary extraction patterns."""
        self.salary_patterns = [
            # Direct salary indicators
            r'(?i)salary[:\s]+([^\n\r]{1,50})',
            r'(?i)compensation[:\s]+([^\n\r]{1,50})',
            r'(?i)pay[:\s]+([^\n\r]{1,50})',
            
            # Salary ranges
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*-\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*to\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*/\s*(hour|hr|year|yr|annually)',
            
            # Hourly rates
            r'\$(\d{1,3}(?:\.\d{2})?)\s*/\s*(?:hour|hr)',
            r'(\d{1,3}(?:\.\d{2})?)\s*dollars?\s*per\s*hour',
        ]
    
    def _init_experience_patterns(self):
        """Initialize experience level extraction patterns."""
        self.experience_patterns = [
            # Direct experience indicators
            r'(?i)experience[:\s]+([^\n\r]{1,50})',
            r'(?i)(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(?i)(entry.level|junior|senior|lead|principal|staff)',
            
            # Experience levels
            r'(?i)(0-2|1-3|2-5|3-7|5-10|10\+)\s*years?',
            r'(?i)(beginner|intermediate|Improved|expert)',
            r'(?i)(intern|internship|co-op|new grad|graduate)',
        ]
    
    def _init_employment_type_patterns(self):
        """Initialize employment type extraction patterns."""
        self.employment_type_patterns = [
            r'(?i)(full.time|part.time|contract|temporary|permanent|freelance)',
            r'(?i)(remote|hybrid|on.site|work.from.home)',
            r'(?i)(internship|co-op|seasonal)',
        ]
    
    def _init_skills_patterns(self):
        """Initialize technical skills extraction patterns."""
        # Common technical skills (this could be expanded significantly)
        self.technical_skills = [
            # Programming Languages
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust', 'PHP', 'Ruby',
            'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'SQL', 'HTML', 'CSS',
            
            # Frameworks & Libraries
            'React', 'Angular', 'Vue.js', 'Node.js', 'Express', 'Django', 'Flask', 'Spring',
            'Laravel', 'Rails', 'jQuery', 'Bootstrap', 'Tailwind',
            
            # Databases
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 'SQL Server',
            'Elasticsearch', 'Cassandra', 'DynamoDB',
            
            # Cloud & DevOps
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'GitLab', 'GitHub',
            'Terraform', 'Ansible', 'Chef', 'Puppet',
            
            # Tools & Technologies
            'Git', 'Linux', 'Unix', 'Windows', 'MacOS', 'Jira', 'Confluence', 'Slack',
            'Figma', 'Sketch', 'Photoshop', 'Illustrator',
        ]
        
        self.skills_patterns = [
            r'(?i)skills?[:\s]+([^\n\r]{1,200})',
            r'(?i)technologies?[:\s]+([^\n\r]{1,200})',
            r'(?i)tools?[:\s]+([^\n\r]{1,200})',
            r'(?i)requirements?[:\s]+([^\n\r]{1,500})',
        ]
    
    def _init_requirements_patterns(self):
        """Initialize job requirements extraction patterns."""
        self.requirements_patterns = [
            r'(?i)requirements?[:\s]+([^\n\r]{1,500})',
            r'(?i)qualifications?[:\s]+([^\n\r]{1,500})',
            r'(?i)must\s+have[:\s]+([^\n\r]{1,200})',
            r'(?i)required[:\s]+([^\n\r]{1,200})',
            r'(?i)minimum[:\s]+([^\n\r]{1,200})',
        ]
    
    def _init_benefits_patterns(self):
        """Initialize benefits extraction patterns."""
        self.benefits_patterns = [
            r'(?i)benefits?[:\s]+([^\n\r]{1,300})',
            r'(?i)perks?[:\s]+([^\n\r]{1,300})',
            r'(?i)we\s+offer[:\s]+([^\n\r]{1,300})',
            r'(?i)compensation\s+package[:\s]+([^\n\r]{1,300})',
        ]
        
        # Common benefits keywords
        self.common_benefits = [
            'health insurance', 'dental', 'vision', '401k', 'retirement',
            'vacation', 'pto', 'sick leave', 'remote work', 'flexible hours',
            'stock options', 'equity', 'bonus', 'gym membership', 'wellness',
            'professional development', 'training', 'conference', 'education',
        ]
    
    def extract_job_data(self, job_data: Dict[str, Any]) -> ExtractionResult:
        """
        Extract structured data from job information using custom logic.
        
        Args:
            job_data: Dictionary containing job information (title, description, url, etc.)
            
        Returns:
            ExtractionResult with extracted structured data
        """
        result = ExtractionResult()
        
        # Get text content for extraction
        description = job_data.get('description') or job_data.get('job_description', '')
        title = job_data.get('title', '')
        url = job_data.get('url', '')
        
        # Combine all text for comprehensive extraction
        full_text = f"{title}\n{description}"
        
        try:
            # Extract individual components
            result.title = self.extract_title(full_text, title)
            result.company = self.extract_company(full_text, url)
            result.location = self.extract_location(full_text)
            result.salary_range = self.extract_salary(full_text)
            result.experience_level = self.extract_experience_level(full_text)
            result.employment_type = self.extract_employment_type(full_text)
            result.skills = self.extract_skills(full_text)
            result.requirements = self.extract_requirements(full_text)
            result.benefits = self.extract_benefits(full_text)
            
            # Calculate confidence based on successful extractions
            result.confidence = self._calculate_confidence(result)
            
            self.logger.debug(f"Extracted data with confidence {result.confidence:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error during extraction: {e}")
            result.confidence = 0.0
        
        return result
    
    def extract_title(self, text: str, existing_title: str = "") -> Optional[str]:
        """Extract job title using custom patterns."""
        # If we already have a clean title, use it
        if existing_title and len(existing_title.strip()) > 3:
            return existing_title.strip()
        
        for pattern in self.title_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                if len(title) > 3 and len(title) < 100:
                    return self._clean_title(title)
        
        return existing_title.strip() if existing_title else None
    
    def extract_company(self, text: str, url: str = "") -> Optional[str]:
        """Extract company name using custom patterns."""
        # Try URL extraction first
        if url:
            company_from_url = self._extract_company_from_url(url)
            if company_from_url:
                return company_from_url
        
        # Try text patterns
        for pattern in self.company_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                company = match.group(1).strip()
                if len(company) > 2 and len(company) < 80:
                    return self._clean_company_name(company)
        
        return None
    
    def extract_location(self, text: str) -> Optional[str]:
        """Extract location using custom patterns."""
        for pattern in self.location_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                location = match.group(1).strip()
                if len(location) > 2 and len(location) < 80:
                    return self._clean_location(location)
        
        return None
    
    def extract_salary(self, text: str) -> Optional[str]:
        """Extract salary information using custom patterns."""
        for pattern in self.salary_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                if len(match.groups()) >= 2:
                    # Range format
                    return f"${match.group(1)} - ${match.group(2)}"
                else:
                    # Single value or formatted string
                    salary = match.group(1).strip()
                    if '$' not in salary:
                        salary = f"${salary}"
                    return salary
        
        return None
    
    def extract_experience_level(self, text: str) -> Optional[str]:
        """Extract experience level using custom patterns."""
        for pattern in self.experience_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                experience = match.group(1).strip().lower()
                
                # Normalize experience levels
                if any(word in experience for word in ['entry', 'junior', '0-2', '1-3', 'new grad', 'intern']):
                    return 'Entry Level'
                elif any(word in experience for word in ['senior', '5-10', '7+', 'lead']):
                    return 'Senior Level'
                elif any(word in experience for word in ['principal', 'staff', '10+', 'expert']):
                    return 'Principal Level'
                else:
                    return 'Mid Level'
        
        return None
    
    def extract_employment_type(self, text: str) -> Optional[str]:
        """Extract employment type using custom patterns."""
        for pattern in self.employment_type_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                emp_type = match.group(1).strip().lower()
                
                # Normalize employment types
                if 'full' in emp_type:
                    return 'Full-time'
                elif 'part' in emp_type:
                    return 'Part-time'
                elif 'contract' in emp_type:
                    return 'Contract'
                elif 'remote' in emp_type:
                    return 'Remote'
                elif 'hybrid' in emp_type:
                    return 'Hybrid'
                elif 'intern' in emp_type:
                    return 'Internship'
                else:
                    return emp_type.title()
        
        return None
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills using pattern matching."""
        found_skills = []
        text_lower = text.lower()
        
        # Look for skills in the predefined list
        for skill in self.technical_skills:
            if skill.lower() in text_lower:
                # Verify it's a whole word match
                if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                    found_skills.append(skill)
        
        # Also try pattern-based extraction
        for pattern in self.skills_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                skills_text = match.group(1)
                # Extract skills from comma-separated or bullet-pointed lists
                additional_skills = self._parse_skills_from_text(skills_text)
                found_skills.extend(additional_skills)
        
        # Remove duplicates and return
        return list(set(found_skills))
    
    def extract_requirements(self, text: str) -> List[str]:
        """Extract job requirements using custom patterns."""
        requirements = []
        
        for pattern in self.requirements_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                req_text = match.group(1)
                parsed_reqs = self._parse_list_from_text(req_text)
                requirements.extend(parsed_reqs)
        
        return list(set(requirements))[:10]  # Limit to top 10
    
    def extract_benefits(self, text: str) -> List[str]:
        """Extract benefits using custom patterns."""
        benefits = []
        text_lower = text.lower()
        
        # Look for common benefits
        for benefit in self.common_benefits:
            if benefit in text_lower:
                benefits.append(benefit.title())
        
        # Also try pattern-based extraction
        for pattern in self.benefits_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                benefits_text = match.group(1)
                additional_benefits = self._parse_list_from_text(benefits_text)
                benefits.extend(additional_benefits)
        
        return list(set(benefits))[:8]  # Limit to top 8
    
    def _extract_company_from_url(self, url: str) -> Optional[str]:
        """Extract company name from URL domain."""
        try:
            domain = urlparse(url).netloc.lower()
            if not domain:
                return None
            
            # Remove common prefixes and suffixes
            domain = re.sub(r'^(www\.|jobs\.|careers\.|apply\.)', '', domain)
            domain = re.sub(r'\.(com|org|net|ca|co\.uk|io|ai)$', '', domain)
            
            # Split by dots and take the main part
            parts = domain.split('.')
            if parts:
                company_name = parts[0]
                
                # Clean up the name
                company_name = re.sub(r'[^a-zA-Z0-9\s]', ' ', company_name)
                company_name = ' '.join(word.capitalize() for word in company_name.split())
                
                if len(company_name) > 2:
                    return company_name
            
        except Exception as e:
            self.logger.debug(f"Error extracting company from URL: {e}")
        
        return None
    
    def _clean_title(self, title: str) -> str:
        """Clean and normalize job title."""
        # Remove HTML tags
        title = re.sub(r'<[^>]+>', '', title)
        
        # Remove extra whitespace
        title = ' '.join(title.split())
        
        # Remove common prefixes/suffixes
        title = re.sub(r'^\s*-\s*', '', title)
        title = re.sub(r'\s*-\s*.*$', '', title)
        
        return title.strip()
    
    def _clean_company_name(self, company: str) -> str:
        """Clean and normalize company name."""
        # Apply cleanup patterns
        for pattern in self.company_cleanup_patterns:
            company = re.sub(pattern, '', company)
        
        # Remove HTML tags
        company = re.sub(r'<[^>]+>', '', company)
        
        # Clean whitespace
        company = ' '.join(company.split())
        
        return company.strip()
    
    def _clean_location(self, location: str) -> str:
        """Clean and normalize location."""
        # Remove HTML tags
        location = re.sub(r'<[^>]+>', '', location)
        
        # Clean whitespace
        location = ' '.join(location.split())
        
        return location.strip()
    
    def _parse_skills_from_text(self, text: str) -> List[str]:
        """Parse skills from comma-separated or bullet-pointed text."""
        skills = []
        
        # Split by common separators
        items = re.split(r'[,;•\n\r]', text)
        
        for item in items:
            item = item.strip()
            if len(item) > 1 and len(item) < 50:
                # Check if it looks like a skill
                if any(skill.lower() in item.lower() for skill in self.technical_skills):
                    skills.append(item)
        
        return skills[:10]  # Limit to 10 skills
    
    def _parse_list_from_text(self, text: str) -> List[str]:
        """Parse list items from text (requirements, benefits, etc.)."""
        items = []
        
        # Split by common separators
        parts = re.split(r'[•\n\r]', text)
        
        for part in parts:
            part = part.strip()
            if len(part) > 5 and len(part) < 200:
                # Clean up the item
                part = re.sub(r'^\s*[-•]\s*', '', part)
                items.append(part)
        
        return items[:10]  # Limit to 10 items
    
    def _calculate_confidence(self, result: ExtractionResult) -> float:
        """Calculate confidence score based on successful extractions."""
        score = 0.0
        total_weight = 0.0
        
        # Weight different fields by importance
        field_weights = {
            'title': 0.25,
            'company': 0.20,
            'location': 0.15,
            'salary_range': 0.10,
            'experience_level': 0.10,
            'employment_type': 0.05,
            'skills': 0.10,
            'requirements': 0.03,
            'benefits': 0.02
        }
        
        for field, weight in field_weights.items():
            total_weight += weight
            value = getattr(result, field)
            
            if value:
                if isinstance(value, list):
                    # For lists, score based on number of items
                    if len(value) > 0:
                        score += weight * min(1.0, len(value) / 5)  # Max score at 5 items
                else:
                    # For strings, score based on presence and length
                    if len(str(value).strip()) > 2:
                        score += weight
        
        return min(1.0, score / total_weight) if total_weight > 0 else 0.0


# Convenience function for easy import
def get_custom_data_extractor() -> CustomDataExtractor:
    """
    Get a configured custom data extractor instance.
    
    Returns:
        Configured CustomDataExtractor instance
    """
    return CustomDataExtractor()