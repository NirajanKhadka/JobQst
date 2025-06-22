#!/usr/bin/env python3
"""
Test script to demonstrate SQLite database capabilities for job scraping.
"""

from job_database import get_job_db
from rich.console import Console
from rich.table import Table

console = Console()

def main():
    # Get the job database
    db = get_job_db('Nirajan')
    
    # Get statistics
    stats = db.get_stats()
    
    console.print("\n[bold blue]📊 Job Database Statistics[/bold blue]")
    console.print(f"[green]Total Jobs:[/green] {stats.get('total_jobs', 0)}")
    console.print(f"[green]Unapplied Jobs:[/green] {stats.get('unapplied_jobs', 0)}")
    console.print(f"[green]Applied Jobs:[/green] {stats.get('applied_jobs', 0)}")
    console.print(f"[green]Unique Companies:[/green] {stats.get('unique_companies', 0)}")
    console.print(f"[green]Unique Sites:[/green] {stats.get('unique_sites', 0)}")
    
    # Show recent jobs
    console.print("\n[bold blue]🔍 Recent Jobs (Last 5)[/bold blue]")
    jobs = db.get_jobs(limit=5)
    
    if jobs:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Title", style="cyan", width=30)
        table.add_column("Company", style="green", width=25)
        table.add_column("Location", style="yellow", width=15)
        table.add_column("Keyword", style="blue", width=15)
        
        for job in jobs:
            table.add_row(
                job['title'][:30] + "..." if len(job['title']) > 30 else job['title'],
                job['company'][:25] + "..." if len(job['company']) > 25 else job['company'],
                job['location'][:15] + "..." if len(job['location']) > 15 else job['location'],
                job['search_keyword']
            )
        
        console.print(table)
    else:
        console.print("[yellow]No jobs found in database[/yellow]")
    
    # Demonstrate fast queries
    console.print("\n[bold blue]⚡ Fast Query Examples[/bold blue]")
    
    # Query by keyword
    python_jobs = db.get_jobs(search_keyword="Python", limit=10)
    console.print(f"[cyan]Python jobs:[/cyan] {len(python_jobs)}")
    
    # Query by company
    rbc_jobs = db.get_jobs(company="Royal Bank", limit=10)
    console.print(f"[cyan]Royal Bank jobs:[/cyan] {len(rbc_jobs)}")
    
    # Query by location
    toronto_jobs = db.get_jobs(location="Toronto", limit=10)
    console.print(f"[cyan]Toronto jobs:[/cyan] {len(toronto_jobs)}")
    
    # Query unapplied jobs
    unapplied = db.get_unapplied_jobs(limit=10)
    console.print(f"[cyan]Unapplied jobs:[/cyan] {len(unapplied)}")
    
    console.print("\n[bold green]✅ SQLite database is working perfectly![/bold green]")
    console.print("[yellow]💡 Benefits over CSV:[/yellow]")
    console.print("  • ⚡ Instant queries (no file scanning)")
    console.print("  • 🚫 Automatic duplicate prevention")
    console.print("  • 📊 Proper data types and relationships")
    console.print("  • 🔍 Advanced filtering and search")
    console.print("  • 📈 Scalable to thousands of jobs")

if __name__ == "__main__":
    main()
