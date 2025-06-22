#!/usr/bin/env python3
"""
Test Main Eluta Scraper with Requirements:
- 9 pages per keyword
- 14-day filter (no jobs older than 14 days)
- All keywords from profile
"""

import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import the working Eluta scraper
from scrapers.eluta_working import ElutaWorkingScraper

console = Console()

def test_eluta_scraper():
    """Test the main Eluta scraper with specified requirements."""
    
    console.print(Panel("🚀 Testing Main Eluta Scraper", style="bold blue"))
    console.print("[cyan]Requirements: 9 pages per keyword, 14-day filter, all keywords[/cyan]")
    
    # Load profile
    try:
        with open("profiles/Nirajan/Nirajan.json", "r") as f:
            profile = json.load(f)
        console.print(f"[green]✅ Loaded profile: {profile['name']}[/green]")
        console.print(f"[cyan]📋 Keywords: {len(profile['keywords'])} keywords[/cyan]")
        for keyword in profile['keywords']:
            console.print(f"  • {keyword}")
    except Exception as e:
        console.print(f"[red]❌ Error loading profile: {e}[/red]")
        return
    
    # Initialize scraper with requirements
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Visible for monitoring
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        try:
            # Configure scraper with requirements
            scraper = ElutaWorkingScraper(
                profile=profile,
                browser_context=context,
                max_pages_per_keyword=9,  # 9 pages as requested
                max_jobs_per_keyword=100,  # High limit to get all jobs
                enable_deep_analysis=True
            )
            
            console.print(f"[green]✅ Scraper configured:[/green]")
            console.print(f"  • Max pages per keyword: {scraper.max_pages_per_keyword}")
            console.print(f"  • Max jobs per keyword: {scraper.max_jobs_per_keyword}")
            console.print(f"  • Date filter: {scraper.max_age_days} days")
            console.print(f"  • Keywords to process: {len(scraper.keywords)}")
            
            # Start scraping
            console.print(f"\n[bold green]🚀 Starting Eluta scraping session...[/bold green]")
            start_time = time.time()
            
            all_jobs = []
            jobs_by_keyword = {}
            
            # Process each job from the scraper
            for job in scraper.scrape_jobs():
                keyword = job.get('search_keyword', 'Unknown')
                if keyword not in jobs_by_keyword:
                    jobs_by_keyword[keyword] = []
                
                jobs_by_keyword[keyword].append(job)
                all_jobs.append(job)
                
                # Display job info
                title = job.get('title', 'Unknown')[:50]
                company = job.get('company', 'Unknown')[:30]
                posted_date = job.get('posted_date', 'Unknown')
                location = job.get('location', 'Unknown')
                
                console.print(f"[green]✅ Job: {title}... at {company} ({posted_date}) - {location}[/green]")
            
            # Calculate statistics
            end_time = time.time()
            duration = end_time - start_time
            
            console.print(f"\n[bold green]🎉 Scraping completed![/bold green]")
            console.print(f"[cyan]📊 Statistics:[/cyan]")
            console.print(f"  • Total jobs found: {len(all_jobs)}")
            console.print(f"  • Keywords processed: {len(jobs_by_keyword)}")
            console.print(f"  • Duration: {duration:.1f} seconds")
            
            # Show jobs by keyword
            console.print(f"\n[bold yellow]📋 Jobs by Keyword:[/bold yellow]")
            for keyword, jobs in jobs_by_keyword.items():
                console.print(f"  • {keyword}: {len(jobs)} jobs")
            
            # Show recent jobs (within 14 days)
            recent_jobs = [job for job in all_jobs if is_job_recent_enough(job.get('posted_date', ''))]
            console.print(f"\n[bold green]📅 Recent jobs (≤14 days): {len(recent_jobs)}[/bold green]")
            
            # Show sample of recent jobs
            if recent_jobs:
                console.print(f"\n[bold cyan]📋 Sample Recent Jobs:[/bold cyan]")
                for i, job in enumerate(recent_jobs[:5]):  # Show first 5
                    title = job.get('title', 'Unknown')[:60]
                    company = job.get('company', 'Unknown')
                    posted_date = job.get('posted_date', 'Unknown')
                    location = job.get('location', 'Unknown')
                    
                    console.print(f"  {i+1}. {title}")
                    console.print(f"     {company} | {location} | {posted_date}")
                    console.print()
            
            # Save results to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"eluta_test_results_{timestamp}.json"
            
            # Prepare data for saving
            results = {
                "test_info": {
                    "timestamp": datetime.now().isoformat(),
                    "profile": profile['name'],
                    "keywords_processed": len(scraper.keywords),
                    "max_pages_per_keyword": scraper.max_pages_per_keyword,
                    "max_age_days": scraper.max_age_days,
                    "duration_seconds": duration
                },
                "statistics": {
                    "total_jobs": len(all_jobs),
                    "recent_jobs": len(recent_jobs),
                    "jobs_by_keyword": {k: len(v) for k, v in jobs_by_keyword.items()}
                },
                "jobs": all_jobs
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            console.print(f"[green]✅ Results saved to: {output_file}[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ Scraping error: {e}[/red]")
            import traceback
            traceback.print_exc()
        
        finally:
            input("\nPress Enter to close browser...")
            browser.close()

def is_job_recent_enough(posted_date):
    """Check if job is recent enough (within 14 days)."""
    if not posted_date:
        return True  # Include if no date found
    
    posted_date_lower = posted_date.lower()
    
    # Check for hours/minutes (always recent)
    if "hour" in posted_date_lower or "minute" in posted_date_lower:
        return True
    
    # Check for days
    if "day" in posted_date_lower:
        import re
        match = re.search(r'(\d+)\s*day', posted_date_lower)
        if match:
            days_ago = int(match.group(1))
            return days_ago <= 14
    
    # Check for weeks
    if "week" in posted_date_lower:
        import re
        match = re.search(r'(\d+)\s*week', posted_date_lower)
        if match:
            weeks_ago = int(match.group(1))
            return weeks_ago <= 2  # 2 weeks = 14 days
    
    # Check for months/years (too old)
    if "month" in posted_date_lower or "year" in posted_date_lower:
        return False
    
    return True  # Default to include if unclear

if __name__ == "__main__":
    test_eluta_scraper() 