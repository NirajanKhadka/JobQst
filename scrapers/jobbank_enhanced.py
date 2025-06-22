"""
Enhanced JobBank.gc.ca Scraper
Advanced scraper for the official Canadian government job site.
Optimized for Canadian job market with comprehensive job extraction.
"""

import time
import random
import json
from typing import Dict, Generator, Optional
from urllib.parse import quote_plus, urljoin
from playwright.sync_api import Page, BrowserContext
from rich.console import Console

from .base_scraper import BaseJobScraper

console = Console()


class EnhancedJobBankScraper(BaseJobScraper):
    """
    Enhanced JobBank.gc.ca scraper for official Canadian government jobs.
    No authentication required, but includes anti-detection measures.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)
        self.site_name = "JobBank.gc.ca"
        self.base_url = "https://www.jobbank.gc.ca"
        self.requires_browser = True
        self.rate_limit_delay = (2.0, 5.0)  # Government site, be respectful
        self.max_retries = 3
        
        # JobBank-specific settings
        self.jobs_per_page = 20
        self.max_pages = 15
        
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """
        Scrape jobs from JobBank.gc.ca.
        
        Yields:
            Normalized job dictionaries
        """
        if not self.browser_context:
            console.print("[red]JobBank scraper requires browser context![/red]")
            return
        
        yield from self._scrape_with_browser()
    
    def _scrape_with_browser(self) -> Generator[Dict, None, None]:
        """
        JobBank scraping with government-friendly approach.
        """
        page_num = self.current_index // self.jobs_per_page + 1
        console.print(f"[cyan]🔍 JobBank.gc.ca scraping (page {page_num})[/cyan]")
        
        page = self.browser_context.new_page()
        
        try:
            # Setup respectful headers for government site
            self._setup_jobbank_headers(page)
            
            # Navigate to job search
            search_url = self._build_jobbank_search_url()
            console.print(f"[cyan]🌐 Searching JobBank: {search_url}[/cyan]")
            
            if not self._navigate_to_jobs(page, search_url):
                console.print("[red]❌ Failed to navigate to JobBank[/red]")
                return
            
            # Extract jobs from current page
            yield from self._extract_jobbank_jobs(page)
                
        except Exception as e:
            console.print(f"[red]❌ JobBank scraping error: {e}[/red]")
        finally:
            # Respectful closing behavior
            time.sleep(random.uniform(1, 3))
            page.close()
    
    def _setup_jobbank_headers(self, page: Page) -> None:
        """Setup respectful headers for government site."""
        
        # Government-friendly headers
        page.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-CA,en;q=0.9,fr-CA;q=0.8,fr;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        })
        
        # Set realistic viewport
        page.set_viewport_size({"width": 1366, "height": 768})
    
    def _build_jobbank_search_url(self) -> str:
        """Build JobBank search URL."""
        base_url = f"{self.base_url}/jobsearch/jobsearch"
        
        # Build search query
        keywords = " ".join(self.keywords[:3]) if self.keywords else "data analyst"
        location = self.city if self.city else "Toronto, ON"
        
        # JobBank parameters
        params = {
            "searchstring": keywords,
            "locationstring": location,
            "sort": "D",  # Date posted (newest first)
            "page": str(self.current_index // self.jobs_per_page + 1),
            "fprov": "",  # All provinces
            "dateposted": "7"  # Last 7 days
        }
        
        # Build URL
        url_params = "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        return f"{base_url}?{url_params}"
    
    def _navigate_to_jobs(self, page: Page, url: str) -> bool:
        """Navigate to JobBank with retry logic."""
        
        for attempt in range(self.max_retries):
            try:
                # Respectful delay
                delay = random.uniform(2, 4)
                console.print(f"[cyan]⏳ Waiting {delay:.1f}s before navigation[/cyan]")
                time.sleep(delay)
                
                # Navigate
                response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                if response and response.status == 200:
                    # Wait for content to load
                    page.wait_for_timeout(random.randint(2000, 4000))
                    
                    # Verify page loaded
                    if self._verify_jobbank_page(page):
                        return True
                    else:
                        console.print(f"[yellow]⚠️ Page verification failed (attempt {attempt + 1})[/yellow]")
                else:
                    status = response.status if response else "No response"
                    console.print(f"[yellow]⚠️ Navigation failed: {status} (attempt {attempt + 1})[/yellow]")
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Navigation error (attempt {attempt + 1}): {e}[/yellow]")
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                wait_time = (attempt + 1) * 5
                console.print(f"[yellow]⏳ Waiting {wait_time}s before retry...[/yellow]")
                time.sleep(wait_time)
        
        return False
    
    def _verify_jobbank_page(self, page: Page) -> bool:
        """Verify JobBank page loaded correctly."""
        try:
            # Check for JobBank-specific indicators
            jobbank_indicators = [
                ".search-results",
                ".job-posting-brief",
                ".search-result-item",
                "#search-results-container",
                ".job-list"
            ]
            
            for indicator in jobbank_indicators:
                if page.is_visible(indicator, timeout=3000):
                    return True
            
            # Check page title
            title = page.title().lower()
            if "job bank" in title or "jobbank" in title:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _extract_jobbank_jobs(self, page: Page) -> Generator[Dict, None, None]:
        """Extract jobs from JobBank page."""
        try:
            jobs_found = 0
            
            # Wait for job listings to load
            try:
                page.wait_for_selector(".job-posting-brief, .search-result-item", timeout=10000)
            except:
                console.print("[yellow]⚠️ No job listings found[/yellow]")
                return
            
            # Get job listings using multiple selectors
            job_listings = []
            
            # Try different selectors for job listings
            selectors = [
                ".job-posting-brief",
                ".search-result-item",
                ".job-list .job-item",
                "#search-results-container .result-item"
            ]
            
            for selector in selectors:
                listings = page.query_selector_all(selector)
                if listings:
                    job_listings = listings
                    console.print(f"[cyan]📋 Found {len(listings)} job listings using selector: {selector}[/cyan]")
                    break
            
            if not job_listings:
                console.print("[yellow]⚠️ No job listings found with any selector[/yellow]")
                return
            
            # Extract each job
            for listing in job_listings:
                try:
                    job = self._extract_job_from_listing(listing)
                    if job:
                        jobs_found += 1
                        yield self.normalize_job(job)
                        
                        # Respectful delay between extractions
                        time.sleep(random.uniform(0.3, 1.0))
                        
                except Exception as e:
                    console.print(f"[yellow]⚠️ Error extracting job: {e}[/yellow]")
                    continue
            
            console.print(f"[green]✅ Extracted {jobs_found} jobs from JobBank[/green]")
            
            # Update pagination
            self.current_index += max(jobs_found, self.jobs_per_page)
            
        except Exception as e:
            console.print(f"[red]❌ Error extracting JobBank jobs: {e}[/red]")
    
    def _extract_job_from_listing(self, listing) -> Optional[Dict]:
        """Extract job information from a JobBank listing."""
        try:
            job = {}
            
            # Extract job title and URL
            title_selectors = [
                ".job-title a",
                ".posting-title a",
                "h3 a",
                ".title-link"
            ]
            
            for selector in title_selectors:
                title_elem = listing.query_selector(selector)
                if title_elem:
                    job['title'] = title_elem.inner_text().strip()
                    # Get job URL
                    href = title_elem.get_attribute('href')
                    if href:
                        job['url'] = urljoin(self.base_url, href)
                    break
            
            if not job.get('title'):
                return None
            
            # Extract company name
            company_selectors = [
                ".company-name",
                ".employer-name",
                ".posting-employer",
                ".job-employer"
            ]
            
            for selector in company_selectors:
                company_elem = listing.query_selector(selector)
                if company_elem:
                    job['company'] = company_elem.inner_text().strip()
                    break
            
            # Extract location
            location_selectors = [
                ".job-location",
                ".posting-location",
                ".location",
                ".work-location"
            ]
            
            for selector in location_selectors:
                location_elem = listing.query_selector(selector)
                if location_elem:
                    job['location'] = location_elem.inner_text().strip()
                    break
            
            # Extract posted date
            date_selectors = [
                ".posting-date",
                ".date-posted",
                ".job-date",
                ".posted-date"
            ]
            
            for selector in date_selectors:
                date_elem = listing.query_selector(selector)
                if date_elem:
                    job['posted_date'] = date_elem.inner_text().strip()
                    break
            
            # Extract job summary
            summary_selectors = [
                ".job-summary",
                ".posting-summary",
                ".job-description-brief",
                ".description-brief"
            ]
            
            for selector in summary_selectors:
                summary_elem = listing.query_selector(selector)
                if summary_elem:
                    job['summary'] = summary_elem.inner_text().strip()
                    break
            
            # Extract additional JobBank-specific information
            try:
                # Salary information
                salary_elem = listing.query_selector(".salary, .wage, .compensation")
                if salary_elem:
                    job['salary'] = salary_elem.inner_text().strip()
                
                # Job type
                job_type_elem = listing.query_selector(".job-type, .employment-type")
                if job_type_elem:
                    job['job_type'] = job_type_elem.inner_text().strip()
                
                # NOC code (National Occupational Classification)
                noc_elem = listing.query_selector(".noc-code, .classification")
                if noc_elem:
                    job['noc_code'] = noc_elem.inner_text().strip()
                    
            except Exception:
                pass  # Additional metadata is optional
            
            # Set default values
            job.setdefault('company', 'Government of Canada')
            job.setdefault('location', 'Canada')
            job.setdefault('summary', 'No description available')
            job.setdefault('posted_date', 'Recently posted')
            
            return job
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting job from listing: {e}[/yellow]")
            return None

    def normalize_job(self, job: Dict) -> Dict:
        """Normalize job data to standard format."""
        try:
            normalized = {
                'title': job.get('title', 'Unknown Job Title'),
                'company': job.get('company', 'Government of Canada'),
                'location': job.get('location', 'Canada'),
                'summary': job.get('summary', 'No description available'),
                'url': job.get('url', ''),
                'posted_date': job.get('posted_date', 'Recently posted'),
                'site': self.site_name,
                'site_display': 'JobBank',
                'search_keyword': ', '.join(self.keywords) if self.keywords else 'data analyst',
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'salary': job.get('salary', ''),
                'job_type': job.get('job_type', ''),
                'noc_code': job.get('noc_code', ''),
                'applied': False,
                'application_date': None,
                'notes': ''
            }

            return normalized

        except Exception as e:
            console.print(f"[red]❌ Error normalizing job: {e}[/red]")
            return {}
