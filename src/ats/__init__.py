"""
ATS Detection and Submitter Module
Provides automatic detection of ATS systems and returns appropriate submitters.
"""

import logging
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ATS URL patterns for detection
ATS_PATTERNS = {
    "workday": [
        r"\.workday\.com",
        r"\.workdaycdn\.com",
        r"/jobs/[^/]+\.workday\.com",
        r"workday\..*\.com",
    ],
    "greenhouse": [r"\.greenhouse\.io", r"boards\.greenhouse\.io", r"job-boards\.greenhouse\.io"],
    "icims": [r"\.icims\.com", r"careers\.icims\.com", r"\.icims\..*\.com"],
    "bamboohr": [r"\.bamboohr\.com", r"careers\.bamboohr\.com", r"\.bamboohr\..*\.com"],
    "lever": [r"\.lever\.co", r"jobs\.lever\.co", r"\.leverpostings\.com"],
}

# Company-specific ATS mappings (for when URL patterns aren't enough)
COMPANY_ATS_MAPPINGS = {
    "microsoft": "icims",
    "google": "greenhouse",
    "amazon": "workday",
    "meta": "workday",
    "apple": "workday",
    "salesforce": "workday",
    "netflix": "greenhouse",
    "uber": "greenhouse",
    "airbnb": "greenhouse",
}


def detect(job_url: str, company_name: str = None) -> Optional[str]:
    """
    Detect the ATS system from a job URL and optionally company name.

    Args:
        job_url: The URL of the job posting
        company_name: Optional company name for additional context

    Returns:
        String identifier of the detected ATS system, or None if not detected
    """
    if not job_url:
        logger.warning("No job URL provided for ATS detection")
        return None

    try:
        # Parse the URL
        parsed_url = urlparse(job_url.lower())
        full_url = job_url.lower()

        logger.debug(f"Detecting ATS for URL: {job_url}")

        # Check URL patterns for each ATS
        for ats_name, patterns in ATS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, full_url):
                    logger.info(f"Detected {ats_name.upper()} ATS from URL pattern: {pattern}")
                    return ats_name

        # Check company-specific mappings if company name is provided
        if company_name:
            company_lower = company_name.lower().strip()

            # Direct company mapping
            if company_lower in COMPANY_ATS_MAPPINGS:
                detected_ats = COMPANY_ATS_MAPPINGS[company_lower]
                logger.info(
                    f"Detected {detected_ats.upper()} ATS from company mapping: {company_name}"
                )
                return detected_ats

            # Partial company name matching
            for company_key, ats_name in COMPANY_ATS_MAPPINGS.items():
                if company_key in company_lower or company_lower in company_key:
                    logger.info(
                        f"Detected {ats_name.upper()} ATS from partial company match: {company_name}"
                    )
                    return ats_name

        # Additional heuristic checks based on URL structure
        domain = parsed_url.netloc

        # Check for common ATS subdomains
        if any(subdomain in domain for subdomain in ["careers", "jobs", "talent", "apply"]):
            # Look for ATS-specific keywords in the path or query
            url_content = f"{parsed_url.path} {parsed_url.query}"

            if "workday" in url_content:
                logger.info("Detected WORKDAY ATS from URL content analysis")
                return "workday"
            elif "greenhouse" in url_content:
                logger.info("Detected GREENHOUSE ATS from URL content analysis")
                return "greenhouse"
            elif "icims" in url_content:
                logger.info("Detected ICIMS ATS from URL content analysis")
                return "icims"
            elif "bamboo" in url_content:
                logger.info("Detected BAMBOOHR ATS from URL content analysis")
                return "bamboohr"
            elif "lever" in url_content:
                logger.info("Detected LEVER ATS from URL content analysis")
                return "lever"

        logger.debug(f"No ATS detected for URL: {job_url}")
        return None

    except Exception as e:
        logger.error(f"Error detecting ATS for URL {job_url}: {e}")
        return None


def get_submitter(ats_type: str, browser_context=None):
    """
    Get the appropriate submitter instance for the detected ATS type.

    Args:
        ats_type: The ATS type identifier (e.g., 'workday', 'greenhouse')
        browser_context: Optional browser context for submitter initialization

    Returns:
        Submitter instance for the specified ATS, or fallback submitter
    """
    if not ats_type:
        logger.warning("No ATS type provided, using fallback submitter")
        return _get_fallback_submitter(browser_context)

    try:
        ats_type = ats_type.lower().strip()
        logger.info(f"Getting submitter for ATS type: {ats_type}")

        # Import submitters dynamically to avoid circular imports
        if ats_type == "workday":
            from .workday import WorkdaySubmitter

            return WorkdaySubmitter(browser_context)

        elif ats_type == "greenhouse":
            from .greenhouse import GreenhouseSubmitter

            return GreenhouseSubmitter(browser_context)

        elif ats_type == "icims":
            from .icims import ICIMSSubmitter

            return ICIMSSubmitter(browser_context)

        elif ats_type == "bamboohr":
            # BambooHR integration has been removed. Use fallback submitter to maintain functionality.
            logger.warning("BambooHR integration removed; using Generic fallback submitter")
            return _get_fallback_submitter(browser_context)

        elif ats_type == "lever":
            # Note: Lever submitter is currently incomplete
            logger.warning("Lever ATS submitter is not fully implemented, using fallback")
            return _get_fallback_submitter(browser_context)

        else:
            logger.warning(f"Unknown ATS type: {ats_type}, using fallback submitter")
            return _get_fallback_submitter(browser_context)

    except ImportError as e:
        logger.error(f"Failed to import submitter for {ats_type}: {e}")
        return _get_fallback_submitter(browser_context)
    except Exception as e:
        logger.error(f"Error creating submitter for {ats_type}: {e}")
        return _get_fallback_submitter(browser_context)


def _get_fallback_submitter(browser_context=None):
    """
    Get a fallback submitter when specific ATS detection fails.

    Args:
        browser_context: Optional browser context

    Returns:
        Fallback submitter instance
    """
    try:
        # Try to use GenericATSSubmitter first
        from .fallback_submitters import GenericATSSubmitter

        logger.info("Using Generic ATS Submitter as fallback")
        return GenericATSSubmitter(browser_context)

    except ImportError:
        logger.warning("Generic ATS Submitter not available, using manual fallback")
        try:
            from .fallback_submitters import ManualApplicationSubmitter

            return ManualApplicationSubmitter(browser_context)
        except ImportError:
            logger.error("No fallback submitters available")
            return None


def get_supported_ats_types() -> Dict[str, Dict[str, Any]]:
    """
    Get information about supported ATS types.

    Returns:
        Dictionary with ATS type information including patterns and status
    """
    return {
        "workday": {
            "name": "Workday",
            "patterns": ATS_PATTERNS["workday"],
            "status": "active",
            "description": "Workday Human Capital Management ATS",
        },
        "greenhouse": {
            "name": "Greenhouse",
            "patterns": ATS_PATTERNS["greenhouse"],
            "status": "active",
            "description": "Greenhouse recruiting software",
        },
        "icims": {
            "name": "iCIMS",
            "patterns": ATS_PATTERNS["icims"],
            "status": "active",
            "description": "iCIMS Talent Cloud ATS",
        },
        "bamboohr": {
            "name": "BambooHR",
            "patterns": ATS_PATTERNS["bamboohr"],
            "status": "removed",
            "description": "BambooHR integration removed; routes to Generic fallback submitter",
        },
        "lever": {
            "name": "Lever",
            "patterns": ATS_PATTERNS["lever"],
            "status": "incomplete",
            "description": "Lever recruiting platform (implementation in progress)",
        },
    }
