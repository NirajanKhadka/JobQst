import asyncio
from src.scrapers.scraping_models import JobData, JobStatus

async def processing_stage(processing_queue: asyncio.Queue, analysis_queue: asyncio.Queue, metrics):
    """Processes jobs from the processing_queue and moves them to the analysis_queue."""
    while True:
        try:
            job_data: JobData = await processing_queue.get()
            job_data.status = JobStatus.PROCESSING
            
            if not job_data.title or not job_data.company:
                job_data.status = JobStatus.FAILED
                metrics.increment('jobs_failed')
                continue
            
            if not await _is_suitable_job(job_data):
                job_data.status = JobStatus.FAILED
                metrics.increment('jobs_failed')
                continue
            
            await analysis_queue.put(job_data)
            metrics.increment('jobs_processed')
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Processing stage error: {e}")
            metrics.increment('errors')

async def _is_suitable_job(job_data: JobData) -> bool:
    """Checks if a job is suitable based on keywords."""
    title = job_data.title.lower()
    summary = job_data.summary.lower()
    
    senior_keywords = ["senior", "sr.", "lead", "principal", "manager"]
    if any(keyword in title for keyword in senior_keywords):
        return False
        
    entry_keywords = ["junior", "jr.", "entry", "graduate", "intern"]
    if any(keyword in title for keyword in entry_keywords):
        return True
        
    return True