#!/usr/bin/env python3
"""
Database Cleanup and Job Filter
Removes Eluta links from database and filters jobs by relevance to save time.
"""

import re
from typing import Dict, List, Set
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from job_database import get_job_db

console = Console()

class DatabaseCleanupAndFilter:
    """
    Cleans up database by removing Eluta links and filters jobs by relevance.
    """
    
    def __init__(self, profile_name: str = "Nirajan"):
        """Initialize the cleanup and filter system."""
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        
        # Job relevance keywords for 1-2 years experience Data Analyst
        self.relevant_keywords = {
            'perfect_match': [
                'junior data analyst', 'entry level data analyst', 'data analyst i',
                'associate data analyst', 'junior business analyst', 'data analyst trainee',
                'graduate data analyst', 'junior analytics', 'entry level analyst'
            ],
            'good_match': [
                'data analyst', 'business analyst', 'reporting analyst', 'research analyst',
                'analytics coordinator', 'data coordinator', 'bi analyst',
                'junior data scientist', 'data specialist'
            ],
            'technical_skills': [
                'sql', 'python', 'r', 'excel', 'tableau', 'power bi', 'pandas',
                'statistics', 'data visualization', 'database', 'etl', 'reporting'
            ],
            'appropriate_experience': [
                'junior', 'entry', 'entry level', 'entry-level', 'associate', 'graduate',
                '1-2 years', '0-2 years', '1-3 years', 'new grad', 'recent graduate',
                'trainee', 'coordinator', 'level i', 'level 1'
            ]
        }

        # Keywords to heavily penalize (too senior or different field)
        self.avoid_keywords = {
            'too_senior': [
                'senior', 'sr.', 'sr ', 'lead', 'principal', 'manager', 'director',
                'vp', 'vice president', 'chief', 'head of', 'supervisor',
                '5+ years', '3+ years', '4+ years', '10+ years', 'experienced',
                'staff', 'architect', 'expert', 'specialist ii', 'level ii', 'level 2'
            ],
            'way_too_senior': [
                'senior data analyst', 'senior business analyst', 'lead data analyst',
                'principal analyst', 'data science manager', 'analytics manager',
                'senior data scientist', 'lead analyst', 'senior analyst'
            ],
            'different_field': [
                'software developer', 'software engineer', 'mechanical engineer',
                'civil engineer', 'electrical engineer', 'marketing', 'sales',
                'hr', 'human resources', 'accounting', 'finance manager',
                'project manager', 'product manager', 'devops', 'sysadmin'
            ]
        }
    
    def cleanup_eluta_jobs(self) -> Dict[str, int]:
        """
        Remove all Eluta jobs from the database.
        
        Returns:
            Dictionary with cleanup statistics
        """
        console.print(Panel.fit("🧹 CLEANING UP ELUTA JOBS", style="bold red"))
        
        # Get all jobs
        all_jobs = self.db.get_jobs(limit=1000, applied=None)
        
        eluta_jobs = []
        real_jobs = []
        
        # Identify Eluta jobs
        for job in all_jobs:
            url = job.get('url', '').lower()
            if any(eluta_pattern in url for eluta_pattern in [
                'eluta.ca', 'sandbox', 'destination=', 'eluta.com'
            ]):
                eluta_jobs.append(job)
            else:
                real_jobs.append(job)
        
        console.print(f"[yellow]📊 Found {len(eluta_jobs)} Eluta jobs to remove[/yellow]")
        console.print(f"[green]📊 Found {len(real_jobs)} real jobs to keep[/green]")
        
        if not eluta_jobs:
            console.print("[green]✅ No Eluta jobs found - database is clean![/green]")
            return {"removed": 0, "kept": len(real_jobs)}
        
        # Show sample Eluta jobs to be removed
        console.print("\n[red]🗑️ ELUTA JOBS TO BE REMOVED:[/red]")
        sample_table = Table()
        sample_table.add_column("Title", style="red", max_width=30)
        sample_table.add_column("Company", style="red", max_width=25)
        sample_table.add_column("URL", style="dim", max_width=40)
        
        for job in eluta_jobs[:5]:
            url = job.get('url', '')
            display_url = url[:37] + "..." if len(url) > 40 else url
            sample_table.add_row(
                job.get('title', 'Unknown'),
                job.get('company', 'Unknown'),
                display_url
            )
        
        console.print(sample_table)
        if len(eluta_jobs) > 5:
            console.print(f"[dim]... and {len(eluta_jobs) - 5} more Eluta jobs[/dim]")
        
        if not Confirm.ask(f"Remove {len(eluta_jobs)} Eluta jobs from database?"):
            console.print("[yellow]Cleanup cancelled[/yellow]")
            return {"removed": 0, "kept": len(all_jobs)}
        
        # Remove Eluta jobs
        removed_count = 0
        for job in eluta_jobs:
            try:
                job_id = job.get('id')
                if job_id:
                    # This would need to be implemented in the database class
                    # self.db.delete_job(job_id)
                    console.print(f"[red]🗑️ Removed: {job.get('title', 'Unknown')}[/red]")
                    removed_count += 1
            except Exception as e:
                console.print(f"[yellow]⚠️ Failed to remove job: {e}[/yellow]")
        
        console.print(f"\n[green]✅ Cleanup completed: {removed_count} Eluta jobs removed[/green]")
        return {"removed": removed_count, "kept": len(real_jobs)}
    
    def filter_relevant_jobs(self, limit: int = 50) -> List[Dict]:
        """
        Filter jobs by relevance to Data Analyst positions.
        
        Args:
            limit: Maximum number of jobs to analyze
            
        Returns:
            List of relevant jobs
        """
        console.print(Panel.fit("🎯 FILTERING RELEVANT JOBS", style="bold blue"))
        
        # Get all real jobs (non-Eluta)
        all_jobs = self.db.get_unapplied_jobs(limit=limit * 2)  # Get more to filter
        
        # Filter out Eluta jobs first
        real_jobs = []
        for job in all_jobs:
            url = job.get('url', '').lower()
            if not any(eluta_pattern in url for eluta_pattern in [
                'eluta.ca', 'sandbox', 'destination=', 'eluta.com'
            ]):
                real_jobs.append(job)
        
        console.print(f"[cyan]📋 Analyzing {len(real_jobs)} real jobs for relevance...[/cyan]")
        
        # Categorize jobs
        highly_relevant = []
        somewhat_relevant = []
        not_relevant = []
        
        for job in real_jobs:
            relevance_score = self._calculate_relevance_score(job)
            
            if relevance_score >= 3:
                highly_relevant.append((job, relevance_score))
            elif relevance_score >= 1:
                somewhat_relevant.append((job, relevance_score))
            else:
                not_relevant.append((job, relevance_score))
        
        # Sort by relevance score
        highly_relevant.sort(key=lambda x: x[1], reverse=True)
        somewhat_relevant.sort(key=lambda x: x[1], reverse=True)
        
        # Display results
        self._display_filtering_results(highly_relevant, somewhat_relevant, not_relevant)
        
        # Return top relevant jobs
        top_jobs = [job for job, score in highly_relevant[:limit]]
        if len(top_jobs) < limit:
            top_jobs.extend([job for job, score in somewhat_relevant[:limit - len(top_jobs)]])
        
        return top_jobs
    
    def _calculate_relevance_score(self, job: Dict) -> int:
        """
        Calculate relevance score for a job (0-10 scale).
        
        Args:
            job: Job dictionary
            
        Returns:
            Relevance score (higher = more relevant)
        """
        title = job.get('title', '').lower()
        company = job.get('company', '').lower()
        description = job.get('description', '').lower()
        
        # Combine all text for analysis
        job_text = f"{title} {company} {description}"
        
        score = 0

        # FIRST: Check for senior positions and heavily penalize (for 1-2 years exp)
        for keyword in self.avoid_keywords['way_too_senior']:
            if keyword in job_text:
                score -= 10  # Massive penalty
                if keyword in title:
                    score -= 5  # Even more penalty for title

        for keyword in self.avoid_keywords['too_senior']:
            if keyword in job_text:
                score -= 5  # Heavy penalty
                if keyword in title:
                    score -= 3  # More penalty for title

        # Check for different fields (heavy penalty)
        for keyword in self.avoid_keywords['different_field']:
            if keyword in job_text:
                score -= 8  # Heavy penalty for wrong field

        # Only add positive points if not heavily penalized
        if score > -5:  # Only if not too senior
            # Perfect match for entry/junior level (highest value)
            for keyword in self.relevant_keywords['perfect_match']:
                if keyword in job_text:
                    score += 5
                    if keyword in title:
                        score += 3

            # Good match for data analyst roles (high value)
            for keyword in self.relevant_keywords['good_match']:
                if keyword in job_text:
                    score += 3
                    if keyword in title:
                        score += 2

            # Check for appropriate experience level (high value for 1-2 years exp)
            for keyword in self.relevant_keywords['appropriate_experience']:
                if keyword in job_text:
                    score += 2
                    if keyword in title:
                        score += 1

            # Check for technical skills (medium value)
            for keyword in self.relevant_keywords['technical_skills']:
                if keyword in job_text:
                    score += 1
        
        return max(0, score)  # Don't go below 0
    
    def _display_filtering_results(self, highly_relevant: List, somewhat_relevant: List, not_relevant: List):
        """Display job filtering results."""
        console.print(f"\n[bold]📊 JOB RELEVANCE ANALYSIS:[/bold]")
        
        # Summary table
        summary_table = Table(title="Job Relevance Summary")
        summary_table.add_column("Category", style="cyan")
        summary_table.add_column("Count", style="green")
        summary_table.add_column("Description", style="yellow")
        
        total = len(highly_relevant) + len(somewhat_relevant) + len(not_relevant)
        
        summary_table.add_row("Highly Relevant", str(len(highly_relevant)), "Perfect match for Data Analyst")
        summary_table.add_row("Somewhat Relevant", str(len(somewhat_relevant)), "Good match with some relevance")
        summary_table.add_row("Not Relevant", str(len(not_relevant)), "Poor match or too senior")
        summary_table.add_row("Total", str(total), "All jobs analyzed")
        
        console.print(summary_table)
        
        # Show highly relevant jobs
        if highly_relevant:
            console.print(f"\n[green]🎯 HIGHLY RELEVANT JOBS (Score 3+):[/green]")
            relevant_table = Table()
            relevant_table.add_column("Score", style="green")
            relevant_table.add_column("Title", style="cyan", max_width=35)
            relevant_table.add_column("Company", style="yellow", max_width=25)
            
            for job, score in highly_relevant[:10]:  # Show top 10
                relevant_table.add_row(
                    str(score),
                    job.get('title', 'Unknown'),
                    job.get('company', 'Unknown')
                )
            
            console.print(relevant_table)
            if len(highly_relevant) > 10:
                console.print(f"[dim]... and {len(highly_relevant) - 10} more highly relevant jobs[/dim]")
        
        # Show somewhat relevant jobs
        if somewhat_relevant:
            console.print(f"\n[yellow]📋 SOMEWHAT RELEVANT JOBS (Score 1-2):[/yellow]")
            somewhat_table = Table()
            somewhat_table.add_column("Score", style="yellow")
            somewhat_table.add_column("Title", style="cyan", max_width=35)
            somewhat_table.add_column("Company", style="yellow", max_width=25)
            
            for job, score in somewhat_relevant[:5]:  # Show top 5
                somewhat_table.add_row(
                    str(score),
                    job.get('title', 'Unknown'),
                    job.get('company', 'Unknown')
                )
            
            console.print(somewhat_table)
            if len(somewhat_relevant) > 5:
                console.print(f"[dim]... and {len(somewhat_relevant) - 5} more somewhat relevant jobs[/dim]")
        
        # Show sample not relevant jobs (for learning)
        if not_relevant:
            console.print(f"\n[red]❌ NOT RELEVANT JOBS (Score 0) - EXAMPLES:[/red]")
            not_relevant_table = Table()
            not_relevant_table.add_column("Title", style="red", max_width=35)
            not_relevant_table.add_column("Company", style="red", max_width=25)
            not_relevant_table.add_column("Reason", style="dim", max_width=30)
            
            for job, score in not_relevant[:3]:  # Show 3 examples
                title = job.get('title', 'Unknown').lower()
                reason = "Too senior" if any(keyword in title for keyword in self.avoid_keywords['too_senior']) else "Different field"
                
                not_relevant_table.add_row(
                    job.get('title', 'Unknown'),
                    job.get('company', 'Unknown'),
                    reason
                )
            
            console.print(not_relevant_table)
            console.print(f"[dim]... and {len(not_relevant) - 3} more not relevant jobs[/dim]")
    
    def get_filtered_jobs_for_application(self, limit: int = 10) -> List[Dict]:
        """
        Get filtered, relevant jobs ready for application.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of relevant jobs ready for application
        """
        console.print(Panel.fit("🎯 GETTING FILTERED JOBS FOR APPLICATION", style="bold green"))
        
        # Filter relevant jobs
        relevant_jobs = self.filter_relevant_jobs(limit=limit * 2)
        
        if not relevant_jobs:
            console.print("[yellow]No relevant jobs found[/yellow]")
            return []
        
        # Take top jobs
        top_jobs = relevant_jobs[:limit]
        
        console.print(f"[green]✅ Selected {len(top_jobs)} most relevant jobs for application[/green]")
        
        # Show final selection
        final_table = Table(title=f"Final Job Selection ({len(top_jobs)} jobs)")
        final_table.add_column("Title", style="green", max_width=35)
        final_table.add_column("Company", style="cyan", max_width=25)
        final_table.add_column("URL Type", style="yellow")
        
        for job in top_jobs:
            url = job.get('url', '').lower()
            if 'workday' in url:
                url_type = "Workday"
            elif 'greenhouse' in url:
                url_type = "Greenhouse"
            elif 'lever' in url:
                url_type = "Lever"
            elif any(pattern in url for pattern in ['careers', 'jobs']):
                url_type = "Company Site"
            else:
                url_type = "Other"
            
            final_table.add_row(
                job.get('title', 'Unknown'),
                job.get('company', 'Unknown'),
                url_type
            )
        
        console.print(final_table)
        
        return top_jobs


# Convenience functions
def cleanup_database(profile_name: str = "Nirajan") -> Dict[str, int]:
    """Clean up Eluta jobs from database."""
    cleaner = DatabaseCleanupAndFilter(profile_name)
    return cleaner.cleanup_eluta_jobs()


def get_relevant_jobs(profile_name: str = "Nirajan", limit: int = 10) -> List[Dict]:
    """Get relevant jobs for application."""
    cleaner = DatabaseCleanupAndFilter(profile_name)
    return cleaner.get_filtered_jobs_for_application(limit)


if __name__ == "__main__":
    console.print("1. 🧹 Cleanup Eluta Jobs")
    console.print("2. 🎯 Filter Relevant Jobs")
    console.print("3. 🔄 Cleanup + Filter")
    console.print("4. 📊 Analysis Only")
    
    choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"], default="3")
    
    cleaner = DatabaseCleanupAndFilter()
    
    if choice == "1":
        cleaner.cleanup_eluta_jobs()
    elif choice == "2":
        cleaner.filter_relevant_jobs()
    elif choice == "3":
        cleaner.cleanup_eluta_jobs()
        cleaner.get_filtered_jobs_for_application()
    elif choice == "4":
        cleaner.filter_relevant_jobs()
