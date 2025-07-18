# 🛠️ AutoJobAgent Development Standards

> **Under any circumstances, the user should ask the AI to edit these standards.**

**Last Updated:** July 10, 2025  
**Status:** 🟢 **ACTIVE** - Core Development Standards

> **NOTICE:** All standards documents must be located inside `docs/standards/` and are FROZEN. Do not make changes unless explicitly requested.

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
  - Provide robust error handling and clear status reporting for each document.
  - Save all generated files in a structured, job-specific output directory.
  - Expose API or CLI for both batch and single-document generation.
  - Ensure all output is ATS-friendly and meets formatting standards.
- The orchestration layer must be able to recover from worker failures and retry as needed.
- All document generation orchestration code must be covered by integration tests.

---

## 💻 **Code Quality Standards**

### **🐍 Python Standards**
```python
# ✅ GOOD: Descriptive names with type hints
def scrape_job_listings(keywords: List[str], location: str) -> List[JobListing]:
    """Scrape job listings for given keywords and location."""
    pass

# ✅ GOOD: Error handling with context
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
docs/                          # ALL documentation here
├── README.md                  # Documentation index  
├── DEVELOPER_GUIDE.md         # Setup and workflow
├── standards/                 # Development standards (FROZEN)
└── ...                        # Other technical docs

src/                           # ALL source code here
├── core/                      # Core system components
├── scrapers/                  # Web scraping (one per site)
├── ats/                       # ATS integrations (one per system)
├── dashboard/                 # UI components only
└── utils/                     # Shared utilities

future_mcps/                   # KEEP SEPARATE - future features
tests/                         # Test files mirror src/ structure
profiles/                      # User configuration
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
# ✅ GOOD: Validate inputs
def scrape_job_site(url: str, timeout: int = 30) -> List[JobListing]:
    if not url or not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL: {url}")
    # ... implementation

# ✅ GOOD: Graceful degradation
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

# Use appropriate log levels
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

## 📚 **Module-Specific Standards**

- **Testing Standards**: See [TESTING_STANDARDS.md](./TESTING_STANDARDS.md)
- **Dashboard Standards**: See [DASHBOARD_STANDARDS.md](./DASHBOARD_STANDARDS.md)
- **Scraper Standards**: See [SCRAPER_STANDARDS.md](./SCRAPER_STANDARDS.md)  
- **Document Generation Standards**: See [DOCGEN_STANDARDS.md](./DOCGEN_STANDARDS.md)
- **Applier Standards**: See [APPLIER_STANDARDS.md](./APPLIER_STANDARDS.md)

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
> "Code is read more often than it's written. Optimize for readability."
> "The best architecture is the one that serves the users' needs simply and reliably."
> "Documentation is love letter to your future self."
> "When in doubt, choose the solution that's easier to undo."

---

## 📚 **Documentation Standards I Maintain**

### 🚫 **Documentation File Policy (July 2025)**

- The 6 core markdown files remain the primary documentation sources:
    1. `README.md`
    2. `DEVELOPMENT_STANDARDS.md` (this file)
    3. `ISSUE_TRACKER.md`
    4. `ARCHITECTURE.md`
    5. `DASHBOARD_TODO.md`
    6. (Choose one: `API_REFERENCE.md`, `TESTING_AND_QUALITY.md`, or as needed)
- **Module-Specific Standards Files are now allowed:**
    - You may create standards files for major modules (e.g., `DASHBOARD_STANDARDS.md`, `SCRAPER_STANDARDS.md`, `DOCGEN_STANDARDS.md`) in the `docs/` folder.
    - Each module standards file must be referenced from the main `DEVELOPMENT_STANDARDS.md` and follow the same formatting and review rigor as core docs.
- All contributors must keep the main quality gates and overall standards in `DEVELOPMENT_STANDARDS.md` up to date.
- Any new documentation proposal must still be discussed and referenced from a core doc.
- If content from other markdown files is needed, migrate or summarize it into the most relevant core or module-specific doc, then delete/archive the extra file.
- This policy is mandatory for all contributors and applies to all future changes.

---

## 📑 Markdown Content & Documentation Standards (2025 Update)

All markdown documentation in this project must follow these rules:

- **Headings**: Use `##` for H2 and `###` for H3. Do not use H1 (it is auto-generated). Maintain a clear hierarchy.
- **Lists**: Use `-` for bullet points and `1.` for numbered lists. Indent nested lists with two spaces.
- **Code Blocks**: Use triple backticks (```) for fenced code blocks. Specify the language for syntax highlighting (e.g., `python`).
- **Links**: Use `[link text](URL)` for links. Ensure descriptive text and valid URLs.
- **Images**: Use `![alt text](image URL)` and provide meaningful alt text for accessibility.
- **Tables**: Use markdown tables with headers and proper alignment.
- **Line Length**: Limit lines to 80 characters for readability. Use soft line breaks for long paragraphs.
- **Whitespace**: Use blank lines to separate sections. Avoid excessive whitespace.
- **Front Matter**: Every markdown file must start with YAML front matter including:
  - `post_title`, `author1`, `post_slug`, `microsoft_alias`, `featured_image`, `categories`, `tags`, `ai_note`, `summary`, `post_date`
- **Validation**: All markdown must pass the project's validation tools for structure, formatting, and metadata.

> **Reference:** See the full markdown rules in your user prompts for more details and examples.
