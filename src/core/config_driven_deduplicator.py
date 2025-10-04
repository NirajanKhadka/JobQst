"""
Config-Driven Smart Deduplication System
Uses validation_config.json for all thresholds and matching rules.

Key Improvements:
- Loads thresholds from validation_config.json
- Configurable similarity rules for title/company/location
- Support for multiple matching strategies
- Performance optimized with O(1) lookups where possible
- Replaces hardcoded thresholds in smart_deduplication.py
"""

import re
import hashlib
import logging
from typing import List, Dict, Set, Tuple, Any, Optional
from difflib import SequenceMatcher
from urllib.parse import urlparse
import time

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class ConfigDrivenJobDeduplicator:
    """
    Config-driven job deduplication system
    
    Features:
    - Loads all thresholds from validation_config.json
    - Configurable similarity rules
    - Multiple matching strategies
    - Performance optimized
    - Replaces hardcoded smart_deduplication.py
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize config-driven deduplicator
        
        Args:
            config_dir: Path to config directory (auto-detected if not provided)
        """
        start_time = time.time()
        
        # Initialize config loader
        self.config_loader = ConfigLoader(config_dir)
        
        # Load configurations
        self._load_configurations()
        
        # Initialize tracking sets
        self.processed_hashes: Set[str] = set()
        self.processed_urls: Set[str] = set()
        self.title_company_pairs: Set[str] = set()
        
        init_time = (time.time() - start_time) * 1000
        title_threshold = self.thresholds.get('title', 0.85)
        company_threshold = self.thresholds.get('company', 0.90)
        logger.info(
            f"ConfigDrivenJobDeduplicator initialized in {init_time:.2f}ms "
            f"(thresholds: title={title_threshold:.0%}, "
            f"company={company_threshold:.0%})"
        )

    def _load_configurations(self):
        """Load validation configuration"""
        self.validation_config = self.config_loader.load_config("validation_config.json")
        
        # Extract deduplication thresholds
        dedup_config = self.validation_config.get("deduplication_thresholds", {})
        
        # Extract threshold values (handling nested structure)
        title_config = dedup_config.get("title_similarity", {})
        company_config = dedup_config.get("company_similarity", {})
        desc_config = dedup_config.get("description_similarity", {})
        
        self.thresholds = {
            "title": title_config.get("threshold", 0.85) if isinstance(title_config, dict) else 0.85,
            "company": company_config.get("threshold", 0.90) if isinstance(company_config, dict) else 0.90,
            "location": 0.80,  # Default, not in config
            "description": desc_config.get("threshold", 0.75) if isinstance(desc_config, dict) else 0.75,
            "overall": dedup_config.get("fuzzy_match_min", 0.75)
        }
        
        # Extract matching strategies
        matching_strategies = self.validation_config.get("matching_strategies", {})
        
        self.strategies = {
            "exact_url": matching_strategies.get("exact_url_match", True),
            "signature": matching_strategies.get("job_signature_match", True),
            "title_company": matching_strategies.get("title_company_pair", True),
            "fuzzy": matching_strategies.get("fuzzy_similarity", True),
            "domain": matching_strategies.get("same_domain_check", False)
        }
        
        # Extract normalization rules
        url_validation = self.validation_config.get("url_validation", {})
        
        self.normalization_rules = {
            "remove_www": url_validation.get("remove_www", True),
            "lowercase": True,
            "remove_whitespace": True,
            "remove_special_chars": False
        }
        
        logger.debug(
            f"Deduplication config loaded: "
            f"{len(self.thresholds)} thresholds, "
            f"{sum(self.strategies.values())} active strategies"
        )

    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison
        
        Args:
            text: Text to normalize
        
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()
        
        # Remove common variations
        text = re.sub(r"\b(jr|sr|senior|junior|lead|principal)\b", "", text)
        text = re.sub(r"\b(i|ii|iii|iv|v)\b", "", text)  # Roman numerals
        text = re.sub(r"\([^)]*\)", "", text)  # Remove parentheses content
        text = re.sub(r"\s*[-–—]\s*", " ", text)  # Normalize dashes
        
        # Remove extra spaces again
        text = re.sub(r"\s+", " ", text).strip()
        
        return text

    def normalize_company(self, company: str) -> str:
        """
        Normalize company name for comparison
        
        Args:
            company: Company name to normalize
        
        Returns:
            Normalized company name
        """
        if not company:
            return ""
        
        company = self.normalize_text(company)
        
        # Remove common company suffixes
        suffixes = [
            r"\b(inc|incorporated|corp|corporation|ltd|limited|llc|co|company)\b",
            r"\b(technologies|technology|tech|solutions|systems|services)\b",
            r"\b(group|international|global|worldwide)\b",
        ]
        
        for suffix in suffixes:
            company = re.sub(suffix, "", company)
        
        return company.strip()

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        
        if norm1 == norm2:
            return 1.0
        
        # Use sequence matcher for similarity
        return SequenceMatcher(None, norm1, norm2).ratio()

    def extract_domain(self, url: str) -> str:
        """
        Extract domain from URL
        
        Args:
            url: URL string
        
        Returns:
            Domain string
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www prefix if configured
            if self.normalization_rules["remove_www"]:
                domain = re.sub(r"^www\.", "", domain)
            
            return domain
        except (ValueError, AttributeError) as e:
            logger.debug(f"URL parse failed: {e}")
            return ""

    def generate_job_signature(self, job: Dict[str, Any]) -> str:
        """
        Generate a unique signature for a job
        
        Args:
            job: Job dictionary
        
        Returns:
            MD5 hash signature
        """
        title = self.normalize_text(job.get("title", ""))
        company = self.normalize_company(job.get("company", ""))
        location = self.normalize_text(job.get("location", ""))
        
        # Create signature from normalized fields
        signature = f"{title}|{company}|{location}"
        return hashlib.md5(signature.encode()).hexdigest()

    def is_duplicate_job(
        self,
        job: Dict[str, Any],
        existing_jobs: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Check if job is a duplicate of existing jobs
        
        Uses configurable matching strategies from validation_config.json
        
        Args:
            job: Job to check
            existing_jobs: List of existing jobs
        
        Returns:
            Tuple of (is_duplicate, reason)
        """
        job_url = job.get("url", "")
        job_title = job.get("title", "")
        job_company = job.get("company", "")
        job_location = job.get("location", "")
        
        # Strategy 1: Exact URL match
        if self.strategies["exact_url"] and job_url:
            if job_url in self.processed_urls:
                return True, "Exact URL match"
        
        # Strategy 2: Job signature match
        if self.strategies["signature"]:
            job_signature = self.generate_job_signature(job)
            if job_signature in self.processed_hashes:
                return True, "Job signature match"
        
        # Strategy 3: Title-Company pair match
        if self.strategies["title_company"]:
            title_company_key = (
                f"{self.normalize_text(job_title)}|"
                f"{self.normalize_company(job_company)}"
            )
            if title_company_key in self.title_company_pairs:
                return True, "Title-Company pair match"
        
        # Strategy 4: Fuzzy similarity checks
        if self.strategies["fuzzy"]:
            for existing_job in existing_jobs:
                # Skip if same URL (already checked above)
                if job_url and job_url == existing_job.get("url", ""):
                    continue
                
                # Calculate similarities
                title_sim = self.calculate_text_similarity(
                    job_title, existing_job.get("title", "")
                )
                company_sim = self.calculate_text_similarity(
                    job_company, existing_job.get("company", "")
                )
                location_sim = self.calculate_text_similarity(
                    job_location, existing_job.get("location", "")
                )
                
                # Check if similarities exceed thresholds
                if (
                    title_sim >= self.thresholds["title"]
                    and company_sim >= self.thresholds["company"]
                    and location_sim >= self.thresholds["location"]
                ):
                    return True, (
                        f"High similarity match "
                        f"(title: {title_sim:.0%}, "
                        f"company: {company_sim:.0%}, "
                        f"location: {location_sim:.0%})"
                    )
                
                # Check overall threshold
                overall_sim = (
                    title_sim * 0.5 + company_sim * 0.3 + location_sim * 0.2
                )
                if overall_sim >= self.thresholds["overall"]:
                    return True, f"Overall similarity match ({overall_sim:.0%})"
        
        # Strategy 5: Same domain check (if enabled)
        if self.strategies["domain"] and job_url:
            job_domain = self.extract_domain(job_url)
            for existing_job in existing_jobs:
                existing_url = existing_job.get("url", "")
                if existing_url:
                    existing_domain = self.extract_domain(existing_url)
                    if job_domain and job_domain == existing_domain:
                        # Same domain - check title similarity
                        title_sim = self.calculate_text_similarity(
                            job_title, existing_job.get("title", "")
                        )
                        if title_sim >= 0.90:
                            return True, "Same domain + high title similarity"
        
        # Not a duplicate
        return False, ""

    def add_job(self, job: Dict[str, Any]):
        """
        Add job to tracking sets
        
        Args:
            job: Job dictionary to add
        """
        # Add URL
        job_url = job.get("url", "")
        if job_url:
            self.processed_urls.add(job_url)
        
        # Add signature
        job_signature = self.generate_job_signature(job)
        self.processed_hashes.add(job_signature)
        
        # Add title-company pair
        job_title = job.get("title", "")
        job_company = job.get("company", "")
        title_company_key = (
            f"{self.normalize_text(job_title)}|"
            f"{self.normalize_company(job_company)}"
        )
        self.title_company_pairs.add(title_company_key)

    def deduplicate_jobs(
        self,
        jobs: List[Dict[str, Any]],
        verbose: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Deduplicate a list of jobs
        
        Args:
            jobs: List of job dictionaries
            verbose: Whether to print progress
        
        Returns:
            Tuple of (unique_jobs, stats)
        """
        unique_jobs = []
        stats = {
            "total": len(jobs),
            "duplicates": 0,
            "unique": 0,
            "url_match": 0,
            "signature_match": 0,
            "title_company_match": 0,
            "fuzzy_match": 0,
            "domain_match": 0
        }
        
        for i, job in enumerate(jobs, 1):
            is_dup, reason = self.is_duplicate_job(job, unique_jobs)
            
            if is_dup:
                stats["duplicates"] += 1
                
                # Track reason
                if "URL" in reason:
                    stats["url_match"] += 1
                elif "signature" in reason:
                    stats["signature_match"] += 1
                elif "Title-Company" in reason:
                    stats["title_company_match"] += 1
                elif "similarity" in reason:
                    stats["fuzzy_match"] += 1
                elif "domain" in reason:
                    stats["domain_match"] += 1
                
                if verbose:
                    logger.debug(f"Duplicate #{i}: {reason} - {job.get('title', '')}")
            else:
                unique_jobs.append(job)
                self.add_job(job)
                stats["unique"] += 1
        
        return unique_jobs, stats

    def clear_tracking(self):
        """Clear all tracking sets"""
        self.processed_hashes.clear()
        self.processed_urls.clear()
        self.title_company_pairs.clear()
        logger.debug("Deduplicator tracking cleared")


# Convenience function
def create_deduplicator(config_dir: Optional[str] = None) -> ConfigDrivenJobDeduplicator:
    """
    Create a config-driven deduplicator instance
    
    Args:
        config_dir: Optional path to config directory
    
    Returns:
        ConfigDrivenJobDeduplicator instance
    """
    return ConfigDrivenJobDeduplicator(config_dir)


if __name__ == "__main__":
    # Test the config-driven deduplicator
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Config-Driven Job Deduplicator...")
    
    dedup = create_deduplicator()
    
    print(f"\nThresholds:")
    for key, value in dedup.thresholds.items():
        print(f"  {key}: {value:.0%}")
    
    print(f"\nActive Strategies:")
    for key, value in dedup.strategies.items():
        print(f"  {key}: {'✓' if value else '✗'}")
    
    # Test cases
    test_jobs = [
        {
            "title": "Senior Software Engineer",
            "company": "Tech Corp Inc.",
            "location": "Toronto, ON",
            "url": "https://example.com/job/12345"
        },
        {
            "title": "Senior Software Engineer",  # Exact duplicate
            "company": "Tech Corp Inc.",
            "location": "Toronto, ON",
            "url": "https://example.com/job/12345"
        },
        {
            "title": "Sr. Software Engineer",  # Similar title
            "company": "Tech Corp",  # Similar company
            "location": "Toronto, Ontario",  # Similar location
            "url": "https://example.com/job/67890"
        },
        {
            "title": "Junior Developer",  # Different job
            "company": "Different Company",
            "location": "Vancouver, BC",
            "url": "https://example.com/job/11111"
        },
    ]
    
    print("\n=== Deduplication Test ===")
    unique_jobs, stats = dedup.deduplicate_jobs(test_jobs, verbose=True)
    
    print(f"\nResults:")
    print(f"  Total jobs: {stats['total']}")
    print(f"  Unique jobs: {stats['unique']}")
    print(f"  Duplicates: {stats['duplicates']}")
    print(f"    URL matches: {stats['url_match']}")
    print(f"    Signature matches: {stats['signature_match']}")
    print(f"    Title-Company matches: {stats['title_company_match']}")
    print(f"    Fuzzy matches: {stats['fuzzy_match']}")
    
    print("\n✅ Config-Driven Job Deduplicator is ready!")
