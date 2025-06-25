# 🎯 Core Working Logic & Important Details

## 📋 **CRITICAL SYSTEM PARAMETERS**

### **Dashboard Configuration**
- **Port**: Always `8002` (not 8000)
- **URL**: `http://localhost:8002`
- **PID File**: `dashboard.pid` for process tracking
- **Auto-launch**: Dashboard starts automatically with all operations

### **Eluta Scraper Configuration**
- **Keyword Format**: `["data analyst"]` (single keyword, no location)
- **Page Parameter**: `pg=1`, `pg=2`, etc. (NOT `page=`)
- **Max Pages**: 2-5 pages per keyword
- **Max Jobs**: 10 jobs per scrape
- **Working Method**: `.organic-job` selector + `expect_popup()` + 1-second delay

### **Scraper Registry Parameters**
```python
# CORRECT format for Eluta scraper
scraper_config = {
    "keywords": ["data analyst"],  # Single keyword only
    "max_pages": 2,               # Use pg= parameter
    "max_jobs": 10                # Target job count
}
```

### **Database Configuration**
- **Profile-based**: Each profile gets its own database
- **Location**: `profiles/{profile_name}/{profile_name}.db`
- **Schema**: Modern SQLite with experience levels and match scores
- **Real Data Only**: No fake/sample data allowed

## 🔧 **Core Working Methods**

### **1. Eluta Scraping (Proven Method)**
```python
# The breakthrough technique that works every time
job_elements = page.query_selector_all(".organic-job")  # Perfect selector
with page.expect_popup() as popup_info:
    job_elem.click()  # Click triggers new tab
    time.sleep(1)     # Simple 1-second delay
popup = popup_info.value
real_url = popup.url  # Actual ATS application URL
```

### **2. Dashboard API Endpoints**
- **Main Dashboard**: `http://localhost:8002/`
- **Dashboard Numbers**: `http://localhost:8002/api/dashboard-numbers`
- **System Status**: `http://localhost:8002/api/system-status`
- **Quick Test**: `http://localhost:8002/api/quick-test`
- **API Test Center**: `http://localhost:8002/api-test`

### **3. Profile Management**
```python
# Profile structure
profile = {
    "name": "User Name",
    "profile_name": "profile_name",
    "email": "user@example.com",
    "keywords": ["data analyst"],  # Single keyword
    "skills": ["Python", "SQL", "Excel"],
    "resume_path": "profiles/profile_name/resume.pdf",
    "cover_letter_path": "profiles/profile_name/cover_letter.pdf"
}
```

## 🎯 **Key Working Principles**

### **1. Simplicity First**
- **One keyword**: Use single keyword like `["data analyst"]`
- **No location**: Remove location restrictions for broader search
- **Minimal config**: Only essential parameters

### **2. Proven Methods Only**
- **Eluta**: `.organic-job` + `expect_popup()` method
- **Dashboard**: Port 8002 always
- **Database**: Profile-based SQLite
- **Real data**: No fake/sample data ever

### **3. Conservative Stability**
- **2 workers**: Maximum stability, minimum bot detection
- **5 pages**: Comprehensive coverage per keyword
- **14-day filter**: Recent jobs only
- **Error tolerance**: Graceful degradation

## 📊 **Test Configuration**

### **Eluta Data Analyst Test**
```python
# CORRECT test configuration
test_config = {
    "keywords": ["data analyst"],  # Single keyword
    "max_pages": 2,               # Use pg= parameter
    "max_jobs": 10                # Target 10 jobs
}
```

### **Dashboard Test**
```python
# CORRECT dashboard URL
dashboard_url = "http://localhost:8002"  # Always port 8002
```

## 🚨 **Common Mistakes to Avoid**

### **❌ WRONG - Don't Do This**
```python
# Wrong: Multiple keywords
"keywords": ["data analyst", "business analyst"]

# Wrong: Location restrictions
"location": "Toronto, ON"

# Wrong: Wrong port
dashboard_url = "http://localhost:8000"

# Wrong: Wrong page parameter
"page": 1  # Should be pg=1
```

### **✅ CORRECT - Do This**
```python
# Correct: Single keyword
"keywords": ["data analyst"]

# Correct: No location
# (omit location parameter)

# Correct: Right port
dashboard_url = "http://localhost:8002"

# Correct: Right page parameter
"max_pages": 2  # System uses pg= internally
```

## 🔄 **Workflow Steps**

### **1. Profile Setup**
- Create profile with single keyword
- No location restrictions
- Essential skills only

### **2. Dashboard Launch**
- Always port 8002
- Auto-launch with operations
- PID tracking for cleanup

### **3. Eluta Scraping**
- Single keyword search
- 2-5 pages maximum
- 10 jobs target
- Real ATS URLs only

### **4. Document Customization**
- One-time resume/cover letter modification
- Job-specific customization
- Save to profile directory

### **5. Dashboard Verification**
- Real-time updates on port 8002
- Job count verification
- API endpoint testing

## 📝 **Important Notes**

1. **Port 8002**: Dashboard always runs on port 8002, never 8000
2. **Single Keyword**: Use one keyword like `["data analyst"]`
3. **No Location**: Remove location restrictions for broader search
4. **Real Data**: Never use fake/sample data
5. **Conservative**: 2 workers, 5 pages maximum for stability
6. **Proven Methods**: Only use tested and working techniques

## 🎯 **Quick Reference**

| Component | Parameter | Value |
|-----------|-----------|-------|
| Dashboard | Port | 8002 |
| Eluta | Keywords | `["data analyst"]` |
| Eluta | Pages | 2-5 (pg= parameter) |
| Eluta | Jobs | 10 per scrape |
| Database | Type | Profile-based SQLite |
| Workers | Count | 2 (conservative) |
| Data | Type | Real only (no fake) |

This document should be updated whenever new working methods or important parameters are discovered. 