import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class ScrapingMetrics:
    """Metrics for tracking scraping performance."""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_jobs_found: int = 0
    unique_jobs_added: int = 0
    duplicates_filtered: int = 0
    errors_encountered: int = 0
    sites_scraped: int = 0
    keywords_processed: int = 0
    average_jobs_per_keyword: float = 0.0
    scraping_rate_per_minute: float = 0.0
    data_quality_score: float = 0.0
    keyword_performance: Dict[str, Dict] = field(default_factory=dict)

    def finalize(self):
        self.end_time = time.time()
        duration_minutes = (self.end_time - self.start_time) / 60
        if self.keywords_processed > 0:
            self.average_jobs_per_keyword = self.unique_jobs_added / self.keywords_processed
        if duration_minutes > 0:
            self.scraping_rate_per_minute = self.unique_jobs_added / duration_minutes
        if self.unique_jobs_added > 0:
            total_quality = sum(p.get('avg_quality_score', 0) * p.get('total_jobs_processed', 0) for p in self.keyword_performance.values())
            self.data_quality_score = total_quality / self.unique_jobs_added

    def update_batch_metrics(self, keywords: List[str], raw_jobs: List[Dict], processed_jobs: List[Dict]):
        self.total_jobs_found += len(raw_jobs)
        self.keywords_processed += len(keywords)
        for keyword in keywords:
            keyword_jobs = [j for j in raw_jobs if j.get('search_keyword') == keyword]
            keyword_processed = [j for j in processed_jobs if j.get('search_keyword') == keyword]
            
            if keyword not in self.keyword_performance:
                self.keyword_performance[keyword] = {'total_attempts': 0, 'total_jobs_found': 0, 'total_jobs_processed': 0}
            
            perf = self.keyword_performance[keyword]
            perf['total_attempts'] += 1
            perf['total_jobs_found'] += len(keyword_jobs)
            perf['total_jobs_processed'] += len(keyword_processed)