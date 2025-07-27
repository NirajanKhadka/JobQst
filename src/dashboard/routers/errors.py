"""
Error visualization router for the AutoJobAgent Dashboard API.

This module provides REST API endpoints for error analysis, visualization,
and management of failed jobs and dead-letter queue operations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Path

from src.dashboard.components.error_visualization import error_visualization_manager

# Set up router and logging
router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/summary")
async def get_error_summary() -> Dict[str, Any]:
    """
    Get comprehensive error summary and statistics.
    
    Returns:
        Dictionary containing error summary information
    """
    try:
        error_summary = await error_visualization_manager.get_error_summary()
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": error_summary.__dict__
        }
        
    except Exception as e:
        logger.error(f"Error getting error summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get error summary: {str(e)}")


@router.get("/failed-jobs")
async def get_failed_jobs_analysis(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of failed jobs to analyze")
) -> Dict[str, Any]:
    """
    Get detailed analysis of failed jobs.
    
    Args:
        limit: Maximum number of failed jobs to analyze
        
    Returns:
        Dictionary containing failed jobs analysis
    """
    try:
        analysis = await error_visualization_manager.get_failed_jobs_analysis(limit)
        return analysis
        
    except Exception as e:
        logger.error(f"Error getting failed jobs analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze failed jobs: {str(e)}")


@router.get("/timeline")
async def get_error_timeline(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to include in timeline")
) -> Dict[str, Any]:
    """
    Get error timeline for visualization.
    
    Args:
        hours: Number of hours to include in timeline (max 7 days)
        
    Returns:
        Dictionary containing error timeline data
    """
    try:
        timeline = await error_visualization_manager.get_error_timeline(hours)
        return timeline
        
    except Exception as e:
        logger.error(f"Error getting error timeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get error timeline: {str(e)}")


@router.get("/job/{job_id}")
async def get_job_error_details(
    job_id: str = Path(..., description="Job ID to get error details for")
) -> Dict[str, Any]:
    """
    Get detailed error information for a specific job.
    
    Args:
        job_id: Job ID to get error details for
        
    Returns:
        Dictionary containing detailed error information
    """
    try:
        error_details = await error_visualization_manager.get_error_details(job_id)
        
        if not error_details:
            raise HTTPException(status_code=404, detail=f"No error details found for job ID: {job_id}")
        
        return error_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job error details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job error details: {str(e)}")


@router.get("/patterns")
async def get_error_patterns() -> Dict[str, Any]:
    """
    Get error patterns and trends analysis.
    
    Returns:
        Dictionary containing error patterns analysis
    """
    try:
        # Get comprehensive analysis
        failed_jobs_analysis = await error_visualization_manager.get_failed_jobs_analysis(200)
        error_summary = await error_visualization_manager.get_error_summary()
        
        # Extract patterns
        patterns = {
            "timestamp": datetime.now().isoformat(),
            "error_type_patterns": failed_jobs_analysis.get("error_breakdown", {}),
            "stage_failure_patterns": failed_jobs_analysis.get("stage_failures", {}),
            "company_failure_patterns": failed_jobs_analysis.get("company_failures", {}),
            "time_patterns": failed_jobs_analysis.get("time_distribution", {}),
            "retry_patterns": failed_jobs_analysis.get("retry_analysis", {}),
            "correlation_patterns": len(failed_jobs_analysis.get("correlation_tracking", {})),
            "trend_analysis": {
                "overall_trend": error_summary.error_trend,
                "critical_error_ratio": error_summary.critical_errors / max(error_summary.total_errors, 1),
                "recent_error_spike": error_summary.recent_errors > (error_summary.total_errors * 0.3)
            },
            "recommendations": failed_jobs_analysis.get("recovery_suggestions", [])
        }
        
        return patterns
        
    except Exception as e:
        logger.error(f"Error getting error patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get error patterns: {str(e)}")


@router.get("/categories")
async def get_error_categories() -> Dict[str, Any]:
    """
    Get error categorization and classification.
    
    Returns:
        Dictionary containing error categories
    """
    try:
        failed_jobs_analysis = await error_visualization_manager.get_failed_jobs_analysis(300)
        error_breakdown = failed_jobs_analysis.get("error_breakdown", {})
        
        categories = {
            "timestamp": datetime.now().isoformat(),
            "total_error_types": len(error_breakdown),
            "categories": {},
            "severity_distribution": {
                "critical": 0,
                "warning": 0,
                "info": 0
            },
            "retryability": {
                "retryable": 0,
                "non_retryable": 0
            }
        }
        
        # Categorize errors
        for error_type, data in error_breakdown.items():
            is_critical = error_visualization_manager._is_critical_error(error_type)
            is_retryable = error_visualization_manager._is_retryable_error(error_type)
            
            # Determine category
            if "connection" in error_type.lower():
                category = "connectivity"
            elif "validation" in error_type.lower() or "missing" in error_type.lower():
                category = "data_quality"
            elif "timeout" in error_type.lower() or "rate" in error_type.lower():
                category = "performance"
            elif "permission" in error_type.lower() or "auth" in error_type.lower():
                category = "authorization"
            else:
                category = "processing"
            
            if category not in categories["categories"]:
                categories["categories"][category] = {
                    "count": 0,
                    "error_types": [],
                    "severity": "info"
                }
            
            categories["categories"][category]["count"] += data["count"]
            categories["categories"][category]["error_types"].append({
                "type": error_type,
                "count": data["count"],
                "examples": data.get("examples", [])
            })
            
            # Update severity
            if is_critical:
                categories["categories"][category]["severity"] = "critical"
                categories["severity_distribution"]["critical"] += data["count"]
            elif categories["categories"][category]["severity"] != "critical":
                categories["categories"][category]["severity"] = "warning"
                categories["severity_distribution"]["warning"] += data["count"]
            else:
                categories["severity_distribution"]["info"] += data["count"]
            
            # Update retryability
            if is_retryable:
                categories["retryability"]["retryable"] += data["count"]
            else:
                categories["retryability"]["non_retryable"] += data["count"]
        
        return categories
        
    except Exception as e:
        logger.error(f"Error getting error categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get error categories: {str(e)}")


@router.get("/dashboard-data")
async def get_error_dashboard_data() -> Dict[str, Any]:
    """
    Get comprehensive error data for dashboard display.
    
    Returns:
        Dictionary containing all error dashboard data
    """
    try:
        # Get all error data
        error_summary = await error_visualization_manager.get_error_summary()
        failed_jobs_analysis = await error_visualization_manager.get_failed_jobs_analysis(100)
        error_timeline = await error_visualization_manager.get_error_timeline(24)
        
        # Compile dashboard data
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": error_summary.__dict__,
            "failed_jobs_analysis": {
                "total_failed_jobs": failed_jobs_analysis.get("total_failed_jobs", 0),
                "error_breakdown": failed_jobs_analysis.get("error_breakdown", {}),
                "stage_failures": failed_jobs_analysis.get("stage_failures", {}),
                "top_companies": dict(list(failed_jobs_analysis.get("company_failures", {}).items())[:5]),
                "recovery_suggestions": failed_jobs_analysis.get("recovery_suggestions", [])
            },
            "timeline": {
                "data": error_timeline.get("timeline", []),
                "summary": error_timeline.get("summary", {}),
                "time_range_hours": error_timeline.get("time_range_hours", 24)
            },
            "alerts": [],
            "quick_stats": {
                "error_rate": error_summary.error_rate_percent,
                "critical_errors": error_summary.critical_errors,
                "recent_errors": error_summary.recent_errors,
                "trend": error_summary.error_trend,
                "most_common_error": error_summary.top_error_types[0]["type"] if error_summary.top_error_types else "None"
            }
        }
        
        # Add alerts for critical conditions
        if error_summary.error_rate_percent > 10:
            dashboard_data["alerts"].append({
                "type": "high_error_rate",
                "severity": "critical",
                "message": f"Error rate is {error_summary.error_rate_percent}% - above 10% threshold"
            })
        
        if error_summary.critical_errors > 5:
            dashboard_data["alerts"].append({
                "type": "critical_errors",
                "severity": "critical",
                "message": f"{error_summary.critical_errors} critical errors detected"
            })
        
        if error_summary.error_trend == "increasing":
            dashboard_data["alerts"].append({
                "type": "increasing_errors",
                "severity": "warning",
                "message": "Error rate is trending upward"
            })
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting error dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get error dashboard data: {str(e)}")


@router.get("/health-impact")
async def get_error_health_impact() -> Dict[str, Any]:
    """
    Get analysis of how errors are impacting system health.
    
    Returns:
        Dictionary containing error health impact analysis
    """
    try:
        error_summary = await error_visualization_manager.get_error_summary()
        failed_jobs_analysis = await error_visualization_manager.get_failed_jobs_analysis(200)
        
        # Calculate health impact metrics
        total_jobs = failed_jobs_analysis.get("total_failed_jobs", 0)
        stage_failures = failed_jobs_analysis.get("stage_failures", {})
        
        # Determine most impacted stage
        most_impacted_stage = max(stage_failures, key=stage_failures.get) if stage_failures else None
        
        # Calculate system impact score (0-100)
        impact_score = min(100, (
            (error_summary.error_rate_percent * 2) +  # Error rate impact
            (error_summary.critical_errors * 5) +     # Critical errors impact
            (error_summary.recent_errors * 2)         # Recent errors impact
        ))
        
        # Determine impact level
        if impact_score >= 70:
            impact_level = "severe"
        elif impact_score >= 40:
            impact_level = "moderate"
        elif impact_score >= 20:
            impact_level = "minor"
        else:
            impact_level = "minimal"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "impact_score": round(impact_score, 1),
            "impact_level": impact_level,
            "metrics": {
                "error_rate_percent": error_summary.error_rate_percent,
                "critical_errors": error_summary.critical_errors,
                "recent_errors": error_summary.recent_errors,
                "total_failed_jobs": total_jobs
            },
            "stage_impact": {
                "most_impacted_stage": most_impacted_stage,
                "stage_failure_counts": stage_failures
            },
            "trend_impact": {
                "error_trend": error_summary.error_trend,
                "trend_severity": "high" if error_summary.error_trend == "increasing" else "low"
            },
            "recommendations": [
                "Monitor error trends closely" if impact_level in ["moderate", "severe"] else "Continue normal monitoring",
                f"Focus on {most_impacted_stage} stage issues" if most_impacted_stage else "No specific stage focus needed",
                "Consider scaling back operations" if impact_level == "severe" else "Normal operations can continue"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting error health impact: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get error health impact: {str(e)}")