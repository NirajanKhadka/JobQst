"""
Lever ATS submitter implementation.
Handles job application automation for Lever-based job portals.
"""

from typing import Dict

from playwright.sync_api import Page
from rich.console import Console

from .base_submitter import BaseSubmitter
from src.core.exceptions import NeedsHumanException

console = Console()


class LeverSubmitter(BaseSubmitter):
    """
    Submitter for Lever ATS (FUTURE FEATURE).
    This is a stub implementation that will be developed in a future release.
    """

    def __init__(self, browser_context=None):
        self.browser_context = browser_context

    def submit(self, job: Dict, profile: Dict, resume_path: str, cover_letter_path: str) -> str:
        """
        Submit an application to Lever ATS.

        Args:
            job: Job dictionary with details
            profile: User profile dictionary
            resume_path: Path to the resume file
            cover_letter_path: Path to the cover letter file

        Returns:
            Status string (e.g., "Applied", "Failed", "Manual")

        Raises:
            NotImplementedError: This is a future feature
        """
        console.print("[bold yellow]Lever ATS integration is a future feature[/bold yellow]")
        raise NotImplementedError(
            "Lever ATS integration is not yet implemented. "
            "This feature will be available in a future release."
        )
