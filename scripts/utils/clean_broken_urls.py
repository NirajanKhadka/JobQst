#!/usr/bin/env python3
"""
Clean Broken URLs - Remove obviously broken job URLs from database
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.job_database import get_job_db
from src.utils.simple_url_filter import get_simple_url_filter
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def clean_broken_urls():
    """Clean broken URLs from the database."""
    console.print(Panel.fit("[bold blue]Cleaning Broken Job URLs[/bold blue]", title="URL Cleanup"))
    
    db = get_job_db("Nirajan")
    url_filter = get_simple_url_filter()
    
    # Get all jobs
    all_jobs = db.get_all_jobs()
    console.print(f"[blue]📊 Checking {len(all_jobs)} jobs...[/blue]")
    
    # Filter jobs
    valid_jobs, invalid_jobs = url_filter.filter_jobs(all_jobs)
    
    console.print(f"[green]✅ Valid URLs: {len(valid_jobs)}[/green]")
    console.print(f"[red]❌ Invalid URLs: {len(invalid_jobs)}[/red]")
    
    if not invalid_jobs:
        console.print("[green]🎉 No broken URLs found![/green]")
        return
    
    # Show invalid URL samples
    console.print("\n[bold red]Invalid URLs found:[/bold red]")
    
    invalid_table = Table(title="Broken URLs")
    invalid_table.add_column("ID", style="cyan")
    invalid_table.add_column("URL", style="red")
    invalid_table.add_column("Reason", style="yellow")
    invalid_table.add_column("Title", style="magenta")
    
    for job in invalid_jobs[:10]:  # Show first 10
        job_id = str(job.get('id', 'N/A'))
        url = job.get('url', 'No URL')
        title = job.get('title', 'No title')
        reason = url_filter.get_invalid_reason(url)
        
        # Truncate long URLs
        display_url = url[:50] + "..." if len(url) > 50 else url
        display_title = title[:30] + "..." if len(title) > 30 else title
        
        invalid_table.add_row(job_id, display_url, reason, display_title)
    
    console.print(invalid_table)
    
    if len(invalid_jobs) > 10:
        console.print(f"[yellow]... and {len(invalid_jobs) - 10} more invalid URLs[/yellow]")
    
    # Show breakdown by reason
    reason_counts = {}
    for job in invalid_jobs:
        url = job.get('url', '')
        reason = url_filter.get_invalid_reason(url)
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    console.print("\n[bold]Breakdown by reason:[/bold]")
    for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
        console.print(f"  • {reason}: {count} URLs")
    
    # Ask user what to do
    console.print(f"\n[yellow]⚠️ Found {len(invalid_jobs)} broken URLs[/yellow]")
    console.print("\nOptions:")
    console.print("1. Delete all broken URLs")
    console.print("2. Mark as 'invalid_url' status")
    console.print("3. Show details only (no changes)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        # Delete broken URLs
        console.print(f"[red]🗑️ Deleting {len(invalid_jobs)} broken URLs...[/red]")
        
        deleted_count = 0
        for job in invalid_jobs:
            job_id = job.get('id')
            if job_id:
                try:
                    success = db.delete_job(job_id)
                    if success:
                        deleted_count += 1
                except Exception as e:
                    console.print(f"[red]Error deleting job {job_id}: {e}[/red]")
        
        console.print(f"[green]✅ Deleted {deleted_count} broken URLs[/green]")
        
        # Show final stats
        remaining_jobs = db.get_all_jobs()
        console.print(f"[blue]📊 Jobs remaining in database: {len(remaining_jobs)}[/blue]")
        
    elif choice == "2":
        # Mark as invalid
        console.print(f"[yellow]🏷️ Marking {len(invalid_jobs)} URLs as invalid...[/yellow]")
        
        marked_count = 0
        for job in invalid_jobs:
            job_id = job.get('id')
            if job_id:
                try:
                    url = job.get('url', '')
                    reason = url_filter.get_invalid_reason(url)
                    
                    update_data = {
                        'status': 'invalid_url',
                        'processing_notes': f"Invalid URL: {reason}"
                    }
                    
                    success = db.update_job(job_id, update_data)
                    if success:
                        marked_count += 1
                except Exception as e:
                    console.print(f"[red]Error updating job {job_id}: {e}[/red]")
        
        console.print(f"[green]✅ Marked {marked_count} URLs as invalid[/green]")
        
    else:
        console.print("[blue]ℹ️ No changes made - analysis only[/blue]")
    
    # Show some valid URL examples
    if valid_jobs:
        console.print("\n[bold green]Examples of valid URLs:[/bold green]")
        for job in valid_jobs[:5]:
            url = job.get('url', '')
            title = job.get('title', 'No title')
            console.print(f"  ✅ {url}")
            console.print(f"     Title: {title}")

def main():
    """Main function."""
    console.print(Panel.fit(
        "[bold blue]Broken URL Cleaner[/bold blue]\n\n"
        "This tool identifies and removes broken job URLs like:\n"
        "• https://www.eluta.ca/job/1\n"
        "• https://www.eluta.ca/job/2\n"
        "• Other obviously invalid URLs\n\n"
        "Valid URLs like Bombardier, Workday, etc. will be preserved.",
        title="URL Cleanup"
    ))
    
    clean_broken_urls()
    
    console.print("\n[green]✅ URL cleanup complete![/green]")

if __name__ == "__main__":
    main()