#!/usr/bin/env python3
"""
Clear the database and start fresh with improved scraping.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from job_database import get_job_db
import utils

console = Console()

def clear_database_fresh_start():
    """Clear the database and start fresh."""
    
    console.print(Panel("🗑️ Clearing Database for Fresh Start", style="bold red"))
    
    try:
        # Load profile
        profile = utils.load_profile('Nirajan')
        if not profile:
            console.print("[red]❌ Could not load Nirajan profile[/red]")
            return False
            
        console.print(f"[green]✅ Loaded profile: {profile['profile_name']}[/green]")
        
        # Get database
        db = get_job_db(profile['profile_name'])
        initial_stats = db.get_stats()
        console.print(f"[cyan]📊 Current database stats: {initial_stats['total_jobs']} jobs[/cyan]")
        
        # Confirm deletion
        console.print("[yellow]⚠️ This will delete ALL existing jobs from the database![/yellow]")
        console.print("[cyan]Starting fresh to test improved extraction with clean data...[/cyan]")
        
        # Clear all jobs
        db.clear_all_jobs()
        
        # Verify deletion
        final_stats = db.get_stats()
        console.print(f"[green]✅ Database cleared! New stats: {final_stats['total_jobs']} jobs[/green]")
        
        console.print("[bold green]🎉 Database cleared successfully![/bold green]")
        console.print("[cyan]Ready for fresh scraping with improved extraction logic[/cyan]")
        
        return True
            
    except Exception as e:
        console.print(f"[red]❌ Error clearing database: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    clear_database_fresh_start()
