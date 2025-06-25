import asyncio
from typing import Dict
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import async_playwright

from src.core.job_database import get_job_db
from src.utils.job_analysis_engine import JobAnalyzer
from src.pipeline.stages.scraping import scrape_keyword
from src.pipeline.stages.processing import processing_stage
from src.pipeline.stages.analysis import analysis_stage
from src.pipeline.stages.storage import storage_stage

class ModernJobPipeline:
    def __init__(self, profile: Dict, config: Dict):
        self.profile = profile
        self.config = config
        self.db = get_job_db()
        self.analyzer = JobAnalyzer(use_ai=config.get('enable_ai_analysis', True))
        self.thread_pool = ThreadPoolExecutor(max_workers=config.get('max_workers', 4))
        
        self.scraping_queue = asyncio.Queue()
        self.processing_queue = asyncio.Queue()
        self.analysis_queue = asyncio.Queue()
        self.storage_queue = asyncio.Queue()
        
        self.metrics = self # Simplified for this example
        self.stats = {'jobs_scraped': 0, 'jobs_processed': 0, 'jobs_analyzed': 0, 'jobs_saved': 0, 'jobs_failed': 0, 'jobs_duplicates': 0, 'errors': 0}

    def increment(self, key, value=1):
        self.stats[key] += value

    async def start(self):
        self.tasks = [
            asyncio.create_task(self._start_scraping()),
            asyncio.create_task(processing_stage(self.processing_queue, self.analysis_queue, self.metrics)),
            asyncio.create_task(analysis_stage(self.analysis_queue, self.storage_queue, self.metrics, self.analyzer, self.thread_pool)),
            asyncio.create_task(storage_stage(self.storage_queue, self.metrics, self.db, self.thread_pool)),
        ]
        await asyncio.gather(*self.tasks)

    async def _start_scraping(self):
        keywords = self.profile.get("keywords", [])
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            for keyword in keywords:
                await scrape_keyword(page, keyword, self.scraping_queue)
            await browser.close()

        # Signal end of scraping
        await self.processing_queue.put(None)

async def main():
    profile = {"keywords": ["python developer", "data analyst"]}
    config = {"max_workers": 4, "enable_ai_analysis": False}
    pipeline = ModernJobPipeline(profile, config)
    await pipeline.start()

if __name__ == "__main__":
    asyncio.run(main())
