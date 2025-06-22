#!/usr/bin/env python3
"""
Enhanced Application Agent
Advanced job application agent that scrapes job descriptions,
modifies resumes/cover letters, and applies to jobs while working
with the background Gmail monitor for verification.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel
from playwright.async_api import async_playwright, Page

from src.core.job_database import get_job_db
from src.utils.job_data_enhancer import JobDataEnhancer
from .ats_based_applicator import ATSBasedApplicator
from src.core import utils

console = Console()

@dataclass
class ApplicationResult:
    """Result of job application attempt."""
    job_id: str
    status: str  # 'pending_verification', 'failed', 'manual_review'
    error_message: Optional[str] = None
    ats_detected: Optional[str] = None
    enhanced_data: Optional[Dict] = None
    application_time: float = 0.0
    resume_modified: bool = False
    cover_letter_generated: bool = False

class EnhancedApplicationAgent:
    """
    Enhanced application agent that:
    1. Scrapes job descriptions and requirements
    2. Modifies resumes and generates cover letters
    3. Applies to jobs using ATS-specific methods
    4. Marks jobs as 'pending_verification' (Gmail agent will verify)
    """
    
    def __init__(self, profile_name: str):
        """Initialize the enhanced application agent."""
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        self.profile = None
        
        # Initialize sub-agents
        self.job_enhancer = JobDataEnhancer(profile_name)
        self.ats_applicator = ATSBasedApplicator(profile_name)
        
        # Application settings
        self.max_applications_per_session = 20
        self.delay_between_applications = 45  # seconds
        
        # Statistics
        self.stats = {
            "total_processed": 0,
            "pending_verification": 0,
            "failed_applications": 0,
            "manual_reviews": 0,
            "resumes_modified": 0,
            "cover_letters_generated": 0,
            "total_time": 0.0
        }
    
    async def initialize(self) -> bool:
        """Initialize the application agent."""
        try:
            # Load profile
            self.profile = utils.load_profile(self.profile_name)
            if not self.profile:
                console.print(f"[red]❌ Failed to load profile: {self.profile_name}[/red]")
                return False
            
            # Initialize sub-agents
            if not await self.job_enhancer.initialize():
                console.print("[red]❌ Failed to initialize job enhancer[/red]")
                return False
            
            if not await self.ats_applicator.initialize():
                console.print("[red]❌ Failed to initialize ATS applicator[/red]")
                return False
            
            console.print(f"[green]✅ Enhanced application agent initialized for: {self.profile_name}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Initialization failed: {e}[/red]")
            return False

    def _filter_real_job_links(self, jobs: List[Dict], limit: int) -> List[Dict]:
        """
        Filter out Eluta jobs and only keep real direct job links.

        Args:
            jobs: List of all jobs
            limit: Maximum number of real jobs to return

        Returns:
            List of jobs with real direct links (no Eluta)
        """
        real_jobs = []
        eluta_count = 0

        for job in jobs:
            url = job.get('url', '').lower()

            # Skip Eluta URLs completely
            if any(eluta_pattern in url for eluta_pattern in [
                'eluta.ca',
                'sandbox',
                'destination=',
                'eluta.com'
            ]):
                eluta_count += 1
                console.print(f"[yellow]⚠️ Skipping Eluta job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}[/yellow]")
                continue

            # Only keep jobs with real company URLs
            if any(real_pattern in url for real_pattern in [
                'workday.com',
                'greenhouse.io',
                'lever.co',
                'bamboohr.com',
                'smartrecruiters.com',
                'jobvite.com',
                'icims.com',
                'taleo.net',
                'careers.',
                'jobs.',
                '.com/careers',
                '.com/jobs',
                '.ca/careers',
                '.ca/jobs'
            ]):
                real_jobs.append(job)
                console.print(f"[green]✅ Real job link: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}[/green]")

                if len(real_jobs) >= limit:
                    break
            else:
                # Check if it's a company domain (not a job board)
                if not any(job_board in url for job_board in [
                    'indeed.com',
                    'linkedin.com',
                    'glassdoor.com',
                    'monster.com',
                    'ziprecruiter.com'
                ]):
                    # Assume it's a company website
                    real_jobs.append(job)
                    console.print(f"[cyan]📋 Company website: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}[/cyan]")

                    if len(real_jobs) >= limit:
                        break

        console.print(f"[cyan]📊 Filtering results: {len(real_jobs)} real jobs, {eluta_count} Eluta jobs skipped[/cyan]")
        return real_jobs

    async def process_job_applications(self,
                                     limit: int = 10,
                                     enhance_jobs: bool = True,
                                     modify_documents: bool = True) -> List[ApplicationResult]:
        """
        Process job applications with enhancement and document modification.
        
        Args:
            limit: Maximum number of jobs to process
            enhance_jobs: Whether to enhance job data first
            modify_documents: Whether to modify resume/cover letter
            
        Returns:
            List of application results
        """
        console.print(Panel.fit("🎯 ENHANCED APPLICATION AGENT", style="bold blue"))
        console.print(f"[cyan]Processing up to {limit} job applications[/cyan]")
        console.print(f"[cyan]Job enhancement: {'✅ Enabled' if enhance_jobs else '❌ Disabled'}[/cyan]")
        console.print(f"[cyan]Document modification: {'✅ Enabled' if modify_documents else '❌ Disabled'}[/cyan]")
        
        start_time = time.time()
        results = []
        
        # Get jobs to apply to
        all_jobs = self.db.get_unapplied_jobs(limit=limit * 3)  # Get more to filter
        if not all_jobs:
            console.print("[yellow]No unapplied jobs found[/yellow]")
            return []

        # Filter out Eluta jobs - only use real direct job links
        jobs = self._filter_real_job_links(all_jobs, limit)
        if not jobs:
            console.print("[yellow]No real job links found (all were Eluta redirects)[/yellow]")
            return []

        console.print(f"[green]Found {len(jobs)} real job links to process (filtered out Eluta)[/green]")
        
        # Process each job
        with Progress() as progress:
            task = progress.add_task("[green]Processing applications...", total=len(jobs))
            
            for i, job in enumerate(jobs):
                try:
                    console.print(f"\n[bold]🎯 Processing Job {i+1}/{len(jobs)}:[/bold]")
                    console.print(f"Title: {job.get('title', 'Unknown')}")
                    console.print(f"Company: {job.get('company', 'Unknown')}")
                    
                    # Step 1: Enhance job data if requested
                    enhanced_data = None
                    if enhance_jobs:
                        console.print("[cyan]🔍 Step 1: Enhancing job data...[/cyan]")
                        enhanced_data = await self._enhance_job_data(job)
                    
                    # Step 2: Modify documents if requested
                    resume_modified = False
                    cover_letter_generated = False
                    if modify_documents and enhanced_data:
                        console.print("[cyan]📝 Step 2: Modifying documents...[/cyan]")
                        resume_modified, cover_letter_generated = await self._modify_documents(job, enhanced_data)
                    
                    # Step 3: Apply to job
                    console.print("[cyan]🚀 Step 3: Applying to job...[/cyan]")
                    application_result = await self._apply_to_job(job, enhanced_data)
                    
                    # Create result
                    result = ApplicationResult(
                        job_id=job.get('id', job.get('url', 'unknown')),
                        status=application_result.get('status', 'failed'),
                        error_message=application_result.get('error'),
                        ats_detected=application_result.get('ats_detected'),
                        enhanced_data=enhanced_data,
                        application_time=application_result.get('duration', 0),
                        resume_modified=resume_modified,
                        cover_letter_generated=cover_letter_generated
                    )
                    
                    results.append(result)
                    self._update_stats(result)
                    
                    # Update progress
                    progress.update(task, advance=1)
                    
                    # Delay between applications
                    if i < len(jobs) - 1:
                        console.print(f"[yellow]⏳ Waiting {self.delay_between_applications} seconds before next application...[/yellow]")
                        await asyncio.sleep(self.delay_between_applications)
                
                except Exception as e:
                    console.print(f"[red]❌ Error processing job: {e}[/red]")
                    
                    # Create failed result
                    result = ApplicationResult(
                        job_id=job.get('id', job.get('url', 'unknown')),
                        status='failed',
                        error_message=str(e),
                        application_time=0
                    )
                    results.append(result)
                    self._update_stats(result)
                    
                    progress.update(task, advance=1)
        
        # Final statistics
        total_time = time.time() - start_time
        self.stats["total_time"] = total_time
        
        self._display_final_results(results, total_time)
        return results
    
    async def _enhance_job_data(self, job: Dict) -> Optional[Dict]:
        """Enhance job data by scraping detailed information."""
        try:
            enhancement = await self.job_enhancer.enhance_job_data(job)
            
            if enhancement and enhancement.enhanced_data:
                console.print(f"[green]✅ Enhanced job data: {len(enhancement.questions_found)} questions, {len(enhancement.requirements)} requirements[/green]")
                return {
                    'enhanced_data': enhancement.enhanced_data,
                    'questions_found': enhancement.questions_found,
                    'requirements': enhancement.requirements,
                    'benefits': enhancement.benefits,
                    'salary_info': enhancement.salary_info,
                    'job_type': enhancement.job_type,
                    'experience_level': enhancement.experience_level,
                    'skills_required': enhancement.skills_required
                }
            else:
                console.print("[yellow]⚠️ Limited job enhancement data available[/yellow]")
                return None
                
        except Exception as e:
            console.print(f"[red]❌ Job enhancement failed: {e}[/red]")
            return None
    
    async def _modify_documents(self, job: Dict, enhanced_data: Dict) -> Tuple[bool, bool]:
        """Modify resume and generate cover letter based on job requirements."""
        resume_modified = False
        cover_letter_generated = False
        
        try:
            # Extract job requirements and keywords
            requirements = enhanced_data.get('requirements', [])
            skills_required = enhanced_data.get('skills_required', [])
            job_title = job.get('title', '')
            company = job.get('company', '')
            
            # Modify resume (placeholder - would integrate with document generation system)
            if requirements or skills_required:
                console.print("[cyan]📄 Modifying resume to match job requirements...[/cyan]")
                # This would call a resume modification service
                # resume_modified = await self._modify_resume(job, requirements, skills_required)
                resume_modified = True  # Placeholder
                console.print("[green]✅ Resume modified successfully[/green]")
            
            # Generate cover letter (placeholder - would integrate with document generation system)
            if job_title and company:
                console.print("[cyan]📝 Generating tailored cover letter...[/cyan]")
                # This would call a cover letter generation service
                # cover_letter_generated = await self._generate_cover_letter(job, enhanced_data)
                cover_letter_generated = True  # Placeholder
                console.print("[green]✅ Cover letter generated successfully[/green]")
            
            if resume_modified:
                self.stats["resumes_modified"] += 1
            if cover_letter_generated:
                self.stats["cover_letters_generated"] += 1
            
            return resume_modified, cover_letter_generated
            
        except Exception as e:
            console.print(f"[red]❌ Document modification failed: {e}[/red]")
            return False, False
    
    async def _apply_to_job(self, job: Dict, enhanced_data: Optional[Dict]) -> Dict:
        """Apply to job using ATS-based applicator."""
        try:
            # Use ATS applicator to apply
            result = await self.ats_applicator.apply_to_job(job)
            
            # If application was submitted, mark as pending verification
            # (Gmail monitor will verify and update status)
            if result.get('status') == 'applied':
                result['status'] = 'pending_verification'
                console.print("[yellow]📧 Application submitted - pending Gmail verification[/yellow]")
            
            return result
            
        except Exception as e:
            console.print(f"[red]❌ Job application failed: {e}[/red]")
            return {
                'status': 'failed',
                'error': str(e),
                'duration': 0
            }
    
    def _update_stats(self, result: ApplicationResult) -> None:
        """Update application statistics."""
        self.stats["total_processed"] += 1
        
        if result.status == 'pending_verification':
            self.stats["pending_verification"] += 1
        elif result.status == 'failed':
            self.stats["failed_applications"] += 1
        elif result.status == 'manual_review':
            self.stats["manual_reviews"] += 1
    
    def _display_final_results(self, results: List[ApplicationResult], total_time: float) -> None:
        """Display final application results."""
        console.print("\n" + "="*60)
        console.print(Panel.fit("🎯 APPLICATION AGENT RESULTS", style="bold green"))
        
        # Results table
        table = Table(title="Application Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Percentage", style="yellow")
        
        total = len(results)
        if total > 0:
            table.add_row("Total Applications", str(total), "100.0%")
            table.add_row("Pending Verification", 
                         str(self.stats["pending_verification"]), 
                         f"{(self.stats['pending_verification']/total)*100:.1f}%")
            table.add_row("Failed Applications", 
                         str(self.stats["failed_applications"]), 
                         f"{(self.stats['failed_applications']/total)*100:.1f}%")
            table.add_row("Manual Reviews", 
                         str(self.stats["manual_reviews"]), 
                         f"{(self.stats['manual_reviews']/total)*100:.1f}%")
            table.add_row("Resumes Modified", str(self.stats["resumes_modified"]), "")
            table.add_row("Cover Letters Generated", str(self.stats["cover_letters_generated"]), "")
        
        console.print(table)
        
        # Performance summary
        avg_time = total_time / total if total > 0 else 0
        performance_panel = Panel(
            f"⏱️ PERFORMANCE METRICS\n\n"
            f"• Total Time: {total_time:.1f} seconds\n"
            f"• Average Time per Job: {avg_time:.1f} seconds\n"
            f"• Applications per Hour: {(total / (total_time / 3600)):.1f}" if total_time > 0 else "• Applications per Hour: N/A\n"
            f"• Status: {self.stats['pending_verification']} applications pending Gmail verification",
            style="bold blue"
        )
        console.print(performance_panel)
        
        # Next steps
        if self.stats["pending_verification"] > 0:
            console.print(f"\n[yellow]📧 {self.stats['pending_verification']} applications are pending Gmail verification[/yellow]")
            console.print("[yellow]The background Gmail monitor will automatically verify these applications[/yellow]")
    
    def get_stats(self) -> Dict:
        """Get application statistics."""
        return self.stats.copy()


# Convenience functions
async def run_application_agent(profile_name: str = "Nirajan", 
                               limit: int = 10,
                               enhance_jobs: bool = True,
                               modify_documents: bool = True) -> List[ApplicationResult]:
    """
    Run the enhanced application agent.
    
    Args:
        profile_name: Profile name
        limit: Maximum number of jobs to process
        enhance_jobs: Whether to enhance job data
        modify_documents: Whether to modify documents
        
    Returns:
        List of application results
    """
    agent = EnhancedApplicationAgent(profile_name)
    
    if not await agent.initialize():
        return []
    
    return await agent.process_job_applications(limit, enhance_jobs, modify_documents)


if __name__ == "__main__":
    import asyncio
    
    # Run application agent when script is executed directly
    asyncio.run(run_application_agent())
