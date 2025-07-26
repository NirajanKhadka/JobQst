# AutoJobAgent Technology Stack

## Core Technologies

### Backend & Runtime
- **Python 3.10+** (3.11 recommended) - Core language with modern async support
- **SQLite** - Primary database for local data storage and job management
- **Playwright** - Browser automation for web scraping with JavaScript link handling
- **Streamlit** - Dashboard and web interface framework
- **Rich** - Enhanced CLI output and logging

### AI & Document Generation
- **Ollama + Llama3 7B** - Primary AI service for job analysis and compatibility scoring
- **Enhanced Rule-Based Analysis** - Intelligent fallback when AI is unavailable
- **ReliableJobProcessorAnalyzer** - Fault-tolerant AI analysis with automatic fallbacks
- **python-docx** - Document manipulation and generation
- **reportlab** - PDF generation capabilities

### Web Scraping & Automation
- **Playwright MCP** - Model Context Protocol for enhanced browser automation (in migration)
- **BeautifulSoup4** - HTML parsing and data extraction
- **requests** - HTTP client for API interactions
- **asyncio** - Asynchronous programming for concurrent operations

### Dashboard & UI
- **Streamlit** - Primary web interface framework
- **pandas** - Data manipulation and analysis
- **plotly** - Interactive charts and visualizations
- **streamlit-aggrid** - Enhanced data tables
- **streamlit-autorefresh** - Real-time dashboard updates

### Development & Quality
- **pytest** - Testing framework with comprehensive test suite
- **black** - Code formatting
- **mypy** - Type checking
- **flake8** - Code linting
- **isort** - Import sorting

## Build System & Dependencies

### Package Management
- **pip** - Primary package manager
- **requirements.txt** - Production dependencies
- **pyproject.toml** - Project configuration and optional dependencies

### Key Dependencies
```
# Core web scraping
requests>=2.28.0
beautifulsoup4>=4.11.0
playwright>=1.42.0

# Document processing
python-docx>=0.8.11
openpyxl>=3.0.10

# Dashboard - Streamlit
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.15.0

# AI Integration (optional)
google-generativeai>=0.3.0  # Gemini API
```

## Common Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate environment (Windows)
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Development Commands
```bash
# Start main application
python main.py

# Launch dashboard
python -m streamlit run src/dashboard/unified_dashboard.py

# Run tests
pytest tests/ -v

# Code formatting
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

### AI Integration Commands
```bash
# Start Ollama service (required for AI analysis)
ollama serve

# Pull Llama3 model (primary AI model)
ollama pull llama3

# Test complete scraping + AI processing pipeline
python test_scraper_with_limit.py  # Scrape job URLs
python test_job_processor.py       # Process with AI analysis

# Check AI service status
ollama list
```

# Linting
flake8 src/
```

### Testing Commands
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest -m "unit" -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Performance testing
pytest tests/performance/ -v
```

### Production Commands
```bash
# Health check
python main.py --action health-check

# Start scraping
python main.py --action scrape --headless

# Generate documents
python main.py --action generate-docs

# Run benchmarks
python main.py --action benchmark
```

## Architecture Patterns

### Design Patterns Used
- **Command Pattern** - CLI command handling
- **Strategy Pattern** - ATS integration strategies
- **Observer Pattern** - Real-time dashboard updates
- **Factory Pattern** - Dynamic ATS submitter creation

### Code Organization
- **Modular Architecture** - Clear separation of concerns
- **Service Layer** - Business logic abstraction
- **Repository Pattern** - Data access abstraction
- **Dependency Injection** - Loose coupling between components

## Platform Specifics

### Windows (Primary Platform)
- **PowerShell** scripts for automation
- **Windows-specific** path handling
- **CMD** compatibility for batch operations

### Cross-Platform Support
- **Python** ensures cross-platform compatibility
- **Playwright** works on Windows, macOS, Linux
- **SQLite** database is portable across platforms

## Performance Considerations

### Optimization Features
- **Async Processing** - Concurrent job scraping and processing
- **Connection Pooling** - Efficient browser and database usage
- **Caching** - Avoid redundant operations
- **Lazy Loading** - Import heavy modules only when needed
- **Worker Pools** - Parallel document generation (up to 5 workers)

### Monitoring & Metrics
- **Health Checks** - System, database, and service monitoring
- **Performance Metrics** - Real-time system resource tracking
- **Error Tracking** - Comprehensive logging and error handling
- **Resource Monitoring** - CPU, memory, and disk usage tracking