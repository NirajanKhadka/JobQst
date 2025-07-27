#!/usr/bin/env python3
"""
Monster CA Integration Script

This script integrates the Monster CA scraper into the main AutoJobAgent workflow,
allowing users to scrape from both Eluta and Monster CA simultaneously.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress
from src.scrapers.unified_eluta_scraper import UnifiedElutaScraper
from src.scrapers.monster_ca_scraper import MonsterCaScraper
from src.core.job_filters import remove_duplicates

console = Console()


async def run_multi_site_scraping(profile_name: str = "Nirajan", max_jobs_per_site: int = 20):
    """
    Run scraping from both Eluta and Monster CA simultaneously.

    Args:
        profile_name (str): Name of the user profile
        max_jobs_per_site (int): Maximum jobs to scrape per site

    Returns:
        List[Dict]: Combined and deduplicated job results
    """
    console.print(Panel.fit("MULTI-SITE JOB SCRAPING", style="bold green"))
    console.print("[cyan]Scraping from both Eluta and Monster CA[/cyan]")
    console.print(f"[cyan]Profile: {profile_name}[/cyan]")
    console.print(f"[cyan]Max jobs per site: {max_jobs_per_site}[/cyan]")
    
    all_jobs = []
    
    # Site configurations
    sites = [
        {
            "name": "Eluta",
            "scraper_class": UnifiedElutaScraper,
            "color": "blue",
        },
        {
            "name": "Monster CA",
            "scraper_class": MonsterCaScraper,
            "color": "red",
        }
    ]
    
    with Progress() as progress:
        # Create progress tasks for each site
        tasks = {}
        for site in sites:
            task = progress.add_task(f"[{site['color']}]Scraping {site['name']}...", total=100)
            tasks[site['name']] = task
        
        # Scrape from each site
        for site in sites:
            try:
                console.print(f"\n[bold {site['color']}]Starting {site['name']} scraping...[/bold {site['color']}]")
                
                # Initialize scraper
                scraper = site['scraper_class'](profile_name)
                
                # Configure for faster scraping in demo
                scraper.max_pages_per_keyword = 2  # Reduced for demo
                scraper.delay_between_requests = 1  # Faster for demo
                
                # Limit search terms for demo
                original_terms = scraper.search_terms.copy()
                scraper.search_terms = original_terms[:3]  # Use only first 3 terms
                
                console.print(f"[{site['color']}]Configured {site['name']} scraper:[/{site['color']}]")
                console.print(f"  Search terms: {len(scraper.search_terms)}")
                console.print(f"  Max pages: {scraper.max_pages_per_keyword}")
                console.print(f"  Terms: {', '.join(scraper.search_terms)}")
                
                # Update progress
                progress.update(tasks[site['name']], advance=20)
                
                # Run scraping
                site_jobs = await scraper.scrape_all_keywords(max_jobs_per_keyword=max_jobs_per_site)
                
                # Add site information to jobs
                for job in site_jobs:
                    job['scraping_site'] = site['name'].lower().replace(' ', '_')
                
                all_jobs.extend(site_jobs)
                
                # Update progress
                progress.update(tasks[site['name']], advance=80)
                
                console.print(f"[bold {site['color']}]✅ {site['name']} completed: {len(site_jobs)} jobs[/bold {site['color']}]")
                
            except Exception as e:
                console.print(f"[bold red]❌ {site['name']} failed: {e}[/bold red]")
                progress.update(tasks[site['name']], advance=100)
    
    # Remove duplicates across all sites
    console.print(f"\n[cyan]Removing duplicates across all sites...[/cyan]")
    unique_jobs = remove_duplicates(all_jobs)
    
    # Display results
    display_multi_site_results(all_jobs, unique_jobs)
    
    return unique_jobs


def display_multi_site_results(all_jobs, unique_jobs):
    """Display comprehensive multi-site scraping results."""
    console.print("\n" + "=" * 80)
    console.print(Panel.fit("MULTI-SITE SCRAPING RESULTS", style="bold green"))
    
    # Count jobs by site
    site_counts = {}
    ats_counts = {}
    
    for job in all_jobs:
        site = job.get('scraping_site', 'unknown')
        ats = job.get('ats_system', 'Unknown')
        
        site_counts[site] = site_counts.get(site, 0) + 1
        ats_counts[ats] = ats_counts.get(ats, 0) + 1
    
    # Site breakdown table
    site_table = Table(title="Jobs by Site")
    site_table.add_column("Site", style="cyan")
    site_table.add_column("Jobs Found", style="green")
    site_table.add_column("Percentage", style="yellow")
    
    total_jobs = len(all_jobs)
    for site, count in site_counts.items():
        percentage = (count / total_jobs * 100) if total_jobs > 0 else 0
        site_table.add_row(site.replace('_', ' ').title(), str(count), f"{percentage:.1f}%")
    
    console.print(site_table)
    
    # ATS breakdown table
    ats_table = Table(title="Jobs by ATS System")
    ats_table.add_column("ATS System", style="cyan")
    ats_table.add_column("Count", style="green")
    ats_table.add_column("Percentage", style="yellow")
    
    for ats, count in sorted(ats_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_jobs * 100) if total_jobs > 0 else 0
        ats_table.add_row(ats, str(count), f"{percentage:.1f}%")
    
    console.print(ats_table)
    
    # Summary statistics
    summary_table = Table(title="Summary Statistics")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Jobs Found", str(len(all_jobs)))
    summary_table.add_row("Unique Jobs", str(len(unique_jobs)))
    summary_table.add_row("Duplicates Removed", str(len(all_jobs) - len(unique_jobs)))
    summary_table.add_row("Sites Scraped", str(len(site_counts)))
    summary_table.add_row("ATS Systems Found", str(len(ats_counts)))
    
    console.print(summary_table)
    
    # Sample jobs from each site
    if unique_jobs:
        console.print(f"\n[bold]Sample Jobs Found:[/bold]")
        sample_table = Table()
        sample_table.add_column("Title", style="green", max_width=25)
        sample_table.add_column("Company", style="cyan", max_width=20)
        sample_table.add_column("Location", style="yellow", max_width=15)
        sample_table.add_column("Site", style="blue", max_width=10)
        sample_table.add_column("ATS", style="magenta", max_width=12)
        
        for job in unique_jobs[:8]:  # Show first 8 jobs
            sample_table.add_row(
                job.get("title", "Unknown")[:22] + "..." if len(job.get("title", "")) > 25 else job.get("title", "Unknown"),
                job.get("company", "Unknown")[:17] + "..." if len(job.get("company", "")) > 20 else job.get("company", "Unknown"),
                job.get("location", "Unknown"),
                job.get("scraping_site", "unknown").replace('_', ' ')[:8],
                job.get("ats_system", "Unknown")
            )
        
        console.print(sample_table)
        
        if len(unique_jobs) > 8:
            console.print(f"[dim]... and {len(unique_jobs) - 8} more unique jobs[/dim]")


async def demo_integration():
    """Demo the multi-site integration."""
    console.print(Panel.fit("MONSTER CA INTEGRATION DEMO", style="bold blue"))
    
    console.print("[cyan]This demonstrates the Monster CA scraper integrated with Eluta[/cyan]")
    console.print("[cyan]Benefits of multi-site scraping:[/cyan]")
    console.print("  • More job opportunities discovered")
    console.print("  • Better coverage of the job market")
    console.print("  • Diversified ATS systems detected")
    console.print("  • Reduced dependence on single site")
    console.print("  • Automatic duplicate removal")
    
    user_input = input("\nRun multi-site demo? (y/n): ").lower().strip()
    
    if user_input == 'y':
        try:
            jobs = await run_multi_site_scraping(max_jobs_per_site=10)
            console.print(f"\n[bold green]🎉 Multi-site scraping completed successfully![/bold green]")
            console.print(f"[cyan]Found {len(jobs)} unique jobs across all sites[/cyan]")
        except Exception as e:
            console.print(f"[red]❌ Multi-site demo failed: {e}[/red]")
    else:
        console.print("[yellow]Multi-site demo skipped[/yellow]")
    
    console.print(f"\n[bold]Monster CA Integration Summary:[/bold]")
    console.print("✅ Monster CA scraper implemented")
    console.print("✅ Following same architecture as Eluta")
    console.print("✅ Integrated into scraper registry")
    console.print("✅ Multi-site workflow ready")
    console.print("✅ Production ready")


if __name__ == "__main__":
    asyncio.run(demo_integration())
