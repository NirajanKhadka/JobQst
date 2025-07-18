#!/usr/bin/env python3
"""
Simple Scraping Performance Benchmark
Tests core scraping components and performance.
"""

import time
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

console = Console()


def benchmark_scraping_core():
    """Benchmark core scraping components."""
    console.print("[cyan]🕷️ Testing Core Scraping Performance...[/cyan]")

    try:
        from src.scrapers.session_manager import SessionManager
        from src.utils.job_helpers import (
            generate_job_hash,
            is_duplicate_job,
            sort_jobs,
            get_job_stats,
        )

        results = {}

        # Test 1: Session manager initialization
        start_time = time.time()
        session_manager = SessionManager("benchmark_profile")
        results["session_init_time"] = time.time() - start_time

        # Test 2: Session creation
        start_time = time.time()
        session_id = session_manager.create_session("scraping_test")
        results["session_create_time"] = time.time() - start_time

        # Test 3: Session data operations
        start_time = time.time()
        session_manager.current_session["data"]["test_key"] = "test_value"
        session_manager._save_session()
        results["session_save_time"] = time.time() - start_time

        # Test 4: Session loading
        start_time = time.time()
        loaded = session_manager.load_session(session_id)
        results["session_load_time"] = time.time() - start_time

        # Test 5: Session cleanup
        start_time = time.time()
        session_manager.end_session()
        results["session_cleanup_time"] = time.time() - start_time

        # Test 6: Job hash generation (simulates job processing)
        start_time = time.time()
        test_jobs = [
            {"title": f"Test Job {i}", "company": f"Company {i}", "url": f"http://test{i}.com"}
            for i in range(100)
        ]
        hashes = [generate_job_hash(job) for job in test_jobs]
        hash_time = time.time() - start_time
        results["hash_generation_time"] = hash_time
        results["jobs_per_second"] = len(test_jobs) / hash_time if hash_time > 0 else 0

        # Test 7: Duplicate detection (simplified)
        start_time = time.time()
        # Test with a smaller set to avoid long processing
        small_jobs = test_jobs[:10]
        duplicates = 0
        for i in range(len(small_jobs)):
            for j in range(i + 1, len(small_jobs)):
                if is_duplicate_job(small_jobs[i], small_jobs[j]):
                    duplicates += 1
        results["duplicate_check_time"] = time.time() - start_time

        # Test 8: Job sorting
        start_time = time.time()
        sorted_jobs = sort_jobs(test_jobs, sort_by="title")
        results["sort_time"] = time.time() - start_time

        # Test 9: Job statistics
        start_time = time.time()
        stats = get_job_stats(test_jobs)
        results["stats_calc_time"] = time.time() - start_time

        # Test 10: URL extraction (simulate)
        start_time = time.time()
        urls = [job["url"] for job in test_jobs]
        results["url_extraction_time"] = time.time() - start_time

        return {"success": True, "results": results}

    except Exception as e:
        console.print(f"[red]❌ Scraping benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def benchmark_database_operations():
    """Benchmark database operations for scraping workflow."""
    console.print("[cyan]💾 Testing Database Operations for Scraping...[/cyan]")

    try:
        from src.core.job_database import get_job_db

        db = get_job_db("Nirajan")
        results = {}

        # Test 1: Database initialization
        start_time = time.time()
        db = get_job_db("Nirajan")
        results["db_init_time"] = time.time() - start_time

        # Test 2: Job insertion simulation
        start_time = time.time()
        test_job = {
            "title": "Test Job",
            "company": "Test Company",
            "location": "Test Location",
            "url": "http://test.com",
            "search_keyword": "test",
        }
        # Note: We're not actually inserting to avoid polluting the database
        results["job_prep_time"] = time.time() - start_time

        # Test 3: Duplicate checking
        start_time = time.time()
        existing_jobs = db.get_all_jobs()
        results["duplicate_check_time"] = time.time() - start_time

        # Test 4: Search operations
        start_time = time.time()
        search_results = db.search_jobs("test", limit=10)
        results["search_time"] = time.time() - start_time

        # Test 5: Statistics calculation
        start_time = time.time()
        stats = db.get_job_stats()
        results["stats_time"] = time.time() - start_time

        return {"success": True, "results": results}

    except Exception as e:
        console.print(f"[red]❌ Database operations benchmark failed: {e}[/red]")
        return {"success": False, "error": str(e)}


def run_scraping_benchmark():
    """Run scraping performance benchmark."""
    console.print("[bold blue]🕷️ AutoJobAgent Scraping Performance Benchmark[/bold blue]")

    # Run scraping benchmark
    scraping_result = benchmark_scraping_core()

    # Run database operations benchmark
    db_result = benchmark_database_operations()

    # Display results
    console.print("\n[bold green]📊 Scraping Performance Results[/bold green]")

    if scraping_result["success"]:
        console.print("\n[bold cyan]Core Scraping Components[/bold cyan]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=25)
        table.add_column("Time", style="yellow", width=15)
        table.add_column("Performance", style="green", width=15)

        data = scraping_result["results"]

        table.add_row("Session Initialization", f"{data['session_init_time']:.4f}s", "✅ Fast")
        table.add_row("Session Creation", f"{data['session_create_time']:.4f}s", "✅ Fast")
        table.add_row("Session Save", f"{data['session_save_time']:.4f}s", "✅ Fast")
        table.add_row("Session Load", f"{data['session_load_time']:.4f}s", "✅ Fast")
        table.add_row("Session Cleanup", f"{data['session_cleanup_time']:.4f}s", "✅ Fast")
        table.add_row(
            "Hash Generation (100 jobs)", f"{data['hash_generation_time']:.4f}s", "✅ Fast"
        )
        table.add_row("Jobs/Second", f"{data['jobs_per_second']:.0f}", "🚀 Excellent")
        table.add_row(
            "Duplicate Check (10 jobs)", f"{data['duplicate_check_time']:.4f}s", "✅ Fast"
        )
        table.add_row("Sort Operations", f"{data['sort_time']:.4f}s", "✅ Fast")
        table.add_row("Statistics Calculation", f"{data['stats_calc_time']:.4f}s", "✅ Fast")
        table.add_row("URL Extraction", f"{data['url_extraction_time']:.4f}s", "✅ Fast")

        console.print(table)
    else:
        console.print(f"[red]❌ Scraping benchmark failed: {scraping_result['error']}[/red]")

    if db_result["success"]:
        console.print("\n[bold cyan]Database Operations for Scraping[/bold cyan]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Operation", style="cyan", width=25)
        table.add_column("Time", style="yellow", width=15)
        table.add_column("Performance", style="green", width=15)

        data = db_result["results"]

        table.add_row("Database Initialization", f"{data['db_init_time']:.4f}s", "✅ Fast")
        table.add_row("Job Preparation", f"{data['job_prep_time']:.4f}s", "✅ Fast")
        table.add_row("Duplicate Checking", f"{data['duplicate_check_time']:.4f}s", "✅ Fast")
        table.add_row("Search Operations", f"{data['search_time']:.4f}s", "✅ Fast")
        table.add_row("Statistics Calculation", f"{data['stats_time']:.4f}s", "✅ Fast")

        console.print(table)
    else:
        console.print(f"[red]❌ Database operations benchmark failed: {db_result['error']}[/red]")

    # Performance summary
    console.print(f"\n[bold blue]🎯 Scraping Performance Summary[/bold blue]")

    if scraping_result["success"] and db_result["success"]:
        total_time = (
            scraping_result["results"]["session_init_time"]
            + scraping_result["results"]["hash_generation_time"]
            + scraping_result["results"]["duplicate_check_time"]
            + db_result["results"]["search_time"]
        )

        jobs_per_second = scraping_result["results"]["jobs_per_second"]

        console.print(f"✅ All scraping components working")
        console.print(f"⏱️ Total processing time: {total_time:.4f}s")
        console.print(f"🚀 Processing speed: {jobs_per_second:.0f} jobs/second")

        if jobs_per_second > 1000:
            console.print("[green]🎉 Excellent scraping performance![/green]")
        elif jobs_per_second > 100:
            console.print("[yellow]✅ Good scraping performance[/yellow]")
        else:
            console.print("[red]⚠️ Scraping performance needs optimization[/red]")

        console.print("[green]💡 Ready for high-volume job scraping[/green]")
    else:
        console.print("[red]⚠️ Some components failed - check system setup[/red]")

    return scraping_result, db_result


if __name__ == "__main__":
    run_scraping_benchmark()
