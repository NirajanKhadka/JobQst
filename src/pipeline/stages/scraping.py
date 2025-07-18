import asyncio
from typing import Optional
from datetime import datetime

from src.scrapers.scraping_models import JobData
from src.scrapers.mcp_browser_client import get_browser_client


async def scrape_keyword_mcp(keyword: str, scraping_queue: asyncio.Queue):
    """Scrapes a single keyword using MCP and puts the results in a queue."""
    browser_client = get_browser_client()
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
            # Navigate using MCP
            if not await browser_client.navigate_to_url(search_url):
                print(f"Failed to navigate to {search_url}")
                continue
            
            # Wait for content to load
            await browser_client.wait_for_content()
            
            # Get page snapshot
            snapshot = await browser_client.get_page_snapshot()
            if not snapshot:
                print(f"Failed to get page snapshot for {search_url}")
                continue
            
            # Find job elements in the snapshot
            job_elements = await browser_client.find_job_elements(snapshot)

            if not job_elements:
                print(f"No job elements found on page {page_num}")
                break

            for i, job_elem in enumerate(job_elements):
                if jobs_processed >= max_jobs:
                    break

                job_data = await browser_client.extract_job_data_from_element(
                    job_elem, keyword, page_num, i + 1
                )
                if job_data:
                    # Convert to JobData model
                    job_data_obj = JobData(
                        title=job_data['title'],
                        company=job_data['company'],
                        location=job_data['location'],
                        summary=job_data['summary'],
                        search_keyword=job_data['search_keyword'],
                        job_id=job_data['job_id'],
                        url=job_data['url']
                    )
                    await scraping_queue.put(job_data_obj)
                    jobs_processed += 1

        except Exception as e:
            print(f"Page {page_num} error: {e}")
            continue


# Keep the original function for backward compatibility
async def scrape_keyword(page, keyword: str, scraping_queue: asyncio.Queue):
    """Legacy scraping function using direct Playwright API."""
    print("Warning: Using legacy Playwright scraping. Consider using scrape_keyword_mcp() instead.")
    
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

                job_data = await _extract_job_data(job_elem, keyword, page_num, i + 1)
                if job_data:
                    await scraping_queue.put(job_data)
                    jobs_processed += 1

        except Exception as e:
            print(f"Page {page_num} error: {e}")
            continue


async def _extract_job_data(
    job_elem, keyword: str, page_num: int, job_num: int
) -> Optional[JobData]:
    """Extracts job data from a single job element."""
    try:
        text = await job_elem.inner_text()
        lines = [line.strip() for line in text.split("\n") if line.strip()]

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
