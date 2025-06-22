"""
Base Job Scraper
Provides common functionality for all job site scrapers.
"""

import json
import random
import re
import requests
import time
from abc import ABC, abstractmethod
from typing import Dict, Generator, List, Optional
from rich.console import Console

console = Console()

# Try to import ollama for keyword extraction
OLLAMA_AVAILABLE = False
OLLAMA_MODULE = None

try:
    import ollama
    OLLAMA_MODULE = ollama

    # Test if Ollama is working using HTTP API to avoid SSL issues
    import requests
    response = requests.get("http://localhost:11434/api/tags", timeout=3)
    if response.status_code == 200:
        OLLAMA_AVAILABLE = True
    else:
        console.print("[yellow]Ollama service not responding[/yellow]")
except ImportError:
    console.print("[yellow]Ollama Python package not installed[/yellow]")
except requests.exceptions.RequestException:
    console.print("[yellow]Ollama service not running[/yellow]")
except Exception as e:
    console.print(f"[yellow]Ollama not available: {e}[/yellow]")


class BaseJobScraper(ABC):
    """
    Base class for all job site scrapers.
    Provides common functionality and defines the interface.
    """
    
    def __init__(self, profile: Dict, *, browser_context=None, start: int = 0):
        """
        Initialize the scraper with profile and settings.
        
        Args:
            profile: User profile dictionary with search parameters
            browser_context: Optional Playwright browser context
            start: Starting index for pagination
        """
        self.profile = profile
        self.current_index = start
        self.browser_context = browser_context
        self.keywords = profile.get("keywords", [])
        self.location = profile.get("location", "")
        self.ollama_model = profile.get("ollama_model", "mistral:7b")
        
        # Extract city from location for better search results
        self.city = self.location.split(",")[0].strip() if self.location else ""
        
        # Convert keywords list to search string - use ALL keywords as user requested
        if isinstance(self.keywords, list):
            self.search_terms = " ".join(self.keywords)
        else:
            self.search_terms = str(self.keywords)
        
        # Site-specific settings (to be overridden by subclasses)
        self.site_name = "Unknown"
        self.base_url = ""
        self.requires_browser = False
        self.rate_limit_delay = (1.5, 3.0)  # Min, max delay between requests
    
    @abstractmethod
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """
        Scrape jobs from the job site.
        Must be implemented by subclasses.
        
        Yields:
            Job dictionaries with standardized fields
        """
        pass
    
    def batched(self, batch_size: int) -> Generator[List[Dict], None, None]:
        """
        Generate batches of jobs with the specified batch size.
        
        Args:
            batch_size: Number of jobs to include in each batch
            
        Yields:
            List of job dictionaries in each batch
        """
        batch = []
        
        try:
            for job in self.scrape_jobs():
                # Extract keywords using Ollama
                try:
                    job = self.extract_keywords(job)
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to extract keywords: {e}[/yellow]")
                
                batch.append(job)
                
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
                    
                    # Add delay between batches
                    delay = random.uniform(*self.rate_limit_delay)
                    time.sleep(delay)
            
            # Yield remaining jobs if any
            if batch:
                yield batch
                
        except Exception as e:
            console.print(f"[bold red]Error in {self.site_name} scraping: {e}[/bold red]")
            if batch:
                yield batch
    
    def normalize_job(self, raw_job: Dict) -> Dict:
        """
        Normalize a raw job dictionary to standard format.

        Args:
            raw_job: Raw job data from site-specific scraping

        Returns:
            Normalized job dictionary
        """
        return {
            "title": raw_job.get("title", "Unknown Title").strip(),
            "company": raw_job.get("company", "Unknown Company").strip(),
            "location": raw_job.get("location", "Unknown Location").strip(),
            "url": raw_job.get("url", "").strip(),
            "apply_url": raw_job.get("apply_url", raw_job.get("url", "")).strip(),  # Use apply_url if available, fallback to url
            "summary": raw_job.get("summary", "").strip(),
            "site": self.site_name,
            "keywords": raw_job.get("keywords", []),
            "salary": raw_job.get("salary", ""),
            "job_type": raw_job.get("job_type", ""),
            "posted_date": raw_job.get("posted_date", ""),
            "company_rating": raw_job.get("company_rating", ""),
        }
    
    def extract_keywords(self, job: Dict) -> Dict:
        """
        Extract keywords from job summary using Ollama or fallback methods.

        Args:
            job: Job dictionary with summary

        Returns:
            Job dictionary with added keywords
        """
        if not job.get("summary"):
            job["keywords"] = []
            return job

        if OLLAMA_AVAILABLE:
            # Retry up to 3 times with Ollama
            for attempt in range(3):
                try:
                    prompt = (
                        "List 8 technical keywords that a resume should contain "
                        "to match this job summary, return a JSON list."
                        "\n==SUMMARY==\n" + job["summary"]
                    )

                    response = OLLAMA_MODULE.generate(
                        model=self.ollama_model.replace(":7b", ""),  # Remove version suffix
                        prompt=prompt,
                        options={
                            "temperature": 0,
                            "num_predict": 120
                        }
                    )

                    # Extract the response text
                    kw_text = response["response"]

                    # Try to parse as JSON
                    try:
                        keywords = json.loads(kw_text)
                        if isinstance(keywords, list):
                            job["keywords"] = keywords
                            return job
                    except json.JSONDecodeError:
                        # If not valid JSON, try to extract keywords using regex
                        matches = re.findall(r'["\'](.*?)["\']', kw_text)
                        if matches:
                            job["keywords"] = matches
                            return job

                    # Fallback: split by commas and clean up
                    keywords = [k.strip(' "\'[]') for k in kw_text.split(',')]
                    job["keywords"] = [k for k in keywords if k]
                    return job

                except Exception as e:
                    console.print(f"[yellow]Attempt {attempt+1} failed to extract keywords: {e}[/yellow]")
                    time.sleep(2)  # Wait before retry

        # Fallback keyword extraction using simple text analysis
        job["keywords"] = self.extract_keywords_fallback(job["summary"])
        return job

    def extract_keywords_fallback(self, summary: str) -> List[str]:
        """
        Fallback method to extract keywords from job summary using simple text analysis.

        Args:
            summary: Job summary text

        Returns:
            List of extracted keywords
        """
        # Common technical keywords to look for
        tech_keywords = [
            "Python", "Java", "JavaScript", "SQL", "Excel", "PowerBI", "Tableau",
            "AWS", "Azure", "Docker", "Kubernetes", "React", "Angular", "Node.js",
            "Machine Learning", "Data Analysis", "Statistics", "R", "MATLAB",
            "Git", "Linux", "Windows", "API", "REST", "JSON", "XML", "HTML", "CSS",
            "Agile", "Scrum", "DevOps", "CI/CD", "Testing", "QA", "Automation",
            "C++", "C#", "PHP", "Ruby", "Go", "Rust", "Swift", "Kotlin",
            "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn",
            "MongoDB", "PostgreSQL", "MySQL", "Redis", "Elasticsearch"
        ]

        # Extract keywords that appear in the summary
        found_keywords = []
        summary_lower = summary.lower()

        for keyword in tech_keywords:
            if keyword.lower() in summary_lower:
                found_keywords.append(keyword)

        # Also extract capitalized words that might be technologies
        words = re.findall(r'\b[A-Z][a-z]+\b', summary)
        for word in words:
            if len(word) > 2 and word not in found_keywords:
                found_keywords.append(word)

        # Limit to 8 keywords
        return found_keywords[:8]
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for requests to avoid being blocked.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    def handle_rate_limiting(self, attempt: int = 1) -> None:
        """
        Handle rate limiting with exponential backoff.
        
        Args:
            attempt: Current attempt number
        """
        delay = min(30, 2 ** attempt + random.uniform(0, 1))
        console.print(f"[yellow]Rate limited on {self.site_name}. Waiting {delay:.1f} seconds...[/yellow]")
        time.sleep(delay)
