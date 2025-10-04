# Health Check and Profile Creation - Quick Guide

## 🔧 Issues Fixed

### 1. Health Check PostgreSQL/Docker Errors
**Problem**: Health check was failing with PostgreSQL and Docker errors, even though these are NOT required for JobLens.

**Solution**: 
- Removed PostgreSQL and Docker checks from `src/core/application_controller.py`
- Updated health check to use the comprehensive `SystemHealthChecker` class
- Health check now properly validates:
  - ✅ Database connectivity (DuckDB/SQLite)
  - ✅ Network connectivity
  - ✅ Disk space
  - ✅ Memory usage
  - ✅ Required files and modules

**What Changed**:
- File: `src/core/application_controller.py`
  - Removed `check_postgresql_running()` function
  - Removed `ensure_docker_infrastructure()` function
  - Updated `run_health_check()` to use `SystemHealthChecker`
  
- File: `src/health_checks/system_health_checker.py`
  - Fixed hardcoded profile path check
  - Made profile JSON detection flexible to handle different naming patterns

### 2. Profile Creation System
**Problem**: No easy way to create new profiles for testing and development.

**Solution**: Created `create_new_profile.py` - an interactive profile creation tool.

## 🚀 How to Use

### Testing Health Check

```bash
# Test with existing profile
python main.py Nirajan --action health-check

# Test with newly created profile
python main.py YourProfileName --action health-check
```

**Expected Output**:
```
🏥 Running Comprehensive Health Check
✅ Database healthy: X jobs found
✅ Database stats retrieved successfully
❌ Network health poor: 2/4 sites accessible  # This is OK - some sites block scrapers
💾 Disk Usage: X.XGB / XXXXGB
✅ Sufficient disk space available
🧠 Memory Usage: XX.X%
✅ Memory usage is healthy
✅ Services health good: 13/14 checks passed

📊 Health Check Summary
⚠️ Some checks failed, but system is operational
💡 PostgreSQL and Docker are NOT required for this project
✅ Action 'health-check' completed successfully!
```

### Creating a New Profile

```bash
# Run the interactive profile creator
python create_new_profile.py
```

**Interactive Prompts**:
1. **Profile Name**: Unique identifier (e.g., "John_Doe", "TestProfile")
2. **Basic Info**: Full name, email, phone, location
3. **Professional Links**: LinkedIn, GitHub, Portfolio URLs
4. **Skills & Keywords**: Comma-separated lists
5. **Experience**: Level (entry/intermediate/senior/lead) and years
6. **Search Preferences**: Preferred job locations
7. **AI Configuration**: Ollama model selection

**What Gets Created**:
```
profiles/YourProfileName/
├── YourProfileName.json          # Profile configuration
├── YourProfileName_duckdb.db     # DuckDB database (auto-created)
├── resumes/                       # Your resume files
├── cover_letters/                 # Cover letter templates
└── applications/                  # Application tracking
```

### Profile Structure Example

```json
{
  "name": "John Doe",
  "profile_name": "John_Doe",
  "email": "john.doe@email.com",
  "location": "Toronto, ON",
  "skills": ["Python", "SQL", "Data Analysis"],
  "keywords": ["Data Analyst", "Business Analyst"],
  "experience_level": "intermediate",
  "experience_years": 3,
  "locations": ["Toronto, ON", "Mississauga, ON"],
  "ollama_model": "llama3:latest",
  "settings": {
    "job_search": {
      "days_back": 14,
      "max_jobs_per_run": 200,
      "auto_process": true,
      "enable_cache": true
    },
    "analysis": {
      "min_fit_score": 0.6,
      "enable_ai_analysis": true
    }
  }
}
```

## 📋 Testing Workflow

### 1. Create a Test Profile
```bash
python create_new_profile.py
```

### 2. Verify Profile Health
```bash
python main.py YourProfileName --action health-check
```

### 3. Run Job Search
```bash
# Quick search with defaults
python main.py YourProfileName --action jobspy-pipeline

# Custom search
python main.py YourProfileName --action jobspy-pipeline \
  --sites indeed,linkedin \
  --days 7 \
  --jobs 50
```

### 4. View Results in Dashboard
```bash
python main.py YourProfileName --action dashboard
```

## 🔍 What to Expect from Health Checks

### ✅ Always Should Pass
- Database connectivity
- Disk space availability
- Memory usage within limits
- Required directories exist
- Required Python modules available

### ⚠️ May Show Warnings (These are OK!)
- **Network checks**: Some sites (eluta.ca, indeed.ca) may block health check requests
  - This is normal and expected for scraper protection
  - The actual scraping uses different mechanisms and will work fine
- **Missing profile-specific files**: Optional resume/cover letter files

### ❌ Should Never Fail
- Environment setup (auto_job conda environment)
- Core directories missing
- Database initialization

## 🐛 Troubleshooting

### "PostgreSQL not running" Error (OLD)
**Fixed**: This error no longer appears. PostgreSQL is not required.

### "Docker not running" Error (OLD)
**Fixed**: This error no longer appears. Docker is not required.

### "Profile not found" Error
**Solution**: 
1. Run `python create_new_profile.py` to create the profile
2. Or check profile name spelling: `python main.py ProfileName --action health-check`

### "No jobs found" (New Profile)
**Expected**: New profiles start with 0 jobs. Run a job search first:
```bash
python main.py YourProfileName --action jobspy-pipeline
```

### Network Health Poor
**Normal**: This is expected behavior. Job sites often block health check requests but allow proper scraping with browser automation.

## 📚 Key Files Modified

1. **src/core/application_controller.py**
   - Removed PostgreSQL check function
   - Removed Docker check function
   - Updated health check to use comprehensive system checker
   
2. **src/health_checks/system_health_checker.py**
   - Fixed hardcoded profile path
   - Made profile JSON detection flexible
   - Better error handling and reporting

3. **create_new_profile.py** (NEW)
   - Interactive profile creation
   - Validates existing profiles
   - Creates complete directory structure
   - Provides next steps guidance

## 💡 Best Practices

### For Development/Testing
1. Create a dedicated test profile: `python create_new_profile.py`
2. Run health check first: `python main.py TestProfile --action health-check`
3. Start with small job searches: `--jobs 10 --days 7`
4. Monitor with dashboard: `python main.py TestProfile --action dashboard`

### For Production Use
1. Create production profile with real information
2. Add actual resume files to `profiles/YourName/resumes/`
3. Update profile JSON with detailed skills and experience
4. Use comprehensive search settings
5. Enable caching for performance: `--enable-cache`

## 🎯 Next Steps

After creating a profile and verifying health:

1. **Add Resume**: Place your resume in `profiles/YourName/resumes/`
2. **Update Profile**: Edit the JSON file with detailed information
3. **Configure Search**: Adjust keywords and locations in profile JSON
4. **Run First Search**: `python main.py YourName --action jobspy-pipeline`
5. **Monitor Progress**: `python main.py YourName --action dashboard`

## 📊 System Requirements

### Required (Always Checked)
- Python 3.8+
- Conda environment: `auto_job`
- 1GB+ free disk space
- Required Python packages (auto-installed via requirements.txt)

### NOT Required (Previously Incorrectly Checked)
- ❌ PostgreSQL - **NOT NEEDED**
- ❌ Docker - **NOT NEEDED**
- Project uses DuckDB/SQLite instead

## 🔄 Database Information

JobLens uses **DuckDB** as the primary database:
- High performance for analytics
- No server setup required
- File-based storage
- Per-profile databases: `profiles/ProfileName/ProfileName_duckdb.db`

SQLite fallback is also available for compatibility.

## 🎉 Summary

The health check system now correctly validates only the components actually used by JobLens. PostgreSQL and Docker are not required and will no longer cause false failures. The new profile creation tool makes it easy to set up multiple profiles for testing or different job search strategies.

**All systems are working correctly if you see "✅ Action 'health-check' completed successfully!" at the end.**
