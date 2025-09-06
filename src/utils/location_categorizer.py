"""
Location Categorization and RCIP City Tagging Utility
Provides functionality to analyze and categorize job locations with special focus on RCIP cities.
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class LocationInfo:
    """Information about a job location."""
    original: str
    city: str
    province: str
    province_code: str
    location_type: str  # remote, hybrid, onsite
    location_category: str  # major_city, rcip_city, immigration_priority, custom
    city_tags: List[str]  # ["rcip", "tech_hub", "immigration_priority"]
    is_rcip_city: bool
    is_immigration_priority: bool

class LocationCategorizer:
    """Categorizes and tags job locations with RCIP and immigration priority information."""
    
    def __init__(self):
        # RCIP (Regional and Community Immigration Program) Cities
        self.rcip_cities = {
            # Atlantic Canada
            "charlottetown", "summerside",  # PE
            "fredericton", "moncton", "saint john",  # NB
            "halifax", "sydney", "yarmouth", "truro",  # NS
            "st. john's", "corner brook",  # NL
            
            # Quebec (outside Montreal)
            "quebec city", "trois-rivières", "sherbrooke", 
            "saguenay", "gatineau", "rimouski",
            
            # Ontario (outside GTA)
            "ottawa", "london", "windsor", "kingston",
            "sudbury", "thunder bay", "sault ste. marie",
            "north bay", "peterborough", "barrie",
            
            # Manitoba
            "winnipeg", "brandon", "steinbach",
            
            # Saskatchewan  
            "saskatoon", "regina", "prince albert",
            "moose jaw", "swift current",
            
            # Alberta (outside Calgary/Edmonton)
            "red deer", "lethbridge", "medicine hat",
            "grande prairie", "fort mcmurray",
            
            # British Columbia (outside Vancouver)
            "victoria", "kelowna", "kamloops", "prince george",
            "nanaimo", "chilliwack", "vernon"
        }
        
        self.immigration_priority_cities = {
            "charlottetown", "fredericton", "halifax", 
            "quebec city", "sherbrooke", "ottawa",
            "london", "winnipeg", "saskatoon", "regina",
            "victoria", "kelowna", "kamloops"
        }
        
        self.major_cities = {
            "toronto", "vancouver", "calgary", "edmonton",
            "montreal", "ottawa", "winnipeg", "quebec city",
            "hamilton", "waterloo", "kitchener"
        }
        
        self.tech_hubs = {
            "toronto", "vancouver", "waterloo", "kitchener",
            "calgary", "ottawa", "montreal", "edmonton",
            "halifax", "victoria"
        }
        
        self.province_codes = {
            "ontario": "ON", "british columbia": "BC", "alberta": "AB",
            "quebec": "QC", "manitoba": "MB", "saskatchewan": "SK",
            "nova scotia": "NS", "new brunswick": "NB", 
            "prince edward island": "PE", "newfoundland and labrador": "NL",
            "northwest territories": "NT", "nunavut": "NU", "yukon": "YT"
        }
        
        self.province_abbrev_map = {
            "on": "ON", "bc": "BC", "ab": "AB", "qc": "QC",
            "mb": "MB", "sk": "SK", "ns": "NS", "nb": "NB",
            "pe": "PE", "nl": "NL", "nt": "NT", "nu": "NU", "yt": "YT"
        }

    def analyze_location(self, location: str) -> LocationInfo:
        """Analyze a job location string and return detailed categorization."""
        if not location or not isinstance(location, str):
            return self._create_unknown_location(location or "Unknown")
            
        location_clean = self._clean_location(location)
        
        # Check for remote work
        if self._is_remote(location_clean):
            return self._create_remote_location(location)
            
        # Extract city and province
        city, province, province_code = self._extract_city_province(location_clean)
        
        if not city:
            return self._create_unknown_location(location)
            
        # Categorize the location
        location_type = self._determine_location_type(location_clean)
        location_category = self._categorize_location(city)
        city_tags = self._generate_city_tags(city, province_code)
        is_rcip = city.lower() in self.rcip_cities
        is_immigration_priority = city.lower() in self.immigration_priority_cities
        
        return LocationInfo(
            original=location,
            city=city,
            province=province,
            province_code=province_code,
            location_type=location_type,
            location_category=location_category,
            city_tags=city_tags,
            is_rcip_city=is_rcip,
            is_immigration_priority=is_immigration_priority
        )

    def _clean_location(self, location: str) -> str:
        """Clean and normalize location string."""
        # Remove extra whitespace and convert to lowercase for analysis
        return re.sub(r'\s+', ' ', location.strip())

    def _is_remote(self, location: str) -> bool:
        """Check if location indicates remote work."""
        remote_indicators = [
            "remote", "work from home", "telecommute", "virtual",
            "anywhere", "home office", "distributed"
        ]
        location_lower = location.lower()
        return any(indicator in location_lower for indicator in remote_indicators)

    def _extract_city_province(self, location: str) -> Tuple[str, str, str]:
        """Extract city name and province from location string."""
        # Common patterns: "City, Province" or "City, AB" 
        
        # First, try to find province code pattern
        province_pattern = r',\s*([A-Z]{2})(?:\s|$)'
        province_match = re.search(province_pattern, location)
        
        if province_match:
            province_code = province_match.group(1).upper()
            city_part = location[:province_match.start()].strip()
            
            # Map province code to full name
            province_name = self._get_province_name(province_code)
            
            return city_part, province_name, province_code
            
        # Try full province name pattern
        for full_name, code in self.province_codes.items():
            if full_name.lower() in location.lower():
                # Extract city (everything before province name)
                city_part = location.lower().replace(full_name.lower(), "").strip(" ,")
                return city_part.title(), full_name.title(), code
                
        # If no province found, treat entire string as city
        return location.strip(" ,"), "Unknown", ""

    def _get_province_name(self, province_code: str) -> str:
        """Get full province name from code."""
        code_to_name = {v: k for k, v in self.province_codes.items()}
        return code_to_name.get(province_code.upper(), "Unknown").title()

    def _determine_location_type(self, location: str) -> str:
        """Determine if location is remote, hybrid, or onsite."""
        location_lower = location.lower()
        
        if "remote" in location_lower or "work from home" in location_lower:
            return "remote"
        elif "hybrid" in location_lower:
            return "hybrid"
        else:
            return "onsite"

    def _categorize_location(self, city: str) -> str:
        """Categorize the city based on its characteristics."""
        city_lower = city.lower()
        
        if city_lower in self.major_cities:
            return "major_city"
        elif city_lower in self.rcip_cities:
            return "rcip_city"
        elif city_lower in self.immigration_priority_cities:
            return "immigration_priority"
        else:
            return "custom"

    def _generate_city_tags(self, city: str, province_code: str) -> List[str]:
        """Generate tags for the city based on its characteristics."""
        tags = []
        city_lower = city.lower()
        
        if city_lower in self.rcip_cities:
            tags.append("rcip")
            
        if city_lower in self.immigration_priority_cities:
            tags.append("immigration_priority")
            
        if city_lower in self.major_cities:
            tags.append("major_city")
            
        if city_lower in self.tech_hubs:
            tags.append("tech_hub")
            
        # Add province-specific tags
        if province_code in ["ON", "BC", "AB"]:
            tags.append("high_demand_province")
            
        if province_code in ["NS", "NB", "PE", "NL"]:
            tags.append("atlantic_canada")
            
        if province_code in ["MB", "SK"]:
            tags.append("prairie_province")
            
        return tags

    def _create_remote_location(self, original: str) -> LocationInfo:
        """Create LocationInfo for remote work."""
        return LocationInfo(
            original=original,
            city="Remote",
            province="Multiple",
            province_code="",
            location_type="remote",
            location_category="remote",
            city_tags=["remote", "flexible"],
            is_rcip_city=False,
            is_immigration_priority=False
        )

    def _create_unknown_location(self, original: str) -> LocationInfo:
        """Create LocationInfo for unknown/unparseable locations."""
        return LocationInfo(
            original=original,
            city="Unknown",
            province="Unknown",
            province_code="",
            location_type="unknown",
            location_category="unknown",
            city_tags=["unknown"],
            is_rcip_city=False,
            is_immigration_priority=False
        )

    def get_rcip_cities_summary(self) -> Dict[str, List[str]]:
        """Get a summary of RCIP cities by province."""
        rcip_by_province = {}
        
        # This is a simplified mapping - in practice, you'd want a more comprehensive database
        rcip_mapping = {
            "PE": ["Charlottetown", "Summerside"],
            "NB": ["Fredericton", "Moncton", "Saint John"],
            "NS": ["Halifax", "Sydney", "Yarmouth", "Truro"],
            "NL": ["St. John's", "Corner Brook"],
            "QC": ["Quebec City", "Trois-Rivières", "Sherbrooke", "Saguenay", "Gatineau", "Rimouski"],
            "ON": ["Ottawa", "London", "Windsor", "Kingston", "Sudbury", "Thunder Bay"],
            "MB": ["Winnipeg", "Brandon", "Steinbach"],
            "SK": ["Saskatoon", "Regina", "Prince Albert", "Moose Jaw"],
            "AB": ["Red Deer", "Lethbridge", "Medicine Hat", "Grande Prairie"],
            "BC": ["Victoria", "Kelowna", "Kamloops", "Prince George", "Nanaimo"]
        }
        
        return rcip_mapping

# Convenience function for easy usage
def categorize_job_location(location: str) -> LocationInfo:
    """Analyze and categorize a job location string."""
    categorizer = LocationCategorizer()
    return categorizer.analyze_location(location)
