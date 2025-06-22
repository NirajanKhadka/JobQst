#!/usr/bin/env python3
"""
Comprehensive Eluta Scraper
Scrapes ALL keywords from profile, filters for 0-2 years experience,
and covers last 14 days across Canada.
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Set
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel
from playwright.async_api import async_playwright

from job_database import get_job_db
import utils

console = Console()

class ComprehensiveElutaScraper:
    """
    Comprehensive Eluta scraper that uses ALL keywords and filters for entry-level positions.
    """
    
    def __init__(self, profile_name: str = "Nirajan"):
        """Initialize the comprehensive scraper."""
        self.profile_name = profile_name
        self.profile = utils.load_profile(profile_name)
        self.db = get_job_db(profile_name)
        
        # Get ALL keywords and skills from profile
        self.keywords = self.profile.get("keywords", [])
        self.skills = self.profile.get("skills", [])
        
        # Combine and deduplicate keywords
        all_terms = set(self.keywords + self.skills)
        self.search_terms = list(all_terms)
        
        console.print(f"[cyan]📋 Loaded {len(self.search_terms)} unique search terms[/cyan]")
        
        # Experience level filters for 0-2 years
        self.entry_level_keywords = [
            'junior', 'entry', 'entry level', 'entry-level', 'associate', 
            'graduate', 'new grad', 'recent graduate', 'trainee', 'coordinator',
            '0-2 years', '1-2 years', '0-1 years', 'level i', 'level 1',
            'intern', 'internship', 'co-op', 'coop'
        ]
        
        # Keywords to avoid (too senior for 0-2 years experience)
        self.avoid_keywords = [
            'senior', 'sr.', 'sr ', 'lead', 'principal', 'manager', 'director',
            'supervisor', 'head of', 'chief', 'vp', 'vice president',
            '3+ years', '4+ years', '5+ years', '10+ years', 'experienced',
            'expert', 'specialist ii', 'level ii', 'level 2', 'staff'
        ]
        
        # Scraping settings
        self.base_url = "https://www.eluta.ca/search"
        self.max_pages_per_keyword = 5  # 5 pages per keyword for comprehensive coverage
        self.jobs_per_page = 10
        self.delay_between_requests = 1  # seconds (faster for more coverage)
        
        # Results tracking
        self.all_jobs = []
        self.processed_urls = set()
        self.stats = {
            'keywords_processed': 0,
            'pages_scraped': 0,
            'jobs_found': 0,
            'jobs_filtered_out': 0,
            'entry_level_jobs': 0,
            'duplicates_skipped': 0
        }
    
    async def scrape_all_keywords(self, max_jobs_per_keyword: int = 30) -> List[Dict]:
        """
        Scrape jobs for ALL keywords with 0-2 years experience filter.
        
        Args:
            max_jobs_per_keyword: Maximum jobs to scrape per keyword
            
        Returns:
            List of filtered job dictionaries
        """
        console.print(Panel.fit("🎯 COMPREHENSIVE ELUTA SCRAPING", style="bold blue"))
        console.print(f"[cyan]🇨🇦 Searching across Canada[/cyan]")
        console.print(f"[cyan]📅 Last 14 days only[/cyan]")
        console.print(f"[cyan]👶 0-2 years experience filter[/cyan]")
        console.print(f"[cyan]🔍 {len(self.search_terms)} search terms[/cyan]")
        console.print(f"[cyan]📄 {self.max_pages_per_keyword} pages per keyword[/cyan]")
        console.print(f"[cyan]📊 Expected: {len(self.search_terms) * self.max_pages_per_keyword} total pages[/cyan]")

        # Display all search terms
        console.print(f"\n[bold]🔑 Search Terms:[/bold]")
        for i, term in enumerate(self.search_terms, 1):
            console.print(f"  {i:2d}. {term}")

        if not input(f"\nPress Enter to start comprehensive scraping ({len(self.search_terms)} keywords × {self.max_pages_per_keyword} pages = {len(self.search_terms) * self.max_pages_per_keyword} total pages) or Ctrl+C to cancel..."):
            pass
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()
            
            try:
                with Progress() as progress:
                    main_task = progress.add_task(
                        "[green]Scraping keywords...", 
                        total=len(self.search_terms)
                    )
                    
                    for keyword in self.search_terms:
                        console.print(f"\n[bold]🔍 Processing: {keyword}[/bold]")
                        
                        keyword_jobs = await self._scrape_keyword(
                            page, keyword, max_jobs_per_keyword, progress
                        )
                        
                        # Filter for entry-level positions
                        filtered_jobs = self._filter_entry_level_jobs(keyword_jobs, keyword)
                        
                        self.all_jobs.extend(filtered_jobs)
                        self.stats['keywords_processed'] += 1
                        
                        progress.update(main_task, advance=1)
                        
                        # Delay between keywords
                        await asyncio.sleep(self.delay_between_requests)
                
                # Remove duplicates
                unique_jobs = self._remove_duplicates(self.all_jobs)
                
                # Display final results
                self._display_comprehensive_results(unique_jobs)
                
                return unique_jobs
                
            finally:
                input("Press Enter to close browser...")
                await context.close()
                await browser.close()
    
    async def _scrape_keyword(self, page, keyword: str, max_jobs: int, progress: Progress) -> List[Dict]:
        """Scrape jobs for a specific keyword across multiple pages."""
        keyword_jobs = []
        jobs_collected = 0

        # Scrape multiple pages for comprehensive coverage
        for page_num in range(1, self.max_pages_per_keyword + 1):
            if jobs_collected >= max_jobs:
                break

            # Build search URL for Canada-wide search (empty location = all Canada)
            search_url = f"{self.base_url}?q={keyword}&l=&posted=14&pg={page_num}"  # Last 14 days, page number

            try:
                console.print(f"[cyan]🌐 Page {page_num}: {search_url}[/cyan]")
                await page.goto(search_url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)

                # Check if jobs found
                job_elements = await page.query_selector_all('.organic-job')
                if not job_elements:
                    console.print(f"[yellow]⚠️ No jobs found on page {page_num} for '{keyword}'[/yellow]")
                    break  # No more pages

                console.print(f"[green]✅ Found {len(job_elements)} jobs on page {page_num} for '{keyword}'[/green]")

                # Process jobs on current page
                jobs_on_page = 0
                for i, job_element in enumerate(job_elements):
                    if jobs_collected >= max_jobs:
                        break

                    try:
                        job_data = await self._extract_job_data(page, job_element, i + 1, page_num)
                        if job_data:
                            job_data['search_keyword'] = keyword
                            job_data['page_number'] = page_num
                            keyword_jobs.append(job_data)
                            self.stats['jobs_found'] += 1
                            jobs_collected += 1
                            jobs_on_page += 1

                    except Exception as e:
                        console.print(f"[red]❌ Error processing job {i+1} on page {page_num}: {e}[/red]")
                        continue

                self.stats['pages_scraped'] += 1
                console.print(f"[cyan]📄 Page {page_num}: Collected {jobs_on_page} jobs (Total: {jobs_collected})[/cyan]")

                # Clean up any leftover tabs
                await self._cleanup_extra_tabs(page.context)

                # Delay between pages
                await asyncio.sleep(self.delay_between_requests)

            except Exception as e:
                console.print(f"[red]❌ Error scraping page {page_num} for keyword '{keyword}': {e}[/red]")
                break

        console.print(f"[green]🎯 Keyword '{keyword}' complete: {jobs_collected} jobs from {page_num} pages[/green]")
        return keyword_jobs

    async def _cleanup_extra_tabs(self, context) -> None:
        """Clean up any extra tabs that might have been opened."""
        try:
            pages = context.pages
            # Keep only the main page (first one), close others
            if len(pages) > 1:
                for page in pages[1:]:  # Skip the first page
                    if not page.is_closed():
                        await page.close()
                        console.print(f"[dim]🗙 Cleaned up extra tab[/dim]")
        except Exception as e:
            console.print(f"[dim]⚠️ Tab cleanup warning: {e}[/dim]")

    async def _extract_job_data(self, page, job_element, job_number: int, page_num: int = 1) -> Dict:
        """Extract job data from a job element."""
        try:
            # Get job text content
            job_text = await job_element.inner_text()
            lines = [line.strip() for line in job_text.split('\n') if line.strip()]
            
            if len(lines) < 2:
                return None
            
            # Initialize job data
            job_data = {
                "title": lines[0] if lines else "",
                "company": "",
                "location": "",
                "salary": "",
                "description": "",
                "url": "",
                "apply_url": "",
                "source": "eluta.ca",
                "scraped_date": datetime.now().isoformat(),
                "ats_system": "Unknown",
                "scraped_successfully": False,
                "posted_date": "",
                "experience_level": "Unknown"
            }
            
            # Parse company (remove "TOP EMPLOYER" tag)
            if len(lines) > 1:
                company_line = lines[1]
                job_data["company"] = company_line.replace("TOP EMPLOYER", "").strip()
            
            # Parse location
            if len(lines) > 2:
                job_data["location"] = lines[2]
            
            # Parse description and look for salary
            if len(lines) > 3:
                description_lines = lines[3:]
                job_data["description"] = " ".join(description_lines)[:300] + "..."
                
                # Look for salary in description
                for line in description_lines:
                    if any(salary_indicator in line.lower() for salary_indicator in ['$', 'salary', 'wage', 'pay']):
                        job_data["salary"] = line
                        break
            
            # Extract real URL by clicking and handling new tab
            try:
                title_link = await job_element.query_selector('a')
                if title_link:
                    console.print(f"[cyan]🖱️ Clicking job {job_number} to get real URL...[/cyan]")

                    # Get current number of pages
                    initial_pages = len(page.context.pages)

                    # Click the link (this will open a new tab)
                    await title_link.click()

                    # Wait for new tab to open
                    await asyncio.sleep(2)

                    # Get all pages and find the new one
                    current_pages = page.context.pages
                    if len(current_pages) > initial_pages:
                        # New tab opened, get the last page (newest tab)
                        new_tab = current_pages[-1]

                        try:
                            # Wait for the new tab to load
                            await new_tab.wait_for_load_state("domcontentloaded", timeout=10000)

                            # Get the real URL from the new tab
                            real_url = new_tab.url

                            job_data["url"] = real_url
                            job_data["apply_url"] = real_url
                            job_data["ats_system"] = self._detect_ats_system(real_url)
                            job_data["scraped_successfully"] = True

                            console.print(f"[green]✅ Got real URL: {real_url[:60]}...[/green]")

                            # Close the new tab immediately
                            await new_tab.close()
                            console.print(f"[cyan]🗙 Closed tab for job {job_number}[/cyan]")

                        except Exception as tab_error:
                            console.print(f"[yellow]⚠️ Error processing new tab for job {job_number}: {tab_error}[/yellow]")

                            # Try to get URL anyway and close tab
                            try:
                                real_url = new_tab.url if new_tab else ""
                                if real_url:
                                    job_data["url"] = real_url
                                    job_data["apply_url"] = real_url
                                    job_data["ats_system"] = self._detect_ats_system(real_url)
                                    console.print(f"[yellow]📎 Got partial URL: {real_url[:60]}...[/yellow]")

                                # Close tab
                                if new_tab and not new_tab.is_closed():
                                    await new_tab.close()
                                    console.print(f"[cyan]🗙 Closed tab for job {job_number}[/cyan]")

                            except:
                                pass
                    else:
                        # No new tab opened, try to get href
                        href = await title_link.get_attribute('href')
                        if href:
                            job_data["url"] = href
                            job_data["apply_url"] = href
                            job_data["ats_system"] = "Eluta Redirect"
                            console.print(f"[yellow]📎 Using href (no new tab): {href[:60]}...[/yellow]")
                        else:
                            console.print(f"[yellow]⚠️ No new tab and no href for job {job_number}[/yellow]")
                else:
                    # No link found
                    job_data["url"] = ""
                    job_data["apply_url"] = ""
                    job_data["ats_system"] = "Unknown"
                    console.print(f"[yellow]⚠️ No link element found for job {job_number}[/yellow]")

            except Exception as e:
                console.print(f"[red]❌ Could not get URL for job {job_number}: {e}[/red]")
                # Set basic job data without URL
                job_data["url"] = ""
                job_data["apply_url"] = ""
                job_data["ats_system"] = "Unknown"
            
            return job_data
            
        except Exception as e:
            console.print(f"[red]❌ Error extracting job data: {e}[/red]")
            return None
    
    def _detect_ats_system(self, url: str) -> str:
        """Detect ATS system from URL."""
        url_lower = url.lower()
        
        if 'workday' in url_lower:
            return 'Workday'
        elif 'greenhouse' in url_lower:
            return 'Greenhouse'
        elif 'lever' in url_lower:
            return 'Lever'
        elif 'bamboohr' in url_lower:
            return 'BambooHR'
        elif 'smartrecruiters' in url_lower:
            return 'SmartRecruiters'
        elif 'jobvite' in url_lower:
            return 'Jobvite'
        elif 'icims' in url_lower:
            return 'iCIMS'
        elif 'taleo' in url_lower:
            return 'Taleo'
        else:
            return 'Company Website'
    
    def _filter_entry_level_jobs(self, jobs: List[Dict], keyword: str) -> List[Dict]:
        """Filter jobs to only include entry-level positions (0-2 years experience)."""
        entry_level_jobs = []
        
        for job in jobs:
            title = job.get('title', '').lower()
            description = job.get('description', '').lower()
            job_text = f"{title} {description}"
            
            # Check if job is too senior
            is_too_senior = any(avoid_term in job_text for avoid_term in self.avoid_keywords)
            
            if is_too_senior:
                console.print(f"[red]❌ Filtered out (too senior): {job.get('title', 'Unknown')}[/red]")
                self.stats['jobs_filtered_out'] += 1
                continue
            
            # Check if job is entry-level or has no experience requirements
            is_entry_level = any(entry_term in job_text for entry_term in self.entry_level_keywords)
            
            # If it's explicitly entry-level or doesn't mention senior requirements, include it
            if is_entry_level or not is_too_senior:
                job['experience_level'] = 'Entry Level' if is_entry_level else 'No Experience Specified'
                entry_level_jobs.append(job)
                self.stats['entry_level_jobs'] += 1
                console.print(f"[green]✅ Entry-level job: {job.get('title', 'Unknown')}[/green]")
            else:
                console.print(f"[yellow]⚠️ Filtered out (experience unclear): {job.get('title', 'Unknown')}[/yellow]")
                self.stats['jobs_filtered_out'] += 1
        
        return entry_level_jobs
    
    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on application URL."""
        unique_jobs = []
        seen_urls = set()

        for job in jobs:
            # Use apply_url as primary identifier, fallback to url, then title+company
            primary_url = job.get('apply_url', '') or job.get('url', '')

            # Create unique identifier
            if primary_url:
                unique_id = primary_url
            else:
                # Fallback: use title + company as identifier
                title = job.get('title', '').lower().strip()
                company = job.get('company', '').lower().strip()
                unique_id = f"{title}_{company}"

            if unique_id and unique_id not in seen_urls:
                unique_jobs.append(job)
                seen_urls.add(unique_id)
                console.print(f"[green]✅ Unique job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}[/green]")
            else:
                self.stats['duplicates_skipped'] += 1
                console.print(f"[yellow]🔄 Duplicate skipped: {job.get('title', 'Unknown')}[/yellow]")

        console.print(f"[cyan]📊 Deduplication: {len(unique_jobs)} unique jobs, {self.stats['duplicates_skipped']} duplicates removed[/cyan]")
        return unique_jobs
    
    def _display_comprehensive_results(self, jobs: List[Dict]) -> None:
        """Display comprehensive scraping results."""
        console.print("\n" + "="*80)
        console.print(Panel.fit("🎯 COMPREHENSIVE SCRAPING RESULTS", style="bold green"))
        
        # Statistics table
        stats_table = Table(title="Scraping Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="green")
        
        stats_table.add_row("Keywords Processed", str(self.stats['keywords_processed']))
        stats_table.add_row("Pages Scraped", str(self.stats['pages_scraped']))
        stats_table.add_row("Total Jobs Found", str(self.stats['jobs_found']))
        stats_table.add_row("Entry-Level Jobs", str(self.stats['entry_level_jobs']))
        stats_table.add_row("Jobs Filtered Out", str(self.stats['jobs_filtered_out']))
        stats_table.add_row("Duplicates Skipped", str(self.stats['duplicates_skipped']))
        stats_table.add_row("Final Unique Jobs", str(len(jobs)))
        
        console.print(stats_table)
        
        # Sample jobs table
        if jobs:
            console.print(f"\n[bold]📋 Sample Entry-Level Jobs Found:[/bold]")
            sample_table = Table()
            sample_table.add_column("Title", style="green", max_width=30)
            sample_table.add_column("Company", style="cyan", max_width=25)
            sample_table.add_column("Location", style="yellow", max_width=15)
            sample_table.add_column("ATS", style="blue", max_width=12)
            sample_table.add_column("Keyword", style="magenta", max_width=15)
            
            for job in jobs[:10]:  # Show first 10
                sample_table.add_row(
                    job.get('title', 'Unknown')[:27] + "..." if len(job.get('title', '')) > 30 else job.get('title', 'Unknown'),
                    job.get('company', 'Unknown')[:22] + "..." if len(job.get('company', '')) > 25 else job.get('company', 'Unknown'),
                    job.get('location', 'Unknown'),
                    job.get('ats_system', 'Unknown'),
                    job.get('search_keyword', 'Unknown')[:12] + "..." if len(job.get('search_keyword', '')) > 15 else job.get('search_keyword', 'Unknown')
                )
            
            console.print(sample_table)
            
            if len(jobs) > 10:
                console.print(f"[dim]... and {len(jobs) - 10} more entry-level jobs[/dim]")
        
        # Save to database
        if jobs:
            console.print(f"\n[cyan]💾 Saving {len(jobs)} entry-level jobs to database...[/cyan]")
            saved_count = 0
            for job in jobs:
                try:
                    self.db.add_job(job)
                    saved_count += 1
                except Exception as e:
                    console.print(f"[yellow]⚠️ Could not save job: {e}[/yellow]")
            
            console.print(f"[green]✅ Saved {saved_count} jobs to database[/green]")


# Convenience function
async def run_comprehensive_scraping(profile_name: str = "Nirajan", max_jobs_per_keyword: int = 30) -> List[Dict]:
    """Run comprehensive Eluta scraping."""
    scraper = ComprehensiveElutaScraper(profile_name)
    return await scraper.scrape_all_keywords(max_jobs_per_keyword)


if __name__ == "__main__":
    asyncio.run(run_comprehensive_scraping())
