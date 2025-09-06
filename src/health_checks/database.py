import sqlite3
from pathlib import Path
from typing import Dict


def check_database_health(config: Dict) -> Dict:
    """Check database health and integrity."""
    try:
        db_path = Path("jobs.db")

        if not db_path.exists():
            return {"status": "warning", "message": "Database file not found"}

        db_size_mb = db_path.stat().st_size / (1024 * 1024)
        if db_size_mb > config.get("database_max_size_mb", 1000):
            return {
                "status": "warning",
                "message": f"Database size ({db_size_mb:.1f}MB) exceeds limit",
            }

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]

            if integrity_result != "ok":
                return {
                    "status": "critical",
                    "message": f"Database integrity check failed: {integrity_result}",
                }

            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            required_tables = ["jobs", "applications"]
            missing_tables = [table for table in required_tables if table not in tables]

            if missing_tables:
                return {"status": "critical", "message": f"Missing tables: {missing_tables}"}

        return {
            "status": "healthy",
            "message": f"Database healthy ({db_size_mb:.1f}MB, {len(tables)} tables)",
        }

    except Exception as e:
        return {"status": "critical", "message": f"Database check failed: {str(e)}"}

