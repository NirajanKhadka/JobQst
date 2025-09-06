#!/usr/bin/env python3
"""Quick script to check jobs in Nirajan's DuckDB database."""

import duckdb
import sys

def check_nirajan_jobs():
    """Check jobs in the Nirajan DuckDB database."""
    try:
        conn = duckdb.connect('profiles/Nirajan/nirajan_duckdb.db')
        
        # Check if jobs table exists
        try:
            result = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()
            count = result[0] if result else 0
            print(f"Jobs in Nirajan DuckDB: {count}")
            
            if count > 0:
                jobs = conn.execute('SELECT title, company, location FROM jobs LIMIT 5').fetchall()
                print("Sample jobs:")
                for job in jobs:
                    print(f"  - {job[0]} at {job[1]} ({job[2]})")
            else:
                print("No jobs found in database.")
                
        except Exception as e:
            print(f"Error checking jobs table: {e}")
            # Try to see what tables exist
            try:
                tables = conn.execute('SHOW TABLES').fetchall()
                print(f"Available tables: {tables}")
            except Exception as e2:
                print(f"Error showing tables: {e2}")
                
        conn.close()
        
    except Exception as e:
        print(f"Error connecting to DuckDB: {e}")

if __name__ == "__main__":
    check_nirajan_jobs()
