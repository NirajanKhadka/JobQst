import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
from src.scrapers.scraping_models import JobData, JobStatus
from src.ai.enhanced_job_analyzer import EnhancedJobAnalyzer

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


async def analysis_stage(
    analysis_queue: asyncio.Queue,
    storage_queue: asyncio.Queue,
    metrics,
    analyzer: EnhancedJobAnalyzer,
    thread_pool,
):
    """
    Analyzes jobs and moves them to the storage_queue with structured logging and correlation IDs.
    """
    stage_correlation_id = str(uuid.uuid4())
    logger.info(f"[{stage_correlation_id}] ANALYSIS: Stage started with analyzer={bool(analyzer)}")
    
    while True:
        job_correlation_id = None
        job_data = None
        analysis_start_time = datetime.now()
        
        try:
            job_data: JobData = await analysis_queue.get()
            
            # Extract or create correlation ID
            job_correlation_id = getattr(job_data, "correlation_id", str(uuid.uuid4()))
            if not hasattr(job_data, "correlation_id"):
                job_data.correlation_id = job_correlation_id
            
            # Log job received for analysis
            StructuredLogger.log_job_event(
                job_correlation_id, "analysis", "job_received", job_data,
                {"analysis_start_time": analysis_start_time.isoformat(), "has_analyzer": bool(analyzer)}
            )
            
            job_data.status = JobStatus.ANALYZED

            if analyzer:
                try:
                    # Log analysis start
                    StructuredLogger.log_job_event(
                        job_correlation_id, "analysis", "analysis_started", job_data,
                        {"analyzer_type": type(analyzer).__name__}
                    )
                    
                    loop = asyncio.get_event_loop()
                    analysis_result = await loop.run_in_executor(
                        thread_pool, analyzer.analyze_job_deep, job_data.to_dict(), None
                    )
                    
                    job_data.analysis_data = analysis_result
                    analysis_time = (datetime.now() - analysis_start_time).total_seconds()
                    
                    # Log successful analysis
                    StructuredLogger.log_job_event(
                        job_correlation_id, "analysis", "analysis_completed", job_data,
                        {
                            "analysis_time_seconds": analysis_time,
                            "analysis_result_keys": list(analysis_result.keys()) if isinstance(analysis_result, dict) else None,
                            "analysis_data_size": len(str(analysis_result)) if analysis_result else 0
                        }
                    )
                    
                except Exception as e:
                    analysis_time = (datetime.now() - analysis_start_time).total_seconds()
                    error_msg = f"Analysis error: {e}"
                    
                    StructuredLogger.log_job_event(
                        job_correlation_id, "analysis", "analysis_failed", job_data,
                        {
                            "error": error_msg,
                            "exception_type": type(e).__name__,
                            "analysis_time_seconds": analysis_time
                        }, "error"
                    )
                    
                    # Set empty analysis data to continue processing
                    job_data.analysis_data = {}
            else:
                # No analyzer available
                StructuredLogger.log_job_event(
                    job_correlation_id, "analysis", "analysis_skipped", job_data,
                    {"reason": "no_analyzer_available"}, "warning"
                )
                job_data.analysis_data = {}

            # Move to storage queue
            total_processing_time = (datetime.now() - analysis_start_time).total_seconds()
            
            StructuredLogger.log_job_event(
                job_correlation_id, "analysis", "job_analyzed_successfully", job_data,
                {"total_processing_time_seconds": total_processing_time, "next_stage": "storage"}
            )
            
            await storage_queue.put(job_data)
            metrics.increment("jobs_analyzed")
            
            # Log performance metrics periodically
            if metrics.get_count("jobs_analyzed") % 50 == 0:
                StructuredLogger.log_stage_metrics(
                    stage_correlation_id, "analysis", {
                        "jobs_analyzed": metrics.get_count("jobs_analyzed"),
                        "errors": metrics.get_count("errors"),
                        "average_processing_time": total_processing_time,
                        "analyzer_available": bool(analyzer)
                    }
                )

        except asyncio.CancelledError:
            logger.info(f"[{stage_correlation_id}] ANALYSIS: Stage cancelled")
            break
        except Exception as e:
            error_msg = f"Analysis stage error: {e}"
            
            if job_correlation_id and job_data:
                StructuredLogger.log_job_event(
                    job_correlation_id, "analysis", "unexpected_error", job_data,
                    {"error": error_msg, "exception_type": type(e).__name__}, "error"
                )
            else:
                logger.error(f"[{stage_correlation_id}] ANALYSIS: {error_msg}")
            
            metrics.increment("errors")
