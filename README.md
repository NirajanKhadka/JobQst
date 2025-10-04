# JobQst - Intelligent Job Discovery Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy.readthedocs.io/)
[![Compliance: 93/100](https://img.shields.io/badge/compliance-93%2F100-success.svg)](docs/DEVELOPMENT_STANDARDS.md)

> **Automated job discovery across Indeed, LinkedIn, Glassdoor & ZipRecruiter with AI-powered matching**

---

## What Is JobQst?

JobQst automates job searching across 4 major job sites using [JobSpy](https://github.com/cullena20/JobSpy), then uses AI to match jobs to your profile. Built with clean Python, type safety, and a Dash dashboard for visualization.

**Built for:** Developers and tech professionals job hunting in Canada/USA.

### Core Features

- 🔍 Multi-site scraping (Indeed, LinkedIn, Glassdoor, ZipRecruiter)
- 🧠 AI-powered job matching with compatibility scores
- 📊 Real-time analytics dashboard
- ⚡ Intelligent caching (70% performance boost)
- 🎯 Profile-based system with dedicated databases
- 🛡️ Type-safe code (93/100 compliance)

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/NirajanKhadka/JobQst.git
cd JobQst

# Create environment (Python 3.11 required)
conda create -n auto_job python=3.11
conda activate auto_job

# Install dependencies
pip install -r requirements.txt

# Create your profile
python main.py --setup-profile YourName

# Start job discovery
python main.py YourName --action jobspy-pipeline --jobspy-preset canada_comprehensive

# View dashboard
python main.py YourName --action dashboard
```

Access dashboard at: `http://localhost:8050`

---

## System Requirements

### Minimum

- **Python:** 3.11+ (required)
- **Memory:** 4GB RAM
- **Storage:** 2GB free space
- **Network:** Stable internet connection

### Recommended

- **Memory:** 8GB+ RAM
- **GPU:** CUDA-compatible for AI processing
- **Storage:** SSD with 5GB+ free space

---

## Installation

### Standard Setup

```bash
# Clone repository
git clone https://github.com/NirajanKhadka/JobQst.git
cd JobQst

# Create conda environment (recommended)
conda create -n auto_job python=3.11
conda activate auto_job

# Install dependencies
pip install -r requirements.txt

# Verify installation
python --version  # Should show Python 3.11+
```

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run quality checks
python -m black --check src/ tests/
python -m mypy src/
pytest --cov=src --cov-report=html
```

---

## Usage Guide

### 1. Profile Setup

```bash
# Interactive setup
python main.py --setup-profile YourName

# Or manually edit: profiles/YourName/YourName.json
{
  "profile_name": "YourName",
  "keywords": ["Python Developer", "Software Engineer"],
  "locations": ["Toronto", "Vancouver", "Remote"],
  "experience_level": "mid",
  "salary_range": "80000-120000"
}
```

### 2. Job Discovery

```bash
# Modern JobSpy pipeline (recommended)
python main.py YourName --action jobspy-pipeline \
  --jobspy-preset canada_comprehensive \
  --enable-cache

# Custom search
python main.py YourName --action jobspy-pipeline \
  --sites indeed,linkedin \
  --locations "Toronto, ON" "Vancouver, BC" \
  --search-terms "Python Developer" "Data Scientist"

# Legacy scraping (fallback)
python main.py YourName --action scrape --jobs 100
```

**Available Presets:**

- `canada_comprehensive` - 20+ Canadian cities
- `tech_hubs_canada` - Toronto, Vancouver, Montreal, etc.
- `usa_comprehensive` - 50+ USA cities
- `usa_tech_hubs` - San Francisco, Seattle, Austin, etc.
- `remote_focused` - Remote opportunities

### 3. Job Analysis

```bash
# Analyze discovered jobs
python main.py YourName --action analyze-jobs --enable-cache

# Force reprocessing
python main.py YourName --action analyze-jobs --force-reprocess
```

### 4. Dashboard

```bash
# Launch dashboard
python main.py YourName --action dashboard
# Access at: http://localhost:8050
```

**Dashboard Features:**

- **Ranked Jobs** - Browse and filter jobs by compatibility score
- **Job Tracker** - Manage application status
- **Market Insights** - Analytics and trends

---

## Configuration

### JobSpy Presets

Presets are defined in `src/config/jobspy_integration_config.py`:

```python
JOBSPY_LOCATION_SETS = {
    "canada_comprehensive": [/* 20+ cities */],
    "tech_hubs_canada": ["Toronto", "Vancouver", "Montreal", ...],
    "usa_tech_hubs": ["San Francisco", "Seattle", "Austin", ...],
}

JOBSPY_QUERY_PRESETS = {
    "comprehensive": [/* 20+ search terms */],
    "python_focused": ["Python Developer", "Python Engineer", ...],
    "data_focused": ["Data Analyst", "Data Scientist", ...],
}
```

### Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_TYPE=duckdb  # or sqlite

# AI Processing
ENABLE_GPU=true
DISABLE_HEAVY_AI=false

# Logging
LOG_LEVEL=INFO

# Caching
ENABLE_CACHE=true
CACHE_TTL_SECONDS=300
```

---

## Architecture Overview

```text
JobQst Pipeline

CLI (main.py)
    ↓
Command Dispatcher
    ↓
JobSpy Controller
    ↓
Multi-Site Workers (4 sites parallel)
    ↓
Unified Deduplication
    ↓
Two-Stage Processing (CPU → GPU)
    ↓
DuckDB Storage
    ↓
Dashboard (Dash)
```

**Key Components:**

- **JobSpy Workers** (`src/scrapers/multi_site_jobspy_workers.py`) - Parallel scraping
- **Two-Stage Processor** (`src/analysis/two_stage_processor.py`) - AI analysis
- **DuckDB Database** (`src/core/duckdb_database.py`) - High-performance storage
- **Unified Deduplication** (`src/core/unified_deduplication.py`) - Single dedup system
- **Dashboard** (`src/dashboard/dash_app/app.py`) - Interactive UI

See [Architecture Documentation](docs/ARCHITECTURE.md) for complete system design.

---

## Performance

### Scraping

- **Speed:** 2-3 jobs/second with 4 parallel workers
- **Success Rate:** 85-90% (varies by site)
- **Relevance:** 95%+ after AI filtering

### Processing

- **Stage 1 (CPU):** ~100 jobs/minute
- **Stage 2 (AI):** ~20 jobs/minute (with cache: ~100 jobs/minute)
- **Cache Hit Rate:** 70-80%

### Database

- **DuckDB vs SQLite:** 10-100x faster analytical queries
- **Query Speed:** <500ms for dashboard with cache

---

## Testing

```bash
# Full test suite
pytest tests/ -v --cov=src --cov-report=html

# Specific categories
pytest tests/unit/ -v                    # Fast unit tests
pytest tests/integration/ -v             # Integration tests
pytest tests/integration/ -v --real-scraping  # With live scraping

# Quick health check
python test_complete_pipeline.py
```

**Current Coverage:** ~85% (target: 90%)

---

## Development Standards

**Code Quality:** 93/100 ✅

### Quality Tools

```bash
# Code formatting
python -m black src/ tests/

# Type checking
python -m mypy src/

# Linting
python -m flake8 src/ tests/

# Import sorting
python -m isort src/ tests/

# Security scanning
python -m bandit -r src/
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Troubleshooting

### Quick Fixes

| Problem | Solution |
|---------|----------|
| No jobs found | Check keywords: `python -c "from src.utils.profile_helpers import load_profile; print(load_profile('YourProfile')['keywords'])"` |
| Database errors | Restart: `pkill -f python; python main.py YourProfile` |
| Wrong environment | Activate: `conda activate auto_job` |
| Import errors | Reinstall: `pip install -r requirements.txt` |

### Environment Verification

```bash
# Check Python version
python --version  # Should be 3.11+

# Check environment
python -c "import sys; print(sys.executable)"
# Expected: .../miniconda3/envs/auto_job/python.exe

# Verify tools
python -m black --version
python -m mypy --version
```

---

## Documentation

For detailed system architecture and design patterns, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Write clean, tested code
4. Run quality checks: `pre-commit run --all-files`
5. Commit with conventional commits: `feat: add amazing feature`
6. Push and create Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **[JobSpy](https://github.com/cullena20/JobSpy)** - Multi-site job scraping foundation
- **[DuckDB](https://duckdb.org/)** - High-performance analytics database
- **[Dash](https://dash.plotly.com/)** - Interactive dashboard framework

---

**Built for job seekers with ❤️ and modern Python**

*JobQst - Making job search intelligent, automated, and effective.*
