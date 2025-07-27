import asyncio
import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
from src.scrapers.scraping_models import JobData, JobStatus
from src.pipeline.redis_queue import RedisQueue

# Set up structured logging
logger = logging.getLogger(__name__)

class StructuredLogger:
    """Structured logging with correlation IDs for pipeline stages."""
    
    @staticmethod
    def log_job_event(correlation_id: str, stage: str, event: str, job_data: JobData,
                     extra_data: Dict[str, Any] = None, level: str = "info"):
        """Log structured job processing events."""
        log_entry = {
            "correlation_id": correlation_id,
            "stage": stage,
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "job_id": getattr(job_data, 'job_id', 'unknown'),
            "job_title": getattr(job_data, 'title', 'unknown'),
            "job_company": getattr(job_data, 'company', 'unknown'),
            "job_status": getattr(job_data, 'status', 'unknown').value if hasattr(getattr(job_data, 'status', None), 'value') else str(getattr(job_data, 'status', 'unknown')),
            "retry_count": getattr(job_data, 'retry_count', 0)
        }
        
        if extra_data:
            log_entry.update(extra_data)
        
        log_message = f"[{correlation_id}] {stage.upper()}: {event} - Job: {log_entry['job_title']} at {log_entry['job_company']}"
        
        if level == "error":
            logger.error(log_message, extra=log_entry)
        elif level == "warning":
            logger.warning(log_message, extra=log_entry)
        elif level == "debug":
            logger.debug(log_message, extra=log_entry)
        else:
            logger.info(log_message, extra=log_entry)
    
    @staticmethod
    def log_stage_metrics(correlation_id: str, stage: str, metrics_data: Dict[str, Any]):
        """Log stage performance metrics."""
        log_entry = {
            "correlation_id": correlation_id,
            "stage": stage,
            "event": "metrics_update",
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics_data
        }
        
        logger.info(f"[{correlation_id}] {stage.upper()}: Metrics update", extra=log_entry)


async def processing_stage(processing_queue: asyncio.Queue, analysis_queue: asyncio.Queue, metrics, use_redis: bool = True, redis_queue_name: str = "jobs:main"):
    """
    Processes jobs from the processing_queue or Redis and moves them to the analysis_queue.
    Implements retry and dead-letter logic with structured logging and correlation IDs.
    """
    redis_queue = RedisQueue(queue_name=redis_queue_name)
    max_retries = int(os.getenv("JOB_MAX_RETRIES", 3))
    stage_correlation_id = str(uuid.uuid4())
    
    logger.info(f"[{stage_correlation_id}] PROCESSING: Stage started with Redis={use_redis}, queue={redis_queue_name}")
    
    while True:
        job_correlation_id = None
        job_data = None
        processing_start_time = datetime.now()
        
        try:
            # Get job from queue
            if use_redis:
                job_dict = await redis_queue.dequeue(timeout=5)
                if not job_dict:
                    await asyncio.sleep(1)
                    continue
                job_data = JobData(**job_dict) if isinstance(job_dict, dict) else None
                
                # Extract or create correlation ID
                job_correlation_id = job_dict.get("correlation_id", str(uuid.uuid4()))
                if not job_dict.get("correlation_id"):
                    job_dict["correlation_id"] = job_correlation_id
                    
            else:
                job_data: JobData = await processing_queue.get()
                job_correlation_id = getattr(job_data, "correlation_id", str(uuid.uuid4()))
                if not hasattr(job_data, "correlation_id"):
                    job_data.correlation_id = job_correlation_id
            
            if not job_data:
                continue
                
            # Log job received
            StructuredLogger.log_job_event(
                job_correlation_id, "processing", "job_received", job_data,
                {"processing_start_time": processing_start_time.isoformat()}
            )
            
            job_data.status = JobStatus.PROCESSING

            # Validate job data
            if not getattr(job_data, "title", None) or not getattr(job_data, "company", None):
                job_data.status = JobStatus.FAILED
                error_msg = "Missing required fields: title or company"
                
                StructuredLogger.log_job_event(
                    job_correlation_id, "processing", "validation_failed", job_data,
                    {"error": error_msg, "has_title": bool(getattr(job_data, "title", None)),
                     "has_company": bool(getattr(job_data, "company", None))}, "error"
                )
                
                metrics.increment("jobs_failed")
                
                # Move to dead-letter if using Redis
                if use_redis:
                    job_dict_with_error = job_data.to_dict() if hasattr(job_data, 'to_dict') else job_dict
                    job_dict_with_error.update({
                        "error_reason": error_msg,
                        "failed_at": datetime.now().isoformat(),
                        "correlation_id": job_correlation_id
                    })
                    await redis_queue.move_to_deadletter(job_dict_with_error)
                continue

            # Check job suitability
            if not await _is_suitable_job(job_data, job_correlation_id):
                job_data.status = JobStatus.FAILED
                error_msg = "Job failed suitability check"
                
                StructuredLogger.log_job_event(
                    job_correlation_id, "processing", "suitability_failed", job_data,
                    {"error": error_msg}, "warning"
                )
                
                metrics.increment("jobs_failed")
                
                if use_redis:
                    job_dict_with_error = job_data.to_dict() if hasattr(job_data, 'to_dict') else job_dict
                    job_dict_with_error.update({
                        "error_reason": error_msg,
                        "failed_at": datetime.now().isoformat(),
                        "correlation_id": job_correlation_id
                    })
                    await redis_queue.move_to_deadletter(job_dict_with_error)
                continue

            # Check retry count
            retry_count = getattr(job_data, "retry_count", 0)
            if retry_count > max_retries:
                job_data.status = JobStatus.FAILED
                error_msg = f"Max retries exceeded: {retry_count}/{max_retries}"
                
                StructuredLogger.log_job_event(
                    job_correlation_id, "processing", "max_retries_exceeded", job_data,
                    {"error": error_msg, "retry_count": retry_count, "max_retries": max_retries}, "error"
                )
                
                metrics.increment("jobs_failed")
                
                if use_redis:
                    job_dict_with_error = job_data.to_dict() if hasattr(job_data, 'to_dict') else job_dict
                    job_dict_with_error.update({
                        "error_reason": error_msg,
                        "failed_at": datetime.now().isoformat(),
                        "correlation_id": job_correlation_id
                    })
                    await redis_queue.move_to_deadletter(job_dict_with_error)
                continue

            # Successfully processed - move to analysis queue
            processing_time = (datetime.now() - processing_start_time).total_seconds()
            
            StructuredLogger.log_job_event(
                job_correlation_id, "processing", "job_processed_successfully", job_data,
                {"processing_time_seconds": processing_time, "next_stage": "analysis"}
            )
            
            await analysis_queue.put(job_data)
            metrics.increment("jobs_processed")
            
            # Log performance metrics periodically
            if metrics.get_count("jobs_processed") % 100 == 0:
                StructuredLogger.log_stage_metrics(
                    stage_correlation_id, "processing", {
                        "jobs_processed": metrics.get_count("jobs_processed"),
                        "jobs_failed": metrics.get_count("jobs_failed"),
                        "average_processing_time": processing_time
                    }
                )

        except asyncio.CancelledError:
            logger.info(f"[{stage_correlation_id}] PROCESSING: Stage cancelled")
            break
        except Exception as e:
            error_msg = f"Processing stage error: {e}"
            
            if job_correlation_id and job_data:
                StructuredLogger.log_job_event(
                    job_correlation_id, "processing", "unexpected_error", job_data,
                    {"error": error_msg, "exception_type": type(e).__name__}, "error"
                )
            else:
                logger.error(f"[{stage_correlation_id}] PROCESSING: {error_msg}")
            
            metrics.increment("errors")


async def _is_suitable_job(job_data: JobData, correlation_id: str = None) -> bool:
    """
    Checks if a job is suitable based on keywords with structured logging.
    
    Args:
        job_data: Job data to evaluate
        correlation_id: Correlation ID for logging
        
    Returns:
        bool: True if job is suitable, False otherwise
    """
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    
    title = job_data.title.lower() if job_data.title else ""
    summary = job_data.summary.lower() if job_data.summary else ""

    senior_keywords = ["senior", "sr.", "lead", "principal", "manager"]
    entry_keywords = ["junior", "jr.", "entry", "graduate", "intern"]
    
    # Check for senior-level positions (exclude)
    senior_matches = [keyword for keyword in senior_keywords if keyword in title]
    if senior_matches:
        StructuredLogger.log_job_event(
            correlation_id, "processing", "job_rejected_senior_level", job_data,
            {"rejection_reason": "senior_level_position", "matched_keywords": senior_matches}, "debug"
        )
        return False

    # Check for entry-level positions (include)
    entry_matches = [keyword for keyword in entry_keywords if keyword in title]
    if entry_matches:
        StructuredLogger.log_job_event(
            correlation_id, "processing", "job_accepted_entry_level", job_data,
            {"acceptance_reason": "entry_level_position", "matched_keywords": entry_matches}, "debug"
        )
        return True

    # Default acceptance for mid-level positions
    StructuredLogger.log_job_event(
        correlation_id, "processing", "job_accepted_default", job_data,
        {"acceptance_reason": "default_acceptance", "title_keywords_checked": len(senior_keywords + entry_keywords)}, "debug"
    )
    return True
