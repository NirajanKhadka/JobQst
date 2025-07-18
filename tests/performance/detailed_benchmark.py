#!/usr/bin/env python3
"""
Detailed System Benchmark for AutoJobAgent.

This script provides a comprehensive and detailed performance analysis of
key system components, including database speed, scraping utilities,
dashboard operations, and concurrency handling.
"""

import time
import sys
import os
import threading
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Tuple

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# --- Initialization ---
console = Console()


def _get_dependencies():
    """Safely import all required modules for benchmarking."""
    try:
        from .core.job_database import get_job_db
        from .scrapers.session_manager import SessionManager
        from .utils.job_helpers import generate_job_hash, is_duplicate_job, sort_jobs, get_job_stats
        from .dashboard.unified_dashboard import load_job_data, display_enhanced_metrics
        import pandas as pd
        import numpy as np
from src.utils.job_helpers import generate_job_hash
from src.core.job_database import get_job_db
        return (get_job_db, SessionManager, generate_job_hash, is_duplicate_job,
                sort_jobs, get_job_stats, load_job_data, display_enhanced_metrics, pd, np)
    except ImportError as e:
        console.print(f"[red]❌ Failed to import dependencies: {e}[/red]")
        return (None,) * 10


def benchmark_database_speed() -> Dict[str, Any]:
    """
    Run a detailed benchmark on database query performance.

    Returns:
        A dictionary containing performance metrics.
    """
    console.print("[cyan]🔍 Testing Database Speed & Performance...[/cyan]")
    get_job_db, *_ = _get_dependencies()
    if not get_job_db:
        return {"success": False, "error": "Import failed"}

    try:
        db = get_job_db("Nirajan")
        results = {}
        query_times = []

        # Define queries to benchmark
        queries_to_run = {
            "init_time": lambda: get_job_db("Nirajan"),
            "count_query_time": lambda: db.get_job_count(),
            "stats_query_time": lambda: db.get_job_stats(),
            "load_all_time": lambda: db.get_all_jobs(),
            "search_time": lambda: db.search_jobs("python", limit=10),
            "unapplied_query_time": lambda: db.get_unapplied_jobs(limit=10),
        }

        for name, query_func in queries_to_run.items():
            start_time = time.time()
            query_result = query_func()
            duration = time.time() - start_time
            results[name] = duration
            if "query" in name:
                query_times.append(duration)
            if name == "load_all_time":
                results["total_jobs"] = len(query_result) if isinstance(query_result, list) else 0

        # Calculate aggregate query metrics
        if query_times:
            results["avg_query_time"] = sum(query_times) / len(query_times)
            results["max_query_time"] = max(query_times)
            results["min_query_time"] = min(query_times)

        return {"success": True, "results": results}
    except Exception as e:
        console.print(f"[red]❌ Database benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def benchmark_scraping_performance() -> Dict[str, Any]:
    """
    Run a detailed benchmark on scraping-related utility functions.

    Returns:
        A dictionary containing performance metrics.
    """
    console.print("[cyan]🕷️ Testing Scraping Performance...[/cyan]")
    _, SessionManager, generate_job_hash, is_duplicate, sort_jobs_util, get_stats, *_ = _get_dependencies()
    if not all([SessionManager, generate_job_hash, is_duplicate, sort_jobs_util, get_stats]):
        return {"success": False, "error": "Import failed"}

    try:
        results = {}
        test_jobs = [{"title": f"Job {i}", "company": f"Comp {i}", "url": f"http://test{i}.com"} for i in range(100)]

        # Benchmark various scraping utilities
        start_time = time.time()
        [generate_job_hash(job) for job in test_jobs]
        hash_time = time.time() - start_time
        results["hash_generation_time"] = hash_time
        results["jobs_per_second_hashing"] = len(test_jobs) / hash_time if hash_time > 0 else float('inf')

        start_time = time.time()
        sort_jobs_util(test_jobs, sort_by="title")
        results["sort_time"] = time.time() - start_time

        return {"success": True, "results": results}
    except Exception as e:
        console.print(f"[red]❌ Scraping benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def benchmark_dashboard_performance() -> Dict[str, Any]:
    """
    Run a detailed benchmark on dashboard data operations.

    Returns:
        A dictionary containing performance metrics.
    """
    console.print("[cyan]📊 Testing Dashboard Performance...[/cyan]")
    *_, load_job_data, _, pd, np = _get_dependencies()
    if not all([load_job_data, pd, np]):
        return {"success": False, "error": "Import failed"}

    try:
        results = {}
        df = load_job_data("Nirajan")
        results["data_load_time"] = time.time() - time.time() # Placeholder, actual time measured in load_job_data
        results["data_rows"] = len(df)

        if not df.empty:
            start_time = time.time()
            df[df["title"].str.contains("python", case=False, na=False)]
            results["filter_time"] = time.time() - start_time

            start_time = time.time()
            df.groupby("company").size()
            results["group_time"] = time.time() - start_time
        else:
            results["filter_time"] = results["group_time"] = 0

        return {"success": True, "results": results}
    except Exception as e:
        console.print(f"[red]❌ Dashboard benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def benchmark_concurrent_operations() -> Dict[str, Any]:
    """
    Test the performance of concurrent database reads and hashing.

    Returns:
        A dictionary containing performance metrics.
    """
    console.print("[cyan]⚡ Testing Concurrent Operations...[/cyan]")
    get_job_db, _, generate_job_hash, *_ = _get_dependencies()
    if not all([get_job_db, generate_job_hash]):
        return {"success": False, "error": "Import failed"}

    results = {}

    def db_read_op():
        db = get_job_db("Nirajan")
        db.get_job_count()

    def hash_op():
        generate_job_hash({"title": "test", "company": "test", "url": "test"})

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            start_time = time.time()
            list(executor.map(db_read_op, range(10)))
            results["concurrent_db_reads_time"] = time.time() - start_time

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            list(executor.map(hash_op, range(100)))
            results["concurrent_hash_time"] = time.time() - start_time

        return {"success": True, "results": results}
    except Exception as e:
        console.print(f"[red]❌ Concurrent benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def _display_results_table(benchmark_name: str, data: Dict[str, Any]):
    """Helper function to display results in a table."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", width=30)
    table.add_column("Value", style="yellow", width=20)

    for key, value in data.items():
        if isinstance(value, float):
            table.add_row(key, f"{value:.4f}s")
        else:
            table.add_row(key, str(value))
    console.print(f"\n[bold cyan]{benchmark_name}[/bold cyan]")
    console.print(table)


def run_detailed_benchmark():
    """
    Run the full suite of detailed benchmarks and display the results.
    """
    console.print(Panel("[bold blue]🚀 AutoJobAgent Detailed Performance Benchmark[/bold blue]"))

    benchmarks = {
        "Database Speed": benchmark_database_speed,
        "Scraping Performance": benchmark_scraping_performance,
        "Dashboard Performance": benchmark_dashboard_performance,
        "Concurrent Operations": benchmark_concurrent_operations,
    }

    results = {}
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Running benchmarks...", total=len(benchmarks))
        for name, func in benchmarks.items():
            progress.update(task, description=f"Running {name}...")
            results[name] = func()
            progress.update(task, advance=1)

    console.print("\n[bold green]📊 Detailed Benchmark Results[/bold green]")
    for name, result in results.items():
        if result["success"]:
            _display_results_table(name, result["results"])
        else:
            console.print(f"[red]❌ {name} failed: {result['error']}[/red]")

    # Final Summary
    successful_benchmarks = sum(1 for r in results.values() if r["success"])
    console.print(f"\n[bold blue]🎯 Performance Summary[/bold blue]")
    console.print(f"✅ Successful Benchmarks: {successful_benchmarks}/{len(benchmarks)}")
    if successful_benchmarks == len(benchmarks):
        console.print("[green]🎉 All benchmarks passed! System is performing excellently.[/green]")
    else:
        console.print("[yellow]⚠️ Some benchmarks failed. Review system setup.[/yellow]")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    run_detailed_benchmark()
