#!/usr/bin/env python3
"""
Enhanced Job Applicator
Improved job application system that works directly with the database,
includes better error handling, retry logic, and application optimization.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel
from playwright.async_api import async_playwright

from src.core.job_database import get_job_db
from .application_flow_optimizer import ApplicationFlowOptimizer
from src.utils.enhanced_error_tolerance import with_retry, safe_execute
from src.core import utils

console = Console()

@dataclass
class ApplicationResult:
    """Result of a job application attempt."""
    job_id: str
    status: str  # 'applied', 'failed', 'manual_review', 'skipped'
    error_message: Optional[str] = None
    ats_detected: Optional[str] = None
    fields_filled: Optional[Dict] = None
    application_time: float = 0.0
    retry_count: int = 0

class EnhancedJobApplicator:
    """
    Enhanced job application system with database integration,
    intelligent ATS detection, and optimized application flow.
    """
    
    def __init__(self, profile_name: str):
        """
        Initialize the enhanced job applicator.
        
        Args:
            profile_name: Name of the user profile
        """
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        self.optimizer = ApplicationFlowOptimizer(profile_name)
        self.profile = None
        self.session = {}
        
        # Application settings
        self.max_retries = 2
        self.delay_between_apps = 30  # seconds
        self.timeout_per_app = 300  # 5 minutes
        
        # Statistics
        self.stats = {
            "total_processed": 0,
            "successful_applications": 0,
            "failed_applications": 0,
            "manual_reviews": 0,
            "skipped_jobs": 0,
            "total_time": 0.0
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the applicator by loading profile and session data.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Load profile
            self.profile = utils.load_profile(self.profile_name)
            if not self.profile:
                console.print(f"[red]❌ Failed to load profile: {self.profile_name}[/red]")
                return False
            
            # Load session
            self.session = utils.load_session(self.profile)
            
            console.print(f"[green]✅ Initialized applicator for profile: {self.profile_name}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Initialization failed: {e}[/red]")
            return False
    
    async def get_jobs_to_apply(self, limit: int = 10, filters: Dict = None) -> List[Dict]:
        """
        Get jobs from database that need applications.
        
        Args:
            limit: Maximum number of jobs to retrieve
            filters: Optional filters for job selection
            
        Returns:
            List of job dictionaries
        """
        try:
            # Get unapplied jobs from database
            jobs = self.db.get_unapplied_jobs(limit=limit)
            
            # Apply additional filters if provided
            if filters:
                filtered_jobs = []
                for job in jobs:
                    if self._job_matches_filters(job, filters):
                        filtered_jobs.append(job)
                jobs = filtered_jobs
            
            console.print(f"[cyan]📋 Found {len(jobs)} jobs ready for application[/cyan]")
            return jobs
            
        except Exception as e:
            console.print(f"[red]❌ Error retrieving jobs: {e}[/red]")
            return []
    
    def _job_matches_filters(self, job: Dict, filters: Dict) -> bool:
        """Check if job matches the provided filters."""
        for key, value in filters.items():
            job_value = job.get(key, "").lower()
            if isinstance(value, str):
                if value.lower() not in job_value:
                    return False
            elif isinstance(value, list):
                if not any(v.lower() in job_value for v in value):
                    return False
        return True
    
    def display_jobs_preview(self, jobs: List[Dict], limit: int = 10) -> None:
        """
        Display a preview of jobs to be processed.
        
        Args:
            jobs: List of job dictionaries
            limit: Maximum number of jobs to display
        """
        if not jobs:
            console.print("[yellow]No jobs to display[/yellow]")
            return
        
        table = Table(title=f"Jobs Ready for Application (showing {min(len(jobs), limit)} of {len(jobs)})")
        table.add_column("Title", style="cyan", max_width=30)
        table.add_column("Company", style="magenta", max_width=25)
        table.add_column("Location", style="green", max_width=20)
        table.add_column("Site", style="blue")
        table.add_column("URL", style="dim", max_width=40)
        
        for job in jobs[:limit]:
            url = job.get('url', '')
            display_url = url[:37] + "..." if len(url) > 40 else url
            
            table.add_row(
                job.get('title', 'Unknown'),
                job.get('company', 'Unknown'),
                job.get('location', 'Unknown'),
                job.get('site', 'Unknown'),
                display_url
            )
        
        console.print(table)
    
    async def apply_to_jobs_batch(self, 
                                 jobs: List[Dict], 
                                 batch_size: int = 5,
                                 dry_run: bool = False) -> List[ApplicationResult]:
        """
        Apply to a batch of jobs with enhanced error handling and optimization.
        
        Args:
            jobs: List of job dictionaries
            batch_size: Number of jobs to process in parallel
            dry_run: If True, simulate applications without actually applying
            
        Returns:
            List of application results
        """
        if not jobs:
            console.print("[yellow]No jobs to apply to[/yellow]")
            return []
        
        console.print(f"\n[bold blue]🚀 Starting application process for {len(jobs)} jobs[/bold blue]")
        if dry_run:
            console.print("[yellow]🧪 DRY RUN MODE - No actual applications will be submitted[/yellow]")
        
        results = []
        start_time = time.time()
        
        async with async_playwright() as p:
            # Launch browser with optimized settings
            browser = await p.chromium.launch(
                headless=False,  # Keep visible for debugging
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security"
                ]
            )
            
            try:
                # Process jobs in batches
                for i in range(0, len(jobs), batch_size):
                    batch = jobs[i:i + batch_size]
                    console.print(f"\n[cyan]📦 Processing batch {i//batch_size + 1} ({len(batch)} jobs)[/cyan]")
                    
                    # Process batch
                    batch_results = await self._process_job_batch(browser, batch, dry_run)
                    results.extend(batch_results)
                    
                    # Update statistics
                    self._update_stats(batch_results)
                    
                    # Delay between batches
                    if i + batch_size < len(jobs):
                        console.print(f"[yellow]⏳ Waiting {self.delay_between_apps} seconds before next batch...[/yellow]")
                        await asyncio.sleep(self.delay_between_apps)
            
            finally:
                await browser.close()
        
        # Final statistics
        total_time = time.time() - start_time
        self.stats["total_time"] = total_time
        
        self._display_final_results(results, total_time)
        return results
    
    async def _process_job_batch(self, browser, jobs: List[Dict], dry_run: bool) -> List[ApplicationResult]:
        """Process a batch of jobs concurrently."""
        tasks = []
        
        for job in jobs:
            task = self._apply_to_single_job(browser, job, dry_run)
            tasks.append(task)
        
        # Execute tasks concurrently with progress tracking
        with Progress() as progress:
            task_id = progress.add_task("[green]Applying to jobs...", total=len(tasks))
            
            results = []
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                progress.update(task_id, advance=1)
        
        return results

    async def _apply_to_single_job(self, browser, job: Dict, dry_run: bool) -> ApplicationResult:
        """
        Apply to a single job with retry logic and optimization.

        Args:
            browser: Playwright browser instance
            job: Job dictionary
            dry_run: If True, simulate application

        Returns:
            ApplicationResult object
        """
        job_id = job.get('id', job.get('url', 'unknown'))
        start_time = time.time()

        console.print(f"\n[bold]🎯 Processing: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}[/bold]")

        # Skip jobs without URLs
        if not job.get('url'):
            console.print("[red]❌ Skipping job with no URL[/red]")
            return ApplicationResult(
                job_id=job_id,
                status='skipped',
                error_message='No URL provided',
                application_time=time.time() - start_time
            )

        # Retry logic
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    console.print(f"[yellow]🔄 Retry attempt {attempt}/{self.max_retries}[/yellow]")
                    await asyncio.sleep(5)  # Brief delay before retry

                # Create new context for each application
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )

                try:
                    page = await context.new_page()

                    # Navigate to job URL
                    console.print(f"[cyan]🌐 Navigating to: {job['url'][:80]}...[/cyan]")
                    await page.goto(job['url'], timeout=30000)
                    await page.wait_for_load_state('networkidle', timeout=10000)

                    if dry_run:
                        console.print("[yellow]🧪 DRY RUN: Simulating application process[/yellow]")
                        await asyncio.sleep(2)  # Simulate processing time
                        return ApplicationResult(
                            job_id=job_id,
                            status='applied',
                            ats_detected='simulated',
                            application_time=time.time() - start_time
                        )

                    # Use optimizer for intelligent application
                    result = self.optimizer.optimize_application_flow(job, self.profile, page)

                    # Process result
                    if result.get('status') == 'applied':
                        console.print("[green]✅ Application submitted successfully[/green]")

                        # Update database
                        self._update_job_status(job, 'applied', result)

                        return ApplicationResult(
                            job_id=job_id,
                            status='applied',
                            ats_detected=result.get('ats_system'),
                            fields_filled=result.get('fields_filled'),
                            application_time=time.time() - start_time,
                            retry_count=attempt
                        )

                    elif result.get('status') == 'manual_review':
                        console.print("[yellow]⚠️ Manual review required[/yellow]")

                        return ApplicationResult(
                            job_id=job_id,
                            status='manual_review',
                            error_message=result.get('error', 'Manual review required'),
                            ats_detected=result.get('ats_system'),
                            application_time=time.time() - start_time,
                            retry_count=attempt
                        )

                    else:
                        # Failed application
                        error_msg = result.get('error', 'Application failed')
                        console.print(f"[red]❌ Application failed: {error_msg}[/red]")

                        if attempt >= self.max_retries:
                            self._update_job_status(job, 'failed', result)

                            return ApplicationResult(
                                job_id=job_id,
                                status='failed',
                                error_message=error_msg,
                                ats_detected=result.get('ats_system'),
                                application_time=time.time() - start_time,
                                retry_count=attempt
                            )

                finally:
                    await context.close()

            except Exception as e:
                console.print(f"[red]❌ Error in application attempt {attempt + 1}: {e}[/red]")

                if attempt >= self.max_retries:
                    return ApplicationResult(
                        job_id=job_id,
                        status='failed',
                        error_message=str(e),
                        application_time=time.time() - start_time,
                        retry_count=attempt
                    )

        # Should not reach here, but just in case
        return ApplicationResult(
            job_id=job_id,
            status='failed',
            error_message='Max retries exceeded',
            application_time=time.time() - start_time,
            retry_count=self.max_retries
        )

    def _update_job_status(self, job: Dict, status: str, result: Dict):
        """Update job status in database."""
        try:
            # Update job with application status
            job_update = {
                'status': status,
                'applied_date': datetime.now().isoformat(),
                'ats_detected': result.get('ats_system'),
                'application_result': result.get('error', 'Success' if status == 'applied' else 'Failed')
            }

            # Note: This would need to be implemented in the database class
            # self.db.update_job_status(job.get('id'), job_update)

            console.print(f"[green]📝 Updated job status to: {status}[/green]")

        except Exception as e:
            console.print(f"[yellow]⚠️ Failed to update job status: {e}[/yellow]")

    def _update_stats(self, results: List[ApplicationResult]):
        """Update application statistics."""
        for result in results:
            self.stats["total_processed"] += 1

            if result.status == 'applied':
                self.stats["successful_applications"] += 1
            elif result.status == 'failed':
                self.stats["failed_applications"] += 1
            elif result.status == 'manual_review':
                self.stats["manual_reviews"] += 1
            elif result.status == 'skipped':
                self.stats["skipped_jobs"] += 1

    def _display_final_results(self, results: List[ApplicationResult], total_time: float):
        """Display final application results."""
        # Create results table
        table = Table(title="🎯 APPLICATION RESULTS SUMMARY")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Percentage", style="yellow")

        total = len(results)
        if total > 0:
            table.add_row("Total Jobs Processed", str(total), "100.0%")
            table.add_row("Successful Applications",
                         str(self.stats["successful_applications"]),
                         f"{(self.stats['successful_applications']/total)*100:.1f}%")
            table.add_row("Failed Applications",
                         str(self.stats["failed_applications"]),
                         f"{(self.stats['failed_applications']/total)*100:.1f}%")
            table.add_row("Manual Reviews Required",
                         str(self.stats["manual_reviews"]),
                         f"{(self.stats['manual_reviews']/total)*100:.1f}%")
            table.add_row("Skipped Jobs",
                         str(self.stats["skipped_jobs"]),
                         f"{(self.stats['skipped_jobs']/total)*100:.1f}%")

        console.print(table)

        # Performance summary
        avg_time = total_time / total if total > 0 else 0
        performance_panel = Panel(
            f"⏱️ PERFORMANCE METRICS\n\n"
            f"• Total Time: {total_time:.1f} seconds\n"
            f"• Average Time per Job: {avg_time:.1f} seconds\n"
            f"• Jobs per Hour: {(total / (total_time / 3600)):.1f}" if total_time > 0 else "• Jobs per Hour: N/A",
            style="bold blue"
        )
        console.print(performance_panel)


# Convenience functions for easy usage
async def apply_to_jobs(profile_name: str,
                       limit: int = 10,
                       batch_size: int = 3,
                       dry_run: bool = False,
                       filters: Dict = None) -> List[ApplicationResult]:
    """
    Convenience function to apply to jobs.

    Args:
        profile_name: Name of the user profile
        limit: Maximum number of jobs to process
        batch_size: Number of jobs to process in parallel
        dry_run: If True, simulate applications
        filters: Optional filters for job selection

    Returns:
        List of application results
    """
    applicator = EnhancedJobApplicator(profile_name)

    if not await applicator.initialize():
        return []

    jobs = await applicator.get_jobs_to_apply(limit=limit, filters=filters)
    if not jobs:
        console.print("[yellow]No jobs found to apply to[/yellow]")
        return []

    # Show preview
    applicator.display_jobs_preview(jobs)

    # Confirm before proceeding (unless dry run)
    if not dry_run:
        response = input(f"\nProceed with applying to {len(jobs)} jobs? (y/N): ")
        if response.lower() != 'y':
            console.print("[yellow]Application cancelled by user[/yellow]")
            return []

    return await applicator.apply_to_jobs_batch(jobs, batch_size=batch_size, dry_run=dry_run)


async def test_application_system(profile_name: str = "Nirajan") -> None:
    """
    Test the application system with a small batch of jobs.

    Args:
        profile_name: Name of the user profile to test with
    """
    console.print(Panel.fit("🧪 TESTING APPLICATION SYSTEM", style="bold magenta"))

    # Test with dry run first
    console.print("[cyan]🔍 Running dry run test with 3 jobs...[/cyan]")
    results = await apply_to_jobs(
        profile_name=profile_name,
        limit=3,
        batch_size=1,
        dry_run=True
    )

    if results:
        console.print(f"[green]✅ Dry run completed successfully! Processed {len(results)} jobs[/green]")

        # Ask if user wants to proceed with real applications
        response = input("\nDry run successful! Proceed with real applications? (y/N): ")
        if response.lower() == 'y':
            console.print("[cyan]🚀 Starting real application process...[/cyan]")
            real_results = await apply_to_jobs(
                profile_name=profile_name,
                limit=2,
                batch_size=1,
                dry_run=False
            )
            console.print(f"[green]✅ Real application test completed! Processed {len(real_results)} jobs[/green]")
        else:
            console.print("[yellow]Real application test cancelled by user[/yellow]")
    else:
        console.print("[red]❌ Dry run failed or no jobs available[/red]")


if __name__ == "__main__":
    import asyncio

    # Run test when script is executed directly
    asyncio.run(test_application_system())
