"""
Customizable Scraper Configuration

Provides user-friendly configuration options for job scraping
with support for keywords, locations, job boards, and filters.
"""
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ScrapeConfig:
    """Configuration for customizable job scraping."""
    
    # Basic search parameters
    keywords: List[str] = field(default_factory=list)
    job_titles: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    
    # Job board selection
    sites: List[str] = field(default_factory=lambda: [
        "indeed", "linkedin", "glassdoor", "zip_recruiter"
    ])
    
    # Filters
    experience_levels: List[str] = field(default_factory=list)
    job_types: List[str] = field(default_factory=list)  # full-time, part-time, etc.
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    remote_ok: bool = True
    
    # Advanced options
    max_results_per_site: int = 50
    date_posted: str = "month"  # today, week, month, all
    company_exclude: List[str] = field(default_factory=list)
    
    # Country/region settings
    country: str = "canada"  # canada, usa, uk, etc.
    
    # User preferences
    user_id: str = "default"
    config_name: str = "default"
    save_preferences: bool = True


class CustomizableScraperManager:
    """
    Manager for customizable scraper configurations.
    Provides easy-to-use interface for setting up job searches.
    """
    
    def __init__(self, config_dir: str = "config/scraper"):
        """Initialize scraper manager."""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration templates
        self.templates = self._load_default_templates()
        
        logger.info(f"Scraper manager initialized with config dir: "
                   f"{self.config_dir}")
    
    def _load_default_templates(self) -> Dict[str, ScrapeConfig]:
        """Load default configuration templates."""
        templates = {
            "tech_comprehensive": ScrapeConfig(
                keywords=["python", "javascript", "react", "aws", "docker"],
                job_titles=["software engineer", "developer", "data scientist"],
                locations=["toronto", "vancouver", "montreal", "remote"],
                experience_levels=["entry", "mid", "senior"],
                job_types=["full-time"],
                max_results_per_site=100,
                config_name="tech_comprehensive"
            ),
            
            "data_science": ScrapeConfig(
                keywords=["python", "sql", "machine learning", "pandas", 
                         "tensorflow", "data analysis"],
                job_titles=["data scientist", "data analyst", "ml engineer"],
                locations=["toronto", "vancouver", "remote"],
                experience_levels=["mid", "senior"],
                job_types=["full-time"],
                salary_min=70000,
                max_results_per_site=75,
                config_name="data_science"
            ),
            
            "business_analyst": ScrapeConfig(
                keywords=["excel", "powerbi", "sql", "tableau", 
                         "business intelligence"],
                job_titles=["business analyst", "data analyst", 
                           "business intelligence analyst"],
                locations=["toronto", "calgary", "ottawa", "remote"],
                experience_levels=["entry", "mid"],
                job_types=["full-time", "contract"],
                salary_min=50000,
                max_results_per_site=60,
                config_name="business_analyst"
            ),
            
            "sales_marketing": ScrapeConfig(
                keywords=["sales", "marketing", "crm", "lead generation"],
                job_titles=["sales representative", "marketing specialist", 
                           "account manager"],
                locations=["toronto", "vancouver", "calgary"],
                experience_levels=["entry", "mid"],
                job_types=["full-time"],
                max_results_per_site=80,
                config_name="sales_marketing"
            ),
            
            "remote_only": ScrapeConfig(
                keywords=["remote", "work from home", "distributed"],
                job_titles=["software engineer", "developer", "designer"],
                locations=["remote", "remote - canada", "work from home"],
                remote_ok=True,
                max_results_per_site=100,
                config_name="remote_only"
            )
        }
        
        return templates
    
    def get_template(self, template_name: str) -> Optional[ScrapeConfig]:
        """Get a configuration template."""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """List available configuration templates."""
        return list(self.templates.keys())
    
    def create_custom_config(self, 
                           keywords: List[str] = None,
                           job_titles: List[str] = None,
                           locations: List[str] = None,
                           sites: List[str] = None,
                           **kwargs) -> ScrapeConfig:
        """
        Create a custom scraper configuration.
        
        Args:
            keywords: List of keywords to search for
            job_titles: Specific job titles to target
            locations: Locations to search in
            sites: Job boards to search on
            **kwargs: Additional configuration options
            
        Returns:
            ScrapeConfig object
        """
        config = ScrapeConfig(
            keywords=keywords or [],
            job_titles=job_titles or [],
            locations=locations or [],
            sites=sites or ["indeed", "linkedin", "glassdoor"],
            **kwargs
        )
        
        return config
    
    def save_config(self, config: ScrapeConfig, 
                   filename: str = None) -> str:
        """Save configuration to file."""
        if not filename:
            filename = f"{config.user_id}_{config.config_name}.json"
        
        filepath = self.config_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2)
            
            logger.info(f"Saved scraper config to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save config to {filepath}: {e}")
            raise
    
    def load_config(self, filename: str) -> Optional[ScrapeConfig]:
        """Load configuration from file."""
        filepath = self.config_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Config file not found: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            config = ScrapeConfig(**data)
            logger.info(f"Loaded scraper config from {filepath}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config from {filepath}: {e}")
            return None
    
    def list_saved_configs(self, user_id: str = None) -> List[str]:
        """List saved configuration files."""
        pattern = f"{user_id}_*.json" if user_id else "*.json"
        config_files = list(self.config_dir.glob(pattern))
        return [f.name for f in config_files]
    
    def validate_config(self, config: ScrapeConfig) -> Dict[str, Any]:
        """Validate a scraper configuration."""
        issues = []
        warnings = []
        
        # Check required fields
        if not config.keywords and not config.job_titles:
            issues.append("Either keywords or job_titles must be specified")
        
        if not config.locations:
            warnings.append("No locations specified - will search globally")
        
        if not config.sites:
            issues.append("At least one job site must be specified")
        
        # Check site validity
        valid_sites = {"indeed", "linkedin", "glassdoor", "zip_recruiter"}
        invalid_sites = set(config.sites) - valid_sites
        if invalid_sites:
            issues.append(f"Invalid sites: {invalid_sites}")
        
        # Check salary range
        if (config.salary_min and config.salary_max and 
            config.salary_min > config.salary_max):
            issues.append("Minimum salary cannot be greater than maximum")
        
        # Check results limit
        if config.max_results_per_site > 200:
            warnings.append("High results limit may slow down scraping")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    def convert_to_jobspy_params(self, config: ScrapeConfig) -> Dict[str, Any]:
        """Convert ScrapeConfig to JobSpy parameters."""
        # Combine keywords and job titles for search
        search_terms = []
        search_terms.extend(config.keywords)
        search_terms.extend(config.job_titles)
        
        # Create search query
        search_query = " OR ".join(f'"{term}"' for term in search_terms)
        
        # Map experience levels
        experience_map = {
            "entry": "entry_level",
            "mid": "mid_level", 
            "senior": "senior_level"
        }
        
        mapped_experience = [
            experience_map.get(exp, exp) 
            for exp in config.experience_levels
        ]
        
        jobspy_params = {
            "search_term": search_query,
            "location": ", ".join(config.locations) if config.locations else "",
            "results_wanted": config.max_results_per_site,
            "site_name": config.sites,
            "distance": 50,  # km
            "country_indeed": config.country,
            "hours_old": self._convert_date_posted(config.date_posted),
            "is_remote": config.remote_ok,
        }
        
        # Add optional parameters
        if mapped_experience:
            jobspy_params["job_level"] = mapped_experience
        
        if config.job_types:
            jobspy_params["job_type"] = config.job_types
        
        return jobspy_params
    
    def _convert_date_posted(self, date_posted: str) -> int:
        """Convert date posted string to hours."""
        mapping = {
            "today": 24,
            "week": 168,   # 7 * 24
            "month": 720,  # 30 * 24
            "all": 8760    # 365 * 24
        }
        return mapping.get(date_posted, 720)
    
    def get_dashboard_options(self) -> Dict[str, Any]:
        """Get options for dashboard configuration UI."""
        return {
            "sites": [
                {"value": "indeed", "label": "Indeed"},
                {"value": "linkedin", "label": "LinkedIn"},
                {"value": "glassdoor", "label": "Glassdoor"},
                {"value": "zip_recruiter", "label": "ZipRecruiter"}
            ],
            "countries": [
                {"value": "canada", "label": "Canada"},
                {"value": "usa", "label": "USA"},
                {"value": "uk", "label": "United Kingdom"}
            ],
            "experience_levels": [
                {"value": "entry", "label": "Entry Level"},
                {"value": "mid", "label": "Mid Level"},
                {"value": "senior", "label": "Senior Level"}
            ],
            "job_types": [
                {"value": "full-time", "label": "Full Time"},
                {"value": "part-time", "label": "Part Time"},
                {"value": "contract", "label": "Contract"},
                {"value": "internship", "label": "Internship"}
            ],
            "date_posted": [
                {"value": "today", "label": "Today"},
                {"value": "week", "label": "Past Week"},
                {"value": "month", "label": "Past Month"},
                {"value": "all", "label": "All Time"}
            ],
            "popular_keywords": [
                "python", "javascript", "react", "aws", "docker",
                "sql", "excel", "tableau", "powerbi", "salesforce",
                "marketing", "sales", "customer service", "project management"
            ],
            "popular_locations": [
                "toronto", "vancouver", "montreal", "calgary", "ottawa",
                "remote", "work from home", "hybrid"
            ]
        }


# Global instance
_scraper_manager_instance = None


def get_scraper_manager() -> CustomizableScraperManager:
    """Get global scraper manager instance."""
    global _scraper_manager_instance
    if _scraper_manager_instance is None:
        _scraper_manager_instance = CustomizableScraperManager()
    return _scraper_manager_instance
