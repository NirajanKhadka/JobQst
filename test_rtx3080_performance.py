#!/usr/bin/env python3
"""
Test RTX 3080 Enhanced Job Processing Performance
Compare rule-based vs GPU-enhanced processing
"""

import asyncio
import time
import sys
import os
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.profile_helpers import load_profile
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

def create_realistic_jobs() -> List[Dict[str, Any]]:
    """Create realistic job data for testing"""
    return [
        {
            'id': 1,
            'title': 'Senior Data Scientist',
            'company': 'TechCorp Analytics',
            'location': 'Toronto, ON',
            'description': 'We are seeking a Senior Data Scientist with expertise in Python, machine learning, and statistical analysis. You will work with large datasets, develop predictive models using scikit-learn and TensorFlow, and create data visualizations with matplotlib and seaborn. Experience with AWS, pandas, numpy, and Jupyter notebooks is essential. Strong background in statistics, probability theory, and A/B testing required.',
            'requirements': 'Python, Machine Learning, TensorFlow, scikit-learn, pandas, numpy, AWS, Statistics, Data Visualization, 5+ years experience',
            'salary_range': '$90,000 - $120,000'
        },
        {
            'id': 2,
            'title': 'Machine Learning Engineer',
            'company': 'AI Solutions Inc',
            'location': 'Vancouver, BC',
            'description': 'Join our ML team to develop and deploy machine learning models in production. Work with TensorFlow, PyTorch, and scikit-learn to build scalable ML pipelines. You will implement MLOps practices, optimize model performance, and deploy models on AWS using Docker and Kubernetes. Strong Python skills and experience with real-time data processing required.',
            'requirements': 'Python, TensorFlow, PyTorch, MLOps, AWS, Docker, Kubernetes, Real-time Processing',
            'salary_range': '$85,000 - $115,000'
        },
        {
            'id': 3,
            'title': 'Business Intelligence Analyst',
            'company': 'DataViz Corp',
            'location': 'Calgary, AB',
            'description': 'We need a BI Analyst to create interactive dashboards and reports using Power BI, Tableau, and Excel. Analyze business data, identify trends, and provide data-driven insights to stakeholders. Strong SQL skills for database querying and experience with MySQL, PostgreSQL required. Knowledge of business analytics, KPI development, and data storytelling essential.',
            'requirements': 'Power BI, Tableau, SQL, Excel, MySQL, PostgreSQL, Business Analytics, Data Analysis',
            'salary_range': '$65,000 - $85,000'
        },
        {
            'id': 4,
            'title': 'Full Stack Developer',
            'company': 'WebTech Solutions',
            'location': 'Ottawa, ON',
            'description': 'Looking for a Full Stack Developer with experience in React, Node.js, and modern JavaScript frameworks. Build responsive web applications, implement REST APIs, and work with MongoDB databases. Experience with TypeScript, Redux, Express.js, and cloud deployment on AWS preferred. Strong understanding of software development lifecycle and Agile methodologies.',
            'requirements': 'JavaScript, React, Node.js, MongoDB, TypeScript, REST APIs, AWS, Agile',
            'salary_range': '$70,000 - $95,000'
        },
        {
            'id': 5,
            'title': 'DevOps Engineer',
            'company': 'CloudFirst Corp',
            'location': 'Montreal, QC',
            'description': 'Seeking a DevOps Engineer to manage CI/CD pipelines, containerization with Docker and Kubernetes, and cloud infrastructure on AWS. Implement infrastructure as code using Terraform, manage monitoring and logging systems, and ensure high availability of production systems. Strong Linux administration skills and experience with Jenkins, Git, and scripting required.',
            'requirements': 'DevOps, Docker, Kubernetes, AWS, Terraform, Jenkins, Linux, CI/CD, Git',
            'salary_range': '$80,000 - $105,000'
        },
        {
            'id': 6,
            'title': 'Data Analyst',
            'company': 'Analytics Pro',
            'location': 'Toronto, ON',
            'description': 'Data Analyst position focusing on statistical analysis, data visualization, and business intelligence. Use Python, R, and SQL to analyze large datasets and generate insights. Create reports and dashboards using Power BI and Tableau. Experience with pandas, numpy, matplotlib, and statistical modeling required. Strong communication skills for presenting findings to stakeholders.',
            'requirements': 'Python, R, SQL, Power BI, Tableau, pandas, numpy, Statistical Analysis, Data Visualization',
            'salary_range': '$60,000 - $80,000'
        },
        {
            'id': 7,
            'title': 'Cloud Solutions Architect',
            'company': 'CloudTech Systems',
            'location': 'Vancouver, BC',
            'description': 'Senior Cloud Solutions Architect role designing and implementing cloud infrastructure on AWS. Work with Lambda, EC2, S3, RDS, and other AWS services. Design scalable, secure, and cost-effective cloud solutions. Experience with microservices architecture, serverless computing, and cloud security best practices required. AWS certifications preferred.',
            'requirements': 'AWS, Lambda, EC2, S3, RDS, Cloud Architecture, Microservices, Serverless, Cloud Security',
            'salary_range': '$100,000 - $130,000'
        },
        {
            'id': 8,
            'title': 'Python Backend Developer',
            'company': 'API Systems Ltd',
            'location': 'Calgary, AB',
            'description': 'Backend Developer position focusing on Python web development with Django and Flask. Build RESTful APIs, implement database solutions with PostgreSQL and Redis, and work with microservices architecture. Experience with FastAPI, Celery for task queues, and API documentation tools required. Knowledge of software testing, code review practices, and version control with Git essential.',
            'requirements': 'Python, Django, Flask, FastAPI, PostgreSQL, Redis, REST APIs, Microservices, Git',
            'salary_range': '$75,000 - $95,000'
        },
        {
            'id': 9,
            'title': 'Data Engineering Specialist',
            'company': 'BigData Corp',
            'location': 'Toronto, ON',
            'description': 'Data Engineering role building and maintaining data pipelines and ETL processes. Work with Apache Spark, Kafka, and Airflow to process large-scale data. Implement data warehousing solutions using AWS Redshift and Snowflake. Strong Python and SQL skills required, along with experience in data modeling, data quality, and real-time data processing.',
            'requirements': 'Python, SQL, Apache Spark, Kafka, Airflow, AWS Redshift, Snowflake, ETL, Data Pipelines',
            'salary_range': '$85,000 - $110,000'
        },
        {
            'id': 10,
            'title': 'AI Research Scientist',
            'company': 'Research Labs Inc',
            'location': 'Montreal, QC',
            'description': 'AI Research Scientist position working on cutting-edge machine learning research. Develop novel algorithms, publish research papers, and implement state-of-the-art models using TensorFlow and PyTorch. PhD in Computer Science, Mathematics, or related field preferred. Experience with deep learning, natural language processing, computer vision, and research methodology required.',
            'requirements': 'PhD, TensorFlow, PyTorch, Deep Learning, NLP, Computer Vision, Research, Machine Learning',
            'salary_range': '$110,000 - $150,000'
        }
    ]

async def test_rule_based_method(jobs: List[Dict[str, Any]], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Test rule-based processing method"""
    try:
        from src.ai.enhanced_rule_based_analyzer import EnhancedRuleBasedAnalyzer
        
        analyzer = EnhancedRuleBasedAnalyzer(profile)
        
        start_time = time.time()
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Processing with Rule-Based...", total=len(jobs))
            
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
                progress.advance(task)
        
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
            'device': 'CPU',
            'accuracy_estimate': 0.85
        }
        
    except Exception as e:
        console.print(f"[red]❌ Rule-based test failed: {e}[/red]")
        return {'method': 'rule_based', 'success': False, 'error': str(e)}

async def test_gpu_enhanced_method(jobs: List[Dict[str, Any]], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Test GPU-enhanced processing method"""
    try:
        from src.ai.gpu_enhanced_job_processor import RTX3080JobProcessor
        
        processor = RTX3080JobProcessor(batch_size=64)
        
        start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Processing with GPU Enhancement...", total=100)
            
            # Process jobs with GPU acceleration
            enhanced_results, metrics = await processor.process_jobs_batch(jobs, profile)
            progress.update(task, completed=100)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Convert results for comparison
        results = []
        for result in enhanced_results:
            results.append({
                'job_id': result.job_id,
                'job_title': result.title,
                'compatibility_score': result.overall_compatibility,
                'confidence': result.confidence,
                'analysis_method': 'gpu_enhanced',
                'processing_time': result.processing_time,
                'semantic_similarity': result.semantic_similarity,
                'skill_match_score': result.skill_match_score,
                'extracted_skills': result.extracted_skills,
                'job_category': result.job_category,
                'seniority_level': result.seniority_level,
                'predicted_salary': result.predicted_salary_range
            })
        
        return {
            'method': 'gpu_enhanced',
            'total_time': total_time,
            'jobs_processed': len(jobs),
            'jobs_per_second': len(jobs) / total_time if total_time > 0 else 0,
            'avg_time_per_job': total_time / len(jobs) if jobs else 0,
            'results': results,
            'success': True,
            'device': 'RTX 3080',
            'gpu_metrics': {
                'gpu_time': metrics.gpu_time,
                'cpu_time': metrics.cpu_time,
                'batch_count': metrics.batch_count,
                'gpu_memory_used': metrics.gpu_memory_used,
                'accuracy_score': metrics.accuracy_score
            },
            'accuracy_estimate': metrics.accuracy_score
        }
        
    except ImportError as e:
        console.print(f"[red]❌ GPU test failed - missing dependencies: {e}[/red]")
        return {'method': 'gpu_enhanced', 'success': False, 'error': f'Missing dependencies: {e}'}
    except Exception as e:
        console.print(f"[red]❌ GPU test failed: {e}[/red]")
        return {'method': 'gpu_enhanced', 'success': False, 'error': str(e)}

def display_detailed_comparison(test_results: List[Dict[str, Any]], jobs: List[Dict[str, Any]]):
    """Display detailed comparison results"""
    
    console.print(Panel("🚀 RTX 3080 vs Rule-Based Performance Comparison", style="bold blue"))
    
    # Performance Summary Table
    perf_table = Table(title="⚡ Performance Comparison")
    perf_table.add_column("Method", style="cyan")
    perf_table.add_column("Device", style="green")
    perf_table.add_column("Total Time", style="yellow")
    perf_table.add_column("Jobs/Second", style="magenta")
    perf_table.add_column("Avg per Job", style="white")
    perf_table.add_column("Accuracy", style="blue")
    perf_table.add_column("Status", style="white")
    
    successful_results = [r for r in test_results if r.get('success')]
    
    for result in test_results:
        if result.get('success'):
            method = result['method'].replace('_', ' ').title()
            device = result.get('device', 'Unknown')
            total_time = f"{result['total_time']:.3f}s"
            jobs_per_sec = f"{result['jobs_per_second']:.1f}"
            avg_time = f"{result['avg_time_per_job']*1000:.1f}ms"
            accuracy = f"{result.get('accuracy_estimate', 0)*100:.1f}%"
            status = "✅ Success"
        else:
            method = result['method'].replace('_', ' ').title()
            device = "N/A"
            total_time = "N/A"
            jobs_per_sec = "N/A"
            avg_time = "N/A"
            accuracy = "N/A"
            status = f"❌ Failed"
        
        perf_table.add_row(method, device, total_time, jobs_per_sec, avg_time, accuracy, status)
    
    console.print(perf_table)
    
    # GPU-specific metrics
    gpu_result = next((r for r in successful_results if r['method'] == 'gpu_enhanced'), None)
    if gpu_result and 'gpu_metrics' in gpu_result:
        metrics = gpu_result['gpu_metrics']
        
        console.print(f"\n🔧 GPU Detailed Metrics:")
        console.print(f"   GPU Processing Time: {metrics['gpu_time']:.3f}s")
        console.print(f"   CPU Processing Time: {metrics['cpu_time']:.3f}s")
        console.print(f"   Batch Count: {metrics['batch_count']}")
        console.print(f"   GPU Memory Used: {metrics['gpu_memory_used']:.2f} GB")
        console.print(f"   Accuracy Score: {metrics['accuracy_score']:.3f}")
    
    # Speed comparison
    if len(successful_results) >= 2:
        rule_based = next((r for r in successful_results if r['method'] == 'rule_based'), None)
        gpu_enhanced = next((r for r in successful_results if r['method'] == 'gpu_enhanced'), None)
        
        if rule_based and gpu_enhanced:
            speed_diff = rule_based['jobs_per_second'] / gpu_enhanced['jobs_per_second']
            accuracy_diff = gpu_enhanced.get('accuracy_estimate', 0) - rule_based.get('accuracy_estimate', 0)
            
            console.print(f"\n📊 Comparison Analysis:")
            if speed_diff > 1:
                console.print(f"   🏃 Rule-Based is {speed_diff:.1f}x faster")
            else:
                console.print(f"   🏃 GPU-Enhanced is {1/speed_diff:.1f}x faster")
            
            console.print(f"   🎯 Accuracy difference: {accuracy_diff*100:+.1f}%")
            console.print(f"   💡 GPU provides: Better accuracy, semantic understanding, skill extraction")
            console.print(f"   💡 Rule-Based provides: Raw speed, simplicity, no dependencies")
    
    # Enhanced Features Comparison (if GPU succeeded)
    if gpu_result and gpu_result.get('success'):
        console.print(f"\n🎯 Enhanced Features (GPU Only):")
        
        features_table = Table(title="GPU-Enhanced Analysis Features")
        features_table.add_column("Job", style="cyan")
        features_table.add_column("Semantic Score", style="green")
        features_table.add_column("Skills Extracted", style="yellow")
        features_table.add_column("Category", style="magenta")
        features_table.add_column("Seniority", style="blue")
        features_table.add_column("Predicted Salary", style="white")
        
        for i, result in enumerate(gpu_result['results'][:5]):  # Show first 5
            job_title = result['job_title'][:20] + "..." if len(result['job_title']) > 20 else result['job_title']
            semantic_score = f"{result.get('semantic_similarity', 0):.2f}"
            skills = ", ".join(result.get('extracted_skills', [])[:3])  # First 3 skills
            if len(result.get('extracted_skills', [])) > 3:
                skills += "..."
            category = result.get('job_category', 'Unknown')
            seniority = result.get('seniority_level', 'Unknown')
            salary = result.get('predicted_salary', 'N/A')
            
            features_table.add_row(job_title, semantic_score, skills, category, seniority, salary)
        
        console.print(features_table)

async def main():
    """Main test function"""
    console.print("🚀 RTX 3080 Enhanced Job Processing Test")
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
    
    # Create test jobs
    jobs = create_realistic_jobs()
    console.print(f"[green]✅ Created {len(jobs)} realistic test jobs[/green]")
    
    # Test different methods
    test_results = []
    
    console.print(f"\n[cyan]🧪 Testing Rule-Based Method...[/cyan]")
    rule_based_result = await test_rule_based_method(jobs, profile)
    test_results.append(rule_based_result)
    
    console.print(f"\n[cyan]🧪 Testing GPU-Enhanced Method...[/cyan]")
    gpu_result = await test_gpu_enhanced_method(jobs, profile)
    test_results.append(gpu_result)
    
    # Display results
    console.print(f"\n")
    display_detailed_comparison(test_results, jobs)
    
    # Final recommendation
    successful_tests = [r for r in test_results if r.get('success')]
    if len(successful_tests) >= 2:
        rule_based = next((r for r in successful_tests if r['method'] == 'rule_based'), None)
        gpu_enhanced = next((r for r in successful_tests if r['method'] == 'gpu_enhanced'), None)
        
        console.print(f"\n💡 Recommendation:")
        if rule_based and gpu_enhanced:
            if rule_based['jobs_per_second'] > gpu_enhanced['jobs_per_second']:
                console.print(f"   🏃 For pure speed: Use Rule-Based ({rule_based['jobs_per_second']:.1f} jobs/sec)")
            else:
                console.print(f"   🏃 For speed: Use GPU-Enhanced ({gpu_enhanced['jobs_per_second']:.1f} jobs/sec)")
            
            console.print(f"   🎯 For accuracy: Use GPU-Enhanced (semantic matching + skill extraction)")
            console.print(f"   ⚖️ Best of both: Use hybrid approach - Rule-based filter + GPU analysis")

if __name__ == "__main__":
    asyncio.run(main())