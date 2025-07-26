#!/usr/bin/env python3
"""
Test Verified Job Processor
Tests the new job processor that only marks jobs as processed when all fields are verified
"""

import sys
import time
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.dashboard.verified_job_processor import get_verified_job_processor
from src.core.job_database import get_job_db
from src.utils.job_verifier import get_job_verifier
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def analyze_current_database():
    """Analyze the current database to show job completeness."""
    console.print(Panel.fit("[bold blue]Database Analysis[/bold blue]", title="Starting Analysis"))
    
    db = get_job_db("Nirajan")
    verifier = get_job_verifier()
    
    all_jobs = db.get_all_jobs()
    console.print(f"[blue]📊 Total jobs in database: {len(all_jobs)}[/blue]")
    
    # Analyze job completeness
    complete_jobs = 0
    incomplete_jobs = 0
    status_counts = {}
    missing_field_counts = {}
    
    for job in all_jobs:
        # Count statuses
        status = job.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Verify completeness
        verification = verifier.verify_job_completeness(job)
        
        if verification['is_complete']:
            complete_jobs += 1
        else:
            incomplete_jobs += 1
            
            # Count missing fields
            for field in verification['missing_required']:
                missing_field_counts[field] = missing_field_counts.get(field, 0) + 1
    
    # Create status table
    status_table = Table(title="Job Status Distribution")
    status_table.add_column("Status", style="cyan")
    status_table.add_column("Count", style="magenta")
    status_table.add_column("Percentage", style="green")
    
    for status, count in status_counts.items():
        percentage = (count / len(all_jobs)) * 100
        status_table.add_row(status, str(count), f"{percentage:.1f}%")
    
    console.print(status_table)
    
    # Create completeness table
    completeness_table = Table(title="Job Completeness Analysis")
    completeness_table.add_column("Category", style="cyan")
    completeness_table.add_column("Count", style="magenta")
    completeness_table.add_column("Percentage", style="green")
    
    complete_pct = (complete_jobs / len(all_jobs)) * 100
    incomplete_pct = (incomplete_jobs / len(all_jobs)) * 100
    
    completeness_table.add_row("✅ Complete Jobs", str(complete_jobs), f"{complete_pct:.1f}%")
    completeness_table.add_row("❌ Incomplete Jobs", str(incomplete_jobs), f"{incomplete_pct:.1f}%")
    
    console.print(completeness_table)
    
    # Show most common missing fields
    if missing_field_counts:
        missing_table = Table(title="Most Common Missing Fields")
        missing_table.add_column("Field", style="cyan")
        missing_table.add_column("Missing Count", style="red")
        
        sorted_missing = sorted(missing_field_counts.items(), key=lambda x: x[1], reverse=True)
        for field, count in sorted_missing[:5]:
            missing_table.add_row(field, str(count))
        
        console.print(missing_table)
    
    return {
        'total_jobs': len(all_jobs),
        'complete_jobs': complete_jobs,
        'incomplete_jobs': incomplete_jobs,
        'status_counts': status_counts,
        'missing_field_counts': missing_field_counts
    }

def test_verified_processor():
    """Test the verified job processor."""
    console.print(Panel.fit("[bold green]Testing Verified Job Processor[/bold green]", title="Test Start"))
    
    # Analyze database first
    analysis = analyze_current_database()
    if analysis['incomplete_jobs'] == 0:
        console.print("[green]✅ All jobs are already complete! No processing needed.[/green]")
        return
    # Initialize processor
    processor = get_verified_job_processor("Nirajan")
    console.print(f"[cyan]Processor initialized: {processor}[cyan]")
    # Start processor
    started = processor.start_processing()
    console.print(f"[cyan]Processor started: {started}[cyan]")
    if not started:
        console.print("[red]❌ Failed to start processor[/red]")
        return
    # Add jobs for verification
    # Add only one job for verification (for testing)
    all_jobs = analyze_current_database()['total_jobs']
    # Get one incomplete job
    db = get_job_db("Nirajan")
    verifier = get_job_verifier()
    jobs_added = 0
    for job in db.get_all_jobs():
        verification = verifier.verify_job_completeness(job)
        if not verification['is_complete']:
            processor.add_jobs_for_verification([job])
            jobs_added = 1
            break
    console.print(f"[cyan]Jobs added for verification: {jobs_added}[cyan]")
    if jobs_added == 0:
        console.print("[yellow]⚠️ No jobs added for processing[/yellow]")
        processor.stop_processing()
        return
    console.print(f"[blue]🔄 Processing {jobs_added} job...[blue]")
    # Monitor processing
    start_time = time.time()
    last_stats = None
    max_wait_time = 300  # seconds
    try:
        while True:
            stats = processor.get_processing_stats()
            # Show progress if stats changed
            if stats != last_stats:
                processed = stats['processing_stats']['total_jobs']
                complete = stats['processing_stats']['verified_complete']
                needs_processing = stats['processing_stats']['needs_processing']
                failed = stats['processing_stats']['failed_scraping']
                queue_size = stats['queue_size']
                elapsed = time.time() - start_time
                console.print(f"[blue]📊 Progress: {processed}/{jobs_added} | ✅ Complete: {complete} | 🔄 Needs Work: {needs_processing} | ❌ Failed: {failed} | Queue: {queue_size} | Time: {elapsed:.1f}s[blue]")
                last_stats = stats
            # Check if processing is complete
            if stats['queue_size'] == 0 and stats['processing_stats']['total_jobs'] >= jobs_added:
                console.print("[green]✅ Processing complete![green]")
                break
            if time.time() - start_time > max_wait_time:
                console.print("[red]❌ Processing timed out after 5 minutes. Check for stuck jobs or processor issues.[/red]")
                break
            time.sleep(3)  # Check every 3 seconds
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Processing interrupted by user[/yellow]")
    
    # Stop processor
    processor.stop_processing()
    
    # Show final statistics
    processor.print_stats_summary()
    
    # Re-analyze database to show improvements
    console.print(Panel.fit("[bold blue]Post-Processing Analysis[/bold blue]", title="Results"))
    final_analysis = analyze_current_database()
    
    # Show improvement
    improvement = final_analysis['complete_jobs'] - analysis['complete_jobs']
    if improvement > 0:
        console.print(f"[green]🎉 Improved {improvement} jobs from incomplete to complete![/green]")
    else:
        console.print("[yellow]⚠️ No jobs were improved. Check processing logs for issues.[/yellow]")

def show_sample_incomplete_jobs():
    """Show sample incomplete jobs for debugging."""
    console.print(Panel.fit("[bold yellow]Sample Incomplete Jobs[/bold yellow]", title="Debug Info"))
    
    db = get_job_db("Nirajan")
    verifier = get_job_verifier()
    
    all_jobs = db.get_all_jobs()
    incomplete_jobs = []
    
    for job in all_jobs:
        verification = verifier.verify_job_completeness(job)
        if not verification['is_complete']:
            incomplete_jobs.append({
                'job': job,
                'verification': verification
            })
    
    # Show first 5 incomplete jobs
    for i, item in enumerate(incomplete_jobs[:5]):
        job = item['job']
        verification = item['verification']
        
        console.print(f"\n[bold]Job {i+1} (ID: {job.get('id')})[/bold]")
        console.print(f"URL: {job.get('url', 'N/A')[:60]}...")
        console.print(f"Title: {job.get('title', 'N/A')}")
        console.print(f"Company: {job.get('company', 'N/A')}")
        console.print(f"Status: {job.get('status', 'N/A')}")
        console.print(f"Missing Required: {verification['missing_required']}")
        console.print(f"Missing Important: {verification['missing_important']}")
        console.print(f"Completion Score: {verification['completion_score']:.2f}")

if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold blue]Verified Job Processor Test[/bold blue]\n\n"
        "This test will:\n"
        "1. Analyze current database completeness\n"
        "2. Process incomplete jobs with proper verification\n"
        "3. Only mark jobs as 'processed' when ALL required fields are filled\n"
        "4. Use proper tab management during scraping\n"
        "5. Show before/after comparison",
        title="Test Overview"
    ))
    
    # Show sample incomplete jobs first
    show_sample_incomplete_jobs()
    
    # Ask user if they want to proceed
    proceed = input("\nDo you want to start processing incomplete jobs? (y/n): ")
    
    if proceed.lower() in ['y', 'yes']:
        test_verified_processor()
    else:
        console.print("[yellow]Test cancelled by user[/yellow]")