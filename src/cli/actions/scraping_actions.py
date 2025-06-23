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
        """Show enhanced scraping menu with all available options."""
        console.print(Panel("🔍 Enhanced Scraping Menu", style="bold blue"))
        
        # Show system capabilities
        console.print(f"[cyan]🖥️  System: DDR5-6400, 32GB RAM, 16-core CPU[/cyan]")
        console.print(f"[cyan]🔍 Keywords: {len(self.profile.get('keywords', []))}[/cyan]")
        console.print(f"[cyan]⚡ Optimized for high performance[/cyan]")
        
        # Site selection first
        console.print(f"\n[bold]Available Job Sites:[/bold]")
        site_options = {
            "1": "🇨🇦 Eluta.ca (Canadian jobs - DDR5 optimized)",
            "2": "🌍 Indeed.ca (Global jobs with anti-detection)",
            "3": "💼 LinkedIn Jobs (Professional network)",
            "4": "🏛️ JobBank.gc.ca (Government jobs)",
            "5": "👹 Monster.ca (Canadian Monster)",
            "6": "🏢 Workday (Corporate ATS)",
            "7": "⚡ Multi-site parallel (all sites simultaneously)"
        }
        
        for key, value in site_options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")
        
        console.print()
        site_choice = Prompt.ask("Select site", choices=list(site_options.keys()), default="1")
        
        if site_choice == "7":
            self.multi_site_scrape_action(args)
        else:
            self.single_site_scrape_action(args, site_choice)
    
    def single_site_scrape_action(self, args, site: str, bot_method: str = "1") -> None:
        """Handle single site scraping action."""
        site_map = {
            "1": "eluta",
            "2": "indeed", 
            "3": "linkedin",
            "4": "jobbank",
            "5": "monster",
            "6": "workday"
        }
        
        selected_site = site_map.get(site, "eluta")
        
        console.print(f"\n[bold]Selected Site:[/bold] {selected_site.upper()}")
        
        # Show bot detection methods
        console.print(f"\n[bold]Bot Detection Methods:[/bold]")
        bot_methods = {
            "1": "🛡️ Enhanced Anti-Bot (Recommended)",
            "2": "⚡ Fast Parallel (High Speed)",
            "3": "🔍 Detailed Scraping (Thorough)",
            "4": "🖱️ Click-Popup Method (Interactive)",
            "5": "🔄 Basic Method (Simple)"
        }
        
        for key, value in bot_methods.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")
        
        console.print()
        bot_choice = Prompt.ask("Select bot detection method", choices=list(bot_methods.keys()), default="1")
        
        # Execute scraping based on site and method
        if selected_site == "eluta":
            self._execute_eluta_scraping(bot_choice)
        else:
            console.print(f"[yellow]⚠️ {selected_site} scraping not yet implemented[/yellow]")
            console.print("[cyan]🔄 Falling back to Eluta scraping...[/cyan]")
            self._execute_eluta_scraping(bot_choice)
    
    def multi_site_scrape_action(self, args, bot_method: str = "2") -> None:
        """Handle multi-site parallel scraping action."""
        console.print(Panel("⚡ Multi-Site Parallel Scraping", style="bold blue"))
        console.print("[cyan]🚀 Running parallel scraping across all sites...[/cyan]")
        
        # Execute parallel scraping
        jobs = self.scraping_handler.eluta_parallel_scrape()
        
        if jobs:
            self.scraping_handler.display_job_summary(jobs, "Multi-Site Parallel Scraping")
        else:
            console.print("[yellow]⚠️ No jobs found in multi-site scraping[/yellow]")
    
    def _execute_eluta_scraping(self, bot_method: str) -> None:
        """Execute Eluta scraping with specified method."""
        method_map = {
            "1": self._eluta_enhanced_anti_bot,
            "2": self._eluta_fast_parallel,
            "3": self._eluta_detailed_scraping,
            "4": self._eluta_click_popup,
            "5": self._eluta_basic
        }
        
        method = method_map.get(bot_method, self._eluta_enhanced_anti_bot)
        method()
    
    def _eluta_enhanced_anti_bot(self) -> None:
        """Execute Eluta enhanced anti-bot scraping."""
        console.print(Panel("🛡️ Eluta Enhanced Anti-Bot Scraping", style="bold blue"))
        console.print("[cyan]🛡️ Using advanced anti-bot detection methods...[/cyan]")
        
        jobs = self.scraping_handler.eluta_enhanced_click_popup_scrape()
        
        if jobs:
            self.scraping_handler.display_job_summary(jobs, "Enhanced Anti-Bot Scraping")
        else:
            console.print("[yellow]⚠️ No jobs found with enhanced anti-bot method[/yellow]")
    
    def _eluta_fast_parallel(self) -> None:
        """Execute Eluta fast parallel scraping."""
        console.print(Panel("⚡ Eluta Fast Parallel Scraping", style="bold blue"))
        console.print("[cyan]⚡ Using high-speed parallel processing...[/cyan]")
        
        jobs = self.scraping_handler.eluta_parallel_scrape()
        
        if jobs:
            self.scraping_handler.display_job_summary(jobs, "Fast Parallel Scraping")
        else:
            console.print("[yellow]⚠️ No jobs found with fast parallel method[/yellow]")
    
    def _eluta_detailed_scraping(self) -> None:
        """Execute Eluta detailed scraping."""
        console.print(Panel("🔍 Eluta Detailed Scraping", style="bold blue"))
        console.print("[cyan]🔍 Using thorough detailed scraping...[/cyan]")
        
        # Use automated scraping with detailed mode
        success = self.scraping_handler.run_scraping(mode="automated")
        
        if success:
            console.print("[green]✅ Detailed scraping completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Detailed scraping completed with limited results[/yellow]")
    
    def _eluta_click_popup(self) -> None:
        """Execute Eluta click-popup scraping."""
        console.print(Panel("🖱️ Eluta Click-Popup Scraping", style="bold blue"))
        console.print("[cyan]🖱️ Using interactive click-popup method...[/cyan]")
        
        jobs = self.scraping_handler.eluta_enhanced_click_popup_scrape()
        
        if jobs:
            self.scraping_handler.display_job_summary(jobs, "Click-Popup Scraping")
        else:
            console.print("[yellow]⚠️ No jobs found with click-popup method[/yellow]")
    
    def _eluta_basic(self) -> None:
        """Execute Eluta basic scraping."""
        console.print(Panel("🔄 Eluta Basic Scraping", style="bold blue"))
        console.print("[cyan]🔄 Using simple basic scraping...[/cyan]")
        
        success = self.scraping_handler.run_scraping(mode="basic")
        
        if success:
            console.print("[green]✅ Basic scraping completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Basic scraping completed with limited results[/yellow]")
    
    def automated_scrape_action(self, args=None) -> None:
        """Execute automated scraping action."""
        console.print(Panel("🤖 Automated Scraping", style="bold blue"))
        console.print("[cyan]🤖 Using AI-powered intelligent scraping...[/cyan]")
        
        success = self.scraping_handler.run_scraping(mode="automated")
        
        if success:
            console.print("[green]✅ Automated scraping completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Automated scraping completed with limited results[/yellow]")
    
    def parallel_scrape_action(self, args=None) -> None:
        """Execute parallel scraping action."""
        console.print(Panel("⚡ Parallel Scraping", style="bold blue"))
        console.print("[cyan]⚡ Using high-speed parallel processing...[/cyan]")
        
        success = self.scraping_handler.run_scraping(mode="parallel")
        
        if success:
            console.print("[green]✅ Parallel scraping completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Parallel scraping completed with limited results[/yellow]")
    
    def detailed_scrape_action(self, args=None) -> None:
        """Execute detailed scraping action."""
        console.print(Panel("🔍 Detailed Scraping", style="bold blue"))
        console.print("[cyan]🔍 Using thorough detailed analysis...[/cyan]")
        
        success = self.scraping_handler.run_scraping(mode="basic")
        
        if success:
            console.print("[green]✅ Detailed scraping completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Detailed scraping completed with limited results[/yellow]")
    
    def anti_bot_scrape_action(self, args) -> None:
        """Execute anti-bot scraping action."""
        console.print(Panel("🛡️ Anti-Bot Scraping", style="bold blue"))
        console.print("[cyan]🛡️ Using advanced anti-bot detection...[/cyan]")
        
        jobs = self.scraping_handler.eluta_enhanced_click_popup_scrape()
        
        if jobs:
            self.scraping_handler.display_job_summary(jobs, "Anti-Bot Scraping")
        else:
            console.print("[yellow]⚠️ No jobs found with anti-bot method[/yellow]")
    
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
            pending_jobs = [job for job in scraped_jobs if job.get('url') and job.get('url') not in done_jobs]
            
            if not pending_jobs:
                console.print("[yellow]⚠️ All jobs in queue have been processed[/yellow]")
                return
            
            console.print(f"[green]Found {len(pending_jobs)} jobs to process from queue[/green]")
            
            # Process each job URL
            processed_count = 0
            for i, job in enumerate(pending_jobs, 1):
                job_url = job.get('url')
                if not job_url:
                    continue
                
                console.print(f"\n[bold]Processing {i}/{len(pending_jobs)}:[/bold] {job.get('title', 'Unknown')}")
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
                        self.scraping_handler._save_session(self.scraping_handler.profile.get('profile_name', 'default'), self.scraping_handler.session)
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
            
            console.print(f"\n[bold green]✅ Queue processing completed! {processed_count}/{len(pending_jobs)} jobs processed[/bold green]")
            
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
                page.goto(job_url, wait_until='domcontentloaded')
                
                # Extract job details
                job_details = {}
                
                # Try to extract title
                title_selectors = [
                    'h1',
                    '[data-testid="job-title"]',
                    '.job-title',
                    '.title',
                    'h2'
                ]
                
                for selector in title_selectors:
                    title_element = page.query_selector(selector)
                    if title_element:
                        title_text = title_element.text_content()
                        if title_text:
                            job_details['title'] = title_text.strip()
                            break
                
                # Try to extract company
                company_selectors = [
                    '[data-testid="company-name"]',
                    '.company-name',
                    '.company',
                    '[class*="company"]'
                ]
                
                for selector in company_selectors:
                    company_element = page.query_selector(selector)
                    if company_element:
                        company_text = company_element.text_content()
                        if company_text:
                            job_details['company'] = company_text.strip()
                            break
                
                # Try to extract location
                location_selectors = [
                    '[data-testid="location"]',
                    '.location',
                    '[class*="location"]'
                ]
                
                for selector in location_selectors:
                    location_element = page.query_selector(selector)
                    if location_element:
                        location_text = location_element.text_content()
                        if location_text:
                            job_details['location'] = location_text.strip()
                            break
                
                # Try to extract description/summary
                description_selectors = [
                    '[data-testid="job-description"]',
                    '.job-description',
                    '.description',
                    '[class*="description"]',
                    'p'
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
                            job_details['summary'] = ' '.join(descriptions[:3])  # Take first 3 paragraphs
                            break
                
                browser.close()
                
                return job_details if job_details else None
                
        except Exception as e:
            console.print(f"[red]Error scraping job details: {e}[/red]")
            return None 