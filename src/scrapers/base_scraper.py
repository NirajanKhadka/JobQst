"""
Abstract base class for job scrapers.

This module provides the BaseJobScraper abstract base class that defines
the interface all job scrapers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseJobScraper(ABC):
    """
    Abstract base class for all job scrapers.

    This class defines the interface that all job scrapers must implement.
    It cannot be instantiated directly - subclasses must implement all
    abstract methods.
    """

    def __init__(self, profile: Dict[str, Any]):
        """
        Initialize the scraper with a user profile.

        Args:
            profile: User profile containing keywords, location, etc.
        """
        self.profile = profile
        self.logger = logging.getLogger(self.__class__.__name__)

        # Validate required profile fields
        self._validate_profile(profile)

    def _validate_profile(self, profile: Dict[str, Any]) -> None:
        """
        Validate that the profile contains required fields.

        Args:
            profile: The profile to validate

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ["profile_name", "keywords"]
        missing_fields = [field for field in required_fields if field not in profile]

        if missing_fields:
            raise ValueError(f"Profile missing required fields: {missing_fields}")

    @abstractmethod
    def scrape_jobs(self, num_jobs: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape jobs from the target website.

        Args:
            num_jobs: Maximum number of jobs to scrape
            **kwargs: Additional scraper-specific parameters

        Returns:
            List of job dictionaries containing title, company, location, etc.
        """
        pass

    @abstractmethod
    def get_scraper_name(self) -> str:
        """
        Return the name of this scraper.

        Returns:
            String identifier for this scraper
        """
        pass

    def get_job_url(self, job_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract job URL from scraped job data.

        Args:
            job_data: Job dictionary

        Returns:
            Job URL if available, None otherwise
        """
        return job_data.get("url") or job_data.get("link") or job_data.get("job_url")

    def validate_job_data(self, job_data: Dict[str, Any]) -> bool:
        """
        Validate that scraped job data contains required fields.

        Args:
            job_data: Job dictionary to validate

        Returns:
            True if job data is valid, False otherwise
        """
        required_fields = ["title", "company"]
        return all(field in job_data and job_data[field] for field in required_fields)

    def clean_job_data(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and normalize job data.

        Args:
            job_data: Raw job data

        Returns:
            Cleaned job data
        """
        cleaned = {}

        # Clean title
        cleaned["title"] = str(job_data.get("title", "")).strip()

        # Clean company
        cleaned["company"] = str(job_data.get("company", "")).strip()

        # Clean location
        cleaned["location"] = str(job_data.get("location", "")).strip()

        # Clean description
        description = job_data.get("description", "")
        if description:
            cleaned["description"] = str(description).strip()

        # Preserve other fields
        for key, value in job_data.items():
            if key not in cleaned and value is not None:
                cleaned[key] = value

        return cleaned

    def __repr__(self) -> str:
        """String representation of the scraper."""
        return f"{self.__class__.__name__}(profile={self.profile.get('profile_name', 'unknown')})"
