"""
Comprehensive CPU vs GPU Job Processing Benchmark
Compares extraction quality and performance between no-AI (CPU) and AI (GPU) processors
using real scraped jobs from Nirajan profile database.
"""

import asyncio
import time
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.columns import Columns
from rich.text import Text

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

console = Console()

@dataclass
class ExtractionComparison:
    """Detailed comparison of extraction results."""
    job_id: str
    job_title: str
    
    # CPU Results
    cpu_skills: List[str]
    cpu_experience: str
    cpu_salary: Dict[str, Any]
    cpu_confidence: float
    cpu_compatibility: float
    cpu_processing_time: float
    
    # GPU Results  
    gpu_skills: List[str]
    gpu_experience: str
    gpu_salary: Dict[str, Any]
    gpu_confidence: float
    gpu_compatibility: float
    gpu_processing_time: float
    
    # Comparison metrics
    skills_overlap: float
    experience_match: bool
    salary_match: bool
    confidence_diff: float
    compatibility_diff: float

@dataclass
class BenchmarkResults:
    """Overall benchmark results."""
    total_jobs: int
    
    # Performance metrics
    cpu_total_time: float
    gpu_total_time: float
    cpu_jobs_per_sec: float
    gpu_jobs_per_sec: float
    
    # Quality metrics
    cpu_avg_skills: float
    gpu_avg_skills: float
    cpu_avg_confidence: float
    gpu_avg_confidence: float
    cpu_avg_compatibility: float
    gpu_avg_compatibility: float
    
    # Comparison metrics
    avg_skills_overlap: float
    experience_agreement: float
    salary_agreement: float
    
    # Detailed comparisons
    extraction_comparisons: List[ExtractionComparison]

class CPUvsGPUBenchmark:
    """Comprehensive benchmark comparing CPU and GPU job processing."""
    
    def __init__(self, profile_name: str = "Nirajan"):
        self.profile_name = profile_name
        self.console = Console()
        
        # Initialize database
        try:
            from src.core.job_database import get_job_db
            self.db = get_job_db(profile_name)
            self.console.print(f"[green]✅ Connected to {profile_name} profile database[/green]")
        except Exception as e:
            self.console.print(f"[red]❌ Failed to connect to database: {e}[/red]")
            raise
        
        # Initialize processors
        self._initialize_processors()
    
    def _initialize_processors(self):
        """Initialize both CPU and GPU processors."""
        try:
            # Initialize CPU processor (no-AI)
            from src.ai.parallel_job_processor import get_parallel_processor
            self.cpu_processor = get_parallel_processor(max_workers=8, max_concurrent=16)
            self.console.print("[green]✅ CPU processor initialized[/green]")
        except Exception as e:
            self.console.print(f"[red]❌ Failed to initialize CPU processor: {e}[/red]")
            raise
        
        try:
            # Initialize GPU processor (AI)
            from src.ai.gpu_job_processor import get_gpu_processor
            self.gpu_processor = get_gpu_processor()
            self.console.print("[green]✅ GPU processor initialized[/green]")
        except Exception as e:
            self.console.print(f"[yellow]⚠️ GPU processor not available: {e}[/yellow]")
            self.gpu_processor = None
    
    def fetch_test_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch real jobs for testing."""
        self.console.print(f"[cyan]🔍 Fetching {limit} real jobs for benchmark...[/cyan]")
        
        try:
            all_jobs = self.db.get_all_jobs()
            
            if not all_jobs:
                self.console.print("[red]❌ No jobs found in database[/red]")
                return []
            
            # Filter jobs with meaningful content
            valid_jobs = []
            for job in all_jobs:
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
                
                # Only include jobs with substantial content
                if len(processor_job['description']) > 100:
                    valid_jobs.append(processor_job)
                
                if len(valid_jobs) >= limit:
                    break
            
            self.console.print(f"[green]✅ Found {len(valid_jobs)} valid jobs for benchmark[/green]")
            return valid_jobs
            
        except Exception as e:
            self.console.print(f"[red]❌ Error fetching jobs: {e}[/red]")
            return []
    
    async def run_cpu_processing(self, jobs: List[Dict[str, Any]]) -> Tuple[List[Dict], float]:
        """Run CPU processing and return results with timing."""
        self.console.print("[cyan]🔄 Running CPU (No-AI) processing...[/cyan]")
        
        start_time = time.time()
        result = await self.cpu_processor.process_jobs_async(jobs)
        processing_time = time.time() - start_time
        
        return result.job_results, processing_time
    
    async def run_gpu_processing(self, jobs: List[Dict[str, Any]]) -> Tuple[List[Dict], float]:
        """Run GPU processing and return results with timing."""
        if not self.gpu_processor:
            self.console.print("[yellow]⚠️ GPU processor not available, skipping GPU processing[/yellow]")
            return [], 0.0
        
        self.console.print("[cyan]🔄 Running GPU (AI) processing...[/cyan]")
        
        start_time = time.time()
        result = await self.gpu_processor.process_jobs_gpu_async(jobs)
        processing_time = time.time() - start_time
        
        return result.job_results, processing_time
    
    def compare_extractions(self, jobs: List[Dict], cpu_results: List[Dict], 
                          gpu_results: List[Dict]) -> List[ExtractionComparison]:
        """Compare extraction results between CPU and GPU processing."""
        comparisons = []
        
        for i, (job, cpu_result, gpu_result) in enumerate(zip(jobs, cpu_results, gpu_results)):
            # Extract data from results
            cpu_skills = cpu_result.get('required_skills', [])
            gpu_skills = gpu_result.get('required_skills', [])
            
            # Calculate skills overlap
            cpu_skills_set = set(cpu_skills)
            gpu_skills_set = set(gpu_skills)
            if cpu_skills_set or gpu_skills_set:
                skills_overlap = len(cpu_skills_set & gpu_skills_set) / len(cpu_skills_set | gpu_skills_set)
            else:
                skills_overlap = 1.0
            
            # Compare experience levels
            cpu_exp = cpu_result.get('experience_level', 'Unknown')
            gpu_exp = gpu_result.get('experience_level', 'Unknown')
            experience_match = cpu_exp == gpu_exp
            
            # Compare salary extraction
            cpu_salary = cpu_result.get('salary_info', {})
            gpu_salary = gpu_result.get('salary_info', {})
            salary_match = cpu_salary.get('salary_mentioned', False) == gpu_salary.get('salary_mentioned', False)
            
            # Calculate differences
            cpu_conf = cpu_result.get('analysis_confidence', 0.0)
            gpu_conf = gpu_result.get('analysis_confidence', 0.0)
            confidence_diff = gpu_conf - cpu_conf
            
            cpu_compat = cpu_result.get('compatibility_score', 0.0)
            gpu_compat = gpu_result.get('compatibility_score', 0.0)
            compatibility_diff = gpu_compat - cpu_compat
            
            comparison = ExtractionComparison(
                job_id=job['id'],
                job_title=job['title'],
                cpu_skills=cpu_skills,
                cpu_experience=cpu_exp,
                cpu_salary=cpu_salary,
                cpu_confidence=cpu_conf,
                cpu_compatibility=cpu_compat,
                cpu_processing_time=cpu_result.get('processing_time', 0.0),
                gpu_skills=gpu_skills,
                gpu_experience=gpu_exp,
                gpu_salary=gpu_salary,
                gpu_confidence=gpu_conf,
                gpu_compatibility=gpu_compat,
                gpu_processing_time=gpu_result.get('inference_time', 0.0),
                skills_overlap=skills_overlap,
                experience_match=experience_match,
                salary_match=salary_match,
                confidence_diff=confidence_diff,
                compatibility_diff=compatibility_diff
            )
            
            comparisons.append(comparison)
        
        return comparisons
    
    def display_detailed_comparison(self, comparisons: List[ExtractionComparison]):
        """Display detailed side-by-side comparison of extraction results."""
        self.console.print("\n[bold blue]🔍 Detailed Extraction Comparison[/bold blue]")
        
        for i, comp in enumerate(comparisons[:5]):  # Show first 5 jobs
            self.console.print(f"\n[bold cyan]Job {i+1}: {comp.job_title[:50]}...[/bold cyan]")
            
            # Create side-by-side comparison table
            comparison_table = Table(title=f"Extraction Results Comparison")
            comparison_table.add_column("Aspect", style="cyan", width=20)
            comparison_table.add_column("CPU (No-AI)", style="yellow", width=30)
            comparison_table.add_column("GPU (AI)", style="green", width=30)
            comparison_table.add_column("Match/Diff", style="magenta", width=15)
            
            # Skills comparison
            cpu_skills_str = ", ".join(comp.cpu_skills[:4])
            if len(comp.cpu_skills) > 4:
                cpu_skills_str += f" (+{len(comp.cpu_skills)-4})"
            
            gpu_skills_str = ", ".join(comp.gpu_skills[:4])
            if len(comp.gpu_skills) > 4:
                gpu_skills_str += f" (+{len(comp.gpu_skills)-4})"
            
            comparison_table.add_row(
                "Skills Extracted",
                cpu_skills_str or "None",
                gpu_skills_str or "None",
                f"{comp.skills_overlap:.1%} overlap"
            )
            
            # Experience level
            exp_match_icon = "✅" if comp.experience_match else "❌"
            comparison_table.add_row(
                "Experience Level",
                comp.cpu_experience,
                comp.gpu_experience,
                f"{exp_match_icon} {'Match' if comp.experience_match else 'Different'}"
            )
            
            # Salary extraction
            cpu_salary_str = "Yes" if comp.cpu_salary.get('salary_mentioned', False) else "No"
            gpu_salary_str = "Yes" if comp.gpu_salary.get('salary_mentioned', False) else "No"
            salary_match_icon = "✅" if comp.salary_match else "❌"
            
            comparison_table.add_row(
                "Salary Detected",
                cpu_salary_str,
                gpu_salary_str,
                f"{salary_match_icon} {'Match' if comp.salary_match else 'Different'}"
            )
            
            # Confidence scores
            comparison_table.add_row(
                "Confidence",
                f"{comp.cpu_confidence:.1%}",
                f"{comp.gpu_confidence:.1%}",
                f"{comp.confidence_diff:+.1%}"
            )
            
            # Compatibility scores
            comparison_table.add_row(
                "Compatibility",
                f"{comp.cpu_compatibility:.1%}",
                f"{comp.gpu_compatibility:.1%}",
                f"{comp.compatibility_diff:+.1%}"
            )
            
            self.console.print(comparison_table)
    
    def display_aggregate_results(self, results: BenchmarkResults):
        """Display aggregate benchmark results."""
        self.console.print("\n[bold green]📊 Aggregate Benchmark Results[/bold green]")
        
        # Performance comparison
        perf_table = Table(title="⚡ Performance Comparison")
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("CPU (No-AI)", style="yellow")
        perf_table.add_column("GPU (AI)", style="green")
        perf_table.add_column("Winner", style="magenta")
        
        # Processing speed
        speed_winner = "CPU" if results.cpu_jobs_per_sec > results.gpu_jobs_per_sec else "GPU"
        perf_table.add_row(
            "Jobs per Second",
            f"{results.cpu_jobs_per_sec:.1f}",
            f"{results.gpu_jobs_per_sec:.1f}",
            f"🏆 {speed_winner}"
        )
        
        # Total processing time
        time_winner = "CPU" if results.cpu_total_time < results.gpu_total_time else "GPU"
        perf_table.add_row(
            "Total Time",
            f"{results.cpu_total_time:.3f}s",
            f"{results.gpu_total_time:.3f}s",
            f"🏆 {time_winner}"
        )
        
        self.console.print(perf_table)
        
        # Quality comparison
        quality_table = Table(title="🎯 Extraction Quality Comparison")
        quality_table.add_column("Metric", style="cyan")
        quality_table.add_column("CPU (No-AI)", style="yellow")
        quality_table.add_column("GPU (AI)", style="green")
        quality_table.add_column("Difference", style="magenta")
        
        quality_table.add_row(
            "Avg Skills per Job",
            f"{results.cpu_avg_skills:.1f}",
            f"{results.gpu_avg_skills:.1f}",
            f"{results.gpu_avg_skills - results.cpu_avg_skills:+.1f}"
        )
        
        quality_table.add_row(
            "Avg Confidence",
            f"{results.cpu_avg_confidence:.1%}",
            f"{results.gpu_avg_confidence:.1%}",
            f"{results.gpu_avg_confidence - results.cpu_avg_confidence:+.1%}"
        )
        
        quality_table.add_row(
            "Avg Compatibility",
            f"{results.cpu_avg_compatibility:.1%}",
            f"{results.gpu_avg_compatibility:.1%}",
            f"{results.gpu_avg_compatibility - results.cpu_avg_compatibility:+.1%}"
        )
        
        self.console.print(quality_table)
        
        # Agreement metrics
        agreement_table = Table(title="🤝 Agreement Between Methods")
        agreement_table.add_column("Aspect", style="cyan")
        agreement_table.add_column("Agreement Rate", style="yellow")
        agreement_table.add_column("Assessment", style="green")
        
        agreement_table.add_row(
            "Skills Overlap",
            f"{results.avg_skills_overlap:.1%}",
            "High" if results.avg_skills_overlap > 0.7 else "Moderate" if results.avg_skills_overlap > 0.5 else "Low"
        )
        
        agreement_table.add_row(
            "Experience Level",
            f"{results.experience_agreement:.1%}",
            "High" if results.experience_agreement > 0.8 else "Moderate" if results.experience_agreement > 0.6 else "Low"
        )
        
        agreement_table.add_row(
            "Salary Detection",
            f"{results.salary_agreement:.1%}",
            "High" if results.salary_agreement > 0.8 else "Moderate" if results.salary_agreement > 0.6 else "Low"
        )
        
        self.console.print(agreement_table)
    
    def generate_recommendations(self, results: BenchmarkResults):
        """Generate recommendations based on benchmark results."""
        self.console.print("\n[bold blue]💡 Recommendations[/bold blue]")
        
        # Speed recommendation
        if results.cpu_jobs_per_sec > results.gpu_jobs_per_sec * 1.5:
            self.console.print("[green]🚀 For SPEED: Use CPU (No-AI) processing[/green]")
            self.console.print(f"[dim]   - {results.cpu_jobs_per_sec/results.gpu_jobs_per_sec:.1f}x faster than GPU[/dim]")
        elif results.gpu_jobs_per_sec > results.cpu_jobs_per_sec * 1.2:
            self.console.print("[green]🚀 For SPEED: Use GPU (AI) processing[/green]")
            self.console.print(f"[dim]   - {results.gpu_jobs_per_sec/results.cpu_jobs_per_sec:.1f}x faster than CPU[/dim]")
        else:
            self.console.print("[yellow]⚡ SPEED: Both methods have similar performance[/yellow]")
        
        # Quality recommendation
        if results.gpu_avg_skills > results.cpu_avg_skills * 1.2:
            self.console.print("[green]🎯 For QUALITY: Use GPU (AI) processing[/green]")
            self.console.print(f"[dim]   - Extracts {results.gpu_avg_skills - results.cpu_avg_skills:.1f} more skills per job[/dim]")
        elif results.cpu_avg_skills > results.gpu_avg_skills * 1.1:
            self.console.print("[green]🎯 For QUALITY: Use CPU (No-AI) processing[/green]")
            self.console.print(f"[dim]   - More consistent skill extraction[/dim]")
        else:
            self.console.print("[yellow]🎯 QUALITY: Both methods extract similar information[/yellow]")
        
        # Agreement assessment
        if results.avg_skills_overlap > 0.8 and results.experience_agreement > 0.8:
            self.console.print("[green]✅ HIGH AGREEMENT: Both methods produce very similar results[/green]")
            self.console.print("[green]   → CPU processing is sufficient for most use cases[/green]")
        elif results.avg_skills_overlap > 0.6:
            self.console.print("[yellow]⚠️ MODERATE AGREEMENT: Some differences in extraction quality[/yellow]")
            self.console.print("[yellow]   → Consider GPU for higher accuracy requirements[/yellow]")
        else:
            self.console.print("[red]❌ LOW AGREEMENT: Significant differences between methods[/red]")
            self.console.print("[red]   → GPU processing recommended for better accuracy[/red]")
        
        # Final recommendation
        self.console.print("\n[bold cyan]🎯 Final Recommendation:[/bold cyan]")
        
        if (results.cpu_jobs_per_sec > results.gpu_jobs_per_sec and 
            results.avg_skills_overlap > 0.7):
            self.console.print("[green]✅ Use CPU (No-AI) processing[/green]")
            self.console.print("[green]   - Faster processing with similar quality[/green]")
            self.console.print("[green]   - Lower resource requirements[/green]")
            self.console.print("[green]   - Simpler deployment[/green]")
        elif results.gpu_avg_skills > results.cpu_avg_skills * 1.3:
            self.console.print("[green]✅ Use GPU (AI) processing[/green]")
            self.console.print("[green]   - Significantly better extraction quality[/green]")
            self.console.print("[green]   - Worth the additional complexity[/green]")
        else:
            self.console.print("[yellow]⚖�� Both methods are viable[/yellow]")
            self.console.print("[yellow]   - Choose based on your priorities:[/yellow]")
            self.console.print("[yellow]   - Speed & Simplicity → CPU[/yellow]")
            self.console.print("[yellow]   - Maximum Accuracy → GPU[/yellow]")
    
    async def run_benchmark(self, num_jobs: int = 10) -> BenchmarkResults:
        """Run the complete benchmark."""
        self.console.print(Panel(
            "[bold blue]🏁 CPU vs GPU Job Processing Benchmark[/bold blue]\n"
            "[cyan]Comparing extraction quality and performance[/cyan]\n"
            f"[yellow]Testing with {num_jobs} real jobs from {self.profile_name} database[/yellow]",
            title="Comprehensive Benchmark"
        ))
        
        # Fetch test jobs
        jobs = self.fetch_test_jobs(num_jobs)
        if not jobs:
            raise ValueError("No jobs available for testing")
        
        # Run CPU processing
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            cpu_task = progress.add_task("Running CPU processing...", total=1)
            cpu_results, cpu_time = await self.run_cpu_processing(jobs)
            progress.update(cpu_task, completed=1)
            
            gpu_task = progress.add_task("Running GPU processing...", total=1)
            gpu_results, gpu_time = await self.run_gpu_processing(jobs)
            progress.update(gpu_task, completed=1)
        
        if not gpu_results:
            self.console.print("[red]❌ GPU processing failed, cannot complete benchmark[/red]")
            return None
        
        # Compare results
        comparisons = self.compare_extractions(jobs, cpu_results, gpu_results)
        
        # Calculate aggregate metrics
        cpu_skills_counts = [len(r.get('required_skills', [])) for r in cpu_results]
        gpu_skills_counts = [len(r.get('required_skills', [])) for r in gpu_results]
        
        cpu_confidences = [r.get('analysis_confidence', 0.0) for r in cpu_results]
        gpu_confidences = [r.get('analysis_confidence', 0.0) for r in gpu_results]
        
        cpu_compatibilities = [r.get('compatibility_score', 0.0) for r in cpu_results]
        gpu_compatibilities = [r.get('compatibility_score', 0.0) for r in gpu_results]
        
        results = BenchmarkResults(
            total_jobs=len(jobs),
            cpu_total_time=cpu_time,
            gpu_total_time=gpu_time,
            cpu_jobs_per_sec=len(jobs) / cpu_time if cpu_time > 0 else 0,
            gpu_jobs_per_sec=len(jobs) / gpu_time if gpu_time > 0 else 0,
            cpu_avg_skills=sum(cpu_skills_counts) / len(cpu_skills_counts) if cpu_skills_counts else 0,
            gpu_avg_skills=sum(gpu_skills_counts) / len(gpu_skills_counts) if gpu_skills_counts else 0,
            cpu_avg_confidence=sum(cpu_confidences) / len(cpu_confidences) if cpu_confidences else 0,
            gpu_avg_confidence=sum(gpu_confidences) / len(gpu_confidences) if gpu_confidences else 0,
            cpu_avg_compatibility=sum(cpu_compatibilities) / len(cpu_compatibilities) if cpu_compatibilities else 0,
            gpu_avg_compatibility=sum(gpu_compatibilities) / len(gpu_compatibilities) if gpu_compatibilities else 0,
            avg_skills_overlap=sum(c.skills_overlap for c in comparisons) / len(comparisons) if comparisons else 0,
            experience_agreement=sum(1 for c in comparisons if c.experience_match) / len(comparisons) if comparisons else 0,
            salary_agreement=sum(1 for c in comparisons if c.salary_match) / len(comparisons) if comparisons else 0,
            extraction_comparisons=comparisons
        )
        
        return results

async def main():
    """Main benchmark function."""
    try:
        benchmark = CPUvsGPUBenchmark("Nirajan")
        
        # Run benchmark with 10 jobs
        results = await benchmark.run_benchmark(10)
        
        if results:
            # Display detailed comparison
            benchmark.display_detailed_comparison(results.extraction_comparisons)
            
            # Display aggregate results
            benchmark.display_aggregate_results(results)
            
            # Generate recommendations
            benchmark.generate_recommendations(results)
            
            console.print(f"\n[bold green]🎉 Benchmark completed![/bold green]")
            console.print(f"[green]✅ Tested {results.total_jobs} real jobs from Nirajan database[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Benchmark failed: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())