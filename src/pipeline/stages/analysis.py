import asyncio
from src.scrapers.scraping_models import JobData, JobStatus
from src.enhanced_job_analyzer import JobAnalyzer


async def analysis_stage(
    analysis_queue: asyncio.Queue,
    storage_queue: asyncio.Queue,
    metrics,
    analyzer: JobAnalyzer,
    thread_pool,
):
    """Analyzes jobs and moves them to the storage_queue."""
    while True:
        try:
            job_data: JobData = await analysis_queue.get()
            job_data.status = JobStatus.ANALYZED

            if analyzer:
                try:
                    loop = asyncio.get_event_loop()
                    analysis_result = await loop.run_in_executor(
                        thread_pool, analyzer.analyze_job_deep, job_data.to_dict(), None
                    )
                    job_data.analysis_data = analysis_result
                except Exception as e:
                    print(f"Analysis error: {e}")

            await storage_queue.put(job_data)
            metrics.increment("jobs_analyzed")

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Analysis stage error: {e}")
            metrics.increment("errors")
