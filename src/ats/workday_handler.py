"""
Workday ATS Handler
Provides the Workday-specific application logic for UniversalApplier.
"""

import asyncio
from typing import Dict
from playwright.async_api import Page
from rich.console import Console
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
)

console = Console()

async def apply_workday(page: Page, job: Dict) -> str:
    """
    Apply to a job using Workday ATS-specific logic.
    This function can be expanded with Workday-specific steps.
    
    For now, uses generic application logic with Workday-specific logging.
    """
    console.print("[cyan]🏢 Using Workday-specific application process...[/cyan]")
    
    # TODO: Implement Workday-specific logic here
    # For now, fallback to generic application process
    
    try:
        # Step 1: Find and click apply button
        if not await find_and_click_apply_button(page):
            return "no_apply_button"

        # Step 2: Handle potential redirects or new tabs
        await asyncio.sleep(2)

        # Step 3: Fill application form(s) - handle multi-step forms
        max_steps = 10
        for step in range(max_steps):
            console.print(f"[cyan]📝 Processing Workday form step {step + 1}...[/cyan]")

            # Check for CAPTCHA or login requirements
            if await check_for_captcha(page):
                return "captcha_detected"

            if await check_for_login_required(page):
                return "login_required"

            # Get profile data from context
            profile = getattr(page.context, '_profile', {})
            resume_path = getattr(page.context, '_resume_path', '')
            cover_letter_path = getattr(page.context, '_cover_letter_path', '')
            
            # Fill visible form fields
            fields_filled = await fill_form_fields(page, profile)
            console.print(f"[green]✅ Filled {fields_filled} Workday form fields[/green]")

            # Upload documents
            if resume_path:
                resume_uploaded = await upload_resume(page, resume_path)
                if resume_uploaded:
                    console.print("[green]✅ Resume uploaded to Workday[/green]")

            if cover_letter_path:
                cover_uploaded = await upload_cover_letter(page, cover_letter_path)
                if cover_uploaded:
                    console.print("[green]✅ Cover letter uploaded to Workday[/green]")
            
            # Try to proceed to next step
            if await click_next_or_continue(page):
                console.print("[green]✅ Proceeded to next Workday step[/green]")
                await asyncio.sleep(2)
                continue

            # Try to submit if no next step
            if await click_submit_button(page):
                console.print("[green]✅ Workday application submitted![/green]")
                return "applied"

            # If we can't proceed or submit, we might be done or stuck
            break

        return "manual"  # Couldn't complete automatically

    except Exception as e:
        console.print(f"[red]❌ Workday application error: {e}[/red]")
        return f"error: {str(e)}"

