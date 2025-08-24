# 🛠️ JobQst Troubleshooting Guide

**Last Updated:** August 23, 2025  
**Status:** 🟢 ACTIVE | **Version:** 2.0.0

## 📋 Table of Contents
1. [Environment Setup Issues](#environment-setup-issues)
2. [JobSpy Integration Problems](#jobspy-integration-problems)
3. [AI Service Issues](#ai-service-issues)
4. [Dashboard Problems](#dashboard-problems)
5. [Multi-Site Scraping Issues](#multi-site-scraping-issues)
6. [Performance Optimization](#performance-optimization)
7. [Database Issues](#database-issues)
8. [Diagnostic Tools](#diagnostic-tools)
9. [Common Error Codes](#common-error-codes)
10. [FAQ](#faq)

---

## 1. Environment Setup Issues <a name="environment-setup-issues"></a>

### Conda Environment Problems
**Symptoms:** Import errors, package conflicts, wrong Python version
```bash
# Verify environment setup
conda info --envs
conda activate auto_job
python --version  # Should be 3.11+
```

**Solutions:**
- **Recreate conda environment:**
  ```bash
  conda deactivate
  conda env remove -n auto_job
  conda create -n auto_job python=3.11
  conda activate auto_job
  pip install -r requirements.txt
  ```

- **Fix activation issues:**
  ```bash
  # Windows PowerShell
  conda init powershell
  # Then restart terminal
  
  # Alternative activation
  conda run -n auto_job python main.py TestProfile --action dashboard
  ```

### JobSpy Installation Issues
**Symptoms:** `ModuleNotFoundError: No module named 'jobspy'`
```bash
# Install JobSpy with force reinstall
pip uninstall python-jobspy -y
pip install python-jobspy --no-cache-dir

# Verify installation
python -c "from jobspy import scrape_jobs; print('JobSpy installed successfully')"
```

### Playwright Browser Issues
**Symptoms:** Browser automation failures, missing chromium
```bash
# Install browser dependencies
playwright install chromium --force

# For Ubuntu/Debian systems
sudo apt-get install libnss3 libatk-bridge2.0-0 libdrm2 libgtk-3-0 libgbm1

# Verify browser installation
playwright --version
```

---

## 2. JobSpy Integration Problems <a name="jobspy-integration-problems"></a>

### Multi-Site Connection Failures
**Symptoms:** Some job sites failing, incomplete results
```python
# Test individual site connectivity
from src.scrapers.jobspy_enhanced_scraper import JobSpyEnhancedScraper

scraper = JobSpyEnhancedScraper("TestProfile")
# Test each site individually
test_sites = ["indeed", "linkedin", "glassdoor", "zip_recruiter"]
for site in test_sites:
    try:
        result = await scraper.test_site_connection(site)
        print(f"{site}: {'✓' if result else '✗'}")
    except Exception as e:
        print(f"{site}: Error - {e}")
```

**Solutions:**
- **Rate limiting issues:**
  ```python
  # Adjust rate limits in config
  JOBSPY_CONFIG = {
      "rate_limit_delay": 10,  # seconds between requests
      "max_retries": 3,
      "timeout": 60
  }
  ```

- **Site-specific blocks:**
  ```bash
  # Use preset with fewer sites
  python main.py TestProfile --action jobspy-pipeline --sites indeed,linkedin
  ```

### JobSpy Configuration Errors
**Symptoms:** "Invalid configuration" errors, unexpected behavior
```python
# Validate configuration
from src.config.jobspy_integration_config import validate_config

config = {
    "sites": ["indeed", "linkedin"],
    "locations": ["New York, NY"],
    "search_terms": ["python developer"],
    "country_code": "USA"
}

is_valid, errors = validate_config(config)
if not is_valid:
    print("Config errors:", errors)
```

---

## 3. AI Service Issues <a name="ai-service-issues"></a>

### AI Processing Failures
**Symptoms:** Jobs not getting compatibility scores, AI analysis stuck
```python
# Test AI service connectivity
from src.services.ai_integration_service import AIIntegrationService

ai_service = AIIntegrationService("TestProfile")
test_result = await ai_service.test_connection()
print(f"AI Service Status: {test_result}")
```

**Solutions:**
- **Memory issues:**
  ```python
  # Reduce batch size for AI processing
  AI_CONFIG = {
      "batch_size": 25,  # Reduced from 50
      "max_concurrent": 2,  # Reduced from 4
      "timeout": 120
  }
  ```

- **Model loading errors:**
  ```bash
  # Clear AI cache and restart
  rm -rf cache/embeddings/*
  python main.py TestProfile --action analyze-jobs --force-refresh
  ```

### Semantic Scoring Issues
**Symptoms:** All jobs getting same score, unrealistic compatibility ratings
```python
# Debug semantic scoring
from src.services.ai_integration_service import AIIntegrationService

ai_service = AIIntegrationService("TestProfile")
debug_scores = await ai_service.debug_semantic_scoring(
    job_text="Python developer position",
    profile_keywords=["python", "developer", "backend"]
)
print("Debug scores:", debug_scores)
```

---

## 4. Dashboard Problems <a name="dashboard-problems"></a>

### Dash Dashboard Issues
**Symptoms:** Dashboard not starting, component errors, data not loading
```bash
# Test dashboard startup
conda run -n auto_job python src/dashboard/dash_app/app.py

# Check dashboard port (default 8050)
curl http://localhost:8050

# Use VS Code task
# Ctrl+Shift+P → Tasks: Run Task → "Start Dash Dashboard"
```

**Solutions:**
- **Port conflicts:**
  ```bash
  # Check what's using port 8050
  netstat -tulpn | grep :8050
  
  # Kill processes using the port
  lsof -ti:8050 | xargs kill -9
  ```

- **Component import errors:**
  ```python
  # Test component imports
  from src.dashboard.dash_app.components.sidebar import create_sidebar
  from src.dashboard.dash_app.layouts.jobs_layout import create_jobs_layout
  print("Dashboard components loaded successfully")
  ```

- **Data loading issues:**
  ```python
  # Test data loading
  from src.core.job_database import JobDB
  
  db = JobDB("TestProfile")
  connection_status = db.test_connection()
  print(f"Database Status: {connection_status}")
  ```

### Dashboard Performance Issues
**Symptoms:** Slow loading, high memory usage, unresponsive interface
```python
# Optimize dashboard configuration
DASH_CONFIG = {
    "serve_locally": True,
    "suppress_callback_exceptions": True,
    "update_title": None,  # Disable title updates for performance
}
```

# Check Node.js version
node --version  # Should be 16+ or 18+

# Debug build
npm run dev --verbose
```

---

## 5. Multi-Site Scraping Issues <a name="multi-site-scraping-issues"></a>

### Parallel Worker Failures
**Symptoms:** Some workers failing, inconsistent results
```python
# Debug worker coordination
from src.scrapers.multi_site_jobspy_workers import MultiSiteJobSpyWorkers

workers = MultiSiteJobSpyWorkers(config)
worker_status = await workers.diagnose_workers()
for site, status in worker_status.items():
    print(f"{site}: {status}")
```

**Solutions:**
- **Reduce concurrency:**
  ```python
  # Lower concurrent workers
  config.max_concurrent_workers = 2  # Instead of 4
  ```

- **Site-specific timeouts:**
  ```python
  SITE_TIMEOUTS = {
      "indeed": 60,
      "linkedin": 90,  # LinkedIn often slower
      "glassdoor": 60,
      "zip_recruiter": 45
  }
  ```
**Solutions:**
- Rotate user agents
- Implement proxy rotation
- Increase delay between requests

---

## 3. Dashboard Errors <a name="dashboard-errors"></a>

### Dashboard Not Loading
**Symptoms:** Blank screen, unresponsive UI, port conflicts
```bash
# Check port usage and kill conflicting processes
netstat -ano | findstr :8501  # Windows
lsof -i :8501                 # Linux/Mac
kill -9 $(lsof -t -i:8501)   # Kill process using port

# Start dashboard with different configuration
streamlit run src/dashboard/unified_dashboard.py --server.port 8502 --server.headless true
```

**Common Dashboard Fixes:**
```python
# Fix Streamlit configuration issues
# Create .streamlit/config.toml
[server]
port = 8501
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

# Clear Streamlit cache
import streamlit as st
st.cache_data.clear()
st.cache_resource.clear()
```

### Data Not Displaying
**Symptoms:** Empty job lists, missing metrics, database connection errors
```python
# Debug database connection
from src.core.job_database import get_job_db

def debug_database():
    try:
        db = get_job_db("Nirajan")
        stats = db.get_stats()
        print(f"Database stats: {stats}")
        
        # Test basic operations
        jobs = db.get_jobs_by_status("scraped", limit=5)
        print(f"Found {len(jobs)} scraped jobs")
        
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

# Fix common database issues
def fix_database_issues():
    # Recreate database if corrupted
    import os
    db_path = "data/jobs.db"
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup"
        os.rename(db_path, backup_path)
        print(f"Database backed up to {backup_path}")
    
    # Initialize fresh database
    db = get_job_db("Nirajan")
    print("Fresh database initialized")
```

### Dashboard Performance Issues
**Symptoms:** Slow loading, high memory usage, UI freezing
```python
# Optimize dashboard performance
import streamlit as st

# Use session state for expensive operations
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_job_data():
    db = get_job_db("Nirajan")
    return db.get_jobs_by_status("scraped", limit=100)

# Implement pagination for large datasets
def paginate_jobs(jobs, page_size=20):
    if 'page_num' not in st.session_state:
        st.session_state.page_num = 0
    
    start_idx = st.session_state.page_num * page_size
    end_idx = start_idx + page_size
    return jobs[start_idx:end_idx]

# Reduce auto-refresh frequency
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# Only refresh every 30 seconds
if time.time() - st.session_state.last_refresh > 30:
    st.rerun()
    st.session_state.last_refresh = time.time()
```

---

## 4. Scraper Issues <a name="scraper-issues"></a>

### JobSpy Installation Issues
**Symptoms:** Import errors, module not found, scraping failures
```bash
# Check JobSpy installation
python -c "from jobspy import scrape_jobs; print('JobSpy Available')"

# Verify Python version compatibility
python --version  # Requires 3.10+
```

**Solutions:**
```bash
# Install/reinstall JobSpy
pip uninstall python-jobspy
pip install python-jobspy

# Fix common dependency conflicts
pip install --upgrade requests beautifulsoup4 lxml

# Test basic functionality
python -c "from jobspy import scrape_jobs; jobs = scrape_jobs(site_name='indeed', search_term='python', location='Canada', results_wanted=5); print(f'Found {len(jobs)} jobs')"
```

### Eluta Scraper Browser Issues
**Symptoms:** Browser crashes, tab management problems, popup handling failures
```bash
# Install/reinstall Playwright browsers
playwright uninstall
playwright install chromium
playwright install-deps  # Linux dependencies
```

**Solutions:**
```python
# Fix tab management issues
eluta_config = {
    "max_tabs": 3,  # Reduce if memory issues
    "headless": True,  # Always use headless in production
    "timeout": 30,  # Increase for slow connections
    "delay": 2.0   # Increase delay between requests
}

# Handle popup issues
async def handle_popups(page):
    try:
        # Close common popups
        await page.click('button[aria-label="Close"]', timeout=2000)
        await page.click('.popup-close', timeout=2000)
    except:
        pass  # Ignore if no popups
```

### Dual Scraper Fallback Issues
**Symptoms:** Both scrapers failing, no jobs found, fallback not triggering
```python
# Debug fallback logic
async def debug_scraper_fallback():
    try:
        # Test JobSpy first
        jobs = await jobspy_scraper.scrape_jobs(['python'], limit=5)
        if len(jobs) >= 3:  # Minimum threshold
            return jobs
        logger.warning(f"JobSpy returned only {len(jobs)} jobs, trying Eluta")
    except Exception as e:
        logger.error(f"JobSpy failed: {e}")
    
    # Fallback to Eluta
    try:
        jobs = await eluta_scraper.scrape_all_keywords(limit=10)
        logger.info(f"Eluta fallback returned {len(jobs)} jobs")
        return jobs
    except Exception as e:
        logger.error(f"Both scrapers failed: {e}")
        return []

# Network connectivity check
def check_connectivity():
    test_urls = [
        "https://www.indeed.com",
        "https://www.eluta.ca",
        "https://www.google.com"
    ]
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return True
        except:
            continue
    return False
```

### Worker Pool Issues
**Symptoms:** Workers hanging, memory leaks, resource exhaustion
```python
# Fix worker pool configuration
async def fix_worker_pools():
    # Limit concurrent workers
    max_workers = min(6, os.cpu_count())  # Don't exceed CPU cores
    
    # Implement proper cleanup
    async with asyncio.Semaphore(max_workers) as semaphore:
        async with semaphore:
            # Worker logic with timeout
            try:
                result = await asyncio.wait_for(
                    worker_function(), 
                    timeout=60  # 1 minute timeout per job
                )
                return result
            except asyncio.TimeoutError:
                logger.error("Worker timeout - killing task")
                return None

# Memory management for large datasets
def process_in_batches(jobs, batch_size=50):
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        yield process_batch(batch)
        # Force garbage collection between batches
        import gc
        gc.collect()
```

---

## 5. Performance Optimization <a name="performance-optimization"></a>

### High Memory Usage
**Symptoms:** System slowdown, out of memory errors, browser crashes
```python
# Monitor memory usage
import psutil
import gc

def monitor_memory():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.1f} MB")
    
    if memory_mb > 1000:  # Over 1GB
        print("High memory usage detected - forcing cleanup")
        gc.collect()
        return True
    return False

# Fix memory leaks in scrapers
async def scrape_with_memory_management():
    browser = None
    try:
        browser = await playwright.chromium.launch()
        
        # Process in smaller batches
        for batch in chunked(job_urls, 10):
            results = await process_batch(batch)
            
            # Force cleanup between batches
            gc.collect()
            
            # Monitor memory and restart browser if needed
            if monitor_memory():
                await browser.close()
                browser = await playwright.chromium.launch()
                
    finally:
        if browser:
            await browser.close()
```

### CPU Performance Issues
**Symptoms:** High CPU usage, slow processing, system unresponsiveness
```python
# Optimize CPU-intensive operations
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Use thread pool for CPU-bound tasks
def cpu_intensive_task(job_data):
    # Process job data
    return processed_data

async def process_jobs_optimized(jobs):
    # Limit concurrent CPU tasks
    max_workers = min(4, os.cpu_count() // 2)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, cpu_intensive_task, job)
            for job in jobs
        ]
        
        # Process with progress tracking
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            results.append(result)
            
            # Add small delay to prevent CPU saturation
            await asyncio.sleep(0.01)
        
        return results

# Two-stage processing optimization
async def optimize_two_stage_processing():
    # Stage 1: Fast CPU processing (limit workers)
    stage1_workers = min(6, os.cpu_count())
    
    # Stage 2: GPU processing (if available)
    if torch.cuda.is_available():
        # Use GPU for Text analysis
        batch_size = 32  # Optimize for GPU memory
    else:
        # Fallback to CPU with limited workers
        stage1_workers = min(3, os.cpu_count() // 2)
```

### Database Performance Issues
**Symptoms:** Slow queries, database locks, connection timeouts
```python
# Optimize database operations
def optimize_database_performance():
    # Create indexes for common queries
    with db._get_connection() as conn:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status_date ON jobs(status, scraped_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company_title ON jobs(company, title)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_match_score ON jobs(match_score DESC)")
        conn.commit()

# Batch database operations
def batch_database_operations(jobs, batch_size=100):
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        
        with db._get_connection() as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO jobs (...) VALUES (...)",
                [job_to_tuple(job) for job in batch]
            )
            conn.commit()
        
        # Small delay between batches
        time.sleep(0.1)

# Connection pool optimization
def optimize_connection_pool():
    # Increase pool size for high-load scenarios
    pool_size = min(10, os.cpu_count() * 2)
    
    # Implement connection health checks
    def test_connection(conn):
        try:
            conn.execute("SELECT 1")
            return True
        except:
            return False
```

---

## 6. Diagnostic Tools <a name="diagnostic-tools"></a>

### System Health Checks
```python
# Comprehensive system diagnostics
def run_system_diagnostics():
    print("🔍 JobLens System Diagnostics")
    print("=" * 50)
    
    # 1. Python Environment
    import sys
    print(f"Python Version: {sys.version}")
    print(f"Python Path: {sys.executable}")
    
    # 2. Database Health
    try:
        from src.core.job_database import get_job_db
        db = get_job_db("Nirajan")
        stats = db.get_stats()
        print(f"✅ Database: {stats['total_jobs']} jobs, {stats['database_size_mb']:.1f} MB")
    except Exception as e:
        print(f"❌ Database Error: {e}")
    
    # 3. Scraper Availability
    try:
        from jobspy import scrape_jobs
        print("✅ JobSpy: Available")
    except ImportError:
        print("❌ JobSpy: Not installed")
    
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright: Available")
    except ImportError:
        print("❌ Playwright: Not installed")
    
    # 4. System Resources
    import psutil
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('.')
    
    print(f"💻 CPU Usage: {cpu_percent}%")
    print(f"🧠 Memory: {memory.percent}% ({memory.available // 1024 // 1024} MB free)")
    print(f"💾 Disk: {disk.percent}% ({disk.free // 1024 // 1024 // 1024} GB free)")
    
    # 5. Network Connectivity
    import requests
    try:
        response = requests.get("https://www.google.com", timeout=5)
        print("✅ Network: Connected")
    except:
        print("❌ Network: Connection issues")

# Run diagnostics
if __name__ == "__main__":
    run_system_diagnostics()
```

### Component-Specific Diagnostics
```python
# Test individual components
async def test_scrapers():
    print("🕷️ Testing Scrapers")
    
    # Test JobSpy
    try:
        from jobspy import scrape_jobs
        jobs = scrape_jobs(
            site_name="indeed",
            search_term="python",
            location="Canada",
            results_wanted=3
        )
        print(f"✅ JobSpy: Found {len(jobs)} jobs")
    except Exception as e:
        print(f"❌ JobSpy Error: {e}")
    
    # Test Eluta
    try:
        from src.scrapers.unified_eluta_scraper import ElutaScraper
        scraper = ElutaScraper("Nirajan", {"pages": 1, "jobs": 5})
        jobs = await scraper.scrape_all_keywords(limit=5)
        print(f"✅ Eluta: Found {len(jobs)} jobs")
    except Exception as e:
        print(f"❌ Eluta Error: {e}")

def test_database():
    print("🗄️ Testing Database")
    
    try:
        from src.core.job_database import get_job_db
        db = get_job_db("test_profile")
        
        # Test basic operations
        test_job = {
            "job_id": "test_123",
            "title": "Test Job",
            "company": "Test Company",
            "url": "https://test.com/job/123"
        }
        
        # Add job
        success = db.add_job(test_job)
        print(f"✅ Add Job: {'Success' if success else 'Failed'}")
        
        # Retrieve job
        retrieved = db.get_job("test_123")
        print(f"✅ Get Job: {'Success' if retrieved else 'Failed'}")
        
        # Get stats
        stats = db.get_stats()
        print(f"✅ Database Stats: {stats['total_jobs']} total jobs")
        
    except Exception as e:
        print(f"❌ Database Error: {e}")

def test_dashboard():
    print("📊 Testing Dashboard Components")
    
    try:
        import streamlit as st
        print("✅ Streamlit: Available")
        
        # Test dashboard components
        from src.dashboard.components.Improved_job_table import render_Improved_job_table
        print("✅ Job Table Component: Available")
        
        from src.dashboard.components.scraping_config_component import render_scraping_config
        print("✅ Scraping Config Component: Available")
        
    except Exception as e:
        print(f"❌ Dashboard Error: {e}")
```

### Performance Benchmarking
```python
# Benchmark system performance
import time
import asyncio

async def benchmark_scrapers():
    print("⚡ Performance Benchmarks")
    
    # Benchmark JobSpy
    start_time = time.time()
    try:
        from jobspy import scrape_jobs
        jobs = scrape_jobs(
            site_name="indeed",
            search_term="python",
            location="Canada",
            results_wanted=10
        )
        jobspy_time = time.time() - start_time
        jobspy_rate = len(jobs) / jobspy_time if jobspy_time > 0 else 0
        print(f"📈 JobSpy: {len(jobs)} jobs in {jobspy_time:.1f}s ({jobspy_rate:.1f} jobs/sec)")
    except Exception as e:
        print(f"❌ JobSpy Benchmark Failed: {e}")
    
    # Benchmark Eluta
    start_time = time.time()
    try:
        from src.scrapers.unified_eluta_scraper import ElutaScraper
        scraper = ElutaScraper("Nirajan", {"pages": 1, "jobs": 10})
        jobs = await scraper.scrape_all_keywords(limit=10)
        eluta_time = time.time() - start_time
        eluta_rate = len(jobs) / eluta_time if eluta_time > 0 else 0
        print(f"📈 Eluta: {len(jobs)} jobs in {eluta_time:.1f}s ({eluta_rate:.1f} jobs/sec)")
    except Exception as e:
        print(f"❌ Eluta Benchmark Failed: {e}")

# Database performance test
def benchmark_database():
    print("🗄️ Database Performance")
    
    from src.core.job_database import get_job_db
    db = get_job_db("benchmark_test")
    
    # Test batch insert performance
    test_jobs = [
        {
            "job_id": f"test_{i}",
            "title": f"Test Job {i}",
            "company": f"Company {i}",
            "url": f"https://test.com/job/{i}"
        }
        for i in range(100)
    ]
    
    start_time = time.time()
    for job in test_jobs:
        db.add_job(job)
    insert_time = time.time() - start_time
    
    print(f"📈 Database: 100 inserts in {insert_time:.1f}s ({100/insert_time:.1f} ops/sec)")
    
    # Test query performance
    start_time = time.time()
    jobs = db.get_jobs_by_status("scraped", limit=100)
    query_time = time.time() - start_time
    
    print(f"📈 Database: Query 100 jobs in {query_time:.3f}s")
```

---

## 7. FAQ <a name="faq"></a>

### How do I reset the system completely?
```python
# Complete system reset script
def reset_system():
    import os
    import shutil
    
    print("🔄 Resetting JobLens System")
    
    # 1. Backup current data
    backup_dir = f"backup_{int(time.time())}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup database
    if os.path.exists("data/jobs.db"):
        shutil.copy2("data/jobs.db", f"{backup_dir}/jobs.db")
        print(f"✅ Database backed up to {backup_dir}/")
    
    # 2. Clear generated documents
    for profile_dir in os.listdir("profiles"):
        docs_path = f"profiles/{profile_dir}/generated_documents"
        if os.path.exists(docs_path):
            shutil.rmtree(docs_path)
            print(f"✅ Cleared documents for {profile_dir}")
    
    # 3. Clear cache directories
    cache_dirs = ["cache", "temp", "logs"]
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            os.makedirs(cache_dir, exist_ok=True)
            print(f"✅ Cleared {cache_dir}/")
    
    # 4. Reset database
    if os.path.exists("data/jobs.db"):
        os.remove("data/jobs.db")
        print("✅ Database reset")
    
    # 5. Initialize fresh system
    from src.core.job_database import get_job_db
    db = get_job_db("Nirajan")  # Initialize fresh database
    print("✅ Fresh database initialized")
    
    print(f"🎉 System reset complete. Backup saved to {backup_dir}/")

# Run reset
if __name__ == "__main__":
    reset_system()
```

### Why is my dashboard showing display issues?
```python
# Fix common dashboard display problems
import streamlit as st

# 1. Fix dark theme issues
st.markdown("""
<style>
    .main { background-color: #0e1117; color: #fafafa; }
    .stSelectbox > div > div { background-color: #262730; }
    .stTextInput > div > div > input { background-color: #262730; color: #fafafa; }
    .stDataFrame { background-color: #262730; }
</style>
""", unsafe_allow_html=True)

# 2. Fix table display issues
def fix_table_display(df):
    # Ensure proper column types
    if 'match_score' in df.columns:
        df['match_score'] = pd.to_numeric(df['match_score'], errors='coerce')
    
    # Handle missing values
    df = df.fillna('')
    
    # Limit text length for display
    for col in ['title', 'company', 'summary']:
        if col in df.columns:
            df[col] = df[col].astype(str).str[:100] + '...'
    
    return df

# 3. Fix memory issues with large datasets
@st.cache_data(ttl=300)
def load_jobs_cached(status, limit=100):
    from src.core.job_database import get_job_db
    db = get_job_db("Nirajan")
    return db.get_jobs_by_status(status, limit=limit)
```

### Common Error Messages and Solutions

**Error: "ModuleNotFoundError: No module named 'jobspy'"**
```bash
pip install python-jobspy
# If still failing, try:
pip install --upgrade python-jobspy
python -c "from jobspy import scrape_jobs; print('Success')"
```

**Error: "playwright._impl._api_types.Error: Browser closed"**
```python
# Fix browser lifecycle management
async def fix_browser_issues():
    browser = None
    try:
        browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        # Use browser...
    finally:
        if browser and not browser.is_closed():
            await browser.close()
```

**Error: "sqlite3.OperationalError: database is locked"**
```python
# Fix database locking issues
import time
import sqlite3

def safe_database_operation(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return operation()
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                continue
            raise
```

**Error: "streamlit.errors.StreamlitAPIException: st.cache_data"**
```python
# Fix Streamlit caching issues
import streamlit as st

# Clear all caches
st.cache_data.clear()
st.cache_resource.clear()

# Use proper cache decorators
@st.cache_data(ttl=300, show_spinner=False)
def cached_function(param):
    return expensive_operation(param)
```

### Where are active issues tracked?
- **Current Issues**: [ISSUE_TRACKER.md](ISSUE_TRACKER.md)
- **Performance Issues**: Check system diagnostics above
- **Known Limitations**: See [ARCHITECTURE.md](ARCHITECTURE.md#limitations)
- **Feature Requests**: Submit via GitHub issues

---

**Maintainer:** JobLens Development Team  
**Documentation:** [ARCHITECTURE.md](ARCHITECTURE.md) | [DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md)