"""
JobData and job data utilities for AutoJobAgent.
"""

import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class JobData:
    """Simple job data structure."""
    title: str
    company: str
    location: str = ""
    url: str = ""
    summary: str = ""
    salary: str = ""
    job_type: str = ""
    posted_date: str = ""
    site: str = ""
    search_keyword: str = ""
    scraped_at: str = ""
    raw_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def get_hash(self) -> str:
        """Generate hash for duplicate detection."""
        content = f"{self.title.lower()}{self.company.lower()}{self.url}"
        return hashlib.md5(content.encode()).hexdigest() 