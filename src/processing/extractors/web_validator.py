"""
Web Validator

Validates extracted job data using web search and validation rules.
"""

import logging
from typing import Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation checks."""
    is_valid: bool
    confidence: float
    validation_method: str
    details: str = ""


class WebValidator:
    """Validates extracted data using web search and rule-based validation."""
    
    def __init__(self, search_client: Optional[Any] = None):
        """
        Initialize WebValidator.
        Optionally accepts a search_client for real web validation.
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.search_client = search_client
        self.search_available = self._check_search_availability()

    def _check_search_availability(self) -> bool:
        """
        Check if web search is available (search_client is provided).
        """
        if self.search_client is None:
            self.logger.info("WebValidator: No search client provided")
            return False
        # Check if search_client has a 'search' method
        if not hasattr(self.search_client, 'search'):
            self.logger.warning(
                "WebValidator: Provided search client lacks 'search' method"
            )
            return False
        return True

    def validate_company(self, company: str) -> ValidationResult:
        """
        Validate company name using web search if available.
        Returns ValidationResult with details and confidence.
        """
        if not self.search_available:
            self.logger.info(
                f"WebValidator: Web search not available for company '{company}'"
            )
            return ValidationResult(
                is_valid=True,
                confidence=0.5,
                validation_method="no_web_search",
                details="Web search not available"
            )
        
        try:
            # Use search_client to search for company name
            results = self.search_client.search(f'"{company}" company')
            if results and len(results) > 0:
                self.logger.info(
                    f"WebValidator: Company '{company}' found in search results"
                )
                return ValidationResult(
                    is_valid=True,
                    confidence=0.9,
                    validation_method="web_search",
                    details=f"Company '{company}' found in search results"
                )
            else:
                self.logger.warning(
                    f"WebValidator: Company '{company}' not found in search"
                )
                return ValidationResult(
                    is_valid=False,
                    confidence=0.5,
                    validation_method="web_search",
                    details=f"Company '{company}' not found in search results"
                )
        except Exception as e:
            self.logger.error(
                f"WebValidator: Search failed for company '{company}': {e}"
            )
            return ValidationResult(
                is_valid=True,
                confidence=0.5,
                validation_method="web_search_failed",
                details=f"Search failed: {str(e)}"
            )

    def validate_job_title(self, title: str) -> ValidationResult:
        """Validate job title using rule-based validation."""
        if not title or len(title) < 3 or len(title) > 100:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_method="rule_based",
                details="Title length invalid"
            )
        
        # Check for job-related keywords
        job_keywords = [
            'engineer', 'developer', 'manager', 'analyst', 'specialist',
            'coordinator', 'director', 'lead', 'senior', 'junior'
        ]
        
        has_job_keywords = any(keyword in title.lower() for keyword in job_keywords)
        
        return ValidationResult(
            is_valid=has_job_keywords,
            confidence=0.8 if has_job_keywords else 0.3,
            validation_method="rule_based",
            details="Job keywords found" if has_job_keywords else "No job keywords"
        )

    def validate_location(self, location: str) -> ValidationResult:
        """Validate location format using rule-based validation."""
        if not location or len(location) < 3:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_method="rule_based",
                details="Location too short"
            )
        
        # Check for valid location patterns
        import re
        location_patterns = [
            r'^[A-Z][a-zA-Z\s\-]+,\s*[A-Z]{2}$',  # City, Province/State
            r'(?i)^(remote|hybrid|work from home)$',  # Remote work
        ]
        
        is_valid = any(re.match(pattern, location) for pattern in location_patterns)
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=0.8 if is_valid else 0.4,
            validation_method="rule_based",
            details="Valid location format" if is_valid else "Invalid format"
        )

    def validate_salary(self, salary: str) -> ValidationResult:
        """Validate salary format using rule-based validation."""
        if not salary:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_method="rule_based",
                details="Empty salary"
            )
        
        # Check for reasonable salary patterns
        import re
        salary_patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+',  # $50,000 - $70,000
            r'[\d,]+k\s*-\s*[\d,]+k',    # 50k - 70k
            r'\$[\d,]+(?:k|,000)?',      # $50,000 or $50k
        ]
        
        is_valid = any(re.search(pattern, salary, re.IGNORECASE) 
                      for pattern in salary_patterns)
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=0.8 if is_valid else 0.3,
            validation_method="rule_based",
            details="Valid salary format" if is_valid else "Invalid format"
        )
