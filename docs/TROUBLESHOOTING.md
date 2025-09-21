# JobQst Troubleshooting Guide

**Version**: 2.0.0  
**Last Updated**: September 21, 2025

This guide helps you resolve common issues with JobQst quickly and effectively.

## Quick Diagnostics

### System Health Check

```bash
# Run the complete pipeline test
python test_complete_pipeline.py

# Check database connectivity
python -c "from src.core.job_database import get_job_db; print(f'Jobs: {get_job_db(\"YourProfile\").get_job_count()}')"

# Verify profile exists
python -c "from src.utils.profile_helpers import load_profile; print(load_profile('YourProfile'))"
```

## Common Issues

### 1. Installation Problems

#### Issue: `ModuleNotFoundError` when running JobQst

**Symptoms:**
```
ModuleNotFoundError: No module named 'src.core.job_database'
```

**Solutions:**
```bash
# Ensure you're in the project root directory
cd /path/to/jobqst

# Install dependencies
pip install -r requirements.txt

# Verify Python path
python -c "import sys; print(sys.path)"
```

#### Issue: GPU/CUDA errors during AI processing

**Symptoms:**
```
RuntimeError: CUDA out of memory
torch.cuda.is_available() returns False
```

**Solutions:**
```bash
# Disable GPU processing (use CPU only)
export DISABLE_HEAVY_AI=1
python main.py YourProfile --action scrape

# Or reduce batch size in processing
# Edit config to use smaller batches
```

### 2. Database Issues

#### Issue: Database connection errors

**Symptoms:**
```
Connection Error: Can't open a connection to same database file
```

**Solutions:**
```bash
# Close all running JobQst processes
pkill -f "python.*main.py"

# Remove lock files if they exist
rm -f profiles/YourProfile/*.db-wal
rm -f profiles/YourProfile/*.db-shm

# Restart JobQst
python main.py YourProfile
```

#### Issue: Database corruption

**Symptoms:**
```
database disk image is malformed
```

**Solutions:**
```bash
# Backup existing database
cp profiles/YourProfile/YourProfile_duckdb.db profiles/YourProfile/backup_$(date +%Y%m%d).db

# Create fresh database (will lose data)
rm profiles/YourProfile/YourProfile_duckdb.db

# Re-run scraping to rebuild
python main.py YourProfile --action scrape --jobs 50
```

### 3. Scraping Issues

#### Issue: No jobs found during scraping

**Symptoms:**
```
✅ Eluta scraping completed: 0 jobs found
```

**Solutions:**
```bash
# Check your keywords are relevant
python -c "from src.utils.profile_helpers import load_profile; print(load_profile('YourProfile')['keywords'])"

# Test with broader keywords
python main.py YourProfile --action scrape --jobs 10 --keywords "developer,engineer"

# Check internet connection
curl -I https://www.eluta.ca
```

#### Issue: Scraping is very slow

**Symptoms:**
- Takes >5 minutes to scrape 50 jobs
- Browser windows opening/closing slowly

**Solutions:**
```bash
# Enable headless mode for faster scraping
python main.py YourProfile --action scrape --headless

# Reduce concurrent workers if system is slow
# Edit scraper config to use fewer workers

# Check system resources
top -p $(pgrep -f python)
```

#### Issue: Rate limiting / IP blocking

**Symptoms:**
```
HTTP 429: Too Many Requests
Connection refused errors
```

**Solutions:**
```bash
# Increase delays between requests
# Edit scraper config: delay: 2.0 (instead of 1.0)

# Use different scraping approach
python main.py YourProfile --action scrape --mode conservative

# Wait and try again later
sleep 3600  # Wait 1 hour
```

### 4. Processing Issues

#### Issue: AI processing fails

**Symptoms:**
```
ProcessingError: Model loading failed
CUDA out of memory
```

**Solutions:**
```bash
# Disable GPU processing
export DISABLE_HEAVY_AI=1

# Use CPU-only processing
python main.py YourProfile --action process --cpu-only

# Reduce batch size
python main.py YourProfile --action process --batch-size 16
```

#### Issue: Jobs not getting compatibility scores

**Symptoms:**
- Jobs have `fit_score: null` in database
- Processing completes but no scores assigned

**Solutions:**
```bash
# Check if jobs need processing
python -c "from src.core.job_database import get_job_db; db = get_job_db('YourProfile'); print(f'Unprocessed: {len(db.get_jobs_for_processing())}')"

# Force reprocessing
python main.py YourProfile --action process --force-reprocess

# Check profile has skills defined
python -c "from src.utils.profile_helpers import load_profile; print(load_profile('YourProfile').get('skills', 'No skills defined'))"
```

### 5. Dashboard Issues

#### Issue: Dashboard won't start

**Symptoms:**
```
ModuleNotFoundError: No module named 'dash'
Port 8501 already in use
```

**Solutions:**
```bash
# Install dashboard dependencies
pip install dash plotly pandas

# Use different port
python src/dashboard/unified_dashboard.py --profile YourProfile --port 8502

# Kill existing dashboard
pkill -f "streamlit\|dash"
```

#### Issue: Dashboard shows no data

**Symptoms:**
- Dashboard loads but shows "0 jobs"
- Empty charts and tables

**Solutions:**
```bash
# Verify database has data
python -c "from src.core.job_database import get_job_db; print(f'Jobs: {get_job_db(\"YourProfile\").get_job_count()}')"

# Check profile name matches
ls profiles/  # List available profiles

# Refresh dashboard data
# Restart dashboard with correct profile name
```

### 6. Profile Issues

#### Issue: Profile not found

**Symptoms:**
```
ValueError: Profile 'YourProfile' not found!
```

**Solutions:**
```bash
# List available profiles
ls profiles/

# Create new profile
python main.py --setup-profile YourProfile

# Check profile file exists and is valid JSON
cat profiles/YourProfile/YourProfile.json | python -m json.tool
```

#### Issue: Invalid profile configuration

**Symptoms:**
```
JSONDecodeError: Expecting ',' delimiter
KeyError: 'keywords'
```

**Solutions:**
```bash
# Validate profile JSON
python -c "import json; print(json.load(open('profiles/YourProfile/YourProfile.json')))"

# Reset profile to defaults
python main.py --setup-profile YourProfile --reset

# Manually fix profile file
# Ensure required fields: profile_name, keywords
```

## Performance Optimization

### Slow Performance

#### Symptoms:
- Scraping takes >10 minutes for 100 jobs
- High CPU/memory usage
- System becomes unresponsive

#### Solutions:

```bash
# Reduce concurrent workers
# Edit config: max_workers: 5 (instead of 10)

# Use lighter processing
export DISABLE_HEAVY_AI=1

# Process in smaller batches
python main.py YourProfile --action scrape --jobs 25

# Monitor system resources
htop  # or Task Manager on Windows
```

### Memory Issues

#### Symptoms:
```
MemoryError: Unable to allocate array
System runs out of RAM
```

#### Solutions:

```bash
# Reduce batch sizes
# Edit processing config: batch_size: 16

# Clear cache periodically
rm -rf cache/

# Process jobs in smaller chunks
python main.py YourProfile --action process --limit 50
```

## Environment-Specific Issues

### Windows Issues

#### Issue: Unicode encoding errors

**Symptoms:**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```

**Solutions:**
```cmd
# Set UTF-8 encoding
set PYTHONIOENCODING=utf-8

# Or use PowerShell instead of CMD
powershell
python main.py YourProfile
```

#### Issue: Path issues with backslashes

**Solutions:**
```python
# Use forward slashes or raw strings in config
"db_path": "profiles/YourProfile/data.db"  # Good
"db_path": r"profiles\YourProfile\data.db"  # Also good
```

### macOS Issues

#### Issue: Permission denied errors

**Solutions:**
```bash
# Fix permissions
chmod +x main.py
chmod -R 755 src/

# Use virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Linux Issues

#### Issue: Missing system dependencies

**Solutions:**
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-dev build-essential

# For CentOS/RHEL
sudo yum install python3-devel gcc
```

## Debugging Tips

### Enable Debug Logging

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py YourProfile --action scrape --verbose

# Check log files
tail -f logs/jobqst.log
```

### Profile Performance

```bash
# Profile scraping performance
python -m cProfile -o scraping.prof main.py YourProfile --action scrape --jobs 10

# Analyze profile
python -c "import pstats; pstats.Stats('scraping.prof').sort_stats('cumulative').print_stats(20)"
```

### Database Debugging

```bash
# Check database schema
python -c "from src.core.job_database import get_job_db; db = get_job_db('YourProfile'); print(db.conn.execute('PRAGMA table_info(jobs)').fetchall())"

# Check recent jobs
python -c "from src.core.job_database import get_job_db; db = get_job_db('YourProfile'); jobs = db.get_jobs(limit=5); [print(f\"{j['title']} at {j['company']}\") for j in jobs]"
```

## Getting Help

### Before Asking for Help

1. **Run the health check**: `python test_complete_pipeline.py`
2. **Check the logs**: Look in `logs/` directory for error messages
3. **Verify your setup**: Ensure profile exists and has valid keywords
4. **Try with minimal data**: Test with just 10 jobs first

### Information to Include

When reporting issues, include:

```bash
# System information
python --version
pip list | grep -E "(torch|playwright|duckdb|dash)"

# JobQst status
python test_complete_pipeline.py

# Error logs
tail -20 logs/jobqst.log

# Profile information (remove sensitive data)
python -c "from src.utils.profile_helpers import load_profile; p = load_profile('YourProfile'); print({k: v for k, v in p.items() if k != 'personal_info'})"
```

### Where to Get Help

1. **Check this troubleshooting guide first**
2. **Review the [README.md](../README.md) for setup instructions**
3. **Check [Architecture Guide](ARCHITECTURE.md) for technical details**
4. **Create GitHub issue with reproduction steps**

## Quick Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| No jobs found | Check keywords: `python -c "from src.utils.profile_helpers import load_profile; print(load_profile('YourProfile')['keywords'])"` |
| Database errors | Restart: `pkill -f python; python main.py YourProfile` |
| Slow scraping | Use headless: `python main.py YourProfile --action scrape --headless` |
| Memory issues | Disable AI: `export DISABLE_HEAVY_AI=1` |
| Dashboard empty | Check profile: `ls profiles/` |
| Import errors | Reinstall: `pip install -r requirements.txt` |

---

**Troubleshooting Guide Version**: 2.0.0  
**Last Updated**: September 21, 2025  
**Maintainer**: JobQst Development Team

*Most issues can be resolved by running the health check and following the solutions above. For persistent problems, create a GitHub issue with the diagnostic information.*