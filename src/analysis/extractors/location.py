"""
Location extraction and standardization.

Handles location extraction with support for city/province patterns,
remote work indicators, and location format standardization.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set

from .base import BaseExtractor, ExtractionConfidence, PatternMatch

logger = logging.getLogger(__name__)


class LocationExtractor(BaseExtractor):
    """Extracts and standardizes location information."""

    def __init__(self):
        """Initialize location extractor with patterns and standard locations."""
        super().__init__()
        self._init_patterns()
        self._init_standard_locations()

    def _init_patterns(self) -> None:
        """Initialize location extraction patterns."""
        self.patterns = {}
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

        for level, patterns in raw_patterns.items():
            self.patterns[level] = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns]

    def _init_standard_locations(self) -> None:
        """Initialize standard location formats."""
        self.standard_locations = {
            # Canadian Cities
            "toronto, on",
            "vancouver, bc",
            "montreal, qc",
            "calgary, ab",
            "ottawa, on",
            "edmonton, ab",
            "winnipeg, mb",
            "quebec city, qc",
            "hamilton, on",
            "kitchener, on",
            "london, on",
            "halifax, ns",
            # US Cities
            "new york, ny",
            "san francisco, ca",
            "seattle, wa",
            "austin, tx",
            "boston, ma",
            "chicago, il",
            "los angeles, ca",
            "denver, co",
            # Remote Options
            "remote",
            "remote - canada",
            "remote - north america",
            "hybrid",
            "work from home",
            "telecommute",
        }

    def extract(self, job_data: Dict[str, Any]) -> Optional[str]:
        """Extract location from job data.

        Args:
            job_data: Dictionary containing job posting data

        Returns:
            Extracted and standardized location or None
        """
        content = self._prepare_content(job_data)
        candidates = []

        # Check job_data first
        if job_data.get("location"):
            location = job_data["location"].strip()
            if self._validate_location(location):
                candidates.append(
                    PatternMatch(
                        value=location,
                        confidence=ExtractionConfidence.HIGH.value,
                        pattern_type="job_data",
                        source_location="job_data",
                    )
                )

        # Extract from content using patterns
        for confidence_level, patterns in self.patterns.items():
            for pattern in patterns:
                matches = pattern.findall(content)
                for match in matches:
                    if isinstance(match, tuple):
                        # Handle city, province/state tuples
                        if len(match) == 2:
                            location = f"{match[0].strip()}, {match[1].strip()}"
                        else:
                            location = " ".join(match).strip()
                    else:
                        location = match.strip()

                    # Validate location
                    if self._validate_location(location):
                        confidence = ExtractionConfidence[confidence_level.upper()].value
                        candidates.append(
                            PatternMatch(
                                value=location,
                                confidence=confidence,
                                pattern_type=confidence_level,
                                source_location="content",
                            )
                        )

        if candidates:
            best = max(candidates, key=lambda x: x.confidence)
            return self._standardize_location(best.value)

        return None

    def _prepare_content(self, job_data: Dict[str, Any]) -> str:
        """Prepare content for extraction."""
        content_parts = []

        for field in ["description", "job_description", "location", "summary"]:
            value = job_data.get(field)
            if value and isinstance(value, str):
                content_parts.append(value)

        return "\n".join(content_parts)

    def _validate_location(self, location: str) -> bool:
        """Validate location format.

        Args:
            location: Location to validate

        Returns:
            True if valid location
        """
        if not location or len(location) < 3:
            return False

        # Check against known locations
        if location.lower() in self.standard_locations:
            return True

        # Check for valid location patterns
        location_patterns = [
            r"^[A-Z][a-zA-Z\s\-]+,\s*[A-Z]{2}$",  # City, Province/State
            r"(?i)^(remote|hybrid|work from home)$",  # Remote work
        ]

        return any(re.match(pattern, location) for pattern in location_patterns)

    def _standardize_location(self, location: str) -> str:
        """Standardize location format.

        Args:
            location: Location to standardize

        Returns:
            Standardized location string
        """
        # Standardize remote work indicators
        if re.search(r"(?i)(remote|work from home|telecommute)", location):
            return "Remote"

        # Standardize city, province format
        match = re.match(r"([^,]+),\s*([A-Z]{2})", location)
        if match:
            return f"{match.group(1).strip()}, {match.group(2).upper()}"

        return location.strip()
