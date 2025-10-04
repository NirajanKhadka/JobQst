#!/usr/bin/env python3
"""
Eluta Job Scraper - Single Unified Implementation

This is the ONLY Eluta scraper for AutoJobAgent. It follows development standards:
- Single responsibility: Scrapes Eluta.ca job listings and saves to database
- Clean architecture: Separates scraping logic from data persistence
- Error handling: Graceful failure with detailed logging
- Performance: Optimized tab management and concurrent processing
- Maintainability: Clear, documented code under 500 lines

Features:
- Scrapes job URLs, titles, companies, locations from Eluta.ca
- Saves all data to database with proper status tracking
- Handles popups, tabs, and anti-bot measures
- Configurable pages, jobs per keyword, and processing options
- Real-time progress reporting and statistics
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel
from rich.table import Table
from playwright.async_api import async_playwright, Browser

from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile
from src.utils.simple_url_filter import get_simple_url_filter
from src.ats.ats_utils import detect_ats_system

console = Console()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class ElutaScraper:
    """
    Single Eluta scraper implementation following development standards.

    Responsibilities:
    - Scrape job listings from Eluta.ca
    - Extract job URLs, titles, companies, locations
    - Save all data to database with proper status
    - Handle browser automation and anti-bot measures

    Args:
        profile_name: User profile name for database and keywords
        config: Optional configuration dictionary
    """

    def __init__(self, profile_name: str = "Nirajan", config: Optional[Dict] = None):
        """Initialize the Eluta scraper with profile and configuration."""
        self.profile_name = profile_name
        self.profile = load_profile(profile_name)
        if not self.profile:
            raise ValueError(f"Profile '{profile_name}' not found!")

        self.db = get_job_db(profile_name)
        self.keywords = self.profile.get("keywords", [])
        self.url_filter = get_simple_url_filter()

        # Configuration with sensible defaults
        self.base_url = "https://www.eluta.ca/search"
        self.max_pages_per_keyword = config.get("pages", 5) if config else 5
        self.max_jobs_per_keyword = config.get("jobs", 20) if config else 20
        self.delay_between_requests = config.get("delay", 1.0) if config else 1.0
        self.headless = config.get("headless", False) if config else False
        self.max_tabs_threshold = config.get("max_tabs", 5) if config else 5

        # Results tracking
        self.processed_urls = set()
        self.stats = {
            "keywords_total": len(self.keywords),
            "keywords_processed": 0,
            "pages_scraped": 0,
            "jobs_found": 0,
            "jobs_saved": 0,
            "duplicates_skipped": 0,
            "french_jobs_skipped": 0,
            "senior_jobs_skipped": 0,
            "tabs_closed": 0,
            "extraction_failures": 0,
            "url_extraction_failures": 0,
            "title_extraction_failures": 0,
            "start_time": None,
            "end_time": None,
        }

        logger.info(
            f"ElutaScraper initialized for profile '{profile_name}' with {len(self.keywords)} keywords"
        )

    async def scrape_all_keywords(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Main scraping method that processes all keywords and saves jobs to database.

        Args:
            limit: Optional limit on jobs per keyword (overrides config)

        Returns:
            List of scraped job dictionaries
        """
        self.stats["start_time"] = datetime.now()
        max_jobs = limit or self.max_jobs_per_keyword

        console.print(Panel.fit("🚀 ELUTA JOB SCRAPER", style="bold blue"))
        console.print(f"[cyan]📋 Keywords: {len(self.keywords)}[/cyan]")
        console.print(f"[cyan]📄 Pages per keyword: {self.max_pages_per_keyword}[/cyan]")
        console.print(f"[cyan]🎯 Jobs per keyword: {max_jobs}[/cyan]")
        console.print(f"[cyan]🌐 Headless mode: {'✅' if self.headless else '❌'}[/cyan]")

        all_jobs = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)

            try:
                with Progress() as progress:
                    main_task = progress.add_task(
                        "[green]Processing keywords...", total=len(self.keywords)
                    )

                    for keyword in self.keywords:
                        console.print(f"\n[bold]🔍 Processing keyword: {keyword}[/bold]")

                        keyword_jobs = await self._scrape_keyword(keyword, browser, max_jobs)
                        all_jobs.extend(keyword_jobs)

                        # Save jobs to database immediately
                        self._save_jobs_to_database(keyword_jobs)

                        self.stats["keywords_processed"] += 1
                        progress.update(main_task, advance=1)

                        # Brief delay between keywords
                        await asyncio.sleep(self.delay_between_requests)

            finally:
                await browser.close()

        self.stats["end_time"] = datetime.now()
        self._display_final_summary(all_jobs)

        return all_jobs

    async def _scrape_keyword(self, keyword: str, browser: Browser, max_jobs: int) -> List[Dict]:
        """
        Scrape jobs for a single keyword with proper tab management.

        Args:
            keyword: Search keyword
            browser: Playwright browser instance
            max_jobs: Maximum jobs to scrape for this keyword

        Returns:
            List of job dictionaries
        """
        results = []
        context = None

        try:
            # Create fresh context for each keyword
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            # Set up popup and dialog handlers
            self._setup_context_handlers(context)

            page = await context.new_page()

            # Inject anti-popup scripts
            await self._inject_anti_popup_scripts(page)

            # Scrape multiple pages for this keyword
            for page_num in range(1, self.max_pages_per_keyword + 1):
                if len(results) >= max_jobs:
                    break

                try:
                    page_jobs = await self._scrape_page(
                        page, keyword, page_num, max_jobs - len(results)
                    )
                    results.extend(page_jobs)
                    self.stats["pages_scraped"] += 1

                    # Monitor and cleanup tabs if needed (but allow for job detail tabs)
                    await self._monitor_tab_count(context, len(results))

                except Exception as page_error:
                    logger.warning(
                        f"Error scraping page {page_num} for keyword '{keyword}': {page_error}"
                    )
                    # Continue with next page instead of failing completely
                    continue

        except Exception as e:
            logger.error(f"Error scraping keyword '{keyword}': {e}")
            self.stats["extraction_failures"] += 1

        finally:
            # Ensure context is properly closed
            if context:
                try:
                    await context.close()
                except Exception as close_error:
                    logger.warning(f"Error closing context for keyword '{keyword}': {close_error}")

        console.print(f"[green]✅ Keyword '{keyword}': {len(results)} jobs found[/green]")
        return results

    def _setup_context_handlers(self, context) -> None:
        """Set up popup and dialog handlers for browser context."""
        main_page_url = None

        def on_new_page(new_page):
            try:
                nonlocal main_page_url
                url = new_page.url() if callable(new_page.url) else new_page.url

                # Set the first page as main page
                if main_page_url is None:
                    main_page_url = url
                    logger.info(f"Main page set: {url}")
                    return

                # Only close if it's not the main page and looks like a popup
                if url != main_page_url and (
                    "about:blank" in url or "popup" in url.lower() or url.startswith("javascript:")
                ):
                    logger.info(f"Closing popup/tab: {url}")
                    asyncio.create_task(new_page.close())
                    self.stats["tabs_closed"] += 1
                else:
                    logger.info(f"Keeping page: {url}")
            except Exception as e:
                logger.warning(f"Error handling new page: {e}")

        def on_dialog(dialog):
            try:
                asyncio.create_task(dialog.dismiss())
            except Exception:
                pass

        context.on("page", on_new_page)
        context.on("page", lambda p: p.on("dialog", on_dialog))

    async def _inject_anti_popup_scripts(self, page) -> None:
        """Inject JavaScript to handle target="_blank" but allow job navigation."""
        await page.add_init_script(
            """
            // Remove target="_blank" from links after page loads to prevent unwanted popups
            // but don't block window.open as Eluta uses it for job navigation
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(function() {
                    var links = document.querySelectorAll('a[target="_blank"]');
                    links.forEach(function(link) { 
                        link.removeAttribute('target'); 
                    });
                }, 1000);
            });
        """
        )

    async def _scrape_page(self, page, keyword: str, page_num: int, max_jobs: int) -> List[Dict]:
        """
        Scrape jobs from a single page with improved error handling.

        Args:
            page: Playwright page instance
            keyword: Search keyword
            page_num: Page number
            max_jobs: Maximum jobs to extract from this page

        Returns:
            List of job dictionaries from this page
        """
        search_url = f"{self.base_url}?q={keyword.replace(' ', '+')}+sort%3Arank&page={page_num}"

        try:
            # Navigate to page with retries
            for attempt in range(3):
                try:
                    await page.goto(search_url, wait_until="networkidle", timeout=30000)
                    break
                except Exception as nav_error:
                    if attempt == 2:
                        raise nav_error
                    logger.warning(f"Navigation attempt {attempt + 1} failed: {nav_error}")
                    await asyncio.sleep(2)

            # Handle popups and remove target="_blank"
            await self._handle_page_interactions(page)
            await asyncio.sleep(self.delay_between_requests)

            # Find job elements
            job_elements = await self._find_job_elements(page)
            console.print(
                f"[cyan]📄 Page {page_num}: Found {len(job_elements)} job elements[/cyan]"
            )

            if not job_elements:
                logger.warning(f"No job elements found on page {page_num} for keyword '{keyword}'")
                return []

            # Extract job data
            page_jobs = []
            extraction_attempts = 0
            successful_extractions = 0

            for i, job_element in enumerate(job_elements[:max_jobs]):
                extraction_attempts += 1
                try:
                    job_data = await self._extract_job_data_with_page(
                        job_element, keyword, page_num, page
                    )
                    if job_data and self._is_valid_job(job_data):
                        page_jobs.append(job_data)
                        successful_extractions += 1
                        self.stats["jobs_found"] += 1
                        console.print(
                            f"[green]✓ Extracted: {job_data['title']} at {job_data['company']}[/green]"
                        )
                    else:
                        logger.debug(f"Job data validation failed for element {i}")
                except Exception as extract_error:
                    logger.warning(f"Error extracting job {i}: {extract_error}")
                    continue

            console.print(
                f"[cyan]📊 Page {page_num}: {successful_extractions}/{extraction_attempts} jobs extracted successfully[/cyan]"
            )
            return page_jobs

        except Exception as e:
            logger.error(f"Error scraping page {page_num} for keyword '{keyword}': {e}")
            return []

    async def _handle_page_interactions(self, page) -> None:
        """Handle page interactions like popups, dialogs, and target="_blank" removal."""
        try:
            # Remove target="_blank" attributes
            await self._remove_target_blank(page)

            # Handle any dialogs that might appear
            try:
                # Wait briefly for any dialogs to appear
                await asyncio.sleep(1)

                # Check for common popup/modal selectors and close them
                popup_selectors = [
                    ".modal",
                    ".popup",
                    ".overlay",
                    ".dialog",
                    "[role='dialog']",
                    ".close-button",
                    ".modal-close",
                ]

                for selector in popup_selectors:
                    try:
                        popup = await page.query_selector(selector)
                        if popup:
                            # Try to find and click close button
                            close_btn = await popup.query_selector(
                                ".close, .x, [aria-label='close']"
                            )
                            if close_btn:
                                await close_btn.click()
                                logger.info(f"Closed popup with selector: {selector}")
                            else:
                                # Try to click outside the popup
                                await page.click("body")
                    except Exception:
                        continue

            except Exception as popup_error:
                logger.debug(f"Popup handling error: {popup_error}")

        except Exception as e:
            logger.warning(f"Error handling page interactions: {e}")

    async def _remove_target_blank(self, page) -> None:
        """Remove target='_blank' attributes to prevent new tabs."""
        await page.evaluate(
            """
            var links = document.querySelectorAll('a[target="_blank"]');
            links.forEach(function(link) { link.removeAttribute('target'); });
        """
        )

    async def _monitor_tab_count(self, context, job_count: int) -> None:
        """Monitor and cleanup tabs when threshold is reached (more lenient for job extraction)."""
        try:
            pages = context.pages
            extra_tabs = len(pages) - 1  # Subtract main page

            # Increase threshold since we're intentionally opening job detail tabs
            cleanup_threshold = self.max_tabs_threshold * 2  # Double the threshold

            if extra_tabs >= cleanup_threshold:
                console.print(
                    f"[yellow]🧹 Cleaning up {extra_tabs} extra tabs (threshold: {cleanup_threshold})[/yellow]"
                )

                tabs_closed = 0
                for page in pages[1:]:  # Skip main page
                    try:
                        if not page.is_closed():
                            await page.close()
                            tabs_closed += 1
                            self.stats["tabs_closed"] += 1
                    except Exception as e:
                        logger.warning(f"Error closing tab: {e}")

        except Exception as e:
            logger.warning(f"Tab monitoring error: {e}")

    async def _find_job_elements(self, page) -> List:
        """Find job elements using multiple selectors for reliableness."""
        # Wait for content to load
        try:
            await page.wait_for_selector("body", timeout=10000)
            await asyncio.sleep(2)  # Give time for dynamic content
        except Exception:
            pass

        # Try multiple selectors to find job elements - updated for current Eluta structure
        selectors = [
            # Modern Eluta selectors
            ".job-tile",
            ".job-card",
            ".job-listing",
            ".job-item",
            ".search-result",
            ".result-item",
            # Generic selectors
            "[data-job]",
            ".organic-job",
            ".job-result",
            ".result",
            "article",
            # Fallback - look for any clickable elements with job-like content
            "a[href*='job']",
            "div[class*='job']",
            "li[class*='job']",
            # Last resort - headings that might contain job titles
            "h2, h3, h4",
        ]

        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    return elements
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        # If no elements found, try to get page content for debugging
        try:
            page_content = await page.content()
            if "job" in page_content.lower():
                logger.warning("Page contains 'job' text but no job elements found with selectors")
                # Try to find any div or article elements as last resort
                elements = await page.query_selector_all("div, article, li")
                if elements:
                    logger.info(f"Using fallback: found {len(elements)} generic elements")
                    return elements[:20]  # Limit to first 20 to avoid processing too many
        except Exception as e:
            logger.warning(f"Error getting page content: {e}")

        logger.warning("No job elements found with any selector")
        return []

    async def _extract_job_data_with_page(
        self, job_element, keyword: str, page_num: int, page
    ) -> Optional[Dict]:
        """
        Extract job data from a job element with click-and-capture URL extraction.

        Args:
            job_element: Playwright element handle
            keyword: Search keyword
            page_num: Page number
            page: Playwright page instance for click-and-capture

        Returns:
            Job data dictionary or None if extraction fails
        """
        try:
            # Debug: Log the element text content
            try:
                element_text = await job_element.inner_text()
                logger.debug(f"Element text: {element_text[:200]}...")
            except Exception:
                pass

            # Get job title first (needed for validation)
            job_title = await self._extract_job_title(job_element)
            if not job_title or len(job_title.strip()) < 3:
                logger.warning(f"Invalid job title: '{job_title}', skipping")
                return None

            # Extract job URL using click-and-capture method
            job_url = await self._extract_job_url(job_element, page)
            if not job_url:
                logger.warning("No job URL found, skipping element")
                return None

            # Extract additional info from container
            container_text = await self._get_container_text(job_element)
            company, location, salary = self._parse_container_text(container_text)

            # Create job data
            job_data = {
                "title": job_title.strip(),
                "company": company or "Unknown",
                "location": location or "Unknown",
                "salary": salary or "",
                "url": job_url,
                "ats_system": (
                    detect_ats_system(job_url)
                    if not job_url.startswith("eluta-job://")
                    else "unknown"
                ),
                "search_keyword": keyword,
                "scraped_date": datetime.now().isoformat(),
                "page_number": page_num,
                "source": "eluta.ca",
                "status": "scraped",
            }

            logger.info(f"Successfully extracted job: {job_title} at {company} - {job_url}")
            return job_data

        except Exception as e:
            logger.error(f"Error extracting job data: {e}")
            self.stats["extraction_failures"] += 1
            return None

    async def _extract_job_title(self, job_element) -> Optional[str]:
        """Extract job title using multiple methods with debugging."""
        try:
            # Method 1: Look for title in common selectors
            title_selectors = [
                "h2",
                "h3",
                "h4",
                ".title",
                ".job-title",
                ".position",
                ".role",
                "a",
                ".link",
            ]

            for selector in title_selectors:
                try:
                    title_element = await job_element.query_selector(selector)
                    if title_element:
                        title = await title_element.inner_text()
                        if title and len(title.strip()) > 3:
                            logger.debug(f"Found title via {selector}: {title.strip()}")
                            return title.strip()
                except Exception:
                    continue

            # Method 2: Get text from the element itself
            element_text = await job_element.inner_text()
            if element_text:
                # Take the first line as title if it looks like a job title
                lines = [line.strip() for line in element_text.split("\n") if line.strip()]
                if lines:
                    first_line = lines[0]
                    if len(first_line) > 3 and len(first_line) < 100:
                        logger.debug(f"Found title via first line: {first_line}")
                        return first_line

            # Method 3: Look for text in link elements
            links = await job_element.query_selector_all("a")
            for link in links:
                try:
                    link_text = await link.inner_text()
                    if link_text and 5 < len(link_text.strip()) < 100:
                        logger.debug(f"Found title via link text: {link_text.strip()}")
                        return link_text.strip()
                except Exception:
                    continue

            # Debug: Log element content if no title found
            try:
                element_text = await job_element.inner_text()
                logger.debug(f"No title found for element with text: {element_text[:100]}...")
            except Exception:
                pass

            self.stats["title_extraction_failures"] += 1
            return None

        except Exception as e:
            logger.debug(f"Error extracting job title: {e}")
            self.stats["title_extraction_failures"] += 1
            return None

    async def _extract_job_url(self, job_element, page) -> Optional[str]:
        """
        Extract actual job URL by clicking and capturing the new tab URL.
        This is the proven method for Eluta since they use JavaScript navigation.
        """
        try:
            # Find the clickable job title link
            title_link = await job_element.query_selector("h2 a")
            if not title_link:
                logger.debug("No clickable title link found")
                self.stats["url_extraction_failures"] += 1
                return None

            # Get current number of pages to detect new tab
            context = page.context
            initial_pages = len(context.pages)

            # Click the job title link
            await title_link.click()
            await asyncio.sleep(3)  # Wait for new tab to open

            # Check if a new tab opened
            current_pages = context.pages
            if len(current_pages) > initial_pages:
                # New tab opened - get the URL
                new_page = current_pages[-1]  # Last page is the new one

                # Wait for the page to load
                try:
                    await new_page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    await asyncio.sleep(2)  # Fallback wait

                # Get the actual job URL
                actual_url = new_page.url
                logger.info(f"Captured job URL from new tab: {actual_url}")

                # Close the new tab immediately
                try:
                    await new_page.close()
                    self.stats["tabs_closed"] += 1
                    logger.debug("Closed job details tab")
                except Exception as e:
                    logger.warning(f"Error closing tab: {e}")

                # Validate and return the URL
                if (
                    actual_url
                    and actual_url != "about:blank"
                    and "eluta.ca" not in actual_url.lower()
                ):
                    return actual_url
                else:
                    logger.warning(f"Invalid URL captured: {actual_url}")
                    self.stats["url_extraction_failures"] += 1
                    return None

            else:
                logger.warning("No new tab opened after click")
                self.stats["url_extraction_failures"] += 1
                return None

        except Exception as e:
            logger.error(f"Error extracting job URL: {e}")
            self.stats["url_extraction_failures"] += 1
            return None

    def _normalize_url(self, href: str) -> Optional[str]:
        """Normalize and validate URL."""
        if not href:
            return None

        # Clean up the URL
        href = href.strip()

        # Handle onclick JavaScript
        if "onclick" in href.lower() or "javascript:" in href.lower():
            # Try to extract URL from JavaScript
            import re

            url_match = re.search(r'https?://[^\s\'"]+', href)
            if url_match:
                href = url_match.group(0)
            else:
                return None

        # Convert relative URLs to absolute
        if href.startswith("/"):
            return f"https://www.eluta.ca{href}"
        elif href.startswith("http"):
            return href
        elif href.startswith("www."):
            return f"https://{href}"
        else:
            # Try to construct URL if it looks like a path
            if "/" in href and not href.startswith("mailto:"):
                return f"https://www.eluta.ca/{href.lstrip('/')}"
            return None

    async def _get_container_text(self, job_element) -> str:
        """Get text from job container for parsing."""
        try:
            # Try to find parent container with more info
            container = job_element
            for _ in range(3):  # Look up to 3 levels up
                parent = await container.query_selector("..")
                if not parent:
                    break
                container = parent

            return await container.inner_text()
        except Exception:
            return ""

    def _parse_container_text(self, container_text: str) -> tuple:
        """Parse container text to extract company, location, salary with improved logic."""
        lines = [line.strip() for line in container_text.split("\n") if line.strip()]

        company = ""
        location = ""
        salary = ""

        # Common patterns for Eluta job listings
        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Skip the job title (usually first line)
            if i == 0:
                continue

            # Company detection - usually second line, avoid certain patterns
            if (
                not company
                and len(line) > 2
                and len(line) < 100
                and not any(
                    skip in line_lower
                    for skip in [
                        "posted",
                        "ago",
                        "days",
                        "salary",
                        "$",
                        "apply",
                        "view",
                        "click",
                        "hours",
                        "minutes",
                        "seconds",
                        "top employer",
                        "featured",
                    ]
                )
                and
                # Look for company indicators
                (
                    any(indicator in line for indicator in ["Inc.", "Ltd.", "Corp.", "LLC", "Co."])
                    or (len(line) > 5 and not any(char.isdigit() for char in line[:10]))
                )
            ):
                company = line.replace("TOP EMPLOYER", "").strip()

            # Location detection (Canadian provinces and major cities)
            elif not location and (
                any(
                    prov in line.upper()
                    for prov in ["ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB", "PE", "NL"]
                )
                or any(
                    city in line
                    for city in [
                        "Toronto",
                        "Montreal",
                        "Vancouver",
                        "Calgary",
                        "Ottawa",
                        "Edmonton",
                        "Winnipeg",
                        "Quebec",
                    ]
                )
            ):
                location = line

            # Salary detection
            elif not salary and (
                "$" in line
                or any(
                    word in line_lower for word in ["salary", "wage", "hourly", "/hour", "/year"]
                )
            ):
                salary = line

        # Fallback: if no company found, try to get it from a different pattern
        if not company and len(lines) > 1:
            # Sometimes company is in the second line
            potential_company = lines[1]
            if (
                len(potential_company) > 2
                and len(potential_company) < 100
                and not any(
                    skip in potential_company.lower() for skip in ["posted", "ago", "days", "$"]
                )
            ):
                company = potential_company.replace("TOP EMPLOYER", "").strip()

        return company, location, salary

    def _is_valid_job(self, job_data: Dict) -> bool:
        """Validate job data before saving."""
        if not job_data.get("url"):
            return False

        if not job_data.get("title"):
            return False

        # Check for duplicates
        if job_data["url"] in self.processed_urls:
            self.stats["duplicates_skipped"] += 1
            return False

        # Skip French language jobs (more precise detection)
        title_lower = job_data.get("title", "").lower()
        company_lower = job_data.get("company", "").lower()
        location_lower = job_data.get("location", "").lower()

        # Check for strong French indicators
        is_french = False

        # Strong French indicators in title (exact word matches)
        french_title_words = [
            "gestionnaire",
            "coordonnateur",
            "spécialiste",
            "conseiller",
            "ingénieur",
        ]
        if any(f" {word} " in f" {title_lower} " for word in french_title_words):
            is_french = True

        # French-specific terms
        if any(term in title_lower for term in ["français", "francais", "québécois"]):
            is_french = True

        # Quebec/Montreal locations - skip all jobs in these cities
        if any(
            location in location_lower
            for location in ["québec", "quebec", "quebec city", "montréal", "montreal"]
        ):
            is_french = True

        # Skip if title is primarily in French (contains French words but no English equivalent)
        if "développeur" in title_lower and "developer" not in title_lower:
            is_french = True

        if is_french:
            logger.info(f"Skipping French job: {job_data['title']}")
            self.stats["french_jobs_skipped"] = self.stats.get("french_jobs_skipped", 0) + 1
            return False

        # Skip senior/lead positions
        senior_indicators = [
            "senior",
            "lead",
            "principal",
            "staff",
            "architect",
            "director",
            "manager",
            "head of",
        ]

        if any(indicator in title_lower for indicator in senior_indicators):
            logger.info(f"Skipping senior/lead job: {job_data['title']}")
            self.stats["senior_jobs_skipped"] = self.stats.get("senior_jobs_skipped", 0) + 1
            return False

        # Validate URL (must be a real HTTP URL)
        if not (
            job_data["url"].startswith("http") and self.url_filter.is_valid_job_url(job_data["url"])
        ):
            return False

        self.processed_urls.add(job_data["url"])
        return True

    def _save_jobs_to_database(self, jobs: List[Dict]) -> None:
        """Save jobs to database with error handling."""
        for job in jobs:
            try:
                self.db.add_job(job)
                self.stats["jobs_saved"] += 1
                logger.debug(f"Saved job: {job['title']} at {job['company']}")
            except Exception as e:
                logger.error(f"Error saving job to database: {e}")
                # Continue with other jobs even if one fails

    def _display_final_summary(self, jobs: List[Dict]) -> None:
        """Display final scraping summary with statistics."""
        elapsed_time = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        jobs_per_minute = (len(jobs) / (elapsed_time / 60)) if elapsed_time > 0 else 0

        console.print("\n" + "=" * 80)
        console.print(Panel.fit("🎉 ELUTA SCRAPER COMPLETED", style="bold green"))

        # Statistics table
        stats_table = Table(title="Scraping Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        stats_table.add_row("Keywords Processed", str(self.stats["keywords_processed"]))
        stats_table.add_row("Pages Scraped", str(self.stats["pages_scraped"]))
        stats_table.add_row("Jobs Found", str(self.stats["jobs_found"]))
        stats_table.add_row("Jobs Saved", str(self.stats["jobs_saved"]))
        stats_table.add_row("Duplicates Skipped", str(self.stats["duplicates_skipped"]))
        stats_table.add_row("French Jobs Skipped", str(self.stats.get("french_jobs_skipped", 0)))
        stats_table.add_row("Senior Jobs Skipped", str(self.stats.get("senior_jobs_skipped", 0)))
        stats_table.add_row(
            "URL Extraction Failures", str(self.stats.get("url_extraction_failures", 0))
        )
        stats_table.add_row(
            "Title Extraction Failures", str(self.stats.get("title_extraction_failures", 0))
        )
        stats_table.add_row("Tabs Closed", str(self.stats["tabs_closed"]))
        stats_table.add_row("Processing Time", f"{elapsed_time:.1f}s")
        stats_table.add_row("Jobs per Minute", f"{jobs_per_minute:.1f}")

        console.print(stats_table)

        # Sample jobs table
        if jobs:
            console.print(f"\n[bold]📋 Sample Jobs (showing first 5):[/bold]")
            sample_table = Table()
            sample_table.add_column("Title", style="green", max_width=30)
            sample_table.add_column("Company", style="cyan", max_width=20)
            sample_table.add_column("Location", style="yellow", max_width=15)
            sample_table.add_column("ATS", style="magenta", max_width=10)

            for job in jobs[:5]:
                sample_table.add_row(
                    (
                        job.get("title", "Unknown")[:27] + "..."
                        if len(job.get("title", "")) > 30
                        else job.get("title", "Unknown")
                    ),
                    (
                        job.get("company", "Unknown")[:17] + "..."
                        if len(job.get("company", "")) > 20
                        else job.get("company", "Unknown")
                    ),
                    (
                        job.get("location", "Unknown")[:12] + "..."
                        if len(job.get("location", "")) > 15
                        else job.get("location", "Unknown")
                    ),
                    (
                        job.get("ats_system", "Unknown")[:7] + "..."
                        if len(job.get("ats_system", "")) > 10
                        else job.get("ats_system", "Unknown")
                    ),
                )

            console.print(sample_table)

        console.print(
            f"\n[bold green]✅ Successfully scraped {len(jobs)} jobs and saved to database![/bold green]"
        )
        logger.info(f"Scraping completed: {len(jobs)} jobs processed in {elapsed_time:.1f}s")


# Entry point functions for compatibility
async def run_unified_eluta_scraper(profile_name: str, config: Optional[Dict] = None) -> List[Dict]:
    """
    Main entry point for running the Eluta scraper.

    Args:
        profile_name: Profile name for scraping
        config: Optional configuration dictionary

    Returns:
        List of scraped job dictionaries
    """
    scraper = ElutaScraper(profile_name, config)
    return await scraper.scrape_all_keywords()


async def run_core_eluta_scraper(profile_name: str, config: Optional[Dict] = None) -> List[Dict]:
    """
    Compatibility entry point for core scraper calls.

    Args:
        profile_name: Profile name for scraping
        config: Optional configuration dictionary

    Returns:
        List of scraped job dictionaries
    """
    return await run_unified_eluta_scraper(profile_name, config)


# Main function removed - use scraper class directly


class UnifiedElutaScraper(ElutaScraper):
    """Backward-compat alias for ElutaScraper used in older tests."""

    pass
