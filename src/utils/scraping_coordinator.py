from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console

from src.core.job_database import get_job_db
from src.scraping.cache import ScrapingCache
from src.scraping.metrics import ScrapingMetrics
# Assuming a generic scraper interface
from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper

console = Console()

class OptimizedScrapingCoordinator:
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        self.cache = ScrapingCache(profile_name)
        self.metrics = ScrapingMetrics()
        self.max_concurrent_scrapers = 3

    def scrape_optimized(self, keywords: List[str], sites: List[str] = None) -> List[Dict]:
        if sites is None:
            sites = ['eluta']
        
        all_jobs = []
        with ThreadPoolExecutor(max_workers=self.max_concurrent_scrapers) as executor:
            future_to_keyword = {executor.submit(self._scrape_single_keyword, keyword, site): keyword for keyword in keywords for site in sites}
            
            for future in as_completed(future_to_keyword):
                keyword = future_to_keyword[future]
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                except Exception as exc:
                    console.print(f"{keyword} generated an exception: {exc}")

        processed_jobs = self._process_job_batch(all_jobs)
        self.metrics.finalize()
        self.cache.save_cache(self.metrics.__dict__)
        return processed_jobs

    def _scrape_single_keyword(self, keyword: str, site: str) -> List[Dict]:
        profile = {'keywords': [keyword]} # Simplified profile
        scraper = ComprehensiveElutaScraper(profile)
        return list(scraper.scrape_jobs())

    def _process_job_batch(self, jobs: List[Dict]) -> List[Dict]:
        processed_jobs = []
        for job in jobs:
            if not self.cache.is_url_processed(job.get('url', '')):
                # Simplified processing
                self.db.add_job(job)
                self.cache.add_processed_url(job.get('url', ''))
                processed_jobs.append(job)
        return processed_jobs

def run_optimized_scraping(profile_name: str, keywords: List[str]):
    coordinator = OptimizedScrapingCoordinator(profile_name)
    coordinator.scrape_optimized(keywords)

if __name__ == '__main__':
    run_optimized_scraping("Nirajan", ["python developer", "data analyst"])
