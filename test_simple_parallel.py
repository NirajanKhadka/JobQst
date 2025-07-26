"""
Simple Parallel Job Processing Test
Tests parallel job processing for RTX 3080 without complex CUDA compilation.
"""

import asyncio
import time
import logging
import concurrent.futures
from typing import Dict, List, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def analyze_job_simple(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple job analysis using rule-based approach.
    Simulates what ExLlamaV2 would do but without CUDA compilation issues.
    """
    # Simulate processing time
    time.sleep(0.1)  # 100ms per job
    
    description = job.get('description', '').lower()
    title = job.get('title', '').lower()
    
    # Extract skills using simple keyword matching
    skill_keywords = {
        'python': ['python', 'django', 'flask', 'fastapi'],
        'javascript': ['javascript', 'js', 'react', 'vue', 'angular', 'node'],
        'sql': ['sql', 'mysql', 'postgresql', 'database'],
        'machine learning': ['ml', 'machine learning', 'ai', 'tensorflow', 'pytorch'],
        'cloud': ['aws', 'azure', 'gcp', 'cloud', 'docker', 'kubernetes'],
        'data science': ['data science', 'pandas', 'numpy', 'analytics']
    }
    
    required_skills = []
    for skill, keywords in skill_keywords.items():
        if any(keyword in description or keyword in title for keyword in keywords):
            required_skills.append(skill.title())
    
    # Extract experience level
    experience_level = 'Entry'
    if any(exp in description for exp in ['senior', '5+ years', '3+ years']):
        experience_level = 'Senior'
    elif any(exp in description for exp in ['mid', '2+ years', '3 years']):
        experience_level = 'Mid-level'
    
    # Calculate compatibility score
    compatibility_score = min(0.9, 0.5 + len(required_skills) * 0.1)
    
    result = job.copy()
    result.update({
        'required_skills': required_skills,
        'job_requirements': [f'{experience_level} level experience'],
        'compatibility_score': compatibility_score,
        'analysis_confidence': 0.8,
        'extracted_benefits': ['Health insurance', 'Remote work'],
        'analysis_reasoning': f'Found {len(required_skills)} relevant skills',
        'processing_method': 'parallel_cpu',
        'processed_at': time.time()
    })
    
    return result

def test_sequential_processing(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Test sequential job processing."""
    console.print("[cyan]🔄 Testing sequential processing...[/cyan]")
    
    start_time = time.time()
    results = []
    
    for i, job in enumerate(jobs):
        console.print(f"[dim]Processing job {i+1}/{len(jobs)}...[/dim]")
        result = analyze_job_simple(job)
        results.append(result)
    
    processing_time = time.time() - start_time
    jobs_per_second = len(results) / processing_time if processing_time > 0 else 0
    
    console.print(f"[green]✅ Sequential processing complete: {jobs_per_second:.2f} jobs/sec[/green]")
    
    return {
        'method': 'sequential',
        'jobs_processed': len(results),
        'processing_time': processing_time,
        'jobs_per_second': jobs_per_second,
        'results': results
    }

def test_parallel_processing(jobs: List[Dict[str, Any]], max_workers: int = 4) -> Dict[str, Any]:
    """Test parallel job processing using ThreadPoolExecutor."""
    console.print(f"[cyan]🚀 Testing parallel processing ({max_workers} workers)...[/cyan]")
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_job = {executor.submit(analyze_job_simple, job): job for job in jobs}
        
        results = []
        for i, future in enumerate(concurrent.futures.as_completed(future_to_job)):
            console.print(f"[dim]Completed job {i+1}/{len(jobs)}...[/dim]")
            result = future.result()
            results.append(result)
    
    processing_time = time.time() - start_time
    jobs_per_second = len(results) / processing_time if processing_time > 0 else 0
    
    console.print(f"[green]✅ Parallel processing complete: {jobs_per_second:.2f} jobs/sec[/green]")
    
    return {
        'method': f'parallel_{max_workers}_workers',
        'jobs_processed': len(results),
        'processing_time': processing_time,
        'jobs_per_second': jobs_per_second,
        'results': results
    }

async def test_async_processing(jobs: List[Dict[str, Any]], max_concurrent: int = 8) -> Dict[str, Any]:
    """Test async job processing."""
    console.print(f"[cyan]⚡ Testing async processing ({max_concurrent} concurrent)...[/cyan]")
    
    async def analyze_job_async(job: Dict[str, Any]) -> Dict[str, Any]:
        # Run CPU-bound task in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, analyze_job_simple, job)
    
    start_time = time.time()
    
    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_job_with_semaphore(job: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            return await analyze_job_async(job)
    
    # Process all jobs concurrently
    tasks = [process_job_with_semaphore(job) for job in jobs]
    results = await asyncio.gather(*tasks)
    
    processing_time = time.time() - start_time
    jobs_per_second = len(results) / processing_time if processing_time > 0 else 0
    
    console.print(f"[green]✅ Async processing complete: {jobs_per_second:.2f} jobs/sec[/green]")
    
    return {
        'method': f'async_{max_concurrent}_concurrent',
        'jobs_processed': len(results),
        'processing_time': processing_time,
        'jobs_per_second': jobs_per_second,
        'results': results
    }

def create_test_jobs(count: int = 10) -> List[Dict[str, Any]]:
    """Create test jobs for benchmarking."""
    console.print(f"[cyan]📝 Creating {count} test jobs...[/cyan]")
    
    job_templates = [
        {
            'title': 'Senior Python Developer',
            'company': 'TechCorp',
            'description': 'Looking for a senior Python developer with Django, FastAPI, and machine learning experience. Must have 5+ years of experience in web development and strong problem-solving skills.',
            'location': 'Toronto, ON'
        },
        {
            'title': 'Data Scientist',
            'company': 'DataCorp', 
            'description': 'Data scientist role requiring Python, machine learning, pandas, numpy, and statistical analysis skills. PhD in Computer Science preferred with 3+ years experience.',
            'location': 'Vancouver, BC'
        },
        {
            'title': 'DevOps Engineer',
            'company': 'CloudCorp',
            'description': 'DevOps engineer with AWS, Docker, Kubernetes, and CI/CD pipeline experience. Must know Terraform, Ansible, and have 4+ years of cloud infrastructure experience.',
            'location': 'Montreal, QC'
        },
        {
            'title': 'Frontend Developer',
            'company': 'WebCorp',
            'description': 'Frontend developer with React, JavaScript, TypeScript, and modern web technologies. 3+ years of experience building responsive web applications.',
            'location': 'Calgary, AB'
        },
        {
            'title': 'Full Stack Developer',
            'company': 'StartupCorp',
            'description': 'Full stack developer with Python, JavaScript, React, Node.js, and SQL database experience. Looking for someone with 2+ years of experience.',
            'location': 'Ottawa, ON'
        }
    ]
    
    test_jobs = []
    for i in range(count):
        template = job_templates[i % len(job_templates)]
        job = template.copy()
        job['id'] = f'test_job_{i + 1:03d}'
        job['url'] = f'https://example.com/job/{i + 1}'
        job['status'] = 'scraped'
        test_jobs.append(job)
    
    console.print(f"[green]✅ Created {len(test_jobs)} test jobs[/green]")
    return test_jobs

def display_performance_comparison(results: List[Dict[str, Any]]):
    """Display performance comparison table."""
    console.print("\n[bold green]📊 Performance Comparison Results[/bold green]")
    
    # Create comparison table
    table = Table(title="Job Processing Performance Comparison")
    table.add_column("Method", style="cyan", no_wrap=True)
    table.add_column("Jobs/Second", style="green")
    table.add_column("Processing Time", style="yellow")
    table.add_column("Speedup", style="bold green")
    
    # Use sequential as baseline
    baseline_jps = next((r['jobs_per_second'] for r in results if r['method'] == 'sequential'), 1.0)
    
    for result in results:
        speedup = result['jobs_per_second'] / baseline_jps if baseline_jps > 0 else 1.0
        
        table.add_row(
            result['method'].replace('_', ' ').title(),
            f"{result['jobs_per_second']:.2f}",
            f"{result['processing_time']:.2f}s",
            f"{speedup:.1f}x"
        )
    
    console.print(table)
    
    # Find best performer
    best_result = max(results, key=lambda x: x['jobs_per_second'])
    best_speedup = best_result['jobs_per_second'] / baseline_jps
    
    if best_speedup > 5:
        console.print(f"[bold green]🏆 EXCELLENT: {best_result['method']} achieved {best_speedup:.1f}x speedup![/bold green]")
    elif best_speedup > 3:
        console.print(f"[green]🥇 VERY GOOD: {best_result['method']} achieved {best_speedup:.1f}x speedup[/green]")
    elif best_speedup > 2:
        console.print(f"[yellow]🥈 GOOD: {best_result['method']} achieved {best_speedup:.1f}x speedup[/yellow]")
    else:
        console.print(f"[yellow]🥉 MODERATE: Best speedup was {best_speedup:.1f}x[/yellow]")

async def main():
    """Main test function."""
    console.print(Panel(
        "[bold blue]🎯 Simple Parallel Job Processing Test[/bold blue]\n"
        "[cyan]Testing parallel processing approaches for RTX 3080[/cyan]",
        title="AutoJobAgent Parallel Processing Test"
    ))
    
    # Create test jobs
    test_jobs = create_test_jobs(10)
    
    results = []
    
    # Test 1: Sequential processing (baseline)
    sequential_result = test_sequential_processing(test_jobs)
    results.append(sequential_result)
    
    # Test 2: Parallel processing with 2 workers
    parallel_2_result = test_parallel_processing(test_jobs, max_workers=2)
    results.append(parallel_2_result)
    
    # Test 3: Parallel processing with 4 workers
    parallel_4_result = test_parallel_processing(test_jobs, max_workers=4)
    results.append(parallel_4_result)
    
    # Test 4: Parallel processing with 8 workers
    parallel_8_result = test_parallel_processing(test_jobs, max_workers=8)
    results.append(parallel_8_result)
    
    # Test 5: Async processing with 8 concurrent
    async_8_result = await test_async_processing(test_jobs, max_concurrent=8)
    results.append(async_8_result)
    
    # Test 6: Async processing with 16 concurrent
    async_16_result = await test_async_processing(test_jobs, max_concurrent=16)
    results.append(async_16_result)
    
    # Display comparison
    display_performance_comparison(results)
    
    # Summary
    console.print("\n[bold blue]📋 Test Summary[/bold blue]")
    for result in results:
        console.print(f"[green]✅ {result['method']}: {result['jobs_per_second']:.2f} jobs/sec[/green]")
    
    console.print("\n[bold green]🎉 Parallel processing test complete![/bold green]")
    console.print("[cyan]This demonstrates the performance benefits of parallel processing[/cyan]")
    console.print("[cyan]even without complex GPU acceleration like ExLlamaV2.[/cyan]")

if __name__ == "__main__":
    asyncio.run(main())