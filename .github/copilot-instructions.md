# JobLens AI Coding Agent Instructions

This document provides essential guidance for AI coding agents working on the JobLens codebase. Following these instructions will help you be more effective and align with the project's architecture and conventions.

## 1. Core Architecture & "Big Picture"

JobLens is a modern, profile-driven automated job discovery and analysis platform built with clean Python architecture. The system follows a layered microservices-like design with clear separation of concerns.

### Key Architectural Patterns

- **Profile-Centric Design**: Everything revolves around user profiles in `profiles/` directory. Each profile has its own DuckDB database and settings. `src/core/user_profile_manager.py` is the single source of truth for profile management.

- **Modern Database Architecture**: 
  - **Primary**: DuckDB for 10-100x faster analytics (`src/core/duckdb_database.py`)
  - **Legacy Support**: SQLite fallback via unified interface (`src/core/job_database.py`)
  - **Profile-Specific**: Each profile gets its own database instance

- **Orchestration Layer**: The `src/orchestration/` package provides centralized control:
  - `command_dispatcher.py` routes CLI commands to appropriate handlers
  - `jobspy_controller.py` manages job discovery operations
  - `processing_controller.py` handles batch job processing
  - Multiple orchestration services bridge dashboard and core functionality

- **Service-Oriented Structure**: Services in `src/services/` with dashboard bridges in `src/dashboard/services/`:
  - `OrchestrationService` - Real system orchestration with worker monitoring
  - `DataService`, `ConfigService`, `SystemService` - Dashboard data providers
  - `HealthMonitor` - System health and performance monitoring

- **Three-Layer Caching System**: Intelligent caching with 70% performance improvements:
  - HTML caching for scraping operations
  - Embedding caching for AI analysis
  - Result caching for processed jobs

### Data Flow & Component Integration

```
CLI (main.py) → Command Dispatcher → Orchestration Controllers → Services → Database
                                                                      ↓
Dashboard ← Dashboard Services ← Service Registry ← Core Services ← Processing Pipeline
```

1. **Job Discovery**: JobSpy integration with parallel workers for 4 sites (Indeed, LinkedIn, Glassdoor, ZipRecruiter)
2. **Processing Pipeline**: `src/pipeline/fast_job_pipeline.py` with two-stage processing and intelligent caching
3. **Analysis Engine**: AI-powered job-profile matching with skills gap analysis
4. **Dashboard Interface**: Modern Dash application with real-time monitoring and performance analytics

## 2. Critical Developer Workflows

**CRITICAL: Always work in the `auto_job` conda environment. The system will automatically attempt to relaunch under this environment if not detected.**

### Terminal & Environment Management

- **Environment Enforcement**: The system automatically checks for `auto_job` environment and attempts relaunch via `conda run -n auto_job`
- **VS Code Tasks**: Use `Ctrl+Shift+P` → "Tasks: Run Task" for standard operations
- **Available VS Code Tasks**:
  - `Run all tests (pytest)` - Execute full test suite with proper environment
  - `Start Dash Dashboard` - Launch Dash analytics interface
  - `Start Dashboard Backend` - FastAPI server (legacy, now integrated)
  - `Install Frontend Dependencies` - Dashboard dependency management

### Core CLI Commands & Workflows

**Main Entry Point**: `main.py` with strict profile-action pattern

```bash
# Modern JobSpy pipeline (primary workflow)
python main.py <ProfileName> --action jobspy-pipeline \
  --jobspy-preset canada_comprehensive \
  --database-type duckdb \
  --enable-cache

# Legacy scraping (fallback)
python main.py <ProfileName> --action scrape --keywords "python,data"

# Job analysis with caching
python main.py <ProfileName> --action analyze-jobs --enable-cache

# Dashboard with performance monitoring
python main.py <ProfileName> --action dashboard --enable-monitoring

# Health checks and system diagnostics
python main.py <ProfileName> --action health-check --show-cache-stats
```

### JobSpy Configuration Presets

- **Canada**: `canada_comprehensive`, `tech_hubs_canada`, `mississauga_focused`
- **USA**: `usa_comprehensive`, `usa_tech_hubs`, `usa_major_cities`
- **Remote**: `remote_focused` for distributed opportunities

### Testing Strategy

```bash
# Full test suite with coverage
pytest tests/ -v --cov=src --cov-report=html

# Category-specific testing
pytest tests/unit/ -v                    # Fast unit tests
pytest tests/integration/ -v             # Integration tests
pytest tests/dashboard/ -v               # Dashboard components
pytest tests/performance/ -v             # Performance benchmarks

# Real-world testing flags
pytest --real-scraping                   # Enable actual web scraping
pytest --skip-slow                       # Skip performance tests
```

## 3. Project-Specific Conventions & Patterns

### Profile Management Architecture

- **UserProfileManager** (`src/core/user_profile_manager.py`): Single source of truth for all profile operations
- **Profile Structure**: Each profile gets its own directory in `profiles/` with dedicated DuckDB database
- **Never** directly manipulate profile JSON files - always use UserProfileManager methods
- **Profile Data Class**: Uses modern `@dataclass` patterns with type safety

### Database Architecture & Performance

- **Primary Database**: DuckDB (`src/core/duckdb_database.py`) for 10-100x faster analytics
- **Unified Interface**: `src/core/job_database.py` provides abstraction layer
- **Database Factory**: `get_job_db(profile_name)` returns appropriate database instance
- **Caching System**: Three-layer intelligent caching (HTML, embeddings, results) with 70% performance gains

### Service Layer Patterns

- **Service Registry**: `src/dashboard/services/base_service.py` implements service discovery pattern
- **Bridge Services**: Dashboard services in `src/dashboard/services/` bridge to core services in `src/services/`
- **Health Monitoring**: `HealthMonitor` provides real-time system diagnostics
- **Worker Management**: `OrchestrationService` manages real worker processes and system resources

### Asynchronous Architecture

- **AsyncIO Patterns**: Extensive use in scraping (`src/scrapers/parallel_job_scraper.py`)
- **Worker Pools**: Multi-site parallel processing with configurable concurrency
- **Background Processing**: Two-stage job processing pipeline with intelligent batching
- **Task Management**: Real worker monitoring via `RealWorkerMonitorService`

### Configuration Management

- **Modern Config**: `src/config/modern_config_manager.py` with type-safe patterns
- **JobSpy Presets**: Pre-configured location and search strategies in `jobspy_integration_config.py`
- **Environment Variables**: `.env` support with fallback to sensible defaults
- **Profile Settings**: JSON-based configuration with validation

### Error Handling & Logging

- **Rich Console**: Used throughout for enhanced terminal output
- **Structured Logging**: Service-specific loggers with proper log rotation
- **AI Service Events**: Specialized logging for AI analysis operations (`ai_service_logger.py`)
- **Graceful Degradation**: System continues operation even with service failures

## 4. Key Files & Directories to Reference

### Core Architecture Files

- **`main.py`**: Primary CLI entry point with environment enforcement
- **`src/core/user_profile_manager.py`**: Profile management authority
- **`src/core/duckdb_database.py`**: High-performance database implementation
- **`src/orchestration/command_dispatcher.py`**: Command routing and dispatch logic

### Processing & Pipeline

- **`src/pipeline/fast_job_pipeline.py`**: Two-stage processing with caching
- **`src/scrapers/multi_site_jobspy_workers.py`**: Parallel JobSpy integration
- **`src/pipeline/jobspy_streaming_orchestrator.py`**: Streaming job discovery orchestration
- **`src/config/jobspy_integration_config.py`**: JobSpy presets and location strategies

### Service & Dashboard Architecture

- **`src/services/orchestration_service.py`**: Real system orchestration
- **`src/dashboard/services/`**: Dashboard service bridge layer
- **`src/dashboard/dash_app/`**: Modern Dash application with real-time monitoring
- **`src/services/real_worker_monitor_service.py`**: Worker process monitoring

### Testing & Quality

- **`tests/conftest.py`**: Comprehensive test configuration with real data fixtures
- **`tests/integration/`**: Integration tests following DEVELOPMENT_STANDARDS.md
- **`docs/DEVELOPMENT_STANDARDS.md`**: Code quality and architectural guidelines
- **`profiles/`**: Real user profiles for development and testing (never use fabricated data)

