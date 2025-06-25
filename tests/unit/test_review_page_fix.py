#!/usr/bin/env python3
"""
Test script to verify that the scraper no longer opens review pages.
This tests if the scraper correctly avoids canadastop100.com URLs.
"""

import sys
from pathlib import Path
from rich.console import Console

console = Console()

def test_review_page_avoidance():
    """Test that the scraper avoids review pages."""
    try:
        # Import the enhanced scraper
        from src.scrapers.eluta_enhanced import ElutaEnhancedScraper
        
        # Create a test profile with SQL developer (as mentioned by user)
        test_profile = {
            "profile_name": "test_review_fix",
            "keywords": ["sql developer"],
            "location": "Toronto",
            "ollama_model": "mistral:7b"
        }
        
        console.print("[bold blue]🧪 Testing Review Page Avoidance[/bold blue]")
        console.print("[cyan]📋 This test verifies that the scraper avoids canadastop100.com URLs[/cyan]")
        console.print("[cyan]🎯 Looking for actual job URLs, not review/employer pages[/cyan]")
        
        # Initialize scraper with deep scraping disabled for faster testing
        scraper = ElutaEnhancedScraper(test_profile, deep_scraping=False)
        
        console.print("[cyan]📋 Scraper initialized (deep scraping disabled for speed)[/cyan]")
        console.print(f"[cyan]🔍 Testing with keyword: {test_profile['keywords'][0]}[/cyan]")
        
        # Test scraping a small number of jobs
        console.print("[yellow]⚠️ Starting test scrape (limited to 3 jobs for testing)...[/yellow]")
        
        jobs = []
        job_count = 0
        review_url_count = 0
        valid_job_url_count = 0
        
        for job in scraper.scrape_jobs():
            jobs.append(job)
            job_count += 1
            
            # Display job details
            console.print(f"\n[bold green]📋 Job {job_count}:[/bold green]")
            console.print(f"[cyan]Title: {job.get('title', 'N/A')}[/cyan]")
            console.print(f"[cyan]Company: {job.get('company', 'N/A')}[/cyan]")
            console.print(f"[cyan]Location: {job.get('location', 'N/A')}[/cyan]")
            console.print(f"[blue]URL: {job.get('url', 'N/A')}[/blue]")
            
            # Check for review page URLs
            url = job.get('url', '')
            if url:
                # Check for review/employer page indicators
                bad_indicators = [
                    'canadastop100.com',
                    'reviews.',
                    'top-employer',
                    'employer-review'
                ]
                
                is_review_page = any(indicator in url for indicator in bad_indicators)
                
                if is_review_page:
                    console.print(f"[red]❌ REVIEW PAGE DETECTED: {url}[/red]")
                    review_url_count += 1
                elif url.startswith('https://www.eluta.ca/job/') or url.startswith('https://www.eluta.ca/direct/'):
                    console.print(f"[green]✅ Valid job URL: {url}[/green]")
                    valid_job_url_count += 1
                else:
                    console.print(f"[yellow]⚠️ Unknown URL format: {url}[/yellow]")
            else:
                console.print(f"[red]❌ No URL found[/red]")
            
            # Stop after 3 jobs for testing
            if job_count >= 3:
                break
        
        # Summary
        console.print(f"\n[bold blue]📊 Review Page Avoidance Test Summary:[/bold blue]")
        console.print(f"[cyan]Total jobs tested: {len(jobs)}[/cyan]")
        console.print(f"[green]✅ Valid job URLs: {valid_job_url_count}[/green]")
        console.print(f"[red]❌ Review page URLs: {review_url_count}[/red]")
        
        if review_url_count == 0:
            console.print(f"[bold green]🎉 Review page avoidance is working! No review URLs found.[/bold green]")
            return True
        else:
            console.print(f"[bold red]❌ Found {review_url_count} review page URLs. Fix needed.[/bold red]")
            
            # Show examples of review URLs found
            console.print(f"\n[bold]🔗 Review URLs Found (for debugging):[/bold]")
            for job in jobs:
                url = job.get('url', '')
                if any(indicator in url for indicator in ['canadastop100.com', 'reviews.', 'top-employer']):
                    console.print(f"  [red]❌ {job.get('title', 'Unknown')}: {url}[/red]")
            
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Test failed with error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    console.print("[bold blue]🔧 Review Page Avoidance Test[/bold blue]")
    console.print("[cyan]This test verifies that the scraper no longer opens review pages[/cyan]")
    console.print("[cyan]like canadastop100.com URLs instead of actual job postings[/cyan]")
    
    success = test_review_page_avoidance()
    
    if success:
        console.print("\n[bold green]✅ Review page avoidance test passed![/bold green]")
        console.print("[green]The scraper successfully avoids review/employer pages![/green]")
        return 0
    else:
        console.print("\n[bold red]❌ Review page avoidance test failed![/bold red]")
        console.print("[red]The scraper still needs improvement to avoid review pages.[/red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
