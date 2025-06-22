#!/usr/bin/env python3
"""
Test the improved job filtering logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from job_database import get_job_db
import utils

console = Console()

def test_improved_filtering():
    """Test the improved job filtering logic."""
    
    console.print(Panel("🧪 Testing Improved Job Filtering", style="bold cyan"))
    
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
        
        # Test scraping with a completely new keyword
        console.print("[cyan]🔍 Testing with new keyword 'Software Engineer'...[/cyan]")
        
        from scrapers.eluta_enhanced import ElutaEnhancedScraper
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            
            # Create scraper with new keyword
            test_profile = profile.copy()
            test_profile["keywords"] = ["Software Engineer"]  # New keyword
            
            scraper = ElutaEnhancedScraper(test_profile, browser_context=context, deep_scraping=False)
            scraper.max_pages_per_keyword = 1  # Just test 1 page
            
            console.print("[cyan]🚀 Starting test scraping with improved filtering...[/cyan]")
            jobs = list(scraper.scrape_jobs())
            browser.close()
        
        console.print(f"[green]✅ Scraping complete! Found {len(jobs)} jobs[/green]")
        
        if jobs:
            # Analyze job quality
            console.print("[cyan]📋 Analyzing job quality:[/cyan]")
            
            real_jobs = 0
            questionable_jobs = 0
            
            for i, job in enumerate(jobs, 1):
                title = job['title']
                company = job['company']
                
                # Check if this looks like a real job
                questionable_indicators = [
                    'full-time (', 'part-time (', 'canada\'s top', 'advertise your',
                    'dismiss', 'giving back', 'equity is good', 'questrade team',
                    'computing -', 'finance/banking'
                ]
                
                is_questionable = any(indicator in title.lower() for indicator in questionable_indicators)
                
                if is_questionable:
                    console.print(f"  ❌ {i}. {title} at {company} [QUESTIONABLE]")
                    questionable_jobs += 1
                else:
                    console.print(f"  ✅ {i}. {title} at {company} [REAL JOB]")
                    real_jobs += 1
            
            console.print(f"\n[cyan]📊 Quality Analysis:[/cyan]")
            console.print(f"[green]✅ Real jobs: {real_jobs}[/green]")
            console.print(f"[red]❌ Questionable jobs: {questionable_jobs}[/red]")
            
            if real_jobs > 0:
                quality_rate = (real_jobs / len(jobs)) * 100
                console.print(f"[cyan]📈 Quality rate: {quality_rate:.1f}%[/cyan]")
                
                if quality_rate >= 80:
                    console.print("[bold green]🎉 EXCELLENT quality rate![/bold green]")
                elif quality_rate >= 60:
                    console.print("[yellow]⚠️ Good quality rate, some improvement possible[/yellow]")
                else:
                    console.print("[red]❌ Poor quality rate, filtering needs improvement[/red]")
            
            # Save jobs to database
            console.print(f"\n[cyan]💾 Saving {len(jobs)} jobs to database...[/cyan]")
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
    test_improved_filtering()
