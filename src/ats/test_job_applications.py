#!/usr/bin/env python3
"""
Test Job Applications
Quick script to test and start the job application process.
"""

import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from enhanced_job_applicator import apply_to_jobs, test_application_system, EnhancedJobApplicator
from job_database import get_job_db

console = Console()

async def main():
    """Main function to test and run job applications."""
    
    console.print(Panel.fit("🎯 JOB APPLICATION SYSTEM", style="bold blue"))
    
    # Check available profiles
    try:
        from utils import get_available_profiles
        profiles = get_available_profiles()
        console.print(f"[cyan]Available profiles: {', '.join(profiles)}[/cyan]")
        
        # Use Nirajan profile by default
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
    
    # Show menu options
    console.print(f"\n[bold]🚀 Application Options:[/bold]")
    console.print("1. 🧪 Test System (Dry Run)")
    console.print("2. 🎯 Apply to 5 Jobs")
    console.print("3. 🚀 Apply to 10 Jobs") 
    console.print("4. 💼 Apply to 20 Jobs")
    console.print("5. 🔧 Custom Application")
    console.print("6. 📊 View Job Preview Only")
    
    choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6"], default="1")
    
    if choice == "1":
        # Test system with dry run
        await test_application_system(profile_name)
        
    elif choice == "2":
        # Apply to 5 jobs
        console.print("[cyan]🎯 Applying to 5 jobs...[/cyan]")
        results = await apply_to_jobs(
            profile_name=profile_name,
            limit=5,
            batch_size=2,
            dry_run=False
        )
        console.print(f"[green]✅ Completed! Processed {len(results)} jobs[/green]")
        
    elif choice == "3":
        # Apply to 10 jobs
        console.print("[cyan]🎯 Applying to 10 jobs...[/cyan]")
        results = await apply_to_jobs(
            profile_name=profile_name,
            limit=10,
            batch_size=3,
            dry_run=False
        )
        console.print(f"[green]✅ Completed! Processed {len(results)} jobs[/green]")
        
    elif choice == "4":
        # Apply to 20 jobs
        console.print("[cyan]🎯 Applying to 20 jobs...[/cyan]")
        results = await apply_to_jobs(
            profile_name=profile_name,
            limit=20,
            batch_size=3,
            dry_run=False
        )
        console.print(f"[green]✅ Completed! Processed {len(results)} jobs[/green]")
        
    elif choice == "5":
        # Custom application
        limit = int(Prompt.ask("Number of jobs to apply to", default="5"))
        batch_size = int(Prompt.ask("Batch size (parallel jobs)", default="2"))
        dry_run = Confirm.ask("Dry run mode?", default=False)
        
        # Optional filters
        use_filters = Confirm.ask("Use filters?", default=False)
        filters = None
        if use_filters:
            company_filter = Prompt.ask("Company filter (optional)", default="")
            location_filter = Prompt.ask("Location filter (optional)", default="")
            
            filters = {}
            if company_filter:
                filters['company'] = company_filter
            if location_filter:
                filters['location'] = location_filter
        
        console.print(f"[cyan]🎯 Custom application: {limit} jobs, batch size {batch_size}[/cyan]")
        results = await apply_to_jobs(
            profile_name=profile_name,
            limit=limit,
            batch_size=batch_size,
            dry_run=dry_run,
            filters=filters
        )
        console.print(f"[green]✅ Completed! Processed {len(results)} jobs[/green]")
        
    elif choice == "6":
        # Preview only
        applicator = EnhancedJobApplicator(profile_name)
        if await applicator.initialize():
            jobs = await applicator.get_jobs_to_apply(limit=20)
            applicator.display_jobs_preview(jobs, limit=20)
        else:
            console.print("[red]❌ Failed to initialize applicator[/red]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Application cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
