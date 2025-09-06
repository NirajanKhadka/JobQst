"""
Glassdoor Error Handler for JobSpy Integration
Handles common Glassdoor API errors and provides fallback mechanisms.

Common issues:
- 400 status code from Glassdoor API
- Location parsing failures
- Rate limiting
- Network connectivity issues
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from rich.console import Console

try:
    from jobspy import scrape_jobs
    JOBSPY_AVAILABLE = True
except ImportError:
    JOBSPY_AVAILABLE = False

console = Console()
logger = logging.getLogger(__name__)

@dataclass
class GlassdoorErrorConfig:
    """Configuration for Glassdoor error handling."""
    enable_fallback: bool = True
    max_retries: int = 2
    retry_delay: float = 2.0
    fallback_sites: List[str] = None
    skip_glassdoor_on_error: bool = True
    use_alternative_locations: bool = True

class GlassdoorErrorHandler:
    """Handles Glassdoor-specific errors in JobSpy integration."""
    
    def __init__(self, config: Optional[GlassdoorErrorConfig] = None):
        self.config = config or GlassdoorErrorConfig()
        self.error_count = 0
        self.location_errors = {}
        self.fallback_active = False
        
        # Default fallback sites (exclude Glassdoor)
        if not self.config.fallback_sites:
            self.config.fallback_sites = ["indeed", "linkedin", "zip_recruiter"]
    
    async def safe_scrape_with_glassdoor_handling(
        self, 
        site_name: List[str], 
        search_term: str, 
        location: str, 
        **kwargs
    ) -> Optional[Any]:
        """
        Safely scrape jobs with Glassdoor error handling.
        
        Args:
            site_name: List of sites to scrape
            search_term: Job search term
            location: Location to search
            **kwargs: Additional JobSpy parameters
        
        Returns:
            DataFrame with jobs or None if all attempts fail
        """
        
        # Track if Glassdoor is in the sites list
        has_glassdoor = "glassdoor" in site_name
        
        if not has_glassdoor:
            # No Glassdoor, proceed normally
            return await self._safe_scrape(site_name, search_term, location, **kwargs)
        
        # First attempt with all sites including Glassdoor
        try:
            console.print(f"[cyan]🔍 Attempting search with Glassdoor included...[/cyan]")
            result = await self._safe_scrape(site_name, search_term, location, **kwargs)
            
            if result is not None and len(result) > 0:
                console.print(f"[green]✅ Glassdoor search successful![/green]")
                return result
                
        except Exception as e:
            if self._is_glassdoor_error(str(e)):
                console.print(f"[yellow]⚠️ Glassdoor error detected: {str(e)[:100]}...[/yellow]")
                self.error_count += 1
                self._record_location_error(location, str(e))
                
                if self.config.enable_fallback:
                    return await self._handle_glassdoor_fallback(
                        site_name, search_term, location, **kwargs
                    )
            else:
                console.print(f"[red]❌ Non-Glassdoor error: {e}[/red]")
                raise e
        
        return None
    
    async def _handle_glassdoor_fallback(
        self, 
        site_name: List[str], 
        search_term: str, 
        location: str, 
        **kwargs
    ) -> Optional[Any]:
        """Handle Glassdoor fallback strategies."""
        
        fallback_strategies = [
            self._fallback_exclude_glassdoor,
            self._fallback_alternative_location,
            self._fallback_simplified_search
        ]
        
        for strategy in fallback_strategies:
            try:
                console.print(f"[cyan]🔄 Trying fallback strategy: {strategy.__name__}[/cyan]")
                result = await strategy(site_name, search_term, location, **kwargs)
                
                if result is not None and len(result) > 0:
                    console.print(f"[green]✅ Fallback successful with {strategy.__name__}![/green]")
                    self.fallback_active = True
                    return result
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Fallback {strategy.__name__} failed: {e}[/yellow]")
                continue
        
        console.print(f"[red]❌ All Glassdoor fallback strategies failed for: {search_term} in {location}[/red]")
        return None
    
    async def _fallback_exclude_glassdoor(
        self, 
        site_name: List[str], 
        search_term: str, 
        location: str, 
        **kwargs
    ) -> Optional[Any]:
        """Fallback 1: Exclude Glassdoor and use other sites."""
        
        sites_without_glassdoor = [site for site in site_name if site != "glassdoor"]
        
        if not sites_without_glassdoor:
            sites_without_glassdoor = self.config.fallback_sites
        
        console.print(f"[cyan]🔄 Retrying without Glassdoor: {sites_without_glassdoor}[/cyan]")
        
        return await self._safe_scrape(
            sites_without_glassdoor, search_term, location, **kwargs
        )
    
    async def _fallback_alternative_location(
        self, 
        site_name: List[str], 
        search_term: str, 
        location: str, 
        **kwargs
    ) -> Optional[Any]:
        """Fallback 2: Try alternative location formats."""
        
        alternative_locations = self._get_alternative_locations(location)
        sites_without_glassdoor = [site for site in site_name if site != "glassdoor"]
        
        for alt_location in alternative_locations:
            try:
                console.print(f"[cyan]🔄 Trying alternative location: {alt_location}[/cyan]")
                result = await self._safe_scrape(
                    sites_without_glassdoor, search_term, alt_location, **kwargs
                )
                
                if result is not None and len(result) > 0:
                    return result
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Alternative location {alt_location} failed: {e}[/yellow]")
                continue
        
        return None
    
    async def _fallback_simplified_search(
        self, 
        site_name: List[str], 
        search_term: str, 
        location: str, 
        **kwargs
    ) -> Optional[Any]:
        """Fallback 3: Simplified search with reduced parameters."""
        
        sites_without_glassdoor = [site for site in site_name if site != "glassdoor"]
        
        # Simplified kwargs (remove potentially problematic parameters)
        simplified_kwargs = {
            "results_wanted": kwargs.get("results_wanted", 50),
            "hours_old": kwargs.get("hours_old", 168),
            "country_indeed": kwargs.get("country_indeed", "Canada"),
            "verbose": False  # Disable verbose to reduce errors
        }
        
        console.print(f"[cyan]🔄 Simplified search: {sites_without_glassdoor}[/cyan]")
        
        return await self._safe_scrape(
            sites_without_glassdoor, search_term, location, **simplified_kwargs
        )
    
    async def _safe_scrape(
        self, 
        site_name: List[str], 
        search_term: str, 
        location: str, 
        **kwargs
    ) -> Optional[Any]:
        """Safely execute JobSpy scrape with retry logic."""
        
        if not JOBSPY_AVAILABLE:
            raise ImportError("JobSpy not available. Install with: pip install python-jobspy")
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    console.print(f"[yellow]🔄 Retry attempt {attempt}/{self.config.max_retries}[/yellow]")
                    await asyncio.sleep(self.config.retry_delay)
                
                # Execute the scrape
                result = scrape_jobs(
                    site_name=site_name,
                    search_term=search_term,
                    location=location,
                    **kwargs
                )
                
                return result
                
            except Exception as e:
                if attempt == self.config.max_retries:
                    raise e
                else:
                    console.print(f"[yellow]⚠️ Attempt {attempt + 1} failed: {str(e)[:100]}...[/yellow]")
                    continue
    
    def _is_glassdoor_error(self, error_message: str) -> bool:
        """Check if error is Glassdoor-related."""
        glassdoor_error_indicators = [
            "glassdoor response status code 400",
            "glassdoor: location not parsed",
            "glassdoor api error",
            "glassdoor rate limit",
            "glassdoor connection error",
            "glassdoor timeout"
        ]
        
        error_lower = error_message.lower()
        return any(indicator in error_lower for indicator in glassdoor_error_indicators)
    
    def _record_location_error(self, location: str, error: str):
        """Record location-specific errors for analysis."""
        if location not in self.location_errors:
            self.location_errors[location] = []
        
        self.location_errors[location].append({
            "error": error,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    def _get_alternative_locations(self, location: str) -> List[str]:
        """Get alternative location formats for problematic locations."""
        
        alternatives = []
        
        # If location has specific area, try broader location
        if "," in location:
            parts = location.split(",")
            if len(parts) >= 2:
                # Try just city and province/state
                broader_location = f"{parts[0].strip()}, {parts[-1].strip()}"
                if broader_location != location:
                    alternatives.append(broader_location)
                
                # Try just the city
                city_only = parts[0].strip()
                alternatives.append(city_only)
        
        # Add remote alternatives
        if "Canada" in location or "CA" in location:
            alternatives.extend([
                "Remote, Canada",
                "Toronto, ON",  # Major Canadian city fallback
                "Vancouver, BC"
            ])
        elif "USA" in location or "US" in location:
            alternatives.extend([
                "Remote, USA",
                "New York, NY",  # Major US city fallback
                "San Francisco, CA"
            ])
        
        # Filter out the original location
        alternatives = [alt for alt in alternatives if alt != location]
        
        return alternatives[:3]  # Limit to 3 alternatives
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for analysis."""
        return {
            "total_errors": self.error_count,
            "fallback_active": self.fallback_active,
            "location_errors": dict(self.location_errors),
            "problematic_locations": list(self.location_errors.keys())
        }
    
    def reset_stats(self):
        """Reset error statistics."""
        self.error_count = 0
        self.location_errors = {}
        self.fallback_active = False

# Convenience function for easy integration
async def safe_jobspy_scrape(
    site_name: List[str],
    search_term: str,
    location: str,
    enable_glassdoor_fallback: bool = True,
    **kwargs
) -> Optional[Any]:
    """
    Convenience function for safe JobSpy scraping with Glassdoor error handling.
    
    Args:
        site_name: List of sites to scrape
        search_term: Job search term
        location: Location to search
        enable_glassdoor_fallback: Whether to enable Glassdoor fallback mechanisms
        **kwargs: Additional JobSpy parameters
    
    Returns:
        DataFrame with jobs or None if all attempts fail
    """
    
    if not JOBSPY_AVAILABLE:
        raise ImportError("JobSpy not available. Install with: pip install python-jobspy")
    
    if not enable_glassdoor_fallback:
        # Direct scrape without error handling
        return scrape_jobs(
            site_name=site_name,
            search_term=search_term,
            location=location,
            **kwargs
        )
    
    # Use error handler
    handler = GlassdoorErrorHandler()
    return await handler.safe_scrape_with_glassdoor_handling(
        site_name, search_term, location, **kwargs
    )