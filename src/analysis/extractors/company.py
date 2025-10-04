"""
Company name extraction and validation.

Handles company name extraction with hierarchical patterns and domain validation
for fast, reliable results without web scraping.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from .base import (
    BaseExtractor,
    ExtractionConfidence,
    ExtractionResult,
    PatternMatch,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class CompanyExtractor(BaseExtractor):
    """Extracts and validates company names with domain validation."""

    def __init__(self):
        """Initialize company extractor with patterns and validation."""
        super().__init__()
        self._init_patterns()
        self._init_known_companies()
        self._init_web_validator()

    def _init_patterns(self) -> None:
        """Initialize hierarchical company extraction patterns."""
        self.patterns = {}
        raw_patterns = {
            "very_high": [
                r'(?i)company[_\s]*name[:\s]*["\']([^"\']{2,50})["\']',
                r'<span[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)</span>',
                r'data-testid="company"[^>]*>([^<]+)<',
            ],
            "high": [
                r"(?i)company[:\s]+([A-Z][a-zA-Z\s&.,\-()]{2,50})(?=\s*\n|\s*$|\s*Location|\s*Salary)",
                r"(?i)employer[:\s]+([A-Z][a-zA-Z\s&.,\-()]{2,50})(?=\s*\n|\s*$|\s*Location|\s*Salary)",
                r"(?i)at\s+([A-Z][a-zA-Z\s&.,\-()]{2,50})\s*(?:\n|$)",
            ],
            "medium": [
                r"([A-Z][a-zA-Z\s&.,\-()]{2,50})\s+(?:Inc|LLC|Corp|Corporation|Ltd|Limited|Company|Co\.)",
                r"([A-Z][a-zA-Z\s&.,\-()]{2,50})\s+(?:Technologies|Technology|Tech|Solutions|Systems|Services)",
            ],
            "low": [
                r"([A-Z][a-zA-Z\s&.,\-()]{3,40})",
            ],
        }

        for level, patterns in raw_patterns.items():
            self.patterns[level] = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns]

    def _init_known_companies(self) -> None:
        """Initialize database of known companies."""
        self.known_companies = {
            # Big Tech
            "google",
            "microsoft",
            "amazon",
            "apple",
            "meta",
            "facebook",
            "netflix",
            "tesla",
            "nvidia",
            "intel",
            "amd",
            "qualcomm",
            # Canadian Tech
            "shopify",
            "blackberry",
            "corel",
            "opentext",
            "constellation software",
            "cgi",
            "manulife",
            "rbc",
            "td bank",
            "scotiabank",
            "bmo",
            # Startups & Scale-ups
            "stripe",
            "airbnb",
            "uber",
            "lyft",
            "doordash",
            "instacart",
            "zoom",
            "slack",
            "atlassian",
            "datadog",
            "snowflake",
            # Consulting & Services
            "accenture",
            "deloitte",
            "pwc",
            "kpmg",
            "ey",
            "mckinsey",
            "ibm",
            "cognizant",
            "infosys",
            "tcs",
            "wipro",
            "capgemini",
        }

    def _init_web_validator(self) -> None:
        """Initialize domain-based web validator."""
        try:
            from ..utils.domain_validator import DomainValidator

            self.domain_validator = DomainValidator()
            self.validation_available = True
        except ImportError:
            self.logger.warning("DomainValidator not available, validation disabled")
            self.domain_validator = None
            self.validation_available = False

    def extract(self, job_data: Dict[str, Any]) -> Optional[str]:
        """Extract company name from job data.

        Args:
            job_data: Dictionary containing job posting data

        Returns:
            Extracted company name or None
        """
        content = self._prepare_content(job_data)
        candidates = []

        # First check if company is already in job_data (highest priority)
        if job_data.get("company"):
            company = job_data["company"].strip()
            if self._validate_company_name(company):
                candidates.append(
                    PatternMatch(
                        value=company,
                        confidence=ExtractionConfidence.HIGH.value,
                        pattern_type="job_data",
                        source_location="job_data",
                    )
                )

        # Extract from content using patterns
        for confidence_level, patterns in self.patterns.items():
            for pattern in patterns:
                matches = pattern.findall(content)
                for match in matches:
                    if isinstance(match, tuple):
                        match = " ".join(match).strip()

                    # Clean and validate company
                    cleaned_match = self._clean_company_name(match)
                    if self._validate_company_name(cleaned_match):
                        confidence = ExtractionConfidence[confidence_level.upper()].value
                        candidates.append(
                            PatternMatch(
                                value=cleaned_match,
                                confidence=confidence,
                                pattern_type=confidence_level,
                                source_location="content",
                            )
                        )

        # Return best candidate
        if candidates:
            best = max(candidates, key=lambda x: x.confidence)
            return self._clean_company_name(best.value)

        return None

    def validate_company(self, company: str) -> ValidationResult:
        """Validate company name using domain validation.

        Args:
            company: Company name to validate

        Returns:
            ValidationResult with validation status and confidence
        """
        if not company:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_method="empty",
                details="Empty company name",
            )

        # Use domain validation if available
        if self.validation_available and self.domain_validator:
            try:
                result = self.domain_validator.validate_company_domain(company)
                return ValidationResult(
                    is_valid=result["is_valid"],
                    confidence=result["confidence"],
                    validation_method=result["method"],
                    details=f"Domain validation: {result.get('domain', 'no domain found')}",
                )
            except Exception as e:
                self.logger.error(f"Domain validation error for '{company}': {e}")

        # Fallback to basic validation
        is_valid = self._validate_company_name(company)
        return ValidationResult(
            is_valid=is_valid,
            confidence=0.5 if is_valid else 0.0,
            validation_method="basic",
            details="Basic pattern validation",
        )

    def _prepare_content(self, job_data: Dict[str, Any]) -> str:
        """Prepare content for extraction."""
        content_parts = []

        for field in ["description", "job_description", "company", "summary"]:
            value = job_data.get(field)
            if value and isinstance(value, str):
                content_parts.append(value)

        return "\n".join(content_parts)

    def _clean_company_name(self, company: str) -> str:
        """Clean and normalize company name."""
        if not company:
            return ""

        # Remove newlines and extra whitespace
        cleaned = re.sub(r"\s+", " ", company.strip())

        # Remove common noise words
        noise_words = ["location", "salary", "posted", "apply", "job", "opening", "careers"]

        # Split by common separators and take first part
        parts = re.split(r"[|\-–—\n]", cleaned)
        cleaned = parts[0].strip()

        # Remove noise words from the end
        words = cleaned.split()
        while words and words[-1].lower() in noise_words:
            words.pop()

        # Ensure reasonable length
        result = " ".join(words).strip()
        if len(result) > 60:
            result = result[:60].strip()

        return result

    def _validate_company_name(self, company: str) -> bool:
        """Validate company name."""
        if not company or len(company) < 2 or len(company) > 80:
            return False

        # Check against known companies
        if company.lower() in self.known_companies:
            return True

        # Basic validation rules
        return not any(
            invalid in company.lower()
            for invalid in ["job", "position", "role", "hiring", "apply", "career"]
        )
