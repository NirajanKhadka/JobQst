# JobLens - Intelligent Job Discovery & Automation Platform

<div align="center">

**🎯 Profile-Driven Job Discovery** - Modern job searching with intelligent matching, comprehensive analytics, and clean Python architecture.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy.readthedocs.io/)
[![Playwright](https://img.shields.io/badge/Playwright-Automation-34D399.svg)](https://playwright.dev/)
[![Dash](https://img.shields.io/badge/Dash-Dashboard-00D4AA.svg)](https://dash.plotly.com/)

[🚀 Quick Start](#quick-start) • [🔧 Setup](#installation--setup) • [💻 Development](#quick-development-notes)

</div>

---

## What is JobLens?

JobLens is a modern job discovery platform built with clean Python architecture. It streamlines job searching across multiple sources, provides intelligent job-profile matching, and offers powerful analytics through interactive dashboards.

### 🎯 **Perfect For:**

- **Job Seekers** wanting automated, intelligent job discovery and tracking
- **Career Professionals** managing applications with AI-powered insights  
- **Developers** seeking opportunities with location-specific search capabilities
- **Anyone** optimizing their job search with automation and analytics

### ✨ **Current Features (September 2025)**

- ✅ **Multi-Source Scraping** - JobSpy integration (Indeed, LinkedIn, Glassdoor, ZipRecruiter) + Eluta.ca
- ✅ **DuckDB Analytics** - 10-100x faster analytics with optimized 17-field schema
- ✅ **Intelligent 3-Layer Caching** - HTML, embedding, and result caching for 70% faster processing
- ✅ **Modern Dash Dashboard** - Interactive web interface with real-time monitoring
- ✅ **AI-Powered Matching** - Semantic job-profile compatibility scoring
- ✅ **Type-Safe Architecture** - Full type annotations following modern Python standards
- ✅ **Performance Monitoring** - Real-time health checks and system metrics
- ✅ **Automated Backup System** - Database backup with rotation and integrity verification

---

## Key Features

### 🔍 Multi-Source Job Discovery

- **Primary Engine**: JobSpy (Indeed, LinkedIn, Glassdoor, ZipRecruiter)
- **Fallback**: Eluta.ca for Canadian opportunities  
- **Parallel Workers**: Configurable concurrent scraping
- **Smart Deduplication**: AI-powered duplicate detection
- **Geographic Focus**: USA & Canada job markets

### 🧠 Intelligent Analysis & Matching

- **Profile-Based Scoring**: AI job-profile compatibility assessment
- **Skills Gap Analysis**: Identify missing skills and suggestions
- **Resume Processing**: Auto profile creation from PDF resumes
- **Location Intelligence**: Remote/hybrid/onsite categorization
- **Experience Matching**: Level-appropriate job recommendations

### 📊 Advanced Analytics & Performance

- **DuckDB Analytics**: 10-100x faster analytical queries vs traditional databases
- **Intelligent Caching**: 3-layer caching (HTML, embeddings, results) with 70% performance boost
- **Real-time Monitoring**: Live system health, cache hit rates, and performance metrics
- **Performance Dashboard**: Dedicated analytics interface with cache statistics
- **Automated Backup**: Daily database backups with integrity verification
- **Resource Optimization**: Memory-efficient processing with configurable worker pools

---

## Quick Start

### Prerequisites

- **Python 3.11+** (Required for modern type annotations and features)
- **Git** for repository cloning
- **Conda** (recommended) or Python venv for environment management
- **Optional**: PostgreSQL for production deployments

### Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/NirajanKhadka/JobLens.git
cd JobLens

# 2. Create conda environment (recommended)
conda create -n auto_job python=3.11
conda activate auto_job

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install browser automation
playwright install chromium

# 5. Setup environment (optional)
cp .env.example .env
# Edit .env with your configuration if needed
```

### Basic Usage

```bash
# Ensure you're in the auto_job environment
conda activate auto_job

# 1. Scrape jobs using JobSpy with DuckDB optimization
python main.py YourProfile --action jobspy-pipeline \
  --jobspy-preset canada_comprehensive \
  --database-type duckdb

# 2. Analyze and score scraped jobs with intelligent caching
python main.py YourProfile --action analyze-jobs --enable-cache

# 3. Launch dashboard with performance monitoring
python main.py YourProfile --action dashboard --enable-monitoring

# 4. Performance dashboard with cache analytics
python main.py YourProfile --action performance-dashboard

# 5. System health check and cache statistics
python main.py YourProfile --action health-check --show-cache-stats
```

### Available Actions

| Action | Description | Example |
|--------|-------------|---------|
| `jobspy-pipeline` | **Modern scraping** with JobSpy integration + DuckDB | `--jobspy-preset usa_comprehensive --database-type duckdb` |
| `scrape` | **Legacy scraping** with Eluta fallback | `--keywords "python,data"` |
| `analyze-jobs` | **AI analysis** with intelligent caching | `--enable-cache --cache-profile` |
| `dashboard` | **Enhanced Dash interface** with performance monitoring | `--enable-monitoring --show-cache-stats` |
| `performance-dashboard` | **Dedicated performance analytics** interface | Real-time system metrics and cache analytics |
| `health-check` | **System health monitoring** and diagnostics | `--detailed --show-cache-stats` |
| `cache-management` | **Cache statistics** and cleanup operations | `--action cache-stats`, `--action cache-clear` |
| `interactive` | **CLI menu** for guided workflows | Interactive command selection |

## Architecture Overview

JobLens follows a clean, modular architecture with type-safe Python code:

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│   Job Sources   │───▶│  Scraping Engine │───▶│   Analysis Pipeline  │
│                 │    │                  │    │                      │
│ • JobSpy Sites  │    │ • Parallel       │    │ • Profile Matching   │
│ • Eluta.ca      │    │   Workers        │    │ • AI Scoring         │
│ • Custom APIs   │    │ • Rate Limiting  │    │ • Skills Analysis    │
└─────────────────┘    └──────────────────┘    └──────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│    Database     │    │   Monitoring     │    │     Dashboard        │
│                 │    │                  │    │                      │
│ • DuckDB        │    │ • Health Checks  │    │ • Dash Interface     │
│ • Profile-based │    │ • Performance    │    │ • Real-time Stats    │
│ • Caching       │    │ • Cache Analytics│    │ • Job Management     │
└─────────────────┘    └──────────────────┘    └──────────────────────┘
```

### Core Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Scraping Engine** | JobSpy, Playwright, AsyncIO | Multi-source job discovery with parallel processing |
| **Analysis Pipeline** | Custom AI, Transformers | Profile-based job scoring and skills analysis |
| **Database** | DuckDB | High-performance analytics with optimized schema |
| **Caching** | LRU Cache | 3-layer caching for 70% performance improvement |
| **Dashboard** | Dash (Plotly) | Interactive web interface with real-time monitoring |
| **CLI** | Click, Rich | Command-line automation and management |

## Modern Python API Examples

### Type-Safe Job Processing

```python
from typing import List, Dict, Optional, Any
from pathlib import Path
from src.core.user_profile_manager import UserProfileManager
from src.analysis.job_analyzer import JobAnalyzer
from src.models.job import JobListing

def process_job_pipeline(
    profile_name: str,
    keywords: List[str],
    max_jobs: int = 100,
    enable_cache: bool = True
) -> Dict[str, Any]:
    """Process complete job discovery pipeline with type safety.
    
    Args:
        profile_name: User profile identifier
        keywords: Job search keywords
        max_jobs: Maximum jobs to process
        enable_cache: Enable intelligent caching
        
    Returns:
        Processing results with job count and metrics
        
    Raises:
        ValueError: If profile not found or keywords empty
        ProcessingError: If pipeline fails
    """
    if not keywords:
        raise ValueError("Keywords cannot be empty")
    
    # Load user profile with validation
    profile_manager = UserProfileManager()
    profile = profile_manager.load_profile(profile_name)
    
    # Initialize job analyzer with caching
    analyzer = JobAnalyzer(profile, enable_cache=enable_cache)
    
    # Process jobs with progress tracking
    results = analyzer.analyze_job_batch(keywords, max_jobs)
    
    return {
        "jobs_processed": len(results),
        "cache_hit_rate": analyzer.get_cache_stats().hit_rate,
        "processing_time": results.processing_time,
        "high_fit_jobs": [job for job in results.jobs if job.fit_score > 0.8]
    }
```

### Configuration Management

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class JobScrapingConfig(BaseModel):
    """Type-safe configuration for job scraping operations."""
    
    keywords: List[str] = Field(..., min_items=1, max_items=10)
    locations: List[str] = Field(default_factory=list)
    max_jobs_per_site: int = Field(default=100, ge=1, le=1000)
    enable_cache: bool = Field(default=True)
    cache_ttl_hours: int = Field(default=24, ge=1, le=168)
    
    @validator('keywords')
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Validate and clean keywords."""
        cleaned = [keyword.strip().lower() for keyword in v if keyword.strip()]
        if not cleaned:
            raise ValueError("At least one valid keyword required")
        return cleaned
    
    @validator('locations')
    def validate_locations(cls, v: List[str]) -> List[str]:
        """Validate location format."""
        return [loc.strip() for loc in v if loc.strip()]

# Usage with type safety
config = JobScrapingConfig(
    keywords=["python developer", "software engineer"],
    locations=["Toronto, ON", "Vancouver, BC"],
    max_jobs_per_site=200,
    enable_cache=True
)
```

### Async Job Analysis

```python
import asyncio
from typing import AsyncIterator, List
from src.services.ai_integration_service import AIIntegrationService

async def analyze_jobs_async(
    jobs: List[JobListing],
    batch_size: int = 10
) -> AsyncIterator[Dict[str, Any]]:
    """Asynchronously analyze jobs with batching.
    
    Args:
        jobs: List of job listings to analyze
        batch_size: Number of jobs to process concurrently
        
    Yields:
        Analysis results for each job batch
    """
    ai_service = AIIntegrationService()
    
    # Process jobs in batches to avoid overwhelming the system
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        
        # Create concurrent analysis tasks
        tasks = [
            ai_service.analyze_job_compatibility(job)
            for job in batch
        ]
        
        # Execute batch concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Yield successful results, log errors
        for job, result in zip(batch, results):
            if isinstance(result, Exception):
                logger.error(f"Analysis failed for job {job.id}: {result}")
                continue
            
            yield {
                "job_id": job.id,
                "fit_score": result.fit_score,
                "skills_match": result.skills_match,
                "analysis_time": result.processing_time
            }

# Usage
async def main():
    jobs = await scraper.get_jobs(keywords=["python"])
    
    async for analysis_result in analyze_jobs_async(jobs):
        print(f"Job {analysis_result['job_id']}: {analysis_result['fit_score']:.2f}")
```

## Configuration & Environment

### Environment Setup
```bash
# Essential environment variables (.env)
DATABASE_TYPE=duckdb  # Options: duckdb (recommended), postgresql, sqlite
DATABASE_URL=postgresql://user:password@localhost/jobqst  # if using PostgreSQL

# Performance optimization
ENABLE_CACHING=true
CACHE_SIZE_MB=500
CACHE_TTL_HOURS=24

# Scraping configuration
SCRAPING_DELAY=2
MAX_CONCURRENT_WORKERS=4
BROWSER_HEADLESS=true

# Dashboard configuration
DASH_PORT=8050
ENABLE_PERFORMANCE_MONITORING=true

# JobSpy integration
JOBSPY_MAX_WORKERS=3
JOBSPY_SITES=indeed,linkedin,glassdoor,ziprecruiter

# Monitoring and backup
ENABLE_AUTO_BACKUP=true
BACKUP_RETENTION_DAYS=7
ENABLE_HEALTH_CHECKS=true

# Optional AI features (all models run locally - no API keys needed)
# AI_ANALYSIS_ENABLED=true  # Uses local transformer models
# DISABLE_HEAVY_AI=false  # Set to true for faster startup
```

### Profile Configuration
Create profiles in `profiles/YourName/YourName.json`:

```json
{
  "name": "Your Name",
  "email": "your.email@example.com",
  "location": "Toronto, ON",
  "experience_level": "senior",
  "keywords": ["python developer", "machine learning", "devops"],
  "skills": ["Python", "Docker", "Kubernetes", "AWS", "PostgreSQL"],
  "preferences": {
    "remote_work": true,
    "salary_min": 90000,
    "company_size": ["startup", "medium"],
    "industries": ["technology", "fintech", "healthtech"]
  },
  "education": {
    "degree": "Computer Science",
    "level": "bachelor"
  },
  "certifications": ["AWS Certified Solutions Architect"]
}
```

### JobSpy Presets
Choose from pre-configured search strategies:

| Preset | Description | Coverage |
|--------|-------------|----------|
| `usa_comprehensive` | Full USA job market coverage | All major cities |
| `canada_comprehensive` | Complete Canadian market | All provinces |
| `tech_hubs_canada` | Canadian tech centers only | Toronto, Vancouver, Montreal |
| `usa_tech_hubs` | USA tech hotspots | SF, NYC, Seattle, Austin |
| `remote_focused` | Remote-first opportunities | Global remote positions |

## Testing & Development

### Running Tests
```bash
# Activate environment
conda activate auto_job

# Run full test suite
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v             # Integration tests
pytest tests/dashboard/ -v               # Dashboard tests

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Test specific components
pytest tests/scrapers/test_jobspy_integration.py -v
```

### Development Workflow
```bash
# 1. Install development dependencies
pip install -r requirements-dev.txt

# 2. Code formatting (if available)
black src/ tests/
isort src/ tests/

# 3. Run linting (if configured)
flake8 src/ tests/

# 4. Test your changes
pytest tests/ -v

# 5. Manual testing
python main.py TestProfile --action jobspy-pipeline --jobspy-preset tech_hubs_canada
```

### Available VS Code Tasks
Use `Ctrl+Shift+P` → "Tasks: Run Task":

- **Run all tests (pytest)** - Execute full test suite
- **Start Dash Dashboard** - Launch Dash analytics interface

## Deployment & Production

### Local Production Setup
```bash
# 1. Production environment setup
conda create -n jobqst_prod python=3.11
conda activate jobqst_prod
pip install -r requirements.txt

# 2. PostgreSQL database setup (recommended for production)
createdb jobqst_production
export DATABASE_URL=postgresql://user:password@localhost/jobqst_production

# 3. Run database migrations
python -c "from src.core.database_migration import run_migrations; run_migrations()"

# 4. Start services
python main.py ProductionProfile --action dashboard  # Dashboard
python main.py ProductionProfile --action jobspy-pipeline  # Background scraping
```

### Docker Deployment
```bash
# Development environment
docker-compose -f docker-compose.dev.yml up

# Production deployment
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs jobqst-app
```

### Cloud Deployment Options

#### Option 1: Traditional VPS/VM
- Deploy using Docker Compose
- PostgreSQL + Redis for production scale
- Nginx reverse proxy for dashboard access
- Systemd services for background processing

#### Option 2: Container Platforms
- **AWS ECS/Fargate**: Container orchestration
- **Google Cloud Run**: Serverless container deployment  
- **Azure Container Instances**: Managed container hosting
- **Railway/Render**: Simple deployment with built-in PostgreSQL

#### Option 3: Self-Hosted
```bash
# Systemd service example (Ubuntu/CentOS)
sudo cp deploy/jobqst.service /etc/systemd/system/
sudo systemctl enable jobqst
sudo systemctl start jobqst
```

## Documentation & Resources

### 📚 **Core Documentation**
- **[📝 Changelog](docs/CHANGELOG.md)** - Version history and changes

### 🔗 **Quick References**
- Available VS Code tasks and commands are listed above
- Configuration examples provided in this README

---

## Troubleshooting

### **Common Issues**

<details>
<summary><strong>🔧 Environment & Installation</strong></summary>

```bash
# Python version issues
python --version  # Should be 3.11+
conda list python  # Check conda environment

# Dependency conflicts
conda activate auto_job
pip install -r requirements.txt --force-reinstall

# Browser automation issues
playwright install chromium --force
```
</details>

<details>
<summary><strong>🌐 Scraping Problems</strong></summary>

```bash
# JobSpy integration issues
pip install python-jobspy --upgrade

# Rate limiting or blocks
# Edit .env:
SCRAPING_DELAY=5
MAX_CONCURRENT_WORKERS=2

# Browser automation failures
export BROWSER_HEADLESS=false  # Debug mode
```
</details>

<details>
<summary><strong>💾 Database Issues</strong></summary>

```bash
# PostgreSQL connection problems
export DATABASE_URL=sqlite:///jobs.db  # Fallback to SQLite

# Migration issues
python -c "from src.core.database_migration import reset_database; reset_database()"

# Profile database corruption
python main.py YourProfile --action health-check
```
</details>

<details>
<summary><strong>📊 Dashboard Problems</strong></summary>

```bash
# Port conflicts
export DASH_PORT=8051

# Dashboard won't start
python src/dashboard/dash_app/app.py

# Missing data in dashboard
python main.py YourProfile --action analyze-jobs  # Ensure jobs are processed
```
</details>

### **Getting Help**

If you run into issues, check the troubleshooting section above or reach out directly since this is a small team project.

---

## Quick Development Notes

Since this is a two-person project, development is simple:

### 🚀 **Setup**
```bash
# 1. Clone and setup
git clone https://github.com/NirajanKhadka/JobLens.git
cd JobLens
conda create -n auto_job python=3.11
conda activate auto_job
pip install -r requirements.txt

# 2. Test your changes
pytest tests/ -v

# 3. Manual testing
python main.py TestProfile --action jobspy-pipeline --jobspy-preset tech_hubs_canada
```

### 📝 **Simple Guidelines**
- Test your changes before pushing
- Use clear commit messages
- Update README if adding new features

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Main dependencies:
- [JobSpy](https://github.com/speedyapply/JobSpy) - MIT License
- [Playwright](https://github.com/microsoft/playwright-python) - Apache 2.0  
- [Dash](https://github.com/plotly/dash) - MIT License

---

## Acknowledgments

Built with:
- **Python 3.11+** - Core language
- **JobSpy, Playwright** - Web scraping  
- **DuckDB** - High-performance database
- **Dash (Plotly)** - Interactive dashboard
- **Rich, Click** - CLI interface

Special thanks to the [JobSpy Project](https://github.com/speedyapply/JobSpy) for excellent multi-site scraping foundation.

---

**Ready to get started?** → [Quick Start](#quick-start)

**Made with ❤️ for better job discovery**

