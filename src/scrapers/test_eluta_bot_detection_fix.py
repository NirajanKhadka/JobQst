#!/usr/bin/env python3
"""
Test script for the improved Eluta scraper with enhanced bot detection handling.
This script tests the new anti-detection measures and manual verification workflow.
"""

import sys
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def test_eluta_scraper_improvements():
    """Test the improved Eluta scraper with enhanced anti-detection."""
    
    console.print(Panel("🧪 Testing Eluta Scraper Bot Detection Fixes", style="bold blue"))
    
    try:
        # Import required modules
        from scrapers.eluta_enhanced import ElutaEnhancedScraper
        from playwright.sync_api import sync_playwright
        import utils
        
        # Load test profile
        console.print("[cyan]📋 Loading test profile...[/cyan]")
        try:
            profile = utils.load_profile("Nirajan")
            console.print(f"[green]✅ Profile loaded: {profile['profile_name']}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Could not load profile: {e}[/red]")
            return False
        
        # Create test configuration
        test_config = {
            'comprehensive_mode': False,  # Use standard mode for testing
            'deep_scraping': True,       # Enable click-and-wait functionality
        }
        
        console.print("[cyan]🚀 Starting Eluta scraper test with enhanced anti-detection...[/cyan]")
        
        # Test with visible browser for manual verification if needed
        with sync_playwright() as p:
            console.print("[cyan]🌐 Launching browser with enhanced stealth...[/cyan]")
            
            # Launch browser with anti-detection arguments
            browser = p.chromium.launch(
                headless=False,  # Visible for manual verification
                args=[
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Initialize enhanced scraper
            scraper = ElutaEnhancedScraper(profile, browser_context=context, **test_config)
            
            console.print("[bold green]🛡️ Enhanced Eluta scraper initialized with:[/bold green]")
            console.print("[cyan]  • Advanced stealth browser configuration[/cyan]")
            console.print("[cyan]  • Human-like navigation patterns[/cyan]")
            console.print("[cyan]  • Enhanced manual verification workflow[/cyan]")
            console.print("[cyan]  • Session persistence and recovery[/cyan]")
            console.print("[cyan]  • Click-and-wait job URL extraction[/cyan]")
            
            # Start scraping test
            console.print("\n[bold yellow]🔍 Starting scraping test...[/bold yellow]")
            console.print("[yellow]This test will:[/yellow]")
            console.print("[yellow]  1. Test enhanced stealth measures[/yellow]")
            console.print("[yellow]  2. Handle bot detection gracefully[/yellow]")
            console.print("[yellow]  3. Extract real job URLs using click-and-wait[/yellow]")
            console.print("[yellow]  4. Save session state for future use[/yellow]")
            
            start_time = datetime.now()
            jobs_found = []
            
            try:
                # Limit to first few jobs for testing
                job_count = 0
                max_test_jobs = 3
                
                for job in scraper.scrape_jobs():
                    job_count += 1
                    jobs_found.append(job)
                    
                    console.print(f"[green]✅ Job {job_count}: {job['title']} at {job['company']}[/green]")
                    console.print(f"[cyan]   URL: {job['url']}[/cyan]")
                    console.print(f"[cyan]   Deep scraped: {job.get('deep_scraped', False)}[/cyan]")
                    
                    if job_count >= max_test_jobs:
                        console.print(f"[yellow]🛑 Stopping test after {max_test_jobs} jobs[/yellow]")
                        break
                
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠️ Test interrupted by user[/yellow]")
            except Exception as e:
                console.print(f"\n[red]❌ Scraping error: {e}[/red]")
                import traceback
                traceback.print_exc()
            
            finally:
                browser.close()
            
            # Test results
            end_time = datetime.now()
            duration = end_time - start_time
            
            console.print(f"\n[bold blue]📊 Test Results:[/bold blue]")
            
            # Create results table
            table = Table(title="Eluta Scraper Test Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Jobs Found", str(len(jobs_found)))
            table.add_row("Test Duration", f"{duration.total_seconds():.1f} seconds")
            table.add_row("Bot Detection Handled", "✅ Yes" if len(jobs_found) > 0 else "❌ No")
            table.add_row("Click-and-Wait Working", "✅ Yes" if any(job.get('deep_scraped') for job in jobs_found) else "❌ No")
            table.add_row("Real URLs Extracted", "✅ Yes" if any('eluta.ca/job/' in job['url'] or 'lever.co' in job['url'] or 'workday' in job['url'] for job in jobs_found) else "❌ No")
            
            console.print(table)
            
            # Detailed job analysis
            if jobs_found:
                console.print(f"\n[bold green]✅ SUCCESS: Found {len(jobs_found)} jobs![/bold green]")
                console.print("[green]Enhanced anti-detection measures are working![/green]")
                
                for i, job in enumerate(jobs_found, 1):
                    console.print(f"\n[cyan]Job {i} Details:[/cyan]")
                    console.print(f"  Title: {job['title']}")
                    console.print(f"  Company: {job['company']}")
                    console.print(f"  Location: {job['location']}")
                    console.print(f"  URL: {job['url']}")
                    console.print(f"  Deep Scraped: {job.get('deep_scraped', False)}")
                    console.print(f"  Site: {job.get('site', 'unknown')}")
                
                return True
            else:
                console.print(f"\n[red]❌ FAILURE: No jobs found[/red]")
                console.print("[yellow]This could indicate:[/yellow]")
                console.print("[yellow]  • Bot detection is still blocking access[/yellow]")
                console.print("[yellow]  • Manual verification was not completed[/yellow]")
                console.print("[yellow]  • Network or site issues[/yellow]")
                console.print("[yellow]  • Need to adjust anti-detection parameters[/yellow]")
                
                return False
    
    except ImportError as e:
        console.print(f"[red]❌ Import error: {e}[/red]")
        console.print("[yellow]Make sure all required modules are installed[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Test error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    console.print(Panel("🧪 Eluta Bot Detection Fix Test", style="bold blue"))
    
    console.print("[cyan]This test will validate the enhanced Eluta scraper with:[/cyan]")
    console.print("[cyan]  • Advanced stealth browser configuration[/cyan]")
    console.print("[cyan]  • Human-like behavior patterns[/cyan]")
    console.print("[cyan]  • Enhanced manual verification workflow[/cyan]")
    console.print("[cyan]  • Session persistence and recovery[/cyan]")
    console.print("[cyan]  • Click-and-wait job URL extraction[/cyan]")
    
    console.print("\n[yellow]⚠️ Note: If bot detection is triggered, you'll be guided through manual verification[/yellow]")
    console.print("[yellow]The browser will open visibly so you can complete any CAPTCHA if needed[/yellow]")
    
    input("\nPress Enter to start the test...")
    
    success = test_eluta_scraper_improvements()
    
    if success:
        console.print("\n[bold green]🎉 TEST PASSED: Eluta scraper improvements are working![/bold green]")
        console.print("[green]The enhanced anti-detection measures successfully extracted jobs[/green]")
    else:
        console.print("\n[bold red]❌ TEST FAILED: Issues detected with the scraper[/bold red]")
        console.print("[yellow]Check the output above for specific issues and solutions[/yellow]")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
