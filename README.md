# AutoJobAgent

**Job application automation with web scraping and document generation.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **🔍 Web Scraping**: Multi-site job scraping from Eluta, Indeed, LinkedIn, and other job boards
- **🤖 Document Generation**: Resume and cover letter generation using Gemini API
- **⚡ Concurrent Processing**: Parallel job processing for better performance
- **📊 Job Filtering**: Filter jobs by language, seniority level, and keywords
- **🎯 ATS Integration**: Automated application submission to various ATS platforms
- **📈 Dashboard**: Streamlit-based web interface for job management

## Quick Start

### Redis Integration (Job Queue)

The job pipeline now uses Redis for high-throughput, persistent job queueing. You must have a Redis server running and configure the connection string in your `.env` file:

```
REDIS_URL=redis://localhost:6379/0
```

If you need to install Redis locally:
- **Windows:** Use [Memurai](https://www.memurai.com/) or [Redis for Windows](https://github.com/microsoftarchive/redis/releases)
- **macOS/Linux:** Use `brew install redis` or your package manager

Start Redis before running the pipeline:
```powershell
# Windows (Memurai)
memurai.exe
# macOS/Linux
redis-server
```

The pipeline will automatically use the `REDIS_URL` from your environment.

### Prerequisites
- **Python 3.10+**
- **Ollama with OpenHermes 2.5**
- **Playwright browsers**

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd automate_job
python -m venv .venv
.\.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Setup OpenHermes 2.5
ollama pull openhermes:v2.5
ollama serve
```

### Quick Test
```bash
# Test OpenHermes 2.5 connection
python tests/integration/test_ollama_connection.py

# Test AI job analysis
python tests/integration/test_openhermes_analyzer.py

# Test optimized scraper
python tests/integration/test_optimized_scraper.py
```

## Usage

### Optimized Scraper
```python
from src.scrapers.optimized_eluta_scraper import OptimizedElutaScraper
import asyncio

async def main():
    scraper = OptimizedElutaScraper('Nirajan')
    jobs = await scraper.scrape_all_keywords_optimized(max_jobs_per_keyword=10)
    print(f'Found {len(jobs)} jobs!')

asyncio.run(main())
```

### Dashboard
```bash
python -m streamlit run src/dashboard/unified_dashboard.py
```

## System Components

- **Web Scraping**: Playwright-based browser automation
- **Job Processing**: Rule-based filtering and keyword matching  
- **Document Generation**: Gemini API integration for personalized documents
- **Database**: SQLite for job storage and management
- **Dashboard**: Streamlit web interface with real-time updates

## Configuration

### Profile Setup (`profiles/Nirajan/Nirajan.json`)
```json
{
  "name": "Your Name",
  "skills": ["Python", "Data Analysis", "Machine Learning"],
  "openhermes_config": {
    "model": "openhermes:v2.5",
    "temperature": 0.2,
    "max_tokens": 2048
  }
}
```

### Environment (`.env`)
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=openhermes:v2.5
STREAMLIT_PORT=8501
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Optimized      │    │  OpenHermes 2.5  │    │  Concurrent     │
│  Web Scraper    │───▶│  AI Analysis     │───▶│  Processing     │
│  (Tab Closure)  │    │  (Job Matching)  │    │  (2 Jobs/Time)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Test specific components
python tests/integration/test_ollama_connection.py      # AI connection
python tests/integration/test_openhermes_analyzer.py    # Job analysis
python tests/integration/test_optimized_scraper.py      # Scraper optimization
```

## Documentation

- **[SCRAPER_IMPROVEMENTS_SUMMARY.md](SCRAPER_IMPROVEMENTS_SUMMARY.md)** - Latest optimizations
- **[OPTIMIZATION_COMPARISON.md](OPTIMIZATION_COMPARISON.md)** - Performance comparison
- **[docs/](docs/)** - Complete documentation

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Test changes: `pytest tests/ -v`
4. Submit pull request

## License

MIT License - see LICENSE file for details.

---

**🎉 Ready for production with optimized performance and OpenHermes 2.5 AI!**