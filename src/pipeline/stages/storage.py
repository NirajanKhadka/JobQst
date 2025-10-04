import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
from src.scrapers.scraping_models import JobData, JobStatus
from src.core.job_database import get_job_db

# Set up structured logging
logger = logging.getLogger(__name__)


class StructuredLogger:
    """Structured logging with correlation IDs for pipeline stages."""

    @staticmethod
    def log_job_event(
        correlation_id: str,
        stage: str,
        event: str,
        job_data: JobData,
        extra_data: Dict[str, Any] = None,
        level: str = "info",
    ):
        """Log structured job processing events."""
        log_entry = {
            "correlation_id": correlation_id,
            "stage": stage,
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "job_id": getattr(job_data, "job_id", "unknown"),
            "job_title": getattr(job_data, "title", "unknown"),
            "job_company": getattr(job_data, "company", "unknown"),
            "job_status": (
                getattr(job_data, "status", "unknown").value
                if hasattr(getattr(job_data, "status", None), "value")
                else str(getattr(job_data, "status", "unknown"))
            ),
            "retry_count": getattr(job_data, "retry_count", 0),
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
            "metrics": metrics_data,
        }

        logger.info(f"[{correlation_id}] {stage.upper()}: Metrics update", extra=log_entry)


async def storage_stage(storage_queue: asyncio.Queue, metrics, db, thread_pool):
    """
    Saves jobs to the database with structured logging and correlation IDs.
    """
    stage_correlation_id = str(uuid.uuid4())
    logger.info(
        f"[{stage_correlation_id}] STORAGE: Stage started with database={type(db).__name__}"
    )

    while True:
        job_correlation_id = None
        job_data = None
        storage_start_time = datetime.now()

        try:
            job_data: JobData = await storage_queue.get()

            # Extract or create correlation ID
            job_correlation_id = getattr(job_data, "correlation_id", str(uuid.uuid4()))
            if not hasattr(job_data, "correlation_id"):
                job_data.correlation_id = job_correlation_id

            # Log job received for storage
            StructuredLogger.log_job_event(
                job_correlation_id,
                "storage",
                "job_received",
                job_data,
                {"storage_start_time": storage_start_time.isoformat()},
            )

            job_data.status = JobStatus.SAVED

            try:
                # Log database save attempt
                StructuredLogger.log_job_event(
                    job_correlation_id,
                    "storage",
                    "database_save_started",
                    job_data,
                    {"database_type": type(db).__name__},
                )

                loop = asyncio.get_event_loop()
                success = await loop.run_in_executor(thread_pool, db.add_job, job_data.to_dict())

                storage_time = (datetime.now() - storage_start_time).total_seconds()

                if success:
                    # Job successfully saved
                    StructuredLogger.log_job_event(
                        job_correlation_id,
                        "storage",
                        "job_saved_successfully",
                        job_data,
                        {
                            "storage_time_seconds": storage_time,
                            "database_operation": "insert",
                            "final_status": "saved",
                        },
                    )
                    metrics.increment("jobs_saved")
                else:
                    # Job was a duplicate
                    job_data.status = JobStatus.DUPLICATE
                    StructuredLogger.log_job_event(
                        job_correlation_id,
                        "storage",
                        "job_duplicate_detected",
                        job_data,
                        {
                            "storage_time_seconds": storage_time,
                            "database_operation": "duplicate_check",
                            "final_status": "duplicate",
                        },
                        "warning",
                    )
                    metrics.increment("jobs_duplicates")

            except Exception as e:
                storage_time = (datetime.now() - storage_start_time).total_seconds()
                error_msg = f"Database save error: {e}"

                StructuredLogger.log_job_event(
                    job_correlation_id,
                    "storage",
                    "database_save_failed",
                    job_data,
                    {
                        "error": error_msg,
                        "exception_type": type(e).__name__,
                        "storage_time_seconds": storage_time,
                        "database_operation": "failed",
                    },
                    "error",
                )

                job_data.status = JobStatus.FAILED
                metrics.increment("jobs_failed")

            # Log performance metrics periodically
            if (metrics.get_count("jobs_saved") + metrics.get_count("jobs_duplicates")) % 25 == 0:
                StructuredLogger.log_stage_metrics(
                    stage_correlation_id,
                    "storage",
                    {
                        "jobs_saved": metrics.get_count("jobs_saved"),
                        "jobs_duplicates": metrics.get_count("jobs_duplicates"),
                        "jobs_failed": metrics.get_count("jobs_failed"),
                        "average_storage_time": storage_time,
                        "database_type": type(db).__name__,
                    },
                )

        except asyncio.CancelledError:
            logger.info(f"[{stage_correlation_id}] STORAGE: Stage cancelled")
            break
        except Exception as e:
            error_msg = f"Storage stage error: {e}"

            if job_correlation_id and job_data:
                StructuredLogger.log_job_event(
                    job_correlation_id,
                    "storage",
                    "unexpected_error",
                    job_data,
                    {"error": error_msg, "exception_type": type(e).__name__},
                    "error",
                )
            else:
                logger.error(f"[{stage_correlation_id}] STORAGE: {error_msg}")

            metrics.increment("errors")
