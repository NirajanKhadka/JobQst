"""
CSV Batch Job Application Module.
Processes job applications from CSV files containing job URLs and details.
"""

import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from playwright.sync_api import sync_playwright

# Import functions directly to avoid circular imports
def detect(url: str) -> str:
    """Detect ATS system from URL."""
    url_lower = url.lower()
    if 'workday' in url_lower:
        return 'workday'
    elif 'icims' in url_lower:
        return 'icims'
    elif 'greenhouse' in url_lower:
        return 'greenhouse'
    elif 'lever' in url_lower:
        return 'lever'
    elif 'bamboohr' in url_lower:
        return 'bamboohr'
    elif 'smartrecruiters' in url_lower:
        return 'smartrecruiters'
    else:
        return 'unknown'

def get_submitter(ats_name: str, browser_context=None):
    """Get appropriate submitter for ATS system."""
    from .ats_based_applicator import ATSBasedApplicator
    return ATSBasedApplicator("Nirajan")  # Default profile name

from src.core import utils
from src.utils.document_generator import customize

console = Console()

class CSVJobApplicator:
    """
    Handles batch job applications from CSV files.
    """
    
    def __init__(self, profile_name: str = "default"):
        """
        Initialize the CSV applicator.
        
        Args:
            profile_name: Name of the user profile to use
        """
        self.profile_name = profile_name
        self.profile = None
        self.session = {}
        
    def load_profile(self) -> bool:
        """
        Load the user profile.
        
        Returns:
            True if profile loaded successfully, False otherwise
        """
        try:
            # Try both profile.json and {profile_name}.json
            profile_paths = [
                Path("profiles") / self.profile_name / "profile.json",
                Path("profiles") / self.profile_name / f"{self.profile_name}.json"
            ]

            profile_path = None
            for path in profile_paths:
                if path.exists():
                    profile_path = path
                    break

            if not profile_path:
                console.print(f"[bold red]Profile not found in: {[str(p) for p in profile_paths]}[/bold red]")
                return False

            self.profile = utils.load_profile(self.profile_name)
            console.print(f"[green]Loaded profile: {self.profile_name}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[bold red]Error loading profile: {e}[/bold red]")
            return False
    
    def load_session(self) -> None:
        """Load or create session data."""
        self.session = utils.load_session(self.profile)
    
    def save_session(self) -> None:
        """Save session data."""
        utils.save_session(self.profile, self.session)
    
    def read_csv_jobs(self, csv_path: str) -> List[Dict]:
        """
        Read job data from CSV file.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            List of job dictionaries
            
        Expected CSV format:
        url,title,company,location,summary
        """
        jobs = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Validate required columns
                required_columns = ['url']
                if not all(col in reader.fieldnames for col in required_columns):
                    console.print(f"[bold red]CSV must contain at least 'url' column[/bold red]")
                    console.print(f"[yellow]Found columns: {reader.fieldnames}[/yellow]")
                    return []
                
                for row_num, row in enumerate(reader, start=2):
                    if not row.get('url', '').strip():
                        console.print(f"[yellow]Skipping row {row_num}: empty URL[/yellow]")
                        continue
                    
                    job = {
                        'url': row['url'].strip(),
                        'title': row.get('title', 'Unknown Position').strip(),
                        'company': row.get('company', 'Unknown Company').strip(),
                        'location': row.get('location', 'Unknown Location').strip(),
                        'summary': row.get('summary', '').strip(),
                        'site': 'CSV Import'
                    }
                    
                    jobs.append(job)
                
                console.print(f"[green]Loaded {len(jobs)} jobs from CSV[/green]")
                return jobs
                
        except FileNotFoundError:
            console.print(f"[bold red]CSV file not found: {csv_path}[/bold red]")
            return []
        except Exception as e:
            console.print(f"[bold red]Error reading CSV file: {e}[/bold red]")
            return []
    
    def display_jobs_preview(self, jobs: List[Dict], limit: int = 10) -> None:
        """
        Display a preview of jobs from the CSV.
        
        Args:
            jobs: List of job dictionaries
            limit: Maximum number of jobs to display
        """
        if not jobs:
            console.print("[yellow]No jobs to display[/yellow]")
            return
        
        table = Table(title=f"Jobs Preview (showing {min(len(jobs), limit)} of {len(jobs)})")
        table.add_column("Title", style="cyan")
        table.add_column("Company", style="magenta")
        table.add_column("Location", style="green")
        table.add_column("URL", style="blue", max_width=50)
        
        for job in jobs[:limit]:
            table.add_row(
                job['title'],
                job['company'],
                job['location'],
                job['url'][:47] + "..." if len(job['url']) > 50 else job['url']
            )
        
        console.print(table)
    
    def filter_applied_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Filter out jobs that have already been applied to.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of jobs not yet applied to
        """
        done_hashes = set(self.session.get("done", []))
        filtered_jobs = []
        
        for job in jobs:
            job_hash = utils.hash_job(job)
            if job_hash not in done_hashes:
                filtered_jobs.append(job)
            else:
                console.print(f"[yellow]Skipping already applied job: {job['title']} at {job['company']}[/yellow]")
        
        console.print(f"[green]{len(filtered_jobs)} new jobs to process (filtered {len(jobs) - len(filtered_jobs)} already applied)[/green]")
        return filtered_jobs
    
    def apply_to_jobs(self, jobs: List[Dict], ats_choice: str = "auto", delay_seconds: int = 30) -> Dict[str, int]:
        """
        Apply to jobs from the list with enhanced error handling and retry mechanisms.

        Args:
            jobs: List of job dictionaries
            ats_choice: ATS system to use ("auto" for detection, or specific ATS name)
            delay_seconds: Delay between applications in seconds

        Returns:
            Dictionary with application statistics
        """
        if not jobs:
            console.print("[yellow]No jobs to apply to[/yellow]")
            return {"applied": 0, "failed": 0, "manual": 0, "total": 0, "retried": 0, "skipped": 0}

        stats = {"applied": 0, "failed": 0, "manual": 0, "total": len(jobs), "retried": 0, "skipped": 0}
        failed_jobs = []  # Track failed jobs for potential retry

        # Enhanced browser configuration for better reliability
        with sync_playwright() as p:
            browser_args = [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]

            browser = p.chromium.launch(
                headless=False,  # Use headed mode for better debugging
                args=browser_args
            )

            # Create context with enhanced settings
            ctx = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            try:
                with Progress() as progress:
                    task = progress.add_task("[green]Applying to jobs...", total=len(jobs))
                    
                    for i, job in enumerate(jobs):
                        console.print(f"\n[bold blue]Processing job {i+1}/{len(jobs)}[/bold blue]")
                        console.print(f"[cyan]Title:[/cyan] {job.get('title', 'Unknown')}")
                        console.print(f"[cyan]Company:[/cyan] {job.get('company', 'Unknown')}")
                        console.print(f"[cyan]URL:[/cyan] {job.get('url', 'No URL')}")

                        # Skip jobs without URLs
                        if not job.get("url"):
                            console.print("[red]❌ Skipping job with no URL[/red]")
                            stats["skipped"] += 1
                            progress.update(task, advance=1)
                            continue

                        # Enhanced application process with retry logic
                        max_retries = 2
                        retry_count = 0
                        application_successful = False

                        while retry_count <= max_retries and not application_successful:
                            try:
                                if retry_count > 0:
                                    console.print(f"[yellow]🔄 Retry attempt {retry_count}/{max_retries}[/yellow]")
                                    stats["retried"] += 1
                                    time.sleep(5)  # Brief delay before retry

                                # Generate documents with error handling
                                console.print("[green]📄 Generating tailored documents...[/green]")
                                pdf_cv, pdf_cl = self._generate_documents_with_fallback(job)

                                if not pdf_cv:
                                    console.print("[red]❌ Failed to generate documents[/red]")
                                    break

                                # Detect ATS with fallback
                                detected_ats = self._detect_ats_with_fallback(job["url"], ats_choice)
                                console.print(f"[green]🔍 Detected ATS:[/green] {detected_ats}")

                                # Get submitter with error handling
                                submitter = self._get_submitter_with_fallback(detected_ats, ctx)

                                if not submitter:
                                    console.print("[red]❌ Failed to get ATS submitter[/red]")
                                    break

                                # Submit application with timeout and error handling
                                console.print("[green]🚀 Submitting application...[/green]")
                                status = self._submit_application_with_timeout(submitter, job, pdf_cv, pdf_cl)
                                console.print(f"[bold]📊 Status:[/bold] {status}")

                                # Update statistics based on status
                                if status and ("Applied" in status or "Success" in status):
                                    stats["applied"] += 1
                                    application_successful = True
                                elif status and ("Manual" in status or "Review" in status):
                                    stats["manual"] += 1
                                    application_successful = True
                                else:
                                    if retry_count >= max_retries:
                                        stats["failed"] += 1
                                        failed_jobs.append({
                                            "job": job,
                                            "error": status,
                                            "attempts": retry_count + 1
                                        })

                                # Log result with enhanced details
                                self._log_application_result(job, status, pdf_cv, pdf_cl, detected_ats, retry_count)

                                # Mark as done if successful
                                if application_successful:
                                    job_hash = utils.hash_job(job)
                                    self.session.setdefault("done", []).append(job_hash)
                                    self.save_session()
                                    console.print("[green]✅ Application completed successfully[/green]")
                                    break

                            except Exception as e:
                                console.print(f"[bold red]❌ Error processing job (attempt {retry_count + 1}): {e}[/bold red]")
                                retry_count += 1

                                if retry_count > max_retries:
                                    stats["failed"] += 1
                                    failed_jobs.append({
                                        "job": job,
                                        "error": str(e),
                                        "attempts": retry_count
                                    })
                                    break

                            retry_count += 1

                        # Update progress
                        progress.update(task, advance=1)

                        # Intelligent delay between applications
                        if i < len(jobs) - 1:
                            # Longer delay after failures to avoid rate limiting
                            actual_delay = delay_seconds * (2 if not application_successful else 1)
                            console.print(f"[yellow]⏳ Waiting {actual_delay} seconds before next application...[/yellow]")
                            time.sleep(actual_delay)
                
            finally:
                ctx.close()
                browser.close()
        
        return stats
    
    def _generate_documents(self, job: Dict) -> Tuple[str, str]:
        """
        Generate tailored resume and cover letter for a job.
        
        Args:
            job: Job dictionary
            
        Returns:
            Tuple of (resume_path, cover_letter_path)
        """
        job_hash = utils.hash_job(job)
        
        # Generate resume
        resume_docx = customize(job, self.profile)
        pdf_cv = utils.save_document_as_pdf(resume_docx, job_hash, self.profile, is_resume=True)
        
        # Generate cover letter
        cover_letter_docx = customize(job, self.profile)
        pdf_cl = utils.save_document_as_pdf(cover_letter_docx, job_hash, self.profile, is_resume=False)
        
        return pdf_cv, pdf_cl

    def _generate_documents_with_fallback(self, job: Dict) -> Tuple[str, str]:
        """
        Generate tailored documents with fallback error handling.

        Args:
            job: Job dictionary

        Returns:
            Tuple of (resume_path, cover_letter_path) or (None, None) on failure
        """
        try:
            return self._generate_documents(job)
        except Exception as e:
            console.print(f"[red]❌ Document generation failed: {e}[/red]")
            # Try to use generic documents as fallback
            try:
                console.print("[yellow]🔄 Attempting fallback with generic documents...[/yellow]")
                job_hash = utils.hash_job(job)

                # Use basic profile info for generic documents
                generic_job = {
                    "title": "Generic Position",
                    "company": job.get("company", "Company"),
                    "description": "Generic job description"
                }

                resume_docx = customize(generic_job, self.profile)
                pdf_cv = utils.save_document_as_pdf(resume_docx, job_hash, self.profile, is_resume=True)

                cover_letter_docx = customize(generic_job, self.profile)
                pdf_cl = utils.save_document_as_pdf(cover_letter_docx, job_hash, self.profile, is_resume=False)

                console.print("[green]✅ Fallback documents generated successfully[/green]")
                return pdf_cv, pdf_cl

            except Exception as fallback_error:
                console.print(f"[red]❌ Fallback document generation also failed: {fallback_error}[/red]")
                return None, None

    def _detect_ats_with_fallback(self, url: str, ats_choice: str) -> str:
        """
        Detect ATS with fallback to manual detection.

        Args:
            url: Job URL
            ats_choice: User's ATS choice

        Returns:
            Detected ATS system name
        """
        try:
            if ats_choice != "auto":
                return ats_choice

            detected_ats = detect(url)
            if detected_ats and detected_ats != "unknown":
                return detected_ats

            # Fallback: try to detect from URL patterns
            url_lower = url.lower()
            if "workday" in url_lower:
                return "workday"
            elif "icims" in url_lower:
                return "icims"
            elif "greenhouse" in url_lower:
                return "greenhouse"
            elif "bamboohr" in url_lower:
                return "bamboohr"
            elif "lever" in url_lower:
                return "lever"
            else:
                return "manual"  # Default fallback

        except Exception as e:
            console.print(f"[yellow]⚠️ ATS detection failed: {e}, using manual[/yellow]")
            return "manual"

    def _get_submitter_with_fallback(self, ats_name: str, ctx):
        """
        Get ATS submitter with error handling.

        Args:
            ats_name: ATS system name
            ctx: Browser context

        Returns:
            ATS submitter instance or None
        """
        try:
            submitter = get_submitter(ats_name, ctx)
            return submitter
        except Exception as e:
            console.print(f"[red]❌ Failed to get {ats_name} submitter: {e}[/red]")
            # Try manual submitter as fallback
            try:
                console.print("[yellow]🔄 Falling back to manual submitter...[/yellow]")
                return get_submitter("manual", ctx)
            except Exception as fallback_error:
                console.print(f"[red]❌ Manual submitter fallback failed: {fallback_error}[/red]")
                return None

    def _submit_application_with_timeout(self, submitter, job: Dict, pdf_cv: str, pdf_cl: str, timeout: int = 300) -> str:
        """
        Submit application with timeout and error handling.

        Args:
            submitter: ATS submitter instance
            job: Job dictionary
            pdf_cv: Resume PDF path
            pdf_cl: Cover letter PDF path
            timeout: Timeout in seconds

        Returns:
            Application status string
        """
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("Application submission timed out")

        try:
            # Set timeout (only on Unix systems)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout)

            status = submitter.submit(job, self.profile, pdf_cv, pdf_cl)

            # Clear timeout
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)

            return status

        except TimeoutError:
            console.print(f"[red]❌ Application submission timed out after {timeout} seconds[/red]")
            return "Timeout"
        except Exception as e:
            console.print(f"[red]❌ Application submission failed: {e}[/red]")
            return f"Failed: {str(e)}"
        finally:
            # Ensure timeout is cleared
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)

    def _log_application_result(self, job: Dict, status: str, pdf_cv: str, pdf_cl: str, ats: str, retry_count: int):
        """
        Log application result with enhanced details.

        Args:
            job: Job dictionary
            status: Application status
            pdf_cv: Resume PDF path
            pdf_cl: Cover letter PDF path
            ats: ATS system used
            retry_count: Number of retry attempts
        """
        try:
            # Enhanced logging with retry information
            enhanced_status = f"{status} (attempts: {retry_count + 1})" if retry_count > 0 else status
            utils.append_log_row(job, self.profile, enhanced_status, pdf_cv, pdf_cl, ats)
        except Exception as e:
            console.print(f"[yellow]⚠️ Failed to log application result: {e}[/yellow]")

    def print_statistics(self, stats: Dict[str, int]) -> None:
        """
        Print enhanced application statistics with retry and error details.

        Args:
            stats: Statistics dictionary
        """
        table = Table(title="📊 Enhanced Application Results")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Percentage", style="green")
        table.add_column("Details", style="yellow")

        total = stats["total"]
        if total > 0:
            # Calculate success rate
            successful = stats["applied"] + stats["manual"]
            success_rate = successful / total * 100

            table.add_row(
                "✅ Applied",
                str(stats["applied"]),
                f"{stats['applied']/total*100:.1f}%",
                "Fully automated"
            )
            table.add_row(
                "👤 Manual Review",
                str(stats["manual"]),
                f"{stats['manual']/total*100:.1f}%",
                "Requires manual action"
            )
            table.add_row(
                "❌ Failed",
                str(stats["failed"]),
                f"{stats['failed']/total*100:.1f}%",
                "Could not process"
            )
            table.add_row(
                "⏭️ Skipped",
                str(stats.get("skipped", 0)),
                f"{stats.get('skipped', 0)/total*100:.1f}%",
                "No URL or invalid"
            )
            table.add_row(
                "🔄 Retried",
                str(stats.get("retried", 0)),
                f"{stats.get('retried', 0)/total*100:.1f}%",
                "Retry attempts made"
            )
            table.add_row(
                "📈 Success Rate",
                str(successful),
                f"{success_rate:.1f}%",
                "Applied + Manual"
            )
            table.add_row(
                "📊 Total Processed",
                str(total),
                "100.0%",
                "All jobs attempted"
            )

        console.print(table)

        # Additional summary
        if total > 0:
            console.print(f"\n[bold green]🎯 Summary:[/bold green]")
            console.print(f"  • {stats['applied']} jobs applied automatically")
            console.print(f"  • {stats['manual']} jobs require manual review")
            console.print(f"  • {stats['failed']} jobs failed to process")
            if stats.get("retried", 0) > 0:
                console.print(f"  • {stats['retried']} retry attempts made")
            if stats.get("skipped", 0) > 0:
                console.print(f"  • {stats['skipped']} jobs skipped (no URL)")

            # Performance insights
            if stats["applied"] > 0:
                console.print(f"\n[bold blue]💡 Performance:[/bold blue]")
                console.print(f"  • Automation rate: {stats['applied']/total*100:.1f}%")
                if stats.get("retried", 0) > 0:
                    retry_rate = stats["retried"] / total * 100
                    console.print(f"  • Retry rate: {retry_rate:.1f}%")
                    if retry_rate > 20:
                        console.print(f"  • [yellow]⚠️ High retry rate detected - consider checking network/ATS issues[/yellow]")

    def get_field_mapping(self):
        return {
            'profile_fields': ['first_name', 'last_name'],
            'job_fields': ['title', 'company', 'location'],
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'title': 'Job Title',
            'company': 'Company',
            'location': 'Location'
        }

# Backward compatibility alias
CSVApplicator = CSVJobApplicator

def apply_from_csv(csv_path: str, profile_name: str, ats: str = "auto", delay: int = 30, preview: bool = False, limit: int = None) -> int:
    """Apply to jobs from CSV file (wrapper function for compatibility).

    Args:
        csv_path: Path to CSV file containing job data
        profile_name: Profile name to use
        ats: ATS system to use (auto, workday, icims, greenhouse, bamboohr)
        delay: Delay between applications in seconds
        preview: Preview jobs without applying
        limit: Limit number of jobs to process

    Returns:
        0 if successful, 1 if failed
    """
    console.print(f"[bold]Applying to jobs from CSV file:[/bold] {csv_path}")

    # Initialize applicator
    applicator = CSVJobApplicator(profile_name)

    # Load profile
    if not applicator.load_profile():
        return 1

    # Load session
    applicator.load_session()

    # Read jobs from CSV
    jobs = applicator.read_csv_jobs(csv_path)
    if not jobs:
        return 1

    # Apply limit if specified
    if limit:
        jobs = jobs[:limit]
        console.print(f"[yellow]Limited to first {limit} jobs[/yellow]")

    # Display preview
    applicator.display_jobs_preview(jobs)

    if preview:
        console.print("[yellow]Preview mode - not applying to jobs[/yellow]")
        return 0

    # Filter already applied jobs
    jobs = applicator.filter_applied_jobs(jobs)

    if not jobs:
        console.print("[green]All jobs have already been applied to![/green]")
        return 0

    # Confirm before proceeding
    console.print(f"\n[bold yellow]Ready to apply to {len(jobs)} jobs[/bold yellow]")
    confirm = input("Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        console.print("[yellow]Cancelled by user[/yellow]")
        return 0

    # Apply to jobs
    stats = applicator.apply_to_jobs(jobs, ats, delay)

    # Print results
    applicator.print_statistics(stats)

    # Return success/failure based on stats
    if stats["applied"] > 0 or stats["manual"] > 0:
        return 0  # Success
    else:
        return 1  # Failed

def main():
    """Main function for CSV application processing."""
    import argparse

    parser = argparse.ArgumentParser(description="Apply to jobs from CSV file")
    parser.add_argument("profile", help="Profile name to use")
    parser.add_argument("csv_file", help="Path to CSV file containing job data")
    parser.add_argument("--ats", default="auto", help="ATS system to use (auto, workday, icims, greenhouse, bamboohr)")
    parser.add_argument("--delay", type=int, default=30, help="Delay between applications in seconds")
    parser.add_argument("--preview", action="store_true", help="Preview jobs without applying")
    parser.add_argument("--limit", type=int, help="Limit number of jobs to process")

    args = parser.parse_args()

    # Use the wrapper function
    result = apply_from_csv(
        csv_path=args.csv_file,
        profile_name=args.profile,
        ats=args.ats,
        delay=args.delay,
        preview=args.preview,
        limit=args.limit
    )

    return result


if __name__ == "__main__":
    main()
