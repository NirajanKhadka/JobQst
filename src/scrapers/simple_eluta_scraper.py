#!/usr/bin/env python3
"""
Simple Eluta Scraper - Based on Actual Site Analysis
This scraper is built from real analysis of Eluta.ca structure.
"""

import time
import re
from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class SimpleElutaScraper:
    def __init__(self):
        self.base_url = "https://www.eluta.ca/search"
        self.jobs_found = []
        
    def scrape_jobs(self, keyword="analyst", location="Toronto", max_jobs=5):
        """Scrape jobs from Eluta using the analyzed structure."""
        
        console.print(Panel(f"🔍 Simple Eluta Scraper - {keyword} in {location}", style="bold blue"))
        
        with sync_playwright() as p:
            # Launch browser (visible for debugging)
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                # Build search URL
                search_url = f"{self.base_url}?q={keyword}&l={location}"
                console.print(f"[cyan]🌐 Navigating to: {search_url}[/cyan]")
                
                # Navigate to search page
                page.goto(search_url, timeout=30000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(3)  # Wait for JavaScript to load
                
                console.print("[cyan]📋 Looking for job listings...[/cyan]")
                
                # Use the discovered selector: .organic-job
                job_elements = page.query_selector_all(".organic-job")
                console.print(f"[green]✅ Found {len(job_elements)} job listings[/green]")
                
                # Process each job (limit to max_jobs)
                for i, job_elem in enumerate(job_elements[:max_jobs]):
                    console.print(f"\n[cyan]📋 Processing Job {i+1}/{min(len(job_elements), max_jobs)}[/cyan]")
                    
                    job_data = self._extract_job_data(job_elem, page, i+1)
                    if job_data:
                        self.jobs_found.append(job_data)
                        self._display_job(job_data, i+1)
                    else:
                        console.print(f"[yellow]⚠️ Could not extract job {i+1}[/yellow]")
                
                console.print(f"\n[bold green]🎉 Scraping complete! Found {len(self.jobs_found)} jobs[/bold green]")
                
            except Exception as e:
                console.print(f"[red]❌ Scraping error: {e}[/red]")
                import traceback
                traceback.print_exc()
            
            finally:
                input("\nPress Enter to close browser...")
                browser.close()
        
        return self.jobs_found
    
    def _extract_job_data(self, job_elem, page, job_number):
        """Extract job data from a job element."""
        try:
            # Get all text content
            full_text = job_elem.inner_text().strip()
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            
            if len(lines) < 3:
                console.print(f"[yellow]⚠️ Job {job_number}: Not enough text lines[/yellow]")
                return None
            
            # Parse the structure based on analysis
            job_data = {
                "title": "",
                "company": "",
                "location": "",
                "salary": "",
                "description": "",
                "url": "",
                "source": "eluta.ca"
            }
            
            # Extract title (first line, may include salary)
            title_line = lines[0]
            
            # Check if salary is in title line
            salary_match = re.search(r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?', title_line)
            if salary_match:
                job_data["salary"] = salary_match.group(0)
                job_data["title"] = title_line.replace(salary_match.group(0), "").strip()
            else:
                job_data["title"] = title_line
            
            # Extract company (second line, remove "TOP EMPLOYER" if present)
            if len(lines) > 1:
                company_line = lines[1]
                job_data["company"] = company_line.replace("TOP EMPLOYER", "").strip()
            
            # Extract location (third line)
            if len(lines) > 2:
                job_data["location"] = lines[2]
            
            # Extract description (remaining lines)
            if len(lines) > 3:
                job_data["description"] = " ".join(lines[3:])[:200] + "..."
            
            # Try to get job URL by clicking (your suggestion: click and wait 1 sec)
            job_url = self._get_job_url(job_elem, page, job_number)
            job_data["url"] = job_url
            
            return job_data
            
        except Exception as e:
            console.print(f"[red]❌ Error extracting job {job_number}: {e}[/red]")
            return None
    
    def _get_job_url(self, job_elem, page, job_number):
        """Try to get the real job URL by clicking and waiting."""
        try:
            console.print(f"[cyan]🖱️ Attempting to get URL for job {job_number}...[/cyan]")
            
            # Store original URL
            original_url = page.url
            
            # Try clicking on the job element
            job_elem.click()
            
            # Wait 1 second as you suggested
            console.print("[yellow]⏳ Waiting 1 second for navigation...[/yellow]")
            time.sleep(1)
            
            # Check if URL changed
            new_url = page.url
            
            if new_url != original_url:
                console.print(f"[green]✅ Got job URL: {new_url}[/green]")
                
                # Go back to search results for next job
                page.go_back()
                time.sleep(1)
                
                return new_url
            else:
                console.print(f"[yellow]⚠️ No navigation occurred for job {job_number}[/yellow]")
                
                # Try clicking on links within the job element
                links = job_elem.query_selector_all("a")
                for i, link in enumerate(links[:2]):  # Try first 2 links
                    try:
                        console.print(f"[cyan]🔗 Trying link {i+1} in job element...[/cyan]")
                        link.click()
                        time.sleep(1)
                        
                        new_url = page.url
                        if new_url != original_url:
                            console.print(f"[green]✅ Link {i+1} worked: {new_url}[/green]")
                            page.go_back()
                            time.sleep(1)
                            return new_url
                    except:
                        continue
                
                # If no navigation worked, return the search page URL
                return original_url
                
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not get URL for job {job_number}: {e}[/yellow]")
            return page.url
    
    def _display_job(self, job_data, job_number):
        """Display job data in a nice format."""
        console.print(f"\n[bold green]📋 Job {job_number}:[/bold green]")
        console.print(f"[cyan]Title:[/cyan] {job_data['title']}")
        console.print(f"[cyan]Company:[/cyan] {job_data['company']}")
        console.print(f"[cyan]Location:[/cyan] {job_data['location']}")
        if job_data['salary']:
            console.print(f"[cyan]Salary:[/cyan] {job_data['salary']}")
        console.print(f"[cyan]URL:[/cyan] {job_data['url']}")
        if job_data['description']:
            console.print(f"[cyan]Description:[/cyan] {job_data['description']}")
    
    def display_summary(self):
        """Display a summary table of all jobs found."""
        if not self.jobs_found:
            console.print("[yellow]No jobs found to display[/yellow]")
            return
        
        table = Table(title=f"Eluta Jobs Summary ({len(self.jobs_found)} jobs)")
        table.add_column("Title", style="cyan", width=30)
        table.add_column("Company", style="green", width=20)
        table.add_column("Location", style="yellow", width=15)
        table.add_column("Salary", style="magenta", width=15)
        
        for job in self.jobs_found:
            table.add_row(
                job['title'][:27] + "..." if len(job['title']) > 30 else job['title'],
                job['company'][:17] + "..." if len(job['company']) > 20 else job['company'],
                job['location'],
                job['salary'] or "Not specified"
            )
        
        console.print(table)

def main():
    """Main function to test the simple scraper."""
    console.print(Panel("🔍 Simple Eluta Scraper Test", style="bold blue"))
    console.print("[cyan]This scraper is built from actual site analysis of Eluta.ca[/cyan]")
    console.print("[yellow]It uses the discovered .organic-job selector and click-and-wait approach[/yellow]")
    
    # Get user input
    keyword = input("\nEnter job keyword (default: analyst): ").strip() or "analyst"
    location = input("Enter location (default: Toronto): ").strip() or "Toronto"
    max_jobs = input("Enter max jobs to scrape (default: 3): ").strip()
    max_jobs = int(max_jobs) if max_jobs.isdigit() else 3
    
    # Create and run scraper
    scraper = SimpleElutaScraper()
    jobs = scraper.scrape_jobs(keyword, location, max_jobs)
    
    # Display results
    if jobs:
        console.print(f"\n[bold green]🎉 Successfully scraped {len(jobs)} jobs![/bold green]")
        scraper.display_summary()
    else:
        console.print("\n[red]❌ No jobs were scraped[/red]")
        console.print("[yellow]This could be due to:[/yellow]")
        console.print("[yellow]  • Bot detection blocking access[/yellow]")
        console.print("[yellow]  • JavaScript not executing properly[/yellow]")
        console.print("[yellow]  • Site structure changes[/yellow]")

if __name__ == "__main__":
    main()
