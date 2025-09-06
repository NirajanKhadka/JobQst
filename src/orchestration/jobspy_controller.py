from __future__ import annotations

import asyncio
from typing import List, Dict, Any, Optional

import pandas as pd
from rich.console import Console

from src.pipeline.jobspy_streaming_orchestrator import (
    OrchestratorConfig as PipelineConfig,
    run_jobspy_to_two_stage,
)
from .types import OrchestratorConfig, DiscoveryResult

console = Console()


async def run_jobspy_discovery_async(cfg: OrchestratorConfig, profile_name: str) -> pd.DataFrame:
    """Run JobSpy discovery and optional enrichment, returning a DataFrame."""
    # Map to pipeline function expecting separate params
    df_results = await _discover_only(
        profile_name=profile_name,
        location_set=cfg.location_set,
        query_preset=cfg.query_preset,
        sites=cfg.sites,
        max_jobs_per_site_location=cfg.max_jobs_per_site_location,
        per_site_concurrency=cfg.per_site_concurrency,
        max_total_jobs=cfg.max_total_jobs,
        fetch_descriptions=cfg.fetch_descriptions,
        description_fetch_concurrency=cfg.description_fetch_concurrency,
    )
    return df_results


async def _discover_only(
    profile_name: str,
    location_set: str,
    query_preset: str,
    sites: Optional[List[str]],
    max_jobs_per_site_location: int,
    per_site_concurrency: int,
    max_total_jobs: Optional[int],
    fetch_descriptions: bool,
    description_fetch_concurrency: int,
) -> pd.DataFrame:
    """Reuse pipeline orchestrator to run discovery + enrichment only, return DataFrame."""
    # We reuse the orchestrator but pull intermediate DF before processing
    from src.scrapers.multi_site_jobspy_workers import MultiSiteJobSpyWorkers

    workers = MultiSiteJobSpyWorkers(profile_name, max_jobs_per_site_location, per_site_concurrency)
    ms_result = await workers.run_comprehensive_search(
        location_set=location_set,
        query_preset=query_preset,
        sites=sites,
        per_site_concurrency=per_site_concurrency,
        max_total_jobs=max_total_jobs,
    )
    df = ms_result.combined_data

    if fetch_descriptions and isinstance(df, pd.DataFrame) and not df.empty:
        try:
            df = await workers.run_optimized_description_fetching(df, max_concurrency=description_fetch_concurrency)
        except Exception as e:
            console.print(f"[yellow]Description enrichment failed: {e}[/yellow]")

    return df if isinstance(df, pd.DataFrame) else pd.DataFrame()


def run_jobspy_discovery(cfg: OrchestratorConfig, profile_name: str) -> DiscoveryResult:
    """Synchronous wrapper for discovery so dashboard can call without managing event loops."""
    df: pd.DataFrame
    try:
        df = asyncio.run(run_jobspy_discovery_async(cfg, profile_name))
    except RuntimeError:
        # If already in an event loop (e.g., Streamlit), run nested via create_task
        df = asyncio.get_event_loop().run_until_complete(run_jobspy_discovery_async(cfg, profile_name))

    summary = {
        "rows": len(df),
        "columns": list(df.columns) if not df.empty else [],
        "sites": df["source_site"].unique().tolist() if "source_site" in df.columns else [],
    }
    return DiscoveryResult(total_jobs=len(df), dataframe_summary=summary)

