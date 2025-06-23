"""
JobRecord dataclass and related utilities for job database operations.
"""

import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class JobRecord:
    """Simple job record structure."""
    title: str
    company: str
    location: str = ""
    summary: str = ""
    url: str = ""
    search_keyword: str = ""
    site: str = "unknown"
    scraped_at: str = ""
    job_id: str = ""
    raw_data: Optional[Dict[str, Any]] = None
    analysis_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}
        if self.analysis_data is None:
            self.analysis_data = {}
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()
        if not self.job_id:
            self.job_id = self._generate_job_id()
    
    def _generate_job_id(self) -> str:
        """Generate a unique job ID."""
        content = f"{self.title}{self.company}{self.url}{self.scraped_at}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def get_hash(self) -> str:
        """Get hash for duplicate detection."""
        content = f"{self.title.lower()}{self.company.lower()}"
        return hashlib.md5(content.encode()).hexdigest() 