import asyncio
from playwright.async_api import Page
from typing import Optional
from datetime import datetime

from src.scrapers.scraping_models import JobData

async def scrape_keyword(page: Page, keyword: str, scraping_queue: asyncio.Queue):
    """Scrapes a single keyword and puts the results in a queue."""
    jobs_processed = 0
    max_pages = 5
    max_jobs = 100

    for page_num in range(1, max_pages + 1):
        if jobs_processed >= max_jobs:
            break
        
        search_url = f"https://www.eluta.ca/search?q={keyword}"
        if page_num > 1:
            search_url += f"&pg={page_num}"
        
        try:
            await page.goto(search_url, timeout=30000)
            job_elements = await page.query_selector_all(".organic-job")
            
            if not job_elements:
                break
            
            for i, job_elem in enumerate(job_elements):
                if jobs_processed >= max_jobs:
                    break
                
                job_data = await _extract_job_data(job_elem, keyword, page_num, i+1)
                if job_data:
                    await scraping_queue.put(job_data)
                    jobs_processed += 1
                    
        except Exception as e:
            print(f"Page {page_num} error: {e}")
            continue

async def _extract_job_data(job_elem, keyword: str, page_num: int, job_num: int) -> Optional[JobData]:
    """Extracts job data from a single job element."""
    try:
        text = await job_elem.inner_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if len(lines) < 2:
            return None
        
        job_data = JobData(
            title=lines[0],
            company=lines[1],
            location=lines[2] if len(lines) > 2 else "",
            summary=" ".join(lines[3:]) if len(lines) > 3 else "",
            search_keyword=keyword,
            job_id=f"{keyword}_{page_num}_{job_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )
        
        link = await job_elem.query_selector("a")
        if link:
            job_data.url = await link.get_attribute("href")
            
        return job_data
    except Exception:
        return None