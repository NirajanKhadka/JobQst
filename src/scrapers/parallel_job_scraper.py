import asyncio
from typing import Dict, List

from src.utils import profile_helpers
from src.scrapers.scraping_models import ScrapingTask
from src.scraping_workers.basic_scraper import basic_scraping_worker
from src.scraping_workers.detail_scraper import detail_scraping_worker

class ParallelJobScraper:
    def __init__(self, profile_name: str = "Nirajan", num_workers: int = 3):
        self.profile_name = profile_name
        self.profile = profile_helpers.load_profile(profile_name)
        self.search_terms = list(set(self.profile.get("keywords", []) + self.profile.get("skills", [])))
        self.num_workers = num_workers
        
        self.basic_scrape_queue = asyncio.Queue()
        self.detail_scrape_queue = asyncio.Queue()
        self.url_extract_queue = asyncio.Queue()
        
        self.stats = {'tasks_created': 0, 'tasks_completed': 0, 'jobs_scraped': 0}

    async def start_parallel_scraping(self, max_jobs_per_keyword: int = 50) -> List[Dict]:
        await self._create_scraping_tasks(max_jobs_per_keyword)
        
        workers = []
        for i in range(self.num_workers):
            workers.append(asyncio.create_task(basic_scraping_worker(f"BasicWorker-{i+1}", self.basic_scrape_queue, self.detail_scrape_queue, self.stats)))
        
        workers.append(asyncio.create_task(detail_scraping_worker("DetailWorker-1", self.detail_scrape_queue, self.url_extract_queue, self.stats)))
        
        await self.basic_scrape_queue.join()
        await self.detail_scrape_queue.join()
        
        for worker in workers:
            worker.cancel()
            
        return [] # Simplified for this example

    async def _create_scraping_tasks(self, max_jobs_per_keyword: int):
        task_id = 0
        for keyword in self.search_terms:
            for page_num in range(1, 6): # 5 pages
                task = ScrapingTask(task_id=f"task_{task_id}", task_type="basic_scrape", keyword=keyword, page_number=page_num)
                await self.basic_scrape_queue.put(task)
                task_id += 1
        self.stats['tasks_created'] = task_id

async def run_parallel_scraping(profile_name: str = "Nirajan", num_workers: int = 3, max_jobs_per_keyword: int = 50):
    scraper = ParallelJobScraper(profile_name, num_workers)
    return await scraper.start_parallel_scraping(max_jobs_per_keyword)

if __name__ == "__main__":
    asyncio.run(run_parallel_scraping())
