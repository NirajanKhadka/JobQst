from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class OrchestratorConfig:
    # Discovery
    location_set: str = "canada_comprehensive"
    query_preset: str = "comprehensive"
    sites: Optional[List[str]] = None  # defaults to all
    max_jobs_per_site_location: int = 80
    per_site_concurrency: int = 4
    max_total_jobs: Optional[int] = 2200

    # Enrichment
    fetch_descriptions: bool = True
    description_fetch_concurrency: int = 24

    # Processing
    batch_size: int = 250
    cpu_workers: int = 12
    max_concurrent_stage2: int = 2


@dataclass
class DiscoveryResult:
    total_jobs: int
    dataframe_summary: Dict[str, Any]

