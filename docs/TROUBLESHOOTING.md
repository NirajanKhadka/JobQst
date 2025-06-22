# Enhanced Click-and-Popup Troubleshooting Guide

## Common Issues and Solutions

### 🖱️ Click-and-Popup Issues

#### Issue: "Popup timeout" or "Could not get real URL" messages
**Symptoms**: 
- Jobs are found but URLs cannot be extracted
- Timeout errors during popup handling
- "No popup detected" messages

**Solutions**:
1. **Check Internet Connection**
   ```bash
   # Test connectivity to job sites
   ping eluta.ca
   ping indeed.ca
   ```

2. **Increase Popup Timeout**
   ```python
   # In scraper configuration
   popup_timeout = 10000  # Increase to 10 seconds
   ```

3. **Use Single Browser Context**
   ```bash
   # Select option 4: Basic Click-and-Popup (single-threaded)
   # This reduces load and improves reliability
   ```

4. **Verify Site Accessibility**
   - Manually visit the job site in your browser
   - Check if the site structure has changed
   - Ensure no CAPTCHA or blocking is present

#### Issue: 3-Second Wait Seems Too Long
**Symptoms**:
- Scraping feels slow
- Impatience with popup wait times

**Solutions**:
1. **Understand the Purpose**
   - 3-second waits ensure reliable job URL extraction
   - Prevents missed jobs due to incomplete page loading
   - Reduces bot detection risk

2. **Use Multi-Browser Mode for Speed**
   ```bash
   # Select option 2: Multi-Browser Click-and-Popup
   # This processes multiple keywords simultaneously
   ```

3. **Don't Reduce Wait Times**
   - The 3-second wait is optimized based on testing
   - Shorter waits lead to missed job URLs
   - Longer waits don't improve reliability significantly

### 🤖 Bot Detection Issues

#### Issue: CAPTCHA pages or blocked requests
**Symptoms**:
- CAPTCHA challenges appear
- Empty results despite jobs being visible
- "Access denied" or similar messages

**Solutions**:
1. **Use Ultra-Conservative Settings**
   ```python
   # Maximum stealth configuration
   scraper = ElutaWorkingScraper(
       profile,
       max_workers=1,  # Single browser context
       human_delays={"between_jobs": (3.0, 5.0)}  # Longer delays
   )
   ```

2. **Enable Cookie Persistence**
   ```python
   # Maintain session state
   human_config = HumanBehaviorConfig(
       save_cookies=True,
       cookie_file="scrapers/cookies.json"
   )
   ```

3. **Take Breaks Between Sessions**
   - Wait 30-60 minutes between scraping sessions
   - Don't run multiple scrapers simultaneously
   - Use different keywords in different sessions

4. **Manual Browser Test**
   - Open the job site manually in your browser
   - Complete any CAPTCHA challenges
   - Save cookies for the scraper to use

### 📅 Job Filtering Issues

#### Issue: No jobs found despite visible listings
**Symptoms**:
- Scraper completes but finds 0 jobs
- Dashboard shows 0 jobs after filtering

**Solutions**:
1. **Check Date Filter Settings**
   ```python
   # Verify date filter configuration
   # Eluta: 14 days maximum
   # Other sites: 124 days maximum
   ```

2. **Review Experience Level Filter**
   ```python
   # Check if jobs are being filtered out for experience level
   # Target: 0-2 years experience only
   ```

3. **Use Verbose Logging**
   ```bash
   python main.py Nirajan --verbose
   # This shows why jobs are being filtered out
   ```

4. **Check Keywords**
   - Ensure keywords are not too specific
   - Try broader terms like "developer" instead of "senior python developer"
   - Use multiple related keywords

#### Issue: Senior jobs marked as entry-level
**Symptoms**:
- Jobs requiring 5+ years experience appear in results
- Experience level classification seems incorrect

**Solutions**:
1. **Check Confidence Score**
   - Low confidence scores (< 0.6) need manual review
   - Use dashboard to see confidence levels

2. **Review Job Description**
   - Some jobs have misleading titles
   - Check full job description for actual requirements

3. **Update Filter Keywords**
   ```python
   # Add site-specific senior keywords if needed
   senior_keywords = ["5+ years", "senior", "lead", "manager"]
   ```

### 🌐 Multi-Browser Context Issues

#### Issue: Browser contexts crash or hang
**Symptoms**:
- Scraper stops responding
- Browser windows remain open after completion
- Memory usage increases significantly

**Solutions**:
1. **Reduce Browser Contexts**
   ```python
   # Use fewer contexts
   max_workers = 1  # Single context for stability
   ```

2. **Increase System Resources**
   - Close other applications
   - Ensure sufficient RAM (8GB+ recommended)
   - Use SSD storage for better performance

3. **Monitor Resource Usage**
   ```bash
   # Check system resources during scraping
   htop  # Linux/Mac
   taskmgr  # Windows
   ```

4. **Clean Browser Data**
   ```python
   # Clear browser cache and cookies periodically
   scraper.cleanup_tabs()
   ```

### 📊 Dashboard Issues

#### Issue: Dashboard not auto-launching
**Symptoms**:
- Dashboard doesn't open automatically
- Cannot access dashboard at localhost:8002

**Solutions**:
1. **Check Port Availability**
   ```bash
   # Check if port 8002 is in use
   netstat -an | grep 8002
   ```

2. **Manual Dashboard Launch**
   ```bash
   # Start dashboard manually
   python dashboard/app.py
   ```

3. **Check Firewall Settings**
   - Ensure localhost connections are allowed
   - Check antivirus software blocking

4. **Use Alternative Port**
   ```python
   # Change dashboard port if needed
   app.run(host='127.0.0.1', port=8003)
   ```

### 🔧 Performance Issues

#### Issue: Scraping is very slow
**Symptoms**:
- Takes hours to complete
- Very few jobs processed per minute

**Solutions**:
1. **Use Multi-Browser Mode**
   ```bash
   # Select option 2: Multi-Browser Click-and-Popup
   # Processes multiple keywords simultaneously
   ```

2. **Optimize Keywords**
   - Use fewer, broader keywords
   - Remove very specific or rare terms
   - Focus on high-volume keywords

3. **Adjust Page Limits**
   ```python
   # Reduce pages per keyword if needed
   max_pages_per_keyword = 3  # Instead of 5
   ```

4. **Check System Performance**
   - Ensure adequate RAM and CPU
   - Close unnecessary applications
   - Use wired internet connection

#### Issue: High memory usage
**Symptoms**:
- System becomes slow during scraping
- Out of memory errors

**Solutions**:
1. **Reduce Concurrent Operations**
   ```python
   max_workers = 1  # Single browser context
   max_jobs_per_keyword = 20  # Lower limit
   ```

2. **Enable Garbage Collection**
   ```python
   import gc
   gc.collect()  # Force garbage collection
   ```

3. **Process in Batches**
   - Scrape fewer keywords at once
   - Take breaks between scraping sessions

## Debug Mode

### Enable Verbose Logging
```bash
python main.py Nirajan --verbose
```

### Check Log Files
```bash
# View recent logs
tail -f logs/scraping.log
tail -f logs/application.log
```

### Test Individual Components
```bash
# Test click-popup framework
python -m pytest tests/test_click_popup_framework.py -v

# Test job filtering
python -m pytest tests/test_job_filters.py -v

# Test complete integration
python -m pytest tests/test_comprehensive_scraping.py -v
```

## Getting Help

### Before Reporting Issues
1. ✅ Check this troubleshooting guide
2. ✅ Enable verbose logging
3. ✅ Test with single browser context
4. ✅ Verify internet connectivity
5. ✅ Check dashboard for error messages

### Information to Include
- Operating system and version
- Python version
- Error messages (full text)
- Steps to reproduce the issue
- Screenshots of dashboard (if applicable)
- Log file excerpts

### Performance Expectations
- **Speed**: 20-30 jobs per minute (with human delays)
- **Success Rate**: 95%+ job extraction success
- **Filtering Accuracy**: 80%+ relevant jobs after filtering
- **Memory Usage**: 500MB-1GB typical
- **CPU Usage**: 20-40% during active scraping

Remember: The enhanced click-and-popup system prioritizes reliability and human-like behavior over raw speed. The 3-second popup waits and human delays are essential for consistent results and avoiding bot detection.
