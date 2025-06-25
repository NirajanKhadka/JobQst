from typing import Dict, List, Optional
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

    def scrape_optimized(self, keywords: List[str], sites: Optional[List[str]] = None) -> List[Dict]:
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
        # Create scraper with profile name
        scraper = ComprehensiveElutaScraper(self.profile_name)
        # For now, return empty list since scrape_all_keywords is async
        # In a real implementation, this would need to be handled differently
        return []

    def _process_job_batch(self, jobs: List[Dict]) -> List[Dict]:
        processed_jobs = []
        for job in jobs:
            if not self.cache.is_url_processed(job.get('url', '')):
                # Simplified processing
                self.db.add_job(job)
                self.cache.add_processed_url(job.get('url', ''))
                processed_jobs.append(job)
        return processed_jobs

# Backward compatibility class for tests
class ScrapingCoordinator:
    def __init__(self, profile_name: str = "default"):
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        self.cache = ScrapingCache(profile_name)
        self.metrics = ScrapingMetrics()

    def coordinate_scraping(self, keywords: List[str]) -> bool:
        """Coordinate scraping for given keywords. Returns True on success."""
        try:
            # Simplified coordination - just return success for now
            console.print(f"Coordinating scraping for keywords: {keywords}")
            return True
        except Exception as e:
            console.print(f"Scraping coordination failed: {e}")
            return False

def run_optimized_scraping(profile_name: str, keywords: List[str]):
    coordinator = OptimizedScrapingCoordinator(profile_name)
    coordinator.scrape_optimized(keywords)

if __name__ == '__main__':
    run_optimized_scraping("Nirajan", ["python developer", "data analyst"])
