---
post_title: "JobLens Developer Guide"
author1: "Nirajan Khadka"
post_slug: "developer-guide"
microsoft_alias: "nirajank"
featured_image: ""
categories: ["development", "setup", "scrapers"]
tags: ["development", "setup", "jobspy", "eluta", "workflow"]
ai_note: "Complete development setup and workflow guide for dual scraper architecture."
summary: "Complete development setup for dual scraper architecture with JobSpy and Eluta integration"
post_date: "2025-07-17"
---

## 🚀 JobLens Developer Guide

*Complete development setup for dual scraper architecture with JobSpy and Eluta integration*

This guide covers the development setup for JobLens dual-scraper architecture (JobSpy + Eluta) for job discovery, matching, and ranking.

## 📋 Table of Contents

1. [Quick Setup](#quick-setup)
2. [Dual Scraper Development](#dual-scraper-development)
3. [Pipeline Development](#pipeline-development)
4. [Code Structure](#code-structure)
5. [Testing Framework](#testing-framework)
6. [Performance Optimization](#performance-optimization)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)
9. [Configuration Management](#configuration-management)
10. [Additional Resources](#additional-resources)
11. [Documentation Navigation](#documentation-navigation)

---

## 🚀 Quick Setup

### **Prerequisites**
- Python 3.10+ (3.11 recommended)
- Git
- VS Code, Cursor, or compatible IDE (recommended)


### **Development Environment Setup**
```bash
# Clone repository
git clone <repository-url>
cd automate_job

# Create virtual environment
python -m venv .venv

# Activate environment
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Windows (cmd)
.\.venv\Scripts\activate.bat
# Linux/Mac
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install JobSpy for primary scraper
pip install python-jobspy

# Install Playwright for Eluta scraper
playwright install chromium

# Verify JobSpy installation
python -c "from jobspy import scrape_jobs; print('JobSpy Available: True')"

# Verify Eluta scraper
python -c "from src.scrapers.unified_eluta_scraper import ElutaScraper; print('Eluta Scraper Available: True')"

# Launch development dashboard
python -m streamlit run src/dashboard/unified_dashboard.py --server.port 8501 --server.runOnSave true

# Test dual scraper setup
python main.py Nirajan --action jobspy-pipeline --jobspy-preset fast
```

---

## 🔧 Dual Scraper Development

### **Architecture Overview**

AutoJobAgent uses a dual scraper architecture with JobSpy as the primary multi-site scraper and Eluta as the reliable fallback.

```
src/scrapers/                           # Scraper implementations
├── jobspy_Improved_scraper.py          # Primary: JobSpy multi-site
├── multi_site_jobspy_workers.py        # JobSpy worker coordination
├── unified_eluta_scraper.py            # Secondary: Eluta fallback
├── external_job_scraper.py             # External description enhancement


src/pipeline/                           # Pipeline orchestration
├── Improved_fast_job_pipeline.py       # Primary: 3-phase pipeline
├── fast_job_pipeline.py                # Secondary: Eluta-only pipeline
└── jobspy_streaming_orchestrator.py    # JobSpy coordination

src/config/                             # Configuration management
├── jobspy_integration_config.py        # JobSpy presets and settings
└── ai_service_config.py                # AI processing configuration
```

### **Development Workflow**

#### **1. JobSpy Scraper Development**

```python
# Basic JobSpy scraper usage
from src.scrapers.jobspy_Improved_scraper import JobSpyImprovedScraper

# Initialize with profile
scraper = JobSpyImprovedScraper("Nirajan")

# Run with preset configuration
jobs = await scraper.scrape_with_preset("quality")

# Custom configuration
custom_config = JobSpyConfig(
    locations=["Toronto, ON", "Mississauga, ON"],
    search_terms=["python developer", "software engineer"],
    sites=["indeed", "linkedin"],
    results_per_search=50
)
jobs = await scraper.scrape_jobs(custom_config)
```

#### **2. Multi-Site Worker Development**

```python
# Multi-site worker coordination
from src.scrapers.multi_site_jobspy_workers import MultiSiteJobSpyWorkers

# Initialize workers
workers = MultiSiteJobSpyWorkers(config)

# Run parallel site workers
result = await workers.run_all_workers()

# Access individual site results
indeed_jobs = result.worker_results[0].jobs_data
linkedin_jobs = result.worker_results[1].jobs_data
```

#### **3. Eluta Scraper Development**

```python
# Eluta scraper for fallback/supplementary use
from src.scrapers.unified_eluta_scraper import ElutaScraper

# Initialize scraper
scraper = ElutaScraper("Nirajan", {"jobs": 20, "pages": 3})

# Run scraping
jobs = await scraper.scrape_all_keywords()

# Access statistics
print(f"Jobs found: {scraper.stats['jobs_found']}")
print(f"Success rate: {scraper.stats['success_rate']}")
```

#### **4. Improved Pipeline Development**

```python
# 3-phase Improved pipeline with dual scrapers
from src.pipeline.Improved_fast_job_pipeline import ImprovedFastJobPipeline

# Initialize pipeline
pipeline = ImprovedFastJobPipeline("Nirajan", {
    "enable_jobspy": True,
    "enable_eluta": True,
    "jobspy_preset": "quality",
    "external_workers": 6,
    "processing_method": "auto"
})

# Run complete pipeline
results = await pipeline.run_complete_pipeline()

# Access phase results
jobspy_jobs = results["phase1_jobspy"]
eluta_jobs = results["phase1_eluta"] 
Improved_jobs = results["phase2_external"]
processed_jobs = results["phase3_ai"]
```

#### **5. Configuration Development**

```python
# JobSpy configuration presets
from src.config.jobspy_integration_config import JOBSPY_CONFIG_PRESETS

# Access preset configurations
fast_config = JOBSPY_CONFIG_PRESETS["fast"]
quality_config = JOBSPY_CONFIG_PRESETS["quality"]
comprehensive_config = JOBSPY_CONFIG_PRESETS["comprehensive"]

# Create custom preset
custom_preset = {
    "locations": ["Your Target Areas"],
    "search_terms": ["Your Keywords"],
    "sites": ["indeed", "linkedin"],
    "max_jobs": 100,
    "hours_old": 168
}
```
#### **4. External Job Description Enhancement**

```python
# External job description scraper for Improved content
from src.scrapers.external_job_scraper import ExternalJobDescriptionScraper

# Initialize external scraper with workers
external_scraper = ExternalJobDescriptionScraper(
    profile_name="Nirajan",
    max_workers=6
)

# Enhance job descriptions from URLs
job_urls = ["https://company.com/job1", "https://company.com/job2"]
Improved_jobs = await external_scraper.scrape_job_descriptions(job_urls)

# Access Improved content
for job in Improved_jobs:
    print(f"Title: {job['title']}")
    print(f"Description: {job['description']}")
    print(f"Requirements: {job['requirements']}")
```