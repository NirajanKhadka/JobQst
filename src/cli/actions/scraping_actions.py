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
        
        # Show simplified scraping methods
        console.print(f"\n[bold]Scraping Methods:[/bold]")
        bot_methods = {
            "1": "🔄 Simple Sequential (Reliable, one-at-a-time)",
            "2": "⚡ Multi-Worker (High-performance, parallel)"
        }
        
        for key, value in bot_methods.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")
        
        console.print()
        bot_choice = Prompt.ask("Select scraping method", choices=list(bot_methods.keys()), default="1")
        
        # Execute scraping based on site and method
        if selected_site == "eluta":
            self._execute_eluta_scraping(bot_choice)
        else:
            console.print(f"[yellow]⚠️ {selected_site} scraping not yet implemented[/yellow]")
            console.print("[cyan]🔄 Falling back to Eluta scraping...[/cyan]")
            self._execute_eluta_scraping(bot_choice)
    
    def multi_site_scrape_action(self, args, bot_method: str = "2") -> None:
        """Handle multi-site parallel scraping action using simplified architecture."""
        console.print(Panel("⚡ Multi-Site Scraping (Simplified Architecture)", style="bold blue"))
        console.print("[cyan]🚀 Running multi-site scraping with simplified architecture...[/cyan]")
        
        # Use the simplified multi-worker method
        success = self.scraping_handler.run_scraping(mode="multi_worker")
        
        if success:
            console.print("[green]✅ Multi-site scraping completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Multi-site scraping completed with limited results[/yellow]")
    
    def _execute_eluta_scraping(self, method_choice: str) -> None:
        """Execute Eluta scraping with the selected method."""
        if method_choice == "1":
            # Simple sequential method
            console.print("[cyan]🔄 Using simple sequential scraping...[/cyan]")
            success = self.scraping_handler.run_scraping(mode="simple")
        else:
            # Multi-worker method
            console.print("[cyan]⚡ Using multi-worker scraping...[/cyan]")
            success = self.scraping_handler.run_scraping(mode="multi_worker")
        
        if success:
            console.print("[green]✅ Scraping completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Scraping completed with limited results[/yellow]")
    
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