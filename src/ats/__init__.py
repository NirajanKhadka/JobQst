import warnings
warnings.warn("[DEPRECATED] Use 'src.ats' instead of root-level 'ats' module. This module will be removed.", DeprecationWarning)

"""
ATS package initialization.
Provides functions to detect and get submitters for various ATS systems.
"""

import re
from typing import Dict, Optional, Union

from playwright.sync_api import BrowserContext

# Import ATS submitters
from .base_submitter import BaseSubmitter

# Import fallback submitters
from .fallback_submitters import GenericATSSubmitter, ManualApplicationSubmitter, EmergencyEmailSubmitter

# Import available submitters (some may be stubs)
try:
    from .workday import WorkdaySubmitter
    WORKDAY_AVAILABLE = True
except ImportError:
    WORKDAY_AVAILABLE = False

try:
    from .icims import ICIMSSubmitter
    ICIMS_AVAILABLE = True
except ImportError:
    ICIMS_AVAILABLE = False

try:
    from .greenhouse import GreenhouseSubmitter
    GREENHOUSE_AVAILABLE = True
except ImportError:
    GREENHOUSE_AVAILABLE = False

try:
    from .bamboohr import BambooHRSubmitter
    BAMBOOHR_AVAILABLE = True
except ImportError:
    BAMBOOHR_AVAILABLE = False

try:
    from .lever import LeverSubmitter
    LEVER_AVAILABLE = True
except ImportError:
    LEVER_AVAILABLE = False

# URL patterns for ATS detection
ATS_PATTERNS = {
    "workday": [
        r"myworkdayjobs\.com",
        r"workday\.com",
        r"wd3\.myworkdayjobs\.com",
        r"workdayjobs\.com"
    ],
    "icims": [
        r"icims\.com",
        r"jobs\.icims\.com",
        r"careers\.icims\.com"
    ],
    "greenhouse": [
        r"greenhouse\.io",
        r"boards\.greenhouse\.io",
        r"app\.greenhouse\.io"
    ],
    "lever": [
        r"lever\.co",
        r"jobs\.lever\.co",
        r"careers\.lever\.co"
    ],
    "bamboohr": [
        r"bamboohr\.com",
        r"\.bamboohr\.com",
        r"careers\.bamboohr\.com"
    ]
}

# Registry of ATS submitters - only include available ones
ATS_SUBMITTERS = {}

# Register available submitters
if WORKDAY_AVAILABLE:
    ATS_SUBMITTERS["workday"] = WorkdaySubmitter

if ICIMS_AVAILABLE:
    ATS_SUBMITTERS["icims"] = ICIMSSubmitter

if GREENHOUSE_AVAILABLE:
    ATS_SUBMITTERS["greenhouse"] = GreenhouseSubmitter

if BAMBOOHR_AVAILABLE:
    ATS_SUBMITTERS["bamboohr"] = BambooHRSubmitter

if LEVER_AVAILABLE:
    ATS_SUBMITTERS["lever"] = LeverSubmitter


def detect(url: str) -> str:
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


def get_submitter(ats_name: str, browser_context: BrowserContext) -> BaseSubmitter:
    """
    Get a submitter instance for the specified ATS.

    Args:
        ats_name: ATS system name
        browser_context: Playwright browser context

    Returns:
        ATS submitter instance

    Raises:
        ValueError: If ATS is unknown or not supported
    """
    if ats_name == "unknown":
        raise ValueError("Unknown ATS system")

    if ats_name == "lever" and not LEVER_AVAILABLE:
        raise ValueError("Lever ATS support is not available")

    if ats_name not in ATS_SUBMITTERS:
        raise ValueError(f"Unsupported ATS system: {ats_name}")

    # Create and return the submitter instance
    return ATS_SUBMITTERS[ats_name](browser_context)


def get_submitter_with_fallbacks(ats_name: str, browser_context: BrowserContext) -> BaseSubmitter:
    """
    Get a submitter instance with comprehensive fallback support.
    Fallback chain: Specific ATS -> Generic ATS -> Manual -> Emergency Email

    Args:
        ats_name: ATS system name
        browser_context: Playwright browser context

    Returns:
        ATS submitter instance (never fails)
    """
    from rich.console import Console
    console = Console()

    # Method 1: Try specific ATS submitter
    try:
        if ats_name != "unknown" and ats_name in ATS_SUBMITTERS:
            console.print(f"[cyan]🔄 Using specific {ats_name} submitter...[/cyan]")
            return get_submitter(ats_name, browser_context)
    except Exception as e:
        console.print(f"[yellow]❌ Specific {ats_name} submitter failed: {e}[/yellow]")

    # Method 2: Try generic ATS submitter
    try:
        console.print("[cyan]🔄 Using generic ATS submitter...[/cyan]")
        return GenericATSSubmitter(browser_context)
    except Exception as e:
        console.print(f"[yellow]❌ Generic ATS submitter failed: {e}[/yellow]")

    # Method 3: Try manual application submitter
    try:
        console.print("[yellow]🔄 Using manual application submitter...[/yellow]")
        return ManualApplicationSubmitter(browser_context)
    except Exception as e:
        console.print(f"[yellow]❌ Manual application submitter failed: {e}[/yellow]")

    # Method 4: Emergency email submitter (always works)
    console.print("[red]🚨 Using emergency email submitter as final fallback...[/red]")
    return EmergencyEmailSubmitter(browser_context)


def submit_application_with_fallbacks(job: dict, profile: dict, resume_path: str,
                                    cover_letter_path: str, browser_context: BrowserContext) -> str:
    """
    Submit job application with comprehensive fallback methods.

    Args:
        job: Job dictionary
        profile: User profile dictionary
        resume_path: Path to resume file
        cover_letter_path: Path to cover letter file
        browser_context: Playwright browser context

    Returns:
        Application status string
    """
    from rich.console import Console
    console = Console()

    console.print(f"[bold]🚀 Starting application with fallbacks for: {job.get('title', 'Unknown')}[/bold]")

    # Detect ATS system
    ats_name = detect(job.get("url", ""))
    console.print(f"[cyan]🔍 Detected ATS: {ats_name}[/cyan]")

    # Get submitter with fallbacks
    submitter = get_submitter_with_fallbacks(ats_name, browser_context)

    # Submit application
    try:
        status = submitter.submit(job, profile, resume_path, cover_letter_path)
        console.print(f"[bold green]✅ Application result: {status}[/bold green]")
        return status
    except Exception as e:
        console.print(f"[red]❌ All application methods failed: {e}[/red]")
        return f"Failed - {str(e)}"


# Additional helper functions

def register_submitter(ats_name: str, submitter_class) -> None:
    """
    Register a new ATS submitter.
    
    Args:
        ats_name: ATS system name
        submitter_class: Submitter class
    """
    ATS_SUBMITTERS[ats_name] = submitter_class


def get_supported_ats() -> list:
    """
    Get a list of supported ATS systems.
    
    Returns:
        List of supported ATS system names
    """
    return list(ATS_SUBMITTERS.keys())
