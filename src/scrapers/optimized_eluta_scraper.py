#!/usr/bin/env python3
"""
Optimized Eluta Scraper with Immediate Tab Closure and Concurrent Job Processing
- Closes tabs immediately after copying job URLs
- Processes jobs concurrently for better performance
- Improved resource management
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel
from playwright.async_api import async_playwright

from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile
from src.ats.ats_utils import detect_ats_system
from src.core.job_filters import filter_entry_level_jobs, remove_duplicates
from src.ai.enhanced_job_analyzer import EnhancedJobAnalyzer
from src.utils.simple_url_filter import get_simple_url_filter

console = Console()


class OptimizedElutaScraper:
    """
    Optimized Eluta scraper with immediate tab closure and concurrent processing.
    """

    def __init__(self, profile_name: str = "Nirajan"):
        """Initialize the optimized scraper."""
        self.profile_name = profile_name
        self.profile = load_profile(profile_name)
        if not self.profile:
            raise ValueError(f"Profile '{profile_name}' not found!")
        self.db = get_job_db(profile_name)

        # Only use 'keywords' from profile JSON for scraping
        self.keywords = self.profile.get("keywords", [])
        self.search_terms = list(self.keywords)
        console.print(f"[cyan]Loaded {len(self.search_terms)} keywords from profile JSON[/cyan]")

        # Initialize URL filter for reliable job URL validation
        self.url_filter = get_simple_url_filter()
        console.print("[green]✅ URL filter initialized - will skip invalid URLs[/green]")

        # Scraping settings
        self.base_url = "https://www.eluta.ca/search"
        self.max_pages_per_keyword = 8  # Full run: 8 pages per keyword
        self.jobs_per_page = 10
        self.delay_between_requests = 0.5  # Faster for testing
        self.max_concurrent_jobs = 2  # Process 2 jobs concurrently

        # Results tracking
        self.processed_urls = set()
        self.stats = {
            "keywords_processed": 0,
            "pages_scraped": 0,
            "jobs_found": 0,
            "duplicates_skipped": 0,
            "tabs_closed": 0,
        }

    async def scrape_all_keywords_optimized(self, max_jobs_per_keyword: int = 10) -> List[Dict]:
        """
        Optimized scraping with immediate tab closure and concurrent processing.
        
        Args:
            max_jobs_per_keyword: Maximum jobs to scrape per keyword
            
        Returns:
            List of saved job dictionaries
        """
        console.print(Panel.fit("OPTIMIZED ELUTA SCRAPING", style="bold green"))
        console.print(f"[cyan]🚀 Immediate tab closure enabled[/cyan]")
        console.print(f"[cyan]📊 {len(self.search_terms)} keywords × {self.max_pages_per_keyword} pages[/cyan]")

        # Display search terms
        console.print(f"\n[bold]Search Terms (first 5):[/bold]")
        for i, term in enumerate(self.search_terms[:5], 1):
            console.print(f"  {i:2d}. {term}")
        if len(self.search_terms) > 5:
            console.print(f"  ... and {len(self.search_terms) - 5} more")

        if not input(f"\nPress Enter to start optimized scraping or Ctrl+C to cancel..."):
            pass

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            try:
                with Progress() as progress:
                    main_task = progress.add_task(
                        "[green]Scraping keywords...", total=len(self.search_terms)
                    )

                    # Process all keywords for full run
                    all_keywords = self.search_terms
                    console.print(f"[yellow]🌐 Running full scrape with {len(all_keywords)} keywords[/yellow]")

                    for keyword_index, keyword in enumerate(all_keywords):
                        console.print(f"\n[bold]Processing: {keyword} ({keyword_index + 1}/{len(all_keywords)})[/bold]")
                        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
                        page = await context.new_page()
                        try:
                            # Scrape job URLs quickly (with immediate tab closure)
                            job_urls = await self._scrape_job_urls_fast(
                                page, keyword, max_jobs_per_keyword, progress
                            )
                            console.print(f"[green]✅ Found {len(job_urls)} job URLs for '{keyword}'[/green]")

                            # Save jobs to database with status 'scraped'
                            for job in job_urls:
                                if job.get("url"):
                                    job_record = {
                                        "title": job.get("title", ""),
                                        "company": job.get("company", ""),
                                        "location": job.get("location", ""),
                                        "url": job.get("url", ""),
                                        "search_keyword": keyword,
                                        "scraped_date": job.get("scraped_date", datetime.now().isoformat()),
                                        "status": "scraped"
                                    }
                                    self.db.add_job(job_record)
                                    console.print(f"[cyan]💾 Saved job to DB: {job_record['title']} at {job_record['company']}[/cyan]")

                            self.stats["keywords_processed"] += 1
                            progress.update(main_task, advance=1)
                        finally:
                            # Clean up context and ensure all tabs/pages are closed
                            console.print(f"[dim]🧹 Cleaning up context for keyword: {keyword}[/dim]")
                            for page in context.pages:
                                if not page.is_closed():
                                    try:
                                        await page.close()
                                        self.stats["tabs_closed"] += 1
                                    except Exception as e:
                                        console.print(f"[yellow]⚠️ Error closing page/tab: {e}[/yellow]")
                            await context.close()
                            await asyncio.sleep(self.delay_between_requests)
                console.print("[green]🎉 Scraping and saving jobs completed![/green]")
            finally:
                console.print("[dim]🧹 Closing browser...[/dim]")
                await browser.close()

    async def _scrape_job_urls_fast(
        self, page, keyword: str, max_jobs: int, progress: Progress
    ) -> List[Dict]:
        """
        Fast job URL scraping with immediate tab closure.
        
        Returns:
            List of job URL dictionaries with basic info
        """
        job_urls = []
        pages_scraped = 0

        try:
            # Navigate to search page
            search_url = f"{self.base_url}?q={keyword.replace(' ', '+')}+sort%3Arank"
            await page.goto(search_url, wait_until="networkidle")
            await asyncio.sleep(self.delay_between_requests)

            while pages_scraped < self.max_pages_per_keyword and len(job_urls) < max_jobs:
                pages_scraped += 1
                self.stats["pages_scraped"] += 1

                console.print(f"[cyan]📄 Scraping page {pages_scraped} for '{keyword}'[/cyan]")

                # Wait for job results
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(1)

                # Find job elements
                job_elements = await self._find_job_elements(page)
                console.print(f"[cyan]Found {len(job_elements)} job elements on page {pages_scraped}[/cyan]")

                if not job_elements:
                    console.print(f"[yellow]No job elements found on page {pages_scraped}, stopping[/yellow]")
                    break

                # Extract job URLs quickly
                for job_number, job_element in enumerate(job_elements, 1):
                    if len(job_urls) >= max_jobs:
                        break

                    try:
                        # Extract basic job info and URL quickly
                        job_url_data = await self._extract_job_url_fast(
                            page, job_element, job_number, pages_scraped, keyword
                        )

                        if job_url_data and job_url_data.get("url"):
                            # Check for duplicates
                            job_url = job_url_data.get("url", "")
                            if job_url in self.processed_urls:
                                self.stats["duplicates_skipped"] += 1
                                continue

                            self.processed_urls.add(job_url)
                            job_urls.append(job_url_data)
                            self.stats["jobs_found"] += 1

                            console.print(
                                f"[green]✅ URL {len(job_urls)}: {job_url_data['title'][:40]}...[/green]"
                            )

                    except Exception as e:
                        console.print(f"[red]Error extracting job {job_number}: {e}[/red]")
                        continue

                # Navigate to next page if needed
                if len(job_urls) < max_jobs and pages_scraped < self.max_pages_per_keyword:
                    next_page_num = pages_scraped + 1
                    next_page_url = f"{self.base_url}?q={keyword.replace(' ', '+')}+sort%3Arank&pg={next_page_num}"
                    console.print(f"[cyan]➡️ Going to page {next_page_num}[/cyan]")
                    await page.goto(next_page_url, wait_until="networkidle")
                    await asyncio.sleep(self.delay_between_requests)

        except Exception as e:
            console.print(f"[red]Error scraping URLs for keyword '{keyword}': {e}[/red]")

        return job_urls

    async def _find_job_elements(self, page) -> List:
        """Find job elements using multiple selectors."""
        job_elements = []
        
        selectors_to_try = [
            ".organic-job",
            ".job-result", 
            ".job-listing",
            ".job-item",
            "[data-job]",
            ".result",
            "article",
            ".listing"
        ]
        
        for selector in selectors_to_try:
            elements = await page.query_selector_all(selector)
            if elements:
                console.print(f"[green]Found {len(elements)} elements with selector: {selector}[/green]")
                job_elements = elements
                break
        
        # Fallback to title elements
        if not job_elements:
            title_elements = await page.query_selector_all("h2, h3")
            actual_job_elements = []
            for elem in title_elements:
                try:
                    text = await elem.inner_text()
                    if (len(text.strip()) > 15 and
                        any(keyword in text.lower() for keyword in ['developer', 'analyst', 'engineer', 'specialist', 'coordinator', 'manager', 'intern', 'associate', 'junior', 'senior'])):
                        actual_job_elements.append(elem)
                except:
                    continue
            job_elements = actual_job_elements
            
        return job_elements

    async def _extract_job_url_fast(
        self, page, job_element, job_number: int, page_num: int, keyword: str
    ) -> Dict:
        """
        Fast extraction of job URL and basic info with immediate tab closure.
        """
        try:
            # Get job title
            job_title = await job_element.inner_text()
            
            # Find job container
            job_container = job_element
            for _ in range(5):
                job_container = await job_container.query_selector("..")
                if not job_container:
                    break
                
                container_text = await job_container.inner_text()
                if any(keyword in container_text.lower() for keyword in ['company', 'location', 'salary']):
                    break
            
            if not job_container:
                return {}
            
            # Parse container text for basic info
            container_text = await job_container.inner_text()
            lines = [line.strip() for line in container_text.split("\n") if line.strip()]
            
            # Basic job data
            job_data = {
                "title": job_title,
                "company": "",
                "location": "",
                "salary": "",
                "url": "",
                "search_keyword": keyword,
                "scraped_date": datetime.now().isoformat(),
                "job_number": job_number,
                "page_number": page_num,
            }
            
            # Quick parsing for company and location
            for line in lines[1:6]:  # Check first few lines after title
                if not job_data["company"] and len(line) > 2 and len(line) < 60:
                    if not any(skip in line.lower() for skip in ['posted', 'ago', 'days', 'salary', '$']):
                        job_data["company"] = line
                        break
            
            # Get job URL with immediate tab closure
            job_url = await self._get_job_url_with_immediate_closure(
                page, job_element, job_number
            )
            
            if job_url:
                job_data["url"] = job_url
                job_data["ats_system"] = detect_ats_system(job_url)
                return job_data
            
            return {}
            
        except Exception as e:
            console.print(f"[red]Error extracting job URL {job_number}: {e}[/red]")
            return {}

    async def _get_job_url_with_immediate_closure(
        self, page, job_elem, job_number: int
    ) -> str:
        """
        Get job URL and immediately close any tabs that open.
        """
        try:
            # Find the job link
            link = await job_elem.query_selector("a")
            
            if not link:
                # Look in parent container
                parent = await job_elem.query_selector("..")
                if parent:
                    link = await parent.query_selector("a")
            
            if not link:
                return ""

            href = await link.get_attribute("href")
            if not href:
                return ""

            # If it's a direct external URL, use it
            if href.startswith("http") and "eluta.ca" not in href:
                console.print(f"[green]Direct URL for job {job_number}: {href[:50]}...[/green]")
                return href

            # If it's a relative URL, make it absolute
            if href.startswith("/") and not any(skip in href for skip in ["/search?", "q=", "pg="]):
                full_url = "https://www.eluta.ca" + href
                console.print(f"[cyan]Absolute URL for job {job_number}: {full_url[:50]}...[/cyan]")
                return full_url

            # If we need to click the link, do it with immediate tab management
            if href == "#!" or not href or href.startswith("#"):
                console.print(f"[cyan]Clicking link for job {job_number} (with immediate tab closure)...[/cyan]")
                
                context = page.context
                initial_pages = len(context.pages)
                
                try:
                    # Click the link
                    await link.click()
                    await asyncio.sleep(1)  # Brief wait for navigation
                    
                    # Check for new tabs and close them immediately after getting URL
                    current_pages = context.pages
                    if len(current_pages) > initial_pages:
                        # New tab opened
                        new_page = current_pages[-1]  # Last page is usually the new one
                        
                        try:
                            # Wait briefly for the page to load
                            await new_page.wait_for_load_state("domcontentloaded", timeout=5000)
                            final_url = new_page.url
                            
                            # Immediately close the new tab
                            await new_page.close()
                            self.stats["tabs_closed"] += 1
                            
                            console.print(f"[green]✅ Got URL and closed tab for job {job_number}: {final_url[:50]}...[/green]")
                            return final_url
                            
                        except Exception as tab_error:
                            console.print(f"[yellow]⚠️ Tab handling error for job {job_number}: {tab_error}[/yellow]")
                            # Try to close the tab anyway
                            try:
                                await new_page.close()
                                self.stats["tabs_closed"] += 1
                            except:
                                pass
                    
                    # If no new tab, check current page URL
                    current_url = page.url
                    if current_url and "eluta.ca" not in current_url:
                        return current_url
                        
                except Exception as click_error:
                    console.print(f"[yellow]⚠️ Click error for job {job_number}: {click_error}[/yellow]")
            
            return href if href.startswith("http") else ""
            
        except Exception as e:
            console.print(f"[red]Error getting URL for job {job_number}: {e}[/red]")
            return ""






# Test function
async def test_optimized_scraper():
    """Test the optimized scraper."""
    console.print("🧪 Testing Optimized Scraper")
    console.print("=" * 50)
    
    try:
        scraper = OptimizedElutaScraper(profile_name="Nirajan")
        jobs = await scraper.scrape_all_keywords_optimized(max_jobs_per_keyword=5)
        
        console.print(f"\n✅ Test completed! Found {len(jobs)} jobs")
        
    except Exception as e:
        console.print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_optimized_scraper())