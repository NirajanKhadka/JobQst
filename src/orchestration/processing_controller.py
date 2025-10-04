from __future__ import annotations

import asyncio
from typing import List, Dict, Any

from rich.console import Console

from src.analysis.two_stage_processor import get_two_stage_processor, TwoStageResult
from .types import OrchestratorConfig

console = Console()


async def _process_in_batches(
    jobs: List[Dict[str, Any]], cpu_workers: int, max_concurrent_stage2: int, batch_size: int
) -> List[TwoStageResult]:
    """Process jobs in bounded batches using the Two-Stage Processor."""
    from math import ceil

    processor = get_two_stage_processor(
        {"profile_name": "auto"},
        cpu_workers=cpu_workers,
        max_concurrent_stage2=max_concurrent_stage2,
    )

    total = len(jobs)
    if total == 0:
        return []

    all_results: List[TwoStageResult] = []
    batches = ceil(total / batch_size)

    for i in range(0, total, batch_size):
        batch = jobs[i : i + batch_size]
        results = await processor.process_jobs(batch)
        all_results.extend(results)
        del results

    return all_results


def run_processing_batches(
    jobs: List[Dict[str, Any]], cfg: OrchestratorConfig
) -> List[TwoStageResult]:
    """Synchronous facade to process jobs according to config."""

    async def _runner():
        return await _process_in_batches(
            jobs,
            cpu_workers=cfg.cpu_workers,
            max_concurrent_stage2=cfg.max_concurrent_stage2,
            batch_size=cfg.batch_size,
        )

    try:
        return asyncio.run(_runner())
    except RuntimeError:
        return asyncio.get_event_loop().run_until_complete(_runner())
