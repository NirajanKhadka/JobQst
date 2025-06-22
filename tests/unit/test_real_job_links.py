#!/usr/bin/env python3
"""
Test Real Job Links
Test script to verify we're filtering out Eluta jobs and only using real job links.
"""

import asyncio
import sys
from pathlib import Path

# Add project root and src directory to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# Import modules with correct paths
from src.ats.enhanced_application_agent import EnhancedApplicationAgent
from src.core.job_database import get_job_db

console = Console()

async def test_job_link_filtering():
    """Test job link filtering to ensure we skip Eluta and use real links."""
    
    console.print(Panel.fit("🔍 TESTING REAL JOB LINK FILTERING", style="bold blue"))
    
    profile_name = "Nirajan"
    
    # Initialize agent
    agent = EnhancedApplicationAgent(profile_name)
    if not await agent.initialize():
        console.print("[red]❌ Failed to initialize agent[/red]")
        return
    
    # Get all jobs from database
    db = get_job_db(profile_name)
    all_jobs = db.get_unapplied_jobs(limit=50)
    
    console.print(f"[cyan]📋 Total jobs in database: {len(all_jobs)}[/cyan]")
    
    # Analyze job URLs
    eluta_jobs = []
    real_jobs = []
    other_jobs = []
    
    for job in all_jobs:
        url = job.get('url', '').lower()
        
        if any(eluta_pattern in url for eluta_pattern in [
            'eluta.ca', 'sandbox', 'destination=', 'eluta.com'
        ]):
            eluta_jobs.append(job)
        elif any(real_pattern in url for real_pattern in [
            'workday.com', 'greenhouse.io', 'lever.co', 'bamboohr.com',
            'smartrecruiters.com', 'jobvite.com', 'icims.com', 'taleo.net',
            'careers.', 'jobs.', '.com/careers', '.com/jobs', '.ca/careers', '.ca/jobs'
        ]):
            real_jobs.append(job)
        else:
            other_jobs.append(job)
    
    # Display analysis
    console.print(f"\n[bold]📊 JOB URL ANALYSIS:[/bold]")
    
    analysis_table = Table(title="Job URL Categories")
    analysis_table.add_column("Category", style="cyan")
    analysis_table.add_column("Count", style="green")
    analysis_table.add_column("Percentage", style="yellow")
    
    total = len(all_jobs)
    analysis_table.add_row("Eluta Jobs", str(len(eluta_jobs)), f"{(len(eluta_jobs)/total)*100:.1f}%")
    analysis_table.add_row("Real Job Links", str(len(real_jobs)), f"{(len(real_jobs)/total)*100:.1f}%")
    analysis_table.add_row("Other URLs", str(len(other_jobs)), f"{(len(other_jobs)/total)*100:.1f}%")
    analysis_table.add_row("Total", str(total), "100.0%")
    
    console.print(analysis_table)
    
    # Show sample Eluta jobs (to confirm they're being filtered)
    if eluta_jobs:
        console.print(f"\n[yellow]⚠️ ELUTA JOBS (WILL BE SKIPPED):[/yellow]")
        eluta_table = Table()
        eluta_table.add_column("Title", style="red", max_width=30)
        eluta_table.add_column("Company", style="red", max_width=25)
        eluta_table.add_column("URL", style="dim", max_width=50)
        
        for job in eluta_jobs[:5]:  # Show first 5
            url = job.get('url', '')
            display_url = url[:47] + "..." if len(url) > 50 else url
            eluta_table.add_row(
                job.get('title', 'Unknown'),
                job.get('company', 'Unknown'),
                display_url
            )
        
        console.print(eluta_table)
        if len(eluta_jobs) > 5:
            console.print(f"[dim]... and {len(eluta_jobs) - 5} more Eluta jobs[/dim]")
    
    # Show sample real jobs (these will be processed)
    if real_jobs:
        console.print(f"\n[green]✅ REAL JOB LINKS (WILL BE PROCESSED):[/green]")
        real_table = Table()
        real_table.add_column("Title", style="green", max_width=30)
        real_table.add_column("Company", style="green", max_width=25)
        real_table.add_column("URL", style="cyan", max_width=50)
        
        for job in real_jobs[:5]:  # Show first 5
            url = job.get('url', '')
            display_url = url[:47] + "..." if len(url) > 50 else url
            real_table.add_row(
                job.get('title', 'Unknown'),
                job.get('company', 'Unknown'),
                display_url
            )
        
        console.print(real_table)
        if len(real_jobs) > 5:
            console.print(f"[dim]... and {len(real_jobs) - 5} more real job links[/dim]")
    
    # Show other jobs for review
    if other_jobs:
        console.print(f"\n[cyan]📋 OTHER URLS (NEED REVIEW):[/cyan]")
        other_table = Table()
        other_table.add_column("Title", style="yellow", max_width=30)
        other_table.add_column("Company", style="yellow", max_width=25)
        other_table.add_column("URL", style="dim", max_width=50)
        
        for job in other_jobs[:5]:  # Show first 5
            url = job.get('url', '')
            display_url = url[:47] + "..." if len(url) > 50 else url
            other_table.add_row(
                job.get('title', 'Unknown'),
                job.get('company', 'Unknown'),
                display_url
            )
        
        console.print(other_table)
        if len(other_jobs) > 5:
            console.print(f"[dim]... and {len(other_jobs) - 5} more other URLs[/dim]")
    
    # Test the filtering function
    console.print(f"\n[bold]🧪 TESTING FILTERING FUNCTION:[/bold]")
    filtered_jobs = agent._filter_real_job_links(all_jobs, limit=10)
    
    console.print(f"[green]✅ Filtering test completed![/green]")
    console.print(f"[green]Real jobs found: {len(filtered_jobs)}/10 requested[/green]")
    
    # Recommendations
    console.print(f"\n[bold]💡 RECOMMENDATIONS:[/bold]")
    
    if len(eluta_jobs) > len(real_jobs):
        console.print("[yellow]⚠️ Most jobs are Eluta redirects - consider scraping different sources[/yellow]")
    
    if len(real_jobs) >= 10:
        console.print("[green]✅ Sufficient real job links available for applications[/green]")
        
        if Confirm.ask("Would you like to test applying to real jobs only?"):
            console.print("[cyan]🚀 Starting application test with real jobs only...[/cyan]")
            
            # Test with 2 real jobs
            results = await agent.process_job_applications(
                limit=2,
                enhance_jobs=True,
                modify_documents=True
            )
            
            console.print(f"[green]✅ Application test completed: {len(results)} jobs processed[/green]")
    else:
        console.print(f"[yellow]⚠️ Only {len(real_jobs)} real job links available - may need more job sources[/yellow]")


async def show_job_url_samples():
    """Show samples of different job URL types."""
    console.print(Panel.fit("📋 JOB URL SAMPLES", style="bold cyan"))
    
    db = get_job_db("Nirajan")
    jobs = db.get_unapplied_jobs(limit=20)
    
    console.print("[bold]Sample Job URLs:[/bold]")
    for i, job in enumerate(jobs[:10]):
        url = job.get('url', '')
        title = job.get('title', 'Unknown')
        
        # Categorize URL
        if 'eluta.ca' in url.lower():
            category = "[red]ELUTA[/red]"
        elif any(pattern in url.lower() for pattern in ['workday', 'greenhouse', 'lever', 'careers', 'jobs']):
            category = "[green]REAL[/green]"
        else:
            category = "[yellow]OTHER[/yellow]"
        
        console.print(f"{i+1:2d}. {category} {title[:40]:<40} {url[:60]}")


if __name__ == "__main__":
    console.print("1. 🔍 Test Job Link Filtering")
    console.print("2. 📋 Show Job URL Samples")
    
    choice = Prompt.ask("Select option", choices=["1", "2"], default="1")
    
    if choice == "1":
        asyncio.run(test_job_link_filtering())
    elif choice == "2":
        asyncio.run(show_job_url_samples())
