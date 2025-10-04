"""
Smart Deduplication System
Advanced job deduplication using multiple similarity metrics.
"""

import re
import hashlib
from typing import List, Dict, Set, Tuple, Any
from difflib import SequenceMatcher
from urllib.parse import urlparse
from rich.console import Console

console = Console()


class SmartJobDeduplicator:
    """Advanced job deduplication with multiple similarity checks."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.processed_hashes: Set[str] = set()
        self.processed_urls: Set[str] = set()
        self.title_company_pairs: Set[str] = set()

    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
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
        """Normalize company name for comparison."""
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
        """Calculate similarity between two text strings."""
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
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www prefix
            domain = re.sub(r"^www\.", "", domain)
            return domain
        except (ValueError, AttributeError) as e:
            logger.debug("URL parse failed: %s", str(e))
            return ""

    def generate_job_signature(self, job: Dict[str, Any]) -> str:
        """Generate a unique signature for a job."""
        title = self.normalize_text(job.get("title", ""))
        company = self.normalize_company(job.get("company", ""))
        location = self.normalize_text(job.get("location", ""))

        # Create signature from normalized fields
        signature = f"{title}|{company}|{location}"
        return hashlib.md5(signature.encode()).hexdigest()

    def is_duplicate_job(
        self, job: Dict[str, Any], existing_jobs: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Check if job is a duplicate of existing jobs.

        Returns:
            Tuple of (is_duplicate, reason)
        """
        job_url = job.get("url", "")
        job_title = job.get("title", "")
        job_company = job.get("company", "")
        job_location = job.get("location", "")

        # 1. Exact URL match
        if job_url and job_url in self.processed_urls:
            return True, "Exact URL match"

        # 2. Job signature match
        job_signature = self.generate_job_signature(job)
        if job_signature in self.processed_hashes:
            return True, "Job signature match"

        # 3. Title-Company pair match
        title_company_key = (
            f"{self.normalize_text(job_title)}|{self.normalize_company(job_company)}"
        )
        if title_company_key in self.title_company_pairs:
            return True, "Title-Company pair match"

        # 4. Advanced similarity checks
        for existing_job in existing_jobs:
            # Skip if same URL (already checked above)
            if job_url and job_url == existing_job.get("url", ""):
                continue

            # Check title similarity
            title_similarity = self.calculate_text_similarity(
                job_title, existing_job.get("title", "")
            )

            # Check company similarity
            company_similarity = self.calculate_text_similarity(
                job_company, existing_job.get("company", "")
            )

            # Check location similarity
            location_similarity = self.calculate_text_similarity(
                job_location, existing_job.get("location", "")
            )

            # If title and company are very similar, likely duplicate
            if title_similarity >= 0.9 and company_similarity >= 0.8:
                return (
                    True,
                    f"High similarity (T:{title_similarity:.2f}, C:{company_similarity:.2f})",
                )

            # If all three are moderately similar, likely duplicate
            if title_similarity >= 0.8 and company_similarity >= 0.7 and location_similarity >= 0.7:
                return True, f"Moderate similarity across all fields"

            # Check for same job at different URLs (common with job boards)
            if title_similarity >= 0.95 and company_similarity >= 0.9:
                job_domain = self.extract_domain(job_url)
                existing_domain = self.extract_domain(existing_job.get("url", ""))

                # Different domains but same job = cross-posted
                if job_domain != existing_domain and job_domain and existing_domain:
                    return True, f"Cross-posted job (domains: {job_domain} vs {existing_domain})"

        return False, "Not a duplicate"

    def add_job_to_tracking(self, job: Dict[str, Any]) -> None:
        """Add job to tracking sets to prevent future duplicates."""
        job_url = job.get("url", "")
        if job_url:
            self.processed_urls.add(job_url)

        job_signature = self.generate_job_signature(job)
        self.processed_hashes.add(job_signature)

        title_company_key = f"{self.normalize_text(job.get('title', ''))}|{self.normalize_company(job.get('company', ''))}"
        self.title_company_pairs.add(title_company_key)

    def deduplicate_job_list(
        self, jobs: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Deduplicate a list of jobs.

        Returns:
            Tuple of (unique_jobs, stats)
        """
        if not jobs:
            return [], {"total": 0, "unique": 0, "duplicates": 0}

        unique_jobs = []
        duplicate_count = 0
        duplicate_reasons = {}

        console.print(f"[cyan]🔍 Smart deduplication: Processing {len(jobs)} jobs...[/cyan]")

        for i, job in enumerate(jobs):
            is_duplicate, reason = self.is_duplicate_job(job, unique_jobs)

            if is_duplicate:
                duplicate_count += 1
                duplicate_reasons[reason] = duplicate_reasons.get(reason, 0) + 1

                # Log duplicate for debugging (first few only)
                if duplicate_count <= 5:
                    title = job.get("title", "Unknown")[:30]
                    company = job.get("company", "Unknown")[:15]
                    console.print(
                        f"[dim]🔄 Duplicate {duplicate_count}: {title}... at {company} ({reason})[/dim]"
                    )
            else:
                unique_jobs.append(job)
                self.add_job_to_tracking(job)

        # Show deduplication summary
        console.print(
            f"[green]✅ Deduplication complete: {len(unique_jobs)} unique, {duplicate_count} duplicates removed[/green]"
        )

        if duplicate_reasons:
            console.print("[cyan]📊 Duplicate reasons:[/cyan]")
            for reason, count in duplicate_reasons.items():
                console.print(f"  • {reason}: {count}")

        stats = {
            "total": len(jobs),
            "unique": len(unique_jobs),
            "duplicates": duplicate_count,
            "duplicate_reasons": duplicate_reasons,
        }

        return unique_jobs, stats

    def get_deduplication_stats(self) -> Dict[str, int]:
        """Get current deduplication tracking stats."""
        return {
            "tracked_urls": len(self.processed_urls),
            "tracked_signatures": len(self.processed_hashes),
            "tracked_title_company_pairs": len(self.title_company_pairs),
        }


def smart_deduplicate_jobs(
    jobs: List[Dict[str, Any]], similarity_threshold: float = 0.85
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience function for smart job deduplication.

    Args:
        jobs: List of job dictionaries
        similarity_threshold: Similarity threshold for duplicate detection

    Returns:
        Tuple of (unique_jobs, deduplication_stats)
    """
    deduplicator = SmartJobDeduplicator(similarity_threshold)
    return deduplicator.deduplicate_job_list(jobs)


def test_deduplication():
    """Test the smart deduplication system."""
    test_jobs = [
        {
            "title": "Python Developer",
            "company": "Tech Corp Inc.",
            "location": "Toronto, ON",
            "url": "https://example.com/job1",
        },
        {
            "title": "Python Developer",  # Exact duplicate
            "company": "Tech Corp Inc.",
            "location": "Toronto, ON",
            "url": "https://example.com/job1",
        },
        {
            "title": "Senior Python Developer",  # Similar but different
            "company": "Tech Corp",
            "location": "Toronto, Ontario",
            "url": "https://different.com/job2",
        },
        {
            "title": "Python Software Engineer",  # Similar title, same company
            "company": "Tech Corp Inc",
            "location": "Toronto, ON",
            "url": "https://another.com/job3",
        },
    ]

    unique_jobs, stats = smart_deduplicate_jobs(test_jobs)

    console.print(f"[bold]Test Results:[/bold]")
    console.print(f"Original jobs: {stats['total']}")
    console.print(f"Unique jobs: {stats['unique']}")
    console.print(f"Duplicates removed: {stats['duplicates']}")


if __name__ == "__main__":
    test_deduplication()
