#!/usr/bin/env python3
"""
Test script with a new keyword to verify extraction improvements.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from job_database import get_job_db
import utils

console = Console()

def test_new_keyword():
    """Test extraction with a new keyword to avoid duplicates."""
    
    console.print(Panel("🧪 Testing New Keyword Extraction", style="bold cyan"))
    
    try:
        # Load profile
        profile = utils.load_profile('Nirajan')
        if not profile:
            console.print("[red]❌ Could not load Nirajan profile[/red]")
            return False
            
        console.print(f"[green]✅ Loaded profile: {profile['profile_name']}[/green]")
        
        # Get initial database stats
        db = get_job_db(profile['profile_name'])
        initial_stats = db.get_stats()
        console.print(f"[cyan]📊 Initial database stats: {initial_stats['total_jobs']} jobs[/cyan]")
        
        # Test scraping with a new keyword to avoid duplicates
        console.print("[cyan]🔍 Testing with new keyword 'Business Analyst'...[/cyan]")
        
        from scrapers.eluta_enhanced import ElutaEnhancedScraper
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            
            # Create scraper with new keyword
            test_profile = profile.copy()
            test_profile["keywords"] = ["Business Analyst"]  # New keyword
            
            scraper = ElutaEnhancedScraper(test_profile, browser_context=context, deep_scraping=False)
            scraper.max_pages_per_keyword = 1  # Just test 1 page
            
            console.print("[cyan]🚀 Starting test scraping with new keyword...[/cyan]")
            jobs = list(scraper.scrape_jobs())
            browser.close()
        
        console.print(f"[green]✅ Scraping complete! Found {len(jobs)} jobs[/green]")
        
        if jobs:
            # Show sample jobs
            console.print("[cyan]📋 Sample extracted jobs:[/cyan]")
            for i, job in enumerate(jobs[:5], 1):
                console.print(f"  {i}. {job['title']} at {job['company']}")
                console.print(f"     URL: {job['url'][:60]}...")
            
            # Save jobs to database
            console.print(f"[cyan]💾 Saving {len(jobs)} jobs to database...[/cyan]")
            saved_count = 0
            duplicate_count = 0
            
            for job in jobs:
                if db.add_job(job):
                    saved_count += 1
                else:
                    duplicate_count += 1
            
            console.print(f"[green]💾 Saved {saved_count} new jobs to database ({duplicate_count} duplicates skipped)[/green]")
            
            # Get final database stats
            final_stats = db.get_stats()
            console.print(f"[cyan]📊 Final database stats: {final_stats['total_jobs']} jobs[/cyan]")
            
            # Calculate improvement
            jobs_added = final_stats['total_jobs'] - initial_stats['total_jobs']
            console.print(f"[bold green]🎉 Successfully added {jobs_added} new jobs to database![/bold green]")
            
            return True
        else:
            console.print("[yellow]⚠️ No jobs were extracted[/yellow]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Error during test: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_new_keyword()
