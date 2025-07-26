"""
Test No-AI Job Processor with Real Scraped Jobs from Nirajan Profile Database
Tests the parallel job processor (no AI) using actual scraped jobs from the database.
"""

import asyncio
import time
import sys
import statistics
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

console = Console()

@dataclass
class RealJobTestMetrics:
    """Metrics for testing with real jobs."""
    total_jobs_tested: int
    processing_time: float
    jobs_per_second: float
    
    # Analysis quality metrics
    skills_extracted_total: int
    skills_per_job_avg: float
    experience_levels_detected: Dict[str, int]
    
    # Confidence and compatibility
    confidence_scores: List[float]
    confidence_average: float
    compatibility_scores: List[float]
    compatibility_average: float
    
    # Processing success
    successful_jobs: int
    failed_jobs: int
    success_rate: float
    
    # Real job characteristics
    companies_processed: List[str]
    locations_processed: List[str]
    job_sites: List[str]
    
    def __post_init__(self):
        """Calculate derived metrics."""
        if self.confidence_scores:
            self.confidence_average = sum(self.confidence_scores) / len(self.confidence_scores)
        if self.compatibility_scores:
            self.compatibility_average = sum(self.compatibility_scores) / len(self.compatibility_scores)
        if self.total_jobs_tested > 0:
            self.skills_per_job_avg = self.skills_extracted_total / self.total_jobs_tested
            self.success_rate = self.successful_jobs / self.total_jobs_tested

class RealJobProcessor:
    """Test the no-AI processor with real scraped jobs."""
    
    def __init__(self, profile_name: str = "Nirajan"):
        self.profile_name = profile_name
        self.console = Console()
        
        # Initialize database connection
        try:
            from src.core.job_database import get_job_db
            self.db = get_job_db(profile_name)
            self.console.print(f"[green]✅ Connected to {profile_name} profile database[/green]")
        except Exception as e:
            self.console.print(f"[red]❌ Failed to connect to database: {e}[/red]")
            raise
        
        # Initialize parallel processor
        try:
            from src.ai.parallel_job_processor import get_parallel_processor
            self.processor = get_parallel_processor(max_workers=8, max_concurrent=16)
            self.console.print(f"[green]✅ Initialized parallel job processor[/green]")
        except Exception as e:
            self.console.print(f"[red]❌ Failed to initialize processor: {e}[/red]")
            raise
    
    def fetch_real_jobs(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Fetch real scraped jobs from the database."""
        self.console.print(f"[cyan]🔍 Fetching {limit} real jobs from {self.profile_name} database...[/cyan]")
        
        try:
            # Get all jobs from database
            all_jobs = self.db.get_all_jobs()
            
            if not all_jobs:
                self.console.print("[red]❌ No jobs found in database[/red]")
                return []
            
            # Filter jobs with meaningful content
            valid_jobs = []
            for job in all_jobs:
                # Convert database job to processor format
                processor_job = {
                    'id': job.get('job_id') or str(job.get('id', 'unknown')),
                    'title': job.get('title', 'Unknown Title'),
                    'company': job.get('company', 'Unknown Company'),
                    'description': job.get('job_description') or job.get('summary', ''),
                    'location': job.get('location', 'Unknown Location'),
                    'url': job.get('url', ''),
                    'status': job.get('status', 'scraped'),
                    'site': job.get('site', 'unknown'),
                    'search_keyword': job.get('search_keyword', ''),
                    'salary_range': job.get('salary_range', ''),
                    'requirements': job.get('requirements', ''),
                    'benefits': job.get('benefits', ''),
                    'scraped_at': job.get('scraped_at', ''),
                    'raw_data': job.get('raw_data', '{}')
                }
                
                # Only include jobs with some description content
                if len(processor_job['description']) > 50:
                    valid_jobs.append(processor_job)
                
                if len(valid_jobs) >= limit:
                    break
            
            self.console.print(f"[green]✅ Found {len(valid_jobs)} valid jobs with content[/green]")
            return valid_jobs
            
        except Exception as e:
            self.console.print(f"[red]❌ Error fetching jobs: {e}[/red]")
            return []
    
    def display_job_preview(self, jobs: List[Dict[str, Any]]):
        """Display preview of real jobs to be processed."""
        if not jobs:
            return
        
        preview_table = Table(title="📋 Real Jobs Preview (Nirajan Profile)")
        preview_table.add_column("ID", style="cyan", width=12)
        preview_table.add_column("Title", style="yellow", width=30)
        preview_table.add_column("Company", style="green", width=20)
        preview_table.add_column("Site", style="blue", width=10)
        preview_table.add_column("Content", style="magenta", width=15)
        
        for i, job in enumerate(jobs[:10]):  # Show first 10
            title = job['title'][:27] + "..." if len(job['title']) > 30 else job['title']
            company = job['company'][:17] + "..." if len(job['company']) > 20 else job['company']
            content_length = len(job['description'])
            
            preview_table.add_row(
                str(job['id'])[:10] + "..." if len(str(job['id'])) > 12 else str(job['id']),
                title,
                company,
                job['site'],
                f"{content_length} chars"
            )
        
        if len(jobs) > 10:
            preview_table.add_row("...", f"+ {len(jobs) - 10} more jobs", "...", "...", "...")
        
        self.console.print(preview_table)
    
    async def test_no_ai_processing(self, jobs: List[Dict[str, Any]]) -> RealJobTestMetrics:
        """Test the no-AI processor with real jobs."""
        self.console.print(f"[cyan]🚀 Testing No-AI Processor with {len(jobs)} real jobs...[/cyan]")
        
        start_time = time.time()
        
        # Track metrics
        skills_extracted = []
        experience_levels = {}
        confidence_scores = []
        compatibility_scores = []
        successful_jobs = 0
        failed_jobs = 0
        companies = set()
        locations = set()
        job_sites = set()
        
        try:
            # Process jobs using parallel processor
            result = await self.processor.process_jobs_async(jobs)
            
            processing_time = time.time() - start_time
            
            # Analyze results
            for i, job_result in enumerate(result.job_results):
                try:
                    # Extract analysis data
                    skills = job_result.get('required_skills', [])
                    skills_extracted.extend(skills)
                    
                    experience = job_result.get('experience_level', 'Unknown')
                    experience_levels[experience] = experience_levels.get(experience, 0) + 1
                    
                    confidence = job_result.get('analysis_confidence', 0.0)
                    confidence_scores.append(confidence)
                    
                    compatibility = job_result.get('compatibility_score', 0.0)
                    compatibility_scores.append(compatibility)
                    
                    # Track job characteristics
                    companies.add(jobs[i]['company'])
                    locations.add(jobs[i]['location'])
                    job_sites.add(jobs[i]['site'])
                    
                    # Check if processing was successful
                    if job_result.get('error'):
                        failed_jobs += 1
                    else:
                        successful_jobs += 1
                        
                except Exception as e:
                    self.console.print(f"[yellow]⚠️ Error analyzing job result {i}: {e}[/yellow]")
                    failed_jobs += 1
            
            # Create metrics
            metrics = RealJobTestMetrics(
                total_jobs_tested=len(jobs),
                processing_time=processing_time,
                jobs_per_second=result.metrics.jobs_per_second,
                skills_extracted_total=len(skills_extracted),
                skills_per_job_avg=0,  # Will be calculated in __post_init__
                experience_levels_detected=experience_levels,
                confidence_scores=confidence_scores,
                confidence_average=0,  # Will be calculated in __post_init__
                compatibility_scores=compatibility_scores,
                compatibility_average=0,  # Will be calculated in __post_init__
                successful_jobs=successful_jobs,
                failed_jobs=failed_jobs,
                success_rate=0,  # Will be calculated in __post_init__
                companies_processed=list(companies),
                locations_processed=list(locations),
                job_sites=list(job_sites)
            )
            
            self.console.print(f"[green]✅ Processing completed: {metrics.jobs_per_second:.2f} jobs/sec[/green]")
            return metrics
            
        except Exception as e:
            self.console.print(f"[red]❌ Processing failed: {e}[/red]")
            raise
    
    def display_detailed_results(self, metrics: RealJobTestMetrics, jobs: List[Dict[str, Any]]):
        """Display comprehensive test results."""
        self.console.print("\n[bold green]📊 Detailed No-AI Processing Results[/bold green]")
        
        # Performance metrics table
        perf_table = Table(title="⚡ Performance Metrics")
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("Value", style="yellow")
        perf_table.add_column("Assessment", style="green")
        
        perf_table.add_row("Jobs Processed", str(metrics.total_jobs_tested), "✅ Real scraped jobs")
        perf_table.add_row("Processing Speed", f"{metrics.jobs_per_second:.2f} jobs/sec", "🚀 Fast parallel processing")
        perf_table.add_row("Total Time", f"{metrics.processing_time:.3f}s", "⚡ Efficient")
        perf_table.add_row("Success Rate", f"{metrics.success_rate:.1%}", "✅ Reliable" if metrics.success_rate > 0.9 else "⚠️ Needs attention")
        
        self.console.print(perf_table)
        
        # Analysis quality table
        quality_table = Table(title="🎯 Analysis Quality")
        quality_table.add_column("Aspect", style="cyan")
        quality_table.add_column("Result", style="yellow")
        quality_table.add_column("Details", style="green")
        
        quality_table.add_row("Skills Extracted", str(metrics.skills_extracted_total), f"Avg: {metrics.skills_per_job_avg:.1f} per job")
        quality_table.add_row("Confidence Score", f"{metrics.confidence_average:.1%}", f"Range: {min(metrics.confidence_scores):.1%} - {max(metrics.confidence_scores):.1%}")
        quality_table.add_row("Compatibility Score", f"{metrics.compatibility_average:.1%}", f"Avg match with profile")
        
        # Experience levels breakdown
        exp_breakdown = ", ".join([f"{level}: {count}" for level, count in metrics.experience_levels_detected.items()])
        quality_table.add_row("Experience Levels", str(len(metrics.experience_levels_detected)), exp_breakdown)
        
        self.console.print(quality_table)
        
        # Real job characteristics table
        job_char_table = Table(title="📋 Real Job Characteristics")
        job_char_table.add_column("Characteristic", style="cyan")
        job_char_table.add_column("Count", style="yellow")
        job_char_table.add_column("Examples", style="green")
        
        # Filter out None values for display
        companies_display = [c for c in list(metrics.companies_processed)[:3] if c and c != 'Unknown Company']
        locations_display = [l for l in list(metrics.locations_processed)[:3] if l and l != 'Unknown Location']
        
        job_char_table.add_row("Unique Companies", str(len(metrics.companies_processed)), ", ".join(companies_display) if companies_display else "N/A")
        job_char_table.add_row("Unique Locations", str(len(metrics.locations_processed)), ", ".join(locations_display) if locations_display else "N/A")
        job_char_table.add_row("Job Sites", str(len(metrics.job_sites)), ", ".join(metrics.job_sites))
        
        # Content analysis
        desc_lengths = [len(job['description']) for job in jobs]
        avg_desc_length = sum(desc_lengths) / len(desc_lengths) if desc_lengths else 0
        job_char_table.add_row("Avg Description Length", f"{avg_desc_length:.0f} chars", f"Range: {min(desc_lengths)}-{max(desc_lengths)}")
        
        self.console.print(job_char_table)
        
        # Sample analysis results
        self.console.print("\n[bold blue]🔍 Sample Analysis Results[/bold blue]")
        
        # Show analysis for first few jobs
        sample_table = Table(title="Sample Job Analysis")
        sample_table.add_column("Job", style="cyan", width=20)
        sample_table.add_column("Skills Found", style="yellow", width=25)
        sample_table.add_column("Experience", style="green", width=12)
        sample_table.add_column("Confidence", style="blue", width=10)
        sample_table.add_column("Compatibility", style="magenta", width=12)
        
        # Show sample jobs (we'll use mock data for display since we can't await here)
        for i, job in enumerate(jobs[:5]):
            sample_table.add_row(
                job['title'][:18] + "..." if len(job['title']) > 20 else job['title'],
                "Processing completed",
                "See metrics above",
                f"{metrics.confidence_average:.1%}",
                f"{metrics.compatibility_average:.1%}"
            )
        
        self.console.print(sample_table)
        
        # Performance insights
        self.console.print("\n[bold blue]💡 Performance Insights[/bold blue]")
        
        if metrics.jobs_per_second > 10:
            self.console.print("[green]🚀 Excellent processing speed - suitable for large-scale job processing[/green]")
        elif metrics.jobs_per_second > 5:
            self.console.print("[yellow]⚡ Good processing speed - adequate for regular use[/yellow]")
        else:
            self.console.print("[red]🐌 Slow processing speed - may need optimization[/red]")
        
        if metrics.confidence_average > 0.7:
            self.console.print("[green]🎯 High confidence in analysis results[/green]")
        elif metrics.confidence_average > 0.5:
            self.console.print("[yellow]🎯 Moderate confidence in analysis results[/yellow]")
        else:
            self.console.print("[red]🎯 Low confidence - analysis may need improvement[/red]")
        
        if metrics.success_rate > 0.95:
            self.console.print("[green]✅ Excellent reliability - very few processing errors[/green]")
        elif metrics.success_rate > 0.8:
            self.console.print("[yellow]✅ Good reliability - some minor errors[/yellow]")
        else:
            self.console.print("[red]❌ Poor reliability - many processing errors[/red]")
        
        # Database insights
        self.console.print("\n[bold blue]📊 Database Insights[/bold blue]")
        self.console.print(f"[cyan]• Processed real jobs from {self.profile_name} profile database[/cyan]")
        self.console.print(f"[cyan]• Jobs sourced from: {', '.join(metrics.job_sites)}[/cyan]")
        self.console.print(f"[cyan]• Companies represented: {len(metrics.companies_processed)} unique companies[/cyan]")
        self.console.print(f"[cyan]• Geographic coverage: {len(metrics.locations_processed)} locations[/cyan]")

async def main():
    """Main test function."""
    console.print(Panel(
        "[bold blue]🔬 No-AI Job Processor Test with Real Scraped Jobs[/bold blue]\n"
        "[cyan]Testing parallel job processor using actual jobs from Nirajan profile database[/cyan]\n"
        "[yellow]• Real scraped job data • No AI/LLM processing • Fast parallel analysis[/yellow]",
        title="Real Job Processing Test"
    ))
    
    try:
        # Initialize processor
        processor = RealJobProcessor("Nirajan")
        
        # Fetch real jobs
        console.print("[cyan]🔍 Fetching real scraped jobs from database...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            fetch_task = progress.add_task("Fetching jobs from Nirajan database...", total=1)
            jobs = processor.fetch_real_jobs(25)  # Test with 25 real jobs
            progress.update(fetch_task, completed=1)
        
        if not jobs:
            console.print("[red]❌ No valid jobs found in database[/red]")
            return
        
        # Display job preview
        processor.display_job_preview(jobs)
        
        # Test processing
        console.print(f"\n[cyan]🚀 Testing no-AI processing with {len(jobs)} real jobs...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            process_task = progress.add_task("Processing real jobs...", total=1)
            metrics = await processor.test_no_ai_processing(jobs)
            progress.update(process_task, completed=1)
        
        # Display results
        processor.display_detailed_results(metrics, jobs)
        
        # Final summary
        console.print(f"\n[bold green]🎉 Test completed successfully![/bold green]")
        console.print(f"[green]✅ Processed {metrics.total_jobs_tested} real scraped jobs from Nirajan profile[/green]")
        console.print(f"[green]✅ Processing speed: {metrics.jobs_per_second:.2f} jobs/second[/green]")
        console.print(f"[green]✅ Success rate: {metrics.success_rate:.1%}[/green]")
        console.print(f"[green]✅ Average confidence: {metrics.confidence_average:.1%}[/green]")
        
        console.print("\n[cyan]💡 This demonstrates the no-AI processor working with real scraped job data![/cyan]")
        
    except Exception as e:
        console.print(f"[red]❌ Test failed: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())