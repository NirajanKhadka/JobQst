#!/usr/bin/env python3
"""
Additional Module Testing for AutoJobAgent
Tests additional modules and functions that might have issues.
"""

import time
import traceback
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class AdditionalModuleTester:
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
    
    def test_resume_modifier_functions(self):
        """Test resume modification and document generation functions."""
        console.print("[bold blue]🔍 Testing Resume Modifier Functions[/bold blue]")
        
        try:
            import document_generator
            
            # Test main functions
            functions_to_test = [
                ('customize', 'Main document customization function'),
                ('tailor_resume', 'Resume tailoring function'),
                ('tailor_cover_letter', 'Cover letter tailoring function'),
                ('extract_keywords_with_ai', 'AI keyword extraction function'),
            ]
            
            working_functions = 0
            for func_name, description in functions_to_test:
                if hasattr(document_generator, func_name):
                    console.print(f"[green]✅ {func_name}: {description}[/green]")
                    working_functions += 1
                else:
                    console.print(f"[yellow]⚠️ {func_name}: Not found[/yellow]")
                    self.log_issue(
                        f'DOC-{func_name.upper()}-001',
                        'document_generator',
                        'MEDIUM',
                        f'{func_name} function not found',
                        f'Implement {func_name} function for {description.lower()}'
                    )
            
            # Test with sample data
            try:
                import utils
                profile = utils.load_profile("Nirajan")
                test_job = {
                    'title': 'Python Developer',
                    'company': 'Test Company',
                    'summary': 'Python development role requiring Django and Flask experience'
                }
                
                # Test customize function if it exists
                if hasattr(document_generator, 'customize'):
                    try:
                        resume_path, cover_letter_path = document_generator.customize(test_job, profile)
                        console.print(f"[green]✅ Document customization successful[/green]")
                        console.print(f"[cyan]  Resume: {resume_path}[/cyan]")
                        console.print(f"[cyan]  Cover Letter: {cover_letter_path}[/cyan]")
                    except Exception as e:
                        console.print(f"[yellow]⚠️ Document customization failed: {e}[/yellow]")
                        self.log_issue(
                            'DOC-CUSTOMIZE-002',
                            'document_generator',
                            'HIGH',
                            'Document customization function exists but fails to execute',
                            'Debug the customize function implementation and dependencies',
                            e
                        )
                
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not test with sample data: {e}[/yellow]")
            
            return working_functions > 0
            
        except Exception as e:
            console.print(f"[red]❌ Error testing document generator: {e}[/red]")
            self.log_issue(
                'DOC-MODULE-001',
                'document_generator',
                'HIGH',
                'Failed to import document_generator module',
                'Check document_generator.py for syntax errors and import issues',
                e
            )
            return False
    
    def test_scraper_functionality(self):
        """Test scraper functionality in detail."""
        console.print("[bold blue]🔍 Testing Scraper Functionality[/bold blue]")
        
        try:
            from scrapers.eluta_enhanced import ElutaEnhancedScraper
            import utils
            
            # Test scraper initialization and basic methods
            profile = utils.load_profile("Nirajan")
            test_profile = profile.copy()
            test_profile["keywords"] = ["Python"]  # Single keyword for testing
            
            scraper = ElutaEnhancedScraper(test_profile)
            
            # Test key methods exist
            methods_to_test = [
                ('scrape_jobs', 'Main scraping method'),
                ('_search_keyword', 'Keyword search method'),
                ('_scrape_page', 'Page scraping method'),
                ('_extract_job_from_element', 'Job extraction method'),
                ('_is_job_recent', 'Date filtering method'),
            ]
            
            working_methods = 0
            for method_name, description in methods_to_test:
                if hasattr(scraper, method_name):
                    console.print(f"[green]✅ {method_name}: {description}[/green]")
                    working_methods += 1
                else:
                    console.print(f"[yellow]⚠️ {method_name}: Not found[/yellow]")
                    self.log_issue(
                        f'SCRAPER-{method_name.upper()}-001',
                        'eluta_enhanced',
                        'MEDIUM',
                        f'{method_name} method not found in ElutaEnhancedScraper',
                        f'Implement {method_name} method for {description.lower()}'
                    )
            
            # Test scraper configuration
            if hasattr(scraper, 'max_age_days'):
                console.print(f"[green]✅ Date filtering configured: {scraper.max_age_days} days[/green]")
            else:
                console.print("[yellow]⚠️ Date filtering not configured[/yellow]")
                self.log_issue(
                    'SCRAPER-CONFIG-001',
                    'eluta_enhanced',
                    'LOW',
                    'Date filtering configuration not found',
                    'Add max_age_days configuration to scraper'
                )
            
            return working_methods >= 3  # At least 3 key methods should exist
            
        except Exception as e:
            console.print(f"[red]❌ Error testing scraper functionality: {e}[/red]")
            self.log_issue(
                'SCRAPER-FUNC-001',
                'scraper_functionality',
                'HIGH',
                'Failed to test scraper functionality',
                'Check ElutaEnhancedScraper implementation and dependencies',
                e
            )
            return False
    
    def test_utility_functions_detailed(self):
        """Test utility functions in detail."""
        console.print("[bold blue]🔍 Testing Utility Functions in Detail[/bold blue]")
        
        try:
            import utils
            
            # Test critical utility functions
            functions_to_test = [
                ('load_profile', 'Profile loading'),
                ('save_session', 'Session saving'),
                ('load_session', 'Session loading'),
                ('hash_job', 'Job hashing'),
                ('create_browser_context', 'Browser context creation'),
                ('detect_available_browsers', 'Browser detection'),
                ('fill_if_empty', 'Form filling helper'),
                ('smart_attach', 'File attachment helper'),
                ('append_log_row', 'Logging helper'),
                ('save_document_as_pdf', 'PDF conversion'),
            ]
            
            working_functions = 0
            for func_name, description in functions_to_test:
                if hasattr(utils, func_name):
                    console.print(f"[green]✅ {func_name}: {description}[/green]")
                    working_functions += 1
                    
                    # Test specific functions with sample data
                    if func_name == 'hash_job':
                        try:
                            test_job = {'title': 'Test', 'url': 'https://test.com', 'company': 'Test Co'}
                            job_hash = utils.hash_job(test_job)
                            if len(job_hash) >= 8:  # Should be a reasonable hash length
                                console.print(f"[cyan]  ✓ Hash generated: {job_hash[:8]}...[/cyan]")
                            else:
                                console.print(f"[yellow]  ⚠️ Hash too short: {job_hash}[/yellow]")
                        except Exception as e:
                            console.print(f"[yellow]  ⚠️ Hash function failed: {e}[/yellow]")
                    
                    elif func_name == 'detect_available_browsers':
                        try:
                            browsers = utils.detect_available_browsers()
                            console.print(f"[cyan]  ✓ Detected {len(browsers)} browsers[/cyan]")
                        except Exception as e:
                            console.print(f"[yellow]  ⚠️ Browser detection failed: {e}[/yellow]")
                            
                else:
                    console.print(f"[yellow]⚠️ {func_name}: Not found[/yellow]")
                    self.log_issue(
                        f'UTILS-{func_name.upper()}-001',
                        'utils',
                        'MEDIUM',
                        f'{func_name} function not found',
                        f'Implement {func_name} function for {description.lower()}'
                    )
            
            return working_functions >= 7  # At least 7 key functions should exist
            
        except Exception as e:
            console.print(f"[red]❌ Error testing utility functions: {e}[/red]")
            self.log_issue(
                'UTILS-DETAILED-001',
                'utils',
                'HIGH',
                'Failed to test utility functions in detail',
                'Check utils.py for import and function implementation issues',
                e
            )
            return False
    
    def test_dashboard_functionality(self):
        """Test dashboard functionality."""
        console.print("[bold blue]🔍 Testing Dashboard Functionality[/bold blue]")
        
        try:
            import dashboard_api
            
            # Test FastAPI components
            components_to_test = [
                ('app', 'FastAPI application instance'),
                ('ConnectionManager', 'WebSocket connection manager'),
                ('websocket_endpoint', 'WebSocket endpoint function'),
                ('get_application_stats', 'Statistics endpoint'),
                ('pause_automation', 'Pause control endpoint'),
            ]
            
            working_components = 0
            for component_name, description in components_to_test:
                if hasattr(dashboard_api, component_name):
                    console.print(f"[green]✅ {component_name}: {description}[/green]")
                    working_components += 1
                else:
                    console.print(f"[yellow]⚠️ {component_name}: Not found[/yellow]")
                    self.log_issue(
                        f'DASHBOARD-{component_name.upper()}-001',
                        'dashboard_api',
                        'MEDIUM',
                        f'{component_name} not found in dashboard_api',
                        f'Implement {component_name} for {description.lower()}'
                    )
            
            # Test if FastAPI app is properly configured
            if hasattr(dashboard_api, 'app'):
                try:
                    app = dashboard_api.app
                    routes = [route.path for route in app.routes]
                    console.print(f"[cyan]  ✓ Found {len(routes)} routes: {routes[:5]}{'...' if len(routes) > 5 else ''}[/cyan]")
                except Exception as e:
                    console.print(f"[yellow]  ⚠️ Could not inspect app routes: {e}[/yellow]")
            
            return working_components >= 3  # At least 3 key components should exist
            
        except Exception as e:
            console.print(f"[red]❌ Error testing dashboard functionality: {e}[/red]")
            self.log_issue(
                'DASHBOARD-FUNC-001',
                'dashboard_api',
                'HIGH',
                'Failed to test dashboard functionality',
                'Check dashboard_api.py for FastAPI implementation issues',
                e
            )
            return False
    
    def test_profile_system_detailed(self):
        """Test profile system in detail."""
        console.print("[bold blue]🔍 Testing Profile System in Detail[/bold blue]")
        
        try:
            import utils
            
            # Test profile loading
            profile = utils.load_profile("Nirajan")
            
            # Check required profile fields
            required_fields = [
                'name', 'email', 'profile_name', 'keywords', 'city',
                'profile_dir', 'location', 'phone'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field in profile:
                    console.print(f"[green]✅ {field}: {profile[field]}[/green]")
                else:
                    console.print(f"[yellow]⚠️ {field}: Missing[/yellow]")
                    missing_fields.append(field)
            
            if missing_fields:
                self.log_issue(
                    'PROFILE-FIELDS-001',
                    'profile_system',
                    'MEDIUM',
                    f'Missing profile fields: {missing_fields}',
                    f'Add missing fields to profile: {", ".join(missing_fields)}'
                )
            
            # Check profile directory structure
            profile_dir = Path(profile.get('profile_dir', f'profiles/{profile["profile_name"]}'))
            required_files = [
                f"{profile['profile_name']}.json",
                f"{profile['profile_name']}_Resume.docx",
                f"{profile['profile_name']}_CoverLetter.docx"
            ]
            
            missing_files = []
            for file_name in required_files:
                file_path = profile_dir / file_name
                if file_path.exists():
                    console.print(f"[green]✅ {file_name}: Exists ({file_path.stat().st_size} bytes)[/green]")
                else:
                    console.print(f"[yellow]⚠️ {file_name}: Missing[/yellow]")
                    missing_files.append(file_name)
            
            if missing_files:
                self.log_issue(
                    'PROFILE-FILES-001',
                    'profile_system',
                    'MEDIUM',
                    f'Missing profile files: {missing_files}',
                    f'Create missing profile files: {", ".join(missing_files)}'
                )
            
            return len(missing_fields) == 0 and len(missing_files) == 0
            
        except Exception as e:
            console.print(f"[red]❌ Error testing profile system: {e}[/red]")
            self.log_issue(
                'PROFILE-SYSTEM-001',
                'profile_system',
                'HIGH',
                'Failed to test profile system',
                'Check profile loading and file structure',
                e
            )
            return False
    
    def run_additional_tests(self):
        """Run all additional tests."""
        console.print(Panel("🔍 Additional Module Testing", style="bold blue"))
        
        tests = [
            ("Resume Modifier Functions", self.test_resume_modifier_functions),
            ("Scraper Functionality", self.test_scraper_functionality),
            ("Utility Functions Detailed", self.test_utility_functions_detailed),
            ("Dashboard Functionality", self.test_dashboard_functionality),
            ("Profile System Detailed", self.test_profile_system_detailed),
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
        
        # Generate final issues tracker
        self.generate_final_issues_tracker()
        
        return all(result[1] for result in results)
    
    def display_results(self, results):
        """Display test results."""
        console.print("\n")
        table = Table(title="🔍 Additional Module Test Results")
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
        console.print(f"[bold]Additional Issues Found: {len(self.issues_found)}[/bold]")
    
    def generate_final_issues_tracker(self):
        """Generate final comprehensive issues tracker."""
        console.print("\n[bold blue]📝 Generating Final Issues Tracker...[/bold blue]")
        
        content = self._generate_final_markdown()
        
        with open('FINAL_ISSUES_TRACKER.md', 'w', encoding='utf-8') as f:
            f.write(content)
        
        console.print(f"[green]✅ Final issues tracker generated: FINAL_ISSUES_TRACKER.md[/green]")
    
    def _generate_final_markdown(self):
        """Generate final comprehensive markdown."""
        content = """# 🔧 AutoJobAgent Final Issues Tracker

*Comprehensive analysis of all modules and functions*

## 📊 Executive Summary

"""
        
        content += f"**Total Issues Found: {len(self.issues_found)}**\n\n"
        
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
    tester = AdditionalModuleTester()
    success = tester.run_additional_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
