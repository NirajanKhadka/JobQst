# AutoJobAgent API Reference

## Overview
This document provides comprehensive API documentation for the AutoJobAgent system, including the dashboard API, scraper interfaces, and utility functions.

## 🚀 Dashboard API

### Base URL
```
http://localhost:8002
```

### Health Check
**Endpoint**: `GET /api/health`

**Description**: Check system health status

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-24T10:30:00Z",
  "checks": {
    "database_connection": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "disk_space": {
      "status": "healthy",
      "message": "Sufficient disk space available"
    },
    "memory_usage": {
      "status": "healthy",
      "message": "Memory usage: 45%"
    }
  }
}
```

**Status Codes**:
- `200`: System healthy
- `503`: System unhealthy

### Jobs API

#### Get All Jobs
**Endpoint**: `GET /api/jobs`

**Query Parameters**:
- `limit` (optional): Number of jobs to return (default: 50)
- `offset` (optional): Number of jobs to skip (default: 0)
- `status` (optional): Filter by status (applied, pending, rejected)
- `site` (optional): Filter by job site (eluta, indeed, linkedin)

**Response**:
```json
{
  "jobs": [
    {
      "id": "job_123",
      "title": "Python Developer",
      "company": "Tech Corp",
      "location": "Toronto, ON",
      "url": "https://example.com/job/123",
      "site": "eluta",
      "status": "pending",
      "date_posted": "2025-06-20",
      "experience_level": "entry",
      "confidence_score": 0.85
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

#### Get Job by ID
**Endpoint**: `GET /api/jobs/{job_id}`

**Response**:
```json
{
  "id": "job_123",
  "title": "Python Developer",
  "company": "Tech Corp",
  "location": "Toronto, ON",
  "url": "https://example.com/job/123",
  "site": "eluta",
  "status": "pending",
  "date_posted": "2025-06-20",
  "experience_level": "entry",
  "confidence_score": 0.85,
  "description": "Full job description...",
  "requirements": ["Python", "Django", "SQL"],
  "salary_range": "$60,000 - $80,000",
  "application_url": "https://apply.example.com/123"
}
```

#### Update Job Status
**Endpoint**: `PUT /api/jobs/{job_id}/status`

**Request Body**:
```json
{
  "status": "applied",
  "notes": "Application submitted successfully"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Job status updated successfully"
}
```

### Statistics API

#### Get System Statistics
**Endpoint**: `GET /api/stats`

**Response**:
```json
{
  "total_jobs": 150,
  "jobs_by_status": {
    "pending": 100,
    "applied": 30,
    "rejected": 20
  },
  "jobs_by_site": {
    "eluta": 80,
    "indeed": 40,
    "linkedin": 30
  },
  "jobs_by_experience": {
    "entry": 120,
    "mid": 20,
    "senior": 10
  },
  "scraping_stats": {
    "last_scrape": "2025-06-24T09:00:00Z",
    "jobs_found": 25,
    "success_rate": 0.95
  }
}
```

#### Get Scraping History
**Endpoint**: `GET /api/stats/scraping-history`

**Query Parameters**:
- `days` (optional): Number of days to look back (default: 7)

**Response**:
```json
{
  "history": [
    {
      "date": "2025-06-24",
      "jobs_found": 25,
      "success_rate": 0.95,
      "sites_scraped": ["eluta", "indeed"]
    },
    {
      "date": "2025-06-23",
      "jobs_found": 30,
      "success_rate": 0.92,
      "sites_scraped": ["eluta"]
    }
  ]
}
```

### System API

#### Get System Information
**Endpoint**: `GET /api/system/info`

**Response**:
```json
{
  "version": "2.0.0",
  "python_version": "3.11.0",
  "platform": "Windows-10-10.0.26100",
  "uptime": "2 hours 30 minutes",
  "memory_usage": "45%",
  "disk_usage": "30%",
  "active_profiles": ["default", "test"]
}
```

#### Get Available Profiles
**Endpoint**: `GET /api/system/profiles`

**Response**:
```json
{
  "profiles": [
    {
      "name": "default",
      "email": "user@example.com",
      "location": "Toronto, ON",
      "skills": ["Python", "JavaScript", "SQL"],
      "created": "2025-06-20T10:00:00Z"
    }
  ]
}
```

## 🔧 Scraper API

### Simplified Scraper Architecture

The AutoJobAgent system has been simplified to use only two scraping methods for better maintainability and performance:

#### 1. Simple Sequential Method
**Purpose**: Basic one-at-a-time scraping for reliability and simplicity
**Use Case**: When you need consistent, reliable scraping with minimal complexity
**Characteristics**: 
- Single-threaded processing
- Sequential job processing
- Lower resource usage
- Higher reliability
- Suitable for smaller job volumes

#### 2. Multi-Worker Method  
**Purpose**: Master worker controlling other workers with a single producer
**Use Case**: When you need high-performance scraping with parallel processing
**Characteristics**:
- Master worker coordinates multiple worker processes
- Single producer feeds jobs to workers
- Parallel job processing
- Higher resource usage
- Suitable for larger job volumes

### Scraper Interface

#### Base Scraper Class
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseScraper(ABC):
    """Base class for all job scrapers."""
    
    def __init__(self, profile: str, **kwargs):
        self.profile = profile
        self.site_name = ""
        self.base_url = ""
    
    @abstractmethod
    def scrape_jobs(self, keywords: List[str]) -> List[Dict]:
        """Scrape jobs for given keywords."""
        pass
    
    def get_job_details(self, job_url: str) -> Dict:
        """Get detailed information for a specific job."""
        pass
```

#### Simplified Scraper Methods

**Simple Sequential Scraping**
```python
from src.cli.handlers.scraping_handler import ScrapingHandler

# Initialize scraper with profile
scraping_handler = ScrapingHandler(profile)

# Run simple sequential scraping
success = scraping_handler.run_scraping(mode="simple")
```

**Multi-Worker Scraping**
```python
from src.core.job_processor_queue import create_job_processor_queue

# Create multi-worker queue (2 workers by default)
queue = create_job_processor_queue(
    profile_name="default",
    num_workers=2,
    dashboard_callback=your_callback_function
)

# Start the multi-worker system
queue.start()

# Add jobs to the queue
queue.add_jobs_from_scraping(scraped_jobs)

# Wait for completion
queue.wait_for_completion()
```

#### Available Scrapers
```python
from src.scrapers import SCRAPER_REGISTRY

# Get available scrapers
scrapers = list(SCRAPER_REGISTRY.keys())
# ['eluta', 'eluta_optimized', 'eluta_multi_ip', 'indeed', 'linkedin', 'monster', 'jobbank']

# Create scraper instance
scraper_class = SCRAPER_REGISTRY['eluta']
scraper = scraper_class('default_profile')
```

### Scraper Configuration

#### Human Behavior Configuration
```python
from src.scrapers.human_behavior import HumanBehaviorConfig

config = HumanBehaviorConfig(
    between_jobs=(3.0, 5.0),      # Random delay between jobs
    between_clicks=(1.0, 2.0),    # Delay between clicks
    popup_wait=3.0,               # Wait time for popups
    mouse_acceleration=True,      # Natural mouse movement
    save_cookies=True,            # Persist session
    cookie_file="cookies.json"
)
```

#### Simplified Scraper Settings
```python
# Simple Sequential Settings
simple_settings = {
    'max_pages_per_keyword': 5,    # Pages to scrape
    'max_jobs_per_keyword': 50,    # Jobs per keyword
    'timeout': 30000,              # 30 seconds
    'retry_attempts': 3,           # Retry failed jobs
    'headless': False              # Show browser
}

# Multi-Worker Settings
multi_worker_settings = {
    'num_workers': 2,              # Number of worker processes
    'max_workers': 1,              # Browser contexts per worker
    'max_pages_per_keyword': 5,    # Pages to scrape
    'max_jobs_per_keyword': 50,    # Jobs per keyword
    'timeout': 30000,              # 30 seconds
    'retry_attempts': 3,           # Retry failed jobs
    'headless': False              # Show browser
}
```

### Job Processor Queue API

#### Queue Management
```python
from src.core.job_processor_queue import JobProcessorQueue, JobTask

# Create queue with 2 workers
queue = JobProcessorQueue(
    profile_name="default",
    num_workers=2,
    dashboard_callback=your_callback
)

# Start the queue
queue.start()

# Add individual job
job_task = JobTask(
    job_url="https://example.com/job/123",
    job_id="job_123",
    title="Python Developer",
    company="Tech Corp",
    location="Toronto, ON",
    search_keyword="python"
)
queue.add_job(job_task)

# Add multiple jobs from scraping
queue.add_jobs_from_scraping(scraped_jobs)

# Get statistics
stats = queue.get_stats()

# Wait for completion
queue.wait_for_completion(timeout=300)  # 5 minutes

# Stop the queue
queue.stop()
```

#### Dashboard Callback
```python
def dashboard_callback(data):
    """Callback function for real-time dashboard updates."""
    if data.get('type') == 'job_processing_stats':
        stats = data.get('stats', {})
        queue_size = data.get('queue_size', 0)
        print(f"📊 Worker Stats: {stats.get('successful', 0)}/{stats.get('total_processed', 0)} successful, Queue: {queue_size}")
```

### Scraping Metrics

#### Metrics Collection
```python
from src.scraping.metrics import ScrapingMetrics

metrics = ScrapingMetrics()

# Record scraping event
metrics.record_scraping_event('eluta', 'python', 25, 0.95)

# Get metrics
stats = metrics.get_scraping_stats()

# Finalize metrics
metrics.finalize()
```

#### Metrics Data Structure
```python
@dataclass
class ScrapingMetrics:
    start_time: float
    end_time: Optional[float] = None
    total_jobs_found: int = 0
    unique_jobs_added: int = 0
    duplicates_filtered: int = 0
    errors_encountered: int = 0
    sites_scraped: int = 0
    keywords_processed: int = 0
    average_jobs_per_keyword: float = 0.0
    scraping_rate_per_minute: float = 0.0
    data_quality_score: float = 0.0
    keyword_performance: Dict[str, Dict] = field(default_factory=dict)
```

## 📊 Database API

### Database Interface

#### ModernJobDatabase
```python
from src.core.job_database import ModernJobDatabase

db = ModernJobDatabase()

# Save job
job_data = {
    'title': 'Python Developer',
    'company': 'Tech Corp',
    'url': 'https://example.com/job/123',
    'site': 'eluta'
}
db.save_job(job_data)

# Get jobs
jobs = db.get_jobs(limit=50, offset=0)

# Update job status
db.update_job_status('job_123', 'applied')

# Get statistics
stats = db.get_job_stats()
```

#### Database Methods

**Save Job**
```python
def save_job(self, job_data: Dict) -> str:
    """Save job to database. Returns job ID."""
```

**Get Jobs**
```python
def get_jobs(self, limit: int = 50, offset: int = 0, 
             status: Optional[str] = None, 
             site: Optional[str] = None) -> List[Dict]:
    """Get jobs with optional filtering."""
```

**Update Job Status**
```python
def update_job_status(self, job_id: str, status: str, 
                     notes: Optional[str] = None) -> bool:
    """Update job status. Returns success boolean."""
```

**Get Job Statistics**
```python
def get_job_stats(self) -> Dict:
    """Get comprehensive job statistics."""
```

## 🎯 ATS (Application Tracking System) API

### Base Submitter Interface
```python
from src.ats.base_submitter import BaseSubmitter
from src.core.exceptions import NeedsHumanException

class BaseSubmitter(ABC):
    """Base class for ATS submitters."""
    
    def __init__(self, profile: str):
        self.profile = profile
        self.ats_name = ""
    
    @abstractmethod
    def submit(self, job_data: Dict) -> bool:
        """Submit application to ATS. Returns success boolean."""
        pass
```

### Available ATS Submitters

#### Workday Submitter
```python
from src.ats.workday import WorkdaySubmitter

submitter = WorkdaySubmitter('default_profile')
success = submitter.submit(job_data)
```

#### Greenhouse Submitter
```python
from src.ats.greenhouse import GreenhouseSubmitter

submitter = GreenhouseSubmitter('default_profile')
success = submitter.submit(job_data)
```

#### CSV Submitter
```python
from src.ats.csv_applicator import CSVJobApplicator

submitter = CSVJobApplicator('default_profile')
success = submitter.submit(job_data)
```

### ATS Configuration
```python
ats_config = {
    'workday': {
        'base_url': 'https://company.workday.com',
        'timeout': 30000,
        'retry_attempts': 3
    },
    'greenhouse': {
        'base_url': 'https://boards-api.greenhouse.io',
        'api_key': 'your_api_key'
    },
    'csv': {
        'output_file': 'applications.csv',
        'include_timestamp': True
    }
}
```

## 🛠️ Utility API

### Job Helpers
```python
from src.utils.job_helpers import (
    generate_job_hash,
    extract_job_details,
    validate_job_data,
    clean_job_text
)

# Generate unique job hash
job_hash = generate_job_hash(job_data)

# Extract job details from URL
details = extract_job_details(job_url)

# Validate job data
is_valid = validate_job_data(job_data)

# Clean job text
clean_text = clean_job_text(raw_text)
```

### Profile Helpers
```python
from src.utils.profile_helpers import (
    get_available_profiles,
    load_profile,
    save_profile,
    validate_profile
)

# Get available profiles
profiles = get_available_profiles()

# Load profile
profile_data = load_profile('default')

# Save profile
save_profile('default', profile_data)

# Validate profile
is_valid = validate_profile(profile_data)
```

### File Operations
```python
from src.utils.file_operations import (
    save_jobs_to_json,
    load_jobs_from_json,
    save_jobs_to_csv,
    backup_database
)

# Save jobs to JSON
save_jobs_to_json(jobs, 'jobs.json')

# Load jobs from JSON
jobs = load_jobs_from_json('jobs.json')

# Save jobs to CSV
save_jobs_to_csv(jobs, 'jobs.csv')

# Backup database
backup_database('backup.db')
```

### Job Analysis
```python
from src.utils.job_analyzer import JobAnalyzer

analyzer = JobAnalyzer()

# Analyze single job
analysis = analyzer.analyze_job(job_data)

# Analyze jobs in batch
analyses = analyzer.analyze_jobs_batch(jobs)

# Get recommendations
recommendations = analyzer.get_recommendations(profile_data)
```

### Job Data Processing
```python
from src.utils.job_data_consumer import JobDataConsumer
from src.utils.job_data_enhancer import JobDataEnhancer

# Consume and process jobs
consumer = JobDataConsumer()
processed_jobs = consumer.consume_jobs(jobs)
filtered_jobs = consumer.filter_jobs(jobs, criteria)
statistics = consumer.get_statistics(jobs)

# Enhance job data
enhancer = JobDataEnhancer()
enhanced_jobs = enhancer.enhance_job(job_data)
salary_info = enhancer.extract_salary_info(job_description)
experience_level = enhancer.extract_experience_level(job_description)
relevance_score = enhancer.calculate_relevance_score(job_data, profile_data)
```

## 🔍 Health Check API

### Health Check Interface
```python
from src.agents.system_health_monitor import SystemHealthMonitor

monitor = SystemHealthMonitor()

# Run all health checks
status = monitor.run_health_checks()

# Run specific health check
db_status = monitor.check_database_connection()
disk_status = monitor.check_disk_space()
memory_status = monitor.check_memory_usage()
```

### Health Check Modules
```python
from src.health_checks import (
    database,
    disk,
    memory,
    network,
    browser,
    ollama
)

# Database health
db_health = database.check_database_connection()

# Disk health
disk_health = disk.check_disk_space()

# Memory health
memory_health = memory.check_memory_usage()

# Network health
network_health = network.check_network_connectivity()

# Browser health
browser_health = browser.check_browser_installation()

# Ollama health
ollama_health = ollama.check_ollama_service()
```

## 🚨 Error Handling

### Exception Types
```python
from src.core.exceptions import (
    NeedsHumanException,
    ScrapingException,
    DatabaseException,
    ConfigurationException
)

# Human intervention required
raise NeedsHumanException("CAPTCHA detected, manual intervention needed")

# Scraping error
raise ScrapingException("Failed to extract job URL")

# Database error
raise DatabaseException("Database connection failed")

# Configuration error
raise ConfigurationException("Invalid profile configuration")
```

### Error Response Format
```json
{
  "error": {
    "type": "NeedsHumanException",
    "message": "CAPTCHA detected, manual intervention needed",
    "code": "HUMAN_INTERVENTION_REQUIRED",
    "timestamp": "2025-06-24T10:30:00Z",
    "details": {
      "job_url": "https://example.com/job/123",
      "site": "eluta",
      "screenshot_path": "/tmp/captcha_screenshot.png"
    }
  }
}
```

## 📝 Configuration API

### Configuration Management
```python
from src.core.config_manager import ConfigManager

config_manager = ConfigManager()

# Load configuration
config = config_manager.load_config()

# Save configuration
config_manager.save_config(config)

# Get specific setting
dashboard_port = config_manager.get_setting('dashboard.port')

# Update setting
config_manager.update_setting('dashboard.port', 8003)
```

### Configuration Schema
```json
{
  "dashboard": {
    "port": 8002,
    "host": "0.0.0.0",
    "debug": false
  },
  "database": {
    "path": "data/jobs.db",
    "backup_interval": 24
  },
  "scraping": {
    "max_workers": 1,
    "timeout": 30000,
    "retry_attempts": 3
  },
  "ats": {
    "default_submitter": "csv",
    "auto_submit": false
  }
}
```

## 🔐 Authentication & Security

### API Security
- All API endpoints require proper authentication
- Rate limiting is implemented
- Input validation is enforced
- CORS is configured for web dashboard

### Rate Limiting
```
- Dashboard API: 100 requests per minute
- Scraper API: 10 requests per minute
- Health Check API: 60 requests per minute
```

### Input Validation
```python
from pydantic import BaseModel, validator

class JobData(BaseModel):
    title: str
    company: str
    url: str
    site: str
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith('http'):
            raise ValueError('URL must start with http')
        return v
```

## 📊 Monitoring & Logging

### Logging Configuration
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### Metrics Collection
```python
from src.scraping.metrics import ScrapingMetrics

metrics = ScrapingMetrics()

# Record scraping event
metrics.record_scraping_event('eluta', 'python', 25, 0.95)

# Get metrics
stats = metrics.get_scraping_stats()
```

---

**Last Updated**: June 2025  
**Version**: 2.0  
**Maintainer**: Development Team 