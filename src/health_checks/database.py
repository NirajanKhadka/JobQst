from pathlib import Path
from typing import Dict
import duckdb


def check_database_health(config: Dict) -> Dict:
    """Check DuckDB database health and integrity."""
    try:
        # Look for DuckDB databases in profiles directory
        profiles_dir = Path("profiles")
        if not profiles_dir.exists():
            return {
                "status": "warning",
                "message": "Profiles directory not found"
            }
        
        db_files = list(profiles_dir.glob("**/*_duckdb.db"))
        if not db_files:
            return {
                "status": "warning",
                "message": "No DuckDB databases found"
            }
        
        # Check the first available DuckDB database
        db_path = db_files[0]
        
        if not db_path.exists():
            return {
                "status": "warning",
                "message": "DuckDB database file not found"
            }

        db_size_mb = db_path.stat().st_size / (1024 * 1024)
        max_size = config.get("database_max_size_mb", 1000)
        if db_size_mb > max_size:
            return {
                "status": "warning",
                "message": f"Database size ({db_size_mb:.1f}MB) exceeds limit",
            }

        with duckdb.connect(str(db_path)) as conn:
            # Check if database can be accessed
            try:
                tables_result = conn.execute("SHOW TABLES").fetchall()
                tables = [row[0] for row in tables_result]
            except Exception as e:
                return {
                    "status": "critical",
                    "message": f"Database access failed: {str(e)}",
                }

            required_tables = ["jobs", "applications"]
            missing_tables = [
                table for table in required_tables if table not in tables
            ]

            if missing_tables:
                return {
                    "status": "warning",
                    "message": f"Missing tables: {missing_tables}"
                }

            # Check job count
            try:
                result = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()
                job_count = result[0] if result else 0
            except Exception:
                job_count = 0

        return {
            "status": "healthy",
            "message": f"DuckDB healthy ({db_size_mb:.1f}MB, "
                      f"{len(tables)} tables, {job_count} jobs)",
        }

    except Exception as e:
        return {
            "status": "critical",
            "message": f"DuckDB health check failed: {str(e)}"
        }

