
import asyncio
from playwright.async_api import async_playwright
import sqlite3
import argparse
import urllib.parse

DB_PATH = 'data/jobs.db'
TARGET_COUNT = 50

# Utility: Save job to DB (customize as needed)
def save_job_to_db(job):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        title TEXT, company TEXT, location TEXT, salary TEXT, link TEXT UNIQUE
    )''')
    try:
        c.execute('INSERT INTO jobs (title, company, location, salary, link) VALUES (?, ?, ?, ?, ?)',
                  (job['title'], job['company'], job['location'], job['salary'], job['link']))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Duplicate
    finally:
        conn.close()

async def extract_jobs_from_page(page):
    jobs = []
    h2s = await page.query_selector_all('h2')
    print(f"[DEBUG] Found {len(h2s)} h2 elements on page.")
    for h2 in h2s:
        title = (await h2.inner_text()).strip()
        link_elem = await h2.query_selector('a')
        link = await link_elem.get_attribute('href') if link_elem else ''
        card = await h2.evaluate_handle('node => node.parentElement')
        company = ''
        location = ''
        salary = ''
        if card:
            company_elem = await card.query_selector('a[href^="/jobs-at-"]')
            if company_elem:
                company = (await company_elem.inner_text()).strip()
            # Try to find location (ends with province code)
            children = await card.evaluate('node => Array.from(node.children).map(c => c.textContent)')
            for child in children:
                if child and child.strip().endswith(('AB', 'BC', 'ON', 'QC', 'NS', 'MB', 'NB', 'NL', 'PE', 'SK', 'YT', 'NT', 'NU')):
                    location = child.strip()
                    break
            # Try to find salary
            text = await card.inner_text()
            import re
            m = re.search(r'\$[\d,.]+(\s*-\s*\$[\d,.]+)?', text)
            if m:
                salary = m.group(0)
        jobs.append({'title': title, 'company': company, 'location': location, 'salary': salary, 'link': link})
    filtered = [j for j in jobs if j['title'] and j['link']]
    print(f"[DEBUG] Extracted {len(filtered)} jobs from page. Sample: {filtered[0] if filtered else 'None'}")
    return filtered

async def resolve_real_link(context, job):
    if job['link'] == '#!':
        # Open popup/tab and get real URL
        page = await context.new_page()
        await page.goto('https://www.eluta.ca/search?q=engineer+sort%3Arank&pg=1')  # Ensure on correct domain
        await page.click(f'text="{job["title"]}"')
        await page.wait_for_load_state('domcontentloaded')
        real_url = page.url
        await page.close()
        job['link'] = real_url
    return job


def build_search_url(keywords: str, location: str = None, page: int = 1) -> str:
    q = urllib.parse.quote_plus(keywords)
    url = f"https://www.eluta.ca/search?q={q}+sort%3Arank"
    # Only add location if not 'Canada' or empty
    if location and location.strip().lower() != 'canada':
        loc = urllib.parse.quote_plus(location)
        url += f"&l={loc}"
    url += f"&pg={page}"
    return url


async def main():
    parser = argparse.ArgumentParser(description="Eluta.ca Job Scraper (Playwright MCP)")
    parser.add_argument('-k', '--keywords', nargs='+', type=str, default=["Data Scientist", "Data Analyst", "Data"], help='List of search keywords (default: Data Scientist, Data Analyst, Data)')
    parser.add_argument('-l', '--location', type=str, default="Canada", help='Location (default: Canada)')
    parser.add_argument('-p', '--pages', type=int, default=10, help='Number of pages to scrape per keyword (default: 10)')
    args = parser.parse_args()

    keywords_list = args.keywords
    location = args.location
    max_pages = args.pages

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        unique_jobs = []
        seen = set()
        for kw in keywords_list:
            for page_num in range(1, max_pages + 1):
                search_url = build_search_url(kw, location, page_num)
                await page.goto(search_url)
                jobs = await extract_jobs_from_page(page)
                for job in jobs:
                    key = (job['title'], job['company'], job['link'])
                    if key in seen:
                        continue
                    job = await resolve_real_link(context, job)
                    key = (job['title'], job['company'], job['link'])
                    if key in seen:
                        continue
                    seen.add(key)
                    unique_jobs.append(job)
                    save_job_to_db(job)
        await browser.close()
    print(f"Saved {len(unique_jobs)} unique jobs across all keywords.")

if __name__ == '__main__':
    asyncio.run(main())
