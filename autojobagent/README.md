# AutoJobAgent

Advanced job application automation system with AI-powered matching and comprehensive job site support.

## Features

- **Multi-site Job Scraping**: Supports Indeed, LinkedIn, Workday, and more
- **AI-Powered Document Tailoring**: Customize resumes and cover letters for each application
- **ATS Integration**: Automated application submission to various ATS platforms
- **Persistent Sessions**: Save login state and application history
- **Interactive CLI**: User-friendly command-line interface
- **Web Dashboard**: Real-time monitoring and control

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/NirajanKhadka/automate_job_idea001.git
   cd automate_job_idea002
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # On Windows:
   .\.venv\Scripts\activate
   # On Unix or MacOS:
   # source .venv/bin/activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

4. Install Playwright browsers:
   ```bash
   playwright install
   ```

## Usage

### Command Line Interface

```bash
# Start in interactive mode
autojobagent --profile myprofile

# Apply to a specific job
autojobagent --profile myprofile apply --url JOB_URL

# Scrape jobs
autojobagent --profile myprofile scrape --query "python developer"

# Start web dashboard
autojobagent --profile myprofile dashboard
```

### Python API

```python
from autojobagent.core.models import UserProfile, JobPosting
from autojobagent.core.job_application.service import JobApplicationService

# Create a profile
profile = UserProfile(
    name="Your Name",
    email="your.email@example.com",
    location="Your Location"
)

# Initialize the service
service = JobApplicationService(profile)


# Create a job posting
job = JobPosting(
    id="job123",
    title="Software Engineer",
    company="Tech Corp",
    location="Remote",
    description="Job description here...",
    url="https://example.com/jobs/123",
    source="test"
)

# Create an application
application = service.create_application(
    job=job,
    resume_path="/path/to/your/resume.pdf"
)
```

## Development

### Setting Up Development Environment

1. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Run linters:
   ```bash
   flake8 autojobagent tests
   black --check autojobagent tests
   isort --check-only autojobagent tests
   mypy autojobagent
   ```

4. Format code:
   ```bash
   black autojobagent tests
   isort autojobagent tests
   ```

## License

MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) before submitting pull requests.
