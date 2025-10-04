#!/usr/bin/env python3
"""
Job Analysis Metadata Handler
Manages analysis method metadata throughout the job processing pipeline
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AnalysisMetadata:
    """Analysis metadata structure"""

    method: str  # 'mistral_7b', 'llama3', 'Improved_rule_based', 'fallback'
    timestamp: str
    duration_ms: Optional[float] = None
    confidence: Optional[float] = None
    analyzer_version: Optional[str] = None
    service_health: Optional[Dict[str, Any]] = None
    error_info: Optional[str] = None


class JobAnalysisMetadataHandler:
    """Handles analysis method metadata throughout the job processing pipeline"""

    def __init__(self):
        """Initialize metadata handler"""
        self.analysis_method_stats = {
            "mistral_7b": 0,
            "llama3": 0,
            "Improved_rule_based": 0,
            "fallback": 0,
            "unknown": 0,
        }

        self.performance_stats = {
            "total_analyses": 0,
            "average_duration_by_method": {},
            "success_rate_by_method": {},
            "last_updated": None,
        }

    def extract_metadata_from_analysis(self, analysis_result: Dict[str, Any]) -> AnalysisMetadata:
        """
        Extract metadata from analysis result.

        Args:
            analysis_result: Job analysis result dictionary

        Returns:
            AnalysisMetadata object
        """
        method = analysis_result.get("analysis_method", "unknown")
        timestamp = analysis_result.get("analysis_timestamp")

        # Convert timestamp if it's a float
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp).isoformat()
        elif timestamp is None:
            timestamp = datetime.now().isoformat()

        return AnalysisMetadata(
            method=method,
            timestamp=timestamp,
            duration_ms=analysis_result.get("duration_ms"),
            confidence=analysis_result.get("confidence"),
            analyzer_version=analysis_result.get("analyzer_version"),
            service_health=analysis_result.get("analyzer_stats"),
            error_info=analysis_result.get("error"),
        )

    def update_job_with_metadata(
        self, job_data: Dict[str, Any], analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update job data with analysis metadata.

        Args:
            job_data: Original job data
            analysis_result: Analysis result

        Returns:
            Updated job data with metadata
        """
        metadata = self.extract_metadata_from_analysis(analysis_result)

        # Update statistics
        self._update_statistics(metadata)

        # Add metadata to job data
        updated_job = job_data.copy()
        updated_job.update(
            {
                "analysis_method": metadata.method,
                "analysis_timestamp": metadata.timestamp,
                "analysis_confidence": metadata.confidence,
                "analyzer_version": metadata.analyzer_version,
                "analysis_duration_ms": metadata.duration_ms,
                "analysis_metadata": {
                    "method": metadata.method,
                    "timestamp": metadata.timestamp,
                    "confidence": metadata.confidence,
                    "version": metadata.analyzer_version,
                    "duration_ms": metadata.duration_ms,
                    "service_health": metadata.service_health,
                    "error_info": metadata.error_info,
                },
            }
        )

        # Preserve original analysis result
        updated_job["llm_analysis"] = analysis_result

        return updated_job

    def _update_statistics(self, metadata: AnalysisMetadata):
        """Update internal statistics with new metadata."""
        # Update method counts
        if metadata.method in self.analysis_method_stats:
            self.analysis_method_stats[metadata.method] += 1
        else:
            self.analysis_method_stats["unknown"] += 1

        self.performance_stats["total_analyses"] += 1
        self.performance_stats["last_updated"] = datetime.now().isoformat()

        # Update duration statistics
        if metadata.duration_ms:
            method = metadata.method
            if method not in self.performance_stats["average_duration_by_method"]:
                self.performance_stats["average_duration_by_method"][method] = []

            durations = self.performance_stats["average_duration_by_method"][method]
            durations.append(metadata.duration_ms)

            # Keep only last 100 durations for each method
            if len(durations) > 100:
                durations.pop(0)

    def get_analysis_method_distribution(self) -> Dict[str, Any]:
        """
        Get analysis method distribution statistics.

        Returns:
            Dictionary with method distribution data
        """
        total = sum(self.analysis_method_stats.values())
        if total == 0:
            return {
                "total_analyses": 0,
                "distribution": {},
                "percentages": {},
                "primary_method": None,
            }

        percentages = {
            method: round((count / total) * 100, 1)
            for method, count in self.analysis_method_stats.items()
            if count > 0
        }

        primary_method = max(self.analysis_method_stats, key=self.analysis_method_stats.get)

        return {
            "total_analyses": total,
            "distribution": self.analysis_method_stats.copy(),
            "percentages": percentages,
            "primary_method": (
                primary_method if self.analysis_method_stats[primary_method] > 0 else None
            ),
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary by analysis method.

        Returns:
            Performance summary dictionary
        """
        summary = {
            "total_analyses": self.performance_stats["total_analyses"],
            "last_updated": self.performance_stats["last_updated"],
            "methods": {},
        }

        for method, durations in self.performance_stats["average_duration_by_method"].items():
            if durations:
                summary["methods"][method] = {
                    "count": len(durations),
                    "average_duration_ms": round(sum(durations) / len(durations), 1),
                    "min_duration_ms": round(min(durations), 1),
                    "max_duration_ms": round(max(durations), 1),
                }

        return summary

    def filter_jobs_by_analysis_method(
        self, jobs: List[Dict[str, Any]], method: str
    ) -> List[Dict[str, Any]]:
        """
        Filter jobs by analysis method.

        Args:
            jobs: List of job dictionaries
            method: Analysis method to filter by

        Returns:
            Filtered list of jobs
        """
        return [job for job in jobs if job.get("analysis_method") == method]

    def get_jobs_needing_reanalysis(
        self, jobs: List[Dict[str, Any]], prefer_method: str = "mistral_7b"
    ) -> List[Dict[str, Any]]:
        """
        Get jobs that could benefit from reanalysis with a preferred method.

        Args:
            jobs: List of job dictionaries
            prefer_method: Preferred analysis method

        Returns:
            List of jobs that could be reanalyzed
        """
        candidates = []

        for job in jobs:
            current_method = job.get("analysis_method", "unknown")

            # Skip if already analyzed with preferred method
            if current_method == prefer_method:
                continue

            # Include if analyzed with fallback methods
            if current_method in ["Improved_rule_based", "fallback", "unknown"]:
                candidates.append(job)

            # Include if analyzed with lower-priority AI method
            elif current_method == "llama3" and prefer_method == "mistral_7b":
                candidates.append(job)

        return candidates

    def generate_analysis_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report.

        Returns:
            Analysis report dictionary
        """
        distribution = self.get_analysis_method_distribution()
        performance = self.get_performance_summary()

        # Calculate health metrics
        ai_methods = ["mistral_7b", "llama3"]
        ai_analyses = sum(self.analysis_method_stats[method] for method in ai_methods)
        total_analyses = distribution["total_analyses"]

        ai_success_rate = (ai_analyses / total_analyses * 100) if total_analyses > 0 else 0

        # Determine system health
        if ai_success_rate >= 80:
            health_status = "excellent"
            health_color = "green"
        elif ai_success_rate >= 50:
            health_status = "good"
            health_color = "yellow"
        elif ai_success_rate >= 20:
            health_status = "degraded"
            health_color = "orange"
        else:
            health_status = "poor"
            health_color = "red"

        return {
            "summary": {
                "total_analyses": total_analyses,
                "ai_success_rate": round(ai_success_rate, 1),
                "health_status": health_status,
                "health_color": health_color,
                "primary_method": distribution["primary_method"],
                "last_updated": performance["last_updated"],
            },
            "distribution": distribution,
            "performance": performance,
            "recommendations": self._generate_recommendations(distribution, performance),
        }

    def _generate_recommendations(
        self, distribution: Dict[str, Any], performance: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on analysis statistics."""
        recommendations = []

        total = distribution["total_analyses"]
        if total == 0:
            return ["No analyses performed yet"]

        # Check AI service usage
        ai_methods = ["mistral_7b", "llama3"]
        ai_count = sum(distribution["distribution"][method] for method in ai_methods)
        ai_percentage = (ai_count / total) * 100

        if ai_percentage < 20:
            recommendations.append("Low AI service usage - check Ollama connectivity")
        elif ai_percentage < 50:
            recommendations.append(
                "Moderate AI service usage - consider optimizing connection reliability"
            )

        # Check fallback usage
        fallback_count = distribution["distribution"].get("Improved_rule_based", 0) + distribution[
            "distribution"
        ].get("fallback", 0)
        fallback_percentage = (fallback_count / total) * 100

        if fallback_percentage > 50:
            recommendations.append("High fallback usage - AI services may be unreliable")

        # Check performance
        for method, stats in performance["methods"].items():
            if stats["average_duration_ms"] > 30000:  # 30 seconds
                recommendations.append(
                    f"{method} is slow (avg: {stats['average_duration_ms']:.0f}ms)"
                )

        if not recommendations:
            recommendations.append("Analysis system is performing well")

        return recommendations

    def reset_statistics(self):
        """Reset all statistics."""
        self.analysis_method_stats = {
            "mistral_7b": 0,
            "llama3": 0,
            "Improved_rule_based": 0,
            "fallback": 0,
            "unknown": 0,
        }

        self.performance_stats = {
            "total_analyses": 0,
            "average_duration_by_method": {},
            "success_rate_by_method": {},
            "last_updated": None,
        }

        logger.info("Job analysis metadata statistics reset")


# Global metadata handler instance
_global_metadata_handler = None


def get_job_analysis_metadata_handler() -> JobAnalysisMetadataHandler:
    """Get or create global job analysis metadata handler."""
    global _global_metadata_handler

    if _global_metadata_handler is None:
        _global_metadata_handler = JobAnalysisMetadataHandler()

    return _global_metadata_handler


# Convenience functions
def update_job_with_analysis_metadata(
    job_data: Dict[str, Any], analysis_result: Dict[str, Any]
) -> Dict[str, Any]:
    """Update job with analysis metadata."""
    handler = get_job_analysis_metadata_handler()
    return handler.update_job_with_metadata(job_data, analysis_result)


def get_analysis_method_stats() -> Dict[str, Any]:
    """Get analysis method distribution statistics."""
    handler = get_job_analysis_metadata_handler()
    return handler.get_analysis_method_distribution()


def generate_analysis_report() -> Dict[str, Any]:
    """Generate comprehensive analysis report."""
    handler = get_job_analysis_metadata_handler()
    return handler.generate_analysis_report()


# Main functionality moved to CLI module or tests
# Import and use the functions directly
