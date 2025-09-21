# JobLens Development Standards

**Last Updated:** September 6, 2025  
**Status:** Active - Enforced Standards  

## Document Overview

This document establishes mandatory development standards for the JobLens project. These standards are framework-agnostic and focus on modern Python practices, code quality, and maintainability. All code contributions must comply with these standards.

## Core Development Philosophy

### Fundamental Principles
1. **Clean Code**: Write code that tells a story and can be understood by humans
2. **Type Safety**: Leverage Python's type system for better code reliability
3. **Performance Awareness**: Write efficient code that scales with data growth
4. **Security First**: Every line of code should be secure by design
5. **Framework Independence**: Standards apply regardless of implementation framework
6. **AI Collaboration**: Write code that works well with AI assistants and tools

### Quality Hierarchy
```
Production Quality > Readability > Performance > Clever Solutions
```

## Modern Python Standards

### Import Organization

All Python files must organize imports according to PEP 8 and Google Python Style Guide:

```python
# 1. Standard library imports (alphabetical)
import asyncio
import logging
import pathlib
from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Optional, Union

# 2. Third-party imports (alphabetical)
import aiohttp
import pandas as pd
import pydantic
import requests

# 3. Local application imports (alphabetical)
from src.core.exceptions import JobScrapingError
from src.models.job import JobListing
from src.utils.logging import get_logger
```

### Import Patterns (MANDATORY)

```python
# ✅ GOOD: Explicit imports
from typing import List, Dict, Optional, Union, Any
from collections.abc import Sequence, Mapping, Iterable
from pathlib import Path

# ✅ GOOD: Local imports with clear modules
from src.scrapers.base import BaseScraper
from src.models.job import JobListing

# ❌ BAD: Wildcard imports
from typing import *
from src.scrapers import *

# ❌ BAD: Relative imports beyond parent
from ...utils import helper
```

### Type Annotations (MANDATORY)

All functions must include comprehensive type annotations:

```python
# ✅ GOOD: Complete type annotations
from typing import List, Dict, Optional, Union, Any
from pathlib import Path

def process_job_data(
    jobs: List[Dict[str, Any]], 
    output_path: Path,
    filters: Optional[Dict[str, Union[str, int]]] = None
) -> int:
    """Process job data and save to file.
    
    Args:
        jobs: List of job dictionaries from scrapers
        output_path: Path to save processed data
        filters: Optional filters to apply
        
    Returns:
        Number of jobs processed
        
    Raises:
        ValueError: If jobs list is empty
        FileNotFoundError: If output directory doesn't exist
    """
    if not jobs:
        raise ValueError("Jobs list cannot be empty")
    
    # Implementation...
    return len(processed_jobs)
```

### Modern Python Patterns

#### Use pathlib over os.path

```python
# ✅ GOOD: pathlib
from pathlib import Path

config_path = Path("config") / "settings.json"
if config_path.exists():
    data = config_path.read_text()

# ❌ BAD: os.path
import os
config_path = os.path.join("config", "settings.json")
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        data = f.read()
```

#### Context Managers for Resource Handling

```python
# ✅ GOOD: Context managers
from contextlib import contextmanager
import sqlite3

@contextmanager
def get_database_connection():
    conn = sqlite3.connect("jobs.db")
    try:
        yield conn
    finally:
        conn.close()

with get_database_connection() as conn:
    cursor = conn.cursor()
    # Use connection
```

#### Async Patterns for I/O Operations

```python
# ✅ GOOD: Async for I/O
import asyncio
import aiohttp
from typing import List

async def fetch_job_urls(urls: List[str]) -> List[str]:
    """Fetch multiple URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_single_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, str)]

async def fetch_single_url(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as response:
        return await response.text()
```

## Code Organization Standards

### Function Design Rules

- **Single Responsibility**: Each function should do one thing well
- **Pure Functions**: Prefer functions without side effects when possible
- **Max 30 lines**: Functions exceeding 30 lines should be refactored
- **Clear Contracts**: Input/output types and behavior must be explicit
- **Early Returns**: Use early returns to reduce nesting complexity

```python
# ✅ GOOD: Clear, focused function
def calculate_job_match_score(
    job: JobListing, 
    user_skills: List[str]
) -> float:
    """Calculate how well a job matches user skills.
    
    Args:
        job: Job listing to evaluate
        user_skills: List of user's skills
        
    Returns:
        Match score between 0.0 and 1.0
    """
    if not job.required_skills or not user_skills:
        return 0.0
    
    user_skills_set = {skill.lower() for skill in user_skills}
    job_skills_set = {skill.lower() for skill in job.required_skills}
    
    matches = user_skills_set & job_skills_set
    return len(matches) / len(job_skills_set)
```

### File Structure Standards

```text
src/                           # All source code
├── core/                      # Core business logic
│   ├── models/               # Data models and schemas
│   ├── services/             # Business services
│   └── exceptions.py         # Custom exceptions
├── scrapers/                  # Web scraping modules
│   ├── base.py              # Base scraper interface
│   ├── jobspy/              # JobSpy integration
│   └── eluta/               # Eluta scraper
├── storage/                   # Data persistence
│   ├── database/            # Database operations
│   └── cache/               # Caching layer
├── api/                       # API interfaces
│   ├── routes/              # API route handlers
│   └── middleware/          # Request/response middleware
└── utils/                     # Shared utilities
    ├── logging.py           # Logging configuration
    ├── config.py            # Configuration management
    └── validators.py        # Data validation

tests/                         # Test files mirror src/
docs/                          # Documentation only
profiles/                      # User configurations
```

### Naming Conventions

Follow PEP 8 and Google Python Style Guide:

```python
# Files and modules
job_scraper.py              # snake_case
eluta_integration.py        # descriptive, specific

# Classes
class JobListing:           # PascalCase
class ElutaScraper:         # Clear, specific purpose
class DatabaseConnection:  # Noun phrases

# Functions and variables
def scrape_job_details():   # snake_case, verb phrases
user_preferences = {}      # snake_case, descriptive
MAX_RETRY_ATTEMPTS = 3     # UPPER_SNAKE_CASE for constants

# Private/internal
def _parse_salary_range():  # Leading underscore
_internal_cache = {}       # Private module variables
```

### File Size Guidelines

- **Functions**: Maximum 30 lines (excluding docstrings)
- **Classes**: Maximum 200 lines (consider composition over inheritance)
- **Modules**: Maximum 500 lines (split if larger)
- **🚨 CRITICAL**: Any file >1000 lines requires immediate refactoring
- **Test Files**: Maximum 500 lines per test module

## Quality Gates (MANDATORY)

All code must pass these quality gates before merge. No exceptions.

### Automated Quality Checks

```bash
# Code formatting (must pass)
black --check src/ tests/
isort --check-only src/ tests/

# Linting (must pass) 
flake8 src/ tests/
pylint src/

# Type checking (must pass)
mypy src/

# Security scanning (must pass)
bandit -r src/
safety check

# Test coverage (minimum 80%)
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

### Manual Quality Checklist

- [ ] **Functionality**: Code works as intended and meets requirements
- [ ] **Type Safety**: All functions have proper type annotations
- [ ] **Error Handling**: Graceful failure with informative error messages
- [ ] **Performance**: No significant performance degradation
- [ ] **Security**: Input validation and secure coding practices
- [ ] **Documentation**: Code is self-documenting with clear docstrings
- [ ] **Testing**: Comprehensive tests covering happy path and edge cases
- [ ] **Dependencies**: No unnecessary dependencies added
- [ ] **Backwards Compatibility**: Existing functionality remains intact

## Error Handling Standards

### Exception Hierarchy

Create clear exception hierarchies for better error handling:

```python
# ✅ GOOD: Custom exception hierarchy
class JobScrapingError(Exception):
    """Base exception for job scraping operations."""
    pass

class NetworkError(JobScrapingError):
    """Raised when network operations fail."""
    pass

class ParseError(JobScrapingError):
    """Raised when data parsing fails."""
    pass

class RateLimitError(JobScrapingError):
    """Raised when rate limits are exceeded."""
    pass
```

### Defensive Programming

```python
# ✅ GOOD: Input validation and error context
def scrape_job_listings(url: str, max_pages: int = 10) -> List[JobListing]:
    """Scrape job listings from a URL."""
    # Input validation
    if not url or not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL: {url}")
    
    if not (1 <= max_pages <= 100):
        raise ValueError(f"max_pages must be 1-100, got {max_pages}")
        
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return parse_job_listings(response.text)
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"Request failed: {e}") from e
```

### Logging Standards

```python
import logging

logger = logging.getLogger(__name__)

def scrape_with_logging(url: str) -> Optional[Dict[str, Any]]:
    logger.info("Starting scrape", extra={"url": url})
    
    try:
        result = perform_scrape(url)
        logger.info("Scrape completed", extra={"jobs_found": len(result)})
        return result
    except NetworkError as e:
        logger.warning("Network error", extra={"error": str(e)})
        return None
    except Exception as e:
        logger.error("Unexpected error", extra={"error": str(e)}, exc_info=True)
        raise
```

## Security Standards

### Input Validation

All external input must be validated and sanitized:

```python
# ✅ GOOD: Comprehensive input validation
from pydantic import BaseModel, validator

class JobSearchRequest(BaseModel):
    keywords: List[str]
    location: str
    max_results: int = 50
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if not v or len(v) > 10:
            raise ValueError('Keywords must be 1-10 items')
        return [keyword.strip() for keyword in v if keyword.strip()]
```

### Secure Configuration

```python
# ✅ GOOD: Secure configuration
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///jobs.db"
    secret_key: str  # Never hardcode!
    debug: bool = False
    
    class Config:
        env_file = ".env"
```

### Dependency Security

- Pin dependency versions in requirements.txt
- Use `safety check` for vulnerability scanning  
- Use `bandit -r src/` for security linting

## Performance Standards

### Algorithmic Efficiency

Follow Big O notation guidelines:

```python
# ✅ GOOD: O(n) algorithm for job matching
def find_matching_jobs(jobs: List[JobListing], skills: Set[str]) -> List[JobListing]:
    matches = []
    skills_lower = {skill.lower() for skill in skills}
    
    for job in jobs:
        job_skills = {skill.lower() for skill in job.required_skills}
        if job_skills & skills_lower:  # Set intersection is O(1) average
            matches.append(job)
    
    return matches
```

### Memory Management and Caching

```python
# ✅ GOOD: Generator for large datasets
def process_large_job_dataset(file_path: Path) -> Iterator[JobListing]:
    with file_path.open() as f:
        for line in f:
            yield JobListing.parse_raw(line)

# ✅ GOOD: LRU cache for expensive operations
@lru_cache(maxsize=1000)
def calculate_job_similarity(job1_id: str, job2_id: str) -> float:
    return similarity_score
```

## Testing Standards

### Modern Testing Patterns

Use pytest with comprehensive fixtures and mocking:

```python
# ✅ GOOD: Comprehensive test structure
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_http_response():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"jobs": [{"title": "Developer"}]}
    return response

@pytest.mark.asyncio
async def test_scrape_jobs_success(mock_http_response):
    with patch('requests.get', return_value=mock_http_response):
        jobs = await scraper.scrape_jobs("developer", "remote")
        assert len(jobs) > 0

@pytest.mark.parametrize("keywords,location,expected", [
    (["python"], "remote", True),
    ([], "remote", False),
])
def test_validate_search_params(keywords, location, expected):
    result = JobScraper.validate_search_params(keywords, location)
    assert result == expected
```

### Test Organization

```text
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Component interaction tests  
├── e2e/           # End-to-end tests
└── conftest.py    # Shared fixtures
```

## AI-Friendly Development Patterns

### Structured Documentation for AI

Write docstrings that AI tools can parse and understand:

```python
# ✅ GOOD: AI-parseable docstring
def calculate_job_relevance_score(
    job_description: str,
    user_profile: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """Calculate relevance score between job and user profile.
    
    Uses NLP and skill matching to determine job-user compatibility.
    
    Args:
        job_description: Full text of job posting
        user_profile: Dict with skills, experience_years, locations, salary_range
        weights: Optional scoring weights for different factors
    
    Returns:
        Relevance score between 0.0 (no match) and 1.0 (perfect match)
    
    Example:
        >>> user = {"skills": ["python"], "experience_years": 5}
        >>> score = calculate_job_relevance_score(job_text, user)
        >>> print(f"Relevance: {score:.2f}")
        Relevance: 0.87
    """
    pass
```

### Configuration Schema Validation

Use Pydantic for self-documenting configuration:

```python
# ✅ GOOD: Self-validating configuration
from pydantic import BaseModel, Field, validator

class ScrapingConfig(BaseModel):
    """Configuration for job scraping operations."""
    max_concurrent_requests: int = Field(default=5, ge=1, le=20)
    request_timeout: int = Field(default=30, ge=5, le=300)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    
    @validator('max_concurrent_requests')
    def validate_requests(cls, v):
        if not (1 <= v <= 20):
            raise ValueError('Must be 1-20 requests')
        return v
```

## Development Workflow Standards

### Git Workflow

Follow conventional commits for clear change tracking:

```bash
# Commit message format: <type>(<scope>): <description>

# Types:
feat: New feature
fix: Bug fix
docs: Documentation changes
style: Code style changes (formatting, no logic change)
refactor: Code refactoring
test: Adding or updating tests
chore: Build process or auxiliary tool changes

# Examples:
feat(scraper): add LinkedIn integration with rate limiting
fix(database): resolve connection pool exhaustion
docs(api): update job search endpoint documentation
refactor(utils): extract common validation functions
test(scrapers): add integration tests for Eluta scraper
```

### Continuous Integration

All changes must pass automated CI pipeline with:

- Code formatting (black, isort)
- Linting (flake8, pylint)
- Type checking (mypy)
- Security scanning (bandit, safety)
- Test coverage (minimum 80%)

## Documentation Standards

### Docstring Standards

Use Google-style docstrings for consistency:

```python
# ✅ GOOD: Complete Google-style docstring
def scrape_job_listings(
    source: str,
    filters: Dict[str, Any],
    max_results: int = 100
) -> List[JobListing]:
    """Scrape job listings from specified source with filters.
    
    Args:
        source: Job board identifier ('indeed', 'linkedin', 'eluta')
        filters: Search filters (keywords, location, remote_only, etc.)
        max_results: Maximum number of jobs to return (1-1000)
    
    Returns:
        List of JobListing objects with title, company, location, etc.
    
    Raises:
        ValueError: If source is not supported or filters are invalid
        ScrapingError: If scraping operation fails
    
    Example:
        >>> jobs = scrape_job_listings('indeed', {'keywords': ['python']}, 50)
        >>> len(jobs)
        43
    """
    pass
```

## Dependency Management

### Requirements Structure

Organize dependencies clearly:

```text
# requirements.txt - Production only
requests==2.31.0
pydantic==2.5.0

# requirements-dev.txt - Development dependencies  
-r requirements.txt
pytest==7.4.3
black==23.11.0
mypy==1.7.1
```

### Security Configuration

```python
# pyproject.toml security configuration
[tool.bandit]
exclude_dirs = ["tests", "docs"]
skips = ["B101"]  # Skip assert_used

[tool.safety]
# Ignore specific vulnerabilities if necessary (with justification)
ignore = ["51358"]  # Example: ignore specific CVE with reason

[tool.pip-audit]
# Additional security scanning
desc = true
format = "json"
```

## Professional Development Mantras

> "Code is written once but read a thousand times. Optimize for clarity."
>
> "Type annotations are love letters to your future debugging sessions."
>
> "The best code is code that doesn't need comments because it speaks for itself."
>
> "Security isn't a feature, it's a foundation."
>
> "Performance problems are solved with better algorithms, not faster hardware."
>
> "If it's not tested, it's broken."
>
> "Documentation is a time machine that lets you remember why you made that clever decision." ← *The one quirky touch*

---

*This document serves as the complete development standards reference for JobLens. These standards are framework-agnostic and focus on modern Python practices that enable clean, maintainable, and secure code.*

**Last Updated:** September 6, 2025  
**Maintainer:** JobLens Development Team


