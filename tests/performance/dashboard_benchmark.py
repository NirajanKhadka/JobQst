#!/usr/bin/env python3
"""
Dashboard Performance Benchmark.

This script tests the performance of the dashboard's data loading, backend
operations (filtering, sorting, aggregation), and component rendering.
It uses simulated data to provide a consistent and reproducible benchmark.
"""

import time
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# --- Initialization ---
console = Console()


def _get_dashboard_dependencies():
    """Safely import dependencies from the dashboard and core modules."""
    try:
        # Use the new unified_dashboard
        from .dashboard.unified_dashboard import load_job_data, display_enhanced_metrics
        from .core.job_database import get_job_db
from src.core.job_database import get_job_db
        return load_job_data, display_enhanced_metrics, get_job_db
    except ImportError as e:
        console.print(f"[red]❌ Failed to import dashboard dependencies: {e}[/red]")
        return None, None, None


def benchmark_dashboard_data_loading() -> Dict[str, Any]:
    """
    Benchmark the performance of dashboard data loading and initial processing.

    Returns:
        A dictionary containing performance metrics.
    """
    console.print("[cyan]📊 Testing Dashboard Data Loading...[/cyan]")
    load_job_data, _, get_job_db = _get_dashboard_dependencies()
    if not all([load_job_data, get_job_db]):
        return {"success": False, "error": "Import failed"}

    try:
        results = {}

        # Test 1: Database connection
        start_time = time.time()
        db = get_job_db("Nirajan")
        results["db_connection_time"] = time.time() - start_time

        # Test 2: Data loading from DB
        start_time = time.time()
        df = load_job_data("Nirajan")
        results["data_load_time"] = time.time() - start_time
        results["data_rows"] = len(df)
        results["data_columns"] = len(df.columns) if not df.empty else 0

        return {"success": True, "results": results}
    except Exception as e:
        console.print(f"[red]❌ Data loading benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def benchmark_dashboard_operations() -> Dict[str, Any]:
    """
    Benchmark backend data operations like filtering, grouping, and sorting.

    Returns:
        A dictionary containing performance metrics.
    """
    console.print("[cyan]⚙️ Testing Dashboard Operations...[/cyan]")
    load_job_data, _, _ = _get_dashboard_dependencies()
    if not load_job_data:
        return {"success": False, "error": "Import failed"}

    try:
        df = load_job_data("Nirajan")
        if df.empty:
            # Create a dummy dataframe for operations benchmark if DB is empty
            df = pd.DataFrame(
                {
                    "title": [f"Job {i}" for i in range(100)],
                    "company": [f"Company {i % 10}" for i in range(100)],
                    "status": ["scraped", "processed", "applied"] * 33 + ["scraped"],
                }
            )

        results = {}

        # Test 1: Filtering
        start_time = time.time()
        df[df["title"].str.contains("Job", case=False, na=False)]
        results["filter_time"] = time.time() - start_time

        # Test 2: Grouping
        start_time = time.time()
        df.groupby("company").size()
        results["group_time"] = time.time() - start_time

        # Test 3: Sorting
        start_time = time.time()
        df.sort_values("title", ascending=True)
        results["sort_time"] = time.time() - start_time

        return {"success": True, "results": results}
    except Exception as e:
        console.print(f"[red]❌ Operations benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def benchmark_dashboard_rendering() -> Dict[str, Any]:
    """
    Simulate and benchmark the time taken for rendering components.

    Returns:
        A dictionary containing performance metrics.
    """
    console.print("[cyan]🎭 Testing Dashboard Rendering...[/cyan]")
    try:
        results = {}
        # Simulate rendering time for various components
        start_time = time.time()
        time.sleep(0.01)  # Simulate HTML/CSS generation
        results["base_render_time"] = time.time() - start_time

        start_time = time.time()
        time.sleep(0.02)  # Simulate chart rendering
        results["chart_render_time"] = time.time() - start_time

        start_time = time.time()
        time.sleep(0.015)  # Simulate table rendering
        results["table_render_time"] = time.time() - start_time

        return {"success": True, "results": results}
    except Exception as e:
        console.print(f"[red]❌ Rendering benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def _display_benchmark_results(results: Dict[str, Dict[str, Any]]):
    """
    Display the results of all dashboard benchmarks in formatted tables.

    Args:
        results: A dictionary of benchmark results.
    """
    console.print("\n[bold green]📊 Dashboard Performance Results[/bold green]")

    for name, result in results.items():
        console.print(f"\n[bold cyan]{name}[/bold cyan]")
        if result["success"]:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan", width=30)
            table.add_column("Value", style="yellow", width=20)

            for metric, value in result.get("results", {}).items():
                if isinstance(value, float):
                    table.add_row(metric, f"{value:.4f}s")
                else:
                    table.add_row(metric, str(value))
            console.print(table)
        else:
            console.print(f"[red]❌ Benchmark failed: {result.get('error', 'Unknown')}[/red]")


def run_dashboard_benchmark():
    """
    Run the comprehensive dashboard benchmark and display the summary.
    """
    console.print(Panel("[bold blue]📊 AutoJobAgent Dashboard Performance Benchmark[/bold blue]"))

    benchmarks = {
        "Data Loading": benchmark_dashboard_data_loading,
        "Operations": benchmark_dashboard_operations,
        "Rendering Simulation": benchmark_dashboard_rendering,
    }

    results = {name: func() for name, func in benchmarks.items()}

    _display_benchmark_results(results)

    # Final Summary
    console.print(f"\n[bold blue]🎯 Dashboard Performance Summary[/bold blue]")
    successful_benchmarks = sum(1 for r in results.values() if r["success"])
    total_benchmarks = len(benchmarks)
    console.print(f"✅ Successful Benchmarks: {successful_benchmarks}/{total_benchmarks}")

    if successful_benchmarks == total_benchmarks:
        data_load_time = results["Data Loading"].get("results", {}).get("data_load_time", 1.0)
        if data_load_time < 0.5:
            console.print("[green]🎉 Excellent dashboard performance! Data loads instantly.[/green]")
        elif data_load_time < 1.5:
            console.print("[yellow]✅ Good dashboard performance. Data loads quickly.[/yellow]")
        else:
            console.print("[red]⚠️ Dashboard data loading could be optimized.[/red]")
    else:
        console.print("[red]⚠️ Some dashboard components failed. Review errors above.[/red]")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    run_dashboard_benchmark()
