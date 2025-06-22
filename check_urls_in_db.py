import sqlite3

# Check profile database
conn = sqlite3.connect('profiles/Nirajan/Nirajan.db')
cursor = conn.cursor()

# Get total jobs
cursor.execute('SELECT COUNT(*) FROM jobs')
total = cursor.fetchone()[0]

# Get jobs with URLs
cursor.execute('SELECT COUNT(*) FROM jobs WHERE url IS NOT NULL AND url != ""')
with_urls = cursor.fetchone()[0]

print(f"📊 Database Status:")
print(f"   Total jobs: {total}")
print(f"   Jobs with URLs: {with_urls}")
print(f"   Jobs without URLs: {total - with_urls}")
print(f"   URL coverage: {with_urls/total*100:.1f}%" if total > 0 else "No jobs found")

# Show sample jobs with URLs
if with_urls > 0:
    print(f"\n🔗 Sample jobs with URLs:")
    cursor.execute('SELECT title, url FROM jobs WHERE url IS NOT NULL AND url != "" LIMIT 5')
    for title, url in cursor.fetchall():
        print(f"   Title: {title[:50]}...")
        print(f"   URL: {url[:80]}...")
        print()

# Show sample jobs without URLs
if total - with_urls > 0:
    print(f"\n❌ Sample jobs without URLs:")
    cursor.execute('SELECT title, url FROM jobs WHERE url IS NULL OR url = "" LIMIT 3')
    for title, url in cursor.fetchall():
        print(f"   Title: {title[:50]}...")
        print(f"   URL: {url if url else 'None'}")
        print()

conn.close() 