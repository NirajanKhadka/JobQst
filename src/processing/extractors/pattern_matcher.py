"""
Pattern Matcher

Contains regex patterns and matching logic for extracting job data
from text content with hierarchical confidence levels.
"""

import re
import logging
from typing import Dict, List, NamedTuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ExtractionConfidence(Enum):
    """Confidence levels for extraction results."""

    VERY_HIGH = 0.95  # Web-validated or multiple pattern matches
    HIGH = 0.85  # Single high-confidence pattern match
    MEDIUM = 0.70  # Medium-confidence pattern or validated format
    LOW = 0.50  # Low-confidence pattern or fallback
    VERY_LOW = 0.25  # Unreliable extraction


class PatternMatch(NamedTuple):
    """Represents a pattern match with metadata."""

    value: str
    confidence: float
    pattern_type: str
    source_location: str


class JobPatternMatcher:
    """Hierarchical pattern matcher for job data extraction."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._init_patterns()

    def _init_patterns(self):
        """Initialize all pattern hierarchies."""
        self._init_title_patterns()
        self._init_company_patterns()
        self._init_location_patterns()
        self._init_salary_patterns()
        self._init_experience_patterns()
        self._init_employment_patterns()
        self._init_skills_patterns()

    def _init_title_patterns(self):
        """Initialize hierarchical job title patterns."""
        self.title_patterns = {}
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
        self._compile_patterns("title", raw_patterns)

    def _init_company_patterns(self):
        """Initialize hierarchical company patterns."""
        self.company_patterns = {}
        raw_patterns = {
            "very_high": [
                r'(?i)company[_\s]*name[:\s]*["\']([^"\']{2,50})["\']',
                r'<span[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)</span>',
                r'data-testid="company"[^>]*>([^<]+)<',
            ],
            "high": [
                r"(?i)company[:\s]+([A-Z][a-zA-Z\s&.,\-()]{2,50})(?=\s*\n|\s*$|\s*Location|\s*Salary)",
                r"(?i)employer[:\s]+([A-Z][a-zA-Z\s&.,\-()]{2,50})(?=\s*\n|\s*$|\s*Location|\s*Salary)",
                r"(?i)at\s+([A-Z][a-zA-Z\s&.,\-()]{2,50})\s*(?:\n|$)",
            ],
            "medium": [
                r"([A-Z][a-zA-Z\s&.,\-()]{2,50})\s+(?:Inc|LLC|Corp|Corporation|Ltd|Limited|Company|Co\.)",
                r"([A-Z][a-zA-Z\s&.,\-()]{2,50})\s+(?:Technologies|Technology|Tech|Solutions|Systems|Services)",
            ],
            "low": [
                r"([A-Z][a-zA-Z\s&.,\-()]{3,40})",
            ],
        }
        self._compile_patterns("company", raw_patterns)

    def _init_location_patterns(self):
        """Initialize location extraction patterns."""
        self.location_patterns = {}
        raw_patterns = {
            "very_high": [
                r'(?i)location[:\s]*["\']([^"\']{3,50})["\']',
                r'(?i)city[:\s]*["\']([^"\']{3,30})["\']',
            ],
            "high": [
                r"([A-Z][a-zA-Z\s\-]+),\s*([A-Z]{2})\b",
                r"([A-Z][a-zA-Z\s\-]+),\s*([A-Z]{2})\s*(?:\d{5})?",
                r"(?i)(Remote|Work from Home|Telecommute|Hybrid)",
            ],
            "medium": [
                r"(?i)location[:\s]+([A-Z][a-zA-Z\s,\-]{3,50})",
                r"(?i)based in[:\s]+([A-Z][a-zA-Z\s,\-]{3,50})",
            ],
            "low": [
                r"\b([A-Z][a-zA-Z\s]{3,25})\b",
            ],
        }
        self._compile_patterns("location", raw_patterns)

    def _init_salary_patterns(self):
        """Initialize salary extraction patterns."""
        self.salary_patterns = {}
        raw_patterns = {
            "very_high": [
                r"(?i)salary[:\s]*\$?([\d,]+)\s*-\s*\$?([\d,]+)",
                r"(?i)compensation[:\s]*\$?([\d,]+)\s*-\s*\$?([\d,]+)",
            ],
            "high": [
                r"\$?([\d,]+)k?\s*-\s*\$?([\d,]+)k?(?:\s*(?:per\s*year|annually|/year))?",
                r"(?i)(?:salary|pay|compensation)[:\s]*\$?([\d,]+)(?:k|,000)?",
            ],
            "medium": [
                r"\$[\d,]+\s*-\s*\$[\d,]+",
                r"[\d,]+k\s*-\s*[\d,]+k",
            ],
        }
        self._compile_patterns("salary", raw_patterns)

    def _init_experience_patterns(self):
        """Initialize experience level patterns."""
        self.experience_patterns = {}
        raw_patterns = {
            "very_high": [
                r'(?i)experience[_\s]*level[:\s]*["\']([^"\']+)["\']',
                r'(?i)seniority[:\s]*["\']([^"\']+)["\']',
            ],
            "high": [
                r"(?i)(Senior|Junior|Entry[_\s]*Level|Mid[_\s]*Level|Lead|Principal|Staff)",
                r"(?i)(\d+)\+?\s*years?\s*(?:of\s*)?experience",
            ],
            "medium": [
                r"(?i)experience[:\s]+([^.\n]{5,30})",
                r"(?i)level[:\s]+([^.\n]{5,20})",
            ],
        }
        self._compile_patterns("experience", raw_patterns)

    def _init_employment_patterns(self):
        """Initialize employment type patterns."""
        self.employment_patterns = {}
        raw_patterns = {
            "very_high": [
                r'(?i)employment[_\s]*type[:\s]*["\']([^"\']+)["\']',
                r'(?i)job[_\s]*type[:\s]*["\']([^"\']+)["\']',
            ],
            "high": [
                r"(?i)(Full[_\s]*time|Part[_\s]*time|Contract|Temporary|Permanent|Freelance)",
                r"(?i)employment[:\s]+([^.\n]{5,20})",
            ],
        }
        self._compile_patterns("employment", raw_patterns)

    def _init_skills_patterns(self):
        """Initialize skills extraction patterns."""
        self.skills_patterns = {}
        raw_patterns = {
            "very_high": [
                r"(?i)(?:required\s*)?(?:skills|technologies|tech\s*stack)[:\s]*([^.\n]{10,200})",
                r"(?i)technical\s*requirements[:\s]*([^.\n]{10,200})",
            ],
            "high": [
                r"(?i)experience\s*(?:with|in)[:\s]*([^.\n]{10,100})",
                r"(?i)proficiency\s*(?:with|in)[:\s]*([^.\n]{10,100})",
            ],
        }
        self._compile_patterns("skills", raw_patterns)

    def _compile_patterns(self, pattern_type: str, raw_patterns: Dict[str, List[str]]):
        """Compile regex patterns for performance."""
        compiled_patterns = {}
        for level, patterns in raw_patterns.items():
            compiled_patterns[level] = [
                re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns
            ]
        setattr(self, f"{pattern_type}_patterns", compiled_patterns)

    def extract_with_patterns(self, content: str, pattern_type: str) -> List[PatternMatch]:
        """Extract data using specified pattern type."""
        patterns = getattr(self, f"{pattern_type}_patterns", {})
        candidates = []

        # Try patterns in order of confidence
        for confidence_level, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = pattern.findall(content)
                for match in matches:
                    if isinstance(match, tuple):
                        # Handle tuple matches (e.g., city, state)
                        if len(match) == 2:
                            value = f"{match[0].strip()}, {match[1].strip()}"
                        else:
                            value = " ".join(match).strip()
                    else:
                        value = match.strip()

                    if value and len(value) > 1:
                        confidence_enum = ExtractionConfidence[confidence_level.upper()]
                        candidates.append(
                            PatternMatch(
                                value=value,
                                confidence=confidence_enum.value,
                                pattern_type=confidence_level,
                                source_location="content",
                            )
                        )

        return candidates

    def get_best_match(self, candidates: List[PatternMatch]) -> Optional[PatternMatch]:
        """Get the best match from candidates based on confidence."""
        if not candidates:
            return None
        return max(candidates, key=lambda x: x.confidence)

    def parse_skills_from_text(self, skills_text: str) -> List[str]:
        """Parse individual skills from skills text."""
        skills = set()

        # Split by common delimiters
        skill_candidates = re.split(r"[,;•\n\r]+", skills_text)

        for candidate in skill_candidates:
            candidate = candidate.strip()
            if candidate and len(candidate) > 1:
                skills.add(candidate)

        return list(skills)
