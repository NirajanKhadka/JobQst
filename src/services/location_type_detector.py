#!/usr/bin/env python3
"""
Location Type Detection Service for JobQst
Automatically detects and categorizes jobs as Remote, Hybrid, or On-site
based on job descriptions, titles, and location information.
"""

import re
import logging
from typing import Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LocationPattern:
    """Pattern for detecting location types."""

    keywords: List[str]
    weight: float
    negative_keywords: List[str] = None


class LocationTypeDetector:
    """Service for detecting job location types."""

    def __init__(self):
        self.remote_patterns = [
            LocationPattern(["remote", "fully remote", "100% remote"], 1.0),
            LocationPattern(["work from home", "wfh"], 0.9),
            LocationPattern(["telecommute", "telework"], 0.8),
            LocationPattern(["distributed team", "remote-first"], 0.9),
            LocationPattern(["anywhere", "location independent"], 0.7),
            LocationPattern(["remote work", "remote position"], 0.9),
        ]

        self.hybrid_patterns = [
            LocationPattern(["hybrid", "hybrid work"], 1.0),
            LocationPattern(["flexible work", "flexible schedule"], 0.7),
            LocationPattern(["remote-friendly"], 0.8),
            LocationPattern(["work from office occasionally"], 0.8),
            LocationPattern(["2-3 days in office", "2 days office"], 0.9),
            LocationPattern(["split between home and office"], 0.9),
            LocationPattern(["combination of remote and office"], 0.9),
        ]

        self.onsite_patterns = [
            LocationPattern(["on-site", "onsite", "on site"], 1.0),
            LocationPattern(["in-office", "office-based"], 0.9),
            LocationPattern(["must be located in", "must be based in"], 0.8),
            LocationPattern(["relocate to", "relocation required"], 0.9),
            LocationPattern(["local candidates only"], 0.8),
            LocationPattern(["no remote work"], 1.0, ["remote"]),
        ]

    def detect_location_type(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect location type for a job.

        Args:
            job_data: Dictionary containing job information

        Returns:
            Dictionary with location_type and confidence score
        """
        # Collect text from relevant fields
        text_fields = [
            job_data.get("title", ""),
            job_data.get("description", ""),
            job_data.get("job_description", ""),
            job_data.get("location", ""),
            job_data.get("summary", ""),
            job_data.get("requirements", ""),
        ]

        full_text = " ".join(str(field) for field in text_fields if field)
        full_text = full_text.lower()

        # Calculate scores for each type
        remote_score = self._calculate_pattern_score(full_text, self.remote_patterns)
        hybrid_score = self._calculate_pattern_score(full_text, self.hybrid_patterns)
        onsite_score = self._calculate_pattern_score(full_text, self.onsite_patterns)

        # Determine location type based on highest score
        max_score = max(remote_score, hybrid_score, onsite_score)

        if max_score == 0:
            location_type = "unknown"
            confidence = 0.0
        elif remote_score == max_score:
            location_type = "remote"
            confidence = min(remote_score, 1.0)
        elif hybrid_score == max_score:
            location_type = "hybrid"
            confidence = min(hybrid_score, 1.0)
        else:
            location_type = "onsite"
            confidence = min(onsite_score, 1.0)

        # Apply additional logic
        result = self._apply_additional_logic(
            job_data, location_type, confidence, remote_score, hybrid_score, onsite_score
        )

        logger.debug(
            f"Location detection: {job_data.get('title', 'Unknown')} -> "
            f"{result['location_type']} (confidence: {result['confidence']:.2f})"
        )

        return result

    def _calculate_pattern_score(self, text: str, patterns: List[LocationPattern]) -> float:
        """Calculate weighted score for a set of patterns."""
        total_score = 0.0

        for pattern in patterns:
            # Check for positive keywords
            matches = sum(1 for keyword in pattern.keywords if keyword in text)

            if matches > 0:
                # Check for negative keywords (if any)
                if pattern.negative_keywords:
                    negative_matches = sum(
                        1 for keyword in pattern.negative_keywords if keyword in text
                    )
                    if negative_matches > 0:
                        continue  # Skip this pattern if negative keywords found

                # Add weighted score
                score = (matches / len(pattern.keywords)) * pattern.weight
                total_score += score

        return total_score

    def _apply_additional_logic(
        self,
        job_data: Dict[str, Any],
        location_type: str,
        confidence: float,
        remote_score: float,
        hybrid_score: float,
        onsite_score: float,
    ) -> Dict[str, Any]:
        """Apply additional logic to refine location type detection."""

        # Check location field for geographic specificity
        location = job_data.get("location", "").lower()

        # If location is very specific (has address/zip), likely onsite
        address_indicators = [
            r"\d{5}",  # ZIP code
            r"\d+\s+\w+\s+(street|st|avenue|ave|road|rd|drive|dr)",  # Street address
            "suite",
            "floor",
            "building",
        ]

        if any(re.search(pattern, location) for pattern in address_indicators):
            if location_type == "unknown" or confidence < 0.7:
                location_type = "onsite"
                confidence = 0.8

        # If salary/compensation mentions location allowances, likely remote
        compensation_text = " ".join(
            [
                job_data.get("salary_range", ""),
                job_data.get("benefits", ""),
                job_data.get("description", ""),
            ]
        ).lower()

        remote_benefits = [
            "home office allowance",
            "internet allowance",
            "remote work stipend",
            "equipment provided",
        ]

        if any(benefit in compensation_text for benefit in remote_benefits):
            if location_type == "unknown" or (location_type == "onsite" and confidence < 0.8):
                location_type = "remote"
                confidence = max(confidence, 0.7)

        # Company-specific logic (some companies are known for remote work)
        company = job_data.get("company", "").lower()
        remote_friendly_companies = [
            "automattic",
            "gitlab",
            "buffer",
            "zapier",
            "basecamp",
            "github",
            "stackoverflow",
            "toptal",
            "remote.com",
        ]

        if any(comp in company for comp in remote_friendly_companies):
            if location_type == "unknown":
                location_type = "remote"
                confidence = 0.6

        return {
            "location_type": location_type,
            "confidence": confidence,
            "scores": {"remote": remote_score, "hybrid": hybrid_score, "onsite": onsite_score},
        }

    def bulk_detect_location_types(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect location types for multiple jobs."""
        results = []

        for job in jobs:
            detection_result = self.detect_location_type(job)
            job_result = job.copy()
            job_result.update(detection_result)
            results.append(job_result)

        return results

    def get_location_statistics(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about location types in a job list."""
        stats = {
            "total_jobs": len(jobs),
            "remote": 0,
            "hybrid": 0,
            "onsite": 0,
            "unknown": 0,
            "confidence_distribution": {
                "high": 0,  # >= 0.8
                "medium": 0,  # 0.5 - 0.8
                "low": 0,  # < 0.5
            },
        }

        for job in jobs:
            location_type = job.get("location_type", "unknown")
            confidence = job.get("confidence", 0.0)

            stats[location_type] += 1

            if confidence >= 0.8:
                stats["confidence_distribution"]["high"] += 1
            elif confidence >= 0.5:
                stats["confidence_distribution"]["medium"] += 1
            else:
                stats["confidence_distribution"]["low"] += 1

        # Calculate percentages
        if stats["total_jobs"] > 0:
            for key in ["remote", "hybrid", "onsite", "unknown"]:
                stats[f"{key}_percentage"] = (stats[key] / stats["total_jobs"]) * 100

        return stats
