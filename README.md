# 🤖 AutoJobAgent

*Automated Job Application System*

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AutoJobAgent** is a comprehensive job application automation system that scrapes job listings, analyzes them with AI, and automates applications to 15+ ATS systems.

## 🚀 Quick Start

### 1. Installation
```bash
git clone <repository>
cd automate_job_idea002
pip install -r requirements/requirements.txt
```

### 2. Create Your Profile
```bash
python main.py --action setup
```

### 3. Start Scraping Jobs
```bash
python main.py your_profile_name --action scrape
```

The dashboard will automatically launch at http://localhost:8002

## 🎯 Features

- **Smart Job Scraping**: Extracts real ATS URLs from job sites
- **AI-Powered Analysis**: Job relevance scoring and experience detection
- **Automated Applications**: Supports 15+ ATS systems (Workday, Greenhouse, etc.)
- **Real-Time Dashboard**: Live monitoring and statistics
- **Document Customization**: AI-powered resume and cover letter tailoring

## 📋 Requirements

- Python 3.8+
- Edge or Chromium browser
- 1GB+ free storage space

## 🔧 Usage

```bash
# Interactive mode (recommended)
python main.py your_profile_name

# Direct actions
python main.py your_profile_name --action scrape    # Scrape jobs
python main.py your_profile_name --action apply     # Apply to jobs
python main.py your_profile_name --action dashboard # Launch dashboard
```

## 📊 Dashboard

- **URL**: http://localhost:8002
- **Features**: Real-time job metrics, application tracking, system health
- **Auto-launch**: Starts automatically with scraping operations

## 🆘 Getting Help

- Check the detailed documentation for troubleshooting
- Review system logs for error details
- Ensure all dependencies are installed

## 📄 License

MIT License - see LICENSE file for details.

---

**Status**: Core functionality operational. Ready for use. 