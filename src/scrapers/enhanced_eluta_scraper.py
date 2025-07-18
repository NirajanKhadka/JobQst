#!/usr/bin/env python3
"""
🚀 Enhanced Eluta Scraper with AI Content Extraction
Advanced CLI options + Small model integration for intelligent job analysis

Features:
- Flexible CLI options (days, pages, job limits)
- AI-powered content extraction using small models  
- Automatic database field filling
- Expert-level prompt engineering
"""

import asyncio
import argparse
import time
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel
from playwright.async_api import async_playwright
import requests
from bs4 import BeautifulSoup

from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile
from src.ats.ats_utils import detect_ats_system
from src.core.job_filters import filter_entry_level_jobs, remove_duplicates

console = Console()


class AIJobContentExtractor:
    """AI-powered job content extractor using small models"""
    
    def __init__(self, model_name: str = "llama3.2:1b"):
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434"
        self.extraction_cache = {}
        
    def extract_job_content(self, url: str, existing_job_data: Dict) -> Dict:
        """Extract detailed job content from URL using AI"""
        try:
            # Step 1: Scrape web content
            web_content = self._scrape_web_content(url)
            if not web_content:
                console.print(f"[red]❌ Could not scrape content from {url[:50]}[/red]")
                return existing_job_data
                
            # Step 2: Use AI to extract structured data
            extracted_data = self._ai_extract_job_details(web_content, existing_job_data)
            
            # Step 3: Merge with existing data
            enhanced_job = {**existing_job_data, **extracted_data}
            enhanced_job["content_extracted_at"] = datetime.now().isoformat()
            enhanced_job["extraction_model"] = self.model_name
            
            console.print(f"[green]✅ Enhanced job with AI extraction[/green]")
            return enhanced_job
            
        except Exception as e:
            console.print(f"[red]❌ Error in AI extraction: {e}[/red]")
            return existing_job_data
    
    def _scrape_web_content(self, url: str) -> Optional[str]:
        """Scrape clean text content from job URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit content size for AI processing
            return text[:5000] if text else None
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Web scraping failed: {e}[/yellow]")
            return None
    
    def _ai_extract_job_details(self, web_content: str, existing_data: Dict) -> Dict:
        """Use AI to extract structured job details from web content"""
        try:
            prompt = self._create_expert_extraction_prompt(web_content, existing_data)
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                ai_response = response.json().get("response", "")
                return self._parse_ai_response(ai_response)
            else:
                console.print(f"[red]❌ AI model request failed: {response.status_code}[/red]")
                return {}
                
        except Exception as e:
            console.print(f"[red]❌ AI extraction failed: {e}[/red]")
            return {}
    
    def _create_expert_extraction_prompt(self, content: str, existing_data: Dict) -> str:
        """Create expert-level prompt for job data extraction"""
        return f"""You are an expert job data extraction AI. Analyze the following job posting content and extract structured information.

EXISTING DATA:
Title: {existing_data.get('title', 'Unknown')}
Company: {existing_data.get('company', 'Unknown')}
Location: {existing_data.get('location', 'Unknown')}

JOB POSTING CONTENT:
{content}

EXTRACTION INSTRUCTIONS:
Extract the following information with high accuracy. Use "Unknown" if information is not found.

1. EXPERIENCE LEVEL: Determine from requirements (entry/junior/mid/senior/executive)
2. SKILLS: Extract all technical skills, tools, programming languages, software
3. REQUIREMENTS: Extract key qualifications and requirements
4. SALARY: Extract salary/wage information if mentioned
5. JOB TYPE: Extract employment type (full-time/part-time/contract/remote/hybrid/onsite)
6. EDUCATION: Extract education requirements
7. DESCRIPTION: Extract a clean, comprehensive job description (max 500 words)
8. BENEFITS: Extract benefits, perks, or additional compensation
9. DEPARTMENT: Extract department/team information
10. POSTING DATE: Extract when the job was posted

FORMAT YOUR RESPONSE EXACTLY AS JSON:
{{
  "experience_level": "entry|junior|mid|senior|executive",
  "skills": ["skill1", "skill2", "skill3"],
  "requirements": ["req1", "req2", "req3"],
  "salary": "salary information or Unknown",
  "job_type": "full-time|part-time|contract|remote|hybrid|onsite",
  "education": "education requirements or Unknown",
  "description": "comprehensive job description",
  "benefits": "benefits information or Unknown",
  "department": "department/team or Unknown",
  "posting_date": "posting date or Unknown"
}}

IMPORTANT: 
- Return ONLY the JSON, no additional text
- Be precise with experience level classification
- Extract ALL relevant skills mentioned
- Keep descriptions factual and comprehensive"""

    def _parse_ai_response(self, response: str) -> Dict:
        """Parse AI response into structured data"""
        try:
            # Clean response and extract JSON
            response = response.strip()
            
            # Find JSON in response
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx + 1]
                parsed_data = json.loads(json_str)
                
                # Validate and clean data
                cleaned_data = {}
                
                # Experience level validation
                valid_levels = ["entry", "junior", "mid", "senior", "executive", "unknown"]
                exp_level = parsed_data.get("experience_level", "unknown").lower()
                cleaned_data["experience_level"] = exp_level if exp_level in valid_levels else "unknown"
                
                # Skills (convert to comma-separated string for database)
                skills = parsed_data.get("skills", [])
                if isinstance(skills, list):
                    cleaned_data["extracted_skills"] = ", ".join(skills)
                else:
                    cleaned_data["extracted_skills"] = str(skills)
                
                # Requirements (convert to comma-separated string)
                requirements = parsed_data.get("requirements", [])
                if isinstance(requirements, list):
                    cleaned_data["requirements"] = "; ".join(requirements)
                else:
                    cleaned_data["requirements"] = str(requirements)
                
                # Direct mappings
                cleaned_data["salary"] = parsed_data.get("salary", "Unknown")
                cleaned_data["job_type"] = parsed_data.get("job_type", "Unknown")
                cleaned_data["education"] = parsed_data.get("education", "Unknown")
                cleaned_data["description"] = parsed_data.get("description", "")[:1000]  # Limit length
                cleaned_data["benefits"] = parsed_data.get("benefits", "Unknown")
                cleaned_data["department"] = parsed_data.get("department", "Unknown")
                cleaned_data["posting_date"] = parsed_data.get("posting_date", "Unknown")
                
                return cleaned_data
                
            else:
                console.print(f"[red]❌ No valid JSON found in AI response[/red]")
                return {}
                
        except json.JSONDecodeError as e:
            console.print(f"[red]❌ JSON parsing error: {e}[/red]")
            return {}
        except Exception as e:
            console.print(f"[red]❌ Response parsing error: {e}[/red]")
            return {}


class EnhancedElutaScraper:
    """Enhanced Eluta scraper with AI content extraction and flexible CLI options"""

    def __init__(self, profile_name: str = "Nirajan", ai_model: str = "llama3.2:1b"):
        """Initialize the enhanced scraper"""
        self.profile_name = profile_name
        self.profile = load_profile(profile_name)
        self.db = get_job_db(profile_name)
        
        # Initialize AI extractor
        self.ai_extractor = AIJobContentExtractor(ai_model)

        # Get search terms from profile
        self.keywords = self.profile.get("keywords", [])
        self.skills = self.profile.get("skills", [])
        all_terms = set(self.keywords + self.skills)
        self.search_terms = list(all_terms)

        console.print(f"[cyan]📋 Loaded {len(self.search_terms)} search terms[/cyan]")
        console.print(f"[cyan]🤖 Using AI model: {ai_model}[/cyan]")

        # Base configuration
        self.base_url = "https://www.eluta.ca/search"
        
        # Default settings (will be overridden by CLI)
        self.max_pages_per_keyword = 3
        self.max_jobs_per_keyword = 20
        self.days_posted = 14
        self.delay_between_requests = 1

        # Results tracking
        self.all_jobs = []
        self.processed_urls = set()
        self.stats = {
            "keywords_processed": 0,
            "pages_scraped": 0,
            "jobs_found": 0,
            "jobs_enhanced": 0,
            "ai_extractions": 0,
            "database_saves": 0,
        }

    async def scrape_with_options(
        self,
        days: int = 14,
        pages_per_keyword: int = 3,
        max_jobs_per_keyword: int = 20,
        keywords_limit: Optional[int] = None,
        enable_ai_extraction: bool = True
    ) -> List[Dict]:
        """
        Scrape jobs with flexible options
        
        Args:
            days: Number of days to look back (7, 14, 30)
            pages_per_keyword: Max pages to scrape per keyword (1-10)
            max_jobs_per_keyword: Max jobs to collect per keyword (10-100)
            keywords_limit: Limit number of keywords to process (for testing)
            enable_ai_extraction: Whether to use AI for content extraction
        """
        
        # Update settings
        self.days_posted = days
        self.max_pages_per_keyword = pages_per_keyword
        self.max_jobs_per_keyword = max_jobs_per_keyword
        
        # Limit keywords if specified
        search_terms = self.search_terms[:keywords_limit] if keywords_limit else self.search_terms
        
        console.print(Panel.fit("🚀 ENHANCED ELUTA SCRAPING", style="bold blue"))
        console.print(f"[cyan]📅 Last {days} days[/cyan]")
        console.print(f"[cyan]📄 {pages_per_keyword} pages per keyword[/cyan]")
        console.print(f"[cyan]🎯 {max_jobs_per_keyword} jobs per keyword[/cyan]")
        console.print(f"[cyan]🔤 {len(search_terms)} keywords{' (limited)' if keywords_limit else ''}[/cyan]")
        console.print(f"[cyan]🤖 AI extraction: {'✅ Enabled' if enable_ai_extraction else '❌ Disabled'}[/cyan]")
        
        expected_pages = len(search_terms) * pages_per_keyword
        console.print(f"[yellow]📊 Expected: ~{expected_pages} pages, ~{len(search_terms) * max_jobs_per_keyword} jobs[/yellow]")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()

            try:
                with Progress() as progress:
                    main_task = progress.add_task("[green]Scraping keywords...", total=len(search_terms))

                    for i, keyword in enumerate(search_terms, 1):
                        console.print(f"\n[bold]🔍 Processing {i}/{len(search_terms)}: {keyword}[/bold]")
                        
                        keyword_jobs = await self._scrape_keyword_enhanced(
                            page, keyword, progress, enable_ai_extraction
                        )
                        
                        self.all_jobs.extend(keyword_jobs)
                        self.stats["keywords_processed"] += 1
                        progress.update(main_task, advance=1)
                        
                        await asyncio.sleep(self.delay_between_requests)

                # Remove duplicates and filter
                unique_jobs = remove_duplicates(self.all_jobs)
                filtered_jobs = filter_entry_level_jobs(unique_jobs)
                
                self._display_enhanced_results(filtered_jobs)
                await self._save_jobs_to_database(filtered_jobs)
                
                return filtered_jobs

            finally:
                console.print("\n[yellow]⏸️ Press Enter to close browser...[/yellow]")
                input()
                await context.close()
                await browser.close()

    async def _scrape_keyword_enhanced(
        self, page, keyword: str, progress: Progress, enable_ai: bool
    ) -> List[Dict]:
        """Enhanced keyword scraping with AI content extraction"""
        keyword_jobs = []
        jobs_collected = 0

        for page_num in range(1, self.max_pages_per_keyword + 1):
            if jobs_collected >= self.max_jobs_per_keyword:
                break

            # Build search URL
            search_url = f"{self.base_url}?q={keyword}&l=&posted={self.days_posted}&pg={page_num}"

            try:
                console.print(f"[cyan]📄 Page {page_num}: {search_url}[/cyan]")
                await page.goto(search_url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)

                # Check for jobs
                job_elements = await page.query_selector_all(".organic-job")
                if not job_elements:
                    console.print(f"[yellow]⚠️ No jobs found on page {page_num}[/yellow]")
                    break

                console.print(f"[green]✅ Found {len(job_elements)} jobs on page {page_num}[/green]")

                # Process each job
                for i, job_element in enumerate(job_elements):
                    if jobs_collected >= self.max_jobs_per_keyword:
                        break

                    try:
                        # Extract basic job data
                        job_data = await self._extract_job_data_enhanced(
                            page, job_element, i + 1, page_num
                        )
                        
                        if job_data:
                            job_data["search_keyword"] = keyword
                            job_data["page_number"] = page_num
                            
                            # AI enhancement if enabled and we have a valid URL
                            if enable_ai and job_data.get("apply_url") and "eluta.ca" not in job_data["apply_url"]:
                                console.print(f"[blue]🤖 Enhancing job {i+1} with AI...[/blue]")
                                enhanced_job = self.ai_extractor.extract_job_content(
                                    job_data["apply_url"], job_data
                                )
                                if enhanced_job != job_data:
                                    self.stats["ai_extractions"] += 1
                                    job_data = enhanced_job
                                    console.print(f"[green]✨ Job enhanced with AI[/green]")
                            
                            keyword_jobs.append(job_data)
                            self.stats["jobs_found"] += 1
                            jobs_collected += 1

                    except Exception as e:
                        console.print(f"[red]❌ Error processing job {i+1}: {e}[/red]")
                        continue

                self.stats["pages_scraped"] += 1
                console.print(f"[cyan]📊 Page {page_num}: {len([j for j in keyword_jobs if j.get('page_number') == page_num])} jobs collected[/cyan]")

                await self._cleanup_extra_tabs(page.context)
                await asyncio.sleep(self.delay_between_requests)

            except Exception as e:
                console.print(f"[red]❌ Error scraping page {page_num}: {e}[/red]")
                break

        console.print(f"[green]✅ Keyword '{keyword}' complete: {jobs_collected} jobs[/green]")
        return keyword_jobs

    async def _extract_job_data_enhanced(
        self, page, job_element, job_number: int, page_num: int = 1
    ) -> Dict:
        """Enhanced job data extraction"""
        try:
            job_text = await job_element.inner_text()
            lines = [line.strip() for line in job_text.split("\n") if line.strip()]

            if len(lines) < 2:
                return {}

            # Initialize enhanced job data structure
            job_data = {
                "title": lines[0] if lines else "",
                "company": "",
                "location": "",
                "salary": "Unknown",
                "description": "",
                "url": "",
                "apply_url": "",
                "source": "eluta.ca",
                "scraped_date": datetime.now().isoformat(),
                "ats_system": "Unknown",
                "scraped_successfully": False,
                
                # Enhanced fields for AI extraction
                "experience_level": "Unknown",
                "extracted_skills": "",
                "requirements": "",
                "job_type": "Unknown", 
                "education": "Unknown",
                "benefits": "Unknown",
                "department": "Unknown",
                "posting_date": "Unknown",
                "content_extracted_at": "",
                "extraction_model": "",
            }

            # Parse basic info
            if len(lines) > 1:
                company_line = lines[1]
                job_data["company"] = company_line.replace("TOP EMPLOYER", "").strip()

            if len(lines) > 2:
                job_data["location"] = lines[2]

            if len(lines) > 3:
                description_lines = lines[3:]
                job_data["description"] = " ".join(description_lines)[:500] + "..."

            # Get application URL
            job_url = await self._get_real_job_url_enhanced(job_element, page, job_number)
            if job_url:
                job_data["apply_url"] = job_url
                job_data["url"] = job_url
                job_data["scraped_successfully"] = True
                job_data["ats_system"] = detect_ats_system(job_url)

            return job_data

        except Exception as e:
            console.print(f"[red]❌ Error extracting job data: {e}[/red]")
            return {}

    async def _get_real_job_url_enhanced(self, job_elem, page, job_number):
        """Enhanced URL extraction with better error handling"""
        try:
            links = await job_elem.query_selector_all("a")
            
            for i, link in enumerate(links):
                href = await link.get_attribute("href")
                
                if href and not any(skip in href for skip in ["/search?", "q=", "pg=", "posted="]):
                    # Direct external URL
                    if href.startswith("http") and "eluta.ca" not in href:
                        console.print(f"[green]🔗 Direct URL found: {href[:60]}[/green]")
                        return href
                    
                    # Eluta redirect URL
                    if href.startswith("/redirect") or "redirect" in href:
                        if href.startswith("/"):
                            full_url = "https://www.eluta.ca" + href
                        else:
                            full_url = href
                        console.print(f"[blue]🔀 Redirect URL: {full_url[:60]}[/blue]")
                        return full_url

            # Fallback to popup method
            if links:
                console.print(f"[yellow]⚠️ Using popup fallback for job {job_number}[/yellow]")
                try:
                    async with page.expect_popup() as popup_info:
                        await links[0].click()
                        await asyncio.sleep(2)
                    popup = await popup_info.value
                    await popup.wait_for_load_state()
                    real_url = popup.url
                    await popup.close()
                    return real_url
                except:
                    pass

            return ""

        except Exception as e:
            console.print(f"[red]❌ URL extraction error for job {job_number}: {e}[/red]")
            return ""

    async def _cleanup_extra_tabs(self, context) -> None:
        """Clean up extra browser tabs"""
        try:
            pages = context.pages
            if len(pages) > 1:
                for page in pages[1:]:
                    if not page.is_closed():
                        await page.close()
        except Exception as e:
            console.print(f"[dim]⚠️ Tab cleanup warning: {e}[/dim]")

    def _display_enhanced_results(self, jobs: List[Dict]) -> None:
        """Display enhanced scraping results"""
        console.print("\n" + "=" * 80)
        console.print(Panel.fit("🎉 ENHANCED SCRAPING RESULTS", style="bold green"))

        # Enhanced statistics table
        stats_table = Table(title="📊 Scraping Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="green")

        stats_table.add_row("🔤 Keywords Processed", str(self.stats["keywords_processed"]))
        stats_table.add_row("📄 Pages Scraped", str(self.stats["pages_scraped"]))
        stats_table.add_row("🎯 Jobs Found", str(self.stats["jobs_found"]))
        stats_table.add_row("🤖 AI Extractions", str(self.stats["ai_extractions"]))
        stats_table.add_row("💾 Database Saves", str(self.stats["database_saves"]))
        stats_table.add_row("✨ Final Unique Jobs", str(len(jobs)))

        console.print(stats_table)

        # Enhanced jobs sample
        if jobs:
            console.print(f"\n[bold]🎯 Sample Enhanced Jobs:[/bold]")
            sample_table = Table()
            sample_table.add_column("Title", style="green", max_width=25)
            sample_table.add_column("Company", style="cyan", max_width=20)
            sample_table.add_column("Level", style="yellow", max_width=10)
            sample_table.add_column("Skills", style="blue", max_width=25)
            sample_table.add_column("AI Enhanced", style="magenta", max_width=10)

            for job in jobs[:8]:
                enhanced = "✅" if job.get("extraction_model") else "❌"
                skills = job.get("extracted_skills", "Unknown")[:22] + "..." if len(job.get("extracted_skills", "")) > 25 else job.get("extracted_skills", "Unknown")
                
                sample_table.add_row(
                    job.get("title", "Unknown")[:22] + "..." if len(job.get("title", "")) > 25 else job.get("title", "Unknown"),
                    job.get("company", "Unknown")[:17] + "..." if len(job.get("company", "")) > 20 else job.get("company", "Unknown"),
                    job.get("experience_level", "Unknown"),
                    skills,
                    enhanced
                )

            console.print(sample_table)

    async def _save_jobs_to_database(self, jobs: List[Dict]) -> None:
        """Save enhanced jobs to database"""
        if not jobs:
            return
            
        console.print(f"\n[cyan]💾 Saving {len(jobs)} jobs to database...[/cyan]")
        saved_count = 0
        
        for job in jobs:
            try:
                self.db.add_job(job)
                saved_count += 1
                self.stats["database_saves"] += 1
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not save job: {e}[/yellow]")

        console.print(f"[green]✅ Saved {saved_count} enhanced jobs to database[/green]")


def create_cli_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="🚀 Enhanced Eluta Scraper with AI Content Extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick test (7 days, 2 pages, 10 jobs, 5 keywords)
  python enhanced_eluta_scraper.py --days 7 --pages 2 --jobs 10 --keywords 5

  # Moderate scrape (14 days, 3 pages, 20 jobs per keyword)
  python enhanced_eluta_scraper.py --days 14 --pages 3 --jobs 20

  # Comprehensive scrape (30 days, 5 pages, 50 jobs per keyword)
  python enhanced_eluta_scraper.py --days 30 --pages 5 --jobs 50

  # Fast scrape without AI (for bulk collection)
  python enhanced_eluta_scraper.py --days 14 --pages 3 --no-ai

  # Use different AI model
  python enhanced_eluta_scraper.py --model tinyllama:1.1b
        """
    )
    
    parser.add_argument(
        "--days", 
        type=int, 
        default=14, 
        choices=[7, 14, 30],
        help="Number of days to look back (7, 14, or 30)"
    )
    
    parser.add_argument(
        "--pages", 
        type=int, 
        default=3, 
        choices=range(1, 11),
        metavar="1-10",
        help="Max pages to scrape per keyword (1-10)"
    )
    
    parser.add_argument(
        "--jobs", 
        type=int, 
        default=20, 
        choices=range(5, 101),
        metavar="5-100",
        help="Max jobs to collect per keyword (5-100)"
    )
    
    parser.add_argument(
        "--keywords", 
        type=int, 
        default=None,
        help="Limit number of keywords to process (for testing)"
    )
    
    parser.add_argument(
        "--profile", 
        type=str, 
        default="Nirajan",
        help="Profile name to use for search terms"
    )
    
    parser.add_argument(
        "--model", 
        type=str, 
        default="llama3.2:1b",
        choices=["llama3.2:1b", "tinyllama:1.1b", "llama3.2:3b"],
        help="AI model for content extraction"
    )
    
    parser.add_argument(
        "--no-ai", 
        action="store_true",
        help="Disable AI content extraction (faster scraping)"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Run quick test (7 days, 1 page, 5 jobs, 3 keywords)"
    )
    
    return parser


async def main():
    """Main function with CLI argument parsing"""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Test mode override
    if args.test:
        args.days = 7
        args.pages = 1
        args.jobs = 5
        args.keywords = 3
        console.print("[yellow]🧪 TEST MODE: Limited scraping for quick testing[/yellow]")
    
    # Display configuration
    console.print(Panel.fit("🚀 ENHANCED ELUTA SCRAPER", style="bold blue"))
    console.print(f"[cyan]📅 Days: {args.days}[/cyan]")
    console.print(f"[cyan]📄 Pages per keyword: {args.pages}[/cyan]")
    console.print(f"[cyan]🎯 Jobs per keyword: {args.jobs}[/cyan]")
    console.print(f"[cyan]🔤 Keywords limit: {args.keywords or 'All'}[/cyan]")
    console.print(f"[cyan]👤 Profile: {args.profile}[/cyan]")
    console.print(f"[cyan]🤖 AI Model: {args.model}[/cyan]")
    console.print(f"[cyan]🚀 AI Extraction: {'❌ Disabled' if args.no_ai else '✅ Enabled'}[/cyan]")
    
    if not args.test:
        response = input("\n⚡ Start scraping? (y/N): ")
        if response.lower() != 'y':
            console.print("[yellow]❌ Scraping cancelled[/yellow]")
            return
    
    # Initialize and run scraper
    scraper = EnhancedElutaScraper(args.profile, args.model)
    
    jobs = await scraper.scrape_with_options(
        days=args.days,
        pages_per_keyword=args.pages,
        max_jobs_per_keyword=args.jobs,
        keywords_limit=args.keywords,
        enable_ai_extraction=not args.no_ai
    )
    
    console.print(f"\n[bold green]🎉 Scraping complete! Found {len(jobs)} enhanced jobs.[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
