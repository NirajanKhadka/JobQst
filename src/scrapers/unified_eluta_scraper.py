#!/usr/bin/env python3
"""
Unified Eluta Scraper
- Combines optimized, enhanced, and comprehensive Eluta scraping
- Async, parallel, AI-powered, and highly configurable
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from playwright.async_api import async_playwright

from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile
from src.ats.ats_utils import detect_ats_system
from src.core.job_filters import filter_entry_level_jobs, remove_duplicates
from src.utils.simple_url_filter import get_simple_url_filter

console = Console()


class UnifiedElutaScraper:
    """
    Unified Eluta Scraper
    - Scrapes Eluta job listings for each keyword in the user profile.
    - Manages browser contexts and tabs robustly, including popups.
    - Filters duplicates and non-entry-level jobs before saving.
    - Uses asyncio for parallel scraping with concurrency control.
    """
    def __init__(self, profile_name: str = "Nirajan", config: Optional[Dict] = None):
        """
        Initialize the UnifiedElutaScraper.
        Loads user profile, sets up configuration, and prepares job database.
        Raises ValueError if profile is not found.
        """
        self.profile_name = profile_name
        self.profile = load_profile(profile_name)
        if not self.profile:
            raise ValueError(f"Profile '{profile_name}' not found!")
        self.db = get_job_db(profile_name)
        self.keywords = self.profile.get("keywords", [])
        self.search_terms = list(self.keywords)
        self.url_filter = get_simple_url_filter()
        self.base_url = "https://www.eluta.ca/search"
        self.max_pages_per_keyword = config.get("pages", 5) if config else 5
        self.jobs_per_page = 10
        self.delay_between_requests = config.get("delay", 1) if config else 1
        self.max_concurrent_jobs = config.get("workers", 4) if config else 4
        self.max_jobs_per_keyword = config.get("jobs", 20) if config else 20
        self.headless = config.get("headless", True) if config else True
        self.stats = {
            "keywords_processed": 0,
            "pages_scraped": 0,
            "jobs_found": 0,
            "duplicates_skipped": 0,
            "tabs_closed": 0
        }

    async def scrape_all_keywords(self) -> List[Dict]:
        """
        Scrape job listings for all keywords in the user profile in parallel.
        Ensures all browser resources are cleaned up and no tab leaks occur.
        Returns a list of unique, filtered job dicts.
        """
        console.print("[bold green]UNIFIED ELUTA SCRAPING (NO AI) STARTED[/bold green]")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            try:
                tasks = []
                sem = asyncio.Semaphore(self.max_concurrent_jobs)
                for keyword in self.search_terms:
                    tasks.append(self._scrape_keyword(browser, keyword, sem))
                all_results = await asyncio.gather(*tasks)
                jobs = [job for sublist in all_results for job in sublist]
                jobs = remove_duplicates(jobs)
                jobs = filter_entry_level_jobs(jobs)
                self._save_jobs(jobs)
                console.print(f"[green]✅ Scraping complete. {len(jobs)} jobs saved.[/green]")
                return jobs
            finally:
                # Always close the browser to prevent resource leaks
                await browser.close()

    async def _scrape_keyword(self, browser, keyword: str, sem: asyncio.Semaphore) -> List[Dict]:
        """
        Scrape job listings for a single keyword.
        Opens a new browser context and page, attaches popup handler, and scrapes up to max_pages_per_keyword.
        Ensures all tabs (main and popups) are closed and stats are updated.
        Returns a list of job dicts for this keyword.
        """
        results = []
        async with sem:
            context = None
            page = None
            try:
                context = await browser.new_context(viewport={"width": 1920, "height": 1080})
                page = await context.new_page()

                # Auto-close any popup tabs opened by Eluta
                async def handle_popup(popup):
                    try:
                        await popup.close()
                        self.stats["tabs_closed"] += 1
                        console.print(f"[yellow]⚠️ Closed popup tab: {popup.url}[/yellow]")
                    except Exception as e:
                        console.print(f"[yellow]⚠️ Error closing popup tab: {e}[/yellow]")

                page.on("popup", handle_popup)

                for page_num in range(1, self.max_pages_per_keyword + 1):
                    search_url = f"{self.base_url}?q={keyword.replace(' ', '+')}+sort%3Arank&page={page_num}"
                    try:
                        await page.goto(search_url, wait_until="networkidle")
                    except Exception as e:
                        console.print(f"[yellow]⚠️ Error navigating to {search_url}: {e}[/yellow]")
                        continue
                    await asyncio.sleep(self.delay_between_requests)
                    try:
                        job_elements = await self._find_job_elements(page)
                    except Exception as e:
                        console.print(f"[yellow]⚠️ Error finding job elements: {e}[/yellow]")
                        continue
                    for job_element in job_elements[:self.max_jobs_per_keyword]:
                        job_url_data = await self._extract_job_url_fast(page, job_element, keyword)
                        if job_url_data and self.url_filter(job_url_data.get("url", "")):
                            results.append(job_url_data)
                return results
            except Exception as e:
                console.print(f"[red]❌ Exception in _scrape_keyword for '{keyword}': {e}[/red]")
                return results
            finally:
                # Ensure page and context are always closed, and increment tabs_closed stat
                if page is not None:
                    try:
                        await page.close()
                        self.stats["tabs_closed"] += 1
                    except Exception as e:
                        console.print(f"[yellow]⚠️ Error closing page: {e}[/yellow]")
                if context is not None:
                    try:
                        await context.close()
                    except Exception as e:
                        console.print(f"[yellow]⚠️ Error closing context: {e}[/yellow]")

    async def _find_job_elements(self, page):
        """
        Find all job result elements on the current Eluta search results page.
        Returns a list of element handles.
        """
        # Implementation depends on Eluta's DOM structure
        return await page.query_selector_all(".result")

    async def _extract_job_url_fast(self, page, job_element, keyword):
        """
        Extract job URL and basic info from a job element.
        Returns a dict with job details, or None if extraction fails.
        """
        try:
            title = await job_element.query_selector_eval(".title", "el => el.innerText")
            company = await job_element.query_selector_eval(".company", "el => el.innerText")
            location = await job_element.query_selector_eval(".location", "el => el.innerText")
            url = await job_element.query_selector_eval("a", "el => el.href")
            return {
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "search_keyword": keyword,
                "scraped_date": datetime.now().isoformat()
            }
        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting job info: {e}[/yellow]")
            return None



    def _save_jobs(self, jobs: List[Dict]):
        """
        Save a list of job dicts to the job database.
        """
        for job in jobs:
            self.db.add_job(job)

# CLI entrypoint
async def run_unified_eluta_scraper(profile_name: str, config: Optional[Dict] = None):
    """
    Entrypoint for running the UnifiedElutaScraper asynchronously.
    """
    scraper = UnifiedElutaScraper(profile_name, config)
    return await scraper.scrape_all_keywords()
