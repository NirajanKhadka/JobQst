import time
from urllib.parse import quote_plus
import sqlite3
from playwright.sync_api import sync_playwright

def init_db(db_path="jobs.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT UNIQUE,
            summary TEXT,
            date_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def insert_job(conn, job, source="Indeed"):
    try:
        conn.execute("""
            INSERT OR IGNORE INTO jobs (source, title, company, location, url, summary)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            source,
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("url", ""),
            job.get("summary", "")
        ))
        conn.commit()
    except Exception as e:
        print(f"Error saving job: {e}")

QUERY = "Data Analyst Power BI SQL Python Data Science Machine Learning"
LOCATION = "Mississauga"
MAX_PAGES = 2

def main():
    conn = init_db("jobs.db")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # human mode!
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            locale="en-CA",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        for n in range(MAX_PAGES):
            url = (
                f"https://ca.indeed.com/jobs"
                f"?q={quote_plus(QUERY)}"
                f"&l={quote_plus(LOCATION)}"
                f"&start={n*10}"
            )
            print(f"Indeed: {url}")
            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)
                jobs = []
                cards = page.locator("a.tapItem")
                for i in range(cards.count()):
                    card = cards.nth(i)
                    job = {
                        "title": card.locator("h2").inner_text(),
                        "company": card.locator(".companyName").inner_text(),
                        "location": card.locator(".companyLocation").inner_text() if card.locator(".companyLocation").count() else "",
                        "summary": card.locator(".job-snippet").inner_text() if card.locator(".job-snippet").count() else "",
                        "url": card.get_attribute("href"),
                    }
                    jobs.append(job)
                    insert_job(conn, job, "Indeed")
                print(f"Indeed page {n+1}: {len(jobs)} jobs")
                for job in jobs:
                    print(f"- {job['title']} at {job['company']} [{job['url']}]")
                time.sleep(3)
            except Exception as e:
                print(f"Error on Indeed page {n+1}: {e}")

        page.close()
        context.close()
        browser.close()
    conn.close()

if __name__ == "__main__":
    main()
