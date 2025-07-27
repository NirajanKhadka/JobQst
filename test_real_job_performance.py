#!/usr/bin/env python3
"""
Real Job Performance Test - Compare processing methods on actual Nirajan profile jobs
Tests speed and accuracy of rule-based vs other methods on real database jobs
"""

import time
import sys
import os
import asyncio
from typing import Dict, List, Any
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def create_sample_jobs() -> List[Dict[str, Any]]:
    """Create sample jobs for testing when database is empty"""
    return [
        {
            'id': 1,
            'title': 'Senior Data Analyst',
            'company': 'TechCorp Analytics',
            'location': 'Toronto, ON',
            'url': 'https://example.com/job1',
            'description': 'We are seeking a Senior Data Analyst with expertise in Python, SQL, and machine learning. The role involves analyzing large datasets, creating predictive models, and building interactive dashboards using Power BI and Tableau. Experience with AWS, pandas, numpy, and scikit-learn is required. Must have 3+ years of experience in data analysis and statistical modeling.',
            'requirements': 'Python, SQL, Machine Learning, Power BI, Tableau, AWS, 3+ years experience',
            'salary_range': '$70,000 - $90,000',
            'experience_level': 'Senior',
            'employment_type': 'Full-time',
            'posted_date': '2024-01-15',
            'current_analysis_method': 'unknown',
            'current_compatibility_score': 0,
            'current_confidence': 0
        },
        {
            'id': 2,
            'title': 'Machine Learning Engineer',
            'company': 'AI Solutions Inc',
            'location': 'Vancouver, BC',
            'url': 'https://example.com/job2',
            'description': 'Join our ML team to develop and deploy machine learning models using TensorFlow, scikit-learn, and Python. You will work on real-time data processing, model optimization, and cloud deployment on AWS. Strong background in statistics, probability, and data visualization required. Experience with Docker, FastAPI, and automated data collection is a plus.',
            'requirements': 'Python, TensorFlow, Machine Learning, AWS, Docker, Statistics, Data Visualization',
            'salary_range': '$80,000 - $110,000',
            'experience_level': 'Mid',
            'employment_type': 'Full-time',
            'posted_date': '2024-01-14',
            'current_analysis_method': 'unknown',
            'current_compatibility_score': 0,
            'current_confidence': 0
        },
        {
            'id': 3,
            'title': 'Business Intelligence Analyst',
            'company': 'DataViz Corp',
            'location': 'Calgary, AB',
            'url': 'https://example.com/job3',
            'description': 'We need a BI Analyst to create interactive dashboards and reports using Power BI, Tableau, and Excel. You will analyze business data, identify trends, and provide data-driven insights to stakeholders. Knowledge of SQL, database management, and business analytics is essential. Experience with MySQL, PostgreSQL, and data workflows preferred.',
            'requirements': 'Power BI, Tableau, SQL, Excel, Business Analytics, Database Management',
            'salary_range': '$60,000 - $80,000',
            'experience_level': 'Mid',
            'employment_type': 'Full-time',
            'posted_date': '2024-01-13',
            'current_analysis_method': 'unknown',
            'current_compatibility_score': 0,
            'current_confidence': 0
        },
        {
            'id': 4,
            'title': 'Data Science Intern',
            'company': 'StartupTech',
            'location': 'Montreal, QC',
            'url': 'https://example.com/job4',
            'description': 'Internship opportunity for aspiring data scientists. Work with Python, pandas, numpy, and Jupyter notebooks to analyze data and build predictive models. Learn about machine learning, statistical analysis, and data visualization using matplotlib and seaborn. Great opportunity to gain hands-on experience with real-world data projects.',
            'requirements': 'Python, Pandas, NumPy, Jupyter, Machine Learning, Statistical Analysis',
            'salary_range': '$35,000 - $45,000',
            'experience_level': 'Entry',
            'employment_type': 'Internship',
            'posted_date': '2024-01-12',
            'current_analysis_method': 'unknown',
            'current_compatibility_score': 0,
            'current_confidence': 0
        },
        {
            'id': 5,
            'title': 'Cloud Data Engineer',
            'company': 'CloudFirst Solutions',
            'location': 'Ottawa, ON',
            'url': 'https://example.com/job5',
            'description': 'Looking for a Cloud Data Engineer to design and implement data pipelines on AWS. You will work with Lambda, QuickSight, and various AWS services to process and analyze real-time data. Strong Python skills and experience with cloud practitioner concepts required. Knowledge of data management, automated data collection, and data processing workflows essential.',
            'requirements': 'AWS, Lambda, QuickSight, Python, Data Management, Real-time Data Processing',
            'salary_range': '$75,000 - $95,000',
            'experience_level': 'Senior',
            'employment_type': 'Full-time',
            'posted_date': '2024-01-11',
            'current_analysis_method': 'unknown',
            'current_compatibility_score': 0,
            'current_confidence': 0
        }
    ]

async def get_sample_jobs(profile_name: str = "Nirajan", limit: int = 5) -> List[Dict[str, Any]]:
    """Get sample jobs from the database"""
    try:
        db = get_job_db(profile_name)
        
        # Get jobs with descriptions for better testing
        jobs = db.get_jobs(limit=limit)
        console.print(f"[dim]Debug: Found {len(jobs)} total jobs in database[/dim]")
        
        if not jobs:
            console.print("[yellow]⚠️ No jobs found in database. Creating sample jobs for testing...[/yellow]")
            return create_sample_jobs()
        
        # Jobs are already in dict format from get_jobs()
        # Filter jobs with descriptions for better testing
        filtered_jobs = []
        for job in jobs:
            console.print(f"[dim]Debug: Job {job.get('id')}: {job.get('title')} - Description: {bool(job.get('description'))}[/dim]")
            if job.get('description') and job.get('description').strip():
                # Add current analysis info for comparison
                job['current_analysis_method'] = job.get('analysis_method', 'unknown')
                job['current_compatibility_score'] = job.get('compatibility_score', 0)
                job['current_confidence'] = job.get('confidence', 0)
                filtered_jobs.append(job)
            else:
                # Use jobs without descriptions too, but add empty description
                job['description'] = job.get('description') or f"Job posting for {job.get('title', 'Unknown Position')} at {job.get('company', 'Unknown Company')}. {job.get('requirements', '')}"
                job['current_analysis_method'] = job.get('analysis_method', 'unknown')
                job['current_compatibility_score'] = job.get('compatibility_score', 0)
                job['current_confidence'] = job.get('confidence', 0)
                filtered_jobs.append(job)
        
        return filtered_jobs[:limit]  # Ensure we don't exceed limit
        
    except Exception as e:
        console.print(f"[red]❌ Error getting jobs from database: {e}[/red]")
        return []

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
                'analysis_method': analysis.get('analysis_method', 'rule_based'),
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
            'success': True
        }
        
    except Exception as e:
        console.print(f"[red]❌ Rule-based test failed: {e}[/red]")
        return {'method': 'rule_based', 'success': False, 'error': str(e)}

async def test_hybrid_method(jobs: List[Dict[str, Any]], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Test hybrid processing method"""
    try:
        from src.analysis.hybrid_processor import HybridProcessingEngine
        
        engine = HybridProcessingEngine(user_profile=profile, use_enhanced_extractor=True)
        
        start_time = time.time()
        results = []
        
        for job in jobs:
            analysis = engine.process_job(job)
            results.append({
                'job_id': job['id'],
                'job_title': job['title'],
                'compatibility_score': analysis.compatibility_score,
                'confidence': analysis.analysis_confidence,
                'analysis_method': analysis.processing_method,
                'processing_time': analysis.total_processing_time
            })
        
        end_time = time.time()
        total_time = end_time - start_time
        
        return {
            'method': 'hybrid',
            'total_time': total_time,
            'jobs_processed': len(jobs),
            'jobs_per_second': len(jobs) / total_time if total_time > 0 else 0,
            'avg_time_per_job': total_time / len(jobs) if jobs else 0,
            'results': results,
            'success': True
        }
        
    except Exception as e:
        console.print(f"[red]❌ Hybrid test failed: {e}[/red]")
        return {'method': 'hybrid', 'success': False, 'error': str(e)}

async def test_fast_pipeline_method(jobs: List[Dict[str, Any]], profile_name: str) -> Dict[str, Any]:
    """Test Fast Pipeline processing method"""
    try:
        from src.pipeline.fast_job_pipeline import FastJobPipeline
        
        # Configure pipeline for processing existing jobs
        config = {
            "eluta_pages": 0,  # Not scraping new jobs
            "eluta_jobs": 0,   # Not scraping new jobs
            "external_workers": 0,  # Not scraping descriptions
            "processing_method": "rule_based",
            "save_to_database": False,  # Don't save during test
            "enable_duplicate_check": False,
        }
        
        pipeline = FastJobPipeline(profile_name, config)
        
        start_time = time.time()
        
        # Process jobs directly (skip scraping phases)
        processed_jobs, stats = await pipeline.process_jobs_direct(jobs)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        results = []
        for job in processed_jobs:
            results.append({
                'job_id': job.get('id'),
                'job_title': job.get('title'),
                'compatibility_score': job.get('compatibility_score', 0),
                'confidence': job.get('confidence', 0),
                'analysis_method': job.get('processing_method', 'fast_pipeline'),
                'processing_time': job.get('processing_time', 0)
            })
        
        return {
            'method': 'fast_pipeline',
            'total_time': total_time,
            'jobs_processed': len(processed_jobs),
            'jobs_per_second': len(processed_jobs) / total_time if total_time > 0 else 0,
            'avg_time_per_job': total_time / len(processed_jobs) if processed_jobs else 0,
            'results': results,
            'success': True,
            'stats': stats
        }
        
    except Exception as e:
        console.print(f"[red]❌ Fast Pipeline test failed: {e}[/red]")
        return {'method': 'fast_pipeline', 'success': False, 'error': str(e)}

def display_performance_comparison(test_results: List[Dict[str, Any]], jobs: List[Dict[str, Any]]):
    """Display performance comparison results"""
    
    console.print(Panel("🚀 Real Job Performance Test Results", style="bold blue"))
    
    # Performance Summary Table
    perf_table = Table(title="⚡ Performance Comparison")
    perf_table.add_column("Method", style="cyan")
    perf_table.add_column("Total Time", style="green")
    perf_table.add_column("Jobs/Second", style="yellow")
    perf_table.add_column("Avg per Job", style="magenta")
    perf_table.add_column("Status", style="white")
    
    successful_results = [r for r in test_results if r.get('success')]
    
    for result in test_results:
        if result.get('success'):
            method = result['method'].replace('_', ' ').title()
            total_time = f"{result['total_time']:.3f}s"
            jobs_per_sec = f"{result['jobs_per_second']:.1f}"
            avg_time = f"{result['avg_time_per_job']*1000:.1f}ms"
            status = "✅ Success"
        else:
            method = result['method'].replace('_', ' ').title()
            total_time = "N/A"
            jobs_per_sec = "N/A"
            avg_time = "N/A"
            status = f"❌ Failed: {result.get('error', 'Unknown')[:30]}..."
        
        perf_table.add_row(method, total_time, jobs_per_sec, avg_time, status)
    
    console.print(perf_table)
    
    if len(successful_results) >= 2:
        # Speed comparison
        fastest = min(successful_results, key=lambda x: x['total_time'])
        slowest = max(successful_results, key=lambda x: x['total_time'])
        
        if fastest != slowest:
            speed_advantage = slowest['total_time'] / fastest['total_time']
            console.print(f"\n🏆 Fastest Method: {fastest['method'].replace('_', ' ').title()}")
            console.print(f"⚡ Speed Advantage: {speed_advantage:.1f}x faster than {slowest['method'].replace('_', ' ').title()}")
    
    # Accuracy Comparison Table
    if successful_results:
        acc_table = Table(title="🎯 Accuracy Comparison")
        acc_table.add_column("Job", style="cyan")
        acc_table.add_column("Current DB", style="white")
        
        for result in successful_results:
            method_name = result['method'].replace('_', ' ').title()
            acc_table.add_column(method_name, style="green")
        
        # Show results for each job
        for i, job in enumerate(jobs[:5]):  # Limit to 5 jobs for readability
            current_score = job.get('current_compatibility_score') or 0
            current_method = job.get('current_analysis_method') or 'unknown'
            row = [
                f"{job['title'][:30]}...",
                f"{current_score:.2f} ({current_method})"
            ]
            
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
    
    # Sample Job Details
    console.print(Panel("📋 Sample Job Details", style="bold yellow"))
    for i, job in enumerate(jobs[:3]):  # Show first 3 jobs
        console.print(f"\n[bold]Job {i+1}:[/bold] {job['title']}")
        console.print(f"[dim]Company:[/dim] {job['company']}")
        console.print(f"[dim]Location:[/dim] {job['location']}")
        current_score = job.get('current_compatibility_score') or 0
        console.print(f"[dim]Current Score:[/dim] {current_score:.2f}")
        if job.get('description'):
            desc_preview = job['description'][:100] + "..." if len(job['description']) > 100 else job['description']
            console.print(f"[dim]Description:[/dim] {desc_preview}")

async def main():
    """Main test function"""
    console.print("🧪 Real Job Performance Test - Nirajan Profile")
    console.print("=" * 60)
    
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
    
    # Get sample jobs
    console.print(f"[cyan]📋 Getting 5 sample jobs from database...[/cyan]")
    jobs = await get_sample_jobs(profile_name, 5)
    
    if not jobs:
        console.print("[red]❌ No jobs found in database[/red]")
        return
    
    console.print(f"[green]✅ Found {len(jobs)} jobs for testing[/green]")
    
    # Test different methods
    test_results = []
    
    console.print(f"\n[cyan]🧪 Testing Rule-Based Method...[/cyan]")
    rule_based_result = await test_rule_based_method(jobs, profile)
    test_results.append(rule_based_result)
    
    console.print(f"[cyan]🧪 Testing Hybrid Method...[/cyan]")
    hybrid_result = await test_hybrid_method(jobs, profile)
    test_results.append(hybrid_result)
    
    console.print(f"[cyan]🧪 Testing Fast Pipeline Method...[/cyan]")
    pipeline_result = await test_fast_pipeline_method(jobs, profile_name)
    test_results.append(pipeline_result)
    
    # Display results
    console.print(f"\n")
    display_performance_comparison(test_results, jobs)
    
    # Summary
    successful_tests = [r for r in test_results if r.get('success')]
    if successful_tests:
        fastest = min(successful_tests, key=lambda x: x['total_time'])
        console.print(f"\n[bold green]🏆 Winner: {fastest['method'].replace('_', ' ').title()}[/bold green]")
        console.print(f"[green]⚡ Speed: {fastest['jobs_per_second']:.1f} jobs/second[/green]")
        console.print(f"[green]⏱️ Time per job: {fastest['avg_time_per_job']*1000:.1f}ms[/green]")

if __name__ == "__main__":
    asyncio.run(main())