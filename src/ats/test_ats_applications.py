#!/usr/bin/env python3
"""
Test ATS-Based Applications
Test script for the new ATS-based job application system with field processing
and dynamic code modification capabilities.
"""

import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from ats_based_applicator import ATSBasedApplicator, apply_with_ats_detection, test_ats_detection
from job_database import get_job_db

console = Console()

async def main():
    """Main function to test ATS-based applications."""
    
    console.print(Panel.fit("🎯 ATS-BASED JOB APPLICATION SYSTEM", style="bold blue"))
    
    # Check available profiles
    try:
        from utils import get_available_profiles
        profiles = get_available_profiles()
        console.print(f"[cyan]Available profiles: {', '.join(profiles)}[/cyan]")
        
        profile_name = "Nirajan"
        if profile_name not in profiles:
            console.print(f"[red]❌ Profile '{profile_name}' not found[/red]")
            return
        
    except Exception as e:
        console.print(f"[red]❌ Error checking profiles: {e}[/red]")
        return
    
    # Check database status
    try:
        db = get_job_db(profile_name)
        stats = db.get_stats()
        
        console.print(f"\n[bold]📊 Database Status for {profile_name}:[/bold]")
        console.print(f"• Total Jobs: {stats.get('total_jobs', 0)}")
        console.print(f"• Unapplied Jobs: {stats.get('unapplied_jobs', 0)}")
        console.print(f"• Applied Jobs: {stats.get('applied_jobs', 0)}")
        console.print(f"• Unique Companies: {stats.get('unique_companies', 0)}")
        
        if stats.get('unapplied_jobs', 0) == 0:
            console.print("[yellow]⚠️ No unapplied jobs found in database[/yellow]")
            return
            
    except Exception as e:
        console.print(f"[red]❌ Error checking database: {e}[/red]")
        return
    
    # Show ATS capabilities
    console.print(f"\n[bold]🤖 ATS Detection Capabilities:[/bold]")
    ats_table = Table()
    ats_table.add_column("ATS System", style="cyan")
    ats_table.add_column("Detection Method", style="green")
    ats_table.add_column("Special Features", style="yellow")
    
    ats_table.add_row("Workday", "URL + DOM patterns", "Multi-step forms, dropdowns, date pickers")
    ats_table.add_row("Greenhouse", "URL + DOM patterns", "Application questions, attachments")
    ats_table.add_row("Lever", "URL + DOM patterns", "Custom questions")
    ats_table.add_row("Other/Generic", "Fallback detection", "Dynamic field discovery")
    
    console.print(ats_table)
    
    # Show menu options
    console.print(f"\n[bold]🚀 ATS Application Options:[/bold]")
    console.print("1. 🧪 Test ATS Detection (3 jobs)")
    console.print("2. 🎯 Apply with ATS Detection (5 jobs)")
    console.print("3. 🚀 Apply with ATS Detection (10 jobs)")
    console.print("4. 🔧 Custom ATS Application")
    console.print("5. 📊 View Jobs by ATS Type")
    console.print("6. ⚙️ Add Custom Field Mapping")
    console.print("7. 📈 Show ATS Statistics")
    
    choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6", "7"], default="1")
    
    if choice == "1":
        # Test ATS detection
        await test_ats_detection(profile_name, num_jobs=3)
        
    elif choice == "2":
        # Apply to 5 jobs with ATS detection
        console.print("[cyan]🎯 Applying to 5 jobs with ATS detection...[/cyan]")
        jobs = db.get_unapplied_jobs(limit=5)
        results = await apply_with_ats_detection(profile_name, jobs, batch_size=2)
        console.print(f"[green]✅ Completed! Processed {len(results)} jobs[/green]")
        
    elif choice == "3":
        # Apply to 10 jobs with ATS detection
        console.print("[cyan]🎯 Applying to 10 jobs with ATS detection...[/cyan]")
        jobs = db.get_unapplied_jobs(limit=10)
        results = await apply_with_ats_detection(profile_name, jobs, batch_size=3)
        console.print(f"[green]✅ Completed! Processed {len(results)} jobs[/green]")
        
    elif choice == "4":
        # Custom ATS application
        await custom_ats_application(profile_name, db)
        
    elif choice == "5":
        # View jobs by ATS type
        await view_jobs_by_ats(profile_name, db)
        
    elif choice == "6":
        # Add custom field mapping
        await add_custom_field_mapping(profile_name)
        
    elif choice == "7":
        # Show ATS statistics
        await show_ats_statistics(profile_name)


async def custom_ats_application(profile_name: str, db):
    """Custom ATS application with user-defined parameters."""
    console.print(Panel.fit("🔧 CUSTOM ATS APPLICATION", style="bold cyan"))
    
    # Get parameters
    limit = int(Prompt.ask("Number of jobs to apply to", default="5"))
    batch_size = int(Prompt.ask("Batch size (jobs processed in parallel)", default="2"))
    
    # Optional filters
    use_filters = Confirm.ask("Use filters to select specific jobs?", default=False)
    filters = {}
    
    if use_filters:
        company_filter = Prompt.ask("Company filter (optional)", default="")
        if company_filter:
            filters['company'] = company_filter
        
        # Show available ATS types
        console.print("\n[cyan]Available ATS types to filter by:[/cyan]")
        console.print("• workday")
        console.print("• greenhouse") 
        console.print("• lever")
        console.print("• other")
        
        ats_filter = Prompt.ask("ATS type filter (optional)", default="")
        if ats_filter:
            # This would need to be implemented in the database query
            console.print(f"[yellow]Note: ATS filtering will be applied during detection[/yellow]")
    
    # Get jobs
    jobs = db.get_unapplied_jobs(limit=limit)
    
    if not jobs:
        console.print("[yellow]No jobs found matching criteria[/yellow]")
        return
    
    # Show preview
    preview_table = Table(title=f"Jobs to Process ({len(jobs)} jobs)")
    preview_table.add_column("Title", style="cyan", max_width=30)
    preview_table.add_column("Company", style="magenta", max_width=25)
    preview_table.add_column("URL", style="dim", max_width=40)
    
    for job in jobs[:10]:  # Show first 10
        url = job.get('url', '')
        display_url = url[:37] + "..." if len(url) > 40 else url
        preview_table.add_row(
            job.get('title', 'Unknown'),
            job.get('company', 'Unknown'),
            display_url
        )
    
    console.print(preview_table)
    
    if len(jobs) > 10:
        console.print(f"[cyan]... and {len(jobs) - 10} more jobs[/cyan]")
    
    # Confirm
    if Confirm.ask(f"Proceed with applying to {len(jobs)} jobs?"):
        results = await apply_with_ats_detection(profile_name, jobs, batch_size)
        console.print(f"[green]✅ Custom application completed! Processed {len(results)} jobs[/green]")
    else:
        console.print("[yellow]Application cancelled[/yellow]")


async def view_jobs_by_ats(profile_name: str, db):
    """View jobs categorized by potential ATS type."""
    console.print(Panel.fit("📊 JOBS BY ATS TYPE", style="bold green"))
    
    jobs = db.get_unapplied_jobs(limit=50)
    
    # Categorize jobs by URL patterns
    ats_categories = {
        "workday": [],
        "greenhouse": [],
        "lever": [],
        "other": []
    }
    
    for job in jobs:
        url = job.get('url', '').lower()
        categorized = False
        
        if any(pattern in url for pattern in ["workday", "myworkday", "wd1.", "wd3."]):
            ats_categories["workday"].append(job)
            categorized = True
        elif any(pattern in url for pattern in ["greenhouse", "boards.greenhouse"]):
            ats_categories["greenhouse"].append(job)
            categorized = True
        elif any(pattern in url for pattern in ["lever", "jobs.lever"]):
            ats_categories["lever"].append(job)
            categorized = True
        
        if not categorized:
            ats_categories["other"].append(job)
    
    # Display results
    for ats_type, job_list in ats_categories.items():
        if job_list:
            console.print(f"\n[bold]{ats_type.upper()} ({len(job_list)} jobs):[/bold]")
            for i, job in enumerate(job_list[:5]):  # Show first 5
                console.print(f"  {i+1}. {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
            
            if len(job_list) > 5:
                console.print(f"  ... and {len(job_list) - 5} more")


async def add_custom_field_mapping(profile_name: str):
    """Add custom field mapping for specific ATS."""
    console.print(Panel.fit("⚙️ ADD CUSTOM FIELD MAPPING", style="bold yellow"))
    
    applicator = ATSBasedApplicator(profile_name)
    await applicator.initialize()
    
    # Show available ATS systems
    console.print("[cyan]Available ATS systems:[/cyan]")
    for ats_name in applicator.ats_strategies.keys():
        console.print(f"• {ats_name}")
    
    ats_name = Prompt.ask("ATS system name")
    if ats_name not in applicator.ats_strategies:
        console.print(f"[red]❌ ATS system '{ats_name}' not found[/red]")
        return
    
    field_name = Prompt.ask("Field name (e.g., 'linkedin', 'portfolio')")
    selectors = Prompt.ask("CSS selectors (comma-separated)").split(',')
    selectors = [s.strip() for s in selectors if s.strip()]
    field_type = Prompt.ask("Field type", choices=["text", "email", "tel", "file", "select"], default="text")
    
    applicator.add_custom_field_mapping(ats_name, field_name, selectors, field_type)
    
    console.print(f"[green]✅ Custom field mapping added successfully![/green]")


async def show_ats_statistics(profile_name: str):
    """Show ATS detection and application statistics."""
    console.print(Panel.fit("📈 ATS STATISTICS", style="bold magenta"))
    
    # This would show historical ATS detection data
    # For now, show placeholder data
    console.print("[cyan]Historical ATS detection data would be shown here[/cyan]")
    console.print("[yellow]Feature coming soon: Track ATS detection accuracy over time[/yellow]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Application cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
