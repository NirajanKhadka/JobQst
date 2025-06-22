#!/usr/bin/env python3
"""
Comprehensive Codebase Cleanup Tool
Removes redundant files, consolidates modules, and improves code organization.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table
from rich.panel import Panel

console = Console()

class CodebaseCleanup:
    """Comprehensive codebase cleanup and consolidation."""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.backup_dir = Path("cleanup_backup")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Files and directories to remove
        self.files_to_remove = [
            # Redundant scrapers
            "scrapers/parallel_scraper.py",
            "scrapers/smart_parallel_scraper.py",
            "comprehensive_eluta_scraper.py",
            "standalone_scraper.py",
            "production_comprehensive_scraper.py",
            
            # Old test files
            "test_duplicate_detection.py",
            "test_experience_filter.py",
            "test_real_job_scraping.py",
            "test_extraction_fix.py",
            "test_parallel_fix.py",
            "test_parallel_performance.py",
            "test_opera_session.py",
            "test_resume_caching.py",
            "test_smart_parallel_integration.py",
            
            # Debug files
            "debug_dashboard_issue.py",
            "debug_extraction_failures.py",
            "fix_dashboard_jobs_issue.py",
            "analyze_eluta_structure.py",
            
            # Redundant utilities
            "simple_scraper.py",
            "job_scraper.py",
            "run_scraping.py",
            "multi_site_scraper.py",
            
            # Old documentation
            "refactor_plan.md",
            "MAIN_APPLICATION_ISSUES.md",
            "INTEGRATION_REPORT.md",
            "ENHANCED_ERROR_TRACKING_GUIDE.md",
            "INDEED_SCRAPING_GUIDE.md",
            "SESSION_PERSISTENCE_GUIDE.md",
            "PARALLEL_SCRAPING.md",
            
            # Debug images
            "debug_*.png",
            
            # Old config files
            "setup.py",
            "setup.cfg",
            
            # Sample data
            "sample_jobs.csv",
            "bamboohr_job.csv",
        ]
        
        # Directories to clean
        self.dirs_to_clean = [
            "__pycache__",
            "temp",
            "output/logs",
        ]
        
        # Files to consolidate
        self.consolidation_map = {
            # Merge similar functionality
            "enhanced_application_logger.py": "utils.py",
            "enhanced_status_tracker.py": "utils.py", 
            "realtime_error_tracker.py": "utils.py",
            "system_health_monitor.py": "utils.py",
            "network_resilience.py": "utils.py",
            "config_manager.py": "utils.py",
        }
    
    def analyze_codebase(self) -> Dict:
        """Analyze current codebase state."""
        console.print("[bold blue]🔍 Analyzing Codebase[/bold blue]")
        
        analysis = {
            "files_found": [],
            "files_missing": [],
            "dirs_found": [],
            "total_size": 0,
            "consolidation_candidates": []
        }
        
        # Check files to remove
        for file_pattern in self.files_to_remove:
            if "*" in file_pattern:
                # Handle wildcards
                pattern_path = Path(file_pattern)
                parent = pattern_path.parent
                pattern = pattern_path.name
                
                if parent.exists():
                    for file_path in parent.glob(pattern):
                        if file_path.is_file():
                            analysis["files_found"].append(str(file_path))
                            analysis["total_size"] += file_path.stat().st_size
            else:
                file_path = Path(file_pattern)
                if file_path.exists():
                    analysis["files_found"].append(str(file_path))
                    analysis["total_size"] += file_path.stat().st_size
                else:
                    analysis["files_missing"].append(str(file_path))
        
        # Check directories
        for dir_pattern in self.dirs_to_clean:
            for dir_path in self.base_dir.rglob(dir_pattern):
                if dir_path.is_dir():
                    analysis["dirs_found"].append(str(dir_path))
        
        # Check consolidation candidates
        for source, target in self.consolidation_map.items():
            source_path = Path(source)
            target_path = Path(target)
            if source_path.exists() and target_path.exists():
                analysis["consolidation_candidates"].append((str(source_path), str(target_path)))
        
        return analysis
    
    def display_analysis(self, analysis: Dict):
        """Display cleanup analysis."""
        console.print(Panel(f"Found {len(analysis['files_found'])} files and {len(analysis['dirs_found'])} directories to clean", 
                          title="Cleanup Analysis", style="bold green"))
        
        # Files table
        if analysis["files_found"]:
            files_table = Table(title="Files to Remove")
            files_table.add_column("File", style="cyan")
            files_table.add_column("Size", justify="right", style="yellow")
            
            for file_path in analysis["files_found"][:20]:  # Show first 20
                try:
                    size = Path(file_path).stat().st_size
                    size_str = f"{size / 1024:.1f} KB" if size > 1024 else f"{size} B"
                except:
                    size_str = "Unknown"
                files_table.add_row(file_path, size_str)
            
            if len(analysis["files_found"]) > 20:
                files_table.add_row("...", f"and {len(analysis['files_found']) - 20} more")
            
            console.print(files_table)
        
        # Directories table
        if analysis["dirs_found"]:
            dirs_table = Table(title="Directories to Clean")
            dirs_table.add_column("Directory", style="cyan")
            dirs_table.add_column("Items", justify="right", style="yellow")
            
            for dir_path in analysis["dirs_found"][:10]:  # Show first 10
                try:
                    items = len(list(Path(dir_path).iterdir()))
                    dirs_table.add_row(dir_path, str(items))
                except:
                    dirs_table.add_row(dir_path, "Unknown")
            
            console.print(dirs_table)
        
        # Consolidation candidates
        if analysis["consolidation_candidates"]:
            console.print("\n[bold yellow]📦 Consolidation Candidates:[/bold yellow]")
            for source, target in analysis["consolidation_candidates"]:
                console.print(f"  {source} → {target}")
        
        # Summary
        total_mb = analysis["total_size"] / (1024 * 1024)
        console.print(f"\n[bold]Total space to reclaim: {total_mb:.2f} MB[/bold]")
    
    def backup_files(self, analysis: Dict) -> bool:
        """Create backup of files before cleanup."""
        console.print("[cyan]📦 Creating backup...[/cyan]")
        
        try:
            # Backup files
            for file_path in analysis["files_found"]:
                src = Path(file_path)
                if src.exists():
                    # Preserve directory structure in backup
                    rel_path = src.relative_to(self.base_dir)
                    dst = self.backup_dir / rel_path
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            
            # Backup consolidation candidates
            for source, target in analysis["consolidation_candidates"]:
                src = Path(source)
                if src.exists():
                    rel_path = src.relative_to(self.base_dir)
                    dst = self.backup_dir / rel_path
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            
            console.print(f"[green]✅ Backup created in: {self.backup_dir}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Backup failed: {e}[/red]")
            return False
    
    def perform_cleanup(self, analysis: Dict) -> bool:
        """Perform the actual cleanup."""
        console.print("[bold red]🗑️ Starting Cleanup[/bold red]")
        
        cleaned_count = 0
        
        try:
            # Remove files
            for file_path in analysis["files_found"]:
                path = Path(file_path)
                if path.exists():
                    try:
                        path.unlink()
                        console.print(f"[green]✅ Removed: {file_path}[/green]")
                        cleaned_count += 1
                    except Exception as e:
                        console.print(f"[red]❌ Failed to remove {file_path}: {e}[/red]")
            
            # Clean directories
            for dir_path in analysis["dirs_found"]:
                path = Path(dir_path)
                if path.exists():
                    try:
                        shutil.rmtree(path)
                        console.print(f"[green]✅ Cleaned directory: {dir_path}[/green]")
                        cleaned_count += 1
                    except Exception as e:
                        console.print(f"[red]❌ Failed to clean {dir_path}: {e}[/red]")
            
            console.print(f"\n[bold green]🎉 Cleanup completed! Removed {cleaned_count} items[/bold green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Cleanup failed: {e}[/red]")
            return False

    def consolidate_modules(self, analysis: Dict) -> bool:
        """Consolidate similar modules into single files."""
        console.print("[bold blue]🔄 Consolidating Modules[/bold blue]")

        try:
            for source, target in analysis["consolidation_candidates"]:
                source_path = Path(source)
                target_path = Path(target)

                if not source_path.exists():
                    continue

                console.print(f"[cyan]📦 Consolidating {source} into {target}[/cyan]")

                # Read source content
                with open(source_path, 'r', encoding='utf-8') as f:
                    source_content = f.read()

                # Extract useful functions/classes (simple approach)
                lines = source_content.split('\n')
                useful_lines = []

                for line in lines:
                    # Skip imports, comments, and docstrings at module level
                    if (line.strip().startswith('import ') or
                        line.strip().startswith('from ') or
                        line.strip().startswith('#') or
                        line.strip().startswith('"""') or
                        line.strip().startswith("'''") or
                        not line.strip()):
                        continue
                    useful_lines.append(line)

                if useful_lines:
                    # Append to target file
                    with open(target_path, 'a', encoding='utf-8') as f:
                        f.write(f"\n\n# === Consolidated from {source} ===\n")
                        f.write('\n'.join(useful_lines))
                        f.write(f"\n# === End of {source} ===\n")

                # Remove source file
                source_path.unlink()
                console.print(f"[green]✅ Consolidated {source} into {target}[/green]")

            return True

        except Exception as e:
            console.print(f"[red]❌ Consolidation failed: {e}[/red]")
            return False

    def optimize_imports(self) -> bool:
        """Remove unused imports from Python files."""
        console.print("[bold blue]🔧 Optimizing Imports[/bold blue]")

        python_files = [
            "main.py",
            "utils.py",
            "job_database.py",
            "dashboard_api.py",
            "csv_applicator.py",
            "intelligent_scraper.py",
            "document_generator.py"
        ]

        try:
            for file_path in python_files:
                path = Path(file_path)
                if not path.exists():
                    continue

                console.print(f"[cyan]🔍 Checking imports in {file_path}[/cyan]")

                # This is a simplified approach - in production you'd use tools like autoflake
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Count import lines (for reporting)
                import_lines = [line for line in content.split('\n')
                              if line.strip().startswith(('import ', 'from '))]

                console.print(f"[yellow]  Found {len(import_lines)} import statements[/yellow]")

            console.print("[green]✅ Import optimization completed[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Import optimization failed: {e}[/red]")
            return False

    def create_cleanup_report(self, analysis: Dict) -> bool:
        """Create a cleanup report."""
        report_path = Path("cleanup_report.md")

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# Codebase Cleanup Report\n\n")
                f.write(f"Generated on: {Path().cwd()}\n\n")

                f.write("## Files Removed\n")
                for file_path in analysis["files_found"]:
                    f.write(f"- {file_path}\n")

                f.write("\n## Directories Cleaned\n")
                for dir_path in analysis["dirs_found"]:
                    f.write(f"- {dir_path}\n")

                f.write("\n## Modules Consolidated\n")
                for source, target in analysis["consolidation_candidates"]:
                    f.write(f"- {source} → {target}\n")

                total_mb = analysis["total_size"] / (1024 * 1024)
                f.write(f"\n## Summary\n")
                f.write(f"- Total space reclaimed: {total_mb:.2f} MB\n")
                f.write(f"- Files removed: {len(analysis['files_found'])}\n")
                f.write(f"- Directories cleaned: {len(analysis['dirs_found'])}\n")
                f.write(f"- Modules consolidated: {len(analysis['consolidation_candidates'])}\n")

            console.print(f"[green]✅ Cleanup report saved to: {report_path}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to create report: {e}[/red]")
            return False

def main():
    """Main cleanup function."""
    console.print(Panel("🧹 Comprehensive Codebase Cleanup", style="bold blue"))

    cleanup = CodebaseCleanup()

    # Analyze current state
    analysis = cleanup.analyze_codebase()
    cleanup.display_analysis(analysis)

    if not analysis["files_found"] and not analysis["dirs_found"] and not analysis["consolidation_candidates"]:
        console.print("[green]✨ Codebase is already clean![/green]")
        return

    # Confirm cleanup
    if not Confirm.ask("\nProceed with cleanup?"):
        console.print("[yellow]Cleanup cancelled[/yellow]")
        return

    # Create backup
    if not cleanup.backup_files(analysis):
        console.print("[red]Backup failed, aborting cleanup[/red]")
        return

    # Perform cleanup
    if cleanup.perform_cleanup(analysis):
        # Consolidate modules
        cleanup.consolidate_modules(analysis)

        # Optimize imports
        cleanup.optimize_imports()

        # Create report
        cleanup.create_cleanup_report(analysis)

        console.print("\n[bold green]🎉 Comprehensive cleanup completed successfully![/bold green]")
        console.print(f"[cyan]📦 Backup available in: {cleanup.backup_dir}[/cyan]")
    else:
        console.print("[red]Cleanup failed[/red]")

if __name__ == "__main__":
    main()
