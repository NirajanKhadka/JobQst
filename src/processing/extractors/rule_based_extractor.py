"""
Rule-Based Extractor

Main extraction logic using pattern matching, industry standards,
and web validation for reliable job data extraction.
"""

import re
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .base_extractor import ExtractionResult, ExtractionConfidence
from .pattern_matcher import JobPatternMatcher
from .industry_standards import IndustryStandardsDatabase
from .web_validator import WebValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class RuleBasedExtractionResult(ExtractionResult):
    """Enhanced result with rule-based metadata."""
    # Additional rule-based fields
    field_confidences: Dict[str, float] = field(default_factory=dict)
    validation_results: Dict[str, ValidationResult] = field(default_factory=dict)
    patterns_used: Dict[str, str] = field(default_factory=dict)
    web_validated_fields: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize default values."""
        super().__post_init__()
        if self.skills is None:
            self.skills = []
        if self.requirements is None:
            self.requirements = []
        if self.validation_errors is None:
            self.validation_errors = []


class RuleBasedExtractor:
    """
    Rule-based job data extractor with hierarchical patterns and validation.
    Uses pattern matching, industry standards, and web validation.
    """
    
    def __init__(self, search_client: Optional[Any] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.pattern_matcher = JobPatternMatcher()
        self.industry_db = IndustryStandardsDatabase()
        self.web_validator = WebValidator(search_client)
        
    def extract_job_data(self, job_data: Dict[str, Any]) -> RuleBasedExtractionResult:
        """
        Extract job data with rule-based reliability and validation.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            RuleBasedExtractionResult: Comprehensive analysis of extracted data
        """
        start_time = time.time()
        
        try:
            if not job_data or not isinstance(job_data, dict):
                self.logger.warning("Received empty or invalid job_data input")
                return RuleBasedExtractionResult()
            
            content = self._prepare_content(job_data)
            result = RuleBasedExtractionResult()
            
            # Extract core fields with error handling
            self._extract_all_fields(content, job_data, result)
            
            # Validate extraction results
            self._validate_extraction(result)
            
            # Calculate overall confidence
            result.overall_confidence = self._calculate_overall_confidence(result)
            
            # Set metadata
            result.processing_time = time.time() - start_time
            result.extraction_method = "rule_based"
            
            self.logger.info(
                f"Rule-based extraction completed with "
                f"{result.overall_confidence:.2f} confidence"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Critical error in extract_job_data: {e}")
            return RuleBasedExtractionResult()
    
    def _prepare_content(self, job_data: Dict[str, Any]) -> str:
        """Prepare job content for extraction."""
        content_parts = []
        
        # Add description/job_description
        for desc_field in ['description', 'job_description']:
            if job_data.get(desc_field) and isinstance(job_data.get(desc_field), str):
                content_parts.append(job_data[desc_field])
        
        # Add other relevant fields
        for field in ['title', 'company', 'location', 'summary']:
            value = job_data.get(field)
            if value and isinstance(value, str):
                content_parts.append(f"{field}: {value}")
        
        return '\n'.join(content_parts)
    
    def _extract_all_fields(self, content: str, job_data: Dict[str, Any], 
                           result: RuleBasedExtractionResult) -> None:
        """Extract all fields with comprehensive error handling."""
        extraction_methods = [
            ('title', self._extract_title),
            ('company', lambda c: self._extract_company(c, job_data)),
            ('location', self._extract_location),
            ('salary_range', self._extract_salary),
            ('experience_level', self._extract_experience),
            ('employment_type', self._extract_employment_type),
            ('skills', self._extract_skills),
            ('requirements', self._extract_requirements),
        ]
        
        for field_name, method in extraction_methods:
            try:
                value = method(content)
                setattr(result, field_name, value)
            except Exception as e:
                self.logger.error(f"Error extracting {field_name}: {e}")
                setattr(result, field_name, None if field_name != 'skills' else [])
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extract job title using pattern matching."""
        candidates = self.pattern_matcher.extract_with_patterns(content, 'title')
        
        # Filter and validate candidates
        valid_candidates = []
        for candidate in candidates:
            cleaned_title = self._clean_title(candidate.value)
            if self._validate_title(cleaned_title):
                valid_candidates.append(candidate._replace(value=cleaned_title))
        
        # Return best candidate
        best_match = self.pattern_matcher.get_best_match(valid_candidates)
        return best_match.value if best_match else None
    
    def _extract_company(self, content: str, job_data: Dict[str, Any]) -> Optional[str]:
        """Extract company name with validation."""
        candidates = []
        
        # First check if company is already in job_data
        if job_data.get('company'):
            company = job_data['company'].strip()
            if self._validate_company_name(company):
                from .pattern_matcher import PatternMatch
                candidates.append(PatternMatch(
                    value=company,
                    confidence=0.85,
                    pattern_type="job_data",
                    source_location="job_data"
                ))
        
        # Extract from content using patterns
        pattern_candidates = self.pattern_matcher.extract_with_patterns(content, 'company')
        
        # Validate pattern candidates
        for candidate in pattern_candidates:
            cleaned_company = self._clean_company_name(candidate.value)
            if self._validate_company_name(cleaned_company):
                candidates.append(candidate._replace(value=cleaned_company))
        
        # Return best candidate
        best_match = self.pattern_matcher.get_best_match(candidates)
        return best_match.value if best_match else None
    
    def _extract_location(self, content: str) -> Optional[str]:
        """Extract location with format standardization."""
        candidates = self.pattern_matcher.extract_with_patterns(content, 'location')
        
        # Validate and standardize candidates
        valid_candidates = []
        for candidate in candidates:
            if self._validate_location(candidate.value):
                standardized = self._standardize_location(candidate.value)
                valid_candidates.append(candidate._replace(value=standardized))
        
        best_match = self.pattern_matcher.get_best_match(valid_candidates)
        return best_match.value if best_match else None
    
    def _extract_salary(self, content: str) -> Optional[str]:
        """Extract salary range with format standardization."""
        candidates = self.pattern_matcher.extract_with_patterns(content, 'salary')
        
        # Validate and standardize candidates
        valid_candidates = []
        for candidate in candidates:
            if self._validate_salary(candidate.value):
                standardized = self._standardize_salary(candidate.value)
                valid_candidates.append(candidate._replace(value=standardized))
        
        best_match = self.pattern_matcher.get_best_match(valid_candidates)
        return best_match.value if best_match else None
    
    def _extract_experience(self, content: str) -> Optional[str]:
        """Extract experience level."""
        candidates = self.pattern_matcher.extract_with_patterns(content, 'experience')
        
        # Validate and standardize candidates
        valid_candidates = []
        for candidate in candidates:
            if self._validate_experience(candidate.value):
                standardized = self._standardize_experience(candidate.value)
                valid_candidates.append(candidate._replace(value=standardized))
        
        best_match = self.pattern_matcher.get_best_match(valid_candidates)
        return best_match.value if best_match else None
    
    def _extract_employment_type(self, content: str) -> Optional[str]:
        """Extract employment type."""
        candidates = self.pattern_matcher.extract_with_patterns(content, 'employment')
        
        # Validate and standardize candidates
        valid_candidates = []
        for candidate in candidates:
            if self._validate_employment_type(candidate.value):
                standardized = self._standardize_employment_type(candidate.value)
                valid_candidates.append(candidate._replace(value=standardized))
        
        best_match = self.pattern_matcher.get_best_match(valid_candidates)
        return best_match.value if best_match else None
    
    def _extract_skills(self, content: str) -> List[str]:
        """Extract technical skills."""
        all_skills = set()
        
        # Extract from skill patterns
        candidates = self.pattern_matcher.extract_with_patterns(content, 'skills')
        for candidate in candidates:
            skills = self.pattern_matcher.parse_skills_from_text(candidate.value)
            all_skills.update(skills)
        
        # Look for individual skills in content
        for skill in self.industry_db.skills:
            match = re.search(r'\b' + re.escape(skill) + r'\b', content, re.IGNORECASE)
            if match:
                all_skills.add(match.group())
        
        # Validate and return top skills
        validated_skills = [skill for skill in all_skills if self._validate_skill(skill)]
        return sorted(validated_skills)[:15]  # Limit to top 15
    
    def _extract_requirements(self, content: str) -> List[str]:
        """Extract job requirements."""
        requirements = []
        
        # Look for requirement sections
        requirement_patterns = [
            r'(?i)requirements?[:\s]*\n?([^.\n]{10,200})',
            r'(?i)qualifications?[:\s]*\n?([^.\n]{10,200})',
            r'(?i)must\s*have[:\s]*([^.\n]{10,200})',
            r'(?i)required[:\s]*([^.\n]{10,200})',
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                req = match.strip()
                if len(req) > 10 and self._validate_requirement(req):
                    requirements.append(req)
        
        return requirements[:10]  # Limit to top 10
    
    # Validation methods
    def _clean_title(self, title: str) -> str:
        """Clean and normalize job title."""
        if not title:
            return ""
        
        # Remove newlines and extra whitespace
        cleaned = re.sub(r'\s+', ' ', title.strip())
        
        # Remove common noise words and separators
        parts = re.split(r'[|\-–—\n]', cleaned)
        cleaned = parts[0].strip()
        
        # Remove noise words from the end
        noise_words = ['company', 'location', 'salary', 'posted', 'apply', 'job']
        words = cleaned.split()
        while words and words[-1].lower() in noise_words:
            words.pop()
        
        # Ensure reasonable length
        result = ' '.join(words).strip()
        return result[:80] if len(result) > 80 else result
    
    def _validate_title(self, title: str) -> bool:
        """Validate job title."""
        if not title or len(title) < 3 or len(title) > 100:
            return False
        
        # Check against industry standards
        if self.industry_db.is_valid_job_title(title):
            return True
        
        # Check for job-related keywords
        job_keywords = ['engineer', 'developer', 'manager', 'analyst', 'specialist']
        return any(keyword in title.lower() for keyword in job_keywords)
    
    def _clean_company_name(self, company: str) -> str:
        """Clean and normalize company name."""
        if not company:
            return ""
        
        # Remove extra whitespace and separators
        cleaned = re.sub(r'\s+', ' ', company.strip())
        parts = re.split(r'[|\-–—\n]', cleaned)
        cleaned = parts[0].strip()
        
        # Remove noise words
        noise_words = ['location', 'salary', 'posted', 'apply', 'job', 'careers']
        words = cleaned.split()
        while words and words[-1].lower() in noise_words:
            words.pop()
        
        result = ' '.join(words).strip()
        return result[:60] if len(result) > 60 else result
    
    def _validate_company_name(self, company: str) -> bool:
        """Validate company name."""
        if not company or len(company) < 2 or len(company) > 80:
            return False
        
        # Check against industry standards
        if self.industry_db.is_valid_company(company):
            return True
        
        # Basic validation rules
        invalid_terms = ['job', 'position', 'role', 'hiring', 'apply', 'career']
        return not any(invalid in company.lower() for invalid in invalid_terms)
    
    def _validate_location(self, location: str) -> bool:
        """Validate location format."""
        if not location or len(location) < 3:
            return False
        
        # Check against industry standards
        if self.industry_db.is_valid_location(location):
            return True
        
        # Check for valid location patterns
        location_patterns = [
            r'^[A-Z][a-zA-Z\s\-]+,\s*[A-Z]{2}$',  # City, Province/State
            r'(?i)^(remote|hybrid|work from home)$',  # Remote work
        ]
        
        return any(re.match(pattern, location) for pattern in location_patterns)
    
    def _validate_salary(self, salary: str) -> bool:
        """Validate salary format."""
        if not salary:
            return False
        
        # Check for reasonable salary patterns
        salary_patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+',  # $50,000 - $70,000
            r'[\d,]+k\s*-\s*[\d,]+k',    # 50k - 70k
            r'\$[\d,]+(?:k|,000)?',      # $50,000 or $50k
        ]
        
        return any(re.search(pattern, salary, re.IGNORECASE) 
                  for pattern in salary_patterns)
    
    def _validate_experience(self, experience: str) -> bool:
        """Validate experience level."""
        if not experience:
            return False
        
        valid_levels = ['entry', 'junior', 'mid', 'senior', 'lead', 'principal']
        return (any(level in experience.lower() for level in valid_levels) or 
                re.search(r'\d+\s*years?', experience, re.IGNORECASE))
    
    def _validate_employment_type(self, emp_type: str) -> bool:
        """Validate employment type."""
        if not emp_type:
            return False
        
        valid_types = ['full-time', 'part-time', 'contract', 'temporary', 'permanent']
        return any(valid_type in emp_type.lower().replace(' ', '-') 
                  for valid_type in valid_types)
    
    def _validate_skill(self, skill: str) -> bool:
        """Validate technical skill."""
        if not skill or len(skill) < 2:
            return False
        
        return self.industry_db.is_valid_skill(skill)
    
    def _validate_requirement(self, requirement: str) -> bool:
        """Validate job requirement."""
        return 10 < len(requirement) < 200
    
    # Standardization methods
    def _standardize_location(self, location: str) -> str:
        """Standardize location format."""
        # Standardize remote work indicators
        if re.search(r'(?i)(remote|work from home|telecommute)', location):
            return "Remote"
        
        # Standardize city, province format
        match = re.match(r'([^,]+),\s*([A-Z]{2})', location)
        if match:
            return f"{match.group(1).strip()}, {match.group(2).upper()}"
        
        return location.strip()
    
    def _standardize_salary(self, salary: str) -> str:
        """Standardize salary format."""
        # Convert k notation to full numbers
        salary = re.sub(r'(\d+)k', r'\1,000', salary, flags=re.IGNORECASE)
        
        # Ensure dollar signs
        if not salary.startswith('$'):
            salary = '$' + salary
        
        return salary
    
    def _standardize_experience(self, experience: str) -> str:
        """Standardize experience level."""
        experience_lower = experience.lower()
        
        if 'senior' in experience_lower:
            return "Senior"
        elif 'junior' in experience_lower or 'entry' in experience_lower:
            return "Junior"
        elif 'lead' in experience_lower:
            return "Lead"
        elif 'principal' in experience_lower:
            return "Principal"
        elif re.search(r'\d+\s*years?', experience_lower):
            years_match = re.search(r'(\d+)\s*years?', experience_lower)
            if years_match:
                years = int(years_match.group(1))
                if years <= 2:
                    return "Junior"
                elif years <= 5:
                    return "Mid-Level"
                else:
                    return "Senior"
        
        return experience.title()
    
    def _standardize_employment_type(self, emp_type: str) -> str:
        """Standardize employment type."""
        emp_type_lower = emp_type.lower().replace(' ', '-')
        
        type_mapping = {
            'full': "Full-time",
            'part': "Part-time",
            'contract': "Contract",
            'temp': "Temporary",
            'permanent': "Permanent",
            'freelance': "Freelance"
        }
        
        for key, value in type_mapping.items():
            if key in emp_type_lower:
                return value
        
        return emp_type.title()
    
    def _validate_extraction(self, result: RuleBasedExtractionResult) -> None:
        """Validate extraction results and add validation metadata."""
        # Validate company with web search if available
        if result.company:
            validation = self.web_validator.validate_company(result.company)
            result.validation_results['company'] = validation
            if validation.is_valid and validation.confidence > 0.8:
                result.web_validated_fields.append('company')
        
        # Calculate field confidences
        result.field_confidences = {
            'title': self._get_field_confidence(result.title, self._validate_title),
            'company': self._get_field_confidence(result.company, 
                                                self._validate_company_name),
            'location': self._get_field_confidence(result.location, 
                                                 self._validate_location),
            'salary_range': self._get_field_confidence(result.salary_range, 
                                                     self._validate_salary),
            'skills': 0.7 if result.skills else 0.0,
        }
    
    def _get_field_confidence(self, value: Optional[str], 
                            validator_func) -> float:
        """Get confidence for a field value."""
        if not value:
            return 0.0
        return 0.9 if validator_func(value) else 0.5
    
    def _calculate_overall_confidence(self, result: RuleBasedExtractionResult) -> float:
        """Calculate overall confidence score."""
        weights = {
            'title': 0.28,
            'company': 0.22,
            'location': 0.15,
            'salary_range': 0.15,
            'skills': 0.15,
            'validation': 0.05
        }
        
        # Base confidence from field extractions
        base_confidence = sum(
            result.field_confidences.get(field, 0.0) * weight
            for field, weight in weights.items()
            if field != 'validation'
        )
        
        # Ensure minimum confidence if any field is present
        if base_confidence == 0.0 and any(v > 0.0 for v in result.field_confidences.values()):
            base_confidence = 0.3
        
        # Validation bonus
        validation_bonus = 0.0
        if result.web_validated_fields:
            validation_bonus = 0.1 * len(result.web_validated_fields) / 5
        
        return min(base_confidence + validation_bonus, 1.0)


# Convenience function
def get_rule_based_extractor(search_client: Optional[Any] = None) -> RuleBasedExtractor:
    """Get a configured rule-based extractor instance."""
    return RuleBasedExtractor(search_client)

