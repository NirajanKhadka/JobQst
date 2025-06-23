#!/usr/bin/env python3
"""
Working Eluta Scraper - Based on Successful Analysis
This scraper uses the proven method:
1. Find .organic-job containers
2. Extract job data from text
3. Click on job title links
4. Use expect_popup() to capture new tab URLs
5. Extract real ATS application URLs
"""

import time
import re
from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class WorkingElutaScraper:
    def __init__(self):
        self.base_url = "https://www.eluta.ca/search"
        self.jobs_found = []
        
    def scrape_jobs(self, keyword="analyst", location="Canada", max_jobs=5):
        """Scrape jobs using the proven method."""
        
        console.print(Panel(f"🎯 Working Eluta Scraper - {keyword} in {location}", style="bold green"))
        console.print("[cyan]Using proven method: .organic-job + expect_popup()[/cyan]")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                # Handle Canada-wide search
                if location.lower() in ['canada', 'nationwide', 'all canada']:
                    # For Canada-wide search, use empty location or "Canada"
                    location_param = ""  # Empty location searches all of Canada on Eluta
                else:
                    location_param = location

                # Navigate to search
                search_url = f"{self.base_url}?q={keyword}&l={location_param}"
                console.print(f"[cyan]🌐 Navigating to: {search_url}[/cyan]")
                console.print(f"[yellow]🇨🇦 Searching across Canada for '{keyword}' jobs[/yellow]")
                
                page.goto(search_url, timeout=30000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(3)
                
                # Find job containers using proven selector
                job_elements = page.query_selector_all(".organic-job")
                console.print(f"[green]✅ Found {len(job_elements)} job listings[/green]")
                
                if not job_elements:
                    console.print("[red]❌ No job listings found[/red]")
                    return []
                
                # Process jobs (limit to max_jobs)
                jobs_to_process = min(len(job_elements), max_jobs)
                console.print(f"[cyan]📋 Processing {jobs_to_process} jobs...[/cyan]")
                
                for i, job_elem in enumerate(job_elements[:max_jobs]):
                    console.print(f"\n[bold cyan]--- Processing Job {i+1}/{jobs_to_process} ---[/bold cyan]")
                    
                    job_data = self._extract_job_data(job_elem, page, i+1)
                    if job_data:
                        self.jobs_found.append(job_data)
                        self._display_job_summary(job_data, i+1)
                    else:
                        console.print(f"[yellow]⚠️ Could not extract job {i+1}[/yellow]")
                    
                    # Small delay between jobs
                    if i < jobs_to_process - 1:
                        time.sleep(1)
                
                console.print(f"\n[bold green]🎉 Scraping complete! Successfully extracted {len(self.jobs_found)} jobs[/bold green]")
                
            except Exception as e:
                console.print(f"[red]❌ Scraping error: {e}[/red]")
                import traceback
                traceback.print_exc()
            
            finally:
                input("\nPress Enter to close browser...")
                browser.close()
        
        return self.jobs_found
    
    def _extract_job_data(self, job_elem, page, job_number):
        """Extract complete job data including real application URL."""
        try:
            # Step 1: Extract basic job data from text
            text = job_elem.inner_text().strip()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if len(lines) < 2:
                console.print(f"[yellow]⚠️ Job {job_number}: Insufficient text content[/yellow]")
                return None
            
            job_data = {
                "title": "",
                "company": "",
                "location": "",
                "salary": "",
                "description": "",
                "url": "",
                "apply_url": "",
                "source": "eluta.ca",
                "ats_system": "",
                "scraped_successfully": False
            }
            
            # Parse title and salary
            title_line = lines[0]
            salary_match = re.search(r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?', title_line)
            if salary_match:
                job_data["salary"] = salary_match.group(0)
                job_data["title"] = title_line.replace(salary_match.group(0), "").strip()
            else:
                job_data["title"] = title_line
            
            # Parse company (remove "TOP EMPLOYER" tag)
            if len(lines) > 1:
                company_line = lines[1]
                job_data["company"] = company_line.replace("TOP EMPLOYER", "").strip()
            
            # Parse location
            if len(lines) > 2:
                job_data["location"] = lines[2]
            
            # Parse description
            if len(lines) > 3:
                job_data["description"] = " ".join(lines[3:])[:300] + "..."
            
            console.print(f"[cyan]📋 Basic data: {job_data['title'][:40]}... at {job_data['company']}[/cyan]")
            
            # Step 2: Get real application URL using proven method
            real_url = self._get_real_job_url(job_elem, page, job_number)
            if real_url:
                job_data["apply_url"] = real_url
                job_data["url"] = real_url  # Use real URL as primary URL
                job_data["scraped_successfully"] = True
                
                # Detect ATS system
                job_data["ats_system"] = self._detect_ats_system(real_url)
                
                console.print(f"[green]✅ Got real URL: {real_url[:60]}...[/green]")
                console.print(f"[cyan]🏢 ATS System: {job_data['ats_system']}[/cyan]")
            else:
                # Fallback to search page URL
                job_data["url"] = page.url
                job_data["apply_url"] = page.url
                console.print(f"[yellow]⚠️ Using fallback URL[/yellow]")
            
            return job_data
            
        except Exception as e:
            console.print(f"[red]❌ Error extracting job {job_number}: {e}[/red]")
            return None
    
    def _get_real_job_url(self, job_elem, page, job_number):
        """Get real job URL using the proven expect_popup method."""
        try:
            # Find job title link
            links = job_elem.query_selector_all("a")
            title_link = None
            
            for link in links:
                link_text = link.inner_text().strip()
                if link_text and len(link_text) > 10:  # Likely a job title
                    title_link = link
                    break
            
            if not title_link:
                console.print(f"[yellow]⚠️ No title link found for job {job_number}[/yellow]")
                return None
            
            # Use proven expect_popup method
            console.print(f"[cyan]🖱️ Clicking title link for job {job_number}...[/cyan]")
            
            with page.expect_popup(timeout=5000) as popup_info:
                title_link.click()
            
            popup = popup_info.value
            popup_url = popup.url
            
            # Close popup immediately
            popup.close()
            
            return popup_url
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not get real URL for job {job_number}: {e}[/yellow]")
            return None
    
    def _detect_ats_system(self, url):
        """Detect the ATS system from URL."""
        if not url:
            return "Unknown"
        
        ats_systems = {
            "workday": "Workday",
            "myworkday": "Workday", 
            "ultipro": "UltiPro",
            "greenhouse": "Greenhouse",
            "lever.co": "Lever",
            "icims": "iCIMS",
            "bamboohr": "BambooHR",
            "smartrecruiters": "SmartRecruiters",
            "jobvite": "Jobvite",
            "taleo": "Taleo",
            "successfactors": "SuccessFactors"
        }
        
        url_lower = url.lower()
        for keyword, system in ats_systems.items():
            if keyword in url_lower:
                return system
        
        return "Company Website"
    
    def _display_job_summary(self, job_data, job_number):
        """Display a summary of the extracted job."""
        console.print(f"[bold green]📋 Job {job_number} Summary:[/bold green]")
        console.print(f"[cyan]  Title:[/cyan] {job_data['title']}")
        console.print(f"[cyan]  Company:[/cyan] {job_data['company']}")
        console.print(f"[cyan]  Location:[/cyan] {job_data['location']}")
        if job_data['salary']:
            console.print(f"[cyan]  Salary:[/cyan] {job_data['salary']}")
        console.print(f"[cyan]  ATS:[/cyan] {job_data['ats_system']}")
        console.print(f"[cyan]  Success:[/cyan] {'✅ Yes' if job_data['scraped_successfully'] else '❌ No'}")
    
    def display_results_table(self):
        """Display results in a nice table."""
        if not self.jobs_found:
            console.print("[yellow]No jobs to display[/yellow]")
            return
        
        table = Table(title=f"Eluta Scraping Results ({len(self.jobs_found)} jobs)")
        table.add_column("Title", style="cyan", width=25)
        table.add_column("Company", style="green", width=20)
        table.add_column("Location", style="yellow", width=12)
        table.add_column("Salary", style="magenta", width=12)
        table.add_column("ATS", style="blue", width=10)
        table.add_column("Success", style="bold", width=8)
        
        for job in self.jobs_found:
            table.add_row(
                job['title'][:22] + "..." if len(job['title']) > 25 else job['title'],
                job['company'][:17] + "..." if len(job['company']) > 20 else job['company'],
                job['location'],
                job['salary'] or "N/A",
                job['ats_system'],
                "✅" if job['scraped_successfully'] else "❌"
            )
        
        console.print(table)
        
        # Show success rate
        successful = sum(1 for job in self.jobs_found if job['scraped_successfully'])
        success_rate = (successful / len(self.jobs_found)) * 100
        console.print(f"\n[bold green]Success Rate: {successful}/{len(self.jobs_found)} ({success_rate:.1f}%)[/bold green]")

def main():
    """Main function for testing."""
    scraper = WorkingElutaScraper()
    jobs = scraper.scrape_jobs("python developer", "Canada", max_jobs=3)
    scraper.display_results_table()

if __name__ == "__main__":
    main()

# Backward compatibility alias for tests
ElutaWorkingScraper = WorkingElutaScraper
