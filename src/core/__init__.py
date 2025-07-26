"""
Core module for AutoJobAgent.

This module provides core functionality including database operations,
job record management, and data processing utilities.
"""

from .job_database import ModernJobDatabase, get_job_db
from .job_record import JobRecord

try:
    from .db_queries import DBQueries
    DB_QUERIES_AVAILABLE = True
except ImportError:
    DB_QUERIES_AVAILABLE = False

__all__ = [
    'ModernJobDatabase',
    'get_job_db', 
    'JobRecord',
]

if DB_QUERIES_AVAILABLE:
    __all__.append('DBQueries')