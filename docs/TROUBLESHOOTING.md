# JobLens Troubleshooting Guide

**Last Updated:** January 13, 2025  
**Status:** Active Reference  
**Compliance Score:** 93/100 ✅  
**Environment:** Python 3.11.11 (auto_job conda)

## Quick Diagnostics

Run these first to identify issues:

```bash
# 1. Environment verification (CRITICAL)
python --version  # Should show: Python 3.11.11
python -c "import sys; print(sys.executable)"
# Expected: .../miniconda3/envs/auto_job/python.exe

# 2. Database connectivity
python -c "from src.core.job_database import get_job_db; print(f'Jobs: {get_job_db(\"YourProfile\").get_job_count()}')"

# 3. Profile verification
python -c "from src.utils.profile_helpers import load_profile; print(load_profile('YourProfile'))"

# 4. Complete pipeline test
python test_complete_pipeline.py
```

## Critical Environment Issues

### Wrong Python Environment

**Symptoms:**
```
Python 3.10.x instead of 3.11.11
ModuleNotFoundError: No module named 'black'
Incorrect sys.executable path (base conda instead of auto_job)
```

**Solution:**
```bash
# 1. Activate correct environment
conda activate auto_job

# 2. Verify
python --version  # Python 3.11.11
python -c "import sys; print(sys.executable)"

# 3. Install dependencies if missing
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Verify dev tools
python -m black --version   # 25.1.0
python -m flake8 --version  # 7.1.1
python -m mypy --version    # 1.14.1
```

**Reference:** See `ENVIRONMENT_SETUP_GUIDE.md` for complete setup

### Development Tools Not Found

**Symptoms:**
```
ModuleNotFoundError: No module named 'black'
```

**Solution:**
```bash
# Ensure correct environment
conda activate auto_job

# Install dev dependencies
pip install -r requirements-dev.txt

# Verify
python -c "import black, flake8, mypy, pytest; print('✅ All tools installed')"
```

### Pre-commit Hooks Failing

**Symptoms:**
```
pre-commit: command not found
Pre-commit hooks fail on commit
```

**Solution:**
```bash
# Install and setup
pip install pre-commit
pre-commit install

# Run manually to see errors
pre-commit run --all-files

# Fix issues, then commit
git add <fixed-files>
git commit -m "Fix pre-commit issues"
```

## Database Issues

### Connection Errors

**Symptoms:**
```
Connection Error: Can't open a connection to same database file
```

**Solution:**
```bash
# Close all JobLens processes
pkill -f "python.*main.py"  # Linux/Mac
# Windows: taskkill /F /IM python.exe

# Remove lock files
rm -f profiles/YourProfile/*.db-wal
rm -f profiles/YourProfile/*.db-shm

# Restart
python main.py YourProfile
```

### Database Corruption

**Symptoms:**
```
database disk image is malformed
```

**Solution:**
```bash
# Backup
cp profiles/YourProfile/YourProfile_duckdb.db profiles/YourProfile/backup_$(date +%Y%m%d).db

# Fresh database (will lose data)
rm profiles/YourProfile/YourProfile_duckdb.db

# Rebuild
python main.py YourProfile --action scrape --jobs 50
```

## Scraping Issues

### No Jobs Found

**Symptoms:**
```
✅ Eluta scraping completed: 0 jobs found
```

**Solution:**
```bash
# Check keywords
python -c "from src.utils.profile_helpers import load_profile; print(load_profile('YourProfile')['keywords'])"

# Test with broader keywords
python main.py YourProfile --action scrape --jobs 10 --keywords "developer,engineer"

# Check internet
curl -I https://www.indeed.com
```

### Slow Scraping

**Symptoms:**
- Takes >5 minutes to scrape 50 jobs

**Solution:**
```bash
# Enable headless mode
python main.py YourProfile --action scrape --headless

# Check system resources
top -p $(pgrep -f python)  # Linux/Mac
# Windows: Task Manager
```

### Rate Limiting

**Symptoms:**
```
HTTP 429: Too Many Requests
Connection refused errors
```

**Solution:**
```bash
# Increase delays in scraper config
# Edit: delay: 2.0 (instead of 1.0)

# Wait and retry
sleep 3600  # Wait 1 hour
python main.py YourProfile --action scrape
```

## Processing Issues

### AI Processing Fails

**Symptoms:**
```
ProcessingError: Model loading failed
CUDA out of memory
```

**Solution:**
```bash
# Disable GPU
export DISABLE_HEAVY_AI=1

# Use CPU-only
python main.py YourProfile --action process --cpu-only

# Reduce batch size
python main.py YourProfile --action process --batch-size 16
```

### Missing Compatibility Scores

**Symptoms:**
- Jobs have `fit_score: null`

**Solution:**
```bash
# Check unprocessed jobs
python -c "from src.core.job_database import get_job_db; db = get_job_db('YourProfile'); print(f'Unprocessed: {len(db.get_jobs_for_processing())}')"

# Force reprocessing
python main.py YourProfile --action process --force-reprocess

# Check profile has skills
python -c "from src.utils.profile_helpers import load_profile; print(load_profile('YourProfile').get('skills'))"
```

## Dashboard Issues

### Dashboard Won't Start

**Symptoms:**
```
ModuleNotFoundError: No module named 'dash'
Port 8050 already in use
```

**Solution:**
```bash
# Install dependencies
pip install dash plotly pandas

# Use different port
python src/dashboard/unified_dashboard.py --profile YourProfile --port 8052

# Kill existing dashboard
pkill -f "dash"  # Linux/Mac
# Windows: taskkill /F /FI "WINDOWTITLE eq Dash*"
```

### Dashboard Shows No Data

**Symptoms:**
- Dashboard loads but shows "0 jobs"

**Solution:**
```bash
# Verify database has data
python -c "from src.core.job_database import get_job_db; print(f'Jobs: {get_job_db(\"YourProfile\").get_job_count()}')"

# Check profile name
ls profiles/  # List available profiles

# Restart with correct profile
python src/dashboard/unified_dashboard.py --profile YourProfile
```

## Profile Issues

### Profile Not Found

**Symptoms:**
```
ValueError: Profile 'YourProfile' not found!
```

**Solution:**
```bash
# List profiles
ls profiles/

# Create new profile
python main.py --setup-profile YourProfile

# Validate JSON
cat profiles/YourProfile/YourProfile.json | python -m json.tool
```

### Invalid Profile Configuration

**Symptoms:**
```
JSONDecodeError: Expecting ',' delimiter
KeyError: 'keywords'
```

**Solution:**
```bash
# Validate profile
python -c "import json; print(json.load(open('profiles/YourProfile/YourProfile.json')))"

# Reset to defaults
python main.py --setup-profile YourProfile --reset

# Ensure required fields: profile_name, keywords
```

## Performance Issues

### Slow Performance

**Symptoms:**
- High CPU/memory usage
- System unresponsive

**Solution:**
```bash
# Reduce workers (edit config)
# max_workers: 5 (instead of 10)

# Use lighter processing
export DISABLE_HEAVY_AI=1

# Smaller batches
python main.py YourProfile --action scrape --jobs 25

# Monitor resources
htop  # Linux/Mac
# Windows: Task Manager
```

### Memory Issues

**Symptoms:**
```
MemoryError: Unable to allocate array
System runs out of RAM
```

**Solution:**
```bash
# Reduce batch sizes (edit config)
# batch_size: 16

# Clear cache
rm -rf cache/

# Process in chunks
python main.py YourProfile --action process --limit 50
```

## Platform-Specific Issues

### Windows

**Unicode Errors:**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```

**Solution:**
```cmd
# Set UTF-8
set PYTHONIOENCODING=utf-8

# Use PowerShell
powershell
python main.py YourProfile
```

**Path Issues:**
```python
# Use forward slashes or raw strings
"db_path": "profiles/YourProfile/data.db"  # Good
"db_path": r"profiles\YourProfile\data.db"  # Also good
```

### macOS

**Permission Errors:**
```bash
# Fix permissions
chmod +x main.py
chmod -R 755 src/

# Use virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Linux

**Missing Dependencies:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev build-essential

# CentOS/RHEL
sudo yum install python3-devel gcc
```

## Debugging Tips

### Enable Debug Logging

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Verbose output
python main.py YourProfile --action scrape --verbose

# Check logs
tail -f logs/jobqst.log
```

### Profile Performance

```bash
# Profile scraping
python -m cProfile -o scraping.prof main.py YourProfile --action scrape --jobs 10

# Analyze
python -c "import pstats; pstats.Stats('scraping.prof').sort_stats('cumulative').print_stats(20)"
```

### Database Debugging

```bash
# Check schema
python -c "from src.core.job_database import get_job_db; db = get_job_db('YourProfile'); print(db.conn.execute('PRAGMA table_info(jobs)').fetchall())"

# Check recent jobs
python -c "from src.core.job_database import get_job_db; db = get_job_db('YourProfile'); jobs = db.get_jobs(limit=5); [print(f\"{j['title']} at {j['company']}\") for j in jobs]"
```

## Quick Reference Table

| Problem | Quick Fix |
|---------|-----------|
| No jobs found | Check keywords: `python -c "from src.utils.profile_helpers import load_profile; print(load_profile('YourProfile')['keywords'])"` |
| Database errors | Restart: `pkill -f python; python main.py YourProfile` |
| Slow scraping | Use headless: `python main.py YourProfile --action scrape --headless` |
| Memory issues | Disable AI: `export DISABLE_HEAVY_AI=1` |
| Dashboard empty | Check profile: `ls profiles/` |
| Import errors | Reinstall: `pip install -r requirements.txt` |
| Wrong environment | Activate: `conda activate auto_job` |

## Getting Help

### Before Asking

1. Run health check: `python test_complete_pipeline.py`
2. Check logs: `logs/` directory
3. Verify setup: profile exists with valid keywords
4. Test minimal: try with 10 jobs first

### Information to Include

```bash
# System info
python --version
pip list | grep -E "(torch|playwright|duckdb|dash)"

# JobLens status
python test_complete_pipeline.py

# Recent logs
tail -20 logs/jobqst.log

# Profile info (remove sensitive data)
python -c "from src.utils.profile_helpers import load_profile; p = load_profile('YourProfile'); print({k: v for k, v in p.items() if k != 'personal_info'})"
```

### Where to Get Help

1. Check this guide first
2. Review `README.md` for setup
3. Check `ARCHITECTURE.md` for technical details
4. Create GitHub issue with reproduction steps

## Related Documentation

- **[DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md)** - Coding standards (93/100 compliance)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[README.md](../README.md)** - User guide
- **[ENVIRONMENT_SETUP_GUIDE.md](ENVIRONMENT_SETUP_GUIDE.md)** - Complete environment setup

---

**Version:** 3.0.0  
**Last Updated:** January 13, 2025  
**Maintainer:** JobQst Development Team

> "Most issues are environment-related. When in doubt, check your Python version and active conda environment first."
