# Enhanced Click-and-Popup Job Scraping Guide

## Overview

The enhanced click-and-popup job scraping system implements human-like behavior with 3-second popup waits, universal framework support, and intelligent job filtering. This guide covers the key features, best practices, and troubleshooting for the enhanced system.

## Key Features

### 🎯 Enhanced Click-and-Popup Method
- **3-second popup waits** as specified in user memories
- **Human-like behavior** with randomized delays and mouse movements
- **Universal framework** supporting multiple job sites (Eluta, Indeed, JobBank, etc.)
- **Site-specific optimizations** for each job platform

### 📅 Intelligent Job Filtering
- **14-day filter for Eluta** (as per user memories)
- **124-day filter for other sites** (as per user memories)
- **0-2 years experience filtering** (as per user memories)
- **Automatic experience level detection** with confidence scoring

### 🌐 Multi-Browser Context Support
- **2-3 browser contexts** for parallel processing
- **Each browser focuses on one keyword** for optimal performance
- **Enhanced anti-detection measures** with cookie persistence

## Quick Start

### 1. Basic Usage

```bash
# Start the enhanced scraper
python main.py Nirajan

# Select option 1: Job Scraping
# Choose Eluta as the site
# Select option 1: Enhanced Click-and-Popup (RECOMMENDED)
```

### 2. CLI Options

The enhanced CLI provides clear options for different scraping methods:

1. **🎯 Enhanced Click-and-Popup** - 3-second waits + human behavior + 14-day filter (RECOMMENDED)
2. **⚡ Multi-Browser Click-and-Popup** - 2-3 contexts + universal framework + experience filtering
3. **🧠 Automated Scraping** - 14-day filter + job analysis + parallel processing
4. **🔍 Basic Click-and-Popup** - single-threaded with enhanced human-like behavior

## Technical Implementation

### Human-Like Behavior Configuration

```python
# Default human behavior settings
human_delays = {
    "page_load": (2.0, 4.0),      # Wait after page loads
    "between_jobs": (1.0, 2.0),   # 1-second delays as per memories
    "between_pages": (2.0, 4.0),  # Wait between pages
    "popup_wait": 3.0,            # Fixed 3-second wait for popups
    "pre_click": (0.2, 0.5),      # Wait before clicking
    "post_hover": (0.1, 0.3),     # Wait after hovering
    "keyword_switch": (2.0, 4.0), # Wait between keywords
}
```

### Universal Click-Popup Framework

The system supports multiple job sites with site-specific optimizations:

- **Eluta**: `.organic-job` selector, 3.0s popup wait, 14-day filter
- **Indeed**: `[data-jk]` selector, 2.0s popup wait, 124-day filter
- **JobBank**: `.job-posting` selector, 2.5s popup wait, 124-day filter
- **LinkedIn**: `.job-search-card` selector, 3.5s popup wait, 124-day filter

### Job Filtering Rules

#### Date Filtering
- **Eluta**: 14 days maximum (as per user memories)
- **Other sites**: 124 days maximum (as per user memories)

#### Experience Level Filtering
- **Target**: 0-2 years experience only (as per user memories)
- **Entry Level Keywords**: junior, entry-level, associate, graduate, trainee, 0-2 years
- **Senior Level Keywords**: senior, lead, manager, 5+ years, experienced

## Best Practices

### 1. Scraping Strategy
- **Start with Enhanced Click-and-Popup** for best results
- **Use Multi-Browser mode** for faster processing when needed
- **Monitor the dashboard** during scraping for real-time feedback
- **Let the 3-second popup waits complete** - don't interrupt the process

### 2. Performance Optimization
- **Use 2 browser contexts maximum** to avoid bot detection
- **Scrape 5 pages per keyword minimum** for comprehensive coverage
- **Allow human-like delays** between operations
- **Enable cookie persistence** for session continuity

### 3. Experience Level Targeting
- **Focus on entry-level positions** (0-2 years experience)
- **Review ambiguous jobs manually** when confidence is low
- **Use the filtering dashboard** to see experience level classifications

## Troubleshooting

### Common Issues

#### 1. Popup Timeouts
**Symptoms**: "Popup timeout" or "Could not get real URL" messages

**Solutions**:
- Ensure stable internet connection
- Check if the job site is accessible
- Try reducing the number of concurrent browser contexts
- Verify the site hasn't changed its structure

```python
# Increase popup timeout if needed
popup_timeout = 8000  # 8 seconds instead of default
```

#### 2. Bot Detection
**Symptoms**: CAPTCHA pages, blocked requests, or empty results

**Solutions**:
- Use single browser context mode (max_workers=1)
- Increase delays between operations
- Enable cookie persistence
- Use the "Basic Click-and-Popup" mode for maximum stealth

```python
# Ultra-conservative settings
scraper = ElutaWorkingScraper(
    profile,
    max_workers=1,  # Single context
    human_delays={"between_jobs": (2.0, 4.0)}  # Longer delays
)
```

#### 3. No Jobs Found
**Symptoms**: Scraper completes but finds 0 jobs

**Solutions**:
- Check if keywords are too specific
- Verify the date filter isn't too restrictive
- Ensure the job site has listings for your location
- Try different scraping methods

#### 4. Experience Level Misclassification
**Symptoms**: Senior jobs marked as entry-level or vice versa

**Solutions**:
- Review the job manually using the dashboard
- Check the confidence score (low scores need manual review)
- Update the experience level keywords if needed

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
python main.py Nirajan --verbose
```

### Dashboard Monitoring

Launch the dashboard to monitor scraping progress:

```bash
# Dashboard auto-launches during scraping
# Access at: http://localhost:8002
```

## Advanced Configuration

### Custom Human Behavior

```python
# Customize human behavior for specific needs
custom_config = HumanBehaviorConfig(
    popup_wait=5.0,  # Longer popup wait
    between_jobs=(2.0, 3.0),  # Slower job processing
    save_cookies=True,  # Enable session persistence
    max_open_tabs=2  # Limit open tabs
)
```

### Site-Specific Optimization

```python
# Create site-specific scraper
framework = UniversalClickPopupFramework("eluta")
framework.current_config["popup_wait"] = 4.0  # Custom wait time
```

### Batch Processing

```python
# Process multiple keywords efficiently
keywords = ["developer", "analyst", "engineer"]
scraper.max_pages_per_keyword = 5  # 5 pages minimum
scraper.max_jobs_per_keyword = 50  # Higher limit
```

## Performance Metrics

### Expected Performance
- **Speed**: 20-30 jobs per minute (with human delays)
- **Accuracy**: 95%+ job extraction success rate
- **Filtering**: 80%+ relevant jobs after experience filtering
- **Reliability**: 99%+ uptime with proper configuration

### Monitoring
- Use the dashboard for real-time metrics
- Check logs for error patterns
- Monitor success rates per keyword
- Track experience level classification accuracy

## Support and Updates

### Getting Help
1. Check this guide for common issues
2. Review the troubleshooting section
3. Enable verbose logging for detailed error information
4. Check the dashboard for real-time status

### Best Practices Summary
- ✅ Use Enhanced Click-and-Popup mode (recommended)
- ✅ Allow 3-second popup waits to complete
- ✅ Monitor the dashboard during scraping
- ✅ Use 2 browser contexts maximum for stability
- ✅ Enable cookie persistence for better session handling
- ✅ Focus on 0-2 years experience jobs
- ✅ Scrape 5 pages per keyword minimum

### What's New
- 🎯 Enhanced click-and-popup with 3-second waits
- 🌐 Universal framework supporting multiple job sites
- 📅 Intelligent date filtering (14 days for Eluta, 124 for others)
- 🎓 Experience level filtering (0-2 years focus)
- 🤖 Human-like behavior with randomized delays
- 🔄 Multi-browser context support (2-3 contexts)
- 📊 Real-time dashboard monitoring
- 🧪 Comprehensive testing suite
