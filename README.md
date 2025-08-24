# JobQst - Intelligent Job Discovery Platform

<div align="center">

**🧹 Recently Modernized & Cleaned** - Profile-driven job discovery, matching, and ranking with AI-powered insights.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Playwright](https://img.shields.io/badge/Playwright-Automation-34D399.svg)](https://playwright.dev/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B.svg)](https://streamlit.io/)

[🚀 Quick Start](#-quick-start) • [📖 Documentation](docs/) • [🎥 Demo](#-demo) • [🤝 Contributing](#-contributing)

</div>

---

## What is JobQst?

JobQst is an intelligent job discovery platform that automates job searching across multiple sites, analyzes job-profile compatibility using AI, and provides comprehensive analytics. Recently modernized with a clean, maintainable architecture.

### 🎯 **Perfect For:**
- **Job Seekers** looking to automate and optimize their job search process
- **Career Changers** managing applications across different fields with AI insights
- **Professionals** who want intelligent job matching and application tracking
- **Anyone** seeking to leverage AI for better job discovery and analysis

### ✨ **What's New (August 2025)**
- ✅ **56+ files cleaned** - Removed redundant scripts and duplicates
- ✅ **Architecture streamlined** - Single entry point with library modules
- ✅ **Zero functionality lost** - All features preserved and enhanced
- ✅ **AI-powered features** - Enhanced with semantic scoring and smart caching

---

## Key Features

<table>
<tr>
<td width="33%">

### 🔍 Smart Job Discovery
- **Dual Strategy**: JobSpy (4 sites) + Eluta.ca fallback
- **Sites**: Indeed, LinkedIn, Glassdoor, ZipRecruiter
- **Parallel Processing**: Multi-site concurrent scraping
- **Smart Deduplication**: AI-powered duplicate detection

</td>
<td width="33%">

### 🧠 AI-Powered Analysis
- **Semantic Scoring**: AI job-profile compatibility
- **Skills Analysis**: Gap identification & suggestions
- **Resume Analysis**: Auto profile creation from PDFs
- **Location Intelligence**: Remote/hybrid/onsite detection

</td>
<td width="33%">

### 📊 Modern Dashboard
- **Real-time Monitoring**: Live scraping status
- **Interactive Analytics**: Trends and insights
- **Application Tracking**: End-to-end management
- **Profile Management**: Visual configuration

</td></tr>
</table>
<td width="33%">

### Ranking & Filtering
- Fit scoring and sorting by relevance
- Quick filters (remote, location, recency)
- Optional Streamlit dashboard for browsing

</td>
</tr>
</table>

### Management
- Optional Streamlit dashboard for browsing and filtering
- CLI for automated workflows

---

## Quick Start

### Prerequisites
- Python 3.11+ (3.12 recommended)
- Git

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/NirajanKhadka/automate_job_idea001.git
cd automate_job_idea001

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install browser automation
playwright install chromium

# 6. Setup environment
cp .env.example .env
# Edit .env with your configuration
```

### Configuration
Add or adjust these settings in your .env file:
```bash
# Database
DATABASE_URL=sqlite:///jobs.db

# Web scraping
SCRAPING_DELAY=2
MAX_CONCURRENT_REQUESTS=5
BROWSER_HEADLESS=true

# Dashboard (optional)
STREAMLIT_PORT=8501
```

### Launch
```bash
# Scrape jobs
python main.py YourProfile --action scrape --keywords "python developer,data analyst" --days 14 --pages 3 --jobs 20

# Analyze and rank scraped jobs for your profile
python main.py YourProfile --action analyze-jobs

# Optional dashboard
python main.py YourProfile --action dashboard
# Then open http://localhost:8501
```

---

## Demo

### Dashboard (optional)
Browse, filter, and sort jobs by fit score:

```bash
# Scrape
python main.py Nirajan --action scrape --keywords "python,data" --days 14

# Analyze & rank
python main.py Nirajan --action analyze-jobs

# Launch dashboard
python main.py Nirajan --action dashboard
```

---

## Integrations & Dependencies

### Open Source Integrations
JobQst leverages open source libraries for job discovery:

#### Core Scraping
- [JobSpy](https://github.com/speedyapply/JobSpy) — Multi-site scraping (Indeed, LinkedIn, Glassdoor, ZipRecruiter)
  - Install: `pip install python-jobspy`

#### Web Automation & UI
- [Playwright](https://playwright.dev/) — Browser automation
- [Streamlit](https://streamlit.io/) — Optional dashboard
- [Rich](https://rich.readthedocs.io/) — Terminal output

### Optional
```bash
# Enable JobSpy
pip install python-jobspy

# PostgreSQL (optional)
pip install psycopg2-binary
```

---

## System Architecture

High-level data flow:

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│   Job Sources   │───▶│   Web Scrapers   │───▶│ Matching & Scoring   │
│                 │    │                  │    │                      │
│ • Eluta         │    │ • Playwright     │    │ • Profile signals    │
│ • JobSpy sites  │    │ • Async workers  │    │ • Filtering          │
│ • Others (opt)  │    │ • Rate limiting  │    │ • Ranking            │
└─────────────────┘    └──────────────────┘    └──────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐                                    ┌─────────────────┐
│   Database      │                                    │   Dashboard     │
│ • SQLite        │                                    │ • Streamlit     │
│ • Job storage   │                                    │ • Optional UI   │
└─────────────────┘                                    └─────────────────┘
```

### Core Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Scrapers** | Playwright, AsyncIO, JobSpy | Multi-site job discovery |
| **Matching & Scoring** | Profile-based rules | Fit scoring and ranking |
| **Database** | SQLite/PostgreSQL | Job storage |
| **Dashboard** | Streamlit (optional) | Browsing and filtering |
| **CLI** | Click, Rich | Command-line workflows |

---

## Usage Examples

### Basic Job Scraping
```python
from src.scrapers.parallel_job_scraper import ParallelJobScraper
import asyncio

async def scrape_jobs():
    # Initialize scraper with profile
    profile = {
        "name": "John Doe",
        "keywords": ["python", "data analyst", "software engineer"],
        "location": "Toronto",
        "experience_level": "mid"
    }
    
    scraper = ParallelJobScraper(profile, max_workers=4)
    jobs = await scraper.scrape_jobs(max_jobs_per_keyword=20)
    
  print(f"Found {len(jobs)} jobs!")
    return jobs

# Run the scraper
jobs = asyncio.run(scrape_jobs())
```

### Dashboard Integration (optional)
```python
from src.dashboard.dashboard_manager import DashboardManager

manager = DashboardManager()
manager.start_dashboard()
```

---

## Configuration

### Profile Setup
Create a profile configuration file at `profiles/YourName/YourName.json`:

```json
{
  "name": "Your Name",
  "email": "your.email@example.com",
  "phone": "+1-234-567-8900",
  "location": "Toronto, ON",
  "keywords": [
    "python developer",
    "data analyst", 
    "software engineer",
    "machine learning"
  ],
  "experience_level": "mid",
  "skills": [
    "Python", "JavaScript", "SQL", 
    "React", "Django", "PostgreSQL"
  ],
  "preferences": {
    "remote_work": true,
    "salary_min": 80000,
    "company_size": ["startup", "medium", "large"]
  }
}
```

### Environment Variables
Configure your `.env` file:

```bash
# Core Settings
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///jobs.db
DATABASE_BACKUP_ENABLED=true

# Web Scraping
SCRAPING_DELAY=2
MAX_CONCURRENT_REQUESTS=5
BROWSER_HEADLESS=true

# Dashboard
STREAMLIT_PORT=8501
DASHBOARD_AUTO_REFRESH=30

# (Optional) extras can be added as needed
```

---

## Testing

### Run Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v          # Unit tests
pytest tests/integration/ -v   # Integration tests
pytest tests/e2e/ -v           # End-to-end tests

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Manual Testing
```bash
# Test scraper functionality
python tests/integration/test_optimized_scraper.py

# Test dashboard components
python tests/integration/test_dashboard.py
```

---

## Performance & Monitoring
Basic health checks and logging are included. Performance depends on target sites and network conditions.

---

## Documentation

### References
- [Documentation Hub](docs/README.md)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

### **Quick References**
- **[Installation Guide](docs/DEVELOPER_GUIDE.md#quick-setup)** - Detailed setup instructions
- **[Configuration Reference](.env.example)** - Environment variable guide
- **[CLI Reference](docs/API_REFERENCE.md#cli-commands)** - Command-line usage
- **[Dashboard Guide](docs/TROUBLESHOOTING.md#dashboard-issues)** - Web interface help

---

## Security & Privacy

### Data Protection
- **Local Storage**: All job data stored locally in SQLite database
- **API Security**: Secure API key management with environment variables
- **Browser Isolation**: Separate browser profiles for each user
- **No Data Sharing**: Your data never leaves your local environment

### Best Practices
- Keep your `.env` file secure and never commit it to version control
- Regularly backup your job database using the built-in backup system
- Use strong, unique API keys for external services
- Monitor system logs for unusual activity

---

## Deployment

### Local Development
```bash
# Development mode with hot reload
python main.py YourProfile --action dashboard --debug

# Production mode
python main.py YourProfile --action dashboard --production
```

### Docker Deployment
```bash
# Build container
docker build -t jobqst .

# Run with Docker Compose
docker-compose -f docker-compose.dev.yml up

# Production deployment
docker-compose up -d
```

### Cloud Deployment
Container-based deployment works on most providers (AWS/GCP/Azure/Heroku/VPS).

---

## Troubleshooting

### **Common Issues**

<details>
<summary><strong>🔧 Installation Problems</strong></summary>

```bash
# Python version issues
python --version  # Should be 3.11+

# Dependency conflicts
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Playwright browser issues
playwright install chromium --force
```
</details>

<details>
<summary><strong>🌐 Scraping Issues</strong></summary>

```bash
# Rate limiting
# Increase delays in .env:
SCRAPING_DELAY=5
MAX_CONCURRENT_REQUESTS=2

# Browser crashes
# Try headless mode:
BROWSER_HEADLESS=true

# Network issues
# Check your internet connection and firewall settings
```
</details>

<details>
<summary><strong>Scoring/Ranking Issues</strong></summary>

```bash
# Ensure jobs are scraped first, then run analysis
python main.py YourProfile --action scrape --keywords "python"
python main.py YourProfile --action analyze-jobs
```
</details>

### **Getting Help**
- **[📖 Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Comprehensive troubleshooting
- **[🐛 Issue Tracker](docs/ISSUE_TRACKER.md)** - Known issues and solutions
- **[💬 Discussions](https://github.com/NirajanKhadka/automate_job_idea001/discussions)** - Community support

---

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/YourUsername/automate_job_idea001.git
cd automate_job_idea001

# Create a feature branch
git checkout -b feature/amazing-new-feature

# Install dependencies
pip install -r requirements.txt

# Run tests to ensure everything works
pytest tests/ -v
```

### Contribution Guidelines
1. **Code Quality**: Follow PEP 8 and use `black` for formatting
2. **Testing**: Add tests for new features and ensure all tests pass
3. **Documentation**: Update documentation for any new features
4. **Commit Messages**: Use clear, descriptive commit messages
5. **Pull Requests**: Submit PRs with detailed descriptions

### Areas for Contribution
- 🔍 **New Job Sites**: Add scrapers for additional job boards
- 🤖 **AI Improvements**: Enhance job analysis algorithms
- 🎨 **UI/UX**: Improve dashboard design and user experience
- 🧪 **Testing**: Expand test coverage and add integration tests
- 📖 **Documentation**: Improve guides and add examples

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### **License Summary**
- ✅ **Commercial Use**: Free to use commercially
- ✅ **Modification**: Modify and distribute freely
- ✅ **Distribution**: Share with others
- ✅ **Private Use**: Use privately without restrictions
- ❗ **Liability**: No warranty or liability provided

---

## Acknowledgments

### **Technologies & Libraries**
- **[Playwright](https://playwright.dev/)** - Reliable browser automation
- **[Streamlit](https://streamlit.io/)** - Beautiful web interface framework
- **[Rich](https://rich.readthedocs.io/)** - Beautiful terminal output
- **[Click](https://click.palletsprojects.com/)** - Elegant command-line interfaces

### **Community**
Special thanks to contributors, testers, and users who help make JobQst better.

---

## Support & Contact

### **Getting Help**
- [Documentation](docs/)
- [Issues](https://github.com/NirajanKhadka/automate_job_idea001/issues)
- [Discussions](https://github.com/NirajanKhadka/automate_job_idea001/discussions)
