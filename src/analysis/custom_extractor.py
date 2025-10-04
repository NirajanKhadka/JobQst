"""
Custom job data extractor - backward compatibility wrapper.

This module maintains backward compatibility with existing code while delegating
to the new modular extractor architecture in extractors/ package.

DEPRECATED: This file is maintained for backward compatibility only.
New code should import directly from src.analysis.extractors package.
"""

import logging
from typing import Any, Dict, Set

# Import from new modular architecture
from .extractors import CustomExtractor, get_Improved_custom_extractor
from .extractors.base import (
    ExtractionConfidence,
    ExtractionResult,
    PatternMatch,
    ValidationResult,
)
from .extractors.company import CompanyExtractor

logger = logging.getLogger(__name__)

# Type alias for backward compatibility
ImprovedExtractionResult = ExtractionResult


class IndustryStandardsDatabase:
    """Legacy compatibility class - wraps data from specialized extractors."""

    def __init__(self):
        """Initialize with data from specialized extractors."""
        from .extractors.title import TitleExtractor
        from .extractors.company import CompanyExtractor
        from .extractors.location import LocationExtractor
        from .extractors.skills import SkillsExtractor

        title_ext = TitleExtractor()
        company_ext = CompanyExtractor()
        location_ext = LocationExtractor()
        skills_ext = SkillsExtractor()

        self.job_titles = title_ext.standard_titles
        self.companies = company_ext.known_companies
        self.locations = location_ext.standard_locations
        self.skills = skills_ext.standard_skills


class WebValidator:
    """Legacy compatibility class - wraps CompanyExtractor validation."""

    def __init__(self, search_client=None):
        """Initialize with company extractor."""
        self.company_extractor = CompanyExtractor()
        self.search_available = self.company_extractor.validation_available

    def validate_company(self, company: str) -> ValidationResult:
        """Validate company using domain validation."""
        return self.company_extractor.validate_company(company)


logger.info(
    "Loading custom_extractor.py - backward compatibility wrapper. "
    "Consider importing from src.analysis.extractors directly."
)

# Export all classes for backward compatibility
__all__ = [
    "CustomExtractor",
    "get_Improved_custom_extractor",
    "ExtractionResult",
    "ImprovedExtractionResult",  # Alias
    "ExtractionConfidence",
    "PatternMatch",
    "ValidationResult",
    "IndustryStandardsDatabase",  # Legacy compatibility
    "WebValidator",  # Legacy compatibility
]
