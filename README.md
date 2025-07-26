# AutoJobAgent

**Intelligent job application automation with optimized web scraping and OpenHermes 2.5 AI analysis.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenHermes 2.5](https://img.shields.io/badge/AI-OpenHermes%202.5-green.svg)](#ai-integration)

## 🚀 Latest Optimizations

### **Immediate Tab Closure + Concurrent Processing**
- **90% Memory Reduction**: Tabs close immediately after URL extraction
- **2x Faster Processing**: Concurrent job analysis (2 jobs simultaneously)
- **OpenHermes 2.5 AI**: Superior job compatibility analysis
- **Stable Performance**: Consistent resource usage throughout scraping

## Features

- **🔍 Optimized Web Scraping**: Multi-site scraping with immediate tab closure
- **🤖 OpenHermes 2.5 AI**: Advanced job analysis and compatibility scoring
- **⚡ Concurrent Processing**: Parallel job processing for maximum efficiency
- **📊 Smart Filtering**: Entry-level job filtering with AI-powered matching
- **🎯 ATS Integration**: Automated application submission support
- **📈 Real-time Dashboard**: Streamlit-based monitoring and management

## Quick Start

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

## Performance Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Peak Tabs** | 20+ | 1-2 | **90% reduction** |
| **Processing Speed** | Sequential | Concurrent | **2x faster** |
| **Memory Usage** | Growing | Stable | **Constant** |
| **AI Analysis** | Mistral 7B | OpenHermes 2.5 | **Superior quality** |

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