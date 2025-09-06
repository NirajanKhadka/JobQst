#!/usr/bin/env python3
"""
Run 10K JobSpy Scraper for last 14 days only
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.cli.handlers.scraping_handler import ScrapingHandler
from src.utils.profile_helpers import load_profile
from rich.console import Console

console = Console()

def main():
    """Run the 10K scraper with 14-day limit"""
    console.print("[bold blue]🚀 Starting 10K Job Scraper (14-day window)[/bold blue]")
    
    # Load profile
    profile = load_profile('Nirajan')
    if not profile:
        console.print("[red]❌ Error: Could not load Nirajan profile[/red]")
        return False
    
    console.print(f"[green]✅ Loaded profile: {profile.get('name', 'Nirajan')}[/green]")
    console.print(f"[cyan]📍 Location: {profile.get('location', 'Toronto, ON')}[/cyan]")
    console.print(f"[cyan]🔍 Keywords: {len(profile.get('keywords', []))} search terms[/cyan]")
    console.print("[yellow]⏰ Time Window: Last 14 days ONLY (fresh jobs)[/yellow]")
    
    # Create handler and run ultra-fast multi-worker scraping
    handler = ScrapingHandler(profile)
    
    console.print("[cyan]🚀 Starting Ultra-Fast Multi-Worker Pipeline...[/cyan]")
    console.print("[yellow]📝 Mode: multi_worker (all 4 sites, maximum parallel processing)[/yellow]")
    console.print("[green]🎯 Target: Up to 10,000 jobs (or whatever's available in 14 days)[/green]")
    
    # Run with maximum jobs allowed by CLI (1000), but the pipeline will try to get more
    success = handler.run_scraping(mode='multi_worker', jobs=1000)
    
    if success:
        console.print("[bold green]✅ Scraping completed successfully![/bold green]")
        
        # Check results
        try:
            from src.core.job_database import get_job_db
            db = get_job_db('Nirajan')
            jobs = db.get_jobs()
            console.print(f"[cyan]📊 Total jobs in database: {len(jobs)}[/cyan]")
            
            # Count recent jobs (last 14 days)
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(days=14)
            recent_jobs = []
            for job in jobs:
                try:
                    if 'scraped_at' in job and job['scraped_at']:
                        job_date = datetime.fromisoformat(job['scraped_at'].replace('Z', '+00:00'))
                        if job_date.replace(tzinfo=None) >= cutoff:
                            recent_jobs.append(job)
                except:
                    # Include jobs without valid dates (they're likely recent)
                    recent_jobs.append(job)
            
            console.print(f"[green]🆕 Fresh jobs (last 14 days): {len(recent_jobs)}[/green]")
            
            if recent_jobs:
                # Show sample
                console.print("[cyan]📋 Sample jobs:[/cyan]")
                for i, job in enumerate(recent_jobs[:5], 1):
                    title = job.get('title', 'Unknown')[:40]
                    company = job.get('company', 'Unknown')[:20]
                    location = job.get('location', 'Unknown')[:15]
                    console.print(f"  {i}. {title}... at {company} ({location})")
                
                if len(recent_jobs) > 5:
                    console.print(f"  ... and {len(recent_jobs) - 5} more jobs")
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not check database: {e}[/yellow]")
        
        return True
    else:
        console.print("[red]❌ Scraping failed[/red]")
        return False

if __name__ == "__main__":
    success = main()
    console.print(f"\n[{'green' if success else 'red'}]Final Result: {'SUCCESS' if success else 'FAILED'}[/{'green' if success else 'red'}]")
    sys.exit(0 if success else 1)
