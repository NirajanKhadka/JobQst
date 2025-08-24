"""
Database Configuration Manager
Handles both SQLite and PostgreSQL connections with automatic fallback.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlparse
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    database_type: str  # 'postgresql' or 'sqlite'
    connection_string: str
    pool_size: int = 5
    max_connections: int = 10
    sqlite_path: Optional[str] = None
    postgres_config: Optional[Dict[str, Any]] = None


class DatabaseConfigManager:
    """Manages database configuration and connection setup."""
    
    def __init__(self):
        self.config = self._load_config()
        self._connection_pool = None
        
    def _load_config(self) -> DatabaseConfig:
        """Load database configuration from environment variables."""
        database_url = os.getenv('DATABASE_URL', 'sqlite:///data/jobs.db')
        
        if (database_url.startswith('postgresql://') or 
            database_url.startswith('postgres://')):
            # PostgreSQL configuration
            parsed = urlparse(database_url)
            postgres_config = {
                'host': parsed.hostname or 'localhost',
                'port': parsed.port or 5432,
                'database': parsed.path.lstrip('/') or 'autojob',
                'user': parsed.username or 'postgres',
                'password': parsed.password or 'password'
            }
            
            return DatabaseConfig(
                database_type='postgresql',
                connection_string=database_url,
                postgres_config=postgres_config,
                pool_size=int(os.getenv('DB_POOL_SIZE', 5)),
                max_connections=int(os.getenv('DB_MAX_CONNECTIONS', 10))
            )
        else:
            # SQLite configuration (fallback)
            if database_url.startswith('sqlite:///'):
                sqlite_path = database_url[10:]  # Remove 'sqlite:///'
            else:
                sqlite_path = database_url
                
            # Ensure absolute path
            if not os.path.isabs(sqlite_path):
                sqlite_path = os.path.join(os.getcwd(), sqlite_path)
                
            return DatabaseConfig(
                database_type='sqlite',
                connection_string=database_url,
                sqlite_path=sqlite_path
            )
    
    def test_connection(self) -> tuple[bool, str]:
        """Test database connection."""
        try:
            if self.config.database_type == 'postgresql':
                return self._test_postgresql_connection()
            else:
                return self._test_sqlite_connection()
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def _test_postgresql_connection(self) -> tuple[bool, str]:
        """Test PostgreSQL connection."""
        try:
            conn = psycopg2.connect(
                host=self.config.postgres_config['host'],
                port=self.config.postgres_config['port'],
                database=self.config.postgres_config['database'],
                user=self.config.postgres_config['user'],
                password=self.config.postgres_config['password'],
                connect_timeout=5
            )
            conn.close()
            return True, "PostgreSQL connection successful"
        except psycopg2.OperationalError as e:
            return False, f"PostgreSQL connection failed: {str(e)}"
    
    def _test_sqlite_connection(self) -> tuple[bool, str]:
        """Test SQLite connection."""
        try:
            # Ensure directory exists
            Path(self.config.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.config.sqlite_path)
            conn.execute("SELECT 1")
            conn.close()
            return True, "SQLite connection successful"
        except sqlite3.Error as e:
            return False, f"SQLite connection failed: {str(e)}"
    
    def get_connection_pool(self):
        """Get or create connection pool for PostgreSQL."""
        if self.config.database_type != 'postgresql':
            return None
            
        if self._connection_pool is None:
            try:
                self._connection_pool = ThreadedConnectionPool(
                    minconn=1,
                    maxconn=self.config.max_connections,
                    host=self.config.postgres_config['host'],
                    port=self.config.postgres_config['port'],
                    database=self.config.postgres_config['database'],
                    user=self.config.postgres_config['user'],
                    password=self.config.postgres_config['password']
                )
                logger.info("PostgreSQL connection pool created successfully")
            except Exception as e:
                logger.error(f"Failed to create PostgreSQL connection pool: {e}")
                raise
                
        return self._connection_pool
    
    def close_pool(self):
        """Close the connection pool."""
        if self._connection_pool:
            self._connection_pool.closeall()
            self._connection_pool = None
            logger.info("PostgreSQL connection pool closed")

# Global instance
db_config_manager = DatabaseConfigManager()


def get_database_config() -> DatabaseConfig:
    """Get the current database configuration."""
    return db_config_manager.config


def test_database_connection() -> tuple[bool, str]:
    """Test the current database connection."""
    return db_config_manager.test_connection()


def get_connection_pool():
    """Get the PostgreSQL connection pool if available."""
    return db_config_manager.get_connection_pool()
