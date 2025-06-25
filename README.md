# AutoJobAgent

AutoJobAgent is a job application automation system designed to streamline the process of finding and applying to jobs online. It provides a unified interface for job scraping, application tracking, and dashboard monitoring.

## Features
- Automated job scraping from multiple job boards
- Resume and cover letter customization
- Application status tracking
- Dashboard for monitoring job search progress
- Modular architecture for easy extension

## Quick Start

### 1. Installation
```bash
git clone <repository-url>
cd automate_job_idea002
pip install -r requirements/requirements.txt
```

### 2. Profile Setup
```bash
python main.py --action setup
```

### 3. Start Scraping
```bash
python main.py <YourProfileName> --action scrape
```

### 4. Launch Dashboard
```bash
python main.py <YourProfileName> --action dashboard
# Access at: http://localhost:8002
```

## System Requirements
- Python 3.8+
- Chromium-based browser (Edge or Chrome recommended)

## Documentation
- For advanced configuration and troubleshooting, see the `docs/` directory.
- For developer notes and internal logic, see project markdown files (not included in this public README).

## License
MIT License

---

*This README is safe for public sharing and does not include proprietary or sensitive internal logic.* 