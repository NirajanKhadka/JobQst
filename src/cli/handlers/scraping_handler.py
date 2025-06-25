"""
Scraping Handler for AutoJobAgent CLI.

Handles all job scraping operations including:
- Single site scraping
- Multi-site parallel scraping
- Different scraping modes (automated, parallel, basic)
- Bot detection methods
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from src.core.session import SessionManager
from src.utils.job_analysis_engine import run_intelligent_scraping

console = Console()
logger = logging.getLogger(__name__)


class ScrapingHandler:
    """Handles all job scraping operations."""
    
    def __init__(self, profile: Dict):
        self.profile = profile
        # Create session manager and load session data
        self.session_manager = SessionManager()
        self.session = self._load_session(profile.get('profile_name', 'default'))
    
    def _load_session(self, profile_name: str) -> Dict:
        """Load session data for a profile."""
        try:
            import json
            from pathlib import Path
            
            session_file = Path(f"profiles/{profile_name}/session.json")
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                logger.info(f"✅ Loaded session for profile: {profile_name}")
                return session_data
            else:
                logger.warning(f"⚠️ No session file found for profile: {profile_name}")
                return {}
        except Exception as e:
            logger.error(f"❌ Failed to load session for profile '{profile_name}': {e}")
            return {}
    
    def _save_session(self, profile_name: str, session_data: Dict) -> bool:
        """Save session data for a profile."""
        try:
            import json
            from pathlib import Path
            
            session_file = Path(f"profiles/{profile_name}/session.json")
            session_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved session for profile: {profile_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save session for profile '{profile_name}': {e}")
            return False
    
    def run_scraping(self, sites: Optional[List[str]] = None, keywords: Optional[List[str]] = None, 
                    mode: str = "simple") -> bool:
        """Run job scraping with simplified architecture.

        Args:
            sites: List of sites to scrape (default: ['eluta'])
            keywords: List of keywords to search (default: from profile)
            mode: Scraping mode ('simple', 'multi_worker')

        Returns:
            bool: True if scraping was successful, False otherwise
        """
        console.print(f"[bold blue]🔍 Running {mode} job scraping...[/bold blue]")

        # Set defaults
        if sites is None:
            sites = ['eluta']
        if keywords is None:
            keywords = self.profile.get('keywords', [])

        # Validate and normalize scraping mode
        try:
            mode = self._validate_scraping_mode(mode)
            console.print(f"[cyan]Using scraping mode: {self._get_scraping_mode_description(mode)}[/cyan]")
        except ValueError as e:
            console.print(f"[red]❌ {e}[/red]")
            return False

        try:
            if mode == "simple":
                return self._run_simple_scraping(sites, keywords or [])
            elif mode == "multi_worker":
                return self._run_multi_worker_scraping(sites, keywords or [])
            else:
                console.print(f"[red]❌ Unknown scraping mode: {mode}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]❌ Error during scraping: {e}[/red]")
            import traceback
            traceback.print_exc()
            return False
    
    def _run_simple_scraping(self, sites: List[str], keywords: List[str]) -> bool:
        """Run simple sequential scraping for reliability."""
        from src.scrapers.comprehensive_eluta_scraper import run_comprehensive_scraping
        import asyncio

        console.print("[cyan]🔄 Using simple sequential scraping for reliability[/cyan]")

        try:
            profile_name = self.profile.get('profile_name', 'default')
            jobs = asyncio.run(run_comprehensive_scraping(profile_name, max_jobs_per_keyword=10))

            if jobs:
                # Save jobs to session
                self.session["scraped_jobs"] = jobs
                self._save_session(self.profile.get('profile_name', 'default'), self.session)

                console.print(f"[bold green]✅ Simple scraping found {len(jobs)} jobs![/bold green]")
                return True
            else:
                console.print("[yellow]⚠️ Simple scraping found no jobs[/yellow]")
                return False
        except Exception as e:
            console.print(f"[red]❌ Error in simple scraping: {e}[/red]")
            return False
    
    def _run_multi_worker_scraping(self, sites: List[str], keywords: List[str]) -> bool:
        """Run multi-worker scraping with master worker controlling other workers."""
        from src.core.job_processor_queue import create_job_processor_queue
        from src.scrapers.comprehensive_eluta_scraper import run_comprehensive_scraping
        import asyncio

        console.print("[cyan]⚡ Using multi-worker scraping with master worker coordination[/cyan]")
        
        try:
            profile_name = self.profile.get('profile_name', 'default')
            
            # First, scrape jobs using the comprehensive scraper
            scraped_jobs = asyncio.run(run_comprehensive_scraping(profile_name, max_jobs_per_keyword=20))
            
            if not scraped_jobs:
                console.print("[yellow]⚠️ No jobs found to process with multi-worker system[/yellow]")
                return False
            
            # Create multi-worker queue (2 workers by default)
            def multi_worker_dashboard_callback(data):
                if data.get('type') == 'job_processing_stats':
                    stats = data.get('stats', {})
                    queue_size = data.get('queue_size', 0)
                    console.print(f"[cyan]📊 Multi-Worker Stats: {stats.get('successful', 0)}/{stats.get('total_processed', 0)} successful, Queue: {queue_size}[/cyan]")
            
            queue = create_job_processor_queue(
                profile_name=profile_name,
                num_workers=2,
                dashboard_callback=multi_worker_dashboard_callback
            )
            
            # Start the multi-worker system
            queue.start()
            
            # Add scraped jobs to the queue for processing
            queue.add_jobs_from_scraping(scraped_jobs)
            
            # Wait for completion
            queue.wait_for_completion(timeout=300)  # 5 minutes timeout
            
            # Stop the queue
            queue.stop()
            
            # Get final statistics
            stats = queue.get_stats()
            
            if stats.get('total_processed', 0) > 0:
                console.print(f"[bold green]✅ Multi-worker processing completed! Processed {stats.get('total_processed', 0)} jobs[/bold green]")
                return True
            else:
                console.print("[yellow]⚠️ Multi-worker processing completed with no successful jobs[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Error in multi-worker scraping: {e}[/red]")
            return False
    
    def eluta_enhanced_click_popup_scrape(self) -> List[Dict]:
        """Run Eluta enhanced click-popup scraping."""
        from src.scrapers.comprehensive_eluta_scraper import run_comprehensive_scraping
        import asyncio
        
        console.print("[cyan]🖱️ Running Eluta enhanced click-popup scraping...[/cyan]")
        
        try:
            profile_name = self.profile.get('profile_name', 'default')
            jobs = asyncio.run(run_comprehensive_scraping(profile_name, max_jobs_per_keyword=10))
            
            if jobs:
                self.session["scraped_jobs"] = jobs
                self._save_session(self.profile.get('profile_name', 'default'), self.session)
                console.print(f"[bold green]✅ Found {len(jobs)} jobs![/bold green]")
            
            return jobs
        except Exception as e:
            console.print(f"[red]❌ Error in enhanced scraping: {e}[/red]")
            return []
    
    def _validate_scraping_mode(self, mode: str) -> str:
        """Validate and normalize scraping mode."""
        valid_modes = {
            "simple": "simple",
            "multi_worker": "multi_worker",
            "multi-worker": "multi_worker",
            "multiworker": "multi_worker"
        }
        
        normalized_mode = valid_modes.get(mode.lower(), mode.lower())
        
        if normalized_mode not in ["simple", "multi_worker"]:
            raise ValueError(f"Invalid scraping mode: {mode}. Valid modes: simple, multi_worker")
        
        return normalized_mode
    
    def _get_scraping_mode_description(self, mode: str) -> str:
        """Get human-readable description of scraping mode."""
        descriptions = {
            "simple": "Simple Sequential (Reliable, one-at-a-time processing)",
            "multi_worker": "Multi-Worker (High-performance, parallel processing)"
        }
        
        return descriptions.get(mode, f"Unknown mode: {mode}")
    
    def display_job_summary(self, jobs: List[Dict], operation_name: str = "Job Scraping") -> None:
        """Display a professional summary of scraped jobs."""
        if not jobs:
            console.print("[yellow]No jobs found[/yellow]")
            return
        
        summary = self._create_job_summary(jobs)
        
        console.print(f"\n[bold green]📊 {operation_name} Summary[/bold green]")
        console.print(f"[cyan]Total Jobs:[/cyan] {summary['total_jobs']}")
        console.print(f"[cyan]Jobs with URLs:[/cyan] {summary['jobs_with_urls']}")
        console.print(f"[cyan]URL Coverage:[/cyan] {summary['url_coverage']:.1f}%")
        console.print(f"[cyan]Average Quality Score:[/cyan] {summary['avg_quality']:.1f}/10")
        
        # Show top companies
        if summary['top_companies']:
            console.print(f"\n[cyan]Top Companies:[/cyan] {', '.join(summary['top_companies'][:5])}")
    
    def _create_job_summary(self, jobs: List[Dict]) -> Dict:
        """Create a summary of scraped jobs."""
        total_jobs = len(jobs)
        jobs_with_urls = sum(1 for job in jobs if job.get('url'))
        url_coverage = (jobs_with_urls / total_jobs * 100) if total_jobs > 0 else 0
        
        # Calculate average quality score
        quality_scores = [job.get('quality_score', 5) for job in jobs]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Get top companies
        companies = [job.get('company', 'Unknown') for job in jobs]
        company_counts = {}
        for company in companies:
            company_counts[company] = company_counts.get(company, 0) + 1
        
        top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)
        top_company_names = [company for company, count in top_companies[:5]]
        
        return {
            'total_jobs': total_jobs,
            'jobs_with_urls': jobs_with_urls,
            'url_coverage': url_coverage,
            'avg_quality': avg_quality,
            'top_companies': top_company_names
        } 