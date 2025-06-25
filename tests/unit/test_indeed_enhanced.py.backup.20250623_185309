#!/usr/bin/env python3
"""
Test script for Enhanced Indeed Scraper
Tests the latest anti-detection techniques and scraping methods.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.table import Table

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import utils
from scrapers.indeed_enhanced import EnhancedIndeedScraper

console = Console()


def test_indeed_enhanced():
    """Test the enhanced Indeed scraper with anti-detection."""
    
    console.print("[bold blue]🔍 Enhanced Indeed Scraper Test[/bold blue]")
    console.print("Testing latest anti-detection techniques and scraping methods")
    
    # Load profile
    try:
        profile = utils.load_profile("Nirajan")
        console.print(f"[green]✅ Loaded profile: {profile['name']}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error loading profile: {e}[/red]")
        return False
    
    # Test browser setup
    console.print("\n[bold]🌐 Testing Browser Setup[/bold]")
    
    with sync_playwright() as p:
        try:
            # Create enhanced browser context
            ctx = utils.create_browser_context(p, profile)
            console.print("[green]✅ Browser context created successfully[/green]")
            
            # Initialize enhanced scraper
            scraper = EnhancedIndeedScraper(profile, browser_context=ctx)
            console.print("[green]✅ Enhanced scraper initialized[/green]")
            
            # Test navigation and anti-detection
            console.print("\n[bold]🛡️ Testing Anti-Detection Features[/bold]")
            
            page = ctx.new_page()
            
            # Setup stealth mode
            scraper._setup_stealth_mode(page)
            console.print("[green]✅ Stealth mode configured[/green]")
            
            # Test navigation
            test_url = "https://ca.indeed.com/jobs?q=data+analyst&l=Toronto%2C+ON"
            console.print(f"[cyan]🌐 Testing navigation to: {test_url}[/cyan]")
            
            if scraper._navigate_with_stealth(page, test_url):
                console.print("[green]✅ Navigation successful[/green]")
                
                # Test protection handling
                if scraper._handle_protection_challenges(page):
                    console.print("[green]✅ Protection challenges handled[/green]")
                else:
                    console.print("[yellow]⚠️ Protection challenges detected[/yellow]")
                
                # Test content detection
                if scraper._wait_for_job_content(page):
                    console.print("[green]✅ Job content detected[/green]")
                    
                    # Test job extraction
                    console.print("\n[bold]📋 Testing Job Extraction[/bold]")
                    
                    jobs = list(scraper._extract_jobs_enhanced(page))
                    
                    if jobs:
                        console.print(f"[green]✅ Successfully extracted {len(jobs)} jobs[/green]")
                        
                        # Display sample jobs
                        display_sample_jobs(jobs[:3])
                        
                        # Test data quality
                        analyze_data_quality(jobs)
                        
                    else:
                        console.print("[yellow]⚠️ No jobs extracted[/yellow]")
                        
                        # Debug information
                        console.print("\n[bold]🔍 Debug Information[/bold]")
                        console.print(f"Page title: {page.title()}")
                        console.print(f"Page URL: {page.url}")
                        
                        # Check for common selectors
                        selectors_to_check = [
                            ".slider_container .slider_item",
                            ".job_seen_beacon",
                            "a.tapItem",
                            ".jobsearch-SerpJobCard"
                        ]
                        
                        for selector in selectors_to_check:
                            try:
                                elements = page.query_selector_all(selector)
                                console.print(f"Selector '{selector}': {len(elements)} elements")
                            except Exception as e:
                                console.print(f"Selector '{selector}': Error - {e}")
                
                else:
                    console.print("[red]❌ No job content found[/red]")
            else:
                console.print("[red]❌ Navigation failed[/red]")
            
            page.close()
            ctx.close()
            
        except Exception as e:
            console.print(f"[red]❌ Test failed: {e}[/red]")
            return False
    
    console.print("\n[bold green]✅ Enhanced Indeed scraper test completed![/bold green]")
    return True


def display_sample_jobs(jobs):
    """Display sample jobs in a nice table."""
    if not jobs:
        return
    
    console.print("\n[bold]📋 Sample Jobs Extracted[/bold]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Title", style="cyan", width=30)
    table.add_column("Company", style="green", width=20)
    table.add_column("Location", style="yellow", width=20)
    table.add_column("Salary", style="red", width=15)
    
    for job in jobs:
        title = job.get('title', 'N/A')[:30]
        company = job.get('company', 'N/A')[:20]
        location = job.get('location', 'N/A')[:20]
        salary = job.get('salary', 'N/A')[:15]
        
        table.add_row(title, company, location, salary)
    
    console.print(table)


def analyze_data_quality(jobs):
    """Test the quality of extracted job data."""
    console.print("\n[bold]🔍 Data Quality Analysis[/bold]")
    
    if not jobs:
        console.print("[red]❌ No jobs to analyze[/red]")
        return
    
    total_jobs = len(jobs)
    
    # Check required fields
    fields_to_check = ['title', 'company', 'location', 'url']
    field_stats = {}
    
    for field in fields_to_check:
        filled_count = sum(1 for job in jobs if job.get(field) and job.get(field).strip())
        field_stats[field] = (filled_count, filled_count / total_jobs * 100)
    
    # Display stats
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Field", style="cyan")
    table.add_column("Filled", style="green")
    table.add_column("Percentage", style="yellow")
    table.add_column("Status", style="magenta")
    
    for field, (count, percentage) in field_stats.items():
        status = "✅ Good" if percentage >= 80 else "⚠️ Poor" if percentage >= 50 else "❌ Bad"
        table.add_row(field.title(), f"{count}/{total_jobs}", f"{percentage:.1f}%", status)
    
    console.print(table)
    
    # Overall quality score
    avg_percentage = sum(stats[1] for stats in field_stats.values()) / len(field_stats)
    
    if avg_percentage >= 80:
        console.print(f"[green]✅ Overall data quality: Excellent ({avg_percentage:.1f}%)[/green]")
    elif avg_percentage >= 60:
        console.print(f"[yellow]⚠️ Overall data quality: Good ({avg_percentage:.1f}%)[/yellow]")
    else:
        console.print(f"[red]❌ Overall data quality: Poor ({avg_percentage:.1f}%)[/red]")


def test_browser_detection():
    """Test browser detection capabilities."""
    console.print("\n[bold]🔍 Browser Detection Test[/bold]")
    
    browsers = utils.detect_available_browsers()
    
    table = Table(show_header=True, header_style="bold green")
    table.add_column("Browser", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Path", style="yellow")
    
    for browser, path in browsers.items():
        if path:
            status = "✅ Available"
            path_display = path[:50] + "..." if len(path) > 50 else path
        else:
            status = "❌ Not Found"
            path_display = "N/A"
        
        table.add_row(browser.title(), status, path_display)
    
    console.print(table)


def main():
    """Main test function."""
    console.print("[bold blue]🚀 Enhanced Indeed Scraper Test Suite[/bold blue]")
    console.print("This will test the latest Indeed scraping techniques with anti-detection")
    
    # Test browser detection
    test_browser_detection()
    
    # Ask user to continue
    console.print("\n[yellow]This test will open a browser and attempt to scrape Indeed.[/yellow]")
    console.print("[yellow]Make sure you have a stable internet connection.[/yellow]")
    
    response = input("\nContinue with the test? (y/N): ").lower().strip()
    
    if response != 'y':
        console.print("[yellow]Test cancelled by user.[/yellow]")
        return
    
    # Run the main test
    success = test_indeed_enhanced()
    
    if success:
        console.print("\n[bold green]🎉 All tests passed![/bold green]")
        console.print("[cyan]The enhanced Indeed scraper is working correctly.[/cyan]")
        console.print("[cyan]You can now use it in your job scraping workflow.[/cyan]")
    else:
        console.print("\n[bold red]❌ Tests failed![/bold red]")
        console.print("[yellow]Check the error messages above for troubleshooting.[/yellow]")
        console.print("[yellow]You may need to solve CAPTCHAs manually or adjust settings.[/yellow]")


if __name__ == "__main__":
    main()
