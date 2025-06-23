#!/usr/bin/env python3
"""
Fast Eluta Producer - Optimized for DDR5-6400 and single browser context.
Focuses only on scraping and saving raw data for maximum speed.
Updated for single keyword testing with 9 pages and 14-day filtering.
"""

import json
import os
import time
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Generator, Optional, Any
from queue import Queue
import urllib.parse
import random
import re
import hashlib

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from playwright.sync_api import sync_playwright, Page
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

console = Console()

# Import BeautifulSoup for real data extraction
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    console.print("[yellow]⚠️ BeautifulSoup not available. Real data extraction will be limited.[/yellow]")

# Import the new JobProcessor
from src.utils.job_data_consumer import JobProcessor

class FastElutaProducer:
    """
    Fast Eluta scraper optimized for single browser context.
    Submits jobs directly to a JobProcessor.
    """
    
    def __init__(self, profile: Dict, processor: Any):
        self.profile = profile
        self.keywords = profile.get("keywords", ["software"])
        self.processor = processor
        self.output_dir = Path("temp/raw_jobs") # For debug files
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Scraping settings
        self.base_url = "https://www.eluta.ca/search"
        self.max_pages_per_keyword = profile.get("pages_to_scrape", 2)
        self.max_jobs_per_keyword = 50 # Limit jobs per keyword
        
        # Date filtering for last 14 days
        self.min_date = datetime.now() - timedelta(days=14)
        
        # Performance tracking
        self.stats = {
            'keywords_processed': 0,
            'pages_scraped': 0,
            'jobs_scraped': 0,
            'jobs_submitted': 0,
            'jobs_filtered_by_date': 0,
            'start_time': None,
            'end_time': None
        }
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        console.print(Panel.fit("🚀 FAST ELUTA PRODUCER (PROCESSOR MODE)", style="bold blue"))
        console.print(f"🔗 Processor: Attached")
        console.print(f"🔍 Keywords: {len(self.keywords)}")
        console.print(f"📄 Max pages per keyword: {self.max_pages_per_keyword}")
        console.print(f"📅 Date filter: Last 14 days")
    
    def scrape_all_keywords(self) -> None:
        """Scrape all keywords and save raw data."""
        self.stats['start_time'] = datetime.now()
        
        console.print(f"\n[bold green]🎯 Starting complete scraping session: {self.session_id}[/bold green]")
        console.print(f"[yellow]🚀 COMPLETE MODE: Using {len(self.keywords)} keywords with {self.max_pages_per_keyword} pages each[/yellow]")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,  # Visible for stability
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
                
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                page = context.new_page()
                
                # Try to navigate to the base page first to accept cookies, etc.
                try:
                    console.print("[cyan]Navigating to Eluta base page to warm up...[/cyan]")
                    page.goto("https://www.eluta.ca/", timeout=30000)
                    time.sleep(random.uniform(2, 4))
                except Exception as e:
                    console.print(f"[yellow]⚠️ Could not warm up base page: {e}[/yellow]")

                # Scrape each keyword
                for keyword in self.keywords:
                    console.print(f"\n[bold blue]🔍 Scraping keyword: {keyword}[/bold blue]")
                    self._scrape_keyword(page, keyword)
                    self.stats['keywords_processed'] += 1
                    
                    # Small delay between keywords
                    time.sleep(2)
                
        except Exception as e:
            console.print(f"[red]❌ Scraping error: {e}[/red]")
        finally:
            self.stats['end_time'] = datetime.now()
            self._print_final_stats()
    
    def _scrape_keyword(self, page: Page, keyword: str) -> None:
        """Scrape a single keyword across multiple pages."""
        jobs_processed = 0
        
        for page_num in range(1, self.max_pages_per_keyword + 1):
            if jobs_processed >= self.max_jobs_per_keyword:
                break
                
            console.print(f"[cyan]📄 Page {page_num}/{self.max_pages_per_keyword} for '{keyword}'[/cyan]")
            
            # Build search URL with date filter for last 14 days
            search_url = f"{self.base_url}?q={urllib.parse.quote(keyword)}"
            if page_num > 1:
                search_url += f"&pg={page_num}"
            
            # Add date filter for last 14 days
            date_filter = f"&date={self.min_date.strftime('%Y-%m-%d')}"
            search_url += date_filter
            
            try:
                # Navigate to search page
                page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
                
                # More human-like waiting
                page.wait_for_timeout(random.uniform(2000, 4000))
                page.mouse.move(random.randint(400, 800), random.randint(200, 400))
                page.wait_for_load_state("networkidle", timeout=15000)

                # Check for CAPTCHA
                if "User Verification" in page.title():
                    console.print("[red]❌ CAPTCHA detected. Aborting this keyword.[/red]")
                    # Saving the HTML for debugging
                    debug_path = self.output_dir / f"captcha_debug_{keyword}.html"
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(page.content())
                    console.print(f"[yellow]⚠️ CAPTCHA HTML saved to {debug_path}[/yellow]")
                    break

                # Find job elements
                job_elements = page.query_selector_all(".job-item") # Updated selector based on manual check
                
                if not job_elements:
                    console.print(f"[yellow]⚠️ No jobs found on page {page_num}. Trying legacy selector...[/yellow]")
                    job_elements = page.query_selector_all(".organic-job")

                if not job_elements:
                    console.print(f"[yellow]⚠️ Still no jobs found on page {page_num}. The page structure might have changed.[/yellow]")
                    # Saving the HTML for debugging
                    debug_path = self.output_dir / f"no_jobs_debug_{keyword}_{page_num}.html"
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(page.content())
                    console.print(f"[yellow]⚠️ No-jobs HTML saved to {debug_path}[/yellow]")
                    break
                
                console.print(f"[green]✅ Found {len(job_elements)} jobs on page {page_num}[/green]")
                
                # Extract and save jobs
                for i, job_elem in enumerate(job_elements):
                    if jobs_processed >= self.max_jobs_per_keyword:
                        break
                    
                    job_data = self._extract_raw_job_data(job_elem, page, keyword, page_num, i+1)
                    if job_data:
                        # Check if job is within last 14 days
                        if self._is_job_within_date_range(job_data):
                            self._submit_job_to_processor(job_data)
                            jobs_processed += 1
                            self.stats['jobs_scraped'] += 1
                        else:
                            self.stats['jobs_filtered_by_date'] += 1
                
                self.stats['pages_scraped'] += 1
                
                # Brief delay between pages
                time.sleep(1)
                
            except Exception as e:
                console.print(f"[red]❌ Page {page_num} error: {e}[/red]")
                continue
    
    def _is_job_within_date_range(self, job_data: Dict) -> bool:
        """Check if job is within the last 14 days."""
        try:
            # Look for date information in the job data
            text = job_data.get("raw_text", "").lower()
            
            # Common date patterns
            date_patterns = [
                r'(\d{1,2})\s+(days?|hours?|minutes?)\s+ago',
                r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}/\d{1,2}/\d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    # If we find "days ago" and it's more than 14, filter out
                    if 'days ago' in match.group(0):
                        days_ago = int(match.group(1))
                        if days_ago > 14:
                            return False
                    # For other patterns, assume it's recent enough
                    return True
            
            # If no date found, assume it's recent
            return True
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Date filtering error: {e}[/yellow]")
            return True  # Default to including the job
    
    def _extract_raw_job_data(self, job_elem, page, keyword: str, page_num: int, job_num: int) -> Optional[Dict]:
        """Extracts raw job data from a single job element using the proven click-and-wait method."""
        try:
            with page.expect_popup(timeout=10000) as popup_info:
                job_elem.click()
                time.sleep(1) # Simple, reliable 1-second delay

            popup = popup_info.value
            popup.wait_for_load_state('domcontentloaded', timeout=15000)
            
            real_url = popup.url
            title = popup.title()
            
            # Get the full HTML content for real data extraction
            html_content = popup.content()
            
            popup.close()

            # Extract basic data from the original listing
            company_elem = job_elem.query_selector('.company-name')
            company = company_elem.inner_text() if company_elem else ""
            
            location_elem = job_elem.query_selector('.location')
            location = location_elem.inner_text() if location_elem else ""
            
            summary_elem = job_elem.query_selector('.summary')
            summary = summary_elem.inner_text() if summary_elem else ""
            
            job_id_eluta = job_elem.get_attribute('data-job-id') or ""

            # Extract real job data from the popup HTML if BeautifulSoup is available
            if BEAUTIFULSOUP_AVAILABLE and html_content:
                enhanced_data = self._extract_real_job_data_from_html(html_content, real_url, title, company, location)
            else:
                enhanced_data = {
                    "title": title,
                    "company_name": company,
                    "location": location,
                    "summary": summary,
                    "job_description": summary
                }

            job_data = {
                "job_id": f"eluta_{job_id_eluta}",
                "title": enhanced_data.get("title", title),
                "company_name": enhanced_data.get("company_name", company),
                "location": enhanced_data.get("location", location),
                "summary": enhanced_data.get("summary", summary),
                "job_description": enhanced_data.get("job_description", summary),
                "job_url": real_url,
                "scraped_at": datetime.now().isoformat(),
                "search_keyword": keyword,
                "page_number": page_num,
                "job_number": job_num,
                "session_id": self.session_id,
                "raw_text": job_elem.inner_text(),
                "html_content": html_content  # Store the full HTML for later processing
            }
            return job_data

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not extract job data: {e}[/yellow]")
            return None

    def _extract_real_job_data_from_html(self, html_content: str, url: str, fallback_title: str, fallback_company: str, fallback_location: str) -> Dict:
        """Extract real job data from HTML content using BeautifulSoup."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract job title
            title = fallback_title
            title_selectors = [
                'h1', 'h2', '.job-title', '.title', '[data-testid="job-title"]',
                '.position-title', '.role-title', 'title'
            ]
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    extracted_title = element.get_text(strip=True)
                    if extracted_title and len(extracted_title) > 5 and extracted_title != fallback_title:
                        title = extracted_title
                        break
            
            # Extract company name
            company = fallback_company
            company_selectors = [
                '.company-name', '.company', '.employer', '[data-testid="company-name"]',
                '.organization', '.employer-name'
            ]
            for selector in company_selectors:
                element = soup.select_one(selector)
                if element:
                    extracted_company = element.get_text(strip=True)
                    if extracted_company and len(extracted_company) > 2:
                        company = extracted_company
                        break
            
            # Extract location
            location = fallback_location
            location_selectors = [
                '.location', '.job-location', '[data-testid="location"]',
                '.address', '.job-address'
            ]
            for selector in location_selectors:
                element = soup.select_one(selector)
                if element:
                    extracted_location = element.get_text(strip=True)
                    if extracted_location and len(extracted_location) > 3:
                        location = extracted_location
                        break
            
            # Extract job description/summary
            description = ""
            desc_selectors = [
                '.job-description', '.description', '.job-summary',
                '.job-details', '.content', '.job-content',
                '[data-testid="job-description"]', '.summary'
            ]
            for selector in desc_selectors:
                element = soup.select_one(selector)
                if element:
                    description = element.get_text(strip=True)
                    if description and len(description) > 50:  # Make sure it's substantial
                        break
            
            # If no description found, try to get main content
            if not description:
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    description = main_content.get_text(strip=True)[:2000]  # Limit length
            
            return {
                "title": title,
                "company_name": company,
                "location": location,
                "summary": description[:500] if description else "",  # Truncate summary
                "job_description": description
            }
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Real data extraction failed: {e}[/yellow]")
            return {
                "title": fallback_title,
                "company_name": fallback_company,
                "location": fallback_location,
                "summary": "",
                "job_description": ""
            }

    def _submit_job_to_processor(self, job_data: Dict) -> None:
        """Submits a job directly to the JobProcessor."""
        self.processor.submit_job(job_data)
        self.stats['jobs_submitted'] += 1
    
    def _print_final_stats(self) -> None:
        """Print final producer statistics."""
        if not self.stats['start_time']:
            return
            
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        console.print(Panel.fit("📊 PRODUCER COMPLETE", style="bold green"))
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right")
        
        table.add_row("Keywords Processed", f"{self.stats['keywords_processed']}")
        table.add_row("Pages Scraped", f"{self.stats['pages_scraped']}")
        table.add_row("Jobs Scraped", f"[green]{self.stats['jobs_scraped']}[/green]")
        table.add_row("Jobs Submitted to Processor", f"[cyan]{self.stats['jobs_submitted']}[/cyan]")
        table.add_row("Jobs Filtered by Date", f"[yellow]{self.stats['jobs_filtered_by_date']}[/yellow]")
        table.add_row("⏱️ Duration", f"{duration:.2f} seconds")
        
        console.print(table)


def main():
    """Main function for testing the producer independently."""
    console.print(Panel("Running FastElutaProducer Standalone Test", style="bold yellow"))
    
    # Dummy profile for testing
    test_profile = {
        "keywords": ["software developer", "project manager"],
        "pages_to_scrape": 1
    }

    # Dummy processor for testing
    class DummyProcessor:
        def __init__(self):
            self.submitted_jobs = []
        def submit_job(self, job_data):
            self.submitted_jobs.append(job_data)
            console.print(f"DummyProcessor received job: {job_data['title'][:30]}...")
        def wait_for_completion(self):
            console.print(f"DummyProcessor processed {len(self.submitted_jobs)} jobs.")

    processor = DummyProcessor()
    producer = FastElutaProducer(profile=test_profile, processor=processor)
    
    try:
        producer.scrape_all_keywords()
    finally:
        console.print("\nStandalone test finished.")
        console.print(f"Total jobs submitted to dummy processor: {len(processor.submitted_jobs)}")

if __name__ == "__main__":
    main() 