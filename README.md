# JobQst - Intelligent Job Discovery & Automation Platform

<div align="center">

**🎯 Profile-Driven Job Discovery** - Automated job searching, intelligent matching, and comprehensive analytics with modern dashboard interfaces.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Playwright](https:/### **Getting Help**
- **[🐛 Issue Tracker](https://github.com/NirajanKhadka/automate_job_idea001/issues)** - Special thanks to all contributors, testers, and users who make JobQst better every day!eport bugs and feature requests
- **[💬 Discussions](https://github.com/NirajanKhadka/automate_job_idea001/discussions)** - Community support and Q&A.shields.io/badge/Playwright-Automation-34D399.svg)](https://playwright.dev/)
[![Dash](https://img.shields.io/badge/Dash-Dashboard-00D4AA.svg)](https://dash.plotly.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-316192.svg)](https://www.postgresql.org/)

[🚀 Quick Start](#-quick-start) • [📖 Documentation](docs/) • [🔧 Setup](#installation) • [🤝 Contributing](#-contributing)

</div>

---

## What is JobQst?

JobQst is a comprehensive job discovery and automation platform that streamlines job searching across multiple sources, provides intelligent job-profile matching, and offers powerful analytics through modern dashboard interfaces. Built with a modular, scalable architecture supporting both CLI automation and interactive web interfaces.

### 🎯 **Perfect For:**
- **Job Seekers** who want automated, intelligent job discovery and tracking
- **Career Professionals** managing applications across multiple platforms with AI-powered insights  
- **Tech Workers** seeking opportunities in Canada/USA with location-specific search capabilities
- **Anyone** who wants to optimize their job search with automation and analytics

### ✨ **Current Features (August 2025)**
- ✅ **Multi-Source Scraping** - JobSpy integration (Indeed, LinkedIn, Glassdoor, ZipRecruiter) + Eluta.ca
- ✅ **PostgreSQL Database** - Robust data storage with profile-based organization
- ✅ **Dash Dashboard** - Interactive web interface with analytics and visualizations
- ✅ **Intelligent Matching** - AI-powered job-profile compatibility scoring
- ✅ **Parallel Processing** - Concurrent scraping with configurable worker limits

---

## Key Features

<table>
<tr>
<td width="33%">

### 🔍 Multi-Source Job Discovery
- **Primary Engine**: JobSpy (Indeed, LinkedIn, Glassdoor, ZipRecruiter)
- **Fallback**: Eluta.ca for Canadian opportunities
- **Parallel Workers**: Configurable concurrent scraping
- **Smart Deduplication**: AI-powered duplicate detection
- **Geographic Focus**: USA & Canada job markets

</td>
<td width="33%">

### 🧠 Intelligent Analysis & Matching
- **Profile-Based Scoring**: AI job-profile compatibility assessment
- **Skills Gap Analysis**: Identify missing skills and suggestions
- **Resume Processing**: Auto profile creation from PDF resumes  
- **Location Intelligence**: Remote/hybrid/onsite categorization
- **Experience Matching**: Level-appropriate job recommendations

</td>
<td width="33%">

### 📊 Modern Dashboard Interface
- **Dash Analytics**: Interactive web dashboard with Plotly visualizations
- **Real-time Monitoring**: Live scraping and processing status
- **Profile Management**: Visual configuration and management
- **Job Analytics**: Charts, filters, and insights
- **Multi-tab Interface**: Jobs, Analytics, Processing, System monitoring

</td></tr>
</table>

---

## Quick Start

### Prerequisites
- **Python 3.11+** (3.11.11 tested and recommended)
- **Git** for repository cloning
- **Conda** (recommended) or Python venv
- **PostgreSQL** (optional, SQLite used by default)

### Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/NirajanKhadka/automate_job_idea001.git
cd automate_job_idea001

# 2. Create conda environment (recommended)
conda create -n auto_job python=3.11
conda activate auto_job

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install browser automation
playwright install chromium

# 5. Setup environment (optional)
cp .env.example .env
# Edit .env with your configuration if needed
```

### Basic Usage

```bash
# Make sure you're in the auto_job environment
conda activate auto_job

# 1. Scrape jobs using JobSpy (modern pipeline)
python main.py YourProfile --action jobspy-pipeline --jobspy-preset canada_comprehensive

# 2. Analyze and score scraped jobs
python main.py YourProfile --action analyze-jobs

# 3. Launch interactive dashboard
python main.py YourProfile --action dashboard

# 4. Alternative: Direct Dash app launch
python src/dashboard/dash_app/app.py
```

### Available Actions

| Action | Description | Example |
|--------|-------------|---------|
| `jobspy-pipeline` | **Modern scraping** with JobSpy integration | `--jobspy-preset usa_comprehensive` |
| `scrape` | **Legacy scraping** with Eluta fallback | `--keywords "python,data"` |
| `analyze-jobs` | **AI analysis** and scoring of scraped jobs | Auto-processes all jobs in profile |
| `dashboard` | **Dash interface** for browsing and management | Opens web dashboard |
| `interactive` | **CLI menu** for guided workflows | Interactive command selection |

## Architecture Overview

JobQst follows a modular, event-driven architecture designed for scalability and maintainability:

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│   Job Sources   │───▶│  Scraping Engine │───▶│   Analysis Pipeline  │
│                 │    │                  │    │                      │
│ • JobSpy Sites  │    │ • Parallel       │    │ • Profile Matching   │
│ • Eluta.ca      │    │   Workers        │    │ • AI Scoring         │
│ • Custom APIs   │    │ • Rate Limiting  │    │ • Skills Analysis    │
└─────────────────┘    └──────────────────┘    └──────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│    Database     │    │   Event System   │    │     Dashboards       │
│                 │    │                  │    │                      │
│ • PostgreSQL    │    │ • Local Events   │    │ • Dash (main)        │
│ • SQLite        │    │ • Process        │    │ • CLI Tools          │
│ • Profile-based │    │   Monitoring     │    │                      │
└─────────────────┘    └──────────────────┘    └──────────────────────┘
```

### Core Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Scraping Engine** | JobSpy, Playwright, AsyncIO | Multi-source job discovery with parallel processing |
| **Analysis Pipeline** | Custom AI, Transformers | Profile-based job scoring and skills analysis |
| **Database Layer** | PostgreSQL/SQLite | Profile-organized job storage |
| **Dashboard Suite** | Dash (Plotly) | Interactive web interface with analytics |
| **CLI System** | Click, Rich | Automation-friendly command-line operations |
| **Event System** | Custom Event Bus | Coordinated processing and real-time updates |

## Usage Examples

### 1. Modern JobSpy Pipeline (Recommended)
```bash
# USA comprehensive search
python main.py YourProfile --action jobspy-pipeline --jobspy-preset usa_comprehensive

# Canada tech hubs focus
python main.py YourProfile --action jobspy-pipeline --jobspy-preset tech_hubs_canada

# Custom configuration
python main.py YourProfile --action jobspy-pipeline \
  --sites indeed,linkedin \
  --max-jobs-total 500 \
  --experience-level mid_level
```

### 2. Profile-Based Job Analysis
```python
# After scraping, analyze job compatibility
from src.core.user_profile_manager import UserProfileManager
from src.analysis.job_analyzer import JobAnalyzer

# Load profile
profile_manager = UserProfileManager()
profile = profile_manager.load_profile("YourProfile")

# Analyze jobs
analyzer = JobAnalyzer(profile)
analyzed_jobs = analyzer.analyze_all_jobs()

# Top matches
top_jobs = [job for job in analyzed_jobs if job.fit_score > 0.8]
print(f"Found {len(top_jobs)} high-fit jobs!")
```

### 3. Dashboard Integration
```bash
# Quick dashboard launch
python main.py YourProfile --action dashboard

# Direct Dash app launch
python src/dashboard/dash_app/app.py
```

### 4. Custom Profile Creation
```json
// profiles/YourProfile/YourProfile.json
{
  "name": "Your Name",
  "location": "Toronto, ON",
  "experience_level": "senior",
  "keywords": ["python", "machine learning", "data science"],
  "skills": ["Python", "SQL", "Docker", "AWS"],
  "preferences": {
    "remote_work": true,
    "salary_min": 100000,
    "company_types": ["tech", "startup"]
  },
  "education": {
    "degree": "Bachelor's in Computer Science",
    "certifications": ["AWS Certified", "Google Cloud"]
  }
}
```

## Configuration & Environment

### Environment Setup
```bash
# Essential environment variables (.env)
DATABASE_URL=postgresql://user:password@localhost/jobqst  # or sqlite:///jobs.db
SCRAPING_DELAY=2
MAX_CONCURRENT_WORKERS=4
BROWSER_HEADLESS=true

# Dashboard configuration
DASH_PORT=8050

# JobSpy integration
JOBSPY_MAX_WORKERS=3
JOBSPY_SITES=indeed,linkedin,glassdoor,ziprecruiter

# Optional AI features
OPENAI_API_KEY=your_key_here  # for enhanced analysis
```

### Profile Configuration
Create profiles in `profiles/YourName/YourName.json`:

```json
{
  "name": "Your Name",
  "email": "your.email@example.com",
  "location": "Toronto, ON",
  "experience_level": "senior",
  "keywords": ["python developer", "machine learning", "devops"],
  "skills": ["Python", "Docker", "Kubernetes", "AWS", "PostgreSQL"],
  "preferences": {
    "remote_work": true,
    "salary_min": 90000,
    "company_size": ["startup", "medium"],
    "industries": ["technology", "fintech", "healthtech"]
  },
  "education": {
    "degree": "Computer Science",
    "level": "bachelor"
  },
  "certifications": ["AWS Certified Solutions Architect"]
}
```

### JobSpy Presets
Choose from pre-configured search strategies:

| Preset | Description | Coverage |
|--------|-------------|----------|
| `usa_comprehensive` | Full USA job market coverage | All major cities |
| `canada_comprehensive` | Complete Canadian market | All provinces |
| `tech_hubs_canada` | Canadian tech centers only | Toronto, Vancouver, Montreal |
| `usa_tech_hubs` | USA tech hotspots | SF, NYC, Seattle, Austin |
| `remote_focused` | Remote-first opportunities | Global remote positions |

## Testing & Development

### Running Tests
```bash
# Activate environment
conda activate auto_job

# Run full test suite
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v             # Integration tests
pytest tests/dashboard/ -v               # Dashboard tests

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Test specific components
pytest tests/scrapers/test_jobspy_integration.py -v
```

### Development Workflow
```bash
# 1. Install development dependencies
pip install -r requirements-dev.txt

# 2. Code formatting (if available)
black src/ tests/
isort src/ tests/

# 3. Run linting (if configured)
flake8 src/ tests/

# 4. Test your changes
pytest tests/ -v

# 5. Manual testing
python main.py TestProfile --action jobspy-pipeline --jobspy-preset tech_hubs_canada
```

### Available VS Code Tasks
Use `Ctrl+Shift+P` → "Tasks: Run Task":

- **Run all tests (pytest)** - Execute full test suite
- **Start Dash Dashboard** - Launch Dash analytics interface

## Deployment & Production

### Local Production Setup
```bash
# 1. Production environment setup
conda create -n jobqst_prod python=3.11
conda activate jobqst_prod
pip install -r requirements.txt

# 2. PostgreSQL database setup (recommended for production)
createdb jobqst_production
export DATABASE_URL=postgresql://user:password@localhost/jobqst_production

# 3. Run database migrations
python -c "from src.core.database_migration import run_migrations; run_migrations()"

# 4. Start services
python main.py ProductionProfile --action dashboard  # Dashboard
python main.py ProductionProfile --action jobspy-pipeline  # Background scraping
```

### Docker Deployment
```bash
# Development environment
docker-compose -f docker-compose.dev.yml up

# Production deployment
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs jobqst-app
```

### Cloud Deployment Options

#### Option 1: Traditional VPS/VM
- Deploy using Docker Compose
- PostgreSQL + Redis for production scale
- Nginx reverse proxy for dashboard access
- Systemd services for background processing

#### Option 2: Container Platforms
- **AWS ECS/Fargate**: Container orchestration
- **Google Cloud Run**: Serverless container deployment  
- **Azure Container Instances**: Managed container hosting
- **Railway/Render**: Simple deployment with built-in PostgreSQL

#### Option 3: Self-Hosted
```bash
# Systemd service example (Ubuntu/CentOS)
sudo cp deploy/jobqst.service /etc/systemd/system/
sudo systemctl enable jobqst
sudo systemctl start jobqst
```

## Documentation & Resources

### 📚 **Core Documentation**
- **[📖 Documentation Hub](docs/README.md)** - Complete documentation index
- **[🏗️ Architecture Guide](docs/ARCHITECTURE.md)** - System design and patterns
- **[ Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### 🔗 **Quick References**
- **[⚡ CLI Reference](docs/API_REFERENCE.md#cli-commands)** - All command-line options

---

## Troubleshooting

### **Common Issues**

<details>
<summary><strong>🔧 Environment & Installation</strong></summary>

```bash
# Python version issues
python --version  # Should be 3.11+
conda list python  # Check conda environment

# Dependency conflicts
conda activate auto_job
pip install -r requirements.txt --force-reinstall

# Browser automation issues
playwright install chromium --force
```
</details>

<details>
<summary><strong>🌐 Scraping Problems</strong></summary>

```bash
# JobSpy integration issues
pip install python-jobspy --upgrade

# Rate limiting or blocks
# Edit .env:
SCRAPING_DELAY=5
MAX_CONCURRENT_WORKERS=2

# Browser automation failures
export BROWSER_HEADLESS=false  # Debug mode
```
</details>

<details>
<summary><strong>💾 Database Issues</strong></summary>

```bash
# PostgreSQL connection problems
export DATABASE_URL=sqlite:///jobs.db  # Fallback to SQLite

# Migration issues
python -c "from src.core.database_migration import reset_database; reset_database()"

# Profile database corruption
python main.py YourProfile --action health-check
```
</details>

<details>
<summary><strong>📊 Dashboard Problems</strong></summary>

```bash
# Port conflicts
export DASH_PORT=8051

# Dashboard won't start
python src/dashboard/dash_app/app.py

# Missing data in dashboard
python main.py YourProfile --action analyze-jobs  # Ensure jobs are processed
```
</details>

### **Getting Help**
- **[� Issue Tracker](https://github.com/NirajanKhadka/automate_job_idea001/issues)** - Report bugs and feature requests
- **[💬 Discussions](https://github.com/NirajanKhadka/automate_job_idea001/discussions)** - Community support and Q&A
- **[📧 Contact](mailto:contact@jobqst.dev)** - Direct support (if available)

---

## Contributing

We welcome contributions! JobQst is actively developed and always looking for improvements.

### 🚀 **Development Setup**
```bash
# 1. Fork and clone
git clone https://github.com/YourUsername/automate_job_idea001.git
cd automate_job_idea001

# 2. Create development environment
conda create -n jobqst_dev python=3.11
conda activate jobqst_dev
pip install -r requirements.txt
pip install -r requirements-dev.txt  # if available

# 3. Create feature branch
git checkout -b feature/amazing-improvement

# 4. Run tests to ensure everything works
pytest tests/ -v
```

### 📋 **Contribution Areas**

#### 🔍 **Scraping & Data**
- Add new job sites (Monster, CareerBuilder, etc.)
- Improve JobSpy integration and error handling
- Enhance data extraction and cleaning algorithms
- Implement smart rate limiting and anti-detection

#### 🧠 **AI & Analytics** 
- Improve job-profile matching algorithms
- Add skills gap analysis and career recommendations
- Enhance resume parsing and profile generation

#### 🎨 **Dashboard & UI**
- Improve Dash components and visualizations  
- Improve mobile responsiveness and accessibility
- Create interactive analytics and reporting features

#### 🔧 **Infrastructure & DevOps**
- Add Docker improvements and orchestration
- Implement CI/CD pipelines and automated testing
- Add monitoring, logging, and alerting systems

### 🎯 **Priority Features**
1. **Enhanced Dash Dashboard** - Improve the current web interface
2. **Database Connection Fixes** - Resolve PostgreSQL connectivity issues
3. **Improved Job Analysis** - Better job matching algorithms
4. **Mobile-Friendly Interface** - Responsive dashboard design

### 📝 **Guidelines**
- **Code Quality**: Follow PEP 8, use type hints, add docstrings
- **Testing**: Add tests for new features (pytest framework)
- **Documentation**: Update docs for any new functionality
- **Commits**: Use clear, descriptive commit messages
- **Pull Requests**: Include detailed descriptions and test evidence

### 🏆 **Recognition**
Contributors are recognized in our [CONTRIBUTORS.md](CONTRIBUTORS.md) file and release notes.

---

## License & Legal

### **MIT License**
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for full details.

**License Summary:**
- ✅ **Commercial Use** - Use freely in commercial projects
- ✅ **Modification** - Modify and distribute your changes
- ✅ **Distribution** - Share with others freely
- ✅ **Private Use** - Use privately without restrictions
- ❗ **Liability** - No warranty or liability provided
- ❗ **Attribution** - Must include original license notice

### **Third-Party Licenses**
JobQst integrates with several open-source projects:
- **[JobSpy](https://github.com/speedyapply/JobSpy)** - MIT License
- **[Playwright](https://github.com/microsoft/playwright-python)** - Apache 2.0
- **[Dash](https://github.com/plotly/dash)** - MIT License

---

## Acknowledgments & Credits

### **🙏 Special Thanks**
- **[JobSpy Project](https://github.com/speedyapply/JobSpy)** - Excellent multi-site scraping foundation
- **[Dash & Plotly Team](https://dash.plotly.com/)** - Powerful analytics dashboard framework
- **[Playwright Developers](https://playwright.dev/)** - Robust browser automation

### **🏗️ Built With**
- **Core Language**: Python 3.11+
- **Web Scraping**: JobSpy, Playwright
- **Database**: PostgreSQL, SQLite
- **Dashboard**: Dash (Plotly)
- **CLI/UI**: Rich, Click
- **Testing**: Pytest

### **🌟 Community**
Special thanks to all contributors, testers, and users who make JobLens better every day!

---

<div align="center">

### **Ready to revolutionize your job search? Get started now!**

[🚀 **Quick Start**](#-quick-start) • [📖 **Documentation**](docs/) • [🤝 **Contribute**](#-contributing)

**Made with ❤️ for better job discovery**

</div>
