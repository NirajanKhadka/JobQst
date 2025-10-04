"""
ATS Fallback Submitters
Provides comprehensive fallback methods for job applications when primary ATS submitters fail.
"""

import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from playwright.sync_api import BrowserContext, Page
from rich.console import Console

from .base_submitter import BaseSubmitter

console = Console()


class GenericATSSubmitter(BaseSubmitter):
    """
    Generic ATS submitter that attempts to handle unknown ATS systems.
    Uses common patterns and heuristics to fill forms.
    """

    def submit(self, job: Dict, profile: Dict, resume_path: str, cover_letter_path: str) -> str:
        """
        Submit application using generic ATS patterns.

        Args:
            job: Job dictionary
            profile: User profile
            resume_path: Path to resume file
            cover_letter_path: Path to cover letter file

        Returns:
            Status string
        """
        console.print("[cyan]🔄 Using Generic ATS Submitter...[/cyan]")

        try:
            page = self.ctx.new_page()
            page.goto(job["url"], timeout=60000)

            # Wait for page to load
            page.wait_for_load_state("networkidle", timeout=30000)

            # Try to find and click apply button
            if not self._find_and_click_apply_button(page):
                return "Manual - Could not find apply button"

            # Fill application form using generic patterns
            if self._fill_generic_application_form(page, profile, resume_path, cover_letter_path):
                console.print("[green]✅ Generic ATS application submitted[/green]")
                return "Applied"
            else:
                return "Manual - Form filling failed"

        except Exception as e:
            console.print(f"[red]❌ Generic ATS submission failed: {e}[/red]")
            return f"Failed - {str(e)}"
        finally:
            if "page" in locals():
                page.close()

    def _find_and_click_apply_button(self, page: Page) -> bool:
        """Find and click the apply button using various patterns."""
        apply_selectors = [
            "button:has-text('Apply')",
            "a:has-text('Apply')",
            "input[value*='Apply']",
            "button:has-text('Apply Now')",
            "a:has-text('Apply Now')",
            "button[class*='apply']",
            "a[class*='apply']",
            ".apply-button",
            "#apply-button",
            "[data-testid*='apply']",
            "button:has-text('Submit Application')",
            "a:has-text('Submit Application')",
        ]

        for selector in apply_selectors:
            try:
                if page.is_visible(selector, timeout=5000):
                    page.click(selector)
                    page.wait_for_load_state("networkidle", timeout=15000)
                    console.print(f"[green]✅ Clicked apply button: {selector}[/green]")
                    return True
            except Exception:
                continue

        console.print("[yellow]⚠️ Could not find apply button[/yellow]")
        return False

    def _fill_generic_application_form(
        self, page: Page, profile: Dict, resume_path: str, cover_letter_path: str
    ) -> bool:
        """Fill application form using generic patterns."""
        try:
            # Fill basic profile information
            self._fill_basic_profile_info(page, profile)

            # Upload resume
            self._upload_resume_generic(page, resume_path)

            # Upload cover letter if available
            if cover_letter_path and Path(cover_letter_path).exists():
                self._upload_cover_letter_generic(page, cover_letter_path)

            # Handle common form steps
            max_steps = 10
            for step in range(max_steps):
                console.print(f"[cyan]Processing form step {step + 1}...[/cyan]")

                # Try to fill any visible form fields
                self._fill_visible_form_fields(page, profile)

                # Try to proceed to next step
                if not self._proceed_to_next_step(page):
                    # Try to submit if no next step
                    if self._try_submit_application(page):
                        return True
                    break

                # Wait for next page to load
                time.sleep(2)

            return False

        except Exception as e:
            console.print(f"[red]❌ Error filling generic form: {e}[/red]")
            return False

    def _fill_basic_profile_info(self, page: Page, profile: Dict) -> None:
        """Fill basic profile information using common field patterns."""
        field_mappings = {
            # Name fields
            "input[name*='first']": profile.get("first_name", ""),
            "input[name*='last']": profile.get("last_name", ""),
            "input[name*='name']": profile.get("name", ""),
            # Contact fields
            "input[name*='email']": profile.get("email", ""),
            "input[name*='phone']": profile.get("phone", ""),
            "input[type='email']": profile.get("email", ""),
            "input[type='tel']": profile.get("phone", ""),
            # Address fields
            "input[name*='address']": profile.get("address", ""),
            "input[name*='city']": profile.get("city", ""),
            "input[name*='location']": profile.get("location", ""),
            # Common text areas
            "textarea[name*='cover']": f"Dear Hiring Manager,\n\nI am interested in this position and believe my skills would be a great fit.\n\nBest regards,\n{profile.get('name', '')}",
        }

        for selector, value in field_mappings.items():
            if value:
                try:
                    if page.is_visible(selector, timeout=2000):
                        page.fill(selector, str(value))
                        console.print(f"[green]✅ Filled field: {selector}[/green]")
                except Exception:
                    continue

    def _upload_resume_generic(self, page: Page, resume_path: str) -> bool:
        """Upload resume using common file input patterns."""
        if not Path(resume_path).exists():
            return False

        upload_selectors = [
            "input[type='file'][name*='resume']",
            "input[type='file'][name*='cv']",
            "input[type='file'][id*='resume']",
            "input[type='file'][id*='cv']",
            "input[type='file']",  # Generic file input
        ]

        for selector in upload_selectors:
            try:
                if page.is_visible(selector, timeout=2000):
                    page.set_input_files(selector, resume_path)
                    console.print(f"[green]✅ Uploaded resume via: {selector}[/green]")
                    time.sleep(2)  # Wait for upload
                    return True
            except Exception:
                continue

        return False

    def _upload_cover_letter_generic(self, page: Page, cover_letter_path: str) -> bool:
        """Upload cover letter using common patterns."""
        if not Path(cover_letter_path).exists():
            return False

        upload_selectors = [
            "input[type='file'][name*='cover']",
            "input[type='file'][name*='letter']",
            "input[type='file'][id*='cover']",
            "input[type='file'][id*='letter']",
        ]

        for selector in upload_selectors:
            try:
                if page.is_visible(selector, timeout=2000):
                    page.set_input_files(selector, cover_letter_path)
                    console.print(f"[green]✅ Uploaded cover letter via: {selector}[/green]")
                    time.sleep(2)
                    return True
            except Exception:
                continue

        return False

    def _fill_visible_form_fields(self, page: Page, profile: Dict) -> None:
        """Fill any visible form fields with appropriate data."""
        try:
            # Get all visible input fields
            inputs = page.query_selector_all(
                "input[type='text'], input[type='email'], input[type='tel'], textarea"
            )

            for input_elem in inputs:
                try:
                    if not input_elem.is_visible():
                        continue

                    # Get field attributes
                    name = input_elem.get_attribute("name") or ""
                    id_attr = input_elem.get_attribute("id") or ""
                    placeholder = input_elem.get_attribute("placeholder") or ""

                    # Determine appropriate value based on field characteristics
                    field_text = (name + " " + id_attr + " " + placeholder).lower()

                    value = None
                    if any(keyword in field_text for keyword in ["email", "mail"]):
                        value = profile.get("email", "")
                    elif any(keyword in field_text for keyword in ["phone", "tel", "mobile"]):
                        value = profile.get("phone", "")
                    elif any(keyword in field_text for keyword in ["name", "first"]):
                        value = profile.get("first_name", profile.get("name", ""))
                    elif any(keyword in field_text for keyword in ["last", "surname"]):
                        value = profile.get("last_name", "")
                    elif any(keyword in field_text for keyword in ["address", "street"]):
                        value = profile.get("address", "")
                    elif any(keyword in field_text for keyword in ["city", "location"]):
                        value = profile.get("city", profile.get("location", ""))

                    if value:
                        input_elem.fill(str(value))

                except Exception:
                    continue

        except Exception as e:
            console.print(f"[yellow]⚠️ Error filling visible fields: {e}[/yellow]")

    def _proceed_to_next_step(self, page: Page) -> bool:
        """Try to proceed to the next step in the application."""
        next_selectors = [
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Save & Continue')",
            "input[type='submit'][value*='Next']",
            "input[type='submit'][value*='Continue']",
            "a:has-text('Next')",
            "a:has-text('Continue')",
            ".next-button",
            "#next-button",
            "[data-testid*='next']",
            "[data-testid*='continue']",
        ]

        for selector in next_selectors:
            try:
                if page.is_visible(selector, timeout=2000):
                    page.click(selector)
                    page.wait_for_load_state("networkidle", timeout=15000)
                    console.print(f"[green]✅ Proceeded to next step: {selector}[/green]")
                    return True
            except Exception:
                continue

        return False

    def _try_submit_application(self, page: Page) -> bool:
        """Try to submit the final application."""
        submit_selectors = [
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Send Application')",
            "input[type='submit'][value*='Submit']",
            "input[type='submit'][value*='Apply']",
            "a:has-text('Submit')",
            "a:has-text('Apply')",
            ".submit-button",
            "#submit-button",
            "[data-testid*='submit']",
            "[data-testid*='apply']",
        ]

        for selector in submit_selectors:
            try:
                if page.is_visible(selector, timeout=2000):
                    page.click(selector)
                    page.wait_for_load_state("networkidle", timeout=15000)
                    console.print(f"[green]✅ Submitted application: {selector}[/green]")
                    return True
            except Exception:
                continue

        return False


class ManualApplicationSubmitter(BaseSubmitter):
    """
    Manual application submitter - opens the job page and provides instructions.
    This is the ultimate fallback when all automated methods fail.
    """

    def submit(self, job: Dict, profile: Dict, resume_path: str, cover_letter_path: str) -> str:
        """
        Open job page for manual application.

        Args:
            job: Job dictionary
            profile: User profile
            resume_path: Path to resume file
            cover_letter_path: Path to cover letter file

        Returns:
            Status string
        """
        console.print("[red]🚨 Using Manual Application Mode[/red]")

        try:
            page = self.ctx.new_page()
            page.goto(job["url"], timeout=60000)

            # Display manual application instructions
            self._display_manual_instructions(job, profile, resume_path, cover_letter_path)

            # Keep page open for manual application
            console.print(
                "[yellow]⏸️ Page opened for manual application. Press Enter when done...[/yellow]"
            )
            input()  # Wait for user input

            page.close()
            return "Manual - User completed manually"

        except Exception as e:
            console.print(f"[red]❌ Error opening manual application: {e}[/red]")
            return f"Failed - {str(e)}"

    def _display_manual_instructions(
        self, job: Dict, profile: Dict, resume_path: str, cover_letter_path: str
    ) -> None:
        """Display instructions for manual application."""
        console.print("\n[bold red]📋 MANUAL APPLICATION INSTRUCTIONS[/bold red]")
        console.print("=" * 60)
        console.print(f"[bold]Job Title:[/bold] {job.get('title', 'Unknown')}")
        console.print(f"[bold]Company:[/bold] {job.get('company', 'Unknown')}")
        console.print(f"[bold]URL:[/bold] {job.get('url', 'Unknown')}")
        console.print()
        console.print("[bold]📄 Documents to upload:[/bold]")
        console.print(f"  • Resume: {resume_path}")
        if cover_letter_path and Path(cover_letter_path).exists():
            console.print(f"  • Cover Letter: {cover_letter_path}")
        console.print()
        console.print("[bold]👤 Profile Information:[/bold]")
        console.print(f"  • Name: {profile.get('name', 'N/A')}")
        console.print(f"  • Email: {profile.get('email', 'N/A')}")
        console.print(f"  • Phone: {profile.get('phone', 'N/A')}")
        console.print(f"  • Location: {profile.get('location', 'N/A')}")
        console.print()
        console.print(
            "[bold yellow]⚠️ Please complete the application manually and press Enter when done.[/bold yellow]"
        )
        console.print("=" * 60)


class EmergencyEmailSubmitter(BaseSubmitter):
    """
    Emergency email submitter - creates an email draft for manual sending.
    Used when even manual browser application fails.
    """

    def submit(self, job: Dict, profile: Dict, resume_path: str, cover_letter_path: str) -> str:
        """
        Create email draft for manual sending.

        Args:
            job: Job dictionary
            profile: User profile
            resume_path: Path to resume file
            cover_letter_path: Path to cover letter file

        Returns:
            Status string
        """
        console.print("[red]🚨 Using Emergency Email Mode[/red]")

        try:
            email_draft = self._create_email_draft(job, profile, resume_path, cover_letter_path)

            # Save email draft to file
            draft_file = (
                Path("emergency_applications")
                / f"email_draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            draft_file.parent.mkdir(exist_ok=True)

            with open(draft_file, "w", encoding="utf-8") as f:
                f.write(email_draft)

            console.print(f"[green]✅ Email draft saved to: {draft_file}[/green]")
            console.print(
                "[yellow]📧 Please send this email manually with the attached documents.[/yellow]"
            )

            return f"Manual - Email draft created: {draft_file}"

        except Exception as e:
            console.print(f"[red]❌ Error creating email draft: {e}[/red]")
            return f"Failed - {str(e)}"

    def _create_email_draft(
        self, job: Dict, profile: Dict, resume_path: str, cover_letter_path: str
    ) -> str:
        """Create email draft content."""
        subject = (
            f"Application for {job.get('title', 'Position')} - {profile.get('name', 'Applicant')}"
        )

        body = f"""Subject: {subject}

Dear Hiring Manager,

I am writing to express my interest in the {job.get('title', 'position')} role at {job.get('company', 'your company')}.

{job.get('summary', 'I believe my skills and experience make me a strong candidate for this position.')}

Please find my resume and cover letter attached for your review.

I look forward to hearing from you.

Best regards,
{profile.get('name', 'Your Name')}
{profile.get('email', 'your.email@example.com')}
{profile.get('phone', 'Your Phone Number')}

---
Job Details:
- Title: {job.get('title', 'N/A')}
- Company: {job.get('company', 'N/A')}
- URL: {job.get('url', 'N/A')}
- Applied: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Attachments to include:
- Resume: {resume_path}
- Cover Letter: {cover_letter_path if cover_letter_path and Path(cover_letter_path).exists() else 'N/A'}
"""

        return body


class FallbackATSSubmitter:
    def __init__(self, *args, **kwargs):
        pass
