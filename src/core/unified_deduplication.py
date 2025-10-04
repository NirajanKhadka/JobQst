#!/usr/bin/env python3
"""
Unified Deduplication Interface - Phase 2 Consolidation

This module provides a single, standardized interface for job deduplication
across all JobLens components. It wraps the SmartJobDeduplicator with
additional convenience methods for different use cases.
"""

from typing import List, Dict, Any, Tuple
from src.core.smart_deduplication import SmartJobDeduplicator, smart_deduplicate_jobs
from rich.console import Console

console = Console()


class UnifiedJobDeduplicator:
    """
    Unified interface for job deduplication across all JobLens components.

    This class provides a consistent API for deduplication while internally
    using the SmartJobDeduplicator for all actual processing.
    """

    def __init__(self, similarity_threshold: float = 0.85):
        self.deduplicator = SmartJobDeduplicator(similarity_threshold)
        self.similarity_threshold = similarity_threshold

    def deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate jobs and return only unique jobs.

        This is the main interface used by pipeline components.
        """
        if not jobs:
            return jobs

        unique_jobs, stats = self.deduplicator.deduplicate_job_list(jobs)

        # Log performance improvement
        if stats["duplicates"] > 0:
            reduction_pct = (stats["duplicates"] / stats["total"]) * 100
            console.print(
                f"[green]🚀 Performance boost: {stats['duplicates']} duplicates removed ({reduction_pct:.1f}% reduction)[/green]"
            )

        return unique_jobs

    def deduplicate_with_stats(
        self, jobs: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Deduplicate jobs and return both unique jobs and detailed statistics.

        Used when detailed deduplication metrics are needed.
        """
        return self.deduplicator.deduplicate_job_list(jobs)

    def is_duplicate(self, job: Dict[str, Any], existing_jobs: List[Dict[str, Any]]) -> bool:
        """
        Check if a single job is a duplicate of existing jobs.

        Used for real-time duplicate checking during scraping.
        """
        is_dup, _ = self.deduplicator.is_duplicate_job(job, existing_jobs)
        return is_dup

    def add_job_to_tracking(self, job: Dict[str, Any]) -> None:
        """
        Add a job to the deduplication tracking system.

        Used to prevent future duplicates of this job.
        """
        self.deduplicator.add_job_to_tracking(job)

    def get_stats(self) -> Dict[str, int]:
        """Get current deduplication statistics."""
        return self.deduplicator.get_deduplication_stats()

    def reset_tracking(self) -> None:
        """Reset the deduplication tracking (start fresh)."""
        self.deduplicator.processed_hashes.clear()
        self.deduplicator.processed_urls.clear()
        self.deduplicator.title_company_pairs.clear()


# Global deduplicator instance for performance (reuse tracking across calls)
_global_deduplicator = None


def get_unified_deduplicator(similarity_threshold: float = 0.85) -> UnifiedJobDeduplicator:
    """
    Get the global unified deduplicator instance.

    This provides a singleton pattern for better performance by reusing
    the deduplication tracking across multiple calls.
    """
    global _global_deduplicator

    if (
        _global_deduplicator is None
        or _global_deduplicator.similarity_threshold != similarity_threshold
    ):
        _global_deduplicator = UnifiedJobDeduplicator(similarity_threshold)

    return _global_deduplicator


def deduplicate_jobs_unified(
    jobs: List[Dict[str, Any]], similarity_threshold: float = 0.85
) -> List[Dict[str, Any]]:
    """
    Convenience function for unified job deduplication.

    This is the main function that should be used throughout JobLens
    for job deduplication. It replaces all previous deduplication methods.

    Args:
        jobs: List of job dictionaries to deduplicate
        similarity_threshold: Similarity threshold for duplicate detection (0.0-1.0)

    Returns:
        List of unique jobs with duplicates removed
    """
    deduplicator = get_unified_deduplicator(similarity_threshold)
    return deduplicator.deduplicate_jobs(jobs)


def deduplicate_jobs_with_stats(
    jobs: List[Dict[str, Any]], similarity_threshold: float = 0.85
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience function for unified job deduplication with statistics.

    Args:
        jobs: List of job dictionaries to deduplicate
        similarity_threshold: Similarity threshold for duplicate detection (0.0-1.0)

    Returns:
        Tuple of (unique_jobs, deduplication_stats)
    """
    deduplicator = get_unified_deduplicator(similarity_threshold)
    return deduplicator.deduplicate_with_stats(jobs)


# Backward compatibility aliases
smart_deduplicate_jobs = deduplicate_jobs_unified  # For existing code
