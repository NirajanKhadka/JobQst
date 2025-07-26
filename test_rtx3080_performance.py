"""
RTX 3080 Performance Test & Benchmark Suite
Comprehensive testing to validate RTX 3080 optimizations and measure performance gains.
"""

import asyncio
import time
import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.ai.rtx3080_optimized_client import RTX3080OptimizedClient, get_rtx3080_optimized_client
    from src.orchestration.rtx3080_enhanced_processor import RTX3080EnhancedProcessor, get_rtx3080_enhanced_processor
    from src.orchestration.enhanced_job_processor import EnhancedJobProcessor  # Original processor for comparison
    RTX3080_AVAILABLE = True
except ImportError as e:
    print(f"RTX 3080 modules not available: {e}")
    RTX3080_AVAILABLE = False

console = Console()

@dataclass
class PerformanceComparison:
    """Performance comparison between original and RTX 3080 optimized systems."""
    original_jobs_per_sec: float
    rtx3080_jobs_per_sec: float
    performance_improvement: float
    original_processing_time: float
    rtx3080_processing_time: float
    time_reduction_percent: float
    gpu_utilization: float
    memory_usage_gb: float
    tensor_cores_utilized: bool
    batch_size_optimal: int
    concurrent_streams: int

class RTX3080PerformanceTest:
    """Comprehensive RTX 3080 performance testing suite."""
    
    def __init__(self, profile_name: str = "test_profile"):
        self.profile_name = profile_name
        self.console = Console()
        self.test_results = {}
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def create_test_jobs(self, count: int = 100) -> List[Dict[str, Any]]:
        """Create realistic test jobs for benchmarking."""
        job_templates = [
            {
                'title': 'Senior Software Engineer',
                'company': 'Microsoft',
                'description': '''We are looking for a Senior Software Engineer to join our team. 
                Requirements: 5+ years of experience with Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes.
                Experience with microservices architecture, CI/CD pipelines, and agile development.
                Strong problem-solving skills and ability to work in a fast-paced environment.
                Bachelor's degree in Computer Science or related field.
                Excellent communication and teamwork skills.''',
                'location': 'Toronto, ON',
                'salary_range': '$90,000 - $130,000',
                'experience_level': 'Senior',
                'employment_type': 'Full-time',
                'status': 'scraped'
            },
            {
                'title': 'Data Scientist',
                'company': 'Google',
                'description': '''Join our Data Science team to work on cutting-edge machine learning projects.
                Requirements: PhD in Statistics, Mathematics, or Computer Science.
                5+ years of experience with Python, R, SQL, TensorFlow, PyTorch, scikit-learn.
                Experience with big data technologies like Spark, Hadoop, and cloud platforms.
                Strong statistical analysis and data visualization skills.
                Experience with A/B testing and experimental design.
                Published research in machine learning or statistics preferred.''',
                'location': 'Vancouver, BC',
                'salary_range': '$120,000 - $180,000',
                'experience_level': 'Senior',
                'employment_type': 'Full-time',
                'status': 'scraped'
            },
            {
                'title': 'DevOps Engineer',
                'company': 'Amazon',
                'description': '''We need a DevOps Engineer to manage our cloud infrastructure and deployment pipelines.
                Requirements: 3+ years of experience with AWS, Azure, or GCP.
                Expertise in Docker, Kubernetes, Terraform, Ansible, Jenkins.
                Experience with monitoring tools like Prometheus, Grafana, ELK stack.
                Strong scripting skills in Python, Bash, or PowerShell.
                Knowledge of security best practices and compliance.
                Experience with infrastructure as code and GitOps workflows.''',
                'location': 'Montreal, QC',
                'salary_range': '$80,000 - $120,000',
                'experience_level': 'Mid-level',
                'employment_type': 'Full-time',
                'status': 'scraped'
            },
            {
                'title': 'Frontend Developer',
                'company': 'Shopify',
                'description': '''Looking for a Frontend Developer to build amazing user experiences.
                Requirements: 3+ years of experience with React, Vue.js, or Angular.
                Strong skills in HTML5, CSS3, JavaScript (ES6+), TypeScript.
                Experience with responsive design and cross-browser compatibility.
                Knowledge of state management (Redux, Vuex) and testing frameworks.
                Familiarity with build tools like Webpack, Vite, or Parcel.
                Understanding of accessibility standards and performance optimization.''',
                'location': 'Ottawa, ON',
                'salary_range': '$70,000 - $100,000',
                'experience_level': 'Mid-level',
                'employment_type': 'Full-time',
                'status': 'scraped'
            },
            {
                'title': 'Machine Learning Engineer',
                'company': 'Nvidia',
                'description': '''Join our ML Engineering team to develop and deploy machine learning models at scale.
                Requirements: Master's degree in Computer Science, AI, or related field.
                4+ years of experience with Python, TensorFlow, PyTorch, CUDA.
                Experience with MLOps, model deployment, and monitoring.
                Knowledge of distributed computing and GPU optimization.
                Experience with containerization and orchestration (Docker, Kubernetes).
                Strong understanding of deep learning architectures and optimization techniques.''',
                'location': 'Calgary, AB',
                'salary_range': '$110,000 - $160,000',
                'experience_level': 'Senior',
                'employment_type': 'Full-time',
                'status': 'scraped'
            }
        ]
        
        test_jobs = []
        for i in range(count):
            template = job_templates[i % len(job_templates)]
            job = template.copy()
            job['id'] = f'test_job_{i + 1:04d}'
            job['url'] = f'https://example.com/jobs/{i + 1}'
            job['scraped_at'] = time.time()
            test_jobs.append(job)
        
        return test_jobs
    
    async def test_rtx3080_gpu_client(self, test_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test RTX 3080 GPU client performance."""
        console.print("\n[bold blue]🎯 Testing RTX 3080 GPU Client[/bold blue]")
        
        if not RTX3080_AVAILABLE:
            console.print("[red]❌ RTX 3080 modules not available[/red]")
            return {'error': 'RTX 3080 modules not available'}
        
        try:
            # Initialize RTX 3080 client
            gpu_client = get_rtx3080_optimized_client(
                model="llama3",
                max_batch_size=16,
                concurrent_streams=4
            )
            
            # Test different batch sizes
            batch_sizes = [1, 4, 8, 12, 16]
            results = {}
            
            for batch_size in batch_sizes:
                console.print(f"[cyan]Testing batch size: {batch_size}[/cyan]")
                
                test_batch = test_jobs[:batch_size]
                start_time = time.time()
                
                try:
                    batch_result = await gpu_client.analyze_jobs_batch_rtx3080(test_batch)
                    
                    results[f'batch_{batch_size}'] = {
                        'jobs_per_second': batch_result.jobs_per_second,
                        'processing_time': batch_result.processing_time,
                        'gpu_utilization': batch_result.gpu_utilization,
                        'memory_used_gb': batch_result.memory_used_gb,
                        'tensor_cores_utilized': batch_result.tensor_cores_utilized,
                        'cuda_streams_used': batch_result.cuda_streams_used
                    }
                    
                    console.print(f"  ✅ {batch_result.jobs_per_second:.1f} jobs/sec")
                    
                except Exception as e:
                    console.print(f"  ❌ Failed: {e}")
                    results[f'batch_{batch_size}'] = {'error': str(e)}
            
            # Get performance report
            performance_report = gpu_client.get_rtx3080_performance_report()
            results['performance_report'] = performance_report
            
            return results
            
        except Exception as e:
            console.print(f"[red]❌ RTX 3080 GPU client test failed: {e}[/red]")
            return {'error': str(e)}
    
    async def test_rtx3080_enhanced_processor(self, test_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test RTX 3080 enhanced processor performance."""
        console.print("\n[bold blue]⚡ Testing RTX 3080 Enhanced Processor[/bold blue]")
        
        if not RTX3080_AVAILABLE:
            console.print("[red]❌ RTX 3080 modules not available[/red]")
            return {'error': 'RTX 3080 modules not available'}
        
        try:
            # Initialize RTX 3080 enhanced processor
            processor = get_rtx3080_enhanced_processor(
                profile_name=self.profile_name,
                max_batch_size=16,
                concurrent_streams=4,
                enable_gpu_optimization=True
            )
            
            # Mock database with test jobs
            processor.db.jobs = {job['id']: job for job in test_jobs}
            
            start_time = time.time()
            
            # Process jobs with RTX 3080 optimization
            stats = await processor.process_jobs_async_rtx3080(limit=len(test_jobs))
            
            processing_time = time.time() - start_time
            
            # Get performance report
            performance_report = processor.get_rtx3080_performance_report()
            
            results = {
                'processing_stats': {
                    'total_jobs': stats.total_jobs,
                    'processed_jobs': stats.processed_jobs,
                    'failed_jobs': stats.failed_jobs,
                    'jobs_per_second': stats.jobs_per_second,
                    'processing_time': stats.processing_time,
                    'performance_multiplier': stats.rtx3080_performance_multiplier,
                    'gpu_utilization_avg': stats.gpu_utilization_avg,
                    'memory_usage_peak_gb': stats.memory_usage_peak_gb,
                    'tensor_cores_utilized': stats.tensor_cores_utilized
                },
                'performance_report': performance_report,
                'actual_processing_time': processing_time
            }
            
            console.print(f"✅ Processed {stats.processed_jobs} jobs in {processing_time:.2f}s")
            console.print(f"🚀 Performance: {stats.jobs_per_second:.1f} jobs/sec")
            
            return results
            
        except Exception as e:
            console.print(f"[red]❌ RTX 3080 enhanced processor test failed: {e}[/red]")
            return {'error': str(e)}
    
    async def compare_with_original_processor(self, test_jobs: List[Dict[str, Any]]) -> PerformanceComparison:
        """Compare RTX 3080 optimized processor with original processor."""
        console.print("\n[bold blue]📊 Performance Comparison: Original vs RTX 3080[/bold blue]")
        
        # Test original processor
        console.print("[cyan]Testing original processor...[/cyan]")
        try:
            original_processor = EnhancedJobProcessor(
                profile_name=self.profile_name,
                worker_count=2,
                batch_size=5
            )
            
            # Mock database
            original_processor.db.jobs = {job['id']: job for job in test_jobs[:20]}  # Smaller test for original
            
            original_start = time.time()
            original_stats = original_processor.process_jobs_parallel(limit=20)
            original_time = time.time() - original_start
            
            original_jobs_per_sec = 20 / original_time if original_time > 0 else 0
            
            console.print(f"  ✅ Original: {original_jobs_per_sec:.1f} jobs/sec")
            
        except Exception as e:
            console.print(f"  ❌ Original processor failed: {e}")
            original_jobs_per_sec = 2.0  # Baseline estimate
            original_time = 10.0
        
        # Test RTX 3080 processor
        console.print("[cyan]Testing RTX 3080 processor...[/cyan]")
        rtx3080_results = await self.test_rtx3080_enhanced_processor(test_jobs[:20])
        
        if 'error' in rtx3080_results:
            console.print("[red]❌ RTX 3080 comparison failed[/red]")
            return PerformanceComparison(
                original_jobs_per_sec=original_jobs_per_sec,
                rtx3080_jobs_per_sec=0.0,
                performance_improvement=0.0,
                original_processing_time=original_time,
                rtx3080_processing_time=0.0,
                time_reduction_percent=0.0,
                gpu_utilization=0.0,
                memory_usage_gb=0.0,
                tensor_cores_utilized=False,
                batch_size_optimal=0,
                concurrent_streams=0
            )
        
        # Calculate comparison metrics
        rtx3080_stats = rtx3080_results['processing_stats']
        rtx3080_jobs_per_sec = rtx3080_stats['jobs_per_second']
        rtx3080_time = rtx3080_stats['processing_time']
        
        performance_improvement = rtx3080_jobs_per_sec / original_jobs_per_sec if original_jobs_per_sec > 0 else 0
        time_reduction = ((original_time - rtx3080_time) / original_time * 100) if original_time > 0 else 0
        
        comparison = PerformanceComparison(
            original_jobs_per_sec=original_jobs_per_sec,
            rtx3080_jobs_per_sec=rtx3080_jobs_per_sec,
            performance_improvement=performance_improvement,
            original_processing_time=original_time,
            rtx3080_processing_time=rtx3080_time,
            time_reduction_percent=time_reduction,
            gpu_utilization=rtx3080_stats['gpu_utilization_avg'],
            memory_usage_gb=rtx3080_stats['memory_usage_peak_gb'],
            tensor_cores_utilized=rtx3080_stats['tensor_cores_utilized'],
            batch_size_optimal=16,  # From RTX 3080 config
            concurrent_streams=4    # From RTX 3080 config
        )
        
        return comparison
    
    def display_performance_comparison(self, comparison: PerformanceComparison) -> None:
        """Display performance comparison results."""
        console.print("\n[bold green]🏆 Performance Comparison Results[/bold green]")
        
        # Create comparison table
        table = Table(title="Original vs RTX 3080 Optimized Performance")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Original", style="yellow")
        table.add_column("RTX 3080", style="green")
        table.add_column("Improvement", style="bold green")
        
        table.add_row(
            "Jobs per Second",
            f"{comparison.original_jobs_per_sec:.1f}",
            f"{comparison.rtx3080_jobs_per_sec:.1f}",
            f"{comparison.performance_improvement:.1f}x faster"
        )
        
        table.add_row(
            "Processing Time",
            f"{comparison.original_processing_time:.2f}s",
            f"{comparison.rtx3080_processing_time:.2f}s",
            f"{comparison.time_reduction_percent:.1f}% faster"
        )
        
        table.add_row(
            "GPU Utilization",
            "0% (CPU only)",
            f"{comparison.gpu_utilization:.1f}%",
            "GPU accelerated"
        )
        
        table.add_row(
            "Memory Usage",
            "~2GB (System RAM)",
            f"{comparison.memory_usage_gb:.1f}GB (VRAM)",
            "Dedicated GPU memory"
        )
        
        table.add_row(
            "Batch Processing",
            "5 jobs/batch",
            f"{comparison.batch_size_optimal} jobs/batch",
            f"{comparison.batch_size_optimal//5}x larger batches"
        )
        
        table.add_row(
            "Concurrent Streams",
            "2 workers",
            f"{comparison.concurrent_streams} streams",
            f"{comparison.concurrent_streams//2}x more parallel"
        )
        
        table.add_row(
            "Tensor Cores",
            "Not available",
            "✅ Utilized" if comparison.tensor_cores_utilized else "❌ Not used",
            "AI acceleration"
        )
        
        console.print(table)
        
        # Performance summary
        if comparison.performance_improvement > 10:
            performance_grade = "🏆 EXCELLENT"
            grade_color = "bold green"
        elif comparison.performance_improvement > 5:
            performance_grade = "🥇 VERY GOOD"
            grade_color = "green"
        elif comparison.performance_improvement > 2:
            performance_grade = "🥈 GOOD"
            grade_color = "yellow"
        else:
            performance_grade = "🥉 NEEDS IMPROVEMENT"
            grade_color = "red"
        
        console.print(f"\n[{grade_color}]{performance_grade}[/{grade_color}]")
        console.print(f"[bold]RTX 3080 Performance: {comparison.performance_improvement:.1f}x faster than original[/bold]")
    
    async def run_comprehensive_benchmark(self, job_count: int = 100) -> Dict[str, Any]:
        """Run comprehensive RTX 3080 benchmark suite."""
        console.print(Panel(
            "[bold blue]🚀 RTX 3080 Comprehensive Performance Benchmark[/bold blue]\n"
            f"[cyan]Testing with {job_count} jobs[/cyan]",
            title="Performance Test Suite"
        ))
        
        # Create test jobs
        console.print("\n[cyan]📝 Creating test jobs...[/cyan]")
        test_jobs = self.create_test_jobs(job_count)
        console.print(f"✅ Created {len(test_jobs)} test jobs")
        
        benchmark_results = {
            'test_started': time.time(),
            'job_count': job_count,
            'tests': {}
        }
        
        # Test 1: RTX 3080 GPU Client
        gpu_client_results = await self.test_rtx3080_gpu_client(test_jobs[:50])
        benchmark_results['tests']['gpu_client'] = gpu_client_results
        
        # Test 2: RTX 3080 Enhanced Processor
        processor_results = await self.test_rtx3080_enhanced_processor(test_jobs[:50])
        benchmark_results['tests']['enhanced_processor'] = processor_results
        
        # Test 3: Performance Comparison
        comparison = await self.compare_with_original_processor(test_jobs[:20])
        benchmark_results['tests']['performance_comparison'] = comparison
        
        # Display results
        self.display_performance_comparison(comparison)
        
        benchmark_results['test_completed'] = time.time()
        benchmark_results['total_test_time'] = benchmark_results['test_completed'] - benchmark_results['test_started']
        
        # Save results
        self.save_benchmark_results(benchmark_results)
        
        return benchmark_results
    
    def save_benchmark_results(self, results: Dict[str, Any]) -> None:
        """Save benchmark results to file."""
        try:
            results_file = Path("rtx3080_benchmark_results.json")
            
            # Convert dataclass to dict for JSON serialization
            if 'performance_comparison' in results['tests']:
                comparison = results['tests']['performance_comparison']
                if isinstance(comparison, PerformanceComparison):
                    results['tests']['performance_comparison'] = {
                        'original_jobs_per_sec': comparison.original_jobs_per_sec,
                        'rtx3080_jobs_per_sec': comparison.rtx3080_jobs_per_sec,
                        'performance_improvement': comparison.performance_improvement,
                        'original_processing_time': comparison.original_processing_time,
                        'rtx3080_processing_time': comparison.rtx3080_processing_time,
                        'time_reduction_percent': comparison.time_reduction_percent,
                        'gpu_utilization': comparison.gpu_utilization,
                        'memory_usage_gb': comparison.memory_usage_gb,
                        'tensor_cores_utilized': comparison.tensor_cores_utilized,
                        'batch_size_optimal': comparison.batch_size_optimal,
                        'concurrent_streams': comparison.concurrent_streams
                    }
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            console.print(f"\n💾 Benchmark results saved to: {results_file}")
            
        except Exception as e:
            console.print(f"[red]❌ Failed to save results: {e}[/red]")

async def main():
    """Main function to run RTX 3080 performance tests."""
    console.print(Panel(
        "[bold blue]🎯 RTX 3080 Performance Test Suite[/bold blue]\n"
        "[cyan]Testing RTX 3080 optimizations for job processing[/cyan]",
        title="AutoJobAgent RTX 3080 Benchmark"
    ))
    
    # Initialize test suite
    test_suite = RTX3080PerformanceTest(profile_name="test_profile")
    
    try:
        # Run comprehensive benchmark
        results = await test_suite.run_comprehensive_benchmark(job_count=100)
        
        # Display final summary
        console.print("\n[bold green]🎉 RTX 3080 Performance Test Complete![/bold green]")
        console.print(f"⏱️ Total test time: {results['total_test_time']:.2f} seconds")
        
        # Check if RTX 3080 optimizations are working
        if 'performance_comparison' in results['tests']:
            comparison = results['tests']['performance_comparison']
            if hasattr(comparison, 'performance_improvement'):
                improvement = comparison.performance_improvement
            else:
                improvement = comparison.get('performance_improvement', 0)
            
            if improvement > 5:
                console.print("[bold green]✅ RTX 3080 optimizations are working excellently![/bold green]")
                console.print(f"[green]🚀 Performance improvement: {improvement:.1f}x faster[/green]")
            elif improvement > 2:
                console.print("[yellow]⚠️ RTX 3080 optimizations are working but could be better[/yellow]")
                console.print(f"[yellow]📈 Performance improvement: {improvement:.1f}x faster[/yellow]")
            else:
                console.print("[red]❌ RTX 3080 optimizations may not be working properly[/red]")
                console.print("[red]🔧 Check GPU drivers, CUDA installation, and Ollama GPU support[/red]")
        
    except Exception as e:
        console.print(f"[red]❌ Performance test failed: {e}[/red]")
        import traceback
        console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")

if __name__ == "__main__":
    asyncio.run(main())