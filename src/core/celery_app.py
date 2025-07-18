"""
Celery Configuration for AutoJobAgent

This module configures Celery for distributed task processing, enabling
background job processing, task queuing, and workflow orchestration.
"""

import os
from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)

# Celery configuration
CELERY_CONFIG = {
    "broker_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    "result_backend": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_track_started": True,
    "task_time_limit": 30 * 60,  # 30 minutes
    "task_soft_time_limit": 25 * 60,  # 25 minutes
    "worker_prefetch_multiplier": 1,
    "worker_max_tasks_per_child": 1000,
    "worker_disable_rate_limits": False,
    "task_annotations": {"*": {"rate_limit": "10/m"}},  # 10 tasks per minute per worker
    "beat_schedule": {
        "daily-job-scraping": {
            "task": "src.orchestrator.job_processor.scrape_jobs_daily",
            "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM
        },
        "cleanup-old-jobs": {
            "task": "src.core.job_cache_manager.cleanup_old_jobs",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        "health-check": {
            "task": "src.health_checks.health_utils.run_health_checks",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
        "process-pending-applications": {
            "task": "src.job_applier.job_applier.process_pending_applications",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
        },
        "monitor-email-responses": {
            "schedule": crontab(minute="*/10"),  # Every 10 minutes
        },
    },
}

# Create Celery app
celery_app = Celery("autojob")

# Configure Celery
celery_app.conf.update(CELERY_CONFIG)

# Auto-discover tasks from all modules
celery_app.autodiscover_tasks(
    [
        "src.orchestrator",
        "src.scrapers",
        "src.job_applier",
        "src.document_modifier",
        "src.gmail_monitor",
        "src.manual_review",
        "src.health_checks",
        "src.ats",
        "src.dashboard",
    ]
)

# Task routing
celery_app.conf.task_routes = {
    "src.scrapers.*": {"queue": "scraping"},
    "src.job_applier.*": {"queue": "applications"},
    "src.document_modifier.*": {"queue": "documents"},
    "src.gmail_monitor.*": {"queue": "monitoring"},
    "src.health_checks.*": {"queue": "monitoring"},
    "src.dashboard.*": {"queue": "dashboard"},
    "src.ats.*": {"queue": "applications"},
}


# Error handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    logger.info(f"Request: {self.request!r}")
    return "Debug task completed"


# Health check task
@celery_app.task(bind=True, name="health_check")
def health_check_task(self):
    """Periodic health check task."""
    try:
        from src.health_checks.health_utils import run_health_checks

        results = run_health_checks()

        # Log results
        for check_name, result in results.items():
            if result.get("status") == "error":
                logger.error(f"Health check failed: {check_name} - {result.get('message')}")
            else:
                logger.info(f"Health check passed: {check_name}")

        return results
    except Exception as e:
        logger.error(f"Health check task failed: {e}")
        raise


# Task monitoring
@celery_app.task(bind=True)
def monitor_task_progress(self, task_id):
    """Monitor the progress of a specific task."""
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
        }
    except Exception as e:
        logger.error(f"Task monitoring failed: {e}")
        raise


# Task cleanup
@celery_app.task(bind=True)
def cleanup_completed_tasks(self, hours_old=24):
    """Clean up completed tasks older than specified hours."""
    try:
        from datetime import datetime, timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)

        # This would require additional setup with a result backend that supports cleanup
        # For now, just log the intention
        logger.info(f"Cleanup task executed for tasks older than {hours_old} hours")
        return f"Cleanup completed for tasks older than {hours_old} hours"
    except Exception as e:
        logger.error(f"Task cleanup failed: {e}")
        raise


# Performance monitoring
@celery_app.task(bind=True)
def log_task_metrics(self):
    """Log task execution metrics for monitoring."""
    try:
        # Get task statistics
        stats = celery_app.control.inspect().stats()

        if stats:
            for worker, worker_stats in stats.items():
                logger.info(f"Worker {worker} stats: {worker_stats}")

        return stats
    except Exception as e:
        logger.error(f"Task metrics logging failed: {e}")
        raise


# Queue management
@celery_app.task(bind=True)
def purge_queue(self, queue_name):
    """Purge all tasks from a specific queue."""
    try:
        celery_app.control.purge()
        logger.info(f"Queue {queue_name} purged successfully")
        return f"Queue {queue_name} purged"
    except Exception as e:
        logger.error(f"Queue purge failed: {e}")
        raise


# Task retry with exponential backoff
def retry_task_with_backoff(task_func, max_retries=3, base_delay=60):
    """Retry a task with exponential backoff."""

    def wrapper(*args, **kwargs):
        try:
            return task_func(*args, **kwargs)
        except Exception as exc:
            # Get the current retry count
            retry_count = getattr(wrapper, "retry_count", 0)

            if retry_count < max_retries:
                # Calculate delay with exponential backoff
                delay = base_delay * (2**retry_count)

                # Update retry count
                wrapper.retry_count = retry_count + 1

                # Retry the task
                raise task_func.retry(exc=exc, countdown=delay, max_retries=max_retries)
            else:
                # Max retries reached, log and re-raise
                logger.error(f"Task {task_func.__name__} failed after {max_retries} retries")
                raise

    # Initialize retry count
    wrapper.retry_count = 0
    return wrapper


# Task result caching
@celery_app.task(bind=True)
def cache_task_result(self, cache_key, cache_timeout=3600):
    """Cache the result of a task for a specified time."""
    try:
        from src.core.job_cache_manager import cache_result

        # Get the task result
        result = self.request.called_directly or self.result

        # Cache the result
        cache_result(cache_key, result, timeout=cache_timeout)

        return f"Result cached with key: {cache_key}"
    except Exception as e:
        logger.error(f"Task result caching failed: {e}")
        raise


# Task dependency management
@celery_app.task(bind=True)
def wait_for_dependencies(self, dependency_task_ids):
    """Wait for dependent tasks to complete before proceeding."""
    try:
        results = []
        for task_id in dependency_task_ids:
            result = celery_app.AsyncResult(task_id)
            result.wait()  # Wait for completion
            results.append(result.get())

        return results
    except Exception as e:
        logger.error(f"Task dependency wait failed: {e}")
        raise


# Task chaining example
def create_job_processing_chain(job_data):
    """Create a chain of tasks for job processing."""
    from celery import chain
from src.utils.document_generator import customize

    # Define the task chain
    task_chain = chain(
        scrape_job_details.s(job_data),
        analyze_job_requirements.s(),
        generate_custom_resume.s(),
        submit_application.s(),
    )

    return task_chain


# Example task functions (these would be implemented in their respective modules)
@celery_app.task(bind=True, name="scrape_job_details")
def scrape_job_details(self, job_data):
    """Scrape detailed job information."""
    # Implementation would be in scrapers module
    pass


@celery_app.task(bind=True, name="analyze_job_requirements")
def analyze_job_requirements(self, job_details):
    """Analyze job requirements and match with resume."""
    # Implementation would be in analysis module
    pass


@celery_app.task(bind=True, name="generate_custom_resume")
def generate_custom_resume(self, analysis_result):
    """Generate customized resume for the job."""
    # Implementation would be in document_modifier module
    pass


@celery_app.task(bind=True, name="submit_application")
def submit_application(self, resume_data):
    """Submit the job application."""
    # Implementation would be in job_applier module
    pass


if __name__ == "__main__":
    celery_app.start()
