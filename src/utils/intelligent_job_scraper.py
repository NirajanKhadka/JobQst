#!/usr/bin/env python3
"""
🔍 Intelligent Job Scraper
Opens job links and extracts detailed information using smaller, faster models

Features:
- Web scraping with intelligent content extraction
- Fast model analysis (TinyLlama, Phi3, etc.)
- Database enrichment with missing fields
- Retry logic and error handling
- Rate limiting and respectful scraping

Author: AI Assistant
Created: 2025-01-04
"""

import requests
import time
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from functools import lru_cache
import sqlite3
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScrapedJobData:
    """Structured job data from scraping"""
    title: str
    company: str
    location: str
    experience_level: str
    salary_range: str
    job_type: str
    skills_required: List[str]
    qualifications: List[str]
    responsibilities: List[str]
    benefits: List[str]
    full_description: str
    posting_date: str
    application_deadline: str
    remote_policy: str
    confidence_score: float

class WebScraper:
    """Intelligent web scraper for job postings"""
    
    def __init__(self, delay_seconds: float = 2.0):
        """
        Initialize web scraper
        
        Args:
            delay_seconds: Delay between requests to be respectful
        """
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.last_request_time = 0
    
    def _respect_rate_limit(self):
        """Ensure we don't make requests too quickly"""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.delay_seconds:
            time.sleep(self.delay_seconds - time_since_last)
        self.last_request_time = time.time()
    
    def scrape_job_page(self, url: str) -> Optional[str]:
        """
        Scrape job page content
        
        Args:
            url: Job posting URL
            
        Returns:
            HTML content or None if failed
        """
        try:
            self._respect_rate_limit()
            
            logger.info(f"Scraping: {url}")
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to scrape {url}: Status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def extract_text_content(self, html: str) -> str:
        """
        Extract clean text content from HTML
        
        Args:
            html: Raw HTML content
            
        Returns:
            Clean text content
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""

class SmallModelAnalyzer:
    """Analyzes job content using smaller, faster models"""
    
    def __init__(self, model_name: str = "llama3.2:1b"):
        """
        Initialize analyzer with small model
        
        Available small models:
        - llama3.2:1b (1B params - very fast)
        - phi3:3.8b (3.8B params - balanced)
        - tinyllama:1.1b (1.1B params - fastest)
        - gemma2:2b (2B params - efficient)
        """
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434"
        
    def analyze_job_content(self, text_content: str, job_url: str) -> ScrapedJobData:
        """
        Analyze job content and extract structured data
        
        Args:
            text_content: Clean text from job posting
            job_url: Original job URL
            
        Returns:
            Structured job data
        """
        try:
            # Create analysis prompt
            prompt = self._create_extraction_prompt(text_content)
            
            # Get analysis from small model
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
                result = response.json().get("response", "")
                return self._parse_analysis_result(result, text_content, job_url)
            else:
                logger.warning(f"Model analysis failed: {response.status_code}")
                return self._create_fallback_data(text_content, job_url)
                
        except Exception as e:
            logger.error(f"Error in model analysis: {e}")
            return self._create_fallback_data(text_content, job_url)
    
    def _create_extraction_prompt(self, content: str) -> str:
        """Create prompt for job data extraction"""
        # Truncate content if too long (small models have context limits)
        max_content_length = 2000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        return f"""Extract job information from this posting and format as JSON:

JOB POSTING CONTENT:
{content}

Extract the following information and respond with ONLY a JSON object:
{{
    "title": "job title",
    "company": "company name", 
    "location": "job location",
    "experience_level": "entry/mid/senior/executive",
    "salary_range": "salary if mentioned",
    "job_type": "full-time/part-time/contract/internship",
    "skills_required": ["skill1", "skill2", "skill3"],
    "qualifications": ["qualification1", "qualification2"],
    "responsibilities": ["responsibility1", "responsibility2"],
    "benefits": ["benefit1", "benefit2"],
    "remote_policy": "remote/hybrid/onsite/not-specified",
    "posting_date": "date if found",
    "application_deadline": "deadline if found"
}}

Important: Respond with ONLY the JSON object, no other text."""
    
    def _parse_analysis_result(self, result: str, original_content: str, job_url: str) -> ScrapedJobData:
        """Parse model analysis result into structured data"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                return ScrapedJobData(
                    title=data.get("title", "").strip(),
                    company=data.get("company", "").strip(),
                    location=data.get("location", "").strip(),
                    experience_level=data.get("experience_level", "").strip().lower(),
                    salary_range=data.get("salary_range", "").strip(),
                    job_type=data.get("job_type", "").strip().lower(),
                    skills_required=data.get("skills_required", []),
                    qualifications=data.get("qualifications", []),
                    responsibilities=data.get("responsibilities", []),
                    benefits=data.get("benefits", []),
                    full_description=original_content,
                    posting_date=data.get("posting_date", "").strip(),
                    application_deadline=data.get("application_deadline", "").strip(),
                    remote_policy=data.get("remote_policy", "").strip().lower(),
                    confidence_score=0.8  # High confidence for model extraction
                )
            else:
                logger.warning("Could not extract JSON from model response")
                return self._create_fallback_data(original_content, job_url)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return self._create_fallback_data(original_content, job_url)
        except Exception as e:
            logger.error(f"Error parsing analysis result: {e}")
            return self._create_fallback_data(original_content, job_url)
    
    def _create_fallback_data(self, content: str, job_url: str) -> ScrapedJobData:
        """Create fallback data using basic text analysis"""
        try:
            # Basic extraction using regex and keywords
            title = self._extract_title(content)
            company = self._extract_company(content)
            location = self._extract_location(content)
            experience_level = self._extract_experience_level(content)
            skills = self._extract_skills(content)
            
            return ScrapedJobData(
                title=title,
                company=company,
                location=location,
                experience_level=experience_level,
                salary_range="",
                job_type="",
                skills_required=skills,
                qualifications=[],
                responsibilities=[],
                benefits=[],
                full_description=content,
                posting_date="",
                application_deadline="",
                remote_policy="",
                confidence_score=0.3  # Lower confidence for fallback
            )
            
        except Exception as e:
            logger.error(f"Error creating fallback data: {e}")
            return ScrapedJobData(
                title="",
                company="",
                location="",
                experience_level="",
                salary_range="",
                job_type="",
                skills_required=[],
                qualifications=[],
                responsibilities=[],
                benefits=[],
                full_description=content,
                posting_date="",
                application_deadline="",
                remote_policy="",
                confidence_score=0.1
            )
    
    def _extract_title(self, content: str) -> str:
        """Extract job title using basic patterns"""
        content_lower = content.lower()
        
        # Common job title patterns
        title_patterns = [
            r'job title[:\s]+([^\n]{1,80})',
            r'position[:\s]+([^\n]{1,80})',
            r'role[:\s]+([^\n]{1,80})',
            r'^([^\n]{1,80}(?:analyst|engineer|developer|manager|specialist|coordinator))',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content_lower)
            if match:
                return match.group(1).strip()
        
        # Fallback: use first line if it looks like a title
        first_line = content.split('\n')[0].strip()
        if len(first_line) < 100 and any(word in first_line.lower() for word in ['analyst', 'engineer', 'developer', 'manager']):
            return first_line
        
        return ""
    
    def _extract_company(self, content: str) -> str:
        """Extract company name using basic patterns"""
        company_patterns = [
            r'company[:\s]+([^\n]{1,50})',
            r'employer[:\s]+([^\n]{1,50})',
            r'organization[:\s]+([^\n]{1,50})',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, content.lower())
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_location(self, content: str) -> str:
        """Extract location using basic patterns"""
        location_patterns = [
            r'location[:\s]+([^\n]{1,50})',
            r'city[:\s]+([^\n]{1,50})',
            r'([A-Za-z\s]+,\s*[A-Z]{2})',  # City, State format
            r'([A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Za-z]+)',  # City, Province, Country
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_experience_level(self, content: str) -> str:
        """Extract experience level using keywords"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['senior', '5+ years', '5-10 years', 'experienced']):
            return "senior"
        elif any(word in content_lower for word in ['junior', 'entry', 'graduate', '0-2 years', 'new grad']):
            return "entry"
        elif any(word in content_lower for word in ['mid', 'intermediate', '2-5 years', '3-5 years']):
            return "mid"
        elif any(word in content_lower for word in ['executive', 'director', 'vp', 'chief']):
            return "executive"
        
        return ""
    
    def _extract_skills(self, content: str) -> List[str]:
        """Extract skills using keyword matching"""
        content_lower = content.lower()
        
        # Common technical skills
        skills_list = [
            'python', 'java', 'javascript', 'c++', 'c#', 'sql', 'r',
            'machine learning', 'data analysis', 'power bi', 'tableau',
            'excel', 'pandas', 'numpy', 'scikit-learn', 'tensorflow',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'git', 'agile', 'scrum', 'jira', 'confluence'
        ]
        
        found_skills = []
        for skill in skills_list:
            if skill in content_lower:
                found_skills.append(skill)
        
        return found_skills[:10]  # Limit to top 10 skills

class IntelligentJobScraper:
    """Main class combining web scraping and AI analysis"""
    
    def __init__(self, model_name: str = "llama3.2:1b", delay_seconds: float = 2.0):
        """
        Initialize intelligent job scraper
        
        Args:
            model_name: Small model to use for analysis
            delay_seconds: Delay between requests
        """
        self.scraper = WebScraper(delay_seconds)
        self.analyzer = SmallModelAnalyzer(model_name)
        self.db_path = Path("jobs.db")
        
    def scrape_and_analyze_job(self, job_url: str) -> Optional[ScrapedJobData]:
        """
        Scrape job URL and analyze content
        
        Args:
            job_url: URL of job posting
            
        Returns:
            Structured job data or None if failed
        """
        try:
            # Scrape the job page
            html_content = self.scraper.scrape_job_page(job_url)
            if not html_content:
                logger.warning(f"Failed to scrape content from {job_url}")
                return None
            
            # Extract text content
            text_content = self.scraper.extract_text_content(html_content)
            if not text_content or len(text_content) < 100:
                logger.warning(f"Insufficient content extracted from {job_url}")
                return None
            
            # Analyze with AI model
            job_data = self.analyzer.analyze_job_content(text_content, job_url)
            
            logger.info(f"Successfully analyzed job: {job_data.title} at {job_data.company}")
            return job_data
            
        except Exception as e:
            logger.error(f"Error scraping and analyzing {job_url}: {e}")
            return None
    
    def enrich_database_jobs(self, batch_size: int = 5) -> Dict[str, int]:
        """
        Enrich existing database jobs with detailed information
        
        Args:
            batch_size: Number of jobs to process at once
            
        Returns:
            Statistics about processing
        """
        stats = {
            "processed": 0,
            "enriched": 0,
            "failed": 0,
            "skipped": 0
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get jobs that need enrichment (missing detailed info)
            cursor.execute("""
                SELECT id, url, title, company 
                FROM jobs 
                WHERE url IS NOT NULL 
                AND url != '' 
                AND (experience_level IS NULL OR experience_level = '')
                LIMIT ?
            """, (batch_size,))
            
            jobs_to_process = cursor.fetchall()
            
            logger.info(f"Found {len(jobs_to_process)} jobs to enrich")
            
            for job_id, url, title, company in jobs_to_process:
                stats["processed"] += 1
                
                logger.info(f"Processing job {job_id}: {title} at {company}")
                
                # Scrape and analyze
                job_data = self.scrape_and_analyze_job(url)
                
                if job_data and job_data.confidence_score > 0.2:
                    # Update database with enriched data
                    self._update_job_in_database(cursor, job_id, job_data)
                    stats["enriched"] += 1
                    logger.info(f"✅ Enriched job {job_id}")
                else:
                    stats["failed"] += 1
                    logger.warning(f"❌ Failed to enrich job {job_id}")
                
                # Commit after each job to avoid losing progress
                conn.commit()
            
            conn.close()
            
            logger.info(f"Enrichment complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error enriching database: {e}")
            return stats
    
    def _update_job_in_database(self, cursor, job_id: int, job_data: ScrapedJobData):
        """Update job record in database with enriched data"""
        try:
            cursor.execute("""
                UPDATE jobs SET
                    experience_level = ?,
                    salary_range = ?,
                    job_type = ?,
                    skills_required = ?,
                    qualifications = ?,
                    responsibilities = ?,
                    benefits = ?,
                    full_description = ?,
                    posting_date = ?,
                    application_deadline = ?,
                    remote_policy = ?,
                    confidence_score = ?,
                    enrichment_date = datetime('now')
                WHERE id = ?
            """, (
                job_data.experience_level,
                job_data.salary_range,
                job_data.job_type,
                json.dumps(job_data.skills_required),
                json.dumps(job_data.qualifications),
                json.dumps(job_data.responsibilities),
                json.dumps(job_data.benefits),
                job_data.full_description,
                job_data.posting_date,
                job_data.application_deadline,
                job_data.remote_policy,
                job_data.confidence_score,
                job_id
            ))
            
        except Exception as e:
            logger.error(f"Error updating job {job_id} in database: {e}")

def setup_small_models():
    """Download and setup small models for fast analysis"""
    models_to_install = [
        "llama3.2:1b",  # 1B params - very fast
        "phi3:3.8b",    # 3.8B params - balanced
        "tinyllama:1.1b",  # 1.1B params - fastest
        "gemma2:2b"     # 2B params - efficient
    ]
    
    import subprocess
    
    for model in models_to_install:
        try:
            print(f"📥 Installing {model}...")
            result = subprocess.run(['ollama', 'pull', model], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {model} installed successfully")
            else:
                print(f"❌ Failed to install {model}: {result.stderr}")
        except Exception as e:
            print(f"❌ Error installing {model}: {e}")

if __name__ == "__main__":
    # Test the intelligent scraper
    scraper = IntelligentJobScraper(model_name="llama3.2:1b")
    
    # Test URL (replace with actual job URL)
    test_url = "https://example.com/job-posting"
    
    print("🚀 Testing Intelligent Job Scraper")
    print("=" * 50)
    
    job_data = scraper.scrape_and_analyze_job(test_url)
    
    if job_data:
        print(f"✅ Successfully scraped job data:")
        print(f"📋 Title: {job_data.title}")
        print(f"🏢 Company: {job_data.company}")
        print(f"📍 Location: {job_data.location}")
        print(f"🎯 Experience Level: {job_data.experience_level}")
        print(f"💼 Job Type: {job_data.job_type}")
        print(f"🛠️ Skills: {', '.join(job_data.skills_required)}")
        print(f"📊 Confidence: {job_data.confidence_score:.2f}")
    else:
        print("❌ Failed to scrape job data")
    
    # Test database enrichment
    print("\n🔄 Testing database enrichment...")
    stats = scraper.enrich_database_jobs(batch_size=2)
    print(f"📊 Enrichment stats: {stats}")
