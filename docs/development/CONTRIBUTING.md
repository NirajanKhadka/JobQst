# Contributing to AutoJobAgent

## Overview
Thank you for your interest in contributing to AutoJobAgent! This guide will help you get started with development, testing, and contributing to the project.

## 🚀 Getting Started

### 1. **Prerequisites**
- Python 3.8+ (3.11+ recommended)
- Git
- Virtual environment (conda or venv)
- Basic knowledge of web scraping and automation

### 2. **Setup Development Environment**
```bash
# Clone the repository
git clone <repository-url>
cd automate_job_idea002

# Create virtual environment
conda create -n auto_job_dev python=3.11
conda activate auto_job_dev

# Install dependencies
pip install -r requirements/requirements-dev.txt

# Install Playwright browsers
playwright install
```

### 3. **Verify Installation**
```bash
# Run basic tests
pytest tests/test_basic.py -v

# Check system health
python -c "from src.agents.system_health_monitor import SystemHealthMonitor; print(SystemHealthMonitor().run_health_checks())"
```

## 📁 Project Structure

### Core Modules
```
src/
├── agents/           # Multi-agent orchestration
├── ats/             # Application tracking systems
├── cli/             # Command-line interface
├── core/            # Core functionality
├── dashboard/       # Web dashboard
├── scrapers/        # Job scraping modules
├── utils/           # Utility functions
└── health_checks/   # System health monitoring
```

### Key Files
- `main.py` - Main entry point
- `src/app.py` - Application runner
- `src/dashboard/api.py` - Dashboard API
- `tests/` - Test suite (499 tests)

## 🧪 Development Workflow

### 1. **Creating a Feature Branch**
```bash
# Create and switch to feature branch
git checkout -b feature/your-feature-name

# Make your changes
# Test your changes
# Commit with descriptive message
git commit -m "feat: add new scraper for example.com"
```

### 2. **Running Tests**
```bash
# Run all tests
pytest tests/ -v

# Run specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run linting
flake8 src/ tests/
black src/ tests/
```

### 3. **Code Quality Standards**

#### Python Style Guide
- Follow PEP 8
- Use type hints
- Write docstrings for all functions
- Keep functions under 50 lines
- Use meaningful variable names

#### Example Code Style
```python
from typing import List, Dict, Optional
from src.core.exceptions import NeedsHumanException


def process_jobs(jobs: List[Dict], profile: str) -> Dict[str, int]:
    """
    Process a list of jobs with the given profile.
    
    Args:
        jobs: List of job dictionaries
        profile: User profile name
        
    Returns:
        Dictionary with processing statistics
        
    Raises:
        NeedsHumanException: When human intervention is required
    """
    if not jobs:
        return {"processed": 0, "failed": 0}
    
    # Process jobs here
    return {"processed": len(jobs), "failed": 0}
```

### 4. **Adding New Scrapers**

#### Create Scraper Class
```python
# src/scrapers/example_scraper.py
from typing import List, Dict
from src.scrapers.base_scraper import BaseScraper


class ExampleScraper(BaseScraper):
    """Scraper for example.com job site."""
    
    def __init__(self, profile: str, **kwargs):
        super().__init__(profile, **kwargs)
        self.site_name = "example"
        self.base_url = "https://example.com"
    
    def scrape_jobs(self, keywords: List[str]) -> List[Dict]:
        """Scrape jobs for given keywords."""
        jobs = []
        for keyword in keywords:
            jobs.extend(self._scrape_keyword(keyword))
        return jobs
    
    def _scrape_keyword(self, keyword: str) -> List[Dict]:
        """Scrape jobs for a single keyword."""
        # Implementation here
        pass
```

#### Register Scraper
```python
# src/scrapers/__init__.py
from .example_scraper import ExampleScraper

SCRAPER_REGISTRY = {
    # ... existing scrapers
    "example": ExampleScraper,
}
```

#### Add Tests
```python
# tests/unit/test_example_scraper.py
import pytest
from src.scrapers.example_scraper import ExampleScraper


class TestExampleScraper:
    def test_scraper_initialization(self):
        scraper = ExampleScraper("test_profile")
        assert scraper.site_name == "example"
    
    def test_scrape_jobs(self):
        scraper = ExampleScraper("test_profile")
        jobs = scraper.scrape_jobs(["python"])
        assert isinstance(jobs, list)
```

### 5. **Adding New ATS Integrations**

#### Create ATS Class
```python
# src/ats/example_ats.py
from src.ats.base_submitter import BaseSubmitter
from src.core.exceptions import NeedsHumanException


class ExampleATSSubmitter(BaseSubmitter):
    """Submitter for Example ATS."""
    
    def __init__(self, profile: str):
        super().__init__(profile)
        self.ats_name = "example"
    
    def submit(self, job_data: Dict) -> bool:
        """Submit application to Example ATS."""
        try:
            # Implementation here
            return True
        except Exception as e:
            raise NeedsHumanException(f"Manual intervention needed: {e}")
```

#### Add Tests
```python
# tests/unit/test_example_ats.py
import pytest
from src.ats.example_ats import ExampleATSSubmitter
from src.core.exceptions import NeedsHumanException


class TestExampleATSSubmitter:
    def test_submitter_initialization(self):
        submitter = ExampleATSSubmitter("test_profile")
        assert submitter.ats_name == "example"
    
    def test_submit_application(self):
        submitter = ExampleATSSubmitter("test_profile")
        job_data = {"title": "Test Job", "company": "Test Company"}
        result = submitter.submit(job_data)
        assert result is True
```

## 🔧 Development Tools

### 1. **Pre-commit Hooks**
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### 2. **Debugging**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use pdb for debugging
import pdb; pdb.set_trace()

# Use ipdb for better debugging
import ipdb; ipdb.set_trace()
```

### 3. **Performance Profiling**
```python
# Profile function performance
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    return result
```

## 🧪 Testing Guidelines

### 1. **Test Categories**
- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Test module interactions
- **E2E Tests**: Test complete workflows

### 2. **Test Naming Convention**
```python
# test_<module>_<function>_<scenario>.py
test_job_scraper_scrape_jobs_success.py
test_database_save_job_duplicate.py
test_dashboard_api_health_check.py
```

### 3. **Test Structure**
```python
class TestJobScraper:
    def setup_method(self):
        """Setup before each test."""
        self.scraper = JobScraper("test_profile")
    
    def teardown_method(self):
        """Cleanup after each test."""
        # Cleanup code
    
    def test_scrape_jobs_success(self):
        """Test successful job scraping."""
        # Arrange
        keywords = ["python"]
        
        # Act
        jobs = self.scraper.scrape_jobs(keywords)
        
        # Assert
        assert len(jobs) > 0
        assert all("title" in job for job in jobs)
    
    def test_scrape_jobs_empty_keywords(self):
        """Test scraping with empty keywords."""
        jobs = self.scraper.scrape_jobs([])
        assert jobs == []
```

### 4. **Mocking External Dependencies**
```python
from unittest.mock import Mock, patch

def test_external_api_call():
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"jobs": []}
        mock_get.return_value.status_code = 200
        
        result = call_external_api()
        assert result == {"jobs": []}
```

## 📝 Documentation

### 1. **Code Documentation**
- Write docstrings for all public functions
- Include type hints
- Document exceptions and edge cases
- Provide usage examples

### 2. **API Documentation**
- Document all API endpoints
- Include request/response examples
- Document error codes
- Keep documentation up to date

### 3. **User Documentation**
- Update user guides for new features
- Add troubleshooting information
- Include configuration examples
- Provide migration guides

## 🚀 Deployment

### 1. **Local Development**
```bash
# Start development server
python -m uvicorn src.dashboard.api:app --reload --port 8002

# Run with debug mode
python main.py --debug
```

### 2. **Testing Deployment**
```bash
# Run full test suite
pytest tests/ --cov=src --cov-report=html

# Check code quality
flake8 src/ tests/
black --check src/ tests/
mypy src/

# Build and test
python setup.py build
```

### 3. **Production Deployment**
```bash
# Install production dependencies
pip install -r requirements/requirements.txt

# Run production server
python -m uvicorn src.dashboard.api:app --host 0.0.0.0 --port 8002
```

## 🤝 Contributing Process

### 1. **Issue Reporting**
- Use GitHub issues for bug reports
- Include steps to reproduce
- Provide system information
- Attach relevant logs

### 2. **Feature Requests**
- Describe the feature clearly
- Explain the use case
- Suggest implementation approach
- Consider backward compatibility

### 3. **Pull Request Process**
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Update documentation
5. Submit pull request
6. Address review comments
7. Merge after approval

### 4. **Code Review Guidelines**
- Review for functionality
- Check code quality
- Verify test coverage
- Ensure documentation updates
- Test the changes locally

## 🎯 Development Priorities

### 1. **High Priority**
- Bug fixes
- Security updates
- Performance improvements
- Critical feature requests

### 2. **Medium Priority**
- New scraper integrations
- ATS system enhancements
- Dashboard improvements
- Documentation updates

### 3. **Low Priority**
- Nice-to-have features
- UI/UX improvements
- Code refactoring
- Additional test coverage

## 📞 Getting Help

### 1. **Development Questions**
- Check existing documentation
- Search GitHub issues
- Ask in discussions
- Contact maintainers

### 2. **Technical Support**
- Provide detailed error messages
- Include system information
- Share relevant code snippets
- Describe expected vs actual behavior

### 3. **Community Guidelines**
- Be respectful and helpful
- Follow the code of conduct
- Provide constructive feedback
- Help other contributors

## 🏆 Recognition

### 1. **Contributor Levels**
- **Contributor**: First pull request merged
- **Regular Contributor**: 5+ pull requests
- **Core Contributor**: Significant contributions
- **Maintainer**: Project maintenance responsibilities

### 2. **Contributor Hall of Fame**
- GitHub contributors page
- Release notes acknowledgments
- Project documentation credits

---

**Thank you for contributing to AutoJobAgent!** 🚀

Your contributions help make job automation more accessible and effective for everyone.

---

**Last Updated**: June 2025  
**Version**: 2.0  
**Maintainer**: Development Team 