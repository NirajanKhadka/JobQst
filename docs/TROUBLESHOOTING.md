# AutoJobAgent Troubleshooting Guide

## Overview
This guide provides solutions to common issues encountered when using AutoJobAgent. If you encounter an issue not covered here, please check the logs or create an issue report.

## 🚨 Common Issues and Solutions

### 1. **Import Errors**

#### Issue: `ImportError: cannot import name 'utils' from 'src.utils'`
**Solution**: This has been fixed in v2.0. Update your imports to use specific functions:
```python
# ❌ Old way (no longer works)
from src.utils import utils

# ✅ New way
from src.utils.job_helpers import generate_job_hash
from src.utils.profile_helpers import get_available_profiles
from src.utils.file_operations import save_jobs_to_json
```

#### Issue: `ModuleNotFoundError: No module named 'src.core.utils'`
**Solution**: The `src.core.utils` module doesn't exist. Use the correct modules:
```python
# ❌ Wrong
import src.core.utils

# ✅ Correct
import src.core.system_utils
import src.core.file_utils
import src.core.text_utils
```

### 2. **Database Issues**

#### Issue: `JobDatabase` class not found
**Solution**: Use `ModernJobDatabase` instead:
```python
# ❌ Old way
from src.core.job_database import JobDatabase
db = JobDatabase()

# ✅ New way
from src.core.job_database import ModernJobDatabase
db = ModernJobDatabase()
```

#### Issue: Database connection errors
**Solution**: 
1. Check if the database file exists
2. Ensure write permissions to the data directory
3. Create the data directory if it doesn't exist:
```bash
mkdir -p data
mkdir -p profiles/default
```

### 3. **Dashboard Issues**

#### Issue: Dashboard fails to start
**Solution**: 
1. Check if port 8002 is already in use:
```bash
# Windows
netstat -ano | findstr :8002

# Linux/Mac
lsof -i :8002
```

2. Kill the existing process or use a different port:
```bash
# Kill process on Windows
taskkill /PID <process_id> /F

# Kill process on Linux/Mac
kill -9 <process_id>
```

3. Start dashboard manually:
```bash
python -m uvicorn src.dashboard.api:app --port 8002 --host 0.0.0.0
```

#### Issue: Dashboard shows "Cannot connect" error
**Solution**:
1. Check if the dashboard is running: `http://localhost:8002/api/health`
2. Verify firewall settings
3. Check if antivirus is blocking the connection

### 4. **Scraper Issues**

#### Issue: No scrapers available
**Solution**: The scraper registry has been updated. Available scrapers:
- `eluta` - Comprehensive Eluta scraper
- `eluta_optimized` - Optimized parallel scraper
- `eluta_multi_ip` - Multi-IP scraper
- `indeed` - Indeed enhanced scraper
- `linkedin` - LinkedIn enhanced scraper
- `monster` - Monster enhanced scraper
- `jobbank` - JobBank enhanced scraper

#### Issue: Scraper fails with "No module named" error
**Solution**: Install missing dependencies:
```bash
pip install beautifulsoup4 python-docx pandas
```

### 5. **Test Issues**

#### Issue: Tests fail to collect
**Solution**: 
1. Ensure all dependencies are installed
2. Check Python version (3.8+ required)
3. Run tests with verbose output:
```bash
pytest --collect-only -v
```

#### Issue: Specific test failures
**Solution**: 
1. Check test logs for specific error messages
2. Ensure test data files exist
3. Verify database is properly initialized

### 6. **Profile Issues**

#### Issue: Profile not found
**Solution**: 
1. Create a default profile:
```python
from src.core.user_profile_manager import UserProfileManager
pm = UserProfileManager()
pm.create_profile('default', {
    'email': 'your@email.com',
    'location': 'Your City, State',
    'skills': ['Python', 'JavaScript', 'SQL']
})
```

2. Check available profiles:
```python
from src.utils import get_available_profiles
profiles = get_available_profiles()
print(profiles)
```

### 7. **Email Integration Issues**

#### Issue: Gmail verification fails
**Solution**:
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password (not your regular password)
3. Use the App Password in your profile configuration

#### Issue: Email sending fails
**Solution**:
1. Check Gmail settings for "Less secure app access"
2. Verify SMTP settings
3. Check if Gmail is blocking the connection

### 8. **Browser Automation Issues**

#### Issue: Browser fails to start
**Solution**:
1. Install Playwright browsers:
```bash
playwright install
```

2. Check if Chrome/Chromium is installed
3. Verify browser permissions

#### Issue: CAPTCHA detection
**Solution**:
1. The system will automatically detect CAPTCHAs
2. Manual intervention may be required
3. Consider using different IP addresses or proxies

### 9. **Performance Issues**

#### Issue: Slow job processing
**Solution**:
1. Check system resources (CPU, memory)
2. Reduce batch sizes
3. Use parallel processing where available
4. Optimize database queries

#### Issue: Memory usage high
**Solution**:
1. Process jobs in smaller batches
2. Clear job cache periodically
3. Monitor memory usage with system tools

### 10. **Configuration Issues**

#### Issue: Configuration file not found
**Solution**:
1. Create a default configuration:
```python
config = {
    'database_path': 'data/jobs.db',
    'dashboard_port': 8002,
    'max_concurrent_jobs': 5,
    'retry_attempts': 3
}
```

2. Save configuration to file:
```python
import json
with open('config.json', 'w') as f:
    json.dump(config, f, indent=2)
```

## 🔧 Debugging Tools

### 1. **Logging**
Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. **Health Checks**
Run system health checks:
```python
from src.agents.system_health_monitor import SystemHealthMonitor
monitor = SystemHealthMonitor()
status = monitor.run_health_checks()
print(status)
```

### 3. **Database Diagnostics**
Check database status:
```python
from src.core.job_database import ModernJobDatabase
db = ModernJobDatabase()
stats = db.get_job_stats()
print(stats)
```

## 📋 System Requirements

### Minimum Requirements:
- **Python**: 3.8+
- **RAM**: 4GB
- **Storage**: 1GB free space
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+

### Recommended Requirements:
- **Python**: 3.11+
- **RAM**: 8GB+
- **Storage**: 5GB free space
- **CPU**: 4+ cores

## 🆘 Getting Help

### 1. **Check Logs**
Look for error messages in:
- Console output
- Log files in `logs/` directory
- System logs

### 2. **Common Commands**
```bash
# Check system status
python -c "from src.agents.system_health_monitor import SystemHealthMonitor; SystemHealthMonitor().run_health_checks()"

# Test dashboard
curl http://localhost:8002/api/health

# Check available profiles
python -c "from src.utils import get_available_profiles; print(get_available_profiles())"

# Run tests
pytest tests/ -v
```

### 3. **Create Issue Report**
When creating an issue report, include:
- Error message
- Steps to reproduce
- System information
- Log files
- Configuration files (without sensitive data)

## 🎯 Prevention Tips

### 1. **Regular Maintenance**
- Update dependencies regularly
- Clear old log files
- Backup important data
- Monitor system resources

### 2. **Best Practices**
- Use virtual environments
- Keep Python and packages updated
- Test changes in development environment
- Document custom configurations

### 3. **Monitoring**
- Set up system monitoring
- Check logs regularly
- Monitor database size
- Track performance metrics

## 📞 Support

For additional support:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information
4. Contact the development team

---

**Last Updated**: June 2025  
**Version**: 2.0  
**Maintainer**: Development Team
