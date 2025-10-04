"""
Base Extractor Classes and Interfaces

Defines the common interface for all extraction methods following
DEVELOPMENT_STANDARDS.md guidelines for clean architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time


class ExtractionConfidence(Enum):
    """Confidence levels for extraction results"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class ExtractionResult:
    """Standardized result from any extraction method"""

    # Basic job information
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    employment_type: Optional[str] = None

    # Enhanced fields
    skills: list[str] = None
    requirements: list[str] = None
    experience_level: Optional[str] = None
    remote_work: Optional[str] = None

    # Quality metrics
    confidence: ExtractionConfidence = ExtractionConfidence.UNKNOWN
    confidence_score: float = 0.0
    processing_time: float = 0.0
    extraction_method: str = "unknown"

    # Validation flags
    is_valid: bool = True
    validation_errors: list[str] = None

    def __post_init__(self):
        """Initialize default values"""
        if self.skills is None:
            self.skills = []
        if self.requirements is None:
            self.requirements = []
        if self.validation_errors is None:
            self.validation_errors = []


class BaseExtractor(ABC):
    """
    Abstract base class for all extraction methods.

    Implements common functionality and defines the interface
    that all extractors must follow.
    """

    def __init__(self, name: str):
        self.name = name
        self.extraction_count = 0

    @abstractmethod
    def extract(self, job_data: Dict[str, Any]) -> ExtractionResult:
        """
        Extract structured data from job information.

        Args:
            job_data: Raw job data dictionary

        Returns:
            ExtractionResult with extracted information
        """
        pass

    def validate_input(self, job_data: Dict[str, Any]) -> bool:
        """Validate input data before processing"""
        if not isinstance(job_data, dict):
            return False
        if not job_data.get("title") and not job_data.get("description"):
            return False
        return True

    def extract_with_validation(self, job_data: Dict[str, Any]) -> ExtractionResult:
        """Extract with input validation and error handling"""
        start_time = time.time()

        try:
            # Validate input
            if not self.validate_input(job_data):
                return ExtractionResult(
                    is_valid=False,
                    validation_errors=["Invalid input data"],
                    extraction_method=self.name,
                    processing_time=time.time() - start_time,
                )

            # Perform extraction
            result = self.extract(job_data)
            result.extraction_method = self.name
            result.processing_time = time.time() - start_time

            # Update counters
            self.extraction_count += 1

            return result

        except Exception as e:
            return ExtractionResult(
                is_valid=False,
                validation_errors=[f"Extraction failed: {str(e)}"],
                extraction_method=self.name,
                processing_time=time.time() - start_time,
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get extractor statistics"""
        return {
            "name": self.name,
            "extraction_count": self.extraction_count,
            "type": self.__class__.__name__,
        }
