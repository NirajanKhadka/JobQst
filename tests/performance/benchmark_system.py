#!/usr/bin/env python3
"""
Comprehensive System Benchmark for AutoJobAgent.

This script tests all major components of the AutoJobAgent and provides
a detailed report on their performance, helping to identify bottlenecks
and ensure system readiness.
"""

import time
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# --- Constants ---
BENCHMARK_COMPONENTS = [
    "database",
    "dashboard",
    "scraping",
    "ats",
    "utils"
]

# --- Initialization ---
console = Console()


def benchmark_database() -> Dict[str, Any]:
    """
    Benchmark database operations, including initialization and queries.

    Returns:
        A dictionary containing performance metrics for the database.
    """
    console.print("[cyan]🔍 Testing Database Performance...[/cyan]")
    try:
        from .core.job_database import get_job_db

        start_time = time.time()
        db = get_job_db("Nirajan")
        init_time = time.time() - start_time

        start_time = time.time()
        job_count = db.get_job_count()
        count_time = time.time() - start_time

        start_time = time.time()
        stats = db.get_job_stats()
        stats_time = time.time() - start_time

        start_time = time.time()
        db.get_all_jobs()
        load_time = time.time() - start_time

        return {
            "init_time": init_time,
            "count_time": count_time,
            "stats_time": stats_time,
            "load_time": load_time,
            "job_count": job_count,
            "success": True,
        }
    except Exception as e:
        console.print(f"[red]❌ Database benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def benchmark_dashboard() -> Dict[str, Any]:
    """
    Benchmark dashboard data loading and metric calculation.

    Returns:
        A dictionary containing performance metrics for the dashboard.
    """
    console.print("[cyan]📊 Testing Dashboard Performance...[/cyan]")
    try:
        from .dashboard.unified_dashboard import load_job_data, calculate_metrics

        start_time = time.time()
        # Pass a profile name to load_job_data
        df = load_job_data("Nirajan")
        load_time = time.time() - start_time

        start_time = time.time()
        calculate_metrics(df)
        metrics_time = time.time() - start_time

        return {
            "load_time": load_time,
            "metrics_time": metrics_time,
            "data_rows": len(df),
            "success": True,
        }
    except Exception as e:
        console.print(f"[red]❌ Dashboard benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def benchmark_scraping() -> Dict[str, Any]:
    """
    Benchmark scraping session management.

    Returns:
        A dictionary containing performance metrics for scraping components.
    """
    console.print("[cyan]🕷️ Testing Scraping Components...[/cyan]")
    try:
        from .scrapers.session_manager import SessionManager

        start_time = time.time()
        session_manager = SessionManager()
        init_time = time.time() - start_time

        start_time = time.time()
        session_manager.create_session("benchmark_test")
        session_time = time.time() - start_time

        start_time = time.time()
        session_manager.end_session()
        close_time = time.time() - start_time

        return {
            "init_time": init_time,
            "session_time": session_time,
            "close_time": close_time,
            "success": True,
        }
    except Exception as e:
        console.print(f"[red]❌ Scraping benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def benchmark_ats() -> Dict[str, Any]:
    """
    Benchmark ATS detection utilities.

    Returns:
        A dictionary containing performance metrics for ATS components.
    """
    console.print("[cyan]📝 Testing ATS Components...[/cyan]")
    try:
        from .ats.ats_utils import detect_ats_system

        start_time = time.time()
        test_url = "https://myworkdayjobs.com/test"
        detect_ats_system(test_url)
        detect_time = time.time() - start_time

        return {"detect_time": detect_time, "success": True}
    except Exception as e:
        console.print(f"[red]❌ ATS benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def benchmark_utils() -> Dict[str, Any]:
    """
    Benchmark core utility functions like hashing and file operations.

    Returns:
        A dictionary containing performance metrics for utility functions.
    """
    console.print("[cyan]🛠️ Testing Utility Functions...[/cyan]")
    try:
        from .utils.job_helpers import generate_job_hash
        from .utils.file_operations import save_jobs_to_json
from src.utils.file_operations import save_jobs_to_json
from src.utils.job_helpers import generate_job_hash
from src.core.job_database import get_job_db

        start_time = time.time()
        generate_job_hash(
            {"title": "test job", "company": "test company", "url": "test location"}
        )
        hash_time = time.time() - start_time

        start_time = time.time()
        test_jobs = [{"title": "Test Job", "company": "Test Company"}]
        output_file = "test_benchmark.json"
        save_jobs_to_json(test_jobs, output_file)
        file_time = time.time() - start_time

        # Clean up the created file
        if os.path.exists(output_file):
            os.remove(output_file)

        return {"hash_time": hash_time, "file_time": file_time, "success": True}
    except Exception as e:
        console.print(f"[red]❌ Utils benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def _run_all_benchmarks() -> Dict[str, Dict[str, Any]]:
    """
    Execute all benchmark tests and collect their results.

    Returns:
        A dictionary mapping component names to their benchmark results.
    """
    results = {}
    benchmark_map = {
        "database": benchmark_database,
        "dashboard": benchmark_dashboard,
        "scraping": benchmark_scraping,
        "ats": benchmark_ats,
        "utils": benchmark_utils,
    }

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:
        task = progress.add_task("Running benchmarks...", total=len(BENCHMARK_COMPONENTS))
        for name in BENCHMARK_COMPONENTS:
            progress.update(task, description=f"Benchmarking {name}...")
            results[name] = benchmark_map[name]()
            progress.update(task, advance=1)
    return results


def _format_database_results(result: Dict[str, Any]) -> Tuple[str, str, float]:
    """Format database benchmark results for display."""
    perf = f"{result['init_time']:.3f}s"
    details = f"{result['job_count']} jobs, {result['load_time']:.3f}s load"
    total_time = result["init_time"] + result["load_time"]
    return perf, details, total_time


def _format_dashboard_results(result: Dict[str, Any]) -> Tuple[str, str, float]:
    """Format dashboard benchmark results for display."""
    perf = f"{result['load_time']:.3f}s"
    details = f"{result['data_rows']} rows, {result['metrics_time']:.3f}s metrics"
    total_time = result["load_time"] + result["metrics_time"]
    return perf, details, total_time


def _format_scraping_results(result: Dict[str, Any]) -> Tuple[str, str, float]:
    """Format scraping benchmark results for display."""
    perf = f"{result['session_time']:.3f}s"
    details = f"Session init: {result['init_time']:.3f}s"
    total_time = result["init_time"] + result["session_time"]
    return perf, details, total_time


def _format_ats_results(result: Dict[str, Any]) -> Tuple[str, str, float]:
    """Format ATS benchmark results for display."""
    perf = f"{result['detect_time']:.3f}s"
    details = "ATS detection"
    total_time = result["detect_time"]
    return perf, details, total_time


def _format_utils_results(result: Dict[str, Any]) -> Tuple[str, str, float]:
    """Format utils benchmark results for display."""
    perf = f"{result['hash_time']:.3f}s"
    details = f"Hash: {result['hash_time']:.3f}s, File: {result['file_time']:.3f}s"
    total_time = result["hash_time"] + result["file_time"]
    return perf, details, total_time


def _display_results_table(results: Dict[str, Dict[str, Any]]) -> float:
    """
    Display the benchmark results in a formatted table.

    Args:
        results: The dictionary of benchmark results.

    Returns:
        The total time taken for all successful benchmarks.
    """
    console.print("\n[bold green]📊 Benchmark Results[/bold green]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan", width=15)
    table.add_column("Status", style="green", width=10)
    table.add_column("Performance", style="yellow", width=20)
    table.add_column("Details", style="blue", width=30)

    total_time = 0.0
    successful_components = 0

    formatters = {
        "database": _format_database_results,
        "dashboard": _format_dashboard_results,
        "scraping": _format_scraping_results,
        "ats": _format_ats_results,
        "utils": _format_utils_results,
    }

    for component, result in results.items():
        if result["success"]:
            status = "✅ PASS"
            successful_components += 1
            perf, details, component_time = formatters[component](result)
            total_time += component_time
        else:
            status = "❌ FAIL"
            perf = "N/A"
            details = result.get("error", "Unknown error")
        table.add_row(component.upper(), status, perf, details)

    console.print(table)
    return total_time, successful_components


def _display_summary_and_recommendations(total_time: float, successful_components: int):
    """
    Display the overall summary and performance recommendations.

    Args:
        total_time: The total benchmark time.
        successful_components: The number of components that passed.
    """
    console.print(f"\n[bold blue]🎯 Overall Performance Summary[/bold blue]")
    console.print(f"✅ Successful Components: {successful_components}/{len(BENCHMARK_COMPONENTS)}")
    console.print(f"⏱️ Total Benchmark Time: {total_time:.3f}s")

    if successful_components == len(BENCHMARK_COMPONENTS):
        if total_time < 1.0:
            score, color = "EXCELLENT", "green"
        elif total_time < 2.0:
            score, color = "GOOD", "yellow"
        else:
            score, color = "FAIR", "red"
        console.print(f"[{color}]🎯 Performance Score: {score}[/{color}]")
        console.print(f"[{color}]💡 System is ready for production use![/{color}]")
    else:
        console.print("[red]⚠️ Some components failed - check system setup[/red]")

    console.print(f"\n[bold cyan]💡 Recommendations[/bold cyan]")
    if total_time > 2.0:
        console.print("• Consider optimizing database queries and dashboard data loading.")
        console.print("• Review scraping performance for potential bottlenecks.")
    else:
        console.print("• System performance is optimal. All components are working efficiently.")


def run_comprehensive_benchmark():
    """
    Run the comprehensive system benchmark and display the results.
    """
    console.print(Panel("[bold blue]🚀 AutoJobAgent Comprehensive System Benchmark[/bold blue]"))
    results = _run_all_benchmarks()
    total_time, successful_components = _display_results_table(results)
    _display_summary_and_recommendations(total_time, successful_components)


if __name__ == "__main__":
    # Ensure the script can find the 'src' module
    # This is necessary when running the script directly
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    run_comprehensive_benchmark()
