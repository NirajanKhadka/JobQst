"""
ATS Utilities
Shared utilities for ATS detection, patterns, and common operations.
"""

import re
from typing import Dict, List, Optional
from playwright.sync_api import Page, BrowserContext
from rich.console import Console

console = Console()

# URL patterns for ATS detection
ATS_PATTERNS = {
    "workday": [
        r"myworkdayjobs\.com",
        r"workday\.com",
        r"wd3\.myworkdayjobs\.com",
        r"workdayjobs\.com",
    ],
    "icims": [r"icims\.com", r"jobs\.icims\.com", r"careers\.icims\.com"],
    "greenhouse": [r"greenhouse\.io", r"boards\.greenhouse\.io", r"app\.greenhouse\.io"],
    "lever": [r"lever\.co", r"jobs\.lever\.co", r"careers\.lever\.co"],
    "bamboohr": [r"bamboohr\.com", r"\.bamboohr\.com", r"careers\.bamboohr\.com"],
}

# Common form field selectors across ATS systems
COMMON_FORM_SELECTORS = {
    "first_name": [
        "input[name*='firstName']",
        "input[id*='firstName']",
        "input[name*='first_name']",
        "input[id*='first_name']",
        "input[name*='fname']",
        "input[id*='fname']",
    ],
    "last_name": [
        "input[name*='lastName']",
        "input[id*='lastName']",
        "input[name*='last_name']",
        "input[id*='last_name']",
        "input[name*='lname']",
        "input[id*='lname']",
    ],
    "email": [
        "input[type='email']",
        "input[name*='email']",
        "input[id*='email']",
        "input[name*='e-mail']",
        "input[id*='e-mail']",
    ],
    "phone": [
        "input[name*='phone']",
        "input[id*='phone']",
        "input[name*='telephone']",
        "input[id*='telephone']",
        "input[name*='mobile']",
        "input[id*='mobile']",
    ],
    "resume": [
        "input[type='file'][name*='resume']",
        "input[type='file'][id*='resume']",
        "input[type='file'][name*='Resume']",
        "input[type='file'][id*='Resume']",
        "input[type='file'][name*='upload']",
        "input[type='file'][name*='cv']",
        "input[type='file'][id*='cv']",
    ],
    "cover_letter": [
        "input[type='file'][name*='cover']",
        "input[type='file'][id*='cover']",
        "input[type='file'][name*='Cover']",
        "input[type='file'][id*='Cover']",
        "input[type='file'][name*='letter']",
        "input[type='file'][id*='letter']",
    ],
}

# Common apply button selectors
APPLY_BUTTON_SELECTORS = [
    "button:has-text('Apply')",
    "a:has-text('Apply')",
    "button:has-text('Apply Now')",
    "a:has-text('Apply Now')",
    "button:has-text('Submit Application')",
    "a:has-text('Submit Application')",
    "[data-automation-id*='apply']",
    "[class*='apply']",
    "input[type='button'][value*='Apply']",
    "input[type='submit'][value*='Apply']",
]

# Common submit button selectors
SUBMIT_BUTTON_SELECTORS = [
    "button:has-text('Submit')",
    "input[type='submit']",
    "button:has-text('Submit Application')",
    "button:has-text('Send Application')",
    "button:has-text('Complete Application')",
    "[data-automation-id*='submit']",
    "[class*='submit']",
]

# Confirmation message patterns
CONFIRMATION_PATTERNS = [
    "thank you for your application",
    "application submitted",
    "successfully submitted",
    "has been received",
    "application received",
    "thank you for applying",
    "application complete",
]


def detect_ats_system(url: str) -> str:
    """
    Detect the ATS system from a job URL.

    Args:
        url: Job posting URL

    Returns:
        ATS system name or "unknown"
    """
    if not url:
        return "unknown"

    url = url.lower()

    for ats_name, patterns in ATS_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url):
                return ats_name

    return "unknown"


def find_and_click_apply_button(page: Page) -> bool:
    """
    Find and click the apply button using common selectors.

    Args:
        page: Playwright page object

    Returns:
        True if apply button was found and clicked, False otherwise
    """
    for selector in APPLY_BUTTON_SELECTORS:
        try:
            if page.is_visible(selector):
                console.print(f"[green]Found apply button: {selector}[/green]")
                page.click(selector)
                page.wait_for_timeout(2000)
                return True
        except Exception as e:
            console.print(f"[dim]Selector {selector} failed: {e}[/dim]")
            continue

    console.print("[yellow]No apply button found with common selectors[/yellow]")
    return False


def find_and_click_submit_button(page: Page) -> bool:
    """
    Find and click the submit button using common selectors.

    Args:
        page: Playwright page object

    Returns:
        True if submit button was found and clicked, False otherwise
    """
    for selector in SUBMIT_BUTTON_SELECTORS:
        try:
            if page.is_visible(selector):
                console.print(f"[green]Found submit button: {selector}[/green]")
                page.click(selector)
                page.wait_for_timeout(2000)
                return True
        except Exception as e:
            console.print(f"[dim]Selector {selector} failed: {e}[/dim]")
            continue

    console.print("[yellow]No submit button found with common selectors[/yellow]")
    return False


def check_for_confirmation(page: Page) -> bool:
    """
    Check if application was successfully submitted.

    Args:
        page: Playwright page object

    Returns:
        True if confirmation message found, False otherwise
    """
    page_content = page.content().lower()

    for pattern in CONFIRMATION_PATTERNS:
        if pattern in page_content:
            console.print(f"[green]Found confirmation: {pattern}[/green]")
            return True

    # Also check for common confirmation selectors
    confirmation_selectors = [
        "text='Thank you for your application'",
        "text='Application submitted'",
        "text='successfully submitted'",
        "text='has been received'",
        "div.application-confirmation",
        "div.success-message",
        "div.confirmation-message",
    ]

    for selector in confirmation_selectors:
        try:
            if page.is_visible(selector):
                console.print(f"[green]Found confirmation element: {selector}[/green]")
                return True
        except Exception:
            continue

    return False


def fill_common_form_fields(page: Page, profile: Dict, field_type: str) -> int:
    """
    Fill common form fields using shared selectors.

    Args:
        page: Playwright page object
        profile: User profile dictionary
        field_type: Type of field to fill ('personal', 'resume', 'cover_letter')

    Returns:
        Number of fields successfully filled
    """
    fields_filled = 0

    if field_type == "personal":
        # Fill personal information
        field_mappings = {
            "first_name": profile.get("name", "").split()[0] if profile.get("name") else "",
            "last_name": profile.get("name", "").split()[-1] if profile.get("name") else "",
            "email": profile.get("email", ""),
            "phone": profile.get("phone", ""),
        }

        for field_name, value in field_mappings.items():
            if not value:
                continue

            selectors = COMMON_FORM_SELECTORS.get(field_name, [])
            for selector in selectors:
                try:
                    if page.is_visible(selector):
                        page.fill(selector, value)
                        console.print(f"[green]Filled {field_name}: {value}[/green]")
                        fields_filled += 1
                        break
                except Exception:
                    continue

    return fields_filled


def upload_file(page: Page, file_path: str, field_type: str) -> bool:
    """
    Upload a file using common file input selectors.

    Args:
        page: Playwright page object
        file_path: Path to the file to upload
        field_type: Type of file ('resume' or 'cover_letter')

    Returns:
        True if file was uploaded successfully, False otherwise
    """
    selectors = COMMON_FORM_SELECTORS.get(field_type, [])

    for selector in selectors:
        try:
            if page.is_visible(selector):
                page.set_input_files(selector, file_path)
                console.print(f"[green]Uploaded {field_type}: {file_path}[/green]")
                return True
        except Exception as e:
            console.print(f"[dim]Selector {selector} failed: {e}[/dim]")
            continue

    console.print(f"[yellow]No {field_type} upload field found[/yellow]")
    return False


def wait_for_navigation(page: Page, timeout: int = 10000) -> None:
    """
    Wait for page navigation to complete.

    Args:
        page: Playwright page object
        timeout: Timeout in milliseconds
    """
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        try:
            page.wait_for_load_state("domcontentloaded", timeout=timeout)
        except Exception:
            console.print("[yellow]Navigation timeout, continuing...[/yellow]")


def check_for_captcha(page: Page) -> bool:
    """
    Check if CAPTCHA is present on the page.

    Args:
        page: Playwright page object

    Returns:
        True if CAPTCHA detected, False otherwise
    """
    captcha_indicators = [
        "text='CAPTCHA'",
        "text='captcha'",
        "text='Verify you are human'",
        "text='I am not a robot'",
        "iframe[src*='recaptcha']",
        "iframe[src*='captcha']",
        "[class*='captcha']",
        "[id*='captcha']",
    ]

    for indicator in captcha_indicators:
        try:
            if page.is_visible(indicator):
                console.print("[yellow]⚠️ CAPTCHA detected![/yellow]")
                return True
        except Exception:
            continue

    return False


def check_for_login_requirement(page: Page) -> bool:
    """
    Check if login is required before applying.

    Args:
        page: Playwright page object

    Returns:
        True if login is required, False otherwise
    """
    login_indicators = [
        "text='Sign In'",
        "text='Log In'",
        "text='Create an Account'",
        "text='Login'",
        "form[id*='login']",
        "input[name*='password']",
        "input[type='password']",
    ]

    for indicator in login_indicators:
        try:
            if page.is_visible(indicator):
                console.print("[yellow]Login required detected[/yellow]")
                return True
        except Exception:
            continue

    return False

