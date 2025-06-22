"""
Workday Job Scraper
Specialized scraper for Workday-based job portals like TD Bank.
"""

import time
from typing import Dict, Generator
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from rich.console import Console

from .base_scraper import BaseJobScraper

console = Console()


class WorkdayJobScraper(BaseJobScraper):
    """
    Specialized scraper for Workday-based job portals.
    Handles sites like TD Bank, RBC, and other companies using Workday.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)
        self.site_name = "Workday"
        self.base_url = ""  # Will be set based on the specific Workday instance
        self.requires_browser = True  # Workday requires JavaScript
        self.rate_limit_delay = (2.0, 4.0)  # Workday can be strict
        
        # Detect Workday instance from profile or set default
        self.workday_instance = self._detect_workday_instance()
    
    def _detect_workday_instance(self) -> str:
        """Detect which Workday instance to use based on profile or default to TD Bank."""
        # You can extend this to support multiple Workday instances
        return "https://td.wd3.myworkdayjobs.com/TD_Bank_Careers"
    
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """
        Scrape jobs from Workday using Playwright browser context.
        
        Yields:
            Normalized job dictionaries
        """
        if not self.browser_context:
            console.print("[yellow]Workday scraper requires browser context. Skipping.[/yellow]")
            return
        
        yield from self._scrape_with_browser()
    
    def _scrape_with_browser(self) -> Generator[Dict, None, None]:
        """
        Scrape Workday using Playwright browser context.
        """
        page_num = self.current_index // 20 + 1  # Workday typically shows 20 jobs per page
        console.print(f"[cyan]Scraping Workday (page {page_num})[/cyan]")
        
        page = self.browser_context.new_page()
        
        try:
            # Navigate to the Workday jobs search page
            search_url = f"{self.workday_instance}?q={self.search_terms}&locationCountry=f2e609fe92974b6ea9c6e6d62e6ca079"
            
            console.print(f"[green]Navigating to: {search_url}[/green]")
            page.goto(search_url, timeout=30000)
            
            # Wait for job results to load
            try:
                page.wait_for_selector("[data-automation-id='jobPostingItem'], .css-1q2dra3", timeout=15000)
            except PlaywrightTimeoutError:
                console.print("[yellow]Timeout waiting for Workday results[/yellow]")
                return
            
            # Handle cookie consent if present
            self._handle_cookie_consent(page)
            
            # Scroll to load more jobs (Workday uses lazy loading)
            self._scroll_to_load_jobs(page)
            
            # Extract job listings
            job_elements = page.query_selector_all("[data-automation-id='jobPostingItem'], .css-1q2dra3")
            
            if not job_elements:
                console.print("[yellow]No job elements found on Workday[/yellow]")
                return
            
            console.print(f"[green]Found {len(job_elements)} jobs on Workday[/green]")
            
            for job_elem in job_elements:
                try:
                    job = self._extract_job_from_element(job_elem, page)
                    if job:
                        yield self.normalize_job(job)
                except Exception as e:
                    console.print(f"[yellow]Error extracting Workday job: {e}[/yellow]")
                    continue
            
            # Update pagination
            self.current_index += 20
            
        except Exception as e:
            console.print(f"[red]Error scraping Workday: {e}[/red]")
        finally:
            page.close()
    
    def _handle_cookie_consent(self, page) -> None:
        """Handle cookie consent popup if present."""
        try:
            # Look for common cookie consent buttons
            cookie_buttons = [
                "button:has-text('Accept')",
                "button:has-text('Accept All')",
                "button:has-text('I Accept')",
                "[data-automation-id='cookieAcceptButton']",
                ".cookie-accept-button"
            ]
            
            for selector in cookie_buttons:
                if page.is_visible(selector):
                    page.click(selector)
                    console.print("[green]Accepted cookie consent[/green]")
                    time.sleep(1)
                    break
        except Exception:
            pass
    
    def _scroll_to_load_jobs(self, page) -> None:
        """Scroll down to trigger Workday's lazy loading."""
        try:
            # Scroll down multiple times to load more jobs
            for i in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                # Look for "Load More" button and click it
                load_more_selectors = [
                    "button:has-text('Load More')",
                    "button:has-text('Show More')",
                    "[data-automation-id='loadMoreJobs']",
                    ".load-more-button"
                ]
                
                for selector in load_more_selectors:
                    if page.is_visible(selector):
                        page.click(selector)
                        console.print("[green]Clicked Load More button[/green]")
                        time.sleep(3)
                        break
                        
        except Exception as e:
            console.print(f"[yellow]Error during scrolling: {e}[/yellow]")
    
    def _extract_job_from_element(self, job_elem, page) -> Dict:
        """
        Extract job data from a Workday job element.
        
        Args:
            job_elem: Playwright element representing a job listing
            page: Playwright page for additional operations
            
        Returns:
            Job dictionary or None if extraction fails
        """
        try:
            # Extract job title
            title_selectors = [
                "[data-automation-id='jobTitle']",
                ".css-cygeeu",
                "h3 a",
                ".job-title"
            ]
            
            title = ""
            job_url = ""
            
            for selector in title_selectors:
                title_elem = job_elem.query_selector(selector)
                if title_elem:
                    title = title_elem.inner_text().strip()
                    # Try to get the job URL
                    if title_elem.tag_name.lower() == 'a':
                        job_url = title_elem.get_attribute("href") or ""
                    else:
                        # Look for parent or sibling link
                        link_elem = job_elem.query_selector("a")
                        if link_elem:
                            job_url = link_elem.get_attribute("href") or ""
                    break
            
            # Make URL absolute if needed
            if job_url and not job_url.startswith("http"):
                if job_url.startswith("/"):
                    base_domain = self.workday_instance.split("/")[0:3]
                    job_url = "/".join(base_domain) + job_url
                else:
                    job_url = f"{self.workday_instance}/{job_url}"
            
            # Extract company name (usually TD Bank for this instance)
            company_selectors = [
                "[data-automation-id='company']",
                ".company-name",
                ".css-1cxz048"
            ]
            
            company = "TD Bank"  # Default for TD Bank Workday instance
            for selector in company_selectors:
                company_elem = job_elem.query_selector(selector)
                if company_elem:
                    company = company_elem.inner_text().strip()
                    break
            
            # Extract location
            location_selectors = [
                "[data-automation-id='location']",
                ".css-1p0sjhy",
                ".location",
                ".job-location"
            ]
            
            location = ""
            for selector in location_selectors:
                location_elem = job_elem.query_selector(selector)
                if location_elem:
                    location = location_elem.inner_text().strip()
                    break
            
            # Extract job summary/description
            summary_selectors = [
                "[data-automation-id='jobPostingDescription']",
                ".css-1t92pv",
                ".job-description",
                ".job-summary"
            ]
            
            summary = ""
            for selector in summary_selectors:
                summary_elem = job_elem.query_selector(selector)
                if summary_elem:
                    summary = summary_elem.inner_text().strip()
                    break
            
            # Extract posted date if available
            date_selectors = [
                "[data-automation-id='postedDate']",
                ".posted-date",
                ".css-1buv3xy"
            ]
            
            posted_date = ""
            for selector in date_selectors:
                date_elem = job_elem.query_selector(selector)
                if date_elem:
                    posted_date = date_elem.inner_text().strip()
                    break
            
            # Extract job type if available
            job_type_selectors = [
                "[data-automation-id='jobType']",
                ".job-type",
                ".employment-type"
            ]
            
            job_type = ""
            for selector in job_type_selectors:
                type_elem = job_elem.query_selector(selector)
                if type_elem:
                    job_type = type_elem.inner_text().strip()
                    break
            
            # Validate required fields
            if not title:
                console.print(f"[yellow]Skipping Workday job with missing title[/yellow]")
                return None
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "url": job_url,
                "summary": summary,
                "posted_date": posted_date,
                "job_type": job_type,
            }
            
        except Exception as e:
            console.print(f"[yellow]Error extracting Workday job data: {e}[/yellow]")
            return None
    
    def get_job_details(self, job_url: str) -> Dict:
        """
        Get detailed job information from a specific Workday job URL.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Dictionary with detailed job information
        """
        if not self.browser_context:
            console.print("[yellow]Browser context required for job details[/yellow]")
            return {}
        
        page = self.browser_context.new_page()
        
        try:
            console.print(f"[cyan]Getting Workday job details from: {job_url}[/cyan]")
            page.goto(job_url, timeout=30000)
            
            # Wait for job details to load
            page.wait_for_selector("[data-automation-id='jobPostingDescription'], .job-description", timeout=10000)
            
            # Extract detailed job description
            desc_selectors = [
                "[data-automation-id='jobPostingDescription']",
                ".css-1t92pv",
                ".job-description"
            ]
            
            full_description = ""
            for selector in desc_selectors:
                desc_elem = page.query_selector(selector)
                if desc_elem:
                    full_description = desc_elem.inner_text()
                    break
            
            # Extract qualifications
            qual_selectors = [
                "[data-automation-id='qualifications']",
                ".qualifications",
                ".requirements"
            ]
            
            qualifications = ""
            for selector in qual_selectors:
                qual_elem = page.query_selector(selector)
                if qual_elem:
                    qualifications = qual_elem.inner_text()
                    break
            
            # Extract additional job details
            details = {
                "full_description": full_description,
                "qualifications": qualifications,
            }
            
            # Try to extract more structured data
            detail_sections = page.query_selector_all("[data-automation-id*='jobPosting']")
            for section in detail_sections:
                try:
                    automation_id = section.get_attribute("data-automation-id")
                    if automation_id and automation_id not in ["jobPostingDescription"]:
                        content = section.inner_text().strip()
                        if content:
                            details[automation_id] = content
                except:
                    continue
            
            return details
            
        except Exception as e:
            console.print(f"[yellow]Error getting Workday job details: {e}[/yellow]")
            return {}
        finally:
            page.close()
