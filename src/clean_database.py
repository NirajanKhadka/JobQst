#!/usr/bin/env python3
"""
Database Cleanup Script

This script provides functionality to safely back up and clear all job entries
from the application's database. It includes multiple confirmation steps
to prevent accidental data loss.
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
from typing import Optional

# --- Initialization ---
console = Console()


def _get_db_connection(profile_name: str = "Nirajan") -> Optional[object]:
    """
    Safely import and return a database connection object.

    Args:
        profile_name: The name of the profile to connect to.

    Returns:
        A database connection object or None if the import fails.
    """
    try:
        from src.core.job_database import get_job_db

        return get_job_db(profile_name)
    except ImportError as e:
        console.print(f"[red]❌ Failed to import database module: {e}[/red]")
        console.print("[yellow]💡 Make sure you are running this script from the project root directory.[/yellow]")
        return None


def clean_database(profile_name: str = "Nirajan") -> bool:
    """
    Clean the database by removing all job entries after user confirmation.

    Args:
        profile_name: The name of the profile whose database will be cleaned.

    Returns:
        True if the database was cleaned successfully, False otherwise.
    """
    console.print("[bold red]🗑️ Database Cleanup Tool[/bold red]")
    console.print("[yellow]This will remove ALL jobs from the database![/yellow]")

    if not Confirm.ask("Are you sure you want to delete ALL jobs?", default=False):
        console.print("[green]Operation cancelled.[/green]")
        return False

    if not Confirm.ask("This action cannot be undone. Proceed?", default=False):
        console.print("[green]Operation cancelled.[/green]")
        return False

    db = _get_db_connection(profile_name)
    if not db:
        return False

    try:
        initial_count = db.get_job_count()
        console.print(f"[cyan]📊 Current jobs in database: {initial_count}[/cyan]")

        if initial_count == 0:
            console.print("[green]✅ Database is already empty.[/green]")
            return True

        console.print("[red]🗑️ Clearing all jobs from database...[/red]")
        success = db.clear_all_jobs()

        if not success:
            console.print("[red]❌ Failed to clear database via db.clear_all_jobs().[/red]")
            return False

        final_count = db.get_job_count()
        removed_count = initial_count - final_count

        console.print(f"[green]✅ Successfully removed {removed_count} jobs.[/green]")
        console.print(f"[cyan]📊 Jobs remaining: {final_count}[/cyan]")

        if final_count == 0:
            console.print("[bold green]🎉 Database cleaned successfully![/bold green]")
        else:
            console.print("[yellow]⚠️ Some jobs may still remain.[/yellow]")
        return True

    except Exception as e:
        console.print(f"[red]❌ An error occurred during cleanup: {e}[/red]")
        return False


def backup_database(profile_name: str = "Nirajan") -> bool:
    """
    Create a timestamped backup of the database.

    Args:
        profile_name: The name of the profile whose database will be backed up.

    Returns:
        True if the backup was successful, False otherwise.
    """
    db = _get_db_connection(profile_name)
    if not db:
        return False

    try:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"{profile_name}_backup_{timestamp}.db"

        success = db.backup_database(str(backup_path))

        if success:
            console.print(f"[green]✅ Database backed up to: {backup_path}[/green]")
            return True
        else:
            console.print("[red]❌ Failed to create backup.[/red]")
            return False

    except Exception as e:
        console.print(f"[red]❌ An error occurred during backup: {e}[/red]")
        return False


def main():
    """Main function to drive the database cleanup process."""
    console.print("[bold blue]🚀 AutoJobAgent Database Management[/bold blue]")
    console.print("=" * 50)

    if Confirm.ask("Do you want to create a backup before cleaning?", default=True):
        if not backup_database():
            if not Confirm.ask("Backup failed. Continue without a backup?", default=False):
                console.print("[green]Operation cancelled.[/green]")
                return

    clean_database()


if __name__ == "__main__":
    # Ensure the script can find the 'src' module
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    main()
