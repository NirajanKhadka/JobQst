#!/usr/bin/env python3
"""
Profile Creation Script - Easy way to create new JobLens profiles
Usage: python create_new_profile.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

console = Console()

def create_profile_interactive():
    """Create a new profile interactively."""
    console.print(Panel.fit(
        "[bold blue]🆕 JobLens Profile Creator[/bold blue]\n"
        "Let's create your new job search profile!",
        border_style="blue"
    ))
    
    # Get basic information
    name = Prompt.ask("\n[cyan]👤 Profile Name[/cyan] (e.g., 'John_Doe', 'MyProfile')")
    
    # Check if profile already exists
    profile_dir = Path("profiles") / name
    if profile_dir.exists():
        console.print(f"[red]❌ Profile '{name}' already exists![/red]")
        if not Confirm.ask("Overwrite existing profile?", default=False):
            console.print("[yellow]Profile creation cancelled.[/yellow]")
            return False
    
    # Gather profile information
    console.print("\n[bold]Basic Information:[/bold]")
    full_name = Prompt.ask("[cyan]Full Name[/cyan]", default=name.replace("_", " "))
    email = Prompt.ask("[cyan]Email[/cyan]", default="")
    phone = Prompt.ask("[cyan]Phone[/cyan]", default="")
    location = Prompt.ask("[cyan]Location[/cyan] (e.g., 'Toronto, ON')", default="Toronto, ON")
    
    console.print("\n[bold]Professional Links:[/bold]")
    linkedin = Prompt.ask("[cyan]LinkedIn URL[/cyan]", default="")
    github = Prompt.ask("[cyan]GitHub URL[/cyan]", default="")
    portfolio = Prompt.ask("[cyan]Portfolio URL[/cyan]", default="")
    
    console.print("\n[bold]Skills & Keywords:[/bold]")
    console.print("[dim]Enter comma-separated values[/dim]")
    skills_input = Prompt.ask("[cyan]Skills[/cyan] (e.g., 'Python, JavaScript, SQL')", default="")
    skills = [s.strip() for s in skills_input.split(",") if s.strip()]
    
    keywords_input = Prompt.ask("[cyan]Job Keywords[/cyan] (e.g., 'developer, engineer, analyst')", default="")
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
    
    console.print("\n[bold]Experience:[/bold]")
    experience_level = Prompt.ask(
        "[cyan]Experience Level[/cyan]",
        choices=["entry", "intermediate", "senior", "lead"],
        default="intermediate"
    )
    experience_years = Prompt.ask("[cyan]Years of Experience[/cyan]", default="3")
    
    console.print("\n[bold]Search Preferences:[/bold]")
    search_locations_input = Prompt.ask(
        "[cyan]Preferred Locations[/cyan] (e.g., 'Toronto, Mississauga, Brampton')",
        default="Toronto, ON"
    )
    locations = [loc.strip() for loc in search_locations_input.split(",") if loc.strip()]
    
    # AI Model Configuration
    console.print("\n[bold]AI Configuration:[/bold]")
    ollama_model = Prompt.ask(
        "[cyan]Ollama Model[/cyan]",
        default="llama3:latest",
        choices=["llama3:latest", "llama3.1:latest", "mistral:latest", "gemma2:latest"]
    )
    
    # Create profile data
    profile_data = {
        "name": full_name,
        "profile_name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "linkedin": linkedin,
        "github": github,
        "portfolio": portfolio,
        "keywords": keywords,
        "skills": skills,
        "experience_level": experience_level,
        "experience_years": int(experience_years) if experience_years.isdigit() else 3,
        "locations": locations,
        "ollama_model": ollama_model,
        "batch_default": 15,
        "resume_docx": "",
        "cover_letter_docx": "",
        "resume_pdf": "",
        "cover_letter_pdf": "",
        "education": {
            "degree": "",
            "university": "",
            "graduation_year": "",
            "location": "",
            "specialization": "",
            "cgpa": "",
            "relevant_coursework": []
        },
        "experience": [],
        "projects": [],
        "certifications": [],
        "achievements": [],
        "languages": ["English"],
        "domain_knowledge": [],
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "version": "1.0",
            "created_by": "create_new_profile.py"
        },
        "settings": {
            "job_search": {
                "days_back": 14,
                "max_jobs_per_run": 200,
                "auto_process": True,
                "enable_cache": True
            },
            "analysis": {
                "min_fit_score": 0.6,
                "enable_ai_analysis": True,
                "detailed_logging": False
            },
            "notifications": {
                "email_enabled": False,
                "high_match_only": True
            }
        }
    }
    
    # Create profile directory structure
    try:
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Save profile JSON (use simple name format like existing profiles)
        profile_file = profile_dir / f"{name}.json"
        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        # Create subdirectories
        (profile_dir / "resumes").mkdir(exist_ok=True)
        (profile_dir / "cover_letters").mkdir(exist_ok=True)
        (profile_dir / "applications").mkdir(exist_ok=True)
        
        # Create empty database file placeholder
        (profile_dir / "jobs.db").touch()
        
        console.print(f"\n[bold green]✅ Profile '{name}' created successfully![/bold green]")
        console.print(f"[cyan]📁 Profile directory: {profile_dir}[/cyan]")
        console.print(f"[cyan]📄 Profile file: {profile_file}[/cyan]")
        
        # Show next steps
        console.print(Panel.fit(
            f"[bold]Next Steps:[/bold]\n\n"
            f"1. Add your resume: Place it in [cyan]{profile_dir / 'resumes'}[/cyan]\n"
            f"2. Update profile: Edit [cyan]{profile_file}[/cyan] with more details\n"
            f"3. Test health check: [green]python main.py {name} --action health-check[/green]\n"
            f"4. Run job search: [green]python main.py {name} --action jobspy-pipeline[/green]\n"
            f"5. View dashboard: [green]python main.py {name} --action dashboard[/green]",
            title="🎯 Getting Started",
            border_style="green"
        ))
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Error creating profile: {e}[/red]")
        return False


def list_existing_profiles():
    """List all existing profiles."""
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        console.print("[yellow]No profiles directory found.[/yellow]")
        return
    
    profiles = [d for d in profiles_dir.iterdir() if d.is_dir() and d.name != "__pycache__"]
    
    if not profiles:
        console.print("[yellow]No profiles found.[/yellow]")
        return
    
    console.print("\n[bold blue]📋 Existing Profiles:[/bold blue]")
    for i, profile_dir in enumerate(profiles, 1):
        # Check for both naming patterns
        profile_files = list(profile_dir.glob("*.json"))
        profile_files = [f for f in profile_files if not f.name.startswith('.') and not 'BACKUP' in f.name and not 'session' in f.name]
        
        if profile_files:
            try:
                with open(profile_files[0], encoding="utf-8") as f:
                    data = json.load(f)
                    name = data.get("name", profile_dir.name)
                    location = data.get("location", "N/A")
                    console.print(f"  {i}. [cyan]{profile_dir.name}[/cyan] - {name} ({location})")
            except:
                console.print(f"  {i}. [cyan]{profile_dir.name}[/cyan]")
        else:
            console.print(f"  {i}. [cyan]{profile_dir.name}[/cyan] (no profile file)")


def main():
    """Main entry point."""
    console.print("\n[bold blue]🚀 JobLens Profile Management[/bold blue]\n")
    
    list_existing_profiles()
    
    if Confirm.ask("\n[cyan]Create a new profile?[/cyan]", default=True):
        create_profile_interactive()
    else:
        console.print("[yellow]Profile creation cancelled.[/yellow]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Profile creation cancelled.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        sys.exit(1)
