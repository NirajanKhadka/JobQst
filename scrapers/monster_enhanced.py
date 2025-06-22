"""
Enhanced Monster.ca Scraper
Advanced scraper for Monster Canada with anti-detection measures.
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


class EnhancedMonsterScraper(BaseJobScraper):
    """
    Enhanced Monster.ca scraper with anti-detection and comprehensive extraction.
    Designed specifically for the Canadian Monster job site.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)
        self.site_name = "Monster.ca"
        self.base_url = "https://www.monster.ca"
        self.requires_browser = True
        self.rate_limit_delay = (3.0, 6.0)  # Monster can be sensitive
        self.max_retries = 3
        
        # Monster-specific settings
        self.jobs_per_page = 20
        self.max_pages = 10
        
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """
        Scrape jobs from Monster.ca.
        
        Yields:
            Normalized job dictionaries
        """
        if not self.browser_context:
            console.print("[red]Monster scraper requires browser context![/red]")
            return
        
        yield from self._scrape_with_browser()
    
    def _scrape_with_browser(self) -> Generator[Dict, None, None]:
        """
        Monster scraping with anti-detection measures.
        """
        page_num = self.current_index // self.jobs_per_page + 1
        console.print(f"[cyan]🔍 Monster.ca scraping (page {page_num})[/cyan]")
        
        page = self.browser_context.new_page()
        
        try:
            # Setup Monster-specific headers
            self._setup_monster_headers(page)
            
            # Navigate to job search
            search_url = self._build_monster_search_url()
            console.print(f"[cyan]🌐 Searching Monster: {search_url}[/cyan]")
            
            if not self._navigate_to_jobs(page, search_url):
                console.print("[red]❌ Failed to navigate to Monster[/red]")
                return
            
            # Handle any popups or overlays
            self._handle_monster_popups(page)
            
            # Extract jobs from current page
            yield from self._extract_monster_jobs(page)
                
        except Exception as e:
            console.print(f"[red]❌ Monster scraping error: {e}[/red]")
        finally:
            # Human-like closing behavior
            time.sleep(random.uniform(2, 4))
            page.close()
    
    def _setup_monster_headers(self, page: Page) -> None:
        """Setup Monster-specific headers and stealth mode."""
        
        # Monster-optimized headers
        page.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-CA,en;q=0.9,fr-CA;q=0.8",
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
        
        # Anti-detection script for Monster
        monster_stealth = """
        // Remove webdriver traces
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock realistic properties
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-CA', 'en', 'fr-CA'],
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: 'Chrome PDF Plugin'},
                {name: 'Chrome PDF Viewer'},
                {name: 'Native Client'}
            ],
        });
        """
        
        page.add_init_script(monster_stealth)
    
    def _build_monster_search_url(self) -> str:
        """Build Monster search URL."""
        base_url = f"{self.base_url}/jobs/search"
        
        # Build search query
        keywords = " ".join(self.keywords[:3]) if self.keywords else "data analyst"
        location = self.city if self.city else "Toronto, ON"
        
        # Monster parameters
        params = {
            "q": keywords,
            "where": location,
            "page": str(self.current_index // self.jobs_per_page + 1),
            "tm": "7",  # Last 7 days
            "sort": "rv.dt.di"  # Date posted (newest first)
        }
        
        # Build URL
        url_params = "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        return f"{base_url}?{url_params}"
    
    def _navigate_to_jobs(self, page: Page, url: str) -> bool:
        """Navigate to Monster with retry logic."""
        
        for attempt in range(self.max_retries):
            try:
                # Random delay
                delay = random.uniform(3, 6)
                console.print(f"[cyan]⏳ Waiting {delay:.1f}s before navigation[/cyan]")
                time.sleep(delay)
                
                # Navigate
                response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                if response and response.status == 200:
                    # Wait for content to load
                    page.wait_for_timeout(random.randint(3000, 6000))
                    
                    # Verify page loaded
                    if self._verify_monster_page(page):
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
                wait_time = (attempt + 1) * 8
                console.print(f"[yellow]⏳ Waiting {wait_time}s before retry...[/yellow]")
                time.sleep(wait_time)
        
        return False
    
    def _verify_monster_page(self, page: Page) -> bool:
        """Verify Monster page loaded correctly."""
        try:
            # Check for Monster-specific indicators
            monster_indicators = [
                ".results-card",
                ".job-cardstyle__JobCardComponent",
                ".job-listing",
                "#SearchResults",
                ".search-results"
            ]
            
            for indicator in monster_indicators:
                if page.is_visible(indicator, timeout=3000):
                    return True
            
            # Check page title
            title = page.title().lower()
            if "monster" in title and ("jobs" in title or "search" in title):
                return True
            
            return False
            
        except Exception:
            return False
    
    def _handle_monster_popups(self, page: Page) -> None:
        """Handle Monster popups and overlays."""
        try:
            # Common popup selectors
            popup_selectors = [
                ".modal-close",
                ".popup-close",
                ".overlay-close",
                "[data-testid='close-button']",
                ".close-btn"
            ]
            
            for selector in popup_selectors:
                try:
                    if page.is_visible(selector, timeout=2000):
                        page.click(selector)
                        console.print("[green]✅ Closed Monster popup[/green]")
                        time.sleep(1)
                        break
                except:
                    continue
                    
        except Exception as e:
            console.print(f"[yellow]⚠️ Error handling popups: {e}[/yellow]")
    
    def _extract_monster_jobs(self, page: Page) -> Generator[Dict, None, None]:
        """Extract jobs from Monster page."""
        try:
            jobs_found = 0
            
            # Wait for job cards to load
            try:
                page.wait_for_selector(".results-card, .job-cardstyle__JobCardComponent", timeout=10000)
            except:
                console.print("[yellow]⚠️ No job cards found[/yellow]")
                return
            
            # Get job cards using multiple selectors
            job_cards = []
            
            # Try different selectors for job cards
            selectors = [
                ".results-card",
                ".job-cardstyle__JobCardComponent",
                ".job-listing",
                "#SearchResults .job-card",
                ".search-results .job-item"
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
                    job = self._extract_job_from_card(card)
                    if job:
                        jobs_found += 1
                        yield self.normalize_job(job)
                        
                        # Human-like delay between extractions
                        time.sleep(random.uniform(0.5, 1.5))
                        
                except Exception as e:
                    console.print(f"[yellow]⚠️ Error extracting job: {e}[/yellow]")
                    continue
            
            console.print(f"[green]✅ Extracted {jobs_found} jobs from Monster[/green]")
            
            # Update pagination
            self.current_index += max(jobs_found, self.jobs_per_page)
            
        except Exception as e:
            console.print(f"[red]❌ Error extracting Monster jobs: {e}[/red]")
    
    def _extract_job_from_card(self, card) -> Optional[Dict]:
        """Extract job information from a Monster job card."""
        try:
            job = {}
            
            # Extract job title and URL
            title_selectors = [
                ".job-title a",
                ".jobTitle a",
                "h2 a",
                ".title-link",
                "[data-testid='job-title'] a"
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
                ".company-name",
                ".companyName",
                "[data-testid='company-name']",
                ".job-company",
                ".employer-name"
            ]
            
            for selector in company_selectors:
                company_elem = card.query_selector(selector)
                if company_elem:
                    job['company'] = company_elem.inner_text().strip()
                    break
            
            # Extract location
            location_selectors = [
                ".job-location",
                ".location",
                "[data-testid='job-location']",
                ".job-meta .location",
                ".work-location"
            ]
            
            for selector in location_selectors:
                location_elem = card.query_selector(selector)
                if location_elem:
                    job['location'] = location_elem.inner_text().strip()
                    break
            
            # Extract posted date
            date_selectors = [
                ".posted-date",
                ".job-date",
                "[data-testid='posted-date']",
                ".date-posted",
                ".posting-date"
            ]
            
            for selector in date_selectors:
                date_elem = card.query_selector(selector)
                if date_elem:
                    job['posted_date'] = date_elem.inner_text().strip()
                    break
            
            # Extract job summary
            summary_selectors = [
                ".job-summary",
                ".job-description",
                "[data-testid='job-summary']",
                ".description-preview",
                ".job-snippet"
            ]
            
            for selector in summary_selectors:
                summary_elem = card.query_selector(selector)
                if summary_elem:
                    job['summary'] = summary_elem.inner_text().strip()
                    break
            
            # Extract additional Monster-specific information
            try:
                # Salary information
                salary_elem = card.query_selector(".salary, .wage, .compensation, [data-testid='salary']")
                if salary_elem:
                    job['salary'] = salary_elem.inner_text().strip()
                
                # Job type
                job_type_elem = card.query_selector(".job-type, .employment-type, [data-testid='job-type']")
                if job_type_elem:
                    job['job_type'] = job_type_elem.inner_text().strip()
                
                # Experience level
                experience_elem = card.query_selector(".experience-level, .seniority, [data-testid='experience']")
                if experience_elem:
                    job['experience_level'] = experience_elem.inner_text().strip()
                    
            except Exception:
                pass  # Additional metadata is optional
            
            # Set default values
            job.setdefault('company', 'Unknown Company')
            job.setdefault('location', 'Canada')
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
                'location': job.get('location', 'Canada'),
                'summary': job.get('summary', 'No description available'),
                'url': job.get('url', ''),
                'posted_date': job.get('posted_date', 'Recently posted'),
                'site': self.site_name,
                'site_display': 'Monster',
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
