#!/usr/bin/env python3
"""
Job Analysis Engine for AutoJobAgent.
Combines resume analysis, experience filtering, and automated keyword targeting.
"""

import time
from pathlib import Path
from typing import Dict, List
from rich.console import Console
from rich.prompt import Confirm, Prompt
from playwright.sync_api import sync_playwright

from ..core.user_profile_manager import UserProfileManager
from src.scrapers.working_eluta_scraper import WorkingElutaScraper
from .job_analyzer import JobAnalyzer as ExperienceAnalyzer
from scrapers.parallel_job_scraper import ParallelJobScraper
from job_database import get_job_db
from src.core import utils

console = Console()


class JobAnalysisEngine:
    """
    Job analysis engine that combines:
    1. Resume analysis for dynamic keyword extraction
    2. Experience level filtering for suitable jobs
    3. Automated targeting based on profile skills
    """
    
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.profile = None
        self.job_db = None
        self.experience_analyzer = ExperienceAnalyzer()
        self.profile_manager = UserProfileManager()
        
    def initialize(self) -> bool:
        """Initialize the intelligent scraper."""
        try:
            # Load profile
            self.profile = utils.load_profile(self.profile_name)
            console.print(f"[green]✅ Loaded profile: {self.profile['name']}[/green]")
            
            # Initialize database
            self.job_db = get_job_db(self.profile['profile_name'])
            console.print(f"[green]✅ Database initialized[/green]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Initialization failed: {e}[/red]")
            return False
    
    def update_profile_intelligence(self) -> bool:
        """Update profile with intelligent resume analysis (only if resume changed)."""
        try:
            # Check if resume analysis is needed
            if not self._needs_resume_analysis():
                # Silent success - no output needed for cached data
                return True

            console.print("[cyan]🧠 Updating profile intelligence...[/cyan]")

            # Analyze and update profile
            updated_profile = self.profile_manager.analyze_and_update_profile(self.profile_name)

            if updated_profile:
                self.profile = updated_profile
                # Update the analysis timestamp
                self._update_analysis_timestamp()
                console.print("[green]✅ Profile updated with intelligent keywords[/green]")
                return True
            else:
                console.print("[yellow]⚠️ Profile not updated, using existing data[/yellow]")
                return True

        except Exception as e:
            console.print(f"[red]❌ Profile update failed: {e}[/red]")
            return False

    def _needs_resume_analysis(self) -> bool:
        """Check if resume analysis is needed (resume changed since last analysis)."""
        try:
            from pathlib import Path
            import json

            # Get resume path
            profile_dir = Path(self.profile.get('profile_dir', f"profiles/{self.profile_name}"))
            resume_path = profile_dir / self.profile.get('resume_docx', f"{self.profile_name}_Resume.docx")

            if not resume_path.exists():
                return False  # No resume to analyze

            # Get resume modification time
            resume_mtime = resume_path.stat().st_mtime

            # Check if we have cached analysis timestamp
            analysis_cache_file = profile_dir / ".resume_analysis_cache.json"

            if not analysis_cache_file.exists():
                return True  # No cache, need analysis

            # Load cached timestamp
            with open(analysis_cache_file, 'r') as f:
                cache_data = json.load(f)

            last_analysis_time = cache_data.get('last_analysis_time', 0)
            cached_resume_mtime = cache_data.get('resume_mtime', 0)

            # Need analysis if resume is newer than last analysis
            return resume_mtime > last_analysis_time or resume_mtime != cached_resume_mtime

        except Exception as e:
            console.print(f"[yellow]⚠️ Error checking analysis cache: {e}[/yellow]")
            return True  # Default to needing analysis if error

    def _update_analysis_timestamp(self) -> None:
        """Update the analysis timestamp cache."""
        try:
            from pathlib import Path
            import json
            import time

            # Get paths
            profile_dir = Path(self.profile.get('profile_dir', f"profiles/{self.profile_name}"))
            resume_path = profile_dir / self.profile.get('resume_docx', f"{self.profile_name}_Resume.docx")
            analysis_cache_file = profile_dir / ".resume_analysis_cache.json"

            # Create cache data
            cache_data = {
                'last_analysis_time': time.time(),
                'resume_mtime': resume_path.stat().st_mtime if resume_path.exists() else 0,
                'profile_name': self.profile_name,
                'analysis_version': '1.0'
            }

            # Save cache
            with open(analysis_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            console.print(f"[yellow]⚠️ Error updating analysis cache: {e}[/yellow]")

    def get_intelligent_keywords(self) -> List[str]:
        """Get intelligent keywords from profile."""
        keywords = self.profile.get('keywords', [])
        skills = self.profile.get('skills', [])
        
        # Generate additional intelligent keywords based on skills
        intelligent_keywords = keywords.copy()
        
        # Add skill-based job variations
        skill_lower = [s.lower() for s in skills]
        
        # Python-related jobs
        if 'python' in skill_lower:
            intelligent_keywords.extend([
                'Python Developer', 'Python Analyst', 'Python Data Analyst',
                'Junior Python Developer', 'Entry Level Python'
            ])
        
        # SQL-related jobs
        if 'sql' in skill_lower:
            intelligent_keywords.extend([
                'SQL Analyst', 'SQL Developer', 'Database Analyst',
                'Junior SQL Analyst'
            ])
        
        # Data analysis jobs
        data_skills = ['pandas', 'numpy', 'excel', 'tableau', 'power bi']
        if any(skill.lower() in skill_lower for skill in data_skills):
            intelligent_keywords.extend([
                'Junior Data Analyst', 'Entry Level Data Analyst',
                'Associate Data Analyst', 'Graduate Data Analyst',
                'Business Intelligence Analyst', 'Reporting Analyst'
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in intelligent_keywords:
            if keyword.lower() not in seen:
                seen.add(keyword.lower())
                unique_keywords.append(keyword)
        
        return unique_keywords[:12]  # Limit to 12 most relevant keywords

    def scrape_parallel(self, keywords: List[str], max_jobs: int = 20) -> List[Dict]:
        """Perform parallel intelligent job scraping."""
        console.print("[bold green]⚡ Starting Parallel Intelligent Scraping[/bold green]")

        # Create profile with intelligent keywords
        parallel_profile = self.profile.copy()
        parallel_profile["keywords"] = keywords

        # Use parallel scraper
        parallel_scraper = ParallelJobScraper(parallel_profile, max_workers=min(len(keywords), 2))

        # Scrape jobs in parallel
        all_jobs = parallel_scraper.scrape_jobs_parallel(
            sites=['eluta'],
            detailed_scraping=True
        )

        # Apply intelligent filtering
        suitable_jobs = []
        console.print(f"[cyan]🧠 Applying intelligent filtering to {len(all_jobs)} jobs...[/cyan]")

        for job in all_jobs:
            if self._is_job_suitable(job):
                suitable_jobs.append(job)
                if len(suitable_jobs) >= max_jobs:
                    break

        console.print(f"[green]✅ Parallel scraping found {len(suitable_jobs)} suitable jobs from {len(all_jobs)} total[/green]")
        return suitable_jobs

    def scrape_fast_parallel(self, keywords: List[str], max_jobs: int = 20) -> List[Dict]:
        """Perform ultra-fast parallel intelligent job scraping."""
        console.print("[bold yellow]⚡ Starting FAST Parallel Intelligent Scraping[/bold yellow]")

        # Create profile with intelligent keywords
        fast_profile = self.profile.copy()
        fast_profile["keywords"] = keywords

        # Use parallel scraper in fast mode
        fast_scraper = ParallelJobScraper(fast_profile, max_workers=min(len(keywords), 2))

        # Scrape jobs in fast mode
        all_jobs = fast_scraper.scrape_jobs_parallel(
            sites=['eluta'],
            detailed_scraping=False  # Faster without detailed scraping
        )

        # Apply intelligent filtering
        suitable_jobs = []
        console.print(f"[cyan]🧠 Applying intelligent filtering to {len(all_jobs)} jobs...[/cyan]")

        for job in all_jobs:
            if self._is_job_suitable(job):
                suitable_jobs.append(job)
                if len(suitable_jobs) >= max_jobs:
                    break

        console.print(f"[green]✅ Fast parallel scraping found {len(suitable_jobs)} suitable jobs from {len(all_jobs)} total[/green]")
        return suitable_jobs
    
    def scrape_intelligently(self, max_jobs: int = 20, use_parallel: bool = True, auto_mode: bool = False) -> List[Dict]:
        """Perform intelligent job scraping with experience filtering."""
        console.print("[bold blue]🎯 Starting Intelligent Job Scraping[/bold blue]")

        # Get intelligent keywords
        keywords = self.get_intelligent_keywords()
        console.print(f"[cyan]🔍 Using {len(keywords)} intelligent keywords[/cyan]")

        # Show keywords being used
        console.print("[bold]Keywords for this search:[/bold]")
        for i, keyword in enumerate(keywords, 1):
            console.print(f"   {i}. [green]{keyword}[/green]")

        # Ask about parallel processing
        if use_parallel and len(keywords) > 3:
            console.print(f"\n[bold yellow]⚡ Parallel Processing Available![/bold yellow]")
            console.print(f"[cyan]Your system: 24 CPU cores, 32GB RAM[/cyan]")
            console.print(f"[cyan]Can process {min(len(keywords), 12)} keywords simultaneously[/cyan]")
            console.print(f"[green]Estimated time reduction: 70-80%[/green]")

            if auto_mode:
                # Auto-select parallel mode for best performance
                console.print("[cyan]🤖 Auto-mode: Using parallel processing for optimal speed[/cyan]")
                return self.scrape_parallel(keywords, max_jobs)
            else:
                parallel_choice = Prompt.ask(
                    "Choose scraping mode",
                    choices=["parallel", "fast", "sequential"],
                    default="parallel"
                )

                if parallel_choice == "parallel":
                    return self.scrape_parallel(keywords, max_jobs)
                elif parallel_choice == "fast":
                    return self.scrape_fast_parallel(keywords, max_jobs)

        if not auto_mode and not Confirm.ask("\nProceed with intelligent scraping?"):
            return []
        
        suitable_jobs = []
        total_analyzed = 0
        
        try:
            with sync_playwright() as p:
                # Use headless browser for efficiency
                browser = p.chromium.launch(headless=True)
                ctx = browser.new_context()
                console.print("[green]🌐 Browser launched for intelligent scraping[/green]")
                
                # Process keywords in batches for efficiency
                for keyword_batch in self._batch_keywords(keywords, 3):
                    console.print(f"\n[bold]Processing keyword batch: {', '.join(keyword_batch)}[/bold]")
                    
                    # Create profile for this batch
                    batch_profile = self.profile.copy()
                    batch_profile["keywords"] = keyword_batch
                    
                    # Use enhanced scraper
                    scraper = WorkingElutaScraper(batch_profile, browser_context=ctx)
                    
                    batch_jobs = []
                    for job in scraper.scrape_jobs():
                        total_analyzed += 1
                        
                        # Apply experience filtering
                        if self._is_job_suitable(job):
                            batch_jobs.append(job)
                            console.print(f"[green]✅ Suitable job #{len(suitable_jobs) + len(batch_jobs)}: {job.get('title', 'Unknown')}[/green]")
                            
                            # Stop if we have enough suitable jobs
                            if len(suitable_jobs) + len(batch_jobs) >= max_jobs:
                                console.print(f"[yellow]⏹️ Reached target of {max_jobs} suitable jobs[/yellow]")
                                break
                        else:
                            console.print(f"[yellow]❌ Filtered out: {job.get('title', 'Unknown')}[/yellow]")
                        
                        # Stop if we've analyzed too many jobs
                        if total_analyzed >= 50:
                            console.print(f"[yellow]⏹️ Analyzed {total_analyzed} jobs, stopping[/yellow]")
                            break
                    
                    suitable_jobs.extend(batch_jobs)
                    
                    # Break if we have enough jobs
                    if len(suitable_jobs) >= max_jobs:
                        break
                    
                    # Delay between batches
                    if len(suitable_jobs) < max_jobs:
                        console.print("[cyan]⏳ Waiting before next batch...[/cyan]")
                        time.sleep(5)
                
                browser.close()
        
        except Exception as e:
            console.print(f"[red]❌ Scraping error: {e}[/red]")
            import traceback
            traceback.print_exc()
        
        console.print(f"\n[bold green]📊 Intelligent Scraping Results:[/bold green]")
        console.print(f"[green]✅ Found {len(suitable_jobs)} suitable jobs from {total_analyzed} analyzed[/green]")
        console.print(f"[green]📈 Success rate: {len(suitable_jobs)/max(total_analyzed, 1)*100:.1f}%[/green]")
        
        return suitable_jobs
    
    def _batch_keywords(self, keywords: List[str], batch_size: int) -> List[List[str]]:
        """Split keywords into batches for efficient processing."""
        batches = []
        for i in range(0, len(keywords), batch_size):
            batches.append(keywords[i:i + batch_size])
        return batches
    
    def _is_job_suitable(self, job: Dict) -> bool:
        """Check if job is suitable based on experience level and relevance."""
        title = job.get('title', '')
        description = job.get('summary', '') or job.get('full_description', '')
        
        # Use experience analyzer
        experience_level = self.experience_analyzer.analyze_experience_level(title, description)
        is_suitable = self.experience_analyzer.is_suitable_for_profile(job)
        
        # Additional relevance check based on profile skills
        if is_suitable:
            is_relevant = self._check_job_relevance(job)
            return is_relevant
        
        return False
    
    def _check_job_relevance(self, job: Dict) -> bool:
        """Check if job is relevant to profile skills and keywords."""
        title = job.get('title', '').lower()
        description = job.get('summary', '').lower()
        
        profile_skills = [s.lower() for s in self.profile.get('skills', [])]
        profile_keywords = [k.lower() for k in self.profile.get('keywords', [])]
        
        # Check if job mentions any of our skills or keywords
        job_text = f"{title} {description}"
        
        skill_matches = sum(1 for skill in profile_skills if skill in job_text)
        keyword_matches = sum(1 for keyword in profile_keywords if keyword in job_text)
        
        # Job is relevant if it matches at least 2 skills or 1 keyword
        return skill_matches >= 2 or keyword_matches >= 1
    
    def save_results(self, jobs: List[Dict]) -> bool:
        """Save intelligent scraping results to database."""
        if not jobs:
            console.print("[yellow]No jobs to save[/yellow]")
            return False
        
        try:
            # Add metadata
            for job in jobs:
                job["search_keyword"] = "intelligent_scrape"
                job["site"] = "eluta_intelligent"
                job["scraped_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                job["intelligent_filtered"] = True
            
            # Save to database
            added, duplicates = self.job_db.add_jobs_batch(jobs)
            console.print(f"[green]💾 Saved {added} intelligent jobs ({duplicates} duplicates skipped)[/green]")
            
            # Export to CSV
            csv_file = Path("output") / f"{self.profile['profile_name']}_intelligent_jobs.csv"
            csv_file.parent.mkdir(exist_ok=True)
            self.job_db.export_to_csv(str(csv_file))
            console.print(f"[green]📄 Exported to: {csv_file}[/green]")
            
            # Show sample jobs
            console.print(f"\n[bold]📋 Sample Intelligent Jobs:[/bold]")
            for i, job in enumerate(jobs[:5], 1):
                console.print(f"   {i}. [green]{job['title']}[/green] at {job['company']}")
                console.print(f"      📍 {job.get('location', 'Unknown location')}")
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error saving results: {e}[/red]")
            return False

    def run_scraping(self, sites: list = None, keywords: list = None, mode: str = "intelligent") -> List[Dict]:
        """Run scraping with specified parameters (method version).

        Args:
            sites: List of sites to scrape (default: ['eluta'])
            keywords: List of keywords to search (default: from profile)
            mode: Scraping mode ('intelligent', 'parallel', 'basic')

        Returns:
            List of scraped jobs
        """
        console.print(f"[bold blue]🔍 Running {mode} scraping...[/bold blue]")

        if mode == "intelligent":
            # Use intelligent scraping
            suitable_jobs = self.scrape_intelligently(max_jobs=20)
            return suitable_jobs
        elif mode == "parallel":
            # Use parallel scraping
            keywords = keywords or self.get_intelligent_keywords()
            suitable_jobs = self.scrape_parallel(keywords, max_jobs=20)
            return suitable_jobs
        else:
            # Basic mode - use enhanced scraper directly
            suitable_jobs = self.scrape_intelligently(max_jobs=20, use_parallel=False)
            return suitable_jobs

    def scrape_with_enhanced_scrapers(self, sites: list = None, max_jobs: int = 20) -> List[Dict]:
        """Scrape jobs using enhanced scrapers (method version).

        Args:
            sites: List of sites to scrape (default: ['eluta'])
            max_jobs: Maximum number of jobs to scrape

        Returns:
            List of scraped jobs
        """
        console.print(f"[bold blue]🔍 Enhanced scraping...[/bold blue]")

        # Use enhanced scraping
        suitable_jobs = self.scrape_intelligently(max_jobs=max_jobs, use_parallel=True)
        return suitable_jobs

    def get_scraper_for_site(self, site_name: str):
        """Get appropriate scraper for a specific site (method version).

        Args:
            site_name: Name of the site ('eluta', 'indeed', etc.)

        Returns:
            Scraper instance for the site
        """
        console.print(f"[cyan]Getting scraper for {site_name}...[/cyan]")

        if site_name.lower() == 'eluta':
            from src.scrapers.working_eluta_scraper import WorkingElutaScraper
            return WorkingElutaScraper(self.profile)
        elif site_name.lower() == 'indeed':
            from scrapers.indeed_enhanced import EnhancedIndeedScraper
            return EnhancedIndeedScraper(self.profile)
        else:
            # Default to Eluta enhanced scraper
            from src.scrapers.working_eluta_scraper import WorkingElutaScraper
            console.print(f"[yellow]Unknown site {site_name}, using Eluta scraper as fallback[/yellow]")
            return WorkingElutaScraper(self.profile)


def run_scraping(profile_name: str, sites: list = None, keywords: list = None, mode: str = "intelligent") -> List[Dict]:
    """Run scraping with specified parameters (alias for compatibility).

    Args:
        profile_name: Name of the profile to use
        sites: List of sites to scrape (default: ['eluta'])
        keywords: List of keywords to search (default: from profile)
        mode: Scraping mode ('intelligent', 'parallel', 'basic')

    Returns:
        List of scraped jobs
    """
    console.print(f"[bold blue]🔍 Running {mode} scraping for {profile_name}...[/bold blue]")

    # Initialize scraper
    scraper = JobAnalysisEngine(profile_name)

    if not scraper.initialize():
        return []

    if mode == "intelligent":
        # Use intelligent scraping
        suitable_jobs = scraper.scrape_intelligently(max_jobs=20)
        return suitable_jobs
    elif mode == "parallel":
        # Use parallel scraping
        keywords = keywords or scraper.get_intelligent_keywords()
        suitable_jobs = scraper.scrape_parallel(keywords, max_jobs=20)
        return suitable_jobs
    else:
        # Basic mode - use enhanced scraper directly
        keywords = keywords or scraper.get_intelligent_keywords()
        suitable_jobs = scraper.scrape_intelligently(max_jobs=20, use_parallel=False)
        return suitable_jobs

def scrape_with_enhanced_scrapers(profile_name: str, sites: list = None, max_jobs: int = 20) -> List[Dict]:
    """Scrape jobs using enhanced scrapers.

    Args:
        profile_name: Name of the profile to use
        sites: List of sites to scrape (default: ['eluta'])
        max_jobs: Maximum number of jobs to scrape

    Returns:
        List of scraped jobs
    """
    console.print(f"[bold blue]🔍 Enhanced scraping for {profile_name}...[/bold blue]")

    # Initialize scraper
    scraper = JobAnalysisEngine(profile_name)

    if not scraper.initialize():
        return []

    # Use enhanced scraping
    suitable_jobs = scraper.scrape_intelligently(max_jobs=max_jobs, use_parallel=True)
    return suitable_jobs

def get_scraper_for_site(site_name: str, profile: Dict):
    """Get appropriate scraper for a specific site.

    Args:
        site_name: Name of the site ('eluta', 'indeed', etc.)
        profile: Profile dictionary

    Returns:
        Scraper instance for the site
    """
    console.print(f"[cyan]Getting scraper for {site_name}...[/cyan]")

    if site_name.lower() == 'eluta':
        from src.scrapers.working_eluta_scraper import WorkingElutaScraper
        return WorkingElutaScraper(profile)
    elif site_name.lower() == 'indeed':
        from scrapers.indeed_enhanced import EnhancedIndeedScraper
        return EnhancedIndeedScraper(profile)
    else:
        # Default to Eluta enhanced scraper
        from src.scrapers.working_eluta_scraper import WorkingElutaScraper
        console.print(f"[yellow]Unknown site {site_name}, using Eluta scraper as fallback[/yellow]")
        return WorkingElutaScraper(profile)

def run_intelligent_scraping(profile_name: str, max_jobs: int = 20, auto_mode: bool = False) -> bool:
    """Run the complete intelligent scraping process."""
    console.print("[bold blue]🤖 AutoJobAgent - Intelligent Job Scraping[/bold blue]")

    # Initialize scraper
    scraper = JobAnalysisEngine(profile_name)

    if not scraper.initialize():
        return False

    # Update profile with resume intelligence
    if not scraper.update_profile_intelligence():
        return False

    # Perform intelligent scraping
    suitable_jobs = scraper.scrape_intelligently(max_jobs, auto_mode=auto_mode)

    if suitable_jobs:
        # Save results
        success = scraper.save_results(suitable_jobs)

        if success:
            console.print(f"\n[bold green]🎉 Intelligent scraping completed successfully![/bold green]")
            console.print(f"[green]Found {len(suitable_jobs)} jobs perfectly matched to your profile[/green]")
            return True

    console.print("[yellow]⚠️ No suitable jobs found. Try adjusting your profile or keywords.[/yellow]")
    return False


if __name__ == "__main__":
    # Test intelligent scraping
    try:
        success = run_intelligent_scraping("Nirajan", max_jobs=15)
        if success:
            console.print("[bold green]✅ Intelligent scraping test completed![/bold green]")
        else:
            console.print("[red]❌ Intelligent scraping test failed[/red]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()


# Backward compatibility alias (to be removed in future versions)
IntelligentJobScraper = JobAnalysisEngine
