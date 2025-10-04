"""
Job Database Module - Simplified DuckDB-only Implementation

This module provides the main entry point for job database operations.
All database functionality is now handled exclusively through DuckDB.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_job_db(profile: Optional[str] = None):
    """Get job database instance - DuckDB only"""
    from .duckdb_database import DuckDBJobDatabase
    
    # Handle in-memory database special case (for tests)
    if profile == ":memory:":
        # For in-memory, we'd need different handling - not fully supported yet
        # For now, create a temp profile
        import tempfile
        import os
        temp_profile = f"temp_{os.getpid()}"
        return DuckDBJobDatabase(profile_name=temp_profile)
    
    return DuckDBJobDatabase(profile_name=profile)


# Backward compatibility alias for existing code
JobDatabase = get_job_db
