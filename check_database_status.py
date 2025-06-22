import sqlite3
import os

def check_database(db_path, name):
    if not os.path.exists(db_path):
        print(f"❌ {name} database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total jobs
        cursor.execute('SELECT COUNT(*) FROM jobs')
        total = cursor.fetchone()[0]
        
        # Get jobs with URLs
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE url IS NOT NULL AND url != ""')
        with_urls = cursor.fetchone()[0]
        
        # Get jobs without URLs
        without_urls = total - with_urls
        
        print(f"\n📊 {name} Database Status:")
        print(f"   Database: {db_path}")
        print(f"   Total jobs: {total}")
        print(f"   Jobs with URLs: {with_urls}")
        print(f"   Jobs without URLs: {without_urls}")
        if total > 0:
            print(f"   URL coverage: {with_urls/total*100:.1f}%")
        
        # Show sample jobs with URLs
        if with_urls > 0:
            print(f"\n🔗 Sample jobs with URLs:")
            cursor.execute('SELECT title, url FROM jobs WHERE url IS NOT NULL AND url != "" LIMIT 3')
            for title, url in cursor.fetchall():
                print(f"   📋 {title[:50]}...")
                print(f"      🔗 {url[:80]}...")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking {name} database: {e}")

# Check both databases
check_database('data/jobs.db', 'Main')
check_database('profiles/Nirajan/Nirajan.db', 'Nirajan Profile') 