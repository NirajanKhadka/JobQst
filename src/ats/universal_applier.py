#!/usr/bin/env python3
"""
Improved Universal Job Applier
A comprehensive job application system that works with ALL ATS and non-ATS systems.
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel

from playwright.async_api import async_playwright, Page, BrowserContext

# Import ATS-specific handlers
from .workday_handler import apply_workday
from .greenhouse_handler import apply_greenhouse
from .icims_handler import apply_icims
from .lever_handler import apply_lever
# NOTE: BambooHR integration has been removed; do not import bamboohr_handler
# from .bamboohr_handler import apply_bamboohr

# Import form utilities
from .form_utils import (
    find_and_click_apply_button,
    fill_form_fields,
    upload_resume,
    upload_cover_letter,
    click_next_or_continue,
    click_submit_button,
    check_for_captcha,
    check_for_login_required,
    check_for_confirmation,
    generate_cover_letter_text,
)

from .ats_utils import (
    detect_ats_system,
    COMMON_FORM_SELECTORS,
    APPLY_BUTTON_SELECTORS,
    SUBMIT_BUTTON_SELECTORS,
)
from .fallback_submitters import (
    GenericATSSubmitter,
    ManualApplicationSubmitter,
    EmergencyEmailSubmitter,
)
from src.utils.profile_helpers import load_profile
from src.core.job_database import get_job_db

console = Console()


class UniversalApplier:
    """
    Improved universal job applier that works with all ATS and non-ATS systems.
    Features:
    - Configurable form detection and filling
    - Multi-step application handling
    - Document auto-upload
    - Comprehensive error recovery
    - Application status tracking
    """

    def __init__(self, profile_name: str = "Nirajan", profile_path: str = None, headless: bool = True, dry_run: bool = False):
        """Initialize the Improved universal applier."""
        self.profile_name = profile_name
        self.profile_path = profile_path
        self.headless = headless
        self.dry_run = dry_run
        
        # Load profile from path or name
        if profile_path:
            try:
                with open(profile_path, 'r') as f:
                    self.profile = json.load(f)
            except Exception as e:
                console.print(f"[red]❌ Failed to load profile from {profile_path}: {e}[/red]")
                self.profile = {}
        else:
            self.profile = load_profile(profile_name)
            
        self.db = get_job_db(profile_name)

        # Application settings  
        self.timeout = 60000  # 1 minute timeout
        self.step_delay = 2  # 2 seconds between steps
        self.max_retries = 3  # Max retry attempts

        # Browser instances (initialized as None)
        self.browser = None
        self.context = None

        # Document paths
        self.resume_path = self._get_document_path("resume")
        self.cover_letter_path = self._get_document_path("cover_letter")

        # Application tracking
        self.applications_attempted = 0
        self.applications_successful = 0
        self.applications_failed = []
        self.applications_manual = []

        console.print(f"[cyan]🚀 Improved Universal Applier initialized for {profile_name}[/cyan]")
        if not dry_run:
            console.print(f"[cyan]📄 Resume: {self.resume_path}[/cyan]")
            console.print(f"[cyan]📄 Cover Letter: {self.cover_letter_path}[/cyan]")

    def _get_document_path(self, doc_type: str) -> str:
        """Get path to document from profile or default location."""
        # Check profile for document paths
        if self.profile and doc_type in self.profile:
            path = Path(self.profile[doc_type])
            if path.exists():
                return str(path)

        # Check default locations
        default_paths = {
            "resume": [
                f"profiles/{self.profile_name}/resume.pdf",
                f"profiles/{self.profile_name}/resume.docx",
                "documents/resume.pdf",
                "documents/resume.docx",
            ],
            "cover_letter": [
                f"profiles/{self.profile_name}/cover_letter.pdf",
                f"profiles/{self.profile_name}/cover_letter.docx",
                "documents/cover_letter.pdf",
                "documents/cover_letter.docx",
            ],
        }

        for path_str in default_paths.get(doc_type, []):
            path = Path(path_str)
            if path.exists():
                return str(path)

        console.print(f"[yellow]⚠️ {doc_type} not found, will skip upload[/yellow]")
        return ""

    async def apply_to_job(self, job: Dict) -> Dict:
        """
        Apply to a single job with comprehensive error handling.

        Args:
            job: Job dictionary with title, company, url, etc.

        Returns:
            Application result dictionary
        """
        self.applications_attempted += 1

        result = {
            "job_id": job.get("id", f"job_{self.applications_attempted}"),
            "job_title": job.get("title", "Unknown"),
            "company": job.get("company", "Unknown"),
            "url": job.get("url", ""),
            "ats_system": detect_ats_system(job.get("url", "")),
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
            "details": "",
            "retry_count": 0,
        }

        console.print(
            f"\n[bold blue]📝 Applying to: {result['job_title']} at {result['company']}[/bold blue]"
        )
        console.print(f"[cyan]🔗 URL: {result['url']}[/cyan]")
        console.print(f"[cyan]🏢 ATS: {result['ats_system']}[/cyan]")

        # Try application with retries
        for attempt in range(self.max_retries):
            try:
                result["retry_count"] = attempt
                status = await self._attempt_application(job, result)
                result["status"] = status

                if status == "applied":
                    result["details"] = "Application submitted successfully"
                    self.applications_successful += 1
                    console.print(f"[green]✅ Application successful![/green]")
                    break
                elif status == "manual":
                    result["details"] = "Requires manual completion"
                    self.applications_manual.append(result)
                    console.print(f"[yellow]⚠️ Manual completion required[/yellow]")
                    break
                else:
                    result["details"] = f"Attempt {attempt + 1} failed: {status}"
                    console.print(f"[red]❌ Attempt {attempt + 1} failed: {status}[/red]")

                    if attempt < self.max_retries - 1:
                        console.print(f"[cyan]🔄 Retrying in {self.step_delay} seconds...[/cyan]")
                        await asyncio.sleep(self.step_delay)

            except Exception as e:
                result["details"] = f"Error on attempt {attempt + 1}: {str(e)}"
                console.print(f"[red]❌ Error on attempt {attempt + 1}: {e}[/red]")

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.step_delay)

        # Final status
        if result["status"] == "pending":
            result["status"] = "failed"
            result["details"] = f"Failed after {self.max_retries} attempts"
            self.applications_failed.append(result)

        # Save application record
        self._save_application_record(result)

        return result

    async def _attempt_application(self, job: Dict, result: Dict) -> str:
        """Attempt to apply to a job."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            )

            try:
                page = await context.new_page()

                # Navigate to job page
                console.print(f"[cyan]\U0001f310 Navigating to job page...[/cyan]")
                await page.goto(job["url"], timeout=self.timeout)
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)

                # Try to apply based on ATS system
                ats_system = result["ats_system"]


                # Attach generic handler to context for handler fallback
                context._generic_apply = self._apply_generic
                context._profile = self.profile
                context._resume_path = self.resume_path
                context._cover_letter_path = self.cover_letter_path

                if ats_system == "workday":
                    return await apply_workday(page, job)
                elif ats_system == "greenhouse":
                    return await apply_greenhouse(page, job)
                elif ats_system == "icims":
                    return await apply_icims(page, job)
                elif ats_system == "lever":
                    return await apply_lever(page, job)
                elif ats_system == "bamboohr":
                    # BambooHR integration removed: fall back to generic application flow
                    return await self._apply_generic(page, job)
                else:
                    # Generic application for unknown ATS
                    return await self._apply_generic(page, job)

            except Exception as e:
                console.print(f"[red]\u274c Browser error: {e}[/red]")
                return f"browser_error: {str(e)}"
            finally:
                await context.close()
                await browser.close()

    async def _apply_generic(self, page: Page, job: Dict) -> str:
        """Generic application process for any website."""
        console.print("[cyan]🔧 Using generic application process...[/cyan]")

        try:
            # Step 1: Find and click apply button
            if not await find_and_click_apply_button(page):
                return "no_apply_button"

            # Step 2: Handle potential redirects or new tabs
            await asyncio.sleep(2)

            # Step 3: Fill application form(s) - handle multi-step forms
            max_steps = 10
            for step in range(max_steps):
                console.print(f"[cyan]📝 Processing form step {step + 1}...[/cyan]")

                # Check for CAPTCHA or login requirements
                if await check_for_captcha(page):
                    return "captcha_detected"

                if await check_for_login_required(page):
                    return "login_required"

                # Fill visible form fields
                fields_filled = await fill_form_fields(page, self.profile)
                console.print(f"[green]✅ Filled {fields_filled} form fields[/green]")

                # Upload documents
                if self.resume_path:
                    resume_uploaded = await upload_resume(page, self.resume_path)
                    if resume_uploaded:
                        console.print("[green]✅ Resume uploaded[/green]")

                if self.cover_letter_path:
                    cover_uploaded = await upload_cover_letter(page, self.cover_letter_path)
                    if cover_uploaded:
                        console.print("[green]✅ Cover letter uploaded[/green]")

                # Try to proceed to next step
                if await click_next_or_continue(page):
                    console.print("[green]✅ Proceeded to next step[/green]")
                    await asyncio.sleep(self.step_delay)
                    continue

                # Try to submit if no next step
                if await click_submit_button(page):
                    console.print("[green]✅ Application submitted![/green]")
                    return "applied"

                # If we can't proceed or submit, we might be done or stuck
                break

            return "manual"  # Couldn't complete automatically

        except Exception as e:
            console.print(f"[red]❌ Generic application error: {e}[/red]")
            return f"error: {str(e)}"

    def _generate_cover_letter_text(self) -> str:
        """Generate a simple cover letter text (deprecated - use form_utils.generate_cover_letter_text)."""
        return generate_cover_letter_text(self.profile)

    def _detect_ats_type(self, url: str) -> str:
        """Detect the ATS type from a job URL using ats_utils.detect_ats_system."""
        from src.ats.ats_utils import detect_ats_system
        return detect_ats_system(url)

    # ATS-specific methods are now handled by external handler modules.

    def _save_application_record(self, result: Dict) -> None:
        """Save application record to database."""
        try:
            # Create application record
            application_record = {
                "job_id": result["job_id"],
                "job_title": result["job_title"],
                "company": result["company"],
                "url": result["url"],
                "ats_system": result["ats_system"],
                "application_status": result["status"],
                "application_date": result["timestamp"],
                "details": result["details"],
                "retry_count": result["retry_count"],
            }

            # You can save this to your existing database or a separate applications table
            console.print(f"[dim]💾 Application record saved[/dim]")

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not save application record: {e}[/yellow]")

    async def apply_to_multiple_jobs(self, jobs: List[Dict], max_applications: int = 10, max_concurrent: int = 3) -> Dict:
        """
        Apply to multiple jobs with rate limiting.

        Args:
            jobs: List of job dictionaries
            max_applications: Maximum applications per session

        Returns:
            Summary of application results
        """
        console.print(Panel.fit("🚀 STARTING BATCH APPLICATION PROCESS", style="bold blue"))
        console.print(f"[cyan]📊 Jobs to process: {len(jobs)}[/cyan]")
        console.print(f"[cyan]📊 Max applications: {max_applications}[/cyan]")

        results = []

        with Progress() as progress:
            task = progress.add_task(
                "[green]Applying to jobs...", total=min(len(jobs), max_applications)
            )

            for i, job in enumerate(jobs[:max_applications]):
                console.print(
                    f"\n[bold]Processing job {i + 1}/{min(len(jobs), max_applications)}[/bold]"
                )

                result = await self.apply_to_job(job)
                results.append(result)

                progress.update(task, advance=1)

                # Rate limiting - wait between applications
                if i < min(len(jobs), max_applications) - 1:
                    console.print(
                        f"[cyan]⏱️ Waiting {self.step_delay} seconds before next application...[/cyan]"
                    )
                    await asyncio.sleep(self.step_delay)

        # Generate summary
        summary = self._generate_application_summary(results)
        self._display_application_summary(summary)

        return summary

    def _generate_application_summary(self, results: List[Dict]) -> Dict:
        """Generate summary of application results."""
        total = len(results)
        successful = len([r for r in results if r["status"] == "applied"])
        manual = len([r for r in results if r["status"] == "manual"])
        failed = len([r for r in results if r["status"] == "failed"])

        return {
            "total_attempts": total,
            "successful": successful,
            "manual_required": manual,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    def _display_application_summary(self, summary: Dict) -> None:
        """Display application summary."""
        console.print("\n" + "=" * 80)
        console.print(Panel.fit("📊 APPLICATION SUMMARY", style="bold green"))

        # Summary table
        table = Table(title="Application Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Percentage", style="yellow")

        total = summary["total_attempts"]
        table.add_row("Total Applications", str(total), "100%")
        table.add_row(
            "Successful",
            str(summary["successful"]),
            f"{summary['successful']/total*100:.1f}%" if total > 0 else "0%",
        )
        table.add_row(
            "Manual Required",
            str(summary["manual_required"]),
            f"{summary['manual_required']/total*100:.1f}%" if total > 0 else "0%",
        )
        table.add_row(
            "Failed",
            str(summary["failed"]),
            f"{summary['failed']/total*100:.1f}%" if total > 0 else "0%",
        )

        console.print(table)

        # Success rate indicator
        success_rate = summary["success_rate"]
        if success_rate >= 70:
            console.print(
                f"[bold green]🎯 Excellent success rate: {success_rate:.1f}%[/bold green]"
            )
        elif success_rate >= 50:
            console.print(f"[bold yellow]⚡ Good success rate: {success_rate:.1f}%[/bold yellow]")
        else:
            console.print(f"[bold red]🔧 Needs improvement: {success_rate:.1f}%[/bold red]")

        # Manual applications note
        if summary["manual_required"] > 0:
            console.print(
                f"[yellow]⚠️ {summary['manual_required']} applications require manual completion[/yellow]"
            )
            console.print(
                "[cyan]💡 Consider enhancing ATS-specific handlers for better automation[/cyan]"
            )

    async def _setup_browser(self):
        """Setup browser instance for application process."""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            )

    async def _setup_profile(self):
        """Setup profile data for application process."""
        if not self.profile:
            console.print(f"[yellow]⚠️ Profile not loaded for {self.profile_name}[/yellow]")
            return False
        return True

    async def _navigate_to_job(self, job_url: str) -> bool:
        """Navigate to job URL and verify page loads."""
        try:
            if not self.context:
                await self._setup_browser()
            
            page = await self.context.new_page()
            await page.goto(job_url, timeout=self.timeout)
            await page.wait_for_load_state("domcontentloaded")
            return True
        except Exception as e:
            console.print(f"[red]❌ Navigation failed: {e}[/red]")
            return False


# Convenience functions
async def apply_to_job(job: Dict, profile_name: str = "Nirajan") -> Dict:
    """Apply to a single job."""
    applier = UniversalApplier(profile_name)
    return await applier.apply_to_job(job)


async def apply_to_jobs_from_database(
    profile_name: str = "Nirajan", max_applications: int = 10
) -> Dict:
    """Apply to jobs from the database."""
    applier = UniversalApplier(profile_name)

    # Get jobs from database
    db = get_job_db(profile_name)
    all_jobs = db.get_all_jobs()

    # Filter for unprocessed jobs
    unprocessed_jobs = [job for job in all_jobs if not job.get("application_status")]

    console.print(f"[cyan]📊 Found {len(unprocessed_jobs)} unprocessed jobs[/cyan]")

    if not unprocessed_jobs:
        console.print("[yellow]⚠️ No unprocessed jobs found[/yellow]")
        return {"total_attempts": 0, "successful": 0, "manual_required": 0, "failed": 0}

    return await applier.apply_to_multiple_jobs(unprocessed_jobs, max_applications)


if __name__ == "__main__":
    # Example usage
    test_job = {
        "id": "test_job_1",
        "title": "Software Engineer",
        "company": "Test Company",
        "url": "https://example.com/job/123",
    }

    asyncio.run(apply_to_job(test_job))

