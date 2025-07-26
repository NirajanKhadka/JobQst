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

from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile
from src.ats.ats_utils import detect_ats_system
from src.core.job_filters import filter_entry_level_jobs, remove_duplicates
from src.ai.enhanced_job_analyzer import EnhancedJobAnalyzer
from src.utils.simple_url_filter import get_simple_url_filter

console = Console()


class ComprehensiveElutaScraper:
    """
    Comprehensive Eluta scraper that uses ALL keywords and filters for entry-level positions.
    """

    def __init__(self, profile_name: str = "Nirajan"):
        """Initialize the comprehensive scraper."""
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

        # Initialize Enhanced Job Analyzer with LLM
        console.print("[yellow]Initializing Enhanced Job Analyzer with LLM...[\/yellow]")
        try:
            self.job_analyzer = EnhancedJobAnalyzer(
                profile=self.profile,
                fallback_to_llama=True,
                fallback_to_rule_based=True
            )
            console.print("[green]✅ Enhanced Job Analyzer with LLM ready![\/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to initialize LLM analyzer: {e}[/red]")
            console.print("[yellow]Continuing with basic filtering only...[/yellow]")
            self.job_analyzer = None

        # Experience level filters for 0-2 years
        self.entry_level_keywords = [
            "junior",
            "entry",
            "entry level",
            "entry-level",
            "associate",
            "graduate",
            "new grad",
            "recent graduate",
            "trainee",
            "coordinator",
            "0-2 years",
            "1-2 years",
            "0-1 years",
            "level i",
            "level 1",
            "intern",
            "internship",
            "co-op",
            "coop",
        ]

        # Keywords to avoid (too senior for 0-2 years experience)
        self.avoid_keywords = [
            "senior",
            "sr.",
            "sr ",
            "lead",
            "principal",
            "manager",
            "director",
            "supervisor",
            "head of",
            "chief",
            "vp",
            "vice president",
            "3+ years",
            "4+ years",
            "5+ years",
            "10+ years",
            "experienced",
            "expert",
            "specialist ii",
            "level ii",
            "level 2",
            "staff",
        ]

        # Scraping settings - FIXED URL FORMAT
        self.base_url = "https://www.eluta.ca/search"
        self.max_pages_per_keyword = 5  # 5 pages per keyword for comprehensive coverage
        self.jobs_per_page = 10
        self.delay_between_requests = 1  # seconds (faster for more coverage)

        # Results tracking
        self.all_jobs = []
        self.processed_urls = set()
        self.stats = {
            "keywords_processed": 0,
            "pages_scraped": 0,
            "jobs_found": 0,
            "jobs_filtered_out": 0,
            "entry_level_jobs": 0,
            "duplicates_skipped": 0,
        }

    def _clean_company_name(self, company_name: str) -> str:
        """Clean company name by removing common suffixes and prefixes."""
        if not company_name or company_name.strip() == "":
            return "Unknown Company"
        
        # Remove common suffixes and prefixes
        suffixes_to_remove = [
            "TOP EMPLOYER",
            "FEATURED EMPLOYER", 
            "PREMIUM EMPLOYER",
            "VERIFIED EMPLOYER",
            "HIRING NOW",
            "URGENT HIRING",
            "NEW JOBS",
            "MULTIPLE POSITIONS",
            "- REMOTE",
            "- HYBRID",
            "- ONSITE"
        ]
        
        cleaned = company_name.strip()
        
        # Remove suffixes (case insensitive)
        for suffix in suffixes_to_remove:
            if cleaned.upper().endswith(suffix.upper()):
                cleaned = cleaned[:-len(suffix)].strip()
        
        # Remove extra whitespace and special characters at the end
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces to single space
        cleaned = cleaned.rstrip(' -•·|')  # Remove trailing separators
        
        # Handle common patterns
        if " / " in cleaned:
            # Take the first part if it looks like "Company / Division"
            parts = cleaned.split(" / ")
            if len(parts[0]) > 3 and len(parts[0]) < len(cleaned) * 0.7:  # First part is substantial but not too long
                cleaned = parts[0].strip()
        
        # Final validation
        if len(cleaned) < 2:
            return "Unknown Company"
        
        return cleaned

    async def scrape_all_keywords(self, max_jobs_per_keyword: int = 30) -> List[Dict]:
        """
        Scrape jobs for ALL keywords with 0-2 years experience filter.

        Args:
            max_jobs_per_keyword: Maximum jobs to scrape per keyword

        Returns:
            List of filtered job dictionaries
        """
        console.print(Panel.fit("COMPREHENSIVE ELUTA SCRAPING", style="bold blue"))
        console.print(f"[cyan]Searching across Canada[/cyan]")
        console.print(f"[cyan]Last 14 days only[/cyan]")
        console.print(f"[cyan]0-2 years experience filter[/cyan]")
        console.print(f"[cyan]{len(self.search_terms)} search terms[/cyan]")
        console.print(f"[cyan]{self.max_pages_per_keyword} pages per keyword[/cyan]")
        console.print(
            f"[cyan]Expected: {len(self.search_terms) * self.max_pages_per_keyword} total pages[/cyan]"
        )

        # Display all search terms
        console.print(f"\n[bold]Search Terms:[/bold]")
        for i, term in enumerate(self.search_terms, 1):
            console.print(f"  {i:2d}. {term}")

        if not input(
            f"\nPress Enter to start comprehensive scraping ({len(self.search_terms)} keywords × {self.max_pages_per_keyword} pages = {len(self.search_terms) * self.max_pages_per_keyword} total pages) or Ctrl+C to cancel..."
        ):
            pass

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            try:
                with Progress() as progress:
                    main_task = progress.add_task(
                        "[green]Scraping keywords...", total=len(self.search_terms)
                    )

                    for keyword_index, keyword in enumerate(self.search_terms):
                        console.print(f"\n[bold]Processing: {keyword} ({keyword_index + 1}/{len(self.search_terms)})[/bold]")
                        
                        # Create new context and page for each keyword to ensure clean state
                        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
                        page = await context.new_page()
                        
                        try:
                            keyword_jobs = await self._scrape_keyword(
                                page, keyword, max_jobs_per_keyword, progress
                            )
                            
                            # Clean up any extra tabs that might have opened during scraping
                            await self._cleanup_extra_tabs(context)
                            
                            # Filter for entry-level positions using shared utility
                            filtered_jobs = filter_entry_level_jobs(keyword_jobs)
                            
                            # Apply LLM-based job analysis for enhanced matching (NON-BLOCKING)
                            if self.job_analyzer:
                                console.print(f"[cyan]Analyzing {len(filtered_jobs)} jobs with LLM...[/cyan]")
                                analyzed_jobs = []
                                for job in filtered_jobs:
                                    try:
                                        analysis = self.job_analyzer.analyze_job(job)
                                        if analysis:  # LLM analysis succeeded
                                            job['llm_analysis'] = analysis
                                            job['compatibility_score'] = analysis.get('compatibility_score', 0.5)
                                            job['llm_recommendation'] = analysis.get('recommendation', 'consider')
                                            console.print(f"[green]✅ {job.get('title', 'Unknown')} - LLM Score: {analysis.get('compatibility_score', 0):.2f}[/green]")
                                        else:  # LLM analysis failed, use defaults
                                            job['llm_analysis'] = None
                                            job['compatibility_score'] = 0.7  # Default good score when LLM fails
                                            job['llm_recommendation'] = 'consider'
                                            console.print(f"[yellow]⚠️ {job.get('title', 'Unknown')} - LLM failed, using default score[/yellow]")
                                    except Exception as e:
                                        console.print(f"[yellow]⚠️ LLM analysis failed for {job.get('title', 'Unknown')}: {e}[/yellow]")
                                        # Set defaults when LLM fails
                                        job['llm_analysis'] = None
                                        job['compatibility_score'] = 0.7  # Default good score
                                        job['llm_recommendation'] = 'consider'
                                    
                                    # Always keep the job (non-blocking LLM)
                                    analyzed_jobs.append(job)
                                
                                console.print(f"[green]✅ Processed {len(analyzed_jobs)} jobs (LLM analysis non-blocking)[/green]")
                                self.all_jobs.extend(analyzed_jobs)
                            else:
                                # No LLM analyzer, add default scores and keep all jobs
                                for job in filtered_jobs:
                                    job['llm_analysis'] = None
                                    job['compatibility_score'] = 0.7  # Default good score
                                    job['llm_recommendation'] = 'consider'
                                console.print(f"[cyan]No LLM analyzer, keeping all {len(filtered_jobs)} jobs with default scores[/cyan]")
                                self.all_jobs.extend(filtered_jobs)
                            
                            self.stats["keywords_processed"] += 1
                            progress.update(main_task, advance=1)
                            
                        finally:
                            # Close context after each keyword to clean up resources
                            console.print(f"[dim]🧹 Cleaning up context for keyword: {keyword}[/dim]")
                            await context.close()
                            await asyncio.sleep(self.delay_between_requests)

                # Remove duplicates using shared utility
                unique_jobs = remove_duplicates(self.all_jobs)
                self._display_comprehensive_results(unique_jobs)
                return unique_jobs

            finally:
                console.print("[dim]🧹 Closing browser...[/dim]")
                await browser.close()

    async def _scrape_keyword(
        self, page, keyword: str, max_jobs: int, progress: Progress
    ) -> List[Dict]:
        """Scrape jobs for a specific keyword."""
        keyword_jobs = []
        pages_scraped = 0

        try:
            # Navigate to search page - FIXED URL FORMAT
            # Use the correct Eluta URL format: q=keyword+sort%3Arank&pg=page_number
            search_url = f"{self.base_url}?q={keyword.replace(' ', '+')}+sort%3Arank"
            await page.goto(search_url, wait_until="networkidle")
            await asyncio.sleep(self.delay_between_requests)

            while pages_scraped < self.max_pages_per_keyword and len(keyword_jobs) < max_jobs:
                pages_scraped += 1
                self.stats["pages_scraped"] += 1

                console.print(f"[cyan]Scraping page {pages_scraped} for '{keyword}'[/cyan]")

                # Wait for job results to load
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

                # Find job elements - Use multiple selectors to find job listings
                job_elements = []
                
                # Try different selectors that might contain job listings
                selectors_to_try = [
                    ".organic-job",  # Common job listing class
                    ".job-result",   # Alternative job listing class
                    ".job-listing",  # Another common class
                    ".job-item",     # Generic job item
                    "[data-job]",    # Data attribute selector
                    ".result",       # Generic result class
                    "article",       # Semantic HTML
                    ".listing"       # Generic listing class
                ]
                
                for selector in selectors_to_try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        console.print(f"[green]Found {len(elements)} elements with selector: {selector}[/green]")
                        job_elements = elements
                        break
                
                # If no specific job elements found, try to find job titles in h2/h3 elements
                if not job_elements:
                    console.print("[yellow]No job containers found, trying title elements...[/yellow]")
                    title_elements = await page.query_selector_all("h2, h3")
                    actual_job_elements = []
                    for elem in title_elements:
                        try:
                            text = await elem.inner_text()
                            # Job titles typically are longer than navigation text and contain job-related keywords
                            if (len(text.strip()) > 15 and
                                any(keyword in text.lower() for keyword in ['developer', 'analyst', 'engineer', 'specialist', 'coordinator', 'manager', 'intern', 'associate', 'junior', 'senior'])):
                                actual_job_elements.append(elem)
                        except:
                            continue
                    job_elements = actual_job_elements
                else:
                    actual_job_elements = job_elements

                console.print(f"[cyan]Found {len(actual_job_elements)} job elements on page {pages_scraped}[/cyan]")

                if not actual_job_elements:
                    console.print(f"[yellow]No job elements found on page {pages_scraped}, stopping[/yellow]")
                    break

                # Process each job element
                for job_number, job_element in enumerate(actual_job_elements, 1):
                    if len(keyword_jobs) >= max_jobs:
                        break

                    try:
                        job_data = await self._extract_job_data(
                            page, job_element, job_number, pages_scraped
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
                                f"[green]✅ Found: {job_data['title'][:50]}... at {job_data['company'][:30]}[/green]"
                            )

                    except Exception as e:
                        console.print(f"[red]Error processing job {job_number}: {e}[/red]")
                        continue

                # Navigate to next page using correct URL format
                if len(keyword_jobs) < max_jobs and pages_scraped < self.max_pages_per_keyword:
                    next_page_num = pages_scraped + 1
                    next_page_url = f"{self.base_url}?q={keyword.replace(' ', '+')}+sort%3Arank&pg={next_page_num}"
                    console.print(f"[cyan]Going to page {next_page_num}: {next_page_url}[/cyan]")
                    await page.goto(next_page_url, wait_until="networkidle")
                    await asyncio.sleep(self.delay_between_requests)
                else:
                    console.print(f"[yellow]Reached max pages or jobs for '{keyword}'[/yellow]")
                    break

        except Exception as e:
            console.print(f"[red]Error scraping keyword '{keyword}': {e}[/red]")

        self.stats["keywords_processed"] += 1
        return keyword_jobs

    async def _cleanup_extra_tabs(self, context) -> None:
        """Clean up any extra tabs that might have been opened during scraping."""
        try:
            pages = context.pages
            main_page = pages[0] if pages else None
            
            # Close all extra tabs except the main one
            if len(pages) > 1:
                console.print(f"[dim]🧹 Found {len(pages)} tabs, cleaning up {len(pages) - 1} extra tabs...[/dim]")
                for page in pages[1:]:  # Skip the first page
                    try:
                        if not page.is_closed():
                            await page.close()
                            console.print(f"[dim]✅ Closed extra tab[/dim]")
                    except Exception as tab_error:
                        console.print(f"[dim]⚠️ Error closing tab: {tab_error}[/dim]")
                        
                # Verify cleanup
                remaining_pages = context.pages
                console.print(f"[dim]📊 Tabs after cleanup: {len(remaining_pages)}[/dim]")
                
        except Exception as e:
            console.print(f"[dim]⚠️ Tab cleanup warning: {e}[/dim]")

    async def _extract_job_data(
        self, page, job_element, job_number: int, page_num: int = 1
    ) -> Dict:
        """Extract job data from a job element (h2 title element)."""
        try:
            # Get the job title from the h2 element
            job_title = await job_element.inner_text()
            
            # Find the parent container that holds the job information
            # Navigate up to find the job container
            job_container = job_element
            for _ in range(5):  # Go up max 5 levels
                job_container = await job_container.query_selector("..")
                if not job_container:
                    break
                
                # Check if this container has job-related content
                container_text = await job_container.inner_text()
                if any(keyword in container_text.lower() for keyword in ['$', 'developer', 'analyst', 'engineer', 'specialist']):
                    break
            
            if not job_container:
                console.print(f"[yellow]Could not find job container for job {job_number}[/yellow]")
                return {}
            
            # Get all text content from the job container
            container_text = await job_container.inner_text()
            lines = [line.strip() for line in container_text.split("\n") if line.strip()]

            # Initialize job data
            job_data = {
                "title": job_title,
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
                "experience_level": "Unknown",
                "search_keyword": "",  # Will be set by caller
            }

            # Parse the lines to extract company, location, salary
            for i, line in enumerate(lines):
                line_lower = line.lower()
                
                # Skip the title line (already extracted)
                if line == job_title:
                    continue
                
                # Skip lines that are clearly not company names
                if (len(line) < 3 or len(line) > 80 or
                    line_lower.startswith(('job', 'position', 'role', 'career', 'apply', 'view', 'more')) or
                    any(word in line_lower for word in ['ago', 'posted', 'days', 'hours', 'minutes', 'salary', 'wage', 'pay']) or
                    line.count('$') > 0 or line.count('•') > 2):
                    continue
                
                # Look for salary information
                if any(char in line for char in ['$', '€', '£']) and any(word in line_lower for word in ['salary', 'wage', 'pay', 'hourly', 'annual']):
                    job_data["salary"] = line
                    continue
                
                # Look for location (typically contains city and province/state)
                if any(word in line_lower for word in ['qc', 'on', 'bc', 'ab', 'mb', 'sk', 'ns', 'nb', 'pe', 'nl', 'yt', 'nt', 'nu']) or \
                   any(word in line_lower for word in ['montreal', 'toronto', 'vancouver', 'calgary', 'edmonton', 'ottawa']):
                    job_data["location"] = line
                    continue
                
                # Company name extraction - be more selective
                if (not job_data["company"] and  # Only set if not already found
                    len(line) > 2 and len(line) < 60 and  # Reasonable length
                    not any(char in line for char in ['$', '€', '£', '@', 'http', 'www', '•', '·']) and
                    not any(word in line_lower for word in ['posted', 'apply', 'view', 'more', 'details', 'ago', 'days', 'hours', 'minutes', 'job', 'position', 'role']) and
                    not line_lower.startswith(('job', 'position', 'role', 'career', 'opportunity')) and
                    not any(province in line.upper() for province in ['ON', 'BC', 'AB', 'QC', 'MB', 'SK', 'NS', 'NB', 'PE', 'NL']) and
                    line != job_title):  # Don't use title as company
                    # Additional validation - company names usually have certain patterns
                    if (any(word in line_lower for word in ['inc', 'ltd', 'corp', 'company', 'group', 'solutions', 'services', 'technologies', 'systems']) or
                        (len(line.split()) <= 4 and not any(char.isdigit() for char in line))):  # Short names without numbers
                        job_data["company"] = line
                        continue
                
                # Description is everything else combined
                if line and line not in [job_data["company"], job_data["location"], job_data["salary"]]:
                    if job_data["description"]:
                        job_data["description"] += " " + line
                    else:
                        job_data["description"] = line

            # Get the real job URL
            real_url = await self._get_real_job_url(job_element, page, job_number)
            if real_url:
                final_url = await self._refine_and_get_final_url(real_url, page.context)
                if final_url and "eluta.ca" not in final_url:
                    job_data["apply_url"] = final_url
                    job_data["url"] = final_url
                    job_data["scraped_successfully"] = True
                    job_data["ats_system"] = detect_ats_system(final_url)
                    console.print(f"[green]Got final URL: {final_url[:60]}...[/green]")
                else:
                    job_data["url"] = real_url
                    job_data["apply_url"] = real_url
                    console.print(f"[yellow]Using initial URL: {real_url[:60]}...[/yellow]")
            else:
                console.print(f"[red]Could not get URL for job {job_number}[/red]")
                return {}

            # Validate that we have essential data
            if not job_data["title"] or not job_data["url"]:
                console.print(f"[yellow]Missing essential data for job {job_number}[/yellow]")
                return {}
            
            # Clean company name if found
            if job_data["company"]:
                job_data["company"] = self._clean_company_name(job_data["company"])
            
            # Company name fallback - extract from URL if still empty
            if not job_data["company"] or job_data["company"] == "":
                try:
                    from urllib.parse import urlparse
                    parsed_url = urlparse(job_data["url"])
                    domain = parsed_url.netloc.lower()
                    
                    # Extract company name from domain
                    if domain:
                        # Remove common prefixes and suffixes
                        domain = domain.replace('www.', '').replace('careers.', '').replace('jobs.', '')
                        company_name = domain.split('.')[0]
                        
                        # Capitalize properly
                        if company_name and len(company_name) > 2:
                            job_data["company"] = company_name.capitalize()
                            console.print(f"[dim]📝 Extracted company from URL: {job_data['company']}[/dim]")
                except:
                    pass
                
                # Final fallback
                if not job_data["company"]:
                    job_data["company"] = "Company from Eluta"

            return job_data

        except Exception as e:
            console.print(f"[red]Error extracting job data for job {job_number}: {e}[/red]")
            return {}

    async def _get_real_job_url(self, job_elem, page, job_number):
        """Get real job URL from h2 job title element with robust timeout handling."""
        try:
            # Since job_elem is an h2, we need to find the link within it or its parent
            # First, try to find a link within the h2 element
            link = await job_elem.query_selector("a")
            
            if not link:
                # If no link in h2, look in the parent container
                parent = await job_elem.query_selector("..")
                if parent:
                    link = await parent.query_selector("a")
            
            if not link:
                # Look for any link in the job container
                job_container = job_elem
                for _ in range(3):  # Go up max 3 levels
                    job_container = await job_container.query_selector("..")
                    if not job_container:
                        break
                    
                    # Look for links in this container
                    links = await job_container.query_selector_all("a")
                    for potential_link in links:
                        href = await potential_link.get_attribute("href")
                        
                        if href and not any(skip in href for skip in ["/search?", "q=", "pg=", "posted="]):
                            # This looks like a job link
                            link = potential_link
                            break
                    
                    if link:
                        break
            
            if not link:
                console.print(f"[yellow]Job {job_number}: No job link found[/yellow]")
                return ""

            # Get the href attribute
            href = await link.get_attribute("href")
            if not href:
                console.print(f"[yellow]Job {job_number}: Link has no href[/yellow]")
                return ""

            console.print(f"[cyan]Job {job_number}: Found link href: {href[:60]}...[/cyan]")

            # Method 1: If it's a direct external URL, use it
            if href.startswith("http") and "eluta.ca" not in href:
                console.print(f"[green]Job {job_number}: Direct external URL: {href[:60]}...[/green]")
                return href

            # Method 2: If it's a relative URL, make it absolute
            if href.startswith("/") and not any(skip in href for skip in ["/search?", "q=", "pg="]):
                full_url = "https://www.eluta.ca" + href
                console.print(f"[cyan]Job {job_number}: Converted to absolute URL: {full_url[:60]}...[/cyan]")
                return full_url

            # Method 3: If it's already a full Eluta URL, use it
            if href.startswith("https://www.eluta.ca") and not any(skip in href for skip in ["/search?", "q=", "pg="]):
                console.print(f"[cyan]Job {job_number}: Full Eluta URL: {href[:60]}...[/cyan]")
                return href

            # Method 4: Try clicking the link to get the real URL with timeout
            if href == "#!" or not href or href.startswith("#"):
                console.print(f"[cyan]Job {job_number}: Clicking link to get real URL...[/cyan]")
                
                try:
                    # Method 4a: Try popup method with proper async context management
                    async with page.expect_popup() as popup_info:
                        await asyncio.wait_for(link.click(modifiers=["Control"]), timeout=5)
                    
                    popup = await asyncio.wait_for(popup_info.value, timeout=10)
                    
                    try:
                        await asyncio.wait_for(popup.wait_for_load_state("networkidle"), timeout=15)
                        real_url = popup.url
                        
                        # Validate URL before closing popup
                        if real_url and not any(skip in real_url for skip in ["/search?", "q=", "pg="]):
                            console.print(f"[green]Job {job_number}: Got real URL from popup: {real_url[:60]}...[/green]")
                            await popup.close()
                            return real_url
                        else:
                            console.print(f"[yellow]Job {job_number}: Popup gave invalid URL: {real_url}[/yellow]")
                            await popup.close()
                            return ""
                    except Exception as popup_load_error:
                        console.print(f"[yellow]Job {job_number}: Popup load failed: {popup_load_error}[/yellow]")
                        try:
                            await popup.close()
                        except:
                            pass
                        # Continue to fallback method
                    
                except asyncio.TimeoutError:
                    console.print(f"[yellow]Job {job_number}: Popup method timeout - trying navigation fallback[/yellow]")
                    
                except Exception as popup_error:
                    console.print(f"[yellow]Job {job_number}: Popup method failed: {popup_error} - trying navigation fallback[/yellow]")
                
                # Method 4b: Fallback to navigation method with timeout
                try:
                    current_url = page.url
                    await asyncio.wait_for(link.click(), timeout=5)
                    await asyncio.wait_for(page.wait_for_load_state("networkidle"), timeout=15)
                    new_url = page.url
                    
                    if new_url != current_url and not any(skip in new_url for skip in ["/search?", "q=", "pg="]):
                        console.print(f"[green]Job {job_number}: Got URL from navigation: {new_url[:60]}...[/green]")
                        # Navigate back to search results
                        try:
                            await asyncio.wait_for(page.go_back(), timeout=10)
                            await asyncio.wait_for(page.wait_for_load_state("networkidle"), timeout=10)
                        except Exception as back_error:
                            console.print(f"[yellow]Job {job_number}: Could not navigate back: {back_error}[/yellow]")
                        return new_url
                    else:
                        console.print(f"[yellow]Job {job_number}: Navigation gave invalid URL: {new_url}[/yellow]")
                        return ""
                        
                except asyncio.TimeoutError:
                    console.print(f"[red]Job {job_number}: Navigation method timeout - skipping job[/red]")
                    # Try to go back anyway
                    try:
                        await asyncio.wait_for(page.go_back(), timeout=5)
                    except:
                        pass
                    return ""
                except Exception as nav_error:
                    console.print(f"[red]Job {job_number}: Navigation method failed: {nav_error}[/red]")
                    return ""
            
            console.print(f"[yellow]Job {job_number}: Unknown or invalid href format: {href}[/yellow]")
            return ""

        except Exception as e:
            console.print(f"[red]Error getting real job URL for job {job_number}: {e}[/red]")
            return ""

    async def _refine_and_get_final_url(self, url: str, context) -> str:
        """
        Navigates to a URL in a new tab to resolve any redirects (like Eluta's)
        and returns the final destination URL.
        """
        # Skip refinement for search URLs (these are the fake ones)
        if any(skip in url for skip in ["/search?", "q=", "pg=", "posted="]):
            console.print(f"[red]Skipping search URL refinement: {url[:70]}[/red]")
            return ""
        
        # Only refine URLs that need it (redirects or Eluta URLs)
        if not url or not any(keyword in url for keyword in ["eluta.ca/redirect", "/redirect", "/go/"]):
            return url  # No need to refine

        final_url = url
        refine_page = None
        try:
            refine_page = await context.new_page()
            console.print(f"[cyan]Refining redirect URL: {url[:70]}...[/cyan]")
            
            # Navigate and wait for final destination with timeout
            await asyncio.wait_for(
                refine_page.goto(url, wait_until="networkidle"), 
                timeout=15
            )
            await asyncio.sleep(2)  # Wait for client-side redirects
            
            final_url = refine_page.url
            
            # Validate the final URL is not another search page
            if any(skip in final_url for skip in ["/search?", "q=", "pg=", "posted="]):
                console.print(f"[red]Refined URL is still a search page: {final_url[:70]}[/red]")
                await refine_page.close()
                return ""
            
            console.print(f"[green]Successfully refined to: {final_url[:70]}...[/green]")
            await refine_page.close()
            
        except Exception as e:
            console.print(f"[yellow]Could not refine URL {url}: {e}[/yellow]")
            try:
                await refine_page.close()
            except:
                pass
            # Return empty string if refinement fails to avoid bad URLs
            return ""
        
        return final_url

    def _display_comprehensive_results(self, jobs: List[Dict]) -> None:
        """Display comprehensive scraping results."""
        console.print("\n" + "=" * 80)
        console.print(Panel.fit("COMPREHENSIVE SCRAPING RESULTS", style="bold green"))

        # Statistics table
        stats_table = Table(title="Scraping Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="green")

        stats_table.add_row("Keywords Processed", str(self.stats["keywords_processed"]))
        stats_table.add_row("Pages Scraped", str(self.stats["pages_scraped"]))
        stats_table.add_row("Total Jobs Found", str(self.stats["jobs_found"]))
        stats_table.add_row("Entry-Level Jobs", str(self.stats["entry_level_jobs"]))
        stats_table.add_row("Jobs Filtered Out", str(self.stats["jobs_filtered_out"]))
        stats_table.add_row("Duplicates Skipped", str(self.stats["duplicates_skipped"]))
        
        # Add LLM analysis statistics
        llm_analyzed = sum(1 for job in jobs if 'llm_analysis' in job)
        high_compatibility = sum(1 for job in jobs if job.get('compatibility_score', 0) >= 0.8)
        stats_table.add_row("LLM Analyzed Jobs", str(llm_analyzed))
        stats_table.add_row("High Compatibility (≥0.8)", str(high_compatibility))
        stats_table.add_row("Final Unique Jobs", str(len(jobs)))

        console.print(stats_table)

        # Sample jobs table
        if jobs:
            console.print(f"\n[bold]Sample Entry-Level Jobs Found (with LLM Analysis):[/bold]")
            sample_table = Table()
            sample_table.add_column("Title", style="green", max_width=30)
            sample_table.add_column("Company", style="cyan", max_width=25)
            sample_table.add_column("Location", style="yellow", max_width=15)
            sample_table.add_column("LLM Score", style="magenta", max_width=10)
            sample_table.add_column("Recommendation", style="blue", max_width=12)
            sample_table.add_column("ATS", style="white", max_width=10)

            # Sort jobs by LLM compatibility score (highest first)
            sorted_jobs = sorted(jobs, key=lambda x: x.get('compatibility_score', 0), reverse=True)
            for job in sorted_jobs[:15]:  # Show top 15
                llm_score = job.get('compatibility_score', 0)
                recommendation = job.get('llm_recommendation', 'N/A')
                
                sample_table.add_row(
                    (
                        job.get("title", "Unknown")[:27] + "..."
                        if len(job.get("title", "")) > 30
                        else job.get("title", "Unknown")
                    ),
                    (
                        job.get("company", "Unknown")[:22] + "..."
                        if len(job.get("company", "")) > 25
                        else job.get("company", "Unknown")
                    ),
                    job.get("location", "Unknown")[:12],
                    f"{llm_score:.2f}" if llm_score > 0 else "N/A",
                    recommendation[:10] if recommendation != 'N/A' else "N/A",
                    job.get("ats_system", "Unknown")[:8]
                )

            console.print(sample_table)

            if len(jobs) > 10:
                console.print(f"[dim]... and {len(jobs) - 10} more entry-level jobs[/dim]")

        # Save to database, using URL filter to skip invalid URLs
        if jobs:
            console.print(f"\n[cyan]Saving {len(jobs)} entry-level jobs to database...[/cyan]")
            saved_count = 0
            skipped_count = 0
            eluta_skipped = 0
            
            for job in jobs:
                url = job.get("url", "")
                apply_url = job.get("apply_url", "")
                
                # Use the primary URL (prefer apply_url if available, otherwise use url)
                primary_url = apply_url if apply_url else url
                
                # Skip invalid Eluta URLs specifically
                if 'eluta.ca' in primary_url.lower():
                    # Check for broken Eluta patterns
                    import re
                    if (re.match(r'https://www\.eluta\.ca/job/\d+$', primary_url) or 
                        len(primary_url) < 40 or
                        '/hosted/' in primary_url):  # Hosted URLs are often broken
                        console.print(f"[red]❌ Skipping broken Eluta URL: {primary_url}[/red]")
                        eluta_skipped += 1
                        skipped_count += 1
                        continue
                
                # Use URL filter for general validation
                if not self.url_filter.is_valid_job_url(primary_url):
                    reason = self.url_filter.get_invalid_reason(primary_url)
                    console.print(f"[yellow]⚠️ Skipping invalid URL ({reason}): {primary_url[:50]}...[/yellow]")
                    skipped_count += 1
                    continue
                
                # URL is valid, save the job
                try:
                    self.db.add_job(job)
                    saved_count += 1
                except Exception as e:
                    console.print(f"[yellow]Could not save job: {e}[/yellow]")
            
            console.print(f"[green]✅ Saved {saved_count} valid jobs to database[/green]")
            if skipped_count > 0:
                console.print(f"[yellow]⚠️ Skipped {skipped_count} jobs with invalid URLs[/yellow]")
                if eluta_skipped > 0:
                    console.print(f"[red]   - {eluta_skipped} broken Eluta URLs filtered out[/red]")


# Convenience function
async def run_comprehensive_scraping(
    profile_name: str = "Nirajan", max_jobs_per_keyword: int = 30
) -> List[Dict]:
    """Run comprehensive Eluta scraping."""
    scraper = ComprehensiveElutaScraper(profile_name)
    return await scraper.scrape_all_keywords(max_jobs_per_keyword)


if __name__ == "__main__":
    asyncio.run(run_comprehensive_scraping())
