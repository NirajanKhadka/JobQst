#!/usr/bin/env python3
"""
Test script for the new Deep Eluta Scraper with experience level filtering.
This script tests the enhanced scraper that:
1. Deep scrapes job descriptions
2. Filters for entry-level/1-2 years experience
3. Only saves suitable jobs
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from rich.console import Console

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

import utils
from scrapers.eluta_deep_scraper import ElutaDeepScraper
from job_database import get_job_db

console = Console()


def test_deep_scraper():
    """Test the deep scraper with experience filtering."""
    
    console.print("[bold blue]🧪 Testing Deep Eluta Scraper with Experience Filtering[/bold blue]")
    
    # Load profile
    try:
        profile = utils.load_profile("Nirajan")
        console.print(f"[green]✅ Loaded profile: {profile['name']}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error loading profile: {e}[/red]")
        return False
    
    # Initialize database
    job_db = get_job_db(profile['profile_name'])
    console.print(f"[green]✅ Database initialized[/green]")
    
    # Show current stats
    stats = job_db.get_stats()
    console.print(f"[cyan]📊 Current database: {stats.get('total_jobs', 0)} jobs, {stats.get('unapplied_jobs', 0)} unapplied[/cyan]")
    
    # Test with a small set of keywords for entry-level positions
    test_keywords = ["Junior Data Analyst", "Entry Level Analyst", "Graduate Analyst"]
    
    # Create modified profile for testing
    test_profile = profile.copy()
    test_profile["keywords"] = test_keywords
    
    console.print(f"[cyan]🔍 Testing with keywords: {test_keywords}[/cyan]")
    console.print(f"[cyan]🎯 Looking for: Entry-level, 0-2 years experience, fresh graduates[/cyan]")
    
    suitable_jobs = []
    
    try:
        with sync_playwright() as p:
            # Use headless browser for testing
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            
            console.print("[green]🌐 Browser launched in headless mode[/green]")
            
            # Initialize deep scraper
            scraper = ElutaDeepScraper(test_profile, browser_context=context)
            
            # Scrape jobs with deep analysis
            console.print("[bold]🔍 Starting deep scraping with experience filtering...[/bold]")
            
            job_count = 0
            for job in scraper.scrape_jobs():
                job_count += 1
                suitable_jobs.append(job)
                
                console.print(f"\n[bold green]✅ SUITABLE JOB #{job_count}:[/bold green]")
                console.print(f"   📋 Title: {job.get('title', 'Unknown')}")
                console.print(f"   🏢 Company: {job.get('company', 'Unknown')}")
                console.print(f"   📍 Location: {job.get('location', 'Unknown')}")
                console.print(f"   🎯 Experience Level: {job.get('experience_level', 'Unknown')}")
                console.print(f"   📝 Description Length: {len(job.get('full_description', ''))} chars")
                console.print(f"   🔗 URL: {job.get('url', 'No URL')}")
                
                # Show requirements if available
                requirements = job.get('requirements', [])
                if requirements:
                    console.print(f"   📋 Requirements ({len(requirements)}):")
                    for i, req in enumerate(requirements[:3], 1):
                        console.print(f"      {i}. {req[:80]}...")
                
                # Show skills if available
                skills = job.get('skills_needed', [])
                if skills:
                    console.print(f"   🛠️ Skills: {', '.join(skills[:5])}")
                
                # Limit test to 5 suitable jobs
                if job_count >= 5:
                    console.print(f"[yellow]⏹️ Stopping test after {job_count} suitable jobs found[/yellow]")
                    break
            
            browser.close()
    
    except Exception as e:
        console.print(f"[red]❌ Error during deep scraping: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False
    
    # Save suitable jobs to database
    if suitable_jobs:
        console.print(f"\n[bold]💾 Saving {len(suitable_jobs)} suitable jobs to database...[/bold]")
        
        # Add metadata
        for job in suitable_jobs:
            job["search_keyword"] = "deep_scrape_test"
            job["site"] = "eluta_deep"
            job["scraped_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Save to database
        added, duplicates = job_db.add_jobs_batch(suitable_jobs)
        console.print(f"[green]✅ Saved {added} new suitable jobs ({duplicates} duplicates skipped)[/green]")
        
        # Export to CSV for review
        csv_file = Path("output") / f"{profile['profile_name']}_deep_scraped_jobs.csv"
        csv_file.parent.mkdir(exist_ok=True)
        job_db.export_to_csv(str(csv_file))
        console.print(f"[green]📄 Exported to: {csv_file}[/green]")
        
        # Show final stats
        final_stats = job_db.get_stats()
        console.print(f"\n[bold green]📊 Final database stats:[/bold green]")
        console.print(f"   Total jobs: {final_stats.get('total_jobs', 0)}")
        console.print(f"   Unapplied jobs: {final_stats.get('unapplied_jobs', 0)}")
        console.print(f"   Unique companies: {final_stats.get('unique_companies', 0)}")
        
        # Show sample of suitable jobs
        console.print(f"\n[bold]📋 Sample of suitable jobs found:[/bold]")
        for i, job in enumerate(suitable_jobs[:3], 1):
            console.print(f"   {i}. {job['title']} at {job['company']}")
            console.print(f"      Experience: {job.get('experience_level', 'Unknown')}")
            console.print(f"      Description: {job.get('full_description', '')[:100]}...")
            console.print()
    
    else:
        console.print("[yellow]⚠️ No suitable jobs found in test[/yellow]")
    
    console.print(f"\n[bold green]✅ Deep scraper test completed![/bold green]")
    console.print(f"[green]Found {len(suitable_jobs)} jobs suitable for entry-level/1-2 years experience[/green]")
    
    return True


def analyze_existing_jobs():
    """Analyze existing jobs in database to see experience levels."""
    
    console.print("\n[bold blue]📊 Analyzing existing jobs for experience levels...[/bold blue]")
    
    try:
        profile = utils.load_profile("Nirajan")
        job_db = get_job_db(profile['profile_name'])
        
        # Get all jobs from database
        jobs = job_db.get_all_jobs()
        console.print(f"[cyan]📋 Analyzing {len(jobs)} existing jobs...[/cyan]")
        
        # Initialize deep scraper for analysis
        from scrapers.eluta_deep_scraper import ElutaDeepScraper
        scraper = ElutaDeepScraper(profile)
        
        entry_level_count = 0
        senior_level_count = 0
        unknown_level_count = 0
        
        for job in jobs[:20]:  # Analyze first 20 jobs
            # Analyze experience level from title and description
            title = job.get('title', '')
            description = job.get('summary', '') or job.get('full_description', '')
            
            # Create job dict for analysis
            job_dict = {
                'title': title,
                'full_description': description,
                'experience_level': scraper._analyze_experience_level(description)
            }
            
            # Check if suitable
            is_suitable = scraper._is_suitable_for_profile(job_dict)
            
            if job_dict['experience_level'] == 'entry' or is_suitable:
                entry_level_count += 1
                console.print(f"[green]✅ SUITABLE: {title}[/green]")
            elif job_dict['experience_level'] == 'senior':
                senior_level_count += 1
                console.print(f"[yellow]❌ SENIOR: {title}[/yellow]")
            else:
                unknown_level_count += 1
                console.print(f"[cyan]? UNKNOWN: {title}[/cyan]")
        
        console.print(f"\n[bold]📊 Analysis Results (first 20 jobs):[/bold]")
        console.print(f"   ✅ Entry-level/Suitable: {entry_level_count}")
        console.print(f"   ❌ Senior-level: {senior_level_count}")
        console.print(f"   ? Unknown: {unknown_level_count}")
        console.print(f"   📈 Suitability rate: {entry_level_count/20*100:.1f}%")
        
    except Exception as e:
        console.print(f"[red]❌ Error analyzing existing jobs: {e}[/red]")


if __name__ == "__main__":
    console.print("[bold]🧪 Deep Scraper Test Suite[/bold]")
    
    # Test 1: Deep scraping with filtering
    success = test_deep_scraper()
    
    if success:
        # Test 2: Analyze existing jobs
        analyze_existing_jobs()
    
    console.print("\n[bold]🎉 Test suite completed![/bold]")
