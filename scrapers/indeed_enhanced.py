"""
Enhanced Indeed Job Scraper
Advanced scraper for Indeed.com with anti-detection measures.
Based on latest research and working techniques from 2024/2025.
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


class EnhancedIndeedScraper(BaseJobScraper):
    """
    Enhanced Indeed scraper with advanced anti-detection techniques.
    Based on latest working methods from Reddit, GitHub, and industry research.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)
        self.site_name = "Indeed Enhanced"
        self.base_url = "https://ca.indeed.com"  # Canadian site often has less protection
        self.requires_browser = True  # Browser required for anti-detection
        self.rate_limit_delay = (5.0, 10.0)  # Slower to avoid detection
        self.max_retries = 3
        
        # Rotating user agents (real browser fingerprints)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
    
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """
        Scrape jobs from Indeed using enhanced browser automation.
        
        Yields:
            Normalized job dictionaries
        """
        if not self.browser_context:
            console.print("[red]Enhanced Indeed scraper requires browser context![/red]")
            return
        
        yield from self._scrape_with_enhanced_browser()
    
    def _scrape_with_enhanced_browser(self) -> Generator[Dict, None, None]:
        """
        Enhanced Indeed scraping with advanced anti-detection.
        """
        page_num = self.current_index // 15 + 1
        console.print(f"[cyan]🔍 Enhanced Indeed scraping (page {page_num})[/cyan]")
        
        page = self.browser_context.new_page()
        
        try:
            # Setup enhanced anti-detection
            self._setup_stealth_mode(page)
            
            # Navigate with human-like behavior
            search_url = self._build_search_url()
            console.print(f"[cyan]🌐 Navigating to: {search_url}[/cyan]")
            
            if not self._navigate_with_stealth(page, search_url):
                console.print("[red]❌ Failed to navigate after all retries[/red]")
                return
            
            # Handle anti-bot challenges
            if self._handle_protection_challenges(page):
                console.print("[green]✅ Successfully bypassed protection[/green]")
            
            # Wait for content and extract jobs
            if self._wait_for_job_content(page):
                yield from self._extract_jobs_enhanced(page)
            else:
                console.print("[yellow]⚠️ No job content found[/yellow]")
                
        except Exception as e:
            console.print(f"[red]❌ Enhanced scraping error: {e}[/red]")
        finally:
            # Human-like closing behavior
            time.sleep(random.uniform(1, 3))
            page.close()
    
    def _setup_stealth_mode(self, page: Page) -> None:
        """Setup advanced stealth mode to avoid detection."""
        
        # Advanced anti-detection script
        stealth_script = """
        // Remove webdriver traces
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Remove automation indicators
        if (window.chrome && window.chrome.runtime) {
            delete window.chrome.runtime.onConnect;
            delete window.chrome.runtime.onMessage;
        }
        
        // Mock realistic screen properties
        Object.defineProperty(screen, 'availHeight', {get: () => 1040});
        Object.defineProperty(screen, 'availWidth', {get: () => 1920});
        Object.defineProperty(screen, 'colorDepth', {get: () => 24});
        Object.defineProperty(screen, 'height', {get: () => 1080});
        Object.defineProperty(screen, 'width', {get: () => 1920});
        
        // Mock realistic plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                {name: 'Chromium PDF Plugin', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                {name: 'Microsoft Edge PDF Plugin', filename: 'pdf'},
                {name: 'WebKit built-in PDF', filename: 'WebKit built-in PDF'}
            ],
        });
        
        // Mock realistic languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'en-CA'],
        });
        
        // Override permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Mock realistic connection
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 50,
                downlink: 10,
                saveData: false
            }),
        });
        
        // Hide automation flags
        Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0});
        Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
        Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
        """
        
        page.add_init_script(stealth_script)
        
        # Set realistic viewport
        page.set_viewport_size({"width": 1366, "height": 768})
        
        # Set realistic headers
        page.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,en-CA;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        })
    
    def _build_search_url(self) -> str:
        """Build Indeed search URL with optimized parameters."""
        # Use Canadian Indeed (often less protected)
        base_url = f"{self.base_url}/jobs"
        
        # Build search query
        query = " ".join(self.keywords[:3]) if self.keywords else "data analyst"
        location = self.city if self.city else "Toronto, ON"
        
        # Optimized parameters based on research
        params = {
            "q": query,
            "l": location,
            "start": str(self.current_index),
            "sort": "date",      # Fresh jobs
            "fromage": "7",      # Last 7 days
            "radius": "25",      # 25km radius
            "limit": "50",       # More results
            "filter": "0"        # No duplicates
        }
        
        # Build URL
        url_params = "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        return f"{base_url}?{url_params}"
    
    def _navigate_with_stealth(self, page: Page, url: str) -> bool:
        """Navigate with human-like behavior and retry logic."""
        
        for attempt in range(self.max_retries):
            try:
                # Random delay before navigation
                delay = random.uniform(3, 8)
                console.print(f"[cyan]⏳ Waiting {delay:.1f}s before navigation (attempt {attempt + 1})[/cyan]")
                time.sleep(delay)
                
                # Navigate with timeout
                response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                if response and response.status == 200:
                    # Additional wait for dynamic content
                    page.wait_for_timeout(random.randint(3000, 7000))
                    
                    # Check if page loaded successfully
                    if self._verify_page_loaded(page):
                        return True
                    else:
                        console.print(f"[yellow]⚠️ Page verification failed (attempt {attempt + 1})[/yellow]")
                else:
                    status = response.status if response else "No response"
                    console.print(f"[yellow]⚠️ Navigation failed with status: {status} (attempt {attempt + 1})[/yellow]")
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Navigation error (attempt {attempt + 1}): {e}[/yellow]")
            
            # Exponential backoff with jitter
            if attempt < self.max_retries - 1:
                wait_time = (2 ** attempt) * 10 + random.randint(5, 15)
                console.print(f"[yellow]⏳ Waiting {wait_time}s before retry...[/yellow]")
                time.sleep(wait_time)
        
        return False
    
    def _verify_page_loaded(self, page: Page) -> bool:
        """Verify that the Indeed page loaded correctly."""
        try:
            # Check for Indeed-specific elements
            indeed_indicators = [
                "#searchform",
                ".jobsearch-SerpJobCard",
                "[data-testid='job-title']",
                ".slider_container",
                ".job_seen_beacon"
            ]
            
            for indicator in indeed_indicators:
                try:
                    if page.is_visible(indicator, timeout=2000):
                        return True
                except:
                    continue
            
            # Check page title
            title = page.title().lower()
            if "indeed" in title and ("jobs" in title or "job search" in title):
                return True
            
            return False

        except Exception:
            return False

    def _handle_protection_challenges(self, page: Page) -> bool:
        """Handle Cloudflare and other protection challenges."""
        try:
            # Check for Cloudflare challenge
            if self._is_cloudflare_challenge(page):
                console.print("[yellow]🛡️ Cloudflare challenge detected, waiting...[/yellow]")
                return self._handle_cloudflare(page)

            # Check for CAPTCHA
            if self._is_captcha_present(page):
                console.print("[yellow]🤖 CAPTCHA detected, manual intervention needed[/yellow]")
                return self._handle_captcha(page)

            # Check for rate limiting
            if self._is_rate_limited(page):
                console.print("[yellow]⏱️ Rate limited, waiting...[/yellow]")
                return self._handle_rate_limit(page)

            return True

        except Exception as e:
            console.print(f"[yellow]⚠️ Error handling protection: {e}[/yellow]")
            return False

    def _is_cloudflare_challenge(self, page: Page) -> bool:
        """Check if Cloudflare challenge is present."""
        try:
            cloudflare_indicators = [
                ".cf-browser-verification",
                "#cf-wrapper",
                ".cf-checking-browser",
                "title:has-text('Just a moment')",
                "h1:has-text('Checking your browser')"
            ]

            for indicator in cloudflare_indicators:
                if page.is_visible(indicator, timeout=1000):
                    return True

            # Check page content
            content = page.content().lower()
            if "cloudflare" in content and ("checking" in content or "challenge" in content):
                return True

            return False
        except:
            return False

    def _handle_cloudflare(self, page: Page) -> bool:
        """Handle Cloudflare challenge by waiting."""
        try:
            # Wait for Cloudflare to complete (up to 30 seconds)
            for i in range(30):
                time.sleep(1)
                if not self._is_cloudflare_challenge(page):
                    console.print("[green]✅ Cloudflare challenge passed[/green]")
                    return True
                if i % 5 == 0:
                    console.print(f"[cyan]⏳ Waiting for Cloudflare... ({i+1}/30s)[/cyan]")

            console.print("[red]❌ Cloudflare challenge timeout[/red]")
            return False
        except:
            return False

    def _is_captcha_present(self, page: Page) -> bool:
        """Check if CAPTCHA is present."""
        try:
            captcha_indicators = [
                ".captcha",
                "#captcha",
                "[data-testid='captcha']",
                ".g-recaptcha",
                ".h-captcha",
                "iframe[src*='recaptcha']",
                "iframe[src*='hcaptcha']"
            ]

            for indicator in captcha_indicators:
                if page.is_visible(indicator, timeout=1000):
                    return True

            return False
        except:
            return False

    def _handle_captcha(self, page: Page) -> bool:
        """Handle CAPTCHA (requires manual intervention)."""
        console.print("[bold yellow]🤖 CAPTCHA detected! Manual intervention required.[/bold yellow]")
        console.print("[yellow]Please solve the CAPTCHA in the browser window.[/yellow]")
        console.print("[yellow]Press Enter when done...[/yellow]")

        input()  # Wait for user input

        # Verify CAPTCHA was solved
        time.sleep(2)
        if not self._is_captcha_present(page):
            console.print("[green]✅ CAPTCHA solved successfully[/green]")
            return True
        else:
            console.print("[red]❌ CAPTCHA still present[/red]")
            return False

    def _is_rate_limited(self, page: Page) -> bool:
        """Check if we're being rate limited."""
        try:
            rate_limit_indicators = [
                "text=Too many requests",
                "text=Rate limit exceeded",
                "text=Please try again later",
                ".rate-limit",
                "#rate-limit"
            ]

            for indicator in rate_limit_indicators:
                if page.is_visible(indicator, timeout=1000):
                    return True

            # Check status code
            if hasattr(page, 'response') and page.response:
                if page.response.status == 429:
                    return True

            return False
        except:
            return False

    def _handle_rate_limit(self, page: Page) -> bool:
        """Handle rate limiting by waiting."""
        wait_time = random.randint(60, 120)  # Wait 1-2 minutes
        console.print(f"[yellow]⏱️ Rate limited, waiting {wait_time} seconds...[/yellow]")
        time.sleep(wait_time)

        # Refresh page
        page.reload(wait_until="domcontentloaded")
        return not self._is_rate_limited(page)

    def _wait_for_job_content(self, page: Page) -> bool:
        """Wait for job content to load."""
        try:
            # Multiple selectors for different Indeed layouts
            job_selectors = [
                ".jobsearch-SerpJobCard",
                "[data-testid='job-title']",
                ".slider_item",
                ".job_seen_beacon",
                "a.tapItem",
                ".slider_container .slider_item"
            ]

            # Wait for any job selector to appear
            for selector in job_selectors:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    console.print(f"[green]✅ Job content loaded (found: {selector})[/green]")
                    return True
                except:
                    continue

            console.print("[yellow]⚠️ No job content selectors found[/yellow]")
            return False

        except Exception as e:
            console.print(f"[yellow]⚠️ Error waiting for content: {e}[/yellow]")
            return False

    def _extract_jobs_enhanced(self, page: Page) -> Generator[Dict, None, None]:
        """Extract jobs using multiple layout strategies."""
        try:
            jobs_found = 0

            # Strategy 1: New Indeed layout (slider_item)
            for job in self._extract_from_slider_layout(page):
                jobs_found += 1
                yield job

            # Strategy 2: Classic layout (job_seen_beacon)
            if jobs_found == 0:
                for job in self._extract_from_classic_layout(page):
                    jobs_found += 1
                    yield job

            # Strategy 3: TapItem layout
            if jobs_found == 0:
                for job in self._extract_from_tapitem_layout(page):
                    jobs_found += 1
                    yield job

            console.print(f"[green]✅ Extracted {jobs_found} jobs from Indeed[/green]")

            # Update pagination
            self.current_index += max(jobs_found, 15)

        except Exception as e:
            console.print(f"[red]❌ Error extracting jobs: {e}[/red]")

    def _extract_from_slider_layout(self, page: Page) -> Generator[Dict, None, None]:
        """Extract jobs from slider layout."""
        try:
            cards = page.query_selector_all(".slider_container .slider_item")
            if not cards:
                return

            console.print(f"[cyan]📋 Found {len(cards)} jobs (slider layout)[/cyan]")

            for card in cards:
                try:
                    job = self._extract_job_from_slider_card(card)
                    if job:
                        yield self.normalize_job(job)
                except Exception as e:
                    console.print(f"[yellow]⚠️ Error extracting slider job: {e}[/yellow]")
                    continue

        except Exception as e:
            console.print(f"[yellow]⚠️ Slider layout extraction failed: {e}[/yellow]")

    def _extract_from_classic_layout(self, page: Page) -> Generator[Dict, None, None]:
        """Extract jobs from classic layout."""
        try:
            cards = page.query_selector_all(".job_seen_beacon")
            if not cards:
                return

            console.print(f"[cyan]📋 Found {len(cards)} jobs (classic layout)[/cyan]")

            for card in cards:
                try:
                    job = self._extract_job_from_classic_card(card)
                    if job:
                        yield self.normalize_job(job)
                except Exception as e:
                    console.print(f"[yellow]⚠️ Error extracting classic job: {e}[/yellow]")
                    continue

        except Exception as e:
            console.print(f"[yellow]⚠️ Classic layout extraction failed: {e}[/yellow]")

    def _extract_from_tapitem_layout(self, page: Page) -> Generator[Dict, None, None]:
        """Extract jobs from tapItem layout."""
        try:
            cards = page.query_selector_all("a.tapItem")
            if not cards:
                return

            console.print(f"[cyan]📋 Found {len(cards)} jobs (tapItem layout)[/cyan]")

            for card in cards:
                try:
                    job = self._extract_job_from_tapitem_card(card)
                    if job:
                        yield self.normalize_job(job)
                except Exception as e:
                    console.print(f"[yellow]⚠️ Error extracting tapItem job: {e}[/yellow]")
                    continue

        except Exception as e:
            console.print(f"[yellow]⚠️ TapItem layout extraction failed: {e}[/yellow]")

    def _extract_job_from_slider_card(self, card) -> Optional[Dict]:
        """Extract job data from slider card."""
        try:
            # Title and URL
            title_elem = card.query_selector("h2 a span[title], h2 span[title]")
            title = title_elem.get_attribute("title") if title_elem else ""

            url_elem = card.query_selector("h2 a")
            url = url_elem.get_attribute("href") if url_elem else ""
            if url and not url.startswith("http"):
                url = urljoin(self.base_url, url)

            # Company
            company_elem = card.query_selector("[data-testid='company-name'], .companyName")
            company = company_elem.inner_text().strip() if company_elem else ""

            # Location
            location_elem = card.query_selector("[data-testid='job-location'], .companyLocation")
            location = location_elem.inner_text().strip() if location_elem else ""

            # Summary
            summary_elem = card.query_selector(".job-snippet, [data-testid='job-snippet']")
            summary = summary_elem.inner_text().strip() if summary_elem else ""

            # Salary
            salary_elem = card.query_selector(".salary-snippet, [data-testid='job-salary']")
            salary = salary_elem.inner_text().strip() if salary_elem else ""

            if not title or not company:
                return None

            return {
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "summary": summary,
                "salary": salary,
                "source": "Indeed Enhanced"
            }

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting slider card: {e}[/yellow]")
            return None

    def _extract_job_from_classic_card(self, card) -> Optional[Dict]:
        """Extract job data from classic layout card."""
        try:
            # Title and URL
            title_elem = card.query_selector("h2.jobTitle a span[title], h2.jobTitle span")
            title = title_elem.get_attribute("title") or title_elem.inner_text() if title_elem else ""

            url_elem = card.query_selector("h2.jobTitle a")
            url = url_elem.get_attribute("href") if url_elem else ""
            if url and not url.startswith("http"):
                url = urljoin(self.base_url, url)

            # Company
            company_elem = card.query_selector("span.companyName")
            company = company_elem.inner_text().strip() if company_elem else ""

            # Location
            location_elem = card.query_selector("div.companyLocation")
            location = location_elem.inner_text().strip() if location_elem else ""

            # Summary
            summary_elem = card.query_selector(".job-snippet")
            summary = summary_elem.inner_text().strip() if summary_elem else ""

            # Salary
            salary_elem = card.query_selector(".salary-snippet")
            salary = salary_elem.inner_text().strip() if salary_elem else ""

            if not title or not company:
                return None

            return {
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "summary": summary,
                "salary": salary,
                "source": "Indeed Enhanced"
            }

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting classic card: {e}[/yellow]")
            return None

    def _extract_job_from_tapitem_card(self, card) -> Optional[Dict]:
        """Extract job data from tapItem layout card."""
        try:
            # Title and URL
            title_elem = card.query_selector("h2 span[title]")
            title = title_elem.get_attribute("title") if title_elem else ""

            url = card.get_attribute("href") or ""
            if url and not url.startswith("http"):
                url = urljoin(self.base_url, url)

            # Company
            company_elem = card.query_selector(".companyName")
            company = company_elem.inner_text().strip() if company_elem else ""

            # Location
            location_elem = card.query_selector(".companyLocation")
            location = location_elem.inner_text().strip() if location_elem else ""

            # Summary
            summary_elem = card.query_selector(".job-snippet")
            summary = summary_elem.inner_text().strip() if summary_elem else ""

            # Salary
            salary_elem = card.query_selector(".salary-snippet")
            salary = salary_elem.inner_text().strip() if salary_elem else ""

            if not title or not company:
                return None

            return {
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "summary": summary,
                "salary": salary,
                "source": "Indeed Enhanced"
            }

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting tapItem card: {e}[/yellow]")
            return None
