
#!/usr/bin/env python3
"""
OFFICIAL ELUTA SCRAPER CLI ENTRYPOINT
Unified Eluta Scraper (Main CLI)
- Scrapes Eluta job links and basic info for each keyword in the user profile
- Robust tab/popup handling, concurrency, deduplication, and flexible CLI
- Extracts: job URL, title, company, location, salary, description
- Optional entry-level filter and output to CSV/JSON
- This is the only supported Eluta CLI scraper. All other Eluta scrapers are deprecated.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging
from rich.console import Console
from playwright.async_api import async_playwright, Browser

from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile
from src.utils.simple_url_filter import get_simple_url_filter

console = Console()
logger = logging.getLogger("eluta_scraper")
logging.basicConfig(level=logging.INFO)


class UnifiedElutaScraper:
    """
    Unified Eluta Scraper (Merged, Enhanced, No AI)
    - Scrapes Eluta job links and basic info for each keyword in the user profile.
    - Robust tab/popup handling, concurrency, deduplication, and flexible CLI.
    - Extracts: job URL, title, company, location, salary, description.
    - Optional entry-level filter and output to CSV/JSON.
    """
    def __init__(self, profile_name: str = "Nirajan", config: Optional[Dict] = None):
        self.profile_name = profile_name
        self.profile = load_profile(profile_name)
        if not self.profile:
            raise ValueError(f"Profile '{profile_name}' not found!")
        self.db = get_job_db(profile_name)
        self.keywords = self.profile.get("keywords", [])
        self.url_filter = get_simple_url_filter()
        self.base_url = "https://www.eluta.ca/search"
        self.max_pages_per_keyword = config.get("pages", 5) if config else 5
        self.max_jobs_per_keyword = config.get("jobs", 20) if config else 20
        self.delay_between_requests = config.get("delay", 0.5) if config else 0.5
        self.headless = config.get("headless", False) if config else False
        self.workers = config.get("workers", 2) if config else 2
        self.output_file = config.get("output", None) if config else None
        self.entry_level_only = config.get("entry_level", False) if config else False
        self.processed_urls = set()
        self.stats = {
            "keywords": len(self.keywords),
            "keywords_processed": 0,
            "pages_scraped": 0,
            "jobs_found": 0,
            "jobs_saved": 0,
            "duplicates_skipped": 0,
            "tabs_closed": 0,
            "popups_blocked": 0,
            "extraction_failures": 0,
            "tab_cleanups": 0,
            "start_time": None,
            "end_time": None,
        }

    async def scrape_all_keywords(self) -> List[Dict]:
        """
        Scrape job URLs and info for all keywords, with concurrency and deduplication.
        Returns a list of job dicts (URL, title, company, location, salary, description).
        """
        import asyncio
        from rich.progress import Progress
        self.stats["start_time"] = datetime.now()
        all_jobs = []
        sem = asyncio.Semaphore(self.workers)
        progress = Progress()
        task = progress.add_task("[green]Scraping keywords...", total=len(self.keywords))
        async def scrape_keyword_task(keyword):
            jobs = await self._scrape_keyword(keyword, sem)
            all_jobs.extend(jobs)
            self._save_jobs(jobs)
            self.stats["keywords_processed"] += 1
            progress.update(task, advance=1)
        with progress:
            await asyncio.gather(*(scrape_keyword_task(k) for k in self.keywords))
        self.stats["end_time"] = datetime.now()
        elapsed = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        self.stats["jobs_found"] = len(all_jobs)
        self.stats["jobs_per_minute"] = round(len(all_jobs) / (elapsed / 60), 2) if elapsed > 0 else 0
        self._print_summary(all_jobs)
        if self.output_file:
            self._save_output_file(all_jobs)
        return all_jobs

    async def _scrape_keyword(self, keyword: str, sem: asyncio.Semaphore) -> List[Dict]:
        """
        Scrape job URLs and info for a single keyword using a fresh browser instance.
        Robustly closes all popups/tabs by attaching event listeners before navigation.
        """
        import asyncio
        results = []
        async with sem:
            try:
                async with async_playwright() as p:
                    browser: Browser = await p.chromium.launch(headless=self.headless)
                    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
                    # Attach event handler to close any new page (popup/tab) immediately
                    def on_new_page(new_page):
                        try:
                            logger.info(f"[POPUP] Closing new popup/tab: {getattr(new_page, 'url', lambda: 'unknown')()}")
                            asyncio.create_task(new_page.close())
                            self.stats["tabs_closed"] += 1
                        except Exception as e:
                            logger.warning(f"[POPUP] Error closing popup/tab: {e}")
                    context.on("page", on_new_page)
                    # Also auto-dismiss dialogs
                    def on_dialog(dialog):
                        try:
                            asyncio.create_task(dialog.dismiss())
                        except Exception:
                            pass
                    # Attach dialog handler to all new pages
                    context.on("page", lambda p: p.on("dialog", on_dialog))
                    page = await context.new_page()
                    await page.add_init_script(
                        """
                        window.open = function() { return null; };
                        document.addEventListener('DOMContentLoaded', function() {
                            var links = document.querySelectorAll('a[target="_blank"]');
                            links.forEach(function(link) { link.removeAttribute('target'); });
                        });
                        """
                    )
                    async def remove_target_blank():
                        await page.evaluate("""
                            var links = document.querySelectorAll('a[target="_blank"]');
                            links.forEach(function(link) { link.removeAttribute('target'); });
                        """)
                    for page_num in range(1, self.max_pages_per_keyword + 1):
                        search_url = f"{self.base_url}?q={keyword.replace(' ', '+')}+sort%3Arank&page={page_num}"
                        try:
                            await page.goto(search_url, wait_until="networkidle")
                            await remove_target_blank()
                        except Exception as e:
                            logger.warning(f"Error navigating to {search_url}: {e}")
                            continue
                        await asyncio.sleep(self.delay_between_requests)
                        try:
                            job_elements = await self._find_job_elements(page)
                        except Exception as e:
                            logger.warning(f"Error finding job elements: {e}")
                            continue
                        for job_idx, job_element in enumerate(job_elements[:self.max_jobs_per_keyword], 1):
                            try:
                                job_data = await self._extract_job_info(page, job_element, keyword)
                                url = job_data.get("url", "") if job_data else ""
                                if url and url not in self.processed_urls and self.url_filter.is_valid_job_url(url):
                                    if self.entry_level_only and not self._is_entry_level(job_data):
                                        continue
                                    self.processed_urls.add(url)
                                    results.append(job_data)
                                    self.stats["jobs_saved"] += 1
                                elif url:
                                    self.stats["duplicates_skipped"] += 1
                                
                                # Monitor tabs every 5 jobs for efficiency
                                if job_idx % 5 == 0:
                                    await self._monitor_tab_count(context, job_idx)
                                    
                            except Exception as e:
                                self.stats["extraction_failures"] += 1
                                logger.warning(f"Error extracting job info: {e}")
                        self.stats["pages_scraped"] += 1
                    await context.close()
                    await browser.close()
            except Exception as e:
                logger.error(f"Exception in _scrape_keyword for '{keyword}': {e}")
        return results

    async def _monitor_tab_count(self, context, job_count: int, max_extra_tabs: int = 5) -> None:
        """
        Monitor tab count and cleanup when threshold is reached.
        
        Args:
            context: Browser context
            job_count: Current job count for logging
            max_extra_tabs: Maximum extra tabs before cleanup (default: 5)
        """
        try:
            pages = context.pages
            extra_tabs = len(pages) - 1  # Subtract main page
            
            if extra_tabs >= max_extra_tabs:
                console.print(f"[yellow]🧹 Tab threshold reached: {extra_tabs} extra tabs (max: {max_extra_tabs})[/yellow]")
                
                tabs_closed = 0
                for page in pages[1:]:  # Skip main page
                    try:
                        if not page.is_closed():
                            await page.close()
                            tabs_closed += 1
                            self.stats["tabs_closed"] += 1
                    except Exception as e:
                        console.print(f"[dim]⚠️ Error closing tab: {e}[/dim]")
                
                console.print(f"[green]📊 Cleaned up {tabs_closed} tabs after job {job_count}[/green]")
            elif extra_tabs > 0:
                console.print(f"[dim]📊 Job {job_count}: {extra_tabs} extra tabs (threshold: {max_extra_tabs})[/dim]")
                
        except Exception as e:
            console.print(f"[dim]⚠️ Tab monitoring error: {e}[/dim]")

    async def _find_job_elements(self, page) -> List:
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
                return elements
        return []

    async def _extract_job_info(self, page, job_element, keyword) -> Optional[Dict]:
        """
        Extract job URL, title, company, location, salary, description from a job element.
        """
        try:
            # Get job title
            job_title = await job_element.inner_text()
            # Find parent container for more info
            job_container = job_element
            for _ in range(5):
                parent = await job_container.query_selector("..")
                if not parent:
                    break
                job_container = parent
            container_text = await job_container.inner_text()
            lines = [line.strip() for line in container_text.split("\n") if line.strip()]
            job_data = {
                "title": lines[0] if lines else job_title,
                "company": "",
                "location": "",
                "salary": "",
                "description": "",
                "url": "",
                "search_keyword": keyword,
                "scraped_date": datetime.now().isoformat(),
            }
            # Parse company/location/salary
            for line in lines[1:6]:
                if not job_data["company"] and len(line) > 2 and len(line) < 60:
                    if not any(skip in line.lower() for skip in ['posted', 'ago', 'days', 'salary', '$']):
                        job_data["company"] = line
                        continue
                if not job_data["location"] and (any(city in line.lower() for city in ["toronto", "vancouver", "montreal", "calgary", "edmonton"]) or any(prov in line.upper() for prov in ["ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB", "PE", "NL", "YT", "NT", "NU"])):
                    job_data["location"] = line
                    continue
                if not job_data["salary"] and ("$" in line or "salary" in line.lower()):
                    job_data["salary"] = line
            # Description is everything else
            desc_lines = [l for l in lines if l not in [job_data["title"], job_data["company"], job_data["location"], job_data["salary"]]]
            job_data["description"] = " ".join(desc_lines)[:500]
            # Get job URL
            link = await job_element.query_selector("a")
            href = await link.get_attribute("href") if link else None
            if href and href.startswith("http") and "eluta.ca" not in href:
                job_data["url"] = href
            elif href and href.startswith("/") and not any(skip in href for skip in ["/search?", "q=", "pg="]):
                job_data["url"] = "https://www.eluta.ca" + href
            elif href and (href == "#!" or href.startswith("#")):
                # Try click and get new tab URL
                context = page.context
                initial_pages = len(context.pages)
                try:
                    await link.click()
                    await asyncio.sleep(1)
                    current_pages = context.pages
                    if len(current_pages) > initial_pages:
                        new_page = current_pages[-1]
                        try:
                            await new_page.wait_for_load_state("domcontentloaded", timeout=3000)
                            final_url = new_page.url
                            await new_page.close()
                            self.stats["tabs_closed"] += 1
                            job_data["url"] = final_url
                        except Exception:
                            try:
                                await new_page.close()
                                self.stats["tabs_closed"] += 1
                            except:
                                pass
                    else:
                        current_url = page.url
                        if current_url and "eluta.ca" not in current_url:
                            job_data["url"] = current_url
                except Exception:
                    pass
            return job_data if job_data["url"] else None
        except Exception as e:
            self.stats["extraction_failures"] += 1
            return None

    def _save_jobs(self, jobs: List[Dict]) -> None:
        for job in jobs:
            try:
                self.db.add_job(job)
            except Exception as e:
                logger.warning(f"Error saving job: {e}")

    def _is_entry_level(self, job: Dict) -> bool:
        # Simple entry-level filter based on keywords in title/description
        entry_keywords = ["junior", "entry", "graduate", "new grad", "trainee", "coordinator", "intern", "associate", "0-2 years", "1-2 years", "0-1 years", "level i", "level 1"]
        avoid_keywords = ["senior", "lead", "principal", "manager", "director", "supervisor", "chief", "vp", "vice president", "3+ years", "4+ years", "5+ years", "10+ years", "experienced", "expert", "specialist ii", "level ii", "level 2", "staff"]
        title = job.get("title", "").lower()
        desc = job.get("description", "").lower()
        if any(k in title or k in desc for k in entry_keywords) and not any(k in title or k in desc for k in avoid_keywords):
            return True
        return False

    def _print_summary(self, jobs: List[Dict]):
        from rich.table import Table
        from rich.panel import Panel
        console.print("\n" + "=" * 80)
        console.print(Panel.fit("UNIFIED ELUTA SCRAPER SUMMARY", style="bold green"))
        stats_table = Table(title="Scraping Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="green")
        for k, v in self.stats.items():
            stats_table.add_row(str(k), str(v))
        stats_table.add_row("Final Unique Jobs", str(len(jobs)))
        console.print(stats_table)
        if jobs:
            console.print(f"\n[bold]Sample Jobs:[/bold]")
            sample_table = Table()
            sample_table.add_column("Title", style="green", max_width=25)
            sample_table.add_column("Company", style="cyan", max_width=20)
            sample_table.add_column("Location", style="yellow", max_width=15)
            sample_table.add_column("Salary", style="magenta", max_width=12)
            sample_table.add_column("URL", style="blue", max_width=30)
            for job in jobs[:8]:
                sample_table.add_row(
                    job.get("title", "Unknown")[:25],
                    job.get("company", "Unknown")[:20],
                    job.get("location", "Unknown")[:15],
                    job.get("salary", "")[:12],
                    job.get("url", "")[:30],
                )
            console.print(sample_table)

    def _save_output_file(self, jobs: List[Dict]):
        import csv, json, os
        if self.output_file.endswith(".csv"):
            with open(self.output_file, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
                writer.writeheader()
                writer.writerows(jobs)
            console.print(f"[green]Saved jobs to CSV: {self.output_file}[/green]")
        elif self.output_file.endswith(".json"):
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(jobs, f, ensure_ascii=False, indent=2)
            console.print(f"[green]Saved jobs to JSON: {self.output_file}[/green]")
        else:
            console.print(f"[yellow]Unknown output file type: {self.output_file}[/yellow]")


# CLI entrypoint
async def run_unified_eluta_scraper(profile_name: str, config: Optional[Dict] = None):
    """
    Entrypoint for running the UnifiedElutaScraper asynchronously.
    """
    scraper = UnifiedElutaScraper(profile_name, config)
    return await scraper.scrape_all_keywords()



if __name__ == "__main__":
    import argparse
    import asyncio
    parser = argparse.ArgumentParser(description="Unified Eluta Scraper CLI (Merged, Enhanced, No AI)")
    parser.add_argument("profile", type=str, nargs="?", default="Nirajan", help="Profile name (default: Nirajan)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--pages", type=int, default=5, help="Pages per keyword (default: 5)")
    parser.add_argument("--jobs", type=int, default=20, help="Jobs per keyword (default: 20)")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (default: 0.5)")
    parser.add_argument("--workers", type=int, default=2, help="Concurrent workers (default: 2)")
    parser.add_argument("--output", type=str, default=None, help="Output file (CSV or JSON)")
    parser.add_argument("--entry-level", action="store_true", help="Only save entry-level jobs")
    args = parser.parse_args()
    config = {
        "headless": args.headless,
        "pages": args.pages,
        "jobs": args.jobs,
        "delay": args.delay,
        "workers": args.workers,
        "output": args.output,
        "entry_level": args.entry_level,
    }
    results = asyncio.run(run_unified_eluta_scraper(args.profile, config))
    if results is not None:
        print(f"[green]Total valid job URLs saved: {len(results)}[/green]")

    async def _scrape_keyword(self, browser, keyword: str, sem: asyncio.Semaphore) -> List[Dict]:
        """
        Scrape job URLs for a single keyword using fast extraction and strict popup/tab blocking.
        Only saves valid URLs, skips heavy processing, and tracks all metrics.
        """
        results = []
        async with sem:
            context = None
            page = None
            try:
                context = await browser.new_context(viewport={"width": 1920, "height": 1080})

                # Strict popup and tab blocking: close any new page immediately
                def close_new_page(new_page):
                    try:
                        asyncio.create_task(new_page.close())
                        self.stats["tabs_closed"] += 1
                        self.stats["popups_blocked"] += 1
                        console.print(f"[yellow]⚠️ Blocked and closed popup/tab: {getattr(new_page, 'url', lambda: 'unknown')()}")
                    except Exception as e:
                        console.print(f"[yellow]⚠️ Error closing popup/tab: {e}[/yellow]")
                context.on("page", close_new_page)
                context.on("page", lambda p: p.on("dialog", lambda dialog: dialog.dismiss()))

                page = await context.new_page()

                # Block window.open and remove target="_blank"
                await page.add_init_script(
                    """
                    window.open = function() {
                        console.warn('Blocked window.open call by scraper');
                        return null;
                    };
                    document.addEventListener('DOMContentLoaded', function() {
                        var links = document.querySelectorAll('a[target="_blank"]');
                        links.forEach(function(link) { link.removeAttribute('target'); });
                    });
                    """
                )

                async def remove_target_blank():
                    await page.evaluate("""
                        var links = document.querySelectorAll('a[target="_blank"]');
                        links.forEach(function(link) { link.removeAttribute('target'); });
                    """)

                for page_num in range(1, self.max_pages_per_keyword + 1):
                    search_url = f"{self.base_url}?q={keyword.replace(' ', '+')}+sort%3Arank&page={page_num}"
                    try:
                        await page.goto(search_url, wait_until="networkidle")
                        await remove_target_blank()
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
                        try:
                            job_url_data = await self._extract_job_url_fast(page, job_element, keyword)
                            url = job_url_data.get("url", "") if job_url_data else ""
                            if url and self.url_filter(url) and url not in self.processed_urls:
                                self.processed_urls.add(url)
                                results.append(job_url_data)
                                self.stats["valid_urls_collected"] += 1
                            elif url:
                                self.stats["extraction_failures"] += 1
                        except Exception as e:
                            self.stats["extraction_failures"] += 1
                            console.print(f"[yellow]⚠️ Error extracting job URL: {e}[/yellow]")
                        # After each extraction, close all tabs except the main one
                        await self._close_other_tabs(context, page)
                return results
            except Exception as e:
                console.print(f"[red]❌ Exception in _scrape_keyword for '{keyword}': {e}[/red]")
                return results
            finally:
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

    # _close_other_tabs is no longer needed with robust event handler

    async def _find_job_elements(self, page):
        """
        Find all job result elements using proven selectors from optimized scraper.
        Returns a list of element handles.
        """
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
                return elements
        return []

    async def _extract_job_url_fast(self, page, job_element, keyword):
        """
        Fast extraction of job URL with immediate tab closure. Only returns minimal info.
        """
        try:
            # Try to get the job link
            link = await job_element.query_selector("a")
            if not link:
                return None
            href = await link.get_attribute("href")
            if not href:
                return None
            # Direct external URL
            if href.startswith("http") and "eluta.ca" not in href:
                return {
                    "url": href,
                    "search_keyword": keyword,
                    "scraped_date": datetime.now().isoformat()
                }
            # Relative URL
            if href.startswith("/") and not any(skip in href for skip in ["/search?", "q=", "pg="]):
                full_url = "https://www.eluta.ca" + href
                return {
                    "url": full_url,
                    "search_keyword": keyword,
                    "scraped_date": datetime.now().isoformat()
                }
            # If click is needed, do it and close any new tab immediately
            if href == "#!" or not href or href.startswith("#"):
                context = page.context
                initial_pages = len(context.pages)
                try:
                    await link.click()
                    await asyncio.sleep(1)
                    current_pages = context.pages
                    if len(current_pages) > initial_pages:
                        new_page = current_pages[-1]
                        try:
                            await new_page.wait_for_load_state("domcontentloaded", timeout=3000)
                            final_url = new_page.url
                            await new_page.close()
                            self.stats["tabs_closed"] += 1
                            return {
                                "url": final_url,
                                "search_keyword": keyword,
                                "scraped_date": datetime.now().isoformat()
                            }
                        except Exception as tab_error:
                            try:
                                await new_page.close()
                                self.stats["tabs_closed"] += 1
                            except:
                                pass
                    # If no new tab, check current page URL
                    current_url = page.url
                    if current_url and "eluta.ca" not in current_url:
                        return {
                            "url": current_url,
                            "search_keyword": keyword,
                            "scraped_date": datetime.now().isoformat()
                        }
                except Exception as click_error:
                    self.stats["extraction_failures"] += 1
                    return None
            # Fallback: return only if it's a valid http URL
            if href.startswith("http"):
                return {
                    "url": href,
                    "search_keyword": keyword,
                    "scraped_date": datetime.now().isoformat()
                }
            return None
        except Exception as e:
            self.stats["extraction_failures"] += 1
            return None



    def _save_jobs(self, jobs: List[Dict]):
        """
        Save a list of job dicts (minimal: just URL, keyword, date) to the job database.
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


def main():
    import argparse
    import asyncio
    parser = argparse.ArgumentParser(description="Unified Eluta Scraper CLI (Official)")
    parser.add_argument("profile", type=str, nargs="?", default="Nirajan", help="Profile name (default: Nirajan)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--pages", type=int, default=5, help="Pages per keyword (default: 5)")
    parser.add_argument("--jobs", type=int, default=20, help="Jobs per keyword (default: 20)")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (default: 0.5)")
    parser.add_argument("--workers", type=int, default=2, help="Concurrent workers (default: 2)")
    parser.add_argument("--output", type=str, default=None, help="Output file (CSV or JSON)")
    parser.add_argument("--entry-level", action="store_true", help="Only save entry-level jobs")
    args = parser.parse_args()
    config = {
        "headless": args.headless,
        "pages": args.pages,
        "jobs": args.jobs,
        "delay": args.delay,
        "workers": args.workers,
        "output": args.output,
        "entry_level": args.entry_level,
    }
    results = asyncio.run(run_unified_eluta_scraper(args.profile, config))
    if results is not None:
        print(f"[green]Total valid job URLs saved: {len(results)}[/green]")


if __name__ == "__main__":
    main()
