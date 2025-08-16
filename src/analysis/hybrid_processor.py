#!/usr/bin/env python3
"""
Deprecated: Hybrid Processing Engine
This processor has been replaced by TwoStageProcessor.
Use TwoStageProcessor instead for better performance.
"""
import warnings
from typing import Optional, Dict, Any

# Import the current recommended processor
from .two_stage_processor import (
    TwoStageJobProcessor, 
    get_two_stage_processor, 
    TwoStageResult
)

# Compatibility imports for existing tests
from .custom_data_extractor import ExtractionResult  # noqa: F401

try:
    from ..ai.gpu_ollama_client import JobAnalysisResult  # noqa: F401
except ImportError:
    JobAnalysisResult = None


class HybridProcessingEngine:
    """Deprecated: Use TwoStageJobProcessor instead."""
    
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "HybridProcessingEngine is deprecated. "
            "Use TwoStageJobProcessor instead.",
            DeprecationWarning,
            stacklevel=2
        )
        user_profile = kwargs.get('user_profile', {})
        self._processor = get_two_stage_processor(user_profile)
    
    def process_job(self, job_data: Dict[str, Any]) -> 'HybridProcessingResult':
        """Process job using TwoStageProcessor (compatibility method)."""
        import asyncio
        
        async def _process():
            results = await self._processor.process_jobs([job_data])
            return results[0] if results else None
        
        # Run in event loop
        try:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(_process())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(_process())
        
        return self._convert_result(result)
    
    def _convert_result(self, two_stage_result) -> 'HybridProcessingResult':
        """Convert TwoStageResult to HybridProcessingResult."""
        return HybridProcessingResult(
            title=two_stage_result.stage1.title if two_stage_result.stage1 else "Unknown",
            company=two_stage_result.stage1.company if two_stage_result.stage1 else "Unknown",
            required_skills=two_stage_result.final_skills,
            job_requirements=two_stage_result.final_requirements,
            compatibility_score=two_stage_result.final_compatibility,
            processing_method="two_stage_compatibility",
            total_processing_time=two_stage_result.total_processing_time
        )


class HybridProcessingResult:
    """Compatibility result class."""
    
    def __init__(self, **kwargs):
        self.title = kwargs.get('title', '')
        self.company = kwargs.get('company', '')
        self.location = kwargs.get('location', '')
        self.salary_range = kwargs.get('salary_range')
        self.required_skills = kwargs.get('required_skills', [])
        self.job_requirements = kwargs.get('job_requirements', [])
        self.compatibility_score = kwargs.get('compatibility_score', 0.0)
        self.processing_method = kwargs.get('processing_method', 'hybrid_compat')
        self.total_processing_time = kwargs.get('total_processing_time', 0.0)
        self.analysis_confidence = kwargs.get('analysis_confidence', 0.0)
        self.extracted_benefits = kwargs.get('extracted_benefits', [])
        self.reasoning = kwargs.get('reasoning', 
                                   'Processed via TwoStageProcessor compatibility layer')
        self.custom_logic_confidence = kwargs.get('custom_logic_confidence', 0.0)
        self.llm_processing_time = kwargs.get('llm_processing_time', 0.0)
        self.fallback_used = kwargs.get('fallback_used', False)


def get_hybrid_processing_engine(user_profile: Optional[Dict] = None):
    """Deprecated: Use get_two_stage_processor instead."""
    warnings.warn(
        "get_hybrid_processing_engine is deprecated. "
        "Use get_two_stage_processor instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return HybridProcessingEngine(user_profile=user_profile)


__all__ = [
    "HybridProcessingEngine",
    "HybridProcessingResult", 
    "get_hybrid_processing_engine",
]
