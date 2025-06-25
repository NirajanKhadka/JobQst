"""
Test Enhanced Job Analysis
Demonstrates the new job analysis capabilities for extracting detailed requirements,
keywords, experience levels, and calculating match scores.
"""

import sys
from pathlib import Path

# Add project root and src directory to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.utils.job_analysis_engine import JobAnalysisEngine

console = Console()

def test_job_analysis():
    """Test the job analyzer with sample job descriptions"""
    
    console.print(Panel.fit("🔍 Testing Enhanced Job Analysis", style="bold blue"))
    
    # Initialize analyzer
    analyzer = JobAnalysisEngine(profile_name="test")  # Disable AI for testing
    
    # Sample job descriptions
    sample_jobs = [
        {
            "title": "Senior Data Analyst",
            "company": "RBC",
            "summary": """
            We are seeking a Senior Data Analyst with 5+ years of experience to join our team.
            
            Required Skills:
            - Python programming (pandas, numpy)
            - SQL and database management
            - Tableau or Power BI for visualization
            - Excel advanced functions
            - Bachelor's degree in Computer Science or related field
            
            Preferred Skills:
            - Machine learning experience
            - AWS or Azure cloud platforms
            - R programming language
            
            This is a full-time, hybrid position offering competitive salary $85,000 - $110,000 CAD,
            health benefits, and professional development opportunities.
            """,
            "url": "https://rbc.wd3.myworkdayjobs.com/example"
        },
        {
            "title": "Junior Python Developer",
            "company": "Shopify",
            "summary": """
            Entry-level Python Developer position for recent graduates.
            
            Requirements:
            - Python programming fundamentals
            - Basic understanding of web development
            - Git version control
            - High school diploma minimum
            
            Nice to have:
            - Django or Flask experience
            - JavaScript knowledge
            - Docker familiarity
            
            Full-time remote position with startup culture and stock options.
            """,
            "url": "https://jobs.lever.co/shopify/example"
        },
        {
            "title": "Principal Data Scientist",
            "company": "Microsoft",
            "summary": """
            Principal Data Scientist role requiring 10+ years of experience leading data science teams.
            
            Must have:
            - PhD in Computer Science, Statistics, or related field
            - Advanced machine learning and deep learning
            - Python, R, and Scala programming
            - Big data technologies (Spark, Hadoop)
            - Leadership and mentoring experience
            
            Preferred:
            - Published research papers
            - Azure ML platform experience
            - MLOps and model deployment
            
            Executive-level position, $150,000 - $200,000 CAD, full benefits package.
            On-site position in Toronto with flexible hours.
            """,
            "url": "https://careers.microsoft.com/example"
        }
    ]
    
    # Sample user profile
    user_profile = {
        "name": "Nirajan Khadka",
        "keywords": ["python", "sql", "tableau", "excel", "pandas", "data analysis", "machine learning"],
        "experience_level": "mid",
        "education": "bachelor"
    }
    
    console.print(f"\n[bold]👤 User Profile:[/bold]")
    console.print(f"Skills: {', '.join(user_profile['keywords'])}")
    console.print(f"Experience Level: {user_profile['experience_level']}")
    console.print(f"Education: {user_profile['education']}")
    
    # Analyze each job
    results = []
    for i, job in enumerate(sample_jobs, 1):
        console.print(f"\n[bold cyan]📋 Analyzing Job {i}: {job['title']} at {job['company']}[/bold cyan]")
        
        # Analyze job
        enhanced_job = analyzer.analyze_job_deep(job)
        requirements = enhanced_job["requirements"]
        
        # Calculate match score
        match_score = analyzer.calculate_job_match_score(requirements, user_profile)
        
        results.append({
            "job": job,
            "requirements": requirements,
            "match_score": match_score,
            "enhanced": enhanced_job
        })
        
        # Display results
        display_job_analysis(job, requirements, match_score)
    
    # Summary table
    display_summary_table(results)
    
    return results

def display_job_analysis(job: dict, requirements: dict, match_score: float):
    """Display detailed analysis for a single job"""
    
    # Create analysis table
    table = Table(title=f"Analysis: {job['title']}")
    table.add_column("Category", style="cyan")
    table.add_column("Details", style="white")
    
    # Add rows
    table.add_row("Experience Level", requirements.experience_level.title())
    table.add_row("Years Required", str(requirements.years_experience) if requirements.years_experience else "Not specified")
    table.add_row("Education", requirements.education_level.replace("_", " ").title())
    table.add_row("Required Skills", ", ".join(requirements.required_skills[:5]) + ("..." if len(requirements.required_skills) > 5 else ""))
    table.add_row("Preferred Skills", ", ".join(requirements.preferred_skills[:3]) + ("..." if len(requirements.preferred_skills) > 3 else ""))
    table.add_row("Remote Options", requirements.remote_options.title())
    table.add_row("Employment Type", requirements.employment_type.replace("_", " ").title())
    table.add_row("Industry", requirements.industry.title())
    table.add_row("Salary Range", f"${requirements.salary_range[0]:,} - ${requirements.salary_range[1]:,}" if requirements.salary_range else "Not specified")
    
    # Match score with color coding
    if match_score >= 0.8:
        match_color = "bright_green"
        recommendation = "🎯 Excellent Match - Apply Now!"
    elif match_score >= 0.6:
        match_color = "yellow"
        recommendation = "✅ Good Match - Consider Applying"
    elif match_score >= 0.4:
        match_color = "orange1"
        recommendation = "⚠️ Partial Match - Review Requirements"
    else:
        match_color = "red"
        recommendation = "❌ Poor Match - Skip"
    
    table.add_row("Match Score", f"[{match_color}]{match_score:.2f} ({match_score*100:.0f}%)[/{match_color}]")
    table.add_row("Recommendation", f"[{match_color}]{recommendation}[/{match_color}]")
    
    console.print(table)

def display_summary_table(results: list):
    """Display summary table of all analyzed jobs"""
    
    console.print(f"\n[bold]📊 Job Analysis Summary[/bold]")
    
    # Create summary table
    table = Table(title="Job Match Summary")
    table.add_column("Job Title", style="cyan")
    table.add_column("Company", style="white")
    table.add_column("Experience", style="yellow")
    table.add_column("Required Skills", style="green")
    table.add_column("Match Score", style="bold")
    table.add_column("Recommendation", style="bold")
    
    # Sort by match score (highest first)
    sorted_results = sorted(results, key=lambda x: x["match_score"], reverse=True)
    
    for result in sorted_results:
        job = result["job"]
        requirements = result["requirements"]
        match_score = result["match_score"]
        
        # Color code match score
        if match_score >= 0.8:
            score_color = "bright_green"
            rec_emoji = "🎯"
        elif match_score >= 0.6:
            score_color = "yellow"
            rec_emoji = "✅"
        elif match_score >= 0.4:
            score_color = "orange1"
            rec_emoji = "⚠️"
        else:
            score_color = "red"
            rec_emoji = "❌"
        
        table.add_row(
            job["title"],
            job["company"],
            requirements.experience_level.title(),
            f"{len(requirements.required_skills)} skills",
            f"[{score_color}]{match_score:.2f}[/{score_color}]",
            f"{rec_emoji} {match_score*100:.0f}%"
        )
    
    console.print(table)
    
    # Recommendations
    console.print(f"\n[bold green]🎯 Top Recommendations:[/bold green]")
    top_matches = [r for r in sorted_results if r["match_score"] >= 0.6]
    
    if top_matches:
        for i, result in enumerate(top_matches[:3], 1):
            job = result["job"]
            match_score = result["match_score"]
            console.print(f"{i}. {job['title']} at {job['company']} ({match_score:.2f} match)")
    else:
        console.print("No high-match jobs found. Consider expanding your skill set or looking at different roles.")

def test_skill_extraction():
    """Test skill extraction capabilities"""
    
    console.print(Panel.fit("🔧 Testing Skill Extraction", style="bold green"))
    
    analyzer = JobAnalysisEngine(profile_name="test")
    
    test_descriptions = [
        "Looking for Python developer with Django, PostgreSQL, and AWS experience",
        "Data analyst needed with Tableau, Excel, SQL Server, and R programming skills",
        "Full-stack engineer: React, Node.js, MongoDB, Docker, Kubernetes required"
    ]
    
    for i, desc in enumerate(test_descriptions, 1):
        console.print(f"\n[cyan]Test {i}:[/cyan] {desc}")
        
        required, preferred = analyzer._extract_skills(desc.lower())
        console.print(f"[green]Required:[/green] {', '.join(required)}")
        console.print(f"[yellow]Preferred:[/yellow] {', '.join(preferred)}")

if __name__ == "__main__":
    console.print("[bold blue]🚀 Starting Enhanced Job Analysis Tests[/bold blue]\n")
    
    # Test skill extraction
    test_skill_extraction()
    
    console.print("\n" + "="*60 + "\n")
    
    # Test full job analysis
    results = test_job_analysis()
    
    console.print(f"\n[bold green]✅ Testing completed! Analyzed {len(results)} jobs.[/bold green]")
    console.print("[cyan]💡 This enhanced analysis will make auto-apply much more efficient by targeting the best-matching jobs![/cyan]")
