"""
System Health Monitor
Provides comprehensive health checks and automatic recovery mechanisms for the job automation system.
"""

import os
import sys
import time
import json
import psutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class SystemHealthMonitor:
    """
    Comprehensive system health monitoring with automatic recovery.
    Monitors all critical components and provides recovery mechanisms.
    """
    
    def __init__(self, config_path: str = "health_config.json"):
        """
        Initialize the health monitor.
        
        Args:
            config_path: Path to health monitoring configuration
        """
        self.config_path = Path(config_path)
        self.health_log_path = Path("health_logs")
        self.health_log_path.mkdir(exist_ok=True)
        
        # Load or create configuration
        self.config = self._load_or_create_config()
        
        # Health status tracking
        self.last_check_time = None
        self.health_status = {}
        self.recovery_attempts = {}
        
        console.print("[green]🏥 System Health Monitor initialized[/green]")
    
    def _load_or_create_config(self) -> Dict:
        """Load or create health monitoring configuration."""
        default_config = {
            "check_interval_seconds": 300,  # 5 minutes
            "max_recovery_attempts": 3,
            "critical_disk_usage_percent": 90,
            "critical_memory_usage_percent": 85,
            "database_max_size_mb": 1000,
            "log_retention_days": 30,
            "auto_recovery_enabled": True,
            "components_to_monitor": [
                "database",
                "disk_space",
                "memory_usage",
                "browser_processes",
                "network_connectivity",
                "ollama_service",
                "file_permissions",
                "dependencies"
            ]
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                console.print(f"[yellow]⚠️ Error loading config, using defaults: {e}[/yellow]")
        
        # Save default config
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def run_comprehensive_health_check(self) -> Dict[str, Dict]:
        """
        Run comprehensive health check on all system components.
        
        Returns:
            Dictionary with health status for each component
        """
        console.print("[bold blue]🔍 Running Comprehensive Health Check[/bold blue]")
        
        health_results = {}
        
        for component in self.config["components_to_monitor"]:
            try:
                console.print(f"[cyan]Checking {component}...[/cyan]")
                
                if component == "database":
                    health_results[component] = self._check_database_health()
                elif component == "disk_space":
                    health_results[component] = self._check_disk_space()
                elif component == "memory_usage":
                    health_results[component] = self._check_memory_usage()
                elif component == "browser_processes":
                    health_results[component] = self._check_browser_processes()
                elif component == "network_connectivity":
                    health_results[component] = self._check_network_connectivity()
                elif component == "ollama_service":
                    health_results[component] = self._check_ollama_service()
                elif component == "file_permissions":
                    health_results[component] = self._check_file_permissions()
                elif component == "dependencies":
                    health_results[component] = self._check_dependencies()
                else:
                    health_results[component] = {"status": "unknown", "message": "Unknown component"}
                
            except Exception as e:
                health_results[component] = {
                    "status": "error",
                    "message": f"Health check failed: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
        
        # Update health status
        self.health_status = health_results
        self.last_check_time = datetime.now()
        
        # Log health check results
        self._log_health_results(health_results)
        
        # Display results
        self._display_health_results(health_results)
        
        # Attempt automatic recovery if enabled
        if self.config["auto_recovery_enabled"]:
            self._attempt_automatic_recovery(health_results)
        
        return health_results
    
    def _check_database_health(self) -> Dict:
        """Check database health and integrity."""
        try:
            db_path = Path("jobs.db")
            
            if not db_path.exists():
                return {"status": "warning", "message": "Database file not found"}
            
            # Check database size
            db_size_mb = db_path.stat().st_size / (1024 * 1024)
            if db_size_mb > self.config["database_max_size_mb"]:
                return {
                    "status": "warning",
                    "message": f"Database size ({db_size_mb:.1f}MB) exceeds limit ({self.config['database_max_size_mb']}MB)"
                }
            
            # Test database connection and integrity
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                
                if integrity_result != "ok":
                    return {"status": "critical", "message": f"Database integrity check failed: {integrity_result}"}
                
                # Check if tables exist
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ["jobs", "applications"]
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    return {"status": "critical", "message": f"Missing tables: {missing_tables}"}
            
            return {
                "status": "healthy",
                "message": f"Database healthy ({db_size_mb:.1f}MB, {len(tables)} tables)"
            }
            
        except Exception as e:
            return {"status": "critical", "message": f"Database check failed: {str(e)}"}
    
    def _check_disk_space(self) -> Dict:
        """Check available disk space."""
        try:
            disk_usage = psutil.disk_usage('.')
            used_percent = (disk_usage.used / disk_usage.total) * 100
            free_gb = disk_usage.free / (1024**3)
            
            if used_percent > self.config["critical_disk_usage_percent"]:
                return {
                    "status": "critical",
                    "message": f"Disk usage critical: {used_percent:.1f}% used, {free_gb:.1f}GB free"
                }
            elif used_percent > 80:
                return {
                    "status": "warning",
                    "message": f"Disk usage high: {used_percent:.1f}% used, {free_gb:.1f}GB free"
                }
            else:
                return {
                    "status": "healthy",
                    "message": f"Disk usage normal: {used_percent:.1f}% used, {free_gb:.1f}GB free"
                }
                
        except Exception as e:
            return {"status": "error", "message": f"Disk check failed: {str(e)}"}
    
    def _check_memory_usage(self) -> Dict:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            available_gb = memory.available / (1024**3)
            
            if used_percent > self.config["critical_memory_usage_percent"]:
                return {
                    "status": "critical",
                    "message": f"Memory usage critical: {used_percent:.1f}% used, {available_gb:.1f}GB available"
                }
            elif used_percent > 75:
                return {
                    "status": "warning",
                    "message": f"Memory usage high: {used_percent:.1f}% used, {available_gb:.1f}GB available"
                }
            else:
                return {
                    "status": "healthy",
                    "message": f"Memory usage normal: {used_percent:.1f}% used, {available_gb:.1f}GB available"
                }
                
        except Exception as e:
            return {"status": "error", "message": f"Memory check failed: {str(e)}"}
    
    def _check_browser_processes(self) -> Dict:
        """Check for zombie browser processes."""
        try:
            browser_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    if any(browser in proc.info['name'].lower() for browser in ['chrome', 'firefox', 'edge', 'opera']):
                        browser_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if len(browser_processes) > 20:
                return {
                    "status": "warning",
                    "message": f"Many browser processes running: {len(browser_processes)}"
                }
            else:
                return {
                    "status": "healthy",
                    "message": f"Browser processes normal: {len(browser_processes)} running"
                }
                
        except Exception as e:
            return {"status": "error", "message": f"Browser process check failed: {str(e)}"}
    
    def _check_network_connectivity(self) -> Dict:
        """Check network connectivity."""
        try:
            import requests
            
            test_urls = ["https://www.google.com", "https://github.com"]
            successful_connections = 0
            
            for url in test_urls:
                try:
                    response = requests.head(url, timeout=5)
                    if response.status_code < 400:
                        successful_connections += 1
                except:
                    continue
            
            if successful_connections == 0:
                return {"status": "critical", "message": "No network connectivity"}
            elif successful_connections < len(test_urls):
                return {"status": "warning", "message": "Limited network connectivity"}
            else:
                return {"status": "healthy", "message": "Network connectivity normal"}
                
        except Exception as e:
            return {"status": "error", "message": f"Network check failed: {str(e)}"}
    
    def _check_ollama_service(self) -> Dict:
        """Check Ollama service availability."""
        try:
            import requests
            
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "healthy",
                    "message": f"Ollama service running with {len(models)} models"
                }
            else:
                return {"status": "warning", "message": "Ollama service not responding"}
                
        except Exception as e:
            return {"status": "warning", "message": f"Ollama service check failed: {str(e)}"}
    
    def _check_file_permissions(self) -> Dict:
        """Check file permissions for critical directories."""
        try:
            critical_paths = [
                Path("."),
                Path("profiles"),
                Path("temp"),
                Path("customized_documents")
            ]
            
            permission_issues = []
            
            for path in critical_paths:
                if path.exists():
                    if not os.access(path, os.R_OK | os.W_OK):
                        permission_issues.append(str(path))
            
            if permission_issues:
                return {
                    "status": "critical",
                    "message": f"Permission issues with: {', '.join(permission_issues)}"
                }
            else:
                return {"status": "healthy", "message": "File permissions normal"}
                
        except Exception as e:
            return {"status": "error", "message": f"Permission check failed: {str(e)}"}
    
    def _check_dependencies(self) -> Dict:
        """Check critical Python dependencies."""
        try:
            critical_modules = [
                "playwright", "requests", "rich", "beautifulsoup4",
                "python-docx", "pandas", "psutil"
            ]
            
            missing_modules = []
            
            for module in critical_modules:
                try:
                    __import__(module.replace("-", "_"))
                except ImportError:
                    missing_modules.append(module)
            
            if missing_modules:
                return {
                    "status": "critical",
                    "message": f"Missing dependencies: {', '.join(missing_modules)}"
                }
            else:
                return {"status": "healthy", "message": "All dependencies available"}
                
        except Exception as e:
            return {"status": "error", "message": f"Dependency check failed: {str(e)}"}
    
    def _display_health_results(self, results: Dict[str, Dict]) -> None:
        """Display health check results in a formatted table."""
        table = Table(title="System Health Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Message", style="white")
        
        for component, result in results.items():
            status = result.get("status", "unknown")
            message = result.get("message", "No message")
            
            # Color code status
            if status == "healthy":
                status_display = "[green]✅ Healthy[/green]"
            elif status == "warning":
                status_display = "[yellow]⚠️ Warning[/yellow]"
            elif status == "critical":
                status_display = "[red]❌ Critical[/red]"
            else:
                status_display = "[gray]❓ Unknown[/gray]"
            
            table.add_row(component.title(), status_display, message)
        
        console.print(table)
    
    def _log_health_results(self, results: Dict[str, Dict]) -> None:
        """Log health check results to file."""
        try:
            log_file = self.health_log_path / f"health_{datetime.now().strftime('%Y%m%d')}.json"
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "results": results
            }
            
            # Append to daily log file
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            console.print(f"[yellow]⚠️ Error logging health results: {e}[/yellow]")
    
    def _attempt_automatic_recovery(self, results: Dict[str, Dict]) -> None:
        """Attempt automatic recovery for failed components."""
        console.print("[bold yellow]🔧 Attempting Automatic Recovery[/bold yellow]")
        
        for component, result in results.items():
            if result.get("status") in ["critical", "error"]:
                recovery_key = f"{component}_{datetime.now().strftime('%Y%m%d')}"
                
                # Check if we've already tried recovery today
                if recovery_key in self.recovery_attempts:
                    if self.recovery_attempts[recovery_key] >= self.config["max_recovery_attempts"]:
                        console.print(f"[red]❌ Max recovery attempts reached for {component}[/red]")
                        continue
                else:
                    self.recovery_attempts[recovery_key] = 0
                
                # Attempt recovery
                console.print(f"[cyan]🔧 Attempting recovery for {component}...[/cyan]")
                recovery_success = self._recover_component(component, result)
                
                self.recovery_attempts[recovery_key] += 1
                
                if recovery_success:
                    console.print(f"[green]✅ Recovery successful for {component}[/green]")
                else:
                    console.print(f"[red]❌ Recovery failed for {component}[/red]")
    
    def _recover_component(self, component: str, result: Dict) -> bool:
        """Attempt to recover a specific component."""
        try:
            if component == "database":
                return self._recover_database()
            elif component == "disk_space":
                return self._recover_disk_space()
            elif component == "browser_processes":
                return self._recover_browser_processes()
            elif component == "file_permissions":
                return self._recover_file_permissions()
            else:
                console.print(f"[yellow]⚠️ No recovery method for {component}[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Recovery error for {component}: {e}[/red]")
            return False
    
    def _recover_database(self) -> bool:
        """Attempt to recover database issues."""
        try:
            # Try to backup and recreate database if corrupted
            db_path = Path("jobs.db")
            if db_path.exists():
                backup_path = Path(f"jobs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
                db_path.rename(backup_path)
                console.print(f"[yellow]📦 Database backed up to {backup_path}[/yellow]")
            
            # Initialize new database
            from job_database import JobDatabase
            db = JobDatabase()
            console.print("[green]✅ New database initialized[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Database recovery failed: {e}[/red]")
            return False
    
    def _recover_disk_space(self) -> bool:
        """Attempt to free up disk space."""
        try:
            # Clean up temp files
            temp_dirs = [Path("temp"), Path("customized_documents")]
            files_cleaned = 0
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    for file_path in temp_dir.glob("*"):
                        if file_path.is_file() and file_path.stat().st_mtime < time.time() - 86400:  # 1 day old
                            file_path.unlink()
                            files_cleaned += 1
            
            console.print(f"[green]🗑️ Cleaned {files_cleaned} temporary files[/green]")
            return files_cleaned > 0
            
        except Exception as e:
            console.print(f"[red]❌ Disk space recovery failed: {e}[/red]")
            return False
    
    def _recover_browser_processes(self) -> bool:
        """Attempt to clean up browser processes."""
        try:
            killed_processes = 0
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if any(browser in proc.info['name'].lower() for browser in ['chrome', 'firefox', 'edge']):
                        if 'helper' in proc.info['name'].lower() or 'renderer' in proc.info['name'].lower():
                            proc.terminate()
                            killed_processes += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            console.print(f"[green]🔧 Terminated {killed_processes} browser helper processes[/green]")
            return killed_processes > 0
            
        except Exception as e:
            console.print(f"[red]❌ Browser process recovery failed: {e}[/red]")
            return False
    
    def _recover_file_permissions(self) -> bool:
        """Attempt to fix file permissions."""
        try:
            # This is a placeholder - actual implementation would depend on OS
            console.print("[yellow]⚠️ File permission recovery requires manual intervention[/yellow]")
            return False
            
        except Exception as e:
            console.print(f"[red]❌ File permission recovery failed: {e}[/red]")
            return False
    
    def get_health_summary(self) -> Dict:
        """Get a summary of current health status."""
        if not self.health_status:
            return {"status": "unknown", "message": "No health check performed yet"}
        
        critical_count = sum(1 for result in self.health_status.values() if result.get("status") == "critical")
        warning_count = sum(1 for result in self.health_status.values() if result.get("status") == "warning")
        healthy_count = sum(1 for result in self.health_status.values() if result.get("status") == "healthy")
        
        if critical_count > 0:
            overall_status = "critical"
        elif warning_count > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "critical_issues": critical_count,
            "warnings": warning_count,
            "healthy_components": healthy_count,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None
        }


# Global health monitor instance
health_monitor = SystemHealthMonitor()


if __name__ == "__main__":
    # Run health check
    console.print("[bold]🏥 System Health Monitor Test[/bold]")
    results = health_monitor.run_comprehensive_health_check()
    
    # Display summary
    summary = health_monitor.get_health_summary()
    console.print(f"\n[bold]Overall Status: {summary['overall_status'].upper()}[/bold]")
    console.print(f"Critical Issues: {summary['critical_issues']}")
    console.print(f"Warnings: {summary['warnings']}")
    console.print(f"Healthy Components: {summary['healthy_components']}")
