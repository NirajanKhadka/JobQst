"""
Form Utilities for ATS Job Application
Contains helper functions for form filling, document upload, and page interaction.
"""

import asyncio
from typing import Dict, List
from pathlib import Path
from playwright.async_api import Page
from rich.console import Console

console = Console()


async def find_and_click_apply_button(page: Page) -> bool:
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


async def fill_form_fields(page: Page, profile: Dict) -> int:
    """Fill form fields with profile data."""
    fields_filled = 0

    # Get profile data
    first_name = profile.get(
        "first_name",
        profile.get("name", "").split()[0] if profile.get("name") else "",
    )
    last_name = profile.get(
        "last_name",
        profile.get("name", "").split()[-1] if profile.get("name") else "",
    )
    email = profile.get("email", "")
    phone = profile.get("phone", "")
    location = profile.get("location", "")

    # Field mappings
    field_mappings = {
        # Name fields
        "input[name*='firstName'], input[name*='first_name'], input[name*='fname']": first_name,
        "input[name*='lastName'], input[name*='last_name'], input[name*='lname']": last_name,
        "input[name*='fullName'], input[name*='full_name'], input[name*='name']:not([name*='first']):not([name*='last'])": profile.get(
            "name", ""
        ),
        # Contact fields
        "input[type='email'], input[name*='email']": email,
        "input[type='tel'], input[name*='phone'], input[name*='telephone'], input[name*='mobile']": phone,
        # Location fields
        "input[name*='location'], input[name*='address'], input[name*='city']": location,
        # Common text areas
        "textarea[name*='cover'], textarea[name*='message'], textarea[name*='note']": generate_cover_letter_text(profile),
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


async def upload_resume(page: Page, resume_path: str) -> bool:
    """Upload resume using comprehensive file input detection."""
    if not resume_path or not Path(resume_path).exists():
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
                    await element.set_input_files(resume_path)
                    await asyncio.sleep(2)  # Wait for upload
                    console.print(f"[green]✅ Uploaded resume via: {selector}[/green]")
                    return True
        except Exception:
            continue

    return False


async def upload_cover_letter(page: Page, cover_letter_path: str) -> bool:
    """Upload cover letter using comprehensive detection."""
    if not cover_letter_path or not Path(cover_letter_path).exists():
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
                    await element.set_input_files(cover_letter_path)
                    await asyncio.sleep(2)
                    console.print(f"[green]✅ Uploaded cover letter via: {selector}[/green]")
                    return True
        except Exception:
            continue

    return False


async def click_next_or_continue(page: Page) -> bool:
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


async def click_submit_button(page: Page) -> bool:
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
                if await check_for_confirmation(page):
                    return True

                return True  # Assume success if no error
        except Exception:
            continue

    return False


async def check_for_captcha(page: Page) -> bool:
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


async def check_for_login_required(page: Page) -> bool:
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


async def check_for_confirmation(page: Page) -> bool:
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


def generate_cover_letter_text(profile: Dict) -> str:
    """Generate a simple cover letter text."""
    name = profile.get("name", "")
    return f"""Dear Hiring Manager,

I am writing to express my interest in this position. I believe my skills and experience make me a strong candidate for this role.

Please find my resume attached for your review. I look forward to hearing from you.

Best regards,
{name}"""

