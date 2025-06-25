#!/usr/bin/env python3
"""
Specific Issue Testing for AutoJobAgent
Tests the specific issues found in comprehensive testing and provides detailed analysis.
"""

import time
import traceback
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.core.job_database import ModernJobDatabase

console = Console()

class SpecificIssueTester:
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        
    def log_issue(self, issue_id, component, severity, description, fix_suggestion=None, error=None):
        """Log a specific issue with fix suggestions."""
        issue = {
            'id': issue_id,
            'component': component,
            'severity': severity,
            'description': description,
            'fix_suggestion': fix_suggestion,
            'error': str(error) if error else None,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.issues_found.append(issue)
    
    def test_csv_applicator_function(self):
        """Test the specific CSV applicator function issue."""
        console.print("[bold blue]🔍 Testing CSV Applicator Function Issue[/bold blue]")
        
        try:
            import src.ats.csv_applicator
            
            # Check for the expected function name
            if hasattr(csv_applicator, 'apply_from_csv'):
                console.print("[green]✅ apply_from_csv function found[/green]")
                return True
            else:
                # Check what functions actually exist
                functions = [attr for attr in dir(csv_applicator) if callable(getattr(csv_applicator, attr)) and not attr.startswith('_')]
                console.print(f"[yellow]⚠️ apply_from_csv not found. Available functions: {functions}[/yellow]")
                
                # Check if main function exists (which is the actual entry point)
                if hasattr(csv_applicator, 'main'):
                    console.print("[cyan]ℹ️ Found 'main' function instead[/cyan]")
                    self.log_issue(
                        'CSV-001',
                        'csv_applicator',
                        'MEDIUM',
                        'apply_from_csv function not found, but main function exists',
                        'The CSV applicator uses a main() function and CSVJobApplicator class. The expected apply_from_csv function should be created as a wrapper.'
                    )
                    return False
                
                # Check if CSVJobApplicator class exists
                if hasattr(csv_applicator, 'CSVJobApplicator'):
                    console.print("[cyan]ℹ️ Found CSVJobApplicator class[/cyan]")
                    self.log_issue(
                        'CSV-002',
                        'csv_applicator',
                        'MEDIUM',
                        'apply_from_csv function missing, but CSVJobApplicator class exists',
                        'Create an apply_from_csv wrapper function that uses CSVJobApplicator class'
                    )
                    return False
                
                self.log_issue(
                    'CSV-003',
                    'csv_applicator',
                    'HIGH',
                    'No expected functions or classes found in csv_applicator',
                    'Review csv_applicator.py structure and ensure proper function exports'
                )
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Error testing CSV applicator: {e}[/red]")
            self.log_issue(
                'CSV-004',
                'csv_applicator',
                'HIGH',
                'Failed to import or test csv_applicator module',
                'Check csv_applicator.py for syntax errors and import issues',
                e
            )
            return False
    
    def test_ats_modules_detailed(self):
        """Test ATS modules with detailed analysis."""
        console.print("[bold blue]🔍 Testing ATS Modules in Detail[/bold blue]")
        
        # Check what files actually exist
        ats_dir = Path('ats')
        if not ats_dir.exists():
            console.print("[red]❌ ATS directory not found[/red]")
            self.log_issue(
                'ATS-001',
                'ats_directory',
                'CRITICAL',
                'ATS directory does not exist',
                'Create ats/ directory with proper ATS modules'
            )
            return False
        
        # List actual files
        actual_files = list(ats_dir.glob('*.py'))
        console.print(f"[cyan]Found ATS files: {[f.name for f in actual_files]}[/cyan]")
        
        # Test base_submitter class name issue
        try:
            from src.ats.base_submitter import BaseSubmitter
            console.print("[green]✅ BaseSubmitter class found (correct name)[/green]")
        except ImportError as e:
            console.print(f"[red]❌ BaseSubmitter import failed: {e}[/red]")
            self.log_issue(
                'ATS-002',
                'base_submitter',
                'MEDIUM',
                'BaseSubmitter class import failed',
                'Check ats/base_submitter.py for correct class name and exports',
                e
            )
        
        # Test individual ATS modules
        ats_modules = [
            ('workday', 'ats.workday', 'WorkdaySubmitter'),
            ('icims', 'ats.icims', 'ICIMSSubmitter'),
            ('greenhouse', 'ats.greenhouse', 'GreenhouseSubmitter'),
            ('bamboohr', 'ats.bamboohr', 'BambooHRSubmitter'),
        ]
        
        working_modules = 0
        for module_name, module_path, class_name in ats_modules:
            try:
                module = __import__(module_path, fromlist=[class_name])
                ats_class = getattr(module, class_name)
                console.print(f"[green]✅ {module_name}: {class_name} found[/green]")
                working_modules += 1
            except ImportError as e:
                console.print(f"[yellow]⚠️ {module_name}: Module not found[/yellow]")
                self.log_issue(
                    f'ATS-{module_name.upper()}-001',
                    module_name,
                    'MEDIUM',
                    f'{module_path} module not found',
                    f'The file exists as ats/{module_name}.py but may have import issues or wrong class name',
                    e
                )
            except AttributeError as e:
                console.print(f"[yellow]⚠️ {module_name}: Class {class_name} not found[/yellow]")
                self.log_issue(
                    f'ATS-{module_name.upper()}-002',
                    module_name,
                    'MEDIUM',
                    f'{class_name} class not found in {module_path}',
                    f'Check ats/{module_name}.py for correct class name. Expected: {class_name}',
                    e
                )
        
        return working_modules > 0
    
    def test_base_scraper_abstract_issue(self):
        """Test the BaseJobScraper abstract class issue."""
        console.print("[bold blue]🔍 Testing BaseJobScraper Abstract Class Issue[/bold blue]")
        
        try:
            from src.scrapers.base_scraper import BaseJobScraper
            
            # This should fail because it's abstract
            try:
                test_profile = {'profile_name': 'test', 'keywords': ['Python'], 'city': 'Toronto'}
                scraper = BaseJobScraper(test_profile)
                console.print("[red]❌ BaseJobScraper should not be instantiable (it's abstract)[/red]")
                self.log_issue(
                    'SCRAPER-001',
                    'base_scraper',
                    'LOW',
                    'BaseJobScraper can be instantiated but should be abstract',
                    'This is actually correct behavior - abstract classes should not be instantiable'
                )
                return False
            except TypeError as e:
                if "abstract" in str(e).lower():
                    console.print("[green]✅ BaseJobScraper correctly prevents instantiation (abstract class)[/green]")
                    console.print("[cyan]ℹ️ This is expected behavior for an abstract base class[/cyan]")
                    return True
                else:
                    console.print(f"[yellow]⚠️ BaseJobScraper failed instantiation for different reason: {e}[/yellow]")
                    return False
                    
        except Exception as e:
            console.print(f"[red]❌ Error testing BaseJobScraper: {e}[/red]")
            self.log_issue(
                'SCRAPER-002',
                'base_scraper',
                'MEDIUM',
                'Failed to import BaseJobScraper',
                'Check scrapers/base_scraper.py for import issues',
                e
            )
            return False
    
    def test_database_table_issue(self):
        """Test the database table creation issue."""
        console.print("[bold blue]🔍 Testing Database Table Creation Issue[/bold blue]")
        
        try:
            from src.core.job_database import JobDatabase
            
            # Test with in-memory database
            db = JobDatabase(":memory:")
            
            # Check if tables are created automatically
            try:
                # Try to get stats (this should trigger table creation if not exists)
                stats = db.get_stats()
                console.print(f"[green]✅ Database stats retrieved: {stats}[/green]")
                return True
            except Exception as e:
                if "no such table" in str(e).lower():
                    console.print(f"[red]❌ Database tables not created automatically: {e}[/red]")
                    self.log_issue(
                        'DB-001',
                        'job_database',
                        'HIGH',
                        'Database tables not created automatically on initialization',
                        'Add table creation in JobDatabase.__init__() or create_tables() method'
                    )
                    
                    # Check if there's a create_tables method
                    if hasattr(db, 'create_tables'):
                        console.print("[cyan]ℹ️ Found create_tables method, testing...[/cyan]")
                        try:
                            db.create_tables()
                            stats = db.get_stats()
                            console.print(f"[green]✅ Tables created manually, stats: {stats}[/green]")
                            self.log_issue(
                                'DB-002',
                                'job_database',
                                'MEDIUM',
                                'Tables need to be created manually',
                                'Call create_tables() automatically in __init__ or ensure it\'s called before first use'
                            )
                            return True
                        except Exception as e2:
                            console.print(f"[red]❌ Manual table creation failed: {e2}[/red]")
                            return False
                    else:
                        console.print("[yellow]⚠️ No create_tables method found[/yellow]")
                        return False
                else:
                    console.print(f"[red]❌ Database error: {e}[/red]")
                    return False
                    
        except Exception as e:
            console.print(f"[red]❌ Error testing database: {e}[/red]")
            self.log_issue(
                'DB-003',
                'job_database',
                'HIGH',
                'Failed to import or initialize JobDatabase',
                'Check job_database.py for import and initialization issues',
                e
            )
            return False
    
    def run_specific_tests(self):
        """Run all specific issue tests."""
        console.print(Panel("🔍 Specific Issue Analysis", style="bold blue"))
        
        tests = [
            ("CSV Applicator Function", self.test_csv_applicator_function),
            ("ATS Modules Detailed", self.test_ats_modules_detailed),
            ("BaseJobScraper Abstract", self.test_base_scraper_abstract_issue),
            ("Database Table Creation", self.test_database_table_issue),
        ]
        
        results = []
        for test_name, test_func in tests:
            console.print(f"\n[bold cyan]Running: {test_name}[/bold cyan]")
            start_time = time.time()
            
            try:
                success = test_func()
                duration = time.time() - start_time
                results.append((test_name, success, duration))
            except Exception as e:
                console.print(f"[red]❌ Test {test_name} crashed: {e}[/red]")
                results.append((test_name, False, time.time() - start_time))
        
        # Display results
        self.display_results(results)
        
        # Generate enhanced issues tracker
        self.generate_enhanced_issues_tracker()
        
        return all(result[1] for result in results)
    
    def display_results(self, results):
        """Display test results."""
        console.print("\n")
        table = Table(title="🔍 Specific Issue Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Duration", style="yellow")
        
        for test_name, success, duration in results:
            status = "[green]✅ PASS[/green]" if success else "[red]❌ FAIL[/red]"
            table.add_row(test_name, status, f"{duration:.2f}s")
        
        console.print(table)
        
        passed = sum(1 for _, success, _ in results if success)
        total = len(results)
        console.print(f"\n[bold]Results: {passed}/{total} tests passed[/bold]")
        console.print(f"[bold]Detailed Issues Found: {len(self.issues_found)}[/bold]")
    
    def generate_enhanced_issues_tracker(self):
        """Generate enhanced issues tracker with fix suggestions."""
        console.print("\n[bold blue]📝 Generating Enhanced Issues Tracker...[/bold blue]")
        
        content = self._generate_enhanced_markdown()
        
        with open('ENHANCED_ISSUES_TRACKER.md', 'w', encoding='utf-8') as f:
            f.write(content)
        
        console.print(f"[green]✅ Enhanced issues tracker generated: ENHANCED_ISSUES_TRACKER.md[/green]")
    
    def _generate_enhanced_markdown(self):
        """Generate enhanced markdown with detailed analysis and fixes."""
        content = """# 🔧 AutoJobAgent Enhanced Issues Tracker

*Generated by specific issue analysis with detailed fix suggestions*

## 📊 Executive Summary

"""
        
        content += f"**Total Detailed Issues: {len(self.issues_found)}**\n\n"
        
        # Group by severity
        by_severity = {}
        for issue in self.issues_found:
            severity = issue['severity']
            by_severity.setdefault(severity, []).append(issue)
        
        for severity, issues in by_severity.items():
            content += f"- **{severity}**: {len(issues)} issues\n"
        
        content += "\n---\n\n"
        
        # Add detailed issues
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            issues = by_severity.get(severity, [])
            if not issues:
                continue
                
            content += f"## 🚨 {severity} Priority Issues\n\n"
            
            for issue in issues:
                content += f"### {issue['id']}: {issue['component']}\n\n"
                content += f"**Description:** {issue['description']}\n\n"
                
                if issue['fix_suggestion']:
                    content += f"**💡 Fix Suggestion:**\n{issue['fix_suggestion']}\n\n"
                
                if issue['error']:
                    content += f"**Error Details:**\n```\n{issue['error']}\n```\n\n"
                
                content += f"**Timestamp:** {issue['timestamp']}\n\n"
                content += "**Status:** 🔴 Open\n\n"
                content += "---\n\n"
        
        return content


def main():
    """Main function."""
    tester = SpecificIssueTester()
    success = tester.run_specific_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
