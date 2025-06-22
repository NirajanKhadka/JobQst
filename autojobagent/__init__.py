"""
AutoJobAgent - Automated job application system with AI-powered matching.

This package provides tools for automating job applications, including job scraping,
resume customization, and application submission to various ATS platforms.
"""

__version__ = "1.0.0"
__author__ = "Nirajan Khadka"
__email__ = "Nirajan.Tech@gmail.com"

# Configure logging when the package is imported
from .shared.logging_config import configure_logging

# Initialize with default settings
configure_logging()
