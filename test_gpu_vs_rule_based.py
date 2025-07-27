#!/usr/bin/env python3
"""
Test GPU vs Rule-Based Performance
Compare GPU-accelerated processing with rule-based analysis
"""

import time
import sys
import os
import asyncio
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.profile_helpers import load_profile
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def create_test_jobs() -> List[Dict[str, Any]]:
    """Create test jobs for performance comparison"""
    return [
        {
            'id': 1,
            'title': 'Senior Data Analyst',
            'company': 'TechCorp Analytics',
            'location': 'Toronto, ON',
            'description': 'We are seeking a Senior Data Analyst with expertise in Python, SQL, and machine learning. The role involves analyzing large datasets, creating predictive models, and building interactive dashboards using Power BI and Tableau. Experience with AWS, pandas, numpy, and scikit-learn is required. Must have 3+ years of experience in data analysis and statistical modeling.',
            'requirements': 'Python, SQL, Machine Learning, Power BI, Tableau, AWS, 3+ years experience'
        },
        {
            'id': 2,
            'title': 'Machine Learning Engineer',
            'company': 'AI Solutions Inc',
            'location': 'Vancouver, BC',
            'description': 'Join our ML team to develop and deploy machine learning models using TensorFlow, scikit-learn, and Python. You will work on real-time data processing, model optimization, and cloud deployment on AWS. Strong background in statistics, probability, and data visualization required.',
            'requirements': 'Python, TensorFlow, Machine Learning, AWS, Statistics, Data Visualization'
        },
        {
            'id': 3,
            'title': 'Full Stack Developer',
            'company': 'WebTech Solutions',
            'location': 'Calgary, AB',
            'description': 'Looking for a Full Stack Developer with experience in React, Node.js, and MongoDB. You will build responsive web applications, implement REST APIs, and work with modern JavaScript frameworks. Knowledge of Docker, Git, and Agile methodologies preferred.',
            'requirements': 'JavaScript, React, Node.js, MongoDB, REST APIs, Docker, Git'
        },
        {
            'id': 4,
            'title': 'DevOps Engineer',
            'company': 'CloudFirst Corp',
            'location': 'Ottawa, ON',
            'description': 'Seeking a DevOps Engineer to manage CI/CD pipelines, containerization with Docker and Kubernetes, and cloud infrastructure on AWS. Experience with Terraform, Jenkins, and monitoring tools required. Strong Linux and scripting skills essential.',
            'requirements': 'DevOps, Docker, Kubernetes, AWS, Terraform, Jenkins, Linux'
        },
        {
            'id': 5,
            'title': 'Backend Developer',
            'company': 'API Systems Ltd',
            'location': 'Montreal, QC',
            'description': 'Backend Developer position focusing on microservices architecture, API development, and database optimization. Work with Java, Spring Boot, PostgreSQL, and Redis. Experience with message queues and distributed systems preferred.',
            'requirements': 'Java, Spring Boot, PostgreSQL, Redis, Microservices, API Development'
        }
    ]

async def test_rule_based_method(jobs: List[Dict[str, Any]], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Test rule-based processing method"""
    try:
        from src.ai.enhanced_rule_based_analyzer import EnhancedRuleBasedAnalyzer
        
        analyzer = EnhancedRuleBasedAnalyzer(profile)
        
        start_time = time.time()
        results = []
        
        for job in jobs:
            analysis = analyzer.analyze_job(job)
            results.append({
                'job_id': job['id'],
                'job_title': job['title'],
                'compatibility_score': analysis.get('compatibility_score', 0),
                'confidence': analysis.get('confidence', 0),
                'analysis_method': 'rule_based',
                'processing_time': analysis.get('processing_time', 0)
            })
        
        end_time = time.time()
        total_time = end_time - start_time
        
        return {
            'method': 'rule_based',
            'total_time': total_time,
            'jobs_processed': len(jobs),
            'jobs_per_second': len(jobs) / total_time if total_time > 0 else 0,
            'avg_time_per_job': total_time / len(jobs) if jobs else 0,
            'results': results,
            'success': True,
            'device': 'CPU'
        }
        
    except Exception as e:
        console.print(f"[red]❌ Rule-based test failed: {e}[/red]")
        return {'method': 'rule_based', 'success': False, 'error': str(e)}

async def test_gpu_method(jobs: List[Dict[str, Any]], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Test GPU processing method"""
    try:
        from src.ai.gpu_job_processor import GPUJobProcessor
        import torch
        
        # Check if CUDA is available
        cuda_available = torch.cuda.is_available()
        device = "cuda" if cuda_available else "cpu"
        
        processor = GPUJobProcessor(device=device)
        
        start_time = time.time()
        
        # Process jobs with GPU
        gpu_result = await processor.process_jobs_gpu_async(jobs)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        results = []
        for i, job_result in enumerate(gpu_result.job_results):
            results.append({
                'job_id': jobs[i]['id'],
                'job_title': jobs[i]['title'],
                'compatibility_score': job_result.get('compatibility_score', 0),
                'confidence': job_result.get('confidence', 0),
                'analysis_method': 'gpu',
                'processing_time': job_result.get('processing_time', 0)
            })
        
        return {
            'method': 'gpu',
            'total_time': total_time,
            'jobs_processed': len(jobs),
            'jobs_per_second': len(jobs) / total_time if total_time > 0 else 0,
            'avg_time_per_job': total_time / len(jobs) if jobs else 0,
            'results': results,
            'success': True,
            'device': device.upper(),
            'cuda_available': cuda_available,
            'gpu_metrics': {
                'total_inference_time': gpu_result.metrics.total_inference_time,
                'avg_inference_time': gpu_result.metrics.avg_inference_time,
                'tokens_processed': gpu_result.metrics.tokens_processed
            }
        }
        
    except ImportError as e:
        console.print(f"[red]❌ GPU test failed - missing dependencies: {e}[/red]")
        return {'method': 'gpu', 'success': False, 'error': f'Missing dependencies: {e}'}
    except Exception as e:
        console.print(f"[red]❌ GPU test failed: {e}[/red]")
        return {'method': 'gpu', 'success': False, 'error': str(e)}

def display_comparison_results(test_results: List[Dict[str, Any]], jobs: List[Dict[str, Any]]):
    """Display detailed comparison results"""
    
    console.print(Panel("🚀 GPU vs Rule-Based Performance Comparison", style="bold blue"))
    
    # Performance Summary Table
    perf_table = Table(title="⚡ Performance Comparison")
    perf_table.add_column("Method", style="cyan")
    perf_table.add_column("Device", style="green")
    perf_table.add_column("Total Time", style="yellow")
    perf_table.add_column("Jobs/Second", style="magenta")
    perf_table.add_column("Avg per Job", style="white")
    perf_table.add_column("Status", style="white")
    
    successful_results = [r for r in test_results if r.get('success')]
    
    for result in test_results:
        if result.get('success'):
            method = result['method'].replace('_', ' ').title()
            device = result.get('device', 'Unknown')
            total_time = f"{result['total_time']:.3f}s"
            jobs_per_sec = f"{result['jobs_per_second']:.1f}"
            avg_time = f"{result['avg_time_per_job']*1000:.1f}ms"
            status = "✅ Success"
        else:
            method = result['method'].replace('_', ' ').title()
            device = "N/A"
            total_time = "N/A"
            jobs_per_sec = "N/A"
            avg_time = "N/A"
            status = f"❌ Failed"
        
        perf_table.add_row(method, device, total_time, jobs_per_sec, avg_time, status)
    
    console.print(perf_table)
    
    # Speed comparison
    if len(successful_results) >= 2:
        fastest = min(successful_results, key=lambda x: x['total_time'])
        slowest = max(successful_results, key=lambda x: x['total_time'])
        
        if fastest != slowest:
            speed_advantage = slowest['total_time'] / fastest['total_time']
            console.print(f"\n🏆 Fastest Method: {fastest['method'].replace('_', ' ').title()} ({fastest.get('device', 'Unknown')})")
            console.print(f"⚡ Speed Advantage: {speed_advantage:.1f}x faster than {slowest['method'].replace('_', ' ').title()}")
    
    # GPU-specific metrics
    gpu_result = next((r for r in successful_results if r['method'] == 'gpu'), None)
    if gpu_result:
        console.print(f"\n🔧 GPU Details:")
        console.print(f"   CUDA Available: {'✅ Yes' if gpu_result.get('cuda_available') else '❌ No'}")
        console.print(f"   Device Used: {gpu_result.get('device', 'Unknown')}")
        
        if 'gpu_metrics' in gpu_result:
            metrics = gpu_result['gpu_metrics']
            console.print(f"   Inference Time: {metrics.get('total_inference_time', 0):.3f}s")
            console.print(f"   Tokens Processed: {metrics.get('tokens_processed', 0):,}")
    
    # Accuracy Comparison
    if successful_results:
        acc_table = Table(title="🎯 Accuracy Comparison")
        acc_table.add_column("Job", style="cyan")
        
        for result in successful_results:
            method_name = f"{result['method'].replace('_', ' ').title()} ({result.get('device', 'Unknown')})"
            acc_table.add_column(method_name, style="green")
        
        # Show results for each job
        for i, job in enumerate(jobs):
            row = [f"{job['title'][:25]}..."]
            
            for result in successful_results:
                if i < len(result['results']):
                    job_result = result['results'][i]
                    score = job_result.get('compatibility_score', 0)
                    confidence = job_result.get('confidence', 0)
                    row.append(f"{score:.2f} (conf: {confidence:.2f})")
                else:
                    row.append("N/A")
            
            acc_table.add_row(*row)
        
        console.print(acc_table)

async def main():
    """Main test function"""
    console.print("🧪 GPU vs Rule-Based Performance Test")
    console.print("=" * 50)
    
    # Load profile
    profile_name = "Nirajan"
    try:
        profile = load_profile(profile_name)
        if not profile:
            console.print(f"[red]❌ Could not load profile: {profile_name}[/red]")
            return
        
        console.print(f"[green]✅ Loaded profile: {profile.get('profile_name', profile_name)}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error loading profile: {e}[/red]")
        return
    
    # Create test jobs
    jobs = create_test_jobs()
    console.print(f"[green]✅ Created {len(jobs)} test jobs[/green]")
    
    # Test different methods
    test_results = []
    
    console.print(f"\n[cyan]🧪 Testing Rule-Based Method...[/cyan]")
    rule_based_result = await test_rule_based_method(jobs, profile)
    test_results.append(rule_based_result)
    
    console.print(f"[cyan]🧪 Testing GPU Method...[/cyan]")
    gpu_result = await test_gpu_method(jobs, profile)
    test_results.append(gpu_result)
    
    # Display results
    console.print(f"\n")
    display_comparison_results(test_results, jobs)
    
    # Summary
    successful_tests = [r for r in test_results if r.get('success')]
    if successful_tests:
        fastest = min(successful_tests, key=lambda x: x['total_time'])
        console.print(f"\n[bold green]🏆 Winner: {fastest['method'].replace('_', ' ').title()} ({fastest.get('device', 'Unknown')})[/bold green]")
        console.print(f"[green]⚡ Speed: {fastest['jobs_per_second']:.1f} jobs/second[/green]")
        console.print(f"[green]⏱️ Time per job: {fastest['avg_time_per_job']*1000:.1f}ms[/green]")

if __name__ == "__main__":
    asyncio.run(main())