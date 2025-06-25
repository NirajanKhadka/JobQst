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

from src.core import utils
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
                    mode: str = "automated") -> bool:
        """Run job scraping with specified parameters.

        Args:
            sites: List of sites to scrape (default: ['eluta'])
            keywords: List of keywords to search (default: from profile)
            mode: Scraping mode ('automated', 'parallel', 'basic')

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
            if mode == "automated":
                return self._run_automated_scraping()
            elif mode == "parallel":
                return self._run_parallel_scraping(sites)
            else:  # basic mode
                return self._run_basic_scraping()

        except Exception as e:
            console.print(f"[red]❌ Error during scraping: {e}[/red]")
            import traceback
            traceback.print_exc()
            return False
    
    def _run_automated_scraping(self) -> bool:
        """Run automated scraping with AI filtering."""
        console.print("[cyan]🧠 Using automated scraping with AI filtering[/cyan]")
        success = run_intelligent_scraping(self.profile['profile_name'], max_jobs=15)

        if success:
            console.print("[bold green]✅ Automated scraping completed successfully![/bold green]")
            return True
        else:
            console.print("[yellow]⚠️ Automated scraping completed with limited results[/yellow]")
            return False
    
    def _run_parallel_scraping(self, sites: List[str]) -> bool:
        """Run parallel scraping for speed."""
        from src.scrapers.parallel_job_scraper import run_parallel_scraping

        console.print("[cyan]⚡ Using parallel scraping for speed[/cyan]")
        
        # Run parallel scraping asynchronously
        profile_name = self.profile.get('profile_name', 'default')
        jobs = asyncio.run(run_parallel_scraping(profile_name, num_workers=3, max_jobs_per_keyword=20))

        if jobs:
            # Save jobs to session
            self.session["scraped_jobs"] = jobs
            self._save_session(self.profile.get('profile_name', 'default'), self.session)

            console.print(f"[bold green]✅ Parallel scraping found {len(jobs)} jobs![/bold green]")
            return True
        else:
            console.print("[yellow]⚠️ Parallel scraping found no jobs[/yellow]")
            return False
    
    def _run_basic_scraping(self) -> bool:
        """Run basic scraping using working scraper."""
        from scrapers.eluta_working import ElutaWorkingScraper
        from playwright.sync_api import sync_playwright

        console.print("[cyan]🔍 Using working Eluta scraper[/cyan]")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            scraper = ElutaWorkingScraper(self.profile, browser_context=context)
            jobs = list(scraper.scrape_jobs())
            browser.close()

        if jobs:
            # Save jobs to session
            self.session["scraped_jobs"] = jobs
            self._save_session(self.profile.get('profile_name', 'default'), self.session)

            console.print(f"[bold green]✅ Basic scraping found {len(jobs)} jobs![/bold green]")
            return True
        else:
            console.print("[yellow]⚠️ Basic scraping found no jobs[/yellow]")
            return False
    
    def eluta_parallel_scrape(self) -> List[Dict]:
        """Run Eluta parallel scraping."""
        from scrapers.eluta_optimized_parallel import ElutaOptimizedParallelScraper
        
        console.print("[cyan]⚡ Running Eluta parallel scraping...[/cyan]")
        
        scraper = ElutaOptimizedParallelScraper(self.profile)
        jobs = list(scraper.scrape_jobs())
        
        if jobs:
            self.session["scraped_jobs"] = jobs
            self._save_session(self.profile.get('profile_name', 'default'), self.session)
            console.print(f"[bold green]✅ Found {len(jobs)} jobs![/bold green]")
        
        return jobs
    
    def eluta_enhanced_click_popup_scrape(self) -> List[Dict]:
        """Run Eluta enhanced click-popup scraping."""
        from scrapers.eluta_enhanced import ElutaEnhancedScraper
        
        console.print("[cyan]🖱️ Running Eluta enhanced click-popup scraping...[/cyan]")
        
        scraper = ElutaEnhancedScraper(self.profile)
        jobs = list(scraper.scrape_jobs())
        
        if jobs:
            self.session["scraped_jobs"] = jobs
            self._save_session(self.profile.get('profile_name', 'default'), self.session)
            console.print(f"[bold green]✅ Found {len(jobs)} jobs![/bold green]")
        
        return jobs
    
    def _validate_scraping_mode(self, mode: str) -> str:
        """Validate and normalize scraping mode."""
        valid_modes = {
            "automated": "automated",
            "parallel": "parallel", 
            "basic": "basic",
            "intelligent": "automated",
            "fast": "parallel",
            "simple": "basic"
        }
        
        normalized_mode = valid_modes.get(mode.lower(), mode.lower())
        
        if normalized_mode not in ["automated", "parallel", "basic"]:
            raise ValueError(f"Invalid scraping mode: {mode}. Valid modes: {list(valid_modes.keys())}")
        
        return normalized_mode
    
    def _get_scraping_mode_description(self, mode: str) -> str:
        """Get human-readable description of scraping mode."""
        descriptions = {
            "automated": "Intelligent scraping with AI filtering and analysis",
            "parallel": "High-speed parallel scraping with multiple workers",
            "basic": "Simple, reliable scraping with basic filtering"
        }
        return descriptions.get(mode, "Unknown mode")
    
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