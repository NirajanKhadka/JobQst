"""
Legacy import shim for OptimizedElutaScraper used in tests.
Redirects to current eluta_scraper implementation with a compatible API.
"""

from .eluta_scraper import ElutaScraper as OptimizedElutaScraper

