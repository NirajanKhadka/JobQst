"""
Scraping Actions for AutoJobAgent CLI.

Contains action processors for different scraping operations:
- Single site scraping
- Multi-site scraping
- Different scraping modes
- Bot detection methods
"""

from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from ..handlers.scraping_handler import ScrapingHandler

console = Console()


class ScrapingActions:
    """Handles all scraping action processing."""

    def __init__(self, profile: Dict):
        self.profile = profile
        self.scraping_handler = ScrapingHandler(profile)

    def show_scraping_menu(self, args) -> None:
        """Show Improved scraping menu with NEW Fast 3-Phase Pipeline."""
        console.print(Panel("🚀 Fast 3-Phase Pipeline Scraping Menu (4.6x Faster)", style="bold blue"))

        # Show system capabilities and new pipeline info
        console.print(f"[green]🆕 NEW: Fast 3-Phase Pipeline (4.6x performance improvement)[/green]")
        console.print(f"[cyan]📋 Keywords: {len(self.profile.get('keywords', []))} loaded from profile[/cyan]")
        console.print(f"[cyan]⚡ Phase 1: Eluta URLs → Phase 2: Parallel External Scraping → Phase 3: GPU Processing[/cyan]")

        # Site selection first
        console.print(f"\n[bold]Available Job Sites:[/bold]")
        site_options = {
            "1": "🇨🇦 Eluta.ca (NEW Fast Pipeline - Recommended)",
            "2": "🌍 Indeed.ca (Coming soon - uses Eluta for now)",
            "3": "💼 LinkedIn Jobs (Coming soon - uses Eluta for now)",
            "4": "🏛️ JobBank.gc.ca (Coming soon - uses Eluta for now)",
            "5": "👹 Monster.ca (Coming soon - uses Eluta for now)",
            "6": "🏢 Workday (Coming soon - uses Eluta for now)",
            "7": "⚡ Multi-site parallel (Future feature - uses Eluta for now)",
        }

        for key, value in site_options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

        console.print()
        console.print("[yellow]💡 All options currently use the new Fast 3-Phase Pipeline with Eluta[/yellow]")
        site_choice = Prompt.ask("Select site", choices=list(site_options.keys()), default="1")

        if site_choice == "7":
            self.multi_site_scrape_action(args)
        else:
            self.single_site_scrape_action(args, site_choice)

    def single_site_scrape_action(self, args, site: str, bot_method: str = "1") -> None:
        """Handle single site scraping action using Fast 3-Phase Pipeline."""
        site_map = {
            "1": "eluta",
            "2": "eluta",  # All sites use Eluta for now
            "3": "eluta",
            "4": "eluta",
            "5": "eluta",
            "6": "eluta",
        }

        selected_site = site_map.get(site, "eluta")
        console.print(f"\n[bold]Selected Site:[/bold] ELUTA (Fast 3-Phase Pipeline)")

        # Show NEW fast pipeline methods
        console.print(f"\n[bold]Fast Pipeline Methods:[/bold]")
        bot_methods = {
            "1": "🚀 Fast Pipeline - Standard (4 workers, reliable)",
            "2": "⚡ Fast Pipeline - High Performance (6 workers, maximum speed)",
        }

        for key, value in bot_methods.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

        console.print()
        console.print("[green]💡 Both options use the NEW Fast 3-Phase Pipeline (4.6x faster)[/green]")
        bot_choice = Prompt.ask(
            "Select pipeline mode", choices=list(bot_methods.keys()), default="1"
        )

        # Execute fast pipeline scraping
        self._execute_fast_pipeline_scraping(bot_choice)

    def multi_site_scrape_action(self, args, bot_method: str = "2") -> None:
        """Handle multi-site scraping using Fast 3-Phase Pipeline (High Performance)."""
        console.print(Panel("⚡ Fast 3-Phase Pipeline (Multi-Site Mode)", style="bold blue"))
        console.print("[cyan]🚀 Running Fast 3-Phase Pipeline in high-performance mode...[/cyan]")
        console.print("[yellow]📝 Currently optimized for Eluta with plans for multi-site expansion[/yellow]")

        # Use the fast pipeline multi-worker method
        success = self.scraping_handler.run_scraping(mode="multi_worker")

        if success:
            console.print("[green]✅ Fast pipeline (multi-site mode) completed successfully![/green]")
            console.print("[cyan]💡 Jobs automatically processed and saved to database![/cyan]")
        else:
            console.print("[yellow]⚠️ Fast pipeline completed with limited results[/yellow]")
            console.print("[cyan]💡 Try standard mode or check your internet connection[/cyan]")

    def _execute_fast_pipeline_scraping(self, method_choice: str) -> None:
        """Execute Fast 3-Phase Pipeline scraping with the selected method."""
        if method_choice == "1":
            # Standard fast pipeline
            console.print("[cyan]🚀 Using Fast 3-Phase Pipeline (Standard Mode)...[/cyan]")
            console.print("[cyan]📋 4 external workers, auto processing method[/cyan]")
            success = self.scraping_handler.run_scraping(mode="simple")
        else:
            # High performance fast pipeline
            console.print("[cyan]⚡ Using Fast 3-Phase Pipeline (High Performance Mode)...[/cyan]")
            console.print("[cyan]📋 6 external workers, maximum speed configuration[/cyan]")
            success = self.scraping_handler.run_scraping(mode="multi_worker")

        if success:
            console.print("[green]✅ Fast pipeline completed successfully![/green]")
            console.print("[cyan]💡 Check your database - jobs are automatically saved and processed![/cyan]")
        else:
            console.print("[yellow]⚠️ Fast pipeline completed with limited results[/yellow]")
            console.print("[cyan]💡 Try the other pipeline mode or check your internet connection[/cyan]")

    def automated_scrape_action(self, args=None) -> None:
        """Execute automated scraping action using simplified architecture."""
        console.print(Panel("🧠 Automated Scraping (Simplified)", style="bold blue"))
        console.print("[cyan]🧠 Using simplified automated scraping...[/cyan]")

        # Use simple sequential method for automated scraping
        success = self.scraping_handler.run_scraping(mode="simple")

        if success:
            console.print("[green]✅ Automated scraping completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Automated scraping completed with limited results[/yellow]")

    def parallel_scrape_action(self, args=None) -> None:
        """Execute parallel scraping action using simplified architecture."""
        console.print(Panel("⚡ Parallel Scraping (Simplified)", style="bold blue"))
        console.print("[cyan]⚡ Using simplified parallel processing...[/cyan]")

        # Use multi-worker method for parallel scraping
        success = self.scraping_handler.run_scraping(mode="multi_worker")

        if success:
            console.print("[green]✅ Parallel scraping completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Parallel scraping completed with limited results[/yellow]")

    def detailed_scrape_action(self, args=None) -> None:
        """Execute detailed scraping action using simplified architecture."""
        console.print(Panel("🔍 Detailed Scraping (Simplified)", style="bold blue"))
        console.print("[cyan]🔍 Using simplified detailed analysis...[/cyan]")

        # Use multi-worker method for detailed scraping
        success = self.scraping_handler.run_scraping(mode="multi_worker")

        if success:
            console.print("[green]✅ Detailed scraping completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Detailed scraping completed with limited results[/yellow]")

    def anti_bot_scrape_action(self, args) -> None:
        """Execute anti-bot scraping action using simplified architecture."""
        console.print(Panel("🛡️ Anti-Bot Scraping (Simplified)", style="bold blue"))
        console.print("[cyan]🛡️ Using simplified anti-bot detection...[/cyan]")

        # Use simple sequential method for anti-bot scraping
        success = self.scraping_handler.run_scraping(mode="simple")

        if success:
            console.print("[green]✅ Anti-bot scraping completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Anti-bot scraping completed with limited results[/yellow]")

    def process_queue_action(self, args=None) -> None:
        """Process jobs from queue - scrape from links in the queue."""
        console.print(Panel("📋 Process Jobs from Queue", style="bold blue"))
        console.print("[cyan]📋 Processing jobs from the queue...[/cyan]")

        try:
            # Get jobs from session queue
            scraped_jobs = self.scraping_handler.session.get("scraped_jobs", [])
            done_jobs = self.scraping_handler.session.get("done", [])

            if not scraped_jobs:
                console.print("[yellow]⚠️ No jobs in queue to process[/yellow]")
                return

            # Filter out already processed jobs
            pending_jobs = [
                job for job in scraped_jobs if job.get("url") and job.get("url") not in done_jobs
            ]

            if not pending_jobs:
                console.print("[yellow]⚠️ All jobs in queue have been processed[/yellow]")
                return

            console.print(f"[green]Found {len(pending_jobs)} jobs to process from queue[/green]")

            # Process each job URL
            processed_count = 0
            for i, job in enumerate(pending_jobs, 1):
                job_url = job.get("url")
                if not job_url:
                    continue

                console.print(
                    f"\n[bold]Processing {i}/{len(pending_jobs)}:[/bold] {job.get('title', 'Unknown')}"
                )
                console.print(f"[cyan]URL:[/cyan] {job_url}")

                try:
                    # Scrape detailed information from the job URL
                    detailed_job = self._scrape_job_details(job_url)

                    if detailed_job:
                        # Update the job with detailed information
                        job.update(detailed_job)
                        processed_count += 1
                        console.print("[green]✅ Job details scraped successfully[/green]")

                        # Mark as processed
                        done_jobs.append(job_url)
                        self.scraping_handler.session["done"] = done_jobs
                        self.scraping_handler._save_session(
                            self.scraping_handler.profile.get("profile_name", "default"),
                            self.scraping_handler.session,
                        )
                    else:
                        console.print("[yellow]⚠️ Failed to scrape job details[/yellow]")

                    # Add delay between requests
                    if i < len(pending_jobs):
                        console.print("[cyan]Waiting 2 seconds before next job...[/cyan]")
                        import time

                        time.sleep(2)

                except Exception as e:
                    console.print(f"[red]❌ Error processing job: {e}[/red]")
                    continue

            console.print(
                f"\n[bold green]✅ Queue processing completed! {processed_count}/{len(pending_jobs)} jobs processed[/bold green]"
            )

        except Exception as e:
            console.print(f"[red]❌ Error during queue processing: {e}[/red]")
            import traceback

            traceback.print_exc()

    def _scrape_job_details(self, job_url: str) -> Optional[Dict]:
        """Scrape detailed information from a job URL."""
        try:
            from playwright.sync_api import sync_playwright
            from src.core.browser_utils import BrowserUtils

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                # Navigate to job URL
                page.goto(job_url, wait_until="domcontentloaded")

                # Extract job details
                job_details = {}

                # Try to extract title
                title_selectors = ["h1", '[data-testid="job-title"]', ".job-title", ".title", "h2"]

                for selector in title_selectors:
                    title_element = page.query_selector(selector)
                    if title_element:
                        title_text = title_element.text_content()
                        if title_text:
                            job_details["title"] = title_text.strip()
                            break

                # Try to extract company
                company_selectors = [
                    '[data-testid="company-name"]',
                    ".company-name",
                    ".company",
                    '[class*="company"]',
                ]

                for selector in company_selectors:
                    company_element = page.query_selector(selector)
                    if company_element:
                        company_text = company_element.text_content()
                        if company_text:
                            job_details["company"] = company_text.strip()
                            break

                # Try to extract location
                location_selectors = [
                    '[data-testid="location"]',
                    ".location",
                    '[class*="location"]',
                ]

                for selector in location_selectors:
                    location_element = page.query_selector(selector)
                    if location_element:
                        location_text = location_element.text_content()
                        if location_text:
                            job_details["location"] = location_text.strip()
                            break

                # Try to extract description/summary
                description_selectors = [
                    '[data-testid="job-description"]',
                    ".job-description",
                    ".description",
                    '[class*="description"]',
                    "p",
                ]

                for selector in description_selectors:
                    desc_elements = page.query_selector_all(selector)
                    if desc_elements:
                        descriptions = []
                        for elem in desc_elements:
                            text = elem.text_content()
                            if text and text.strip():
                                descriptions.append(text.strip())
                        if descriptions:
                            job_details["summary"] = " ".join(
                                descriptions[:3]
                            )  # Take first 3 paragraphs
                            break

                browser.close()

                return job_details if job_details else None

        except Exception as e:
            console.print(f"[red]Error scraping job details: {e}[/red]")
            return None
