#!/usr/bin/env python3
"""
Enhanced Database Cleanup and Modernization Tool
This script provides comprehensive database management including cleanup, migration, and optimization.
"""

import os
import sqlite3
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.panel import Panel

console = Console()

class DatabaseManager:
    """Enhanced database management with cleanup, migration, and optimization."""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.output_dir = Path("output")
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def analyze_current_databases(self) -> Dict:
        """Analyze all existing databases and their contents."""
        console.print("[bold blue]🔍 Analyzing Current Database State[/bold blue]")
        
        analysis = {
            "databases": [],
            "csv_files": [],
            "total_jobs": 0,
            "total_applications": 0,
            "profiles": set()
        }
        
        # Find all database files
        db_patterns = ["*.db", "output/*.db", "output/*/*.db"]
        for pattern in db_patterns:
            for db_file in self.base_dir.glob(pattern):
                if db_file.is_file():
                    db_info = self._analyze_database(db_file)
                    analysis["databases"].append(db_info)
                    analysis["total_jobs"] += db_info["job_count"]
                    analysis["total_applications"] += db_info["application_count"]
                    if db_info["profile"]:
                        analysis["profiles"].add(db_info["profile"])
        
        # Find all CSV files
        csv_patterns = ["*.csv", "output/*.csv", "output/*/*.csv"]
        for pattern in csv_patterns:
            for csv_file in self.base_dir.glob(pattern):
                if csv_file.is_file() and "job" in csv_file.name.lower():
                    csv_info = self._analyze_csv(csv_file)
                    analysis["csv_files"].append(csv_info)
        
        return analysis
    
    def _analyze_database(self, db_path: Path) -> Dict:
        """Analyze a single database file."""
        info = {
            "path": str(db_path),
            "size": db_path.stat().st_size,
            "modified": datetime.fromtimestamp(db_path.stat().st_mtime),
            "job_count": 0,
            "application_count": 0,
            "profile": self._extract_profile_from_path(db_path),
            "tables": [],
            "status": "unknown"
        }
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                info["tables"] = [row[0] for row in cursor.fetchall()]
                
                # Count jobs if jobs table exists
                if "jobs" in info["tables"]:
                    cursor.execute("SELECT COUNT(*) FROM jobs")
                    info["job_count"] = cursor.fetchone()[0]
                
                # Count applications if applications table exists
                if "applications" in info["tables"]:
                    cursor.execute("SELECT COUNT(*) FROM applications")
                    info["application_count"] = cursor.fetchone()[0]
                
                info["status"] = "healthy"
                
        except Exception as e:
            info["status"] = f"error: {e}"
        
        return info
    
    def _analyze_csv(self, csv_path: Path) -> Dict:
        """Analyze a single CSV file."""
        info = {
            "path": str(csv_path),
            "size": csv_path.stat().st_size,
            "modified": datetime.fromtimestamp(csv_path.stat().st_mtime),
            "row_count": 0,
            "profile": self._extract_profile_from_path(csv_path)
        }
        
        try:
            import csv
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                info["row_count"] = sum(1 for row in reader) - 1  # Subtract header
        except Exception:
            info["row_count"] = 0
        
        return info
    
    def _extract_profile_from_path(self, path: Path) -> Optional[str]:
        """Extract profile name from file path."""
        name = path.stem
        if "_" in name:
            potential_profile = name.split("_")[0]
            if potential_profile and potential_profile != "default":
                return potential_profile
        return None
    
    def display_analysis(self, analysis: Dict):
        """Display database analysis in a formatted table."""
        console.print(Panel(f"Found {len(analysis['databases'])} databases, {len(analysis['csv_files'])} CSV files", 
                          title="Database Analysis", style="bold green"))
        
        # Database table
        if analysis["databases"]:
            db_table = Table(title="Database Files")
            db_table.add_column("Path", style="cyan")
            db_table.add_column("Profile", style="yellow")
            db_table.add_column("Jobs", justify="right", style="green")
            db_table.add_column("Applications", justify="right", style="blue")
            db_table.add_column("Size", justify="right")
            db_table.add_column("Status", style="red")
            
            for db in analysis["databases"]:
                size_mb = db["size"] / 1024 / 1024
                db_table.add_row(
                    db["path"],
                    db["profile"] or "Unknown",
                    str(db["job_count"]),
                    str(db["application_count"]),
                    f"{size_mb:.2f} MB",
                    db["status"]
                )
            
            console.print(db_table)
        
        # CSV table
        if analysis["csv_files"]:
            csv_table = Table(title="CSV Files")
            csv_table.add_column("Path", style="cyan")
            csv_table.add_column("Profile", style="yellow")
            csv_table.add_column("Rows", justify="right", style="green")
            csv_table.add_column("Size", justify="right")
            
            for csv in analysis["csv_files"]:
                size_kb = csv["size"] / 1024
                csv_table.add_row(
                    csv["path"],
                    csv["profile"] or "Unknown",
                    str(csv["row_count"]),
                    f"{size_kb:.1f} KB"
                )
            
            console.print(csv_table)
        
        # Summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Total Jobs: {analysis['total_jobs']}")
        console.print(f"  Total Applications: {analysis['total_applications']}")
        console.print(f"  Active Profiles: {', '.join(analysis['profiles']) if analysis['profiles'] else 'None'}")
    
    def backup_databases(self, analysis: Dict) -> bool:
        """Create backups of all databases before cleanup."""
        if not analysis["databases"] and not analysis["csv_files"]:
            console.print("[yellow]No databases or CSV files to backup[/yellow]")
            return True
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = self.backup_dir / f"backup_{timestamp}"
        backup_folder.mkdir(exist_ok=True)
        
        console.print(f"[cyan]📦 Creating backup in: {backup_folder}[/cyan]")
        
        try:
            # Backup databases
            for db in analysis["databases"]:
                src = Path(db["path"])
                dst = backup_folder / src.name
                shutil.copy2(src, dst)
                console.print(f"[green]✅ Backed up: {src.name}[/green]")
            
            # Backup CSV files
            for csv in analysis["csv_files"]:
                src = Path(csv["path"])
                dst = backup_folder / src.name
                shutil.copy2(src, dst)
                console.print(f"[green]✅ Backed up: {src.name}[/green]")
            
            # Create backup manifest
            manifest = {
                "timestamp": timestamp,
                "total_jobs": analysis["total_jobs"],
                "total_applications": analysis["total_applications"],
                "profiles": list(analysis["profiles"]),
                "databases": analysis["databases"],
                "csv_files": analysis["csv_files"]
            }
            
            with open(backup_folder / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2, default=str)
            
            console.print(f"[bold green]🎉 Backup completed successfully![/bold green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Backup failed: {e}[/red]")
            return False

    def clean_databases(self, analysis: Dict, keep_data: bool = False) -> bool:
        """Clean up databases and CSV files."""
        console.print("[bold red]🗑️ Starting Database Cleanup[/bold red]")

        if keep_data:
            console.print("[yellow]⚠️ This will clean up old/redundant files but preserve current data[/yellow]")
        else:
            console.print("[yellow]⚠️ This will DELETE ALL job data from the system![/yellow]")

        if not Confirm.ask("Are you sure you want to proceed?"):
            console.print("[green]Operation cancelled[/green]")
            return False

        try:
            cleaned_count = 0

            # Clean database files
            for db in analysis["databases"]:
                db_path = Path(db["path"])

                # Determine if we should clean this database
                should_clean = True
                if keep_data:
                    # Only clean empty or error databases
                    should_clean = (db["job_count"] == 0 and db["application_count"] == 0) or "error" in db["status"]

                if should_clean and db_path.exists():
                    try:
                        db_path.unlink()
                        console.print(f"[green]✅ Removed database: {db_path.name}[/green]")
                        cleaned_count += 1
                    except Exception as e:
                        console.print(f"[red]❌ Failed to remove {db_path.name}: {e}[/red]")

            # Clean CSV files
            for csv in analysis["csv_files"]:
                csv_path = Path(csv["path"])

                # Determine if we should clean this CSV
                should_clean = True
                if keep_data:
                    # Only clean empty CSV files
                    should_clean = csv["row_count"] == 0

                if should_clean and csv_path.exists():
                    try:
                        csv_path.unlink()
                        console.print(f"[green]✅ Removed CSV: {csv_path.name}[/green]")
                        cleaned_count += 1
                    except Exception as e:
                        console.print(f"[red]❌ Failed to remove {csv_path.name}: {e}[/red]")

            console.print(f"\n[bold green]🎉 Cleanup completed! Removed {cleaned_count} files[/bold green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Cleanup failed: {e}[/red]")
            return False

    def optimize_database(self, db_path: Path) -> bool:
        """Optimize a single database file."""
        console.print(f"[cyan]🔧 Optimizing database: {db_path.name}[/cyan]")

        try:
            with sqlite3.connect(db_path) as conn:
                # Run VACUUM to reclaim space and defragment
                conn.execute("VACUUM")

                # Analyze tables for query optimization
                conn.execute("ANALYZE")

                # Update statistics
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM jobs")
                job_count = cursor.fetchone()[0]

                console.print(f"[green]✅ Optimized {db_path.name} ({job_count} jobs)[/green]")
                return True

        except Exception as e:
            console.print(f"[red]❌ Failed to optimize {db_path.name}: {e}[/red]")
            return False

    def create_unified_database(self, analysis: Dict, profile_name: str = "Nirajan") -> bool:
        """Create a single unified database from multiple sources."""
        console.print(f"[bold blue]🔄 Creating Unified Database for {profile_name}[/bold blue]")

        try:
            from src.core.job_database import get_job_db

            # Create new unified database
            unified_db = get_job_db(profile_name)

            total_jobs_migrated = 0
            total_applications_migrated = 0

            # Migrate data from all healthy databases
            for db_info in analysis["databases"]:
                if "error" not in db_info["status"] and db_info["job_count"] > 0:
                    db_path = Path(db_info["path"])

                    console.print(f"[cyan]📥 Migrating from: {db_path.name}[/cyan]")

                    try:
                        with sqlite3.connect(db_path) as source_conn:
                            source_conn.row_factory = sqlite3.Row
                            cursor = source_conn.cursor()

                            # Migrate jobs
                            cursor.execute("SELECT * FROM jobs")
                            jobs = cursor.fetchall()

                            for job_row in jobs:
                                job_dict = dict(job_row)
                                # Convert to format expected by unified database
                                job_data = {
                                    "title": job_dict.get("title", ""),
                                    "company": job_dict.get("company", ""),
                                    "location": job_dict.get("location", ""),
                                    "url": job_dict.get("url", ""),
                                    "apply_url": job_dict.get("apply_url", ""),
                                    "summary": job_dict.get("summary", ""),
                                    "full_description": job_dict.get("full_description", ""),
                                    "salary": job_dict.get("salary", ""),
                                    "job_type": job_dict.get("job_type", ""),
                                    "posted_date": job_dict.get("posted_date", ""),
                                    "site": job_dict.get("site", ""),
                                    "search_keyword": job_dict.get("search_keyword", ""),
                                    "experience_level": job_dict.get("experience_level", ""),
                                    "education_required": job_dict.get("education_required", ""),
                                    "apply_instructions": job_dict.get("apply_instructions", ""),
                                    "deep_scraped": job_dict.get("deep_scraped", False)
                                }

                                if unified_db.add_job(job_data):
                                    total_jobs_migrated += 1

                            console.print(f"[green]✅ Migrated {len(jobs)} jobs from {db_path.name}[/green]")

                    except Exception as e:
                        console.print(f"[yellow]⚠️ Failed to migrate from {db_path.name}: {e}[/yellow]")

            console.print(f"\n[bold green]🎉 Migration completed![/bold green]")
            console.print(f"  Total jobs migrated: {total_jobs_migrated}")
            console.print(f"  Unified database: output/{profile_name}_jobs.db")

            return True

        except Exception as e:
            console.print(f"[red]❌ Migration failed: {e}[/red]")
            return False

def main():
    """Main function with interactive menu."""
    console.print(Panel("🗄️ Enhanced Database Manager", style="bold blue"))

    manager = DatabaseManager()

    while True:
        console.print("\n[bold]Available Actions:[/bold]")
        options = {
            "1": "🔍 Analyze current databases",
            "2": "📦 Backup all databases",
            "3": "🗑️ Clean empty/redundant files",
            "4": "💥 Full cleanup (delete all data)",
            "5": "🔧 Optimize databases",
            "6": "🔄 Create unified database",
            "7": "🚪 Exit"
        }

        for key, value in options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

        choice = Prompt.ask("Select option", choices=list(options.keys()), default="1")

        if choice == "1":  # Analyze
            analysis = manager.analyze_current_databases()
            manager.display_analysis(analysis)

        elif choice == "2":  # Backup
            analysis = manager.analyze_current_databases()
            manager.backup_databases(analysis)

        elif choice == "3":  # Clean empty/redundant
            analysis = manager.analyze_current_databases()
            if analysis["databases"] or analysis["csv_files"]:
                manager.backup_databases(analysis)
                manager.clean_databases(analysis, keep_data=True)
            else:
                console.print("[yellow]No databases found to clean[/yellow]")

        elif choice == "4":  # Full cleanup
            analysis = manager.analyze_current_databases()
            if analysis["databases"] or analysis["csv_files"]:
                manager.backup_databases(analysis)
                manager.clean_databases(analysis, keep_data=False)
            else:
                console.print("[yellow]No databases found to clean[/yellow]")

        elif choice == "5":  # Optimize
            analysis = manager.analyze_current_databases()
            for db_info in analysis["databases"]:
                if "error" not in db_info["status"]:
                    manager.optimize_database(Path(db_info["path"]))

        elif choice == "6":  # Create unified
            analysis = manager.analyze_current_databases()
            profile_name = Prompt.ask("Enter profile name", default="Nirajan")
            manager.create_unified_database(analysis, profile_name)

        elif choice == "7":  # Exit
            console.print("[green]Goodbye![/green]")
            break

        if choice != "7":
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()

def get_database_manager(db_path: str = "data/jobs.db") -> DatabaseManager:
    """Get a database manager instance."""
    return DatabaseManager(db_path)

# Backward compatibility alias
EnhancedDatabaseManager = DatabaseManager
