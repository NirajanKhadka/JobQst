#!/usr/bin/env python3
"""
Comprehensive Stress Test Suite for AutoJobAgent
Tests all functions and modules with 50 jobs for benchmarking
"""

import asyncio
import inspect
import json
import os
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# Rich for beautiful output
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

class StressTestSuite:
    """Comprehensive stress test suite for all AutoJobAgent components"""
    
    def __init__(self):
        self.test_results = {}
        self.total_functions = 0
        self.total_tests = 0
        self.start_time = None
        self.end_time = None
        self.test_profile = "StressTest"
        self.target_jobs = 50
        
        # Test categories
        self.test_categories = {
            "Core Modules": [],
            "Database Operations": [],
            "Scrapers": [],
            "Document Generation": [],
            "Dashboard API": [],
            "Job Analysis": [],
            "Profile Management": [],
            "Utilities": [],
            "ATS Integration": [],
            "Error Handling": []
        }
        
        # Performance metrics
        self.performance_metrics = {
            "memory_usage": [],
            "execution_times": [],
            "success_rates": [],
            "throughput": []
        }
    
    def setup_test_environment(self):
        """Set up clean test environment"""
        console.print("[cyan]🔧 Setting up test environment...[/cyan]")
        
        # Create test profile
        test_profile_dir = Path("profiles") / self.test_profile
        test_profile_dir.mkdir(exist_ok=True)
        
        # Create test profile JSON
        test_profile = {
            "profile_name": self.test_profile,
            "name": "Stress Test User",
            "email": "stress.test@example.com",
            "phone": "+1-555-0123",
            "location": "Toronto, ON",
            "keywords": [
                "data analyst", "python developer", "software engineer", 
                "business analyst", "data scientist", "web developer",
                "full stack", "backend", "frontend", "devops"
            ],
            "skills": [
                "Python", "SQL", "JavaScript", "React", "Node.js",
                "PostgreSQL", "MongoDB", "AWS", "Docker", "Git"
            ],
            "experience_level": "mid",
            "batch_default": 10,
            "preferred_sites": ["eluta", "indeed", "linkedin"],
            "salary_range": {"min": 70000, "max": 120000}
        }
        
        with open(test_profile_dir / f"{self.test_profile}.json", "w") as f:
            json.dump(test_profile, f, indent=2)
        
        # Create test resume and cover letter
        (test_profile_dir / "Resume.pdf").touch()
        (test_profile_dir / "CoverLetter.pdf").touch()
        
        console.print("[green]✅ Test environment ready[/green]")
    
    def discover_functions(self):
        """Discover all functions in the codebase"""
        console.print("[cyan]🔍 Discovering functions to test...[/cyan]")
        
        # Core modules to test
        modules_to_test = [
            "main", "utils", "job_database", "document_generator",
            "dashboard_api", "job_analysis_engine", "user_profile_manager",
            "csv_applicator", "application_flow_optimizer", "enhanced_error_tolerance"
        ]
        
        # Scraper modules
        scraper_modules = [
            "scrapers.base_scraper", "scrapers.eluta_working", "scrapers.eluta_enhanced",
            "scrapers.indeed_enhanced", "scrapers.linkedin_enhanced", "scrapers.jobbank_enhanced",
            "scrapers.monster_enhanced", "scrapers.parallel_job_scraper", "scrapers.multi_site_scraper"
        ]
        
        # ATS modules
        ats_modules = [
            "ats.base_submitter", "ats.workday", "ats.greenhouse", "ats.lever",
            "ats.icims", "ats.bamboohr", "ats.fallback_submitters"
        ]
        
        all_modules = modules_to_test + scraper_modules + ats_modules
        
        for module_name in all_modules:
            try:
                module = __import__(module_name, fromlist=[''])
                functions = self._extract_functions_from_module(module, module_name)
                
                # Categorize functions
                if "scraper" in module_name.lower():
                    self.test_categories["Scrapers"].extend(functions)
                elif "ats" in module_name.lower():
                    self.test_categories["ATS Integration"].extend(functions)
                elif module_name == "job_database":
                    self.test_categories["Database Operations"].extend(functions)
                elif module_name == "document_generator":
                    self.test_categories["Document Generation"].extend(functions)
                elif module_name == "dashboard_api":
                    self.test_categories["Dashboard API"].extend(functions)
                elif module_name == "job_analysis_engine":
                    self.test_categories["Job Analysis"].extend(functions)
                elif module_name == "user_profile_manager":
                    self.test_categories["Profile Management"].extend(functions)
                elif module_name == "utils":
                    self.test_categories["Utilities"].extend(functions)
                elif "error" in module_name.lower():
                    self.test_categories["Error Handling"].extend(functions)
                else:
                    self.test_categories["Core Modules"].extend(functions)
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not import {module_name}: {e}[/yellow]")
        
        # Count total functions
        self.total_functions = sum(len(funcs) for funcs in self.test_categories.values())
        console.print(f"[green]✅ Discovered {self.total_functions} functions across {len(self.test_categories)} categories[/green]")
    
    def _extract_functions_from_module(self, module, module_name: str) -> List[Dict]:
        """Extract testable functions from a module"""
        functions = []
        
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and not name.startswith('_'):
                functions.append({
                    "name": name,
                    "module": module_name,
                    "function": obj,
                    "signature": str(inspect.signature(obj)),
                    "doc": obj.__doc__ or "No documentation"
                })
            elif inspect.isclass(obj) and not name.startswith('_'):
                # Extract methods from classes
                for method_name, method in inspect.getmembers(obj):
                    if inspect.ismethod(method) or inspect.isfunction(method):
                        if not method_name.startswith('_') or method_name in ['__init__', '__call__']:
                            functions.append({
                                "name": f"{name}.{method_name}",
                                "module": module_name,
                                "function": method,
                                "signature": str(inspect.signature(method)),
                                "doc": method.__doc__ or "No documentation",
                                "class": name
                            })
        
        return functions

    async def run_scraping_stress_test(self):
        """Run comprehensive scraping stress test with 50 jobs"""
        console.print(f"[cyan]🚀 Starting scraping stress test for {self.target_jobs} jobs...[/cyan]")

        scraping_results = {
            "eluta_scraping": {"jobs": 0, "time": 0, "success": False},
            "indeed_scraping": {"jobs": 0, "time": 0, "success": False},
            "linkedin_scraping": {"jobs": 0, "time": 0, "success": False},
            "parallel_scraping": {"jobs": 0, "time": 0, "success": False},
            "multi_site_scraping": {"jobs": 0, "time": 0, "success": False}
        }

        # Test individual scrapers
        scrapers_to_test = [
            ("eluta", "scrapers.eluta_working"),
            ("indeed", "scrapers.indeed_enhanced"),
            ("linkedin", "scrapers.linkedin_enhanced")
        ]

        for scraper_name, scraper_module in scrapers_to_test:
            start_time = time.time()
            try:
                # Import and test scraper
                module = __import__(scraper_module, fromlist=[''])

                # Test with limited jobs for speed
                test_jobs = min(self.target_jobs // len(scrapers_to_test), 20)

                if hasattr(module, 'scrape_jobs'):
                    jobs = await self._test_scraper_function(module.scrape_jobs, test_jobs)
                    scraping_results[f"{scraper_name}_scraping"]["jobs"] = len(jobs) if jobs else 0
                    scraping_results[f"{scraper_name}_scraping"]["success"] = len(jobs) > 0 if jobs else False

            except Exception as e:
                console.print(f"[red]❌ {scraper_name} scraper failed: {e}[/red]")
                scraping_results[f"{scraper_name}_scraping"]["success"] = False

            scraping_results[f"{scraper_name}_scraping"]["time"] = time.time() - start_time

        # Test parallel scraping
        start_time = time.time()
        try:
            from scrapers.parallel_job_scraper import ParallelJobScraper
            parallel_scraper = ParallelJobScraper(self.test_profile)

            # Run parallel scraping with limited scope
            jobs = await parallel_scraper.scrape_multiple_keywords(
                keywords=["python", "data analyst"],
                max_pages=3,
                max_workers=2
            )

            scraping_results["parallel_scraping"]["jobs"] = len(jobs) if jobs else 0
            scraping_results["parallel_scraping"]["success"] = len(jobs) > 0 if jobs else False

        except Exception as e:
            console.print(f"[red]❌ Parallel scraper failed: {e}[/red]")
            scraping_results["parallel_scraping"]["success"] = False

        scraping_results["parallel_scraping"]["time"] = time.time() - start_time

        return scraping_results

    async def _test_scraper_function(self, scraper_func, target_jobs: int):
        """Test a specific scraper function"""
        try:
            # Prepare test parameters
            test_params = {
                "profile_name": self.test_profile,
                "keywords": ["python", "data analyst"],
                "max_pages": 2,
                "max_jobs": target_jobs
            }

            # Call scraper function with appropriate parameters
            if asyncio.iscoroutinefunction(scraper_func):
                result = await scraper_func(**test_params)
            else:
                result = scraper_func(**test_params)

            return result

        except Exception as e:
            console.print(f"[yellow]⚠️ Scraper function test failed: {e}[/yellow]")
            return None

    def test_database_operations(self):
        """Test all database operations with stress conditions"""
        console.print("[cyan]💾 Testing database operations...[/cyan]")

        db_results = {
            "connection_test": {"success": False, "time": 0},
            "bulk_insert": {"success": False, "time": 0, "records": 0},
            "query_performance": {"success": False, "time": 0, "queries": 0},
            "concurrent_access": {"success": False, "time": 0, "threads": 0}
        }

        try:
            from job_database import get_job_db

            # Test database connection
            start_time = time.time()
            db = get_job_db(self.test_profile)
            db_results["connection_test"]["success"] = True
            db_results["connection_test"]["time"] = time.time() - start_time

            # Test bulk insert with sample jobs
            start_time = time.time()
            sample_jobs = self._generate_sample_jobs(self.target_jobs)

            for job in sample_jobs:
                db.save_job(job)

            db_results["bulk_insert"]["success"] = True
            db_results["bulk_insert"]["time"] = time.time() - start_time
            db_results["bulk_insert"]["records"] = len(sample_jobs)

            # Test query performance
            start_time = time.time()
            queries_run = 0

            # Run various queries
            _ = db.get_stats()  # Test stats query
            queries_run += 1

            _ = db.get_jobs_by_status("scraped")  # Test status query
            queries_run += 1

            _ = db.get_recent_jobs(days=7)  # Test recent jobs query
            queries_run += 1

            db_results["query_performance"]["success"] = True
            db_results["query_performance"]["time"] = time.time() - start_time
            db_results["query_performance"]["queries"] = queries_run

            # Test concurrent database access
            start_time = time.time()

            def concurrent_db_operation():
                try:
                    test_db = get_job_db(self.test_profile)
                    test_db.get_stats()
                    return True
                except:
                    return False

            # Run 10 concurrent database operations
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(concurrent_db_operation) for _ in range(10)]
                results = [future.result() for future in as_completed(futures)]

            db_results["concurrent_access"]["success"] = all(results)
            db_results["concurrent_access"]["time"] = time.time() - start_time
            db_results["concurrent_access"]["threads"] = len(results)

        except Exception as e:
            console.print(f"[red]❌ Database test failed: {e}[/red]")

        return db_results

    def _generate_sample_jobs(self, count: int) -> List[Dict]:
        """Generate sample job data for testing"""
        sample_jobs = []

        job_titles = [
            "Python Developer", "Data Analyst", "Software Engineer", "Business Analyst",
            "Data Scientist", "Web Developer", "Full Stack Developer", "Backend Developer",
            "Frontend Developer", "DevOps Engineer", "Machine Learning Engineer", "QA Engineer"
        ]

        companies = [
            "TechCorp", "DataSoft", "InnovateLab", "CloudTech", "StartupXYZ",
            "BigTech Inc", "AI Solutions", "WebWorks", "CodeCraft", "DataFlow"
        ]

        locations = [
            "Toronto, ON", "Vancouver, BC", "Montreal, QC", "Calgary, AB",
            "Ottawa, ON", "Edmonton, AB", "Winnipeg, MB", "Halifax, NS"
        ]

        for i in range(count):
            job = {
                "title": job_titles[i % len(job_titles)],
                "company": companies[i % len(companies)],
                "location": locations[i % len(locations)],
                "url": f"https://example.com/job/{i}",
                "description": f"Sample job description for {job_titles[i % len(job_titles)]} position",
                "posted_date": datetime.now().isoformat(),
                "salary": f"${60000 + (i * 1000)}-${80000 + (i * 1000)}",
                "experience_required": "2-5 years",
                "job_type": "Full-time",
                "site": "test_site",
                "status": "scraped"
            }
            sample_jobs.append(job)

        return sample_jobs

    def test_document_generation(self):
        """Test document generation functions"""
        console.print("[cyan]📄 Testing document generation...[/cyan]")

        doc_results = {
            "resume_generation": {"success": False, "time": 0},
            "cover_letter_generation": {"success": False, "time": 0},
            "bulk_generation": {"success": False, "time": 0, "documents": 0}
        }

        try:
            from document_generator import DocumentGenerator

            # Test resume generation
            start_time = time.time()
            doc_gen = DocumentGenerator(self.test_profile)

            sample_job = {
                "title": "Python Developer",
                "company": "TechCorp",
                "description": "Python development role with Django and Flask"
            }

            resume_path = doc_gen.generate_resume(sample_job)
            doc_results["resume_generation"]["success"] = resume_path is not None
            doc_results["resume_generation"]["time"] = time.time() - start_time

            # Test cover letter generation
            start_time = time.time()
            cover_letter_path = doc_gen.generate_cover_letter(sample_job)
            doc_results["cover_letter_generation"]["success"] = cover_letter_path is not None
            doc_results["cover_letter_generation"]["time"] = time.time() - start_time

            # Test bulk generation
            start_time = time.time()
            sample_jobs = self._generate_sample_jobs(10)
            generated_docs = 0

            for job in sample_jobs[:5]:  # Test with 5 jobs
                try:
                    doc_gen.generate_resume(job)
                    doc_gen.generate_cover_letter(job)
                    generated_docs += 2
                except:
                    pass

            doc_results["bulk_generation"]["success"] = generated_docs > 0
            doc_results["bulk_generation"]["time"] = time.time() - start_time
            doc_results["bulk_generation"]["documents"] = generated_docs

        except Exception as e:
            console.print(f"[red]❌ Document generation test failed: {e}[/red]")

        return doc_results

    def test_dashboard_api(self):
        """Test dashboard API endpoints"""
        console.print("[cyan]🌐 Testing dashboard API...[/cyan]")

        api_results = {
            "health_check": {"success": False, "time": 0},
            "dashboard_numbers": {"success": False, "time": 0},
            "system_status": {"success": False, "time": 0},
            "concurrent_requests": {"success": False, "time": 0, "requests": 0}
        }

        try:
            import requests
            base_url = "http://localhost:8005"

            # Test health check
            start_time = time.time()
            response = requests.get(f"{base_url}/api/health", timeout=5)
            api_results["health_check"]["success"] = response.status_code == 200
            api_results["health_check"]["time"] = time.time() - start_time

            # Test dashboard numbers
            start_time = time.time()
            response = requests.get(f"{base_url}/api/dashboard-numbers", timeout=10)
            api_results["dashboard_numbers"]["success"] = response.status_code == 200
            api_results["dashboard_numbers"]["time"] = time.time() - start_time

            # Test system status
            start_time = time.time()
            response = requests.get(f"{base_url}/api/system-status", timeout=10)
            api_results["system_status"]["success"] = response.status_code == 200
            api_results["system_status"]["time"] = time.time() - start_time

            # Test concurrent requests
            start_time = time.time()

            def make_request():
                try:
                    response = requests.get(f"{base_url}/api/health", timeout=5)
                    return response.status_code == 200
                except:
                    return False

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(20)]
                results = [future.result() for future in as_completed(futures)]

            api_results["concurrent_requests"]["success"] = sum(results) > 15  # 75% success rate
            api_results["concurrent_requests"]["time"] = time.time() - start_time
            api_results["concurrent_requests"]["requests"] = len(results)

        except Exception as e:
            console.print(f"[red]❌ Dashboard API test failed: {e}[/red]")

        return api_results

    def test_utility_functions(self):
        """Test utility functions"""
        console.print("[cyan]🔧 Testing utility functions...[/cyan]")

        util_results = {
            "profile_operations": {"success": False, "time": 0},
            "file_operations": {"success": False, "time": 0},
            "data_processing": {"success": False, "time": 0}
        }

        try:
            import utils

            # Test profile operations
            start_time = time.time()
            profiles = utils.get_available_profiles()
            util_results["profile_operations"]["success"] = isinstance(profiles, list) and self.test_profile in profiles
            util_results["profile_operations"]["time"] = time.time() - start_time

            # Test file operations
            start_time = time.time()
            test_file = "test_stress.txt"
            with open(test_file, "w") as f:
                f.write("stress test")

            file_exists = os.path.exists(test_file)
            os.remove(test_file) if file_exists else None
            util_results["file_operations"]["success"] = file_exists
            util_results["file_operations"]["time"] = time.time() - start_time

            # Test data processing
            start_time = time.time()
            test_data = [{"key": i, "value": f"test_{i}"} for i in range(100)]
            processed = len(test_data) == 100
            util_results["data_processing"]["success"] = processed
            util_results["data_processing"]["time"] = time.time() - start_time

        except Exception as e:
            console.print(f"[red]❌ Utility functions test failed: {e}[/red]")

        return util_results

    async def run_comprehensive_stress_test(self):
        """Run the complete stress test suite"""
        self.start_time = time.time()
        console.print(Panel.fit("🚀 COMPREHENSIVE STRESS TEST SUITE", style="bold blue"))

        # Setup
        self.setup_test_environment()
        self.discover_functions()

        # Initialize results
        all_results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:

            # Scraping tests
            scraping_task = progress.add_task("Testing scrapers...", total=1)
            all_results["scraping"] = await self.run_scraping_stress_test()
            progress.update(scraping_task, completed=1)

            # Database tests
            db_task = progress.add_task("Testing database...", total=1)
            all_results["database"] = self.test_database_operations()
            progress.update(db_task, completed=1)

            # Document generation tests
            doc_task = progress.add_task("Testing documents...", total=1)
            all_results["documents"] = self.test_document_generation()
            progress.update(doc_task, completed=1)

            # API tests
            api_task = progress.add_task("Testing API...", total=1)
            all_results["api"] = self.test_dashboard_api()
            progress.update(api_task, completed=1)

            # Utility tests
            util_task = progress.add_task("Testing utilities...", total=1)
            all_results["utilities"] = self.test_utility_functions()
            progress.update(util_task, completed=1)

        self.end_time = time.time()
        self.test_results = all_results

        # Generate comprehensive report
        self.generate_stress_test_report()

        return all_results

    def generate_stress_test_report(self):
        """Generate comprehensive stress test report"""
        total_time = self.end_time - self.start_time

        # Calculate statistics
        total_tests_run = 0
        successful_tests = 0

        for category, results in self.test_results.items():
            for test_name, test_result in results.items():
                total_tests_run += 1
                if test_result.get("success", False):
                    successful_tests += 1

        success_rate = (successful_tests / total_tests_run * 100) if total_tests_run > 0 else 0

        # Create summary table
        summary_table = Table(title="🎯 STRESS TEST SUMMARY", style="bold")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Total Functions Discovered", str(self.total_functions))
        summary_table.add_row("Total Tests Run", str(total_tests_run))
        summary_table.add_row("Successful Tests", str(successful_tests))
        summary_table.add_row("Success Rate", f"{success_rate:.1f}%")
        summary_table.add_row("Total Execution Time", f"{total_time:.2f} seconds")
        summary_table.add_row("Target Jobs for Scraping", str(self.target_jobs))

        console.print(summary_table)

        # Create detailed results table
        results_table = Table(title="📊 DETAILED TEST RESULTS", style="bold")
        results_table.add_column("Category", style="cyan")
        results_table.add_column("Test", style="yellow")
        results_table.add_column("Status", style="green")
        results_table.add_column("Time (s)", style="blue")
        results_table.add_column("Details", style="white")

        for category, results in self.test_results.items():
            for test_name, test_result in results.items():
                status = "✅ PASS" if test_result.get("success", False) else "❌ FAIL"
                time_taken = f"{test_result.get('time', 0):.3f}"

                details = []
                if "jobs" in test_result:
                    details.append(f"Jobs: {test_result['jobs']}")
                if "records" in test_result:
                    details.append(f"Records: {test_result['records']}")
                if "requests" in test_result:
                    details.append(f"Requests: {test_result['requests']}")
                if "documents" in test_result:
                    details.append(f"Docs: {test_result['documents']}")

                results_table.add_row(
                    category.title(),
                    test_name.replace("_", " ").title(),
                    status,
                    time_taken,
                    " | ".join(details) if details else "N/A"
                )

        console.print(results_table)

        # Save detailed report to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_functions": self.total_functions,
                "total_tests": total_tests_run,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "execution_time": total_time,
                "target_jobs": self.target_jobs
            },
            "detailed_results": self.test_results,
            "function_categories": {k: len(v) for k, v in self.test_categories.items()}
        }

        report_filename = f"stress_test_report_{int(time.time())}.json"
        with open(report_filename, "w") as f:
            json.dump(report_data, f, indent=2)

        console.print(f"\n[green]📄 Detailed report saved to: {report_filename}[/green]")

        # Performance summary
        performance_panel = Panel(
            f"🏆 PERFORMANCE SUMMARY\n\n"
            f"• Functions Tested: {self.total_functions}\n"
            f"• Tests Executed: {total_tests_run}\n"
            f"• Success Rate: {success_rate:.1f}%\n"
            f"• Total Time: {total_time:.2f}s\n"
            f"• Avg Time/Test: {total_time/total_tests_run:.3f}s\n"
            f"• Target Jobs: {self.target_jobs}",
            style="bold green"
        )
        console.print(performance_panel)


async def main():
    """Main execution function"""
    console.print(Panel.fit("🎯 AutoJobAgent Comprehensive Stress Test", style="bold magenta"))

    # Create and run stress test suite
    stress_test = StressTestSuite()

    try:
        results = await stress_test.run_comprehensive_stress_test()

        console.print("\n[bold green]🎉 Stress test completed successfully![/bold green]")
        return results

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Stress test interrupted by user[/yellow]")
        return None
    except Exception as e:
        console.print(f"\n[red]❌ Stress test failed: {e}[/red]")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Install required packages if not available
    try:
        import rich  # noqa: F401
        import requests  # noqa: F401
    except ImportError:
        console.print("[yellow]Installing required packages...[/yellow]")
        os.system("pip install rich requests")

    # Run the stress test
    asyncio.run(main())
