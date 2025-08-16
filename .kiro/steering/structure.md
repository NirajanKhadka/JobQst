# AutoJobAgent Project Structure

## Root Directory Organization

```
automate_job/
├── main.py                    # Primary entry point - CLI and dashboard launcher
├── start_api.py              # API server entry point
├── requirements.txt          # Production dependencies
├── pyproject.toml           # Project configuration and build settings
├── pytest.ini              # Test configuration
├── README.md                # Project overview and quick start
├── CHANGELOG.md             # Version history and updates
├── LICENSE                  # MIT license
├── .env.example             # Environment variables template
├── Dockerfile               # Container configuration
├── docker-compose.dev.yml   # Development container setup
└── .gitignore               # Git ignore patterns
```

## Core Source Structure (`src/`)

### Primary Components
```
src/
├── core/                    # Core system components
│   ├── job_database.py      # SQLite database operations
│   ├── job_filters.py       # Job filtering and matching logic
│   ├── process_manager.py   # System process management
│   ├── session.py           # Browser session management
│   └── performance_monitor.py # System performance tracking
│
├── scrapers/                # Web scraping engines
│   ├── comprehensive_eluta_scraper.py    # Primary Eluta scraper
│   ├── Improved_job_description_scraper.py # Job detail extraction
│   ├── modern_job_pipeline.py            # Async scraping pipeline
│   ├── mcp_browser_client.py             # MCP browser automation
│   └── [site]_scraper.py                 # Individual site scrapers
│
├── dashboard/               # Streamlit web interface
│   ├── unified_dashboard.py # Main dashboard application
│   ├── components/          # Modular UI components
│   ├── routers/            # API routing
│   └── services/           # Dashboard business logic
│
├── ats/                    # ATS integration modules
│   ├── base_submitter.py   # Common ATS functionality
│   ├── workday.py          # Workday ATS integration
│   ├── greenhouse.py       # Greenhouse ATS integration
│   └── [ats_name].py       # Individual ATS implementations
│
├── cli/                    # Command-line interface (legacy)
│   ├── actions/            # CLI action handlers
│   ├── handlers/           # Business logic handlers
│   └── menu/               # Interactive menu system
│
└── utils/                  # Shared utilities
    ├── profile_helpers.py  # User profile management
    ├── document_generator.py # Document generation utilities
    └── job_helpers.py      # Job data manipulation
```

### Supporting Modules
```
src/
├── ai/                     # AI and ML components
├── analysis/               # Job analysis engines
├── agents/                 # Multi-agent orchestration
├── health_checks/          # System health monitoring
├── job_applier/           # Job application automation
├── pipeline/              # Data processing pipelines
├── profiles/              # User profile storage
└── services/              # Service layer abstractions
```

## Configuration & Data

### Configuration Files
```
config/
└── health_config.json     # Health check configuration

profiles/                  # User profile data
├── [profile_name]/        # Individual profile directories
├── default/               # Default profile template
└── *.json                 # Profile configuration files

.kiro/                     # Kiro IDE configuration
├── settings/              # IDE settings
└── steering/              # AI steering rules (this file)
```

### Data Storage
```
cache/                     # Temporary data cache
├── job_descriptions/      # Cached job descriptions
└── processed/             # Processed job data

logs/                      # Application logs
├── error_logs.log         # Error logging
├── gemini_api_call_log.json # AI API call logs
└── scheduler/             # Scheduled task logs

temp/                      # Temporary files
└── pytest_output.txt     # Test output cache
```

## Testing Structure (`tests/`)

### Test Organization
```
tests/
├── conftest.py            # Global test configuration and fixtures
├── unit/                  # Unit tests (fast, isolated)
│   ├── test_scrapers.py   # Scraper unit tests
│   ├── test_dashboard.py  # Dashboard component tests
│   └── test_*.py          # Individual module tests
│
├── integration/           # Integration tests (medium speed)
│   ├── test_scraping_integration.py # End-to-end scraping tests
│   └── test_dashboard_integration.py # Dashboard workflow tests
│
├── e2e/                   # End-to-end tests (slow)
│   └── test_full_workflow.py # Complete user workflows
│
├── performance/           # Performance benchmarks
├── fixtures/              # Test data and fixtures
└── system/                # System-level tests
```

## Documentation (`docs/`)

### Documentation Structure (7-Doc Policy)
```
docs/
├── README.md              # Documentation index
├── ARCHITECTURE.md        # System architecture and design
├── API_REFERENCE.md       # API documentation
├── DEVELOPER_GUIDE.md     # Development setup and workflow
├── DEVELOPMENT_STANDARDS.md # Coding standards and guidelines
├── TROUBLESHOOTING.md     # Support and diagnostics
└── ISSUE_TRACKER.md       # Current issues and priorities
```

## Scripts & Automation (`scripts/`)

### Utility Scripts
```
scripts/
├── README.md              # Script documentation
├── run_tests.bat          # Windows test runner
├── start_dev_environment.ps1 # Development setup
├── production_health_check.ps1 # Health monitoring
├── file_size_audit.ps1    # Architecture compliance
└── update_docs.py         # Documentation automation
```

## Key Architectural Principles

### File Organization Rules
- **Single Responsibility**: Each file has one clear purpose
- **Modular Design**: Related functionality grouped together
- **Clear Naming**: Descriptive file and directory names
- **Separation of Concerns**: UI, business logic, and data access separated

### Directory Conventions
- **snake_case** for directories and files
- **Logical grouping** by functionality, not by file type
- **Shallow hierarchy** - avoid deep nesting
- **Clear boundaries** between modules

### Import Patterns
```python
# Absolute imports from src root
from src.core.job_database import get_job_db
from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
from src.dashboard.components.metrics import render_metrics

# Relative imports within modules
from .base_submitter import BaseSubmitter
from ..utils.job_helpers import validate_job_data
```

### Configuration Management
- **Environment variables** for sensitive data
- **JSON files** for structured configuration
- **Profile-based** settings for user customization
- **Hierarchical** configuration with defaults and overrides

### Data Flow Architecture
```
Job Sources → Scrapers → Core Database → Analysis → Dashboard
                    ↓                      ↓
                 Cache ←→ Processing → ATS Integration
```

This structure supports the project's evolution from a monolithic application to a modular, maintainable system with clear separation of concerns and scalable architecture.