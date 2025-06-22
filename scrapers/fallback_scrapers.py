"""
Fallback scrapers for robust job scraping.
These scrapers provide basic functionality when main scrapers fail.
"""

import csv
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from rich.console import Console

from .base_scraper import BaseJobScraper

console = Console()


class BasicFallbackScraper(BaseJobScraper):
    """
    Basic fallback scraper using simple HTTP requests and BeautifulSoup.
    No browser automation, minimal dependencies.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_jobs(self, keywords: List[str]) -> List[Dict]:
        """
        Scrape jobs using basic HTTP requests.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of job dictionaries
        """
        console.print("[cyan]🔍 Using basic fallback scraper...[/cyan]")
        
        all_jobs = []
        
        for keyword in keywords:
            console.print(f"[yellow]Searching for: {keyword}[/yellow]")
            
            try:
                # Try to scrape from a simple job board
                jobs = self._scrape_basic_jobs(keyword)
                all_jobs.extend(jobs)
                
                # Add delay to be respectful
                time.sleep(2)
                
            except Exception as e:
                console.print(f"[red]Error scraping {keyword}: {e}[/red]")
                continue
        
        # Remove duplicates
        unique_jobs = self._remove_duplicates(all_jobs)
        
        console.print(f"[green]Basic scraper found {len(unique_jobs)} unique jobs[/green]")
        return unique_jobs
    
    def _scrape_basic_jobs(self, keyword: str) -> List[Dict]:
        """
        Scrape jobs for a single keyword using basic methods.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        # Try multiple simple job search URLs
        search_urls = [
            f"https://ca.indeed.com/jobs?q={keyword}&l=Canada",
            f"https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={keyword}",
        ]
        
        for url in search_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_jobs = self._extract_jobs_from_soup(soup, keyword)
                    jobs.extend(page_jobs)
                    break  # If one works, use it
            except Exception as e:
                console.print(f"[yellow]Failed to scrape {url}: {e}[/yellow]")
                continue
        
        return jobs
    
    def _extract_jobs_from_soup(self, soup: BeautifulSoup, keyword: str) -> List[Dict]:
        """
        Extract job information from BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object
            keyword: Search keyword
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        # Generic job extraction (works for many sites)
        job_elements = soup.find_all(['div', 'article', 'li'], class_=lambda x: x and any(
            term in x.lower() for term in ['job', 'result', 'posting', 'listing']
        ))
        
        for element in job_elements[:10]:  # Limit to first 10 jobs
            try:
                # Extract title
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=lambda x: x and 'title' in x.lower())
                if not title_elem:
                    title_elem = element.find('a')
                
                title = title_elem.get_text(strip=True) if title_elem else f"Job related to {keyword}"
                
                # Extract company
                company_elem = element.find(['span', 'div', 'p'], class_=lambda x: x and 'company' in x.lower())
                company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
                
                # Extract location
                location_elem = element.find(['span', 'div', 'p'], class_=lambda x: x and any(
                    term in x.lower() for term in ['location', 'city', 'address']
                ))
                location = location_elem.get_text(strip=True) if location_elem else "Canada"
                
                # Extract URL
                link_elem = element.find('a', href=True)
                url = link_elem['href'] if link_elem else ""
                if url and not url.startswith('http'):
                    url = urljoin("https://ca.indeed.com", url)
                
                # Create job dictionary
                job = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'url': url,
                    'summary': f"Job posting for {title} at {company}",
                    'keywords': [keyword],
                    'scraped_date': datetime.now().isoformat(),
                    'source': 'basic_fallback_scraper'
                }
                
                jobs.append(job)
                
            except Exception as e:
                console.print(f"[yellow]Error extracting job: {e}[/yellow]")
                continue
        
        return jobs
    
    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """
        Remove duplicate jobs based on title and company.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of unique job dictionaries
        """
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = (job.get('title', '').lower(), job.get('company', '').lower())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs


class EmergencyCSVScraper(BaseJobScraper):
    """
    Emergency CSV import scraper.
    Allows manual job import via CSV files when all other methods fail.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)
        self.csv_dir = Path("emergency_jobs")
        self.csv_dir.mkdir(exist_ok=True)
    
    def scrape_jobs(self, keywords: List[str]) -> List[Dict]:
        """
        Import jobs from CSV files.
        
        Args:
            keywords: List of keywords (used for filtering)
            
        Returns:
            List of job dictionaries from CSV files
        """
        console.print("[red]🚨 Using emergency CSV import scraper...[/red]")
        console.print(f"[yellow]Looking for CSV files in: {self.csv_dir}[/yellow]")
        
        all_jobs = []
        
        # Look for CSV files in the emergency directory
        csv_files = list(self.csv_dir.glob("*.csv"))
        
        if not csv_files:
            console.print("[red]No CSV files found in emergency_jobs directory[/red]")
            console.print("[yellow]To use this fallback:[/yellow]")
            console.print(f"[yellow]1. Create CSV files in: {self.csv_dir}[/yellow]")
            console.print("[yellow]2. Include columns: title, company, location, url, summary[/yellow]")
            
            # Create a sample CSV file
            self._create_sample_csv()
            return []
        
        # Import jobs from CSV files
        for csv_file in csv_files:
            try:
                jobs = self._import_jobs_from_csv(csv_file, keywords)
                all_jobs.extend(jobs)
                console.print(f"[green]Imported {len(jobs)} jobs from {csv_file.name}[/green]")
            except Exception as e:
                console.print(f"[red]Error importing from {csv_file.name}: {e}[/red]")
        
        console.print(f"[green]Emergency CSV scraper imported {len(all_jobs)} total jobs[/green]")
        return all_jobs
    
    def _import_jobs_from_csv(self, csv_file: Path, keywords: List[str]) -> List[Dict]:
        """
        Import jobs from a single CSV file.
        
        Args:
            csv_file: Path to CSV file
            keywords: List of keywords for filtering
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Filter by keywords if specified
                if keywords:
                    title_text = row.get('title', '').lower()
                    summary_text = row.get('summary', '').lower()
                    
                    if not any(keyword.lower() in title_text or keyword.lower() in summary_text 
                              for keyword in keywords):
                        continue
                
                # Create job dictionary
                job = {
                    'title': row.get('title', 'Unknown Title'),
                    'company': row.get('company', 'Unknown Company'),
                    'location': row.get('location', 'Unknown Location'),
                    'url': row.get('url', ''),
                    'summary': row.get('summary', 'No summary available'),
                    'keywords': keywords,
                    'scraped_date': datetime.now().isoformat(),
                    'source': f'emergency_csv_{csv_file.stem}'
                }
                
                jobs.append(job)
        
        return jobs
    
    def _create_sample_csv(self):
        """Create a sample CSV file for user reference."""
        sample_file = self.csv_dir / "sample_jobs.csv"
        
        sample_data = [
            {
                'title': 'Data Analyst',
                'company': 'Sample Company',
                'location': 'Toronto, ON',
                'url': 'https://example.com/job1',
                'summary': 'Looking for a data analyst with Python and SQL skills.'
            },
            {
                'title': 'Software Developer',
                'company': 'Tech Corp',
                'location': 'Vancouver, BC',
                'url': 'https://example.com/job2',
                'summary': 'Full-stack developer position with React and Node.js.'
            }
        ]
        
        with open(sample_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'company', 'location', 'url', 'summary'])
            writer.writeheader()
            writer.writerows(sample_data)
        
        console.print(f"[green]Created sample CSV file: {sample_file}[/green]")
