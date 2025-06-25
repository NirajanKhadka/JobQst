# Enhanced Click-and-Popup System Guide

## Overview
The Enhanced Click-and-Popup system is a sophisticated job scraping framework that mimics human behavior to extract job URLs from various job sites. This system is designed to be reliable, stealthy, and effective at avoiding bot detection.

## 🎯 How It Works

### 1. **Human Behavior Simulation**
The system simulates realistic human interactions:
- **Random delays** between actions (2-5 seconds)
- **Natural mouse movements** with acceleration/deceleration
- **Realistic click patterns** (not instant clicks)
- **Page scrolling** to simulate reading
- **Tab management** like a real user

### 2. **Popup Detection and Handling**
```python
# Popup detection logic
def detect_popup(page):
    """Detects various types of popups and overlays."""
    selectors = [
        '.popup', '.modal', '.overlay',
        '[role="dialog"]', '.lightbox'
    ]
    for selector in selectors:
        if page.query_selector(selector):
            return True
    return False
```

### 3. **URL Extraction Process**
1. **Click job link** with human-like behavior
2. **Wait for popup** (3 seconds optimized)
3. **Extract real URL** from popup content
4. **Close popup** gracefully
5. **Continue to next job**

## 🚀 Available Scraping Modes

### 1. **Basic Click-and-Popup (Single-Threaded)**
```bash
# Option 4: Basic Click-and-Popup
# Best for: Reliability, avoiding detection
# Speed: 20-30 jobs per minute
```

**Features:**
- Single browser context
- Maximum stealth
- 3-second popup waits
- Human-like delays
- Conservative approach

### 2. **Multi-Browser Click-and-Popup**
```bash
# Option 2: Multi-Browser Click-and-Popup
# Best for: Speed, multiple keywords
# Speed: 50-100 jobs per minute
```

**Features:**
- Multiple browser contexts
- Parallel keyword processing
- Shared session management
- Optimized for speed

### 3. **Ultra-Conservative Mode**
```bash
# Option 5: Ultra-Conservative
# Best for: High-risk sites, avoiding CAPTCHAs
# Speed: 10-15 jobs per minute
```

**Features:**
- Maximum delays (5-10 seconds)
- Single browser context
- Cookie persistence
- Session management

## ⚙️ Configuration Options

### 1. **Human Behavior Configuration**
```python
human_config = HumanBehaviorConfig(
    # Delays between actions
    between_jobs=(3.0, 5.0),      # 3-5 seconds
    between_clicks=(1.0, 2.0),    # 1-2 seconds
    popup_wait=3.0,               # 3 seconds for popups
    
    # Mouse movement simulation
    mouse_acceleration=True,
    natural_curves=True,
    
    # Session management
    save_cookies=True,
    cookie_file="cookies.json",
    
    # Stealth options
    randomize_user_agent=True,
    rotate_proxies=False
)
```

### 2. **Scraper Configuration**
```python
scraper_config = {
    'max_workers': 1,              # Browser contexts
    'max_pages_per_keyword': 5,    # Pages to scrape
    'max_jobs_per_keyword': 50,    # Jobs per keyword
    'timeout': 30000,              # 30 seconds
    'retry_attempts': 3,           # Retry failed jobs
    'headless': False              # Show browser (for debugging)
}
```

### 3. **Popup Detection Settings**
```python
popup_config = {
    'wait_time': 3000,             # 3 seconds
    'selectors': [
        '.job-popup', '.modal-content',
        '[data-testid="job-details"]',
        '.job-description'
    ],
    'close_selectors': [
        '.close', '.modal-close',
        '[aria-label="Close"]'
    ]
}
```

## 🎯 Supported Job Sites

### 1. **Eluta.ca**
- **URL Pattern**: `https://www.eluta.ca/jobs-at-*`
- **Popup Type**: Modal overlay
- **Success Rate**: 95%+
- **Recommended Mode**: Basic or Multi-Browser

### 2. **Indeed.ca**
- **URL Pattern**: `https://ca.indeed.com/viewjob`
- **Popup Type**: In-page expansion
- **Success Rate**: 90%+
- **Recommended Mode**: Multi-Browser

### 3. **LinkedIn Jobs**
- **URL Pattern**: `https://www.linkedin.com/jobs/view`
- **Popup Type**: Side panel
- **Success Rate**: 85%+
- **Recommended Mode**: Ultra-Conservative

### 4. **Monster.ca**
- **URL Pattern**: `https://www.monster.ca/job`
- **Popup Type**: Modal dialog
- **Success Rate**: 80%+
- **Recommended Mode**: Basic

## 🔧 Advanced Features

### 1. **Smart Retry Logic**
```python
def smart_retry(job_url, max_attempts=3):
    """Intelligent retry with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            result = extract_job_details(job_url)
            return result
        except PopupTimeoutError:
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)
        except CAPTCHAError:
            # Switch to manual mode
            return handle_captcha_manually(job_url)
```

### 2. **CAPTCHA Detection**
```python
def detect_captcha(page):
    """Detects various CAPTCHA types."""
    captcha_indicators = [
        'captcha', 'recaptcha', 'hcaptcha',
        'verify you are human', 'robot check'
    ]
    
    page_text = page.content().lower()
    for indicator in captcha_indicators:
        if indicator in page_text:
            return True
    return False
```

### 3. **Session Management**
```python
class SessionManager:
    """Manages browser sessions and cookies."""
    
    def save_session(self, session_data):
        """Saves session for reuse."""
        
    def load_session(self):
        """Loads previous session."""
        
    def rotate_session(self):
        """Creates new session to avoid detection."""
```

## 📊 Performance Optimization

### 1. **Speed vs Reliability Trade-offs**
| Mode | Speed | Reliability | Stealth | Use Case |
|------|-------|-------------|---------|----------|
| Basic | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Production |
| Multi-Browser | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Development |
| Ultra-Conservative | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | High-risk sites |

### 2. **Resource Usage**
- **Memory**: 200-500MB per browser context
- **CPU**: 10-30% during active scraping
- **Network**: 1-5 MB per job processed
- **Storage**: 50-100MB for session data

### 3. **Optimization Tips**
```python
# 1. Use appropriate delays
human_delays = {
    'between_jobs': (2.0, 4.0),    # Faster but still human-like
    'popup_wait': 2.5              # Reduced but reliable
}

# 2. Batch processing
batch_size = 10                    # Process jobs in batches
batch_delay = 30                   # 30-second breaks between batches

# 3. Resource management
max_concurrent = 2                 # Limit concurrent contexts
memory_limit = 1024                # 1GB memory limit
```

## 🛡️ Anti-Detection Strategies

### 1. **User Agent Rotation**
```python
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
]
```

### 2. **Request Pattern Randomization**
```python
def randomize_requests():
    """Randomizes request timing and patterns."""
    # Random delays between requests
    # Varying request headers
    # Different click patterns
    # Random scrolling behavior
```

### 3. **IP Rotation (Optional)**
```python
proxy_config = {
    'enabled': False,              # Set to True for proxy rotation
    'proxy_list': [
        'http://proxy1:8080',
        'http://proxy2:8080'
    ],
    'rotation_interval': 100       # Rotate every 100 requests
}
```

## 🔍 Debugging and Monitoring

### 1. **Verbose Logging**
```bash
python main.py --profile default --verbose
```

**Log Output:**
```
[INFO] Starting job scraping for keyword: "python developer"
[DEBUG] Clicking job link: https://example.com/job/123
[DEBUG] Waiting for popup (3 seconds)...
[DEBUG] Popup detected, extracting URL...
[DEBUG] Extracted URL: https://real-job-url.com
[DEBUG] Closing popup...
[INFO] Successfully processed job #1
```

### 2. **Performance Metrics**
```python
metrics = {
    'jobs_processed': 150,
    'success_rate': 0.95,
    'average_time_per_job': 4.2,
    'popup_success_rate': 0.98,
    'captcha_encounters': 0
}
```

### 3. **Error Tracking**
```python
error_types = {
    'popup_timeout': 5,
    'captcha_detected': 0,
    'network_error': 2,
    'parsing_error': 1
}
```

## 🎯 Best Practices

### 1. **For Production Use**
- Use Basic or Ultra-Conservative mode
- Implement proper error handling
- Monitor success rates
- Take breaks between sessions
- Use realistic delays

### 2. **For Development**
- Use Multi-Browser mode for speed
- Enable verbose logging
- Test with small datasets
- Monitor resource usage
- Use headless mode for testing

### 3. **For High-Risk Sites**
- Use Ultra-Conservative mode
- Implement proxy rotation
- Use session persistence
- Monitor for CAPTCHAs
- Have manual fallback ready

## 🚨 Troubleshooting

### Common Issues:
1. **Popup Timeouts**: Increase wait time or check site structure
2. **CAPTCHA Detection**: Switch to manual mode or use proxies
3. **Memory Issues**: Reduce concurrent contexts
4. **Network Errors**: Check connectivity and retry logic

### Debug Commands:
```bash
# Test popup detection
python -m pytest tests/test_click_popup_framework.py -v

# Test specific site
python -c "from scrapers.eluta_enhanced import ElutaWorkingScraper; scraper = ElutaWorkingScraper(); scraper.test_popup_detection()"

# Monitor performance
python -c "from utils.scraping_coordinator import ScrapingCoordinator; coordinator = ScrapingCoordinator(); coordinator.monitor_performance()"
```

## 📈 Success Metrics

### Target Performance:
- **Success Rate**: 95%+ job extraction
- **Speed**: 20-50 jobs per minute
- **Reliability**: 99%+ uptime
- **Stealth**: 0 CAPTCHA encounters
- **Resource Usage**: <1GB memory, <30% CPU

### Monitoring Dashboard:
Access the dashboard at `http://localhost:8002` to monitor:
- Real-time scraping progress
- Success rates and error counts
- Performance metrics
- System health status

---

**Last Updated**: June 2025  
**Version**: 2.0  
**Maintainer**: Development Team
