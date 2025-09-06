"""
Core module for AutoJobAgent.

This module provides core functionality including database operations,
job data management, and data processing utilities.
"""

from .job_database import get_job_db
from .job_data import JobData

try:
    from .db_queries import DBQueries
    DB_QUERIES_AVAILABLE = True
except ImportError:
    DB_QUERIES_AVAILABLE = False

__all__ = [
    'get_job_db',
    'JobData',
]

if DB_QUERIES_AVAILABLE:
    __all__.append('DBQueries')
