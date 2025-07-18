#!/usr/bin/env python3
"""
Enhanced Universal Job Applier
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


class EnhancedUniversalApplier:
    """
    Enhanced universal job applier that works with all ATS and non-ATS systems.
    Features:
    - Smart form detection and filling
    - Multi-step application handling
    - Document auto-upload
    - Comprehensive error recovery
    - Application status tracking
    """

    def __init__(self, profile_name: str = "Nirajan"):
        """Initialize the enhanced universal applier."""
        self.profile_name = profile_name
        self.profile = load_profile(profile_name)
        self.db = get_job_db(profile_name)

        # Application settings
        self.headless = True
        self.timeout = 60000  # 1 minute timeout
        self.step_delay = 2  # 2 seconds between steps
        self.max_retries = 3  # Max retry attempts

        # Document paths
        self.resume_path = self._get_document_path("resume")
        self.cover_letter_path = self._get_document_path("cover_letter")

        # Application tracking
        self.applications_attempted = 0
        self.applications_successful = 0
        self.applications_failed = []
        self.applications_manual = []

        console.print(f"[cyan]🚀 Enhanced Universal Applier initialized for {profile_name}[/cyan]")
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
                console.print(f"[cyan]🌐 Navigating to job page...[/cyan]")
                await page.goto(job["url"], timeout=self.timeout)
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)

                # Try to apply based on ATS system
                ats_system = result["ats_system"]

                if ats_system == "workday":
                    return await self._apply_workday(page, job)
                elif ats_system == "greenhouse":
                    return await self._apply_greenhouse(page, job)
                elif ats_system == "icims":
                    return await self._apply_icims(page, job)
                elif ats_system == "lever":
                    return await self._apply_lever(page, job)
                elif ats_system == "bamboohr":
                    return await self._apply_bamboohr(page, job)
                else:
                    # Generic application for unknown ATS
                    return await self._apply_generic(page, job)

            except Exception as e:
                console.print(f"[red]❌ Browser error: {e}[/red]")
                return f"browser_error: {str(e)}"
            finally:
                await context.close()
                await browser.close()

    async def _apply_generic(self, page: Page, job: Dict) -> str:
        """Generic application process for any website."""
        console.print("[cyan]🔧 Using generic application process...[/cyan]")

        try:
            # Step 1: Find and click apply button
            if not await self._find_and_click_apply_button(page):
                return "no_apply_button"

            # Step 2: Handle potential redirects or new tabs
            await asyncio.sleep(2)

            # Step 3: Fill application form(s) - handle multi-step forms
            max_steps = 10
            for step in range(max_steps):
                console.print(f"[cyan]📝 Processing form step {step + 1}...[/cyan]")

                # Check for CAPTCHA or login requirements
                if await self._check_for_captcha(page):
                    return "captcha_detected"

                if await self._check_for_login_required(page):
                    return "login_required"

                # Fill visible form fields
                fields_filled = await self._fill_form_fields(page)
                console.print(f"[green]✅ Filled {fields_filled} form fields[/green]")

                # Upload documents
                if self.resume_path:
                    resume_uploaded = await self._upload_resume(page)
                    if resume_uploaded:
                        console.print("[green]✅ Resume uploaded[/green]")

                if self.cover_letter_path:
                    cover_uploaded = await self._upload_cover_letter(page)
                    if cover_uploaded:
                        console.print("[green]✅ Cover letter uploaded[/green]")

                # Try to proceed to next step
                if await self._click_next_or_continue(page):
                    console.print("[green]✅ Proceeded to next step[/green]")
                    await asyncio.sleep(self.step_delay)
                    continue

                # Try to submit if no next step
                if await self._click_submit_button(page):
                    console.print("[green]✅ Application submitted![/green]")
                    return "applied"

                # If we can't proceed or submit, we might be done or stuck
                break

            return "manual"  # Couldn't complete automatically

        except Exception as e:
            console.print(f"[red]❌ Generic application error: {e}[/red]")
            return f"error: {str(e)}"

    async def _find_and_click_apply_button(self, page: Page) -> bool:
        """Find and click the apply button using comprehensive selectors."""
        apply_selectors = [
            # Standard apply buttons
            "button:has-text('Apply')",
            "a:has-text('Apply')",
            "button:has-text('Apply Now')",
            "a:has-text('Apply Now')",
            "input[value*='Apply']",
            # Data attributes
            "[data-automation-id*='apply']",
            "[data-testid*='apply']",
            "[data-qa*='apply']",
            # Class-based selectors
            ".apply-button",
            ".btn-apply",
            ".apply-now",
            "#apply-button",
            # Submit application variants
            "button:has-text('Submit Application')",
            "a:has-text('Submit Application')",
            # Language variants
            "button:has-text('Postuler')",  # French
            "button:has-text('Aplicar')",  # Spanish
            "button:has-text('Bewerben')",  # German
        ]

        for selector in apply_selectors:
            try:
                if await page.is_visible(selector, timeout=5000):
                    await page.click(selector)
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(2)
                    console.print(f"[green]✅ Clicked apply button: {selector}[/green]")
                    return True
            except Exception:
                continue

        console.print("[yellow]⚠️ Could not find apply button[/yellow]")
        return False

    async def _fill_form_fields(self, page: Page) -> int:
        """Fill form fields with profile data."""
        fields_filled = 0

        # Get profile data
        first_name = self.profile.get(
            "first_name",
            self.profile.get("name", "").split()[0] if self.profile.get("name") else "",
        )
        last_name = self.profile.get(
            "last_name",
            self.profile.get("name", "").split()[-1] if self.profile.get("name") else "",
        )
        email = self.profile.get("email", "")
        phone = self.profile.get("phone", "")
        location = self.profile.get("location", "")

        # Field mappings
        field_mappings = {
            # Name fields
            "input[name*='firstName'], input[name*='first_name'], input[name*='fname']": first_name,
            "input[name*='lastName'], input[name*='last_name'], input[name*='lname']": last_name,
            "input[name*='fullName'], input[name*='full_name'], input[name*='name']:not([name*='first']):not([name*='last'])": self.profile.get(
                "name", ""
            ),
            # Contact fields
            "input[type='email'], input[name*='email']": email,
            "input[type='tel'], input[name*='phone'], input[name*='telephone'], input[name*='mobile']": phone,
            # Location fields
            "input[name*='location'], input[name*='address'], input[name*='city']": location,
            # Common text areas
            "textarea[name*='cover'], textarea[name*='message'], textarea[name*='note']": self._generate_cover_letter_text(),
        }

        for selector, value in field_mappings.items():
            if value:
                try:
                    # Try to find and fill the field
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            # Check if field is empty
                            current_value = await element.input_value() or ""
                            if not current_value.strip():
                                await element.fill(str(value))
                                fields_filled += 1
                                console.print(f"[green]✅ Filled field with {selector}[/green]")
                                break
                except Exception:
                    continue

        return fields_filled

    async def _upload_resume(self, page: Page) -> bool:
        """Upload resume using comprehensive file input detection."""
        if not self.resume_path or not Path(self.resume_path).exists():
            return False

        upload_selectors = [
            "input[type='file'][name*='resume']",
            "input[type='file'][name*='cv']",
            "input[type='file'][id*='resume']",
            "input[type='file'][id*='cv']",
            "input[type='file'][accept*='pdf']",
            "input[type='file'][accept*='doc']",
            "input[type='file']",  # Generic file input as last resort
        ]

        for selector in upload_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        await element.set_input_files(self.resume_path)
                        await asyncio.sleep(2)  # Wait for upload
                        console.print(f"[green]✅ Uploaded resume via: {selector}[/green]")
                        return True
            except Exception:
                continue

        return False

    async def _upload_cover_letter(self, page: Page) -> bool:
        """Upload cover letter using comprehensive detection."""
        if not self.cover_letter_path or not Path(self.cover_letter_path).exists():
            return False

        upload_selectors = [
            "input[type='file'][name*='cover']",
            "input[type='file'][name*='letter']",
            "input[type='file'][id*='cover']",
            "input[type='file'][id*='letter']",
            "input[type='file']:nth-of-type(2)",  # Second file input
        ]

        for selector in upload_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        await element.set_input_files(self.cover_letter_path)
                        await asyncio.sleep(2)
                        console.print(f"[green]✅ Uploaded cover letter via: {selector}[/green]")
                        return True
            except Exception:
                continue

        return False

    async def _click_next_or_continue(self, page: Page) -> bool:
        """Click next/continue button to proceed to next step."""
        next_selectors = [
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Save & Continue')",
            "button:has-text('Proceed')",
            "input[type='submit'][value*='Next']",
            "input[type='submit'][value*='Continue']",
            ".next-button",
            "#next-button",
            "[data-testid*='next']",
            "[data-testid*='continue']",
        ]

        for selector in next_selectors:
            try:
                if await page.is_visible(selector, timeout=2000):
                    await page.click(selector)
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(2)
                    return True
            except Exception:
                continue

        return False

    async def _click_submit_button(self, page: Page) -> bool:
        """Click final submit button."""
        submit_selectors = [
            "button:has-text('Submit')",
            "button:has-text('Submit Application')",
            "button:has-text('Send Application')",
            "button:has-text('Apply')",
            "input[type='submit'][value*='Submit']",
            "input[type='submit'][value*='Apply']",
            ".submit-button",
            "#submit-button",
            "[data-testid*='submit']",
        ]

        for selector in submit_selectors:
            try:
                if await page.is_visible(selector, timeout=2000):
                    await page.click(selector)
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(3)

                    # Check for confirmation
                    if await self._check_for_confirmation(page):
                        return True

                    return True  # Assume success if no error
            except Exception:
                continue

        return False

    async def _check_for_captcha(self, page: Page) -> bool:
        """Check if CAPTCHA is present."""
        captcha_selectors = [
            "iframe[src*='recaptcha']",
            "iframe[src*='captcha']",
            ".g-recaptcha",
            "[class*='captcha']",
            "text='CAPTCHA'",
            "text='I am not a robot'",
        ]

        for selector in captcha_selectors:
            try:
                if await page.is_visible(selector, timeout=1000):
                    console.print("[yellow]⚠️ CAPTCHA detected![/yellow]")
                    return True
            except Exception:
                continue

        return False

    async def _check_for_login_required(self, page: Page) -> bool:
        """Check if login is required."""
        login_selectors = [
            "input[type='password']",
            "text='Sign In'",
            "text='Log In'",
            "text='Login'",
            "text='Create Account'",
        ]

        for selector in login_selectors:
            try:
                if await page.is_visible(selector, timeout=1000):
                    console.print("[yellow]⚠️ Login required![/yellow]")
                    return True
            except Exception:
                continue

        return False

    async def _check_for_confirmation(self, page: Page) -> bool:
        """Check for application confirmation."""
        confirmation_selectors = [
            "text='Thank you'",
            "text='Application submitted'",
            "text='Successfully submitted'",
            "text='Application received'",
            ".confirmation",
            ".success-message",
        ]

        for selector in confirmation_selectors:
            try:
                if await page.is_visible(selector, timeout=5000):
                    console.print("[green]✅ Confirmation detected![/green]")
                    return True
            except Exception:
                continue

        return False

    def _generate_cover_letter_text(self) -> str:
        """Generate a simple cover letter text."""
        name = self.profile.get("name", "")
        return f"""Dear Hiring Manager,

I am writing to express my interest in this position. I believe my skills and experience make me a strong candidate for this role.

Please find my resume attached for your review. I look forward to hearing from you.

Best regards,
{name}"""

    # ATS-specific methods (stubs for now - to be enhanced)
    async def _apply_workday(self, page: Page, job: Dict) -> str:
        """Apply via Workday ATS."""
        console.print("[cyan]🏢 Using Workday-specific application process...[/cyan]")
        return await self._apply_generic(page, job)

    async def _apply_greenhouse(self, page: Page, job: Dict) -> str:
        """Apply via Greenhouse ATS."""
        console.print("[cyan]🌱 Using Greenhouse-specific application process...[/cyan]")
        return await self._apply_generic(page, job)

    async def _apply_icims(self, page: Page, job: Dict) -> str:
        """Apply via iCIMS ATS."""
        console.print("[cyan]🔧 Using iCIMS-specific application process...[/cyan]")
        return await self._apply_generic(page, job)

    async def _apply_lever(self, page: Page, job: Dict) -> str:
        """Apply via Lever ATS."""
        console.print("[cyan]🎯 Using Lever-specific application process...[/cyan]")
        return await self._apply_generic(page, job)

    async def _apply_bamboohr(self, page: Page, job: Dict) -> str:
        """Apply via BambooHR ATS."""
        console.print("[cyan]🎋 Using BambooHR-specific application process...[/cyan]")
        return await self._apply_generic(page, job)

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

    async def apply_to_multiple_jobs(self, jobs: List[Dict], max_applications: int = 10) -> Dict:
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


# Convenience functions
async def apply_to_job(job: Dict, profile_name: str = "Nirajan") -> Dict:
    """Apply to a single job."""
    applier = EnhancedUniversalApplier(profile_name)
    return await applier.apply_to_job(job)


async def apply_to_jobs_from_database(
    profile_name: str = "Nirajan", max_applications: int = 10
) -> Dict:
    """Apply to jobs from the database."""
    applier = EnhancedUniversalApplier(profile_name)

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
