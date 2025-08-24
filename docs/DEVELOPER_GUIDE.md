---
post_title: "JobQst Developer Guide"
author1: "Nirajan Khadka"
post_slug: "jobqst-developer-guide"
microsoft_alias: "nirajank"
featured_image: ""
categories: ["development", "ai", "automation", "architecture"]
tags: ["jobqst", "ai-powered", "multi-site-scraping", "semantic-analysis", "clean-architecture"]
ai_note: "Complete developer guide for JobQst intelligent job discovery platform with clean, modern architecture."
summary: "Comprehensive development guide for JobQst AI-powered job discovery platform"
post_date: "2025-08-23"
---

# 🚀 JobQst Developer Guide

*Complete development guide for the intelligent, AI-powered job discovery platform*

This guide covers development setup, architecture patterns, and best practices for JobQst - featuring clean single-entry-point architecture, AI-powered job analysis, and multi-site parallel scraping.

## 📋 Table of Contents

1. [Quick Setup](#quick-setup)
2. [Clean Architecture Overview](#clean-architecture-overview)
3. [AI-Powered Development](#ai-powered-development)
4. [Multi-Site Scraping](#multi-site-scraping)
5. [Testing & Quality](#testing--quality)
6. [Performance & Optimization](#performance--optimization)
7. [Dashboard Development](#dashboard-development)
8. [Deployment & Production](#deployment--production)
9. [Troubleshooting](#troubleshooting)
10. [Contributing Guidelines](#contributing-guidelines)

---

## 🚀 Quick Setup

### **Prerequisites**
- **Python 3.11+** (Required for modern features)
- **Git** for version control
- **Conda** (Recommended for environment management)
- **VS Code/Cursor** with Python extensions (Recommended)

### **Environment Setup**
```bash
# Clone the repository
git clone https://github.com/NirajanKhadka/JobQst.git
cd JobQst

# Create conda environment (recommended)
conda create -n auto_job python=3.11
conda activate auto_job

# Install Python dependencies
pip install -r requirements.txt

# Install JobSpy for multi-site scraping (Indeed, LinkedIn, Glassdoor, ZipRecruiter)
pip install python-jobspy

# Install Playwright for browser automation
playwright install chromium

# Verify installation
python -c "from jobspy import scrape_jobs; print('JobSpy Available: True')"
python -c "from src.scrapers.unified_eluta_scraper import ElutaScraper; print('Eluta Scraper Available: True')"

# Test system functionality
python main.py TestProfile --action jobspy-pipeline --jobspy-preset usa_comprehensive --sites indeed,linkedin
```

### **Dashboard Development**

```bash
# Start the Dash dashboard (Primary interface)
conda run -n auto_job python src/dashboard/dash_app/app.py

# Or use VS Code tasks (Ctrl+Shift+P → Tasks: Run Task)
# - Start Dash Dashboard

# Alternative: Use CLI dashboard action
python main.py TestProfile --action dashboard

# Dashboard will be available at:
# http://localhost:8050 (Dash default port)
```
# - Start Dashboard Frontend
```

---

## 🔧 AI-Powered Architecture

### **System Overview**

JobLens uses a modern AI-powered architecture with intelligent multi-site scraping, semantic analysis, and real-time dashboard capabilities.

```
src/core/                               # Core components
├── user_profile_manager.py             # Profile management system
├── job_database.py                     # Database abstraction layer
└── processor.py                        # Job processing engine

src/scrapers/                           # Multi-site scraping
├── jobspy_enhanced_scraper.py          # Primary: 4-site parallel scraper
├── multi_site_jobspy_workers.py        # Parallel worker coordination
├── unified_eluta_scraper.py            # Fallback: Eluta.ca scraper
└── external_job_scraper.py             # Enhanced job descriptions

src/services/                           # AI and analytics
├── ai_integration_service.py           # AI-powered analysis
├── smart_deduplication_service.py      # Intelligent duplicate removal
├── job_analytics_service.py            # Advanced analytics
└── location_detection_service.py       # Location intelligence

src/pipeline/                           # Processing pipeline
├── fast_job_pipeline.py                # Main processing pipeline
└── jobspy_streaming_orchestrator.py    # Stream processing

dashboard/                              # Modern React/FastAPI dashboard
├── backend/                            # FastAPI backend
└── frontend/                           # React frontend
```

### **Development Workflow**

#### **1. Multi-Site JobSpy Development**

```python
# Modern JobSpy integration with 4 sites in parallel
from src.scrapers.jobspy_enhanced_scraper import JobSpyEnhancedScraper

# Initialize with profile
scraper = JobSpyEnhancedScraper("TestProfile")

# Run USA comprehensive search across all 4 sites
jobs = await scraper.scrape_with_preset("usa_comprehensive")

# Custom multi-site configuration
from src.config.jobspy_integration_config import JobSpyConfig

config = JobSpyConfig(
    locations=["New York, NY", "San Francisco, CA", "Toronto, ON"],
    search_terms=["python developer", "software engineer", "data scientist"],
    sites=["indeed", "linkedin", "glassdoor", "zip_recruiter"],  # All 4 sites
    results_per_search=100,
    country_code="USA"  # or "Canada"
)
jobs = await scraper.scrape_jobs(config)
```

#### **2. AI Integration Development**

```python
# AI-powered job analysis
from src.services.ai_integration_service import AIIntegrationService

# Initialize AI service
ai_service = AIIntegrationService("TestProfile")

# Analyze job compatibility
score = await ai_service.analyze_job_compatibility(job_data, user_profile)

# Smart deduplication
from src.services.smart_deduplication_service import SmartDeduplicationService
dedup_service = SmartDeduplicationService()
unique_jobs = await dedup_service.remove_duplicates(jobs_list)

# Location intelligence
from src.services.location_detection_service import LocationDetectionService
location_service = LocationDetectionService()
location_data = await location_service.analyze_location(job_location)
```

#### **3. Dashboard Development**

```python
# FastAPI backend development
# dashboard/backend/app/main.py
from fastapi import FastAPI, Depends
from app.routers import jobs, analytics, profiles

app = FastAPI(title="JobLens API", version="2.0.0")
app.include_router(jobs.router, prefix="/api/jobs")
app.include_router(analytics.router, prefix="/api/analytics")

# React frontend development
# dashboard/frontend/src/components/JobCard.tsx
import { Job } from '../types/Job';
import { FitScoreIndicator } from './FitScoreIndicator';

export const JobCard: React.FC<{ job: Job }> = ({ job }) => {
  return (
    <div className="job-card">
      <h3>{job.title}</h3>
      <FitScoreIndicator score={job.fit_score} />
    </div>
  );
};
```

#### **4. Testing Development**

```python
# Unit testing with pytest
import pytest
from src.scrapers.jobspy_enhanced_scraper import JobSpyEnhancedScraper

@pytest.mark.asyncio
async def test_jobspy_scraper():
    scraper = JobSpyEnhancedScraper("TestProfile")
    jobs = await scraper.scrape_with_preset("usa_comprehensive")
    assert len(jobs) > 0
    assert all(job.get('title') for job in jobs)

# Integration testing
def test_pipeline_integration():
    from src.pipeline.fast_job_pipeline import FastJobPipeline
    pipeline = FastJobPipeline("TestProfile")
    result = pipeline.run_complete_pipeline()
    assert result["status"] == "success"

# Performance testing
def test_multi_site_performance():
    import time
    start_time = time.time()
    # Run multi-site scraper
    duration = time.time() - start_time
    assert duration < 300  # Should complete within 5 minutes
```

#### **5. CLI Development**

```python
# Main CLI entry point (main.py)
import click
from src.core.user_profile_manager import UserProfileManager

@click.command()
@click.argument('profile_name')
@click.option('--action', required=True, help='Action to perform')
@click.option('--sites', default='indeed,linkedin,glassdoor,zip_recruiter')
def main(profile_name, action, sites):
    """JobLens - AI-Powered Job Discovery Platform"""
    
    # Modern CLI commands
    if action == "jobspy-pipeline":
        # Multi-site parallel scraping
        run_jobspy_pipeline(profile_name, sites.split(','))
    elif action == "analyze-jobs":
        # AI-powered analysis
        run_job_analysis(profile_name)
    elif action == "dashboard":
        # Launch modern dashboard
        launch_dashboard(profile_name)
```

---

## 🧪 Testing Guide

### **Running Tests**

```bash
# Run all tests
conda run -n auto_job python -m pytest

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests
pytest tests/integration/ -v             # Integration tests
pytest tests/scrapers/ -v                # Scraper tests

# Run with coverage
pytest --cov=src tests/ --cov-report=html

# VS Code integration
# Use task: "Run all tests (pytest)"
```

```

### **Test Categories**

```python
# Performance tests
@pytest.mark.performance
def test_scraper_performance():
    """Test scraper performance metrics"""
    pass

# Integration tests  
@pytest.mark.integration
def test_pipeline_integration():
    """Test full pipeline integration"""
    pass

# API tests
@pytest.mark.api
def test_dashboard_api():
    """Test dashboard API endpoints"""
    pass
```

---

## 📊 Performance Monitoring

### **Metrics & Analytics**

```python
# Performance tracking
from src.services.job_analytics_service import JobAnalyticsService

analytics = JobAnalyticsService("TestProfile")

# Track scraping performance
metrics = analytics.get_scraping_metrics()
print(f"Jobs per minute: {metrics['jobs_per_minute']}")
print(f"Success rate: {metrics['success_rate']}%")

# Monitor AI processing
ai_metrics = analytics.get_ai_processing_metrics()
print(f"Analysis speed: {ai_metrics['analyses_per_second']}")
```

### **System Health Checks**

```bash
# Health check scripts
python scripts/production_health_check.ps1

# Database integrity
python check_db.py

# Performance audit
python scripts/maintenance/performance_audit.py
```

---

## 🚀 Deployment Guide

### **Production Setup**

```bash
# Production environment
conda create -n auto_job_prod python=3.11
conda activate auto_job_prod
pip install -r requirements.txt

# Configure production settings
export JOBSPY_RATE_LIMIT=30
export AI_BATCH_SIZE=50
export DASHBOARD_HOST=0.0.0.0
export DASHBOARD_PORT=8000

# Launch production dashboard
uvicorn dashboard.backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### **Docker Deployment**

```bash
# Build and run with Docker
docker-compose -f docker-compose.yml up -d

# Scale services
docker-compose up --scale scraper-worker=4 --scale ai-processor=2
```

---

## 🔧 Troubleshooting

### **Common Issues**

1. **JobSpy Installation Issues**
   ```bash
   pip uninstall python-jobspy
   pip install python-jobspy --no-cache-dir
   ```

2. **Playwright Browser Issues** 
   ```bash
   playwright install chromium --force
   ```

3. **Dashboard Connection Issues**
   ```bash
   # Check ports
   netstat -tulpn | grep :8000
   
   # Restart services
   pkill -f uvicorn
   conda run -n auto_job uvicorn dashboard.backend.app.main:app --reload
   ```

---

## 🤝 Contributing Guidelines

### **Code Standards**

- **Python 3.11+** with type hints
- **Black** for code formatting
- **Pylint** for code analysis  
- **Pytest** for testing
- **Async/await** for I/O operations

### **Pull Request Process**

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Write tests for new functionality
4. Ensure all tests pass: `pytest tests/ -v`
5. Submit pull request with clear description

---

*Last Updated: 2025-01-23 | JobLens v2.0.0*