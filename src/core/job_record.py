"""
JobRecord dataclass and related utilities for job database operations.
"""

import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class JobRecord:
    """Comprehensive job record structure with detailed tracking."""

    title: str
    company: str
    location: str = ""
    summary: str = ""
    url: str = ""
    search_keyword: str = ""
    site: str = "unknown"
    scraped_at: str = ""
    job_id: str = ""

    # Status tracking
    status: str = "scraped"  # scraped, processed, applied
    applied: int = 0
    application_status: str = "not_applied"  # not_applied, applied, pending, accepted, rejected

    # Job details
    experience_level: str = ""
    keywords: str = ""
    job_description: str = ""
    salary_range: str = ""
    job_type: str = ""  # full-time, part-time, contract, etc.
    remote_option: str = ""
    requirements: str = ""
    benefits: str = ""

    # Analysis and matching
    match_score: float = 0.0
    processing_notes: str = ""
    application_date: str = ""

    # Raw data
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

    def update_status(self, new_status: str):
        """Update job status."""
        self.status = new_status
        if new_status == "applied":
            self.applied = 1
            self.application_date = datetime.now().isoformat()

    def set_match_score(self, score: float):
        """Set match score."""
        self.match_score = max(0.0, min(100.0, score))

    def add_processing_note(self, note: str):
        """Add processing note."""
        if self.processing_notes:
            self.processing_notes += f"\n{datetime.now().strftime('%Y-%m-%d %H:%M')}: {note}"
        else:
            self.processing_notes = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {note}"
