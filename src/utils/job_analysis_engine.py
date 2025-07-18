from typing import Dict, List
from rich.console import Console

from src.core.user_profile_manager import UserProfileManager
from src.scrapers.parallel_job_scraper import ParallelJobScraper
from src.core.job_database import get_job_db
from src.utils import profile_helpers
from src.analysis.keyword_generator import get_intelligent_keywords
from src.analysis.resume_analyzer import ResumeAnalyzer
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

    def scrape_intelligently(self, max_jobs: int = 20) -> List[Dict]:
        console.print("[bold blue]🎯 Starting Intelligent Job Scraping[/bold blue]")
        keywords = get_intelligent_keywords(self.profile)
        console.print(f"[cyan]🔍 Using {len(keywords)} intelligent keywords[/cyan]")

        parallel_scraper = ParallelJobScraper(self.profile, max_workers=min(len(keywords), 4))
        all_jobs = parallel_scraper.scrape_jobs_parallel(sites=["eluta"], detailed_scraping=False)

        suitable_jobs = [job for job in all_jobs if self._is_job_suitable(job)][:max_jobs]
        console.print(f"[green]✅ Found {len(suitable_jobs)} suitable jobs[/green]")
        return suitable_jobs

    def _is_job_suitable(self, job: Dict) -> bool:
        title = job.get("title", "").lower()
        if any(term in title for term in ["senior", "lead", "manager"]):
            return False
        return True


def run_intelligent_scraping(profile_name: str, max_jobs: int = 20):
    engine = JobAnalysisEngine(profile_name)
    engine.update_profile_intelligence()
    jobs = engine.scrape_intelligently(max_jobs)
    # Here you would typically save the jobs to the database
    print(f"Found {len(jobs)} suitable jobs.")


if __name__ == "__main__":
    run_intelligent_scraping("Nirajan")
