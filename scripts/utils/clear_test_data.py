from src.core.job_database import get_job_db

db = get_job_db('test_profile')
try:
    db.conn.execute("DELETE FROM jobs WHERE company = 'Test Company'")
    print('✅ Cleared test data')
except Exception as e:
    print(f'Error: {e}')
