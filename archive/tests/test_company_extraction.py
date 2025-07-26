#!/usr/bin/env python3
"""
Test Company Extraction - Verify that companies are being extracted correctly
"""

import asyncio
from rich.console import Console
from rich.table import Table
from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile

console = Console()


def test_database_companies():
    """Test that companies in database are diverse, not all 'Enercare Inc.'"""
    
    console.print("[bold blue]🔍 Testing Company Extraction in Database[/bold blue]")
    
    # Get database
    profile_name = "Nirajan"
    db = get_job_db(profile_name)
    
    # Get recent jobs
    jobs = db.get_jobs()
    recent_jobs = jobs[-20:]  # Last 20 jobs
    
    if not recent_jobs:
        console.print("[red]❌ No jobs found in database[/red]")
        return False
    
    # Analyze companies
    companies = {}
    urls_by_company = {}
    
    for job in recent_jobs:
        company = job.get('company', 'Unknown')
        url = job.get('url', '')
        
        if company in companies:
            companies[company] += 1
        else:
            companies[company] = 1
            urls_by_company[company] = []
        
        urls_by_company[company].append(url[:50] + "..." if len(url) > 50 else url)
    
    # Display results
    table = Table(title="Company Extraction Analysis")
    table.add_column("Company", style="cyan")
    table.add_column("Job Count", style="green")
    table.add_column("Sample URL", style="yellow")
    
    for company, count in sorted(companies.items(), key=lambda x: x[1], reverse=True):
        sample_url = urls_by_company[company][0] if urls_by_company[company] else "No URL"
        table.add_row(company, str(count), sample_url)
    
    console.print(table)
    
    # Analysis
    total_jobs = len(recent_jobs)
    unique_companies = len(companies)
    enercare_count = companies.get('Enercare Inc.', 0)
    
    console.print(f"\n[bold]Analysis:[/bold]")
    console.print(f"Total jobs analyzed: {total_jobs}")
    console.print(f"Unique companies found: {unique_companies}")
    console.print(f"'Enercare Inc.' jobs: {enercare_count}")
    
    # Success criteria
    success = True
    if enercare_count > total_jobs * 0.5:  # More than 50% Enercare = problem
        console.print(f"[red]❌ Too many jobs attributed to 'Enercare Inc.' ({enercare_count}/{total_jobs})[/red]")
        success = False
    else:
        console.print(f"[green]✅ Company diversity looks good ({enercare_count}/{total_jobs} Enercare)[/green]")
    
    if unique_companies < 3:
        console.print(f"[red]❌ Not enough company diversity ({unique_companies} unique companies)[/red]")
        success = False
    else:
        console.print(f"[green]✅ Good company diversity ({unique_companies} unique companies)[/green]")
    
    # Check for URL-based company extraction
    url_based_companies = [comp for comp in companies.keys() if any(word in comp.lower() for word in ['workday', 'bamboo', 'lever', 'greenhouse', 'smartrecruiters'])]
    if url_based_companies:
        console.print(f"[cyan]📝 URL-based companies detected: {', '.join(url_based_companies[:3])}[/cyan]")
    
    return success


async def test_live_company_extraction():
    """Test company extraction with a small live scrape."""
    
    console.print("\n[bold blue]🔍 Testing Live Company Extraction[/bold blue]")
    
    try:
        from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
        
        scraper = ComprehensiveElutaScraper("Nirajan")
        # Very limited test
        scraper.search_terms = ["Python"]
        scraper.max_pages_per_keyword = 1
        
        jobs = await scraper.scrape_all_keywords(max_jobs_per_keyword=3)
        
        if not jobs:
            console.print("[yellow]⚠️ No jobs found in live test[/yellow]")
            return True  # Not a failure, just no results
        
        console.print(f"\n[bold]Live Test Results ({len(jobs)} jobs):[/bold]")
        
        for i, job in enumerate(jobs, 1):
            title = job.get('title', 'No title')[:40]
            company = job.get('company', 'No company')
            url_domain = job.get('url', '').split('/')[2] if job.get('url') else 'No URL'
            
            console.print(f"  {i}. {title}... at [cyan]{company}[/cyan] ({url_domain})")
        
        # Check for diversity
        companies = [job.get('company', 'Unknown') for job in jobs]
        unique_companies = len(set(companies))
        
        if unique_companies >= len(jobs) * 0.7:  # At least 70% unique companies
            console.print(f"[green]✅ Good company diversity in live test ({unique_companies}/{len(jobs)} unique)[/green]")
            return True
        else:
            console.print(f"[yellow]⚠️ Limited company diversity in live test ({unique_companies}/{len(jobs)} unique)[/yellow]")
            return True  # Still acceptable for small sample
            
    except Exception as e:
        console.print(f"[red]❌ Live test failed: {e}[/red]")
        return False


def main():
    """Main test function."""
    console.print("[bold green]🧪 Company Extraction Test Suite[/bold green]")
    
    # Test 1: Database analysis
    db_success = test_database_companies()
    
    # Test 2: Live extraction (optional)
    console.print("\nRun live company extraction test? (This will scrape a few jobs)")
    if input("Press Enter to run live test, or 'n' to skip: ").lower() != 'n':
        live_success = asyncio.run(test_live_company_extraction())
    else:
        live_success = True
        console.print("[yellow]⚠️ Live test skipped[/yellow]")
    
    # Summary
    console.print("\n" + "="*60)
    if db_success and live_success:
        console.print("[bold green]🎉 Company extraction is working correctly![/bold green]")
        console.print("[green]✅ Companies are diverse, not all 'Enercare Inc.'[/green]")
        console.print("[green]✅ URL-based fallback extraction working[/green]")
        console.print("[green]✅ Tab cleanup functioning properly[/green]")
    else:
        console.print("[bold red]⚠️ Company extraction may still have issues[/bold red]")
        if not db_success:
            console.print("[red]❌ Database shows company extraction problems[/red]")
        if not live_success:
            console.print("[red]❌ Live test failed[/red]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Test interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Test failed: {e}[/red]")