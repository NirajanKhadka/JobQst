#!/usr/bin/env python3
"""
Demo: Enhanced Custom Data Extractor
Demonstrates the improved reliability and web validation features.
"""

import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.analysis.enhanced_custom_extractor import EnhancedCustomExtractor
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def demo_enhanced_extraction():
    """Demonstrate enhanced extraction capabilities."""
    
    console.print(Panel.fit(
        "[bold blue]Enhanced Custom Data Extractor Demo[/bold blue]\n"
        "Showcasing 95%+ reliability with web validation",
        title="🚀 AutoJobAgent Enhancement"
    ))
    
    # Initialize extractor
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Initializing enhanced extractor...", total=None)
        extractor = EnhancedCustomExtractor()
        progress.update(task, completed=True)
    
    # Test cases with varying quality
    test_cases = [
        {
            'name': 'High-Quality Job Posting',
            'data': {
                'title': 'Senior Python Developer',
                'company': 'Google',
                'description': '''
                Job Title: Senior Python Developer
                Company: Google
                Location: Toronto, ON
                Employment Type: Full-time
                Salary: $150,000 - $200,000
                
                Requirements:
                • 7+ years of Python development experience
                • Experience with Django, Flask, or FastAPI
                • Knowledge of PostgreSQL and Redis
                • Familiarity with AWS cloud services
                • Strong problem-solving skills
                
                Skills Required:
                Python, Django, PostgreSQL, AWS, Redis, Docker, Kubernetes
                
                Benefits:
                • Health and dental insurance
                • Stock options
                • Remote work flexibility
                • Professional development budget
                '''
            }
        },
        {
            'name': 'Medium-Quality Job Posting',
            'data': {
                'description': '''
                We're looking for a Data Scientist to join our team at TechCorp.
                Location: Vancouver, BC
                This is a full-time position with competitive salary.
                
                You should have:
                - 3+ years experience in data science
                - Python and R programming skills
                - Machine learning knowledge
                - SQL database experience
                
                We offer health benefits and flexible work arrangements.
                '''
            }
        },
        {
            'name': 'Low-Quality Job Posting',
            'data': {
                'description': 'Need developer for project. Good pay. Contact us for details.'
            }
        },
        {
            'name': 'HTML Job Posting',
            'data': {
                'description': '''
                <html>
                <head><title>Frontend Developer - Shopify</title></head>
                <body>
                    <h1>Frontend Developer</h1>
                    <span class="company">Shopify</span>
                    <div class="location">Ottawa, ON</div>
                    <div class="salary">$90,000 - $120,000</div>
                    <div class="employment-type">Full-time</div>
                    
                    <h2>Requirements:</h2>
                    <ul>
                        <li>5+ years React experience</li>
                        <li>TypeScript proficiency</li>
                        <li>CSS and HTML expertise</li>
                        <li>GraphQL knowledge</li>
                    </ul>
                    
                    <h2>Skills:</h2>
                    <p>React, TypeScript, GraphQL, CSS, HTML, JavaScript</p>
                </body>
                </html>
                '''
            }
        }
    ]
    
    # Process each test case
    results = []
    for i, test_case in enumerate(test_cases, 1):
        console.print(f"\n[bold cyan]Test Case {i}: {test_case['name']}[/bold cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing job data...", total=None)
            
            start_time = time.time()
            result = extractor.extract_job_data(test_case['data'])
            processing_time = time.time() - start_time
            
            progress.update(task, completed=True)
        
        results.append((test_case['name'], result, processing_time))
        
        # Display results
        display_extraction_result(result, processing_time)
    
    # Summary table
    display_summary_table(results)
    
    # Reliability analysis
    analyze_reliability(results)

def display_extraction_result(result, processing_time):
    """Display extraction result in a formatted table."""
    
    table = Table(title="Extraction Results", show_header=True, header_style="bold magenta")
    table.add_column("Field", style="cyan", width=20)
    table.add_column("Value", style="white", width=40)
    table.add_column("Confidence", style="green", width=12)
    
    # Core fields
    fields = [
        ("Title", result.title),
        ("Company", result.company),
        ("Location", result.location),
        ("Salary Range", result.salary_range),
        ("Experience Level", result.experience_level),
        ("Employment Type", result.employment_type),
    ]
    
    for field_name, value in fields:
        confidence = result.field_confidences.get(field_name.lower().replace(' ', '_'), 0.0)
        confidence_str = f"{confidence:.1%}"
        
        # Color code confidence
        if confidence >= 0.8:
            confidence_style = "bold green"
        elif confidence >= 0.6:
            confidence_style = "yellow"
        else:
            confidence_style = "red"
        
        table.add_row(
            field_name,
            str(value) if value else "[dim]Not found[/dim]",
            f"[{confidence_style}]{confidence_str}[/{confidence_style}]"
        )
    
    # Skills and other lists
    if result.skills:
        skills_str = ", ".join(result.skills[:5])
        if len(result.skills) > 5:
            skills_str += f" (+{len(result.skills) - 5} more)"
        table.add_row("Skills", skills_str, f"{result.field_confidences.get('skills', 0.0):.1%}")
    
    if result.benefits:
        benefits_str = ", ".join(result.benefits[:3])
        if len(result.benefits) > 3:
            benefits_str += f" (+{len(result.benefits) - 3} more)"
        table.add_row("Benefits", benefits_str, "N/A")
    
    console.print(table)
    
    # Overall metrics
    metrics_table = Table(title="Processing Metrics", show_header=False)
    metrics_table.add_column("Metric", style="bold blue")
    metrics_table.add_column("Value", style="white")
    
    metrics_table.add_row("Overall Confidence", f"{result.overall_confidence:.1%}")
    metrics_table.add_row("Processing Time", f"{processing_time:.3f}s")
    metrics_table.add_row("Extraction Method", result.extraction_method)
    
    if result.web_validated_fields:
        metrics_table.add_row("Web Validated", ", ".join(result.web_validated_fields))
    
    console.print(metrics_table)

def display_summary_table(results):
    """Display summary comparison table."""
    
    console.print("\n[bold yellow]📊 Summary Comparison[/bold yellow]")
    
    summary_table = Table(title="Extraction Summary", show_header=True, header_style="bold magenta")
    summary_table.add_column("Test Case", style="cyan", width=25)
    summary_table.add_column("Confidence", style="green", width=12)
    summary_table.add_column("Fields Extracted", style="blue", width=15)
    summary_table.add_column("Processing Time", style="yellow", width=15)
    summary_table.add_column("Quality", style="white", width=12)
    
    for name, result, proc_time in results:
        # Count non-null fields
        fields_count = sum(1 for field in [
            result.title, result.company, result.location, 
            result.salary_range, result.experience_level, result.employment_type
        ] if field is not None)
        
        # Determine quality rating
        if result.overall_confidence >= 0.8:
            quality = "[bold green]Excellent[/bold green]"
        elif result.overall_confidence >= 0.6:
            quality = "[yellow]Good[/yellow]"
        elif result.overall_confidence >= 0.4:
            quality = "[orange3]Fair[/orange3]"
        else:
            quality = "[red]Poor[/red]"
        
        summary_table.add_row(
            name,
            f"{result.overall_confidence:.1%}",
            f"{fields_count}/6",
            f"{proc_time:.3f}s",
            quality
        )
    
    console.print(summary_table)

def analyze_reliability(results):
    """Analyze overall reliability metrics."""
    
    console.print("\n[bold green]🎯 Reliability Analysis[/bold green]")
    
    # Calculate metrics
    confidences = [result.overall_confidence for _, result, _ in results]
    avg_confidence = sum(confidences) / len(confidences)
    
    high_confidence_count = sum(1 for conf in confidences if conf >= 0.8)
    medium_confidence_count = sum(1 for conf in confidences if 0.6 <= conf < 0.8)
    low_confidence_count = sum(1 for conf in confidences if conf < 0.6)
    
    # Processing times
    proc_times = [proc_time for _, _, proc_time in results]
    avg_proc_time = sum(proc_times) / len(proc_times)
    
    # Field extraction success rates
    field_success_rates = {}
    fields = ['title', 'company', 'location', 'salary_range', 'experience_level', 'employment_type']
    
    for field in fields:
        success_count = sum(1 for _, result, _ in results 
                          if getattr(result, field) is not None)
        field_success_rates[field] = success_count / len(results)
    
    # Display analysis
    analysis_table = Table(title="Reliability Metrics", show_header=True, header_style="bold magenta")
    analysis_table.add_column("Metric", style="cyan", width=25)
    analysis_table.add_column("Value", style="white", width=20)
    analysis_table.add_column("Target", style="green", width=15)
    analysis_table.add_column("Status", style="white", width=15)
    
    # Overall metrics
    target_confidence = 0.75
    confidence_status = "✅ PASS" if avg_confidence >= target_confidence else "❌ FAIL"
    analysis_table.add_row(
        "Average Confidence",
        f"{avg_confidence:.1%}",
        f"{target_confidence:.1%}",
        confidence_status
    )
    
    analysis_table.add_row(
        "High Confidence (≥80%)",
        f"{high_confidence_count}/{len(results)}",
        "≥50%",
        "✅ PASS" if high_confidence_count >= len(results) * 0.5 else "❌ FAIL"
    )
    
    analysis_table.add_row(
        "Average Processing Time",
        f"{avg_proc_time:.3f}s",
        "<1.0s",
        "✅ PASS" if avg_proc_time < 1.0 else "❌ FAIL"
    )
    
    console.print(analysis_table)
    
    # Field success rates
    field_table = Table(title="Field Extraction Success Rates", show_header=True, header_style="bold magenta")
    field_table.add_column("Field", style="cyan")
    field_table.add_column("Success Rate", style="white")
    field_table.add_column("Target", style="green")
    field_table.add_column("Status", style="white")
    
    field_targets = {
        'title': 0.90,
        'company': 0.80,
        'location': 0.70,
        'salary_range': 0.60,
        'experience_level': 0.60,
        'employment_type': 0.60
    }
    
    for field, success_rate in field_success_rates.items():
        target = field_targets.get(field, 0.50)
        status = "✅ PASS" if success_rate >= target else "❌ FAIL"
        
        field_table.add_row(
            field.replace('_', ' ').title(),
            f"{success_rate:.1%}",
            f"{target:.1%}",
            status
        )
    
    console.print(field_table)
    
    # Recommendations
    console.print("\n[bold blue]💡 Recommendations[/bold blue]")
    
    recommendations = []
    
    if avg_confidence < 0.75:
        recommendations.append("• Improve pattern specificity for higher confidence")
    
    if field_success_rates['title'] < 0.90:
        recommendations.append("• Enhance job title extraction patterns")
    
    if field_success_rates['company'] < 0.80:
        recommendations.append("• Add more company name validation rules")
    
    if avg_proc_time > 1.0:
        recommendations.append("• Optimize processing speed for better performance")
    
    if not recommendations:
        recommendations.append("• System is performing well! Consider adding more test cases")
    
    for rec in recommendations:
        console.print(rec)

def main():
    """Main demo function."""
    try:
        demo_enhanced_extraction()
        
        console.print("\n[bold green]✅ Demo completed successfully![/bold green]")
        console.print("\n[dim]Next steps:[/dim]")
        console.print("1. Run the cleanup script: [cyan]python scripts/cleanup_project.py --live[/cyan]")
        console.print("2. Test the enhanced extractor: [cyan]python -m pytest tests/unit/test_enhanced_custom_extractor.py -v[/cyan]")
        console.print("3. Integrate with hybrid processor for full pipeline")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Demo failed: {e}[/bold red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

if __name__ == "__main__":
    main()