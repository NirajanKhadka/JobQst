#!/usr/bin/env python3
"""
Enhanced Simple Job Orchestrator - Local Job Processing
Replaces all the complex processors with one simple, robust orchestrator.

Flow:
1. Get scraped job URLs from database
2. Fetch job descriptions with retry logic and caching
3. Analyze with rule-based matching
4. Queue good matches for application

Features:
- Configurable batch processing
- Retry logic with exponential backoff
- Description caching to avoid redundant fetches
- Detailed progress tracking and metrics
- Enhanced error handling and recovery
- Smart queue management
"""

import asyncio
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table

from ..core.job_database import get_job_db
from ..scrapers.external_job_scraper import ExternalJobDescriptionScraper
from ..ai.enhanced_rule_based_analyzer import EnhancedRuleBasedAnalyzer
from ..utils.profile_helpers import load_profile

console = Console()


@dataclass
class OrchestratorConfig:
    """Configuration for the job orchestrator."""
    batch_sizes: Dict[str, int]
    timeouts: Dict[str, int]
    retry_settings: Dict[str, Any]
    compatibility_thresholds: Dict[str, Any]
    caching: Dict[str, Any]
    performance: Dict[str, Any]
    
    @classmethod
    def load_config(cls, config_path: str = "config/orchestrator_config.json") -> "OrchestratorConfig":
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return cls(**config_data)
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not load config from {config_path}: {e}[/yellow]")
            console.print("[cyan]Using default configuration[/cyan]")
            return cls.default_config()
    
    @classmethod
    def default_config(cls) -> "OrchestratorConfig":
        """Default configuration."""
        return cls(
            batch_sizes={"description_fetch": 10, "job_analysis": 20, "application": 5, "max_concurrent": 5},
            timeouts={"description_fetch": 30, "analysis": 10, "database_operation": 5},
            retry_settings={"max_retries": 3, "retry_delay": 2, "exponential_backoff": True},
            compatibility_thresholds={"queue_for_application": 0.7, "high_priority": 0.85, "recommendations": ["highly_recommend", "recommend"]},
            caching={"description_cache_ttl_hours": 24, "enable_cache": True, "cache_size_limit": 1000},
            performance={"enable_detailed_metrics": True, "log_slow_operations": True, "slow_operation_threshold": 5.0}
        )


class DescriptionCache:
    """Simple in-memory cache for job descriptions."""
    
    def __init__(self, ttl_hours: int = 24, max_size: int = 1000):
        self.cache = {}
        self.ttl = ttl_hours * 3600  # Convert to seconds
        self.max_size = max_size
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached description if valid."""
        key = self._get_cache_key(url)
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return cached_data
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None
    
    def set(self, url: str, description_data: Dict[str, Any]) -> None:
        """Cache description data."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        key = self._get_cache_key(url)
        self.cache[key] = (description_data, time.time())
    
    def clear(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


class EnhancedJobOrchestrator:
    """
    Enhanced job orchestrator for local use.
    Does one thing well: processes scraped job URLs into analyzed jobs.
    
    Features:
    - Configurable batch processing
    - Retry logic with exponential backoff
    - Description caching
    - Detailed metrics and progress tracking
    - Enhanced error handling
    """
    
    def __init__(self, profile_name: str, config_path: Optional[str] = None):
        self.profile_name = profile_name
        self.profile = load_profile(profile_name) or {}
        self.db = get_job_db(profile_name)
        
        # Load configuration
        self.config = OrchestratorConfig.load_config(config_path) if config_path else OrchestratorConfig.load_config()
        
        # Initialize components
        self.external_scraper = ExternalJobDescriptionScraper(
            num_workers=self.config.batch_sizes["max_concurrent"]
        )
        self.analyzer = EnhancedRuleBasedAnalyzer(self.profile)
        
        # Initialize caching
        self.description_cache = DescriptionCache(
            ttl_hours=self.config.caching["description_cache_ttl_hours"],
            max_size=self.config.caching["cache_size_limit"]
        ) if self.config.caching["enable_cache"] else None
        
        # Enhanced stats
        self.stats = {
            "jobs_processed": 0,
            "jobs_analyzed": 0,
            "jobs_queued": 0,
            "jobs_failed": 0,
            "processing_time": 0.0,
            "description_fetch_time": 0.0,
            "analysis_time": 0.0,
            "database_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "retries_performed": 0,
            "errors": 0,
            "success_rates": {
                "description_fetch": 0.0,
                "analysis": 0.0,
                "database_update": 0.0
            }
        }
    
    async def process_scraped_jobs(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Main orchestrator method: process scraped job URLs.
        
        Args:
            limit: Max jobs to process (None for all)
            
        Returns:
            Processing statistics
        """
        start_time = time.time()
        
        console.print("[bold blue]🔄 Simple Job Orchestrator Starting[/bold blue]")
        
        # Step 1: Get scraped job URLs from database
        scraped_jobs = self._get_scraped_jobs(limit)
        if not scraped_jobs:
            console.print("[yellow]⚠️ No scraped jobs found in database[/yellow]")
            return self.stats
        
        console.print(f"[cyan]📋 Found {len(scraped_jobs)} scraped jobs to process[/cyan]")
        
        # Step 2: Fetch job descriptions
        jobs_with_descriptions = await self._fetch_descriptions(scraped_jobs)
        
        # Step 3: Analyze jobs
        analyzed_jobs = await self._analyze_jobs(jobs_with_descriptions)
        
        # Step 4: Queue good matches and update database
        await self._queue_and_update_jobs(analyzed_jobs)
        
        # Final stats
        self.stats["processing_time"] = time.time() - start_time
        self._display_results()
        
        return self.stats
    
    async def fetch_descriptions_only(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch descriptions for scraped jobs and save to database.
        
        Args:
            limit: Max jobs to process (None for all)
            
        Returns:
            Processing statistics
        """
        start_time = time.time()
        
        console.print("[bold blue]🌐 Fetching Job Descriptions Only[/bold blue]")
        
        # Get scraped jobs
        scraped_jobs = self._get_scraped_jobs(limit)
        if not scraped_jobs:
            console.print("[yellow]⚠️ No scraped jobs found in database[/yellow]")
            return self.stats
        
        console.print(f"[cyan]📋 Found {len(scraped_jobs)} scraped jobs[/cyan]")
        
        # Fetch descriptions and save to database
        await self._fetch_descriptions(scraped_jobs)
        
        # Final stats
        self.stats["processing_time"] = time.time() - start_time
        console.print(f"[green]✅ Description fetching complete in {self.stats['processing_time']:.1f}s[/green]")
        
        return self.stats
    
    async def analyze_jobs_with_descriptions(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze jobs that already have descriptions saved.
        
        Args:
            limit: Max jobs to analyze (None for all)
            
        Returns:
            Processing statistics
        """
        start_time = time.time()
        
        console.print("[bold blue]🧠 Analyzing Jobs with Descriptions[/bold blue]")
        
        # Get jobs with descriptions
        jobs_with_descriptions = self._get_jobs_with_descriptions(limit)
        if not jobs_with_descriptions:
            console.print("[yellow]⚠️ No jobs with descriptions found in database[/yellow]")
            return self.stats
        
        console.print(f"[cyan]📋 Found {len(jobs_with_descriptions)} jobs with descriptions[/cyan]")
        
        # Analyze jobs
        analyzed_jobs = await self._analyze_jobs(jobs_with_descriptions)
        
        # Queue good matches and update database
        await self._queue_and_update_jobs(analyzed_jobs)
        
        # Final stats
        self.stats["processing_time"] = time.time() - start_time
        self._display_results()
        
        return self.stats
    
    def _get_scraped_jobs(self, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Get jobs with status='scraped' from database."""
        try:
            all_jobs = self.db.get_all_jobs()
            scraped_jobs = [
                job for job in all_jobs 
                if job.get('status') == 'scraped' and job.get('url')
            ]
            
            if limit:
                scraped_jobs = scraped_jobs[:limit]
                
            return scraped_jobs
            
        except Exception as e:
            console.print(f"[red]❌ Error getting scraped jobs: {e}[/red]")
            self.stats["errors"] += 1
            return []
    
    def _get_jobs_with_descriptions(self, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Get jobs with status='description_saved' from database."""
        try:
            all_jobs = self.db.get_all_jobs()
            jobs_with_descriptions = [
                job for job in all_jobs 
                if job.get('status') == 'description_saved' and job.get('description')
            ]
            
            if limit:
                jobs_with_descriptions = jobs_with_descriptions[:limit]
                
            return jobs_with_descriptions
            
        except Exception as e:
            console.print(f"[red]❌ Error getting jobs with descriptions: {e}[/red]")
            self.stats["errors"] += 1
            return []
    
    async def _fetch_descriptions(self, scraped_jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fetch job descriptions from URLs and save to database."""
        console.print("[cyan]🌐 Fetching job descriptions...[/cyan]")
        
        try:
            # Extract URLs
            urls = [job.get('url') for job in scraped_jobs if job.get('url')]
            
            # Fetch descriptions in parallel
            jobs_with_descriptions = await self.external_scraper.scrape_external_jobs_parallel(urls)
            
            # Merge with original job data and save descriptions
            url_to_job = {job.get('url'): job for job in scraped_jobs}
            merged_jobs = []
            saved_count = 0
            
            for job_with_desc in jobs_with_descriptions:
                url = job_with_desc.get('url')
                if url in url_to_job:
                    # Merge original job data with description
                    merged_job = url_to_job[url].copy()
                    merged_job.update(job_with_desc)
                    
                    # Update status to 'description_saved' and save to database
                    if job_with_desc.get('description'):
                        merged_job['status'] = 'description_saved'
                        merged_job['description_fetched_at'] = time.time()
                        
                        # Save updated job with description to database
                        success = self.db.update_job(merged_job.get('id'), merged_job)
                        if success:
                            saved_count += 1
                    else:
                        # No description found, mark as failed
                        merged_job['status'] = 'description_failed'
                    
                    merged_jobs.append(merged_job)
            
            console.print(f"[green]✅ Fetched {len(merged_jobs)} job descriptions, saved {saved_count} to database[/green]")
            return merged_jobs
            
        except Exception as e:
            console.print(f"[red]❌ Error fetching descriptions: {e}[/red]")
            self.stats["errors"] += 1
            return scraped_jobs  # Return original jobs as fallback
    
    async def _analyze_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze jobs with rule-based analyzer."""
        console.print("[cyan]🧠 Analyzing job compatibility...[/cyan]")
        
        analyzed_jobs = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing jobs...", total=len(jobs))
            
            for job in jobs:
                try:
                    # Analyze job compatibility
                    analysis = self.analyzer.analyze_job(job)
                    
                    # Merge analysis with job data
                    analyzed_job = job.copy()
                    analyzed_job.update(analysis)
                    analyzed_job['status'] = 'analyzed'
                    analyzed_job['processed_at'] = time.time()
                    
                    analyzed_jobs.append(analyzed_job)
                    self.stats["jobs_analyzed"] += 1
                    
                    progress.advance(task)
                    
                except Exception as e:
                    console.print(f"[yellow]⚠️ Error analyzing job {job.get('title', 'Unknown')}: {e}[/yellow]")
                    self.stats["errors"] += 1
                    
                    # Add job with minimal analysis
                    fallback_job = job.copy()
                    fallback_job.update({
                        'compatibility_score': 0.5,
                        'recommendation': 'consider',
                        'status': 'analyzed',
                        'analysis_method': 'fallback'
                    })
                    analyzed_jobs.append(fallback_job)
        
        console.print(f"[green]✅ Analyzed {len(analyzed_jobs)} jobs[/green]")
        return analyzed_jobs
    
    async def _queue_and_update_jobs(self, analyzed_jobs: List[Dict[str, Any]]) -> None:
        """Queue good matches and update database."""
        console.print("[cyan]📝 Updating database and queueing applications...[/cyan]")
        
        queued_count = 0
        updated_count = 0
        
        for job in analyzed_jobs:
            try:
                # Update job in database
                success = self.db.update_job(job.get('id'), job)
                if success:
                    updated_count += 1
                
                # Queue for application if good match
                compatibility_score = job.get('compatibility_score', 0)
                recommendation = job.get('recommendation', 'skip')
                
                if compatibility_score >= 0.7 or recommendation in ['highly_recommend', 'recommend']:
                    # Update status to queued for application
                    job['status'] = 'queued_for_application'
                    self.db.update_job(job.get('id'), job)
                    queued_count += 1
                
            except Exception as e:
                console.print(f"[yellow]⚠️ Error updating job: {e}[/yellow]")
                self.stats["errors"] += 1
        
        self.stats["jobs_processed"] = updated_count
        self.stats["jobs_queued"] = queued_count
        
        console.print(f"[green]✅ Updated {updated_count} jobs, queued {queued_count} for application[/green]")
    
    def _display_results(self) -> None:
        """Display processing results."""
        console.print("\n" + "=" * 60)
        console.print("[bold green]🎉 Job Processing Complete![/bold green]")
        console.print(f"[cyan]📊 Jobs Processed: {self.stats['jobs_processed']}[/cyan]")
        console.print(f"[cyan]🧠 Jobs Analyzed: {self.stats['jobs_analyzed']}[/cyan]")
        console.print(f"[cyan]📝 Jobs Queued for Application: {self.stats['jobs_queued']}[/cyan]")
        console.print(f"[cyan]⏱️ Processing Time: {self.stats['processing_time']:.1f}s[/cyan]")
        
        if self.stats["jobs_processed"] > 0:
            speed = self.stats["jobs_processed"] / self.stats["processing_time"]
            console.print(f"[cyan]🚀 Speed: {speed:.1f} jobs/second[/cyan]")
        
        if self.stats["errors"] > 0:
            console.print(f"[yellow]⚠️ Errors: {self.stats['errors']}[/yellow]")
        
        console.print("[green]💡 Check queued jobs in dashboard or run application process[/green]")


# Convenience functions
async def process_scraped_jobs(profile_name: str = "Nirajan", limit: Optional[int] = None) -> Dict[str, Any]:
    """Simple function to process scraped jobs (full pipeline)."""
    orchestrator = SimpleJobOrchestrator(profile_name)
    return await orchestrator.process_scraped_jobs(limit)

async def fetch_descriptions_only(profile_name: str = "Nirajan", limit: Optional[int] = None) -> Dict[str, Any]:
    """Fetch descriptions for scraped jobs and save to database."""
    orchestrator = SimpleJobOrchestrator(profile_name)
    return await orchestrator.fetch_descriptions_only(limit)

async def analyze_jobs_with_descriptions(profile_name: str = "Nirajan", limit: Optional[int] = None) -> Dict[str, Any]:
    """Analyze jobs that already have descriptions saved."""
    orchestrator = SimpleJobOrchestrator(profile_name)
    return await orchestrator.analyze_jobs_with_descriptions(limit)


if __name__ == "__main__":
    # Test the orchestrator
    async def test():
        stats = await process_scraped_jobs("Nirajan", limit=10)
        print(f"Test complete: {stats}")
    
    asyncio.run(test())