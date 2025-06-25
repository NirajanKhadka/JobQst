import asyncio
from src.scrapers.scraping_models import JobData, JobStatus
from src.core.job_database import ModernJobDatabase

async def storage_stage(storage_queue: asyncio.Queue, metrics, db: ModernJobDatabase, thread_pool):
    """Saves jobs to the database."""
    while True:
        try:
            job_data: JobData = await storage_queue.get()
            job_data.status = JobStatus.SAVED
            
            try:
                loop = asyncio.get_event_loop()
                success = await loop.run_in_executor(
                    thread_pool,
                    db.add_job,
                    job_data.to_dict()
                )
                
                if success:
                    metrics.increment('jobs_saved')
                else:
                    metrics.increment('jobs_duplicates')
                    job_data.status = JobStatus.DUPLICATE
                    
            except Exception as e:
                print(f"Database save error: {e}")
                metrics.increment('jobs_failed')
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Storage stage error: {e}")
            metrics.increment('errors')