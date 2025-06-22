"""
Enhanced Eluta scraper with multiple browser contexts.
Each browser context focuses on one keyword at a time for optimal performance.
"""

import time
import random
import re
import urllib.parse
import threading
from datetime import datetime, timedelta
from typing import Dict, Generator, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright, Page
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .base_scraper import BaseJobScraper
from .human_behavior import HumanBehaviorMixin, UniversalClickPopupFramework

console = Console()

# Try to import job analyzer
try:
    from job_analyzer import JobAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    console.print("[yellow]⚠️ Job analyzer not available - basic analysis only[/yellow]")


class ElutaMultiBrowserScraper(HumanBehaviorMixin, BaseJobScraper):
    """
    Enhanced Eluta scraper using multiple browser contexts.
    Each browser context focuses on one keyword at a time for optimal performance.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        # Extract our custom parameters
        self.max_jobs_per_keyword = kwargs.pop("max_jobs_per_keyword", 50)
        self.max_keywords = kwargs.pop("max_keywords", None)
        self.max_pages_per_keyword = kwargs.pop("max_pages_per_keyword", 5)
        self.max_workers = kwargs.pop("max_workers", 2)  # 2-3 browser contexts as per memories for better performance and stability
        self.enable_deep_analysis = kwargs.pop("enable_deep_analysis", True)

        # Initialize base scraper
        super().__init__(profile, **kwargs)

        self.site_name = "eluta_multi_browser"
        self.base_url = "https://www.eluta.ca/search"
        self.requires_browser = True

        # Store keywords for searching
        self.keywords = profile.get("keywords", [])

        # Moderate delays to avoid bot detection (no location = fewer requests)
        self.page_delay = (2, 4)  # Moderate page delays
        self.click_delay = (1, 2)  # Moderate click delays
        self.worker_delay = (3, 5)  # Moderate delay between workers

        # Date filtering - last 14 days
        self.max_age_days = 14
        self.cutoff_date = datetime.now() - timedelta(days=self.max_age_days)

        # ATS system detection
        self.ats_systems = {
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

        # Enhanced human-like behavior settings as per memories
        self.human_delays = {
            "page_load": (2.0, 4.0),      # Wait after page loads
            "between_jobs": (1.0, 2.0),   # Wait between job clicks (1-second delays as per memories)
            "between_pages": (2.0, 4.0),  # Wait between pages
            "popup_wait": 3.0,            # Fixed 3-second wait for popups as per memories
            "pre_click": (0.2, 0.5),      # Wait before clicking
            "post_hover": (0.1, 0.3),     # Wait after hovering
            "keyword_switch": (2.0, 4.0), # Wait between keywords
            "context_startup": (3.0, 5.0) # Wait between browser context startups
        }

        # Initialize job analyzer if available
        if ANALYZER_AVAILABLE and self.enable_deep_analysis:
            self.job_analyzer = JobAnalyzer(use_ai=False)
            console.print("[green]✅ Job analyzer enabled for enhanced analysis[/green]")
        else:
            self.job_analyzer = None
            console.print("[yellow]⚠️ Job analyzer disabled - basic analysis only[/yellow]")

        # Limit keywords if specified
        if self.max_keywords and len(self.keywords) > self.max_keywords:
            self.keywords = self.keywords[:self.max_keywords]
            console.print(f"[yellow]⚠️ Limited to first {self.max_keywords} keywords[/yellow]")

        # Thread-safe job collection
        self.jobs_lock = threading.Lock()
        self.collected_jobs = []

        # Initialize universal click-popup framework
        self.click_popup_framework = UniversalClickPopupFramework("eluta")

        console.print(f"[green]✅ Multi-Browser Eluta scraper initialized with universal click-popup framework[/green]")
        console.print(f"[cyan]📅 Filtering jobs from last {self.max_age_days} days[/cyan]")
        console.print(f"[cyan]🔍 Will search {len(self.keywords)} keywords with {self.max_workers} browser contexts[/cyan]")
        console.print(f"[cyan]🎯 Max {self.max_jobs_per_keyword} jobs per keyword[/cyan]")
        console.print(f"[cyan]📄 Max {self.max_pages_per_keyword} pages per keyword[/cyan]")
        console.print(f"[cyan]⚡ Each browser context focuses on one keyword at a time[/cyan]")
    
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """Scrape jobs using multiple browser contexts."""
        console.print(f"\n[bold green]🚀 Starting Multi-Browser Eluta scraping[/bold green]")
        
        # Create progress tracker
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            # Create main progress task
            main_task = progress.add_task(
                f"[cyan]Scraping {len(self.keywords)} keywords...", 
                total=len(self.keywords)
            )
            
            # Process keywords in parallel with multiple browser contexts
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all keyword tasks
                future_to_keyword = {
                    executor.submit(self._scrape_keyword_worker, keyword, progress): keyword
                    for keyword in self.keywords
                }
                
                # Process completed tasks
                for future in as_completed(future_to_keyword):
                    keyword = future_to_keyword[future]
                    try:
                        keyword_jobs = future.result()
                        
                        # Thread-safe job collection
                        with self.jobs_lock:
                            self.collected_jobs.extend(keyword_jobs)
                        
                        console.print(f"[green]✅ Keyword '{keyword}' completed: {len(keyword_jobs)} jobs[/green]")
                        
                    except Exception as e:
                        console.print(f"[red]❌ Error processing keyword '{keyword}': {e}[/red]")
                    
                    finally:
                        progress.advance(main_task)
        
        # Yield all collected jobs
        console.print(f"\n[bold green]🎉 Multi-browser scraping completed: {len(self.collected_jobs)} total jobs[/bold green]")
        
        for job in self.collected_jobs:
            yield job
    
    def _scrape_keyword_worker(self, keyword: str, progress: Progress) -> List[Dict]:
        """Worker function to scrape a single keyword with dedicated browser context."""
        worker_jobs = []
        
        # Create worker progress task
        worker_task = progress.add_task(
            f"[yellow]Keyword: {keyword}", 
            total=self.max_pages_per_keyword
        )
        
        # Create dedicated browser context for this keyword
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,  # Visible browser to avoid detection
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                        "--disable-automation",
                        "--disable-extensions",
                        "--no-first-run",
                        "--disable-default-apps",
                        "--disable-background-timer-throttling",
                        "--disable-backgrounding-occluded-windows",
                        "--disable-renderer-backgrounding"
                    ]
                )
                # Randomize user agent and viewport for each context
                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ]

                viewports = [
                    {"width": 1366, "height": 768},
                    {"width": 1920, "height": 1080},
                    {"width": 1440, "height": 900},
                    {"width": 1280, "height": 720}
                ]

                import random
                selected_ua = random.choice(user_agents)
                selected_viewport = random.choice(viewports)

                context = browser.new_context(
                    viewport=selected_viewport,
                    user_agent=selected_ua,
                    extra_http_headers={
                        "Accept-Language": "en-US,en;q=0.9,en-CA;q=0.8",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1"
                    }
                )
                page = context.new_page()
                
                console.print(f"[blue]🌐 Browser context created for keyword: {keyword}[/blue]")
                
                try:
                    # Search this keyword across multiple pages
                    for page_num in range(1, self.max_pages_per_keyword + 1):
                        try:
                            page_jobs = self._scrape_keyword_page(page, keyword, page_num)
                            worker_jobs.extend(page_jobs)
                            
                            progress.advance(worker_task)
                            
                            # Stop if no jobs found on this page
                            if not page_jobs:
                                console.print(f"[yellow]No jobs on page {page_num} for '{keyword}'[/yellow]")
                                break
                            
                            # Enhanced delay between pages using human-like behavior
                            if page_num < self.max_pages_per_keyword:
                                delay = random.uniform(*self.human_delays["between_pages"])
                                console.print(f"[cyan]⏳ Human-like delay {delay:.1f}s before next page...[/cyan]")
                                time.sleep(delay)
                                
                        except Exception as e:
                            console.print(f"[red]❌ Page {page_num} error for '{keyword}': {e}[/red]")
                            progress.advance(worker_task)
                            continue
                    
                except Exception as e:
                    console.print(f"[red]❌ Worker error for '{keyword}': {e}[/red]")
                finally:
                    try:
                        browser.close()
                        console.print(f"[blue]🗙 Browser context closed for keyword: {keyword}[/blue]")
                    except:
                        pass
                        
        except Exception as e:
            console.print(f"[red]❌ Critical error for keyword '{keyword}': {e}[/red]")
        
        return worker_jobs

    def _scrape_keyword_page(self, page: Page, keyword: str, page_num: int) -> List[Dict]:
        """Scrape a single page for a keyword."""
        try:
            # Build search URL without location (use Eluta's default)
            search_url = f"{self.base_url}?q={urllib.parse.quote(keyword)}"
            if page_num > 1:
                search_url += f"&pg={page_num}"

            # Navigate to search page with enhanced human-like behavior
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            # Enhanced page load delay as per memories
            page_delay = random.uniform(*self.human_delays["page_load"])
            console.print(f"[yellow]⏳ Human-like page load delay: {page_delay:.1f}s[/yellow]")
            time.sleep(page_delay)

            # Check for CAPTCHA or verification page
            if self._is_captcha_page(page):
                console.print(f"[red]🚫 CAPTCHA detected for keyword '{keyword}' - skipping[/red]")
                return []

            # Find job containers using proven selector
            job_elements = page.query_selector_all(".organic-job")

            if not job_elements:
                return []

            page_jobs = []
            jobs_processed = 0

            # Process each job on this page
            for i, job_elem in enumerate(job_elements):
                if jobs_processed >= self.max_jobs_per_keyword:
                    break

                job_data = self._extract_job_data(job_elem, page, f"{keyword}-{page_num}-{i+1}")
                if job_data:
                    # Add keyword context
                    job_data["search_keyword"] = keyword
                    job_data["page_number"] = page_num

                    page_jobs.append(job_data)
                    jobs_processed += 1

                # Enhanced delay between jobs using human-like behavior (1-second delays as per memories)
                job_delay = random.uniform(*self.human_delays["between_jobs"])
                time.sleep(job_delay)

            return page_jobs

        except Exception as e:
            console.print(f"[red]❌ Error scraping page {page_num} for keyword '{keyword}': {e}[/red]")
            return []

    def _extract_job_data(self, job_elem, page: Page, job_id: str) -> Optional[Dict]:
        """Extract job data using proven method with enhanced analysis."""
        try:
            # Step 1: Extract basic data from text
            text = job_elem.inner_text().strip()
            lines = [line.strip() for line in text.split('\n') if line.strip()]

            if len(lines) < 2:
                return None

            # Parse job data
            job_data = {
                "title": "",
                "company": "",
                "location": "",
                "salary": "",
                "summary": "",
                "url": "",
                "apply_url": "",
                "site": self.site_name,
                "scraped_at": datetime.now().isoformat(),
                "deep_scraped": False
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

            # Parse summary/description
            if len(lines) > 3:
                job_data["summary"] = " ".join(lines[3:])[:300] + "..."

            # Check if job is within 14-day filter
            if not self._is_job_recent_enough(job_data):
                return None

            # Check if job is entry-level (0-3 years experience)
            if not self._is_entry_level_job(job_data):
                return None

            # Step 2: Get real URL using universal click-popup framework
            real_url = self.universal_extract_job_url(job_elem, page, job_id)
            if real_url:
                job_data["apply_url"] = real_url
                job_data["url"] = real_url
                job_data["ats_system"] = self._detect_ats_system(real_url)
                job_data["deep_scraped"] = True
            else:
                # Fallback to search page URL
                job_data["url"] = page.url
                job_data["apply_url"] = page.url

            # Step 3: Enhanced job analysis if analyzer is available
            if self.job_analyzer:
                try:
                    enhanced_job = self.job_analyzer.analyze_job_deep(job_data, None)

                    # Add match score for this user
                    if "requirements" in enhanced_job:
                        from job_analyzer import JobRequirements
                        requirements = JobRequirements(**enhanced_job["requirements"])
                        match_score = self.job_analyzer.calculate_job_match_score(requirements, self.profile)
                        enhanced_job["match_score"] = match_score
                        enhanced_job["recommended"] = match_score >= 0.6

                    return enhanced_job

                except Exception:
                    # Return basic job data if analysis fails
                    return job_data

            return job_data

        except Exception as e:
            console.print(f"[red]❌ Error extracting job {job_id}: {e}[/red]")
            return None

    def _is_job_recent_enough(self, job: Dict) -> bool:
        """Check if a job was posted within the last 14 days."""
        posted_date = job.get("posted_date", "")

        if not posted_date:
            return True

        posted_date_lower = posted_date.lower()

        if "hour" in posted_date_lower or "minute" in posted_date_lower:
            return True

        if "day" in posted_date_lower:
            match = re.search(r'(\d+)\s*day', posted_date_lower)
            if match:
                days_ago = int(match.group(1))
                return days_ago <= self.max_age_days
            return True

        if "week" in posted_date_lower:
            match = re.search(r'(\d+)\s*week', posted_date_lower)
            if match:
                weeks_ago = int(match.group(1))
                return weeks_ago <= 2
            return False

        if "month" in posted_date_lower:
            return False

        return True

    def _is_entry_level_job(self, job: Dict) -> bool:
        """Check if a job is entry-level (0-3 years experience)."""
        title = job.get("title", "").lower()
        summary = job.get("summary", "").lower()

        # Senior-level keywords that indicate NOT entry-level
        senior_keywords = [
            "senior", "sr.", "lead", "principal", "director", "manager", "mgr",
            "head of", "chief", "vp", "vice president", "supervisor", "team lead",
            "architect", "expert", "specialist", "consultant", "5+ years",
            "6+ years", "7+ years", "8+ years", "9+ years", "10+ years",
            "5 years", "6 years", "7 years", "8 years", "9 years", "10 years"
        ]

        # Check title for senior keywords
        for keyword in senior_keywords:
            if keyword in title:
                return False

        # Check summary for experience requirements
        for keyword in senior_keywords:
            if keyword in summary:
                return False

        # Entry-level indicators (positive signals)
        entry_keywords = [
            "junior", "jr.", "entry", "entry-level", "graduate", "new grad",
            "associate", "trainee", "intern", "co-op", "0-2 years", "0-3 years",
            "1-2 years", "1-3 years", "recent graduate", "fresh graduate"
        ]

        # If explicitly mentions entry-level terms, definitely include
        for keyword in entry_keywords:
            if keyword in title or keyword in summary:
                return True

        # If no clear indicators either way, include it (benefit of doubt for entry-level)
        return True

    def _get_real_job_url(self, job_elem, page: Page, job_id: str) -> Optional[str]:
        """Get real job URL using enhanced click-and-popup method with 3-second wait."""
        try:
            # Find job title link with improved selection logic
            links = job_elem.query_selector_all("a")
            title_link = None

            # Enhanced link selection - prioritize job title links
            for link in links:
                link_text = link.inner_text().strip()
                href = link.get_attribute("href") or ""

                # Prioritize links that look like job titles (longer text, job-related href)
                if link_text and len(link_text) > 10:
                    # Check if this looks like a job title link
                    if ("/job/" in href or "/direct/" in href or
                        any(keyword in link_text.lower() for keyword in ["analyst", "developer", "engineer", "manager", "specialist"])):
                        title_link = link
                        break
                    elif not title_link:  # Fallback to first decent link
                        title_link = link

            if not title_link:
                console.print(f"[yellow]⚠️ No title link found for job {job_id}[/yellow]")
                return None

            # Enhanced click-and-popup method with human-like behavior
            console.print(f"[cyan]🖱️ Clicking title link for job {job_id}...[/cyan]")

            # Add human-like pre-click behavior using configured delays
            try:
                # Scroll element into view if needed
                title_link.scroll_into_view_if_needed()
                time.sleep(random.uniform(*self.human_delays["pre_click"]))

                # Hover before clicking (human-like)
                title_link.hover()
                time.sleep(random.uniform(*self.human_delays["post_hover"]))
            except:
                pass  # Continue if hover/scroll fails

            # Try enhanced expect_popup method with 3-second wait as requested
            try:
                with page.expect_popup(timeout=8000) as popup_info:  # Increased timeout for reliability
                    title_link.click()
                    # KEY: Fixed 3-second wait as specified in memories
                    console.print(f"[yellow]⏳ Waiting {self.human_delays['popup_wait']} seconds for popup to fully load (as per memories)...[/yellow]")
                    time.sleep(self.human_delays["popup_wait"])

                popup = popup_info.value
                popup_url = popup.url

                # Enhanced popup handling with validation
                if popup_url and "eluta.ca" not in popup_url:
                    console.print(f"[green]✅ Got external ATS URL: {popup_url[:60]}...[/green]")
                else:
                    console.print(f"[cyan]📋 Got Eluta URL: {popup_url[:60]}...[/cyan]")

                # Close popup with error handling
                try:
                    popup.close()
                    console.print(f"[cyan]🗙 Closed popup tab for job {job_id}[/cyan]")
                except Exception as close_error:
                    console.print(f"[yellow]⚠️ Could not close popup: {close_error}[/yellow]")

                return popup_url

            except Exception as popup_error:
                console.print(f"[yellow]⚠️ Popup method failed for job {job_id}: {popup_error}[/yellow]")
                # Enhanced fallback - try to get href attribute
                href = title_link.get_attribute("href")
                if href and not href.startswith("#") and href != "javascript:void(0)":
                    return href
                return None

        except Exception:
            return None

    def _detect_ats_system(self, url: str) -> str:
        """Detect ATS system from URL."""
        if not url:
            return "Unknown"

        url_lower = url.lower()
        for keyword, system in self.ats_systems.items():
            if keyword in url_lower:
                return system

        return "Company Website"

    def _is_captcha_page(self, page: Page) -> bool:
        """Check if the current page is a CAPTCHA or verification page."""
        try:
            page_content = page.content().lower()
            page_title = page.title().lower()

            # Common CAPTCHA indicators
            captcha_indicators = [
                "verify you are human",
                "human verification",
                "security check",
                "unusual traffic",
                "captcha",
                "cloudflare",
                "please verify",
                "bot detection",
                "automated requests",
                "suspicious activity"
            ]

            for indicator in captcha_indicators:
                if indicator in page_content or indicator in page_title:
                    return True

            # Check for specific CAPTCHA elements
            captcha_selectors = [
                "iframe[src*='captcha']",
                "div[class*='captcha']",
                "div[id*='captcha']",
                ".cf-browser-verification",
                "#challenge-form",
                ".challenge-form"
            ]

            for selector in captcha_selectors:
                if page.query_selector(selector):
                    return True

            return False

        except Exception:
            return False
