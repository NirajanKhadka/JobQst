#!/usr/bin/env python3
"""
Test script to verify external URL extraction from Eluta scraper.
This tests if the scraper can find real external application URLs like Lever, Workday, etc.
"""

import sys
from pathlib import Path
from rich.console import Console

console = Console()

def test_external_url_extraction():
    """Test the external URL extraction functionality."""
    try:
        # Import the enhanced scraper
        from src.scrapers.eluta_enhanced import ElutaEnhancedScraper
        
        # Create a test profile
        test_profile = {
            "profile_name": "test_external_urls",
            "keywords": ["sql developer"],  # Use the keyword you mentioned
            "location": "Toronto",
            "ollama_model": "mistral:7b"
        }
        
        console.print("[bold blue]🧪 Testing External URL Extraction from Eluta Scraper[/bold blue]")
        console.print("[cyan]📋 This test will check if we can find real external application URLs[/cyan]")
        console.print("[cyan]🎯 Looking for URLs like: jobs.lever.co, workday.com, greenhouse.io, etc.[/cyan]")
        
        # Initialize scraper with deep scraping enabled
        scraper = ElutaEnhancedScraper(test_profile, deep_scraping=True)
        
        console.print("[cyan]📋 Scraper initialized with deep scraping enabled[/cyan]")
        console.print(f"[cyan]🔍 Testing with keyword: {test_profile['keywords'][0]}[/cyan]")
        
        # Test scraping a small number of jobs
        console.print("[yellow]⚠️ Starting test scrape (limited to 2 jobs for testing)...[/yellow]")
        
        jobs = []
        job_count = 0
        external_url_count = 0
        
        for job in scraper.scrape_jobs():
            jobs.append(job)
            job_count += 1
            
            # Display job details
            console.print(f"\n[bold green]📋 Job {job_count}:[/bold green]")
            console.print(f"[cyan]Title: {job.get('title', 'N/A')}[/cyan]")
            console.print(f"[cyan]Company: {job.get('company', 'N/A')}[/cyan]")
            console.print(f"[cyan]Location: {job.get('location', 'N/A')}[/cyan]")
            console.print(f"[blue]Job URL: {job.get('url', 'N/A')}[/blue]")
            console.print(f"[green]Apply URL: {job.get('apply_url', 'N/A')}[/green]")
            console.print(f"[purple]Deep Scraped: {job.get('deep_scraped', False)}[/purple]")
            
            # Check if we found external URLs
            apply_url = job.get('apply_url', '')
            job_url = job.get('url', '')
            
            # Check for external application URLs
            external_domains = [
                'workday.com', 'myworkday.com', 'wd1.myworkdayjobs.com',
                'greenhouse.io', 'boards.greenhouse.io',
                'lever.co', 'jobs.lever.co',
                'icims.com', 'bamboohr.com', 'smartrecruiters.com',
                'jobvite.com', 'ultipro.com', 'successfactors.com',
                'taleo.net'
            ]
            
            is_external = False
            for domain in external_domains:
                if domain in apply_url:
                    console.print(f"[bold green]🎉 Found external ATS URL: {apply_url}[/bold green]")
                    external_url_count += 1
                    is_external = True
                    break
            
            if not is_external:
                if apply_url and 'eluta.ca' not in apply_url and apply_url.startswith('http'):
                    console.print(f"[yellow]⚠️ Found external URL (unknown ATS): {apply_url}[/yellow]")
                    external_url_count += 1
                elif apply_url and 'eluta.ca' in apply_url:
                    console.print(f"[red]❌ Still using Eluta URL: {apply_url}[/red]")
                else:
                    console.print(f"[red]❌ No valid apply URL found[/red]")
            
            # Stop after 2 jobs for testing
            if job_count >= 2:
                break
        
        # Summary
        console.print(f"\n[bold blue]📊 External URL Test Summary:[/bold blue]")
        console.print(f"[cyan]Total jobs tested: {len(jobs)}[/cyan]")
        console.print(f"[green]✅ External URLs found: {external_url_count}[/green]")
        console.print(f"[red]❌ Eluta URLs remaining: {len(jobs) - external_url_count}[/red]")
        
        if external_url_count > 0:
            console.print(f"[bold green]🎉 External URL extraction is working! Found {external_url_count} external URLs.[/bold green]")
            
            # Show examples of external URLs found
            console.print(f"\n[bold]🔗 External URLs Found:[/bold]")
            for job in jobs:
                apply_url = job.get('apply_url', '')
                if apply_url and 'eluta.ca' not in apply_url and apply_url.startswith('http'):
                    console.print(f"  [green]✅ {job.get('title', 'Unknown')}: {apply_url}[/green]")
            
            return True
        else:
            console.print(f"[bold red]❌ No external URLs found. Still need to improve extraction.[/bold red]")
            
            # Show what URLs we did find
            console.print(f"\n[bold]🔗 URLs Found (for debugging):[/bold]")
            for job in jobs:
                apply_url = job.get('apply_url', '')
                console.print(f"  [yellow]⚠️ {job.get('title', 'Unknown')}: {apply_url}[/yellow]")
            
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Test failed with error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    console.print("[bold blue]🔧 External URL Extraction Test[/bold blue]")
    console.print("[cyan]This test verifies that the scraper can find real external application URLs[/cyan]")
    console.print("[cyan]like jobs.lever.co, workday.com, greenhouse.io instead of eluta.ca URLs[/cyan]")
    
    success = test_external_url_extraction()
    
    if success:
        console.print("\n[bold green]✅ External URL extraction test passed![/bold green]")
        console.print("[green]The scraper can now find real external application URLs![/green]")
        return 0
    else:
        console.print("\n[bold red]❌ External URL extraction test failed![/bold red]")
        console.print("[red]The scraper still needs improvement to find external URLs.[/red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
