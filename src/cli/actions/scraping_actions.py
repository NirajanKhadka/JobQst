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
        """Show enhanced scraping menu with multiple locations and sites."""
        console.print(Panel("🌍 Enhanced Job Scraping Hub", style="bold blue"))

        # Show system capabilities
        console.print("[green]🚀 MULTI-LOCATION: Global job search across regions[/green]")
        console.print(
            f"[cyan]📋 Keywords: {len(self.profile.get('keywords', []))} loaded from profile[/cyan]"
        )
        console.print("[cyan]⚡ Sites: Indeed, LinkedIn, Glassdoor, Eluta, Job Bank[/cyan]")
        console.print("[green]🎯 Performance: 2+ jobs/second[/green]")

        # Location selection first
        console.print("\n[bold]🌍 Select Target Location:[/bold]")
        location_options = {
            "1": "🇨🇦 Canada (All provinces)",
            "2": "🇺🇸 United States (All states)",
            "3": "🇬🇧 United Kingdom",
            "4": "🇦🇺 Australia",
            "5": "🇩🇪 Germany",
            "6": "🌍 Global (All locations)",
            "7": "📍 Custom Location",
        }

        for key, value in location_options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

        location_choice = Prompt.ask(
            "Select location", choices=list(location_options.keys()), default="1"
        )

        # Get specific location if custom
        target_location = self._get_target_location(location_choice)

        # Scraping mode selection
        console.print(f"\n[bold]🚀 Scraping Options for {target_location}:[/bold]")
        mode_options = {
            "1": "🚀 Multi-Site Standard (Recommended)",
            "2": "⚡ Multi-Site High Performance (Maximum speed)",
            "3": "🎯 Site-Specific Scraping",
            "4": "🔄 Backup: Eluta Only (Canada focus)",
        }

        for key, value in mode_options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

        console.print()
        console.print("[green]💡 Options 1-2 search multiple sites simultaneously![/green]")
        mode_choice = Prompt.ask(
            "Select scraping option", choices=list(mode_options.keys()), default="1"
        )

        if mode_choice in ["1", "2"]:
            self._execute_multi_site_scraping(mode_choice, target_location)
        elif mode_choice == "3":
            self._show_site_specific_menu(target_location)
        elif mode_choice == "4":
            console.print("[yellow]⚠️ You selected Eluta-only scraping (Canada focus)[/yellow]")
            confirm = Prompt.ask("Continue with Eluta scraping?", choices=["y", "n"], default="y")
            if confirm == "y":
                self._execute_eluta_only_scraping()
            else:
                console.print("[green]✅ Switching to multi-site scraping...[/green]")
                self._execute_multi_site_scraping("1", target_location)

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
        console.print(
            "[green]💡 Both options use the NEW Fast 3-Phase Pipeline (4.6x faster)[/green]"
        )
        bot_choice = Prompt.ask(
            "Select pipeline mode", choices=list(bot_methods.keys()), default="1"
        )

        # Execute fast pipeline scraping
        self._execute_fast_pipeline_scraping(bot_choice)

    def multi_site_scrape_action(self, args, bot_method: str = "2") -> None:
        """Handle multi-site scraping using Fast 3-Phase Pipeline (High Performance)."""
        console.print(Panel("⚡ Fast 3-Phase Pipeline (Multi-Site Mode)", style="bold blue"))
        console.print("[cyan]🚀 Running Fast 3-Phase Pipeline in high-performance mode...[/cyan]")
        console.print(
            "[yellow]📝 Currently optimized for Eluta with plans for multi-site expansion[/yellow]"
        )

        # Use the fast pipeline multi-worker method
        success = self.scraping_handler.run_scraping(mode="multi_worker")

        if success:
            console.print(
                "[green]✅ Fast pipeline (multi-site mode) completed successfully![/green]"
            )
            console.print("[cyan]💡 Jobs automatically processed and saved to database![/cyan]")
        else:
            console.print("[yellow]⚠️ Fast pipeline completed with limited results[/yellow]")
            console.print("[cyan]💡 Try standard mode or check your internet connection[/cyan]")

    def _execute_jobspy_scraping(self, method_choice: str) -> None:
        """Execute JobSpy scraping with parallel processing."""
        try:
            from src.scrapers.jobspy_enhanced_scraper import JobSpyImprovedScraper

            if method_choice == "1":
                # Standard JobSpy
                console.print("[cyan]🚀 Using JobSpy Standard Mode...[/cyan]")
                console.print("[cyan]📋 Parallel scraping: Indeed, LinkedIn, Glassdoor[/cyan]")
                max_jobs = 50
            else:
                # High performance JobSpy
                console.print("[cyan]⚡ Using JobSpy High Performance Mode...[/cyan]")
                console.print("[cyan]📋 Maximum parallel workers across all sites[/cyan]")
                max_jobs = 100

            # Initialize JobSpy scraper
            scraper = JobSpyImprovedScraper(self.profile.get("profile_name", "default"))

            # Run async scraping
            import asyncio

            jobs = asyncio.run(scraper.scrape_jobs_Improved(max_jobs=max_jobs))

            if jobs and len(jobs) > 0:
                console.print(f"[green]✅ JobSpy scraping completed successfully![/green]")
                console.print(f"[cyan]📊 Jobs found: {len(jobs)}[/cyan]")
                console.print(f"[cyan]💾 Jobs saved to database automatically[/cyan]")

                # Show sample jobs
                for i, job in enumerate(jobs[:3], 1):
                    title = job.get("title", "Unknown")[:40]
                    company = job.get("company", "Unknown")[:20]
                    location = job.get("location", "Unknown")[:15]
                    console.print(f"  {i}. {title}... at {company} ({location})")

                if len(jobs) > 3:
                    console.print(f"  ... and {len(jobs) - 3} more jobs")
            else:
                console.print("[yellow]⚠️ JobSpy completed with limited results[/yellow]")
                console.print(
                    "[cyan]💡 Try adjusting your profile keywords or location settings[/cyan]"
                )

        except ImportError:
            console.print(
                "[red]❌ JobSpy not available. Install with: pip install python-jobspy[/red]"
            )
            console.print("[cyan]💡 Falling back to Eluta scraper...[/cyan]")
            # Fallback to existing scraping
            success = self.scraping_handler.run_scraping(
                mode="simple" if method_choice == "1" else "multi_worker"
            )
            if success:
                console.print("[green]✅ Fallback scraping completed![/green]")
        except Exception as e:
            console.print(f"[red]❌ JobSpy error: {e}[/red]")
            console.print("[cyan]💡 Falling back to Eluta scraper...[/cyan]")
            # Fallback to existing scraping
            success = self.scraping_handler.run_scraping(
                mode="simple" if method_choice == "1" else "multi_worker"
            )
            if success:
                console.print("[green]✅ Fallback scraping completed![/green]")

    def _get_target_location(self, choice: str) -> str:
        """Get target location based on user choice."""
        if choice == "1":
            # Show Canadian cities submenu
            return self._select_canadian_city()
        elif choice == "7":
            custom_location = Prompt.ask("Enter custom location (city, country)")
            return custom_location

        location_map = {
            "2": "United States",
            "3": "United Kingdom",
            "4": "Australia",
            "5": "Germany",
            "6": "Global",
        }

        return location_map.get(choice, "Canada")

    def _select_canadian_city(self) -> str:
        """Select specific Canadian city for targeted job search."""
        console.print("\n[bold]🇨🇦 Select Canadian City:[/bold]")

        city_options = {
            "1": "🏙️ Toronto, ON",
            "2": "🌊 Vancouver, BC",
            "3": "🍁 Montreal, QC",
            "4": "🏔️ Calgary, AB",
            "5": "🌾 Edmonton, AB",
            "6": "🦞 Halifax, NS",
            "7": "🏛️ Ottawa, ON",
            "8": "💎 Winnipeg, MB",
            "9": "🌸 Victoria, BC",
            "10": "⚡ Kitchener-Waterloo, ON",
            "11": "🏒 Quebec City, QC",
            "12": "🦬 Saskatoon, SK",
            "13": "🇨🇦 All Major Cities",
        }

        for key, value in city_options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

        city_choice = Prompt.ask("Select city", choices=list(city_options.keys()), default="13")

        city_map = {
            "1": "Toronto, Ontario",
            "2": "Vancouver, British Columbia",
            "3": "Montreal, Quebec",
            "4": "Calgary, Alberta",
            "5": "Edmonton, Alberta",
            "6": "Halifax, Nova Scotia",
            "7": "Ottawa, Ontario",
            "8": "Winnipeg, Manitoba",
            "9": "Victoria, British Columbia",
            "10": "Kitchener, Ontario",
            "11": "Quebec City, Quebec",
            "12": "Saskatoon, Saskatchewan",
            "13": "Canada",
        }

        selected_city = city_map.get(city_choice, "Canada")
        console.print(f"[green]✅ Selected: {selected_city}[/green]")
        return selected_city

    def _show_site_specific_menu(self, location: str) -> None:
        """Show site-specific scraping options."""
        console.print(f"\n[bold]🎯 Site-Specific Scraping for {location}:[/bold]")

        site_options = {
            "1": "🔍 Indeed Only",
            "2": "💼 LinkedIn Only",
            "3": "🏢 Glassdoor Only",
            "4": "🇨🇦 Eluta (Canada)",
            "5": "🏛️ Job Bank (Canada Government)",
            "6": "🔄 All Sites Sequential",
        }

        for key, value in site_options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

        site_choice = Prompt.ask("Select site", choices=list(site_options.keys()), default="6")
        self._execute_site_specific_scraping(site_choice, location)

    def _execute_multi_site_scraping(self, mode: str, location: str) -> None:
        """Execute multi-site scraping with location targeting."""
        console.print(Panel(f"🌍 Multi-Site Scraping: {location}", style="bold blue"))

        max_jobs = 50 if mode == "1" else 100
        console.print(f"[cyan]🚀 Searching {location} across multiple job sites...[/cyan]")
        console.print(f"[cyan]📋 Target: {max_jobs} jobs per site[/cyan]")

        try:
            # Try JobSpy first for international sites
            if location != "Canada":
                console.print("[cyan]🌍 Using JobSpy for international search...[/cyan]")
                self._execute_jobspy_scraping_with_location(mode, location)
            else:
                # For Canada, use both JobSpy and local scrapers
                console.print("[cyan]🇨🇦 Using enhanced Canada-specific scraping...[/cyan]")
                self._execute_canada_enhanced_scraping(mode)

        except Exception as e:
            console.print(f"[red]❌ Multi-site scraping error: {e}[/red]")
            console.print("[cyan]💡 Falling back to single-site scraping...[/cyan]")
            self._execute_eluta_only_scraping()

    def _execute_site_specific_scraping(self, site_choice: str, location: str) -> None:
        """Execute scraping for a specific site."""
        site_map = {
            "1": "indeed",
            "2": "linkedin",
            "3": "glassdoor",
            "4": "eluta",
            "5": "jobbank",
            "6": "all_sequential",
        }

        selected_site = site_map.get(site_choice, "indeed")
        console.print(f"[cyan]🎯 Scraping {selected_site.title()} for {location}...[/cyan]")

        if selected_site == "all_sequential":
            self._execute_sequential_site_scraping(location)
        else:
            self._execute_single_site_scraping(selected_site, location)

    def _execute_jobspy_scraping_with_location(self, mode: str, location: str) -> None:
        """Execute JobSpy scraping with specific location targeting."""
        try:
            from src.scrapers.jobspy_enhanced_scraper import JobSpyImprovedScraper

            console.print(f"[cyan]🌍 JobSpy scraping for {location}...[/cyan]")
            max_jobs = 50 if mode == "1" else 100

            # Initialize JobSpy scraper with location
            scraper = JobSpyImprovedScraper(self.profile.get("profile_name", "default"))

            # Run async scraping with location
            import asyncio

            jobs = asyncio.run(
                scraper.scrape_jobs_with_location(location=location, max_jobs=max_jobs)
            )

            if jobs and len(jobs) > 0:
                console.print(f"[green]✅ JobSpy scraping completed for {location}![/green]")
                console.print(f"[cyan]📊 Jobs found: {len(jobs)}[/cyan]")
                self._display_job_sample(jobs)
            else:
                console.print(f"[yellow]⚠️ Limited results for {location}[/yellow]")

        except ImportError:
            console.print("[red]❌ JobSpy not available[/red]")
            self._execute_eluta_only_scraping()
        except Exception as e:
            console.print(f"[red]❌ JobSpy error: {e}[/red]")
            self._execute_eluta_only_scraping()

    def _execute_canada_enhanced_scraping(self, mode: str) -> None:
        """Execute enhanced scraping specifically for Canada."""
        console.print("[cyan]🇨🇦 Enhanced Canada scraping: JobSpy + Eluta + Job Bank...[/cyan]")

        try:
            # First run JobSpy for Indeed/LinkedIn/Glassdoor in Canada
            self._execute_jobspy_scraping_with_location(mode, "Canada")

            # Then run Eluta for Canadian-specific jobs
            console.print("[cyan]🔄 Adding Eluta.ca jobs...[/cyan]")
            success = self.scraping_handler.run_scraping(mode="eluta_only")

            # Finally try Job Bank (government jobs)
            console.print("[cyan]🏛️ Adding Job Bank (government) jobs...[/cyan]")
            self._execute_jobbank_scraping()

            console.print("[green]✅ Enhanced Canada scraping completed![/green]")

        except Exception as e:
            console.print(f"[red]❌ Enhanced Canada scraping error: {e}[/red]")

    def _execute_sequential_site_scraping(self, location: str) -> None:
        """Execute scraping across all sites sequentially."""
        sites = ["indeed", "linkedin", "glassdoor"]
        if location == "Canada":
            sites.extend(["eluta", "jobbank"])

        console.print(f"[cyan]🔄 Sequential scraping across {len(sites)} sites...[/cyan]")

        for i, site in enumerate(sites, 1):
            console.print(f"[cyan]Step {i}/{len(sites)}: Scraping {site.title()}...[/cyan]")
            try:
                self._execute_single_site_scraping(site, location)
                if i < len(sites):
                    console.print("[dim]Waiting 3 seconds before next site...[/dim]")
                    import time

                    time.sleep(3)
            except Exception as e:
                console.print(f"[yellow]⚠️ {site.title()} scraping failed: {e}[/yellow]")
                continue

    def _execute_single_site_scraping(self, site: str, location: str) -> None:
        """Execute scraping for a single site."""
        if site == "eluta":
            success = self.scraping_handler.run_scraping(mode="eluta_only")
        elif site == "jobbank":
            self._execute_jobbank_scraping()
        else:
            # Use JobSpy for Indeed, LinkedIn, Glassdoor
            try:
                from src.scrapers.jobspy_enhanced_scraper import JobSpyImprovedScraper

                scraper = JobSpyImprovedScraper(self.profile.get("profile_name", "default"))
                import asyncio

                jobs = asyncio.run(scraper.scrape_single_site(site, location, max_jobs=30))
                if jobs:
                    console.print(f"[green]✅ {site.title()}: {len(jobs)} jobs found[/green]")
                else:
                    console.print(f"[yellow]⚠️ {site.title()}: No jobs found[/yellow]")
            except Exception as e:
                console.print(f"[red]❌ {site.title()} error: {e}[/red]")

    def _execute_jobbank_scraping(self) -> None:
        """Execute Job Bank (Canada government) scraping."""
        try:
            from src.scrapers.jobbank_scraper import JobBankScraper

            scraper = JobBankScraper(self.profile)
            jobs = scraper.scrape_jobs()
            if jobs:
                console.print(f"[green]✅ Job Bank: {len(jobs)} government jobs found[/green]")
            else:
                console.print("[yellow]⚠️ Job Bank: No jobs found[/yellow]")
        except ImportError:
            console.print("[yellow]⚠️ Job Bank scraper not available[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Job Bank error: {e}[/red]")

    def _display_job_sample(self, jobs: list) -> None:
        """Display a sample of scraped jobs."""
        console.print("\n[bold]📋 Sample Jobs Found:[/bold]")
        for i, job in enumerate(jobs[:3], 1):
            title = job.get("title", "Unknown")[:40]
            company = job.get("company", "Unknown")[:20]
            location = job.get("location", "Unknown")[:15]
            console.print(f"  {i}. {title}... at {company} ({location})")

        if len(jobs) > 3:
            console.print(f"  ... and {len(jobs) - 3} more jobs")

    def _execute_eluta_only_scraping(self) -> None:
        """Execute Eluta-only scraping as backup option (32x slower than JobSpy)."""
        console.print(Panel("� Eluta Backup Scraper", style="bold yellow"))
        console.print("[yellow]⚠️ BACKUP MODE: This is 32x slower than JobSpy![/yellow]")
        console.print("[yellow]⚠️ Performance: 0.06 jobs/second vs JobSpy's 2+ jobs/second[/yellow]")
        console.print("[yellow]💡 Consider using JobSpy instead for much faster results[/yellow]")
        console.print(
            "[cyan]🔍 Launching comprehensive backup data collection from Eluta.ca...[/cyan]"
        )

        try:
            # Use the scraping handler with Eluta-specific settings
            success = self.scraping_handler.run_scraping(mode="eluta_only")

            if success:
                console.print("[green]✅ Eluta backup scraping completed successfully![/green]")
                console.print("[cyan]💾 Jobs saved to database automatically[/cyan]")
                console.print(
                    "[green]💡 Next time, use JobSpy (option 1-2) for 32x faster results![/green]"
                )
            else:
                console.print(
                    "[yellow]⚠️ Eluta backup scraping completed with limited results[/yellow]"
                )
                console.print(
                    "[cyan]💡 Try using fast JobSpy instead or check internet connection[/cyan]"
                )

        except Exception as e:
            console.print(f"[red]❌ Eluta backup scraping error: {e}[/red]")
            console.print(
                "[green]💡 Consider using fast JobSpy instead (32x faster, more reliable)[/green]"
            )

    # def _execute_combined_scraping(self) -> None:
    #     """Execute combined JobSpy + Eluta scraping."""
    #     # DEPRECATED: Use JobSpy as primary, Eluta as manual backup only
    #     console.print(Panel("🔄 Combined JobSpy + Eluta Scraping", style="bold blue"))
    #     console.print("[cyan]🚀 Running JobSpy first (fast)...[/cyan]")
    #     console.print("[yellow]🐌 Then Eluta for additional coverage (slower)...[/yellow]")
    #
    #     try:
    #         # First run JobSpy for speed
    #         console.print("[cyan]Step 1/2: JobSpy scraping...[/cyan]")
    #         self._execute_jobspy_scraping("1")  # Standard mode
    #
    #         # Then run Eluta for additional coverage
    #         console.print("[yellow]Step 2/2: Eluta scraping (slower)...[/yellow]")
    #         success = self.scraping_handler.run_scraping(mode="eluta_only")
    #
    #         if success:
    #             console.print("[green]✅ Combined scraping completed successfully![/green]")
    #             console.print("[cyan]💾 Maximum job coverage achieved![/cyan]")
    #         else:
    #             console.print("[yellow]⚠️ Combined scraping completed with partial results[/yellow]")
    #
    #     except Exception as e:
    #         console.print(f"[red]❌ Combined scraping error: {e}[/red]")

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
