"""
Lever ATS Handler
Provides the Lever-specific application logic for UniversalApplier.
"""

from typing import Dict
from playwright.async_api import Page
from rich.console import Console

console = Console()

async def apply_lever(page: Page, job: Dict) -> str:
    """
    Apply to a job using Lever ATS-specific logic.
    This function can be expanded with Lever-specific steps.
    """
    console.print("[cyan]🎯 Using Lever-specific application process...[/cyan]")
    # Fallback to generic application process attached to context
    generic_apply = getattr(page.context, '_generic_apply', None)
    if generic_apply:
        return await generic_apply(page, job)
    return "error: generic_apply not available"

