# 📁 `/src` - Core Application Source Code

## 📋 Overview
**Purpose**: Contains all core application source code for AutoJobAgent  
**Architecture**: Modular structure with clear separation of concerns  
**Status**: ✅ **CLEANED UP** - Reorganized following development standards  
**Last Updated**: February 8, 2025

## 🧹 Recent Cleanup (February 2025)
- ✅ Moved loose script files to `scripts/` directory
- ✅ Organized utilities in proper `src/utils/` structure  
- ✅ Consolidated database tools into single script
- ✅ Cleaned up __pycache__ directories and log files
- ✅ Improved file organization following project standards

See [CLEANUP_SUMMARY.md](./CLEANUP_SUMMARY.md) for detailed cleanup information.

---

## 🏗️ **Microservices Architecture Structure**

### **🔧 Core System Components**
```
src/
├── core/                    # Shared system components
│   ├── job_database.py     # Central data management
│   ├── profile_manager.py  # User profile handling
│   └── config_manager.py   # Configuration management
├── orchestration/          # Service coordination
│   ├── local_event_bus.py  # Kafka-style event messaging
│   └── service_orchestrator.py # Service lifecycle management
├── services/               # Independent microservices
│   ├── job_scraping_service.py   # Job discovery and extraction
│   ├── job_analysis_service.py   # ML-powered job analysis
│   └── job_application_service.py # Application automation
└── utils/                  # Shared utilities and helpers
```

### **🎛️ Interface & Integration**
```
src/
├── dashboard/              # Web UI components (legacy)
│   ├── components/        # Reusable UI components
│   └── unified_dashboard.py # Main dashboard (deprecated)
├── cli/                   # Command-line interface
│   ├── handlers/         # CLI command handlers
│   └── main_cli.py       # CLI entry point
└── api/                  # External API integrations
    ├── gemini_integration.py  # AI document generation
    └── job_board_apis.py      # Job board integrations
```

### **🕷️ Data Collection & Processing**
```
src/
├── scrapers/              # Web scraping modules
│   ├── eluta_scraper.py  # Eluta.ca job scraping
│   ├── indeed_scraper.py # Indeed.com integration
│   └── base_scraper.py   # Common scraping functionality
├── analysis/             # Job analysis and matching
│   ├── job_analyzer.py   # ML-powered job analysis
│   └── match_engine.py   # Skill-based job matching
└── document_modifier/    # Document generation
    ├── gemini_resume_generator.py # AI resume creation
    └── document_templates.py      # Template management
```

---

## � **Recent Architecture Improvements (July 2025)**

### **✅ Microservices Migration Completed**
- **Event-Driven**: Replaced tight coupling with async messaging
- **Service Independence**: Each service manages its own lifecycle
- **Scalability**: Horizontal scaling ready architecture
- **Maintainability**: Services are 200-600 lines each (vs 2404-line monolith)

### **✅ Production Deployment**
- **Live Services**: Auto-scraping every 30 minutes
- **Health Monitoring**: Continuous service health checks
- **Graceful Management**: Clean startup/shutdown procedures
- **Performance Metrics**: Real-time system monitoring

---

## 📋 **Entry Points & Main Components**

### **🎯 Primary Entry Points**
- **`main.py`** - Main CLI interface and application entry
- **`production_launcher.py`** - Microservices production deployment
- **`dashboard/unified_dashboard.py`** - Legacy web interface

### **🔧 Core Services (Production)**
- **`orchestration/local_event_bus.py`** - Event messaging system
- **`services/job_scraping_service.py`** - Job discovery service
- **`services/job_analysis_service.py`** - AI analysis service
- **`orchestration/service_orchestrator.py`** - Service management

### **🤖 AI & Document Generation**
- **`gemini_resume_generator.py`** - Primary document generation
- **`ai/gemini_optimizer.py`** - AI optimization and training
- **`document_modifier/`** - Document processing and formatting

---

## 🛠️ **Development Guidelines**

### **📏 File Size Standards (Enforced)**
- **Services**: 200-600 lines (microservices architecture)
- **Utilities**: Max 300 lines for maintainability
- **🚨 Critical Threshold**: Files >1000 lines require immediate refactoring
- **⚠️ Warning Threshold**: Files >500 lines reviewed for splitting

### **🏗️ Architecture Principles**
- **Single Responsibility**: Each service has one clear purpose
- **Event-Driven Communication**: Async messaging between services
- **Service Independence**: Services can be developed and deployed separately
- **Clean APIs**: Well-defined interfaces between components

### **📋 Code Quality Standards**
- **Type Hints**: All functions properly typed
- **Error Handling**: Comprehensive error handling with context
- **Documentation**: Docstrings for all public functions
- **Testing**: Unit tests for all critical functionality
- **Real Data Only**: No placeholder or fabricated content

---

## 🔄 **Migration Status**

### **✅ Completed**
- Microservices architecture implementation
- Event-driven communication system
- Production deployment and monitoring
- File size compliance across all services
- Documentation alignment with new architecture

### **🎯 Current Focus**
- Test suite repair and modernization
- Documentation consolidation (6-doc policy)
- Performance optimization and monitoring
- Improved error handling and recovery

---

## 📚 **Related Documentation**

- **[Development Standards](../docs/standards/DEVELOPMENT_STANDARDS.md)** - Core development guidelines
- **[Architecture](../docs/ARCHITECTURE.md)** - System architecture overview
- **[API Reference](../docs/API_REFERENCE.md)** - Service APIs and integration
- **[Troubleshooting](../docs/TROUBLESHOOTING.md)** - Common issues and solutions

---

*This source code structure follows microservices architecture patterns with event-driven communication and clean separation of concerns. All components are designed for scalability, maintainability, and independent deployment.*
- Benchmark files in multiple locations
- Demo files mixed with production code

---

## 🎯 Target Structure

```
src/
├── 📄 main.py              # Single main entry point
├── 📄 __init__.py         # Package initialization
├── 🗂️ core/               # Core business logic
│   ├── job_database.py    # Database operations
│   ├── session.py         # Session management
│   └── orchestrator.py    # Process orchestration
├── 🗂️ cli/                # Command line interface
│   ├── handlers/          # CLI command handlers
│   └── menu.py           # Interactive menu
├── 🗂️ dashboard/          # Web dashboard
│   ├── api.py            # API endpoints
│   ├── app.py            # Streamlit app
│   └── components/       # UI components
├── 🗂️ ats/                # ATS integration
│   ├── base_submitter.py # Base submission logic
│   ├── workday.py        # Workday integration
│   ├── icims.py          # iCIMS integration
│   └── greenhouse.py     # Greenhouse integration
├── 🗂️ scrapers/           # Web scraping modules
│   ├── base_scraper.py   # Base scraper class
│   ├── eluta/            # Eluta-specific scrapers
│   ├── indeed/           # Indeed-specific scrapers
│   └── session_manager.py # Session management
├── 🗂️ utils/              # Utility functions
│   ├── document_generator.py # Document generation
│   ├── profile_helpers.py    # Profile management
│   ├── job_helpers.py        # Job utilities
│   └── file_operations.py    # File I/O operations
├── 🗂️ ai/                 # AI/ML components
│   ├── Improved_analyzer.py  # AI job analysis
│   ├── llama/               # Llama model integration
│   └── Text features/          # Text Text features
├── 🗂️ services/           # Background services
│   ├── orchestrator.py    # Service orchestration
│   ├── worker_pool.py     # Worker management
│   └── monitor.py         # System monitoring
└── 🗂️ benchmarks/         # Performance benchmarks
    ├── scraping_bench.py  # Scraping benchmarks
    └── dashboard_bench.py # Dashboard benchmarks
```

---

## 📊 Current Folder Analysis

### ✅ Well-Organized Folders
- `📁 core/` - Core business logic (good structure)
- `📁 cli/` - Command line interface (organized)
- `📁 dashboard/` - Web dashboard (clean)
- `📁 ats/` - ATS integrations (structured)
- `📁 utils/` - Utility functions (needs deduplication)

### ⚠️ Needs Reorganization
- `📁 scrapers/` - Some structure, needs cleanup
- `📁 ai/` - Mixed organization
- `📁 services/` - Partial organization

### ❌ Missing/Incomplete
- `📁 benchmarks/` - Scattered files need consolidation
- Proper `__init__.py` files for imports
- Clear module boundaries

---

## 🚨 Files to Move/Reorganize

### Move to `/tests`
```
test_*.py files (20+ files)
comprehensive_benchmark_test.py
scraping_performance_test.py
```

### Move to `/src/benchmarks`
```
benchmark_system.py
dashboard_benchmark.py
detailed_benchmark.py
simple_scraping_benchmark.py
scraping_performance_summary.py
comprehensive_benchmark_summary.py
tensorflow_training_summary.py
```

### Move to `/demos` or `/experiments`
```
demo_monster_ca.py
demo_worker_system.py
monster_quick_test.py
simple_similarity_test.py
```

### Consolidate Main Files
```
main.py ⭐ (KEEP)
main_cli.py ❌ (MERGE)
main_modular.py ❌ (MERGE)
```

---

## 🔧 Immediate Actions

### Phase 1: Emergency Cleanup
1. **Move test files** to `/tests` directory
2. **Create `/src/benchmarks`** and move benchmark files
3. **Create `/experiments`** for demo/experimental files
4. **Consolidate main files** into single entry point

### Phase 2: Folder Documentation
1. Create `README.md` for each subfolder
2. Document module purposes and dependencies
3. Create proper `__init__.py` files

### Phase 3: Function Deduplication
1. Remove duplicate functions found in analysis
2. Update import statements
3. Test all modules work correctly

---

## 📚 Subfolders Documentation Status

| Folder | Documentation | Status |
|--------|---------------|--------|
| `core/` | ❌ Missing | High Priority |
| `cli/` | ❌ Missing | High Priority |
| `dashboard/` | ❌ Missing | High Priority |
| `ats/` | ❌ Missing | High Priority |
| `scrapers/` | ❌ Missing | High Priority |
| `utils/` | ❌ Missing | Critical (duplicates) |
| `ai/` | ❌ Missing | Medium Priority |
| `services/` | ❌ Missing | Medium Priority |

---

## 🎯 Success Metrics

### File Reduction
- **Current**: 60+ files in `/src` root
- **Target**: 3 files in `/src` root (`main.py`, `__init__.py`, config)

### Organization
- All test files in `/tests`
- All benchmarks in `/src/benchmarks`
- All demos in `/experiments`
- Clear module boundaries

### Performance
- Following performance optimization patterns
- Efficient import structures
- Proper caching strategies

---

## ⚠️ Migration Risks

### High Risk
- **Import path changes**: Many files import from current structure
- **Main file consolidation**: Risk of breaking CLI functionality
- **Test file moves**: Risk of breaking test discovery

### Mitigation
- Update all import statements before moving files
- Test each step of reorganization
- Create migration scripts for systematic changes

---

*Last Updated: January 8, 2025*  
*Next Review: After Phase 1 cleanup completion*  
*Estimated Cleanup Time: 4-6 hours*
