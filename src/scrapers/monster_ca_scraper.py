#!/usr/bin/env python3
"""
Monster Canada Comprehensive Scraper

Scrapes job listings from Monster Canada following the same architecture
and standards as the Eluta scraper. Supports comprehensive keyword searching,
entry-level filtering, and parallel processing capabilities.

Monster CA URL Structure:
- Search: https://www.monster.ca/jobs/q-{keyword}-jobs?where={location}&so=p.h.p
- Example: https://www.monster.ca/jobs/q-python-jobs?where=Toronto,ON&so=p.h.p
- Jobs format: https://www.monster.ca/jobs/q-{keyword}-jobs-l-{location}?so=p.h.p
"""

import asyncio
import time
import json
import urllib.parse
import random
from datetime import datetime, timedelta
from typing import Dict, List, Set
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile
from src.ats.ats_utils import detect_ats_system
from src.core.job_filters import filter_entry_level_jobs, remove_duplicates

console = Console()


class MonsterCAScraper:
    """
    Comprehensive Monster Canada scraper following the same architecture as Eluta.
    Searches across all Canadian provinces with keyword-based job discovery.
    """

    def __init__(self, profile_name: str = "Nirajan"):
        """Initialize the Monster CA scraper."""
        self.profile_name = profile_name
        self.profile = load_profile(profile_name)
        self.db = get_job_db(profile_name)

        # Get ALL keywords and skills from profile
        self.keywords = self.profile.get("keywords", [])
        self.skills = self.profile.get("skills", [])

        # Combine and deduplicate keywords
        all_terms = set(self.keywords + self.skills)
        self.search_terms = list(all_terms)

        console.print(f"[cyan]Loaded {len(self.search_terms)} unique search terms[/cyan]")

        # Monster CA specific locations (major Canadian cities)
        self.locations = [
            "",  # All Canada (empty location)
            "Toronto,ON", 
            "Vancouver,BC", 
            "Montreal,QC", 
            "Calgary,AB", 
            "Edmonton,AB", 
            "Ottawa,ON", 
            "Winnipeg,MB", 
            "Quebec City,QC", 
            "Hamilton,ON", 
            "Kitchener,ON",
            "London,ON",
            "Halifax,NS",
            "Victoria,BC",
            "Saskatoon,SK",
            "Regina,SK"
        ]

        # Experience level filters for 0-2 years (same as Eluta)
        self.entry_level_keywords = [
            "junior", "entry", "entry level", "entry-level", "associate", 
            "graduate", "new grad", "recent graduate", "trainee", "coordinator",
            "0-2 years", "1-2 years", "0-1 years", "level i", "level 1",
            "intern", "internship", "co-op", "coop"
        ]

        # Keywords to avoid (too senior)
        self.avoid_keywords = [
            "senior", "sr.", "sr ", "lead", "principal", "manager", "director",
            "supervisor", "head of", "chief", "vp", "vice president", 
            "3+ years", "4+ years", "5+ years", "10+ years", "experienced",
            "expert", "specialist ii", "level ii", "level 2", "staff"
        ]

        # Monster CA specific settings
        self.base_url = "https://www.monster.ca/jobs"
        self.max_pages_per_search = 3  # Pages per keyword-location combination
        self.jobs_per_page = 25  # Monster typically shows 25 jobs per page
        self.delay_between_requests = 2  # Slower to avoid bot detection

        # Results tracking
        self.all_jobs = []
        self.processed_urls = set()
        self.stats = {
            "searches_processed": 0,
            "pages_scraped": 0, 
            "jobs_found": 0,
            "jobs_filtered_out": 0,
            "entry_level_jobs": 0,
            "duplicates_skipped": 0,
        }

    async def scrape_all_keywords(self, max_jobs_per_keyword: int = 30) -> List[Dict]:
        """
        Scrape jobs for ALL keywords across Canadian locations with entry-level filter.

        Args:
            max_jobs_per_keyword: Maximum jobs to scrape per keyword

        Returns:
            List of filtered job dictionaries
        """
        console.print(Panel.fit("COMPREHENSIVE MONSTER CA SCRAPING", style="bold blue"))
        console.print(f"[cyan]Searching across Canada[/cyan]")
        console.print(f"[cyan]Entry-level positions (0-2 years)[/cyan]")
        console.print(f"[cyan]{len(self.search_terms)} search terms[/cyan]")
        console.print(f"[cyan]{len(self.locations)} locations[/cyan]")
        console.print(f"[cyan]{self.max_pages_per_search} pages per search[/cyan]")
        
        total_searches = len(self.search_terms) * len(self.locations)
        console.print(f"[cyan]Expected: {total_searches} total searches[/cyan]")

        # Display search terms
        console.print(f"\n[bold]Search Terms:[/bold]")
        for i, term in enumerate(self.search_terms, 1):
            console.print(f"  {i:2d}. {term}")

        # Display locations
        console.print(f"\n[bold]Locations:[/bold]")
        for i, location in enumerate(self.locations, 1):
            display_loc = location if location else "All Canada"
            console.print(f"  {i:2d}. {display_loc}")

        if not input(f"\nPress Enter to start comprehensive scraping ({total_searches} total searches) or Ctrl+C to cancel..."):
            pass

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()

            # Apply stealth measures to make it look like a real user
            stealth = Stealth()
            await stealth.apply_stealth_async(page)

            # Warm-up phase to build a more human-like browser profile
            console.print("[yellow]Warming up browser to appear more human...[/yellow]")
            try:
                await page.goto("https://www.google.com", timeout=15000)
                await asyncio.sleep(random.uniform(1, 3))
                await page.goto("https://www.reddit.com", timeout=15000)
                await asyncio.sleep(random.uniform(1, 3))
                console.print("[green]Warm-up complete. Starting Monster.ca scraping.[/green]")
            except Exception as e:
                console.print(f"[yellow]Warm-up navigation failed, continuing anyway: {e}[/yellow]")


            try:
                with Progress() as progress:
                    main_task = progress.add_task(
                        "[green]Scraping Monster CA...", total=len(self.search_terms)
                    )

                    for keyword in self.search_terms:
                        console.print(f"\n[bold]Processing keyword: {keyword}[/bold]")
                        keyword_jobs = await self._scrape_keyword_all_locations(
                            page, keyword, max_jobs_per_keyword, progress
                        )
                        
                        # Filter for entry-level positions
                        filtered_jobs = filter_entry_level_jobs(keyword_jobs)
                        self.all_jobs.extend(filtered_jobs)
                        progress.update(main_task, advance=1)
                        
                        # Delay between keywords to avoid rate limiting
                        await asyncio.sleep(self.delay_between_requests)

                # Remove duplicates
                unique_jobs = remove_duplicates(self.all_jobs)
                self._display_comprehensive_results(unique_jobs)
                return unique_jobs

            finally:
                input("Press Enter to close browser...")
                await context.close()
                await browser.close()

    async def _scrape_keyword_all_locations(
        self, page, keyword: str, max_jobs: int, progress: Progress
    ) -> List[Dict]:
        """Scrape a keyword across all Canadian locations."""
        keyword_jobs = []
        
        for location in self.locations:
            if len(keyword_jobs) >= max_jobs:
                break
                
            location_jobs = await self._scrape_keyword_location(
                page, keyword, location, max_jobs // len(self.locations)
            )
            keyword_jobs.extend(location_jobs)
            self.stats["searches_processed"] += 1
            
            # Brief delay between locations
            await asyncio.sleep(1)
        
        console.print(f"[green]Keyword '{keyword}' complete: {len(keyword_jobs)} jobs across all locations[/green]")
        return keyword_jobs

    async def _scrape_keyword_location(
        self, page, keyword: str, location: str, max_jobs: int
    ) -> List[Dict]:
        """Scrape jobs for a specific keyword and location."""
        location_jobs = []
        jobs_collected = 0

        display_location = location if location else "All Canada"
        console.print(f"[cyan]  Location: {display_location}[/cyan]")

        for page_num in range(1, self.max_pages_per_search + 1):
            if jobs_collected >= max_jobs:
                break

            # Build Monster CA search URL
            search_url = self._build_search_url(keyword, location, page_num)
            
            try:
                console.print(f"[cyan]    Page {page_num}: {search_url}[/cyan]")
                await page.goto(search_url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(3)  # Wait for dynamic content to load

                # Updated selectors based on the HTML structure observed in Monster.ca
                job_elements = await page.query_selector_all("[data-testid='JobCard']")
                
                # Try backup selectors if main ones don't work
                if not job_elements:
                    job_elements = await page.query_selector_all("article.indexmodern__JobCardComponent-sc-9vl52l-0")
                
                # More specific Monster.ca selectors
                if not job_elements:
                    job_elements = await page.query_selector_all(".job-search-results-style__JobCardWrap-sc-30547e5b-4")
                
                # Last resort: look for any element containing job information
                if not job_elements:
                    job_elements = await page.query_selector_all("article[data-testid], div[data-job-id], .job-card")

                if not job_elements:
                    console.print(f"[yellow]    No jobs found on page {page_num} for '{keyword}' in {display_location}[/yellow]")
                    break

                console.print(f"[green]    Found {len(job_elements)} jobs on page {page_num}[/green]")

                # Process jobs on current page
                jobs_on_page = 0
                for i, job_element in enumerate(job_elements):
                    if jobs_collected >= max_jobs:
                        break

                    try:
                        job_data = await self._extract_monster_job_data(
                            page, job_element, i + 1, page_num, keyword, location
                        )
                        if job_data:
                            location_jobs.append(job_data)
                            self.stats["jobs_found"] += 1
                            jobs_collected += 1
                            jobs_on_page += 1

                    except Exception as e:
                        console.print(f"[red]    Error processing job {i+1}: {e}[/red]")
                        continue

                self.stats["pages_scraped"] += 1
                console.print(f"[cyan]    Page {page_num}: Collected {jobs_on_page} jobs (Total: {jobs_collected})[/cyan]")

                # Clean up extra tabs
                await self._cleanup_extra_tabs(page.context)
                await asyncio.sleep(self.delay_between_requests)

            except Exception as e:
                console.print(f"[red]    Error scraping page {page_num}: {e}[/red]")
                break

        return location_jobs

    def _build_search_url(self, keyword: str, location: str, page: int = 1) -> str:
        """Build Monster CA search URL."""
        # URL encode the keyword and location
        encoded_keyword = urllib.parse.quote_plus(keyword)
        encoded_location = urllib.parse.quote_plus(location) if location else ""
        
        if location:
            # Format: /jobs/q-{keyword}-jobs-l-{location}?so=p.h.p&page={page}
            # Replace spaces and special characters in location
            clean_location = location.replace(",", "-").replace(" ", "-").lower()
            url = f"{self.base_url}/q-{encoded_keyword}-jobs-l-{clean_location}"
        else:
            # All Canada search: /jobs/q-{keyword}-jobs?so=p.h.p&page={page}
            url = f"{self.base_url}/q-{encoded_keyword}-jobs"
        
        # Add sorting and pagination parameters
        params = ["so=p.h.p"]  # Sort by most relevant/recent
        if page > 1:
            params.append(f"page={page}")
        
        url += "?" + "&".join(params)
        return url

    async def _extract_monster_job_data(
        self, page, job_element, job_index: int, page_num: int, keyword: str, location: str
    ) -> Dict:
        """
        Extract job data from a Monster CA job element.
        Updated selectors based on actual Monster.ca HTML structure.
        """
        try:
            # Skip extraction and navigate to job detail page
            job_link = None
            job_title = "Unknown Title"
            company = "Unknown Company"
            
            # Try to get job link from various possible selectors based on actual HTML
            link_selectors = [
                "[data-testid='jobTitle']",  # Most specific
                "a[href*='job-openings']",   # Direct job links
                ".indexmodern__Title-sc-9vl52l-21",  # Monster's title class
                "h3 a",                      # Title in h3
                ".title-link",               # Generic title link
                ".job-title a"               # Fallback
            ]
            
            for selector in link_selectors:
                try:
                    link_element = await job_element.query_selector(selector)
                    if link_element:
                        job_link = await link_element.get_attribute("href")
                        job_title = await link_element.inner_text()
                        break
                except:
                    continue
                    
            # Get company name
            company_selectors = [
                "[data-testid='company']",
                ".company-name",
                ".indexmodern__Company-sc-9vl52l-22"
            ]
            
            for selector in company_selectors:
                try:
                    company_element = await job_element.query_selector(selector)
                    if company_element:
                        company = await company_element.inner_text()
                        break
                except:
                    continue
            
            # Handle relative URLs
            if job_link and job_link.startswith("//"):
                job_link = "https:" + job_link
            elif job_link and job_link.startswith("/"):
                job_link = "https://www.monster.ca" + job_link
                
            console.print(f"[green]      Job {job_index}: {job_title} at {company}[/green]")
            
            if not job_link:
                console.print(f"[yellow]      No job link found for job {job_index}[/yellow]")
                return None
                
            # Navigate to job detail page in new tab
            detail_page = await page.context.new_page()
            
            try:
                await detail_page.goto(job_link, timeout=15000)
                await detail_page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)
                
                # Extract detailed job information
                job_data = await self._extract_job_details_from_page(detail_page, job_link, keyword, location)
                job_data.update({
                    "title": job_title,
                    "company": company,
                    "source": "Monster CA",
                    "site": "monster",  # Match Eluta's naming convention
                    "search_keyword": keyword,
                    "search_location": location,
                    "scraped_at": datetime.now().isoformat(),
                    "status": "scraped",  # Match the job processing pipeline
                    "applied": 0,  # Default not applied
                    "application_status": "not_applied"  # Match database schema
                })
                
                return job_data
                
            finally:
                await detail_page.close()
                
        except Exception as e:
            console.print(f"[red]      Error extracting job {job_index}: {e}[/red]")
            return None

    async def _extract_job_details_from_page(self, page, job_url: str, keyword: str, location: str) -> Dict:
        """Extract detailed job information from Monster CA job detail page."""
        try:
            # Basic job information - match Eluta's structure exactly
            job_data = {
                "url": job_url,
                "title": "Unknown Title",
                "company": "Unknown Company", 
                "location": "Unknown Location",
                "summary": "",  # Monster calls it description, but map to summary for consistency
                "job_description": "",  # Full description
                "requirements": "",
                "salary": "",
                "salary_range": "",  # Alternative field name
                "job_type": "",
                "posted_date": "",
                "benefits": "",
                "apply_url": job_url,
                "ats_system": "Monster",
                "search_keyword": keyword,
                "search_location": location,
                "scraped_at": datetime.now().isoformat(),
                "site": "monster",  # Consistent with Eluta
                "source": "Monster CA",  # Human readable source
                "status": "scraped",  # Ready for processing
                "applied": 0,
                "application_status": "not_applied",
                "experience_level": "",  # Will be determined by filters
                "remote_option": "",
                "match_score": 0.0,
                "raw_data": ""  # Store original HTML if needed
            }
            
            # Extract title - try multiple selectors
            title_selectors = [
                "h1",
                ".job-title",
                "[data-testid='jobTitle']",
                ".page-title",
                ".job-view-title"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = await page.query_selector(selector)
                    if title_element:
                        title_text = await title_element.inner_text()
                        if title_text and title_text.strip():
                            job_data["title"] = title_text.strip()
                            break
                except:
                    continue
                    
            # Extract company name
            company_selectors = [
                "[data-testid='company']",
                ".company-name", 
                ".employer-name",
                ".company",
                "h2"
            ]
            
            for selector in company_selectors:
                try:
                    company_element = await page.query_selector(selector)
                    if company_element:
                        company_text = await company_element.inner_text()
                        if company_text and company_text.strip():
                            job_data["company"] = company_text.strip()
                            break
                except:
                    continue
                    
            # Extract location
            location_selectors = [
                "[data-testid='jobDetailLocation']",
                ".location",
                ".job-location",
                ".address"
            ]
            
            for selector in location_selectors:
                try:
                    location_element = await page.query_selector(selector)
                    if location_element:
                        location_text = await location_element.inner_text()
                        if location_text and location_text.strip():
                            job_data["location"] = location_text.strip()
                            break
                except:
                    continue
            
            # Extract job description - try to get the main content
            description_selectors = [
                ".job-description",
                ".description",
                ".content",
                ".job-details",
                "[data-testid='jobDescription']",
                ".job-summary"
            ]
            
            description_text = ""
            for selector in description_selectors:
                try:
                    desc_element = await page.query_selector(selector)
                    if desc_element:
                        description_text = await desc_element.inner_text()
                        if description_text and len(description_text) > 100:
                            break
                except:
                    continue
                    
            if description_text:
                job_data["job_description"] = description_text.strip()
                # Create a summary from first 500 characters for compatibility
                job_data["summary"] = description_text.strip()[:500] + "..." if len(description_text) > 500 else description_text.strip()
                
            # Extract salary information
            salary_selectors = [
                ".salary",
                ".compensation", 
                ".pay",
                "[data-testid='salary']"
            ]
            
            for selector in salary_selectors:
                try:
                    salary_element = await page.query_selector(selector)
                    if salary_element:
                        salary_text = await salary_element.inner_text()
                        if salary_text and salary_text.strip():
                            job_data["salary"] = salary_text.strip()
                            job_data["salary_range"] = salary_text.strip()  # Use both fields
                            break
                except:
                    continue
                    
            # Extract job type (full-time, part-time, etc.)
            job_type_selectors = [
                ".job-type",
                ".employment-type",
                "[data-testid='jobType']"
            ]
            
            for selector in job_type_selectors:
                try:
                    type_element = await page.query_selector(selector)
                    if type_element:
                        type_text = await type_element.inner_text()
                        if type_text and type_text.strip():
                            job_data["job_type"] = type_text.strip()
                            break
                except:
                    continue
                    
            # Try to find apply button/link
            apply_selectors = [
                "button:has-text('Apply')",
                "a:has-text('Apply')",
                ".apply-button",
                "[data-testid='apply']"
            ]
            
            for selector in apply_selectors:
                try:
                    apply_element = await page.query_selector(selector)
                    if apply_element:
                        apply_url = await apply_element.get_attribute("href")
                        if apply_url:
                            if apply_url.startswith("//"):
                                apply_url = "https:" + apply_url
                            elif apply_url.startswith("/"):
                                apply_url = "https://www.monster.ca" + apply_url
                            job_data["apply_url"] = apply_url
                            break
                except:
                    continue
                    
            return job_data
            
        except Exception as e:
            console.print(f"[red]Error extracting job details: {e}[/red]")
            return job_data

    async def _cleanup_extra_tabs(self, context):
        """Close extra tabs to prevent browser overload."""
        try:
            pages = context.pages
            if len(pages) > 3:  # Keep main tab + 2 working tabs
                for page in pages[3:]:
                    await page.close()
        except Exception as e:
            console.print(f"[yellow]Tab cleanup warning: {e}[/yellow]")

    def _display_comprehensive_results(self, jobs: List[Dict]):
        """Display comprehensive scraping results with statistics."""
        console.print(Panel.fit("MONSTER CA SCRAPING RESULTS", style="bold green"))
        
        # Create results table
        table = Table(title="Scraping Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Total Searches", str(self.stats["searches_processed"]))
        table.add_row("Pages Scraped", str(self.stats["pages_scraped"]))
        table.add_row("Jobs Found", str(self.stats["jobs_found"]))
        table.add_row("Entry-Level Jobs", str(len(jobs)))
        table.add_row("Unique Jobs", str(len(jobs)))
        
        console.print(table)
        
        if jobs:
            # Show sample jobs
            console.print(f"\n[bold]Sample Jobs Found:[/bold]")
            for i, job in enumerate(jobs[:5], 1):
                console.print(f"{i:2d}. {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')} - {job.get('location', 'Unknown')}")
                
            # Save to database
            saved_count = 0
            for job in jobs:
                try:
                    self.db.add_job(job)
                    saved_count += 1
                except Exception as e:
                    console.print(f"[red]Error saving job: {e}[/red]")
                    
            console.print(f"\n[green]Successfully saved {saved_count} jobs to database![/green]")
        else:
            console.print("[yellow]No entry-level jobs found.[/yellow]")


# Main execution function
async def main():
    """Main function to run Monster CA scraper with interactive options."""
    console.print(Panel.fit(
        "🇨🇦 MONSTER CA JOB SCRAPER\n"
        "Canadian job opportunities from Monster.ca",
        style="bold blue"
    ))
    
    # Interactive configuration
    from rich.prompt import Prompt, Confirm
    
    profile_name = Prompt.ask("Profile name", default="Nirajan")
    max_jobs_per_keyword = int(Prompt.ask("Max jobs per keyword", default="20"))
    
    # Initialize scraper
    scraper = MonsterCAScraper(profile_name)
    
    # Display search preview
    console.print(f"\n[cyan]Profile: {profile_name}[/cyan]")
    console.print(f"[cyan]Search terms: {len(scraper.search_terms)}[/cyan]")
    console.print(f"[cyan]Locations: {len(scraper.locations)}[/cyan]")
    console.print(f"[cyan]Max jobs per keyword: {max_jobs_per_keyword}[/cyan]")
    
    if Confirm.ask(f"\nStart Monster CA scraping?", default=True):
        start_time = time.time()
        jobs = await scraper.scrape_all_keywords(max_jobs_per_keyword=max_jobs_per_keyword)
        end_time = time.time()
        duration = end_time - start_time
        
        if jobs:
            console.print(f"\n[bold green]🎉 Monster CA Scraping Complete![/bold green]")
            console.print(f"[green]✅ {len(jobs)} entry-level jobs found in {duration:.1f} seconds[/green]")
            console.print(f"[green]✅ Jobs saved to profile database: {profile_name}[/green]")
        else:
            console.print("[yellow]⚠️ No jobs found. Check search parameters and site availability.[/yellow]")
    else:
        console.print("[yellow]👋 Monster CA scraping cancelled[/yellow]")


if __name__ == "__main__":
    asyncio.run(main())
