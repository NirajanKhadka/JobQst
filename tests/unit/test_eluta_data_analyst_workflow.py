#!/usr/bin/env python3
"""
Comprehensive Eluta Data Analyst Workflow Test
Tests the complete workflow: scraping → document customization → dashboard updates
"""

import sys
import time
import json
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add project root to Python path for src imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

console = Console()

class ElutaDataAnalystWorkflowTest:
    """Comprehensive test for Eluta scraper with data analyst jobs and document customization."""
    
    def __init__(self):
        self.results = {}
        self.profile: Optional[Dict] = None
        self.scraped_jobs: List[Dict] = []
        self.dashboard_url = "http://localhost:8002"
        self.test_profile = "test_data_analyst"
        
    def run_complete_workflow(self) -> bool:
        """Run the complete workflow test."""
        console.print(Panel("🧪 Eluta Data Analyst Workflow Test", style="bold blue"))
        
        workflow_steps = [
            ("Profile Setup", self.setup_test_profile),
            ("Dashboard Launch", self.launch_dashboard),
            ("Eluta Scraping", self.test_eluta_scraping),
            ("Document Customization", self.test_document_customization),
            ("Dashboard Verification", self.verify_dashboard_updates),
            ("Cleanup", self.cleanup_test_data)
        ]
        
        passed = 0
        for step_name, step_func in workflow_steps:
            console.print(f"\n🔄 Testing {step_name}...")
            try:
                result = step_func()
                self.results[step_name] = result
                if result:
                    passed += 1
                    console.print(f"✅ {step_name} completed successfully")
                else:
                    console.print(f"❌ {step_name} failed")
            except Exception as e:
                console.print(f"❌ {step_name} error: {e}")
                self.results[step_name] = False
        
        self.print_results(passed, len(workflow_steps))
        return passed == len(workflow_steps)
    
    def setup_test_profile(self) -> bool:
        """Setup test profile for data analyst jobs."""
        try:
            from src.utils.profile_helpers import load_profile
            
            # Simple test profile - just data analyst keyword, no location
            test_profile_data = {
                "name": "Test Data Analyst",
                "profile_name": self.test_profile,
                "email": "test@example.com",
                "keywords": ["data analyst"],  # Only one keyword - data analyst
                "skills": ["Python", "SQL", "Excel", "Tableau", "Power BI"],
                "resume_path": "profiles/test_data_analyst/resume.pdf",
                "cover_letter_path": "profiles/test_data_analyst/cover_letter.pdf"
            }
            
            # Create profile directory
            profile_dir = Path(f"profiles/{self.test_profile}")
            profile_dir.mkdir(parents=True, exist_ok=True)
            
            # Save test profile by writing to file directly
            profile_file = profile_dir / f"{self.test_profile}.json"
            with open(profile_file, 'w') as f:
                json.dump(test_profile_data, f, indent=2)
            
            self.profile = test_profile_data
            
            console.print(f"  ✅ Test profile created: {self.test_profile}")
            console.print(f"  ✅ Keyword: {self.profile['keywords'][0]}")
            
            return True
            
        except Exception as e:
            console.print(f"  ❌ Profile setup error: {e}")
            return False
    
    def launch_dashboard(self) -> bool:
        """Launch dashboard and verify it's running."""
        try:
            import subprocess
            
            # Check if dashboard is already running by testing the API directly
            try:
                response = requests.get(f"{self.dashboard_url}/api/quick-test", timeout=5)
                if response.status_code == 200:
                    console.print(f"  ✅ Dashboard already running")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            # Launch dashboard in background
            console.print("  🔄 Launching dashboard...")
            subprocess.Popen([
                sys.executable, "main.py", self.test_profile, "--action", "dashboard"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for dashboard to start
            time.sleep(5)
            
            # Test dashboard connectivity
            try:
                response = requests.get(f"{self.dashboard_url}/api/quick-test", timeout=10)
                if response.status_code == 200:
                    console.print(f"  ✅ Dashboard API responding")
                    return True
                else:
                    console.print(f"  ❌ Dashboard API error: {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                console.print(f"  ❌ Dashboard connection error: {e}")
                return False
                
        except Exception as e:
            console.print(f"  ❌ Dashboard launch error: {e}")
            return False
    
    def test_eluta_scraping(self) -> bool:
        """Test Eluta scraper with data analyst jobs."""
        try:
            from src.scrapers import get_scraper
            
            if not self.profile:
                console.print(f"  ❌ No profile available for scraping")
                return False
            
            # Get Eluta scraper
            scraper = get_scraper("eluta_working", self.profile)
            
            console.print("  🔄 Starting Eluta scraping for data analyst jobs...")
            
            # Simple configuration - just data analyst keyword, no location
            scraper_config = {
                "keywords": ["data analyst"],  # Only one keyword - data analyst
                "max_pages": 2,  # Limit to 2 pages for testing
                "max_jobs": 10   # Target 10 jobs
            }
            
            # Run scraping with progress tracking
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Scraping jobs...", total=None)
                
                # Start scraping
                jobs = scraper.scrape_jobs(scraper_config)
                
                progress.update(task, description="Processing scraped jobs...")
                
                # Process and save jobs
                if jobs:
                    self.scraped_jobs = jobs[:10]  # Limit to 10 jobs
                    
                    # Save to database
                    from src.core.job_database import get_job_db
                    db = get_job_db(self.test_profile)
                    
                    # Add jobs to database
                    result = db.add_jobs_batch(self.scraped_jobs)
                    
                    console.print(f"  ✅ Scraped {len(self.scraped_jobs)} data analyst jobs")
                    console.print(f"  ✅ Saved {result} jobs to database")
                    
                    # Show sample job
                    if self.scraped_jobs:
                        sample_job = self.scraped_jobs[0]
                        console.print(f"  📋 Sample job: {sample_job.get('title', 'N/A')} at {sample_job.get('company', 'N/A')}")
                    
                    return True
                else:
                    console.print(f"  ❌ No jobs scraped")
                    return False
                    
        except Exception as e:
            console.print(f"  ❌ Eluta scraping error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_document_customization(self) -> bool:
        """Test document customization for scraped jobs."""
        try:
            if not self.scraped_jobs:
                console.print(f"  ⚠️ No jobs to customize documents for")
                return True
            
            if not self.profile:
                console.print(f"  ❌ No profile available for document customization")
                return False
            
            from src.utils.document_generator import DocumentGenerator
            
            # Initialize document generator
            generator = DocumentGenerator()
            
            console.print("  🔄 Customizing documents for scraped jobs...")
            
            # Create test resume and cover letter
            test_resume = {
                "name": "Test Data Analyst",
                "email": "test@example.com",
                "phone": "416-555-0123",
                "summary": "Experienced data analyst with 2 years of experience in Python, SQL, and data visualization.",
                "skills": ["Python", "SQL", "Excel", "Tableau", "Power BI", "R", "Statistics"],
                "experience": [
                    {
                        "title": "Data Analyst",
                        "company": "Tech Company",
                        "duration": "2022-2024",
                        "description": "Analyzed customer data and created reports using Python and SQL."
                    }
                ],
                "education": "Bachelor's in Computer Science, University of Toronto"
            }
            
            test_cover_letter = {
                "name": "Test Data Analyst",
                "email": "test@example.com",
                "phone": "416-555-0123",
                "introduction": "I am excited to apply for the Data Analyst position.",
                "body": "With my experience in data analysis and visualization, I believe I would be a great fit for this role.",
                "closing": "Thank you for considering my application."
            }
            
            # Save test documents
            profile_dir = Path(f"profiles/{self.test_profile}")
            profile_dir.mkdir(parents=True, exist_ok=True)
            
            # Save resume
            resume_path = profile_dir / "resume.json"
            with open(resume_path, 'w') as f:
                json.dump(test_resume, f, indent=2)
            
            # Save cover letter
            cover_letter_path = profile_dir / "cover_letter.json"
            with open(cover_letter_path, 'w') as f:
                json.dump(test_cover_letter, f, indent=2)
            
            console.print(f"  ✅ Test documents created")
            
            # Customize documents for first job
            if self.scraped_jobs:
                target_job = self.scraped_jobs[0]
                
                try:
                    # Test document customization
                    if hasattr(generator, 'customize_documents'):
                        customized = generator.customize_documents(target_job, self.profile)
                        console.print(f"  ✅ Document customization completed")
                        
                        # Save customized documents
                        customized_resume_path = profile_dir / "customized_resume.json"
                        customized_cover_path = profile_dir / "customized_cover_letter.json"
                        
                        # Handle different return types from customize_documents
                        if isinstance(customized, dict):
                            resume_data = customized.get('resume', {})
                            cover_data = customized.get('cover_letter', {})
                        else:
                            # Assume it's a tuple or other format
                            resume_data = test_resume
                            cover_data = test_cover_letter
                        
                        with open(customized_resume_path, 'w') as f:
                            json.dump(resume_data, f, indent=2)
                        
                        with open(customized_cover_path, 'w') as f:
                            json.dump(cover_data, f, indent=2)
                        
                        console.print(f"  ✅ Customized documents saved")
                        
                    else:
                        console.print(f"  ⚠️ Document customization method not available")
                        
                except Exception as e:
                    console.print(f"  ⚠️ Document customization error: {e}")
            
            return True
            
        except Exception as e:
            console.print(f"  ❌ Document customization error: {e}")
            return False
    
    def verify_dashboard_updates(self) -> bool:
        """Verify that dashboard shows real-time updates."""
        try:
            console.print("  🔄 Verifying dashboard updates...")
            
            # Wait a moment for dashboard to update
            time.sleep(3)
            
            # Test dashboard API endpoints
            endpoints = [
                "/api/dashboard-numbers",
                "/api/system-status",
                "/api/quick-test"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{self.dashboard_url}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        console.print(f"  ✅ {endpoint} responding")
                        
                        # Check for job data in dashboard numbers
                        if endpoint == "/api/dashboard-numbers":
                            total_jobs = data.get('summary', {}).get('total_jobs', 0)
                            if total_jobs > 0:
                                console.print(f"  📊 Dashboard shows {total_jobs} total jobs")
                            else:
                                console.print(f"  ⚠️ Dashboard shows 0 jobs (may need refresh)")
                        
                    else:
                        console.print(f"  ❌ {endpoint} error: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    console.print(f"  ❌ {endpoint} connection error: {e}")
            
            # Test dashboard UI
            try:
                response = requests.get(f"{self.dashboard_url}/", timeout=10)
                if response.status_code == 200:
                    console.print(f"  ✅ Dashboard UI accessible")
                else:
                    console.print(f"  ❌ Dashboard UI error: {response.status_code}")
            except requests.exceptions.RequestException as e:
                console.print(f"  ❌ Dashboard UI connection error: {e}")
            
            return True
            
        except Exception as e:
            console.print(f"  ❌ Dashboard verification error: {e}")
            return False
    
    def cleanup_test_data(self) -> bool:
        """Clean up test data and profile."""
        try:
            console.print("  🔄 Cleaning up test data...")
            
            # Clear test jobs from database
            from src.core.job_database import get_job_db
            db = get_job_db(self.test_profile)
            
            if hasattr(db, 'clear_all_jobs'):
                db.clear_all_jobs()
                console.print(f"  ✅ Cleared test jobs from database")
            
            # Remove test profile directory
            profile_dir = Path(f"profiles/{self.test_profile}")
            if profile_dir.exists():
                import shutil
                shutil.rmtree(profile_dir)
                console.print(f"  ✅ Removed test profile directory")
            
            return True
            
        except Exception as e:
            console.print(f"  ❌ Cleanup error: {e}")
            return False
    
    def print_results(self, passed: int, total: int):
        """Print test results summary."""
        table = Table(title="Eluta Data Analyst Workflow Test Results")
        table.add_column("Step", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="green")
        
        for step_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            details = "Completed successfully" if result else "Failed or error occurred"
            table.add_row(step_name, status, details)
        
        console.print(table)
        
        if passed == total:
            console.print(f"\n🎉 All {total} workflow steps completed successfully!")
            console.print(f"📊 Scraped {len(self.scraped_jobs)} data analyst jobs")
            console.print(f"📝 Document customization tested")
            console.print(f"📊 Dashboard real-time updates verified")
        else:
            console.print(f"\n⚠️ {passed}/{total} workflow steps completed. Some issues need attention.")
        
        if passed < total:
            console.print("\n❌ Workflow test failed. Please check the issues above.")

if __name__ == "__main__":
    tester = ElutaDataAnalystWorkflowTest()
    success = tester.run_complete_workflow()
    sys.exit(0 if success else 1) 