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
import asyncio
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import sys
import os
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
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

# Import JobSpy component
try:
    from src.dashboard.components.jobspy_component import render_jobspy_control
    HAS_JOBSPY_COMPONENT = True
except ImportError as e:
    HAS_JOBSPY_COMPONENT = False
    render_jobspy_control = None
    logger.warning(f"JobSpy component not found: {e}")

# Import Document Generation component
try:
    from src.dashboard.components.document_generation_component import render_document_generation_tab
    HAS_DOCUMENT_COMPONENT = True
except ImportError as e:
    HAS_DOCUMENT_COMPONENT = False
    render_document_generation_tab = None
    logger.warning(f"Document generation component not found: {e}")

# Import services
try:
    from src.dashboard.services.data_service import get_data_service
    from src.dashboard.services.system_service import get_system_service
    from src.dashboard.services.config_service import get_config_service
    from src.dashboard.services.orchestration_service import get_orchestration_service
    from src.dashboard.services.health_monitor import get_health_monitor
    HAS_SERVICES = True
except ImportError as e:
    HAS_SERVICES = False
    get_data_service = None
    get_system_service = None
    get_config_service = None
    get_orchestration_service = None
    get_health_monitor = None
    logger.warning(f"Dashboard services not available: {e}")

# Import background processor (optional)
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

# Initialize services
if HAS_SERVICES:
    data_service = get_data_service()
    system_service = get_system_service()
    config_service = get_config_service()
    orchestration_service = get_orchestration_service()
    health_monitor = get_health_monitor()
else:
    data_service = None
    system_service = None
    config_service = None
    orchestration_service = None
    health_monitor = None

# Initialize session state with config service
if "auto_refresh" not in st.session_state:
    if config_service:
        default_settings = config_service.get_dashboard_settings()
        st.session_state["auto_refresh"] = default_settings.get("auto_refresh", True)
        st.session_state["refresh_interval"] = default_settings.get("refresh_interval", 10)
    else:
        st.session_state["auto_refresh"] = True
        st.session_state["refresh_interval"] = 10

if "selected_profile" not in st.session_state:
    if config_service:
        st.session_state["selected_profile"] = config_service.get_default_profile()
    else:
        st.session_state["selected_profile"] = "Nirajan"

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
    st.session_state["auto_refresh"] = True  # Enable auto-refresh by default
if "selected_profile" not in st.session_state:
    st.session_state["selected_profile"] = "Nirajan"  # Default profile
if "refresh_interval" not in st.session_state:
    st.session_state["refresh_interval"] = 10  # 10 seconds default

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

# @st.cache_data(ttl=300)  # Cache disabled for testing - uncomment to re-enable
def load_job_data(profile_name: str) -> pd.DataFrame:
    """Load job data from database using DataService."""
    try:
        if data_service:
            # Use DataService which handles caching and status derivation
            return data_service.load_job_data(profile_name)
        else:
            # Fallback to direct database access if service not available
            db_path = f"profiles/{profile_name}/{profile_name}.db"
            
            if not Path(db_path).exists():
                logger.warning(f"Database file not found: {db_path}")
                return pd.DataFrame()

            db = ModernJobDatabase(db_path=db_path)
            jobs = db.get_jobs(limit=2000)
            
            if jobs:
                df = pd.DataFrame(jobs)
                # Ensure proper datetime parsing
                for date_col in ["posted_date", "scraped_at", "created_at", "updated_at"]:
                    if date_col in df.columns:
                        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                return df
            
            return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Failed to load job data for profile {profile_name}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_system_metrics() -> Dict[str, Any]:
    """Get system metrics using SystemService or fallback to basic metrics."""
    try:
        if system_service:
            # Use async system service (non-blocking)
            import asyncio
            try:
                # Try to get metrics asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                metrics = loop.run_until_complete(system_service.get_system_metrics())
                loop.close()
                return metrics
            except Exception as e:
                logger.warning(f"Async metrics failed, using sync fallback: {e}")
                # Fallback to sync health check
                return system_service.get_service_health()
        else:
            # Fallback to basic metrics if service not available
            return _get_basic_system_metrics()
            
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return _get_basic_system_metrics()

def _get_basic_system_metrics() -> Dict[str, Any]:
    """Basic system metrics fallback."""
    try:
        metrics = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),  # Non-blocking
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
            "timestamp": datetime.now().isoformat(),
            "network_status": "unknown",
            "services": {},
            "orchestration": {}
        }
        return metrics
    except Exception as e:
        logger.error(f"Failed to get basic system metrics: {e}")
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_usage": 0,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def display_services_tab(profile_name: str) -> None:
    """Display the Services management tab with orchestration integration."""
    st.markdown("# 🛠️ Service Management & Orchestration")
    st.markdown("Manage and monitor core AutoJobAgent services with real-time orchestration status.")
    
    try:
        # Get comprehensive health status
        if health_monitor:
            with st.spinner("Checking system health..."):
                health_status = asyncio.run(health_monitor.check_service_health())
        else:
            health_status = {"overall_status": "unknown", "services": {}}
        
        # Display overall system status
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            overall_status = health_status.get("overall_status", "unknown")
            status_colors = {
                "healthy": "🟢",
                "degraded": "🟡", 
                "unhealthy": "🔴",
                "unknown": "⚪"
            }
            status_color = status_colors.get(overall_status, "⚪")
            
            st.markdown(f"### {status_color} System Status")
            st.markdown(f"**{overall_status.title()}**")
        
        with col2:
            system_health = health_status.get("services", {}).get("system", {})
            cpu_percent = system_health.get("cpu_percent", 0)
            st.metric("CPU Usage", f"{cpu_percent:.1f}%", 
                     delta=None if cpu_percent < 70 else "High")
        
        with col3:
            memory_percent = system_health.get("memory_percent", 0)
            st.metric("Memory Usage", f"{memory_percent:.1f}%",
                     delta=None if memory_percent < 80 else "High")
        
        with col4:
            network_status = system_health.get("services", {}).get("network", {}).get("status", "unknown")
            network_emoji = "🌐" if network_status == "healthy" else "⚠️"
            st.markdown(f"### {network_emoji} Network")
            st.markdown(f"**{network_status.title()}**")
        
        st.markdown("---")
        
        # Orchestration Status Section
        st.markdown("## 🎯 Orchestration Status")
        
        if orchestration_service:
            orch_col1, orch_col2 = st.columns(2)
            
            with orch_col1:
                st.markdown("### 📋 Job Application Queue")
                try:
                    app_status = asyncio.run(orchestration_service.get_application_queue_status())
                    
                    # Display application metrics
                    app_col1, app_col2, app_col3 = st.columns(3)
                    with app_col1:
                        st.metric("Queued", app_status.get("total_queued", 0))
                    with app_col2:
                        st.metric("In Progress", app_status.get("in_progress", 0))
                    with app_col3:
                        st.metric("Completed Today", app_status.get("completed_today", 0))
                    
                    # Queue health indicator
                    queue_health = app_status.get("queue_health", "unknown")
                    health_color = "🟢" if queue_health == "healthy" else "🟡" if queue_health == "degraded" else "🔴"
                    st.markdown(f"{health_color} **Queue Health:** {queue_health.title()}")
                    
                except Exception as e:
                    st.error(f"Could not get application queue status: {e}")
            
            with orch_col2:
                st.markdown("### 📄 Document Generation")
                try:
                    doc_status = asyncio.run(orchestration_service.get_document_generation_status())
                    
                    # Display document generation metrics
                    doc_col1, doc_col2, doc_col3 = st.columns(3)
                    with doc_col1:
                        st.metric("Active Workers", 
                                f"{doc_status.get('active_workers', 0)}/{doc_status.get('max_workers', 5)}")
                    with doc_col2:
                        st.metric("Queue Length", doc_status.get("queue_length", 0))
                    with doc_col3:
                        st.metric("Generated Today", doc_status.get("documents_generated_today", 0))
                    
                    # Service health indicator
                    service_health = doc_status.get("service_health", "unknown")
                    health_color = "🟢" if service_health == "healthy" else "🟡" if service_health == "degraded" else "🔴"
                    st.markdown(f"{health_color} **Service Health:** {service_health.title()}")
                    
                except Exception as e:
                    st.error(f"Could not get document generation status: {e}")
        
        else:
            st.warning("� Orchestration service not available")
        
        st.markdown("---")
        
        # Service Control Section
        st.markdown("## 🎛️ Service Control")
        
        control_col1, control_col2 = st.columns(2)
        
        with control_col1:
            st.markdown("### 🔄 Health Recovery")
            
            if health_monitor:
                # Service recovery buttons
                services_to_recover = ["database", "system", "orchestration", "cache"]
                selected_service = st.selectbox("Select Service", services_to_recover)
                
                if st.button(f"🚑 Recover {selected_service.title()}", key="recover_service"):
                    with st.spinner(f"Attempting to recover {selected_service}..."):
                        try:
                            recovery_result = asyncio.run(health_monitor.trigger_health_recovery(selected_service))
                            
                            if recovery_result.get("success", False):
                                st.success(f"✅ {recovery_result.get('message', 'Recovery successful')}")
                            else:
                                st.error(f"❌ Recovery failed: {recovery_result.get('error', 'Unknown error')}")
                                
                        except Exception as e:
                            st.error(f"❌ Recovery error: {e}")
            else:
                st.warning("Health monitor not available")
        
        with control_col2:
            st.markdown("### 📊 Health History")
            
            if health_monitor:
                history = health_monitor.get_health_history(limit=5)
                
                if history:
                    for i, check in enumerate(reversed(history)):
                        timestamp = check.get("timestamp", "Unknown")
                        status = check.get("overall_status", "unknown")
                        status_emoji = status_colors.get(status, "⚪")
                        
                        # Parse timestamp for display
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime("%H:%M:%S")
                        except:
                            time_str = timestamp
                        
                        st.markdown(f"{status_emoji} {time_str} - {status.title()}")
                else:
                    st.info("No health history available")
            else:
                st.warning("Health monitor not available")
        
        st.markdown("---")
        
        # Detailed Service Status
        st.markdown("## 📋 Detailed Service Status")
        
        if health_status.get("services"):
            for service_name, service_data in health_status["services"].items():
                with st.expander(f"{service_name.title()} Service Details"):
                    service_status = service_data.get("status", "unknown")
                    status_emoji = status_colors.get(service_status, "⚪")
                    
                    st.markdown(f"**Status:** {status_emoji} {service_status.title()}")
                    
                    # Display service-specific metrics
                    if service_name == "system":
                        st.markdown(f"**CPU:** {service_data.get('cpu_percent', 0):.1f}%")
                        st.markdown(f"**Memory:** {service_data.get('memory_percent', 0):.1f}%")
                        st.markdown(f"**Disk:** {service_data.get('disk_usage', 0):.1f}%")
                        st.markdown(f"**Network:** {service_data.get('network_status', 'unknown')}")
                    
                    elif service_name == "database":
                        st.markdown(f"**Profiles:** {service_data.get('profiles_count', 0)}")
                        st.markdown(f"**Cache Size:** {service_data.get('cache_size', 0)}")
                        st.markdown(f"**Database Healthy:** {service_data.get('database_healthy', False)}")
                    
                    elif service_name == "orchestration":
                        st.markdown(f"**Services Healthy:** {service_data.get('services_healthy', 0)}/{service_data.get('total_services', 0)}")
                        
                        app_proc = service_data.get("application_processor", {})
                        if app_proc:
                            st.markdown(f"**Application Processor:** {app_proc.get('status', 'unknown')}")
                            st.markdown(f"**Queue Length:** {app_proc.get('queue_length', 0)}")
                        
                        doc_gen = service_data.get("document_generator", {})
                        if doc_gen:
                            st.markdown(f"**Document Generator:** {doc_gen.get('status', 'unknown')}")
                            st.markdown(f"**Active Workers:** {doc_gen.get('workers', 0)}")
                    
                    elif service_name == "network":
                        st.markdown(f"**Success Rate:** {service_data.get('success_rate', 0):.1%}")
                        st.markdown(f"**Avg Response Time:** {service_data.get('avg_response_time', 0):.2f}s")
                        st.markdown(f"**Successful Connections:** {service_data.get('successful_connections', 0)}/{service_data.get('total_endpoints', 0)}")
                    
                    elif service_name == "cache":
                        st.markdown(f"**Healthy Caches:** {service_data.get('healthy_caches', 0)}/{service_data.get('total_caches', 0)}")
                        
                        cache_details = service_data.get("cache_details", {})
                        for cache_name, cache_info in cache_details.items():
                            cache_status = cache_info.get("status", "unknown")
                            cache_emoji = "🟢" if cache_status == "healthy" else "🔴"
                            st.markdown(f"- {cache_emoji} {cache_name}: {cache_status}")
                    
                    # Show error if present
                    if "error" in service_data:
                        st.error(f"Error: {service_data['error']}")
                    
                    # Timestamp
                    timestamp = service_data.get("timestamp", "Unknown")
                    st.markdown(f"*Last checked: {timestamp}*")
        
        else:
            st.warning("No detailed service status available")
        
        # Auto-refresh
        if st.session_state.get("auto_refresh", True):
            time.sleep(st.session_state.get("refresh_interval", 10))
            st.rerun()
        
    except Exception as e:
        logger.error(f"Error in services tab: {e}")
        st.error(f"❌ Error loading services tab: {e}")
        
        # Show basic system info as fallback
        if system_service:
            try:
                basic_metrics = asyncio.run(system_service.get_system_metrics())
                st.info("Showing basic system metrics:")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("CPU", f"{basic_metrics.get('cpu_percent', 0):.1f}%")
                with col2:
                    st.metric("Memory", f"{basic_metrics.get('memory_percent', 0):.1f}%")
                with col3:
                    st.metric("Disk", f"{basic_metrics.get('disk_usage', 0):.1f}%")
            except:
                st.error("Could not load basic system metrics")
        
        st.markdown("---")
        
        # Service logs section
        st.markdown("## � Service Logs")
        
        if st.button("� View Recent Logs", key="view_logs"):
            try:
                log_files = [
                    "logs/error_logs.log",
                    "logs/ai_service.log", 
                    "logs/dashboard_orchestrator.log",
                    "logs/scraping_orchestrator.log"
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
        st.info("💡 The reliable service manager component is not installed or configured properly.")
        
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

def display_Improved_metrics(df: pd.DataFrame) -> None:
    """Display Improved metrics with modern styling."""
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
    """Display jobs in a searchable, filterable table with Improved UI/UX."""
    if df.empty:
        st.markdown("""
        <div class="Improved-table-container">
            <div class="Improved-table-header">📋 Job Management Dashboard</div>
            <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                <h3>🚀 No jobs found</h3>
                <p>Start by scraping some job listings to see them here!</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Improved header with container
    st.markdown('<div class="Improved-table-container">', unsafe_allow_html=True)
    st.markdown('<div class="Improved-table-header">📋 Job Management Dashboard</div>', unsafe_allow_html=True)
    
    # Improved statistics display
    total_jobs = len(df)
    # Use exact match for 'Applied' status, not substring to avoid matching partial strings
    applied_jobs = len(df[df.get('status_text', '') == 'Applied'])
    processed_jobs = len(df[df.get('status_text', '').str.contains('Processed', na=False)])
    high_match = len(df[df.get('match_score', 0) >= 80])
    
    st.markdown(f"""
    <div class="Improved-table-stats">
        <div class="Improved-stat-item">
            <div class="Improved-stat-number">{total_jobs}</div>
            <div class="Improved-stat-label">Total Jobs</div>
        </div>
        <div class="Improved-stat-item">
            <div class="Improved-stat-number">{high_match}</div>
            <div class="Improved-stat-label">High Match</div>
        </div>
        <div class="Improved-stat-item">
            <div class="Improved-stat-number">{processed_jobs}</div>
            <div class="Improved-stat-label">Processed</div>
        </div>
        <div class="Improved-stat-item">
            <div class="Improved-stat-number">{applied_jobs}</div>
            <div class="Improved-stat-label">Applied</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Improved filters section
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        st.markdown("### 🔍 **Configurable Filters**")
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
        # Improved table or fallback
        try:
            from src.dashboard.components.Improved_job_table import render_Improved_job_table, display_job_details
            result = render_Improved_job_table(filtered_df, st.session_state.get("selected_profile", "default"))
            if result is None:
                selected_job, selected_indices = None, []
            else:
                selected_job, selected_indices = result
            if selected_job:
                display_job_details(selected_job, filtered_df)
        except ImportError as e:
            st.error(f"Improved table component not available: {e}")
            st.info("Falling back to basic table display...")
            # Improved fallback table with better UI
            st.markdown("### 📋 Job Management Table")
            st.info("💡 For the best experience, install streamlit-aggrid: `pip install streamlit-aggrid`")
            
            # Add statistics
            total_jobs = len(filtered_df)
            applied_jobs = len(filtered_df[filtered_df.get('status_text', '').str.contains('Applied', na=False)])
            processed_jobs = len(filtered_df[filtered_df.get('status_text', '').str.contains('Processed', na=False)])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Jobs", total_jobs)
            with col2:
                st.metric("Processed", processed_jobs)
            with col3:
                st.metric("Applied", applied_jobs)
            
            # Improved table display
            display_columns = ['title', 'company', 'location', 'job_type', 'experience_level', 'salary_range', 'status_text', 'priority', 'match_score']
            available_columns = [col for col in display_columns if col in filtered_df.columns]
            
            if available_columns:
                st.dataframe(
                    filtered_df[available_columns],
                    use_container_width=True,
                    hide_index=True,
                    height=500,
                    column_config={
                        "title": st.column_config.TextColumn(
                            "🎯 Job Title",
                            width="large",
                        ),
                        "company": st.column_config.TextColumn(
                            "🏢 Company",
                            width="medium",
                        ),
                        "location": st.column_config.TextColumn(
                            "📍 Location",
                            width="medium",
                        ),
                        "status_text": st.column_config.TextColumn(
                            "📊 Status",
                            width="medium",
                        ),
                        "priority": st.column_config.TextColumn(
                            "⭐ Priority",
                            width="small",
                        ),
                        "match_score": st.column_config.NumberColumn(
                            "🎯 Match %",
                            width="small",
                            format="%d%%"
                        ),
                        "salary_range": st.column_config.TextColumn(
                            "💰 Salary",
                            width="medium",
                        ),
                        "job_type": st.column_config.TextColumn(
                            "💼 Type",
                            width="small",
                        ),
                        "experience_level": st.column_config.TextColumn(
                            "👨‍💼 Experience",
                            width="small",
                        ),
                    }
                )
            # Improved batch apply section
            st.markdown('<div class="Improved-table-actions">', unsafe_allow_html=True)
            st.markdown("### 🎯 **Quick Actions**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("⚙️ Process All", use_container_width=True, key="process_all_basic"):
                    st.info("🚀 Bulk processing feature coming soon!")
            
            with col2:
                if st.button("📄 Generate Docs", use_container_width=True, key="docs_all_basic"):
                    st.info("📄 Document generation feature coming soon!")
            
            with col3:
                if st.button("🎯 Apply to Top", use_container_width=True, key="apply_top_basic"):
                    st.info("🎯 Auto-apply feature coming soon!")
            
            with col4:
                if st.button("📊 Export Data", use_container_width=True, key="export_basic"):
                    st.info("📊 Export feature coming soon!")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Individual job selection for batch apply
            st.markdown("#### 🔍 **Batch Job Selection**")
            apply_indices = st.multiselect(
                "Select jobs for batch operations:",
                filtered_df.index.tolist(),
                help="Choose multiple jobs to apply batch operations",
                format_func=lambda x: f"🎯 {filtered_df.loc[x].get('title', 'Unknown')} at {filtered_df.loc[x].get('company', 'Unknown')}"
            )
            
            if apply_indices:
                col1, col2 = st.columns(2)
                
                with col1:
                    mode = st.radio(
                        "Application method:",
                        ["Manual (Mark as applied)", "Hybrid (AI-assisted)"],
                        key="batch_apply_mode",
                        help="Choose how to handle the selected job applications"
                    )
                
                with col2:
                    if st.button("🚀 Apply to Selected Jobs", type="primary", use_container_width=True):
                        with st.spinner(f"Applying to {len(apply_indices)} jobs..."):
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
                        st.success(f"✅ Successfully applied to {len(apply_indices)} jobs!")
                        st.experimental_rerun()
                
                # Show selected jobs preview
                st.markdown("##### 📋 **Selected Jobs Preview:**")
                preview_df = filtered_df.loc[apply_indices][['title', 'company', 'status_text', 'match_score']].copy()
                st.dataframe(preview_df, use_container_width=True, hide_index=True)
            
            elif len(filtered_df) > 0:
                st.info("💡 Select jobs above to enable batch operations")
            else:
                st.info("✅ All visible jobs have been processed!")
    
    # Close the Improved table container
    st.markdown('</div>', unsafe_allow_html=True)

def display_system_tab(profile_name: str) -> None:
    """Display Improved system information and orchestration controls with integrated CLI."""
    st.markdown('<h2 class="section-header">🖥️ System Command & Information Center</h2>', unsafe_allow_html=True)
    
    # Main orchestration controls - prominently displayed first
    if HAS_ORCHESTRATION_COMPONENT:
        st.markdown("### 🎛️ Quick Orchestration Controls")
        
        # Quick action buttons for core services
        col1, col2, col3, col4 = st.columns(4)
        
        from src.dashboard.components.orchestration_component import ImprovedOrchestrationComponent
        if 'orchestration_component' not in st.session_state:
            st.session_state.orchestration_component = ImprovedOrchestrationComponent(profile_name)
        orchestration = st.session_state.orchestration_component
        
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
            # Use the Improved orchestration component - Service Control section
            if 'orchestration_component' not in st.session_state:
                from src.dashboard.components.orchestration_component import ImprovedOrchestrationComponent
                st.session_state.orchestration_component = ImprovedOrchestrationComponent(profile_name)
            orchestration = st.session_state.orchestration_component
            orchestration._render_service_control_panel()
        else:
            _render_fallback_service_control(profile_name)
    
    with system_tabs[1]:  # 5-Worker Pool
        if HAS_ORCHESTRATION_COMPONENT:
            # Worker Pool Management section
            if 'orchestration_component' not in st.session_state:
                from src.dashboard.components.orchestration_component import ImprovedOrchestrationComponent
                st.session_state.orchestration_component = ImprovedOrchestrationComponent(profile_name)
            orchestration = st.session_state.orchestration_component
            orchestration._render_worker_pool_management()
        else:
            _render_fallback_worker_info()
    
    with system_tabs[2]:  # Monitoring
        if HAS_ORCHESTRATION_COMPONENT:
            # Service Monitoring section
            if 'orchestration_component' not in st.session_state:
                from src.dashboard.components.orchestration_component import ImprovedOrchestrationComponent
                st.session_state.orchestration_component = ImprovedOrchestrationComponent(profile_name)
            orchestration = st.session_state.orchestration_component
            orchestration._render_service_monitoring()
        else:
            _render_fallback_monitoring()
    
    with system_tabs[3]:  # Auto-Management
        if HAS_ORCHESTRATION_COMPONENT:
            # Auto-Management panel
            if 'orchestration_component' not in st.session_state:
                from src.dashboard.components.orchestration_component import ImprovedOrchestrationComponent
                st.session_state.orchestration_component = ImprovedOrchestrationComponent(profile_name)
            orchestration = st.session_state.orchestration_component
            orchestration._render_auto_management_panel()
        else:
            _render_fallback_auto_management()
    
    with system_tabs[4]:  # CLI Commands
        _render_integrated_cli_commands(profile_name)


def _render_fallback_service_control(profile_name: str):
    """Fallback service control when orchestration component unavailable."""
    st.markdown("### 🔧 Manual Service Controls")
    st.warning("⚠️ Improved orchestration component not available. Use manual commands.")
    
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
    **Improved 5-Worker Document Generation Features:**
    - 🔄 Parallel processing of 5 jobs simultaneously
    - 📁 Automatic folder creation per job application
    - ✏️ Automated resume customization per job
    - 📄 Automated cover letter generation
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
    **Configurable Auto-Start/Stop Logic (Available with full orchestration):**
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
    The CLI interface has been integrated into the **🎛️ System & Configurable Orchestration** tab 
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
            st.info("💡 Click on the 'System & Configurable Orchestration' tab above")
        
        st.markdown("### 🎯 Available Features")
        st.markdown("""
        - **🖥️ CLI Commands**: Full command interface
        - **🎛️ Service Control**: Configurable orchestration panel  
        - **👥 5-Worker Pool**: Parallel document generation
        - **📊 Monitoring**: Real-time system metrics
        - **🤖 Auto-Management**: Automated automation
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
        st_autorefresh(interval=2000, key="unified_dashboard_log_refresh")

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
    """Display Improved profile management in sidebar."""
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


def display_Improved_quick_actions() -> None:
    """Display Improved quick action buttons."""
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
            current_profile = st.session_state.get("selected_profile", "Nirajan")
            selected_profile = st.selectbox(
                "Select Profile",
                profiles,
                index=profiles.index(current_profile) if current_profile in profiles else 0,
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
                st.info("💡 Improved orchestration features are loading... Using standard mode.")
        
        # Load data for selected profile
        with st.spinner("Loading dashboard data..."):
            df = load_job_data(selected_profile)
        
        # Add data verification component in sidebar
        with st.sidebar:
            st.markdown("---")
            try:
                from src.dashboard.components.data_verification import render_data_verification_component
                render_data_verification_component(selected_profile)
            except ImportError:
                # Show basic verification
                db_path = f"profiles/{selected_profile}/{selected_profile}.db"
                if Path(db_path).exists():
                    st.success(f"✅ DB Connected")
                    st.text(f"Jobs: {len(df)}")
                else:
                    st.error(f"❌ DB Missing")
        
        # Modern tab structure - logical workflow order
        tabs = st.tabs([
            "📊 Overview", 
            "💼 Jobs", 
            "✅ Apply Manually",
            "⚙️ Processing",
            "� JobSpy",
            "�📋 Logs",
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
                display_Improved_metrics(df)
            except Exception as e:
                st.error(f"❌ Error in Overview tab: {e}")
                logger.error(f"Overview tab error: {e}")
        
        with tabs[1]:  # Jobs - Modern card-based job management
            try:
                from src.dashboard.components.modern_job_cards import render_modern_job_cards
                render_modern_job_cards(df, selected_profile)
            except ImportError:
                st.error("❌ Modern job cards component not available")
                # Fallback to Improved table
                try:
                    from src.dashboard.components.Improved_job_table import render_Improved_job_table
                    render_Improved_job_table(df, selected_profile)
                except ImportError:
                    # Final fallback to original
                    display_jobs_table(df, selected_profile)
            except Exception as e:
                st.error(f"❌ Error in Jobs tab: {e}")
                logger.error(f"Jobs tab error: {e}")
        
        with tabs[2]:  # Apply Manually - Manual application tracking
            try:
                from src.dashboard.components.manual_application_tracker import render_manual_application_tracker
                render_manual_application_tracker(df, selected_profile)
            except ImportError as e:
                st.error("❌ Manual application tracker component not available")
                st.info(f"Manual application tracking features require the tracker component: {e}")
                # Fallback to basic checkbox list
                st.markdown("### ✅ Basic Manual Application Tracking")
                if not df.empty:
                    for idx, (_, job) in enumerate(df.head(10).iterrows()):
                        job_id = job.get('id', idx)
                        title = job.get('title', 'Unknown')
                        company = job.get('company', 'Unknown')
                        applied = job.get('application_status', 'not_applied') == 'applied'
                        
                        if st.checkbox(f"Applied: {title} at {company}", value=applied, key=f"basic_apply_{job_id}"):
                            st.success(f"✅ Marked as applied: {title}")
                else:
                    st.info("No jobs available for manual application tracking")
            except Exception as e:
                st.error(f"❌ Error in Apply Manually tab: {e}")
                logger.error(f"Apply Manually tab error: {e}")
        
        with tabs[3]:  # Processing - Job processing controls
            try:
                from src.dashboard.components.job_processor_component import get_job_processor_component
                processor_component = get_job_processor_component(selected_profile)
                processor_component.render_processor_controls()
            except ImportError as e:
                st.error("❌ Job processor component not available")
                st.info(f"Job processing features require the processor component: {e}")
            except Exception as e:
                st.error(f"❌ Error in Processing tab: {e}")
                logger.error(f"Processing tab error: {e}")
        
        with tabs[4]:  # JobSpy - Job search and scraping with JobSpy
            try:
                if HAS_JOBSPY_COMPONENT:
                    render_jobspy_control()
                else:
                    st.error("❌ JobSpy component not available")
                    st.info("JobSpy features require the JobSpy component.")
            except Exception as e:
                st.error(f"❌ Error in JobSpy tab: {e}")
                logger.error(f"JobSpy tab error: {e}")
        
        with tabs[5]:  # Logs - System and processing logs
            try:
                from src.dashboard.components.logging_component import logging_component
                logging_component.render_logging_dashboard()
            except ImportError as e:
                st.error("❌ Logging component not available")
                st.info(f"Logging features require the logging component: {e}")
            except Exception as e:
                st.error(f"❌ Error in Logs tab: {e}")
                logger.error(f"Logs tab error: {e}")
        
        with tabs[6]:  # Orchestration - Service control and monitoring
            try:
                if HAS_ORCHESTRATION_COMPONENT:
                    render_orchestration_control(selected_profile)
                else:
                    st.error("❌ Orchestration component not available")
                    st.info("Improved orchestration features require the orchestration component.")
            except Exception as e:
                st.error(f"❌ Error in Orchestration tab: {e}")
                logger.error(f"Orchestration tab error: {e}")
        
        with tabs[6]:  # Analytics - Charts and insights
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
        
        with tabs[7]:  # CLI - Command interface
            try:
                if HAS_CLI_COMPONENT:
                    render_cli_tab(selected_profile)
                else:
                    st.error("❌ CLI component not available")
                    st.info("CLI interface requires the CLI component.")
            except Exception as e:
                st.error(f"❌ Error in CLI tab: {e}")
                logger.error(f"CLI tab error: {e}")
        
        with tabs[8]:  # Settings - Configuration and preferences
            try:
                from src.dashboard.components.settings_component import render_settings_component
                render_settings_component(selected_profile)
            except ImportError:
                # Fallback to scraping configuration
                try:
                    from src.dashboard.components.scraping_config_component import render_scraping_config_component
                    render_scraping_config_component(selected_profile)
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
