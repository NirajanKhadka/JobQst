#!/usr/bin/env python3
"""
Test Fixed Job Scraper
Verifies that the job scraper is now working properly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import sqlite3
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def test_database_fixes():
    """Test that the database fixes were applied correctly."""
    
    console.print("[bold blue]🔍 Testing Database Fixes[/bold blue]")
    
    # Connect to the database
    db_path = "profiles/Nirajan/Nirajan.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for missing titles
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE title IS NULL OR title = '' OR title = 'Unknown Title' OR title = 'Job from URL'")
    missing_titles = cursor.fetchone()[0]
    
    # Check for missing companies
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE company IS NULL OR company = '' OR company = 'Unknown Company'")
    missing_companies = cursor.fetchone()[0]
    
    # Check for missing locations
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE location IS NULL OR location = '' OR location = 'Unknown Location'")
    missing_locations = cursor.fetchone()[0]
    
    # Check for missing salaries
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE salary_range IS NULL OR salary_range = ''")
    missing_salaries = cursor.fetchone()[0]
    
    # Check for missing keywords
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE keywords IS NULL OR keywords = ''")
    missing_keywords = cursor.fetchone()[0]
    
    # Check for missing job descriptions
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE job_description IS NULL OR job_description = ''")
    missing_descriptions = cursor.fetchone()[0]
    
    # Check for unprocessed jobs
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status != 'processed'")
    unprocessed_jobs = cursor.fetchone()[0]
    
    # Get sample jobs
    cursor.execute("""
        SELECT id, title, company, location, salary_range, keywords, match_score 
        FROM jobs 
        ORDER BY match_score DESC
        LIMIT 5
    """)
    sample_jobs = cursor.fetchall()
    
    conn.close()
    
    # Display results
    console.print(f"[green]✅ Missing titles: {missing_titles}[/green]")
    console.print(f"[green]✅ Missing companies: {missing_companies}[/green]")
    console.print(f"[green]✅ Missing locations: {missing_locations}[/green]")
    console.print(f"[green]✅ Missing salaries: {missing_salaries}[/green]")
    console.print(f"[green]✅ Missing keywords: {missing_keywords}[/green]")
    console.print(f"[green]✅ Missing descriptions: {missing_descriptions}[/green]")
    console.print(f"[green]✅ Unprocessed jobs: {unprocessed_jobs}[/green]")
    
    # Display sample jobs
    console.print("\n[bold cyan]📋 Sample Jobs:[/bold cyan]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Location")
    table.add_column("Salary Range")
    table.add_column("Keywords", max_width=30)
    table.add_column("Match Score")
    
    for job in sample_jobs:
        table.add_row(
            str(job[0]),
            job[1] or "MISSING",
            job[2] or "MISSING",
            job[3] or "MISSING",
            job[4] or "MISSING",
            job[5][:30] + "..." if job[5] and len(job[5]) > 30 else (job[5] or "MISSING"),
            str(job[6])
        )
    
    console.print(table)
    
    # Overall assessment
    all_fixed = (
        missing_titles == 0 and
        missing_companies == 0 and
        missing_locations == 0 and
        missing_salaries == 0 and
        missing_keywords <= 5 and  # Allow a few missing keywords
        missing_descriptions == 0 and
        unprocessed_jobs == 0
    )
    
    if all_fixed:
        console.print(Panel(
            "[bold green]🎉 ALL FIXES VERIFIED![/bold green]\n"
            "[cyan]The job processing system is now working correctly.[/cyan]",
            title="SUCCESS",
            style="bold green"
        ))
    else:
        console.print(Panel(
            "[bold yellow]⚠️ SOME ISSUES REMAIN[/bold yellow]\n"
            "[yellow]Some issues still need to be addressed.[/yellow]",
            title="WARNING",
            style="bold yellow"
        ))
    
    return all_fixed

if __name__ == "__main__":
    console.print(Panel(
        "[bold blue]🧪 TESTING FIXED JOB SCRAPER[/bold blue]\n"
        "[cyan]Verifying that the job scraper is now working properly...[/cyan]",
        title="TEST FIXED SCRAPER",
        style="bold blue"
    ))
    
    all_fixed = test_database_fixes()
    
    if all_fixed:
        console.print("[bold green]✅ All tests passed![/bold green]")
    else:
        console.print("[bold yellow]⚠️ Some tests failed![/bold yellow]")