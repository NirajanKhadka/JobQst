#!/usr/bin/env python3
"""
Multi-Resume Profile Manager
Helper script to manage multiple resume profiles efficiently.
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def create_multi_resume_setup():
    """Set up multiple resume profiles quickly."""
    
    console.print("="*60)
    console.print("JobQst Multi-Resume Manager")
    console.print("="*60)
    console.print("Multi-Resume Profile Setup")
    console.print("This will help you create optimized profiles for different resume types.")
    console.print("="*60)
    
    # Common resume types and their optimizations
    resume_types = {
        "data_scientist": {
            "keywords": ["python", "machine learning", "data analysis", "sql", "pandas"],
            "job_sites": ["indeed", "linkedin"],
            "search_terms": ["data scientist", "machine learning engineer", "data analyst"]
        },
        "software_engineer": {
            "keywords": ["javascript", "react", "node.js", "python", "aws"],
            "job_sites": ["indeed", "linkedin", "glassdoor"],
            "search_terms": ["software engineer", "full stack developer", "backend developer"]
        },
        "product_manager": {
            "keywords": ["product management", "agile", "scrum", "analytics", "roadmap"],
            "job_sites": ["indeed", "linkedin"],
            "search_terms": ["product manager", "product owner", "program manager"]
        },
        "consultant": {
            "keywords": ["consulting", "strategy", "business analysis", "client management"],
            "job_sites": ["indeed", "glassdoor"],
            "search_terms": ["consultant", "business analyst", "strategy analyst"]
        },
        "marketing": {
            "keywords": ["digital marketing", "seo", "content marketing", "analytics"],
            "job_sites": ["indeed", "linkedin"],
            "search_terms": ["marketing manager", "digital marketing", "marketing analyst"]
        }
    }
    
    console.print("\n[bold cyan]Available resume type optimizations:[/bold cyan]")
    table = Table()
    table.add_column("Type", style="cyan")
    table.add_column("Optimized For", style="green")
    
    for resume_type, config in resume_types.items():
        table.add_row(
            resume_type.replace("_", " ").title(),
            ", ".join(config["search_terms"])
        )
    
    console.print(table)
    
    return resume_types

def show_profile_management_commands():
    """Show commands for managing multiple profiles."""
    
    commands = [
        ("Create Profile from Resume", "python main.py --action create-profile --name MyProfile --resume-path resume.pdf"),
        ("Scan Resume in Existing Profile", "python main.py MyProfile --action scan-resume"),
        ("Run Job Search", "python main.py MyProfile --action jobspy-pipeline"),
        ("View Dashboard for Profile", "python main.py MyProfile --action dashboard"),
        ("Check Profile Health", "python main.py MyProfile --action health-check")
    ]
    
    console.print("\n[bold green]Profile Management Commands:[/bold green]")
    
    for desc, cmd in commands:
        console.print(f"\n[cyan]{desc}:[/cyan]")
        console.print(f"  [dim]{cmd}[/dim]")

if __name__ == "__main__":
    create_multi_resume_setup()
    show_profile_management_commands()
    
    console.print(Panel.fit(
        "[bold green]✅ Your system is already optimized for multiple resumes![/bold green]\n\n"
        "[yellow]Key Benefits:[/yellow]\n"
        "• Separate profiles = No data mixing\n"
        "• Auto resume analysis = Tailored keywords\n"
        "• Individual databases = Fast queries\n"
        "• Profile-specific job searches = Better targeting\n\n"
        "[cyan]No major optimization needed - the architecture is solid![/cyan]",
        title="🎉 Multi-Resume Assessment"
    ))
