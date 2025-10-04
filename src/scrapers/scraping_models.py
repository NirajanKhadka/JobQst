from dataclasses import dataclass
from typing import Dict, Optional, Any
from enum import Enum


class JobStatus(Enum):
    """Enum representing different job processing states."""

    PENDING = "pending"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    SAVED = "saved"
    FAILED = "failed"
    DUPLICATE = "duplicate"


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
    status: JobStatus = JobStatus.PENDING
    analysis_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert JobData to dictionary format."""
        return {
            "basic_info": self.basic_info,
            "detailed_info": self.detailed_info,
            "real_url": self.real_url,
            "experience_level": self.experience_level,
            "confidence_score": self.confidence_score,
            "needs_detail_scraping": self.needs_detail_scraping,
            "status": self.status.value if self.status else "pending",
            "analysis_data": self.analysis_data,
        }
