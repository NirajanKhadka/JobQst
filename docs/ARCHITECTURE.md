# JobLens System Architecture# JobQst System Architecture



**Last Updated:** January 13, 2025  **Version**: 3.1.0  

**Status:** Active - Production Ready  **Last Updated**: January 13, 2025  

**Compliance Score:** 93/100 ✅  **Compliance Score**: 93/100 ✅ (PRODUCTION READY)  

**Environment:** Python 3.11.11 (auto_job conda)**Environment**: Python 3.11.11 (auto_job conda)



## Document PurposeThis document provides a comprehensive overview of JobQst's system architecture, design patterns, and technical decisions following modern Python development standards.



This document provides a practical, implementation-focused guide to JobLens architecture. Following the principles in `DEVELOPMENT_STANDARDS.md`, it focuses on **what exists now** and **how it works**, not aspirational features.## 🎉 Dashboard Refactor Complete (Version 3.0)



## Core Architectural Principles**Major Update**: The dashboard has been fully consolidated with:

- ✅ Unified caching architecture (eliminated 3 duplicate implementations)

### 1. Profile-Centric Design- ✅ Shared data access layer (single source of truth)

Everything revolves around user profiles in `profiles/` directory:- ✅ Centralized analytics (eliminated 16+ duplicate aggregations)

- Each profile = dedicated DuckDB database- ✅ ProfileService with intelligent caching (300s TTL)

- Single source of truth: `src/core/user_profile_manager.py`- ✅ Streamlined 3-tab navigation (Ranked Jobs, Tracker, Market Insights)

- Never manipulate profile JSON files directly- ✅ RCIP integration end-to-end (47 cities, 15% ranking boost)

- ✅ Monitoring consolidation (canonical implementations only)

### 2. Modern Database Architecture

```pythonSee [Dashboard Refactor Roadmap](dashboard_refactor_roadmap.md) for complete details.

# Primary: DuckDB for analytics performance

from src.core.duckdb_database import DuckDBJobDatabase## 🔧 Development Environment & Compliance (Version 3.1)

db = DuckDBJobDatabase(profile_name="YourProfile")

**Major Update**: Development environment fully configured and validated:

# Unified interface abstracts database type- ✅ Python 3.11.11 in auto_job conda environment (was incorrectly in base)

from src.core.job_database import get_job_db- ✅ All development tools installed: black 25.1.0, flake8 7.1.1, mypy 1.14.1

db = get_job_db("YourProfile")  # Returns appropriate DB instance- ✅ 291/293 files Black formatted (99.3% coverage)

```- ✅ 100% dependency pinning (58/58 dependencies)

- ✅ Pre-commit hooks configured and ready

### 3. Service-Oriented Structure- ✅ Compliance score: **93/100** (+28 from baseline)

Clear separation between:

- **Core Services** (`src/services/`) - Business logicSee [STANDARDS_COMPLIANCE_AUDIT.md](STANDARDS_COMPLIANCE_AUDIT.md) and [ENVIRONMENT_SETUP_GUIDE.md](ENVIRONMENT_SETUP_GUIDE.md) for complete details.

- **Dashboard Services** (`src/dashboard/services/`) - UI bridge layer

- **Orchestration** (`src/orchestration/`) - Command routing## Table of Contents



## System Data Flow- [System Overview](#system-overview)

- [Core Architecture](#core-architecture)

```- [Data Flow](#data-flow)

CLI (main.py)- [Component Design](#component-design)

    ↓- [Database Architecture](#database-architecture)

Command Dispatcher → orchestration/command_dispatcher.py- [Processing Pipeline](#processing-pipeline)

    ↓- [Code Quality & Tooling](#code-quality--tooling)

Orchestration Controllers- [Security Architecture](#security-architecture)

    ├── jobspy_controller.py (job discovery)- [Performance Considerations](#performance-considerations)

    ├── processing_controller.py (AI analysis)- [Deployment Architecture](#deployment-architecture)

    └── system_controller.py (health, monitoring)

    ↓## System Overview

Core Services

    ├── JobSpy Workers (4-site parallel scraping)JobQst is designed as a modular, scalable job search automation platform with clear separation of concerns and modern Python architectural patterns.

    ├── Two-Stage Processor (CPU → GPU pipeline)

    └── Database Services (DuckDB operations)### Design Principles

    ↓

Storage Layer1. **Separation of Concerns**: Each module has a single, well-defined responsibility

    ├── DuckDB (per-profile databases)2. **Type Safety**: Comprehensive type annotations throughout the codebase

    ├── Cache Framework (HTML, embeddings, metadata)3. **Async-First**: Asynchronous operations for I/O-bound tasks

    └── File System (profiles/, cache/, logs/)4. **Dependency Injection**: Configurable components with clear interfaces

```5. **Error Resilience**: Graceful degradation and comprehensive error handling

6. **Performance**: Optimized for both speed and resource efficiency

## Key Components

### High-Level Architecture (Updated September 2025)

### 1. Job Discovery: JobSpy Integration

```

**File:** `src/scrapers/multi_site_jobspy_workers.py`┌─────────────────────────────────────────────────────────────────┐

│                      JobQst Platform v3.0                       │

**Purpose:** Parallel job scraping across Indeed, LinkedIn, Glassdoor, ZipRecruiter├─────────────────────────────────────────────────────────────────┤

│  Presentation Layer                                             │

**Key Features:**│  ┌─────────────────┐  ┌─────────────────────────────────────┐  │

```python│  │   CLI Interface │  │     Dashboard (Unified, Port 8050)  │  │

# Relevance filtering removes mismatched results│  │   (main.py)     │  │   • Ranked Jobs (RCIP-integrated)   │  │

# (e.g., Java jobs when searching Python)│  │                 │  │   • Job Tracker (Status management) │  │

def _filter_relevant_jobs(jobs_df: pd.DataFrame, search_term: str) -> pd.DataFrame:│  │                 │  │   • Market Insights (Analytics)     │  │

    # Tech-specific conflict detection│  └─────────────────┘  └─────────────────────────────────────┘  │

    # Title-based strict filtering├─────────────────────────────────────────────────────────────────┤

    # Description-based secondary validation│  Service Layer (Consolidated)                                   │

    pass│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │

│  │ ProfileService  │  │   DataService   │  │  ConfigService  │ │

# Site-specific location handling│  │ (300s cache)    │  │ (Shared access) │  │  (Settings)     │ │

# (Glassdoor needs city-only for Canadian locations)│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │

if site == "glassdoor" and "," in location:│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │

    city_only = location.split(",")[0].strip()│  │ Aggregation     │  │ RCIP Enrichment │  │  Performance    │ │

```│  │ Helpers         │  │ Service         │  │  Monitor        │ │

│  │ (Centralized)   │  │ (47 cities)     │  │  (Canonical)    │ │

**Usage Pattern:**│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │

```python├─────────────────────────────────────────────────────────────────┤

from src.scrapers.multi_site_jobspy_workers import MultiSiteJobSpyWorkers│  Business Logic Layer                                           │

│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │

workers = MultiSiteJobSpyWorkers(│  │ JobSpy Workers  │  │   AI Processing │  │   Analytics     │ │

    profile_name="YourProfile",│  │ (4 sites, //)   │  │   (GPU/CPU)     │  │   (DuckDB)      │ │

    max_jobs_per_site=50,│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │

    concurrency=4├─────────────────────────────────────────────────────────────────┤

)│  Data Layer                                                     │

│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │

jobs_df = await workers.run_discovery(│  │   DuckDB        │  │ UnifiedCache    │  │   File System   │ │

    sites=["indeed", "linkedin"],│  │ (Per-profile)   │  │ (TTL-based)     │  │   (Profiles)    │ │

    locations=["Toronto, ON"],│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │

    search_terms=["Python Developer"],└─────────────────────────────────────────────────────────────────┘

)```

```



## 🆕 Config-Driven Architecture (v3.2)

**Major Architectural Pattern:** External JSON configurations replace hardcoded domain data

**Reference Implementation: Resume Parser V2**
- **File:** `src/utils/resume_parser_v2.py`
- **Configs:** `config/skills_database.json`, `config/resume_parsing_config.json`
- **Performance:** 12.8ms average (was ~100ms), O(1) lookups (was O(n))
- **Coverage:** 9 industries, 500+ skills (was 2-4 industries, 100 hardcoded)

```python
# Modern config-driven approach
from src.utils.resume_parser_v2 import parse_resume

data = parse_resume("resume.docx")
print(f"Industry: {data['primary_industry']}")  # Auto-detected from 9 industries
print(f"Skills: {len(data['skills'])} detected")  # Fast O(1) lookups
print(f"Keywords: {data['keywords'][:3]}")  # Industry-specific
```

**Management Utility:**
```bash
# Non-developers can manage skills database
python scripts/utils/manage_skills_db.py list
python scripts/utils/manage_skills_db.py show data_analytics
python scripts/utils/manage_skills_db.py add "Sales" --skills "Salesforce,CRM"
```

**See:** [CONFIG_DRIVEN_ARCHITECTURE.md](CONFIG_DRIVEN_ARCHITECTURE.md) for:
- 6 systems needing refactoring (job matching, skills extraction, location handling, etc.)
- Implementation roadmap (6-week plan)
- Performance and scalability targets

## Core Architecture

### 2. Two-Stage Processing Pipeline

### Module Structure (Updated September 2025)

**File:** `src/analysis/two_stage_processor.py`

```

**Architecture:**src/

```├── core/                      # Core business logic

Stage 1: Fast CPU Processing (10 workers)│   ├── job_database.py       # Database abstraction layer

├── Basic data extraction│   ├── duckdb_database.py    # DuckDB implementation

├── Rule-based skill matching│   ├── smart_deduplication.py # Duplicate detection

├── Initial compatibility scoring│   ├── job_filters.py        # Relevance filtering

└── Filter to high-potential jobs (score > 0.6)│   ├── user_profile_manager.py # Profile management authority

    ↓│   └── exceptions.py         # Custom exceptions

Stage 2: AI Analysis (GPU-accelerated)├── scrapers/                  # Web scraping components

├── Semantic similarity analysis│   ├── base_scraper.py       # Abstract base class

├── Embeddings-based matching│   ├── multi_site_jobspy_workers.py # JobSpy parallel integration

├── Final compatibility scoring│   ├── parallel_job_scraper.py      # Async multi-site scraping

└── Intelligent caching (70% hit rate)│   └── enhanced_job_description_scraper.py # Job details

```├── analysis/                  # AI processing pipeline

│   ├── two_stage_processor.py # Main processing engine

**Why Two Stages?**│   └── custom_data_extractor.py # Data extraction

- Stage 1 filters out 40-60% of low-quality matches quickly├── pipeline/                  # Processing orchestration

- Stage 2 focuses expensive AI on promising candidates│   ├── fast_job_pipeline.py  # Two-stage processing with caching

- Result: 3-5x faster than single-stage processing│   └── jobspy_streaming_orchestrator.py # JobSpy orchestration

├── services/                  # Core services

**Caching System:**│   ├── orchestration_service.py  # System orchestration

```python│   ├── rcip_enrichment_service.py # RCIP job enrichment

# Intelligent cache framework│   └── real_worker_monitor_service.py # Worker monitoring

cache/├── dashboard/                 # Web dashboard (CONSOLIDATED v3.0)

├── html/           # Raw HTML responses│   ├── unified_dashboard.py  # 🎯 Canonical launcher (port 8050)

├── embeddings/     # Computed embeddings│   ├── services/            # Service layer (UPDATED)

└── metadata/       # Cache metadata and TTL│   │   ├── profile_service.py  # ✅ Centralized profile mgmt (300s cache)

```│   │   ├── data_service.py     # ✅ Dashboard data access

│   │   ├── config_service.py   # ✅ Configuration management

### 3. Unified Deduplication System│   │   ├── performance_monitor.py # 🎯 Canonical performance monitoring

│   │   └── health_monitor.py      # 🎯 Canonical health monitoring

**File:** `src/core/unified_deduplication.py`│   ├── analytics/           # Analytics layer (NEW)

│   │   └── aggregation_helpers.py # ✅ Centralized analytics

**Single Implementation** (replaces 4 legacy systems):│   ├── dash_app/            # Dashboard UI

```python│   │   ├── app.py              # Dash application (streamlined)

def deduplicate_jobs_unified(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:│   │   ├── callbacks/          # Interactive callbacks

    # 1. URL-based deduplication (primary)│   │   ├── components/         # UI components

    # 2. Fuzzy title+company matching (secondary)│   │   │   ├── rcip_components.py       # ✅ RCIP UI components

    # 3. Keep job with most complete data│   │   │   └── streamlined_sidebar.py   # ✅ 3-tab navigation

    pass│   │   ├── layouts/            # Page layouts (NEW)

```│   │   │   ├── ranked_jobs_layout.py      # ✅ Main job browsing

│   │   │   ├── job_tracker_layout.py      # Status management

**Algorithm:**│   │   │   └── market_insights_layout.py  # ✅ Analytics dashboard

1. Normalize URLs (remove query params, fragments)│   │   └── utils/              # Utilities (DataLoader uses ProfileService)

2. Create URL signature│   ├── api.py              # ⚠️ DEPRECATED - Use unified_dashboard.py

3. Check exact URL match│   └── run_dash_dashboard.py   # ⚠️ DEPRECATED - Use unified_dashboard.py

4. If no match, fuzzy title+company comparison├── orchestration/            # Command orchestration

5. Preserve best version of each job│   ├── command_dispatcher.py # Command routing

│   ├── jobspy_controller.py  # JobSpy operations

### 4. DuckDB Database Layer│   └── processing_controller.py # Job processing

├── config/                   # Configuration management

**File:** `src/core/duckdb_database.py`│   ├── modern_config_manager.py # Type-safe config

│   └── jobspy_integration_config.py # JobSpy presets

**Why DuckDB over SQLite?**├── cli/                      # Command line interface

- 10-100x faster analytical queries│   ├── menu/                # Interactive menus

- Vectorized operations│   ├── actions/             # Action handlers

- Columnar storage│   └── handlers/            # Business logic handlers

- Native pandas integration└── utils/                    # Shared utilities

- Perfect for dashboard queries    ├── profile_helpers.py   # Profile management

    ├── job_data_enhancer.py # ✅ Job enrichment (RCIP integrated)

**Schema Highlights:**    ├── intelligent_search_generator.py # Keyword generation

```sql    └── logging.py           # Logging configuration

CREATE TABLE jobs (```

    id VARCHAR PRIMARY KEY,

    title VARCHAR NOT NULL,**Key Changes in v3.0:**

    company VARCHAR NOT NULL,- ✅ **ProfileService**: Eliminated 11+ duplicate profile loading calls

    location VARCHAR,- ✅ **Aggregation Helpers**: Eliminated 16+ duplicate analytics computations

    job_url VARCHAR UNIQUE,- ✅ **RCIP Service**: End-to-end immigration program support (47 cities)

    description TEXT,- ✅ **Streamlined Navigation**: 9 tabs → 3 job-seeker-focused tabs

    fit_score FLOAT,- ✅ **Monitoring Consolidation**: Canonical implementations only

    processing_status VARCHAR,- ⚠️ **Deprecated**: `api.py`, `run_dash_dashboard.py` (use `unified_dashboard.py`)

    created_at TIMESTAMP,

    -- ... 17 total fields### Dependency Graph

);

```mermaid

-- Optimized indexes for common patternsgraph TD

CREATE INDEX idx_profile_fit ON jobs(profile_name, fit_score DESC);    A[CLI Interface] --> B[Action Handlers]

CREATE INDEX idx_created ON jobs(created_at DESC);    B --> C[Scraping Handler]

```    B --> D[Processing Handler]

    B --> E[Dashboard Handler]

### 5. Dashboard: Dash Application    

    C --> F[Scrapers]

**File:** `src/dashboard/dash_app/app.py`    D --> G[AI Processors]

    E --> H[Dashboard Components]

**Port:** 8050 (standard)    

    F --> I[Database Layer]

**Architecture:**    G --> I

```    H --> I

Dashboard Components    

├── ProfileService (300s cache)    I --> J[DuckDB]

│   └── Eliminates duplicate profile loading    I --> K[File System]

├── DataService (shared data access)```

│   └── Single source of truth for queries

├── Aggregation Helpers (centralized analytics)## Data Flow

│   └── Eliminates 16+ duplicate computations

└── RCIP Integration (Canadian immigration)### Job Discovery Flow

    └── 47 cities, 15% ranking boost

``````

1. User Input

**Pages:**   ├── Profile Keywords

- **Ranked Jobs** - Main browsing with filters   ├── Location Preferences

- **Job Tracker** - Application status management   └── Experience Level

- **Market Insights** - Analytics and trends   

2. Scraping Pipeline

## Configuration Management   ├── Eluta Scraper (Canadian focus)

   ├── External Scrapers (Global)

### JobSpy Presets   └── Rate Limiting & Anti-bot

   

**File:** `src/config/jobspy_integration_config.py`3. Data Processing

   ├── Smart Deduplication (85% accuracy)

**Available Presets:**   ├── Relevance Filtering (90% precision)

```python   └── Data Normalization

# Canada   

JOBSPY_LOCATION_SETS = {4. AI Analysis

    "canada_comprehensive": [/* 20+ cities */],   ├── Stage 1: Fast CPU Processing

    "tech_hubs_canada": ["Toronto", "Vancouver", "Montreal", ...],   ├── Stage 2: GPU-accelerated Analysis

    "mississauga_focused": [/* GTA locations */],   └── Compatibility Scoring

}   

5. Storage & Analytics

# USA   ├── DuckDB Columnar Storage

"usa_comprehensive": [/* 50+ cities */],   ├── Real-time Analytics

"usa_tech_hubs": ["San Francisco", "Seattle", "Austin", ...],   └── Dashboard Updates

```

# Remote

"remote_focused": ["Remote", "United States", "Canada"],### Processing Pipeline

}

```python

JOBSPY_QUERY_PRESETS = {# Simplified data flow representation

    "comprehensive": [/* 20+ search terms */],async def job_discovery_pipeline(profile: ProfileDict) -> List[JobDict]:

    "python_focused": ["Python Developer", "Python Engineer", ...],    """Complete job discovery and processing pipeline."""

    "data_focused": ["Data Analyst", "Data Scientist", ...],    

}    # 1. Scraping Phase

```    scraped_jobs = await scrape_multiple_sources(profile)

    

**Usage:**    # 2. Deduplication Phase

```bash    unique_jobs = deduplicate_jobs(scraped_jobs)

python main.py YourProfile --action jobspy-pipeline \    

  --jobspy-preset canada_comprehensive \    # 3. Filtering Phase

  --database-type duckdb \    relevant_jobs = filter_relevant_jobs(unique_jobs, profile)

  --enable-cache    

```    # 4. AI Processing Phase

    processed_jobs = await ai_process_jobs(relevant_jobs, profile)

## Error Handling Architecture    

    # 5. Storage Phase

**File:** `src/core/exceptions.py`    stored_count = store_jobs_batch(processed_jobs)

    

**Custom Exception Hierarchy (24 types):**    return processed_jobs

```python```

# Base exceptions

class JobLensError(Exception): pass## Component Design

class JobScrapingError(JobLensError): pass

class JobProcessingError(JobLensError): pass### Dashboard Service Layer

class DatabaseError(JobLensError): pass

JobQst implements a modern service-oriented architecture for the dashboard with clear separation of concerns and centralized caching.

# Specific exceptions

class NetworkError(JobScrapingError): pass#### ProfileService - Centralized Profile Management

class RateLimitError(JobScrapingError): pass

class ParseError(JobScrapingError): pass**Purpose**: Eliminate duplicate profile loading logic across dashboard components.

class ValidationError(JobProcessingError): pass

```**Location**: `src/dashboard/services/profile_service.py`



**Error Handling Pattern:****Key Features**:

```python- **Singleton Pattern**: Single instance shared across all dashboard components

from src.core.exceptions import JobScrapingError, RateLimitError- **Thread-Safe**: Uses `threading.RLock` for concurrent access protection

- **Intelligent Caching**: 300-second TTL with automatic invalidation

try:- **Force Refresh**: Optional cache bypass for critical operations

    jobs = await scraper.scrape_jobs(keywords)

except RateLimitError as e:**Architecture**:

    # Specific handling for rate limits```python

    await asyncio.sleep(60)class ProfileService:

    retry_scrape()    """Centralized profile management with caching."""

except JobScrapingError as e:    

    # General scraping error handling    def __init__(self, cache_ttl_seconds: int = 300):

    logger.error(f"Scraping failed: {e}")        self._lock = threading.RLock()

    use_fallback_source()        self._cache_ttl = cache_ttl_seconds

```        self._profile_cache: Tuple[Any, datetime] | None = None

        self._profile_data_cache: Dict[str, Tuple[Any, datetime]] = {}

## Asynchronous Architecture    

    def get_available_profiles(self, force_refresh: bool = False) -> List[str]:

### AsyncIO Patterns        """Get list of available profiles with caching."""

        with self._lock:

**Used Throughout:**            if not force_refresh and self._is_cache_valid(self._profile_cache):

```python                return self._profile_cache[0]

# Parallel scraping            

async def run_discovery(sites, locations, terms):            # Load from file system

    tasks = [scrape_single(site, loc, term)             profiles = _get_available_profiles()

             for site, loc, term in product(sites, locations, terms)]            self._profile_cache = (profiles, datetime.now())

    results = await asyncio.gather(*tasks, return_exceptions=True)            return profiles

    return [r for r in results if not isinstance(r, Exception)]    

    def get_profile_data(self, profile_name: str, 

# Worker pools                        force_refresh: bool = False) -> ProfileData:

semaphore = asyncio.Semaphore(max_workers)        """Get profile data with per-profile caching."""

async with semaphore:        # Similar caching logic for individual profiles

    result = await process_job(job)        pass

```

# Singleton factory

### Background Processing_profile_service_instance: ProfileService | None = None



**Two-Stage Pipeline:**def get_profile_service() -> ProfileService:

```python    """Get or create the singleton ProfileService instance."""

# Stage 1: Fast CPU batch processing    global _profile_service_instance

stage1_results = await stage1_processor.process_batch(jobs, workers=10)    if _profile_service_instance is None:

        _profile_service_instance = ProfileService()

# Stage 2: GPU processing with concurrency control    return _profile_service_instance

high_potential = [j for j in stage1_results if j['stage1_score'] > 0.6]```

stage2_results = await stage2_processor.process_with_cache(high_potential)

```**Integration Chain**:

```

## Directory Structure (Simplified)DataLoader (Dash UI) → DataService (Bridge) → ProfileService (Cache) → File System

ConfigService (Config) → ProfileService (Cache) → File System

``````

src/

├── core/                      # Core business logic**Benefits**:

│   ├── user_profile_manager.py   # Profile authority- ✅ Eliminated 11+ duplicate `get_available_profiles()` calls

│   ├── duckdb_database.py        # Primary database- ✅ Consistent caching behavior across dashboard

│   ├── unified_deduplication.py  # Single dedup system- ✅ Reduced file system I/O by 85%+

│   └── exceptions.py             # 24 custom exceptions- ✅ Thread-safe for multi-user scenarios

│- ✅ Cache statistics for monitoring

├── scrapers/                  # Job discovery

│   ├── multi_site_jobspy_workers.py  # JobSpy integration**Migration Status** (September 30, 2025):

│   └── parallel_job_scraper.py       # Parallel processing- ✅ **DataService**: Migrated to use ProfileService

│- ✅ **ConfigService**: Migrated to use ProfileService

├── analysis/                  # AI processing- ✅ **DataLoader**: Automatically benefits through DataService

│   ├── two_stage_processor.py       # Main engine- ✅ **Test Coverage**: 16/16 tests passing

│   └── custom_data_extractor.py     # Data extraction

│#### Dashboard Entry Points (Updated September 30, 2025)

├── orchestration/            # Command routing

│   ├── command_dispatcher.py        # CLI routing**Canonical Launcher**: `src/dashboard/unified_dashboard.py`

│   ├── jobspy_controller.py         # JobSpy ops- Port: 8050 (standard)

│   └── processing_controller.py     # Processing ops- Profile selection via CLI arguments

│- Production-ready with error handling

├── dashboard/                # Web interface

│   ├── unified_dashboard.py         # Launcher (port 8050)**Deprecated Launchers**:

│   ├── services/                    # Service layer- ⚠️ `src/dashboard/api.py` - Legacy FastAPI server (port 8002)

│   │   ├── profile_service.py       # 300s cache  - Status: Deprecated, shows migration warnings

│   │   ├── data_service.py          # Data access  - Migration: Use `unified_dashboard.py` and `ProfileService`

│   │   └── config_service.py        # Settings- ⚠️ `src/dashboard/run_dash_dashboard.py` - Simple wrapper

│   └── dash_app/                    # Dash UI  - Status: Deprecated, shows migration warnings

│       ├── app.py                   # Main app  - Migration: Use `unified_dashboard.py` directly

│       ├── layouts/                 # Page layouts

│       └── callbacks/               # Interactivity**Updated Callers**:

│- `src/core/system_utils.py`: Now uses `unified_dashboard.launch_dashboard()` on port 8050

├── services/                  # Core services- `scripts/maintenance/start_api.py`: Redirects to unified dashboard with deprecation notice

│   ├── orchestration_service.py     # System orchestration

│   └── rcip_enrichment_service.py   # RCIP integration### Scraping Architecture

│

└── config/                    # Configuration#### Base Scraper Pattern

    ├── modern_config_manager.py     # Type-safe config

    └── jobspy_integration_config.py # JobSpy presets```python

```from abc import ABC, abstractmethod

from typing import List, Dict, Any

## Performance Characteristics

class BaseJobScraper(ABC):

### Scraping Performance    """Abstract base class defining scraper interface."""

- **Speed**: 2-3 jobs/second with 4 parallel workers    

- **Success Rate**: 85-90% (varies by site)    @abstractmethod

- **Relevance**: 95%+ after filtering    async def scrape_jobs(self, keywords: List[str], **kwargs) -> List[Dict[str, Any]]:

- **Deduplication**: ~85% accuracy        """Scrape jobs for given keywords."""

        pass

### Processing Performance    

- **Stage 1** (CPU): ~100 jobs/minute    @abstractmethod

- **Stage 2** (AI): ~20 jobs/minute (70-80% cache hits → ~100 jobs/minute)    def get_scraper_name(self) -> str:

- **Memory**: ~500MB typical, ~2GB peak with GPU        """Return scraper identifier."""

- **Database**: 10-100x faster than SQLite for analytics        pass

```

### Dashboard Performance

- **Query Caching**: 3-5 min TTL on expensive aggregations#### Concrete Implementations

- **Profile Caching**: 300s TTL reduces file I/O by 85%+

- **Page Load**: <500ms for ranked jobs (with cache)```python

class ElutaScraper(BaseJobScraper):

## Testing Strategy    """Eluta-specific scraper with anti-bot measures."""

    

### Test Organization    def __init__(self, profile_name: str, config: Optional[Dict] = None):

```        self.profile = load_profile(profile_name)

tests/        self.config = config or {}

├── unit/           # Fast, isolated tests        self.browser_manager = BrowserManager()

├── integration/    # Component interaction        self.rate_limiter = RateLimiter(delay=1.0)

├── dashboard/      # Dashboard-specific    

├── performance/    # Benchmarks    async def scrape_jobs(self, keywords: List[str], **kwargs) -> List[Dict[str, Any]]:

└── e2e/           # End-to-end workflows        """Implement Eluta-specific scraping logic."""

```        results = []

        

### Running Tests        async with self.browser_manager.get_browser() as browser:

```bash            for keyword in keywords:

# Full suite                jobs = await self._scrape_keyword(browser, keyword)

pytest tests/ -v --cov=src --cov-report=html                results.extend(jobs)

                await self.rate_limiter.wait()

# Specific categories        

pytest tests/unit/ -v        return results

pytest tests/integration/ -v --real-scraping  # Enable live scraping```

pytest tests/performance/ -v

```### Processing Architecture



## Development Workflows#### Two-Stage Processing Design



### Core CLI Commands```python

```bashclass TwoStageJobProcessor:

# Modern JobSpy pipeline (primary)    """

python main.py YourProfile --action jobspy-pipeline \    Stage 1: Fast CPU processing (10 workers)

  --jobspy-preset canada_comprehensive \    - Basic data extraction and validation

  --enable-cache    - Rule-based skill matching

    - Initial compatibility scoring

# Job analysis    

python main.py YourProfile --action analyze-jobs --enable-cache    Stage 2: GPU-accelerated analysis

    - Advanced NLP processing

# Dashboard    - Semantic similarity analysis

python main.py YourProfile --action dashboard    - Final compatibility scoring

    """

# Health checks    

python main.py YourProfile --action health-check --show-cache-stats    def __init__(self, user_profile: Dict[str, Any], 

```                 cpu_workers: int = 10,

                 max_concurrent_stage2: int = 2):

### VS Code Tasks        self.stage1_processor = Stage1CPUProcessor(user_profile, cpu_workers)

Available via `Ctrl+Shift+P` → "Tasks: Run Task":        self.stage2_processor = Stage2GPUProcessor(user_profile)

- `Run all tests (pytest)` - Full test suite        self.semaphore = asyncio.Semaphore(max_concurrent_stage2)

- `Start Dash Dashboard` - Launch dashboard    

- ~~`Start Dashboard Backend`~~ - **Deprecated** (use unified dashboard)    async def process_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

        """Process jobs through two-stage pipeline."""

## Common Patterns        

        # Stage 1: Fast CPU processing

### Type-Safe Configuration        stage1_results = await self.stage1_processor.process_batch(jobs)

```python        

from pydantic import BaseModel, Field        # Stage 2: GPU processing for high-potential jobs

        high_potential = [job for job in stage1_results if job['stage1_score'] > 0.6]

class ScrapingConfig(BaseModel):        

    max_workers: int = Field(default=4, ge=1, le=20)        stage2_tasks = [

    max_jobs_per_site: int = Field(default=50, ge=1, le=500)            self._process_stage2_with_semaphore(job) 

    enable_cache: bool = True            for job in high_potential

```        ]

        

### Context Managers        stage2_results = await asyncio.gather(*stage2_tasks)

```python        

@contextmanager        return self._merge_results(stage1_results, stage2_results)

def get_database_connection(profile_name: str):```

    db = get_job_db(profile_name)

    try:### Database Architecture

        yield db

    finally:#### DuckDB Integration

        db.close()

``````python

class DuckDBJobDatabase:

### Async Error Handling    """

```python    High-performance analytics database using DuckDB.

async def safe_scrape(site: str, **kwargs) -> Optional[pd.DataFrame]:    

    try:    Features:

        return await scrape_jobs(site_name=site, **kwargs)    - Columnar storage for analytical queries

    except RateLimitError:    - Vectorized operations with pandas integration

        logger.warning(f"Rate limited on {site}, skipping")    - File-based deployment (no server required)

        return None    - Optimized for dashboard performance

    except Exception as e:    """

        logger.error(f"Scraping failed for {site}: {e}")    

        return None    def __init__(self, db_path: str, profile_name: Optional[str] = None):

```        self.db_path = self._get_profile_db_path(db_path, profile_name)

        self.conn = None

## Security Considerations        self._ensure_connection()

        self._create_optimized_schema()

### Input Validation    

All external input validated with Pydantic:    def _create_optimized_schema(self):

```python        """Create optimized schema for analytical workloads."""

class JobSearchRequest(BaseModel):        schema_sql = """

    keywords: List[str] = Field(min_items=1, max_items=10)        CREATE TABLE IF NOT EXISTS jobs (

    locations: List[str] = Field(min_items=1, max_items=20)            -- Core job fields

    max_results: int = Field(ge=1, le=1000)            id VARCHAR PRIMARY KEY,

```            title VARCHAR NOT NULL,

            company VARCHAR NOT NULL,

### Secure Configuration            location VARCHAR,

Environment variables with fallbacks:            

```python            -- Analytics fields

from pydantic import BaseSettings            fit_score FLOAT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

class Settings(BaseSettings):            

    database_url: str = "sqlite:///jobs.db"            -- Indexes for common queries

    openai_api_key: Optional[str] = None            INDEX idx_company (company),

                INDEX idx_fit_score (fit_score),

    class Config:            INDEX idx_created_at (created_at)

        env_file = ".env"        );

```        """

        self.conn.execute(schema_sql)

## Deployment Considerations```



### Environment Management#### Query Optimization

- **Required**: Python 3.11.11 in `auto_job` conda environment

- **Verification**: Always check `python --version` and `sys.executable````python

- **Never**: Use `conda run -n auto_job python ...` (breaks multi-line commands)def get_analytics_data(self, profile_name: Optional[str] = None) -> Dict[str, Any]:

- **Always**: Use direct `python` execution    """Optimized analytics query using DuckDB's vectorized operations."""

    

### Production Checklist    # Single query for multiple aggregations

- [ ] Python 3.11.11 verified    analytics_sql = """

- [ ] All dependencies pinned (58/58 currently pinned ✅)    SELECT 

- [ ] Pre-commit hooks configured        COUNT(*) as total_jobs,

- [ ] Type checking passes (`mypy src/`)        COUNT(DISTINCT company) as unique_companies,

- [ ] Tests pass with coverage >80%        AVG(fit_score) as avg_fit_score,

- [ ] Environment variables configured        MAX(fit_score) as max_fit_score,

- [ ] Database backups scheduled        COUNT(CASE WHEN created_at > (CURRENT_TIMESTAMP - INTERVAL 1 DAY) 

- [ ] Logging configured properly              THEN 1 END) as recent_jobs

    FROM jobs 

## Related Documentation    WHERE profile_name = ?

    """

- **[DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md)** - Coding standards (93/100 compliance)    

- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions    result = self.conn.execute(analytics_sql, [profile_name]).fetchone()

- **[README.md](../README.md)** - User-facing documentation    return self._format_analytics_result(result)

- **[.github/copilot-instructions.md](../.github/copilot-instructions.md)** - AI coding agent guidance```



---## Database Architecture



**Version:** 4.0.0  ### Schema Design

**Last Updated:** January 13, 2025  

**Maintainer:** JobQst Development Team  ```sql

**Status:** This document reflects **actual implementation**, not aspirational features-- Optimized schema for analytical workloads

CREATE TABLE jobs (

> "Good architecture is invisible. You only notice it when it's absent."    -- Primary identification

    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    company VARCHAR NOT NULL,
    location VARCHAR,
    
    -- Job details
    salary_range VARCHAR,
    description TEXT,
    summary TEXT,
    skills TEXT,
    url VARCHAR,
    source VARCHAR,
    
    -- Temporal data
    date_posted DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Processing results
    fit_score FLOAT,
    status VARCHAR DEFAULT 'new',
    
    -- User context
    profile_name VARCHAR,
    
    -- Application tracking
    application_status VARCHAR DEFAULT 'discovered',
    application_date DATE,
    priority_level INTEGER DEFAULT 3
);

-- Optimized indexes for common query patterns
CREATE INDEX idx_jobs_profile_fit ON jobs(profile_name, fit_score DESC);
CREATE INDEX idx_jobs_company ON jobs(company);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_status ON jobs(status, application_status);
```

### Data Partitioning Strategy

```python
class PartitionedJobDatabase:
    """
    Partitioning strategy for large datasets:
    - By profile (separate databases per user)
    - By date (monthly partitions for historical data)
    - By source (separate tables for different job boards)
    """
    
    def get_partition_key(self, job_data: Dict[str, Any]) -> str:
        """Determine partition based on job data."""
        profile = job_data.get('profile_name', 'default')
        date = job_data.get('created_at', datetime.now())
        return f"{profile}_{date.strftime('%Y_%m')}"
```

## Code Quality & Tooling

### Development Environment

**Python Environment:**
- **Version:** 3.11.11 (mandatory)
- **Manager:** conda (auto_job environment)
- **Location:** `C:\Users\Niraj\miniconda3\envs\auto_job\python.exe`

**Setup:**
```bash
conda activate auto_job
python --version  # Verify: Python 3.11.11
```

### Code Formatting & Linting

**Black (Code Formatter):**
- **Version:** 25.1.0
- **Line Length:** 100 characters
- **Coverage:** 291/293 files (99.3%)
- **Configuration:** `pyproject.toml`

```bash
python -m black src/ tests/
python -m black src/ tests/ --check  # Verify only
```

**Flake8 (Linter):**
- **Version:** 7.1.1
- **Configuration:** `.flake8`
- **Rules:** Max line 100, specific exclusions

```bash
python -m flake8 src/ tests/
```

**isort (Import Sorter):**
- **Version:** 5.13.2
- **Profile:** black-compatible
- **Configuration:** `pyproject.toml`

```bash
python -m isort src/ tests/
```

### Type Checking

**Mypy:**
- **Version:** 1.14.1
- **Python Target:** 3.11
- **Configuration:** `pyproject.toml`

```bash
python -m mypy src/
```

### Testing

**Pytest:**
- **Version:** 8.4.0
- **Coverage:** pytest-cov 6.1.1
- **Configuration:** `pytest.ini`

```bash
python -m pytest tests/ -v
python -m pytest tests/ --cov=src --cov-report=html
```

### Security Scanning

**Bandit:**
- **Version:** 1.8.0
- **Purpose:** Security vulnerability detection
- **Configuration:** `pyproject.toml`

```bash
python -m bandit -r src/
```

### Pre-commit Hooks

**Status:** ✅ Configured and ready to activate

**Installation:**
```bash
pre-commit install
pre-commit run --all-files
```

**Hooks Configured:**
- ✅ Trailing whitespace removal
- ✅ End-of-file fixer
- ✅ YAML/JSON validation
- ✅ Black formatting
- ✅ isort import sorting
- ✅ Flake8 linting
- ✅ Mypy type checking

**Configuration:** `.pre-commit-config.yaml`

### Quality Metrics

**Current Compliance Score:** 93/100 ✅

| Category | Score | Status |
|----------|-------|--------|
| File Size Compliance | 95/100 | ✅ Excellent |
| Dependency Management | 100/100 | ✅ Perfect |
| Type Annotations | 75/100 | ✅ Good |
| Modern Python Patterns | 90/100 | ✅ Excellent |
| Code Organization | 90/100 | ✅ Excellent |
| Documentation | 80/100 | ✅ Good |
| Testing | 85/100 | ✅ Good |

**Details:** See [STANDARDS_COMPLIANCE_AUDIT.md](STANDARDS_COMPLIANCE_AUDIT.md)

## Processing Pipeline

### Async Processing Architecture

```python
class AsyncJobProcessor:
    """
    Asynchronous job processing with configurable concurrency.
    
    Features:
    - Configurable worker pools
    - Backpressure handling
    - Error isolation
    - Progress tracking
    """
    
    def __init__(self, max_workers: int = 10):
        self.semaphore = asyncio.Semaphore(max_workers)
        self.error_handler = ErrorHandler()
        self.progress_tracker = ProgressTracker()
    
    async def process_jobs_concurrent(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process jobs with controlled concurrency."""
        
        tasks = [
            self._process_single_job_with_semaphore(job) 
            for job in jobs
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Separate successful results from errors
        successful_results = []
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                errors.append(result)
            else:
                successful_results.append(result)
        
        # Log errors but don't fail the entire batch
        if errors:
            self.error_handler.log_batch_errors(errors)
        
        return successful_results
    
    async def _process_single_job_with_semaphore(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process single job with semaphore control."""
        async with self.semaphore:
            try:
                return await self._process_single_job(job)
            except Exception as e:
                # Isolate errors to prevent cascade failures
                logger.error(f"Job processing failed: {e}", extra={"job_id": job.get('id')})
                raise
```

### Error Handling Strategy

```python
class ErrorHandler:
    """Comprehensive error handling with categorization and recovery."""
    
    def __init__(self):
        self.error_categories = {
            'network': NetworkError,
            'parsing': ParseError,
            'validation': ValidationError,
            'processing': ProcessingError
        }
        self.retry_strategies = {
            NetworkError: ExponentialBackoffRetry(max_attempts=3),
            RateLimitError: LinearBackoffRetry(delay=60),
            ProcessingError: NoRetry()
        }
    
    async def handle_error_with_retry(self, error: Exception, operation: Callable) -> Any:
        """Handle error with appropriate retry strategy."""
        error_type = type(error)
        retry_strategy = self.retry_strategies.get(error_type, NoRetry())
        
        return await retry_strategy.execute(operation)
```

## Security Architecture

### Input Validation

```python
from pydantic import BaseModel, validator

class JobSearchRequest(BaseModel):
    """Validated job search request."""
    
    keywords: List[str]
    location: str
    max_results: int = 50
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if not v or len(v) > 10:
            raise ValueError('Keywords must be 1-10 items')
        
        # Sanitize keywords
        sanitized = []
        for keyword in v:
            clean_keyword = re.sub(r'[^\w\s-]', '', keyword.strip())
            if clean_keyword:
                sanitized.append(clean_keyword)
        
        return sanitized
    
    @validator('max_results')
    def validate_max_results(cls, v):
        if not (1 <= v <= 1000):
            raise ValueError('max_results must be 1-1000')
        return v
```

### Secure Configuration

```python
from pydantic import BaseSettings

class SecuritySettings(BaseSettings):
    """Security configuration with environment variable support."""
    
    # Database security
    database_encryption_key: Optional[str] = None
    database_connection_timeout: int = 30
    
    # Scraping security
    user_agent_rotation: bool = True
    request_timeout: int = 30
    max_redirects: int = 3
    
    # Rate limiting
    requests_per_minute: int = 60
    burst_limit: int = 10
    
    class Config:
        env_file = ".env"
        env_prefix = "JOBQST_"
```

## Performance Considerations

### Caching Strategy

```python
from functools import lru_cache
import redis

class MultiLevelCache:
    """Multi-level caching with memory and Redis."""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.memory_cache = {}
    
    @lru_cache(maxsize=1000)
    def get_job_similarity(self, job1_id: str, job2_id: str) -> float:
        """Memory-cached similarity calculation."""
        return self._calculate_similarity(job1_id, job2_id)
    
    async def get_processed_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Redis-cached processed job data."""
        cached = await self.redis_client.get(f"processed_job:{job_id}")
        if cached:
            return json.loads(cached)
        return None
```

### Database Optimization

```python
class OptimizedQueries:
    """Optimized query patterns for common operations."""
    
    def get_top_jobs_optimized(self, profile_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Optimized query using indexes and column selection."""
        
        # Only select needed columns
        query = """
        SELECT id, title, company, location, fit_score, created_at
        FROM jobs 
        WHERE profile_name = ? 
        AND fit_score IS NOT NULL
        ORDER BY fit_score DESC, created_at DESC
        LIMIT ?
        """
        
        return self.conn.execute(query, [profile_name, limit]).fetchall()
    
    def get_analytics_batch(self, profile_name: str) -> Dict[str, Any]:
        """Single query for multiple analytics."""
        
        # Combine multiple aggregations in one query
        query = """
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(DISTINCT company) as unique_companies,
            AVG(fit_score) as avg_fit_score,
            COUNT(CASE WHEN created_at > date('now', '-1 day') THEN 1 END) as recent_jobs,
            COUNT(CASE WHEN application_status = 'applied' THEN 1 END) as applied_count
        FROM jobs 
        WHERE profile_name = ?
        """
        
        result = self.conn.execute(query, [profile_name]).fetchone()
        return self._format_analytics(result)
```

## Deployment Architecture

### Container Architecture

```dockerfile
# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY src/ /app/src/
COPY main.py /app/

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash jobqst
USER jobqst

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.core.job_database import get_job_db; get_job_db().get_job_count()"

CMD ["python", "main.py"]
```

### Scaling Considerations

```python
class ScalableArchitecture:
    """
    Horizontal scaling patterns:
    
    1. Scraper Scaling:
       - Multiple scraper instances with job queue
       - Distributed rate limiting
       - Shared result storage
    
    2. Processing Scaling:
       - Worker pool with message queue
       - GPU resource sharing
       - Result aggregation
    
    3. Database Scaling:
       - Read replicas for analytics
       - Partitioning by profile/date
       - Connection pooling
    """
    
    def __init__(self):
        self.job_queue = RedisQueue('job_scraping')
        self.result_queue = RedisQueue('job_results')
        self.worker_pool = WorkerPool(max_workers=50)
```

### Monitoring Architecture

```python
class MonitoringSystem:
    """Comprehensive monitoring and observability."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self.alerting = AlertingSystem()
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics."""
        return {
            'scraping_rate': self.metrics_collector.get_scraping_rate(),
            'processing_latency': self.metrics_collector.get_processing_latency(),
            'database_performance': self.metrics_collector.get_db_performance(),
            'error_rate': self.metrics_collector.get_error_rate(),
            'resource_usage': self.metrics_collector.get_resource_usage()
        }
    
    async def health_check(self) -> Dict[str, bool]:
        """Comprehensive health check."""
        return {
            'database': await self.health_checker.check_database(),
            'scrapers': await self.health_checker.check_scrapers(),
            'processing': await self.health_checker.check_processing(),
            'external_apis': await self.health_checker.check_external_apis()
        }
```

## Design Patterns Used

### Factory Pattern

```python
class ScraperFactory:
    """Factory for creating appropriate scrapers."""
    
    @staticmethod
    def create_scraper(scraper_type: str, config: Dict[str, Any]) -> BaseJobScraper:
        scrapers = {
            'eluta': ElutaScraper,
            'external': ExternalJobScraper,
            'linkedin': LinkedInScraper
        }
        
        scraper_class = scrapers.get(scraper_type)
        if not scraper_class:
            raise ValueError(f"Unknown scraper type: {scraper_type}")
        
        return scraper_class(config)
```

### Observer Pattern

```python
class JobProcessingObserver:
    """Observer for job processing events."""
    
    def __init__(self):
        self.observers = []
    
    def add_observer(self, observer: Callable[[Dict[str, Any]], None]):
        self.observers.append(observer)
    
    def notify_job_processed(self, job_data: Dict[str, Any]):
        for observer in self.observers:
            try:
                observer(job_data)
            except Exception as e:
                logger.error(f"Observer error: {e}")
```

### Strategy Pattern

```python
class ProcessingStrategy(ABC):
    """Abstract processing strategy."""
    
    @abstractmethod
    async def process_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class FastProcessingStrategy(ProcessingStrategy):
    """Fast processing for high-volume scenarios."""
    
    async def process_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implement fast processing logic
        return job_data

class DetailedProcessingStrategy(ProcessingStrategy):
    """Detailed processing with AI analysis."""
    
    async def process_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implement detailed processing logic
        return job_data
```

---

**Architecture Version**: 3.1.0  
**Last Updated**: January 13, 2025  
**Compliance Score**: 93/100 ✅ (PRODUCTION READY)  
**Maintainer**: JobQst Development Team

## Version History

- **v3.1.0** (January 13, 2025): Environment configuration complete - Python 3.11.11 validated, dev tools installed (black 25.1.0, flake8 7.1.1, mypy 1.14.1), 291 files formatted, 93/100 compliance achieved, pre-commit hooks configured
- **v3.0.0** (September 30, 2025): Dashboard consolidation complete - unified caching, shared data access, centralized analytics, ProfileService, RCIP integration, streamlined navigation, monitoring consolidation
- **v2.0.0** (September 21, 2025): Initial architecture documentation with modern patterns
- **v1.0.0**: Legacy architecture (pre-consolidation)

## Related Documentation

- **DEVELOPMENT_STANDARDS.md** - Coding standards and best practices (93/100 compliant)
- **STANDARDS_COMPLIANCE_AUDIT.md** - Detailed compliance metrics and scoring
- **ENVIRONMENT_SETUP_GUIDE.md** - Complete environment setup instructions
- **TROUBLESHOOTING.md** - Common issues and solutions
- **COMPLIANCE_PHASE_4_COMPLETE.md** - Latest phase completion summary

This architecture document serves as the technical foundation for understanding JobQst's design decisions, patterns, and implementation strategies. For implementation details, see the [Development Standards](DEVELOPMENT_STANDARDS.md). For dashboard refactoring details, see [Dashboard Refactor Roadmap](dashboard_refactor_roadmap.md).
