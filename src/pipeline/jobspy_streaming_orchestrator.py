#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobSpy → Two-Stage Processor Orchestrator (streaming batches with backpressure)

- Runs multi-site JobSpy workers in parallel
- Optionally enriches missing descriptions asynchronously
- Streams jobs into TwoStageJobProcessor in bounded batches to keep memory stable

Usage (example):

    from src.pipeline.jobspy_streaming_orchestrator import run_jobspy_to_two_stage

    results = asyncio.run(run_jobspy_to_two_stage(
        profile_name="Nirajan",
        location_set="canada_comprehensive",
        query_preset="comprehensive",
        sites=["indeed", "linkedin", "glassdoor"],
        max_jobs_per_site_location=80,
        per_site_concurrency=4,
        max_total_jobs=2200,
        batch_size=250,
        cpu_workers=12,
        max_concurrent_stage2=2,
        fetch_descriptions=True,
        description_fetch_concurrency=24
    ))
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from src.scrapers.multi_site_jobspy_workers import MultiSiteJobSpyWorkers
from src.analysis.two_stage_processor import get_two_stage_processor, TwoStageResult
from src.utils.profile_helpers import load_profile

console = Console()


@dataclass
class OrchestratorConfig:
    # Discovery
    location_set: str = "canada_comprehensive"
    query_preset: str = "comprehensive"
    sites: Optional[List[str]] = None  # defaults to all
    max_jobs_per_site_location: int = 80  # results_wanted
    per_site_concurrency: int = 4
    max_total_jobs: Optional[int] = 2200  # early stop per site

    # Enrichment
    fetch_descriptions: bool = True
    description_fetch_concurrency: int = 24

    # Processing
    batch_size: int = 250
    cpu_workers: int = 12
    max_concurrent_stage2: int = 2


def _df_to_job_dicts(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert JobSpy DataFrame rows into processor-friendly dicts."""
    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        rec = {
            "id": str(row.get("job_id") or row.get("id") or row.get("job_url") or ""),
            "title": row.get("title", ""),
            "company": row.get("company", ""),
            "location": row.get("location", ""),
            "description": row.get("description", ""),
            "url": row.get("job_url", ""),
            "source_site": row.get("source_site", "jobspy"),
            "search_term": row.get("search_term", ""),
            "search_location": row.get("search_location", ""),
            "date_posted": row.get("date_posted", ""),
            "compensation": row.get("compensation", ""),
        }
        records.append(rec)
    return records


async def _process_in_batches(jobs: List[Dict[str, Any]], cpu_workers: int, max_concurrent_stage2: int, batch_size: int) -> List[TwoStageResult]:
    """Process jobs in bounded batches to keep memory stable."""
    from math import ceil

    processor = get_two_stage_processor({"profile_name": "auto"}, cpu_workers=cpu_workers, max_concurrent_stage2=max_concurrent_stage2)

    total = len(jobs)
    if total == 0:
        return []

    all_results: List[TwoStageResult] = []
    batches = ceil(total / batch_size)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing batches...", total=batches)
        for i in range(0, total, batch_size):
            batch = jobs[i : i + batch_size]
            # Stage 1 + Stage 2 (internally batched/concurrent)
            results = await processor.process_jobs(batch)
            all_results.extend(results)
            # Explicitly drop references before next loop step
            del results
            progress.advance(task)

    return all_results


async def run_jobspy_to_two_stage(
    profile_name: str = "Nirajan",
    location_set: str = "canada_comprehensive",
    query_preset: str = "comprehensive",
    sites: Optional[List[str]] = None,
    max_jobs_per_site_location: int = 80,
    per_site_concurrency: int = 4,
    max_total_jobs: Optional[int] = 2200,
    batch_size: int = 250,
    cpu_workers: int = 12,
    max_concurrent_stage2: int = 2,
    fetch_descriptions: bool = True,
    description_fetch_concurrency: int = 24,
) -> List[TwoStageResult]:
    """End-to-end: discover with JobSpy, optionally enrich, then process in batches.

    Returns TwoStageResult list so callers can summarize/save as needed.
    """
    profile = load_profile(profile_name) or {"profile_name": profile_name}

    # Step 1: Discover
    workers = MultiSiteJobSpyWorkers(profile_name, max_jobs_per_site_location, per_site_concurrency)
    ms_result = await workers.run_comprehensive_search(
        location_set=location_set,
        query_preset=query_preset,
        sites=sites,
        per_site_concurrency=per_site_concurrency,
        max_total_jobs=max_total_jobs,
    )
    df = ms_result.combined_data

    # Step 2: Optional enrichment
    if fetch_descriptions and isinstance(df, pd.DataFrame) and not df.empty:
        try:
            df = await workers.run_optimized_description_fetching(df, max_concurrency=description_fetch_concurrency)
        except Exception as e:
            console.print(f"[yellow]Description enrichment failed: {e}[/yellow]")

    if df is None or df.empty:
        console.print("[yellow]No jobs to process after discovery/enrichment[/yellow]")
        return []

    # Step 3: Stream to processor in batches
    jobs = _df_to_job_dicts(df)
    results = await _process_in_batches(jobs, cpu_workers=cpu_workers, max_concurrent_stage2=max_concurrent_stage2, batch_size=batch_size)
    return results
