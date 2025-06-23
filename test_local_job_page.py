#!/usr/bin/env python3
"""
Test script to save a real job page locally and test the analysis pipeline.
This allows us to test job parsing without hitting live websites.
"""

import os
import json
import time
import asyncio
from pathlib import Path
from typing import Optional, Dict
from playwright.async_api import async_playwright
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import tempfile
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime

# Import our analysis modules
from src.utils.job_analyzer import JobAnalyzer
from src.utils.job_data_enhancer import JobDataEnhancer
from src.utils import document_generator
from src.core import utils
from src.ats.enhanced_application_agent import EnhancedApplicationAgent
from src.core.job_database import get_job_db

console = Console()

async def save_job_page_locally(url: str, output_dir: str = "test_data") -> Optional[str]:
    """Save a real job page locally for testing."""
    console.print(f"[blue]🔍 Saving job page from: {url}[/blue]")
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to the job page
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait a bit for dynamic content to load
            await asyncio.sleep(3)
            
            # Get the page content
            page_content = await page.content()
            
            # Generate filename from URL
            filename = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('?', '_').replace('&', '_')
            filename = filename[:100] + '.html'  # Limit length
            filepath = os.path.join(output_dir, filename)
            
            # Save the HTML content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(page_content)
            
            console.print(f"[green]✅ Saved job page to: {filepath}[/green]")
            
            # Also save the URL for reference
            url_file = filepath.replace('.html', '_url.txt')
            with open(url_file, 'w') as f:
                f.write(url)
            
            return filepath
            
        except Exception as e:
            console.print(f"[red]❌ Error saving job page: {e}[/red]")
            return None
        finally:
            await browser.close()

def extract_real_job_data_from_html(html_filepath: str, original_url: str) -> Optional[Dict]:
    """Extract real job data from saved HTML file using BeautifulSoup."""
    console.print(f"[blue]🔍 Extracting real job data from: {html_filepath}[/blue]")
    
    try:
        with open(html_filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract job title
        title = ""
        title_selectors = [
            'h1', 'h2', '.job-title', '.title', '[data-testid="job-title"]',
            '.position-title', '.role-title', 'title'
        ]
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 5:  # Make sure it's not just whitespace
                    break
        
        # Extract company name
        company = ""
        company_selectors = [
            '.company-name', '.company', '.employer', '[data-testid="company-name"]',
            '.organization', '.employer-name'
        ]
        for selector in company_selectors:
            element = soup.select_one(selector)
            if element:
                company = element.get_text(strip=True)
                if company and len(company) > 2:
                    break
        
        # Extract location
        location = ""
        location_selectors = [
            '.location', '.job-location', '[data-testid="location"]',
            '.address', '.job-address'
        ]
        for selector in location_selectors:
            element = soup.select_one(selector)
            if element:
                location = element.get_text(strip=True)
                if location and len(location) > 3:
                    break
        
        # Extract job description/summary
        description = ""
        desc_selectors = [
            '.job-description', '.description', '.job-summary',
            '.job-details', '.content', '.job-content',
            '[data-testid="job-description"]', '.summary'
        ]
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                description = element.get_text(strip=True)
                if description and len(description) > 50:  # Make sure it's substantial
                    break
        
        # If no description found, try to get main content
        if not description:
            main_content = soup.find('main') or soup.find('body')
            if main_content:
                description = main_content.get_text(strip=True)[:1000]  # Limit length
        
        # Generate job ID from URL
        job_id = hashlib.md5(original_url.encode()).hexdigest()[:12]
        
        # Create real job data
        job_data = {
            "job_id": f"real_{job_id}",
            "title": title or "Unknown Position",
            "company_name": company or "Unknown Company",
            "location": location or "Unknown Location",
            "summary": description or "No description available",
            "job_url": original_url,
            "scraped_at": datetime.now().isoformat(),
            "search_keyword": "test",
            "page_number": 1,
            "job_number": 1,
            "session_id": "test_session",
            "raw_text": description or "",
            "job_description": description or ""
        }
        
        console.print(f"[green]✅ Extracted real job data: {title} at {company}[/green]")
        return job_data
        
    except Exception as e:
        console.print(f"[red]❌ Error extracting job data: {e}[/red]")
        return None

def test_job_analysis_with_local_file(html_filepath: str, original_url: str) -> Optional[Dict]:
    """Test the job analysis pipeline using real data extracted from local HTML file."""
    console.print(f"[blue]🧪 Testing job analysis with real data from: {html_filepath}[/blue]")
    
    try:
        # Extract real job data from HTML
        job_data = extract_real_job_data_from_html(html_filepath, original_url)
        if not job_data:
            console.print("[red]❌ Failed to extract real job data[/red]")
            return None
        
        # Test the job analyzer with real data
        analyzer = JobAnalyzer(use_ai=False, profile_name="test_profile")
        analysis_result = analyzer.analyze_job_deep(job_data)
        
        return {
            "analysis": analysis_result,
            "original": job_data
        }
        
    except Exception as e:
        console.print(f"[red]❌ Error in job analysis: {e}[/red]")
        return None

async def test_job_enhancement_with_local_file(html_filepath: str, original_url: str) -> Optional[Dict]:
    """Test the job enhancement pipeline using real data from local HTML file."""
    console.print(f"[blue]🧪 Testing job enhancement with real data from: {html_filepath}[/blue]")
    
    try:
        # Extract real job data from HTML
        job_data = extract_real_job_data_from_html(html_filepath, original_url)
        if not job_data:
            console.print("[red]❌ Failed to extract real job data[/red]")
            return None
        
        # Use real URL for enhancement
        job_data["url"] = original_url
        job_data["id"] = job_data["job_id"]
        
        # Test the job enhancer with real data
        enhancer = JobDataEnhancer(profile_name="test_profile")
        await enhancer.initialize()
        enhanced_job = await enhancer.enhance_job_data(job_data)
        
        return {
            "enhanced": enhanced_job,
            "original": job_data
        }
        
    except Exception as e:
        console.print(f"[red]❌ Error in job enhancement: {e}[/red]")
        return None

def display_results(results: Optional[Dict]):
    """Display the analysis results in a nice format."""
    if not results:
        console.print("[red]❌ No results to display[/red]")
        return
    
    console.print("\n" + "="*80)
    console.print("[bold blue]📊 JOB ANALYSIS RESULTS[/bold blue]")
    console.print("="*80)
    
    # Display analysis results
    if "analysis" in results:
        analysis = results["analysis"]
        console.print("\n[bold green]🔍 Job Analysis:[/bold green]")
        
        table = Table(title="Analysis Results")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in analysis.items():
            if key not in ["raw_text", "job_description", "full_description"]:  # Skip large text fields
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value[:5])  # Limit list display
                table.add_row(key, str(value)[:100])  # Limit display length
        
        console.print(table)
    
    # Display enhanced job data
    if "enhanced" in results:
        enhanced = results["enhanced"]
        console.print("\n[bold green]✨ Enhanced Job Data:[/bold green]")
        
        table = Table(title="Enhanced Data")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        # Display enhanced data fields
        enhanced_fields = [
            "job_id", "job_type", "experience_level", "education_required",
            "salary_info", "application_deadline", "requirements", "benefits",
            "skills_required"
        ]
        
        for field in enhanced_fields:
            if hasattr(enhanced, field):
                value = getattr(enhanced, field)
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value[:3])
                table.add_row(field, str(value)[:100])
        
        console.print(table)

def load_test_profile(profile_name: str = "test_profile") -> dict:
    """Load or create a minimal test profile for document generation and application."""
    profile_path = f"profiles/{profile_name}/{profile_name}.json"
    if os.path.exists(profile_path):
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Minimal fallback profile
    return {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "123-456-7890",
        "skills": ["Python", "Data Analysis", "SQL"],
        "experience": [
            {"title": "Data Analyst", "company": "TestCorp", "years": 1}
        ],
        "education": [
            {"degree": "BSc Computer Science", "school": "Test University"}
        ]
    }

async def main():
    """Main function to run the local job page test."""
    console.print(Panel.fit(
        "[bold blue]🧪 Local Job Page Testing Tool[/bold blue]\n"
        "This tool saves real job pages locally and tests the analysis pipeline.",
        border_style="blue"
    ))
    
    # Example job URLs to test with
    test_urls = [
        "https://www.eluta.ca/jobs-at-rbc/software-developer-toronto-on",
        "https://www.eluta.ca/jobs-at-td-bank/data-analyst-toronto-on",
        "https://jobs.jobvite.com/careers/essencemediacom-na/job/okLjvfwD?__jvst=Job%20Board&__jvsd=LinkedIn",
        # Add more URLs as needed
    ]
    
    for url in test_urls:
        console.print(f"\n[bold yellow]Testing URL: {url}[/bold yellow]")
        
        # Save the job page locally
        html_filepath = await save_job_page_locally(url)
        
        if html_filepath and os.path.exists(html_filepath):
            # Test the analysis pipeline with REAL data
            results = test_job_analysis_with_local_file(html_filepath, url)
            
            # Test the enhancement pipeline with REAL data
            enhanced_results = await test_job_enhancement_with_local_file(html_filepath, url)
            
            # Combine results
            if results and enhanced_results:
                results.update(enhanced_results)
            elif enhanced_results:
                results = enhanced_results
            
            # Display results
            display_results(results)

            # --- Step 3: Generate Resume and Cover Letter ---
            console.print("\n[bold blue]📄 Generating Resume and Cover Letter...[/bold blue]")
            profile = load_test_profile()
            job_for_docs = results.get("analysis") if results and "analysis" in results else (results.get("original") if results else None)
            if job_for_docs:
                # Ensure 'company' key exists for document generation
                if 'company' not in job_for_docs and 'company_name' in job_for_docs:
                    job_for_docs['company'] = job_for_docs['company_name']
                
                # Try document generation, with fallback to simple text files
                try:
                    resume_path, cover_letter_path = document_generator.customize(job_for_docs, profile)
                    console.print(f"[green]✅ Resume saved to: {resume_path}[/green]")
                    console.print(f"[green]✅ Cover letter saved to: {cover_letter_path}[/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠️ Document generation failed: {e}[/yellow]")
                    console.print("[yellow]Creating simple text documents for testing...[/yellow]")
                    
                    # Create simple text documents for testing
                    resume_path = tempfile.mktemp(suffix="_resume.txt")
                    cover_letter_path = tempfile.mktemp(suffix="_cover_letter.txt")
                    
                    with open(resume_path, 'w') as f:
                        f.write(f"Test Resume for {job_for_docs.get('title', 'Job')} at {job_for_docs.get('company', 'Company')}")
                    
                    with open(cover_letter_path, 'w') as f:
                        f.write(f"Test Cover Letter for {job_for_docs.get('title', 'Job')} at {job_for_docs.get('company', 'Company')}")
                    
                    console.print(f"[green]✅ Simple resume saved to: {resume_path}[/green]")
                    console.print(f"[green]✅ Simple cover letter saved to: {cover_letter_path}[/green]")

                # --- Step 4: Attempt Auto-Apply ---
                console.print("\n[bold blue]🚀 Attempting Auto-Apply...[/bold blue]")
                # Insert job into test profile's database for the agent to pick up
                job_db = get_job_db("test_profile")
                job_entry = job_for_docs.copy()
                job_entry["url"] = url  # Use the REAL URL
                job_entry["company"] = job_entry.get("company_name", "Unknown")
                job_entry["applied"] = False
                job_db.add_job(job_entry)
                # Run the application agent for this job
                agent = EnhancedApplicationAgent("test_profile")
                await agent.initialize()
                await agent.process_job_applications(limit=1, enhance_jobs=True, modify_documents=True)
            else:
                console.print("[red]❌ No job data for document generation or auto-apply[/red]")
        else:
            console.print("[red]❌ Failed to save or find the job page[/red]")
        
        console.print("\n" + "-"*80)

if __name__ == "__main__":
    asyncio.run(main()) 