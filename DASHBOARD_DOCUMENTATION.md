# JobQst Dashboard - Complete Documentation

**Version:** 2.0  
**Last Updated:** October 4, 2025  
**Status:** Production Ready ✅

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Dashboard Architecture](#dashboard-architecture)
4. [User Guide - Features & Tabs](#user-guide)
5. [Developer Guide](#developer-guide)
6. [Troubleshooting](#troubleshooting)
7. [Performance & Best Practices](#performance-best-practices)
8. [API Reference](#api-reference)

---

## Overview

JobQst Dashboard is a modern, interactive web application built with Dash and Plotly that provides comprehensive job search intelligence, application tracking, and market insights. It transforms raw job data into actionable intelligence using AI-powered analysis.

### Key Features

- 🎯 **AI-Powered Job Ranking** - Smart matching based on your profile
- 🔍 **Intelligent Job Browser** - LinkedIn-style job exploration with filters
- 📊 **Application Tracker** - Kanban-style pipeline management
- 📈 **Market Insights** - Salary trends, location analysis, skill demands
- 🤖 **Automated Scraping** - Real-time job discovery from 4+ sources
- 📝 **Interview Prep** - AI-generated practice questions and tips
- 🔖 **Smart Bookmarks** - Save and organize favorite jobs
- 📦 **Batch Processing** - AI analysis with caching for speed

### Tech Stack

- **Frontend:** Dash (Plotly), Dash Bootstrap Components
- **Backend:** Python 3.11+, FastAPI (legacy)
- **Database:** DuckDB (primary), SQLite (fallback)
- **AI/ML:** OpenAI GPT-4, LangChain
- **Job Sources:** JobSpy (Indeed, LinkedIn, Glassdoor, ZipRecruiter)
- **Styling:** Bootstrap 5 (Cyborg theme), Font Awesome 6

---

## Getting Started

### Prerequisites

```bash
# Required
- Python 3.11+
- Conda environment: auto_job
- OpenAI API key (in .env file)

# Optional
- Git for version control
- VS Code for development
```

### Quick Start

```bash
# 1. Activate the conda environment (CRITICAL!)
conda activate auto_job

# 2. Launch dashboard with your profile
python main.py YourProfileName --action dashboard

# 3. Open browser to http://localhost:8050
# Dashboard loads automatically with your profile data
```

### Alternative Launch Methods

```bash
# Using VS Code task (Recommended)
Ctrl+Shift+P → "Tasks: Run Task" → "Start Dash Dashboard"

# Direct launch (for development)
python src/dashboard/dash_app/app.py

# PowerShell script
.\launch_dashboard.ps1
```

### First-Time Setup

```bash
# 1. Create a new profile
python create_new_profile.py

# 2. Run JobSpy pipeline to get initial data
python main.py YourProfileName --action jobspy-pipeline \
  --jobspy-preset canada_comprehensive \
  --database-type duckdb \
  --enable-cache

# 3. Launch dashboard
python main.py YourProfileName --action dashboard
```

---

## Dashboard Architecture

### Component Structure

```
src/dashboard/dash_app/
├── app.py                      # Main application entry point
├── callbacks/                  # All callback logic (17 files)
│   ├── job_browser_callbacks.py    # Job browsing & filtering
│   ├── job_tracker_callbacks.py    # Application tracking
│   ├── ranked_jobs_callbacks.py    # AI ranking & sorting
│   ├── market_insights_callbacks.py # Analytics & trends
│   ├── scraping_callbacks.py       # Job discovery control
│   └── ...
├── layouts/                    # UI layouts (12 tabs)
│   ├── job_browser_layout.py      # LinkedIn-style browser
│   ├── job_tracker_layout.py      # Kanban board
│   ├── ranked_jobs_layout.py      # Home/ranking view
│   ├── market_insights_layout.py  # Analytics dashboards
│   └── ...
├── components/                 # Reusable UI components
│   ├── enhanced_job_card.py       # Job display cards
│   ├── streamlined_sidebar.py     # Navigation sidebar
│   ├── duplicate_detector.py      # Duplicate job detection
│   ├── performance_optimization.py # Caching & speed
│   └── ...
├── utils/                      # Helper utilities
│   ├── data_loader.py             # Database queries
│   ├── job_intelligence.py        # AI enhancements
│   ├── cache_manager.py           # Query caching
│   └── ...
└── assets/                     # Static files (CSS, JS)
    └── custom_styles.css
```

### Data Flow Architecture

```
User Interaction
    ↓
Dash Callbacks (callbacks/)
    ↓
Data Services (utils/data_loader.py)
    ↓
Database Layer (DuckDB/SQLite)
    ↓
AI Enhancement (utils/job_intelligence.py)
    ↓
Cached Results (cache_manager.py)
    ↓
UI Components (layouts/ + components/)
    ↓
Browser Display
```

### Key Design Patterns

1. **Service-Oriented Architecture**
   - Clear separation between UI, business logic, and data
   - Reusable services for common operations
   - Centralized data loading and caching

2. **Component-Based UI**
   - Modular, reusable components
   - Consistent styling and behavior
   - Easy to maintain and extend

3. **Callback Isolation**
   - Each tab has its own namespace (e.g., `browser-`, `tracker-`)
   - Prevents ID conflicts and duplicate outputs
   - Makes debugging easier

4. **Performance-First Design**
   - Multi-level caching (dashboard queries, AI results, HTML)
   - Intelligent batch processing
   - Lazy loading of expensive operations

---

## User Guide

### Navigation

The dashboard uses a **streamlined sidebar** with the following tabs:

#### 🏠 Home (Ranked Jobs)
**Purpose:** Your personalized job feed with AI-powered ranking

**Features:**
- Top 50 jobs ranked by fit score
- Filter by match score, location type, salary
- Quick stats: total jobs, high matches, RCIP jobs, remote opportunities
- One-click actions: bookmark, apply, view details
- Real-time filtering and sorting

**Best For:** Daily job hunting, finding best matches quickly

---

#### 🔍 Job Browser
**Purpose:** LinkedIn-style job exploration and discovery

**Features:**
- **Search Bar:** Search titles, companies, descriptions
- **Advanced Filters:**
  - Match score range (0-100%)
  - Salary range (40K-150K)
  - Location types: Remote, Hybrid, On-site
  - RCIP city jobs only
  - Date posted: 24h, 7d, 30d, all
- **Sorting Options:**
  - Best Match (fit score)
  - Most Recent
  - Highest Salary
  - Company Name
  - RCIP Priority
- **Enhanced Job Cards:**
  - Top keywords prominently displayed
  - AI summary preview
  - Match score badge
  - RCIP indicator
- **Detailed Modal View:**
  - Full AI summary
  - Top 8 keywords
  - Skill gap analysis (matched vs. missing)
  - Full job description
  - Similar jobs recommendations
- **Duplicate Detection:** Automatically identifies and flags duplicate postings

**Best For:** Exploratory job search, comparing opportunities, finding patterns

---

#### 📋 Job Tracker
**Purpose:** Application pipeline management (Kanban-style)

**Features:**
- **5-Stage Pipeline:**
  1. **Interested** - Jobs you're considering
  2. **Applied** - Applications sent
  3. **Interview** - Active interviews
  4. **Offer** - Offers received
  5. **Rejected** - Closed applications
- **Quick Stats:**
  - Total applications
  - Active interviews
  - Pending responses
  - Success rate
- **Application Cards:**
  - Job title, company, location
  - Application date
  - Match score
  - Quick notes preview
- **Activity Timeline:** Recent application activity
- **Deadline Tracker:** Upcoming interviews and response deadlines

**Best For:** Tracking applications, managing interviews, staying organized

---

#### 📊 Market Insights
**Purpose:** Data-driven market analysis and trends

**Features:**
- **Salary Analysis:**
  - Average, median, range by location
  - Salary distribution charts
  - Top-paying companies
- **Location Trends:**
  - Jobs by city/province
  - Remote vs. on-site distribution
  - RCIP city opportunities
- **Skills Analysis:**
  - Most in-demand skills
  - Skill frequency charts
  - Emerging technologies
- **Company Insights:**
  - Top hiring companies
  - Company job counts
  - Industry distribution
- **Time Series:**
  - Job posting trends over time
  - Match score evolution
  - Application success rates

**Best For:** Understanding job market, salary negotiation, skill planning

---

#### 🤖 Scraper Control
**Purpose:** Automated job discovery and collection

**Features:**
- **Multi-Site Scraping:**
  - Indeed, LinkedIn, Glassdoor, ZipRecruiter
  - Parallel workers for speed
  - Smart deduplication
- **JobSpy Presets:**
  - Canada: `canada_comprehensive`, `tech_hubs_canada`
  - USA: `usa_comprehensive`, `usa_tech_hubs`
  - Remote: `remote_focused`
- **Configuration:**
  - Custom locations
  - Job titles/keywords
  - Results per site
  - Date ranges
- **Status Monitoring:**
  - Real-time progress
  - Jobs found per site
  - Error handling
  - Performance metrics
- **Scheduling:** Set up recurring scrapes

**Best For:** Building job database, staying updated, automated discovery

---

#### 📝 Interview Prep (Coming Soon)
**Purpose:** AI-powered interview preparation

**Planned Features:**
- Company-specific questions
- Role-based practice questions
- AI interview simulator
- Answer tips and strategies
- Industry insights

---

#### ⚙️ Settings
**Purpose:** Profile and dashboard configuration

**Features:**
- **Profile Management:**
  - View/edit profile details
  - Skills and experience
  - Preferences (location, salary, work type)
  - Resume upload
- **Dashboard Settings:**
  - Theme selection
  - Auto-refresh interval
  - Default filters
  - Notification preferences
- **API Configuration:**
  - OpenAI API key
  - Rate limits
  - Model selection
- **Data Management:**
  - Export jobs to CSV/JSON
  - Import existing data
  - Clear cache
  - Database optimization

**Best For:** Customization, maintenance, data management

---

### Common Workflows

#### Workflow 1: Daily Job Hunt
```
1. Open Dashboard → Home tab loads automatically
2. Check "High Match Jobs" stat (80%+ matches)
3. Filter by Remote/Hybrid if needed
4. Click job cards to view details
5. Bookmark interesting jobs
6. Mark as "Applied" when you apply
7. Switch to Job Tracker to manage pipeline
```

#### Workflow 2: Exploratory Search
```
1. Go to Job Browser tab
2. Enter keywords in search (e.g., "python machine learning")
3. Adjust match score range (60%+ for broader search)
4. Sort by "Highest Salary" or "Most Recent"
5. Use RCIP filter if immigration-focused
6. View similar jobs for each interesting posting
7. Export results to CSV for external analysis
```

#### Workflow 3: Market Research
```
1. Go to Market Insights tab
2. Check salary trends for your role
3. Identify top-paying companies
4. Review in-demand skills
5. Compare locations (remote vs. on-site opportunities)
6. Use insights for salary negotiation or skill planning
```

#### Workflow 4: Application Management
```
1. After applying, go to Job Tracker
2. Drag job card from "Interested" to "Applied"
3. Add notes (application date, contact person)
4. Set deadline for response
5. Move to "Interview" when contacted
6. Track interview dates in timeline
7. Update to "Offer" or "Rejected" when decided
```

---

## Developer Guide

### Adding a New Tab

```python
# 1. Create layout file
# src/dashboard/dash_app/layouts/my_new_layout.py

import dash_bootstrap_components as dbc
from dash import html

def create_my_new_layout():
    return dbc.Container([
        html.H2("My New Feature"),
        html.Div(id="my-new-content")
    ])
```

```python
# 2. Create callbacks file
# src/dashboard/dash_app/callbacks/my_new_callbacks.py

from dash import Input, Output, callback

def register_my_new_callbacks(app, profile_name: str):
    @app.callback(
        Output("my-new-content", "children"),
        Input("my-new-trigger", "n_clicks")
    )
    def update_content(n_clicks):
        # Your logic here
        return "Updated content"
```

```python
# 3. Register in app.py

# Import
from src.dashboard.dash_app.layouts.my_new_layout import create_my_new_layout
from src.dashboard.dash_app.callbacks.my_new_callbacks import register_my_new_callbacks

# Add to sidebar navigation (in streamlined_sidebar.py)
dbc.NavLink([
    html.I(className="fas fa-star me-2"),
    "My New Feature"
], href="/mynew", id="nav-mynew", active="exact")

# Add to page routing callback
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/mynew":
        return create_my_new_layout()
    # ... other routes
```

### Component Naming Convention

**CRITICAL:** Use unique namespaces to avoid ID conflicts!

```python
# ✅ CORRECT - Namespaced IDs
{tab_name}-{component_type}-{specific_id}

# Examples:
"browser-job-modal-title"        # Job Browser modal title
"tracker-stats-card"             # Job Tracker stats card
"insights-salary-chart"          # Market Insights salary chart

# ❌ WRONG - Generic IDs (causes conflicts)
"job-modal-title"                # Multiple tabs might use this!
"stats-card"                     # Too generic
"chart"                          # Too generic
```

### Working with Database

```python
from src.core.duckdb_database import DuckDBJobDatabase

# Get database instance
db = DuckDBJobDatabase(profile_name)

# Execute queries
jobs = db.execute_query("SELECT * FROM jobs WHERE fit_score >= 80")

# Use pandas for analysis
import pandas as pd
df = pd.DataFrame(jobs)
```

### Adding AI Features

```python
from src.dashboard.dash_app.utils.job_intelligence import (
    enhance_job_with_intelligence,
    find_similar_jobs
)
from src.core.user_profile_manager import ModernUserProfileManager

# Load profile
profile_mgr = ModernUserProfileManager()
profile = profile_mgr.get_profile(profile_name)

# Enhance single job
enhanced_job = enhance_job_with_intelligence(job, profile)

# Features added:
# - ai_summary: Brief description of what they're looking for
# - top_keywords: Most important terms (8-10)
# - skill_gap: Matched vs. missing skills with percentages

# Find similar jobs
similar = find_similar_jobs(enhanced_job, all_jobs, top_n=5)
```

### Performance Optimization

```python
# Use caching for expensive queries
from src.dashboard.dash_app.utils.cache_manager import DashboardCache

cache = DashboardCache()

@cache.cached_query(ttl_minutes=5)
def expensive_query(profile_name):
    # This result is cached for 5 minutes
    return db.execute_query("COMPLEX QUERY")

# Clear cache when data changes
cache.clear_all()
```

### Testing Components

```python
# Create test file: tests/dashboard/test_my_component.py

import pytest
from src.dashboard.dash_app.layouts.my_new_layout import create_my_new_layout

def test_layout_creation():
    layout = create_my_new_layout()
    assert layout is not None
    # Add more assertions

# Run tests
pytest tests/dashboard/ -v
```

---

## Troubleshooting

### Common Issues

#### 1. Dashboard Won't Start

**Symptoms:** Error on launch, blank page, connection refused

**Solutions:**
```bash
# Check environment
conda activate auto_job
python --version  # Should be 3.11+

# Check for port conflicts
netstat -ano | findstr "8050"  # Windows
lsof -i :8050                   # Mac/Linux

# Kill existing processes
Get-Process python | Where-Object {$_.Path -like "*miniconda3*"} | Stop-Process -Force

# Check dependencies
pip install -r requirements.txt

# Try direct launch
python src/dashboard/dash_app/app.py
```

#### 2. No Data Showing

**Symptoms:** Empty tables, "0 jobs found", blank charts

**Solutions:**
```bash
# Verify database has data
python quick_db_check.py

# Check profile is loaded
# Look at browser console (F12) for errors

# Reload data
python main.py YourProfileName --action jobspy-pipeline \
  --jobspy-preset canada_comprehensive

# Clear cache
rm -rf src/dashboard/dash_app/logs/cache/
```

#### 3. Duplicate Callback Error

**Symptoms:** Console error "Duplicate callback outputs"

**Solutions:**
- This should be fixed as of Oct 4, 2025
- Check that all modal IDs use proper namespacing
- See `DUPLICATE_CALLBACK_FIX.md` for details

#### 4. Slow Performance

**Symptoms:** Long loading times, freezing, timeouts

**Solutions:**
```python
# Enable caching
from src.dashboard.dash_app.components.performance_optimization import enable_caching
enable_caching(app)

# Reduce data size
# Limit queries to recent jobs only
WHERE date_posted >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)

# Check database size
# Large databases (>1GB) may need optimization
```

#### 5. AI Features Not Working

**Symptoms:** No summaries, no skill gaps, "AI unavailable"

**Solutions:**
```bash
# Check .env file has OpenAI key
OPENAI_API_KEY=sk-...

# Verify API credits
# Check OpenAI dashboard

# Check rate limits
# Wait and retry after rate limit cooldown

# Disable AI as fallback
# Dashboard still works without AI features
```

### Debug Mode

```bash
# Run with debug logging
export DASH_DEBUG=True  # Linux/Mac
$env:DASH_DEBUG="True"  # Windows PowerShell

python main.py YourProfileName --action dashboard

# Check logs
tail -f src/dashboard/dash_app/logs/dashboard.log
```

### Browser Console

```
Press F12 in browser → Console tab

Look for:
- JavaScript errors (red)
- Network errors (failed requests)
- Callback errors (duplicate outputs, missing IDs)
```

---

## Performance Best Practices

### For Users

1. **Use Filters Wisely**
   - Start with broad filters, narrow down
   - Avoid loading all jobs at once
   - Use date filters to limit results

2. **Enable Auto-Refresh Sparingly**
   - Disable if not needed (saves resources)
   - Increase interval for slower connections

3. **Clear Cache Periodically**
   - Settings → Data Management → Clear Cache
   - Do this after major data updates

4. **Export Large Datasets**
   - Use CSV export for analysis
   - Don't try to view 1000+ jobs in browser

### For Developers

1. **Query Optimization**
   ```python
   # ✅ GOOD - Specific, indexed columns
   SELECT id, title, company, fit_score 
   FROM jobs 
   WHERE fit_score >= 80 
   ORDER BY date_posted DESC 
   LIMIT 50

   # ❌ BAD - Unfiltered, SELECT *
   SELECT * FROM jobs
   ```

2. **Use Caching Aggressively**
   ```python
   @cache.cached_query(ttl_minutes=5)
   def get_stats(profile_name):
       # Expensive aggregation
       return results
   ```

3. **Lazy Load Heavy Components**
   ```python
   # Load charts only when tab is active
   @app.callback(
       Output("expensive-chart", "figure"),
       Input("tab-selector", "value")
   )
   def load_chart(active_tab):
       if active_tab == "analytics":
           return create_expensive_chart()
       return {}
   ```

4. **Batch Database Operations**
   ```python
   # ✅ GOOD - Single query
   jobs = db.execute_query("SELECT * FROM jobs WHERE id IN (?)", job_ids)

   # ❌ BAD - Loop
   for job_id in job_ids:
       job = db.execute_query("SELECT * FROM jobs WHERE id = ?", job_id)
   ```

---

## API Reference

### Key Functions

#### Data Loading
```python
from src.dashboard.dash_app.utils.data_loader import load_jobs_for_dashboard

jobs = load_jobs_for_dashboard(
    profile_name: str,
    filters: dict = None,
    limit: int = 50,
    use_cache: bool = True
)
```

#### Job Enhancement
```python
from src.dashboard.dash_app.utils.job_intelligence import enhance_job_with_intelligence

enhanced = enhance_job_with_intelligence(
    job: dict,
    profile: dict = None
) -> dict

# Returns job with:
# - ai_summary (str)
# - top_keywords (list)
# - skill_gap (dict)
```

#### Component Creation
```python
from src.dashboard.dash_app.components.enhanced_job_card import create_enhanced_job_card

card = create_enhanced_job_card(
    job: dict,
    view_mode: str = "card"  # "card" or "list"
) -> dbc.Card
```

### Environment Variables

```bash
# .env file
OPENAI_API_KEY=sk-...              # Required for AI features
DASHBOARD_PORT=8050                # Default port
DASHBOARD_DEBUG=False              # Debug mode
CACHE_ENABLED=True                 # Enable caching
CACHE_TTL_MINUTES=5                # Cache lifetime
DATABASE_TYPE=duckdb               # duckdb or sqlite
```

### Configuration Files

```python
# src/dashboard/dash_app/config.py
DASHBOARD_CONFIG = {
    "theme": "cyborg",              # Bootstrap theme
    "refresh_interval": 30000,      # ms
    "jobs_per_page": 50,
    "cache_enabled": True,
    "ai_enabled": True
}
```

---

## Changelog

### Version 2.0 (October 4, 2025)
- ✅ Fixed duplicate callback outputs error
- ✅ Namespaced all modal IDs (browser- vs tracker-)
- ✅ Improved job browser filters
- ✅ Added duplicate job detection
- ✅ Enhanced performance with multi-level caching

### Version 1.5 (October 2025)
- Added Job Browser tab with LinkedIn-style UI
- Added Job Tracker with Kanban board
- Integrated JobSpy for multi-site scraping
- Improved AI summaries and skill gap analysis

### Version 1.0 (September 2025)
- Initial release
- Basic job listing and analytics
- DuckDB integration
- Profile management

---

## Support & Contributing

### Getting Help

1. Check this documentation first
2. Review `TROUBLESHOOTING.md`
3. Check GitHub issues
4. Contact maintainers

### Contributing

```bash
# 1. Fork the repository
# 2. Create feature branch
git checkout -b feature/my-new-feature

# 3. Make changes following conventions
# 4. Test thoroughly
pytest tests/dashboard/ -v

# 5. Submit PR with description
```

### Code Style

- Follow PEP 8 for Python
- Use type hints where possible
- Document complex functions
- Add tests for new features
- Use meaningful variable names

---

## Additional Resources

- **Project Documentation:** See root-level `*.md` files
- **Architecture Guide:** `.github/copilot-instructions.md`
- **Development Standards:** `docs/DEVELOPMENT_STANDARDS.md`
- **JobSpy Config:** `src/config/jobspy_integration_config.py`
- **Database Schema:** `src/core/schema.sql`

---

**Last Updated:** October 4, 2025  
**Maintained By:** JobQst Team  
**License:** MIT
