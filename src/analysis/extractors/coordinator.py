"""
Extraction coordinator - orchestrates all extractors.

This module provides the main CustomExtractor class that coordinates all specialized
extractors and maintains backward compatibility with the original API.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .base import ExtractionResult, ValidationResult
from .company import CompanyExtractor
from .compensation import CompensationExtractor
from .location import LocationExtractor
from .skills import SkillsExtractor
from .title import TitleExtractor

logger = logging.getLogger(__name__)


class CustomExtractor:
    """
    Improved custom data extractor with hierarchical patterns and web validation.

    Coordinates specialized extractors for different job data fields.
    Targets 95%+ reliability for structured data extraction.
    """

    def __init__(self):
        """Initialize extractor with all specialized extractors."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Initialize specialized extractors
        self.title_extractor = TitleExtractor()
        self.company_extractor = CompanyExtractor()
        self.location_extractor = LocationExtractor()
        self.compensation_extractor = CompensationExtractor()
        self.skills_extractor = SkillsExtractor()

        self.logger.info("CustomExtractor initialized with all specialized extractors")

    def extract_job_data(self, job_data: Dict[str, Any]) -> ExtractionResult:
        """
        Extract job data with improved reliability and validation.

        Main entry point for job data extraction. Handles edge cases for empty,
        minimal, or malformed input with reliable error handling.

        Args:
            job_data: Dictionary containing job information

        Returns:
            ExtractionResult with comprehensive analysis of extracted job data
        """
        start_time = time.time()

        try:
            # Validate input
            if not job_data or not isinstance(job_data, dict):
                self.logger.warning("Received empty or invalid job_data input")
                return ExtractionResult()

            # Initialize result
            result = ExtractionResult()

            # Extract core fields with error handling
            try:
                result.title = self.title_extractor.extract(job_data)
            except Exception as e:
                self.logger.error(f"Error extracting title: {e}")

            try:
                result.company = self.company_extractor.extract(job_data)
            except Exception as e:
                self.logger.error(f"Error extracting company: {e}")

            try:
                result.location = self.location_extractor.extract(job_data)
            except Exception as e:
                self.logger.error(f"Error extracting location: {e}")

            try:
                result.salary_range = self.compensation_extractor.extract_salary(job_data)
            except Exception as e:
                self.logger.error(f"Error extracting salary: {e}")

            try:
                result.experience_level = self.compensation_extractor.extract_experience(job_data)
            except Exception as e:
                self.logger.error(f"Error extracting experience: {e}")

            try:
                result.employment_type = self.compensation_extractor.extract_employment_type(
                    job_data
                )
            except Exception as e:
                self.logger.error(f"Error extracting employment type: {e}")

            try:
                result.skills = self.skills_extractor.extract_skills(job_data)
            except Exception as e:
                self.logger.error(f"Error extracting skills: {e}")

            try:
                result.requirements = self.skills_extractor.extract_requirements(job_data)
            except Exception as e:
                self.logger.error(f"Error extracting requirements: {e}")

            try:
                result.benefits = self.skills_extractor.extract_benefits(job_data)
            except Exception as e:
                self.logger.error(f"Error extracting benefits: {e}")

            # Validate extracted data
            self._validate_extraction(result)

            # Calculate overall confidence
            result.overall_confidence = self._calculate_overall_confidence(result)

            # Set metadata
            result.processing_time = time.time() - start_time
            result.extraction_method = "custom_modular"

            self.logger.info(
                f"Extraction completed with {result.overall_confidence:.2f} confidence "
                f"in {result.processing_time:.3f}s"
            )

            return result

        except Exception as e:
            self.logger.critical(f"Critical error in extract_job_data: {e}", exc_info=True)
            return ExtractionResult()

    def _validate_extraction(self, result: ExtractionResult) -> None:
        """Validate extraction results and add validation metadata.

        Args:
            result: ExtractionResult to validate and enhance with metadata
        """
        # Validate company with web validation if available
        if result.company:
            try:
                validation = self.company_extractor.validate_company(result.company)
                result.validation_results["company"] = validation
                if validation.is_valid and validation.confidence > 0.8:
                    result.web_validated_fields.append("company")
            except Exception as e:
                self.logger.warning(f"Company validation failed: {e}")

        # Calculate field confidences
        result.field_confidences = {
            "title": self._calculate_field_confidence(
                result.title, self.title_extractor._validate_title
            ),
            "company": self._calculate_field_confidence(
                result.company, self.company_extractor._validate_company_name
            ),
            "location": self._calculate_field_confidence(
                result.location, self.location_extractor._validate_location
            ),
            "salary_range": self._calculate_field_confidence(
                result.salary_range, self.compensation_extractor._validate_salary
            ),
            "skills": 0.7 if result.skills else 0.0,
        }

    def _calculate_field_confidence(self, value: Optional[str], validator: callable) -> float:
        """Calculate confidence for a single field.

        Args:
            value: Field value to evaluate
            validator: Validation function to call

        Returns:
            Confidence score (0.0-1.0)
        """
        if not value:
            return 0.0

        try:
            if validator(value):
                return 0.9
            else:
                return 0.5
        except Exception:
            return 0.5

    def _calculate_overall_confidence(self, result: ExtractionResult) -> float:
        """Calculate overall confidence score.

        Args:
            result: ExtractionResult with field confidences

        Returns:
            Overall confidence score (0.0-1.0)
        """
        # Define field importance weights
        weights = {
            "title": 0.28,
            "company": 0.22,
            "location": 0.15,
            "salary_range": 0.15,
            "skills": 0.15,
            "validation": 0.05,
        }

        # Base confidence from field extractions
        base_confidence = sum(
            result.field_confidences.get(field, 0.0) * weight
            for field, weight in weights.items()
            if field != "validation"
        )

        # Ensure minimum confidence if any field is present
        if base_confidence == 0.0 and any(v > 0.0 for v in result.field_confidences.values()):
            base_confidence = 0.3

        # Validation bonus
        validation_bonus = 0.0
        if result.web_validated_fields:
            validation_bonus = 0.05 * min(len(result.web_validated_fields), 5) / 5

        return min(base_confidence + validation_bonus, 1.0)


def get_Improved_custom_extractor() -> CustomExtractor:
    """
    Get a configured improved custom extractor instance.

    Backward compatibility function for existing code.

    Returns:
        Configured CustomExtractor instance
    """
    return CustomExtractor()
