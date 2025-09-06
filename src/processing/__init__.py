"""
JobQst Processing Module

Modular processing architecture with clean separation:
- Rule-based extraction (fast, reliable)
- AI-powered analysis (semantic understanding)
- Hybrid coordination (intelligent fallback)

Implements Phase 3 of AI Strategy Analysis.
"""

# Import core processing components
from .extractors import (
    RuleBasedExtractor,
    RuleBasedExtractionResult,
    get_rule_based_extractor,
    IndustryStandardsDatabase,
    WebValidator
)

from .hybrid import (
    JobProcessingCoordinator,
    ProcessingResult,
    ProcessingStrategy,
    create_coordinator,
    process_single_job
)

# AI processing (when available)
try:
    from .ai import *
except ImportError:
    # AI modules not yet implemented
    pass

__all__ = [
    # Rule-based extraction
    'RuleBasedExtractor',
    'RuleBasedExtractionResult', 
    'get_rule_based_extractor',
    'IndustryStandardsDatabase',
    'WebValidator',
    
    # Hybrid coordination
    'JobProcessingCoordinator',
    'ProcessingResult',
    'ProcessingStrategy',
    'create_coordinator',
    'process_single_job',
]

