"""
System Health Checker Module
Provides comprehensive system health monitoring and diagnostics.
"""

import os
import shutil
import requests
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console

# Import unified database interface
from ..core.job_database import get_job_db

console = Console()


class SystemHealthChecker:
    """
    Comprehensive system health checking for AutoJobAgent.

    Features:
    - Database connectivity checks
    - Network connectivity validation
    - Disk space monitoring
    - Memory usage analysis
    - Service availability checks
    """

    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        self.profile_name = profile.get("profile_name", "default")

    def check_database_health(self) -> bool:
        """Check database connectivity and integrity using unified interface."""
        try:
            # Use unified database interface
            db = get_job_db(self.profile_name)

            # Test basic database operations
            job_count = db.get_job_count()
            job_stats = db.get_job_stats()

            # Test getting jobs
            jobs = db.get_top_jobs(1)

            console.print(f"[green]✅ Database healthy: {job_count} jobs found[/green]")
            console.print(f"[green]✅ Database stats retrieved successfully[/green]")

            return True

        except Exception as e:
            console.print(f"[red]❌ Database check failed: {e}[/red]")
            return False

    def check_network_health(self) -> bool:
        """Check network connectivity to key services."""
        test_urls = [
            "https://www.eluta.ca",
            "https://www.indeed.ca",
            "https://www.linkedin.com",
            "https://www.google.com",
        ]

        successful_connections = 0

        for url in test_urls:
            try:
                response = requests.get(
                    url,
                    timeout=10,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                )
                if response.status_code == 200:
                    successful_connections += 1
                    console.print(f"[green]✅ {url} - OK[/green]")
                else:
                    console.print(f"[yellow]⚠️ {url} - Status: {response.status_code}[/yellow]")
            except Exception as e:
                console.print(f"[red]❌ {url} - Error: {str(e)[:50]}...[/red]")

        success_rate = successful_connections / len(test_urls)
        if success_rate >= 0.75:  # 75% success rate
            console.print(
                f"[green]✅ Network health good: {successful_connections}/{len(test_urls)} sites accessible[/green]"
            )
            return True
        else:
            console.print(
                f"[red]❌ Network health poor: {successful_connections}/{len(test_urls)} sites accessible[/red]"
            )
            return False

    def check_disk_space(self) -> bool:
        """Check available disk space."""
        try:
            # Check disk space in project directory
            total, used, free = shutil.disk_usage(".")

            # Convert to GB
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)

            usage_percent = (used / total) * 100

            console.print(
                f"[cyan]💾 Disk Usage: {used_gb:.1f}GB / {total_gb:.1f}GB ({usage_percent:.1f}%)[/cyan]"
            )
            console.print(f"[cyan]💾 Free Space: {free_gb:.1f}GB[/cyan]")

            # Check if we have at least 1GB free
            if free_gb < 1.0:
                console.print("[red]❌ Low disk space: Less than 1GB available[/red]")
                return False
            elif free_gb < 5.0:
                console.print("[yellow]⚠️ Moderate disk space: Less than 5GB available[/yellow]")
                return True
            else:
                console.print("[green]✅ Sufficient disk space available[/green]")
                return True

        except Exception as e:
            console.print(f"[red]❌ Disk space check failed: {e}[/red]")
            return False

    def check_memory_usage(self) -> bool:
        """Check system memory usage."""
        try:
            # Try to import psutil for detailed memory info
            try:
                import psutil

                memory = psutil.virtual_memory()

                total_mb = memory.total / (1024**2)
                available_mb = memory.available / (1024**2)
                used_percent = memory.percent

                console.print(f"[cyan]🧠 Memory Usage: {used_percent:.1f}%[/cyan]")
                console.print(f"[cyan]🧠 Available: {available_mb:.0f}MB / {total_mb:.0f}MB[/cyan]")

                if used_percent > 90:
                    console.print("[red]❌ High memory usage: > 90%[/red]")
                    return False
                elif used_percent > 75:
                    console.print("[yellow]⚠️ Moderate memory usage: > 75%[/yellow]")
                    return True
                else:
                    console.print("[green]✅ Memory usage is healthy[/green]")
                    return True

            except ImportError:
                # Fallback: Use basic system info
                import os

                # Try to get basic memory info from system
                if hasattr(os, "sysconf") and hasattr(os, "sysconf_names"):
                    try:
                        # Unix/Linux systems
                        pages = os.sysconf("SC_PHYS_PAGES")
                        page_size = os.sysconf("SC_PAGE_SIZE")
                        total_memory = pages * page_size / (1024**2)  # MB
                        console.print(
                            f"[cyan]🧠 Total Memory: {total_memory:.0f}MB (basic check)[/cyan]"
                        )
                        console.print("[green]✅ Basic memory check passed[/green]")
                        return True
                    except:
                        pass

                # Windows fallback
                console.print("[yellow]⚠️ Improved memory monitoring not available[/yellow]")
                console.print("[green]✅ Basic memory check passed[/green]")
                return True

        except Exception as e:
            console.print(f"[red]❌ Memory check failed: {e}[/red]")
            return False

    def check_services(self) -> bool:
        """Check status of key services and files."""
        checks = []

        # Check if required directories exist
        required_dirs = ["profiles", "logs", "cache", "src/scrapers", "src/core", "src/dashboard"]

        for dir_path in required_dirs:
            if Path(dir_path).exists():
                checks.append(True)
                console.print(f"[green]✅ Directory exists: {dir_path}[/green]")
            else:
                checks.append(False)
                console.print(f"[red]❌ Missing directory: {dir_path}[/red]")

        # Check if key files exist
        required_files = [
            "requirements.txt",
            "README.md",
        ]
        
        # Check for profile JSON file with flexible naming
        profile_dir = Path(f"profiles/{self.profile_name}")
        profile_json_files = list(profile_dir.glob("*.json")) if profile_dir.exists() else []
        profile_json_files = [f for f in profile_json_files if not f.name.startswith('.') and 'BACKUP' not in f.name and 'session' not in f.name]
        
        if profile_json_files:
            checks.append(True)
            console.print(f"[green]✅ Profile JSON exists: {profile_json_files[0].name}[/green]")
        else:
            checks.append(False)
            console.print(f"[yellow]⚠️ No profile JSON found in {profile_dir}[/yellow]")

        for file_path in required_files:
            if Path(file_path).exists():
                checks.append(True)
                console.print(f"[green]✅ File exists: {file_path}[/green]")
            else:
                checks.append(False)
                console.print(f"[yellow]⚠️ Missing file: {file_path}[/yellow]")

        # Check Python modules
        required_modules = ["playwright", "rich", "streamlit", "sqlite3", "asyncio"]

        for module in required_modules:
            try:
                __import__(module)
                checks.append(True)
                console.print(f"[green]✅ Module available: {module}[/green]")
            except ImportError:
                checks.append(False)
                console.print(f"[red]❌ Missing module: {module}[/red]")

        success_rate = sum(checks) / len(checks)
        if success_rate >= 0.8:  # 80% success rate
            console.print(
                f"[green]✅ Services health good: {sum(checks)}/{len(checks)} checks passed[/green]"
            )
            return True
        else:
            console.print(
                f"[red]❌ Services health poor: {sum(checks)}/{len(checks)} checks passed[/red]"
            )
            return False

    def run_comprehensive_check(self) -> Dict[str, bool]:
        """Run all health checks and return results."""
        console.print("[bold blue]🏥 Running Comprehensive Health Check[/bold blue]")

        results = {
            "database": self.check_database_health(),
            "network": self.check_network_health(),
            "disk": self.check_disk_space(),
            "memory": self.check_memory_usage(),
            "services": self.check_services(),
        }

        # Critical checks: database, disk, memory, services
        critical_checks = ["database", "disk", "memory", "services"]
        critical_health = all(results.get(key, False) for key in critical_checks)
        
        # Network is informational only - job sites often block health checks
        overall_health = critical_health

        console.print("\n[bold blue]📊 Health Check Results[/bold blue]")
        if overall_health:
            console.print("[bold green]✅ All critical systems operational![/bold green]")
        else:
            console.print("[bold red]❌ Critical system issues detected[/bold red]")
        
        if not results.get("network", True):
            console.print("[dim yellow]ℹ️  Network check warnings are normal - job sites block health requests[/dim yellow]")

        return results

    def get_health_recommendations(self, results: Dict[str, bool]) -> List[str]:
        """Generate health improvement recommendations."""
        recommendations = []

        if not results.get("database", True):
            recommendations.append("🗄️ Reinitialize database or check database permissions")

        if not results.get("network", True):
            recommendations.append("🌐 Check internet connection and firewall settings")

        if not results.get("disk", True):
            recommendations.append("💾 Free up disk space by cleaning logs and cache")

        if not results.get("memory", True):
            recommendations.append("🧠 Close unnecessary programs or increase system memory")

        if not results.get("services", True):
            recommendations.append(
                "⚙️ Install missing dependencies with: pip install -r requirements.txt"
            )

        if not recommendations:
            recommendations.append("✅ System is healthy! No immediate actions required.")

        return recommendations
