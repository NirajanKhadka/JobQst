"""
Enhanced JobSpy Integration with Key Optimizations
Key improvements for better JobQst integration:

1. All JobSpy parameters utilized
2. Proxy rotation support  
3. Direct database integration
4. LinkedIn enhanced descriptions
5. Advanced search queries
6. Better performance monitoring
"""

import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from rich.console import Console
from pathlib import Path

# JobSpy import
try:
    from jobspy import scrape_jobs
    JOBSPY_AVAILABLE = True
except ImportError:
    JOBSPY_AVAILABLE = False

# Proxy support
try:
    from swiftshadow import QuickProxy
    SWIFTSHADOW_AVAILABLE = True
except ImportError:
    SWIFTSHADOW_AVAILABLE = False

from ..core.job_database import get_job_db
from ..utils.profile_helpers import load_profile
from ..utils.location_categorizer import categorize_job_location

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class EnhancedJobSpyConfig:
    """Enhanced JobSpy configuration with all available parameters."""
    
    # Core parameters
    locations: List[str] = field(default_factory=list)
    search_terms: List[str] = field(default_factory=list)
    sites: List[str] = field(default_factory=lambda: [
        "indeed", "linkedin", "glassdoor", "zip_recruiter"
    ])
    
    # Results configuration  
    results_wanted: int = 100  # Max per search (was limited to 20)
    hours_old: int = 168  # 7 days
    max_total_jobs: int = 2000  # Much higher limit
    
    # Country settings
    country_indeed: str = "Canada"
    country_linkedin: str = "Canada"
    
    # Enhanced features
    linkedin_fetch_description: bool = True  # Get detailed descriptions
    google_search_term: Optional[str] = None  # Custom Google search
    
    # Proxy settings
    enable_proxies: bool = False
    proxy_countries: List[str] = field(default_factory=lambda: ["US", "CA"])
    
    # Performance
    direct_db_write: bool = True  # Skip conversion overhead
    batch_size: int = 5  # Parallel searches
    verbose: int = 1


class JobSpyScraper:
    """Enhanced JobSpy scraper with key optimizations."""
    
    def __init__(self, profile_name: str, config: Optional[EnhancedJobSpyConfig] = None):
        self.profile_name = profile_name
        self.profile = load_profile(profile_name)
        self.db = get_job_db(profile_name)
        self.config = config or self._load_enhanced_config()
        
        if not JOBSPY_AVAILABLE:
            raise ImportError("Install JobSpy: pip install python-jobspy")
        
        # Proxy setup
        self.proxy = None
        if self.config.enable_proxies and SWIFTSHADOW_AVAILABLE:
            self.proxy = QuickProxy(countries=self.config.proxy_countries)
            console.print("[cyan]🔄 Proxy rotation enabled[/cyan]")
        
        # Direct database path
        if self.config.direct_db_write:
            self.db_path = Path(f"data/{profile_name}/jobs_enhanced.db")
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_enhanced_db()
        
        self.stats = {
            "searches_completed": 0,
            "jobs_found": 0,
            "jobs_saved": 0,
            "linkedin_detailed": 0,
            "proxy_rotations": 0,
            "start_time": None,
            "processing_time": 0.0
        }
    
    def _load_enhanced_config(self) -> EnhancedJobSpyConfig:
        """Load enhanced configuration."""
        
        # Optimized locations
        locations = [
            "Toronto, ON", "Mississauga, ON", "Vancouver, BC", "Montreal, QC",
            "Calgary, AB", "Ottawa, ON", "Edmonton, AB", "Waterloo, ON",
            "Remote, Canada", "Work from Home, Canada"
        ]
        
        # Refined search terms based on Nirajan's actual skills and experience
        search_terms = [
            '"software developer" (python OR javascript OR react)',
            '"full stack developer" (react OR node.js)',
            '"python developer" (django OR flask OR fastapi)',
            '"javascript developer" (react OR node.js)',
            '"react developer" (frontend OR full stack)',
            '"node.js developer" (backend OR api)',
            '"backend developer" (python OR node.js OR api)',
            '"web developer" (react OR javascript OR python)',
            '"api developer" (rest OR fastapi OR node.js)',
            '"cloud developer" (aws OR docker)',
            '"software engineer" (mid level OR 2+ years)',
            '"full stack engineer" -senior -lead'
        ]
        
        config = EnhancedJobSpyConfig(
            locations=locations,
            search_terms=search_terms,
            results_wanted=100,  # Use full JobSpy capacity
            max_total_jobs=2000,  # Much higher than current 100 limit
            linkedin_fetch_description=True,  # Get detailed info
            enable_proxies=False,  # Disable proxy rotation for now
            direct_db_write=True  # Skip conversion overhead
        )
        
        # Debug: Verify configuration
        console.print(f"[yellow]Debug: Config loaded with {len(config.locations)} locations and {len(config.search_terms)} search terms[/yellow]")
        
        return config
    
    def _init_enhanced_db(self):
        """Initialize enhanced database with optimized schema."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs_enhanced (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    job_url TEXT UNIQUE,
                    description TEXT,
                    salary_min INTEGER,
                    salary_max INTEGER,
                    job_type TEXT,
                    is_remote BOOLEAN,
                    date_posted DATE,
                    search_term TEXT,
                    site_source TEXT,
                    company_url TEXT,
                    company_industry TEXT,
                    job_level TEXT,
                    emails TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(job_url, site_source)
                )
            """)
            
            # Performance indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_company ON jobs_enhanced(company)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_location ON jobs_enhanced(location)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_date ON jobs_enhanced(date_posted)")
            
            conn.commit()
            conn.close()
            console.print("[green]✅ Enhanced database initialized[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ Database init failed: {e}[/red]")
            self.config.direct_db_write = False
    
    async def scrape_enhanced(self) -> List[Dict[str, Any]]:
        """Run enhanced scraping with all optimizations."""
        self.stats["start_time"] = datetime.now()
        
        console.print("[bold blue]🚀 Enhanced JobSpy Scraping Started[/bold blue]")
        console.print(f"[cyan]📍 Locations: {len(self.config.locations)}[/cyan]")
        console.print(f"[cyan]🔍 Search terms: {len(self.config.search_terms)}[/cyan]")
        console.print(f"[cyan]🎯 Max jobs: {self.config.max_total_jobs}[/cyan]")
        console.print(f"[cyan]📋 LinkedIn details: {self.config.linkedin_fetch_description}[/cyan]")
        
        # Prepare search combinations
        combinations = [
            (loc, term) for loc in self.config.locations 
            for term in self.config.search_terms
        ]
        
        all_jobs = []
        
        # Run searches in batches
        for i in range(0, len(combinations), self.config.batch_size):
            if len(all_jobs) >= self.config.max_total_jobs:
                break
                
            batch = combinations[i:i + self.config.batch_size]
            
            # Rotate proxy if enabled
            if self.proxy:
                self.proxy = QuickProxy(countries=self.config.proxy_countries)
                self.stats["proxy_rotations"] += 1
            
            # Run batch in parallel
            tasks = [
                self._enhanced_search(location, term)
                for location, term in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, list):
                    all_jobs.extend(result)
                    
                    # Save immediately if enabled
                    if self.config.direct_db_write:
                        await self._save_to_enhanced_db(result)
            
            await asyncio.sleep(1.0)  # Be respectful
        
        # Final statistics
        self.stats["processing_time"] = (
            datetime.now() - self.stats["start_time"]
        ).total_seconds()
        
        self._print_enhanced_results()
        
        return all_jobs
    
    async def _enhanced_search(self, location: str, term: str) -> List[Dict[str, Any]]:
        """Enhanced search with all JobSpy parameters and Glassdoor error handling."""
        try:
            console.print(f"🔍 Searching: '{term}' in {location}")
            
            # Prepare proxies
            proxies = None
            if self.proxy:
                try:
                    # Handle different proxy types
                    if hasattr(self.proxy, 'as_string'):
                        proxies = [self.proxy.as_string()]
                    elif isinstance(self.proxy, str):
                        proxies = [self.proxy]
                    else:
                        proxies = None
                except Exception as e:
                    console.print(f"[yellow]⚠️ Proxy error: {e}. Continuing without proxy.[/yellow]")
                    proxies = None
            
            # Import Glassdoor error handler
            from .glassdoor_error_handler import safe_jobspy_scrape
            
            # Use safe scraping with Glassdoor error handling
            jobs_df = await safe_jobspy_scrape(
                site_name=self.config.sites,
                search_term=term,
                location=location,
                results_wanted=self.config.results_wanted,  # Use full capacity
                hours_old=self.config.hours_old,
                country_indeed=self.config.country_indeed,
                country_linkedin=self.config.country_linkedin,
                linkedin_fetch_description=self.config.linkedin_fetch_description,  # Enhanced data
                google_search_term=self.config.google_search_term,
                verbose=self.config.verbose,
                proxies=proxies,  # Proxy support
                enable_glassdoor_fallback=True  # Enable Glassdoor error handling
            )
            
            if len(jobs_df) > 0:
                # Fast conversion
                jobs_list = self._fast_convert(jobs_df, location, term)
                
                self.stats["searches_completed"] += 1
                self.stats["jobs_found"] += len(jobs_list)
                
                # Count LinkedIn detailed fetches
                if self.config.linkedin_fetch_description:
                    linkedin_jobs = jobs_df[jobs_df.get('site', '') == 'linkedin']
                    self.stats["linkedin_detailed"] += len(linkedin_jobs)
                
                console.print(f"✅ Found {len(jobs_list)} jobs")
                return jobs_list
            else:
                console.print("❌ No jobs found")
                return []
                
        except Exception as e:
            console.print(f"❌ Search error: {e}")
            return []
    
    def _fast_convert(self, jobs_df: pd.DataFrame, location: str, term: str) -> List[Dict[str, Any]]:
        """Fast conversion optimized for database insertion with location categorization."""
        jobs_list = []
        
        for _, row in jobs_df.iterrows():
            job_location = str(row.get('location', location))
            
            # Categorize the location
            location_info = categorize_job_location(job_location)
            
            job = {
                'title': str(row.get('title', '')),
                'company': str(row.get('company', '')),
                'location': job_location,
                'job_url': str(row.get('job_url', '')),
                'description': str(row.get('description', '')),
                'job_type': str(row.get('job_type', '')),
                'is_remote': bool(row.get('is_remote', False)),
                'date_posted': self._parse_date(row.get('date_posted')),
                'search_term': term,
                'site_source': str(row.get('site', 'unknown')),
                'company_url': str(row.get('company_url', '')),
                'company_industry': str(row.get('company_industry', '')),
                'job_level': str(row.get('job_level', '')),
                'emails': str(row.get('emails', '')),
                'salary_min': self._extract_salary(row, 'min_amount'),
                'salary_max': self._extract_salary(row, 'max_amount'),
                
                # Enhanced location fields
                'location_type': location_info.location_type,
                'location_category': location_info.location_category,
                'city_tags': ','.join(location_info.city_tags),  # Convert list to comma-separated string
                'province_code': location_info.province_code,
                'is_rcip_city': 1 if location_info.is_rcip_city else 0,
                'is_immigration_priority': 1 if location_info.is_immigration_priority else 0,
            }
            jobs_list.append(job)
        
        return jobs_list
    
    async def _save_to_enhanced_db(self, jobs: List[Dict[str, Any]]):
        """Save directly to main PostgreSQL database."""
        if not jobs:
            return
        
        try:
            # Save to main database using the db instance - RAW DATA ONLY
            # Let Ultra-Fast Pipeline handle ALL processing and scoring
            for job in jobs:
                # Create salary_range from salary_min/max if available
                salary_range = ""
                if job.get('salary_min') and job.get('salary_max'):
                    salary_range = f"${job['salary_min']} - ${job['salary_max']}"
                elif job.get('salary_min'):
                    salary_range = f"${job['salary_min']}+"
                elif job.get('salary_max'):
                    salary_range = f"Up to ${job['salary_max']}"
                
                # Convert to format expected by main database - RAW DATA ONLY
                job_record = {
                    'title': job['title'],
                    'company': job['company'],
                    'location': job['location'],
                    'url': job['job_url'],
                    'description': job['description'],
                    'salary_range': salary_range,
                    'job_type': job.get('job_type', ''),
                    'is_remote': job.get('is_remote', False),
                    'date_posted': job.get('date_posted'),
                    'search_term': job.get('search_term', ''),
                    'site_source': job.get('site_source', 'jobspy'),
                    'company_url': job.get('company_url', ''),
                    'company_industry': job.get('company_industry', ''),
                    'job_level': job.get('job_level', ''),
                    'emails': job.get('emails', ''),
                    'location_type': job.get('location_type', ''),
                    'location_category': job.get('location_category', ''),
                    'city_tags': job.get('city_tags', ''),
                    'province_code': job.get('province_code', ''),
                    'is_rcip_city': job.get('is_rcip_city', 0),
                    'is_immigration_priority': job.get('is_immigration_priority', 0),
                    # Raw data fields - no processing/scoring here
                    'status': 'scraped',
                    'match_score': 0,  # Will be calculated by Ultra-Fast Pipeline
                    'compatibility_score': 0,  # Will be calculated by Ultra-Fast Pipeline
                    'analysis_status': 'pending',  # Indicates needs processing
                }
                
                # Use the main database to insert RAW data only
                self.db.add_job(job_record)
            
            self.stats["jobs_saved"] += len(jobs)
            
        except Exception as e:
            logger.error(f"Database save error: {e}")
            # Fallback to enhanced database if main database fails
            await self._save_to_enhanced_db_fallback(jobs)
    
    async def _save_to_enhanced_db_fallback(self, jobs: List[Dict[str, Any]]):
        """Fallback: Save using unified database interface."""
        if not jobs:
            return
        
        try:
            # Convert jobs to format expected by unified database
            formatted_jobs = []
            for job in jobs:
                # Create salary_range from salary_min/max if available
                salary_range = ""
                if job.get('salary_min') and job.get('salary_max'):
                    salary_range = (f"${job['salary_min']} - "
                                    f"${job['salary_max']}")
                elif job.get('salary_min'):
                    salary_range = f"${job['salary_min']}+"
                elif job.get('salary_max'):
                    salary_range = f"Up to ${job['salary_max']}"
                
                formatted_job = {
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', ''),
                    'url': job.get('job_url', ''),
                    'description': job.get('description', ''),
                    'salary_range': salary_range,
                    'source': job.get('site_source', 'jobspy'),
                    'date_posted': job.get('date_posted'),
                    'keywords': job.get('search_term', ''),
                    'status': 'active'
                }
                formatted_jobs.append(formatted_job)
            
            # Use unified database interface
            saved_count = 0
            for job in formatted_jobs:
                if self.db.add_job(job):
                    saved_count += 1
            
            console.print(f"[yellow]⚠️ Saved {saved_count} jobs using "
                         f"fallback database interface[/yellow]")
            
        except Exception as e:
            logger.error(f"Fallback database save error: {e}")
    
    def _parse_date(self, date_value) -> Optional[str]:
        """Parse date from various formats."""
        if pd.isna(date_value) or date_value is None:
            return None
        
        try:
            if isinstance(date_value, str) and 'ago' in date_value.lower():
                if 'day' in date_value:
                    days = int(''.join(filter(str.isdigit, date_value)))
                    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                elif 'hour' in date_value:
                    hours = int(''.join(filter(str.isdigit, date_value)))
                    return (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d')
            
            return pd.to_datetime(date_value).strftime('%Y-%m-%d')
        except:
            return None
    
    def _extract_salary(self, row, field: str) -> Optional[int]:
        """Extract salary value."""
        try:
            if field in row and not pd.isna(row[field]):
                return int(float(row[field]))
        except:
            pass
        return None
    
    def _print_enhanced_results(self):
        """Print enhanced results summary."""
        console.print(f"\n[bold green]🚀 Enhanced JobSpy Results[/bold green]")
        console.print(f"[cyan]📊 Searches: {self.stats['searches_completed']}[/cyan]")
        console.print(f"[cyan]🎯 Jobs found: {self.stats['jobs_found']}[/cyan]")
        console.print(f"[cyan]💾 Jobs saved: {self.stats['jobs_saved']}[/cyan]")
        console.print(f"[cyan]📋 LinkedIn detailed: {self.stats['linkedin_detailed']}[/cyan]")
        console.print(f"[cyan]🔄 Proxy rotations: {self.stats['proxy_rotations']}[/cyan]")
        console.print(f"[cyan]⚡ Time: {self.stats['processing_time']:.1f}s[/cyan]")


# Integration function for main.py
async def run_enhanced_jobspy_pipeline(profile_name: str, 
                                     sites: List[str] = None, 
                                     max_jobs: int = 2000) -> bool:
    """Run enhanced JobSpy pipeline with optimizations."""
    
    try:
        # Create enhanced scraper with default config (which loads proper locations/terms)
        scraper = JobSpyScraper(profile_name, None)  # None triggers _load_enhanced_config
        
        # Override specific settings if provided
        if sites:
            scraper.config.sites = sites
        if max_jobs:
            scraper.config.max_total_jobs = max_jobs
        
        # Run enhanced scraper
        results = await scraper.scrape_enhanced()
        
        console.print(f"[bold green]✅ Enhanced pipeline completed: {len(results)} jobs[/bold green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Enhanced pipeline failed: {e}[/red]")
        return False
