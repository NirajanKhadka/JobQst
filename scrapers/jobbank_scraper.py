"""
JobBank.gc.ca Scraper
Official Government of Canada job site scraper.
"""

import time
import urllib.parse
from typing import Dict, Generator
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from rich.console import Console

from .base_scraper import BaseJobScraper

console = Console()


class JobBankScraper(BaseJobScraper):
    """
    Scraper for JobBank.gc.ca - Government of Canada's official job site.
    Uses natural human-like search flow.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)
        self.site_name = "JobBank"
        self.base_url = "https://www.jobbank.gc.ca"
        self.requires_browser = True  # JobBank uses JavaScript
        self.rate_limit_delay = (2.0, 4.0)  # Be respectful to government site
    
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """
        Scrape jobs from JobBank using human-like search flow.
        
        Yields:
            Normalized job dictionaries
        """
        if not self.browser_context:
            console.print("[yellow]JobBank scraper requires browser context. Skipping.[/yellow]")
            return
        
        yield from self._scrape_with_browser()
    
    def _scrape_with_browser(self) -> Generator[Dict, None, None]:
        """
        Scrape JobBank using natural search flow like a human user.
        """
        page_num = self.current_index // 25 + 1  # JobBank shows 25 jobs per page
        console.print(f"[cyan]Scraping JobBank (page {page_num})[/cyan]")
        
        page = self.browser_context.new_page()
        
        try:
            if page_num == 1:
                # Start from homepage like a normal user
                console.print("[cyan]Starting from JobBank homepage...[/cyan]")
                page.goto(f"{self.base_url}/jobsearch/jobsearch", timeout=30000)
                
                # Wait for page to load
                page.wait_for_load_state("networkidle", timeout=15000)
                
                # Fill in search form like a normal user
                # Find job title/keywords field
                keywords_field = page.query_selector("input[name='searchstring'], input[id*='keyword'], input[placeholder*='job']")
                if keywords_field:
                    console.print(f"[cyan]Entering keywords: {self.search_terms}[/cyan]")
                    keywords_field.fill(self.search_terms)
                
                # Find location field
                location_field = page.query_selector("input[name='locationstring'], input[id*='location'], input[placeholder*='location']")
                if location_field:
                    console.print(f"[cyan]Entering location: {self.city}[/cyan]")
                    location_field.fill(self.city)
                
                # Submit search
                search_button = page.query_selector("button[type='submit'], input[type='submit'], .search-button")
                if search_button:
                    console.print("[cyan]Submitting search...[/cyan]")
                    search_button.click()
                else:
                    # Try pressing Enter
                    if keywords_field:
                        keywords_field.press("Enter")
                
                # Wait for results
                page.wait_for_load_state("networkidle", timeout=20000)
                
            else:
                # For subsequent pages, construct URL with pagination
                encoded_search = urllib.parse.quote_plus(self.search_terms)
                encoded_location = urllib.parse.quote_plus(self.city)
                search_url = f"{self.base_url}/jobsearch/jobsearch?searchstring={encoded_search}&locationstring={encoded_location}&page={page_num}"
                
                console.print(f"[cyan]Navigating to page {page_num}[/cyan]")
                page.goto(search_url, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)

            # Wait for job results
            try:
                page.wait_for_selector(".job-posting-brief, .job-result, article", timeout=15000)
                console.print("[green]✅ JobBank results loaded[/green]")
            except PlaywrightTimeoutError:
                console.print("[yellow]⚠️ Timeout waiting for JobBank results[/yellow]")
                return
            
            # Check for no results
            no_results = page.query_selector(".no-results, .noresults")
            if no_results or "0 jobs found" in page.content().lower():
                console.print("[yellow]No more results on JobBank[/yellow]")
                return
            
            # Extract job listings
            job_elements = page.query_selector_all(".job-posting-brief, .job-result, article")
            
            if not job_elements:
                console.print("[yellow]No job elements found on JobBank[/yellow]")
                return

            console.print(f"[green]✅ Found {len(job_elements)} jobs on JobBank[/green]")
            
            for job_elem in job_elements:
                try:
                    job = self._extract_job_from_element(job_elem)
                    if job:
                        yield self.normalize_job(job)
                except Exception as e:
                    console.print(f"[yellow]Error extracting JobBank job: {e}[/yellow]")
                    continue
            
            # Update pagination
            self.current_index += 25
            
        except Exception as e:
            console.print(f"[red]Error scraping JobBank: {e}[/red]")
        finally:
            page.close()
    
    def _extract_job_from_element(self, job_elem) -> Dict:
        """
        Extract job data from a JobBank job element.
        
        Args:
            job_elem: Playwright element representing a job listing
            
        Returns:
            Job dictionary or None if extraction fails
        """
        try:
            # Extract job title and URL
            title_elem = job_elem.query_selector("h3 a, .job-title a, a[href*='jobposting']")
            title = title_elem.inner_text().strip() if title_elem else ""
            
            # Extract job URL
            job_url = ""
            if title_elem:
                href = title_elem.get_attribute("href")
                if href:
                    if href.startswith("/"):
                        job_url = f"{self.base_url}{href}"
                    else:
                        job_url = href
            
            # Extract company name
            company_elem = job_elem.query_selector(".employer-name, .company-name, .employer")
            company = company_elem.inner_text().strip() if company_elem else "Government of Canada"
            
            # Extract location
            location_elem = job_elem.query_selector(".location, .job-location")
            location = location_elem.inner_text().strip() if location_elem else ""
            
            # Extract summary/description
            summary_elem = job_elem.query_selector(".job-description, .description, .summary")
            summary = summary_elem.inner_text().strip() if summary_elem else ""
            
            # Extract salary if available
            salary_elem = job_elem.query_selector(".salary, .wage, .pay")
            salary = salary_elem.inner_text().strip() if salary_elem else ""
            
            # Extract job type
            job_type_elem = job_elem.query_selector(".job-type, .employment-type")
            job_type = job_type_elem.inner_text().strip() if job_type_elem else ""
            
            # Extract posted date
            date_elem = job_elem.query_selector(".date-posted, .posted-date, .date")
            posted_date = date_elem.inner_text().strip() if date_elem else ""
            
            console.print(f"[cyan]📋 JobBank: '{title}' at '{company}' in '{location}'[/cyan]")
            
            # Validate required fields
            if not title:
                console.print(f"[yellow]⚠️ Skipping JobBank job with missing title[/yellow]")
                return None
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "url": job_url,
                "apply_url": job_url,
                "summary": summary,
                "salary": salary,
                "job_type": job_type,
                "posted_date": posted_date,
            }
            
        except Exception as e:
            console.print(f"[yellow]Error extracting JobBank job data: {e}[/yellow]")
            return None
