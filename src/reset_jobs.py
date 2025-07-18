#!/usr/bin/env python3
"""Reset some jobs to scraped status for testing enhanced processor"""

import sqlite3
from pathlib import Path


def reset_jobs_for_testing():
    db_path = "profiles/Nirajan/Nirajan.db"
    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Reset 5 jobs back to 'scraped' status for testing
        cursor.execute(
            """
            UPDATE jobs 
            SET status = 'scraped', 
                match_score = 0,
                experience_level = '',
                processing_notes = '',
                analysis_data = '',
                updated_at = CURRENT_TIMESTAMP
            WHERE job_id IN (
                SELECT job_id FROM jobs 
                WHERE status = 'skip' 
                LIMIT 5
            )
        """
        )

        rows_updated = cursor.rowcount
        conn.commit()

        print(f"✅ Reset {rows_updated} jobs back to 'scraped' status for testing")

        # Show current status distribution
        cursor.execute(
            """
            SELECT status, COUNT(*) as count 
            FROM jobs 
            GROUP BY status 
            ORDER BY count DESC
        """
        )

        print("\n📊 Current Job Status Distribution:")
        for status, count in cursor.fetchall():
            print(f"   {status}: {count} jobs")

        conn.close()

    except Exception as e:
        print(f"Error resetting jobs: {e}")


if __name__ == "__main__":
    reset_jobs_for_testing()
