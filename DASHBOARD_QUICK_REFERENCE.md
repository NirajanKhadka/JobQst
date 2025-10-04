# Dashboard Quick Reference Card

**Quick Access:** `python main.py YourProfileName --action dashboard`  
**URL:** http://localhost:8050  
**Version:** 2.0 (October 4, 2025)

---

## 🚀 Quick Start

```bash
# 1. Activate environment (CRITICAL!)
conda activate auto_job

# 2. Launch dashboard
python main.py Nirajan --action dashboard

# 3. Browser opens automatically to http://localhost:8050
```

---

## 📍 Tab Navigation

| Icon | Tab | Purpose | Key Feature |
|------|-----|---------|-------------|
| 🏠 | **Home** | Ranked jobs feed | AI-powered matching |
| 🔍 | **Job Browser** | Explore & filter | LinkedIn-style search |
| 📋 | **Job Tracker** | Application pipeline | Kanban board |
| 📊 | **Market Insights** | Analytics & trends | Salary/skill analysis |
| 🤖 | **Scraper Control** | Job discovery | 4-site scraping |
| 📝 | **Interview Prep** | Practice questions | AI-generated (soon) |
| ⚙️ | **Settings** | Configuration | Profile & preferences |

---

## 🎯 Common Tasks

### View Best Matches
```
Home → Check "High Match Jobs" stat → Click cards → View details
```

### Search for Jobs
```
Job Browser → Search bar → Apply filters → Sort → Click "View Details"
```

### Track Applications
```
Job Tracker → Drag cards between columns → Add notes → Set deadlines
```

### Check Salaries
```
Market Insights → Salary Analysis → View charts → Compare locations
```

### Discover New Jobs
```
Scraper Control → Select preset → Configure → Start scraping → Monitor
```

### Export Data
```
Settings → Data Management → Export to CSV → Save file
```

---

## 🔍 Job Browser Filters

| Filter | Options | Use Case |
|--------|---------|----------|
| **Search** | Text input | Find specific keywords |
| **Match Score** | 0-100% slider | Quality threshold |
| **Salary** | 40K-150K slider | Compensation range |
| **Location Type** | Remote/Hybrid/Onsite | Work preference |
| **RCIP Only** | Checkbox | Immigration-focused |
| **Date Posted** | 24h/7d/30d/All | Freshness |

### Sorting Options
- **Best Match** (default) - Highest fit scores
- **Most Recent** - Latest postings
- **Highest Salary** - Top compensation
- **Company Name** - Alphabetical
- **RCIP Priority** - RCIP cities first

---

## 📊 Job Tracker Pipeline

```
Interested → Applied → Interview → Offer → Rejected
   (New)     (Sent)   (Active)   (Received) (Closed)
```

**Actions:**
- Drag cards to move stages
- Click card for details
- Add notes and deadlines
- Track interview dates

---

## 🚨 Troubleshooting

### Dashboard Won't Start
```bash
# Kill existing processes
Get-Process python | Where-Object {$_.Path -like "*miniconda3*"} | Stop-Process -Force

# Restart
python main.py Nirajan --action dashboard
```

### No Data Showing
```bash
# Check database
python quick_db_check.py

# Reload data
python main.py Nirajan --action jobspy-pipeline --jobspy-preset canada_comprehensive
```

### Slow Performance
```
Settings → Data Management → Clear Cache → Reload page
```

### AI Features Not Working
```bash
# Check .env file
OPENAI_API_KEY=sk-...

# Verify credits at platform.openai.com
```

---

## ⚡ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+R` | Refresh page |
| `F12` | Open browser console (debug) |
| `Ctrl+Shift+R` | Hard refresh (clear cache) |
| `Esc` | Close modal |

---

## 💡 Pro Tips

1. **Daily Routine:** Check Home tab first thing for new high matches
2. **Smart Filtering:** Start broad, narrow down with filters
3. **Bookmark Liberally:** Use bookmarks for jobs to revisit later
4. **Track Everything:** Move jobs to tracker even if just interested
5. **Export Before Major Changes:** CSV backup of your data
6. **Check Insights Weekly:** Market trends for salary negotiation
7. **Clear Cache Monthly:** Keeps dashboard fast
8. **Use RCIP Filter:** If on immigration pathways

---

## 📈 Stats Dashboard

### Home Tab Quick Stats
- **Total Jobs** - All jobs in database
- **High Match** - 80%+ fit score (your best opportunities!)
- **RCIP Jobs** - Immigration-friendly cities
- **Remote Jobs** - Remote/Hybrid positions
- **Recent Jobs** - Posted in last 7 days
- **Avg Match** - Overall profile alignment

### Tracker Stats
- **Total Applications** - Jobs you've applied to
- **Active Interviews** - Currently interviewing
- **Pending Responses** - Awaiting company response
- **Success Rate** - Offer/application ratio

---

## 🎨 Customization

### Change Theme
```
Settings → Dashboard Settings → Theme → Select → Apply
```

### Auto-Refresh
```
Top bar → Toggle "Auto-refresh" switch
(On = updates every 30 seconds)
```

### Default Filters
```
Settings → Dashboard Settings → Default Filters → Set preferences → Save
```

---

## 🔗 Quick Links

| Resource | Location |
|----------|----------|
| **Full Documentation** | `DASHBOARD_DOCUMENTATION.md` |
| **Troubleshooting** | `TROUBLESHOOTING.md` |
| **Callback Fix Details** | `DUPLICATE_CALLBACK_FIX.md` |
| **Development Guide** | `.github/copilot-instructions.md` |
| **Project README** | `README.md` |

---

## 🆘 Need Help?

1. ✅ Check full documentation: `DASHBOARD_DOCUMENTATION.md`
2. ✅ Review troubleshooting section above
3. ✅ Check browser console (F12) for errors
4. ✅ Verify environment: `conda activate auto_job`
5. ✅ Check database: `python quick_db_check.py`
6. ✅ Review recent changes: Git log

---

## 📝 Recent Updates (October 4, 2025)

✅ Fixed duplicate callback outputs error  
✅ Enhanced job browser with better filters  
✅ Added duplicate job detection  
✅ Improved performance with caching  
✅ Namespaced all component IDs  

---

**Maintained By:** JobQst Team  
**Last Updated:** October 4, 2025  
**Status:** Production Ready ✅
