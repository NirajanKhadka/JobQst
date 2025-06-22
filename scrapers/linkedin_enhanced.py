"""
Enhanced LinkedIn Jobs Scraper
Advanced scraper for LinkedIn Jobs with authentication handling.
Designed for Canadian job market with anti-detection measures.
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


class EnhancedLinkedInScraper(BaseJobScraper):
    """
    Enhanced LinkedIn Jobs scraper with authentication and anti-detection.
    Requires user to be logged in to LinkedIn for best results.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)
        self.site_name = "LinkedIn Jobs"
        self.base_url = "https://www.linkedin.com"
        self.requires_browser = True
        self.rate_limit_delay = (3.0, 7.0)  # LinkedIn is sensitive to rapid requests
        self.max_retries = 3
        self.authenticated = False
        
        # LinkedIn-specific settings
        self.jobs_per_page = 25
        self.max_pages = 10
        
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """
        Scrape jobs from LinkedIn Jobs.
        
        Yields:
            Normalized job dictionaries
        """
        if not self.browser_context:
            console.print("[red]LinkedIn scraper requires browser context![/red]")
            return
        
        yield from self._scrape_with_browser()
    
    def _scrape_with_browser(self) -> Generator[Dict, None, None]:
        """
        LinkedIn scraping with authentication handling.
        """
        page_num = self.current_index // self.jobs_per_page + 1
        console.print(f"[cyan]🔍 LinkedIn Jobs scraping (page {page_num})[/cyan]")
        
        page = self.browser_context.new_page()
        
        try:
            # Setup LinkedIn-specific headers
            self._setup_linkedin_headers(page)
            
            # Check authentication status
            if not self._check_authentication(page):
                console.print("[yellow]⚠️ LinkedIn authentication required[/yellow]")
                if not self._handle_authentication(page):
                    console.print("[red]❌ Failed to authenticate with LinkedIn[/red]")
                    return
            
            # Navigate to jobs search
            search_url = self._build_jobs_search_url()
            console.print(f"[cyan]🌐 Searching LinkedIn Jobs: {search_url}[/cyan]")
            
            if not self._navigate_to_jobs(page, search_url):
                console.print("[red]❌ Failed to navigate to LinkedIn Jobs[/red]")
                return
            
            # Extract jobs from current page
            yield from self._extract_linkedin_jobs(page)
                
        except Exception as e:
            console.print(f"[red]❌ LinkedIn scraping error: {e}[/red]")
        finally:
            # Human-like closing behavior
            time.sleep(random.uniform(2, 4))
            page.close()
    
    def _setup_linkedin_headers(self, page: Page) -> None:
        """Setup LinkedIn-specific headers and stealth mode."""
        
        # LinkedIn-optimized headers
        page.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        })
        
        # Set realistic viewport
        page.set_viewport_size({"width": 1366, "height": 768})
        
        # Anti-detection script for LinkedIn
        linkedin_stealth = """
        // Remove webdriver traces
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock realistic properties
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: 'Chrome PDF Plugin'},
                {name: 'Chrome PDF Viewer'},
                {name: 'Native Client'}
            ],
        });
        """
        
        page.add_init_script(linkedin_stealth)
    
    def _check_authentication(self, page: Page) -> bool:
        """Check if user is authenticated with LinkedIn."""
        try:
            # Navigate to LinkedIn home to check auth
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            # Check for authentication indicators
            auth_indicators = [
                ".global-nav__me",
                ".global-nav__primary-link--me",
                "[data-test-global-nav-me]",
                ".nav-item__profile-member-photo"
            ]
            
            for indicator in auth_indicators:
                if page.is_visible(indicator, timeout=2000):
                    console.print("[green]✅ LinkedIn authentication verified[/green]")
                    self.authenticated = True
                    return True
            
            # Check if we're on login page
            if "login" in page.url or "challenge" in page.url:
                return False
            
            return False
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Error checking LinkedIn auth: {e}[/yellow]")
            return False
    
    def _handle_authentication(self, page: Page) -> bool:
        """Handle LinkedIn authentication."""
        try:
            console.print("[yellow]🔐 LinkedIn authentication required[/yellow]")
            console.print("[yellow]Please log in to LinkedIn in the browser window[/yellow]")
            console.print("[yellow]Press Enter when logged in...[/yellow]")
            
            # Navigate to login page
            page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
            
            # Wait for user to log in
            input()
            
            # Verify authentication
            return self._check_authentication(page)
            
        except Exception as e:
            console.print(f"[red]❌ Authentication error: {e}[/red]")
            return False
    
    def _build_jobs_search_url(self) -> str:
        """Build LinkedIn Jobs search URL."""
        base_url = f"{self.base_url}/jobs/search"
        
        # Build search query
        keywords = " ".join(self.keywords[:3]) if self.keywords else "data analyst"
        location = self.city if self.city else "Toronto, Ontario, Canada"
        
        # LinkedIn Jobs parameters
        params = {
            "keywords": keywords,
            "location": location,
            "f_TPR": "r604800",  # Past week
            "f_JT": "F,P",       # Full-time and Part-time
            "sortBy": "DD",      # Date posted (newest first)
            "start": str(self.current_index)
        }
        
        # Build URL
        url_params = "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        return f"{base_url}?{url_params}"
    
    def _navigate_to_jobs(self, page: Page, url: str) -> bool:
        """Navigate to LinkedIn Jobs with retry logic."""
        
        for attempt in range(self.max_retries):
            try:
                # Random delay
                delay = random.uniform(2, 5)
                console.print(f"[cyan]⏳ Waiting {delay:.1f}s before navigation[/cyan]")
                time.sleep(delay)
                
                # Navigate
                response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                if response and response.status == 200:
                    # Wait for jobs to load
                    page.wait_for_timeout(random.randint(3000, 6000))
                    
                    # Verify jobs page loaded
                    if self._verify_jobs_page(page):
                        return True
                    else:
                        console.print(f"[yellow]⚠️ Jobs page verification failed (attempt {attempt + 1})[/yellow]")
                else:
                    status = response.status if response else "No response"
                    console.print(f"[yellow]⚠️ Navigation failed: {status} (attempt {attempt + 1})[/yellow]")
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Navigation error (attempt {attempt + 1}): {e}[/yellow]")
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                wait_time = (attempt + 1) * 10
                console.print(f"[yellow]⏳ Waiting {wait_time}s before retry...[/yellow]")
                time.sleep(wait_time)
        
        return False
    
    def _verify_jobs_page(self, page: Page) -> bool:
        """Verify LinkedIn Jobs page loaded correctly."""
        try:
            # Check for LinkedIn Jobs indicators
            jobs_indicators = [
                ".jobs-search-results-list",
                ".job-card-container",
                ".jobs-search__results-list",
                "[data-test-id='job-card']",
                ".scaffold-layout__list-container"
            ]
            
            for indicator in jobs_indicators:
                if page.is_visible(indicator, timeout=3000):
                    return True
            
            # Check page title
            title = page.title().lower()
            if "jobs" in title and "linkedin" in title:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _extract_linkedin_jobs(self, page: Page) -> Generator[Dict, None, None]:
        """Extract jobs from LinkedIn Jobs page."""
        try:
            jobs_found = 0
            
            # Wait for job cards to load
            try:
                page.wait_for_selector(".job-card-container, .jobs-search-results-list li", timeout=10000)
            except:
                console.print("[yellow]⚠️ No job cards found[/yellow]")
                return
            
            # Get job cards using multiple selectors
            job_cards = []
            
            # Try different selectors for job cards
            selectors = [
                ".job-card-container",
                ".jobs-search-results-list li",
                "[data-test-id='job-card']",
                ".scaffold-layout__list-container li"
            ]
            
            for selector in selectors:
                cards = page.query_selector_all(selector)
                if cards:
                    job_cards = cards
                    console.print(f"[cyan]📋 Found {len(cards)} job cards using selector: {selector}[/cyan]")
                    break
            
            if not job_cards:
                console.print("[yellow]⚠️ No job cards found with any selector[/yellow]")
                return
            
            # Extract each job
            for card in job_cards:
                try:
                    job = self._extract_job_from_card(card, page)
                    if job:
                        jobs_found += 1
                        yield self.normalize_job(job)
                        
                        # Human-like delay between extractions
                        time.sleep(random.uniform(0.5, 1.5))
                        
                except Exception as e:
                    console.print(f"[yellow]⚠️ Error extracting job: {e}[/yellow]")
                    continue
            
            console.print(f"[green]✅ Extracted {jobs_found} jobs from LinkedIn[/green]")
            
            # Update pagination
            self.current_index += max(jobs_found, self.jobs_per_page)
            
        except Exception as e:
            console.print(f"[red]❌ Error extracting LinkedIn jobs: {e}[/red]")

    def _extract_job_from_card(self, card, page: Page) -> Optional[Dict]:
        """Extract job information from a LinkedIn job card."""
        try:
            job = {}

            # Extract job title
            title_selectors = [
                ".job-card-list__title",
                ".job-card-container__link",
                "[data-test-id='job-title']",
                ".job-title a",
                "h3 a"
            ]

            for selector in title_selectors:
                title_elem = card.query_selector(selector)
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
                ".job-card-container__company-name",
                ".job-card-list__company-name",
                "[data-test-id='job-company']",
                ".company-name"
            ]

            for selector in company_selectors:
                company_elem = card.query_selector(selector)
                if company_elem:
                    job['company'] = company_elem.inner_text().strip()
                    break

            # Extract location
            location_selectors = [
                ".job-card-container__metadata-item",
                ".job-card-list__metadata",
                "[data-test-id='job-location']",
                ".job-location"
            ]

            for selector in location_selectors:
                location_elem = card.query_selector(selector)
                if location_elem:
                    location_text = location_elem.inner_text().strip()
                    if location_text and not any(word in location_text.lower() for word in ['ago', 'hour', 'day', 'week', 'month']):
                        job['location'] = location_text
                        break

            # Extract posted date
            time_selectors = [
                ".job-card-list__footer-wrapper time",
                ".job-card-container__footer time",
                "[data-test-id='job-posted-date']",
                "time"
            ]

            for selector in time_selectors:
                time_elem = card.query_selector(selector)
                if time_elem:
                    posted_text = time_elem.inner_text().strip()
                    job['posted_date'] = posted_text
                    break

            # Extract job summary/description preview
            summary_selectors = [
                ".job-card-list__summary",
                ".job-card-container__summary",
                "[data-test-id='job-summary']",
                ".job-summary"
            ]

            for selector in summary_selectors:
                summary_elem = card.query_selector(selector)
                if summary_elem:
                    job['summary'] = summary_elem.inner_text().strip()
                    break

            # Extract additional metadata
            try:
                # Look for salary information
                salary_elem = card.query_selector(".job-card-container__salary, .salary-range")
                if salary_elem:
                    job['salary'] = salary_elem.inner_text().strip()

                # Look for job type (full-time, part-time, etc.)
                job_type_elem = card.query_selector(".job-card-container__job-type, .job-type")
                if job_type_elem:
                    job['job_type'] = job_type_elem.inner_text().strip()

                # Look for experience level
                experience_elem = card.query_selector(".job-card-container__experience, .experience-level")
                if experience_elem:
                    job['experience_level'] = experience_elem.inner_text().strip()

            except Exception:
                pass  # Additional metadata is optional

            # Set default values
            job.setdefault('company', 'Unknown Company')
            job.setdefault('location', 'Location not specified')
            job.setdefault('summary', 'No description available')
            job.setdefault('posted_date', 'Recently posted')

            return job

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting job from card: {e}[/yellow]")
            return None

    def normalize_job(self, job: Dict) -> Dict:
        """Normalize job data to standard format."""
        try:
            normalized = {
                'title': job.get('title', 'Unknown Job Title'),
                'company': job.get('company', 'Unknown Company'),
                'location': job.get('location', 'Location not specified'),
                'summary': job.get('summary', 'No description available'),
                'url': job.get('url', ''),
                'posted_date': job.get('posted_date', 'Recently posted'),
                'site': self.site_name,
                'site_display': 'LinkedIn',
                'search_keyword': ', '.join(self.keywords) if self.keywords else 'data analyst',
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'salary': job.get('salary', ''),
                'job_type': job.get('job_type', ''),
                'experience_level': job.get('experience_level', ''),
                'applied': False,
                'application_date': None,
                'notes': ''
            }

            return normalized

        except Exception as e:
            console.print(f"[red]❌ Error normalizing job: {e}[/red]")
            return {}
