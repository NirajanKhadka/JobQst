#!/usr/bin/env python3
"""
Quick test to verify that the Eluta scraper no longer extracts review URLs.
This test specifically checks that canadastop100.com URLs are properly filtered out.
"""

import sys
from rich.console import Console
from rich.panel import Panel

console = Console()

def test_review_url_filtering():
    """Test that review URLs are properly filtered out."""
    
    console.print(Panel("🧪 Testing Review URL Filtering Fix", style="bold blue"))
    
    try:
        # Import required modules
        from scrapers.eluta_enhanced import ElutaEnhancedScraper
        from playwright.sync_api import sync_playwright
        import utils
        
        # Load test profile
        console.print("[cyan]📋 Loading test profile...[/cyan]")
        profile = utils.load_profile("Nirajan")
        console.print(f"[green]✅ Profile loaded: {profile['profile_name']}[/green]")
        
        # Test configuration - limit to just 1 job for quick testing
        test_config = {
            'comprehensive_mode': False,
            'deep_scraping': True,
        }
        
        # Temporarily modify keywords to just one for faster testing
        original_keywords = profile.get('keywords', [])
        profile['keywords'] = [original_keywords[0]] if original_keywords else ['analyst']
        
        console.print("[cyan]🚀 Starting quick test with enhanced filtering...[/cyan]")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Visible for debugging
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            scraper = ElutaEnhancedScraper(profile, browser_context=context, **test_config)
            
            console.print("[bold yellow]🔍 Testing URL filtering...[/bold yellow]")
            console.print("[yellow]Looking for jobs and checking that NO canadastop100.com URLs are extracted[/yellow]")
            
            jobs_found = []
            review_urls_found = []
            
            try:
                # Test just the first few jobs
                job_count = 0
                max_test_jobs = 2
                
                for job in scraper.scrape_jobs():
                    job_count += 1
                    jobs_found.append(job)
                    
                    job_url = job.get('url', '')
                    apply_url = job.get('apply_url', '')
                    
                    console.print(f"\n[cyan]Job {job_count}:[/cyan]")
                    console.print(f"  Title: {job['title']}")
                    console.print(f"  Company: {job['company']}")
                    console.print(f"  URL: {job_url}")
                    console.print(f"  Apply URL: {apply_url}")
                    
                    # Check for review URLs (these should NOT be present)
                    if any(bad_domain in job_url for bad_domain in [
                        'canadastop100.com', 'reviews.', 'top-employer', 'employer-review'
                    ]):
                        review_urls_found.append(job_url)
                        console.print(f"[bold red]❌ FOUND REVIEW URL: {job_url}[/bold red]")
                    
                    if any(bad_domain in apply_url for bad_domain in [
                        'canadastop100.com', 'reviews.', 'top-employer', 'employer-review'
                    ]):
                        review_urls_found.append(apply_url)
                        console.print(f"[bold red]❌ FOUND REVIEW APPLY URL: {apply_url}[/bold red]")
                    
                    if job_count >= max_test_jobs:
                        console.print(f"[yellow]🛑 Stopping test after {max_test_jobs} jobs[/yellow]")
                        break
                
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠️ Test interrupted by user[/yellow]")
            except Exception as e:
                console.print(f"\n[red]❌ Test error: {e}[/red]")
                import traceback
                traceback.print_exc()
            
            finally:
                browser.close()
            
            # Test results
            console.print(f"\n[bold blue]📊 Test Results:[/bold blue]")
            console.print(f"[cyan]Jobs found: {len(jobs_found)}[/cyan]")
            console.print(f"[cyan]Review URLs found: {len(review_urls_found)}[/cyan]")
            
            if review_urls_found:
                console.print(f"\n[bold red]❌ TEST FAILED: Found {len(review_urls_found)} review URLs![/bold red]")
                for url in review_urls_found:
                    console.print(f"[red]  - {url}[/red]")
                return False
            elif len(jobs_found) > 0:
                console.print(f"\n[bold green]✅ TEST PASSED: Found {len(jobs_found)} jobs with NO review URLs![/bold green]")
                console.print("[green]The filtering fix is working correctly![/green]")
                
                # Show the valid URLs we found
                for i, job in enumerate(jobs_found, 1):
                    console.print(f"\n[green]Valid Job {i}:[/green]")
                    console.print(f"  URL: {job['url']}")
                    console.print(f"  Apply URL: {job.get('apply_url', 'N/A')}")
                
                return True
            else:
                console.print(f"\n[yellow]⚠️ TEST INCONCLUSIVE: No jobs found[/yellow]")
                console.print("[yellow]This could be due to bot detection or other issues[/yellow]")
                return False
    
    except ImportError as e:
        console.print(f"[red]❌ Import error: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Test error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    console.print(Panel("🧪 Review URL Filtering Test", style="bold blue"))
    
    console.print("[cyan]This test verifies that the Eluta scraper no longer extracts canadastop100.com review URLs[/cyan]")
    console.print("[yellow]⚠️ If bot detection is triggered, complete the verification manually[/yellow]")
    
    input("\nPress Enter to start the test...")
    
    success = test_review_url_filtering()
    
    if success:
        console.print("\n[bold green]🎉 SUCCESS: Review URL filtering is working![/bold green]")
        console.print("[green]The scraper now properly excludes canadastop100.com URLs[/green]")
    else:
        console.print("\n[bold red]❌ FAILURE: Review URLs are still being extracted[/bold red]")
        console.print("[yellow]The filtering logic needs further refinement[/yellow]")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
