#!/usr/bin/env python3
"""
🚀 Job Content Extractor
Extracts detailed job information from URLs using small, fast local models

This works with your existing scraper workflow:
1. Scraper saves job URLs to database
2. This extractor fetches content from URLs
3. Small models analyze content and fill database fields
4. Updates database with extracted information

Models used:
- TinyLlama 1.1B (fastest)
- Llama3.2 1B (good balance)
- Llama3.2 3B (best accuracy)
"""

import requests
import sqlite3
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExtractedJobInfo:
    """Extracted job information"""
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    experience_level: Optional[str] = None
    job_type: Optional[str] = None
    skills: List[str] = None
    requirements: List[str] = None
    benefits: List[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    confidence: float = 0.0
    extraction_method: str = "unknown"

class WebContentFetcher:
    """Fetches job content from URLs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def fetch_job_content(self, url: str) -> Optional[str]:
        """Fetch and clean job content from URL"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find job-specific content areas
            job_content = self._extract_job_content(soup)
            
            if job_content:
                return self._clean_text(job_content)
            else:
                # Fallback to body text
                return self._clean_text(soup.get_text())
                
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return None
    
    def _extract_job_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job-specific content using common selectors"""
        
        # Common job content selectors
        selectors = [
            '.job-description',
            '.job-details',
            '.job-content',
            '.posting-content',
            '.description',
            '[class*="job"]',
            '[class*="posting"]',
            '[class*="description"]',
            'main',
            '.content',
            '#content'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                # Take the largest content block
                largest = max(elements, key=lambda x: len(x.get_text()))
                if len(largest.get_text()) > 200:  # Minimum content length
                    return largest.get_text()
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common noise
        text = re.sub(r'(?i)(cookies?|privacy policy|terms of service)', '', text)
        
        # Limit length to reasonable size
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        return text.strip()

class SmallModelAnalyzer:
    """Analyzes job content using small, fast local models"""
    
    def __init__(self, preferred_model: str = "llama3.2:1b"):
        self.preferred_model = preferred_model
        self.fallback_models = ["tinyllama", "llama3.2:3b"]
        self.ollama_url = "http://localhost:11434"
    
    def extract_job_info(self, content: str, url: str = "") -> ExtractedJobInfo:
        """Extract structured job information from content"""
        
        # Try models in order of preference
        models_to_try = [self.preferred_model] + self.fallback_models
        
        for model in models_to_try:
            try:
                result = self._analyze_with_model(content, model)
                if result and result.confidence > 0.3:
                    result.extraction_method = f"{model}_success"
                    return result
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                continue
        
        # Fallback to basic extraction
        return self._basic_extraction(content, url)
    
    def _analyze_with_model(self, content: str, model: str) -> Optional[ExtractedJobInfo]:
        """Analyze content using specific model"""
        
        prompt = self._create_extraction_prompt(content)
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "num_predict": 500
                    }
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result_text = response.json().get("response", "")
                return self._parse_model_response(result_text, model)
            
        except Exception as e:
            logger.error(f"Error calling model {model}: {e}")
            
        return None
    
    def _create_extraction_prompt(self, content: str) -> str:
        """Create extraction prompt for model"""
        
        # Truncate content if too long
        if len(content) > 3000:
            content = content[:3000] + "..."
        
        return f"""Extract job information from this job posting and format as JSON:

JOB POSTING CONTENT:
{content}

Extract the following information and return ONLY valid JSON:
{{
    "title": "job title",
    "company": "company name",
    "location": "location",
    "salary": "salary range if mentioned",
    "experience_level": "entry/junior/mid/senior/lead/executive",
    "job_type": "full-time/part-time/contract/internship",
    "skills": ["skill1", "skill2", "skill3"],
    "requirements": ["requirement1", "requirement2"],
    "benefits": ["benefit1", "benefit2"],
    "summary": "brief job summary",
    "confidence": 0.8
}}

Return ONLY the JSON object, no other text."""
    
    def _parse_model_response(self, response: str, model: str) -> Optional[ExtractedJobInfo]:
        """Parse model response into structured data"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                return ExtractedJobInfo(
                    title=data.get('title'),
                    company=data.get('company'),
                    location=data.get('location'),
                    salary=data.get('salary'),
                    experience_level=data.get('experience_level'),
                    job_type=data.get('job_type'),
                    skills=data.get('skills', []),
                    requirements=data.get('requirements', []),
                    benefits=data.get('benefits', []),
                    summary=data.get('summary'),
                    confidence=data.get('confidence', 0.5),
                    extraction_method=model
                )
            
        except Exception as e:
            logger.error(f"Error parsing model response: {e}")
            
        return None
    
    def _basic_extraction(self, content: str, url: str) -> ExtractedJobInfo:
        """Basic extraction using regex patterns"""
        
        info = ExtractedJobInfo()
        info.extraction_method = "basic_regex"
        info.confidence = 0.3
        
        # Extract title
        title_patterns = [
            r'(?i)job\s*title[:\s]+([^\n]+)',
            r'(?i)position[:\s]+([^\n]+)',
            r'(?i)<title[^>]*>([^<]+)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content)
            if match:
                info.title = match.group(1).strip()
                break
        
        # Extract company
        company_patterns = [
            r'(?i)company[:\s]+([^\n]+)',
            r'(?i)employer[:\s]+([^\n]+)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, content)
            if match:
                info.company = match.group(1).strip()
                break
        
        # Extract location
        location_patterns = [
            r'(?i)location[:\s]+([^\n]+)',
            r'(?i)(toronto|vancouver|calgary|montreal|ottawa|edmonton|winnipeg)[,\s]*([a-z]{2})',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content)
            if match:
                info.location = match.group(0).strip()
                break
        
        # Extract experience level
        exp_patterns = [
            r'(?i)(entry[\s-]level|junior|senior|lead|executive|intern)',
            r'(?i)(\d+[\s-]*years?[\s-]*experience)',
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, content)
            if match:
                exp_text = match.group(1).lower()
                if 'entry' in exp_text or 'junior' in exp_text or 'intern' in exp_text:
                    info.experience_level = 'entry'
                elif 'senior' in exp_text:
                    info.experience_level = 'senior'
                elif 'lead' in exp_text or 'executive' in exp_text:
                    info.experience_level = 'lead'
                else:
                    info.experience_level = 'mid'
                break
        
        # Extract basic skills
        skill_keywords = [
            'python', 'sql', 'javascript', 'java', 'react', 'angular', 'vue',
            'node.js', 'django', 'flask', 'pandas', 'numpy', 'scikit-learn',
            'machine learning', 'data analysis', 'power bi', 'tableau',
            'excel', 'aws', 'azure', 'docker', 'kubernetes'
        ]
        
        found_skills = []
        content_lower = content.lower()
        for skill in skill_keywords:
            if skill.lower() in content_lower:
                found_skills.append(skill)
        
        info.skills = found_skills[:10]  # Limit to top 10
        
        return info

class JobDatabaseUpdater:
    """Updates job database with extracted information"""
    
    def __init__(self, db_path: str = "data/jobs.db"):
        self.db_path = db_path
    
    def get_jobs_needing_extraction(self, limit: int = 10) -> List[Tuple[int, str]]:
        """Get jobs that need content extraction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find jobs with URLs but missing detailed info
            cursor.execute("""
                SELECT id, url FROM jobs 
                WHERE url IS NOT NULL 
                AND url != ''
                AND (description IS NULL OR description = '' OR length(description) < 100)
                LIMIT ?
            """, (limit,))
            
            jobs = cursor.fetchall()
            conn.close()
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error getting jobs from database: {e}")
            return []
    
    def update_job_info(self, job_id: int, extracted_info: ExtractedJobInfo) -> bool:
        """Update job with extracted information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prepare update data
            update_fields = []
            update_values = []
            
            if extracted_info.title:
                update_fields.append("title = ?")
                update_values.append(extracted_info.title)
            
            if extracted_info.company:
                update_fields.append("company = ?")
                update_values.append(extracted_info.company)
            
            if extracted_info.location:
                update_fields.append("location = ?")
                update_values.append(extracted_info.location)
            
            if extracted_info.salary:
                update_fields.append("salary = ?")
                update_values.append(extracted_info.salary)
            
            if extracted_info.experience_level:
                update_fields.append("experience_level = ?")
                update_values.append(extracted_info.experience_level)
            
            if extracted_info.job_type:
                update_fields.append("job_type = ?")
                update_values.append(extracted_info.job_type)
            
            if extracted_info.summary:
                update_fields.append("summary = ?")
                update_values.append(extracted_info.summary)
            
            if extracted_info.skills:
                update_fields.append("skills = ?")
                update_values.append(json.dumps(extracted_info.skills))
            
            if extracted_info.requirements:
                update_fields.append("requirements = ?")
                update_values.append(json.dumps(extracted_info.requirements))
            
            if extracted_info.benefits:
                update_fields.append("benefits = ?")
                update_values.append(json.dumps(extracted_info.benefits))
            
            # Add metadata
            update_fields.extend([
                "extraction_confidence = ?",
                "extraction_method = ?",
                "last_updated = datetime('now')"
            ])
            update_values.extend([
                extracted_info.confidence,
                extracted_info.extraction_method
            ])
            
            # Add job_id for WHERE clause
            update_values.append(job_id)
            
            # Build and execute update query
            if update_fields:
                query = f"UPDATE jobs SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, update_values)
                conn.commit()
                
                success = cursor.rowcount > 0
                conn.close()
                return success
            
            conn.close()
            return False
            
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            return False

class JobContentExtractor:
    """Main job content extraction system"""
    
    def __init__(self, db_path: str = "data/jobs.db", model: str = "llama3.2:1b"):
        self.fetcher = WebContentFetcher()
        self.analyzer = SmallModelAnalyzer(model)
        self.updater = JobDatabaseUpdater(db_path)
    
    def process_jobs(self, max_jobs: int = 10, delay: float = 2.0) -> Dict[str, int]:
        """Process jobs and extract content"""
        
        logger.info(f"Starting job content extraction for up to {max_jobs} jobs")
        
        stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # Get jobs needing extraction
        jobs_to_process = self.updater.get_jobs_needing_extraction(max_jobs)
        
        if not jobs_to_process:
            logger.info("No jobs found that need content extraction")
            return stats
        
        logger.info(f"Found {len(jobs_to_process)} jobs to process")
        
        for job_id, url in jobs_to_process:
            try:
                logger.info(f"Processing job {job_id}: {url}")
                
                # Fetch content
                content = self.fetcher.fetch_job_content(url)
                if not content:
                    logger.warning(f"Could not fetch content for job {job_id}")
                    stats["failed"] += 1
                    continue
                
                # Extract information
                extracted_info = self.analyzer.extract_job_info(content, url)
                
                if extracted_info.confidence < 0.2:
                    logger.warning(f"Low confidence extraction for job {job_id}")
                    stats["skipped"] += 1
                    continue
                
                # Update database
                if self.updater.update_job_info(job_id, extracted_info):
                    logger.info(f"Successfully updated job {job_id}")
                    stats["successful"] += 1
                else:
                    logger.error(f"Failed to update job {job_id}")
                    stats["failed"] += 1
                
                stats["processed"] += 1
                
                # Delay between requests
                if delay > 0:
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}")
                stats["failed"] += 1
        
        logger.info(f"Extraction complete: {stats}")
        return stats
    
    def extract_single_job(self, job_id: int) -> Optional[ExtractedJobInfo]:
        """Extract content for a single job"""
        try:
            # Get job URL
            conn = sqlite3.connect(self.updater.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT url FROM jobs WHERE id = ?", (job_id,))
            result = cursor.fetchone()
            conn.close()
            
            if not result or not result[0]:
                logger.error(f"No URL found for job {job_id}")
                return None
            
            url = result[0]
            
            # Fetch and analyze
            content = self.fetcher.fetch_job_content(url)
            if content:
                return self.analyzer.extract_job_info(content, url)
            
        except Exception as e:
            logger.error(f"Error extracting job {job_id}: {e}")
            
        return None

# CLI function for easy testing
# Main function removed - use module functions directly
