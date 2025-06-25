#!/usr/bin/env python3
"""
Test script to verify URL extraction from Eluta scraper.
"""

import sys
from pathlib import Path
from rich.console import Console

console = Console()

def test_url_extraction():
    """Test the URL extraction functionality."""
    try:
        # Import the enhanced scraper
        from src.scrapers.eluta_enhanced import ElutaEnhancedScraper
        
        # Create a test profile
        test_profile = {
            "profile_name": "test_user",
            "keywords": ["python developer"],
            "location": "Toronto",
            "ollama_model": "mistral:7b"
        }
        
        console.print("[bold blue]🧪 Testing URL Extraction from Eluta Scraper[/bold blue]")
        
        # Initialize scraper
        scraper = ElutaEnhancedScraper(test_profile)
        
        console.print("[cyan]📋 Scraper initialized successfully[/cyan]")
        console.print(f"[cyan]🔍 Testing with keyword: {test_profile['keywords'][0]}[/cyan]")
        
        # Test scraping a small number of jobs
        console.print("[yellow]⚠️ Starting test scrape (limited to 3 jobs)...[/yellow]")
        
        jobs = []
        job_count = 0
        
        for job in scraper.scrape_jobs():
            jobs.append(job)
            job_count += 1
            
            # Display job details
            console.print(f"\n[bold green]📋 Job {job_count}:[/bold green]")
            console.print(f"[cyan]Title: {job.get('title', 'N/A')}[/cyan]")
            console.print(f"[cyan]Company: {job.get('company', 'N/A')}[/cyan]")
            console.print(f"[cyan]Location: {job.get('location', 'N/A')}[/cyan]")
            console.print(f"[green]URL: {job.get('url', 'N/A')}[/green]")
            console.print(f"[blue]Apply URL: {job.get('apply_url', 'N/A')}[/blue]")
            
            # Check URL validity
            url = job.get('url', '')
            if url:
                if 'extracted_' in url or 'error_' in url:
                    console.print(f"[red]❌ Invalid URL detected: {url}[/red]")
                elif url.startswith('https://www.eluta.ca/job/') or url.startswith('https://www.eluta.ca/direct/'):
                    console.print(f"[green]✅ Valid Eluta URL: {url}[/green]")
                elif url.startswith('http'):
                    console.print(f"[yellow]⚠️ External URL: {url}[/yellow]")
                else:
                    console.print(f"[red]❌ Malformed URL: {url}[/red]")
            else:
                console.print(f"[red]❌ No URL found[/red]")
            
            # Stop after 3 jobs for testing
            if job_count >= 3:
                break
        
        # Summary
        console.print(f"\n[bold blue]📊 Test Summary:[/bold blue]")
        console.print(f"[cyan]Total jobs found: {len(jobs)}[/cyan]")
        
        valid_urls = 0
        invalid_urls = 0
        
        for job in jobs:
            url = job.get('url', '')
            if url and not ('extracted_' in url or 'error_' in url):
                valid_urls += 1
            else:
                invalid_urls += 1
        
        console.print(f"[green]✅ Valid URLs: {valid_urls}[/green]")
        console.print(f"[red]❌ Invalid URLs: {invalid_urls}[/red]")
        
        if valid_urls > 0:
            console.print(f"[bold green]🎉 URL extraction is working correctly![/bold green]")
            return True
        else:
            console.print(f"[bold red]❌ URL extraction needs improvement[/bold red]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Test failed with error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    console.print("[bold blue]🔧 URL Extraction Test[/bold blue]")
    
    success = test_url_extraction()
    
    if success:
        console.print("\n[bold green]✅ All tests passed![/bold green]")
        return 0
    else:
        console.print("\n[bold red]❌ Tests failed![/bold red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
