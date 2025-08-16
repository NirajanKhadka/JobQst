"""
JobSpy Integration Configuration
Provides configuration mapping between JobSpy and AutoJobAgent systems.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class JobSpyIntegrationConfig:
    """Configuration for integrating JobSpy with AutoJobAgent FastJobPipeline."""
    
    # JobSpy settings
    enable_jobspy: bool = True
    jobspy_priority: str = "high"  # high, medium, low
    jobspy_max_jobs: int = 100
    jobspy_locations: List[str] = None
    jobspy_search_terms: List[str] = None
    jobspy_sites: List[str] = None
    
    # Integration settings
    combine_with_existing_scrapers: bool = True
    jobspy_weight: float = 0.6  # 60% JobSpy, 40% existing scrapers
    enable_cross_validation: bool = True
    enable_Improved_deduplication: bool = True
    
    # Pipeline integration
    use_jobspy_in_phase1: bool = True
    use_jobspy_parallel: bool = False
    jobspy_fallback_enabled: bool = True

# Pre-configured location sets optimized from JobSpy testing
JOBSPY_LOCATION_SETS = {
    "mississauga_focused": [
        "Meadowvale, ON", "Lisgar, ON", "Churchill Meadows, ON", "Heartland, ON",
        "Erin Mills, ON", "Malton, ON", "Square One, Mississauga, ON", "Mississauga, ON"
    ],
    "toronto_extended": [
        "Toronto, ON", "North York, ON", "Scarborough, ON", "Etobicoke, ON",
        "Downtown Toronto, ON", "Markham, ON", "Richmond Hill, ON", "Vaughan, ON",
        "Mississauga, ON", "Brampton, ON", "Oakville, ON"
    ],
    "gta_comprehensive": [
        "Toronto, ON", "Mississauga, ON", "Brampton, ON", "Markham, ON",
        "Vaughan, ON", "Richmond Hill, ON", "Oakville, ON", "Burlington, ON",
        "Hamilton, ON", "Pickering, ON", "Ajax, ON", "Whitby, ON"
    ],
    "remote_friendly": [
        "Toronto, ON", "Remote", "Ontario, Canada", "Canada",
        "North America", "Anywhere"
    ],
    "major_canadian_cities": [
        # Major metropolitan areas
        "Toronto, ON", "Vancouver, BC", "Calgary, AB", "Edmonton, AB",
        "Ottawa, ON", "Winnipeg, MB", "Quebec City, QC", "Hamilton, ON",
        
        # Tech hubs and university cities
        "Waterloo, ON", "Kitchener, ON", "London, ON", "Halifax, NS",
        "Saskatoon, SK", "Regina, SK", "Victoria, BC", "Burnaby, BC",
        
        # Additional major centers
        "Laval, QC", "Surrey, BC", "Markham, ON", "Vaughan, ON",
        "Gatineau, QC", "Richmond, BC", "Oakville, ON", "Burlington, ON"
    ],
    "canadian_cities": [
        # Same as major_canadian_cities but with the correct key name
        "Toronto, ON", "Vancouver, BC", "Calgary, AB", "Edmonton, AB",
        "Ottawa, ON", "Winnipeg, MB", "Quebec City, QC", "Hamilton, ON",
        "Waterloo, ON", "Kitchener, ON", "London, ON", "Halifax, NS",
        "Saskatoon, SK", "Regina, SK", "Victoria, BC", "Burnaby, BC",
        "Laval, QC", "Surrey, BC", "Markham, ON", "Vaughan, ON",
        "Gatineau, QC", "Richmond, BC", "Oakville, ON", "Burlington, ON"
    ],
    "canada_comprehensive": [
        # All major cities for maximum coverage
        "Toronto, ON", "Vancouver, BC", "Calgary, AB", "Edmonton, AB",
        "Ottawa, ON", "Waterloo, ON", "Kitchener, ON", "Halifax, NS",
        "Winnipeg, MB", "Quebec City, QC", "Hamilton, ON", "London, ON",
        "Victoria, BC", "Saskatoon, SK", "Regina, SK", "Burnaby, BC",
        "Laval, QC", "Surrey, BC", "Markham, ON", "Vaughan, ON",
        "Gatineau, QC", "Richmond, BC", "Oakville, ON", "Burlington, ON",
        "Mississauga, ON", "Brampton, ON", "Richmond Hill, ON",
        "St. John's, NL", "Fredericton, NB", "Charlottetown, PE"
    ],
    "tech_hubs_canada": [
        # Focus on Canadian tech centers
        "Toronto, ON", "Vancouver, BC", "Waterloo, ON", "Kitchener, ON",
        "Calgary, AB", "Ottawa, ON", "Montreal, QC", "Edmonton, AB",
        "Halifax, NS", "Victoria, BC", "Burnaby, BC", "Richmond, BC"
    ]
}

# Proven search terms from JobSpy testing (ordered by effectiveness)
JOBSPY_SEARCH_TERM_SETS = {
    "python_focused": [
        "python developer", "python software engineer", "python programmer",
        "django developer", "flask developer", "fastapi developer"
    ],
    "general_development": [
        "software developer", "software engineer", "full stack developer",
        "backend developer", "frontend developer", "web developer"
    ],
    "data_science": [
        "data analyst", "data scientist", "business analyst",
        "data engineer", "machine learning engineer", "ai engineer"
    ],
    "specialized_roles": [
        "devops engineer", "cloud engineer", "qa engineer",
        "mobile developer", "game developer", "security engineer"
    ],
    "leadership": [
        "senior developer", "lead developer", "engineering manager",
        "technical lead", "architect", "principal engineer"
    ]
}

# Query presets for different search strategies  
JOBSPY_QUERY_PRESETS = {
    "software_developer": [
        "Software Developer", "Python Developer", "Full Stack Developer",
        "Backend Developer", "Software Engineer", "Web Developer"
    ],
    "data_analyst": [
        "Data Analyst", "Business Analyst", "Data Scientist", 
        "Business Intelligence Analyst", "Research Analyst", "Reporting Analyst"
    ],
    "comprehensive": [
        "Data Analyst", "Data Scientist", "Machine Learning Engineer", "Python Developer",
        "Software Developer", "Business Analyst", "Data Engineer", "Software Engineer",
        "Full Stack Developer", "Backend Developer", "Analytics Specialist", "BI Developer"
    ],
    "entry_level": [
        "Junior Data Analyst", "Entry Level Analyst", "Associate Analyst",
        "Junior Python Developer", "Graduate Analyst", "Trainee Developer"
    ],
    "senior_level": [
        "Senior Data Analyst", "Lead Data Scientist", "Principal Analyst",
        "Senior Python Developer", "Data Science Manager", "Analytics Manager"
    ],
    "tech_focused": [
        "Python", "SQL", "Machine Learning", "Data Analysis", "Power BI",
        "Tableau", "AWS", "Cloud Analytics", "ETL Developer"
    ]
}

# Site combinations optimized from JobSpy results
JOBSPY_SITE_COMBINATIONS = {
    "balanced": ["indeed", "linkedin"],
    "comprehensive": ["indeed", "linkedin", "glassdoor"],
    "linkedin_focused": ["linkedin"],
    "indeed_focused": ["indeed"],
    "maximum_coverage": ["indeed", "linkedin", "glassdoor", "zip_recruiter"],
    "five_sites": ["indeed", "linkedin", "glassdoor", "zip_recruiter", "google"],
    "all_sites": ["indeed", "linkedin", "glassdoor", "zip_recruiter", "google", "bayt", "naukri", "bdjobs"]
}

def get_profile_optimized_config(profile: Dict[str, Any]) -> JobSpyIntegrationConfig:
    """
    Generate JobSpy configuration optimized for a specific user profile.
    """
    
    # Extract profile information
    profile_skills = profile.get("skills", [])
    profile_keywords = profile.get("keywords", [])
    profile_location_preference = profile.get("location_preference", "toronto_extended")
    profile_experience_level = profile.get("experience_level", "mid")
    
    # Determine best location set
    if "mississauga" in str(profile_location_preference).lower():
        locations = JOBSPY_LOCATION_SETS["mississauga_focused"]
    elif "remote" in str(profile_location_preference).lower():
        locations = JOBSPY_LOCATION_SETS["remote_friendly"]
    elif "gta" in str(profile_location_preference).lower():
        locations = JOBSPY_LOCATION_SETS["gta_comprehensive"]
    else:
        locations = JOBSPY_LOCATION_SETS["toronto_extended"]
    
    # Determine best search terms based on skills
    search_terms = []
    
    # Python-focused terms if Python skills detected
    python_skills = ["python", "django", "flask", "fastapi", "pandas", "numpy"]
    if any(skill.lower() in [s.lower() for s in profile_skills] for skill in python_skills):
        search_terms.extend(JOBSPY_SEARCH_TERM_SETS["python_focused"])
    
    # Data science terms if relevant skills detected
    data_skills = ["sql", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "tableau", "power bi"]
    if any(skill.lower() in [s.lower() for s in profile_skills] for skill in data_skills):
        search_terms.extend(JOBSPY_SEARCH_TERM_SETS["data_science"])
    
    # General development terms (always include)
    search_terms.extend(JOBSPY_SEARCH_TERM_SETS["general_development"])
    
    # Add specialized terms based on skills
    cloud_skills = ["aws", "azure", "gcp", "docker", "kubernetes"]
    if any(skill.lower() in [s.lower() for s in profile_skills] for skill in cloud_skills):
        search_terms.extend(JOBSPY_SEARCH_TERM_SETS["specialized_roles"])
    
    # Add leadership terms for senior profiles
    if profile_experience_level in ["senior", "lead", "principal"]:
        search_terms.extend(JOBSPY_SEARCH_TERM_SETS["leadership"])
    
    # Use profile keywords if available (highest priority)
    if profile_keywords:
        search_terms = profile_keywords + [term for term in search_terms if term not in profile_keywords]
    
    # Remove duplicates while preserving order
    search_terms = list(dict.fromkeys(search_terms))
    
    # Determine best sites based on profile preferences
    sites = JOBSPY_SITE_COMBINATIONS["balanced"]  # Default
    
    return JobSpyIntegrationConfig(
        enable_jobspy=True,
        jobspy_priority="high",
        jobspy_max_jobs=100,
        jobspy_locations=locations,
        jobspy_search_terms=search_terms,
        jobspy_sites=sites,
        combine_with_existing_scrapers=True,
        jobspy_weight=0.7,  # Favor JobSpy due to proven results
        enable_cross_validation=True,
        enable_Improved_deduplication=True,
        use_jobspy_in_phase1=True,
        use_jobspy_parallel=False,
        jobspy_fallback_enabled=True
    )

def get_fast_discovery_config() -> JobSpyIntegrationConfig:
    """Configuration optimized for fast job discovery."""
    return JobSpyIntegrationConfig(
        enable_jobspy=True,
        jobspy_priority="high",
        jobspy_max_jobs=50,
        jobspy_locations=JOBSPY_LOCATION_SETS["toronto_extended"][:5],  # Top 5 locations
        jobspy_search_terms=JOBSPY_SEARCH_TERM_SETS["python_focused"] + JOBSPY_SEARCH_TERM_SETS["general_development"][:3],
        jobspy_sites=JOBSPY_SITE_COMBINATIONS["balanced"],
        combine_with_existing_scrapers=False,  # JobSpy only for speed
        jobspy_weight=1.0,
        enable_cross_validation=False,
        enable_Improved_deduplication=True,
        use_jobspy_in_phase1=True,
        use_jobspy_parallel=False,
        jobspy_fallback_enabled=True
    )

def get_comprehensive_discovery_config() -> JobSpyIntegrationConfig:
    """Configuration optimized for comprehensive job discovery."""
    return JobSpyIntegrationConfig(
        enable_jobspy=True,
        jobspy_priority="high",
        jobspy_max_jobs=200,
        jobspy_locations=JOBSPY_LOCATION_SETS["gta_comprehensive"],
        jobspy_search_terms=JOBSPY_SEARCH_TERM_SETS["python_focused"] + 
                           JOBSPY_SEARCH_TERM_SETS["general_development"] + 
                           JOBSPY_SEARCH_TERM_SETS["data_science"],
        jobspy_sites=JOBSPY_SITE_COMBINATIONS["comprehensive"],
        combine_with_existing_scrapers=True,
        jobspy_weight=0.6,
        enable_cross_validation=True,
        enable_Improved_deduplication=True,
        use_jobspy_in_phase1=True,
        use_jobspy_parallel=True,  # Use parallel for maximum coverage
        jobspy_fallback_enabled=True
    )

def get_quality_focused_config() -> JobSpyIntegrationConfig:
    """Configuration optimized for high-quality job matches."""
    return JobSpyIntegrationConfig(
        enable_jobspy=True,
        jobspy_priority="high",
        jobspy_max_jobs=75,
        jobspy_locations=JOBSPY_LOCATION_SETS["mississauga_focused"] + JOBSPY_LOCATION_SETS["toronto_extended"][:3],
        jobspy_search_terms=JOBSPY_SEARCH_TERM_SETS["python_focused"] + JOBSPY_SEARCH_TERM_SETS["data_science"],
        jobspy_sites=JOBSPY_SITE_COMBINATIONS["linkedin_focused"],  # LinkedIn for quality
        combine_with_existing_scrapers=True,
        jobspy_weight=0.8,  # High weight for quality
        enable_cross_validation=True,
        enable_Improved_deduplication=True,
        use_jobspy_in_phase1=True,
        use_jobspy_parallel=False,
        jobspy_fallback_enabled=True
    )

# Configuration presets for easy CLI access
JOBSPY_CONFIG_PRESETS = {
    "fast": get_fast_discovery_config,
    "comprehensive": get_comprehensive_discovery_config,
    "quality": get_quality_focused_config,
    "mississauga": lambda: JobSpyIntegrationConfig(
        enable_jobspy=True,
        jobspy_locations=JOBSPY_LOCATION_SETS["mississauga_focused"],
        jobspy_search_terms=JOBSPY_SEARCH_TERM_SETS["python_focused"],
        jobspy_sites=JOBSPY_SITE_COMBINATIONS["balanced"]
    ),
    "toronto": lambda: JobSpyIntegrationConfig(
        enable_jobspy=True,
        jobspy_locations=JOBSPY_LOCATION_SETS["toronto_extended"],
        jobspy_search_terms=JOBSPY_SEARCH_TERM_SETS["general_development"],
        jobspy_sites=JOBSPY_SITE_COMBINATIONS["balanced"]
    ),
    "remote": lambda: JobSpyIntegrationConfig(
        enable_jobspy=True,
        jobspy_locations=JOBSPY_LOCATION_SETS["remote_friendly"],
        jobspy_search_terms=JOBSPY_SEARCH_TERM_SETS["python_focused"] + JOBSPY_SEARCH_TERM_SETS["data_science"],
        jobspy_sites=JOBSPY_SITE_COMBINATIONS["linkedin_focused"]
    ),
    "canadian_cities": lambda: JobSpyIntegrationConfig(
        enable_jobspy=True,
        jobspy_priority="high",
        jobspy_max_jobs=500,  # Higher limit for comprehensive search
        jobspy_locations=JOBSPY_LOCATION_SETS["major_canadian_cities"],
        jobspy_search_terms=JOBSPY_SEARCH_TERM_SETS["python_focused"] + JOBSPY_SEARCH_TERM_SETS["general_development"],
        jobspy_sites=JOBSPY_SITE_COMBINATIONS["comprehensive"],
        combine_with_existing_scrapers=True,
        jobspy_weight=0.8,
        enable_cross_validation=True,
        enable_Improved_deduplication=True,
        use_jobspy_in_phase1=True,
        use_jobspy_parallel=True,  # Parallel for max coverage
        jobspy_fallback_enabled=True
    ),
    "canada_comprehensive": lambda: JobSpyIntegrationConfig(
        enable_jobspy=True,
        jobspy_priority="high", 
        jobspy_max_jobs=1000,  # Maximum jobs for all cities
        jobspy_locations=JOBSPY_LOCATION_SETS["canada_comprehensive"],
        jobspy_search_terms=JOBSPY_SEARCH_TERM_SETS["python_focused"] + 
                           JOBSPY_SEARCH_TERM_SETS["general_development"] + 
                           JOBSPY_SEARCH_TERM_SETS["data_science"],
        jobspy_sites=JOBSPY_SITE_COMBINATIONS["maximum_coverage"],
        combine_with_existing_scrapers=False,  # JobSpy only for speed
        jobspy_weight=1.0,
        enable_cross_validation=True,
        enable_Improved_deduplication=True,
        use_jobspy_in_phase1=True,
        use_jobspy_parallel=True,
        jobspy_fallback_enabled=True
    ),
    "tech_hubs": lambda: JobSpyIntegrationConfig(
        enable_jobspy=True,
        jobspy_priority="high",
        jobspy_max_jobs=300,
        jobspy_locations=JOBSPY_LOCATION_SETS["tech_hubs_canada"],
        jobspy_search_terms=JOBSPY_SEARCH_TERM_SETS["python_focused"] + JOBSPY_SEARCH_TERM_SETS["specialized_roles"],
        jobspy_sites=JOBSPY_SITE_COMBINATIONS["linkedin_focused"],  # LinkedIn for tech roles
        combine_with_existing_scrapers=True,
        jobspy_weight=0.7,
        enable_cross_validation=True,
        enable_Improved_deduplication=True,
        use_jobspy_in_phase1=True,
        use_jobspy_parallel=False,
        jobspy_fallback_enabled=True
    )
}

def create_custom_config(
    locations: List[str] = None,
    search_terms: List[str] = None,
    sites: List[str] = None,
    max_jobs: int = 100,
    priority: str = "high"
) -> JobSpyIntegrationConfig:
    """Create a custom JobSpy integration configuration."""
    
    return JobSpyIntegrationConfig(
        enable_jobspy=True,
        jobspy_priority=priority,
        jobspy_max_jobs=max_jobs,
        jobspy_locations=locations or JOBSPY_LOCATION_SETS["toronto_extended"],
        jobspy_search_terms=search_terms or JOBSPY_SEARCH_TERM_SETS["python_focused"],
        jobspy_sites=sites or JOBSPY_SITE_COMBINATIONS["balanced"],
        combine_with_existing_scrapers=True,
        jobspy_weight=0.6,
        enable_cross_validation=True,
        enable_Improved_deduplication=True,
        use_jobspy_in_phase1=True,
        use_jobspy_parallel=False,
        jobspy_fallback_enabled=True
    )

# Database schema mapping for JobSpy data
JOBSPY_TO_AUTOJOB_SCHEMA_MAPPING = {
    # JobSpy field -> AutoJobAgent field
    "id": "external_id",
    "site": "data_source",
    "job_url": "url",
    "job_url_direct": "direct_url",
    "title": "title",
    "company": "company",
    "location": "location",
    "date_posted": "date_posted",
    "job_type": "job_type",
    "salary_source": "salary_source",
    "interval": "salary_interval",
    "min_amount": "salary_min",
    "max_amount": "salary_max",
    "currency": "salary_currency",
    "is_remote": "is_remote",
    "job_level": "experience_level",
    "job_function": "job_function",
    "listing_type": "listing_type",
    "company_industry": "company_industry",
    "company_url": "company_url",
    "company_logo": "company_logo",
    "company_url_direct": "company_url_direct",
    "company_addresses": "company_addresses",
    "company_num_employees": "company_size",
    "company_revenue": "company_revenue",
    "company_description": "company_description",
    "company_rating": "company_rating",
    "company_reviews_count": "company_reviews_count",
    "emails": "contact_emails",
    "description": "description",
    "skills": "skills_raw",
    "experience_range": "experience_range",
    "vacancy_count": "vacancy_count",
    "work_from_home_type": "work_from_home_type",
    "search_location": "search_location",
    "search_term": "search_term",
    "search_timestamp": "search_timestamp",
    "search_id": "search_id"
}

def map_jobspy_to_autojob_data(jobspy_row: Dict[str, Any]) -> Dict[str, Any]:
    """Map JobSpy data row to AutoJobAgent database format."""
    
    mapped_data = {}
    
    # Apply schema mapping
    for jobspy_field, autojob_field in JOBSPY_TO_AUTOJOB_SCHEMA_MAPPING.items():
        if jobspy_field in jobspy_row:
            mapped_data[autojob_field] = jobspy_row[jobspy_field]
    
    # Add AutoJobAgent specific fields
    mapped_data.update({
        "status": "scraped",
        "analysis_status": "pending",
        "application_status": "not_applied",
        "compatibility_score": None,
        "data_source": "jobspy",
        "created_at": None,  # Will be set by database
        "updated_at": None   # Will be set by database
    })
    
    return mapped_data
