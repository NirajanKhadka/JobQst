"""
Error visualization components for the AutoJobAgent Dashboard.

This module provides components for visualizing errors, failed jobs,
dead-letter queue analysis, and error trend tracking.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

from src.pipeline.redis_queue import RedisQueue
from src.core.job_database import get_job_db
from src.dashboard.websocket import manager as websocket_manager

logger = logging.getLogger(__name__)


@dataclass
class ErrorSummary:
    """Data class for error summary information."""
    timestamp: str
    total_errors: int
    error_rate_percent: float
    critical_errors: int
    recent_errors: int
    top_error_types: List[Dict[str, Any]]
    error_trend: str


@dataclass
class JobError:
    """Data class for individual job error information."""
    job_id: str
    title: str
    company: str
    error_type: str
    error_message: str
    failed_at: str
    retry_count: int
    correlation_id: Optional[str]
    stage: Optional[str]
    raw_data: Optional[str]


class ErrorVisualizationManager:
    """
    Manager for error visualization and analysis.
    
    Features:
    - Dead-letter queue analysis
    - Error categorization and trending
    - Failed job visualization
    - Error pattern detection
    - Real-time error monitoring
    - Error recovery suggestions
    """
    
    def __init__(self):
        self.error_history = []
        self.error_patterns = defaultdict(int)
        self.last_analysis_time = None
        
        logger.info("Error visualization manager initialized")
    
    async def get_error_summary(self) -> ErrorSummary:
        """
        Get comprehensive error summary.
        
        Returns:
            ErrorSummary containing current error statistics
        """
        try:
            # Get dead-letter queue errors
            deadletter_errors = await self._get_deadletter_errors()
            
            # Get database error statistics
            db_error_stats = await self._get_database_error_stats()
            
            # Calculate error metrics
            total_errors = len(deadletter_errors) + db_error_stats.get("failed_jobs", 0)
            total_jobs = db_error_stats.get("total_jobs", 1)
            error_rate = (total_errors / total_jobs * 100) if total_jobs > 0 else 0
            
            # Categorize errors
            error_categories = self._categorize_errors(deadletter_errors)
            top_error_types = [
                {"type": error_type, "count": count, "percentage": round(count / total_errors * 100, 1)}
                for error_type, count in error_categories.most_common(5)
            ] if total_errors > 0 else []
            
            # Count critical errors (high retry count or specific error types)
            critical_errors = len([
                error for error in deadletter_errors 
                if error.retry_count > 2 or self._is_critical_error(error.error_type)
            ])
            
            # Count recent errors (last hour)
            recent_cutoff = datetime.now() - timedelta(hours=1)
            recent_errors = len([
                error for error in deadletter_errors
                if self._parse_timestamp(error.failed_at) > recent_cutoff
            ])
            
            # Determine error trend
            error_trend = await self._calculate_error_trend()
            
            return ErrorSummary(
                timestamp=datetime.now().isoformat(),
                total_errors=total_errors,
                error_rate_percent=round(error_rate, 2),
                critical_errors=critical_errors,
                recent_errors=recent_errors,
                top_error_types=top_error_types,
                error_trend=error_trend
            )
            
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return ErrorSummary(
                timestamp=datetime.now().isoformat(),
                total_errors=0,
                error_rate_percent=0.0,
                critical_errors=0,
                recent_errors=0,
                top_error_types=[],
                error_trend="unknown"
            )
    
    async def get_failed_jobs_analysis(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get detailed analysis of failed jobs.
        
        Args:
            limit: Maximum number of failed jobs to analyze
            
        Returns:
            Dictionary containing failed jobs analysis
        """
        try:
            # Get failed jobs from dead-letter queue
            deadletter_errors = await self._get_deadletter_errors(limit)
            
            # Analyze error patterns
            error_analysis = {
                "timestamp": datetime.now().isoformat(),
                "total_failed_jobs": len(deadletter_errors),
                "error_breakdown": {},
                "stage_failures": defaultdict(int),
                "company_failures": defaultdict(int),
                "time_distribution": defaultdict(int),
                "retry_analysis": defaultdict(int),
                "correlation_tracking": {},
                "recovery_suggestions": []
            }
            
            # Analyze each failed job
            for error in deadletter_errors:
                # Error type breakdown
                error_type = error.error_type or "unknown"
                if error_type not in error_analysis["error_breakdown"]:
                    error_analysis["error_breakdown"][error_type] = {
                        "count": 0,
                        "examples": [],
                        "avg_retry_count": 0,
                        "stages": set()
                    }
                
                error_analysis["error_breakdown"][error_type]["count"] += 1
                error_analysis["error_breakdown"][error_type]["avg_retry_count"] += error.retry_count
                
                if len(error_analysis["error_breakdown"][error_type]["examples"]) < 3:
                    error_analysis["error_breakdown"][error_type]["examples"].append({
                        "job_id": error.job_id,
                        "title": error.title,
                        "company": error.company,
                        "failed_at": error.failed_at
                    })
                
                if error.stage:
                    error_analysis["error_breakdown"][error_type]["stages"].add(error.stage)
                
                # Stage failure analysis
                if error.stage:
                    error_analysis["stage_failures"][error.stage] += 1
                
                # Company failure analysis
                if error.company:
                    error_analysis["company_failures"][error.company] += 1
                
                # Time distribution (by hour)
                try:
                    failed_time = self._parse_timestamp(error.failed_at)
                    hour_key = failed_time.strftime("%Y-%m-%d %H:00")
                    error_analysis["time_distribution"][hour_key] += 1
                except:
                    pass
                
                # Retry analysis
                retry_bucket = f"{error.retry_count}_retries"
                error_analysis["retry_analysis"][retry_bucket] += 1
                
                # Correlation tracking
                if error.correlation_id:
                    if error.correlation_id not in error_analysis["correlation_tracking"]:
                        error_analysis["correlation_tracking"][error.correlation_id] = []
                    error_analysis["correlation_tracking"][error.correlation_id].append({
                        "job_id": error.job_id,
                        "stage": error.stage,
                        "error_type": error.error_type,
                        "failed_at": error.failed_at
                    })
            
            # Calculate averages and convert sets to lists
            for error_type, data in error_analysis["error_breakdown"].items():
                if data["count"] > 0:
                    data["avg_retry_count"] = round(data["avg_retry_count"] / data["count"], 1)
                data["stages"] = list(data["stages"])
            
            # Convert defaultdicts to regular dicts
            error_analysis["stage_failures"] = dict(error_analysis["stage_failures"])
            error_analysis["company_failures"] = dict(error_analysis["company_failures"])
            error_analysis["time_distribution"] = dict(error_analysis["time_distribution"])
            error_analysis["retry_analysis"] = dict(error_analysis["retry_analysis"])
            
            # Generate recovery suggestions
            error_analysis["recovery_suggestions"] = self._generate_recovery_suggestions(error_analysis)
            
            return error_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing failed jobs: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "total_failed_jobs": 0
            }
    
    async def get_error_timeline(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get error timeline for visualization.
        
        Args:
            hours: Number of hours to include in timeline
            
        Returns:
            Dictionary containing error timeline data
        """
        try:
            # Get failed jobs from dead-letter queue
            deadletter_errors = await self._get_deadletter_errors(500)  # Get more for timeline
            
            # Filter by time range
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_errors = [
                error for error in deadletter_errors
                if self._parse_timestamp(error.failed_at) > cutoff_time
            ]
            
            # Create timeline buckets (hourly)
            timeline_data = []
            current_time = cutoff_time
            
            while current_time <= datetime.now():
                bucket_start = current_time
                bucket_end = current_time + timedelta(hours=1)
                
                # Count errors in this bucket
                bucket_errors = [
                    error for error in recent_errors
                    if bucket_start <= self._parse_timestamp(error.failed_at) < bucket_end
                ]
                
                # Categorize errors in bucket
                error_types = Counter([error.error_type for error in bucket_errors])
                stages = Counter([error.stage for error in bucket_errors if error.stage])
                
                timeline_data.append({
                    "timestamp": bucket_start.isoformat(),
                    "hour": bucket_start.strftime("%H:00"),
                    "total_errors": len(bucket_errors),
                    "error_types": dict(error_types),
                    "stages": dict(stages),
                    "critical_errors": len([e for e in bucket_errors if self._is_critical_error(e.error_type)])
                })
                
                current_time = bucket_end
            
            return {
                "timestamp": datetime.now().isoformat(),
                "time_range_hours": hours,
                "timeline": timeline_data,
                "total_errors_in_range": len(recent_errors),
                "summary": {
                    "peak_hour": max(timeline_data, key=lambda x: x["total_errors"])["hour"] if timeline_data else None,
                    "avg_errors_per_hour": round(len(recent_errors) / hours, 1) if hours > 0 else 0,
                    "error_trend": self._calculate_timeline_trend(timeline_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting error timeline: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "timeline": []
            }
    
    async def get_error_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed error information for a specific job.
        
        Args:
            job_id: Job ID to get error details for
            
        Returns:
            Dictionary containing detailed error information
        """
        try:
            # Search in dead-letter queue
            deadletter_errors = await self._get_deadletter_errors(1000)
            
            job_error = None
            for error in deadletter_errors:
                if error.job_id == job_id:
                    job_error = error
                    break
            
            if not job_error:
                return None
            
            # Get additional context from database if available
            db = get_job_db()
            db_job = None
            try:
                # Try to find job in database
                jobs = db.search_jobs(job_error.title)
                for job in jobs:
                    if job.get("job_id") == job_id:
                        db_job = job
                        break
            except:
                pass
            
            # Parse raw data for additional insights
            raw_data_insights = {}
            if job_error.raw_data:
                try:
                    raw_data = json.loads(job_error.raw_data)
                    raw_data_insights = {
                        "has_url": bool(raw_data.get("url")),
                        "has_description": bool(raw_data.get("job_description")),
                        "data_size": len(str(raw_data)),
                        "fields_present": list(raw_data.keys()) if isinstance(raw_data, dict) else []
                    }
                except:
                    raw_data_insights = {"parse_error": True}
            
            return {
                "timestamp": datetime.now().isoformat(),
                "job_error": asdict(job_error),
                "database_job": db_job,
                "raw_data_insights": raw_data_insights,
                "error_classification": {
                    "is_critical": self._is_critical_error(job_error.error_type),
                    "is_retryable": self._is_retryable_error(job_error.error_type),
                    "suggested_action": self._get_suggested_action(job_error)
                },
                "related_errors": await self._find_related_errors(job_error)
            }
            
        except Exception as e:
            logger.error(f"Error getting error details for job {job_id}: {e}")
            return None
    
    async def _get_deadletter_errors(self, limit: int = 100) -> List[JobError]:
        """Get errors from Redis dead-letter queue."""
        try:
            redis_queue = RedisQueue(queue_name="jobs:main")
            await redis_queue.connect()
            
            # Get items from dead-letter queue
            items = await redis_queue.redis.lrange(redis_queue.deadletter_name, 0, limit - 1)
            
            errors = []
            for item in items:
                try:
                    job_data = json.loads(item)
                    
                    error = JobError(
                        job_id=job_data.get("job_id", "unknown"),
                        title=job_data.get("title", "Unknown"),
                        company=job_data.get("company", "Unknown"),
                        error_type=job_data.get("error_reason", "unknown_error"),
                        error_message=job_data.get("error_message", job_data.get("error_reason", "No error message")),
                        failed_at=job_data.get("failed_at", datetime.now().isoformat()),
                        retry_count=job_data.get("retry_count", 0),
                        correlation_id=job_data.get("correlation_id"),
                        stage=job_data.get("stage"),
                        raw_data=item
                    )
                    
                    errors.append(error)
                    
                except json.JSONDecodeError:
                    # Handle corrupted data
                    error = JobError(
                        job_id="corrupted",
                        title="Corrupted Data",
                        company="Unknown",
                        error_type="data_corruption",
                        error_message="Failed to parse job data from dead-letter queue",
                        failed_at=datetime.now().isoformat(),
                        retry_count=0,
                        correlation_id=None,
                        stage=None,
                        raw_data=item
                    )
                    errors.append(error)
            
            await redis_queue.close()
            return errors
            
        except Exception as e:
            logger.error(f"Error getting dead-letter errors: {e}")
            return []
    
    async def _get_database_error_stats(self) -> Dict[str, int]:
        """Get error statistics from database."""
        try:
            db = get_job_db()
            stats = db.get_job_stats()
            
            return {
                "total_jobs": stats.get("total_jobs", 0),
                "failed_jobs": stats.get("failed_jobs", 0),
                "pending_jobs": stats.get("pending_jobs", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting database error stats: {e}")
            return {"total_jobs": 0, "failed_jobs": 0, "pending_jobs": 0}
    
    def _categorize_errors(self, errors: List[JobError]) -> Counter:
        """Categorize errors by type."""
        return Counter([error.error_type for error in errors])
    
    def _is_critical_error(self, error_type: str) -> bool:
        """Determine if an error type is critical."""
        critical_errors = [
            "database_connection_failed",
            "redis_connection_failed",
            "system_resource_exhausted",
            "authentication_failed",
            "rate_limit_exceeded"
        ]
        return error_type in critical_errors
    
    def _is_retryable_error(self, error_type: str) -> bool:
        """Determine if an error is retryable."""
        non_retryable_errors = [
            "data_corruption",
            "invalid_job_data",
            "authentication_failed",
            "permission_denied"
        ]
        return error_type not in non_retryable_errors
    
    def _get_suggested_action(self, job_error: JobError) -> str:
        """Get suggested action for resolving an error."""
        if job_error.error_type == "Missing required fields: title or company":
            return "Check data source for missing job information"
        elif job_error.error_type == "Job failed suitability check":
            return "Review job filtering criteria"
        elif job_error.retry_count > 3:
            return "Manual review required - multiple retry failures"
        elif "connection" in job_error.error_type.lower():
            return "Check network connectivity and service availability"
        else:
            return "Review error details and consider manual intervention"
    
    async def _find_related_errors(self, job_error: JobError) -> List[Dict[str, Any]]:
        """Find related errors for pattern analysis."""
        try:
            all_errors = await self._get_deadletter_errors(500)
            
            related = []
            for error in all_errors:
                if error.job_id == job_error.job_id:
                    continue
                
                # Check for related errors
                if (error.company == job_error.company or 
                    error.error_type == job_error.error_type or
                    error.correlation_id == job_error.correlation_id):
                    
                    related.append({
                        "job_id": error.job_id,
                        "title": error.title,
                        "company": error.company,
                        "error_type": error.error_type,
                        "failed_at": error.failed_at,
                        "relation_type": self._determine_relation_type(job_error, error)
                    })
            
            return related[:10]  # Limit to 10 related errors
            
        except Exception as e:
            logger.error(f"Error finding related errors: {e}")
            return []
    
    def _determine_relation_type(self, job_error: JobError, other_error: JobError) -> str:
        """Determine the type of relation between two errors."""
        if job_error.correlation_id and job_error.correlation_id == other_error.correlation_id:
            return "same_correlation_id"
        elif job_error.company == other_error.company:
            return "same_company"
        elif job_error.error_type == other_error.error_type:
            return "same_error_type"
        else:
            return "unknown"
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object."""
        try:
            # Try ISO format first
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            try:
                # Try common formats
                return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except:
                # Default to current time if parsing fails
                return datetime.now()
    
    async def _calculate_error_trend(self) -> str:
        """Calculate error trend over time."""
        try:
            # Get errors from last 2 hours
            deadletter_errors = await self._get_deadletter_errors(200)
            
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            two_hours_ago = now - timedelta(hours=2)
            
            recent_errors = len([
                error for error in deadletter_errors
                if self._parse_timestamp(error.failed_at) > one_hour_ago
            ])
            
            previous_errors = len([
                error for error in deadletter_errors
                if two_hours_ago < self._parse_timestamp(error.failed_at) <= one_hour_ago
            ])
            
            if previous_errors == 0:
                return "stable" if recent_errors == 0 else "increasing"
            
            change_percent = ((recent_errors - previous_errors) / previous_errors) * 100
            
            if change_percent > 20:
                return "increasing"
            elif change_percent < -20:
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"Error calculating error trend: {e}")
            return "unknown"
    
    def _calculate_timeline_trend(self, timeline_data: List[Dict[str, Any]]) -> str:
        """Calculate trend from timeline data."""
        if len(timeline_data) < 2:
            return "insufficient_data"
        
        # Compare first half with second half
        mid_point = len(timeline_data) // 2
        first_half_avg = sum(item["total_errors"] for item in timeline_data[:mid_point]) / mid_point
        second_half_avg = sum(item["total_errors"] for item in timeline_data[mid_point:]) / (len(timeline_data) - mid_point)
        
        if first_half_avg == 0:
            return "stable" if second_half_avg == 0 else "increasing"
        
        change_percent = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        
        if change_percent > 25:
            return "increasing"
        elif change_percent < -25:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_recovery_suggestions(self, error_analysis: Dict[str, Any]) -> List[str]:
        """Generate recovery suggestions based on error analysis."""
        suggestions = []
        
        # Check for high retry counts
        high_retry_errors = sum(
            count for retry_type, count in error_analysis["retry_analysis"].items()
            if "3_retries" in retry_type or "4_retries" in retry_type or "5_retries" in retry_type
        )
        
        if high_retry_errors > 5:
            suggestions.append("Consider reviewing retry logic - many jobs failing after multiple retries")
        
        # Check for stage-specific failures
        stage_failures = error_analysis["stage_failures"]
        if stage_failures:
            max_stage = max(stage_failures, key=stage_failures.get)
            if stage_failures[max_stage] > 10:
                suggestions.append(f"High failure rate in {max_stage} stage - investigate stage-specific issues")
        
        # Check for company-specific failures
        company_failures = error_analysis["company_failures"]
        if company_failures:
            max_company = max(company_failures, key=company_failures.get)
            if company_failures[max_company] > 5:
                suggestions.append(f"Multiple failures for {max_company} - check company-specific processing")
        
        # Check for error type patterns
        error_breakdown = error_analysis["error_breakdown"]
        for error_type, data in error_breakdown.items():
            if data["count"] > 10:
                if "connection" in error_type.lower():
                    suggestions.append("Network connectivity issues detected - check service availability")
                elif "validation" in error_type.lower():
                    suggestions.append("Data validation failures - review input data quality")
        
        if not suggestions:
            suggestions.append("Error patterns appear normal - continue monitoring")
        
        return suggestions


# Global error visualization manager instance
error_visualization_manager = ErrorVisualizationManager()