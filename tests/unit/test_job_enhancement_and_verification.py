#!/usr/bin/env python3
"""
Test Job Enhancement and Gmail Verification
Comprehensive test script for job data enhancement and Gmail verification.
"""

import asyncio
import sys
from pathlib import Path

# Add project root and src directory to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

# Import modules with correct paths
from src.utils.job_data_enhancer import JobDataEnhancer
from src.utils.dynamic_gmail_verifier import DynamicGmailVerifier, verify_applications_with_gmail
from src.core.job_database import get_job_db

console = Console()

async def main():
    """Main function to test job enhancement and Gmail verification."""
    
    console.print(Panel.fit("🔍 JOB ENHANCEMENT & GMAIL VERIFICATION", style="bold blue"))
    
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
        
    except Exception as e:
        console.print(f"[red]❌ Error checking database: {e}[/red]")
        return
    
    # Show menu options
    console.print(f"\n[bold]🚀 Enhancement & Verification Options:[/bold]")
    console.print("1. 🔍 Enhance Job Data (Extract missing fields)")
    console.print("2. 📧 Verify Applications with Gmail")
    console.print("3. 🔄 Enhance Jobs + Gmail Verification")
    console.print("4. 📊 View Enhanced Jobs Report")
    console.print("5. 🧪 Test Single Job Enhancement")
    console.print("6. 📋 View Recent Applications")
    
    choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6"], default="1")
    
    if choice == "1":
        # Enhance job data
        await enhance_job_data(profile_name, db)
        
    elif choice == "2":
        # Gmail verification
        await gmail_verification(profile_name)
        
    elif choice == "3":
        # Combined enhancement and verification
        await combined_enhancement_and_verification(profile_name, db)
        
    elif choice == "4":
        # View enhanced jobs report
        await view_enhanced_jobs_report(profile_name)
        
    elif choice == "5":
        # Test single job enhancement
        await run_single_job_enhancement(profile_name, db)
        
    elif choice == "6":
        # View recent applications
        await view_recent_applications(profile_name, db)


async def enhance_job_data(profile_name: str, db):
    """Enhance job data by extracting missing fields."""
    console.print(Panel.fit("🔍 JOB DATA ENHANCEMENT", style="bold green"))
    
    enhancer = JobDataEnhancer(profile_name)
    if not await enhancer.initialize():
        return
    
    # Get jobs with missing fields
    jobs = db.get_unapplied_jobs(limit=20)
    
    if not jobs:
        console.print("[yellow]No jobs available for enhancement[/yellow]")
        return
    
    # Show jobs preview
    console.print(f"\n[cyan]Found {len(jobs)} jobs for enhancement[/cyan]")
    
    # Ask how many to enhance
    limit = int(Prompt.ask("How many jobs to enhance?", default="5"))
    
    if Confirm.ask(f"Enhance {limit} jobs by extracting detailed data from job links?"):
        enhancements = await enhancer.enhance_jobs_batch(jobs, limit=limit)
        
        # Save enhanced data
        if enhancer.save_enhanced_data(enhancements):
            console.print("[green]✅ Job enhancement completed successfully![/green]")
        else:
            console.print("[yellow]⚠️ Enhancement completed but saving failed[/yellow]")


async def gmail_verification(profile_name: str):
    """Verify applications using Gmail."""
    console.print(Panel.fit("📧 GMAIL VERIFICATION", style="bold blue"))
    
    console.print("[yellow]This will open Gmail in your browser for interactive verification[/yellow]")
    console.print("[yellow]You'll be able to see and verify each email match manually[/yellow]")
    
    if Confirm.ask("Proceed with Gmail verification?"):
        matches = await verify_applications_with_gmail(profile_name)
        
        if matches:
            console.print(f"[green]✅ Gmail verification completed! Found {len(matches)} confirmed applications[/green]")
        else:
            console.print("[yellow]No application confirmations found in Gmail[/yellow]")


async def combined_enhancement_and_verification(profile_name: str, db):
    """Combined job enhancement and Gmail verification."""
    console.print(Panel.fit("🔄 COMBINED ENHANCEMENT & VERIFICATION", style="bold magenta"))
    
    console.print("[cyan]This will:[/cyan]")
    console.print("1. 🔍 Enhance job data by extracting missing fields")
    console.print("2. 📧 Verify applications using Gmail")
    console.print("3. 💾 Update database with confirmed applications")
    
    if not Confirm.ask("Proceed with combined process?"):
        return
    
    # Step 1: Enhance job data
    console.print("\n[bold]Step 1: Job Data Enhancement[/bold]")
    enhancer = JobDataEnhancer(profile_name)
    if await enhancer.initialize():
        jobs = db.get_unapplied_jobs(limit=10)
        if jobs:
            enhancements = await enhancer.enhance_jobs_batch(jobs, limit=5)
            enhancer.save_enhanced_data(enhancements)
    
    # Step 2: Gmail verification
    console.print("\n[bold]Step 2: Gmail Verification[/bold]")
    matches = await verify_applications_with_gmail(profile_name)
    
    # Step 3: Summary
    console.print("\n[bold]Step 3: Summary[/bold]")
    console.print(f"[green]✅ Enhanced {len(enhancements) if 'enhancements' in locals() else 0} jobs[/green]")
    console.print(f"[green]✅ Verified {len(matches) if matches else 0} applications via Gmail[/green]")


async def view_enhanced_jobs_report(profile_name: str):
    """View enhanced jobs report."""
    console.print(Panel.fit("📊 ENHANCED JOBS REPORT", style="bold yellow"))
    
    try:
        import json
        from pathlib import Path
        
        enhanced_file = Path(f"profiles/{profile_name}/enhanced_jobs.json")
        
        if not enhanced_file.exists():
            console.print("[yellow]No enhanced jobs report found[/yellow]")
            console.print(f"[dim]Expected location: {enhanced_file}[/dim]")
            return
        
        with open(enhanced_file, 'r') as f:
            data = json.load(f)
        
        console.print(f"[green]📋 Found {len(data)} enhanced jobs[/green]")
        
        # Show summary table
        table = Table(title="Enhanced Jobs Summary")
        table.add_column("Job Title", style="cyan", max_width=30)
        table.add_column("Company", style="green", max_width=25)
        table.add_column("Questions", style="yellow")
        table.add_column("Requirements", style="blue")
        table.add_column("Salary", style="magenta", max_width=20)
        
        for item in data[:10]:  # Show first 10
            original = item.get('original_data', {})
            title = original.get('title', 'Unknown')
            company = original.get('company', 'Unknown')
            questions = str(len(item.get('questions_found', [])))
            requirements = str(len(item.get('requirements', [])))
            salary = item.get('salary_info', 'Not found')[:17] + "..." if item.get('salary_info') else "Not found"
            
            table.add_row(title, company, questions, requirements, salary)
        
        console.print(table)
        
        # Show sample questions
        total_questions = sum(len(item.get('questions_found', [])) for item in data)
        if total_questions > 0:
            console.print(f"\n[yellow]📝 Total questions found across all jobs: {total_questions}[/yellow]")
            
            console.print("\n[bold]Sample Questions:[/bold]")
            question_count = 0
            for item in data:
                for question in item.get('questions_found', [])[:2]:
                    if question_count < 5:
                        console.print(f"• {question.get('question', 'Unknown')[:80]}...")
                        question_count += 1
        
    except Exception as e:
        console.print(f"[red]❌ Error reading enhanced jobs report: {e}[/red]")


async def run_single_job_enhancement(profile_name: str, db):
    """Test enhancement on a single job."""
    console.print(Panel.fit("🧪 SINGLE JOB ENHANCEMENT TEST", style="bold cyan"))
    
    jobs = db.get_unapplied_jobs(limit=10)
    
    if not jobs:
        console.print("[yellow]No jobs available for testing[/yellow]")
        return
    
    # Show available jobs
    table = Table(title="Available Jobs for Testing")
    table.add_column("Index", style="cyan")
    table.add_column("Job Title", style="green", max_width=30)
    table.add_column("Company", style="yellow", max_width=25)
    table.add_column("URL", style="dim", max_width=40)
    
    for i, job in enumerate(jobs[:10]):
        url = job.get('url', '')
        display_url = url[:37] + "..." if len(url) > 40 else url
        
        table.add_row(
            str(i + 1),
            job.get('title', 'Unknown'),
            job.get('company', 'Unknown'),
            display_url
        )
    
    console.print(table)
    
    try:
        choice = int(Prompt.ask("Select job number to enhance", default="1"))
        if 1 <= choice <= len(jobs):
            selected_job = jobs[choice - 1]
            
            enhancer = JobDataEnhancer(profile_name)
            if await enhancer.initialize():
                console.print(f"\n[cyan]🔍 Enhancing: {selected_job.get('title', 'Unknown')}[/cyan]")
                enhancement = await enhancer.enhance_job_data(selected_job)
                
                # Display results
                console.print("\n[bold]Enhancement Results:[/bold]")
                console.print(f"Questions found: {len(enhancement.questions_found)}")
                console.print(f"Requirements found: {len(enhancement.requirements)}")
                console.print(f"Benefits found: {len(enhancement.benefits)}")
                console.print(f"Salary info: {enhancement.salary_info or 'Not found'}")
                console.print(f"Job type: {enhancement.job_type or 'Not found'}")
                console.print(f"Experience level: {enhancement.experience_level or 'Not found'}")
                
                if enhancement.questions_found:
                    console.print("\n[bold]Questions Found:[/bold]")
                    for q in enhancement.questions_found[:3]:
                        console.print(f"• {q['question']}")
                        console.print(f"  [dim]Suggested: {q['suggested_response'][:60]}...[/dim]")
        else:
            console.print("[red]Invalid selection[/red]")
            
    except ValueError:
        console.print("[red]Invalid input[/red]")


async def view_recent_applications(profile_name: str, db):
    """View recent applications."""
    console.print(Panel.fit("📋 RECENT APPLICATIONS", style="bold green"))
    
    try:
        recent_apps = db.get_recent_applications(days=7)
        
        if not recent_apps:
            console.print("[yellow]No recent applications found[/yellow]")
            return
        
        console.print(f"[green]Found {len(recent_apps)} applications in the last 7 days[/green]")
        
        table = Table(title="Recent Applications")
        table.add_column("Date", style="cyan")
        table.add_column("Job Title", style="green", max_width=30)
        table.add_column("Company", style="yellow", max_width=25)
        table.add_column("Status", style="magenta")
        
        for app in recent_apps[:15]:  # Show first 15
            date = app.get('applied_date', 'Unknown')[:10]
            title = app.get('title', 'Unknown')
            company = app.get('company', 'Unknown')
            status = app.get('status', 'Unknown')
            
            table.add_row(date, title, company, status)
        
        console.print(table)
        
        if len(recent_apps) > 15:
            console.print(f"[dim]... and {len(recent_apps) - 15} more applications[/dim]")
            
    except Exception as e:
        console.print(f"[red]❌ Error getting recent applications: {e}[/red]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Process cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
