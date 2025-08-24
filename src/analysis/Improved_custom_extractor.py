"""
Compatibility shim for Improved custom extractor.
Re-exports classes from enhanced_custom_extractor to support older imports.
"""

from .enhanced_custom_extractor import (
    ImprovedCustomExtractor,
    ImprovedExtractionResult,
    ExtractionConfidence,
    IndustryStandardsDatabase,
)

__all__ = [
    "ImprovedCustomExtractor",
    "ImprovedExtractionResult",
    "ExtractionConfidence",
    "IndustryStandardsDatabase",
]
