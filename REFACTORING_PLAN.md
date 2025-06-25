# Refactoring Plan for Codebase Modularity

This document outlines the refactoring plan to improve the modularity of the codebase by ensuring no single file exceeds 500 lines.

## Files Exceeding 500 Lines

The following files have been identified as exceeding the 500-line limit and will be refactored:

1.  `src/agents/background_gmail_monitor.py` (618 lines)
2.  `src/agents/system_health_monitor.py` (572 lines)
3.  `src/ats/workday.py` (594 lines)
4.  `src/core/job_database.py` (770 lines)
5.  `src/core/utils.py` (606 lines)
6.  `src/dashboard/api.py` (2055 lines)
7.  `src/scrapers/big_data_patterns.py` (631 lines)
8.  `src/scrapers/modern_job_pipeline.py` (627 lines)
9.  `src/scrapers/parallel_job_scraper.py` (511 lines)
10. `src/utils/dynamic_gmail_verifier.py` (662 lines)
11. `src/utils/job_analysis_engine.py` (645 lines)
12. `src/utils/scraping_coordinator.py` (501 lines)

---

## Refactoring Details

### 1. `src/agents/background_gmail_monitor.py`

*   **Issue:** This file combines email monitoring, parsing, and database updates, making it large and complex.
*   **Refactoring Plan:**
    *   Create a new `src/email/gmail_client.py` to handle all Playwright interactions with Gmail (login, email fetching).
    *   Create a new `src/email/email_parser.py` to handle parsing of email content (extracting job title, company, etc.).
    *   The `background_gmail_monitor.py` will then coordinate the client and parser, and handle database interactions.

### 2. `src/agents/system_health_monitor.py`

*   **Issue:** This file contains numerous health checks for different system components.
*   **Refactoring Plan:**
    *   Create a `src/health_checks/` directory.
    *   Move each health check function (e.g., `_check_database_health`, `_check_disk_space`) into its own file within the new directory (e.g., `src/health_checks/database.py`, `src/health_checks/disk.py`).
    *   The `system_health_monitor.py` will dynamically load and run these checks.

### 3. `src/ats/workday.py`

*   **Issue:** The Workday submitter is very large due to the complexity of Workday forms.
*   **Refactoring Plan:**
    *   Create a `src/ats/workday_form_filler.py` to handle the dynamic form filling logic (`_dynamic_form_filling` and its helper methods).
    *   Create a `src/ats/workday_login.py` to handle the complex login logic.
    *   The main `workday.py` will orchestrate these components.

### 4. `src/core/job_database.py`

*   **Issue:** This file has grown to include not just database connection management but also a lot of specific query logic.
*   **Refactoring Plan:**
    *   Create a `src/core/db_queries.py` to house all the SQL queries and data retrieval logic (e.g., `get_jobs`, `get_job_stats`).
    *   The `job_database.py` will focus on connection management and basic CRUD operations.

### 5. `src/core/utils.py`

*   **Issue:** A "god object" utility file with a wide range of unrelated functions.
*   **Refactoring Plan:**
    *   Group related functions into more specific utility modules:
        *   `src/utils/file_operations.py` for `save_jobs_to_json`, `load_jobs_from_json`, `save_jobs_to_csv`, `backup_file`.
        *   `src/utils/job_helpers.py` for `extract_company_from_url`, `normalize_location`, `generate_job_hash`, `is_duplicate_job`, `sort_jobs`.
        *   `src/utils/profile_helpers.py` for `get_available_profiles`, `load_profile`, `ensure_profile_files`.

### 6. `src/dashboard/api.py`

*   **Issue:** This is a massive file containing the entire FastAPI application, including all routes, helper functions, and WebSocket logic.
*   **Refactoring Plan:**
    *   Create a `src/dashboard/routers/` directory.
    *   Split the API routes into multiple files based on functionality (e.g., `src/dashboard/routers/jobs.py`, `src/dashboard/routers/stats.py`, `src/dashboard/routers/system.py`).
    *   Create a `src/dashboard/websocket.py` for the WebSocket logic.
    *   The main `api.py` will be much smaller, responsible for creating the FastAPI app and including the routers.

### 7. `src/scrapers/big_data_patterns.py`

*   **Issue:** This file implements several complex data processing patterns.
*   **Refactoring Plan:**
    *   Create a `src/processing/` directory.
    *   Move each major pattern into its own module:
        *   `src/processing/stream_processor.py`
        *   `src/processing/batch_processor.py`
        *   `src/processing/map_reduce.py`
        *   `src/processing/pipeline.py`
    *   Common data classes like `DataChunk` can go into `src/processing/models.py`.

### 8. `src/scrapers/modern_job_pipeline.py`

*   **Issue:** This file defines a complex pipeline with many stages.
*   **Refactoring Plan:**
    *   Create a `src/pipeline/` directory.
    *   Move each pipeline stage (`_scraping_stage`, `_processing_stage`, etc.) into its own module within `src/pipeline/stages/`.
    *   The main `modern_job_pipeline.py` will define the pipeline structure and orchestrate the stages.

### 9. `src/scrapers/parallel_job_scraper.py`

*   **Issue:** This file contains the logic for parallel scraping, including worker implementation.
*   **Refactoring Plan:**
    *   Create a `src/scraping_workers/` directory.
    *   Move the worker logic (`_basic_scraping_worker`, `_detail_scraping_worker`) into separate files in the new directory.
    *   The `parallel_job_scraper.py` will focus on creating and managing the worker pool.

### 10. `src/utils/dynamic_gmail_verifier.py`

*   **Issue:** Similar to the background monitor, this file combines client interaction, parsing, and interactive verification.
*   **Refactoring Plan:**
    *   Reuse the `src/email/gmail_client.py` and `src/email/email_parser.py` created for the background monitor.
    *   Create a `src/verification/interactive_verifier.py` to handle the user interaction (prompts, tables).
    *   The `dynamic_gmail_verifier.py` will coordinate these components.

### 11. `src/utils/job_analysis_engine.py`

*   **Issue:** This engine combines profile intelligence, keyword generation, and scraping orchestration.
*   **Refactoring Plan:**
    *   Create a `src/analysis/keyword_generator.py` for `get_intelligent_keywords`.
    *   Create a `src/analysis/resume_analyzer.py` to handle resume parsing and analysis (this file already exists but can be enhanced).
    *   The `job_analysis_engine.py` will focus on orchestrating the analysis and scraping process.

### 12. `src/utils/scraping_coordinator.py`

*   **Issue:** This file manages scraping coordination, caching, and metrics.
*   **Refactoring Plan:**
    *   Create a `src/scraping/cache.py` to manage the scraping cache logic.
    *   Create a `src/scraping/metrics.py` to handle metrics collection and reporting.
    *   The `scraping_coordinator.py` will focus on the core coordination logic.