#!/usr/bin/env python3
"""
Comprehensive TowardsAI Scraper
Scrapes job listings from https://jobs.towardsai.net with reliable error handling and timeout management.
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile
from src.ats.ats_utils import detect_ats_system
from src.core.job_filters import filter_entry_level_jobs, remove_duplicates

console = Console()


class ComprehensiveTowardsAIScraper:
    """
    Comprehensive TowardsAI scraper with reliable error handling and timeout management.
    """

    def __init__(self, profile_name: str = "Nirajan"):
        """Initialize the comprehensive TowardsAI scraper."""
        self.profile_name = profile_name
        self.profile = load_profile(profile_name)
        if not self.profile:
            raise ValueError(f"Profile '{profile_name}' not found!")
        self.db = get_job_db(profile_name)

        # Get keywords from profile
        self.keywords = self.profile.get("keywords", [])
        self.search_terms = list(self.keywords)
        console.print(f"[cyan]Loaded {len(self.search_terms)} keywords from profile[/cyan]")

        # TowardsAI specific settings
        self.base_url = "https://jobs.towardsai.net"
        self.search_url = f"{self.base_url}/search"
        self.delay_between_requests = 2  # seconds
        
        # Timeout settings (in milliseconds)
        self.page_timeout = 30000  # 30 seconds
        self.element_timeout = 10000  # 10 seconds
        self.click_timeout = 5000   # 5 seconds
        
        # Results tracking
        self.all_jobs = []
        self.processed_urls = set()
        self.stats = {
            "keywords_processed": 0,
            "jobs_found": 0,
            "jobs_filtered_out": 0,
            "entry_level_jobs": 0,
            "duplicates_skipped": 0,
            "timeouts": 0,
            "errors": 0,
        }

    async def scrape_all_keywords(self, max_jobs_per_keyword: int = 20) -> List[Dict]:
        """
        Scrape jobs for ALL keywords from TowardsAI.

        Args:
            max_jobs_per_keyword: Maximum jobs to scrape per keyword

        Returns:
            List of filtered job dictionaries
        """
        console.print(Panel.fit("COMPREHENSIVE TOWARDSAI SCRAPING", style="bold blue"))
        console.print(f"[cyan]Target site: {self.base_url}[/cyan]")
        console.print(f"[cyan]{len(self.search_terms)} search terms[/cyan]")
        console.print(f"[cyan]Max {max_jobs_per_keyword} jobs per keyword[/cyan]")

        # Display all search terms
        console.print(f"\n[bold]Search Terms:[/bold]")
        for i, term in enumerate(self.search_terms, 1):
            console.print(f"  {i:2d}. {term}")

        if not input(f"\nPress Enter to start TowardsAI scraping ({len(self.search_terms)} keywords) or Ctrl+C to cancel..."):
            pass

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                with Progress() as progress:
                    main_task = progress.add_task(
                        "[green]Scraping keywords...", total=len(self.search_terms)
                    )

                    for keyword in self.search_terms:
                        console.print(f"\n[bold]Processing: {keyword}[/bold]")
                        keyword_jobs = await self._scrape_keyword(
                            page, keyword, max_jobs_per_keyword, progress
                        )
                        
                        # Filter for entry-level positions
                        filtered_jobs = filter_entry_level_jobs(keyword_jobs)
                        self.all_jobs.extend(filtered_jobs)
                        self.stats["keywords_processed"] += 1
                        progress.update(main_task, advance=1)
                        
                        # Clean up any extra tabs
                        await self._cleanup_extra_tabs(context)
                        await asyncio.sleep(self.delay_between_requests)

                # Remove duplicates
                unique_jobs = remove_duplicates(self.all_jobs)
                self._display_comprehensive_results(unique_jobs)
                return unique_jobs

            finally:
                await self._cleanup_extra_tabs(context)
                await context.close()
                await browser.close()

    async def _scrape_keyword(
        self, page, keyword: str, max_jobs: int, progress: Progress
    ) -> List[Dict]:
        """Scrape jobs for a specific keyword from TowardsAI."""
        keyword_jobs = []

        try:
            # Navigate to TowardsAI homepage first
            console.print(f"[cyan]Navigating to TowardsAI for '{keyword}'[/cyan]")
            
            try:
                await page.goto(self.base_url, wait_until="networkidle", timeout=self.page_timeout)
                await asyncio.sleep(2)
            except PlaywrightTimeoutError:
                console.print(f"[red]⏰ Page load timeout for TowardsAI homepage[/red]")
                self.stats["timeouts"] += 1
                return keyword_jobs
            except Exception as e:
                console.print(f"[red]❌ Navigation error: {e}[/red]")
                self.stats["errors"] += 1
                return keyword_jobs

            # Look for search functionality or job listings
            await self._search_for_keyword(page, keyword)
            
            # Find job elements
            job_elements = await self._find_job_elements_reliable(page)
            
            if not job_elements:
                console.print(f"[yellow]No job elements found for '{keyword}'[/yellow]")
                return keyword_jobs

            console.print(f"[green]Found {len(job_elements)} job elements for '{keyword}'[/green]")

            # Process each job element
            for job_number, job_element in enumerate(job_elements[:max_jobs], 1):
                try:
                    job_data = await self._extract_job_data_reliable(
                        page, job_element, job_number, keyword
                    )

                    if job_data and job_data.get("title"):
                        # Skip if already processed
                        job_url = job_data.get("url", "")
                        if job_url in self.processed_urls:
                            self.stats["duplicates_skipped"] += 1
                            continue

                        self.processed_urls.add(job_url)
                        keyword_jobs.append(job_data)
                        self.stats["jobs_found"] += 1

                        console.print(
                            f"[green]✅ Found: {job_data['title'][:50]}... at {job_data.get('company', 'Unknown')[:30]}[/green]"
                        )

                except Exception as e:
                    console.print(f"[red]Error processing job {job_number}: {e}[/red]")
                    self.stats["errors"] += 1
                    continue

        except Exception as e:
            console.print(f"[red]Error scraping keyword '{keyword}': {e}[/red]")
            self.stats["errors"] += 1

        return keyword_jobs

    async def _search_for_keyword(self, page, keyword: str):
        """Search for a specific keyword on TowardsAI."""
        try:
            # Look for search input field
            search_selectors = [
                "input[type='search']",
                "input[placeholder*='search']",
                "input[placeholder*='Search']",
                ".search-input",
                "#search",
                "[data-testid='search']"
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.query_selector(selector)
                    if search_input:
                        console.print(f"[cyan]Found search input with selector: {selector}[/cyan]")
                        break
                except:
                    continue
            
            if search_input:
                # Clear and type the keyword
                await search_input.clear()
                await search_input.type(keyword)
                
                # Look for search button or press Enter
                search_button = await page.query_selector("button[type='submit'], .search-button, [data-testid='search-button']")
                if search_button:
                    await search_button.click()
                else:
                    await search_input.press("Enter")
                
                # Wait for search results
                await page.wait_for_load_state("networkidle", timeout=self.page_timeout)
                await asyncio.sleep(2)
                console.print(f"[green]Searched for '{keyword}'[/green]")
            else:
                console.print(f"[yellow]No search functionality found, browsing all jobs[/yellow]")
                
        except Exception as e:
            console.print(f"[yellow]Search failed for '{keyword}': {e}[/yellow]")

    async def _find_job_elements_reliable(self, page) -> List:
        """Find job elements using multiple selectors with fallbacks."""
        job_elements = []
        
        # Try different selectors for TowardsAI job listings
        selectors_to_try = [
            ".job-card",
            ".job-item",
            ".job-listing",
            "[data-testid='job-card']",
            ".job",
            "article",
            ".card",
            "a[href*='/job/']",
            "a[href*='job']"
        ]
        
        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    console.print(f"[green]Found {len(elements)} elements with selector: {selector}[/green]")
                    return elements
            except Exception as e:
                console.print(f"[dim]Selector {selector} failed: {e}[/dim]")
                continue
        
        # Fallback: Look for any links that might be job links
        console.print("[yellow]No job containers found, trying job links...[/yellow]")
        try:
            job_links = await page.query_selector_all("a[href*='job']")
            actual_job_elements = []
            
            for link in job_links:
                try:
                    href = await link.get_attribute("href")
                    if href and ("/job/" in href or "job" in href):
                        actual_job_elements.append(link)
                except:
                    continue
                    
            return actual_job_elements
            
        except Exception as e:
            console.print(f"[red]Fallback selector failed: {e}[/red]")
            return []

    async def _extract_job_data_reliable(
        self, page, job_element, job_number: int, keyword: str
    ) -> Dict:
        """Extract job data from a job element with reliable error handling."""
        try:
            job_data = {
                "title": "",
                "company": "",
                "location": "",
                "salary": "",
                "description": "",
                "url": "",
                "apply_url": "",
                "source": "towardsai.net",
                "scraped_date": datetime.now().isoformat(),
                "ats_system": "Unknown",
                "scraped_successfully": False,
                "posted_date": "",
                "experience_level": "Unknown",
                "search_keyword": keyword,
            }

            # Extract job URL first
            job_url = await self._extract_job_url_reliable(job_element, page, job_number)
            if not job_url:
                return {}
            
            job_data["url"] = job_url
            job_data["apply_url"] = job_url
            job_data["ats_system"] = detect_ats_system(job_url)

            # Extract job title
            title_selectors = [
                "h1", "h2", "h3", ".title", ".job-title", 
                "[data-testid='job-title']", ".card-title"
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = await job_element.query_selector(selector)
                    if title_elem:
                        title = await title_elem.inner_text()
                        if title and len(title.strip()) > 5:
                            job_data["title"] = title.strip()
                            break
                except:
                    continue

            # If no title found in element, try to get it from the link text
            if not job_data["title"]:
                try:
                    link_text = await job_element.inner_text()
                    if link_text and len(link_text.strip()) > 5:
                        job_data["title"] = link_text.strip()
                except:
                    job_data["title"] = f"Job from {keyword} search"

            # Extract company
            company_selectors = [
                ".company", ".employer", ".org", ".company-name",
                "[data-testid='company']", ".card-subtitle"
            ]
            
            for selector in company_selectors:
                try:
                    company_elem = await job_element.query_selector(selector)
                    if company_elem:
                        company = await company_elem.inner_text()
                        if company:
                            job_data["company"] = company.strip()
                            break
                except:
                    continue

            # Extract location
            location_selectors = [
                ".location", ".loc", ".where", ".job-location",
                "[data-testid='location']"
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = await job_element.query_selector(selector)
                    if location_elem:
                        location = await location_elem.inner_text()
                        if location:
                            job_data["location"] = location.strip()
                            break
                except:
                    continue

            # Extract description/summary
            try:
                all_text = await job_element.inner_text()
                if all_text:
                    # Clean up the text and use as description
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    # Skip title and company lines, use the rest as description
                    description_lines = []
                    for line in lines:
                        if (line != job_data["title"] and 
                            line != job_data["company"] and 
                            line != job_data["location"] and
                            len(line) > 10):
                            description_lines.append(line)
                    
                    if description_lines:
                        job_data["description"] = " ".join(description_lines[:3])  # First 3 lines
            except:
                pass

            # Set defaults for missing data
            if not job_data["company"]:
                job_data["company"] = "TowardsAI Company"
            if not job_data["location"]:
                job_data["location"] = "Remote/Global"
            if not job_data["description"]:
                job_data["description"] = f"AI/ML job found via keyword: {keyword}"

            job_data["scraped_successfully"] = True
            return job_data

        except Exception as e:
            console.print(f"[red]Error extracting job data for job {job_number}: {e}[/red]")
            return {}

    async def _extract_job_url_reliable(self, job_element, page, job_number: int) -> str:
        """Extract job URL with reliable timeout handling."""
        try:
            # If the element itself is a link
            if await job_element.get_attribute("href"):
                href = await job_element.get_attribute("href")
                return self._normalize_url(href)
            
            # Look for link within the element
            link = await job_element.query_selector("a")
            if link:
                href = await link.get_attribute("href")
                if href:
                    return self._normalize_url(href)
            
            # Look in parent containers
            current_element = job_element
            for level in range(3):
                try:
                    parent = await current_element.query_selector("..")
                    if not parent:
                        break
                        
                    link = await parent.query_selector("a")
                    if link:
                        href = await link.get_attribute("href")
                        if href:
                            return self._normalize_url(href)
                            
                    current_element = parent
                except:
                    break
            
            console.print(f"[yellow]Job {job_number}: No URL found[/yellow]")
            return ""

        except Exception as e:
            console.print(f"[red]Error extracting URL for job {job_number}: {e}[/red]")
            return ""

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to full format."""
        if not url:
            return ""
        
        if url.startswith("http"):
            return url
        elif url.startswith("/"):
            return self.base_url + url
        else:
            return self.base_url + "/" + url

    async def _cleanup_extra_tabs(self, context) -> None:
        """Clean up any extra tabs that might have been opened."""
        try:
            pages = context.pages
            if len(pages) > 1:
                for page in pages[1:]:  # Keep only the first page
                    if not page.is_closed():
                        await page.close()
                        console.print(f"[dim]Cleaned up extra tab[/dim]")
        except Exception as e:
            console.print(f"[dim]Tab cleanup warning: {e}[/dim]")

    def _display_comprehensive_results(self, jobs: List[Dict]) -> None:
        """Display comprehensive scraping results."""
        console.print("\n" + "=" * 80)
        console.print(Panel.fit("TOWARDSAI SCRAPING RESULTS", style="bold green"))

        # Statistics table
        stats_table = Table(title="Scraping Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="green")

        stats_table.add_row("Keywords Processed", str(self.stats["keywords_processed"]))
        stats_table.add_row("Total Jobs Found", str(self.stats["jobs_found"]))
        stats_table.add_row("Entry-Level Jobs", str(self.stats["entry_level_jobs"]))
        stats_table.add_row("Jobs Filtered Out", str(self.stats["jobs_filtered_out"]))
        stats_table.add_row("Duplicates Skipped", str(self.stats["duplicates_skipped"]))
        stats_table.add_row("Timeouts Handled", str(self.stats["timeouts"]))
        stats_table.add_row("Errors Handled", str(self.stats["errors"]))
        stats_table.add_row("Final Unique Jobs", str(len(jobs)))

        console.print(stats_table)

        # Sample jobs table
        if jobs:
            console.print(f"\n[bold]Sample Jobs Found:[/bold]")
            sample_table = Table()
            sample_table.add_column("Title", style="green", max_width=40)
            sample_table.add_column("Company", style="cyan", max_width=25)
            sample_table.add_column("Location", style="yellow", max_width=20)
            sample_table.add_column("URL", style="blue", max_width=30)

            for job in jobs[:10]:  # Show first 10 jobs
                sample_table.add_row(
                    job.get("title", "Unknown")[:40],
                    job.get("company", "Unknown")[:25],
                    job.get("location", "Unknown")[:20],
                    job.get("url", "")[:30] + "..." if len(job.get("url", "")) > 30 else job.get("url", "")
                )

            console.print(sample_table)

        # Save to database
        if jobs:
            console.print(f"\n[bold]💾 Saving {len(jobs)} jobs to database...[/bold]")
            saved_count = 0
            for job in jobs:
                try:
                    if self.db.add_job(job):
                        saved_count += 1
                except Exception as e:
                    console.print(f"[red]Error saving job: {e}[/red]")
            
            console.print(f"[green]✅ {saved_count}/{len(jobs)} jobs saved to database![/green]")


async # Main function removed - use scraper class directly

