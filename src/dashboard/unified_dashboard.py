#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Professional Dashboard for AutoJobAgent
Combines the best features from streamlit_dashboard.py and modern_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import pyarrow

import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import sys
import os
import time
import logging
from typing import Dict, List, Optional, Tuple
import json
import numpy as np
import psutil

# Try to import auto-refresh, but make it optional
try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False
    st_autorefresh = None

# Configure logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import CLI component
try:
    from src.dashboard.components.cli_component import render_cli_tab
    HAS_CLI_COMPONENT = True
except ImportError as e:
    HAS_CLI_COMPONENT = False
    render_cli_tab = None
    logger.warning(f"CLI component not found: {e}")

# Import Orchestration component
try:
    from src.dashboard.components.orchestration_component import render_orchestration_control
    HAS_ORCHESTRATION_COMPONENT = True
except ImportError as e:
    HAS_ORCHESTRATION_COMPONENT = False
    render_orchestration_control = None
    logger.warning(f"Orchestration component not found: {e}")

# Import Document Generation component
try:
    from src.dashboard.components.document_generation_component import render_document_generation_tab
    HAS_DOCUMENT_COMPONENT = True
except ImportError as e:
    HAS_DOCUMENT_COMPONENT = False
    render_document_generation_tab = None
    logger.warning(f"Document generation component not found: {e}")

# Import background processor
try:
    from .background_processor import get_background_processor, get_document_generator
    HAS_BACKGROUND_PROCESSOR = True
except ImportError:
    HAS_BACKGROUND_PROCESSOR = False
    get_background_processor = None
    get_document_generator = None

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.job_database import ModernJobDatabase, get_job_db
    from src.utils.profile_helpers import get_available_profiles
except ImportError as e:
    st.error(f"❌ Failed to import required modules: {e}")
    st.info("💡 Make sure you're running from the project root directory")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="AutoJobAgent - Unified Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "auto_refresh" not in st.session_state:
    st.session_state["auto_refresh"] = False
if "selected_profile" not in st.session_state:
    st.session_state["selected_profile"] = None

# Load unified CSS from external file
def load_unified_css():
    """Load the unified CSS from the external file."""
    css_path = Path(__file__).parent / "styles" / "unified_dashboard_styles.css"
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        return f"<style>\n{css_content}\n</style>"
    except FileNotFoundError:
        # Fallback to inline CSS if file not found
        return """
        <style>
        /* Fallback CSS - Unified styles file not found */
        .stApp { background: #0f172a !important; color: #f1f5f9 !important; }
        .main { background: #0f172a !important; color: #f1f5f9 !important; }
        .stSidebar { background: #334155 !important; }
        .stButton > button { background: #3b82f6 !important; color: white !important; border-radius: 0.5rem !important; }
        .section-header { color: #f1f5f9; border-bottom: 2px solid #3b82f6; }
        </style>
        """

UNIFIED_CSS = load_unified_css()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_job_data(profile_name: str) -> pd.DataFrame:
    """Load job data from database with caching for improved performance."""
    try:
        db_path = f"profiles/{profile_name}/{profile_name}.db"
        
        if not Path(db_path).exists():
            logger.warning(f"Database file not found: {db_path}")
            return pd.DataFrame()

        db = ModernJobDatabase(db_path=db_path)
        jobs = db.get_jobs(limit=1000)
        
        if jobs:
            df = pd.DataFrame(jobs)
            # Ensure proper datetime parsing
            for date_col in ["posted_date", "scraped_at", "created_at", "updated_at"]:
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            
            # Add derived status based on the 4-stage pipeline
            # Default columns if they don't exist
            # For scraped: if jobs exist in DB, they are at least scraped (default to 1)
            # For others: default to 0 unless explicitly set
            if 'scraped' not in df.columns:
                df['scraped'] = 1  # Jobs in DB are already scraped
            
            for col in ['processed', 'document_created', 'applied']:
                if col not in df.columns:
                    df[col] = 0
            
            # Create status text based on database status field
            def get_status_text(row):
                status = row.get('status', 'scraped').lower()
                application_status = row.get('application_status', 'not_applied').lower()
                
                # Priority order: check application status first, then processing status
                if application_status == 'applied':
                    return 'Applied'
                elif application_status in ['documents_ready', 'document_created']:
                    return 'Document Created'
                elif status in ['processed', 'enhanced', 'analyzed']:
                    return 'Processed'
                elif status == 'scraped' or status is None:
                    return 'Scraped'
                else:
                    return 'New'
            
            df['status_text'] = df.apply(get_status_text, axis=1)
            
            # Add status stage number for sorting/filtering
            def get_status_stage(row):
                status_text = row['status_text']
                if status_text == 'Applied':
                    return 4
                elif status_text == 'Document Created':
                    return 3
                elif status_text == 'Processed':
                    return 2
                elif status_text == 'Scraped':
                    return 1
                else:
                    return 0
            
            df['status_stage'] = df.apply(get_status_stage, axis=1)
            
            # Add priority based on match_score or other criteria
            if 'match_score' in df.columns:
                df['priority'] = pd.cut(df['match_score'], 
                                      bins=[0, 33, 66, 100], 
                                      labels=['Low', 'Medium', 'High'],
                                      include_lowest=True)
            else:
                df['priority'] = 'Medium'
                
            return df
            
        return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Failed to load job data for profile {profile_name}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_system_metrics() -> Dict[str, any]:
    """Get system metrics including database stats and system info."""
    try:
        metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add network connectivity check
        try:
            import requests
            response = requests.get("https://www.google.com", timeout=5)
            metrics["network_status"] = "connected" if response.status_code == 200 else "disconnected"
        except Exception:
            metrics["network_status"] = "disconnected"
        
        # Add process information
        try:
            process_info = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                if proc.info['name'] and any(keyword in proc.info['name'].lower() for keyword in ['streamlit', 'python', 'ollama']):
                    process_info.append(proc.info)
            metrics["active_processes"] = process_info[:10]  # Limit to 10 processes
        except Exception as e:
            logger.warning(f"Could not get process information: {e}")
            metrics["active_processes"] = []
        
        # Add service status checks
        services_status = {}
        
        # Check if Streamlit is running on different ports
        import socket
        for port in [8501, 8502, 8503, 8505]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                services_status[f"streamlit_{port}"] = "running" if result == 0 else "stopped"
                sock.close()
            except Exception:
                services_status[f"streamlit_{port}"] = "unknown"
        
        # Check if Ollama is running (default port 11434)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', 11434))
            services_status["ollama"] = "running" if result == 0 else "stopped"
            sock.close()
        except Exception:
            services_status["ollama"] = "unknown"
        
        # Add orchestration services checks
        orchestration_status = {}
        
        # Check for background processes (scrapers, processors, etc.)
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = ' '.join(proc.info.get('cmdline', []))
                
                # Check for specific orchestration processes
                if 'main.py' in cmdline and any(action in cmdline for action in ['scrape', 'process', 'apply']):
                    if 'scrape' in cmdline:
                        orchestration_status['scraper'] = 'running'
                    elif 'process' in cmdline:
                        orchestration_status['processor'] = 'running'
                    elif 'apply' in cmdline:
                        orchestration_status['applicator'] = 'running'
                
                # Check for scheduler/cron processes
                if any(keyword in proc.info['name'].lower() for keyword in ['scheduler', 'cron', 'task']):
                    orchestration_status['scheduler'] = 'running'
                
                # Check for document generation processes
                if 'python' in proc.info['name'].lower() and any(keyword in cmdline for keyword in ['document', 'generate', 'create']):
                    orchestration_status['document_generator'] = 'running'
                    
        except Exception as e:
            logger.warning(f"Could not check orchestration processes: {e}")
        
        # Check background processor status if available
        if HAS_BACKGROUND_PROCESSOR:
            try:
                processor = get_background_processor()
                generator = get_document_generator()
                
                if processor:
                    proc_status = processor.get_status()
                    if proc_status['active']:
                        orchestration_status['processor'] = 'running'
                
                if generator:
                    gen_status = generator.get_status()
                    if gen_status['active']:
                        orchestration_status['document_generator'] = 'running'
                        
            except Exception as e:
                logger.warning(f"Could not check background processor status: {e}")
        
        # Set default status for services not detected
        default_services = ['scraper', 'processor', 'applicator', 'document_generator', 'scheduler']
        for service in default_services:
            if service not in orchestration_status:
                orchestration_status[service] = 'stopped'
        
        metrics["orchestration"] = orchestration_status
        
        # Add database-specific metrics if available
        try:
            from src.core.job_database import get_job_db
            db = get_job_db("Nirajan")  # Default profile for metrics
            stats = db.get_job_stats()
            metrics.update(stats)
        except Exception as e:
            logger.warning(f"Could not get database metrics: {e}")
            
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {}

def display_services_tab(profile_name: str) -> None:
    """Display the Services management tab with robust service control."""
    st.markdown("# 🛠️ Service Management")
    st.markdown("Manage and monitor core AutoJobAgent services with robust error handling.")
    
    try:
        from src.services.robust_service_manager import get_service_manager
        service_manager = get_service_manager()
        
        # Get current service health
        health = service_manager.get_service_health()
        
        # Display overall system status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            overall_status = health.get("overall_status", "unknown")
            status_color = {
                "healthy": "🟢",
                "degraded": "🟡", 
                "unhealthy": "🔴",
                "unknown": "⚪"
            }.get(overall_status, "⚪")
            
            st.markdown(f"### {status_color} System Status: {overall_status.title()}")
        
        with col2:
            system_info = health.get("system", {})
            cpu_percent = system_info.get("cpu_percent", 0)
            st.metric("CPU Usage", f"{cpu_percent:.1f}%")
        
        with col3:
            memory_percent = system_info.get("memory_percent", 0)
            st.metric("Memory Usage", f"{memory_percent:.1f}%")
        
        st.markdown("---")
        
        # Service control section
        st.markdown("## 🎛️ Service Control")
        
        # Quick actions
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🚀 Start All Services", key="start_all_services"):
                with st.spinner("Starting all services..."):
                    results = service_manager.start_all_services()
                    
                    success_count = sum(1 for success in results.values() if success)
                    total_count = len(results)
                    
                    if success_count == total_count:
                        st.success(f"✅ All {total_count} services started successfully!")
                    elif success_count > 0:
                        st.warning(f"⚠️ {success_count}/{total_count} services started successfully")
                    else:
                        st.error("❌ Failed to start services")
                    
                    # Show detailed results
                    for service_name, success in results.items():
                        status_icon = "✅" if success else "❌"
                        st.write(f"{status_icon} {service_name}: {'Started' if success else 'Failed'}")
        
        with col2:
            if st.button("🛑 Stop All Services", key="stop_all_services"):
                with st.spinner("Stopping all services..."):
                    results = service_manager.stop_all_services()
                    
                    success_count = sum(1 for success in results.values() if success)
                    total_count = len(results)
                    
                    if success_count == total_count:
                        st.success(f"✅ All {total_count} services stopped successfully!")
                    else:
                        st.warning(f"⚠️ {success_count}/{total_count} services stopped")
        
        with col3:
            if st.button("🔄 Refresh Status", key="refresh_services"):
                st.rerun()
        
        with col4:
            if st.button("🔧 Health Check", key="health_check"):
                with st.spinner("Running health check..."):
                    health = service_manager.get_service_health()
                    st.success("✅ Health check completed!")
        
        st.markdown("---")
        
        # Individual service management
        st.markdown("## 📋 Individual Services")
        
        services = health.get("services", {})
        
        for service_name, service_info in services.items():
            with st.expander(f"🔧 {service_info.get('description', service_name)}", expanded=False):
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    status = service_info.get("status", "unknown")
                    status_icons = {
                        "running": "🟢 Running",
                        "stopped": "🔴 Stopped",
                        "starting": "🟡 Starting",
                        "error": "❌ Error",
                        "unknown": "⚪ Unknown"
                    }
                    st.markdown(f"**Status:** {status_icons.get(status, status)}")
                    
                    if service_info.get("required", False):
                        st.markdown("**Required:** ✅ Yes")
                    else:
                        st.markdown("**Required:** ❌ No")
                
                with col2:
                    if service_info.get("pid"):
                        st.markdown(f"**PID:** {service_info['pid']}")
                    
                    if service_info.get("port"):
                        st.markdown(f"**Port:** {service_info['port']}")
                
                with col3:
                    if service_info.get("error"):
                        st.error(f"**Error:** {service_info['error']}")
                    
                    if service_info.get("last_check"):
                        import datetime
                        last_check = datetime.datetime.fromtimestamp(service_info['last_check'])
                        st.markdown(f"**Last Check:** {last_check.strftime('%H:%M:%S')}")
                
                # Service control buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"🚀 Start", key=f"start_{service_name}"):
                        with st.spinner(f"Starting {service_name}..."):
                            success = service_manager.start_service(service_name)
                            if success:
                                st.success(f"✅ {service_name} started successfully!")
                            else:
                                st.error(f"❌ Failed to start {service_name}")
                            time.sleep(1)
                            st.rerun()
                
                with col2:
                    if st.button(f"🛑 Stop", key=f"stop_{service_name}"):
                        with st.spinner(f"Stopping {service_name}..."):
                            success = service_manager.stop_service(service_name)
                            if success:
                                st.success(f"✅ {service_name} stopped successfully!")
                            else:
                                st.error(f"❌ Failed to stop {service_name}")
                            time.sleep(1)
                            st.rerun()
                
                with col3:
                    if st.button(f"🔄 Restart", key=f"restart_{service_name}"):
                        with st.spinner(f"Restarting {service_name}..."):
                            success = service_manager.restart_service(service_name)
                            if success:
                                st.success(f"✅ {service_name} restarted successfully!")
                            else:
                                st.error(f"❌ Failed to restart {service_name}")
                            time.sleep(1)
                            st.rerun()
        
        # Service logs section
        st.markdown("---")
        st.markdown("## 📄 Service Logs")
        
        if st.button("📋 View Recent Logs", key="view_logs"):
            try:
                log_files = [
                    "logs/error_logs.log",
                    "logs/scraper.log", 
                    "logs/processor.log"
                ]
                
                for log_file in log_files:
                    if Path(log_file).exists():
                        with st.expander(f"📄 {log_file}", expanded=False):
                            try:
                                with open(log_file, 'r') as f:
                                    lines = f.readlines()
                                    # Show last 50 lines
                                    recent_lines = lines[-50:] if len(lines) > 50 else lines
                                    st.text_area(
                                        f"Recent entries from {log_file}:",
                                        value=''.join(recent_lines),
                                        height=200,
                                        key=f"log_{log_file.replace('/', '_')}"
                                    )
                            except Exception as e:
                                st.error(f"Error reading {log_file}: {e}")
                    else:
                        st.info(f"Log file {log_file} not found")
            except Exception as e:
                st.error(f"Error accessing logs: {e}")
        
        # Auto-refresh option
        st.markdown("---")
        auto_refresh = st.checkbox("🔄 Auto-refresh every 10 seconds", key="services_auto_refresh")
        
        if auto_refresh:
            time.sleep(10)
            st.rerun()
            
    except ImportError as e:
        st.error(f"❌ Service manager not available: {e}")
        st.info("💡 The robust service manager component is not installed or configured properly.")
        
        # Fallback basic service status
        st.markdown("## 📊 Basic Service Status")
        
        # Check basic services manually
        import socket
        import subprocess
        
        services_to_check = {
            "Ollama (AI Service)": ("localhost", 11434),
            "Streamlit Dashboard": ("localhost", 8501),
        }
        
        for service_name, (host, port) in services_to_check.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    st.success(f"✅ {service_name}: Running on {host}:{port}")
                else:
                    st.error(f"❌ {service_name}: Not running on {host}:{port}")
            except Exception as e:
                st.warning(f"⚠️ {service_name}: Could not check status - {e}")
        
        # Manual service start buttons
        st.markdown("### 🚀 Manual Service Control")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🤖 Start Ollama", key="manual_start_ollama"):
                try:
                    subprocess.Popen(["ollama", "serve"], 
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
                    st.success("✅ Ollama start command sent!")
                    st.info("⏳ Please wait a few seconds for Ollama to start...")
                except Exception as e:
                    st.error(f"❌ Failed to start Ollama: {e}")
        
        with col2:
            if st.button("⚙️ Start Job Processor", key="manual_start_processor"):
                try:
                    subprocess.Popen([sys.executable, "main.py", "--action", "process", "--headless"],
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
                    st.success("✅ Job processor start command sent!")
                    st.info("⏳ Please wait a few seconds for the processor to start...")
                except Exception as e:
                    st.error(f"❌ Failed to start job processor: {e}")
    
    except Exception as e:
        st.error(f"❌ Unexpected error in Services tab: {e}")
        logger.error(f"Services tab error: {e}", exc_info=True)

def display_enhanced_metrics(df: pd.DataFrame) -> None:
    """Display enhanced metrics with modern styling."""
    if df.empty:
        st.warning("📊 No data available for metrics")
        return
    
    # Calculate metrics based on 4-stage pipeline
    total_jobs = len(df)
    scraped_jobs = len(df[df.get('scraped', 0) == 1]) if 'scraped' in df.columns else total_jobs
    processed_jobs = len(df[df.get('processed', 0) == 1]) if 'processed' in df.columns else 0
    document_created_jobs = len(df[df.get('document_created', 0) == 1]) if 'document_created' in df.columns else 0
    applied_jobs = len(df[df.get('applied', 0) == 1]) if 'applied' in df.columns else 0
    
    # Calculate additional metrics
    unique_companies = df['company'].nunique() if 'company' in df.columns else 0
    avg_match_score = df['match_score'].mean() if 'match_score' in df.columns else 0
    
    # Recent activity (last 7 days)
    if 'created_at' in df.columns:
        recent_jobs = len(df[df['created_at'] > (datetime.now() - timedelta(days=7))])
    else:
        recent_jobs = 0
    
    st.markdown('<h2 class="section-header">📊 Job Pipeline Metrics</h2>', unsafe_allow_html=True)
    
    # Display metrics in columns - showing the 4-stage pipeline
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Jobs</div>
                <div class="metric-value">{total_jobs:,}</div>
                <div class="metric-delta positive">+{recent_jobs} this week</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        processing_rate = (processed_jobs / scraped_jobs * 100) if scraped_jobs > 0 else 0
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Processed</div>
                <div class="metric-value">{processed_jobs:,}</div>
                <div class="metric-delta positive">{processing_rate:.1f}% rate</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        document_rate = (document_created_jobs / processed_jobs * 100) if processed_jobs > 0 else 0
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Documents</div>
                <div class="metric-value">{document_created_jobs:,}</div>
                <div class="metric-delta positive">{document_rate:.1f}% rate</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col4:
        application_rate = (applied_jobs / document_created_jobs * 100) if document_created_jobs > 0 else 0
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Applied</div>
                <div class="metric-value">{applied_jobs:,}</div>
                <div class="metric-delta positive">{application_rate:.1f}% rate</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col5:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Avg Match</div>
                <div class="metric-value">{avg_match_score:.0f}%</div>
                <div class="metric-delta">Job relevance</div>
            </div>
            """,
            unsafe_allow_html=True
        )


def display_job_cards(df: pd.DataFrame, limit: int = 6) -> None:
    """Display job cards with proper Streamlit components instead of HTML."""
    if df.empty:
        st.info("🚀 Start scraping to see job opportunities here!")
        return
    
    st.markdown('<h3 class="section-header">💼 Recent Opportunities</h3>', unsafe_allow_html=True)
    
    # Sort by created_at if available, otherwise by index
    if 'created_at' in df.columns:
        recent_jobs = df.sort_values('created_at', ascending=False).head(limit)
    else:
        recent_jobs = df.head(limit)
    
    # Display in a grid using proper Streamlit components
    cols = st.columns(2)
    for idx, (_, job) in enumerate(recent_jobs.iterrows()):
        col = cols[idx % 2]
        with col:
            company = job.get('company', 'Unknown Company')
            title = job.get('title', 'Unknown Position')
            location = job.get('location', 'Location not specified')
            match_score = job.get('match_score', 0)
            job_url = job.get('url', job.get('job_url', ''))
            status_text = job.get('status_text', 'New')
            priority = job.get('priority', 'Medium')
            # Use Streamlit markdown for header, but avoid raw HTML for actions
            st.markdown(f"**{title}** at **{company}**")
            st.write(f"📍 {location}")
            st.write(f"🔍 Status: {status_text} | 🎯 Priority: {priority} | Match: {match_score:.0f}%")
            button_col1, button_col2 = st.columns(2)
            with button_col1:
                if job_url:
                    st.link_button("🔗 View Job", job_url)
                else:
                    st.button("🔗 No URL", disabled=True, key=f"no_url_recent_{idx}")
            with button_col2:
                if st.button("📋 Copy", key=f"copy_recent_{idx}_{hash(str(title))}", help="Copy job info"):
                    job_info = f"{title} at {company} - {location}"
                    st.success(f"Job info copied!")
            st.divider()


def display_analytics_tab(df: pd.DataFrame) -> None:
    """Display simplified analytics without heavy charts."""
    if df.empty:
        st.warning("📈 No data available for analytics")
        return
    
    st.markdown('<h2 class="section-header">📈 Job Analytics</h2>', unsafe_allow_html=True)
    
    # Simple status overview
    if 'status_text' in df.columns:
        st.markdown("### 📊 Pipeline Status")
        
        status_counts = df['status_text'].value_counts()
        
        # Display as simple metrics instead of charts
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            scraped = status_counts.get('Scraped', 0)
            st.metric("🔍 Scraped", scraped)
        
        with col2:
            processed = status_counts.get('Processed', 0)
            st.metric("⚙️ Processed", processed)
        
        with col3:
            docs = status_counts.get('Document Created', 0)
            st.metric("📄 Documents", docs)
        
        with col4:
            applied = status_counts.get('Applied', 0)
            st.metric("✅ Applied", applied)
        
        with col5:
            total = len(df)
            st.metric("📋 Total", total)
    
    # Simple company breakdown
    if 'company' in df.columns:
        st.markdown("### 🏢 Top Companies")
        company_counts = df['company'].value_counts().head(10)
        
        if not company_counts.empty:
            for company, count in company_counts.items():
                st.markdown(f"• **{company}**: {count} jobs")
        else:
            st.info("No company data available")
    
    # Recent activity
    if 'created_at' in df.columns:
        st.markdown("### 📅 Recent Activity")
        
        # Jobs added in last 7 days
        recent_jobs = len(df[df['created_at'] > (datetime.now() - timedelta(days=7))])
        today_jobs = len(df[df['created_at'].dt.date == datetime.now().date()])
        
        recent_col1, recent_col2 = st.columns(2)
        
        with recent_col1:
            st.metric("This Week", recent_jobs)
        
        with recent_col2:
            st.metric("Today", today_jobs)

def apply_to_job_streamlit(job_id: int, job_title: str, company: str, job_url: str, profile_name: str, mode: str) -> None:
    """Apply to a job from the Streamlit dashboard."""
    try:
        from src.core.job_database import get_job_db
        
        with st.spinner("Processing application..."):
            db = get_job_db(profile_name)
            
            if "Manual" in mode:
                # Manual mode: mark as applied and open URL
                db.update_application_status(job_id, "applied", "Applied via Dashboard (Manual)")
                st.success(f"✅ Marked as applied: {job_title} at {company}")
                st.markdown(f"🔗 [**Click here to open job page in new tab**]({job_url})")
                
            elif "Hybrid" in mode:
                try:
                    # Hybrid mode: use applier if available
                    try:
                        from src.job_applier.job_applier import JobApplier
                    except ImportError:
                        try:
                            from src.job_applier import JobApplier
                        except ImportError:
                            st.warning("⚠️ Job applier module not available. Falling back to manual mode.")
                            db.update_application_status(job_id, "applied", "Applied via Dashboard (Manual Fallback)")
                            st.success(f"✅ Marked as applied: {job_title} at {company}")
                            st.markdown(f"🔗 [**Click here to open job page in new tab**]({job_url})")
                            return
                    applier = JobApplier(profile_name=profile_name)
                    result = applier.apply_to_job(job_url)
                    if result.get("success"):
                        db.update_application_status(job_id, "applied", "Applied via Dashboard (Hybrid)")
                        st.success(f"✅ Application completed: {job_title} at {company}")
                        if result.get("details"):
                            st.info(f"Details: {result['details']}")
                    else:
                        st.error(f"❌ Application failed: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error in hybrid application: {str(e)}")
                    # Fallback to manual mode
                    db.update_application_status(job_id, "applied", "Applied via Dashboard (Manual Fallback)")
                    st.success(f"✅ Marked as applied: {job_title} at {company}")
                    st.markdown(f"🔗 [**Click here to open job page in new tab**]({job_url})")
            
            # Auto-refresh the page after 2 seconds
            time.sleep(2)
            st.rerun()
                
    except Exception as e:
        st.error(f"❌ Error applying to job: {str(e)}")
        logger.error(f"Apply error: {e}")


def display_jobs_table(df: pd.DataFrame, profile_name: str = None) -> None:
    """Display jobs in a searchable, filterable table."""
    if df.empty:
        st.warning("📋 No jobs to display")
        return
    
    st.markdown('<h2 class="section-header">📋 Job Management</h2>', unsafe_allow_html=True)
    
    # Filters (now with salary, experience, job type)
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        with col1:
            companies = ["All"] + sorted(df['company'].dropna().unique().tolist())
            selected_company = st.selectbox("🏢 Company", companies)
        with col2:
            status_options = ["All", "New", "Scraped", "Processed", "Document Created", "Applied"]
            selected_status = st.selectbox("📊 Status", status_options)
        with col3:
            priority_options = ["All"] + sorted(df['priority'].dropna().unique().tolist())
            selected_priority = st.selectbox("🎯 Priority", priority_options)
        with col4:
            job_type_options = ["All"] + sorted(df['job_type'].dropna().unique().tolist()) if 'job_type' in df.columns else ["All"]
            selected_job_type = st.selectbox("�️ Job Type", job_type_options)
        with col5:
            experience_options = ["All"] + sorted(df['experience_level'].dropna().unique().tolist()) if 'experience_level' in df.columns else ["All"]
            selected_experience = st.selectbox("🧑‍💼 Experience", experience_options)
        with col6:
            salary_options = ["All"] + sorted(df['salary'].dropna().unique().tolist()) if 'salary' in df.columns else ["All"]
            selected_salary = st.selectbox("💰 Salary", salary_options)
        with col7:
            search_term = st.text_input("🔍 Search", placeholder="Search jobs...")
        st.markdown('</div>', unsafe_allow_html=True)
    # Apply filters
    filtered_df = df.copy()
    if selected_company != "All":
        filtered_df = filtered_df[filtered_df['company'] == selected_company]
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df['status_text'] == selected_status]
    if selected_priority != "All":
        filtered_df = filtered_df[filtered_df['priority'] == selected_priority]
    if selected_job_type != "All" and 'job_type' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['job_type'] == selected_job_type]
    if selected_experience != "All" and 'experience_level' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['experience_level'] == selected_experience]
    if selected_salary != "All" and 'salary' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['salary'] == selected_salary]
    if search_term:
        mask = (
            filtered_df['title'].str.contains(search_term, case=False, na=False) |
            filtered_df['company'].str.contains(search_term, case=False, na=False) |
            filtered_df['location'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    # Display results
    st.write(f"**Found {len(filtered_df)} jobs** (filtered from {len(df)} total)")
    if not filtered_df.empty:
        # Select columns to display - now with salary, experience, job type
        display_columns = ['title', 'company', 'location', 'job_type', 'experience_level', 'salary', 'status_text', 'priority', 'match_score', 'url']
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        display_df = filtered_df[available_columns].copy()
        # Add status emojis
        if 'status_text' in display_df.columns:
            status_emoji_map = {
                'New': '⭕ New',
                'Scraped': '🔍 Scraped', 
                'Processed': '⚙️ Processed',
                'Document Created': '📄 Document Created',
                'Applied': '✅ Applied'
            }
            display_df['status_text'] = display_df['status_text'].map(status_emoji_map)
        if 'match_score' in display_df.columns:
            display_df['match_score'] = display_df['match_score'].apply(lambda x: f"{x:.0f}%")
        # Enhanced table or fallback
        try:
            from src.dashboard.components.enhanced_job_table import render_enhanced_job_table, display_job_details
            result = render_enhanced_job_table(filtered_df, st.session_state.get("selected_profile", "default"))
            if result is None:
                selected_job, selected_indices = None, []
            else:
                selected_job, selected_indices = result
            if selected_job:
                display_job_details(selected_job, filtered_df)
        except ImportError as e:
            st.error(f"Enhanced table component not available: {e}")
            st.info("Falling back to basic table display...")
            # Fallback to basic table with multi-select checkboxes
            display_columns = ['title', 'company', 'location', 'job_type', 'experience_level', 'salary', 'status_text', 'priority', 'match_score']
            available_columns = [col for col in display_columns if col in filtered_df.columns]
            if available_columns:
                st.dataframe(
                    filtered_df[available_columns],
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
            # Multi-select for batch apply
            st.markdown("### 🎯 Batch Apply to Jobs")
            apply_indices = st.multiselect("Select jobs to apply:", filtered_df.index.tolist(), help="Select multiple jobs for batch apply")
            if apply_indices:
                mode = st.radio(
                    "Application method:",
                    ["Manual (Mark as applied)", "Hybrid (AI-assisted)"],
                    key="batch_apply_mode"
                )
                if st.button("🚀 Apply to Selected Jobs", type="primary"):
                    for idx in apply_indices:
                        row = filtered_df.loc[idx]
                        apply_to_job_streamlit(
                            row.get('id', idx),
                            row.get('title', 'Unknown Job'),
                            row.get('company', 'Unknown Company'),
                            row.get('url', ''),
                            profile_name,
                            mode
                        )
                    st.success(f"Applied to {len(apply_indices)} jobs!")
                    st.experimental_rerun()
            else:
                st.info("✅ All visible jobs have been applied to!")

def display_system_tab(profile_name: str) -> None:
    """Display enhanced system information and orchestration controls with integrated CLI."""
    st.markdown('<h2 class="section-header">🖥️ System Command & Information Center</h2>', unsafe_allow_html=True)
    
    # Main orchestration controls - prominently displayed first
    if HAS_ORCHESTRATION_COMPONENT:
        st.markdown("### 🎛️ Quick Orchestration Controls")
        
        # Quick action buttons for core services
        col1, col2, col3, col4 = st.columns(4)
        
        from src.dashboard.components.orchestration_component import EnhancedOrchestrationComponent
        orchestration = EnhancedOrchestrationComponent(profile_name)
        
        with col1:
            if st.button("🚀 Start Core Pipeline", use_container_width=True):
                orchestration._start_all_services()
        
        with col2:
            if st.button("⏹️ Stop Core Pipeline", use_container_width=True):
                orchestration._stop_all_services()
        
        with col3:
            if st.button("🚀 Start 3 Workers", use_container_width=True):
                orchestration._start_n_workers(3)
        
        with col4:
            if st.button("⏹️ Stop All Workers", use_container_width=True):
                orchestration._stop_worker_pool()
        
        st.markdown("---")
    
    # Create sub-tabs for detailed orchestration features
    system_tabs = st.tabs([
        "🎛️ Service Control", 
        "👥 5-Worker Pool", 
        "📊 Monitoring", 
        "🤖 Auto-Management",
        "🖥️ CLI Commands"
    ])
    
    with system_tabs[0]:  # Service Control
        if HAS_ORCHESTRATION_COMPONENT:
            # Use the enhanced orchestration component - Service Control section
            from src.dashboard.components.orchestration_component import EnhancedOrchestrationComponent
            orchestration = EnhancedOrchestrationComponent(profile_name)
            orchestration._render_service_control_panel()
        else:
            _render_fallback_service_control(profile_name)
    
    with system_tabs[1]:  # 5-Worker Pool
        if HAS_ORCHESTRATION_COMPONENT:
            # Worker Pool Management section
            from src.dashboard.components.orchestration_component import EnhancedOrchestrationComponent
            orchestration = EnhancedOrchestrationComponent(profile_name)
            orchestration._render_worker_pool_management()
        else:
            _render_fallback_worker_info()
    
    with system_tabs[2]:  # Monitoring
        if HAS_ORCHESTRATION_COMPONENT:
            # Service Monitoring section
            from src.dashboard.components.orchestration_component import EnhancedOrchestrationComponent
            orchestration = EnhancedOrchestrationComponent(profile_name)
            orchestration._render_service_monitoring()
        else:
            _render_fallback_monitoring()
    
    with system_tabs[3]:  # Auto-Management
        if HAS_ORCHESTRATION_COMPONENT:
            # Auto-Management panel
            from src.dashboard.components.orchestration_component import EnhancedOrchestrationComponent
            orchestration = EnhancedOrchestrationComponent(profile_name)
            orchestration._render_auto_management_panel()
        else:
            _render_fallback_auto_management()
    
    with system_tabs[4]:  # CLI Commands
        _render_integrated_cli_commands(profile_name)


def _render_fallback_service_control(profile_name: str):
    """Fallback service control when orchestration component unavailable."""
    st.markdown("### 🔧 Manual Service Controls")
    st.warning("⚠️ Enhanced orchestration component not available. Use manual commands.")
    
    # Basic system information
    try:
        import psutil
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cpu_percent = psutil.cpu_percent()
            st.metric("System CPU", f"{cpu_percent:.1f}%")
        
        with col2:
            memory = psutil.virtual_memory()
            st.metric("System Memory", f"{memory.percent:.1f}%")
        
        with col3:
            disk = psutil.disk_usage('/')
            st.metric("Disk Usage", f"{disk.percent:.1f}%")
            
    except ImportError:
        st.warning("Install 'psutil' for system monitoring")
    
    # Manual service commands
    service_commands = [
        f"python main.py {profile_name} --action scrape --sites eluta",
        f"python main.py {profile_name} --action process-jobs",
        f"python main.py {profile_name} --action generate-docs",
        f"python main.py {profile_name} --action apply --batch 5"
    ]
    
    for i, cmd in enumerate(service_commands, 1):
        st.markdown(f"**{i}. Service Command:**")
        st.code(cmd, language="bash")


def _render_fallback_worker_info():
    """Fallback worker pool information."""
    st.markdown("### 👥 5-Worker Document Generation")
    st.info("""
    **Enhanced 5-Worker Document Generation Features:**
    - 🔄 Parallel processing of 5 jobs simultaneously
    - 📁 Automatic folder creation per job application
    - ✏️ Intelligent resume customization per job
    - 📄 AI-powered cover letter generation
    - 📊 Individual worker progress tracking
    """)
    
    st.markdown("**Manual Worker Commands:**")
    worker_commands = [
        "python main.py {profile} --action generate-docs --worker 1",
        "python main.py {profile} --action generate-docs --worker 2", 
        "python main.py {profile} --action generate-docs --worker 3",
        "python main.py {profile} --action generate-docs --worker 4",
        "python main.py {profile} --action generate-docs --worker 5"
    ]
    
    for cmd in worker_commands:
        st.code(cmd, language="bash")


def _render_fallback_monitoring():
    """Fallback monitoring panel."""
    st.markdown("### 📊 System Monitoring")
    
    try:
        import psutil
        
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("CPU Usage", f"{cpu_percent:.1f}%")
            
        with col2:
            memory = psutil.virtual_memory()
            st.metric("Memory Usage", f"{memory.percent:.1f}%")
        
        # Process information
        st.markdown("#### 🔍 Python Processes")
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if 'python' in proc.info['name'].lower():
                    python_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if python_processes:
            st.dataframe(python_processes, use_container_width=True)
        else:
            st.info("No Python processes detected")
            
    except ImportError:
        st.warning("Install 'psutil' for detailed system monitoring")


def _render_fallback_auto_management():
    """Fallback auto-management information.""" 
    st.markdown("### 🤖 Auto-Management Features")
    st.info("""
    **Smart Auto-Start/Stop Logic (Available with full orchestration):**
    - �� Auto-start scraper when job count drops below threshold
    - ⚙️ Auto-start processor when scraped jobs exceed threshold
    - 👥 Auto-start workers when processed jobs accumulate
    - ✉️ Auto-start applicator when documents are ready
    - 🛑 Auto-stop services after idle timeout
    - 🧠 Resource-aware service management
    """)
    
    st.markdown("**Manual Scheduling Options:**")
    st.code("# Add to crontab for automated runs", language="bash")
    st.code("0 9 * * * cd /path/to/automate_job && python main.py YourProfile --action scrape", language="bash")
    st.code("0 10 * * * cd /path/to/automate_job && python main.py YourProfile --action process-jobs", language="bash")


def _render_integrated_cli_commands(profile_name: str):
    """Render integrated CLI commands within the System tab."""
    st.markdown("### 🖥️ Integrated CLI Commands")
    st.info("Execute all CLI operations directly from the dashboard with real-time output and status tracking.")
    
    if HAS_CLI_COMPONENT and render_cli_tab:
        # Use the full CLI component
        render_cli_tab(profile_name)
    else:
        # Fallback command interface
        st.markdown("#### 🚀 Quick Command Execution")
        
        # Command categories
        command_categories = {
            "🔍 Scraping Commands": [
                f"python main.py {profile_name} --action scrape --sites eluta",
                f"python main.py {profile_name} --action scrape --sites indeed,linkedin",
                f"python main.py {profile_name} --action scrape --keywords 'Python,Data Analyst'",
                f"python main.py {profile_name} --action scrape --sites eluta --keywords 'AI,ML'"
            ],
            "⚙️ Processing Commands": [
                f"python main.py {profile_name} --action process-jobs",
                f"python main.py {profile_name} --action process-jobs --min-score 80",
                f"python main.py {profile_name} --action reset-jobs --status scraped"
            ],
            "📄 Document Generation": [
                f"python main.py {profile_name} --action generate-docs",
                f"python main.py {profile_name} --action generate-docs --batch 5",
                f"python main.py {profile_name} --action enhance-jobs"
            ],
            "✉️ Application Commands": [
                f"python main.py {profile_name} --action apply --batch 5",
                f"python main.py {profile_name} --action apply --max-applications 10",
                f"python main.py {profile_name} --action benchmark"
            ],
            "🎛️ System Commands": [
                f"python main.py {profile_name} --action dashboard",
                f"python main.py {profile_name} --action status",
                "python clean_database.py",
                "python -m pytest tests/"
            ]
        }
        
        for category, commands in command_categories.items():
            with st.expander(category, expanded=(category == "🔍 Scraping Commands")):
                for cmd in commands:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.code(cmd, language="bash")
                    with col2:
                        if st.button("📋 Copy", key=f"copy_{hash(cmd)}", help="Copy to clipboard"):
                            st.success("Copied!")
                            # Note: Actual clipboard functionality would require additional JS
        
        st.markdown("#### 💡 Usage Tips")
        st.info("""
        - **Copy commands** to your terminal for execution
        - **Modify parameters** like keywords, sites, and batch sizes as needed
        - **Check logs** in the Logs tab for command output
        - **Monitor progress** in the Overview tab metrics
        """)
        
        # Command builder
        st.markdown("#### 🛠️ Custom Command Builder")
        
        with st.form("command_builder"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                action = st.selectbox("Action", [
                    "scrape", "process-jobs", "generate-docs", "apply", 
                    "benchmark", "status", "dashboard"
                ])
            
            with col2:
                if action == "scrape":
                    sites = st.multiselect("Sites", ["eluta", "indeed", "linkedin", "monster"], key="cmd_builder_sites")
                    keywords = st.text_input("Keywords (comma-separated)", key="cmd_builder_keywords")
                elif action in ["apply", "generate-docs"]:
                    batch_size = st.number_input("Batch Size", min_value=1, max_value=20, value=5, key="cmd_builder_batch")
            
            with col3:
                if action == "process-jobs":
                    min_score = st.number_input("Min Score", min_value=0, max_value=100, value=70, key="cmd_builder_score")
            
            if st.form_submit_button("🔨 Build Command"):
                cmd_parts = [f"python main.py {profile_name} --action {action}"]
                
                if action == "scrape":
                    if sites:
                        cmd_parts.append(f"--sites {','.join(sites)}")
                    if keywords:
                        cmd_parts.append(f"--keywords '{keywords}'")
                elif action in ["apply", "generate-docs"] and 'batch_size' in locals():
                    cmd_parts.append(f"--batch {batch_size}")
                elif action == "process-jobs" and 'min_score' in locals():
                    cmd_parts.append(f"--min-score {min_score}")
                
                built_command = " ".join(cmd_parts)
                st.code(built_command, language="bash")
                st.success("✅ Command built! Copy and run in terminal.")

def display_cli_tab(profile_name: str) -> None:
    """Display CLI Interface tab - now integrated into System tab."""
    st.markdown('<h2 class="section-header">🖥️ CLI Interface</h2>', unsafe_allow_html=True)
    
    # Info about integration
    st.info("""
    **🎯 CLI Integration Update:** 
    The CLI interface has been integrated into the **🎛️ System & Smart Orchestration** tab 
    for a more unified control experience.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔄 What's Changed")
        st.markdown("""
        - **✅ Integrated Controls**: CLI commands now available in System tab
        - **✅ Real-time Output**: See command execution in real-time
        - **✅ Service Integration**: Commands directly start/stop services
        - **✅ Progress Tracking**: Monitor command execution status
        - **✅ Command History**: Track all executed operations
        """)
    
    with col2:
        st.markdown("### 🚀 Quick Access")
        if st.button("🎛️ Go to System Tab", use_container_width=True):
            st.info("💡 Click on the 'System & Smart Orchestration' tab above")
        
        st.markdown("### 🎯 Available Features")
        st.markdown("""
        - **🖥️ CLI Commands**: Full command interface
        - **🎛️ Service Control**: Smart orchestration panel  
        - **👥 5-Worker Pool**: Parallel document generation
        - **📊 Monitoring**: Real-time system metrics
        - **🤖 Auto-Management**: Intelligent automation
        """)
    
    # Show legacy CLI if component is available
    if HAS_CLI_COMPONENT and render_cli_tab:
        st.markdown("---")
        st.markdown("### 🔧 Legacy CLI Interface (Deprecated)")
        st.warning("This interface is deprecated and may cause key conflicts. Use the integrated version in the System tab.")
        st.info("💡 The CLI interface has been moved to the System tab for better integration.")
    else:
        st.markdown("---")
        st.markdown("### 💡 Quick Commands")
        st.info("Common CLI commands you can run in a terminal:")
        
        quick_commands = [
            f"python main.py {profile_name} --action scrape --sites eluta",
            f"python main.py {profile_name} --action process-jobs",
            f"python main.py {profile_name} --action generate-docs",
            f"python main.py {profile_name} --action apply --batch 5"
        ]
        
        for i, cmd in enumerate(quick_commands, 1):
            st.markdown(f"**{i}. {cmd.split('--action ')[1].split(' ')[0].title()}:**")
            st.code(cmd, language="bash")


def display_logs_tab() -> None:
    """Display logs from various orchestrator log files with live refresh, search, and filtering."""
    st.markdown('<h2 class="section-header">📄 System & Orchestrator Logs</h2>', unsafe_allow_html=True)

    log_files = {
        "CLI Orchestrator": "logs/cli_orchestrator.log",
        "Scraping Orchestrator": "logs/scraping_orchestrator.log",
        "Application Orchestrator": "logs/application_orchestrator.log",
        "Dashboard Orchestrator": "logs/dashboard_orchestrator.log",
        "System Orchestrator": "logs/system_orchestrator.log",
        "Main Log": "logs/autojobagent.log",
        "Error Log": "error_logs.log"
    }

    log_choice = st.selectbox("Select Log File", list(log_files.keys()))
    log_file_path = Path(log_files[log_choice])

    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 Search log entries", "", key="log_search")
    with col2:
        log_level = st.selectbox("Log Level", ["ALL", "INFO", "WARNING", "ERROR", "CRITICAL"], key="log_level")

    refresh = st.button("🔄 Refresh Log", key="refresh_log")
    auto_refresh = st.checkbox("Live Update (every 2s)", value=False, key="auto_refresh_log")
    if auto_refresh:
        import time
        st_autorefresh(interval=2000, key="log_auto_refresh")

    if log_file_path.exists():
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                log_content = f.read()[-10000:]  # Only last 10k chars
            log_lines = log_content.splitlines()
            # Filter by search term
            if search_term:
                log_lines = [line for line in log_lines if search_term.lower() in line.lower()]
            # Filter by log level
            if log_level != "ALL":
                log_lines = [line for line in log_lines if f" {log_level} " in line]
            if log_lines:
                # Color-coding for log levels
                def color_line(line):
                    if " ERROR " in line or " CRITICAL " in line:
                        return f'<span style="color:#ef4444">{line}</span>'
                    elif " WARNING " in line:
                        return f'<span style="color:#f59e0b">{line}</span>'
                    elif " INFO " in line:
                        return f'<span style="color:#10b981">{line}</span>'
                    else:
                        return line
                html = "<br>".join([color_line(line) for line in log_lines])
                st.markdown(f'<div style="font-family:monospace;font-size:13px;">{html}</div>', unsafe_allow_html=True)
            else:
                st.info("No log entries match your filter.")
        except Exception as e:
            st.error(f"Error reading log file: {e}")
    else:
        st.warning(f"Log file not found: {log_file_path}")

def display_configuration_tab() -> None:
    """Display configuration management tab."""
    st.markdown('<h2 class="section-header">🔧 Configuration Management</h2>', unsafe_allow_html=True)
    
    config_files = get_config_files()
    
    if not config_files:
        st.warning("No configuration files found.")
        return

    selected_file = st.selectbox("Select a configuration file to edit:", config_files)
    
    if selected_file:
        try:
            file_path = Path(selected_file)
            content = file_path.read_text(encoding="utf-8")
            
            st.markdown(f"#### Editing: `{selected_file}`")
            
            edited_content = st.text_area(
                "File content", 
                content, 
                height=500,
                key=f"editor_{selected_file}"
            )
            
            if st.button("💾 Save Changes"):
                try:
                    file_path.write_text(edited_content, encoding="utf-8")
                    st.success(f"✅ Successfully saved changes to `{selected_file}`")
                except Exception as e:
                    st.error(f"❌ Failed to save file: {e}")

        except Exception as e:
            st.error(f"❌ Failed to read file: {e}")


def get_config_files() -> List[str]:
    """Get list of editable configuration files."""
    config_files = []
    
    # Common configuration file locations
    config_paths = [
        project_root / "config",
        project_root / "profiles",
        project_root / "requirements.txt",
        project_root / "pyproject.toml",
        project_root / "health_config.json"
    ]
    
    for path in config_paths:
        if path.is_file():
            # Single file
            config_files.append(str(path))
        elif path.is_dir():
            # Directory - find config files
            for file_path in path.rglob("*.json"):
                config_files.append(str(file_path))
            for file_path in path.rglob("*.toml"):
                config_files.append(str(file_path))
            for file_path in path.rglob("*.yaml"):
                config_files.append(str(file_path))
            for file_path in path.rglob("*.yml"):
                config_files.append(str(file_path))
            for file_path in path.rglob("*.ini"):
                config_files.append(str(file_path))
    
    return sorted(config_files)

def display_profile_management_sidebar(profiles: List[str], selected_profile: str) -> str:
    """Display enhanced profile management in sidebar."""
    st.markdown(
        """
        <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color); margin-bottom: 1rem;">
            <h3 style="margin: 0; color: var(--text-primary);">👤 Profile Management</h3>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Profile selector
    new_selected = st.selectbox(
        "Active Profile",
        profiles,
        index=profiles.index(selected_profile) if selected_profile in profiles else 0,
        key="profile_selector"
    )
    
    # Auto-start background processing when profile changes
    if HAS_BACKGROUND_PROCESSOR and new_selected != selected_profile:
        processor = get_background_processor()
        generator = get_document_generator()
        
        if processor and generator:
            # Start background processing for new profile
            processor.start_processing(new_selected)
            generator.start_generation(new_selected)
            st.success(f"🚀 Started background processing for {new_selected}")
    
    # Background processor status
    if HAS_BACKGROUND_PROCESSOR:
        processor = get_background_processor()
        generator = get_document_generator()
        
        if processor and generator:
            proc_status = processor.get_status()
            gen_status = generator.get_status()
            
            st.markdown(
                """
                <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color); margin: 1rem 0;">
                    <h4 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">🔄 Background Services</h4>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            # Processor status
            proc_icon = "🟢" if proc_status['active'] else "🔴"
            st.markdown(f"{proc_icon} **Job Processor**: {'Active' if proc_status['active'] else 'Stopped'}")
            if proc_status['active']:
                st.caption(f"Processed: {proc_status['processed_count']} | Errors: {proc_status['error_count']}")
            
            # Generator status  
            gen_icon = "🟢" if gen_status['active'] else "🔴"
            st.markdown(f"{gen_icon} **Doc Generator**: {'Active' if gen_status['active'] else 'Stopped'}")
            if gen_status['active']:
                st.caption(f"Generated: {gen_status['generated_count']} | Errors: {gen_status['error_count']}")
            
            # Control buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Start", use_container_width=True, key="start_bg"):
                    processor.start_processing(new_selected)
                    generator.start_generation(new_selected)
                    st.rerun()
            
            with col2:
                if st.button("⏸️ Stop", use_container_width=True, key="stop_bg"):
                    processor.stop_processing()
                    generator.stop_generation()
                    st.rerun()
    
    # Profile actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Edit", use_container_width=True, key="edit_profile"):
            st.session_state["show_profile_editor"] = True
    
    with col2:
        if st.button("📋 Clone", use_container_width=True, key="clone_profile"):
            st.session_state["show_profile_cloner"] = True
    
    # Profile statistics with custom styling
    try:
        db = get_job_db(new_selected)
        stats = db.get_job_stats()
        
        st.markdown(
            """
            <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color); margin: 1rem 0;">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">📊 Profile Stats</h4>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Custom styled metrics
        total_jobs = stats.get('total_jobs', 0)
        applied_count = stats.get('applied_jobs', 0)
        
        # Total Jobs metric
        st.markdown(
            f"""
            <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 0.5rem; border: 1px solid var(--border-color); margin: 0.5rem 0;">
                <div style="color: var(--text-secondary); font-size: 0.875rem; font-weight: 500; text-transform: uppercase;">Total Jobs</div>
                <div style="color: var(--accent-primary); font-size: 1.5rem; font-weight: 700; margin: 0.25rem 0;">{total_jobs:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Applied Jobs metric
        st.markdown(
            f"""
            <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 0.5rem; border: 1px solid var(--border-color); margin: 0.5rem 0;">
                <div style="color: var(--text-secondary); font-size: 0.875rem; font-weight: 500; text-transform: uppercase;">Applied</div>
                <div style="color: var(--success); font-size: 1.5rem; font-weight: 700; margin: 0.25rem 0;">{applied_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Success Rate metric
        if total_jobs > 0:
            app_rate = (applied_count / total_jobs) * 100
            rate_color = "var(--success)" if app_rate > 0 else "var(--text-secondary)"
            st.markdown(
                f"""
                <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 0.5rem; border: 1px solid var(--border-color); margin: 0.5rem 0;">
                    <div style="color: var(--text-secondary); font-size: 0.875rem; font-weight: 500; text-transform: uppercase;">Success Rate</div>
                    <div style="color: {rate_color}; font-size: 1.5rem; font-weight: 700; margin: 0.25rem 0;">{app_rate:.1f}%</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Last activity
        if 'last_activity' in stats:
            st.markdown(
                f"""
                <div style="background: var(--bg-secondary); padding: 0.5rem; border-radius: 0.25rem; border: 1px solid var(--border-color); margin: 0.5rem 0;">
                    <div style="color: var(--text-secondary); font-size: 0.75rem;">Last activity: {stats['last_activity']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    except Exception as e:
        st.error(f"Error loading profile stats: {e}")
    
    return new_selected


def display_enhanced_quick_actions() -> None:
    """Display enhanced quick action buttons."""
    st.markdown(
        """
        <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color); margin: 1rem 0;">
            <h3 style="margin: 0; color: var(--text-primary);">⚡ Quick Actions</h3>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        if st.button("🔄 Refresh", use_container_width=True, key="refresh_data"):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("🚀 Scrape", use_container_width=True, key="start_scrape"):
            st.info("Starting scraper... (implementation needed)")
    
    with action_col2:
        if st.button("📊 Export", use_container_width=True, key="export_jobs"):
            st.info("Export functionality coming soon!")
        
        if st.button("🧹 Cleanup", use_container_width=True, key="cleanup_data"):
            st.info("Cleanup functionality coming soon!")

def check_dashboard_backend_connection() -> bool:
    """
    Check dashboard backend connection health.
    
    Returns:
        True if backend connection is healthy, False otherwise
    """
    try:
        import socket
        import requests
        from pathlib import Path
        
        logger.info("Checking dashboard backend connection...")
        
        # Check database connectivity
        try:
            db = get_job_db("default")  # Test with default profile
            db.get_job_stats()  # Simple query to test connection
            logger.debug("Database connection: OK")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
        
        # Check if required directories exist
        required_dirs = ["profiles", "logs", "cache"]
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                logger.warning(f"Required directory missing: {dir_name}")
                # Don't fail for missing directories, just warn
        
        # Check system resources
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 95:
                logger.warning(f"High CPU usage detected: {cpu_percent}%")
            if memory_percent > 95:
                logger.warning(f"High memory usage detected: {memory_percent}%")
                
            logger.debug(f"System resources: CPU {cpu_percent}%, Memory {memory_percent}%")
            
        except ImportError:
            logger.debug("psutil not available for system resource monitoring")
        
        # Check if required modules can be imported
        try:
            from src.core.job_database import ModernJobDatabase
            from src.utils.profile_helpers import get_available_profiles
            logger.debug("Core modules import: OK")
        except ImportError as e:
            logger.error(f"Core module import failed: {e}")
            return False
        
        # Check network connectivity (optional)
        try:
            response = requests.get("https://httpbin.org/status/200", timeout=5)
            if response.status_code == 200:
                logger.debug("External network connectivity: OK")
            else:
                logger.debug("External network connectivity: Limited")
        except Exception:
            logger.debug("External network connectivity: Not available")
            # Don't fail for network issues
        
        # Check if FastAPI backend is running (if applicable)
        backend_ports = [8000, 8001, 8002]  # Common backend ports
        backend_running = False
        
        for port in backend_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                if result == 0:
                    backend_running = True
                    logger.debug(f"Backend service detected on port {port}")
                    break
                sock.close()
            except Exception:
                continue
        
        if not backend_running:
            logger.debug("No backend service detected on common ports")
            # Don't fail for missing backend - dashboard can work standalone
        
        logger.info("Dashboard backend connection check completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Dashboard backend connection check failed: {e}")
        return False

def main() -> None:
    """Main dashboard function with modern dark theme and reorganized tabs."""
    # Apply modern dark CSS
    st.markdown(UNIFIED_CSS, unsafe_allow_html=True)
    
    # Force dark theme - no light mode toggle needed
    st.markdown("""
    <script>
    document.documentElement.setAttribute('data-theme', 'dark');
    document.body.setAttribute('data-theme', 'dark');
    </script>
    """, unsafe_allow_html=True)
    
    # Modern header
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 2rem; border-radius: 1rem; border: 1px solid #475569; margin-bottom: 2rem;'>
            <h1 style='color: #f1f5f9; margin: 0; font-size: 2.5rem; font-weight: 700;'>🚀 AutoJobAgent</h1>
            <p style='color: #cbd5e1; margin: 0.5rem 0 0 0; font-size: 1.125rem;'>Modern Job Application Automation Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Auto-refresh toggle
        auto_refresh = st.toggle("🔄 Auto Refresh", value=st.session_state.get("auto_refresh", False))
        st.session_state["auto_refresh"] = auto_refresh
        
        if auto_refresh and HAS_AUTOREFRESH:
            st_autorefresh(interval=30000, key="dashboard_refresh")
        elif auto_refresh and not HAS_AUTOREFRESH:
            st.info("💡 Install `streamlit-autorefresh` for auto-refresh")
    
    # Profile selection
    try:
        profiles = get_available_profiles()
        
        if not profiles:
            st.error("❌ No profiles found. Please create a profile first.")
            st.info("💡 Run the job scraper to create profiles automatically.")
            st.code("python main.py Nirajan --action scrape", language="bash")
            return
        
        # Sidebar with profile and quick actions
        with st.sidebar:
            st.markdown("### 👤 Profile Selection")
            selected_profile = st.selectbox(
                "Select Profile",
                profiles,
                index=profiles.index(st.session_state.get("selected_profile", profiles[0])) if st.session_state.get("selected_profile") in profiles else 0,
                key="sidebar_profile_selector"
            )
            st.session_state["selected_profile"] = selected_profile
            
            # Quick system status
            st.markdown("### ⚡ Quick Status")
            try:
                from src.services.orchestration_service import orchestration_service
                services_status = orchestration_service.get_all_services_status()
                running_count = sum(1 for status in services_status.values() if status.get('status') == 'running')
                total_count = len(services_status)
                
                st.metric("Services Running", f"{running_count}/{total_count}")
                
                # Quick service controls
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 Start All", use_container_width=True):
                        for service_name in ["processor_worker_1", "processor_worker_2", "processor_worker_3"]:
                            orchestration_service.start_service(service_name, selected_profile)
                        st.success("Services started!")
                        st.rerun()
                
                with col2:
                    if st.button("⏹️ Stop All", use_container_width=True):
                        for service_name in ["processor_worker_1", "processor_worker_2", "processor_worker_3"]:
                            orchestration_service.stop_service(service_name)
                        st.success("Services stopped!")
                        st.rerun()
                        
            except ImportError:
                st.info("Orchestration service not available")
        
        # Load data for selected profile
        with st.spinner("Loading dashboard data..."):
            df = load_job_data(selected_profile)
        
        # Modern tab structure - logical workflow order
        tabs = st.tabs([
            "📊 Overview", 
            "💼 Jobs", 
            "🎛️ Orchestration",
            "📈 Analytics", 
            "🖥️ CLI",
            "⚙️ Settings"
        ])
        
        with tabs[0]:  # Overview - Main dashboard with key metrics and quick actions
            try:
                from src.dashboard.components.dashboard_overview import render_dashboard_overview
                render_dashboard_overview(df, selected_profile)
            except ImportError:
                st.error("❌ Dashboard overview component not available")
                # Fallback to basic metrics
                display_enhanced_metrics(df)
            except Exception as e:
                st.error(f"❌ Error in Overview tab: {e}")
                logger.error(f"Overview tab error: {e}")
        
        with tabs[1]:  # Jobs - Consolidated job management
            try:
                from src.dashboard.components.modern_job_table import render_modern_job_table
                render_modern_job_table(df, selected_profile)
            except ImportError:
                st.error("❌ Modern job table component not available")
                # Fallback to original
                display_jobs_table(df, selected_profile)
            except Exception as e:
                st.error(f"❌ Error in Jobs tab: {e}")
                logger.error(f"Jobs tab error: {e}")
        
        with tabs[2]:  # Orchestration - Service control and monitoring
            try:
                if HAS_ORCHESTRATION_COMPONENT:
                    render_orchestration_control(selected_profile)
                else:
                    st.error("❌ Orchestration component not available")
                    st.info("Enhanced orchestration features require the orchestration component.")
            except Exception as e:
                st.error(f"❌ Error in Orchestration tab: {e}")
                logger.error(f"Orchestration tab error: {e}")
        
        with tabs[3]:  # Analytics - Charts and insights
            try:
                from src.dashboard.components.analytics_dashboard import render_analytics_dashboard
                render_analytics_dashboard(df, selected_profile)
            except ImportError:
                st.error("❌ Analytics dashboard component not available")
                # Fallback to basic analytics
                display_analytics_tab(df)
            except Exception as e:
                st.error(f"❌ Error in Analytics tab: {e}")
                logger.error(f"Analytics tab error: {e}")
        
        with tabs[4]:  # CLI - Command interface
            try:
                if HAS_CLI_COMPONENT:
                    render_cli_tab(selected_profile)
                else:
                    st.error("❌ CLI component not available")
                    st.info("CLI interface requires the CLI component.")
            except Exception as e:
                st.error(f"❌ Error in CLI tab: {e}")
                logger.error(f"CLI tab error: {e}")
        
        with tabs[5]:  # Settings - Configuration and preferences
            try:
                from src.dashboard.components.settings_component import render_settings_component
                render_settings_component(selected_profile)
            except ImportError:
                st.error("❌ Settings component not available")
                st.info("Settings management requires the settings component.")
            except Exception as e:
                st.error(f"❌ Error in Settings tab: {e}")
                logger.error(f"Settings tab error: {e}")
            
    except Exception as e:
        st.error(f"❌ Dashboard error: {e}")
        logger.error(f"Dashboard error: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
