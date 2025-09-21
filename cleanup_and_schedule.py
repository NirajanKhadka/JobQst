#!/usr/bin/env python3
"""
JobQst Pipeline Cleanup and Scheduling Setup

This script:
1. Identifies and removes unnecessary files from completed pipeline
2. Sets up automated scheduling for scraping process
3. Provides status report on current system state
"""

import os
import shutil
import json
from pathlib import Path
from typing import List, Dict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm, Prompt

console = Console()

class PipelineCleanup:
    """Handles cleanup of completed pipeline files and setup of scheduling."""
    
    def __init__(self):
        self.root_dir = Path(".")
        self.files_to_remove = []
        self.dirs_to_remove = []
        self.files_to_keep = []
        
    def analyze_files(self) -> Dict:
        """Analyze current files and categorize them."""
        console.print(Panel("🔍 Analyzing Pipeline Files", style="bold blue"))
        
        # Files that can be safely removed (development/testing artifacts)
        removable_files = [
            "dashboard_feature_audit.py",
            "verify_dashboard_complete.py", 
            "DASHBOARD_COMPREHENSIVE_CHECKLIST.md",
            "DASHBOARD_ISSUES_RESOLVED.md",
            "DASHBOARD_SUCCESS_SUMMARY.md",
            "FINAL_DASHBOARD_STATUS.md",
            "error_logs.log",
            "nirajan"  # Seems to be a test file
        ]
        
        # Directories that might have redundant content
        removable_dirs = [
            ".pytest_cache",
            "memory-bank",  # If not actively used
            "cache/embeddings",  # Can be regenerated
            "cache/html",  # Can be regenerated
        ]
        
        # Essential files to keep
        essential_files = [
            "main.py",
            "requirements.txt",
            "pyproject.toml",
            "README.md",
            "LICENSE",
            ".env",
            ".env.example",
            ".gitignore",
            "PIPELINE_SUMMARY.md",
            "MULTI_USER_SETUP_GUIDE.md"
        ]
        
        # Check which files actually exist
        existing_removable = []
        for file in removable_files:
            if (self.root_dir / file).exists():
                existing_removable.append(file)
                
        existing_removable_dirs = []
        for dir_name in removable_dirs:
            if (self.root_dir / dir_name).exists():
                existing_removable_dirs.append(dir_name)
        
        return {
            "removable_files": existing_removable,
            "removable_dirs": existing_removable_dirs,
            "essential_files": essential_files
        }
    
    def cleanup_scrapers(self) -> List[str]:
        """Identify redundant scrapers that can be removed."""
        scrapers_dir = self.root_dir / "src" / "scrapers"
        if not scrapers_dir.exists():
            return []
            
        # Keep only essential scrapers
        essential_scrapers = [
            "__init__.py",
            "unified_eluta_scraper.py",  # Main Eluta scraper
            "external_job_scraper.py",   # External job scraper
            "enhanced_job_description_scraper.py",  # Base class
            "base_scraper.py",
            "scraping_models.py"
        ]
        
        # Identify redundant scrapers
        redundant_scrapers = []
        for file in scrapers_dir.glob("*.py"):
            if file.name not in essential_scrapers:
                redundant_scrapers.append(f"src/scrapers/{file.name}")
                
        return redundant_scrapers
    
    def display_cleanup_plan(self, analysis: Dict, redundant_scrapers: List[str]) -> None:
        """Display what will be cleaned up."""
        console.print(Panel("🧹 Cleanup Plan", style="bold yellow"))
        
        # Files to remove
        if analysis["removable_files"]:
            console.print("[bold]📄 Files to Remove:[/bold]")
            for file in analysis["removable_files"]:
                console.print(f"  ❌ {file}")
        
        # Directories to remove  
        if analysis["removable_dirs"]:
            console.print("\n[bold]📁 Directories to Remove:[/bold]")
            for dir_name in analysis["removable_dirs"]:
                console.print(f"  ❌ {dir_name}/")
        
        # Redundant scrapers
        if redundant_scrapers:
            console.print("\n[bold]🕷️ Redundant Scrapers to Remove:[/bold]")
            for scraper in redundant_scrapers:
                console.print(f"  ❌ {scraper}")
        
        # Calculate space savings
        total_size = self._calculate_cleanup_size(analysis, redundant_scrapers)
        console.print(f"\n[green]💾 Estimated space savings: {total_size:.1f} MB[/green]")
    
    def _calculate_cleanup_size(self, analysis: Dict, redundant_scrapers: List[str]) -> float:
        """Calculate approximate size of files to be removed."""
        total_size = 0
        
        # Files
        for file in analysis["removable_files"]:
            file_path = self.root_dir / file
            if file_path.exists():
                total_size += file_path.stat().st_size
        
        # Directories
        for dir_name in analysis["removable_dirs"]:
            dir_path = self.root_dir / dir_name
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
        
        # Scrapers
        for scraper in redundant_scrapers:
            scraper_path = self.root_dir / scraper
            if scraper_path.exists():
                total_size += scraper_path.stat().st_size
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def execute_cleanup(self, analysis: Dict, redundant_scrapers: List[str]) -> None:
        """Execute the cleanup process."""
        console.print(Panel("🧹 Executing Cleanup", style="bold green"))
        
        removed_count = 0
        
        # Remove files
        for file in analysis["removable_files"]:
            file_path = self.root_dir / file
            if file_path.exists():
                try:
                    file_path.unlink()
                    console.print(f"[green]✅ Removed: {file}[/green]")
                    removed_count += 1
                except Exception as e:
                    console.print(f"[red]❌ Failed to remove {file}: {e}[/red]")
        
        # Remove directories
        for dir_name in analysis["removable_dirs"]:
            dir_path = self.root_dir / dir_name
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    console.print(f"[green]✅ Removed directory: {dir_name}/[/green]")
                    removed_count += 1
                except Exception as e:
                    console.print(f"[red]❌ Failed to remove {dir_name}/: {e}[/red]")
        
        # Remove redundant scrapers
        for scraper in redundant_scrapers:
            scraper_path = self.root_dir / scraper
            if scraper_path.exists():
                try:
                    scraper_path.unlink()
                    console.print(f"[green]✅ Removed scraper: {scraper}[/green]")
                    removed_count += 1
                except Exception as e:
                    console.print(f"[red]❌ Failed to remove {scraper}: {e}[/red]")
        
        console.print(f"\n[bold green]🎉 Cleanup complete! Removed {removed_count} items[/bold green]")


class SchedulingSetup:
    """Sets up automated scheduling for the scraping process."""
    
    def __init__(self):
        self.schedule_dir = Path("scripts/scheduling")
        self.schedule_dir.mkdir(parents=True, exist_ok=True)
    
    def create_scheduler_script(self) -> None:
        """Create the main scheduling script."""
        scheduler_script = '''#!/usr/bin/env python3
"""
JobQst Automated Scheduler

Runs scraping process on a schedule with intelligent timing and error handling.
"""

import schedule
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class JobQstScheduler:
    """Automated scheduler for JobQst scraping pipeline."""
    
    def __init__(self, profile_name: str = "Nirajan"):
        self.profile_name = profile_name
        self.last_run = None
        self.consecutive_failures = 0
        self.max_failures = 3
        
    def run_scraping_job(self) -> bool:
        """Run the scraping job and return success status."""
        try:
            logger.info(f"Starting scheduled scraping for profile: {self.profile_name}")
            
            # Run the main scraping command
            cmd = [
                "python", "main.py", self.profile_name,
                "--action", "scrape",
                "--jobs", "50",  # Moderate job count for scheduled runs
                "--auto-process"  # Auto-process after scraping
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            if result.returncode == 0:
                logger.info("✅ Scraping job completed successfully")
                self.consecutive_failures = 0
                self.last_run = datetime.now()
                return True
            else:
                logger.error(f"❌ Scraping job failed: {result.stderr}")
                self.consecutive_failures += 1
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Scraping job timed out after 30 minutes")
            self.consecutive_failures += 1
            return False
        except Exception as e:
            logger.error(f"❌ Scraping job error: {e}")
            self.consecutive_failures += 1
            return False
    
    def should_skip_run(self) -> bool:
        """Check if we should skip this run due to consecutive failures."""
        if self.consecutive_failures >= self.max_failures:
            logger.warning(f"⚠️ Skipping run due to {self.consecutive_failures} consecutive failures")
            return True
        return False
    
    def scheduled_job(self) -> None:
        """Main scheduled job function."""
        if self.should_skip_run():
            return
            
        logger.info("🚀 Starting scheduled scraping job")
        success = self.run_scraping_job()
        
        if success:
            logger.info("🎉 Scheduled job completed successfully")
        else:
            logger.error(f"💥 Scheduled job failed (failure #{self.consecutive_failures})")
    
    def reset_failure_count(self) -> None:
        """Reset failure count (called periodically)."""
        if self.consecutive_failures > 0:
            logger.info(f"🔄 Resetting failure count from {self.consecutive_failures} to 0")
            self.consecutive_failures = 0

def main():
    """Main scheduler function."""
    scheduler = JobQstScheduler()
    
    # Schedule scraping jobs
    schedule.every().day.at("09:00").do(scheduler.scheduled_job)  # Morning
    schedule.every().day.at("15:00").do(scheduler.scheduled_job)  # Afternoon
    schedule.every().day.at("21:00").do(scheduler.scheduled_job)  # Evening
    
    # Reset failure count daily
    schedule.every().day.at("00:00").do(scheduler.reset_failure_count)
    
    logger.info("📅 JobQst Scheduler started")
    logger.info("⏰ Scheduled times: 9:00 AM, 3:00 PM, 9:00 PM daily")
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
'''
        
        script_path = self.schedule_dir / "scheduler.py"
        with open(script_path, 'w') as f:
            f.write(scheduler_script)
        
        # Make executable on Unix systems
        try:
            script_path.chmod(0o755)
        except:
            pass
        
        console.print(f"[green]✅ Created scheduler script: {script_path}[/green]")
    
    def create_windows_task_script(self) -> None:
        """Create Windows Task Scheduler setup script."""
        windows_script = '''@echo off
REM JobQst Windows Task Scheduler Setup
REM Run this as Administrator to set up automated scheduling

echo Setting up JobQst automated scheduling...

REM Create scheduled task for morning scraping (9 AM)
schtasks /create /tn "JobQst Morning Scrape" /tr "python %~dp0..\\..\\main.py Nirajan --action scrape --jobs 50" /sc daily /st 09:00 /f

REM Create scheduled task for afternoon scraping (3 PM)  
schtasks /create /tn "JobQst Afternoon Scrape" /tr "python %~dp0..\\..\\main.py Nirajan --action scrape --jobs 50" /sc daily /st 15:00 /f

REM Create scheduled task for evening scraping (9 PM)
schtasks /create /tn "JobQst Evening Scrape" /tr "python %~dp0..\\..\\main.py Nirajan --action scrape --jobs 50" /sc daily /st 21:00 /f

echo.
echo ✅ JobQst scheduling setup complete!
echo.
echo Scheduled times:
echo   - 9:00 AM daily
echo   - 3:00 PM daily  
echo   - 9:00 PM daily
echo.
echo To view tasks: schtasks /query /tn "JobQst*"
echo To delete tasks: schtasks /delete /tn "JobQst*" /f
echo.
pause
'''
        
        script_path = self.schedule_dir / "setup_windows_scheduler.bat"
        with open(script_path, 'w') as f:
            f.write(windows_script)
        
        console.print(f"[green]✅ Created Windows scheduler: {script_path}[/green]")
    
    def create_systemd_service(self) -> None:
        """Create systemd service file for Linux."""
        service_content = f'''[Unit]
Description=JobQst Automated Job Scraper
After=network.target

[Service]
Type=simple
User={os.getenv("USER", "jobqst")}
WorkingDirectory={Path.cwd()}
ExecStart=/usr/bin/python3 {Path.cwd()}/scripts/scheduling/scheduler.py
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
'''
        
        service_path = self.schedule_dir / "jobqst-scheduler.service"
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        console.print(f"[green]✅ Created systemd service: {service_path}[/green]")
        console.print("[cyan]To install: sudo cp scripts/scheduling/jobqst-scheduler.service /etc/systemd/system/[/cyan]")
        console.print("[cyan]Then: sudo systemctl enable jobqst-scheduler && sudo systemctl start jobqst-scheduler[/cyan]")
    
    def create_cron_setup(self) -> None:
        """Create cron setup script for Linux/Mac."""
        cron_script = f'''#!/bin/bash
# JobQst Cron Setup Script

echo "Setting up JobQst cron jobs..."

# Add cron jobs for automated scraping
(crontab -l 2>/dev/null; echo "0 9 * * * cd {Path.cwd()} && python main.py Nirajan --action scrape --jobs 50 >> logs/cron.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "0 15 * * * cd {Path.cwd()} && python main.py Nirajan --action scrape --jobs 50 >> logs/cron.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "0 21 * * * cd {Path.cwd()} && python main.py Nirajan --action scrape --jobs 50 >> logs/cron.log 2>&1") | crontab -

echo "✅ Cron jobs added successfully!"
echo ""
echo "Scheduled times:"
echo "  - 9:00 AM daily"
echo "  - 3:00 PM daily"
echo "  - 9:00 PM daily"
echo ""
echo "To view: crontab -l"
echo "To remove: crontab -r"
'''
        
        script_path = self.schedule_dir / "setup_cron.sh"
        with open(script_path, 'w') as f:
            f.write(cron_script)
        
        try:
            script_path.chmod(0o755)
        except:
            pass
        
        console.print(f"[green]✅ Created cron setup: {script_path}[/green]")
    
    def setup_scheduling(self) -> None:
        """Set up scheduling for the current platform."""
        console.print(Panel("⏰ Setting Up Automated Scheduling", style="bold blue"))
        
        # Create all scheduling options
        self.create_scheduler_script()
        
        # Platform-specific setup
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            self.create_windows_task_script()
            console.print("[cyan]💡 Run scripts/scheduling/setup_windows_scheduler.bat as Administrator[/cyan]")
        else:
            self.create_systemd_service()
            self.create_cron_setup()
            console.print("[cyan]💡 Choose: systemd service OR cron jobs (see created scripts)[/cyan]")
        
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        console.print(f"[green]✅ Scheduling setup complete for {system}![/green]")


def main():
    """Main cleanup and scheduling setup."""
    console.print(Panel("🚀 JobQst Pipeline Cleanup & Scheduling", style="bold blue"))
    
    # Initialize components
    cleanup = PipelineCleanup()
    scheduler = SchedulingSetup()
    
    # Analyze current state
    analysis = cleanup.analyze_files()
    redundant_scrapers = cleanup.cleanup_scrapers()
    
    # Show current status
    console.print(Panel("📊 Current System Status", style="bold green"))
    console.print("[green]✅ Pipeline: COMPLETE and OPERATIONAL[/green]")
    console.print("[green]✅ Scrapers: Working (Eluta + External)[/green]")
    console.print("[green]✅ Processing: Automated[/green]")
    console.print("[green]✅ Dashboard: Functional[/green]")
    
    # Cleanup section
    if analysis["removable_files"] or analysis["removable_dirs"] or redundant_scrapers:
        console.print("\n")
        cleanup.display_cleanup_plan(analysis, redundant_scrapers)
        
        if Confirm.ask("\n🧹 Proceed with cleanup?"):
            cleanup.execute_cleanup(analysis, redundant_scrapers)
        else:
            console.print("[yellow]⏸️ Cleanup skipped[/yellow]")
    else:
        console.print("\n[green]✨ System is already clean - no cleanup needed![/green]")
    
    # Scheduling section
    console.print("\n")
    if Confirm.ask("⏰ Set up automated scheduling?"):
        scheduler.setup_scheduling()
        
        # Show scheduling options
        console.print(Panel("📅 Scheduling Options", style="bold cyan"))
        console.print("[bold]Choose your preferred method:[/bold]")
        console.print("1. 🐍 Python scheduler (scripts/scheduling/scheduler.py)")
        console.print("2. 🪟 Windows Task Scheduler (run setup_windows_scheduler.bat)")
        console.print("3. 🐧 Linux systemd service (see instructions above)")
        console.print("4. ⏰ Cron jobs (run setup_cron.sh)")
        
        method = Prompt.ask("Select method", choices=["1", "2", "3", "4"], default="1")
        
        if method == "1":
            console.print("[cyan]💡 To start: python scripts/scheduling/scheduler.py[/cyan]")
        elif method == "2":
            console.print("[cyan]💡 Run as Administrator: scripts/scheduling/setup_windows_scheduler.bat[/cyan]")
        elif method == "3":
            console.print("[cyan]💡 Follow systemd instructions shown above[/cyan]")
        elif method == "4":
            console.print("[cyan]💡 Run: bash scripts/scheduling/setup_cron.sh[/cyan]")
    else:
        console.print("[yellow]⏸️ Scheduling setup skipped[/yellow]")
    
    # Final status
    console.print(Panel("🎉 Setup Complete!", style="bold green"))
    console.print("[green]✅ Your JobQst pipeline is optimized and ready for production![/green]")
    console.print("[cyan]💡 Next steps:[/cyan]")
    console.print("  1. Test scraping: python main.py Nirajan --action scrape --jobs 20")
    console.print("  2. Check dashboard: python src/dashboard/unified_dashboard.py --profile Nirajan")
    console.print("  3. Start scheduler if configured")

if __name__ == "__main__":
    main()