#!/usr/bin/env python3
"""
Eluta Site Structure Analysis Tool
This script analyzes the actual HTML structure of Eluta.ca to understand
how job listings are organized and how to properly scrape them.
"""

import time
from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def analyze_eluta_structure():
    """Analyze the actual Eluta.ca site structure."""
    
    console.print(Panel("🔍 Eluta Site Structure Analysis", style="bold blue"))
    
    with sync_playwright() as p:
        # Launch visible browser for analysis
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # Navigate to Eluta search page
            search_url = "https://www.eluta.ca/search?q=analyst&l=Toronto"
            console.print(f"[cyan]🌐 Navigating to: {search_url}[/cyan]")
            page.goto(search_url, timeout=30000)
            
            # Wait for page to load
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
            
            console.print("[cyan]📋 Analyzing page structure...[/cyan]")
            
            # 1. Analyze overall page structure
            console.print("\n[bold yellow]1. OVERALL PAGE STRUCTURE[/bold yellow]")
            
            # Check for main content containers
            main_containers = [
                "main", ".main", "#main",
                ".content", "#content", 
                ".jobs", ".job-list", ".search-results",
                ".container", ".wrapper"
            ]
            
            for selector in main_containers:
                try:
                    element = page.query_selector(selector)
                    if element:
                        console.print(f"[green]✅ Found main container: {selector}[/green]")
                except:
                    pass
            
            # 2. Analyze job listing structure
            console.print("\n[bold yellow]2. JOB LISTING STRUCTURE[/bold yellow]")
            
            # Look for job-related elements
            job_selectors = [
                ".job", ".job-item", ".job-listing", ".job-card",
                "[class*='job']", "[id*='job']",
                ".listing", ".result", ".search-result",
                "article", ".article"
            ]
            
            job_elements_found = {}
            for selector in job_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        job_elements_found[selector] = len(elements)
                        console.print(f"[green]✅ Found {len(elements)} elements with selector: {selector}[/green]")
                except:
                    pass
            
            # 3. Analyze the most promising job container
            if job_elements_found:
                # Find the selector with the most reasonable number of elements (likely job listings)
                best_selector = max(job_elements_found.items(), key=lambda x: x[1] if 3 <= x[1] <= 50 else 0)
                console.print(f"\n[bold green]🎯 Best job container candidate: {best_selector[0]} ({best_selector[1]} elements)[/bold green]")
                
                # Analyze the first few job elements
                elements = page.query_selector_all(best_selector[0])[:3]
                
                for i, element in enumerate(elements, 1):
                    console.print(f"\n[cyan]📋 Analyzing Job Element {i}:[/cyan]")
                    
                    # Get text content
                    text_content = element.inner_text().strip()
                    console.print(f"[yellow]Text content (first 200 chars):[/yellow]")
                    console.print(f"{text_content[:200]}...")
                    
                    # Look for links
                    links = element.query_selector_all("a")
                    console.print(f"[yellow]Links found: {len(links)}[/yellow]")
                    
                    for j, link in enumerate(links[:3]):  # Show first 3 links
                        href = link.get_attribute("href") or "No href"
                        link_text = link.inner_text().strip()[:50]
                        console.print(f"  Link {j+1}: {href} (text: '{link_text}...')")
                    
                    # Look for specific job data
                    job_data = {}
                    
                    # Try to find job title
                    title_selectors = ["h1", "h2", "h3", ".title", ".job-title", "[class*='title']"]
                    for sel in title_selectors:
                        try:
                            title_elem = element.query_selector(sel)
                            if title_elem:
                                job_data["title"] = title_elem.inner_text().strip()
                                break
                        except:
                            pass
                    
                    # Try to find company
                    company_selectors = [".company", ".employer", "[class*='company']", "[class*='employer']"]
                    for sel in company_selectors:
                        try:
                            company_elem = element.query_selector(sel)
                            if company_elem:
                                job_data["company"] = company_elem.inner_text().strip()
                                break
                        except:
                            pass
                    
                    # Try to find location
                    location_selectors = [".location", ".city", "[class*='location']", "[class*='city']"]
                    for sel in location_selectors:
                        try:
                            location_elem = element.query_selector(sel)
                            if location_elem:
                                job_data["location"] = location_elem.inner_text().strip()
                                break
                        except:
                            pass
                    
                    if job_data:
                        console.print(f"[green]📊 Extracted job data: {job_data}[/green]")
            
            # 4. Test click behavior
            console.print("\n[bold yellow]3. TESTING CLICK BEHAVIOR[/bold yellow]")
            
            if job_elements_found:
                console.print("[cyan]Testing click on first job element...[/cyan]")
                
                # Get the first job element
                first_job = page.query_selector(best_selector[0])
                if first_job:
                    # Get current URL
                    original_url = page.url
                    console.print(f"[yellow]Original URL: {original_url}[/yellow]")
                    
                    # Try clicking
                    try:
                        first_job.click()
                        console.print("[cyan]✅ Clicked on job element[/cyan]")
                        
                        # Wait and see what happens
                        time.sleep(2)
                        
                        new_url = page.url
                        console.print(f"[yellow]New URL: {new_url}[/yellow]")
                        
                        if new_url != original_url:
                            console.print("[green]✅ Navigation occurred![/green]")
                            
                            # Check if we're on a job details page
                            page_title = page.title()
                            console.print(f"[yellow]Page title: {page_title}[/yellow]")
                            
                            # Look for apply buttons or external links
                            apply_selectors = [
                                "a:has-text('Apply')", "button:has-text('Apply')",
                                "a[href*='apply']", "a[href*='job']",
                                "a[href^='http']:not([href*='eluta.ca'])"
                            ]
                            
                            for selector in apply_selectors:
                                try:
                                    apply_elements = page.query_selector_all(selector)
                                    if apply_elements:
                                        console.print(f"[green]✅ Found {len(apply_elements)} apply elements with: {selector}[/green]")
                                        
                                        # Show first few
                                        for elem in apply_elements[:2]:
                                            href = elem.get_attribute("href") or "No href"
                                            text = elem.inner_text().strip()[:30]
                                            console.print(f"  Apply link: {href} (text: '{text}...')")
                                except:
                                    pass
                        else:
                            console.print("[yellow]⚠️ No navigation occurred[/yellow]")
                    
                    except Exception as e:
                        console.print(f"[red]❌ Click failed: {e}[/red]")
            
            # 5. Summary and recommendations
            console.print("\n[bold yellow]4. ANALYSIS SUMMARY[/bold yellow]")
            
            table = Table(title="Eluta Structure Analysis Results")
            table.add_column("Component", style="cyan")
            table.add_column("Finding", style="green")
            table.add_column("Recommendation", style="yellow")
            
            if job_elements_found:
                best_selector_name = best_selector[0]
                best_count = best_selector[1]
                table.add_row("Job Container", f"Found: {best_selector_name}", f"Use this selector for job listings")
                table.add_row("Job Count", f"{best_count} elements", "Good number for scraping")
            else:
                table.add_row("Job Container", "Not found", "Need to investigate further")
            
            table.add_row("Click Behavior", "Tested", "Use 1-2 second wait as suggested")
            table.add_row("Site Complexity", "Analyzed", "Appears to be scrapable")
            
            console.print(table)
            
            input("\nPress Enter to close browser and continue...")
            
        except Exception as e:
            console.print(f"[red]❌ Analysis error: {e}[/red]")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

def main():
    """Main analysis function."""
    console.print(Panel("🔍 Eluta Site Structure Analyzer", style="bold blue"))
    console.print("[cyan]This tool will analyze the actual Eluta.ca structure to understand how to scrape it properly.[/cyan]")
    console.print("[yellow]A browser window will open for manual inspection.[/yellow]")
    
    input("\nPress Enter to start analysis...")
    
    analyze_eluta_structure()
    
    console.print("\n[bold green]🎉 Analysis complete![/bold green]")
    console.print("[cyan]Use the findings above to create a proper scraper.[/cyan]")

if __name__ == "__main__":
    main()
