#!/usr/bin/env python3
"""
Process Pending Jobs - Update jobs with "Pending Processing" status
This script processes jobs that were saved with placeholder data and extracts real details.
"""

import asyncio
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress
from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile
from urllib.parse import urlparse
import time

console = Console()


class JobProcessor:
    """Process jobs with pending status to extract real details."""
    
    def __init__(self, profile_name: str = "Nirajan"):
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def clean_company_name(self, company_name: str) -> str:
        """Clean company name by removing common suffixes and prefixes."""
        if not company_name or company_name.strip() == "":
            return "Unknown Company"
        
        # Remove common suffixes and prefixes
        suffixes_to_remove = [
            "TOP EMPLOYER",
            "FEATURED EMPLOYER", 
            "PREMIUM EMPLOYER",
            "VERIFIED EMPLOYER",
            "HIRING NOW",
            "URGENT HIRING",
            "NEW JOBS",
            "MULTIPLE POSITIONS",
            "- REMOTE",
            "- HYBRID",
            "- ONSITE"
        ]
        
        cleaned = company_name.strip()
        
        # Remove suffixes (case insensitive)
        for suffix in suffixes_to_remove:
            if cleaned.upper().endswith(suffix.upper()):
                cleaned = cleaned[:-len(suffix)].strip()
        
        # Remove extra whitespace and special characters at the end
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces to single space
        cleaned = cleaned.rstrip(' -•·|')  # Remove trailing separators
        
        # Handle common patterns
        if " / " in cleaned:
            # Take the first part if it looks like "Company / Division"
            parts = cleaned.split(" / ")
            if len(parts[0]) > 3 and len(parts[0]) < len(cleaned) * 0.7:  # First part is substantial but not too long
                cleaned = parts[0].strip()
        
        # Final validation
        if len(cleaned) < 2:
            return "Unknown Company"
        
        return cleaned
    
    def extract_company_from_url(self, url: str) -> str:
        """Extract company name from URL domain."""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            if domain:
                # Remove common prefixes and suffixes
                domain = domain.replace('www.', '').replace('careers.', '').replace('jobs.', '')
                company_name = domain.split('.')[0]
                
                # Capitalize properly
                if company_name and len(company_name) > 2:
                    return company_name.capitalize()
        except:
            pass
        
        return "Unknown Company"
    
    def extract_job_details(self, url: str) -> dict:
        """Extract job details from URL."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_selectors = ['h1', '.job-title', '[data-testid="job-title"]', '.title']
            title = "Job from URL"
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    title = elem.get_text(strip=True)
                    break
            
            # Extract company
            company_selectors = ['.company', '.employer', '.org', '[data-testid="company"]']
            company = self.extract_company_from_url(url)  # Fallback
            for selector in company_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    company = self.clean_company_name(elem.get_text(strip=True))
                    break
            
            # Extract location
            location_selectors = ['.location', '.loc', '[data-testid="location"]']
            location = "Remote/Unknown"
            for selector in location_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    location = elem.get_text(strip=True)
                    break
            
            # Extract description (first paragraph or job description)
            desc_selectors = ['.job-description', '.description', '.job-summary', 'p']
            description = ""
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    description = elem.get_text(strip=True)[:500]  # Limit length
                    break
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'summary': description,
                'status': 'processed'
            }
            
        except Exception as e:
            console.print(f"[red]Error extracting from {url[:50]}: {e}[/red]")
            return {
                'title': 'Job from URL',
                'company': self.extract_company_from_url(url),
                'location': 'Remote/Unknown',
                'summary': 'Job details could not be extracted',
                'status': 'processed'
            }
    
    def process_pending_jobs(self, limit: int = 20):
        """Process jobs with pending status."""
        console.print(f"[bold blue]🔄 Processing Pending Jobs (limit: {limit})[/bold blue]")
        
        # Get pending jobs
        with self.db._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, url, title, company 
                FROM jobs 
                WHERE (title = 'Pending Processing' OR company = 'Pending Processing')
                AND url IS NOT NULL AND url != ''
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            pending_jobs = cursor.fetchall()
        
        if not pending_jobs:
            console.print("[green]✅ No pending jobs found![/green]")
            return
        
        console.print(f"[cyan]Found {len(pending_jobs)} pending jobs to process[/cyan]")
        
        processed_count = 0
        failed_count = 0
        
        with Progress() as progress:
            task = progress.add_task("[green]Processing jobs...", total=len(pending_jobs))
            
            for job in pending_jobs:
                job_id, url, current_title, current_company = job
                
                console.print(f"[cyan]Processing job {job_id}: {url[:50]}...[/cyan]")
                
                # Extract details
                details = self.extract_job_details(url)
                
                # Update database
                try:
                    with self.db._get_connection() as conn:
                        conn.execute("""
                            UPDATE jobs 
                            SET title = ?, company = ?, location = ?, summary = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (
                            details['title'],
                            details['company'], 
                            details['location'],
                            details['summary'],
                            details['status'],
                            job_id
                        ))
                        conn.commit()
                    
                    console.print(f"[green]✅ Updated: {details['title'][:40]}... at {details['company']}[/green]")
                    processed_count += 1
                    
                except Exception as e:
                    console.print(f"[red]❌ Failed to update job {job_id}: {e}[/red]")
                    failed_count += 1
                
                progress.update(task, advance=1)
                time.sleep(1)  # Rate limiting
        
        console.print(f"\n[bold]Processing Complete:[/bold]")
        console.print(f"[green]✅ Processed: {processed_count}[/green]")
        console.print(f"[red]❌ Failed: {failed_count}[/red]")
    
    def show_company_diversity(self):
        """Show company diversity after processing."""
        console.print(f"\n[bold blue]📊 Company Diversity Analysis[/bold blue]")
        
        with self.db._get_connection() as conn:
            cursor = conn.execute("""
                SELECT company, COUNT(*) as count
                FROM jobs 
                WHERE company IS NOT NULL AND company != ''
                GROUP BY company
                ORDER BY count DESC
                LIMIT 10
            """)
            companies = cursor.fetchall()
        
        if companies:
            from rich.table import Table
            table = Table(title="Top Companies")
            table.add_column("Company", style="cyan")
            table.add_column("Job Count", style="green")
            
            for company, count in companies:
                table.add_row(company, str(count))
            
            console.print(table)
            
            unique_companies = len(companies)
            console.print(f"\n[green]✅ Found {unique_companies} unique companies[/green]")
        else:
            console.print("[red]❌ No companies found in database[/red]")


def main():
    """Main function to process pending jobs."""
    processor = JobProcessor("Nirajan")
    
    console.print("[bold green]🔄 Job Processing Tool[/bold green]")
    console.print("[cyan]This will update jobs with 'Pending Processing' status[/cyan]")
    
    # Show current status
    with processor.db._get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM jobs WHERE title = 'Pending Processing' OR company = 'Pending Processing'")
        pending_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM jobs")
        total_count = cursor.fetchone()[0]
    
    console.print(f"[yellow]Pending jobs: {pending_count}/{total_count}[/yellow]")
    
    if pending_count == 0:
        console.print("[green]✅ No pending jobs to process![/green]")
        processor.show_company_diversity()
        return
    
    # Ask how many to process
    try:
        limit = int(input(f"How many jobs to process? (max {pending_count}, press Enter for 10): ") or "10")
        limit = min(limit, pending_count)
    except ValueError:
        limit = 10
    
    # Process jobs
    processor.process_pending_jobs(limit)
    
    # Show results
    processor.show_company_diversity()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Processing interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Processing failed: {e}[/red]")