"""
Database engine management for job database operations.
"""

import sqlite3
import logging
import threading
from pathlib import Path
from queue import Queue
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseEngine:
    """Manages database connections and initialization."""
    
    def __init__(self, db_path: str = "data/jobs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._connection_pool = Queue(maxsize=5)
        self._init_pool()
        self._init_database()
        logger.info(f"✅ Database engine initialized: {self.db_path}")
    
    def _init_pool(self):
        """Initialize connection pool."""
        for _ in range(5):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._connection_pool.put(conn)
    
    @property
    def conn(self):
        """Backward compatibility property for direct connection access."""
        # Get a connection from the pool for backward compatibility
        try:
            conn = self._connection_pool.get(timeout=1)
            # Return it immediately to avoid blocking the pool
            self._connection_pool.put(conn)
            return conn
        except Exception:
            # If pool is empty, create a temporary connection
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
    
    @property
    def cursor(self):
        """Backward compatibility property for direct cursor access."""
        return self.conn.cursor()
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool."""
        conn = None
        try:
            conn = self._connection_pool.get(timeout=5)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                try:
                    self._connection_pool.put(conn)
                except:
                    # If pool is full, close connection
                    conn.close()
    
    def _init_database(self):
        """Initialize database tables."""
        try:
            with self.get_connection() as conn:
                # Check if jobs table exists
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='jobs'
                """)
                
                table_exists = cursor.fetchone() is not None
                
                if not table_exists:
                    # Create new table with full schema
                    conn.execute("""
                        CREATE TABLE jobs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            job_id TEXT UNIQUE,
                            title TEXT NOT NULL,
                            company TEXT NOT NULL,
                            location TEXT,
                            summary TEXT,
                            url TEXT,
                            search_keyword TEXT,
                            site TEXT,
                            scraped_at TEXT,
                            raw_data TEXT,
                            analysis_data TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            applied INTEGER DEFAULT 0
                        )
                    """)
                    
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_job_id ON jobs(job_id)
                    """)
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_title_company ON jobs(title, company)
                    """)
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_site ON jobs(site)
                    """)
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_scraped_at ON jobs(scraped_at)
                    """)
                    
                    conn.commit()
                    logger.info("✅ Database tables initialized")
                else:
                    # Check if job_id column exists
                    cursor = conn.execute("PRAGMA table_info(jobs)")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    if 'job_id' not in columns:
                        # Add job_id column to existing table
                        logger.info("🔄 Adding job_id column to existing database...")
                        conn.execute("ALTER TABLE jobs ADD COLUMN job_id TEXT")
                        conn.execute("CREATE INDEX IF NOT EXISTS idx_job_id ON jobs(job_id)")
                        
                        # Generate job_id for existing records
                        cursor = conn.execute("SELECT id, title, company, url, scraped_at FROM jobs WHERE job_id IS NULL OR job_id = ''")
                        existing_jobs = cursor.fetchall()
                        
                        for job_row in existing_jobs:
                            job_id, title, company, url, scraped_at = job_row
                            # Generate job_id based on existing data
                            import hashlib
                            content = f"{title}{company}{url}{scraped_at or ''}"
                            job_id_hash = hashlib.md5(content.encode()).hexdigest()[:12]
                            
                            conn.execute("UPDATE jobs SET job_id = ? WHERE id = ?", (job_id_hash, job_id))
                        
                        conn.commit()
                        logger.info(f"✅ Added job_id column and populated {len(existing_jobs)} existing records")
                    
                    # Check for other missing columns and add them
                    missing_columns = []
                    required_columns = {
                        'analysis_data': 'TEXT',
                        'applied': 'INTEGER DEFAULT 0'
                    }
                    
                    for col_name, col_type in required_columns.items():
                        if col_name not in columns:
                            missing_columns.append((col_name, col_type))
                    
                    if missing_columns:
                        logger.info(f"🔄 Adding missing columns: {[col[0] for col in missing_columns]}")
                        for col_name, col_type in missing_columns:
                            conn.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
                        conn.commit()
                        logger.info("✅ Added missing columns")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    def close(self):
        """Close all database connections."""
        try:
            while not self._connection_pool.empty():
                conn = self._connection_pool.get_nowait()
                conn.close()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"❌ Error closing database connections: {e}")


def create_database_engine(db_path: str = "data/jobs.db") -> DatabaseEngine:
    """Create a database engine instance."""
    return DatabaseEngine(db_path) 