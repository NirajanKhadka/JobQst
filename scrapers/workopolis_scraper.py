"""
Workopolis.com Scraper
Major Canadian job board scraper.
"""

import time
import urllib.parse
from typing import Dict, Generator
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from rich.console import Console

from .base_scraper import BaseJobScraper

console = Console()


class WorkopolisScraper(BaseJobScraper):
    """
    Scraper for Workopolis.com - Major Canadian job board.
    Uses natural human-like search flow.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)
        self.site_name = "Workopolis"
        self.base_url = "https://www.workopolis.com"
        self.requires_browser = True  # Workopolis uses JavaScript
        self.rate_limit_delay = (1.5, 3.0)
    
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """
        Scrape jobs from Workopolis using human-like search flow.
        
        Yields:
            Normalized job dictionaries
        """
        if not self.browser_context:
            console.print("[yellow]Workopolis scraper requires browser context. Skipping.[/yellow]")
            return
        
        yield from self._scrape_with_browser()
    
    def _scrape_with_browser(self) -> Generator[Dict, None, None]:
        """
        Scrape Workopolis using natural search flow.
        """
        page_num = self.current_index // 20 + 1  # Workopolis typically shows 20 jobs per page
        console.print(f"[cyan]Scraping Workopolis (page {page_num})[/cyan]")
        
        page = self.browser_context.new_page()
        
        try:
            if page_num == 1:
                # Start from homepage
                console.print("[cyan]Starting from Workopolis homepage...[/cyan]")
                page.goto(f"{self.base_url}/jobs", timeout=30000)
                
                # Wait for page to load
                page.wait_for_load_state("networkidle", timeout=15000)
                
                # Fill search form
                keywords_field = page.query_selector("input[name='keywords'], input[placeholder*='job'], input[id*='keyword']")
                if keywords_field:
                    console.print(f"[cyan]Entering keywords: {self.search_terms}[/cyan]")
                    keywords_field.fill(self.search_terms)
                
                location_field = page.query_selector("input[name='location'], input[placeholder*='location'], input[id*='location']")
                if location_field:
                    console.print(f"[cyan]Entering location: {self.city}[/cyan]")
                    location_field.fill(self.city)
                
                # Submit search
                search_button = page.query_selector("button[type='submit'], input[type='submit'], .search-btn")
                if search_button:
                    console.print("[cyan]Submitting search...[/cyan]")
                    search_button.click()
                else:
                    if keywords_field:
                        keywords_field.press("Enter")
                
                page.wait_for_load_state("networkidle", timeout=20000)
                
            else:
                # Direct URL for pagination
                encoded_search = urllib.parse.quote_plus(self.search_terms)
                encoded_location = urllib.parse.quote_plus(self.city)
                search_url = f"{self.base_url}/jobs/search?keywords={encoded_search}&location={encoded_location}&page={page_num}"
                
                console.print(f"[cyan]Navigating to page {page_num}[/cyan]")
                page.goto(search_url, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)

            # Wait for job results
            try:
                page.wait_for_selector(".job-listing, .job-result, .job-card", timeout=15000)
                console.print("[green]✅ Workopolis results loaded[/green]")
            except PlaywrightTimeoutError:
                console.print("[yellow]⚠️ Timeout waiting for Workopolis results[/yellow]")
                return
            
            # Check for no results
            if "no jobs found" in page.content().lower() or "0 results" in page.content().lower():
                console.print("[yellow]No more results on Workopolis[/yellow]")
                return
            
            # Extract job listings
            job_elements = page.query_selector_all(".job-listing, .job-result, .job-card, article")
            
            if not job_elements:
                console.print("[yellow]No job elements found on Workopolis[/yellow]")
                return

            console.print(f"[green]✅ Found {len(job_elements)} jobs on Workopolis[/green]")
            
            for job_elem in job_elements:
                try:
                    job = self._extract_job_from_element(job_elem)
                    if job:
                        yield self.normalize_job(job)
                except Exception as e:
                    console.print(f"[yellow]Error extracting Workopolis job: {e}[/yellow]")
                    continue
            
            # Update pagination
            self.current_index += 20
            
        except Exception as e:
            console.print(f"[red]Error scraping Workopolis: {e}[/red]")
        finally:
            page.close()
    
    def _extract_job_from_element(self, job_elem) -> Dict:
        """
        Extract job data from a Workopolis job element.
        
        Args:
            job_elem: Playwright element representing a job listing
            
        Returns:
            Job dictionary or None if extraction fails
        """
        try:
            # Extract job title and URL
            title_elem = job_elem.query_selector("h2 a, h3 a, .job-title a, a[href*='job']")
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
            company_elem = job_elem.query_selector(".company-name, .employer, .company")
            company = company_elem.inner_text().strip() if company_elem else "Unknown Company"
            
            # Extract location
            location_elem = job_elem.query_selector(".location, .job-location, .city")
            location = location_elem.inner_text().strip() if location_elem else ""
            
            # Extract summary
            summary_elem = job_elem.query_selector(".job-description, .description, .summary, .snippet")
            summary = summary_elem.inner_text().strip() if summary_elem else ""
            
            # Extract salary
            salary_elem = job_elem.query_selector(".salary, .wage, .pay, .compensation")
            salary = salary_elem.inner_text().strip() if salary_elem else ""
            
            # Extract job type
            job_type_elem = job_elem.query_selector(".job-type, .employment-type, .type")
            job_type = job_type_elem.inner_text().strip() if job_type_elem else ""
            
            # Extract posted date
            date_elem = job_elem.query_selector(".date-posted, .posted-date, .date, .posted")
            posted_date = date_elem.inner_text().strip() if date_elem else ""
            
            console.print(f"[cyan]📋 Workopolis: '{title}' at '{company}' in '{location}'[/cyan]")
            
            # Validate required fields
            if not title or not company:
                console.print(f"[yellow]⚠️ Skipping Workopolis job with missing data[/yellow]")
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
            console.print(f"[yellow]Error extracting Workopolis job data: {e}[/yellow]")
            return None
