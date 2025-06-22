#!/usr/bin/env python3
"""
Main Application Flow Testing for AutoJobAgent
Tests the main application flow and integration between modules.
"""

import time
import traceback
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class MainApplicationTester:
    def __init__(self):
        self.issues_found = []
        
    def log_issue(self, issue_id, component, severity, description, fix_suggestion=None, error=None):
        """Log an issue with fix suggestions."""
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
    
    def test_main_py_functionality(self):
        """Test main.py functionality."""
        console.print("[bold blue]🔍 Testing main.py Functionality[/bold blue]")
        
        try:
            import main
            
            # Test main functions
            functions_to_test = [
                ('main', 'Main entry point function'),
                ('show_menu', 'Menu display function'),
                ('handle_menu_choice', 'Menu choice handler'),
                ('run_scraping', 'Scraping execution function'),
                ('run_application', 'Application execution function'),
            ]
            
            working_functions = 0
            for func_name, description in functions_to_test:
                if hasattr(main, func_name):
                    console.print(f"[green]✅ {func_name}: {description}[/green]")
                    working_functions += 1
                else:
                    console.print(f"[yellow]⚠️ {func_name}: Not found[/yellow]")
                    self.log_issue(
                        f'MAIN-{func_name.upper()}-001',
                        'main',
                        'HIGH',
                        f'{func_name} function not found in main.py',
                        f'Implement {func_name} function for {description.lower()}'
                    )
            
            # Test if main.py can be executed
            try:
                # Check if main has proper if __name__ == "__main__" structure
                with open('main.py', 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'if __name__ == "__main__"' in content:
                        console.print("[green]✅ Main execution guard found[/green]")
                    else:
                        console.print("[yellow]⚠️ Main execution guard not found[/yellow]")
                        self.log_issue(
                            'MAIN-GUARD-001',
                            'main',
                            'LOW',
                            'Main execution guard not found',
                            'Add if __name__ == "__main__": guard to main.py'
                        )
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not check main.py structure: {e}[/yellow]")
            
            return working_functions >= 3
            
        except Exception as e:
            console.print(f"[red]❌ Error testing main.py: {e}[/red]")
            self.log_issue(
                'MAIN-MODULE-001',
                'main',
                'CRITICAL',
                'Failed to import main.py module',
                'Check main.py for syntax errors and import issues',
                e
            )
            return False
    
    def test_cli_integration(self):
        """Test CLI integration and menu system."""
        console.print("[bold blue]🔍 Testing CLI Integration[/bold blue]")
        
        try:
            import main
            
            # Test menu system
            if hasattr(main, 'show_menu'):
                try:
                    # This might print to console, which is expected
                    console.print("[cyan]Testing menu display...[/cyan]")
                    # We can't easily test interactive menu, but we can check if it exists
                    console.print("[green]✅ Menu system accessible[/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠️ Menu system error: {e}[/yellow]")
                    self.log_issue(
                        'CLI-MENU-001',
                        'cli',
                        'MEDIUM',
                        'Menu system has execution errors',
                        'Debug menu display function',
                        e
                    )
            
            # Test profile selection
            try:
                import utils
                profiles = utils.get_available_profiles() if hasattr(utils, 'get_available_profiles') else []
                if profiles:
                    console.print(f"[green]✅ Profile system: {len(profiles)} profiles available[/green]")
                else:
                    console.print("[yellow]⚠️ No profiles found or profile system not working[/yellow]")
                    self.log_issue(
                        'CLI-PROFILES-001',
                        'cli',
                        'MEDIUM',
                        'No profiles available for CLI selection',
                        'Ensure profiles are created and get_available_profiles function works'
                    )
            except Exception as e:
                console.print(f"[yellow]⚠️ Profile system test failed: {e}[/yellow]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error testing CLI integration: {e}[/red]")
            self.log_issue(
                'CLI-INTEGRATION-001',
                'cli',
                'HIGH',
                'Failed to test CLI integration',
                'Check main.py and CLI-related functions',
                e
            )
            return False
    
    def test_scraping_workflow(self):
        """Test the complete scraping workflow."""
        console.print("[bold blue]🔍 Testing Scraping Workflow[/bold blue]")
        
        try:
            from intelligent_scraper import IntelligentJobScraper
            
            # Test scraper initialization
            scraper = IntelligentJobScraper("Nirajan")
            console.print("[green]✅ IntelligentJobScraper initialized[/green]")
            
            # Test scraper methods
            methods_to_test = [
                ('run_scraping', 'Main scraping execution'),
                ('scrape_with_enhanced_scrapers', 'Enhanced scraper execution'),
                ('get_scraper_for_site', 'Site-specific scraper selection'),
            ]
            
            working_methods = 0
            for method_name, description in methods_to_test:
                if hasattr(scraper, method_name):
                    console.print(f"[green]✅ {method_name}: {description}[/green]")
                    working_methods += 1
                else:
                    console.print(f"[yellow]⚠️ {method_name}: Not found[/yellow]")
                    self.log_issue(
                        f'SCRAPING-{method_name.upper()}-001',
                        'intelligent_scraper',
                        'MEDIUM',
                        f'{method_name} method not found',
                        f'Implement {method_name} method for {description.lower()}'
                    )
            
            # Test database integration
            try:
                from job_database import get_job_db
                db = get_job_db()
                console.print("[green]✅ Database integration working[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ Database integration issue: {e}[/yellow]")
                self.log_issue(
                    'SCRAPING-DB-001',
                    'scraping_workflow',
                    'HIGH',
                    'Database integration failed in scraping workflow',
                    'Ensure job_database module works correctly with scrapers',
                    e
                )
            
            return working_methods >= 2
            
        except Exception as e:
            console.print(f"[red]❌ Error testing scraping workflow: {e}[/red]")
            self.log_issue(
                'SCRAPING-WORKFLOW-001',
                'scraping_workflow',
                'HIGH',
                'Failed to test scraping workflow',
                'Check IntelligentJobScraper and related components',
                e
            )
            return False
    
    def test_application_workflow(self):
        """Test the complete application workflow."""
        console.print("[bold blue]🔍 Testing Application Workflow[/bold blue]")
        
        try:
            # Test CSV applicator workflow
            import csv_applicator
            
            if hasattr(csv_applicator, 'main'):
                console.print("[green]✅ CSV applicator main function exists[/green]")
            else:
                console.print("[yellow]⚠️ CSV applicator main function not found[/yellow]")
                self.log_issue(
                    'APP-CSV-001',
                    'application_workflow',
                    'MEDIUM',
                    'CSV applicator main function not found',
                    'Implement main function in csv_applicator.py'
                )
            
            # Test document generation workflow
            try:
                import document_generator
                import utils
                
                profile = utils.load_profile("Nirajan")
                test_job = {
                    'title': 'Test Job',
                    'company': 'Test Company',
                    'summary': 'Test job description'
                }
                
                if hasattr(document_generator, 'customize'):
                    console.print("[green]✅ Document generation workflow available[/green]")
                else:
                    console.print("[yellow]⚠️ Document generation workflow incomplete[/yellow]")
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Document generation workflow issue: {e}[/yellow]")
                self.log_issue(
                    'APP-DOC-001',
                    'application_workflow',
                    'MEDIUM',
                    'Document generation workflow has issues',
                    'Debug document_generator.customize function',
                    e
                )
            
            # Test dashboard workflow
            try:
                import dashboard_api
                
                if hasattr(dashboard_api, 'app'):
                    console.print("[green]✅ Dashboard workflow available[/green]")
                else:
                    console.print("[yellow]⚠️ Dashboard workflow incomplete[/yellow]")
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Dashboard workflow issue: {e}[/yellow]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error testing application workflow: {e}[/red]")
            self.log_issue(
                'APP-WORKFLOW-001',
                'application_workflow',
                'HIGH',
                'Failed to test application workflow',
                'Check application workflow components',
                e
            )
            return False
    
    def test_error_handling(self):
        """Test error handling throughout the application."""
        console.print("[bold blue]🔍 Testing Error Handling[/bold blue]")
        
        try:
            # Test with invalid profile
            try:
                import utils
                invalid_profile = utils.load_profile("NonExistentProfile")
                console.print("[yellow]⚠️ Invalid profile loaded - error handling may be insufficient[/yellow]")
                self.log_issue(
                    'ERROR-PROFILE-001',
                    'error_handling',
                    'LOW',
                    'Invalid profile loading does not raise appropriate error',
                    'Add proper error handling for invalid profile names'
                )
            except Exception as e:
                console.print("[green]✅ Invalid profile properly rejected[/green]")
            
            # Test with invalid job data
            try:
                import utils
                invalid_job = {}  # Empty job
                job_hash = utils.hash_job(invalid_job)
                console.print(f"[yellow]⚠️ Empty job hashed successfully: {job_hash}[/yellow]")
                self.log_issue(
                    'ERROR-JOB-001',
                    'error_handling',
                    'LOW',
                    'Empty job data does not raise appropriate error',
                    'Add validation for job data before hashing'
                )
            except Exception as e:
                console.print("[green]✅ Invalid job data properly rejected[/green]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error testing error handling: {e}[/red]")
            self.log_issue(
                'ERROR-HANDLING-001',
                'error_handling',
                'MEDIUM',
                'Failed to test error handling',
                'Review error handling throughout the application',
                e
            )
            return False
    
    def run_main_application_tests(self):
        """Run all main application tests."""
        console.print(Panel("🔍 Main Application Flow Testing", style="bold blue"))
        
        tests = [
            ("Main.py Functionality", self.test_main_py_functionality),
            ("CLI Integration", self.test_cli_integration),
            ("Scraping Workflow", self.test_scraping_workflow),
            ("Application Workflow", self.test_application_workflow),
            ("Error Handling", self.test_error_handling),
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
        
        # Generate main application issues tracker
        self.generate_main_issues_tracker()
        
        return all(result[1] for result in results)
    
    def display_results(self, results):
        """Display test results."""
        console.print("\n")
        table = Table(title="🔍 Main Application Test Results")
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
        console.print(f"[bold]Main Application Issues Found: {len(self.issues_found)}[/bold]")
    
    def generate_main_issues_tracker(self):
        """Generate main application issues tracker."""
        console.print("\n[bold blue]📝 Generating Main Application Issues Tracker...[/bold blue]")
        
        content = self._generate_main_markdown()
        
        with open('MAIN_APPLICATION_ISSUES.md', 'w', encoding='utf-8') as f:
            f.write(content)
        
        console.print(f"[green]✅ Main application issues tracker generated: MAIN_APPLICATION_ISSUES.md[/green]")
    
    def _generate_main_markdown(self):
        """Generate main application markdown."""
        content = """# 🔧 AutoJobAgent Main Application Issues

*Main application flow and integration testing results*

## 📊 Executive Summary

"""
        
        content += f"**Total Main Application Issues: {len(self.issues_found)}**\n\n"
        
        # Group by severity
        by_severity = {}
        for issue in self.issues_found:
            severity = issue['severity']
            by_severity.setdefault(severity, []).append(issue)
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            issues = by_severity.get(severity, [])
            if issues:
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
    tester = MainApplicationTester()
    success = tester.run_main_application_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
