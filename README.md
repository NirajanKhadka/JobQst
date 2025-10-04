# JobLens - Intelligent Job Discovery Platform# JobQst - Intelligent Job Discovery Platform



[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![Compliance: 93/100](https://img.shields.io/badge/compliance-93%2F100-success.svg)](docs/DEVELOPMENT_STANDARDS.md)[![Type Checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy.readthedocs.io/)



**Automated job discovery across Indeed, LinkedIn, Glassdoor & ZipRecruiter with AI-powered matching****Automated job discovery across Indeed, LinkedIn, Glassdoor & ZipRecruiter with AI-powered matching**



------



## What Is JobLens?## What Is This?



JobLens automates job searching across 4 major job sites using [JobSpy](https://github.com/cullena20/JobSpy), then uses AI to match jobs to your profile. It features a modern Python architecture with DuckDB analytics and a Dash dashboard for visualization.JobQst automates job searching across 4 major job sites using [JobSpy](https://github.com/cullena20/JobSpy), then uses AI to match jobs to your profile. Built with clean Python, type safety, and a Dash dashboard for visualization.



**Built for:** Developers and tech professionals job hunting in Canada/USA.**Built for**: Developers and tech professionals job hunting in Canada/USA.



**Core Features:**## 🚀 Quick Start

- 🔍 Multi-site scraping (Indeed, LinkedIn, Glassdoor, ZipRecruiter)

- 🧠 AI-powered job matching with compatibility scores```bash

- 📊 Real-time analytics dashboard# Clone and setup

- ⚡ Intelligent caching (70% performance boost)git clone https://github.com/NirajanKhadka/JobQst.git

- 🎯 Profile-based system with dedicated databasescd JobQst

- 🛡️ Type-safe code (93/100 compliance)pip install -r requirements.txt



---# Create your profile

python main.py --setup-profile YourName

## Quick Start

# Start scraping

```bashpython main.py YourName --action scrape --jobs 50

# Clone and setup

git clone https://github.com/NirajanKhadka/JobQst.git# View results

cd JobQstpython src/dashboard/unified_dashboard.py --profile YourName

```

# Create environment

conda create -n auto_job python=3.11.11## ✨ Key Features

conda activate auto_job

### 🧠 **Intelligent Job Matching**

# Install dependencies- **AI-Powered Analysis**: GPU-accelerated job compatibility scoring

pip install -r requirements.txt- **Smart Deduplication**: Advanced similarity detection across job boards

- **Relevance Filtering**: Automatically filters irrelevant positions

# Create your profile- **Skill Extraction**: Identifies required skills and technologies

python main.py --setup-profile YourName

### 🕷️ **Multi-Platform Scraping**

# Start discovery- **Eluta Integration**: Specialized Canadian job market scraping

python main.py YourName --action jobspy-pipeline --jobspy-preset canada_comprehensive- **External Job Boards**: Support for major job platforms

- **Rate Limiting**: Respectful scraping with anti-bot measures

# View dashboard- **Parallel Processing**: High-performance concurrent scraping

python main.py YourName --action dashboard

```### 📊 **Real-Time Analytics**

- **Interactive Dashboard**: Comprehensive job market insights

Access dashboard at: `http://localhost:8050`- **Performance Metrics**: Scraping and processing statistics

- **Company Analysis**: Hiring trends and salary insights

---- **Location Intelligence**: Geographic job distribution



## System Requirements### ⚙️ **Production Features**

- **Automated Scheduling**: Set-and-forget job discovery

### Minimum- **Multi-User Support**: Separate profiles and databases

- **Python:** 3.11.11 (required)- **Error Recovery**: Robust error handling and retry logic

- **Memory:** 4GB RAM- **Type Safety**: Full type annotations for reliability

- **Storage:** 2GB free space

- **Network:** Stable internet## 🏗️ Architecture Overview



### Recommended```

- **Memory:** 8GB+ RAMJobQst Pipeline Architecture

- **GPU:** CUDA-compatible for AI processing

- **Storage:** SSD with 5GB+ free┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐

│   Web Scrapers  │───▶│  Smart Processing │───▶│   Dashboard     │

---│                 │    │                  │    │                 │

│ • Eluta         │    │ • Deduplication  │    │ • Analytics     │

## Installation│ • External APIs │    │ • AI Matching    │    │ • Visualizations│

│ • Rate Limiting │    │ • Skill Extract  │    │ • Export Tools  │

### Standard Setup└─────────────────┘    └──────────────────┘    └─────────────────┘

         │                       │                       │

```bash         ▼                       ▼                       ▼

# Clone repository┌─────────────────────────────────────────────────────────────────┐

git clone https://github.com/NirajanKhadka/JobQst.git│                    DuckDB Analytics Database                     │

cd JobQst│          • Columnar Storage  • Vectorized Queries              │

└─────────────────────────────────────────────────────────────────┘

# Create conda environment (recommended)```

conda create -n auto_job python=3.11.11

conda activate auto_job## 📋 System Requirements



# Install dependencies### Minimum Requirements

pip install -r requirements.txt- **Python**: 3.8 or higher

- **Memory**: 4GB RAM

# Verify installation- **Storage**: 2GB free space

python --version  # Should show Python 3.11.11- **Network**: Stable internet connection

python test_complete_pipeline.py

```### Recommended for Optimal Performance

- **Python**: 3.11+

### Development Setup- **Memory**: 8GB+ RAM

- **GPU**: CUDA-compatible GPU for AI processing

```bash- **Storage**: SSD with 5GB+ free space

# Install dev dependencies

pip install -r requirements-dev.txt## 🛠️ Installation



# Install pre-commit hooks### Standard Installation

pre-commit install

```bash

# Run quality checks# Clone repository

python -m black --check src/ tests/git clone <repository-url>

python -m mypy src/cd jobqst

pytest --cov=src --cov-report=html

```# Create virtual environment

python -m venv venv

---source venv/bin/activate  # On Windows: venv\Scripts\activate



## Usage Guide# Install dependencies

pip install -r requirements.txt

### 1. Profile Setup

# Verify installation

```bashpython test_complete_pipeline.py

# Interactive setup```

python main.py --setup-profile YourName

### Development Installation

# Or manually edit: profiles/YourName/YourName.json

{```bash

  "profile_name": "YourName",# Install development dependencies

  "keywords": ["Python Developer", "Software Engineer"],pip install -r requirements-dev.txt

  "locations": ["Toronto", "Vancouver", "Remote"],

  "experience_level": "mid"# Install pre-commit hooks

}pre-commit install

```

# Run quality checks

### 2. Job Discoveryblack --check src/ tests/

mypy src/

```bashpytest --cov=src --cov-report=term-missing

# Modern JobSpy pipeline (recommended)```

python main.py YourName --action jobspy-pipeline \

  --jobspy-preset canada_comprehensive \## 🎯 Usage Guide

  --enable-cache

### Profile Setup

# Custom search

python main.py YourName --action jobspy-pipeline \Create a personalized job search profile:

  --sites indeed,linkedin \

  --locations "Toronto, ON" "Vancouver, BC" \```bash

  --search-terms "Python Developer" "Data Scientist"# Interactive profile creation

python main.py --setup-profile YourName

# Legacy scraping (fallback)

python main.py YourName --action scrape --jobs 100# Or manually edit: profiles/YourName/YourName.json

```{

  "profile_name": "YourName",

**Available Presets:**  "keywords": ["Python Developer", "Software Engineer"],

- `canada_comprehensive` - 20+ Canadian cities  "locations": ["Toronto", "Vancouver", "Remote"],

- `tech_hubs_canada` - Toronto, Vancouver, Montreal, etc.  "experience_level": "mid",

- `usa_comprehensive` - 50+ USA cities  "salary_range": "80000-120000"

- `usa_tech_hubs` - San Francisco, Seattle, Austin, etc.}

- `remote_focused` - Remote opportunities```



### 3. Job Analysis### Job Scraping



```bash```bash

# Analyze discovered jobs# Basic scraping

python main.py YourName --action analyze-jobs --enable-cachepython main.py YourName --action scrape --jobs 100



# Force reprocessing# Advanced scraping with options

python main.py YourName --action analyze-jobs --force-reprocesspython main.py YourName --action scrape \

```  --jobs 200 \

  --sites eluta,external \

### 4. Dashboard  --auto-process \

  --enable-gpu

```bash

# Launch dashboard# Scheduled scraping

python main.py YourName --action dashboardpython scripts/scheduling/scheduler.py

```

# Access at: http://localhost:8050

```### Dashboard Analytics



**Dashboard Features:**```bash

- **Ranked Jobs** - Browse and filter jobs by compatibility score# Launch interactive dashboard

- **Job Tracker** - Manage application statuspython src/dashboard/unified_dashboard.py --profile YourName

- **Market Insights** - Analytics and trends

# Access at: http://localhost:8501

---```



## Configuration### Command Line Interface



### JobSpy Presets```bash

# Interactive mode

Presets are defined in `src/config/jobspy_integration_config.py`:python main.py YourName



```python# Available actions:

JOBSPY_LOCATION_SETS = {# - scrape: Discover new jobs

    "canada_comprehensive": [/* 20+ cities */],# - process: Analyze existing jobs  

    "tech_hubs_canada": ["Toronto", "Vancouver", "Montreal", ...],# - dashboard: Launch analytics dashboard

    "usa_tech_hubs": ["San Francisco", "Seattle", "Austin", ...],# - export: Export job data

}# - cleanup: Remove duplicates

```

JOBSPY_QUERY_PRESETS = {

    "comprehensive": [/* 20+ search terms */],## 📊 Performance Metrics

    "python_focused": ["Python Developer", "Python Engineer", ...],

    "data_focused": ["Data Analyst", "Data Scientist", ...],### Scraping Performance

}- **Speed**: 2+ jobs/second with parallel processing

```- **Accuracy**: 95%+ relevant job matching

- **Deduplication**: 85%+ duplicate detection rate

### Environment Variables- **Coverage**: Multiple job boards and sources



Create `.env` file:### Processing Performance

- **AI Analysis**: GPU-accelerated compatibility scoring

```bash- **Skill Extraction**: 90%+ accuracy in skill identification

# Database- **Response Time**: <2 seconds for job analysis

DATABASE_TYPE=duckdb  # or sqlite- **Throughput**: 100+ jobs/minute processing



# AI Processing## 🔧 Configuration

ENABLE_GPU=true

DISABLE_HEAVY_AI=false### Environment Variables



# Logging```bash

LOG_LEVEL=INFO# .env file configuration

DATABASE_URL=profiles/{profile_name}/{profile_name}_duckdb.db

# CachingLOG_LEVEL=INFO

ENABLE_CACHE=trueENABLE_GPU=true

CACHE_TTL_SECONDS=300MAX_WORKERS=10

```SCRAPING_DELAY=1.0

```

---

### Advanced Configuration

## Architecture Overview

```python

```# config/settings.py

JobLens Pipelinefrom pydantic import BaseSettings



CLI (main.py)class Settings(BaseSettings):

    ↓    max_concurrent_requests: int = 5

Command Dispatcher    request_timeout: int = 30

    ↓    retry_attempts: int = 3

JobSpy Controller    enable_ai_processing: bool = True

    ↓    

Multi-Site Workers (4 sites parallel)    class Config:

    ↓        env_file = ".env"

Unified Deduplication```

    ↓

Two-Stage Processing (CPU → GPU)## 🧪 Testing

    ↓

DuckDB Storage### Running Tests

    ↓

Dashboard (Dash)```bash

```# Full test suite

pytest

**Key Components:**

- **JobSpy Workers** (`src/scrapers/multi_site_jobspy_workers.py`) - Parallel scraping# With coverage

- **Two-Stage Processor** (`src/analysis/two_stage_processor.py`) - AI analysispytest --cov=src --cov-report=html

- **DuckDB Database** (`src/core/duckdb_database.py`) - High-performance storage

- **Unified Deduplication** (`src/core/unified_deduplication.py`) - Single dedup system# Specific test categories

- **Dashboard** (`src/dashboard/dash_app/app.py`) - Interactive UIpytest tests/unit/          # Unit tests

pytest tests/integration/   # Integration tests

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.pytest tests/e2e/          # End-to-end tests



---# Pipeline health check

python test_complete_pipeline.py

## Performance```



### Scraping### Test Coverage Requirements

- **Speed:** 2-3 jobs/second with 4 parallel workers- **Minimum**: 80% code coverage

- **Success Rate:** 85-90% (varies by site)- **Critical paths**: 95% coverage required

- **Relevance:** 95%+ after AI filtering- **New features**: 100% coverage required



### Processing## 📈 Monitoring & Observability

- **Stage 1 (CPU):** ~100 jobs/minute

- **Stage 2 (AI):** ~20 jobs/minute (with cache: ~100 jobs/minute)### Health Checks

- **Cache Hit Rate:** 70-80%

```bash

### Database# System health check

- **DuckDB vs SQLite:** 10-100x faster analytical queriespython test_complete_pipeline.py

- **Query Speed:** <500ms for dashboard with cache

# Database health

---python -c "from src.core.job_database import get_job_db; print(get_job_db().get_job_stats())"



## Testing# Scraper status

python -c "from src.scrapers import get_scraper_status; print(get_scraper_status())"

```bash```

# Full test suite

pytest tests/ -v --cov=src --cov-report=html### Logging



# Specific categories```python

pytest tests/unit/ -v                    # Fast unit tests# Structured logging with context

pytest tests/integration/ -v             # Integration testsimport logging

pytest tests/integration/ -v --real-scraping  # With live scrapingfrom src.utils.logging import get_logger



# Quick health checklogger = get_logger(__name__)

python test_complete_pipeline.pylogger.info("Job scraping started", extra={"profile": "YourName", "target_jobs": 100})

``````



**Current Coverage:** ~85% (target: 90%)## 🚀 Deployment



---### Production Deployment



## Development Standards```bash

# Using Docker

JobLens follows strict development standards documented in [DEVELOPMENT_STANDARDS.md](docs/DEVELOPMENT_STANDARDS.md).docker-compose -f docker-compose.infrastructure.yml up -d



**Current Compliance:** 93/100 ✅# Using systemd (Linux)

sudo cp scripts/scheduling/jobqst-scheduler.service /etc/systemd/system/

### Quality Toolssudo systemctl enable jobqst-scheduler

sudo systemctl start jobqst-scheduler

```bash

# Code formatting# Using Windows Task Scheduler

python -m black src/ tests/# Run as Administrator: scripts/scheduling/setup_windows_scheduler.bat

```

# Type checking

python -m mypy src/### Scaling Considerations



# Linting- **Horizontal Scaling**: Multiple scraper instances with shared database

python -m flake8 src/ tests/- **Vertical Scaling**: Increase worker threads and memory allocation

- **Database Optimization**: Regular VACUUM and index maintenance

# Import sorting- **Caching**: Redis for frequently accessed data

python -m isort src/ tests/

## 🔒 Security

# Security scanning

python -m bandit -r src/### Security Features

```- **Input Validation**: All external input sanitized

- **Rate Limiting**: Respectful scraping practices

### Pre-commit Hooks- **Error Handling**: No sensitive data in error messages

- **Dependency Scanning**: Regular security audits

```bash

# Install hooks### Security Best Practices

pre-commit install

```bash

# Run manually# Security scanning

pre-commit run --all-filesbandit -r src/

```safety check

pip-audit

---

# Secure configuration

## Troubleshooting# Never commit .env files

# Use environment variables for secrets

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues.# Regular dependency updates

```

### Quick Fixes

## 🤝 Contributing

| Problem | Solution |

|---------|----------|### Development Workflow

| No jobs found | Check keywords: `python -c "from src.utils.profile_helpers import load_profile; print(load_profile('YourProfile')['keywords'])"` |

| Database errors | Restart: `pkill -f python; python main.py YourProfile` |1. **Fork** the repository

| Wrong environment | Activate: `conda activate auto_job` |2. **Create** feature branch: `git checkout -b feature/amazing-feature`

| Import errors | Reinstall: `pip install -r requirements.txt` |3. **Follow** [development standards](docs/DEVELOPMENT_STANDARDS.md)

4. **Test** your changes: `pytest`

### Environment Verification5. **Commit** with conventional commits: `feat: add amazing feature`

6. **Push** and create Pull Request

```bash

# Check Python version### Code Quality Requirements

python --version  # Should be 3.11.11

```bash

# Check environment# Before submitting PR

python -c "import sys; print(sys.executable)"black src/ tests/           # Code formatting

# Expected: .../miniconda3/envs/auto_job/python.exeisort src/ tests/           # Import sorting

flake8 src/ tests/          # Linting

# Verify toolsmypy src/                   # Type checking

python -m black --version   # 25.1.0pytest --cov=src            # Test coverage

python -m mypy --version    # 1.14.1```

```

## 📚 Documentation

---

- **[Development Standards](docs/DEVELOPMENT_STANDARDS.md)**: Code quality and patterns

## Documentation- **[Architecture Guide](docs/ARCHITECTURE.md)**: System design and components

- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions

- **[DEVELOPMENT_STANDARDS.md](docs/DEVELOPMENT_STANDARDS.md)** - Coding standards (93/100 compliance)

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design## 🆘 Support

- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Getting Help

---

- **Documentation**: Check docs/ directory first

## Contributing- **Issues**: Create GitHub issue with reproduction steps

- **Discussions**: Use GitHub Discussions for questions

1. Fork the repository- **Security**: Email security issues privately

2. Create feature branch: `git checkout -b feature/amazing-feature`

3. Follow [DEVELOPMENT_STANDARDS.md](docs/DEVELOPMENT_STANDARDS.md)### Common Issues

4. Run quality checks: `pre-commit run --all-files`

5. Commit with conventional commits: `feat: add amazing feature````bash

6. Push and create Pull Request# Database connection issues

python -c "from src.core.job_database import get_job_db; get_job_db().get_job_count()"

---

# Scraper issues

## Licensepython test_complete_pipeline.py



MIT License - see [LICENSE](LICENSE) file for details.# Performance issues

python -m cProfile -o profile.stats main.py YourName --action scrape --jobs 10

---```



## Acknowledgments## 📄 License



- **[JobSpy](https://github.com/cullena20/JobSpy)** - Multi-site job scraping foundationThis project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

- **[DuckDB](https://duckdb.org/)** - High-performance analytics database

- **[Dash](https://dash.plotly.com/)** - Interactive dashboard framework## 🙏 Acknowledgments



---- **JobSpy**: External job board integration

- **DuckDB**: High-performance analytics database

**Built for job seekers with ❤️ and modern Python**- **Playwright**: Reliable web scraping

- **Transformers**: AI-powered job analysis

*JobLens - Making job search intelligent, automated, and effective.*- **Dash**: Interactive dashboard framework


## 🙏 Acknowledgments

Special thanks to the [JobSpy Project](https://github.com/speedyapply/JobSpy) for excellent multi-site scraping foundation.

---

**Ready to get started?** → [Quick Start](#quick-start)

**Built with ❤️ for job seekers everywhere**

*JobQst - Making job search intelligent, automated, and effective.*
=======
# JobQst - Intelligent Job Discovery & Automation Platform

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

## What is JobQst?

JobQst is an intelligent job discovery and analysis platform that automates your job search across **4 major job sites** (Indeed, LinkedIn, Glassdoor, ZipRecruiter) using **JobSpy integration**. It provides **AI-powered job-profile matching**, **intelligent caching**, and **real-time analytics** through a modern Dash dashboard.

Built with **clean Python architecture** following modern development standards with **full type annotations**, **DuckDB analytics**, and **production-ready error handling**.

### 🎯 **Perfect For:**

- **Job Seekers** wanting automated, intelligent job discovery and tracking
- **Career Professionals** managing applications with AI-powered insights  
- **Developers** seeking opportunities with location-specific search capabilities
- **Anyone** optimizing their job search with automation and analytics

### ✨ **Current Features (January 2025)**

- ✅ **JobSpy Multi-Site Integration** - 4 major job sites (Indeed, LinkedIn, Glassdoor, ZipRecruiter) with parallel scraping
- ✅ **AI-Powered Job Matching** - Two-stage processing with semantic similarity analysis and compatibility scoring
- ✅ **Intelligent Caching System** - 3-layer caching (HTML, embeddings, results) for 70% performance improvement
- ✅ **DuckDB Analytics** - High-performance columnar database for 10-100x faster analytics
- ✅ **Modern Dash Dashboard** - Interactive web interface with real-time monitoring and performance analytics
- ✅ **Smart Relevance Filtering** - AI-powered job filtering to eliminate irrelevant results
- ✅ **Type-Safe Architecture** - Full type annotations (93/100 compliance) following modern Python standards
- ✅ **Profile-Based System** - Multiple user profiles with dedicated databases
- ✅ **Unified Deduplication** - Single, authoritative deduplication system across all job sources
- ✅ **Configurable Presets** - Pre-configured search strategies (Canada, USA, Tech Hubs, Remote)

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
git clone https://github.com/NirajanKhadka/JobQst.git
cd JobQst

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

# 1. Run JobSpy discovery pipeline (primary workflow)
python main.py YourProfile --action jobspy-pipeline \
  --jobspy-preset canada_comprehensive \
  --workers 4

# 2. Process and analyze discovered jobs
python main.py YourProfile --action process-jobs

# 3. Launch interactive dashboard
python main.py YourProfile --action dashboard

# 4. System health check and diagnostics
python main.py YourProfile --action health-check

# 5. Interactive CLI menu (guided workflow)
python main.py YourProfile --action interactive
```

### Available Actions

| Action | Description | Key Options |
|--------|-------------|-------------|
| `jobspy-pipeline` | **Multi-site job discovery** via JobSpy | `--jobspy-preset <preset>`, `--sites <sites>`, `--workers <n>` |
| `process-jobs` | **AI-powered job analysis** with caching | `--jobs <limit>`, `--verbose` |
| `dashboard` | **Interactive Dash interface** | Launches at http://localhost:8050 |
| `health-check` | **System diagnostics** | Database, cache, and worker health |
| `benchmark` | **Performance testing** | Pipeline and system benchmarks |
| `interactive` | **CLI menu** for guided workflows | User-friendly menu interface |

## Architecture Overview

JobQst follows a clean, modular architecture with type-safe Python code:

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

## Deployment & Running

### Local Setup (Recommended)

```bash
# 1. Environment setup
conda create -n jobqst_local python=3.11
conda activate jobqst_local
pip install -r requirements.txt

# 2. Start using it
python main.py YourProfile --action jobspy-pipeline
python main.py YourProfile --action dashboard  # Dashboard on localhost:8050
```

### Running on a Server

If you want to run JobQst on a remote server:

```bash
# 1. SSH into server and set up conda environment
ssh your-server
conda create -n auto_job python=3.11
conda activate auto_job
pip install -r requirements.txt

# 2. Run in background with screen/tmux
screen -S jobqst
python main.py YourProfile --action dashboard  # Keeps dashboard running

# 3. Detach with Ctrl+A, D
# Reattach with: screen -r jobqst

# 4. Access dashboard via SSH tunnel
# On your local machine:
ssh -L 8050:localhost:8050 your-server
# Then open http://localhost:8050 in browser
```

### Deployment Notes

**Current Status**: JobQst is designed for local development and personal use.

**What exists:**
- Conda environment setup (documented above)
- Local DuckDB database (per-profile)
- Dash dashboard on localhost:8050
- CLI automation tools

**What doesn't exist (yet):**
- Docker containerization
- Cloud deployment configs
- Production database setup
- Multi-server deployment
- CI/CD pipelines

If you need to run JobQst on a server, you can:
1. Set up the conda environment on the server
2. Run commands via SSH or cron jobs
3. Use screen/tmux to keep dashboard running
4. Forward port 8050 for dashboard access

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
git clone https://github.com/NirajanKhadka/JobQst.git
cd JobQst
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

>>>>>>> 3453a189c0e9f3dda20d826d2c007af33d914c04
