"""
Salary, experience, and employment type extraction.

Handles extraction and standardization of salary ranges, experience levels,
and employment type information.
"""

import logging
import re
from typing import Any, Dict, Optional

from .base import BaseExtractor, ExtractionConfidence, PatternMatch

logger = logging.getLogger(__name__)


class CompensationExtractor(BaseExtractor):
    """Extracts salary, experience, and employment type information."""

    def __init__(self):
        """Initialize compensation extractor with patterns."""
        super().__init__()
        self._init_salary_patterns()
        self._init_experience_patterns()
        self._init_employment_patterns()

    def _init_salary_patterns(self) -> None:
        """Initialize salary extraction patterns."""
        self.salary_patterns = {}
        raw_patterns = {
            "very_high": [
                r"(?i)salary[:\s]*\$?([\d,]+)\s*-\s*\$?([\d,]+)",
                r"(?i)compensation[:\s]*\$?([\d,]+)\s*-\s*\$?([\d,]+)",
            ],
            "high": [
                r"\$?([\d,]+)k?\s*-\s*\$?([\d,]+)k?(?:\s*(?:per\s*year|annually|/year))?",
                r"(?i)(?:salary|pay|compensation)[:\s]*\$?([\d,]+)(?:k|,000)?",
            ],
            "medium": [
                r"\$[\d,]+\s*-\s*\$[\d,]+",
                r"[\d,]+k\s*-\s*[\d,]+k",
            ],
        }

        for level, patterns in raw_patterns.items():
            self.salary_patterns[level] = [
                re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns
            ]

    def _init_experience_patterns(self) -> None:
        """Initialize experience level patterns."""
        self.experience_patterns = {}
        raw_patterns = {
            "very_high": [
                r'(?i)experience[_\s]*level[:\s]*["\']([^"\']+)["\']',
                r'(?i)seniority[:\s]*["\']([^"\']+)["\']',
            ],
            "high": [
                r"(?i)(Senior|Junior|Entry[_\s]*Level|Mid[_\s]*Level|Lead|Principal|Staff)",
                r"(?i)(\d+)\+?\s*years?\s*(?:of\s*)?experience",
            ],
            "medium": [
                r"(?i)experience[:\s]+([^.\n]{5,30})",
                r"(?i)level[:\s]+([^.\n]{5,20})",
            ],
        }

        for level, patterns in raw_patterns.items():
            self.experience_patterns[level] = [
                re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns
            ]

    def _init_employment_patterns(self) -> None:
        """Initialize employment type patterns."""
        self.employment_patterns = {}
        raw_patterns = {
            "very_high": [
                r'(?i)employment[_\s]*type[:\s]*["\']([^"\']+)["\']',
                r'(?i)job[_\s]*type[:\s]*["\']([^"\']+)["\']',
            ],
            "high": [
                r"(?i)(Full[_\s]*time|Part[_\s]*time|Contract|Temporary|Permanent|Freelance)",
                r"(?i)employment[:\s]+([^.\n]{5,20})",
            ],
        }

        for level, patterns in raw_patterns.items():
            self.employment_patterns[level] = [
                re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns
            ]

    def extract_salary(self, job_data: Dict[str, Any]) -> Optional[str]:
        """Extract salary range from job data.

        Args:
            job_data: Dictionary containing job posting data

        Returns:
            Extracted and standardized salary range or None
        """
        content = self._prepare_content(job_data)
        candidates = []

        for confidence_level, patterns in self.salary_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(content)
                for match in matches:
                    if isinstance(match, tuple):
                        if len(match) == 2:
                            salary = f"${match[0]} - ${match[1]}"
                        else:
                            salary = " ".join(match).strip()
                    else:
                        salary = match.strip()

                    if self._validate_salary(salary):
                        confidence = ExtractionConfidence[confidence_level.upper()].value
                        candidates.append(
                            PatternMatch(
                                value=salary,
                                confidence=confidence,
                                pattern_type=confidence_level,
                                source_location="content",
                            )
                        )

        if candidates:
            best = max(candidates, key=lambda x: x.confidence)
            return self._standardize_salary(best.value)

        return None

    def extract_experience(self, job_data: Dict[str, Any]) -> Optional[str]:
        """Extract experience level from job data.

        Args:
            job_data: Dictionary containing job posting data

        Returns:
            Extracted and standardized experience level or None
        """
        content = self._prepare_content(job_data)
        candidates = []

        for confidence_level, patterns in self.experience_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(content)
                for match in matches:
                    if isinstance(match, tuple):
                        experience = " ".join(match).strip()
                    else:
                        experience = match.strip()

                    if self._validate_experience(experience):
                        confidence = ExtractionConfidence[confidence_level.upper()].value
                        candidates.append(
                            PatternMatch(
                                value=experience,
                                confidence=confidence,
                                pattern_type=confidence_level,
                                source_location="content",
                            )
                        )

        if candidates:
            best = max(candidates, key=lambda x: x.confidence)
            return self._standardize_experience(best.value)

        return None

    def extract_employment_type(self, job_data: Dict[str, Any]) -> Optional[str]:
        """Extract employment type from job data.

        Args:
            job_data: Dictionary containing job posting data

        Returns:
            Extracted and standardized employment type or None
        """
        content = self._prepare_content(job_data)
        candidates = []

        for confidence_level, patterns in self.employment_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(content)
                for match in matches:
                    employment_type = match.strip()

                    if self._validate_employment_type(employment_type):
                        confidence = ExtractionConfidence[confidence_level.upper()].value
                        candidates.append(
                            PatternMatch(
                                value=employment_type,
                                confidence=confidence,
                                pattern_type=confidence_level,
                                source_location="content",
                            )
                        )

        if candidates:
            best = max(candidates, key=lambda x: x.confidence)
            return self._standardize_employment_type(best.value)

        return None

    def _prepare_content(self, job_data: Dict[str, Any]) -> str:
        """Prepare content for extraction."""
        content_parts = []

        for field in ["description", "job_description", "summary"]:
            value = job_data.get(field)
            if value and isinstance(value, str):
                content_parts.append(value)

        return "\n".join(content_parts)

    def _validate_salary(self, salary: str) -> bool:
        """Validate salary format."""
        if not salary:
            return False

        salary_patterns = [
            r"\$[\d,]+\s*-\s*\$[\d,]+",
            r"[\d,]+k\s*-\s*[\d,]+k",
            r"\$[\d,]+(?:k|,000)?",
        ]

        return any(re.search(pattern, salary, re.IGNORECASE) for pattern in salary_patterns)

    def _validate_experience(self, experience: str) -> bool:
        """Validate experience level."""
        if not experience:
            return False

        valid_levels = ["entry", "junior", "mid", "senior", "lead", "principal", "staff"]
        return any(level in experience.lower() for level in valid_levels) or re.search(
            r"\d+\s*years?", experience, re.IGNORECASE
        )

    def _validate_employment_type(self, emp_type: str) -> bool:
        """Validate employment type."""
        if not emp_type:
            return False

        valid_types = ["full-time", "part-time", "contract", "temporary", "permanent", "freelance"]
        return any(valid_type in emp_type.lower().replace(" ", "-") for valid_type in valid_types)

    def _standardize_salary(self, salary: str) -> str:
        """Standardize salary format."""
        # Convert k notation to full numbers
        salary = re.sub(r"(\d+)k", r"\1,000", salary, flags=re.IGNORECASE)

        # Ensure dollar signs
        if not salary.startswith("$"):
            salary = "$" + salary

        return salary

    def _standardize_experience(self, experience: str) -> str:
        """Standardize experience level."""
        experience_lower = experience.lower()

        if "senior" in experience_lower:
            return "Senior"
        elif "junior" in experience_lower or "entry" in experience_lower:
            return "Junior"
        elif "lead" in experience_lower:
            return "Lead"
        elif "principal" in experience_lower:
            return "Principal"
        elif re.search(r"\d+\s*years?", experience_lower):
            years_match = re.search(r"(\d+)\s*years?", experience_lower)
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
        emp_type_lower = emp_type.lower().replace(" ", "-")

        if "full" in emp_type_lower:
            return "Full-time"
        elif "part" in emp_type_lower:
            return "Part-time"
        elif "contract" in emp_type_lower:
            return "Contract"
        elif "temp" in emp_type_lower:
            return "Temporary"
        elif "permanent" in emp_type_lower:
            return "Permanent"
        elif "freelance" in emp_type_lower:
            return "Freelance"

        return emp_type.title()
