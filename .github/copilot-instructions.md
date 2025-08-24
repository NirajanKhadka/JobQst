# JobQst AI Coding Agent Instructions

This document provides essential guidance for AI coding agents working on the JobQst codebase. Following these instructions will help you be more effective and align with the project's architecture and conventions.

## 1. Core Architecture & "Big Picture"

JobQst is a profile-driven, automated job discovery and analysis tool. Its architecture is designed for modularity and scalability.ns AI Coding Agent Instructions

This document provides essential guidance for AI coding agents working on the JobLens codebase. Following these instructions will help you be more effective and align with the project's architecture and conventions.

## 1. Core Architecture & "Big Picture"

JobLens is a profile-driven, automated job discovery and analysis tool. Its architecture is designed for modularity and scalability.

- **Dual Scraper Strategy**: The system uses two main scraping sources:
    1.  **JobSpy (`src/scrapers/jobspy_enhanced_scraper.py`)**: The primary, multi-site scraper supporting Indeed, LinkedIn, Glassdoor, and ZipRecruiter with parallel processing
    2.  **Eluta (`src/scrapers/unified_eluta_scraper.py`)**: A fallback scraper for the Canadian job board Eluta.ca.
- **Multi-Site Parallel Processing (`src/scrapers/multi_site_jobspy_workers.py`)**: JobSpy integration uses parallel workers for each site, with configurable concurrency and country support (USA, Canada, etc.)
- **Processing Pipeline (`src/pipeline/fast_job_pipeline.py`)**: After scraping, jobs are sent through a multi-stage pipeline that filters, analyzes, scores, and ranks them based on user profiles.
- **Profile-Centric Design**: All operations revolve around user profiles located in the `profiles/` directory. Each profile has its own database and settings. The `src/core/user_profile_manager.py` is a key component for managing these profiles.
- **Data Flow**:
    1.  The user initiates an action (e.g., `scrape`) via the CLI (`main.py`).
    2.  The appropriate scraper is invoked (JobSpy with 4 sites in parallel or Eluta as fallback).
    3.  Scraped jobs are stored in a local SQLite database (`data/jobs.db`), associated with the user's profile.
    4.  The analysis action processes these jobs, calculating a "fit score".
    5.  The optional dashboard (`src/dashboard/unified_dashboard.py`) provides a UI to view and interact with the ranked jobs.
- **Microservices-like Structure**: The `src` directory is organized into services (e.g., `job_scraping_service.py`, `job_analysis_service.py`) that communicate via a local event bus (`src/orchestration/local_event_bus.py`). When making changes, respect this separation of concerns.

## 2. Critical Developer Workflows

**IMPORTANT: Always work in the `auto_job` conda environment.**

### Simple Terminal Rules

1. **Use existing terminals** - Don't create new ones
2. **Check environment** - Run `conda activate auto_job` if needed
3. **Use VS Code tasks** - Press `Ctrl+Shift+P` → "Tasks: Run Task"
4. **Working directory** - VS Code starts terminals in workspace folder

### Available Tasks
- **Start Dashboard Backend** - Runs FastAPI server
- **Start Dashboard Frontend** - Runs React dev server  
- **Run all tests** - Executes pytest
- **Install Frontend Dependencies** - Runs npm install

### Environment Setup
- **Environment Setup**: Always ensure you're in the `auto_job` conda environment before running any commands
- **Running the Application**: The main entry point is `main.py`. It's a CLI that takes a profile name and an action.
    - **Scraping Jobs**: `python main.py <ProfileName> --action scrape --keywords "keyword1,keyword2"`
    - **JobSpy Pipeline**: `python main.py <ProfileName> --action jobspy-pipeline --jobspy-preset usa_comprehensive --sites indeed,linkedin,glassdoor,zip_recruiter`
    - **Analyzing Jobs**: `python main.py <ProfileName> --action analyze-jobs`
    - **Running the Dashboard**: `python main.py <ProfileName> --action dashboard`
- **JobSpy Integration**: The system supports 4 job sites (Indeed, LinkedIn, Glassdoor, ZipRecruiter) with parallel processing and country-specific configurations
    - **USA Jobs**: Use presets like `usa_comprehensive`, `usa_tech_hubs`, `usa_major_cities`
    - **Canada Jobs**: Use presets like `canada_comprehensive`, `tech_hubs_canada`
- **Testing**: The project uses `pytest`.
    - **Run all tests**: `pytest tests/ -v`
    - **Run specific tests**: `pytest tests/integration/test_optimized_scraper.py`
- **Dependencies**:
    - Install Python packages: `pip install -r requirements.txt`
    - Install JobSpy: `pip install python-jobspy`
    - Install browser dependencies for Playwright: `playwright install chromium`

## 3. Project-Specific Conventions & Patterns

- **Profile Management**: Always interact with user profiles through the `UserProfileManager` in `src/core/user_profile_manager.py`. Avoid directly manipulating profile JSON files.
- **Database Interaction**: Use the `JobDB` class in `src/core/job_database.py` for all database operations. It handles the connection and querying logic for the profile-specific databases.
- **Configuration**: The project uses a combination of `.env` files for environment variables and JSON files in the `config/` directory for more static configuration. Use the `ConfigManager` where appropriate.
- **Asynchronous Operations**: Scraping is heavily asynchronous. Look at `src/scrapers/parallel_job_scraper.py` for an example of how `asyncio` is used to run scrapers in parallel.
- **CLI Commands**: The CLI is built with `click`. New commands should be added to `main.py`, following the existing structure.

## 4. Key Files & Directories to Reference

- **`main.py`**: The main entry point and CLI. A good place to understand the available top-level commands.
- **`docs/ARCHITECTURE.md`**: Provides a high-level overview of the system design.
- **`src/core/user_profile_manager.py`**: The source of truth for how user profiles are managed.
- **`src/core/job_database.py`**: The abstraction layer for the database.
- **`src/scrapers/`**: Contains the logic for all job scrapers. This is where to look for web scraping patterns.
- **`src/scrapers/multi_site_jobspy_workers.py`**: The main JobSpy parallel processing implementation for all 4 sites.
- **`src/config/jobspy_integration_config.py`**: Configuration presets for different countries and job search strategies.
- **`src/pipeline/fast_job_pipeline.py`**: Shows how jobs are processed after being scraped.
- **`profiles/`**: Contains example user profiles. Useful for understanding the data structure of a profile.
