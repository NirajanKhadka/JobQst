#!/usr/bin/env python3
"""
Canada-Wide Scraper Configuration
Configures all scrapers to search throughout Canada instead of specific cities.
"""

from typing import Dict, List
from rich.console import Console

console = Console()

class CanadaWideScraperConfig:
    """
    Configuration for Canada-wide job searching across all provinces and territories.
    """
    
    def __init__(self):
        """Initialize Canada-wide scraper configuration."""
        
        # Major Canadian cities and provinces for comprehensive coverage
        self.canadian_locations = {
            'major_cities': [
                'Toronto, ON', 'Vancouver, BC', 'Montreal, QC', 'Calgary, AB',
                'Edmonton, AB', 'Ottawa, ON', 'Winnipeg, MB', 'Quebec City, QC',
                'Hamilton, ON', 'Kitchener, ON', 'London, ON', 'Victoria, BC',
                'Halifax, NS', 'Oshawa, ON', 'Windsor, ON', 'Saskatoon, SK',
                'Regina, SK', 'St. Johns, NL', 'Barrie, ON', 'Kelowna, BC'
            ],
            'provinces': [
                'Ontario', 'British Columbia', 'Quebec', 'Alberta', 'Manitoba',
                'Saskatchewan', 'Nova Scotia', 'New Brunswick', 'Newfoundland and Labrador',
                'Prince Edward Island', 'Northwest Territories', 'Yukon', 'Nunavut'
            ],
            'province_codes': [
                'ON', 'BC', 'QC', 'AB', 'MB', 'SK', 'NS', 'NB', 'NL', 'PE', 'NT', 'YT', 'NU'
            ]
        }
        
        # Site-specific location configurations
        self.site_configs = {
            'eluta': {
                'canada_wide_search': True,
                'location_parameter': 'l',
                'canada_values': ['Canada', '', 'All Canada', 'Nationwide'],
                'fallback_cities': self.canadian_locations['major_cities'][:5]
            },
            'indeed': {
                'canada_wide_search': True,
                'location_parameter': 'l',
                'canada_values': ['Canada', 'All Canada', 'Nationwide'],
                'fallback_cities': self.canadian_locations['major_cities'][:10]
            },
            'jobbank': {
                'canada_wide_search': True,
                'location_parameter': 'searchstring',
                'canada_values': ['Canada', 'All provinces'],
                'fallback_cities': self.canadian_locations['major_cities'][:8]
            },
            'linkedin': {
                'canada_wide_search': True,
                'location_parameter': 'location',
                'canada_values': ['Canada', 'All Canada'],
                'fallback_cities': self.canadian_locations['major_cities'][:6]
            },
            'monster': {
                'canada_wide_search': True,
                'location_parameter': 'where',
                'canada_values': ['Canada', 'All Canada'],
                'fallback_cities': self.canadian_locations['major_cities'][:5]
            }
        }
    
    def get_search_locations_for_site(self, site_name: str, max_locations: int = 5) -> List[str]:
        """
        Get search locations for a specific site.
        
        Args:
            site_name: Name of the job site
            max_locations: Maximum number of locations to return
            
        Returns:
            List of location strings optimized for the site
        """
        site_name = site_name.lower()
        
        if site_name not in self.site_configs:
            # Default to major cities for unknown sites
            return self.canadian_locations['major_cities'][:max_locations]
        
        config = self.site_configs[site_name]
        
        # Try Canada-wide search first
        if config['canada_wide_search']:
            return config['canada_values'][:1]  # Use primary Canada-wide value
        
        # Fallback to major cities
        return config['fallback_cities'][:max_locations]
    
    def get_location_parameter_name(self, site_name: str) -> str:
        """
        Get the location parameter name for a specific site.
        
        Args:
            site_name: Name of the job site
            
        Returns:
            Parameter name for location in URLs
        """
        site_name = site_name.lower()
        return self.site_configs.get(site_name, {}).get('location_parameter', 'location')
    
    def optimize_location_for_site(self, location: str, site_name: str) -> str:
        """
        Optimize location string for a specific site.
        
        Args:
            location: Original location string
            site_name: Name of the job site
            
        Returns:
            Optimized location string for the site
        """
        site_name = site_name.lower()
        location_lower = location.lower()
        
        # If location is "Canada" or similar, use site-specific Canada value
        if any(canada_term in location_lower for canada_term in ['canada', 'nationwide', 'all']):
            if site_name in self.site_configs:
                return self.site_configs[site_name]['canada_values'][0]
            return 'Canada'
        
        # If location is a province code, expand it
        if location.upper() in self.canadian_locations['province_codes']:
            province_index = self.canadian_locations['province_codes'].index(location.upper())
            return self.canadian_locations['provinces'][province_index]
        
        # Return original location if it's already specific
        return location
    
    def get_multi_location_search_strategy(self, site_name: str) -> Dict:
        """
        Get multi-location search strategy for comprehensive Canada coverage.
        
        Args:
            site_name: Name of the job site
            
        Returns:
            Dictionary with search strategy details
        """
        site_name = site_name.lower()
        
        if site_name not in self.site_configs:
            return {
                'strategy': 'major_cities',
                'locations': self.canadian_locations['major_cities'][:5],
                'parallel_search': True,
                'max_concurrent': 3
            }
        
        config = self.site_configs[site_name]
        
        if config['canada_wide_search']:
            return {
                'strategy': 'canada_wide',
                'locations': config['canada_values'][:1],
                'parallel_search': False,
                'max_concurrent': 1
            }
        else:
            return {
                'strategy': 'multi_city',
                'locations': config['fallback_cities'],
                'parallel_search': True,
                'max_concurrent': 3
            }
    
    def display_canada_coverage_info(self) -> None:
        """Display information about Canada-wide coverage."""
        console.print("\n[bold]🇨🇦 CANADA-WIDE JOB SEARCH CONFIGURATION[/bold]")
        
        console.print(f"\n[cyan]📍 Coverage Areas:[/cyan]")
        console.print(f"• Major Cities: {len(self.canadian_locations['major_cities'])} cities")
        console.print(f"• Provinces/Territories: {len(self.canadian_locations['provinces'])} regions")
        
        console.print(f"\n[cyan]🌐 Site Configurations:[/cyan]")
        for site, config in self.site_configs.items():
            status = "✅ Canada-wide" if config['canada_wide_search'] else "🏙️ Multi-city"
            console.print(f"• {site.title()}: {status}")
        
        console.print(f"\n[green]💡 Benefits of Canada-wide search:[/green]")
        console.print("• Access to jobs across all provinces and territories")
        console.print("• Remote work opportunities from any location")
        console.print("• Better job market coverage and opportunities")
        console.print("• Reduced location bias in job matching")


# Convenience functions
def get_canada_wide_config() -> CanadaWideScraperConfig:
    """Get Canada-wide scraper configuration."""
    return CanadaWideScraperConfig()


def update_profile_for_canada_search(profile: Dict) -> Dict:
    """
    Update profile configuration for Canada-wide search.
    
    Args:
        profile: User profile dictionary
        
    Returns:
        Updated profile with Canada-wide search settings
    """
    updated_profile = profile.copy()
    
    # Update location to Canada if it's a specific city
    current_location = profile.get('location', '')
    if any(city in current_location for city in ['Toronto', 'Vancouver', 'Montreal', 'Calgary']):
        updated_profile['location'] = 'Canada'
        console.print(f"[cyan]📍 Updated location from '{current_location}' to 'Canada' for nationwide search[/cyan]")
    
    # Add Canada-wide search preferences
    if 'search_preferences' not in updated_profile:
        updated_profile['search_preferences'] = {}
    
    updated_profile['search_preferences'].update({
        'canada_wide_search': True,
        'include_remote_jobs': True,
        'max_locations_per_site': 1,  # Use Canada-wide search instead of multiple cities
        'prefer_nationwide_results': True
    })
    
    return updated_profile


def get_optimized_search_locations(site_name: str, original_location: str = "Canada") -> List[str]:
    """
    Get optimized search locations for a site.
    
    Args:
        site_name: Name of the job site
        original_location: Original location from profile
        
    Returns:
        List of optimized location strings
    """
    config = get_canada_wide_config()
    
    # If original location is Canada or similar, use site-optimized Canada search
    if any(term in original_location.lower() for term in ['canada', 'nationwide', 'all']):
        return config.get_search_locations_for_site(site_name, max_locations=1)
    
    # Otherwise, use the original location but optimize it
    optimized = config.optimize_location_for_site(original_location, site_name)
    return [optimized]


if __name__ == "__main__":
    # Test the configuration
    config = CanadaWideScraperConfig()
    config.display_canada_coverage_info()
    
    # Test site-specific configurations
    console.print("\n[bold]🧪 Testing Site Configurations:[/bold]")
    
    test_sites = ['eluta', 'indeed', 'jobbank', 'linkedin', 'monster']
    for site in test_sites:
        locations = config.get_search_locations_for_site(site)
        strategy = config.get_multi_location_search_strategy(site)
        console.print(f"\n[cyan]{site.title()}:[/cyan]")
        console.print(f"  Locations: {locations}")
        console.print(f"  Strategy: {strategy['strategy']}")
        console.print(f"  Parallel: {strategy['parallel_search']}")
