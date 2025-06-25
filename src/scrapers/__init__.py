"""
Job Scrapers Package - Unified Interface
Provides core scrapers for job boards with clean architecture and fallback support.
"""

from typing import Dict, List, Optional, Any
from rich.console import Console

# Import core scrapers from src/scrapers
try:
    from .comprehensive_eluta_scraper import ComprehensiveElutaScraper
    ELUTA_COMPREHENSIVE_AVAILABLE = True
except ImportError:
    ELUTA_COMPREHENSIVE_AVAILABLE = False

try:
    from .eluta_optimized_parallel import ElutaOptimizedParallelScraper
    ELUTA_OPTIMIZED_AVAILABLE = True
except ImportError:
    ELUTA_OPTIMIZED_AVAILABLE = False

try:
    from .eluta_multi_ip import ElutaMultiIPScraper
    ELUTA_MULTI_IP_AVAILABLE = True
except ImportError:
    ELUTA_MULTI_IP_AVAILABLE = False

try:
    from .parallel_job_scraper import ParallelJobScraper
    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False

try:
    from .modern_job_pipeline import ModernJobPipeline
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False

try:
    from .indeed_enhanced import IndeedEnhancedScraper
    INDEED_AVAILABLE = True
except ImportError:
    INDEED_AVAILABLE = False

try:
    from .linkedin_enhanced import LinkedInEnhancedScraper
    LINKEDIN_AVAILABLE = True
except ImportError:
    LINKEDIN_AVAILABLE = False

try:
    from .monster_enhanced import MonsterEnhancedScraper
    MONSTER_AVAILABLE = True
except ImportError:
    MONSTER_AVAILABLE = False

try:
    from .jobbank_enhanced import JobBankEnhancedScraper
    JOBANK_AVAILABLE = True
except ImportError:
    JOBANK_AVAILABLE = False

# Import from root-level scrapers for compatibility
try:
    from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
    from src.scrapers.eluta_optimized_parallel import ElutaOptimizedParallelScraper
    from src.scrapers.eluta_multi_ip import ElutaMultiIPScraper
    from src.scrapers.parallel_job_scraper import ParallelJobScraper as RootParallelJobScraper
    from src.ats.fallback_submitters import GenericATSSubmitter, ManualApplicationSubmitter, EmergencyEmailSubmitter
    ROOT_SCRAPERS_AVAILABLE = True
except ImportError:
    ROOT_SCRAPERS_AVAILABLE = False

# Registry of available scrapers
SCRAPER_REGISTRY = {}

# Add src/scrapers implementations if available
if ELUTA_COMPREHENSIVE_AVAILABLE:
    SCRAPER_REGISTRY["eluta"] = ComprehensiveElutaScraper
    SCRAPER_REGISTRY["eluta_comprehensive"] = ComprehensiveElutaScraper

if ELUTA_OPTIMIZED_AVAILABLE:
    SCRAPER_REGISTRY["eluta_optimized"] = ElutaOptimizedParallelScraper

if ELUTA_MULTI_IP_AVAILABLE:
    SCRAPER_REGISTRY["eluta_multi_ip"] = ElutaMultiIPScraper

if PARALLEL_AVAILABLE:
    SCRAPER_REGISTRY["parallel"] = ParallelJobScraper

if PIPELINE_AVAILABLE:
    SCRAPER_REGISTRY["pipeline"] = ModernJobPipeline

if INDEED_AVAILABLE:
    SCRAPER_REGISTRY["indeed"] = IndeedEnhancedScraper

if LINKEDIN_AVAILABLE:
    SCRAPER_REGISTRY["linkedin"] = LinkedInEnhancedScraper

if MONSTER_AVAILABLE:
    SCRAPER_REGISTRY["monster"] = MonsterEnhancedScraper

if JOBANK_AVAILABLE:
    SCRAPER_REGISTRY["jobbank"] = JobBankEnhancedScraper

# Default scraper for fallback
DEFAULT_SCRAPER = ComprehensiveElutaScraper if ELUTA_COMPREHENSIVE_AVAILABLE else (ElutaOptimizedParallelScraper if ELUTA_OPTIMIZED_AVAILABLE else None)

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
    console = Console()

    # Method 1: Try requested scraper
    try:
        console.print(f"[cyan]🔄 Attempting {site_name} scraper...[/cyan]")
        return get_scraper(site_name, profile, **kwargs)
    except Exception as e:
        console.print(f"[yellow]❌ {site_name} scraper failed: {e}[/yellow]")

    # Method 2: Try enhanced scrapers in priority order
    enhanced_priority = ["eluta", "eluta_optimized", "eluta_multi_ip", "parallel"]
    for enhanced_site in enhanced_priority:
        if enhanced_site != site_name and enhanced_site in SCRAPER_REGISTRY:
            try:
                console.print(f"[cyan]🔄 Trying enhanced {enhanced_site} scraper...[/cyan]")
                return get_scraper(enhanced_site, profile, **kwargs)
            except Exception as e:
                console.print(f"[yellow]❌ Enhanced {enhanced_site} scraper failed: {e}[/yellow]")

    # Method 3: Try basic scraper (if available)
    if ROOT_SCRAPERS_AVAILABLE:
        try:
            console.print("[cyan]🔄 Trying basic scraper...[/cyan]")
            fallback_scraper = GenericATSSubmitter(profile)
            if hasattr(fallback_scraper, "scrape_jobs"):
                return fallback_scraper
            else:
                console.print(f"[yellow]⚠️ Fallback scraper does not support scrape_jobs. Returning fallback instance only.[/yellow]")
                return fallback_scraper
        except Exception as e:
            console.print(f"[yellow]❌ Basic scraper failed: {e}[/yellow]")

    # Method 4: Emergency email submitter
    if ROOT_SCRAPERS_AVAILABLE:
        try:
            console.print("[red]🔄 Using emergency email submitter...[/red]")
            emergency_submitter = EmergencyEmailSubmitter(profile)
            if hasattr(emergency_submitter, "scrape_jobs"):
                return emergency_submitter
            else:
                console.print(f"[yellow]⚠️ Emergency submitter does not support scrape_jobs. Returning fallback instance only.[/yellow]")
                return emergency_submitter
        except Exception as e:
            console.print(f"[red]❌ Emergency email submitter failed: {e}[/red]")
            raise RuntimeError("All scraper fallback methods failed")
    else:
        raise RuntimeError("No scrapers available")

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
    console = Console()

    console.print(f"[bold]🚀 Starting job scraping with fallbacks for keywords: {', '.join(keywords)}[/bold]")

    # Get scraper with fallbacks
    scraper = get_scraper_with_fallbacks(site_name, profile, **kwargs)

    # Try to scrape jobs
    try:
        if hasattr(scraper, "scrape_jobs"):
            jobs = scraper.scrape_jobs(keywords)
            console.print(f"[bold green]✅ Successfully scraped {len(jobs)} jobs![/bold green]")
            return jobs
        else:
            console.print(f"[yellow]⚠️ Fallback scraper does not support scrape_jobs. Returning empty list.[/yellow]")
            return []
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

def create_multi_site_scraper(profile: dict, sites: Optional[List[str]] = None, **kwargs):
    """
    Create a multi-site scraper that can scrape from multiple job sites.
    
    Args:
        profile: User profile dictionary
        sites: List of site names to scrape from
        **kwargs: Additional arguments
        
    Returns:
        Multi-site scraper instance
    """
    if sites is None:
        sites = ["eluta", "indeed", "linkedin"]
    
    scrapers = {}
    for site in sites:
        if site in SCRAPER_REGISTRY:
            try:
                scrapers[site] = get_scraper(site, profile, **kwargs)
            except Exception as e:
                console = Console()
                console.print(f"[yellow]⚠️ Failed to create scraper for {site}: {e}[/yellow]")
    
    return MultiSiteScraper(scrapers, profile)

class MultiSiteScraper:
    """Multi-site scraper that can scrape from multiple job sites."""
    
    def __init__(self, scrapers: Dict[str, Any], profile: dict):
        self.scrapers = scrapers
        self.profile = profile
        self.console = Console()
    
    def scrape_jobs(self, keywords: list) -> List[Dict]:
        """Scrape jobs from all available sites."""
        all_jobs = []
        
        for site_name, scraper in self.scrapers.items():
            try:
                self.console.print(f"[cyan]🔄 Scraping from {site_name}...[/cyan]")
                jobs = scraper.scrape_jobs(keywords)
                all_jobs.extend(jobs)
                self.console.print(f"[green]✅ Scraped {len(jobs)} jobs from {site_name}[/green]")
            except Exception as e:
                self.console.print(f"[red]❌ Failed to scrape from {site_name}: {e}[/red]")
        
        return all_jobs

def get_scraper_registry():
    """
    Get the scraper registry for advanced usage.
    
    Returns:
        Dictionary mapping site names to scraper classes
    """
    return SCRAPER_REGISTRY.copy()

__all__ = [
    'get_scraper', 'get_scraper_with_fallbacks', 'scrape_with_fallbacks',
    'get_available_sites', 'create_multi_site_scraper', 'get_scraper_registry',
    'SCRAPER_REGISTRY', 'DEFAULT_SCRAPER', 'AVAILABLE_SCRAPERS', 'MultiSiteScraper'
]
