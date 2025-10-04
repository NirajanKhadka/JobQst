#!/usr/bin/env python3
"""
Pipeline Migration Utility for JobQst
Provides backwards-compatible interfaces for transitioning from old processing
systems to UnifiedJobProcessingPipeline
"""

import logging
from typing import Any, Dict, List
from dataclasses import dataclass

from .unified_job_processing_pipeline import (
    UnifiedJobProcessingPipeline,
    ProcessingConfig,
    ProcessingStrategy,
    ProcessingResult,
    create_processing_pipeline,
)

logger = logging.getLogger(__name__)


@dataclass
class LegacyProcessingResult:
    """Backwards-compatible result format for old pipeline interfaces"""

    success: bool
    processed_jobs: List[Dict[str, Any]]
    failed_jobs: List[Dict[str, Any]]
    processing_time_seconds: float
    errors: List[str]

    @classmethod
    def from_unified_result(cls, result: ProcessingResult) -> "LegacyProcessingResult":
        """Convert UnifiedProcessingPipeline result to legacy format"""
        processed_jobs = result.metadata.get("processed_jobs", [])
        failed_count = result.failed_count

        # Create placeholder failed jobs if we don't have the actual data
        failed_jobs = [{"error": error} for error in result.errors[:failed_count]]

        return cls(
            success=result.success,
            processed_jobs=processed_jobs,
            failed_jobs=failed_jobs,
            processing_time_seconds=result.processing_time_seconds,
            errors=result.errors,
        )


class TwoStageJobProcessorCompat:
    """
    Backwards-compatible interface for TwoStageJobProcessor
    Internally uses UnifiedJobProcessingPipeline with TWO_STAGE strategy
    """

    def __init__(self, user_profile, ai_service=None, cache_service=None, **kwargs):
        """Initialize with legacy interface"""
        self.user_profile = user_profile

        # Create unified pipeline with two-stage strategy
        self._pipeline = create_processing_pipeline(
            strategy=ProcessingStrategy.TWO_STAGE,
            batch_size=kwargs.get("batch_size", 50),
            max_workers=kwargs.get("max_workers", 4),
            ai_service=ai_service,
            cache_service=cache_service,
        )

        logger.info("TwoStageJobProcessor compatibility layer initialized")

    def process_jobs(self, jobs_data: List[Dict[str, Any]]) -> LegacyProcessingResult:
        """Process jobs using unified pipeline with legacy result format"""
        try:
            result = self._pipeline.process_jobs(jobs_data)
            return LegacyProcessingResult.from_unified_result(result)
        except Exception as error:
            logger.error(f"Processing failed in compatibility layer: {error}")
            return LegacyProcessingResult(
                success=False,
                processed_jobs=[],
                failed_jobs=[{"error": str(error)} for _ in jobs_data],
                processing_time_seconds=0.0,
                errors=[str(error)],
            )


class OptimizedTwoStageProcessorCompat:
    """
    Backwards-compatible interface for OptimizedTwoStageProcessor
    Internally uses UnifiedJobProcessingPipeline with BATCH_OPTIMIZED strategy
    """

    def __init__(
        self,
        user_profile,
        cpu_workers=4,
        max_concurrent_stage2=2,
        ai_service=None,
        cache_service=None,
        **kwargs,
    ):
        """Initialize with legacy interface"""
        self.user_profile = user_profile
        self.cpu_workers = cpu_workers
        self.max_concurrent_stage2 = max_concurrent_stage2

        # Create unified pipeline with batch-optimized strategy
        self._pipeline = create_processing_pipeline(
            strategy=ProcessingStrategy.BATCH_OPTIMIZED,
            batch_size=kwargs.get("batch_size", 100),  # Larger batches for optimization
            max_workers=max(cpu_workers, max_concurrent_stage2),
            ai_service=ai_service,
            cache_service=cache_service,
        )

        logger.info(
            f"OptimizedTwoStageProcessor compatibility layer initialized: "
            f"workers={cpu_workers}, concurrent_stage2={max_concurrent_stage2}"
        )

    def process_jobs(self, jobs_data: List[Dict[str, Any]]) -> LegacyProcessingResult:
        """Process jobs using unified pipeline with legacy result format"""
        try:
            result = self._pipeline.process_jobs(jobs_data)
            return LegacyProcessingResult.from_unified_result(result)
        except Exception as error:
            logger.error(f"Optimized processing failed in compatibility layer: {error}")
            return LegacyProcessingResult(
                success=False,
                processed_jobs=[],
                failed_jobs=[{"error": str(error)} for _ in jobs_data],
                processing_time_seconds=0.0,
                errors=[str(error)],
            )


class BatchProcessorCompat:
    """
    Backwards-compatible interface for BatchProcessor
    Internally uses UnifiedJobProcessingPipeline with BATCH_OPTIMIZED strategy
    """

    def __init__(self, user_profile, batch_size=50, **kwargs):
        """Initialize with legacy interface"""
        self.user_profile = user_profile
        self.batch_size = batch_size

        # Create unified pipeline with batch-optimized strategy
        self._pipeline = create_processing_pipeline(
            strategy=ProcessingStrategy.BATCH_OPTIMIZED,
            batch_size=batch_size,
            max_workers=kwargs.get("max_workers", 4),
        )

        logger.info(f"BatchProcessor compatibility layer initialized: batch_size={batch_size}")

    def process_batch(self, jobs_data: List[Dict[str, Any]]) -> LegacyProcessingResult:
        """Process batch using unified pipeline with legacy result format"""
        try:
            result = self._pipeline.process_jobs(jobs_data)
            return LegacyProcessingResult.from_unified_result(result)
        except Exception as error:
            logger.error(f"Batch processing failed in compatibility layer: {error}")
            return LegacyProcessingResult(
                success=False,
                processed_jobs=[],
                failed_jobs=[{"error": str(error)} for _ in jobs_data],
                processing_time_seconds=0.0,
                errors=[str(error)],
            )


# Factory functions for backwards compatibility
def create_optimized_processor(
    user_profile,
    cpu_workers: int = 4,
    max_concurrent_stage2: int = 2,
    ai_service=None,
    cache_service=None,
    **kwargs,
) -> OptimizedTwoStageProcessorCompat:
    """
    Factory function for creating optimized processor (backwards compatible)

    Args:
        user_profile: User profile for processing
        cpu_workers: Number of CPU workers
        max_concurrent_stage2: Maximum concurrent stage 2 operations
        ai_service: Optional AI service
        cache_service: Optional cache service
        **kwargs: Additional arguments

    Returns:
        OptimizedTwoStageProcessorCompat instance
    """
    return OptimizedTwoStageProcessorCompat(
        user_profile=user_profile,
        cpu_workers=cpu_workers,
        max_concurrent_stage2=max_concurrent_stage2,
        ai_service=ai_service,
        cache_service=cache_service,
        **kwargs,
    )


def create_two_stage_processor(
    user_profile, ai_service=None, cache_service=None, **kwargs
) -> TwoStageJobProcessorCompat:
    """
    Factory function for creating two-stage processor (backwards compatible)

    Args:
        user_profile: User profile for processing
        ai_service: Optional AI service
        cache_service: Optional cache service
        **kwargs: Additional arguments

    Returns:
        TwoStageJobProcessorCompat instance
    """
    return TwoStageJobProcessorCompat(
        user_profile=user_profile, ai_service=ai_service, cache_service=cache_service, **kwargs
    )


def create_batch_processor(user_profile, batch_size: int = 50, **kwargs) -> BatchProcessorCompat:
    """
    Factory function for creating batch processor (backwards compatible)

    Args:
        user_profile: User profile for processing
        batch_size: Size of processing batches
        **kwargs: Additional arguments

    Returns:
        BatchProcessorCompat instance
    """
    return BatchProcessorCompat(user_profile=user_profile, batch_size=batch_size, **kwargs)


# Migration utility function
def migrate_to_unified_pipeline(
    old_processor_type: str, user_profile, **kwargs
) -> UnifiedJobProcessingPipeline:
    """
    Migrate from old processor types to unified pipeline

    Args:
        old_processor_type: Type of old processor
            ('two_stage', 'optimized', 'batch', 'streaming')
        user_profile: User profile for processing
        **kwargs: Additional configuration arguments

    Returns:
        UnifiedJobProcessingPipeline configured for equivalent behavior
    """
    strategy_mapping = {
        "two_stage": ProcessingStrategy.TWO_STAGE,
        "optimized": ProcessingStrategy.BATCH_OPTIMIZED,
        "batch": ProcessingStrategy.BATCH_OPTIMIZED,
        "streaming": ProcessingStrategy.STREAMING,
    }

    strategy = strategy_mapping.get(old_processor_type, ProcessingStrategy.TWO_STAGE)

    # Extract relevant configuration
    batch_size = kwargs.get("batch_size", 50)
    max_workers = max(
        kwargs.get("cpu_workers", 4),
        kwargs.get("max_workers", 4),
        kwargs.get("max_concurrent_stage2", 2),
    )

    return create_processing_pipeline(
        strategy=strategy,
        batch_size=batch_size,
        max_workers=max_workers,
        ai_service=kwargs.get("ai_service"),
        cache_service=kwargs.get("cache_service"),
    )
