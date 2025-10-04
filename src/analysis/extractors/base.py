"""
Base classes and data structures for job data extraction.

This module provides the foundation for all extractors with confidence scoring,
validation, and pattern matching infrastructure.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, NamedTuple

logger = logging.getLogger(__name__)


class ExtractionConfidence(Enum):
    """Confidence levels for extraction results."""

    VERY_HIGH = 0.95  # Web-validated or multiple pattern matches
    HIGH = 0.85  # Single high-confidence pattern match
    MEDIUM = 0.70  # Medium-confidence pattern or validated format
    LOW = 0.50  # Low-confidence pattern or fallback
    VERY_LOW = 0.25  # Unreliable extraction


class PatternMatch(NamedTuple):
    """Represents a pattern match with metadata."""

    value: str
    confidence: float
    pattern_type: str
    source_location: str


@dataclass
class ValidationResult:
    """Result of validation checks."""

    is_valid: bool
    confidence: float
    validation_method: str
    details: str = ""


@dataclass
class ExtractionResult:
    """Comprehensive extraction result with validation and confidence scoring."""

    # Core extracted data
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)

    # Metadata
    overall_confidence: float = 0.0
    field_confidences: Dict[str, float] = field(default_factory=dict)
    validation_results: Dict[str, ValidationResult] = field(default_factory=dict)
    extraction_method: str = "custom"
    processing_time: float = 0.0
    patterns_used: Dict[str, str] = field(default_factory=dict)
    web_validated_fields: List[str] = field(default_factory=list)


class BaseExtractor:
    """Abstract base class for all extractors.

    Provides common functionality for pattern matching, validation,
    and confidence scoring.
    """

    def __init__(self):
        """Initialize base extractor."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def extract(self, job_data: Dict) -> ExtractionResult:
        """Extract data from job posting.

        Args:
            job_data: Dictionary containing job posting data

        Returns:
            ExtractionResult with extracted data and confidence scores
        """
        raise NotImplementedError("Subclasses must implement extract()")

    def calculate_confidence(self, matches: List[PatternMatch]) -> float:
        """Calculate overall confidence from pattern matches.

        Args:
            matches: List of pattern matches

        Returns:
            Overall confidence score (0.0-1.0)
        """
        if not matches:
            return 0.0

        # Weight by confidence and number of matches
        total_confidence = sum(m.confidence for m in matches)
        match_count_factor = min(len(matches) / 3.0, 1.0)  # Cap at 3 matches

        return min((total_confidence / len(matches)) * (0.7 + 0.3 * match_count_factor), 1.0)

    def validate_result(
        self, value: Optional[str], validation_method: str = "pattern"
    ) -> ValidationResult:
        """Validate an extracted value.

        Args:
            value: Value to validate
            validation_method: Method used for validation

        Returns:
            ValidationResult with validation status and confidence
        """
        if not value:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_method=validation_method,
                details="Empty or None value",
            )

        return ValidationResult(
            is_valid=True,
            confidence=ExtractionConfidence.MEDIUM.value,
            validation_method=validation_method,
            details="Basic validation passed",
        )
