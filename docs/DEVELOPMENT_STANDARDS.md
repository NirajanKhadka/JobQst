---
post_title: "JobLens Development Standards - Reference"
author1: "Nirajan Khadka"
post_slug: "development-standards-complete"
microsoft_alias: "nirajank"
featured_image: ""
categories: ["standards", "development", "complete"]
tags: ["standards", "python", "quality", "jobspy", "eluta", "dashboard", "scraper", "applier", "testing"]
ai_note: "Complete consolidated development standards covering all modules and components."
summary: "Development standards for JobLens components including core and module-specific guidelines"
post_date: "2025-07-17"
---

## 🛠️ JobLens Development Standards

> **Under any circumstances, the user should ask the AI to edit these standards.**

**Last Updated:** July 17, 2025  
**Status:** 🟢 **ACTIVE** - Complete Development Standards (7-Doc Policy)

> **NOTICE:** This document consolidates all development standards and is the single 
> source of truth for development practices in JobLens.

---

## 🎯 **Core Philosophy**

- **Stability First**: Never break existing functionality
- **User Experience**: Prioritize practical functionality over complex features
- **Maintainability**: Write code that future-me can understand
- **Documentation**: If it's not documented, it doesn't exist
- **Incremental Progress**: Small, tested changes over large refactors

---

## 🏗️ **Architecture Principles**

### **🔧 SOLID Principles Applied**
- **Single Responsibility**: Each component has ONE clear purpose
- **Open/Closed**: Extend functionality through plugins/modules
- **Liskov Substitution**: All implementations work the same way
- **Interface Segregation**: Clear, minimal APIs
- **Dependency Inversion**: Depend on abstractions, not implementations

### **🏛️ Clean Architecture**
- **Separation of Concerns**: UI ≠ Business Logic ≠ Data Access
- **Domain-Driven Design**: Code structure reflects business concepts
- **Layered Architecture**: Clear boundaries between layers

---

## ⚙️ **Application Orchestration Standards**

### **Job Application Processor/Orchestrator**
- All automated job applications must be managed by a background orchestration service (e.g., `ApplierOrchestrationService`).
- The orchestrator must:
  - Support queueing of job applications with configurable priorities (e.g., match score, deadline).
  - Enforce rate limiting (e.g., max N applications per hour) to avoid spam detection.
  - Track and expose real-time status for each job application (Queued, In Progress, Completed, Failed).
  - Provide error handling and retry logic (with exponential backoff for failures).
  - Allow manual override (pause/resume/cancel individual applications).
  - Maintain a complete audit trail of all application attempts.
- The dashboard must display per-job status and allow triggering individual applications ("Apply Now").
- All orchestration logic should be modular and testable, with clear API boundaries.

### **Document Generation Orchestration**
- Resume and cover letter generation must be handled by a dedicated orchestration layer (e.g., worker pool, document generation queue).
- The document generator must:
  - Support parallel/concurrent generation (e.g., up to 5 workers).
  - Use only real profile data (no placeholders or fabricated content).
  - Provide reliable error handling and clear status reporting for each document.
  - Save all generated files in a structured, job-specific output directory.
  - Expose API or CLI for both batch and single-document generation.
  - Ensure all output is ATS-friendly and meets formatting standards.
- The orchestration layer must be able to recover from worker failures and retry as needed.
- All document generation orchestration code must be covered by integration tests.

---

## 💻 **Code Quality Standards**

### **🐍 Python Standards**
```python
## ✅ GOOD: Descriptive names with type hints
def scrape_job_listings(keywords: List[str], location: str) -> List[JobListing]:
    """Scrape job listings for given keywords and location."""
    pass

## ✅ GOOD: Error handling with context
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    logger.error(f"Failed to fetch {url}: {e}")
    raise ScrapingError(f"Network error accessing {url}") from e
```

### **🔍 Function Design Rules**
- Max 20-30 lines per function
- Single purpose per function
- Clear input/output contracts
- Descriptive names that explain intent
- Proper error handling with context

### **📏 File Size Standards**
- **Functions**: Max 20-30 lines
- **Utility Modules**: Max 300 lines for maintainability
- **Test Files**: Max 500 lines (consider splitting if larger)
- **🚨 CRITICAL THRESHOLD**: Files >1000 lines require immediate refactoring
- **⚠️ WARNING THRESHOLD**: Files >500 lines should be reviewed for splitting

### **🎯 Monolith Prevention**
- **Red Flag**: Any single file >1000 lines
- **Solution**: Extract to separate services or modules
- **Architecture**: Prefer composition over large inheritance hierarchies

---

## 📁 **Project Organization**

### **📂 File Structure**
```
docs/                          ## ALL documentation here
├── README.md                  ## Documentation index  
├── DEVELOPER_GUIDE.md         ## Setup and workflow
├── DEVELOPMENT_STANDARDS.md   ## This file - all standards
└── ...                        ## Other technical docs

src/                           ## ALL source code here
├── core/                      ## Core system components
├── scrapers/                  ## Web scraping (one per site)
├── ats/                       ## ATS integrations (one per system)
├── dashboard/                 ## UI components only
└── utils/                     ## Shared utilities

tests/                         ## Test files mirror src/ structure
profiles/                      ## User configuration
```

### **🏷️ Naming Conventions**
- **Files**: `snake_case.py` (e.g., `eluta_scraper.py`)
- **Classes**: `PascalCase` (e.g., `JobListing`, `ElutaScraper`)
- **Functions**: `snake_case` (e.g., `scrape_job_details`)
- **Variables**: `snake_case` (e.g., `job_title`, `match_score`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)

---

## ✅ **Quality Gates (MANDATORY)**

**ALL quality issues are BLOCKING. No exceptions.**
- [ ] **Functionality**: Works as intended
- [ ] **Error Handling**: Graceful failure with useful messages
- [ ] **Performance**: No significant slowdown
- [ ] **Code Quality**: Passes all linters (black, flake8, mypy)
- [ ] **Type Hints**: All functions properly typed
- [ ] **Real Data**: No placeholders or fabricated content
- [ ] **Documentation**: Updated relevant docs
- [ ] **Testing**: Added/updated tests for changes
- [ ] **CI/CD**: All tests must pass in CI before merge; code must be auto-formatted and linted in CI.

---

## 🚨 **Security Standards**
- Validate and sanitize all user and external input.
- Never hardcode credentials, API keys, or secrets; use environment variables or secure config.
- Never expose sensitive data in logs, error messages, or UI.
- Respect robots.txt, rate limits, and site terms for all integrations.
- Use dependency scanning and keep dependencies up to date.
- All code must be reviewed for security vulnerabilities before merge.

---

## 🚨 **Error Handling Standards**

### **🛡️ Defensive Programming**
```python
## ✅ GOOD: Validate inputs
def scrape_job_site(url: str, timeout: int = 30) -> List[JobListing]:
    if not url or not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL: {url}")
    ## ... implementation

## ✅ GOOD: Graceful degradation
def get_job_description(job_url: str) -> str:
    try:
        return extract_description(job_url)
    except Exception as e:
        logger.warning(f"Failed to extract description from {job_url}: {e}")
        return "Description not available"
```

### **📊 Logging Standards**
```python
import logging

logger = logging.getLogger(__name__)

## Use appropriate log levels
logger.debug("Detailed debugging information")
logger.info("General information about operation")
logger.warning("Something unexpected but recoverable")
logger.error("Error that affects functionality")
logger.critical("Serious error that may abort operation")
```

---

## 🔄 **Development Workflow**

### **📝 Commit Message Standards**
```
✅ GOOD:
feat: Add Indeed scraper with rate limiting
fix: Handle timeout errors in Eluta scraper  
docs: Update API reference for job filtering
refactor: Extract common scraping utilities

❌ BAD:
"Fixed stuff"
"Update"
"Changes"
```

### **🌿 Branch Management**
- **main**: Stable, working code only
- **feature/**: New features (e.g., `feature/indeed-scraper`)
- **fix/**: Bug fixes (e.g., `fix/dashboard-port-conflict`)
- **docs/**: Documentation updates (e.g., `docs/api-reference`)

---

## 🖥️ **Dashboard Module Standards**

### **Python & Streamlit Rules**
- Use descriptive, intent-revealing names for all UI elements and callbacks.
- All Streamlit widgets must have unique keys.
- Avoid global state; use session state or dependency injection.
- UI logic and business logic must be separated (no data processing in UI callbacks).
- Use type hints for all functions.
- All public functions/classes must have docstrings.
- Limit UI callback functions to 30 lines or less.
- Use early returns to reduce nesting in callbacks.
- Handle all user input validation and error display gracefully.
- All UI must be responsive and work across major browsers and devices.
- State management must be explicit and predictable (use Streamlit session state).

### **Dashboard Documentation & Comments**
- Every dashboard component must have a docstring explaining its purpose.
- Inline comments for any non-obvious UI logic.
- Document all custom Streamlit components or wrappers.

### **Dashboard Testing & Quality**
- All dashboard logic must be covered by integration or UI tests where feasible.
- No placeholder/fake data in production UI.
- All UI changes must be reviewed for accessibility, responsiveness, and cross-browser compatibility.
- All UI must handle errors gracefully and provide clear user feedback.

### **Dashboard Performance**
- Minimize unnecessary re-renders (use st.session_state, memoization, etc.).
- Avoid blocking the main thread with heavy computation.
- Profile UI performance with Streamlit profiler or browser dev tools.

### **Dashboard Security**
- Never expose sensitive data in the UI.
- Validate all user inputs before processing.
- Use secure session management for any authentication.

---

## 🗺️ **Scraper Module Standards**

### **Python Rules**
- Use descriptive, intent-revealing names for all classes, functions, and variables.
- All scrapers must implement the common scraper interface.
- No global variables; use dependency injection for configuration.
- Use type hints for all functions and method signatures.
- All public functions/classes must have docstrings.
- Limit scraper methods to 30 lines or less.
- Handle all network errors and timeouts with retries and logging.
- Never hardcode credentials or API keys.
- Implement anti-captcha/anti-bot strategies where allowed (e.g., delays, user agents, headless detection avoidance).
- All scraped data must be validated and conform to a defined schema.
- All scrapers must expose health/heartbeat endpoints or logs for monitoring.
- All scrapers must have a documented update/maintenance strategy for site changes.

### **Dual Scraper Architecture Standards** *(CORE)*
```python
# ✅ GOOD: Primary + Fallback Pattern
async def scrape_jobs(keywords: List[str]) -> List[JobListing]:
    try:
        # Primary: JobSpy multi-site
        jobs = await jobspy_scraper.scrape_multi_site(keywords)
        if len(jobs) >= MIN_JOBS_THRESHOLD:
            return jobs
    except Exception as e:
        logger.warning(f"JobSpy failed: {e}")
    
    # Fallback: Eluta scraper
    return await eluta_scraper.scrape_all_keywords(keywords)

# ✅ GOOD: Worker Pool Management
async def coordinate_workers(configs: List[Dict], max_workers: int = 3):
    semaphore = asyncio.Semaphore(max_workers)
    async with semaphore:
        # Process with resource limits
        pass
```

**Rules:**
- JobSpy primary, Eluta fallback - never both simultaneously
- Max 3 concurrent workers to avoid rate limiting
- Always implement Automated fallback with thresholds
- Monitor success rates: JobSpy >80%, Eluta >90%

### **Scraper Documentation & Comments**
- Every scraper class must have a docstring explaining its target site and logic.
- Inline comments for any non-obvious parsing or anti-bot logic.
- Document all required environment variables or config options.

### **Scraper Testing & Quality**
- All scrapers must have unit tests for core logic and integration tests for site connectivity.
- No placeholder/fake data in production scrapers.
- All changes must be reviewed for anti-bot compliance and site terms.
- All scrapers must be monitored for health and error rates.

### **Scraper Performance**
- Use async or batch requests where possible.
- Minimize memory and bandwidth usage (avoid loading full pages if not needed).
- Profile scraper performance with cProfile or Py-Spy.

### **Scraper Security**
- Respect robots.txt and site terms of service.
- Implement proper rate limiting to avoid being blocked.
- Use secure methods for any authentication or API access.

---

## 📄 **Document Generation Standards**

### **Python Rules**
- Use descriptive, intent-revealing names for all generation classes, functions, and variables.
- All document generators must implement a common interface for generation and validation.
- No global variables; use dependency injection for configuration and templates.
- Use type hints for all functions and method signatures.
- All public functions/classes must have docstrings.
- Limit document generation functions to 30 lines or less.
- Handle all file I/O, template, and API errors with retries and logging.
- Never hardcode credentials or API keys.
- All generated content must use real profile data, never placeholder text.
- All document generation must be reproducible and deterministic.
- All generators must validate output before saving (no placeholder detection).

### **Document Quality Requirements**
- Generated resumes must be ATS-compatible and professionally formatted.
- Generated cover letters must be personalized and relevant to the specific job.
- All documents must pass automated quality checks before being saved.
- No template placeholder text (e.g., "[Your Name]", "{{company}}") in final output.
- All documents must be saved in both source format and PDF.

### **Document Documentation & Comments**
- Every document generator must have a docstring explaining its purpose and output format.
- Inline comments for any non-obvious template logic or transformations.
- Document all required profile fields and template variables.

### **Document Testing & Quality**
- All document generators must have unit tests for core logic and integration tests for end-to-end generation.
- No placeholder/fake data in production document generators.
- All changes must be reviewed for document quality and professional standards.
- All generators must be monitored for success rates and output quality.

### **Document Performance**
- Use efficient template engines and avoid unnecessary file I/O.
- Profile document generation performance and optimize for speed.
- Support parallel/concurrent generation where possible.

---

## 🤖 **Application Applier Module Standards**

### **Python Rules**
- Use descriptive, intent-revealing names for all classes, functions, and variables.
- All applier services must implement clear interfaces for queuing, processing, and status tracking.
- No global variables; use dependency injection for configuration and state.
- Use type hints for all functions and method signatures.
- All public functions/classes must have docstrings.
- Limit orchestration and worker functions to 30 lines or less.
- Handle all network, file, and API errors with retries, logging, and user feedback.
- Never hardcode credentials or API keys.
- All retry logic must be idempotent and safe for repeated execution.
- All concurrency (threads, async, processes) must be safe and avoid race conditions.

### **Orchestration Requirements**
- All job applications must be queued and processed asynchronously.
- Support priority-based processing (e.g., application deadline, match score).
- Implement comprehensive logging and audit trails for all application attempts.
- Provide real-time status updates for queued, processing, completed, and failed applications.
- Support manual intervention (pause, resume, cancel) for any queued application.

### **Applier Documentation & Comments**
- Every applier class must have a docstring explaining its target ATS and application flow.
- Inline comments for any non-obvious form-filling or automation logic.
- Document all required configuration and environment variables.

### **Applier Testing & Quality**
- All appliers must have unit tests for core logic and integration tests for ATS connectivity.
- No placeholder/fake data in production appliers.
- All changes must be reviewed for ATS compliance and application success rates.
- All appliers must be monitored for health and success rates.

### **Applier Performance**
- Use efficient form-filling strategies and minimize redundant operations.
- Profile applier performance and optimize for speed and reliability.
- Support parallel processing where ATS systems allow.

---

## 🗄️ **Database Best Practices**

### **Connection Management**
```python
# ✅ GOOD: Connection pooling (from ModernJobDatabase)
@contextmanager
def _get_connection(self):
    conn = self._connection_pool.get(timeout=5)
    try:
        yield conn
    finally:
        self._connection_pool.put(conn)

# ✅ GOOD: Batch operations
def add_jobs_batch(self, jobs: List[Dict]) -> int:
    with self._get_connection() as conn:
        conn.executemany("INSERT INTO jobs (...) VALUES (...)", jobs)
        conn.commit()
        return len(jobs)
```

**Rules:**
- Always use connection pooling (max 5 connections)
- Batch database operations when possible
- Use transactions for multi-step operations
- Index frequently queried fields (url, title, company)

---

## ⚡ **Async/Concurrency Best Practices**

### **Worker Pool Patterns**
```python
# ✅ GOOD: Async worker with queue
async def worker_loop(worker_id: int, job_queue: asyncio.Queue):
    while True:
        try:
            job_url = await job_queue.get()
            result = await process_job(job_url)
            job_queue.task_done()
        except Exception as e:
            logger.error(f"Worker {worker_id} failed: {e}")

# ✅ GOOD: Resource cleanup
async def scrape_with_cleanup():
    browser = None
    try:
        browser = await playwright.chromium.launch()
        # ... scraping logic
    finally:
        if browser:
            await browser.close()
```

**Rules:**
- Max 6 workers for external scraping, 3 for Eluta
- Always use try/finally for resource cleanup
- Implement proper error propagation in worker pools
- Use asyncio.Semaphore for rate limiting

---

## 🚀 **Performance Standards**

### **Optimization Patterns**
```python
# ✅ GOOD: Two-stage processing
async def process_jobs_optimized(jobs: List[Dict]):
    # Stage 1: Fast CPU processing (10 workers)
    stage1_results = await cpu_process_batch(jobs, workers=10)
    
    # Stage 2: GPU Text analysis (if available)
    if torch.cuda.is_available():
        return await gpu_process_batch(stage1_results)
    return stage1_results

# ✅ GOOD: Memory-efficient processing
def process_large_dataset(jobs: List[Dict], batch_size: int = 50):
    for batch in chunked(jobs, batch_size):
        yield process_batch(batch)
```

**Rules:**
- Process in batches of 50 for memory efficiency
- Use CPU workers for fast filtering, GPU for Text analysis
- Profile with cProfile, optimize bottlenecks first
- Target: 3.5x performance improvement over single-threaded

---

## 🧪 **Testing Standards**

### **Essential Testing Patterns**
```python
# ✅ GOOD: Mock external services
@pytest.fixture
def mock_jobspy():
    with patch('src.scrapers.jobspy_scraper.JobSpyScraper') as mock:
        mock.return_value.scrape_jobs.return_value = SAMPLE_JOBS
        yield mock

# ✅ GOOD: Database testing with cleanup
@pytest.fixture
def test_db():
    db = get_job_db(":memory:")  # In-memory for tests
    yield db
    db.close()

# ✅ GOOD: Integration test pattern
async def test_complete_pipeline():
    pipeline = FastJobPipeline("test_profile")
    jobs = await pipeline.run_complete_pipeline(limit=5)
    assert len(jobs) > 0
    assert all(job.get('url') for job in jobs)
```

**Rules:**
- Mock all external services (JobSpy, Eluta, AI APIs)
- Use in-memory database for tests
- Test critical paths: scraping → processing → database
- Performance tests: measure jobs/second, memory usage

---

## 🔧 **Configuration Management**

### **Profile-Based Config Pattern**
```python
# ✅ GOOD: Environment-aware configuration
def load_config(profile_name: str, env: str = "dev") -> Dict:
    base_config = load_profile(profile_name)
    env_overrides = {
        "dev": {"headless": False, "max_workers": 2},
        "prod": {"headless": True, "max_workers": 6}
    }
    return {**base_config, **env_overrides.get(env, {})}

# ✅ GOOD: Validation at startup
def validate_config(config: Dict) -> None:
    required = ["keywords", "location", "max_jobs"]
    missing = [k for k in required if k not in config]
    if missing:
        raise ConfigError(f"Missing required config: {missing}")
```

**Rules:**
- Validate all configuration at startup
- Use environment-specific overrides (dev/prod)
- Never hardcode credentials - use environment variables
- Provide sensible defaults for all optional settings

---

## 📊 **Monitoring & Observability**

### **Structured Logging Pattern**
```python
# ✅ GOOD: Structured logging with context
logger = logging.getLogger(__name__)

def scrape_with_logging(site: str, keywords: List[str]):
    logger.info("Starting scrape", extra={
        "site": site,
        "keyword_count": len(keywords),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        results = scrape_site(site, keywords)
        logger.info("Scrape completed", extra={
            "site": site,
            "jobs_found": len(results),
            "success": True
        })
        return results
    except Exception as e:
        logger.error("Scrape failed", extra={
            "site": site,
            "error": str(e),
            "success": False
        })
        raise
```

**Rules:**
- Use structured logging with context (site, job_count, timing)
- Log performance metrics (jobs/second, success rates)
- Implement health checks for all critical components
- Monitor: scraper success rates, database connections, AI processing times

---

## 🔒 **Security Essentials**

### **Input Validation & Rate Limiting**
```python
# ✅ GOOD: Input validation
def validate_job_url(url: str) -> bool:
    if not url or not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL: {url}")
    
    # Block known problematic domains
    blocked_domains = ['malicious-site.com']
    if any(domain in url for domain in blocked_domains):
        raise SecurityError(f"Blocked domain in URL: {url}")
    
    return True

# ✅ GOOD: Rate limiting
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    async def acquire(self):
        now = time.time()
        self.requests = [req for req in self.requests if now - req < self.window_seconds]
        if len(self.requests) >= self.max_requests:
            raise RateLimitError("Rate limit exceeded")
        self.requests.append(now)
```

**Rules:**
- Validate all URLs and user inputs
- Implement rate limiting: 10 requests/minute for Eluta, 30/minute for JobSpy
- Never log sensitive data (credentials, personal info)
- Use environment variables for all secrets

---

## 📚 **Documentation Standards**

### **🚫 Documentation File Policy (7-Doc Policy)**

- The 7 core markdown files are the primary documentation sources:
    1. `README.md` (root)
    2. `CHANGELOG.md` (root)
    3. `DEVELOPER_GUIDE.md`
    4. `ARCHITECTURE.md`
    5. `API_REFERENCE.md`
    6. `DEVELOPMENT_STANDARDS.md` (this file)
    7. `TROUBLESHOOTING.md`
- All contributors must keep the main quality gates and overall standards in this file up to date.
- Any new documentation proposal must be discussed and integrated into the most relevant core doc.
- This policy is mandatory for all contributors and applies to all future changes.

---

## 📑 **Markdown Content & Documentation Standards (2025 Update)**

All markdown documentation in this project must follow these rules:

- **YAML Front Matter**: Every markdown file must start with YAML front matter including:
  - `post_title`, `author1`, `post_slug`, `microsoft_alias`, `featured_image`, `categories`, `tags`, `ai_note`, `summary`, `post_date`
- **Headings**: Use `##` for H2 and `###` for H3. Do not use H1 (auto-generated from YAML front matter). Maintain clear hierarchy.
- **Lists**: Use `-` for bullet points and `1.` for numbered lists. Indent nested lists with two spaces.
- **Code Blocks**: Use triple backticks with language specification for syntax highlighting.
- **Links**: Use `[link text](URL)` format with descriptive text and valid URLs.
- **Images**: Use `![alt text](image URL)` with meaningful alt text for accessibility.
- **Tables**: Use markdown tables with headers and proper alignment.
- **Line Length**: Limit lines to 80 characters for readability. Use soft line breaks.
- **Whitespace**: Use blank lines to separate sections. Avoid excessive whitespace.
- **Validation**: All markdown must pass the project's validation tools.

---

## 🎯 **Final Checklist Before Any Commit**

- [ ] **Functionality**: It works as intended
- [ ] **Code Quality**: Passes all automated checks (✅ GREEN only)
- [ ] **Type Hints**: All functions properly typed
- [ ] **Real Data**: No placeholders or fabricated content
- [ ] **Error Handling**: Fails gracefully with clear messages
- [ ] **Performance**: No significant slowdown
- [ ] **Documentation**: Updated relevant files
- [ ] **Testing**: Validated the change works
- [ ] **Architecture**: Fits with existing design patterns
- [ ] **User Experience**: Improves or maintains usability
- [ ] **CI/CD**: All tests pass and code is linted/auto-formatted in CI

---

## 💡 **Philosophy Reminder**

> "Perfect is the enemy of good. Ship working software, then iterate."
> 
> "Code is read more often than it's written. Optimize for readability."
> 
> "The best architecture is the one that serves the users' needs simply and reliably."
> 
> "Documentation is love letter to your future self."
> 
> "When in doubt, choose the solution that's easier to undo."

---

*This document serves as the complete development standards reference for 
JobLens. All development must comply with these standards.*

**Last Updated:** July 17, 2025  
**Maintainer:** JobLens Development Team
