"""
Kijiji Jobs Scraper
Canada's largest classifieds site job section scraper.
"""

import time
import urllib.parse
from typing import Dict, Generator
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from rich.console import Console

from .base_scraper import BaseJobScraper

console = Console()


class KijijiScraper(BaseJobScraper):
    """
    Scraper for Kijiji.ca jobs section - Canada's largest classifieds.
    Uses natural human-like search flow.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)
        self.site_name = "Kijiji"
        self.base_url = "https://www.kijiji.ca"
        self.requires_browser = True  # Kijiji uses JavaScript
        self.rate_limit_delay = (2.0, 4.0)  # Be respectful to avoid blocking
    
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """
        Scrape jobs from Kijiji using human-like search flow.
        
        Yields:
            Normalized job dictionaries
        """
        if not self.browser_context:
            console.print("[yellow]Kijiji scraper requires browser context. Skipping.[/yellow]")
            return
        
        yield from self._scrape_with_browser()
    
    def _scrape_with_browser(self) -> Generator[Dict, None, None]:
        """
        Scrape Kijiji jobs using natural search flow.
        """
        page_num = self.current_index // 20 + 1  # Kijiji shows ~20 ads per page
        console.print(f"[cyan]Scraping Kijiji Jobs (page {page_num})[/cyan]")
        
        page = self.browser_context.new_page()
        
        try:
            if page_num == 1:
                # Start from jobs homepage
                console.print("[cyan]Starting from Kijiji Jobs homepage...[/cyan]")
                page.goto(f"{self.base_url}/b-jobs/canada/c45", timeout=30000)
                
                # Wait for page to load
                page.wait_for_load_state("networkidle", timeout=15000)
                
                # Fill search form
                keywords_field = page.query_selector("input[name='keywords'], input[placeholder*='search'], #SearchKeyword")
                if keywords_field:
                    console.print(f"[cyan]Entering keywords: {self.search_terms}[/cyan]")
                    keywords_field.fill(self.search_terms)
                
                # Location is usually handled by selecting a city/province
                # Try to find location field or dropdown
                location_field = page.query_selector("input[name='locationId'], input[placeholder*='location'], #locationId")
                if location_field:
                    console.print(f"[cyan]Entering location: {self.city}[/cyan]")
                    location_field.fill(self.city)
                
                # Submit search
                search_button = page.query_selector("button[type='submit'], input[type='submit'], .search-button")
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
                search_url = f"{self.base_url}/b-jobs/canada/{encoded_search}/k0c45l0?page={page_num}"
                
                console.print(f"[cyan]Navigating to page {page_num}[/cyan]")
                page.goto(search_url, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)

            # Wait for job results
            try:
                page.wait_for_selector(".search-item, .regular-ad, .ad-container", timeout=15000)
                console.print("[green]✅ Kijiji results loaded[/green]")
            except PlaywrightTimeoutError:
                console.print("[yellow]⚠️ Timeout waiting for Kijiji results[/yellow]")
                return
            
            # Check for no results
            if "no ads were found" in page.content().lower() or "0 ads" in page.content().lower():
                console.print("[yellow]No more results on Kijiji[/yellow]")
                return
            
            # Extract job listings
            job_elements = page.query_selector_all(".search-item, .regular-ad, .ad-container")
            
            if not job_elements:
                console.print("[yellow]No job elements found on Kijiji[/yellow]")
                return

            console.print(f"[green]✅ Found {len(job_elements)} jobs on Kijiji[/green]")
            
            for job_elem in job_elements:
                try:
                    job = self._extract_job_from_element(job_elem)
                    if job:
                        yield self.normalize_job(job)
                except Exception as e:
                    console.print(f"[yellow]Error extracting Kijiji job: {e}[/yellow]")
                    continue
            
            # Update pagination
            self.current_index += 20
            
        except Exception as e:
            console.print(f"[red]Error scraping Kijiji: {e}[/red]")
        finally:
            page.close()
    
    def _extract_job_from_element(self, job_elem) -> Dict:
        """
        Extract job data from a Kijiji job element.
        
        Args:
            job_elem: Playwright element representing a job listing
            
        Returns:
            Job dictionary or None if extraction fails
        """
        try:
            # Extract job title and URL
            title_elem = job_elem.query_selector(".title a, .ad-title a, a[href*='v-']")
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
            
            # Extract location
            location_elem = job_elem.query_selector(".location, .ad-location")
            location = location_elem.inner_text().strip() if location_elem else ""
            
            # Extract description/summary
            desc_elem = job_elem.query_selector(".description, .ad-description")
            summary = desc_elem.inner_text().strip() if desc_elem else ""
            
            # Extract price/salary (Kijiji shows this for some job ads)
            price_elem = job_elem.query_selector(".price, .ad-price")
            salary = price_elem.inner_text().strip() if price_elem else ""
            
            # Extract posted date
            date_elem = job_elem.query_selector(".date-posted, .posted")
            posted_date = date_elem.inner_text().strip() if date_elem else ""
            
            # For Kijiji, company is often not explicitly shown, extract from description or use "Private Seller"
            company = "Private Seller"
            if summary:
                # Try to extract company name from description
                lines = summary.split('\n')
                for line in lines[:3]:  # Check first few lines
                    if any(word in line.lower() for word in ['company', 'corp', 'inc', 'ltd', 'llc']):
                        company = line.strip()
                        break
            
            console.print(f"[cyan]📋 Kijiji: '{title}' at '{company}' in '{location}'[/cyan]")
            
            # Validate required fields
            if not title:
                console.print(f"[yellow]⚠️ Skipping Kijiji job with missing title[/yellow]")
                return None
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "url": job_url,
                "apply_url": job_url,
                "summary": summary,
                "salary": salary,
                "job_type": "Various",  # Kijiji doesn't standardize job types
                "posted_date": posted_date,
            }
            
        except Exception as e:
            console.print(f"[yellow]Error extracting Kijiji job data: {e}[/yellow]")
            return None
