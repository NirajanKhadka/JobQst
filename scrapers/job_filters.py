"""
Enhanced job filtering and experience level detection module.
Implements filtering for jobs posted within last 124 days (14 days for Eluta), 
0-2 years experience only, and better experience level detection.
Based on user memories and existing implementations.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from rich.console import Console

console = Console()


class JobDateFilter:
    """Filter jobs by posting date with site-specific rules."""
    
    def __init__(self, site_name: str = "generic"):
        self.site_name = site_name.lower()
        self.site_configs = self._get_site_date_configs()
        self.current_config = self.site_configs.get(self.site_name, self.site_configs["generic"])
        
    def _get_site_date_configs(self) -> Dict:
        """Get site-specific date filtering configurations."""
        return {
            "eluta": {
                "max_age_days": 14,  # 14 days for Eluta as per memories
                "cutoff_date": datetime.now() - timedelta(days=14),
                "date_patterns": {
                    "hour": r'(\d+)\s*hours?\s*ago',
                    "day": r'(\d+)\s*days?\s*ago',
                    "week": r'(\d+)\s*weeks?\s*ago',
                    "month": r'(\d+)\s*months?\s*ago'
                }
            },
            "indeed": {
                "max_age_days": 124,  # 124 days for other sites as per memories
                "cutoff_date": datetime.now() - timedelta(days=124),
                "date_patterns": {
                    "hour": r'(\d+)\s*hours?\s*ago',
                    "day": r'(\d+)\s*days?\s*ago',
                    "week": r'(\d+)\s*weeks?\s*ago',
                    "month": r'(\d+)\s*months?\s*ago'
                }
            },
            "jobbank": {
                "max_age_days": 124,
                "cutoff_date": datetime.now() - timedelta(days=124),
                "date_patterns": {
                    "hour": r'(\d+)\s*hours?\s*ago',
                    "day": r'(\d+)\s*days?\s*ago',
                    "week": r'(\d+)\s*weeks?\s*ago',
                    "month": r'(\d+)\s*months?\s*ago'
                }
            },
            "generic": {
                "max_age_days": 124,  # Default to 124 days
                "cutoff_date": datetime.now() - timedelta(days=124),
                "date_patterns": {
                    "hour": r'(\d+)\s*hours?\s*ago',
                    "day": r'(\d+)\s*days?\s*ago',
                    "week": r'(\d+)\s*weeks?\s*ago',
                    "month": r'(\d+)\s*months?\s*ago'
                }
            }
        }
    
    def is_job_recent_enough(self, job: Dict) -> bool:
        """Check if a job was posted within the site-specific time limit."""
        posted_date = job.get("posted_date", "")
        
        if not posted_date:
            # If no date info, assume it's recent (benefit of doubt)
            return True
        
        posted_date_lower = posted_date.lower()
        config = self.current_config
        
        # Check hours (always recent)
        if "hour" in posted_date_lower or "minute" in posted_date_lower:
            return True
        
        # Check days
        if "day" in posted_date_lower:
            match = re.search(config["date_patterns"]["day"], posted_date_lower)
            if match:
                days_ago = int(match.group(1))
                is_recent = days_ago <= config["max_age_days"]
                if not is_recent:
                    console.print(f"[yellow]📅 Job too old ({days_ago} days): {job.get('title', 'Unknown')[:50]}...[/yellow]")
                return is_recent
            return True  # If we can't parse, assume recent
        
        # Check weeks
        if "week" in posted_date_lower:
            match = re.search(config["date_patterns"]["week"], posted_date_lower)
            if match:
                weeks_ago = int(match.group(1))
                days_ago = weeks_ago * 7
                is_recent = days_ago <= config["max_age_days"]
                if not is_recent:
                    console.print(f"[yellow]📅 Job too old ({weeks_ago} weeks): {job.get('title', 'Unknown')[:50]}...[/yellow]")
                return is_recent
            return False  # "weeks ago" without number is likely old
        
        # Check months (usually too old)
        if "month" in posted_date_lower:
            match = re.search(config["date_patterns"]["month"], posted_date_lower)
            if match:
                months_ago = int(match.group(1))
                days_ago = months_ago * 30
                is_recent = days_ago <= config["max_age_days"]
                if not is_recent:
                    console.print(f"[yellow]📅 Job too old ({months_ago} months): {job.get('title', 'Unknown')[:50]}...[/yellow]")
                return is_recent
            return False  # "months ago" without number is definitely old
        
        # If no recognizable date pattern, assume recent
        return True


class ExperienceLevelFilter:
    """Filter jobs by experience level (0-2 years only as per memories)."""
    
    def __init__(self):
        self.experience_patterns = self._get_experience_patterns()
        
    def _get_experience_patterns(self) -> Dict:
        """Get experience level detection patterns."""
        return {
            "definitely_entry_level": [
                # Explicit entry level terms
                "entry level", "entry-level", "junior", "jr.", "jr ", "associate",
                "graduate", "new grad", "recent graduate", "fresh graduate",
                "trainee", "intern", "internship", "co-op", "coop", "student",
                "coordinator", "assistant", "level i", "level 1",
                
                # Experience ranges (0-2 years as per memories)
                "0-1 years", "0-2 years", "1-2 years", "0 to 1 years", "0 to 2 years",
                "1 to 2 years", "up to 2 years", "less than 3 years",
                "no experience required", "no experience necessary",
                "minimal experience", "little experience"
            ],
            
            "definitely_too_senior": [
                # Senior level terms
                "senior", "sr.", "sr ", "lead", "principal", "manager", "mgr",
                "director", "supervisor", "head of", "chief", "vp", "vice president",
                "team lead", "team leader", "architect", "expert", "specialist",
                "consultant", "staff engineer", "staff developer",
                
                # Experience requirements (3+ years)
                "3+ years", "4+ years", "5+ years", "6+ years", "7+ years",
                "8+ years", "9+ years", "10+ years", "3 years", "4 years",
                "5 years", "6 years", "7 years", "8 years", "9 years", "10 years",
                "minimum 3 years", "minimum 4 years", "minimum 5 years",
                "at least 3 years", "at least 4 years", "at least 5 years",
                "3-5 years", "4-6 years", "5-7 years", "experienced professional"
            ],
            
            "ambiguous_terms": [
                # Terms that could be entry or senior level
                "analyst", "developer", "engineer", "programmer", "technician",
                "specialist", "representative", "advisor", "officer"
            ],
            
            "positive_entry_indicators": [
                # Additional positive signals for entry level
                "training provided", "will train", "on-the-job training",
                "mentorship", "growth opportunity", "career development",
                "learn and grow", "entry into", "starting position"
            ]
        }
    
    def is_suitable_experience_level(self, job: Dict) -> Tuple[bool, str, float]:
        """
        Check if job is suitable for 0-2 years experience (as per memories).
        
        Returns:
            (is_suitable, experience_level, confidence_score)
        """
        # Handle None or invalid job data
        if not job or not isinstance(job, dict):
            console.print(f"[red]❌ Invalid job data: {job}[/red]")
            return False, "Invalid", 0.0
            
        title = job.get("title", "")
        if not isinstance(title, str):
            title = ""
        summary = job.get("summary", "")
        if not isinstance(summary, str):
            summary = ""
        description = job.get("full_description", "")
        if not isinstance(description, str):
            description = ""
            
        title = title.lower()
        summary = summary.lower()
        description = description.lower()
        
        # Combine all text for analysis
        job_text = f"{title} {summary} {description}"
        
        patterns = self.experience_patterns
        
        # Check for definitely too senior positions (immediate exclusion)
        for senior_term in patterns["definitely_too_senior"]:
            if senior_term in job_text:
                console.print(f"[red]❌ Too senior ({senior_term}): {title[:50]}...[/red]")
                return False, "Senior", 0.9
        
        # Check for definitely entry level (immediate inclusion)
        entry_score = 0
        matched_terms = []
        for entry_term in patterns["definitely_entry_level"]:
            if entry_term in job_text:
                entry_score += 1
                matched_terms.append(entry_term)
        
        # Bonus points for positive entry indicators
        for positive_term in patterns["positive_entry_indicators"]:
            if positive_term in job_text:
                entry_score += 0.5
                matched_terms.append(positive_term)
        
        if entry_score > 0:
            confidence = min(0.9, 0.6 + (entry_score * 0.1))
            console.print(f"[green]✅ Entry level ({', '.join(matched_terms[:2])}): {title[:50]}...[/green]")
            return True, "Entry", confidence
        
        # Check for ambiguous terms (needs further analysis but include by default)
        has_ambiguous = any(term in job_text for term in patterns["ambiguous_terms"])
        
        if has_ambiguous:
            # Include ambiguous jobs but mark for potential review
            console.print(f"[yellow]📋 Ambiguous level (including): {title[:50]}...[/yellow]")
            return True, "Unknown", 0.5
        
        # If no clear indicators either way, include it (benefit of doubt for entry-level as per memories)
        console.print(f"[cyan]📝 No clear indicators (including): {title[:50]}...[/cyan]")
        return True, "Unknown", 0.4


class UniversalJobFilter:
    """Universal job filtering system combining date and experience filters."""
    
    def __init__(self, site_name: str = "generic"):
        self.site_name = site_name
        self.date_filter = JobDateFilter(site_name)
        self.experience_filter = ExperienceLevelFilter()
        
        console.print(f"[green]✅ Universal job filter initialized for {site_name}[/green]")
        console.print(f"[cyan]📅 Date filter: {self.date_filter.current_config['max_age_days']} days[/cyan]")
        console.print(f"[cyan]🎯 Experience filter: 0-2 years only[/cyan]")
    
    def filter_job(self, job: Dict) -> Tuple[bool, Dict]:
        """
        Apply comprehensive filtering to a job.
        
        Returns:
            (should_include, enhanced_job_data)
        """
        # Start with the original job data
        enhanced_job = job.copy()
        
        # Apply date filtering
        if not self.date_filter.is_job_recent_enough(job):
            return False, enhanced_job
        
        # Apply experience level filtering
        is_suitable, experience_level, confidence = self.experience_filter.is_suitable_experience_level(job)
        
        # Enhance job data with filtering results
        enhanced_job.update({
            "experience_level": experience_level,
            "experience_confidence": confidence,
            "filtered_by": self.site_name,
            "filter_passed": is_suitable,
            "filter_timestamp": datetime.now().isoformat()
        })
        
        return is_suitable, enhanced_job
    
    def filter_jobs_batch(self, jobs: List[Dict]) -> List[Dict]:
        """Filter a batch of jobs and return only suitable ones."""
        suitable_jobs = []
        total_jobs = len(jobs)
        
        console.print(f"[cyan]🔍 Filtering {total_jobs} jobs for {self.site_name}...[/cyan]")
        
        for job in jobs:
            should_include, enhanced_job = self.filter_job(job)
            if should_include:
                suitable_jobs.append(enhanced_job)
        
        filtered_count = len(suitable_jobs)
        console.print(f"[green]✅ Filtered {total_jobs} jobs → {filtered_count} suitable jobs ({filtered_count/total_jobs*100:.1f}%)[/green]")
        
        return suitable_jobs
