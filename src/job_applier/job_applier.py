"""
Job Applier Module for AutoJobAgent.

This module provides the JobApplier class, which orchestrates the job application process:
- Launches browser context
- Detects ATS system
- Selects the appropriate submitter
- Handles document paths
- Invokes the submitter to apply for the job

ATS-specific form filling remains in their respective submitter classes.
"""

from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, BrowserContext
from src.ats import detect, get_submitter
from src.document_modifier.document_modifier import customize
from rich.console import Console
import time
from src.utils.document_generator import customize

console = Console()


class JobApplier:
    """
    Orchestrates the job application process for a given job and profile.
    Handles browser automation, ATS detection, and submitter invocation.
    """

    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        self.profile_name = profile.get("profile_name", "default")

    def apply(
        self, job: Dict[str, Any], ats: str = "auto", headless: bool = True, delay: int = 30
    ) -> str:
        """
        Apply to a single job using the appropriate ATS submitter.
        Args:
            job: Job dictionary
            ats: ATS system to use (default: auto-detect)
            headless: Whether to run browser in headless mode
            delay: Delay between applications (if batch)
        Returns:
            Status string (e.g., 'Applied', 'Failed', 'Manual')
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            try:
                console.print(
                    f"[bold blue]📝 Applying to job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}[/bold blue]"
                )
                ats_system = ats if ats != "auto" else detect(job.get("url", ""))
                console.print(f"[cyan]ATS System:[/cyan] {ats_system}")
                submitter = get_submitter(ats_system, context)
                if not submitter:
                    console.print(f"[red]❌ No submitter available for {ats_system}[/red]")
                    return f"No submitter for {ats_system}"
                # Generate documents
                doc_result = customize(job, self.profile_name)
                resume_path = doc_result.get("resume") or ""
                cover_letter_path = doc_result.get("cover_letter") or ""
                # Apply to job
                result = submitter.submit(job, self.profile, resume_path, cover_letter_path)
                if result == "Applied":
                    console.print("[bold green]✅ Application successful![/bold green]")
                else:
                    console.print(f"[red]❌ Application failed: {result}[/red]")
                time.sleep(delay)
                return result
            except Exception as e:
                console.print(f"[red]❌ Error applying to job: {e}[/red]")
                return f"Failed: {e}"
            finally:
                browser.close()
