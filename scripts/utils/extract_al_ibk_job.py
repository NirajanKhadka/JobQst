import sqlite3
import os

db_path = os.path.abspath(os.path.join('profiles', 'Nirajan', 'Nirajan.db'))

def get_al_ibk_job_description():
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT job_id, title, company, job_description FROM jobs WHERE company LIKE '%Al Ibk%' LIMIT 1;")
        row = cursor.fetchone()
        if row:
            job_id, title, company, job_description = row
            print(f"Job ID: {job_id}\nTitle: {title}\nCompany: {company}\nDescription:\n{job_description}")
            return job_description
        else:
            print("No job found for company 'Al Ibk'.")
    except Exception as e:
        print(f"Error accessing database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    get_al_ibk_job_description()
