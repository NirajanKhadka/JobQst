#!/usr/bin/env python3
"""
Working Eluta Scraper - Based on Proven Site Analysis
This scraper uses the proven method discovered through actual site analysis:
1. Find .organic-job containers
2. Extract job data from text content  
3. Click on job title links
4. Use expect_popup() to capture new tab URLs
5. Extract real ATS application URLs

This replaces the complex eluta_enhanced.py with a simple, working approach.
"""

import re
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Generator, List, Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright
from rich.console import Console

from .base_scraper import BaseJobScraper
from .human_behavior import HumanBehaviorMixin
from .job_filters import UniversalJobFilter
from src.scrapers.tab_manager import TabManager

console = Console()

# Import job analyzer for enhanced analysis
try:
    from src.utils.job_analyzer import JobAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    console.print("[yellow]⚠️ Job analyzer not available - basic analysis only[/yellow]")


class ElutaWorkingScraper(HumanBehaviorMixin, BaseJobScraper):
    """
    Working Eluta scraper based on proven site analysis.
    Uses the simple .organic-job + expect_popup() method.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        # Extract our custom parameters before passing to base class
        self.max_jobs_per_keyword = kwargs.pop("max_jobs_per_keyword", 50)  # Increased limit
        self.max_keywords = kwargs.pop("max_keywords", None)  # No limit by default
        self.max_pages_per_keyword = kwargs.pop("max_pages_per_keyword", 5)  # Enhanced pagination - minimum 5 pages as per memories
        self.enable_deep_analysis = kwargs.pop("enable_deep_analysis", True)  # Enable job analysis

        # Initialize base scraper with remaining kwargs
        super().__init__(profile, **kwargs)

        # Initialize job analyzer if available
        if ANALYZER_AVAILABLE and self.enable_deep_analysis:
            self.job_analyzer = JobAnalyzer(use_ai=True)
            console.print("[green]✅ Job analyzer enabled for enhanced analysis[/green]")
        else:
            self.job_analyzer = None
            console.print("[yellow]⚠️ Job analyzer disabled - basic analysis only[/yellow]")

        self.site_name = "eluta_working"
        self.base_url = "https://www.eluta.ca/search"
        self.requires_browser = True

        # Store keywords for searching
        self.keywords = profile.get("keywords", [])

        # Simple, effective delays
        self.page_delay = (2, 4)
        self.click_delay = (1, 2)

        # Date filtering - last 14 days (optimized range)
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

        # Enhanced human-like behavior settings as per memories
        self.human_delays = {
            "page_load": (2.0, 4.0),      # Wait after page loads
            "between_jobs": (1.0, 2.0),   # Wait between job clicks (1-second delays as per memories)
            "between_pages": (2.0, 4.0),  # Wait between pages
            "popup_wait": 3.0,            # Fixed 3-second wait for popups as per memories
            "pre_click": (0.2, 0.5),      # Wait before clicking
            "post_hover": (0.1, 0.3),     # Wait after hovering
            "keyword_switch": (2.0, 4.0)  # Wait between keywords
        }

        # Limit keywords only if max_keywords is specified
        if self.max_keywords and len(self.keywords) > self.max_keywords:
            self.keywords = self.keywords[:self.max_keywords]
            console.print(f"[yellow]⚠️ Limited to first {self.max_keywords} keywords[/yellow]")

        # Initialize universal job filter (14 days for Eluta, 0-2 years experience)
        self.job_filter = UniversalJobFilter("eluta")

        self.tab_manager = TabManager(popup_wait=self.human_delays["popup_wait"])

        console.print(f"[green]✅ Working Eluta scraper initialized with enhanced filtering[/green]")
        console.print(f"[cyan]📅 Filtering jobs from last {self.max_age_days} days[/cyan]")
        console.print(f"[cyan]🔍 Will search {len(self.keywords)} keywords[/cyan]")
        console.print(f"[cyan]🎯 Max {self.max_jobs_per_keyword} jobs per keyword[/cyan]")
        console.print(f"[cyan]📄 Max {self.max_pages_per_keyword} pages per keyword[/cyan]")
    
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """Scrape jobs using the proven working method."""
        if not self.browser_context:
            console.print("[red]❌ Browser context required[/red]")
            return
        
        console.print(f"\n[bold green]🚀 Starting Working Eluta scraping session[/bold green]")
        
        page = self.browser_context.new_page()
        
        # Basic stealth setup
        self._setup_basic_stealth(page)
        
        try:
            # Search each keyword
            for keyword_index, keyword in enumerate(self.keywords, 1):
                console.print(f"\n[bold blue]🔍 Keyword {keyword_index}/{len(self.keywords)}: '{keyword}'[/bold blue]")
                
                # Search this keyword
                for job in self._search_keyword(page, keyword):
                    yield job
                
                # Enhanced delay between keywords using human-like behavior
                if keyword_index < len(self.keywords):
                    self.human_delay("keyword_switch")
        
        finally:
            try:
                page.close()
            except:
                pass
    
    def _setup_basic_stealth(self, page: Page) -> None:
        """Setup basic stealth measures."""
        try:
            # Set realistic viewport
            page.set_viewport_size({"width": 1366, "height": 768})
            
            # Set realistic user agent
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            console.print("[green]✅ Basic stealth configured[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Stealth setup failed: {e}[/yellow]")
    
    def _search_keyword(self, page: Page, keyword: str) -> Generator[Dict, None, None]:
        """Search a single keyword with pagination and extract jobs."""
        try:
            # location = self.profile.get("location", "Toronto")  # REMOVE location for Canada-wide
            jobs_processed = 0

            # Search multiple pages for this keyword
            for page_num in range(1, self.max_pages_per_keyword + 1):
                console.print(f"[bold blue]📄 Page {page_num}/{self.max_pages_per_keyword} for keyword '{keyword}'[/bold blue]")

                # Build search URL with pagination (NO location)
                search_url = f"{self.base_url}?q={urllib.parse.quote(keyword)}"
                if page_num > 1:
                    search_url += f"&pg={page_num}"

                console.print(f"[cyan]🌐 Navigating to: {search_url}[/cyan]")

                # Navigate to search page with enhanced human-like behavior
                self.human_page_navigation(page, search_url)

                # Find job containers using proven selector
                job_elements = page.query_selector_all(".organic-job")
                console.print(f"[green]✅ Found {len(job_elements)} job listings on page {page_num}[/green]")

                if not job_elements:
                    console.print(f"[yellow]⚠️ No job listings found on page {page_num}, stopping pagination[/yellow]")
                    break

                # Process each job on this page
                page_jobs_processed = 0
                for i, job_elem in enumerate(job_elements):
                    if jobs_processed >= self.max_jobs_per_keyword:
                        console.print(f"[yellow]⚠️ Reached limit of {self.max_jobs_per_keyword} jobs for keyword '{keyword}'[/yellow]")
                        return

                    console.print(f"[cyan]📋 Processing job {i+1}/{len(job_elements)} (page {page_num})[/cyan]")

                    job_data = self._extract_job_data(job_elem, page, f"{page_num}-{i+1}")
                    if job_data:
                        # Apply universal job filtering (date + experience level)
                        should_include, filtered_job = self.job_filter.filter_job(job_data)
                        if should_include:
                            yield filtered_job
                            jobs_processed += 1
                            page_jobs_processed += 1
                        else:
                            console.print(f"[yellow]⚠️ Job filtered out: {job_data.get('title', 'Unknown')[:40]}...[/yellow]")

                    # Enhanced delay between jobs using human-like behavior (1-second delays as per memories)
                    self.human_delay("between_jobs")

                console.print(f"[green]✅ Page {page_num} completed: {page_jobs_processed} jobs processed[/green]")

                # Check if we should continue to next page
                if page_jobs_processed == 0:
                    console.print(f"[yellow]⚠️ No jobs processed on page {page_num}, stopping pagination[/yellow]")
                    break

                # Enhanced delay between pages using human-like behavior
                if page_num < self.max_pages_per_keyword:
                    self.human_delay("between_pages")

            console.print(f"[bold green]✅ Keyword '{keyword}' completed: {jobs_processed} total jobs across {page_num} pages[/bold green]")

        except Exception as e:
            console.print(f"[red]❌ Error searching keyword '{keyword}': {e}[/red]")
    
    def _extract_job_data(self, job_elem, page: Page, job_number) -> Optional[Dict]:
        """Extract job data using proven method."""
        try:
            # Step 1: Extract basic data from text
            text = job_elem.inner_text().strip()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if len(lines) < 2:
                console.print(f"[yellow]⚠️ Job {job_number}: Insufficient content[/yellow]")
                return None
            
            # Parse job data
            job_data = {
                "title": "",
                "company": "",
                "location": "",
                "salary": "",
                "summary": "",  # Changed from description to summary
                "url": "",
                "apply_url": "",
                "site": self.site_name,  # Use site_name instead of source
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
            
            console.print(f"[cyan]📋 {job_data['title'][:40]}... at {job_data['company']}[/cyan]")
            
            # Step 2: Get real URL using TabManager click-and-popup method
            real_url = self._get_real_job_url(job_elem, page, job_number)
            if real_url:
                job_data["apply_url"] = real_url
                job_data["url"] = real_url
                job_data["ats_system"] = self._detect_ats_system(real_url)
                job_data["deep_scraped"] = True
                console.print(f"[green]✅ Real URL: {real_url[:50]}... ({job_data['ats_system']})[/green]")
            else:
                # Fallback to search page URL
                job_data["url"] = page.url
                job_data["apply_url"] = page.url
                console.print(f"[yellow]⚠️ Using fallback URL[/yellow]")

            # Step 3: Enhanced job analysis if analyzer is available
            if self.job_analyzer:
                try:
                    enhanced_job = self.job_analyzer.analyze_job_deep(job_data, page)

                    # Add match score for this user
                    if "requirements" in enhanced_job:
                        try:
                            from src.utils.job_analyzer import JobRequirements
                            requirements = JobRequirements(**enhanced_job["requirements"])
                            match_score = self.job_analyzer.calculate_job_match_score(requirements, self.profile)
                            enhanced_job["match_score"] = match_score
                            enhanced_job["recommended"] = match_score >= 0.7  # High match threshold

                            console.print(f"[cyan]📊 Match Score: {match_score:.2f} ({'Recommended' if match_score >= 0.7 else 'Consider'})[/cyan]")
                        except ImportError:
                            console.print("[yellow]⚠️ JobRequirements not available - skipping match score[/yellow]")

                    return enhanced_job

                except Exception as e:
                    console.print(f"[yellow]⚠️ Enhanced analysis failed: {e}[/yellow]")
                    # Return basic job data if analysis fails
                    return job_data

            return job_data
            
        except Exception as e:
            console.print(f"[red]❌ Error extracting job {job_number}: {e}[/red]")
            return None
    
    def _get_real_job_url(self, job_elem, page: Page, job_number: int) -> Optional[str]:
        """Get real job URL using TabManager click-and-popup method."""
        try:
            links = job_elem.query_selector_all("a")
            title_link = None
            for link in links:
                link_text = link.inner_text().strip()
                href = link.get_attribute("href") or ""
                if link_text and len(link_text) > 10:
                    if ("/job/" in href or "/direct/" in href or
                        any(keyword in link_text.lower() for keyword in ["analyst", "developer", "engineer", "manager", "specialist"])):
                        title_link = link
                        break
                    elif not title_link:
                        title_link = link
            if not title_link:
                console.print(f"[yellow]⚠️ No title link found for job {job_number}[/yellow]")
                return None
            # Use TabManager for popup/tab and URL extraction
            popup_url = self.tab_manager.click_and_get_popup_url(title_link, page, str(job_number))
            if popup_url:
                return popup_url
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not get real URL for job {job_number}: {e}[/yellow]")
            # Fallback to href
            try:
                links = job_elem.query_selector_all("a")
                if links:
                    href = links[0].get_attribute("href")
                    if href and not href.startswith("#"):
                        fallback_url = href if href.startswith("http") else f"https://www.eluta.ca{href}"
                        console.print(f"[cyan]📎 Using fallback href: {fallback_url[:60]}...[/cyan]")
                        return fallback_url
            except:
                pass
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
