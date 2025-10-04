"""
Database Configuration Manager - DuckDB Only
Simplified configuration for DuckDB-only database operations.
"""

import os
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration settings for DuckDB."""

    database_type: str = "duckdb"
    duckdb_path: str = "data/jobs_duckdb.db"


class DatabaseConfigManager:
    """Manages DuckDB configuration setup."""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> DatabaseConfig:
        """Load DuckDB configuration from environment variables."""
        database_url = os.getenv("DATABASE_URL", "duckdb:///data/jobs_duckdb.db")

        # Extract DuckDB path from URL
        if database_url.startswith("duckdb:///"):
            duckdb_path = database_url[10:]  # Remove 'duckdb:///'
        else:
            # Default DuckDB path
            duckdb_path = "data/jobs_duckdb.db"

        # Ensure absolute path
        from pathlib import Path

        if not Path(duckdb_path).is_absolute():
            duckdb_path = str(Path.cwd() / duckdb_path)

        return DatabaseConfig(duckdb_path=duckdb_path)

    def test_connection(self) -> tuple[bool, str]:
        """Test DuckDB connection."""
        return self._test_duckdb_connection()

    def _test_duckdb_connection(self) -> tuple[bool, str]:
        """Test DuckDB connection."""
        try:
            import duckdb

            # Ensure directory exists
            Path(self.config.duckdb_path).parent.mkdir(parents=True, exist_ok=True)

            conn = duckdb.connect(self.config.duckdb_path)
            conn.execute("SELECT 1")
            conn.close()
            return True, "DuckDB connection successful"
        except Exception as e:
            return False, f"DuckDB connection failed: {str(e)}"


# Global instance
db_config_manager = DatabaseConfigManager()


def get_database_config() -> DatabaseConfig:
    """Get the current database configuration."""
    return db_config_manager.config


def test_database_connection() -> tuple[bool, str]:
    """Test the current database connection."""
    return db_config_manager.test_connection()
