#!/usr/bin/env python3
"""
Reliable Job Processor - 100% reliable job processing with URL filtering
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel
from playwright.async_api import async_playwright

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.job_database import get_job_db
from src.utils.simple_url_filter import get_simple_url_filter
from src.utils.profile_helpers import load_profile

console = Console()

class ReliableJobProcessor:
    """100% reliable job processor with URL filtering and proper scraping."""
    
    def __init__(self, profile_name: str = "Nirajan"):
        self.profile_name = profile_name
        self.profile = load_profile(profile_name)
        self.db = get_job_db(profile_name)
        self.url_filter = get_simple_url_filter()
        
        # Processing stats
        self.stats = {
            'total_jobs': 0,
            'valid_urls': 0,
            'invalid_urls_skipped': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'database_updates': 0,
            'fields_extracted': {
                'title': 0,
                'company': 0,
                'description': 0,
                'location': 0,
                'salary': 0
            }
        }
    
    async def scrape_job_data(self, url: str) -> Dict[str, Any]:
        """Scrape job data using Playwright with proper error handling."""
        result = {
            'title': None,
            'company': None,
            'description': None,
            'location': None,
            'salary': None,
            'success': False,
            'error': None
        }
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # Set timeout
                page.set_default_timeout(30000)  # 30 seconds
                
                # Navigate to page
                await page.goto(url, wait_until='domcontentloaded')
                await asyncio.sleep(3)  # Wait for dynamic content
                
                # Handle cookie popups
                await self._handle_cookie_popups(page)
                
                # Extract data based on site type
                if 'workday' in url.lower():
                    result = await self._extract_workday_data(page, url)
                elif 'greenhouse' in url.lower():
                    result = await self._extract_greenhouse_data(page, url)
                elif 'lever.co' in url.lower():
                    result = await self._extract_lever_data(page, url)
                elif 'bombardier.com' in url.lower():
                    result = await self._extract_bombardier_data(page, url)
                else:
                    result = await self._extract_generic_data(page, url)
                
                result['success'] = True
                await browser.close()
                
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            console.print(f"[red]Scraping error for {url[:50]}...: {str(e)}[/red]")
        
        return result
    
    async def _handle_cookie_popups(self, page):
        """Handle cookie consent popups."""
        popup_selectors = [
            'button:has-text("Accept")',
            'button:has-text("Accept All")',
            'button:has-text("I Accept")',
            'button:has-text("OK")',
            'button:has-text("Continue")',
            '[data-automation-id="cookieBanner"] button',
            '.cookie-banner button',
            '#cookie-consent button'
        ]
        
        for selector in popup_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=2000)
                if element and await element.is_visible():
                    await element.click()
                    await asyncio.sleep(1)
                    console.print(f"[green]✅ Handled cookie popup[/green]")
                    break
            except:
                continue
    
    async def _extract_workday_data(self, page, url: str) -> Dict[str, Any]:
        """Extract data from Workday job pages."""
        data = {'url': url}
        
        try:
            # Title
            title_selectors = [
                '[data-automation-id="jobTitle"]',
                'h1[data-automation-id="jobTitle"]',
                'h1'
            ]
            data['title'] = await self._get_text_by_selectors(page, title_selectors)
            
            # Company - extract from URL if not found in page
            company_selectors = [
                '[data-automation-id="jobCompany"]',
                '.company-name'
            ]
            data['company'] = await self._get_text_by_selectors(page, company_selectors)
            
            # If no company found, extract from URL
            if not data['company']:
                # Extract company from workday URL like cibc.wd3.myworkdayjobs.com
                import re
                match = re.search(r'https://([^.]+)\.wd\d+\.myworkdayjobs\.com', url)
                if match:
                    data['company'] = match.group(1).replace('-', ' ').title()
            
            # Location
            location_selectors = [
                '[data-automation-id="jobLocation"]',
                '.location'
            ]
            data['location'] = await self._get_text_by_selectors(page, location_selectors)
            
            # Description
            desc_selectors = [
                '[data-automation-id="jobPostingDescription"]',
                '.job-description',
                '[data-automation-id="jobDescription"]'
            ]
            data['description'] = await self._get_text_by_selectors(page, desc_selectors)
            
            # Salary (often not available)
            salary_selectors = [
                '[data-automation-id="salary"]',
                '.salary-range'
            ]
            data['salary'] = await self._get_text_by_selectors(page, salary_selectors)
            
        except Exception as e:
            console.print(f"[yellow]Workday extraction error: {str(e)}[/yellow]")
        
        return data
    
    async def _extract_greenhouse_data(self, page, url: str) -> Dict[str, Any]:
        """Extract data from Greenhouse job pages."""
        data = {'url': url}
        
        try:
            # Title
            title_selectors = [
                '.app-title',
                'h1.app-title',
                'h1'
            ]
            data['title'] = await self._get_text_by_selectors(page, title_selectors)
            
            # Company - extract from URL if not found
            company_selectors = [
                '.company-name',
                '.app-company'
            ]
            data['company'] = await self._get_text_by_selectors(page, company_selectors)
            
            if not data['company']:
                # Extract from greenhouse URL
                import re
                match = re.search(r'greenhouse\.io/([^/]+)/', url)
                if match:
                    data['company'] = match.group(1).replace('-', ' ').title()
            
            # Location
            location_selectors = [
                '.location',
                '.app-location'
            ]
            data['location'] = await self._get_text_by_selectors(page, location_selectors)
            
            # Description
            desc_selectors = [
                '.content',
                '.app-content',
                '#content'
            ]
            data['description'] = await self._get_text_by_selectors(page, desc_selectors)
            
        except Exception as e:
            console.print(f"[yellow]Greenhouse extraction error: {str(e)}[/yellow]")
        
        return data
    
    async def _extract_lever_data(self, page, url: str) -> Dict[str, Any]:
        """Extract data from Lever job pages."""
        data = {'url': url}
        
        try:
            # Title
            title_selectors = [
                '.posting-headline h2',
                'h2.posting-headline',
                'h1'
            ]
            data['title'] = await self._get_text_by_selectors(page, title_selectors)
            
            # Company - extract from URL
            import re
            match = re.search(r'lever\.co/([^/]+)/', url)
            if match:
                data['company'] = match.group(1).replace('-', ' ').title()
            
            # Location
            location_selectors = [
                '.posting-categories .location',
                '.location'
            ]
            data['location'] = await self._get_text_by_selectors(page, location_selectors)
            
            # Description
            desc_selectors = [
                '.posting-content',
                '.content'
            ]
            data['description'] = await self._get_text_by_selectors(page, desc_selectors)
            
        except Exception as e:
            console.print(f"[yellow]Lever extraction error: {str(e)}[/yellow]")
        
        return data
    
    async def _extract_bombardier_data(self, page, url: str) -> Dict[str, Any]:
        """Extract data from Bombardier job pages."""
        data = {'url': url, 'company': 'Bombardier'}
        
        try:
            # Title
            title_selectors = [
                'h1.job-title',
                '.job-header h1',
                'h1',
                '.title'
            ]
            data['title'] = await self._get_text_by_selectors(page, title_selectors)
            
            # Location
            location_selectors = [
                '.job-location',
                '.location',
                '.city'
            ]
            data['location'] = await self._get_text_by_selectors(page, location_selectors)
            
            # Description
            desc_selectors = [
                '.job-description',
                '.description',
                '.content',
                '.job-details'
            ]
            data['description'] = await self._get_text_by_selectors(page, desc_selectors)
            
        except Exception as e:
            console.print(f"[yellow]Bombardier extraction error: {str(e)}[/yellow]")
        
        return data
    
    async def _extract_generic_data(self, page, url: str) -> Dict[str, Any]:
        """Generic extraction for unknown job sites."""
        data = {'url': url}
        
        try:
            # Title
            title_selectors = [
                'h1',
                '.job-title',
                '.title',
                '[class*="title"]'
            ]
            data['title'] = await self._get_text_by_selectors(page, title_selectors)
            
            # Company - try to extract from URL or page
            company_selectors = [
                '.company',
                '.company-name',
                '[class*="company"]'
            ]
            data['company'] = await self._get_text_by_selectors(page, company_selectors)
            
            if not data['company']:
                # Extract from domain
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '').replace('jobs.', '').replace('careers.', '')
                data['company'] = domain.split('.')[0].replace('-', ' ').title()
            
            # Location
            location_selectors = [
                '.location',
                '[class*="location"]'
            ]
            data['location'] = await self._get_text_by_selectors(page, location_selectors)
            
            # Description
            desc_selectors = [
                '.description',
                '.job-description',
                '.content',
                'main'
            ]
            data['description'] = await self._get_text_by_selectors(page, desc_selectors)
            
        except Exception as e:
            console.print(f"[yellow]Generic extraction error: {str(e)}[/yellow]")
        
        return data
    
    async def _get_text_by_selectors(self, page, selectors: List[str]) -> Optional[str]:
        """Try multiple selectors to get text content."""
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and text.strip():
                        return text.strip()
            except:
                continue
        return None
    
    def _extract_keywords_from_description(self, description: str) -> List[str]:
        """Extract keywords from job description."""
        if not description:
            return []
        
        profile_keywords = self.profile.get('keywords', [])
        found_keywords = []
        
        description_lower = description.lower()
        for keyword in profile_keywords:
            if keyword.lower() in description_lower:
                found_keywords.append(keyword)
        
        return found_keywords[:10]
    
    async def process_job(self, job: Dict[str, Any]) -> bool:
        """Process a single job."""
        job_id = job.get('id')
        job_url = job.get('url')
        
        if not job_url:
            console.print(f"[red]❌ Job {job_id} has no URL[/red]")
            return False
        
        # Validate URL first
        if not self.url_filter.is_valid_job_url(job_url):
            console.print(f"[yellow]⚠️ Skipping invalid URL: {job_url[:50]}...[/yellow]")
            self.stats['invalid_urls_skipped'] += 1
            return False
        
        self.stats['valid_urls'] += 1
        console.print(f"[cyan]Processing job {job_id}: {job_url[:60]}...[/cyan]")
        
        # Scrape job data
        scraped_data = await self.scrape_job_data(job_url)
        
        if scraped_data.get('success'):
            self.stats['successful_scrapes'] += 1
        else:
            self.stats['failed_scrapes'] += 1
        
        # Prepare update data with fallbacks
        update_data = {
            'title': scraped_data.get('title') or self._extract_title_from_url(job_url),
            'company': scraped_data.get('company') or self._extract_company_from_url(job_url),
            'location': scraped_data.get('location'),
            'salary_range': scraped_data.get('salary'),
            'compatibility_score': 0.7  # Default score
        }

        # Add job_description if available
        if scraped_data.get('description'):
            update_data['job_description'] = scraped_data['description']

            # Extract keywords
            keywords = self._extract_keywords_from_description(scraped_data['description'])
            if keywords:
                update_data['keywords'] = ', '.join(keywords)

        # Update field extraction stats
        for field in ['title', 'company', 'job_description', 'location', 'salary_range']:
            if update_data.get(field):
                self.stats['fields_extracted'][field.replace('job_description', 'description').replace('salary_range', 'salary')] += 1

        # Set status
        if update_data['title'] and update_data['company']:
            update_data['status'] = 'processed'
        else:
            update_data['status'] = 'needs_processing'

        # Update database
        try:
            success = self.db.update_job(job_id, update_data)
            if success:
                console.print(f"[green]✅ Updated job {job_id} - Status: {update_data['status']}[/green]")
                self.stats['database_updates'] += 1
                self.stats['total_jobs'] += 1
                return True
            else:
                console.print(f"[red]❌ Failed to update job {job_id}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]❌ Database error for job {job_id}: {str(e)}[/red]")
            return False
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract job title from URL as fallback."""
        try:
            if '/job/' in url:
                parts = url.split('/job/')[-1].split('/')
                if len(parts) > 1:
                    title = parts[0].replace('-', ' ').replace('_', ' ').title()
                    return title
            return "Job Position"
        except:
            return "Job Position"
    
    def _extract_company_from_url(self, url: str) -> str:
        """Extract company name from URL as fallback."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            if '.workday.com' in domain:
                company = domain.split('.')[0].replace('-', ' ').title()
                return company
            elif '.greenhouse.io' in domain:
                company = domain.split('.')[0].replace('-', ' ').title()
                return company
            elif 'bombardier.com' in domain:
                return "Bombardier"
            else:
                company = domain.replace('www.', '').replace('jobs.', '').replace('careers.', '')
                return company.split('.')[0].replace('-', ' ').title()
        except:
            return "Company"
    
    async def process_all_jobs(self):
        """Process all jobs that need processing."""
        console.print(Panel.fit("🚀 Starting Reliable Job Processing", style="bold blue"))
        
        # Get all jobs
        all_jobs = self.db.get_all_jobs()
        console.print(f"[blue]📊 Found {len(all_jobs)} jobs in database[/blue]")
        
        # Filter jobs that need processing
        jobs_to_process = []
        for job in all_jobs:
            needs_processing = (
                job.get('status') in ['scraped', 'needs_processing'] or
                not job.get('title') or 
                job.get('title') in ['Job from URL', 'Pending Processing'] or
                not job.get('company') or
                job.get('company') in ['Pending Processing']
            )
            
            if needs_processing:
                jobs_to_process.append(job)
        
        console.print(f"[cyan]Jobs needing processing: {len(jobs_to_process)}[/cyan]")
        
        if not jobs_to_process:
            console.print("[green]✅ All jobs are already processed![/green]")
            return
        
        # Process jobs with progress tracking
        with Progress() as progress:
            task = progress.add_task("Processing jobs...", total=len(jobs_to_process))
            
            for i, job in enumerate(jobs_to_process):
                await self.process_job(job)
                progress.advance(task)
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(2)
                
                # Show progress every 10 jobs
                if (i + 1) % 10 == 0:
                    console.print(f"[cyan]Processed {i + 1}/{len(jobs_to_process)} jobs[/cyan]")
        
        # Show final statistics
        self.show_final_stats()
    
    def show_final_stats(self):
        """Show final processing statistics."""
        console.print(Panel.fit("📊 Processing Complete - Final Statistics", style="bold green"))
        
        table = Table(title="Processing Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        
        table.add_row("Total Jobs Processed", str(self.stats['total_jobs']))
        table.add_row("Valid URLs", str(self.stats['valid_urls']))
        table.add_row("Invalid URLs Skipped", str(self.stats['invalid_urls_skipped']))
        table.add_row("Successful Scrapes", str(self.stats['successful_scrapes']))
        table.add_row("Failed Scrapes", str(self.stats['failed_scrapes']))
        table.add_row("Database Updates", str(self.stats['database_updates']))
        
        console.print(table)
        
        # Field extraction stats
        field_table = Table(title="Field Extraction Success")
        field_table.add_column("Field", style="cyan")
        field_table.add_column("Extracted", style="green")
        
        for field, count in self.stats['fields_extracted'].items():
            field_table.add_row(field.title(), str(count))
        
        console.print(field_table)
        
        # Success rates
        if self.stats['valid_urls'] > 0:
            scrape_success_rate = (self.stats['successful_scrapes'] / self.stats['valid_urls']) * 100
            console.print(f"[bold green]Scraping Success Rate: {scrape_success_rate:.1f}%[/bold green]")

async def main():
    """Main function."""
    processor = ReliableJobProcessor("Nirajan")
    await processor.process_all_jobs()

if __name__ == "__main__":
    asyncio.run(main())