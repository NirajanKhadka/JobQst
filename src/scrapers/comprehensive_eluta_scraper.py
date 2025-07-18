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

console = Console()


class ComprehensiveElutaScraper:
    """
    Comprehensive Eluta scraper that uses ALL keywords and filters for entry-level positions.
    """

    def __init__(self, profile_name: str = "Nirajan"):
        """Initialize the comprehensive scraper."""
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
        
        # Initialize Enhanced Job Analyzer with LLM
        console.print("[yellow]Initializing Enhanced Job Analyzer with LLM...[/yellow]")
        try:
            self.job_analyzer = EnhancedJobAnalyzer(
                profile=self.profile,
                use_llama=True,
                fallback_to_rule_based=True
            )
            console.print("[green]✅ Enhanced Job Analyzer with LLM ready![/green]")
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

        # Scraping settings
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
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
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
                        # Filter for entry-level positions using shared utility
                        filtered_jobs = filter_entry_level_jobs(keyword_jobs)
                        
                        # Apply LLM-based job analysis for enhanced matching
                        if self.job_analyzer:
                            console.print(f"[cyan]Analyzing {len(filtered_jobs)} jobs with LLM...[/cyan]")
                            analyzed_jobs = []
                            for job in filtered_jobs:
                                try:
                                    analysis = self.job_analyzer.analyze_job(job)
                                    job['llm_analysis'] = analysis
                                    job['compatibility_score'] = analysis.get('compatibility_score', 0.5)
                                    job['llm_recommendation'] = analysis.get('recommendation', 'consider')
                                    
                                    # Only keep jobs with good compatibility (>= 0.6) or recommended
                                    if (analysis.get('compatibility_score', 0) >= 0.6 or 
                                        analysis.get('recommendation') in ['highly_recommend', 'recommend']):
                                        analyzed_jobs.append(job)
                                        console.print(f"[green]✅ {job.get('title', 'Unknown')} - Score: {analysis.get('compatibility_score', 0):.2f}[/green]")
                                    else:
                                        console.print(f"[yellow]⚠️ {job.get('title', 'Unknown')} - Low compatibility: {analysis.get('compatibility_score', 0):.2f}[/yellow]")
                                except Exception as e:
                                    console.print(f"[red]❌ LLM analysis failed for job: {e}[/red]")
                                    analyzed_jobs.append(job)  # Keep job even if analysis fails
                            
                            console.print(f"[green]LLM Analysis: {len(analyzed_jobs)}/{len(filtered_jobs)} jobs passed compatibility threshold[/green]")
                            self.all_jobs.extend(analyzed_jobs)
                        else:
                            self.all_jobs.extend(filtered_jobs)
                        self.stats["keywords_processed"] += 1
                        progress.update(main_task, advance=1)
                        await asyncio.sleep(self.delay_between_requests)

                # Remove duplicates using shared utility
                unique_jobs = remove_duplicates(self.all_jobs)
                self._display_comprehensive_results(unique_jobs)
                return unique_jobs

            finally:
                input("Press Enter to close browser...")
                await context.close()
                await browser.close()

    async def _scrape_keyword(
        self, page, keyword: str, max_jobs: int, progress: Progress
    ) -> List[Dict]:
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
                console.print(f"[cyan]Page {page_num}: {search_url}[/cyan]")
                await page.goto(search_url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)

                # Check if jobs found
                job_elements = await page.query_selector_all(".organic-job")
                if not job_elements:
                    console.print(
                        f"[yellow]No jobs found on page {page_num} for '{keyword}'[/yellow]"
                    )
                    break  # No more pages

                console.print(
                    f"[green]Found {len(job_elements)} jobs on page {page_num} for '{keyword}'[/green]"
                )

                # Process jobs on current page
                jobs_on_page = 0
                for i, job_element in enumerate(job_elements):
                    if jobs_collected >= max_jobs:
                        break

                    try:
                        job_data = await self._extract_job_data(page, job_element, i + 1, page_num)
                        if job_data:
                            job_data["search_keyword"] = keyword
                            job_data["page_number"] = page_num
                            keyword_jobs.append(job_data)
                            self.stats["jobs_found"] += 1
                            jobs_collected += 1
                            jobs_on_page += 1

                    except Exception as e:
                        console.print(
                            f"[red]Error processing job {i+1} on page {page_num}: {e}[/red]"
                        )
                        continue

                self.stats["pages_scraped"] += 1
                console.print(
                    f"[cyan]Page {page_num}: Collected {jobs_on_page} jobs (Total: {jobs_collected})[/cyan]"
                )

                # Clean up any leftover tabs
                await self._cleanup_extra_tabs(page.context)

                # Delay between pages
                await asyncio.sleep(self.delay_between_requests)

            except Exception as e:
                console.print(
                    f"[red]Error scraping page {page_num} for keyword '{keyword}': {e}[/red]"
                )
                break

        console.print(
            f"[green]Keyword '{keyword}' complete: {jobs_collected} jobs from {page_num} pages[/green]"
        )
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
                        console.print(f"[dim]Cleaned up extra tab[/dim]")
        except Exception as e:
            console.print(f"[dim]Tab cleanup warning: {e}[/dim]")

    async def _extract_job_data(
        self, page, job_element, job_number: int, page_num: int = 1
    ) -> Dict:
        """Extract job data from a job element."""
        try:
            # Get job text content
            job_text = await job_element.inner_text()
            lines = [line.strip() for line in job_text.split("\n") if line.strip()]

            if len(lines) < 2:
                return {}

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
                "experience_level": "Unknown",
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
                    if any(
                        salary_indicator in line.lower()
                        for salary_indicator in ["$", "salary", "wage", "pay"]
                    ):
                        job_data["salary"] = line
                        break

            # Get real application URL using a refined, multi-step process
            initial_url = await self._get_real_job_url(job_element, page, job_number)
            if initial_url:
                final_url = await self._refine_and_get_final_url(initial_url, page.context)
                if final_url and "eluta.ca" not in final_url:
                    job_data["apply_url"] = final_url
                    job_data["url"] = final_url
                    job_data["scraped_successfully"] = True
                    job_data["ats_system"] = detect_ats_system(final_url)
                    console.print(f"[green]Got final URL: {final_url[:60]}...[/green]")
                    console.print(f"[cyan]ATS System: {job_data['ats_system']}[/cyan]")
                else:
                    job_data["url"] = initial_url
                    job_data["apply_url"] = initial_url
                    console.print(f"[yellow]Using initial URL, refinement failed or yielded Eluta link[/yellow]")
            else:
                job_data["url"] = page.url
                job_data["apply_url"] = page.url
                console.print(f"[yellow]Using fallback URL[/yellow]")

            return job_data

        except Exception as e:
            console.print(f"[red]Error extracting job data: {e}[/red]")
            return {}

    async def _get_real_job_url(self, job_elem, page, job_number):
        """Get real job URL using a more robust, flexible method."""
        try:
            links = await job_elem.query_selector_all("a")
            title_link = None
            href_url = None

            # Debug: Print all links found
            console.print(f"[dim]Job {job_number}: Found {len(links)} links[/dim]")
            
            # Look specifically for job title links (usually the first link or links with job-related attributes)
            for i, link in enumerate(links):
                href = await link.get_attribute("href")
                link_text = await link.inner_text()
                link_class = await link.get_attribute("class") or ""
                
                if href:
                    console.print(f"[dim]  Link {i+1}: {href[:60]} | Text: {link_text[:20]} | Class: {link_class}[/dim]")
                    
                    # Skip search result links (these are the fake ones causing the issue)
                    if ("/search?" in href or 
                        "q=" in href or 
                        "pg=" in href or
                        "posted=" in href):
                        console.print(f"[yellow]  Skipping search URL: {href[:60]}[/yellow]")
                        continue
                    
                    # Look for actual job posting links
                    if (href.startswith("/redirect") or 
                        href.startswith("/go/") or
                        "/job/" in href or
                        "/jobs/" in href or
                        "redirect" in href or
                        "jobid" in href.lower() or
                        # Job title is usually the first meaningful link text
                        (link_text and len(link_text.strip()) > 10 and not any(skip in link_text.lower() for skip in ["more", "search", "filter"]))):
                        title_link = link
                        href_url = href
                        console.print(f"[green]Job {job_number}: Selected job link: {href[:60]}[/green]")
                        break

            # If no specific job link found, try to find the job title link more specifically
            if not title_link and links:
                # Look for links that are likely job titles (longer text, not navigation)
                for link in links:
                    href = await link.get_attribute("href")
                    link_text = await link.inner_text()
                    
                    if (href and href.strip() and 
                        not any(skip in href for skip in ["/search?", "q=", "pg=", "posted="]) and
                        link_text and len(link_text.strip()) > 5):
                        title_link = link
                        href_url = href
                        console.print(f"[yellow]Job {job_number}: Using title link: {href[:60]} | Text: {link_text[:30]}[/yellow]")
                        break
                
                # Last resort: use first non-search link
                if not title_link:
                    for link in links:
                        href = await link.get_attribute("href")
                        if (href and href.strip() and 
                            not any(skip in href for skip in ["/search?", "q=", "pg=", "posted="])):
                            title_link = link
                            href_url = href
                            console.print(f"[yellow]Job {job_number}: Using first non-search link: {href[:60]}[/yellow]")
                            break

            if not title_link:
                console.print(f"[yellow]Job {job_number}: No clickable job link found[/yellow]")
                return ""

            # Method 1: Try to get a direct, absolute URL from href first
            if href_url and href_url.startswith("http") and "eluta.ca" not in href_url:
                console.print(f"[green]Job {job_number}: Found direct external URL: {href_url[:60]}[/green]")
                return href_url

            # Method 2: If it's a relative URL or redirect, try to resolve it
            if href_url:
                if href_url.startswith("/redirect") or "redirect" in href_url:
                    # This is an Eluta redirect - convert to absolute URL
                    if href_url.startswith("/"):
                        base_url = "https://www.eluta.ca"
                        full_url = base_url + href_url
                        console.print(f"[cyan]Job {job_number}: Eluta redirect URL: {full_url[:60]}[/cyan]")
                        return full_url
                    else:
                        console.print(f"[cyan]Job {job_number}: Using redirect URL: {href_url[:60]}[/cyan]")
                        return href_url
                elif href_url.startswith("/") and not any(skip in href_url for skip in ["/search?", "q=", "pg="]):
                    # Convert relative job URL to absolute
                    base_url = "https://www.eluta.ca"
                    full_url = base_url + href_url
                    console.print(f"[cyan]Job {job_number}: Converted to absolute job URL: {full_url[:60]}[/cyan]")
                    return full_url

            # Method 3: Fallback to clicking and expecting a popup (original method)
            console.print(f"[cyan]Job {job_number}: Using popup method as fallback...[/cyan]")
            async with page.expect_popup() as popup_info:
                await title_link.click()
                await asyncio.sleep(2)  # Give popup time to load and potentially redirect
            popup = await popup_info.value
            await popup.wait_for_load_state()
            real_url = popup.url
            await popup.close()
            return real_url

        except Exception as e:
            console.print(f"[red]Error getting real job URL for job {job_number}: {e}[/red]")
            # Attempt to click as a last resort without popup expectation
            try:
                if title_link:
                    await title_link.click()
                    await asyncio.sleep(3) # Wait for navigation
                    return page.url # Return current page url
            except Exception as final_e:
                 console.print(f"[red]Final attempt to get URL failed: {final_e}[/red]")
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
        try:
            refine_page = await context.new_page()
            console.print(f"[cyan]Refining redirect URL: {url[:70]}...[/cyan]")
            
            # Navigate and wait for final destination
            await refine_page.goto(url, wait_until="networkidle", timeout=15000)
            await asyncio.sleep(3)  # Extra wait for client-side redirects
            
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

        # Save to database
        if jobs:
            console.print(f"\n[cyan]Saving {len(jobs)} entry-level jobs to database...[/cyan]")
            saved_count = 0
            for job in jobs:
                try:
                    self.db.add_job(job)
                    saved_count += 1
                except Exception as e:
                    console.print(f"[yellow]Could not save job: {e}[/yellow]")

            console.print(f"[green]Saved {saved_count} jobs to database[/green]")


# Convenience function
async def run_comprehensive_scraping(
    profile_name: str = "Nirajan", max_jobs_per_keyword: int = 30
) -> List[Dict]:
    """Run comprehensive Eluta scraping."""
    scraper = ComprehensiveElutaScraper(profile_name)
    return await scraper.scrape_all_keywords(max_jobs_per_keyword)


if __name__ == "__main__":
    asyncio.run(run_comprehensive_scraping())
