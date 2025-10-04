"""
DuckDB Connection Manager
Handles connection pooling and prevents file locking issues
"""

import logging
import duckdb
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DuckDBConnectionManager:
    """Manages DuckDB connections to prevent file locking issues"""

    @staticmethod
    def get_db_path(profile_name: Optional[str] = None) -> str:
        """Get database path for profile"""
        if profile_name:
            return f"profiles/{profile_name}/{profile_name}_duckdb.db"
        return "data/jobs_duckdb.db"

    @staticmethod
    @contextmanager
    def get_connection(profile_name: Optional[str] = None, read_only: bool = False):
        """Get a database connection with proper cleanup"""
        db_path = DuckDBConnectionManager.get_db_path(profile_name)

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = None
        try:
            # Try normal connection first
            if read_only:
                conn = duckdb.connect(db_path, read_only=True)
            else:
                conn = duckdb.connect(db_path)

            yield conn

        except duckdb.IOException as e:
            if "already open" in str(e) and not read_only:
                # Try read-only connection if file is locked
                logger.warning(f"Database locked, trying read-only: {e}")
                try:
                    if conn:
                        conn.close()
                    conn = duckdb.connect(db_path, read_only=True)
                    yield conn
                except Exception as e2:
                    logger.error(f"Failed to connect in read-only mode: {e2}")
                    raise e2
            else:
                raise e
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise e
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass  # Ignore close errors

    @staticmethod
    def execute_query(
        query: str, params: list = None, profile_name: Optional[str] = None, read_only: bool = True
    ):
        """Execute a query with automatic connection management"""
        with DuckDBConnectionManager.get_connection(profile_name, read_only) as conn:
            if params:
                return conn.execute(query, params).fetchall()
            else:
                return conn.execute(query).fetchall()

    @staticmethod
    def get_columns(query: str, params: list = None, profile_name: Optional[str] = None):
        """Get column names from a query"""
        with DuckDBConnectionManager.get_connection(profile_name, read_only=True) as conn:
            if params:
                result = conn.execute(query, params)
            else:
                result = conn.execute(query)
            return [desc[0] for desc in conn.description]
