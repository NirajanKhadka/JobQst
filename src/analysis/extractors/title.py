"""
Job title extraction and validation.

Handles job title extraction with hierarchical patterns and validation
against industry-standard job titles.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set

from .base import BaseExtractor, ExtractionConfidence, PatternMatch

logger = logging.getLogger(__name__)


class TitleExtractor(BaseExtractor):
    """Extracts and validates job titles."""

    def __init__(self):
        """Initialize title extractor with patterns and standard titles."""
        super().__init__()
        self._init_patterns()
        self._init_standard_titles()

    def _init_patterns(self) -> None:
        """Initialize hierarchical job title patterns."""
        self.patterns = {}
        raw_patterns = {
            "very_high": [
                r"<title>([^<]*(?:Engineer|Developer|Manager|Analyst|Scientist|Designer|Architect)[^<]*)</title>",
                r'(?i)job[_\s]*title[:\s]*["\']([^"\']{5,80})["\']',
                r'(?i)position[_\s]*title[:\s]*["\']([^"\']{5,80})["\']',
            ],
            "high": [
                r"(?i)job\s*title[:\s]+([A-Z][a-zA-Z\s\-,&()]{5,80})(?=\s*\n|\s*$|\s*Company|\s*Location)",
                r"(?i)position[:\s]+([A-Z][a-zA-Z\s\-,&()]{5,80})(?=\s*\n|\s*$|\s*Company|\s*Location)",
                r"(?i)role[:\s]+([A-Z][a-zA-Z\s\-,&()]{5,80})(?=\s*\n|\s*$|\s*Company|\s*Location)",
                r"<h1[^>]*>([^<]*(?:Engineer|Developer|Manager|Analyst)[^<]*)</h1>",
            ],
            "medium": [
                r"(?i)(Senior|Junior|Lead|Principal|Staff)\s+([A-Za-z\s]+(?:Engineer|Developer|Manager|Analyst))",
                r"(?i)^([A-Z][a-zA-Z\s\-,&()]+(?:Engineer|Developer|Manager|Analyst|Specialist))\s*$",
            ],
            "low": [
                r"([A-Z][a-zA-Z\s\-,&()]{10,60})",
            ],
        }

        for level, patterns in raw_patterns.items():
            self.patterns[level] = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns]

    def _init_standard_titles(self) -> None:
        """Initialize standard job titles database."""
        self.standard_titles = {
            # Software Engineering
            "software engineer",
            "senior software engineer",
            "junior software engineer",
            "software developer",
            "senior software developer",
            "junior software developer",
            "full stack developer",
            "frontend developer",
            "backend developer",
            "web developer",
            "mobile developer",
            "ios developer",
            "android developer",
            "devops engineer",
            "site reliability engineer",
            "platform engineer",
            "software architect",
            "technical lead",
            "engineering manager",
            # Data & Analytics
            "data scientist",
            "senior data scientist",
            "data analyst",
            "data engineer",
            "machine learning engineer",
            "ai engineer",
            "research scientist",
            "business analyst",
            "business intelligence analyst",
            "data architect",
            # Product & Design
            "product manager",
            "senior product manager",
            "product owner",
            "ux designer",
            "ui designer",
            "ux/ui designer",
            "product designer",
            "graphic designer",
            "web designer",
            "interaction designer",
            # Management & Leadership
            "engineering manager",
            "technical manager",
            "team lead",
            "tech lead",
            "director of engineering",
            "vp of engineering",
            "cto",
            "head of engineering",
            "project manager",
            "program manager",
            "scrum master",
            # Quality & Testing
            "qa engineer",
            "test engineer",
            "automation engineer",
            "sdet",
            "quality assurance analyst",
            "test automation engineer",
            # Security & Infrastructure
            "security engineer",
            "cybersecurity analyst",
            "information security analyst",
            "network engineer",
            "systems administrator",
            "cloud engineer",
            "infrastructure engineer",
            "database administrator",
        }

    def extract(self, job_data: Dict[str, Any]) -> Optional[str]:
        """Extract job title from job data.

        Args:
            job_data: Dictionary containing job posting data

        Returns:
            Extracted and cleaned job title or None
        """
        content = self._prepare_content(job_data)
        candidates = []

        # First check if title is already in job_data (highest priority)
        if job_data and job_data.get("title"):
            title = job_data["title"].strip()
            if self._validate_title(title):
                candidates.append(
                    PatternMatch(
                        value=title,
                        confidence=ExtractionConfidence.VERY_HIGH.value,
                        pattern_type="job_data",
                        source_location="job_data",
                    )
                )

        # Try patterns in order of confidence as fallback
        for confidence_level, patterns in self.patterns.items():
            for pattern in patterns:
                matches = pattern.findall(content)
                for match in matches:
                    if isinstance(match, tuple):
                        match = " ".join(match).strip()

                    # Clean and validate title
                    cleaned_match = self._clean_title(match)
                    if self._validate_title(cleaned_match):
                        confidence = ExtractionConfidence[confidence_level.upper()].value
                        candidates.append(
                            PatternMatch(
                                value=cleaned_match,
                                confidence=confidence,
                                pattern_type=confidence_level,
                                source_location="content",
                            )
                        )

        # Return best candidate
        if candidates:
            best = max(candidates, key=lambda x: x.confidence)
            return self._clean_title(best.value)

        return None

    def _prepare_content(self, job_data: Dict[str, Any]) -> str:
        """Prepare content for extraction."""
        content_parts = []

        for field in ["description", "job_description", "title", "summary"]:
            value = job_data.get(field)
            if value and isinstance(value, str):
                content_parts.append(value)

        return "\n".join(content_parts)

    def _clean_title(self, title: str) -> str:
        """Clean and normalize job title.

        Args:
            title: Title to clean

        Returns:
            Cleaned title
        """
        if not title:
            return ""

        # Remove newlines and extra whitespace
        cleaned = re.sub(r"\s+", " ", title.strip())

        # Remove common prefixes
        cleaned = re.sub(r"^(Job Title:|Position:|Role:)\s*", "", cleaned, flags=re.IGNORECASE)

        # Remove common noise words
        noise_words = ["company", "location", "salary", "posted", "apply", "job", "opening"]

        # Split by common separators and take the first meaningful part
        parts = re.split(r"[|\-–—\n]", cleaned)
        cleaned = parts[0].strip()

        # Remove noise words from the end
        words = cleaned.split()
        while words and words[-1].lower() in noise_words:
            words.pop()

        # Ensure reasonable length
        result = " ".join(words).strip()
        if len(result) > 80:
            result = result[:80].strip()

        return result

    def _validate_title(self, title: str) -> bool:
        """Validate job title.

        Args:
            title: Title to validate

        Returns:
            True if valid title
        """
        if not title or len(title) < 3 or len(title) > 100:
            return False

        # Check against standard titles
        if title.lower() in self.standard_titles:
            return True

        # Check for job-related keywords
        job_keywords = [
            "engineer",
            "developer",
            "manager",
            "analyst",
            "specialist",
            "coordinator",
            "director",
            "lead",
            "senior",
            "junior",
        ]

        return any(keyword in title.lower() for keyword in job_keywords)
