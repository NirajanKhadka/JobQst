"""
Job Scrapers Package - Refactored and Simplified
Provides core scrapers for job boards with clean architecture.
"""

# Core scrapers - essential functionality only
from .base_scraper import BaseJobScraper
from .eluta_enhanced import ElutaEnhancedScraper
from .eluta_working import ElutaWorkingScraper  # New working scraper
from .parallel_job_scraper import ParallelJobScraper
from .eluta_optimized_parallel import ElutaOptimizedParallelScraper  # Optimized parallel scraper
from .eluta_multi_browser import ElutaMultiBrowserScraper  # Multi-browser context scraper
from .eluta_multi_ip import ElutaMultiIPScraper  # Multi-IP address scraper

# Fallback scrapers for robustness
from .fallback_scrapers import BasicFallbackScraper, EmergencyCSVScraper

# Enhanced scrapers
try:
    from .indeed_enhanced import EnhancedIndeedScraper
    INDEED_AVAILABLE = True
except ImportError:
    INDEED_AVAILABLE = False

try:
    from .linkedin_enhanced import EnhancedLinkedInScraper
    LINKEDIN_AVAILABLE = True
except ImportError:
    LINKEDIN_AVAILABLE = False

try:
    from .jobbank_enhanced import EnhancedJobBankScraper
    JOBBANK_AVAILABLE = True
except ImportError:
    JOBBANK_AVAILABLE = False

try:
    from .monster_enhanced import EnhancedMonsterScraper
    MONSTER_AVAILABLE = True
except ImportError:
    MONSTER_AVAILABLE = False

# Optional specialized scrapers
try:
    from .workday_scraper import WorkdayJobScraper
    WORKDAY_AVAILABLE = True
except ImportError:
    WORKDAY_AVAILABLE = False

# Registry of core scrapers (simplified)
SCRAPER_REGISTRY = {
    "eluta": ElutaWorkingScraper,        # Primary working scraper (proven method)
    "eluta_enhanced": ElutaEnhancedScraper,  # Complex enhanced scraper (backup)
    "parallel": ParallelJobScraper,      # High-performance parallel scraper
    "eluta_optimized": ElutaOptimizedParallelScraper,  # Optimized parallel with job analysis
    "eluta_multi": ElutaMultiBrowserScraper,  # Multi-browser context scraper (single context stealth)
    "eluta_multi_ip": ElutaMultiIPScraper,  # Multi-IP address scraper (requires proxies)
}

# Add optional scrapers if available
if INDEED_AVAILABLE:
    SCRAPER_REGISTRY["indeed"] = EnhancedIndeedScraper

if LINKEDIN_AVAILABLE:
    SCRAPER_REGISTRY["linkedin"] = EnhancedLinkedInScraper

if JOBBANK_AVAILABLE:
    SCRAPER_REGISTRY["jobbank"] = EnhancedJobBankScraper

if MONSTER_AVAILABLE:
    SCRAPER_REGISTRY["monster"] = EnhancedMonsterScraper

if WORKDAY_AVAILABLE:
    SCRAPER_REGISTRY["workday"] = WorkdayJobScraper

# Default scraper for fallback
DEFAULT_SCRAPER = ElutaWorkingScraper

# Available scraper names
AVAILABLE_SCRAPERS = list(SCRAPER_REGISTRY.keys())


def get_scraper(site_name: str, profile: dict, **kwargs):
    """
    Get a scraper instance for the specified site with fallback support.

    Args:
        site_name: Name of the job site (indeed, eluta, linkedin, etc.)
        profile: User profile dictionary
        **kwargs: Additional arguments for the scraper

    Returns:
        Scraper instance

    Raises:
        ValueError: If site_name is not supported
    """
    if site_name not in SCRAPER_REGISTRY:
        available_sites = ", ".join(SCRAPER_REGISTRY.keys())
        raise ValueError(f"Unsupported site: {site_name}. Available sites: {available_sites}")

    scraper_class = SCRAPER_REGISTRY[site_name]
    return scraper_class(profile, **kwargs)


def get_scraper_with_fallbacks(site_name: str, profile: dict, **kwargs):
    """
    Get a scraper instance with comprehensive fallback chain.
    Fallback order: Requested -> Enhanced -> Basic -> Emergency CSV

    Args:
        site_name: Name of the job site
        profile: User profile dictionary
        **kwargs: Additional arguments for the scraper

    Returns:
        Scraper instance or fallback method
    """
    from rich.console import Console
    console = Console()

    # Method 1: Try requested scraper
    try:
        console.print(f"[cyan]🔄 Attempting {site_name} scraper...[/cyan]")
        return get_scraper(site_name, profile, **kwargs)
    except Exception as e:
        console.print(f"[yellow]❌ {site_name} scraper failed: {e}[/yellow]")

    # Method 2: Try enhanced scrapers in priority order
    enhanced_priority = ["eluta", "parallel"]
    for enhanced_site in enhanced_priority:
        if enhanced_site != site_name and enhanced_site in SCRAPER_REGISTRY:
            try:
                console.print(f"[cyan]🔄 Trying enhanced {enhanced_site} scraper...[/cyan]")
                return get_scraper(enhanced_site, profile, **kwargs)
            except Exception as e:
                console.print(f"[yellow]❌ Enhanced {enhanced_site} scraper failed: {e}[/yellow]")

    # Method 3: Try basic scraper (base scraper with minimal functionality)
    try:
        console.print("[cyan]🔄 Trying basic scraper...[/cyan]")
        return BasicFallbackScraper(profile, **kwargs)
    except Exception as e:
        console.print(f"[yellow]❌ Basic scraper failed: {e}[/yellow]")

    # Method 4: Emergency CSV import scraper
    try:
        console.print("[red]🔄 Using emergency CSV import scraper...[/red]")
        return EmergencyCSVScraper(profile, **kwargs)
    except Exception as e:
        console.print(f"[red]❌ Emergency CSV scraper failed: {e}[/red]")
        raise RuntimeError("All scraper fallback methods failed")


def scrape_with_fallbacks(keywords: list, profile: dict, site_name: str = "eluta", **kwargs):
    """
    Scrape jobs with comprehensive fallback methods.

    Args:
        keywords: List of keywords to search for
        profile: User profile dictionary
        site_name: Preferred site name
        **kwargs: Additional scraping arguments

    Returns:
        List of scraped jobs
    """
    from rich.console import Console
    console = Console()

    console.print(f"[bold]🚀 Starting job scraping with fallbacks for keywords: {', '.join(keywords)}[/bold]")

    # Get scraper with fallbacks
    scraper = get_scraper_with_fallbacks(site_name, profile, **kwargs)

    # Try to scrape jobs
    try:
        jobs = scraper.scrape_jobs(keywords)
        console.print(f"[bold green]✅ Successfully scraped {len(jobs)} jobs![/bold green]")
        return jobs
    except Exception as e:
        console.print(f"[red]❌ Scraping failed: {e}[/red]")

        # Final fallback: Return empty list with error info
        console.print("[yellow]⚠️ Returning empty job list as final fallback[/yellow]")
        return []


def get_available_sites():
    """
    Get list of available job sites.
    
    Returns:
        List of available site names
    """
    return list(SCRAPER_REGISTRY.keys())


def create_multi_site_scraper(profile: dict, sites: list = None, **kwargs):
    """
    Create a multi-site scraper that combines results from multiple sites.
    
    Args:
        profile: User profile dictionary
        sites: List of site names to scrape (default: all available)
        **kwargs: Additional arguments for scrapers
        
    Returns:
        MultiSiteScraper instance
    """
    if sites is None:
        sites = get_available_sites()
    
    scrapers = {}
    for site in sites:
        try:
            scrapers[site] = get_scraper(site, profile, **kwargs)
        except ValueError as e:
            print(f"Warning: {e}")
    
    from .multi_site_scraper import MultiSiteScraper
    return MultiSiteScraper(scrapers, profile)
