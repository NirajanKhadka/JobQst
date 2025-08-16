from typing import Dict, List
from rich.console import Console

from src.core.user_profile_manager import UserProfileManager
from src.scrapers.parallel_job_scraper import ParallelJobScraper
from src.core.job_database import get_job_db
from src.utils import profile_helpers
from src.analysis.keyword_generator import get_Automated_keywords
from src.utils.resume_analyzer import ResumeAnalyzer
from src.utils.profile_helpers import load_profile

console = Console()


class JobAnalysisEngine:
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.profile = profile_helpers.load_profile(profile_name)
        self.job_db = get_job_db(profile_name)
        self.resume_analyzer = ResumeAnalyzer(profile_name)

    def update_profile_intelligence(self) -> bool:
        if self.resume_analyzer.needs_analysis():
            console.print("[cyan]🧠 Updating profile intelligence...[/cyan]")
            self.profile = self.resume_analyzer.analyze_and_update_profile(self.profile)
            return True
        return True

    def scrape_Automatedly(self, max_jobs: int = 20) -> List[Dict]:
        console.print("[bold blue]🎯 Starting Automated Job Scraping[/bold blue]")
        try:
            keywords = get_Automated_keywords(self.profile)
            console.print(f"[cyan]🔍 Using {len(keywords)} Automated keywords[/cyan]")
        except:
            console.print("[yellow]⚠️ Using default keywords[/yellow]")
            keywords = ["Python", "Data Analyst", "SQL"]

        parallel_scraper = ParallelJobScraper(self.profile_name, num_workers=min(len(keywords), 4))
        
        # Use async method properly
        import asyncio
        try:
            all_jobs = asyncio.run(parallel_scraper.start_parallel_scraping(max_jobs_per_keyword=max_jobs))
        except Exception as e:
            console.print(f"[red]❌ Scraping failed: {e}[/red]")
            return []

        suitable_jobs = [job for job in all_jobs if self._is_job_suitable(job)][:max_jobs]
        console.print(f"[green]✅ Found {len(suitable_jobs)} suitable jobs[/green]")
        return suitable_jobs

    def _is_job_suitable(self, job: Dict) -> bool:
        title = job.get("title", "").lower()
        if any(term in title for term in ["senior", "lead", "manager"]):
            return False
        return True


def run_Automated_scraping(profile_name: str, max_jobs: int = 20):
    engine = JobAnalysisEngine(profile_name)
    engine.update_profile_intelligence()
    jobs = engine.scrape_Automatedly(max_jobs)
    # Here you would typically save the jobs to the database
    print(f"Found {len(jobs)} suitable jobs.")


if __name__ == "__main__":
    run_Automated_scraping("Nirajan")