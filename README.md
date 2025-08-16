# 🤖 AutoJobAgent

<div align="center">

**Intelligent Job Application Automation Platform**

*Streamline your job search with AI-powered document generation and automated application submission*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B.svg)](https://streamlit.io/)
[![Playwright](https://img.shields.io/badge/Playwright-Automation-34D399.svg)](https://playwright.dev/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](https://github.com/NirajanKhadka/automate_job_idea001)

[🚀 Quick Start](#-quick-start) • [📖 Documentation](docs/) • [🎥 Demo](#-demo) • [🤝 Contributing](#-contributing)

</div>

---

## 🌟 **What is AutoJobAgent?**

AutoJobAgent is a comprehensive job automation platform that revolutionizes how you search, apply, and manage job applications. Built with modern Python technologies, it combines intelligent web scraping, AI-powered document generation, and automated application submission into one powerful system.

### 🎯 **Perfect For:**
- **Job Seekers** looking to automate repetitive application tasks
- **Career Changers** managing multiple applications across different fields  
- **Professionals** who want AI-generated, personalized application materials
- **Anyone** seeking to optimize their job search workflow and save time

---

## ✨ **Key Features**

<table>
<tr>
<td width="33%">

### 🔍 **Smart Job Discovery**
- **Multi-platform scraping**: Eluta, Indeed, LinkedIn, Monster, JobBank
- **Intelligent filtering**: Location, keywords, experience level
- **Real-time processing**: Parallel job discovery with performance optimization
- **Duplicate detection**: Automatic removal of duplicate listings

</td>
<td width="33%">

### 🤖 **AI-Powered Documents**
- **Gemini API integration**: Professional resume & cover letter generation
- **Job-specific customization**: Tailored content for each application
- **Multiple formats**: PDF, DOCX, and text output
- **Template system**: Customizable document templates

</td>
<td width="33%">

### ⚡ **Automated Applications**
- **ATS integration**: Workday, Greenhouse, BambooHR, and more
- **Browser automation**: Playwright-powered application submission
- **Status tracking**: Real-time application progress monitoring
- **Error handling**: Robust fallback mechanisms

</td>
</tr>
</table>

### 📊 **Management & Analytics**
- **Modern Dashboard**: Streamlit-based web interface with real-time updates
- **Analytics**: Application success rates, job market insights
- **Health Monitoring**: System performance and reliability tracking
- **CLI Interface**: Command-line tools for advanced users

---

## 🚀 **Quick Start**

### **Prerequisites**
- **Python 3.11+** (3.12 recommended)
- **Git** for version control
- **Google API Key** for Gemini AI (document generation)

### **Installation**
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

### **Configuration**
```bash
# Edit your .env file with required settings:
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
DATABASE_URL=sqlite:///jobs.db
STREAMLIT_PORT=8501
```

### **Launch the System**
```bash
# Start the dashboard (recommended for first-time users)
python main.py YourProfile --action dashboard

# Or start scraping directly
python main.py YourProfile --action scrape --keywords "python developer,data analyst"

# Access dashboard at: http://localhost:8501
```

---

## 🎥 **Demo**

### **Dashboard Interface**
The modern Streamlit dashboard provides an intuitive interface for job management:

- **📋 Job Board**: View and filter discovered jobs
- **🎯 Application Tracker**: Monitor application status and progress  
- **📊 Analytics**: Success rates and job market insights
- **⚙️ Configuration**: Manage profiles, keywords, and settings
- **🔄 Real-time Updates**: Live status updates and progress tracking

### **CLI Interface**
Power users can leverage the comprehensive command-line interface:

```bash
# Scrape jobs with specific criteria
python main.py Nirajan --action scrape --keywords "python,data" --location "Toronto"

# Generate documents for a specific job
python main.py Nirajan --action generate --job-id 12345

# Submit applications automatically
python main.py Nirajan --action apply --filter "status:reviewed"

# Launch dashboard
python main.py Nirajan --action dashboard
```

---

## 🔧 **Integrations & Dependencies**

### **🤝 Open Source Integrations**
AutoJobAgent leverages excellent open source libraries to provide comprehensive job search capabilities:

#### **Core Scraping Engine**
- **[JobSpy](https://github.com/speedyapply/JobSpy)** - Multi-site job scraping library
  - *MIT License by Cullen Watson*
  - Enables Indeed, LinkedIn, Glassdoor, ZipRecruiter integration
  - High-performance concurrent scraping with 2k+ stars
  - **Installation**: `pip install python-jobspy`

#### **AI & Document Generation**
- **[Google Gemini API](https://ai.google.dev/)** - Advanced AI for resume/cover letter generation
- **[python-docx](https://python-docx.readthedocs.io/)** - Professional document creation

#### **Web Automation & UI**
- **[Playwright](https://playwright.dev/)** - Modern browser automation
- **[Streamlit](https://streamlit.io/)** - Interactive dashboard framework
- **[Rich](https://rich.readthedocs.io/)** - Beautiful terminal output

### **🚀 Optional Enhancements**
```bash
# Enable JobSpy integration for enhanced scraping
pip install python-jobspy

# Add Redis for high-performance job queuing  
pip install redis

# PostgreSQL for production databases
pip install psycopg2-binary
```

---

## 🏗️ **System Architecture**

AutoJobAgent is built on a modular, scalable architecture:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Job Sources   │───▶│   Web Scrapers   │───▶│   AI Analysis   │
│                 │    │                  │    │                 │
│ • Eluta         │    │ • Playwright     │    │ • Gemini API    │
│ • Indeed        │    │ • Async/Await    │    │ • Job Matching  │
│ • LinkedIn      │    │ • Rate Limiting  │    │ • Filtering     │
│ • Monster       │    │ • Error Handling │    │ • Scoring       │
│ • JobSpy Sites  │    │ • JobSpy Workers │    │ • Smart Parsing │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Database      │    │   ATS Systems    │    │   Dashboard     │
│                 │    │                  │    │                 │
│ • SQLite        │    │ • Workday        │    │ • Streamlit     │
│ • Job Storage   │    │ • Greenhouse     │    │ • Real-time UI  │
│ • Status Track  │    │ • BambooHR       │    │ • Analytics     │
│ • Analytics     │    │ • Auto Submit    │    │ • Controls      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **Core Components**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Scrapers** | Playwright, AsyncIO, JobSpy | Multi-platform job discovery |
| **AI Engine** | Google Gemini API | Document generation & job analysis |
| **Database** | SQLite/PostgreSQL | Data persistence & analytics |
| **Dashboard** | Streamlit | Web-based management interface |
| **ATS Integration** | Browser Automation | Automated application submission |
| **CLI** | Click, Rich | Command-line interface |

---

## 📖 **Usage Examples**

### **Basic Job Scraping**
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

### **Document Generation**
```python
from src.document_modifier.document_modifier import DocumentModifier

# Initialize document generator
doc_gen = DocumentModifier(profile_name="JohnDoe")

# Generate AI-powered cover letter
cover_letter_path = doc_gen.generate_ai_cover_letter(
    job_data={
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "description": "We are looking for a skilled Python developer..."
    },
    profile_data={
        "name": "John Doe",
        "skills": ["Python", "Django", "PostgreSQL"],
        "experience": "5 years"
    }
)

print(f"Cover letter generated: {cover_letter_path}")
```

### **Dashboard Integration**
```python
# Launch dashboard programmatically
from src.dashboard.dashboard_manager import DashboardManager

manager = DashboardManager()
manager.start_dashboard(port=8501, auto_open=True)
```

---

## ⚙️ **Configuration**

### **Profile Setup**
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

### **Environment Variables**
Configure your `.env` file:

```bash
# Core Settings
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# AI Configuration
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro

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

# Optional: OpenAI Integration
OPENAI_API_KEY=your_openai_key_here
```

---

## 🧪 **Testing**

### **Run Test Suite**
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v          # Unit tests
pytest tests/integration/ -v   # Integration tests
pytest tests/e2e/ -v          # End-to-end tests

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### **Manual Testing**
```bash
# Test scraper functionality
python tests/integration/test_optimized_scraper.py

# Test AI document generation
python tests/integration/test_gemini_client.py

# Test dashboard components
python tests/integration/test_dashboard.py
```

---

## 📊 **Performance & Metrics**

### **Benchmarks**
- **Job Discovery**: 50-100 jobs/minute (depends on sites)
- **Document Generation**: 2-5 seconds per document
- **Application Submission**: 30-60 seconds per application
- **Memory Usage**: 200-500MB typical operation
- **Success Rate**: 95%+ for job discovery, 85%+ for applications

### **Monitoring**
The system includes comprehensive monitoring:
- **Health Checks**: Automated system health monitoring
- **Performance Metrics**: Response times, success rates
- **Error Tracking**: Detailed error logging and reporting
- **Analytics Dashboard**: Real-time performance insights

---

## 📚 **Documentation**

### **Complete Documentation**
- **[📖 Documentation Hub](docs/README.md)** - Central documentation index
- **[🏗️ Architecture Guide](docs/ARCHITECTURE.md)** - System design and components
- **[🚀 Developer Guide](docs/DEVELOPER_GUIDE.md)** - Development setup and workflows
- **[📋 API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[🛠️ Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### **Quick References**
- **[Installation Guide](docs/DEVELOPER_GUIDE.md#quick-setup)** - Detailed setup instructions
- **[Configuration Reference](.env.example)** - Environment variable guide
- **[CLI Reference](docs/API_REFERENCE.md#cli-commands)** - Command-line usage
- **[Dashboard Guide](docs/TROUBLESHOOTING.md#dashboard-issues)** - Web interface help

---

## 🛡️ **Security & Privacy**

### **Data Protection**
- **Local Storage**: All job data stored locally in SQLite database
- **API Security**: Secure API key management with environment variables
- **Browser Isolation**: Separate browser profiles for each user
- **No Data Sharing**: Your data never leaves your local environment

### **Best Practices**
- Keep your `.env` file secure and never commit it to version control
- Regularly backup your job database using the built-in backup system
- Use strong, unique API keys for external services
- Monitor system logs for unusual activity

---

## 🚀 **Deployment**

### **Local Development**
```bash
# Development mode with hot reload
python main.py YourProfile --action dashboard --debug

# Production mode
python main.py YourProfile --action dashboard --production
```

### **Docker Deployment**
```bash
# Build container
docker build -t autojobagent .

# Run with Docker Compose
docker-compose -f docker-compose.dev.yml up

# Production deployment
docker-compose up -d
```

### **Cloud Deployment**
The system can be deployed on various cloud platforms:
- **Heroku**: Ready-to-deploy with Procfile
- **AWS/GCP/Azure**: Container-based deployment
- **VPS**: Direct deployment on virtual private servers

---

## 🛠️ **Troubleshooting**

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
<summary><strong>🤖 AI Generation Issues</strong></summary>

```bash
# Check API key
echo $GOOGLE_API_KEY

# Test API connection
python -c "from src.utils.gemini_client import GeminiClient; print(GeminiClient().test_connection())"

# Check API quotas and billing in Google Cloud Console
```
</details>

### **Getting Help**
- **[📖 Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Comprehensive troubleshooting
- **[🐛 Issue Tracker](docs/ISSUE_TRACKER.md)** - Known issues and solutions
- **[💬 Discussions](https://github.com/NirajanKhadka/automate_job_idea001/discussions)** - Community support

---

## 🤝 **Contributing**

We welcome contributions! Here's how to get started:

### **Development Setup**
```bash
# Fork and clone the repository
git clone https://github.com/YourUsername/automate_job_idea001.git
cd automate_job_idea001

# Create a feature branch
git checkout -b feature/amazing-new-feature

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests to ensure everything works
pytest tests/ -v
```

### **Contribution Guidelines**
1. **Code Quality**: Follow PEP 8 and use `black` for formatting
2. **Testing**: Add tests for new features and ensure all tests pass
3. **Documentation**: Update documentation for any new features
4. **Commit Messages**: Use clear, descriptive commit messages
5. **Pull Requests**: Submit PRs with detailed descriptions

### **Areas for Contribution**
- 🔍 **New Job Sites**: Add scrapers for additional job boards
- 🤖 **AI Improvements**: Enhance document generation algorithms
- 🎨 **UI/UX**: Improve dashboard design and user experience
- 🧪 **Testing**: Expand test coverage and add integration tests
- 📖 **Documentation**: Improve guides and add examples

---

## 📈 **Roadmap**

### **Upcoming Features**
- [ ] **Mobile App**: React Native mobile application
- [ ] **Advanced Analytics**: Machine learning insights and predictions
- [ ] **Team Collaboration**: Multi-user support and shared workspaces
- [ ] **API Platform**: REST API for third-party integrations
- [ ] **Cloud Sync**: Optional cloud backup and synchronization

### **Long-term Vision**
- **AI-First Platform**: Advanced machine learning for job matching and career guidance
- **Enterprise Features**: Team management, reporting, and compliance tools
- **Integration Ecosystem**: Plugins for popular career platforms and tools
- **Global Expansion**: Support for international job markets and languages

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### **License Summary**
- ✅ **Commercial Use**: Free to use commercially
- ✅ **Modification**: Modify and distribute freely
- ✅ **Distribution**: Share with others
- ✅ **Private Use**: Use privately without restrictions
- ❗ **Liability**: No warranty or liability provided

---

## 🙏 **Acknowledgments**

### **Technologies & Libraries**
- **[Playwright](https://playwright.dev/)** - Reliable browser automation
- **[Streamlit](https://streamlit.io/)** - Beautiful web interface framework
- **[Google Gemini API](https://cloud.google.com/vertex-ai)** - AI-powered document generation
- **[Rich](https://rich.readthedocs.io/)** - Beautiful terminal output
- **[Click](https://click.palletsprojects.com/)** - Elegant command-line interfaces

### **Community**
Special thanks to all contributors, testers, and users who help make AutoJobAgent better every day!

---

## 📞 **Support & Contact**

### **Getting Help**
- **[📖 Documentation](docs/)** - Comprehensive guides and references
- **[🐛 Issues](https://github.com/NirajanKhadka/automate_job_idea001/issues)** - Bug reports and feature requests
- **[💬 Discussions](https://github.com/NirajanKhadka/automate_job_idea001/discussions)** - Community support and questions

### **Professional Support**
For enterprise support, custom development, or consulting services, please contact the development team.

---

<div align="center">

**🎉 Ready to revolutionize your job search?**

[🚀 Get Started](#-quick-start) • [📖 Read the Docs](docs/) • [⭐ Star on GitHub](https://github.com/NirajanKhadka/automate_job_idea001)

---

*Built with ❤️ by [Nirajan Khadka](https://github.com/NirajanKhadka) and the AutoJobAgent community*

</div>