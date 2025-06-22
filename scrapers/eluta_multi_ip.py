"""
Enhanced Eluta scraper with multiple IP addresses using proxies.
Each browser context uses a different IP address to avoid detection.
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

console = Console()

# Try to import job analyzer
try:
    from job_analyzer import JobAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    console.print("[yellow]⚠️ Job analyzer not available - basic analysis only[/yellow]")


class ElutaMultiIPScraper(BaseJobScraper):
    """
    Enhanced Eluta scraper using multiple IP addresses via proxies.
    Each browser context uses a different IP address to avoid detection.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        # Extract our custom parameters
        self.max_jobs_per_keyword = kwargs.pop("max_jobs_per_keyword", 50)
        self.max_keywords = kwargs.pop("max_keywords", None)
        self.max_pages_per_keyword = kwargs.pop("max_pages_per_keyword", 5)
        self.max_workers = kwargs.pop("max_workers", 2)  # 2 different IPs
        self.enable_deep_analysis = kwargs.pop("enable_deep_analysis", True)
        
        # Proxy configuration (you would need to provide actual proxy servers)
        self.proxy_list = kwargs.pop("proxy_list", [
            # Example proxy format - you would need real proxies
            # {"server": "http://proxy1.example.com:8080", "username": "user1", "password": "pass1"},
            # {"server": "http://proxy2.example.com:8080", "username": "user2", "password": "pass2"},
        ])

        # Initialize base scraper
        super().__init__(profile, **kwargs)

        self.site_name = "eluta_multi_ip"
        self.base_url = "https://www.eluta.ca/search"
        self.requires_browser = True

        # Store keywords for searching
        self.keywords = profile.get("keywords", [])

        # Conservative delays for multiple IPs
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

        # Check proxy configuration
        if self.proxy_list:
            console.print(f"[green]✅ Multi-IP Eluta scraper initialized with {len(self.proxy_list)} proxy servers[/green]")
            console.print(f"[cyan]🌐 Each browser context will use a different IP address[/cyan]")
        else:
            console.print(f"[yellow]⚠️ No proxies configured - using single IP with multiple contexts[/yellow]")
            console.print(f"[cyan]💡 To use multiple IPs, configure proxy_list parameter[/cyan]")

        console.print(f"[cyan]📅 Filtering jobs from last {self.max_age_days} days[/cyan]")
        console.print(f"[cyan]🔍 Will search {len(self.keywords)} keywords with {self.max_workers} browser contexts[/cyan]")
        console.print(f"[cyan]🎯 Max {self.max_jobs_per_keyword} jobs per keyword[/cyan]")
        console.print(f"[cyan]📄 Max {self.max_pages_per_keyword} pages per keyword[/cyan]")
        console.print(f"[cyan]📍 Using Eluta's default location (no location parameter)[/cyan]")
    
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """Scrape jobs using multiple IP addresses."""
        console.print(f"\n[bold green]🚀 Starting Multi-IP Eluta scraping[/bold green]")
        
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
            
            # Process keywords in parallel with multiple IPs
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all keyword tasks with different IPs
                future_to_keyword = {}
                for i, keyword in enumerate(self.keywords):
                    # Assign proxy/IP to this worker
                    proxy_config = None
                    if self.proxy_list:
                        proxy_config = self.proxy_list[i % len(self.proxy_list)]
                    
                    future = executor.submit(self._scrape_keyword_worker, keyword, progress, proxy_config)
                    future_to_keyword[future] = keyword
                
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
        console.print(f"\n[bold green]🎉 Multi-IP scraping completed: {len(self.collected_jobs)} total jobs[/bold green]")
        
        for job in self.collected_jobs:
            yield job
    
    def _scrape_keyword_worker(self, keyword: str, progress: Progress, proxy_config: Optional[Dict] = None) -> List[Dict]:
        """Worker function to scrape a single keyword with dedicated IP address."""
        worker_jobs = []
        
        # Create worker progress task
        worker_task = progress.add_task(
            f"[yellow]Keyword: {keyword}", 
            total=self.max_pages_per_keyword
        )
        
        # Create dedicated browser context for this keyword with specific IP
        try:
            with sync_playwright() as p:
                # Configure browser with proxy if available
                browser_args = [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-automation",
                    "--disable-extensions",
                    "--no-first-run",
                    "--disable-default-apps"
                ]
                
                browser = p.chromium.launch(
                    headless=False,  # Visible browser to avoid detection
                    args=browser_args
                )
                
                # Configure context with proxy if available
                context_config = {
                    "viewport": {"width": 1366, "height": 768},
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "extra_http_headers": {
                        "Accept-Language": "en-US,en;q=0.9,en-CA;q=0.8",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1"
                    }
                }
                
                # Add proxy configuration if available
                if proxy_config:
                    context_config["proxy"] = proxy_config
                    console.print(f"[blue]🌐 Using proxy for keyword '{keyword}': {proxy_config['server']}[/blue]")
                else:
                    console.print(f"[blue]🌐 Using default IP for keyword '{keyword}'[/blue]")
                
                context = browser.new_context(**context_config)
                page = context.new_page()
                
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
                            
                            # Moderate delay between pages
                            if page_num < self.max_pages_per_keyword:
                                delay = random.uniform(*self.worker_delay)
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

            # Navigate to search page
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(random.uniform(*self.page_delay))

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

                # Small delay between jobs
                time.sleep(random.uniform(*self.click_delay))

            return page_jobs

        except Exception as e:
            console.print(f"[red]❌ Error scraping page {page_num} for keyword '{keyword}': {e}[/red]")
            return []

    def _extract_job_data(self, job_elem, page: Page, job_id: str) -> Optional[Dict]:
        """Extract job data using proven method."""
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

            # Step 2: Get real URL using proven expect_popup method
            real_url = self._get_real_job_url(job_elem, page)
            if real_url:
                job_data["apply_url"] = real_url
                job_data["url"] = real_url
                job_data["ats_system"] = self._detect_ats_system(real_url)
                job_data["deep_scraped"] = True
            else:
                # Fallback to search page URL
                job_data["url"] = page.url
                job_data["apply_url"] = page.url

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
        senior_keywords = [
            "senior", "sr.", "lead", "principal", "director", "manager", "mgr",
            "head of", "chief", "vp", "vice president", "supervisor", "team lead",
            "architect", "expert", "specialist", "consultant", "5+ years",
            "6+ years", "7+ years", "8+ years", "9+ years", "10+ years",
            "5 years", "6 years", "7 years", "8 years", "9 years", "10 years"
        ]
        for keyword in senior_keywords:
            if keyword in title or keyword in summary:
                return False
        return True

    def _get_real_job_url(self, job_elem, page: Page) -> Optional[str]:
        """Get real job URL using proven expect_popup method with fallback."""
        try:
            links = job_elem.query_selector_all("a")
            title_link = None
            for link in links:
                link_text = link.inner_text().strip()
                if link_text and len(link_text) > 10:
                    title_link = link
                    break
            if not title_link:
                return None
            try:
                with page.expect_popup(timeout=5000) as popup_info:
                    title_link.click()
                    time.sleep(1)
                popup = popup_info.value
                popup_url = popup.url
                popup.close()
                return popup_url
            except Exception:
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
            captcha_indicators = [
                "verify you are human", "human verification", "security check",
                "unusual traffic", "captcha", "cloudflare", "please verify",
                "bot detection", "automated requests", "suspicious activity"
            ]
            for indicator in captcha_indicators:
                if indicator in page_content or indicator in page_title:
                    return True
            captcha_selectors = [
                "iframe[src*='captcha']", "div[class*='captcha']", "div[id*='captcha']",
                ".cf-browser-verification", "#challenge-form", ".challenge-form"
            ]
            for selector in captcha_selectors:
                if page.query_selector(selector):
                    return True
            return False
        except Exception:
            return False
