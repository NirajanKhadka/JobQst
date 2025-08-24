import asyncio
from typing import Dict, List

from src.utils import profile_helpers
from src.scrapers.scraping_models import ScrapingTask
## Removed obsolete imports: src.scraping_workers.basic_scraper, src.scraping_workers.detail_scraper
from src.utils.profile_helpers import load_profile


class ParallelJobScraper:
    def __init__(self, profile_name: str = "Nirajan", num_workers: int = 3):
        self.profile_name = profile_name
        self.profile = profile_helpers.load_profile(profile_name)
        self.search_terms = list(
            set(self.profile.get("keywords", []) + self.profile.get("skills", []))
        )
        self.num_workers = num_workers

        self.basic_scrape_queue = asyncio.Queue()
        self.detail_scrape_queue = asyncio.Queue()
        self.url_extract_queue = asyncio.Queue()

        self.stats = {"tasks_created": 0, "tasks_completed": 0, "jobs_scraped": 0}

    async def start_parallel_scraping(self, max_jobs_per_keyword: int = 50) -> List[Dict]:
        # Refactored: Use unified scraper
        from src.scrapers.unified_eluta_scraper import ElutaScraper
        results = []
        keywords = getattr(self, 'keywords', ["Python", "Data Analyst", "SQL"])
        # Use unified scraper for all scraping
        eluta_scraper = ElutaScraper(self.profile_name)
        jobs = await eluta_scraper.scrape_all_keywords()
        results.extend(jobs[:max_jobs_per_keyword])
        return results

    async def _create_scraping_tasks(self, max_jobs_per_keyword: int):
        task_id = 0
        for keyword in self.search_terms:
            for page_num in range(1, 6):  # 5 pages
                task = ScrapingTask(
                    task_id=f"task_{task_id}",
                    task_type="basic_scrape",
                    keyword=keyword,
                    page_number=page_num,
                )
                await self.basic_scrape_queue.put(task)
                task_id += 1
        self.stats["tasks_created"] = task_id


async def run_parallel_scraping(
    profile_name: str = "Nirajan", num_workers: int = 3, max_jobs_per_keyword: int = 50
):
    scraper = ParallelJobScraper(profile_name, num_workers)
    return await scraper.start_parallel_scraping(max_jobs_per_keyword)


# For testing this scraper, use: python -m pytest tests/scrapers/
# Example usage available in tests/ directory