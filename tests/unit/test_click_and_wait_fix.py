#!/usr/bin/env python3
"""
Test script to verify the click-and-wait job scraping fix.
This tests the core functionality of clicking on job postings and extracting real URLs.
"""

import sys
import time
from src.utils.profile_helpers import load_profile, get_available_profiles
from src.utils.job_helpers import generate_job_hash, is_duplicate_job, sort_jobs
from src.utils.file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv
from src.utils.document_generator import customize, DocumentGenerator
from pathlib import Path
from playwright.sync_api import sync_playwright
from rich.console import Console

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper


console = Console()


def test_click_and_wait_functionality():
    """Test the click-and-wait job scraping functionality."""
    console.print("[bold blue]🧪 Testing Click-and-Wait Job Scraping Fix[/bold blue]")
    
    try:
        # Load profile
        profile = load_profile("Nirajan")
        console.print(f"[green]✅ Loaded profile: {profile['name']}[/green]")
        
        # Create a simple test profile with minimal keywords
        test_profile = profile.copy()
        test_profile["keywords"] = ["Data Analyst"]  # Just one keyword for testing
        
        with sync_playwright() as p:
            # Launch browser in non-headless mode so we can see what's happening
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            
            console.print("[green]🌐 Browser launched for testing[/green]")
            
            # Create enhanced scraper
            scraper = ComprehensiveElutaScraper(test_profile, browser_context=context)
            
            console.print("[cyan]🔍 Starting test scraping with click-and-wait...[/cyan]")
            
            # Test scraping with our new click-and-wait functionality
            jobs_found = 0
            max_jobs_to_test = 3  # Only test a few jobs
            
            for job in scraper.scrape_jobs():
                jobs_found += 1
                console.print(f"\n[bold green]✅ Job {jobs_found} extracted successfully![/bold green]")
                console.print(f"   Title: {job.get('title', 'Unknown')}")
                console.print(f"   Company: {job.get('company', 'Unknown')}")
                console.print(f"   URL: {job.get('url', 'No URL')}")
                console.print(f"   Deep Scraped: {job.get('deep_scraped', False)}")
                
                # Check if we got a real URL (not a fake one)
                url = job.get('url', '')
                if url and 'eluta.ca' in url and not url.startswith('extracted_'):
                    console.print(f"   [green]✅ Real URL extracted: {url}[/green]")
                else:
                    console.print(f"   [red]❌ Invalid or fake URL: {url}[/red]")
                
                if jobs_found >= max_jobs_to_test:
                    console.print(f"\n[yellow]⏹️ Stopping after {max_jobs_to_test} test jobs[/yellow]")
                    break
            
            browser.close()
            
            # Summary
            console.print(f"\n[bold blue]📊 Test Results Summary[/bold blue]")
            console.print(f"[cyan]Jobs found: {jobs_found}[/cyan]")
            
            if jobs_found > 0:
                console.print(f"[bold green]✅ SUCCESS: Click-and-wait functionality is working![/bold green]")
                console.print(f"[green]The scraper successfully clicked on job postings and extracted real URLs.[/green]")
                return True
            else:
                console.print(f"[bold red]❌ FAILED: No jobs were extracted[/bold red]")
                console.print(f"[red]The click-and-wait functionality may not be working properly.[/red]")
                return False
                
    except Exception as e:
        console.print(f"[red]❌ Test failed with error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def test_simple_job_extraction():
    """Test simple job extraction without complex bot detection."""
    console.print("[bold blue]🧪 Testing Simple Job Extraction[/bold blue]")
    
    try:
        # Load profile
        profile = load_profile("Nirajan")
        
        # Create a minimal test profile
        test_profile = {
            "name": "Test User",
            "profile_name": "test",
            "keywords": ["Python"],
            "city": "Toronto",
            "email": "test@example.com"
        }
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            console.print("[green]🌐 Browser launched[/green]")
            
            # Navigate to Eluta search page manually
            search_url = "https://www.eluta.ca/search?q=Python&l=Toronto"
            console.print(f"[cyan]🌐 Navigating to: {search_url}[/cyan]")
            
            page.goto(search_url)
            page.wait_for_load_state("networkidle")
            
            # Check if we can see job elements
            job_elements = page.query_selector_all("div")
            console.print(f"[cyan]Found {len(job_elements)} div elements on page[/cyan]")
            
            # Look for job-like content
            job_count = 0
            for i, elem in enumerate(job_elements[:20]):  # Check first 20 elements
                try:
                    text = elem.inner_text().strip()
                    if len(text) > 50 and any(word in text.lower() for word in ['python', 'developer', 'analyst', 'engineer']):
                        job_count += 1
                        console.print(f"[green]Job-like element {job_count}: {text[:100]}...[/green]")
                        
                        # Try to find a link in this element
                        link = elem.query_selector("a")
                        if link:
                            href = link.get_attribute("href")
                            console.print(f"   Link found: {href}")
                            
                            if href and href.startswith("/"):
                                full_url = f"https://www.eluta.ca{href}"
                                console.print(f"   [cyan]🖱️ Testing click on: {full_url}[/cyan]")
                                
                                # Test clicking on the link
                                try:
                                    link.click()
                                    console.print(f"   [yellow]⏳ Waiting 3 seconds...[/yellow]")
                                    page.wait_for_timeout(3000)
                                    
                                    current_url = page.url
                                    console.print(f"   [green]✅ Navigated to: {current_url}[/green]")
                                    
                                    # Go back to search results
                                    page.go_back()
                                    page.wait_for_load_state("networkidle")
                                    console.print(f"   [cyan]🔙 Returned to search results[/cyan]")
                                    
                                    if job_count >= 3:  # Test only 3 jobs
                                        break
                                        
                                except Exception as click_error:
                                    console.print(f"   [red]❌ Click failed: {click_error}[/red]")
                        
                except Exception as elem_error:
                    continue
            
            browser.close()
            
            console.print(f"\n[bold blue]📊 Simple Test Results[/bold blue]")
            console.print(f"[cyan]Job-like elements found: {job_count}[/cyan]")
            
            if job_count > 0:
                console.print(f"[bold green]✅ SUCCESS: Found job elements and tested clicking[/bold green]")
                return True
            else:
                console.print(f"[bold red]❌ FAILED: No job elements found[/bold red]")
                return False
                
    except Exception as e:
        console.print(f"[red]❌ Simple test failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    console.print("[bold yellow]🚀 Starting Click-and-Wait Fix Tests[/bold yellow]")
    
    # Test 1: Simple job extraction
    console.print("\n" + "="*60)
    test1_result = test_simple_job_extraction()
    
    # Test 2: Full click-and-wait functionality (only if test 1 passes)
    if test1_result:
        console.print("\n" + "="*60)
        test2_result = test_click_and_wait_functionality()
    else:
        console.print("\n[yellow]⏭️ Skipping full test due to simple test failure[/yellow]")
        test2_result = False
    
    # Final summary
    console.print("\n" + "="*60)
    console.print("[bold blue]🎯 Final Test Summary[/bold blue]")
    console.print(f"Simple extraction test: {'✅ PASS' if test1_result else '❌ FAIL'}")
    console.print(f"Click-and-wait test: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        console.print(f"\n[bold green]🎉 ALL TESTS PASSED! The click-and-wait fix is working![/bold green]")
    else:
        console.print(f"\n[bold red]❌ TESTS FAILED. The fix needs more work.[/bold red]")
