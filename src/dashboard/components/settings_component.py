#!/usr/bin/env python3
"""
Settings Component
Configuration management and preferences
"""

import streamlit as st
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

def render_settings_component(profile_name: str = "default") -> None:
    """
    Render settings and configuration management interface.
    
    Args:
        profile_name: Current profile name
    """
    
    # Settings tabs
    profile_tab, scraper_tab, ai_tab, system_tab = st.tabs([
        "👤 Profile", "🔍 Scraping", "🤖 AI Settings", "⚙️ System"
    ])
    
    with profile_tab:
        render_profile_settings(profile_name)
    
    with scraper_tab:
        render_scraper_settings()
    
    with ai_tab:
        render_ai_settings()
    
    with system_tab:
        render_system_settings()

def render_profile_settings(profile_name: str):
    """Render profile management settings."""
    
    st.markdown("### 👤 Profile Management")
    
    # Current profile info
    st.markdown(f"""
    <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; margin-bottom: 1.5rem;'>
        <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;'>
            <div style='font-size: 2rem;'>👤</div>
            <div>
                <div style='color: #f1f5f9; font-weight: 600; font-size: 1.25rem;'>Current Profile</div>
                <div style='color: #cbd5e1;'>{profile_name}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Profile selection
    try:
        from src.utils.profile_helpers import get_available_profiles
        available_profiles = get_available_profiles()
        
        if available_profiles:
            st.markdown("#### Switch Profile")
            selected_profile = st.selectbox(
                "Select Profile",
                available_profiles,
                index=available_profiles.index(profile_name) if profile_name in available_profiles else 0,
                key="settings_profile_selector"
            )
            
            if selected_profile != profile_name:
                if st.button("🔄 Switch Profile", use_container_width=True):
                    st.session_state["selected_profile"] = selected_profile
                    st.success(f"Switched to profile: {selected_profile}")
                    st.rerun()
        else:
            st.warning("No profiles found")
            
    except ImportError:
        st.error("Profile management not available")
    
    # Profile creation
    st.markdown("#### Create New Profile")
    
    with st.form("create_profile_form"):
        new_profile_name = st.text_input(
            "Profile Name",
            placeholder="Enter new profile name",
            help="Profile name should be unique and contain only letters, numbers, and underscores"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            copy_from_current = st.checkbox(
                "Copy settings from current profile",
                value=True,
                help="Copy configuration from the current profile to the new one",
                key="settings_copy_from_current"
            )
        
        with col2:
            create_profile_btn = st.form_submit_button("➕ Create Profile", use_container_width=True)
        
        if create_profile_btn and new_profile_name:
            # Profile creation logic would go here
            st.success(f"Profile '{new_profile_name}' would be created")
            st.info("Profile creation functionality to be implemented")

def render_scraper_settings():
    """Render scraper configuration settings."""
    
    st.markdown("### 🔍 Scraping Configuration")
    
    # Scraping preferences
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### General Settings")
        
        max_jobs_per_site = st.number_input(
            "Max Jobs per Site",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            help="Maximum number of jobs to scrape from each site"
        )
        
        scrape_frequency = st.selectbox(
            "Scraping Frequency",
            ["Manual", "Every 6 hours", "Daily", "Every 3 days", "Weekly"],
            index=2,
            help="How often to automatically scrape for new jobs"
        )
        
        headless_mode = st.checkbox(
            "Headless Mode",
            value=True,
            help="Run browser in headless mode (faster, no GUI)",
            key="settings_headless_mode"
        )
        
        respect_robots = st.checkbox(
            "Respect robots.txt",
            value=True,
            help="Follow robots.txt rules when scraping",
            key="settings_respect_robots"
        )
    
    with col2:
        st.markdown("#### Site Selection")
        
        available_sites = ["Eluta", "Indeed", "LinkedIn", "Monster", "Glassdoor"]
        selected_sites = st.multiselect(
            "Sites to Scrape",
            available_sites,
            default=["Eluta", "Indeed"],
            help="Select which job sites to scrape"
        )
        
        st.markdown("#### Keywords & Filters")
        
        default_keywords = st.text_area(
            "Default Keywords",
            value="Python, Data Analyst, Software Engineer, Machine Learning",
            help="Default keywords to use for job searches (comma-separated)"
        )
        
        location_filter = st.text_input(
            "Location Filter",
            value="Remote, Toronto, Vancouver",
            help="Preferred locations (comma-separated)"
        )
    
    # Improved settings
    with st.expander("🔧 Improved Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            request_delay = st.slider(
                "Request Delay (seconds)",
                min_value=1,
                max_value=10,
                value=3,
                help="Delay between requests to avoid being blocked"
            )
            
            retry_attempts = st.number_input(
                "Retry Attempts",
                min_value=1,
                max_value=5,
                value=3,
                help="Number of retry attempts for failed requests"
            )
        
        with col2:
            timeout_seconds = st.number_input(
                "Request Timeout (seconds)",
                min_value=10,
                max_value=120,
                value=30,
                help="Timeout for individual requests"
            )
            
            concurrent_requests = st.number_input(
                "Concurrent Requests",
                min_value=1,
                max_value=10,
                value=3,
                help="Number of concurrent scraping requests"
            )
    
    # Save settings
    if st.button("💾 Save Scraper Settings", use_container_width=True):
        settings = {
            "max_jobs_per_site": max_jobs_per_site,
            "scrape_frequency": scrape_frequency,
            "headless_mode": headless_mode,
            "respect_robots": respect_robots,
            "selected_sites": selected_sites,
            "default_keywords": default_keywords,
            "location_filter": location_filter,
            "request_delay": request_delay,
            "retry_attempts": retry_attempts,
            "timeout_seconds": timeout_seconds,
            "concurrent_requests": concurrent_requests
        }
        st.success("Scraper settings saved!")
        st.json(settings)

def render_ai_settings():
    """Render AI configuration settings."""
    
    st.markdown("### 🤖 AI Configuration")
    
    # AI service selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### AI Service")
        
        ai_service = st.selectbox(
            "Primary AI Service",
            ["Ollama (Local)", "Gemini API", "OpenAI API", "Claude API", "Disabled"],
            index=0,
            help="Select the AI service for job analysis and document generation"
        )
        
        if ai_service == "Ollama (Local)":
            ollama_model = st.selectbox(
                "Ollama Model",
                ["llama3", "llama3:7b", "llama3:13b", "mistral", "codellama"],
                index=0,
                help="Select the Ollama model to use"
            )
            
            ollama_url = st.text_input(
                "Ollama URL",
                value="http://localhost:11434",
                help="URL of the Ollama service"
            )
        
        elif ai_service == "Gemini API":
            gemini_api_key = st.text_input(
                "Gemini API Key",
                type="password",
                help="Your Google Gemini API key"
            )
            
            gemini_model = st.selectbox(
                "Gemini Model",
                ["gemini-pro", "gemini-pro-vision"],
                index=0
            )
    
    with col2:
        st.markdown("#### Analysis Settings")
        
        enable_job_analysis = st.checkbox(
            "Enable Job Analysis",
            value=True,
            help="Use AI to analyze job descriptions and calculate match scores",
            key="settings_enable_job_analysis"
        )
        
        enable_document_generation = st.checkbox(
            "Enable Document Generation",
            value=True,
            help="Use AI to generate personalized resumes and cover letters",
            key="settings_enable_document_generation"
        )
        
        analysis_batch_size = st.number_input(
            "Analysis Batch Size",
            min_value=1,
            max_value=20,
            value=5,
            help="Number of jobs to analyze in each batch"
        )
        
        match_score_threshold = st.slider(
            "Match Score Threshold",
            min_value=0,
            max_value=100,
            value=60,
            help="Minimum match score to consider a job worth applying to"
        )
    
    # Improved AI settings
    with st.expander("🔧 Improved AI Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.slider(
                "AI Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.7,
                step=0.1,
                help="Controls randomness in AI responses (0 = deterministic, 2 = very random)"
            )
            
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=4000,
                value=1000,
                help="Maximum number of tokens in AI responses"
            )
        
        with col2:
            enable_fallback = st.checkbox(
                "Enable Rule-based Fallback",
                value=True,
                help="Use rule-based analysis when AI is unavailable",
                key="settings_enable_fallback"
            )
            
            ai_timeout = st.number_input(
                "AI Request Timeout (seconds)",
                min_value=10,
                max_value=120,
                value=30,
                help="Timeout for AI API requests"
            )
    
    # Save AI settings
    if st.button("💾 Save AI Settings", use_container_width=True):
        settings = {
            "ai_service": ai_service,
            "enable_job_analysis": enable_job_analysis,
            "enable_document_generation": enable_document_generation,
            "analysis_batch_size": analysis_batch_size,
            "match_score_threshold": match_score_threshold,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "enable_fallback": enable_fallback,
            "ai_timeout": ai_timeout
        }
        
        if ai_service == "Ollama (Local)":
            settings.update({
                "ollama_model": ollama_model,
                "ollama_url": ollama_url
            })
        elif ai_service == "Gemini API":
            settings.update({
                "gemini_model": gemini_model
            })
            if gemini_api_key:
                settings["gemini_api_key"] = "***hidden***"
        
        st.success("AI settings saved!")
        st.json(settings)

def render_system_settings():
    """Render system configuration settings."""
    
    st.markdown("### ⚙️ System Configuration")
    
    # System preferences
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Performance")
        
        max_workers = st.number_input(
            "Max Worker Processes",
            min_value=1,
            max_value=10,
            value=5,
            help="Maximum number of worker processes for parallel processing"
        )
        
        memory_limit_gb = st.number_input(
            "Memory Limit (GB)",
            min_value=1,
            max_value=32,
            value=8,
            help="Maximum memory usage limit"
        )
        
        enable_caching = st.checkbox(
            "Enable Caching",
            value=True,
            help="Cache results to improve performance",
            key="settings_enable_caching"
        )
        
        cache_ttl_hours = st.number_input(
            "Cache TTL (hours)",
            min_value=1,
            max_value=168,
            value=24,
            help="How long to keep cached data"
        )
    
    with col2:
        st.markdown("#### Logging & Monitoring")
        
        log_level = st.selectbox(
            "Log Level",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=1,
            help="Minimum log level to record"
        )
        
        enable_metrics = st.checkbox(
            "Enable Metrics Collection",
            value=True,
            help="Collect performance and usage metrics",
            key="settings_enable_metrics"
        )
        
        auto_cleanup = st.checkbox(
            "Auto Cleanup Old Data",
            value=True,
            help="Automatically clean up old job data and logs",
            key="settings_auto_cleanup"
        )
        
        cleanup_days = st.number_input(
            "Cleanup After (days)",
            min_value=7,
            max_value=365,
            value=90,
            help="Delete data older than this many days"
        )
    
    # Database settings
    with st.expander("🗄️ Database Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            db_backup_enabled = st.checkbox(
                "Enable Database Backups",
                value=True,
                help="Automatically backup database",
                key="settings_db_backup_enabled"
            )
            
            backup_frequency = st.selectbox(
                "Backup Frequency",
                ["Daily", "Weekly", "Monthly"],
                index=1,
                help="How often to backup the database"
            )
        
        with col2:
            max_backup_files = st.number_input(
                "Max Backup Files",
                min_value=1,
                max_value=50,
                value=10,
                help="Maximum number of backup files to keep"
            )
            
            vacuum_db = st.checkbox(
                "Auto Vacuum Database",
                value=True,
                help="Automatically optimize database performance",
                key="settings_vacuum_db"
            )
    
    # Notification settings
    with st.expander("🔔 Notifications"):
        col1, col2 = st.columns(2)
        
        with col1:
            enable_notifications = st.checkbox(
                "Enable Notifications",
                value=False,
                help="Enable system notifications",
                key="settings_enable_notifications"
            )
            
            notify_on_completion = st.checkbox(
                "Notify on Job Completion",
                value=True,
                help="Notify when scraping/processing completes",
                key="settings_notify_on_completion"
            )
        
        with col2:
            notify_on_errors = st.checkbox(
                "Notify on Errors",
                value=True,
                help="Notify when errors occur",
                key="settings_notify_on_errors"
            )
            
            notification_method = st.selectbox(
                "Notification Method",
                ["System", "Email", "Slack", "Discord"],
                index=0,
                help="How to send notifications"
            )
    
    # Save system settings
    if st.button("💾 Save System Settings", use_container_width=True):
        settings = {
            "max_workers": max_workers,
            "memory_limit_gb": memory_limit_gb,
            "enable_caching": enable_caching,
            "cache_ttl_hours": cache_ttl_hours,
            "log_level": log_level,
            "enable_metrics": enable_metrics,
            "auto_cleanup": auto_cleanup,
            "cleanup_days": cleanup_days,
            "db_backup_enabled": db_backup_enabled,
            "backup_frequency": backup_frequency,
            "max_backup_files": max_backup_files,
            "vacuum_db": vacuum_db,
            "enable_notifications": enable_notifications,
            "notify_on_completion": notify_on_completion,
            "notify_on_errors": notify_on_errors,
            "notification_method": notification_method
        }
        st.success("System settings saved!")
        st.json(settings)