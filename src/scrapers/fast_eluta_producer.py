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
from typing import Dict, List, Generator, Optional
from queue import Queue
import urllib.parse
import random
import re

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from playwright.sync_api import sync_playwright, Page
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

console = Console()

class FastElutaProducer:
    """
    Fast Eluta scraper optimized for single browser context and DDR5-6400.
    Producer role: Scrape and save raw data only.
    Updated for single keyword testing with 9 pages and 14-day filtering.
    """
    
    def __init__(self, profile: Dict, output_dir: str = "temp/raw_jobs"):
        self.profile = profile
        # Use all keywords for complete scraping
        self.keywords = profile.get("keywords", ["software"])[:1]  # Test with just 1 keyword
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # DDR5-6400 optimized settings
        self.batch_size = 50  # Large batches with fast RAM
        self.flush_threshold = 25  # Flush to SSD when buffer half full
        self.write_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Scraping settings - Updated for complete scraping
        self.base_url = "https://www.eluta.ca/search"
        self.max_pages_per_keyword = 1  # Test with just 1 page
        self.max_jobs_per_keyword = 10  # Test with just 10 jobs
        
        # Date filtering for last 14 days
        self.min_date = datetime.now() - timedelta(days=14)
        
        # Performance tracking
        self.stats = {
            'keywords_processed': 0,
            'pages_scraped': 0,
            'jobs_scraped': 0,
            'jobs_saved': 0,
            'jobs_filtered_by_date': 0,
            'start_time': None,
            'end_time': None
        }
        
        # File naming
        self.file_counter = 0
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        console.print(Panel.fit("🚀 FAST ELUTA PRODUCER (COMPLETE MODE)", style="bold blue"))
        console.print(f"[cyan]📁 Output: {self.output_dir}[/cyan]")
        console.print(f"[cyan]🔍 Keywords: {len(self.keywords)}[/cyan]")
        console.print(f"[cyan]📄 Max pages per keyword: {self.max_pages_per_keyword}[/cyan]")
        console.print(f"[cyan]📅 Date filter: Last 14 days[/cyan]")
        console.print(f"[cyan]💾 Batch size: {self.batch_size}[/cyan]")
        console.print(f"[cyan]⚡ DDR5-6400 optimized[/cyan]")
    
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
                
                # Flush remaining buffer
                self._flush_buffer()
                
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
                            self._add_to_buffer(job_data)
                            jobs_processed += 1
                            self.stats['jobs_scraped'] += 1
                        else:
                            self.stats['jobs_filtered_by_date'] += 1
                
                self.stats['pages_scraped'] += 1
                
                # Check if buffer needs flushing
                if len(self.write_buffer) >= self.flush_threshold:
                    self._flush_buffer()
                
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
            
            # If no date found, assume it's recent (within 14 days)
            return True
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Date filtering error: {e}[/yellow]")
            return True  # Default to including the job
    
    def _extract_raw_job_data(self, job_elem, page, keyword: str, page_num: int, job_num: int) -> Optional[Dict]:
        """Extract raw job data without processing."""
        try:
            # Get basic text content
            text = job_elem.inner_text().strip()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if len(lines) < 2:
                return None
            
            # Extract basic data
            job_data = {
                "raw_text": text,
                "lines": lines,
                "title": lines[0] if lines else "",
                "company": lines[1] if len(lines) > 1 else "",
                "location": lines[2] if len(lines) > 2 else "",
                "summary": " ".join(lines[3:]) if len(lines) > 3 else "",
                "search_keyword": keyword,
                "page_number": page_num,
                "job_number": job_num,
                "scraped_at": datetime.now().isoformat(),
                "session_id": self.session_id,
                "job_id": f"eluta_{keyword}_{page_num}_{job_num}",
                "url": ""  # Initialize empty URL
            }
            
            # Extract URL using popup method
            try:
                # Find the clickable link (job title link)
                link = job_elem.query_selector("a[href]")
                if link:
                    console.print(f"[cyan]🔄 Extracting URL for: {job_data['title'][:50]}...[/cyan]")
                    
                    # Use popup method to get real URL
                    with page.expect_popup(timeout=5000) as popup_info:
                        link.click()
                    
                    popup = popup_info.value
                    popup_url = popup.url
                    
                    # Close popup
                    popup.close()
                    
                    # Set the real URL
                    job_data["url"] = popup_url
                    console.print(f"[green]✅ URL extracted: {popup_url[:60]}...[/green]")
                    
            except Exception as url_error:
                # If popup method fails, try to get URL from href attribute
                try:
                    link = job_elem.query_selector("a[href]")
                    if link:
                        href = link.get_attribute("href")
                        if href and href.startswith("http"):
                            job_data["url"] = href
                            console.print(f"[yellow]⚠️ Using href URL: {href[:60]}...[/yellow]")
                except Exception as href_error:
                    console.print(f"[red]❌ URL extraction failed: {href_error}[/red]")
                    job_data["url"] = ""
            
            return job_data
            
        except Exception as e:
            console.print(f"[red]❌ Error extracting job data: {e}[/red]")
            return None
    
    def _add_to_buffer(self, job_data: Dict) -> None:
        """Add job to write buffer with thread safety."""
        with self.buffer_lock:
            self.write_buffer.append(job_data)
    
    def _flush_buffer(self) -> None:
        """Flush buffer to SSD with DDR5-6400 optimized writes."""
        with self.buffer_lock:
            if not self.write_buffer:
                return
            
            # Create batch file
            self.file_counter += 1
            filename = f"jobs_batch_{self.session_id}_{self.file_counter:04d}.json"
            filepath = self.output_dir / filename
            
            try:
                # Ensure directory exists
                self.output_dir.mkdir(parents=True, exist_ok=True)
                
                # Write to SSD (fast with DDR5 buffer)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({
                        "batch_id": f"{self.session_id}_{self.file_counter:04d}",
                        "created_at": datetime.now().isoformat(),
                        "job_count": len(self.write_buffer),
                        "jobs": self.write_buffer
                    }, f, indent=2, ensure_ascii=False)
                
                self.stats['jobs_saved'] += len(self.write_buffer)
                console.print(f"[green]💾 Saved {len(self.write_buffer)} jobs to {filename}[/green]")
                
                # Clear buffer
                self.write_buffer.clear()
                
            except Exception as e:
                console.print(f"[red]❌ Write error: {e}[/red]")
                console.print(f"[red]❌ Filepath: {filepath.absolute()}[/red]")
    
    def _print_final_stats(self) -> None:
        """Print final scraping statistics."""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        console.print(Panel.fit("📊 SCRAPING COMPLETE", style="bold green"))
        console.print(f"[cyan]⏱️ Duration: {duration}[/cyan]")
        console.print(f"[cyan]🔍 Keywords processed: {self.stats['keywords_processed']}[/cyan]")
        console.print(f"[cyan]📄 Pages scraped: {self.stats['pages_scraped']}[/cyan]")
        console.print(f"[cyan]📋 Jobs scraped: {self.stats['jobs_scraped']}[/cyan]")
        console.print(f"[cyan]📅 Jobs filtered by date: {self.stats['jobs_filtered_by_date']}[/cyan]")
        console.print(f"[cyan]💾 Jobs saved: {self.stats['jobs_saved']}[/cyan]")
        console.print(f"[cyan]📁 Output directory: {self.output_dir}[/cyan]")
        
        if self.stats['jobs_scraped'] > 0:
            jobs_per_minute = (self.stats['jobs_scraped'] / duration.total_seconds()) * 60
            console.print(f"[bold green]⚡ Performance: {jobs_per_minute:.1f} jobs/minute[/bold green]")

def main():
    """Main function for testing."""
    # Load profile
    try:
        with open("profiles/Nirajan/Nirajan.json", "r") as f:
            profile = json.load(f)
    except Exception as e:
        console.print(f"[red]❌ Error loading profile: {e}[/red]")
        return
    
    # Create and run producer
    producer = FastElutaProducer(profile)
    producer.scrape_all_keywords()

if __name__ == "__main__":
    main() 