#!/usr/bin/env python3
"""
reliable Scraping Configuration Component
Provides a comprehensive interface for configuring and running scrapers
"""

import streamlit as st
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ScrapingConfigComponent:
    """Improved scraping configuration with functional controls."""
    
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.config_file = Path(f"profiles/{profile_name}/scraper_config.json")
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
    def render(self):
        """Render the scraping configuration interface."""
        st.markdown("# 🔍 Scraping Configuration")
        st.markdown("Configure and manage job scraping settings with real-time controls.")
        
        # Load current configuration
        config = self._load_config()
        
        # Create tabs for different configuration sections
        config_tab, run_tab, status_tab = st.tabs([
            "⚙️ Configuration", 
            "🚀 Run Scraper", 
            "📊 Status"
        ])
        
        with config_tab:
            self._render_configuration_tab(config)
        
        with run_tab:
            self._render_run_tab(config)
        
        with status_tab:
            self._render_status_tab()
    
    def _render_configuration_tab(self, config: Dict[str, Any]):
        """Render the configuration settings tab."""
        st.markdown("## ⚙️ Scraper Configuration")
        
        # General Settings
        with st.expander("🔧 General Settings", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                max_jobs = st.number_input(
                    "Max Jobs per Site",
                    min_value=1,
                    max_value=1000,
                    value=config.get("max_jobs_per_site", 50),
                    help="Maximum number of jobs to scrape from each site"
                )
                
                headless_mode = st.checkbox(
                    "Headless Mode",
                    value=config.get("headless", True),
                    help="Run browser in headless mode (no GUI)",
                    key="scraping_headless_mode"
                )
                
                respect_robots = st.checkbox(
                    "Respect robots.txt",
                    value=config.get("respect_robots", True),
                    help="Follow robots.txt guidelines",
                    key="scraping_respect_robots"
                )
            
            with col2:
                scraping_frequency = st.selectbox(
                    "Scraping Frequency",
                    ["Manual", "Hourly", "Every 6 hours", "Daily", "Weekly"],
                    index=["Manual", "Hourly", "Every 6 hours", "Daily", "Weekly"].index(
                        config.get("frequency", "Daily")
                    )
                )
                
                request_delay = st.slider(
                    "Request Delay (seconds)",
                    min_value=1,
                    max_value=10,
                    value=config.get("request_delay", 3),
                    help="Delay between requests to avoid being blocked"
                )
                
                retry_attempts = st.number_input(
                    "Retry Attempts",
                    min_value=1,
                    max_value=5,
                    value=config.get("retry_attempts", 3),
                    help="Number of retry attempts for failed requests"
                )
        
        # Site Selection
        with st.expander("🌐 Site Selection", expanded=True):
            st.markdown("### Sites to Scrape")
            
            available_sites = {
                "eluta": {"name": "Eluta", "enabled": True, "description": "Canadian job board"},
                "indeed": {"name": "Indeed", "enabled": False, "description": "Global job board"},
                "linkedin": {"name": "LinkedIn", "enabled": False, "description": "Professional network"},
                "monster": {"name": "Monster", "enabled": False, "description": "Job search engine"}
            }
            
            selected_sites = []
            for site_key, site_info in available_sites.items():
                enabled = st.checkbox(
                    f"{site_info['name']} - {site_info['description']}",
                    value=config.get("sites", {}).get(site_key, site_info["enabled"]),
                    key=f"site_{site_key}"
                )
                if enabled:
                    selected_sites.append(site_key)
        
        # Keywords & Filters
        with st.expander("🔍 Keywords & Filters", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Search Keywords")
                default_keywords = config.get("keywords", [
                    "Data Analyst", "Data Science", "Machine Learning", "Python"
                ])
                keywords_text = st.text_area(
                    "Keywords (one per line)",
                    value="\n".join(default_keywords),
                    height=150,
                    help="Enter job search keywords, one per line"
                )
                keywords = [k.strip() for k in keywords_text.split("\n") if k.strip()]
            
            with col2:
                st.markdown("### Location Filters")
                location_filter = st.text_input(
                    "Location Filter",
                    value=config.get("location_filter", ""),
                    help="Filter jobs by location (e.g., 'Toronto', 'Remote')"
                )
                
                st.markdown("### Experience Level")
                experience_levels = st.multiselect(
                    "Experience Levels",
                    ["Entry Level", "Mid Level", "Senior Level", "Executive"],
                    default=config.get("experience_levels", ["Entry Level", "Mid Level"])
                )
        
        # Improved Settings
        with st.expander("🔧 Improved Settings", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                request_timeout = st.number_input(
                    "Request Timeout (seconds)",
                    min_value=10,
                    max_value=60,
                    value=config.get("request_timeout", 30)
                )
                
                concurrent_requests = st.number_input(
                    "Concurrent Requests",
                    min_value=1,
                    max_value=10,
                    value=config.get("concurrent_requests", 3)
                )
            
            with col2:
                user_agent = st.text_input(
                    "User Agent",
                    value=config.get("user_agent", "AutoJobAgent/1.0"),
                    help="Custom user agent string"
                )
                
                proxy_enabled = st.checkbox(
                    "Use Proxy",
                    value=config.get("proxy_enabled", False),
                    key="scraping_proxy_enabled"
                )
                
                if proxy_enabled:
                    proxy_url = st.text_input(
                        "Proxy URL",
                        value=config.get("proxy_url", ""),
                        help="Proxy server URL (e.g., http://proxy:8080)"
                    )
        
        # Save Configuration
        if st.button("💾 Save Configuration", type="primary", use_container_width=True):
            new_config = {
                "max_jobs_per_site": max_jobs,
                "headless": headless_mode,
                "respect_robots": respect_robots,
                "frequency": scraping_frequency,
                "request_delay": request_delay,
                "retry_attempts": retry_attempts,
                "sites": {site: site in selected_sites for site in available_sites.keys()},
                "keywords": keywords,
                "location_filter": location_filter,
                "experience_levels": experience_levels,
                "request_timeout": request_timeout,
                "concurrent_requests": concurrent_requests,
                "user_agent": user_agent,
                "proxy_enabled": proxy_enabled,
                "proxy_url": proxy_url if proxy_enabled else ""
            }
            
            if self._save_config(new_config):
                st.success("✅ Configuration saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save configuration")
    
    def _render_run_tab(self, config: Dict[str, Any]):
        """Render the scraper execution tab."""
        st.markdown("## 🚀 Run Scraper")
        
        # Quick run options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Quick Scrape (10 jobs)", use_container_width=True):
                self._run_scraper(limit=10)
        
        with col2:
            if st.button("📋 Standard Scrape (50 jobs)", use_container_width=True):
                self._run_scraper(limit=50)
        
        with col3:
            if st.button("🚀 Full Scrape (All)", use_container_width=True):
                self._run_scraper(limit=None)
        
        st.markdown("---")
        
        # Custom run options
        st.markdown("### 🎛️ Custom Run Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            custom_limit = st.number_input(
                "Custom Job Limit",
                min_value=1,
                max_value=1000,
                value=50,
                help="Number of jobs to scrape"
            )
            
            selected_sites = st.multiselect(
                "Sites to Scrape",
                ["eluta", "indeed", "linkedin", "monster"],
                default=["eluta"],
                help="Select which sites to scrape"
            )
        
        with col2:
            custom_keywords = st.text_area(
                "Custom Keywords (optional)",
                placeholder="Data Analyst\nPython Developer\nMachine Learning",
                help="Override default keywords for this run"
            )
            
            dry_run = st.checkbox(
                "Dry Run (Test Mode)",
                help="Test the scraper without saving results",
                key="scraping_dry_run"
            )
        
        if st.button("🎯 Run Custom Scrape", type="primary", use_container_width=True):
            keywords = [k.strip() for k in custom_keywords.split("\n") if k.strip()] if custom_keywords else None
            self._run_scraper(
                limit=custom_limit,
                sites=selected_sites,
                keywords=keywords,
                dry_run=dry_run
            )
    
    def _render_status_tab(self):
        """Render the scraper status and logs tab."""
        st.markdown("## 📊 Scraper Status")
        
        # Check if scraper is running
        is_running = self._check_scraper_status()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_color = "🟢" if is_running else "🔴"
            status_text = "Running" if is_running else "Stopped"
            st.metric("Scraper Status", f"{status_color} {status_text}")
        
        with col2:
            last_run = self._get_last_run_time()
            st.metric("Last Run", last_run)
        
        with col3:
            total_jobs = self._get_total_jobs_scraped()
            st.metric("Total Jobs Scraped", total_jobs)
        
        # Recent logs
        st.markdown("### 📋 Recent Logs")
        logs = self._get_recent_logs()
        
        if logs:
            st.text_area(
                "Scraper Logs",
                value=logs,
                height=300,
                help="Recent scraper activity logs"
            )
        else:
            st.info("No recent logs available")
        
        # Control buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Status", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("📋 View Full Logs", use_container_width=True):
                self._show_full_logs()
        
        with col3:
            if is_running and st.button("⏹️ Stop Scraper", use_container_width=True):
                self._stop_scraper()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load scraper configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
        
        # Return default configuration
        return {
            "max_jobs_per_site": 50,
            "headless": True,
            "respect_robots": True,
            "frequency": "Daily",
            "request_delay": 3,
            "retry_attempts": 3,
            "sites": {"eluta": True, "indeed": False, "linkedin": False, "monster": False},
            "keywords": ["Data Analyst", "Data Science", "Machine Learning", "Python"],
            "location_filter": "",
            "experience_levels": ["Entry Level", "Mid Level"],
            "request_timeout": 30,
            "concurrent_requests": 3,
            "user_agent": "AutoJobAgent/1.0",
            "proxy_enabled": False,
            "proxy_url": ""
        }
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save scraper configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def _run_scraper(self, limit: int = None, sites: List[str] = None, keywords: List[str] = None, dry_run: bool = False):
        """Run the scraper with specified parameters."""
        try:
            # Build command
            cmd = [sys.executable, "main.py", self.profile_name, "--action", "scrape"]
            
            if limit:
                cmd.extend(["--limit", str(limit)])
            
            if sites:
                cmd.extend(["--sites", ",".join(sites)])
            
            if keywords:
                cmd.extend(["--keywords", ",".join(keywords)])
            
            if dry_run:
                cmd.append("--dry-run")
            
            cmd.append("--headless")
            
            # Show command being executed
            st.info(f"🚀 Running command: {' '.join(cmd)}")
            
            # Run in background
            with st.spinner("Starting scraper..."):
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
                )
                
                st.success(f"✅ Scraper started successfully! PID: {process.pid}")
                st.info("⏳ Check the Status tab for progress updates")
                
        except Exception as e:
            st.error(f"❌ Failed to start scraper: {e}")
            logger.error(f"Scraper start error: {e}")
    
    def _check_scraper_status(self) -> bool:
        """Check if scraper is currently running."""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'main.py' in cmdline and 'scrape' in cmdline:
                        return True
        except Exception as e:
            logger.error(f"Error checking scraper status: {e}")
        return False
    
    def _get_last_run_time(self) -> str:
        """Get the last run time of the scraper."""
        try:
            log_file = Path("logs/scraper.log")
            if log_file.exists():
                import os
                mtime = os.path.getmtime(log_file)
                from datetime import datetime
                return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
        return "Never"
    
    def _get_total_jobs_scraped(self) -> int:
        """Get total number of jobs scraped."""
        try:
            from src.core.job_database import get_job_db
            db = get_job_db(self.profile_name)
            return db.get_job_count()
        except Exception as e:
            logger.error(f"Error getting job count: {e}")
            return 0
    
    def _get_recent_logs(self) -> str:
        """Get recent scraper logs."""
        try:
            log_files = [
                Path("logs/scraper.log"),
                Path("error_logs.log"),
                Path("logs/error_logs.log")
            ]
            
            for log_file in log_files:
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        # Return last 20 lines
                        return ''.join(lines[-20:]) if lines else "No logs available"
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
        
        return "No logs available"
    
    def _show_full_logs(self):
        """Show full logs in an expandable section."""
        try:
            logs = self._get_recent_logs()
            with st.expander("📋 Full Scraper Logs", expanded=True):
                st.text_area("Full Logs", value=logs, height=500)
        except Exception as e:
            st.error(f"Error displaying logs: {e}")
    
    def _stop_scraper(self):
        """Stop the running scraper."""
        try:
            import psutil
            stopped = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'main.py' in cmdline and 'scrape' in cmdline:
                        proc.terminate()
                        stopped = True
                        st.success(f"✅ Stopped scraper process (PID: {proc.info['pid']})")
            
            if not stopped:
                st.warning("⚠️ No running scraper process found")
                
        except Exception as e:
            st.error(f"❌ Error stopping scraper: {e}")


def render_scraping_config_component(profile_name: str):
    """Render the scraping configuration component."""
    component = ScrapingConfigComponent(profile_name)
    component.render()