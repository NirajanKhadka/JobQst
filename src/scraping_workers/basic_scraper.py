import asyncio
from playwright.async_api import async_playwright, Page
from typing import List
from datetime import datetime

from src.scrapers.scraping_models import ScrapingTask, JobData

async def basic_scraping_worker(worker_name: str, basic_scrape_queue: asyncio.Queue, detail_scrape_queue: asyncio.Queue, stats: dict):
    """Worker that performs basic scraping of job search results."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        while True:
            try:
                task: ScrapingTask = await basic_scrape_queue.get()
                jobs = await _scrape_basic_job_info(page, task)
                
                for job_data in jobs:
                    # Simplified filtering for this example
                    if "senior" not in job_data.basic_info.get('title', '').lower():
                        await detail_scrape_queue.put(job_data)
                        
                stats['tasks_completed'] += 1
                stats['jobs_scraped'] += len(jobs)
                basic_scrape_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception:
                continue
                
        await browser.close()

async def _scrape_basic_job_info(page: Page, task: ScrapingTask) -> List[JobData]:
    """Scrapes basic job information from a search results page."""
    jobs = []
    search_url = f"https://www.eluta.ca/search?q={task.keyword}&pg={task.page_number}"
    await page.goto(search_url, timeout=30000)
    
    job_elements = await page.query_selector_all('.organic-job')
    for job_element in job_elements:
        job_text = await job_element.inner_text()
        lines = [line.strip() for line in job_text.split('\n') if line.strip()]
        if len(lines) >= 2:
            job_data = JobData(basic_info={
                "title": lines[0],
                "company": lines[1],
                "location": lines[2] if len(lines) > 2 else "",
                "scraped_date": datetime.now().isoformat(),
            })
            jobs.append(job_data)
            
    return jobs