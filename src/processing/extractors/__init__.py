"""
Processing Extractors Module

Rule-based job data extraction with pattern matching,
industry standards validation, and web validation.
"""

from .base_extractor import ExtractionResult, ExtractionConfidence, BaseExtractor
from .rule_based_extractor import (
    RuleBasedExtractor,
    RuleBasedExtractionResult,
    get_rule_based_extractor,
)
from .pattern_matcher import JobPatternMatcher, PatternMatch
from .industry_standards import IndustryStandardsDatabase
from .web_validator import WebValidator, ValidationResult

__all__ = [
    # Base classes
    "ExtractionResult",
    "ExtractionConfidence",
    "BaseExtractor",
    # Rule-based extractor
    "RuleBasedExtractor",
    "RuleBasedExtractionResult",
    "get_rule_based_extractor",
    # Pattern matching
    "JobPatternMatcher",
    "PatternMatch",
    # Industry standards and validation
    "IndustryStandardsDatabase",
    "WebValidator",
    "ValidationResult",
]
