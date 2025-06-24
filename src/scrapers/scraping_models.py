from dataclasses import dataclass
from typing import Dict, Optional, Any

@dataclass
class ScrapingTask:
    """
    Represents an individual scraping task for the parallel job scraper system.
    """
    task_id: str
    task_type: str  # 'basic_scrape', 'detail_scrape', 'url_extract'
    keyword: str
    page_number: int
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class JobData:
    """
    Enhanced job data structure for storing scraped job information and metadata.
    """
    basic_info: Dict[str, Any]
    detailed_info: Optional[Dict[str, Any]] = None
    real_url: Optional[str] = None
    experience_level: str = "Unknown"
    confidence_score: float = 0.0
    needs_detail_scraping: bool = False 