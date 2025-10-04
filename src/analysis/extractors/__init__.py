"""
Job data extractors package.

Provides modular, specialized extractors for different job data fields.
Main entry point is CustomExtractor which coordinates all extractors.
"""

from .base import (
    BaseExtractor,
    ExtractionConfidence,
    ExtractionResult,
    PatternMatch,
    ValidationResult,
)
from .company import CompanyExtractor
from .compensation import CompensationExtractor
from .coordinator import CustomExtractor, get_Improved_custom_extractor
from .location import LocationExtractor
from .skills import SkillsExtractor
from .title import TitleExtractor

__all__ = [
    # Main extractor (primary interface)
    "CustomExtractor",
    "get_Improved_custom_extractor",
    # Base classes
    "BaseExtractor",
    "ExtractionResult",
    "ExtractionConfidence",
    "PatternMatch",
    "ValidationResult",
    # Specialized extractors',
    "TitleExtractor",
    "CompanyExtractor",
    "LocationExtractor",
    "CompensationExtractor",
    "SkillsExtractor",
]
