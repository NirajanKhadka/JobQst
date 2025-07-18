# Ensure session state keys are initialized
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False
# Fallbacks for undefined project-specific functions/constants
def get_job_db(profile):
    class DummyDB:
        def get_job_stats(self):
            return {}
    return DummyDB()

HAS_AUTOREFRESH = globals().get('HAS_AUTOREFRESH', False)
def st_autorefresh(*args, **kwargs):
    pass

def get_available_profiles():
    return ["Nirajan"]

HAS_DOCUMENT_COMPONENT = globals().get('HAS_DOCUMENT_COMPONENT', False)
def render_document_generation_tab(profile):
    st.info("Document generation component not available.")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Professional Dashboard for AutoJobAgent
Combines the best features from streamlit_dashboard.py and modern_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import os
try:
    import psutil
except ImportError:
    psutil = None

# Fallbacks for undefined background processor and project root
HAS_BACKGROUND_PROCESSOR = globals().get('HAS_BACKGROUND_PROCESSOR', False)
def get_background_processor():
    return None
def get_document_generator():
    return None
class ModernJobDatabase:
    def __init__(self, db_path=None):
        pass
    def get_job_stats(self):
        return {}
project_root = Path(os.getcwd())
import time

# Safe fallback logger
import logging
logger = logging.getLogger("dashboard")

# Fallbacks for undefined constants/components
HAS_ORCHESTRATION_COMPONENT = globals().get('HAS_ORCHESTRATION_COMPONENT', False)
HAS_CLI_COMPONENT = globals().get('HAS_CLI_COMPONENT', False)
def render_cli_tab(*args, **kwargs):
    st.info("CLI component not available.")
UNIFIED_CSS = """
if "auto_refresh" not in st.session_state:
    st.session_state["auto_refresh"] = False
if "selected_profile" not in st.session_state:
    st.session_state["selected_profile"] = None

# Unified Modern CSS - Best of both dashboards
UNIFIED_CSS = """
UNIFIED_CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Reset and base styles */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* Theme variables */
    :root {
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-card: #ffffff;
        --text-primary: #23272f; /* darker for readability */
        --text-secondary: #49505a; /* darker for readability */
        --border-color: #e2e8f0;
        --accent-primary: #3b82f6;
        --accent-secondary: #6366f1;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Dark mode theme */
    [data-theme="dark"] {
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-card: #334155;
        --text-primary: #e2e8f0; /* off-white, not pure white */
        --text-secondary: #b6bdc6; /* light gray, not white */
        --border-color: #475569;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    
    /* Main application styles */
    .stApp {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .main {
        background: var(--bg-secondary) !important;
        padding: 1rem !important;
    }
    
    /* Header styles */
    .dashboard-header {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: var(--text-primary);
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-color);
    }
    
    .dashboard-title {
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .dashboard-subtitle {
        font-size: 1.25rem;
        color: var(--text-secondary);
        margin: 0.5rem 0 0 0;
        font-weight: 500;
        opacity: 0.95;
    }
    
    /* Metric cards */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--accent-primary);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
        border-radius: 1rem 1rem 0 0;
    }
    
    .metric-value {
        font-size: 2.8rem;
        font-weight: 800;
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
        margin: 0.5rem 0;
        text-shadow: 0 1px 2px rgba(0,0,0,0.08);
    }
    
    .metric-label {
        font-size: 1.05rem;
        color: var(--text-secondary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    
    .metric-delta {
        font-size: 0.875rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .metric-delta.positive {
        color: var(--success);
    }
    
    .metric-delta.negative {
        color: var(--error);
    }
    
    /* Job cards */
    .job-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
        position: relative;
    }
    
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--accent-primary);
    }
    
    .job-title {
        font-size: 1.45rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
        line-height: 1.4;
        text-shadow: 0 1px 2px rgba(0,0,0,0.08);
    }
    
    .job-company {
        font-size: 1rem;
        color: var(--accent-primary);
        font-weight: 500;
        margin-bottom: 0.25rem;
    }
    
    .job-location {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-bottom: 1rem;
    }
    
    .job-meta {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-color);
    }
    
    .job-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-primary);
        background: var(--bg-secondary);
    }
    
    .job-badge.applied {
        background: rgba(16, 185, 129, 0.1);
        color: var(--success);
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    
    .job-badge.applied-status {
        background: rgba(16, 185, 129, 0.1);
        color: var(--success);
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    
    .job-badge.document-status {
        background: rgba(99, 102, 241, 0.1);
        color: var(--accent-secondary);
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    .job-badge.processed-status {
        background: rgba(245, 158, 11, 0.1);
        color: var(--warning);
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    
    .job-badge.scraped-status {
        background: rgba(59, 130, 246, 0.1);
        color: var(--accent-primary);
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .job-badge.new-status {
        background: rgba(100, 116, 139, 0.1);
        color: var(--text-secondary);
        border: 1px solid rgba(100, 116, 139, 0.2);
    }

    .job-badge.unapplied {
        background: rgba(59, 130, 246, 0.1);
        color: var(--accent-primary);
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .job-badge.high-priority {
        background: rgba(239, 68, 68, 0.1);
        color: var(--error);
        border: 1px solid rgba(239, 68, 68, 0.2);
    }
    
    .job-badge.medium-priority {
        background: rgba(245, 158, 11, 0.1);
        color: var(--warning);
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    
    .job-badge.low-priority {
        background: rgba(16, 185, 129, 0.1);
        color: var(--success);
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    
    /* Filters and controls */
    .filter-container {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
    }
    
    /* Section headers */
    .section-header {
        font-size: 2.1rem;
        font-weight: 800;
        color: var(--text-primary);
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--accent-primary);
        display: inline-block;
        text-shadow: 0 1px 2px rgba(0,0,0,0.10);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--bg-card);
        border-radius: 1rem;
        padding: 0.5rem;
        border: 1px solid var(--border-color);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 0.5rem;
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--accent-primary) !important;
        color: var(--bg-primary) !important;
        box-shadow: var(--shadow-sm);
    }
    
    /* Buttons */
    .stButton > button {
        background: var(--accent-primary);
        color: var(--bg-primary);
        border: none;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-sm);
    }
    
    .stButton > button:hover {
        background: var(--accent-secondary);
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    
    /* Data tables */
    .stDataFrame {
        border-radius: 1rem;
        overflow: hidden;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
    }
    
    /* Sidebar */
    .stSidebar {
        background: var(--bg-card);
        border-right: 1px solid var(--border-color);
    }
    
    /* Sidebar content styling */
    .stSidebar .stMetric {
        background: var(--bg-secondary);
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid var(--border-color);
        margin: 0.5rem 0;
    }
    
    .stSidebar .stMetric > div {
        color: var(--text-primary) !important;
    }
    
    .stSidebar .stMetric [data-testid="metric-container"] {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 0.5rem;
        padding: 1rem;
    }
    
    .stSidebar .stMetric [data-testid="metric-container"] > div {
        color: var(--text-primary) !important;
    }
    
    .stSidebar .stMetric label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }
    
    .stSidebar .stMetric [data-testid="metric-container"] [data-testid="metric-value"] {
        color: var(--accent-primary) !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }
    
    .stSidebar .stMetric [data-testid="metric-container"] [data-testid="metric-delta"] {
        color: var(--text-secondary) !important;
    }
    
    /* Sidebar headings */
    .stSidebar h3, .stSidebar h4 {
        color: var(--text-primary) !important;
        background: var(--bg-secondary);
        padding: 0.75rem;
        border-radius: 0.5rem;
        border: 1px solid var(--border-color);
        margin: 1rem 0 0.5rem 0;
    }
    
    /* Sidebar buttons */
    .stSidebar .stButton > button {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 0.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stSidebar .stButton > button:hover {
        background: var(--accent-primary) !important;
        color: var(--bg-primary) !important;
        border-color: var(--accent-primary) !important;
        transform: translateY(-1px);
        box-shadow: var(--shadow-sm);
    }
    
    /* Sidebar selectbox */
    .stSidebar .stSelectbox > div > div {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 0.5rem;
    }
    
    .stSidebar .stSelectbox label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    /* Sidebar text and captions */
    .stSidebar .stMarkdown, .stSidebar p, .stSidebar .stCaption {
        color: var(--text-primary) !important;
    }
    
    .stSidebar .stCaption {
        color: var(--text-secondary) !important;
        background: var(--bg-secondary);
        padding: 0.5rem;
        border-radius: 0.25rem;
        border: 1px solid var(--border-color);
        margin: 0.25rem 0;
    }
    
    /* Sidebar info/success/error messages */
    .stSidebar .stSuccess, .stSidebar .stInfo, .stSidebar .stError, .stSidebar .stWarning {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    /* Force all sidebar text to be visible */
    .stSidebar * {
        color: var(--text-primary) !important;
    }
    
    .stSidebar .stMarkdown h1, .stSidebar .stMarkdown h2, .stSidebar .stMarkdown h3, 
    .stSidebar .stMarkdown h4, .stSidebar .stMarkdown h5, .stSidebar .stMarkdown h6 {
        color: var(--text-primary) !important;
    }
    
    /* Charts */
    .js-plotly-plot {
        border-radius: 1rem;
        overflow: hidden;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 0.5rem;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 0.5rem;
    }
    
    .stWarning {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.2);
        border-radius: 0.5rem;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 0.5rem;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .dashboard-header {
            padding: 1.5rem;
        }
        
        .dashboard-title {
            font-size: 2rem;
        }
        
        .metric-card {
            padding: 1rem;
        }
        
        .job-card {
            padding: 1rem;
        }
    }
</style>
"""

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
                
                if application_status == 'applied':
                    return 'Applied'
                elif application_status in ['documents_ready', 'document_created']:
                    return 'Document Created'
                elif status == 'processed':
                    return 'Processed'
                elif status == 'scraped':
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
    """
    Display job cards in the dashboard overview section.
    Shows up to `limit` jobs from the DataFrame.
    """
    if df is None or df.empty:
        st.info("No jobs to display.")
        return

    jobs_to_show = df.head(limit)
    for _, row in jobs_to_show.iterrows():
        title = row.get('title', 'Unknown Title')
        company = row.get('company', 'Unknown Company')
        location = row.get('location', 'Unknown Location')
        status = row.get('status', 'Status')
        priority = row.get('priority', 'Priority')
        match_score = row.get('match_score', 0)
        status_class = status.lower() if isinstance(status, str) else ''
        priority_class = priority.lower() if isinstance(priority, str) else ''
        stage_emoji = ''  # Optionally map status to emoji
        status_text = status
        action_buttons = ''  # Placeholder for future action buttons

        st.markdown(
            f"""
            <div class="job-card fade-in">
                <div class="job-title">{title}</div>
                <div class="job-company">{company}</div>
                <div class="job-location">📍 {location}</div>
                <div class="job-meta">
                    <span class="job-badge {status_class}">{stage_emoji} {status_text}</span>
                    <span class="job-badge {priority_class}-priority">{priority} Priority</span>
                    <span class="job-badge">Match: {match_score:.0f}%</span>
                </div>
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                    {action_buttons}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

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
        st.markdown("### � Recent Activity")
        
        # Jobs added in last 7 days
        recent_jobs = len(df[df['created_at'] > (datetime.now() - timedelta(days=7))])
        today_jobs = len(df[df['created_at'].dt.date == datetime.now().date()])
        
        recent_col1, recent_col2 = st.columns(2)
        
        with recent_col1:
            st.metric("This Week", recent_jobs)
        
        with recent_col2:
            st.metric("Today", today_jobs)

def apply_to_job_streamlit(job_id: int, job_title: str, company: str, job_url: str, profile_name: str, mode: str) -> None:
    """Apply to a job from the Streamlit dashboard with enhanced orchestration."""
    try:
        from src.core.job_database import get_job_db
        
        # Progress tracking
        progress_container = st.empty()
        status_container = st.empty()
        
        with st.spinner("🚀 Processing application..."):
            db = get_job_db(profile_name)
            
            # Step 1: Auto-Document Generation (if enabled)
            doc_generation_enabled = st.session_state.get('auto_doc_generation', True)
            
            if doc_generation_enabled:
                progress_container.progress(0.2, "📄 Generating job-specific documents...")
                
                try:
                    # Try to generate job-specific documents
                    from src.services.document_generator import DocumentGenerator
                    
                    doc_generator = DocumentGenerator(profile_name)
                    
                    # Generate documents for this specific job
                    job_data = {
                        'id': job_id,
                        'title': job_title,
                        'company': company,
                        'url': job_url
                    }
                    
                    documents = doc_generator.generate_job_specific_documents(job_data)
                    
                    if documents:
                        status_container.success(f"✅ Generated job-specific documents: {len(documents)} files")
                    else:
                        status_container.warning("⚠️ Document generation skipped - using default documents")
                        
                except ImportError:
                    status_container.info("💡 Document generator not available - using manual documents")
                except Exception as e:
                    status_container.warning(f"⚠️ Document generation failed: {str(e)} - proceeding with application")
            
            # Step 2: Application Processing
            progress_container.progress(0.5, "🎯 Processing application...")
            
            if "Manual" in mode:
                # Manual mode: mark as applied and open URL
                db.update_application_status(job_id, "applied", "Applied via Dashboard (Manual)")
                progress_container.progress(1.0, "✅ Application marked as complete!")
                status_container.success(f"✅ Marked as applied: {job_title} at {company}")
                st.markdown(f"🔗 [**Click here to open job page in new tab**]({job_url})")
                
            elif "Hybrid" in mode:
                progress_container.progress(0.7, "🤖 Starting AI-assisted application...")
                
                try:
                    # Hybrid mode: use applier
                    from applier import JobApplier
                    
                    applier = JobApplier(profile_name=profile_name)
                    result = applier.apply_to_job(job_url)
                    
                    if result.get("success"):
                        db.update_application_status(job_id, "applied", "Applied via Dashboard (Hybrid)")
                        progress_container.progress(1.0, "✅ AI-assisted application completed!")
                        status_container.success(f"✅ Application completed: {job_title} at {company}")
                        
                        if result.get("details"):
                            st.info(f"📋 Details: {result['details']}")
                    else:
                        progress_container.progress(0.8, "❌ AI application failed - switching to manual")
                        status_container.error(f"❌ Application failed: {result.get('error', 'Unknown error')}")
                        
                        # Fallback to manual mode
                        db.update_application_status(job_id, "applied", "Applied via Dashboard (Manual Fallback)")
                        status_container.success(f"✅ Marked as applied (manual fallback): {job_title} at {company}")
                        st.markdown(f"🔗 [**Click here to complete application manually**]({job_url})")
                        
                except ImportError:
                    progress_container.progress(0.8, "⚠️ Applier not available - using manual mode")
                    status_container.warning("⚠️ Applier module not available. Falling back to manual mode.")
                    db.update_application_status(job_id, "applied", "Applied via Dashboard (Manual Fallback)")
                    status_container.success(f"✅ Marked as applied: {job_title} at {company}")
                    st.markdown(f"🔗 [**Click here to open job page in new tab**]({job_url})")
            
            # Step 3: Application Queue Integration (Future Enhancement)
            progress_container.progress(0.9, "📊 Updating application queue...")
            
            # Update application metrics
            if 'application_count' not in st.session_state:
                st.session_state['application_count'] = 0
            st.session_state['application_count'] += 1
            
            # Final status
            progress_container.progress(1.0, "🎉 Application process complete!")
            
            # Auto-refresh after successful application
            time.sleep(2)
            st.rerun()
                
    except Exception as e:
        st.error(f"❌ Error applying to job: {str(e)}")
        logger.error(f"Apply error: {e}")
        
        # Show detailed error information for debugging
        with st.expander("🔍 Error Details"):
            st.code(f"""
Error Type: {type(e).__name__}
Error Message: {str(e)}
Job ID: {job_id}
Job Title: {job_title}
Company: {company}
Mode: {mode}
            """)
        
        # Provide manual fallback option
        st.markdown(f"### 🔗 Manual Application Fallback")
        st.markdown(f"You can still apply manually: [**Open {job_title} at {company}**]({job_url})")
        
        if st.button("Mark as Applied Manually", key=f"manual_fallback_{job_id}"):
            try:
                db = get_job_db(profile_name)
                db.update_application_status(job_id, "applied", f"Applied manually after error: {str(e)}")
                st.success("✅ Marked as applied manually")
                time.sleep(1)
                st.rerun()
            except Exception as fallback_error:
                st.error(f"❌ Could not mark as applied: {fallback_error}")


def display_jobs_table(df: pd.DataFrame, profile_name: str = None) -> None:
    """Display jobs in a searchable, filterable table."""
    if df.empty:
        st.warning("📋 No jobs to display")
        return
    
    st.markdown('<h2 class="section-header">📋 Job Management</h2>', unsafe_allow_html=True)
    
    # Filters
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Company filter
            companies = ["All"] + sorted(df['company'].dropna().unique().tolist())
            selected_company = st.selectbox("🏢 Company", companies)
        
        with col2:
            # Status filter - Updated for 4-stage pipeline
            status_options = ["All", "New", "Scraped", "Processed", "Document Created", "Applied"]
            selected_status = st.selectbox("📊 Status", status_options)
        
        with col3:
            # Priority filter
            priority_options = ["All"] + sorted(df['priority'].dropna().unique().tolist())
            selected_priority = st.selectbox("🎯 Priority", priority_options)
        
        with col4:
            # Search
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
        # Select columns to display - Updated for new pipeline
        display_columns = ['title', 'company', 'location', 'status_text', 'priority', 'match_score', 'url']
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        # Format for display
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
        
        # Format URLs as clickable links and add individual Apply buttons
        if 'url' in display_df.columns:
            # Add individual apply functionality for each job row
            apply_buttons = []
            apply_button_keys = []
            
            for idx, row in display_df.iterrows():
                job_url = row.get('url', '')
                job_title = row.get('title', 'Unknown')
                company = row.get('company', 'Unknown')
                job_id = filtered_df.loc[idx, 'id'] if 'id' in filtered_df.columns else idx
                status = filtered_df.loc[idx, 'application_status'] if 'application_status' in filtered_df.columns else 'not_applied'
                
                if status == 'applied':
                    apply_buttons.append('✅ Applied')
                    apply_button_keys.append(None)
                else:
                    # Create unique key for each apply button
                    button_key = f"apply_individual_{idx}_{hash(str(job_url))}"
                    apply_buttons.append('🎯 Apply Now')
                    apply_button_keys.append({
                        'key': button_key,
                        'job_id': job_id,
                        'title': job_title,
                        'company': company,
                        'url': job_url
                    })
            
            display_df['apply_action'] = apply_buttons
            display_df['url'] = display_df['url'].apply(
                lambda x: f'<a href="{x}" target="_blank">🔗 View</a>' if pd.notna(x) and x else 'No URL'
            )
            
            # Store apply button info in session state for button handling
            if 'apply_button_keys' not in st.session_state:
                st.session_state['apply_button_keys'] = {}
            st.session_state['apply_button_keys'] = {info['key']: info for info in apply_button_keys if info}
        
        # Rename columns for better display
        column_names = {
            'title': 'Job Title',
            'company': 'Company',
            'location': 'Location',
            'status_text': 'Pipeline Status',
            'priority': 'Priority',
            'match_score': 'Match',
            'url': 'View Job',
            'apply_action': 'Apply'
        }
        display_df = display_df.rename(columns=column_names)
        
        # Display the dataframe
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=600
        )
        
        # Individual Apply Buttons Section
        if not filtered_df.empty and hasattr(st.session_state, 'apply_button_keys') and st.session_state['apply_button_keys']:
            st.markdown("### 🎯 Individual Job Applications")
            st.markdown("Apply to jobs directly from the table above, or use the quick apply options below:")
            
            # Create columns for individual apply buttons
            apply_cols = st.columns(min(3, len(st.session_state['apply_button_keys'])))
            
            for i, (button_key, job_info) in enumerate(st.session_state['apply_button_keys'].items()):
                col_idx = i % len(apply_cols)
                with apply_cols[col_idx]:
                    # Create individual apply button with mode selection
                    with st.container():
                        st.markdown(f"**{job_info['title']}**")
                        st.markdown(f"*{job_info['company']}*")
                        
                        # Mode selection for this specific job
                        mode_key = f"mode_{button_key}"
                        mode = st.radio(
                            "Application method:",
                            ["Manual", "Hybrid"],
                            key=mode_key,
                            horizontal=True
                        )
                        
                        # Individual apply button
                        if st.button(
                            f"🚀 Apply Now",
                            key=button_key,
                            type="primary",
                            use_container_width=True
                        ):
                            # Show application progress
                            with st.spinner(f"Applying to {job_info['title']}..."):
                                apply_to_job_streamlit(
                                    job_info['job_id'],
                                    job_info['title'],
                                    job_info['company'],
                                    job_info['url'],
                                    profile_name,
                                    mode
                                )
                            
                            # Remove this job from apply buttons (it's now applied)
                            if button_key in st.session_state['apply_button_keys']:
                                del st.session_state['apply_button_keys'][button_key]
                            
                            # Trigger rerun to update the display
                            st.rerun()
        
        # Job Application Section (Dropdown Method - Legacy)
        if not filtered_df.empty:
            st.markdown("### 📋 Batch Job Selection")
            st.markdown("Select multiple jobs for batch processing:")
            
            # Select a job to apply to
            job_options = []
            job_mapping = {}
            
            for idx, row in filtered_df.iterrows():
                status = row.get('application_status', 'not_applied')
                if status != 'applied':
                    job_title = row.get('title', 'Unknown Job')
                    company = row.get('company', 'Unknown Company')
                    job_key = f"{job_title} at {company}"
                    job_options.append(job_key)
                    job_mapping[job_key] = {
                        'id': row.get('id', idx),
                        'title': job_title,
                        'company': company,
                        'url': row.get('url', ''),
                        'index': idx
                    }
            
            if job_options:
                selected_job_key = st.selectbox("Select a job to apply to:", [""] + job_options)
                
                if selected_job_key:
                    job_info = job_mapping[selected_job_key]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        mode = st.radio(
                            "Application method:",
                            ["Manual (Mark as applied)", "Hybrid (AI-assisted)"],
                            key="apply_mode"
                        )
                    
                    with col2:
                        if st.button("🚀 Apply Now", type="primary"):
                            apply_to_job_streamlit(
                                job_info['id'], 
                                job_info['title'], 
                                job_info['company'], 
                                job_info['url'], 
                                profile_name,
                                mode
                            )
            else:
                st.info("✅ All visible jobs have been applied to!")

def display_system_tab(profile_name: str) -> None:
    """Display enhanced system information and orchestration controls with integrated CLI."""
    st.markdown('<h2 class="section-header">� Application Orchestration & System Control</h2>', unsafe_allow_html=True)
    
    # Application Queue Status - prominently displayed first
    st.markdown("### 📊 Application Queue Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    queue_size = st.session_state.get('application_queue_size', 0)
    applications_today = st.session_state.get('application_count', 0)
    applications_per_hour = st.session_state.get('applications_per_hour', 3)
    queue_paused = st.session_state.get('queue_paused', False)
    
    with col1:
        st.metric("📋 Queue Size", queue_size, delta=None)
    
    with col2:
        st.metric("✅ Applied Today", applications_today, delta=None)
    
    with col3:
        rate_text = f"{applications_per_hour}/hour"
        if queue_paused:
            rate_text += " (Paused)"
        st.metric("⏱️ Current Rate", rate_text)
    
    with col4:
        auto_doc = st.session_state.get('auto_doc_generation', True)
        doc_status = "✅ Enabled" if auto_doc else "❌ Disabled"
        st.metric("📄 Auto-Docs", doc_status)
    
    # Quick Orchestration Controls
    st.markdown("### 🎛️ Quick Orchestration Controls")
    
    control_col1, control_col2, control_col3, control_col4 = st.columns(4)
    
    with control_col1:
        if st.button("▶️ Start Queue Processing", key="orch_start_queue", use_container_width=True, disabled=not queue_size > 0):
            st.session_state['queue_paused'] = False
            st.session_state['queue_processing'] = True
            st.success("Queue processing started!")
    
    with control_col2:
        if st.button("⏸️ Pause Queue", key="orch_pause_queue", use_container_width=True, disabled=queue_paused):
            st.session_state['queue_paused'] = True
            st.success("Queue paused!")
    
    with control_col3:
        if st.button("🗑️ Clear Queue", key="orch_clear_queue", use_container_width=True, disabled=not queue_size > 0):
            st.session_state['application_queue_size'] = 0
            st.session_state['application_queue'] = []
            st.success("Queue cleared!")
    
    with control_col4:
        if st.button("🔄 Reset Daily Count", key="orch_reset_count", use_container_width=True):
            st.session_state['application_count'] = 0
            st.success("Daily count reset!")
    
    st.markdown("---")
    
    # Main orchestration controls for backend services
    if HAS_ORCHESTRATION_COMPONENT:
        st.markdown("### 🖥️ Backend Service Controls")
        
        # Quick action buttons for core services
        service_col1, service_col2, service_col3, service_col4 = st.columns(4)
        
        from src.dashboard.components.orchestration_component import EnhancedOrchestrationComponent
        orchestration = EnhancedOrchestrationComponent(profile_name)
        
        with service_col1:
            if st.button("🚀 Start Core Pipeline", key="main_start_core_pipeline", use_container_width=True):
                orchestration._start_all_services()
        
        with service_col2:
            if st.button("⏹️ Stop Core Pipeline", key="main_stop_core_pipeline", use_container_width=True):
                orchestration._stop_all_services()
        
        with service_col3:
            if st.button("🚀 Start 3 Workers", key="main_start_3_workers", use_container_width=True):
                orchestration._start_n_workers(3)
        
        with service_col4:
            if st.button("⏹️ Stop All Workers", key="main_stop_all_workers", use_container_width=True):
                orchestration._stop_worker_pool()
        
        st.markdown("---")
    
    # Create sub-tabs for detailed orchestration features
    system_tabs = st.tabs([
        "📊 Application Queue", 
        "🎛️ Service Control", 
        "👥 Worker Pool", 
        "� Monitoring", 
        "🤖 Auto-Management",
        "🖥️ CLI Commands"
    ])
    
    with system_tabs[0]:  # Application Queue Management
        st.markdown("### 📋 Application Queue Management")
        
        # Queue configuration
        config_col1, config_col2 = st.columns(2)
        
        with config_col1:
            st.markdown("**Queue Settings**")
            
            # Application rate limiting
            new_rate = st.slider(
                "Applications per hour",
                min_value=1,
                max_value=10,
                value=applications_per_hour,
                help="Rate limit for automated applications"
            )
            if new_rate != applications_per_hour:
                st.session_state['applications_per_hour'] = new_rate
                st.success(f"Rate updated to {new_rate}/hour")
            
            # Auto-document generation
            auto_doc_enabled = st.checkbox(
                "Auto-generate documents per job",
                value=st.session_state.get('auto_doc_generation', True),
                help="Generate job-specific resume/cover letter"
            )
            st.session_state['auto_doc_generation'] = auto_doc_enabled
            
            # Background processing
            background_enabled = st.checkbox(
                "Enable background processing",
                value=st.session_state.get('enable_background', False),
                help="Process applications in background"
            )
            st.session_state['enable_background'] = background_enabled
        
        with config_col2:
            st.markdown("**Queue Status**")
            
            # Display queue items
            queue_items = st.session_state.get('application_queue', [])
            
            if queue_items:
                st.markdown("**Queued Applications:**")
                for i, item in enumerate(queue_items[:5]):  # Show first 5
                    st.text(f"{i+1}. {item.get('title', 'Unknown')} at {item.get('company', 'Unknown')}")
                
                if len(queue_items) > 5:
                    st.text(f"... and {len(queue_items) - 5} more")
            else:
                st.info("No applications in queue")
            
            # Queue statistics
            if applications_today > 0:
                avg_time = 300  # Estimated 5 minutes per application
                est_completion = queue_size * avg_time / 60  # Convert to minutes
                st.metric("🕒 Est. Completion", f"{est_completion:.1f} min")
        
        # Bulk queue actions
        st.markdown("**Bulk Actions**")
        bulk_col1, bulk_col2, bulk_col3 = st.columns(3)
        
        with bulk_col1:
            if st.button("📥 Add All Scraped Jobs", key="bulk_add_all", use_container_width=True):
                # Add logic to queue all scraped jobs
                st.info("Feature coming soon - will add all scraped jobs to queue")
        
        with bulk_col2:
            if st.button("🎯 Add Filtered Jobs", key="bulk_add_filtered", use_container_width=True):
                # Add logic to queue filtered jobs
                st.info("Feature coming soon - will add filtered jobs to queue")
        
        with bulk_col3:
            if st.button("📊 Export Queue", key="bulk_export_queue", use_container_width=True):
                # Export queue to CSV
                st.info("Feature coming soon - queue export functionality")
    
    with system_tabs[1]:  # Service Control
        if HAS_ORCHESTRATION_COMPONENT:
            # Use the enhanced orchestration component - Service Control section
            from src.dashboard.components.orchestration_component import EnhancedOrchestrationComponent
            orchestration = EnhancedOrchestrationComponent(profile_name)
            orchestration._render_service_control_panel()
        else:
            _render_fallback_service_control(profile_name)
    
    with system_tabs[2]:  # Worker Pool
        if HAS_ORCHESTRATION_COMPONENT:
            # Worker Pool Management section
            from src.dashboard.components.orchestration_component import EnhancedOrchestrationComponent
            orchestration = EnhancedOrchestrationComponent(profile_name)
            orchestration._render_worker_pool_management()
        else:
            _render_fallback_worker_info()
    
    with system_tabs[3]:  # Monitoring
        if HAS_ORCHESTRATION_COMPONENT:
            # Service Monitoring section
            from src.dashboard.components.orchestration_component import EnhancedOrchestrationComponent
            orchestration = EnhancedOrchestrationComponent(profile_name)
            orchestration._render_service_monitoring()
        else:
            _render_fallback_monitoring()
    
    with system_tabs[4]:  # Auto-Management
        if HAS_ORCHESTRATION_COMPONENT:
            # Auto-Management panel
            from src.dashboard.components.orchestration_component import EnhancedOrchestrationComponent
            orchestration = EnhancedOrchestrationComponent(profile_name)
            orchestration._render_auto_management_panel()
        else:
            _render_fallback_auto_management()
    
    with system_tabs[5]:  # CLI Commands
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
    - � Auto-start scraper when job count drops below threshold
    - ⚙️ Auto-start processor when scraped jobs exceed threshold
    - 👥 Auto-start workers when processed jobs accumulate
    - ✉️ Auto-start applicator when documents are ready
    - ⏹️ Auto-stop services after idle timeout
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
        
        st.markdown("### � Available Features")
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
    """Display logs from various log files."""
    st.markdown('<h2 class="section-header">📄 System Logs</h2>', unsafe_allow_html=True)

    log_files = {
        "Error Log": "error_logs.log",
        "Main Log": "logs/autojobagent.log"
    }

    log_choice = st.selectbox("Select Log File", list(log_files.keys()))

    log_file_path = Path(log_files[log_choice])

    if log_file_path.exists():
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                log_content = f.read()
            st.code(log_content, language='log', line_numbers=True)
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


def main() -> None:
    """Main dashboard function."""
    # Apply unified CSS
    st.markdown(UNIFIED_CSS, unsafe_allow_html=True)
    
    # Set theme class based on dark mode
    theme_class = "dark" if st.session_state["dark_mode"] else "light"
    st.markdown(f'<div data-theme="{theme_class}">', unsafe_allow_html=True)
    
    # Header with controls
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col1:
        st.markdown(
            """
            <div class="dashboard-header">
                <h1 class="dashboard-title">🚀 AutoJobAgent</h1>
                <p class="dashboard-subtitle">Unified Professional Job Management Dashboard</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        dark_mode = st.toggle("🌙 Dark", value=st.session_state["dark_mode"])
        st.session_state["dark_mode"] = dark_mode
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        auto_refresh = st.toggle("🔄 Auto", value=st.session_state["auto_refresh"])
        st.session_state["auto_refresh"] = auto_refresh
    
    # Auto-refresh functionality
    if auto_refresh and HAS_AUTOREFRESH:
        st_autorefresh(interval=60000, key="dashboard_refresh")
    elif auto_refresh and not HAS_AUTOREFRESH:
        st.info("💡 Install `streamlit-autorefresh` for auto-refresh functionality")
    
    # Profile selection
    try:
        profiles = get_available_profiles()
        
        if not profiles:
            st.error("❌ No profiles found. Please create a profile first.")
            st.info("💡 Run the job scraper to create profiles automatically.")
            st.code("python main.py Nirajan --action scrape", language="bash")
            return
        
        # Enhanced profile management in sidebar
        with st.sidebar:
            selected_profile = display_profile_management_sidebar(
                profiles, 
                st.session_state.get("selected_profile", profiles[0])
            )
            st.session_state["selected_profile"] = selected_profile
            
            # Enhanced quick actions
            display_enhanced_quick_actions()
            
            # Application Orchestration Configuration
            st.markdown("---")
            st.markdown("### 🚀 Application Orchestration")
            
            # Auto-document generation toggle
            auto_doc_generation = st.checkbox(
                "📄 Auto-generate job-specific documents",
                value=st.session_state.get('auto_doc_generation', True),
                help="Automatically generate tailored resume/cover letter for each job"
            )
            st.session_state['auto_doc_generation'] = auto_doc_generation
            
            # Application rate limiting
            applications_per_hour = st.slider(
                "⏱️ Applications per hour",
                min_value=1,
                max_value=10,
                value=st.session_state.get('applications_per_hour', 3),
                help="Rate limit for automated applications (recommended: 2-5)"
            )
            st.session_state['applications_per_hour'] = applications_per_hour
            
            # Application queue status
            queue_size = st.session_state.get('application_queue_size', 0)
            applications_today = st.session_state.get('application_count', 0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📊 Queue", queue_size)
            with col2:
                st.metric("✅ Today", applications_today)
            
            # Queue management buttons
            if queue_size > 0:
                if st.button("⏸️ Pause Queue", key="pause_queue", use_container_width=True):
                    st.session_state['queue_paused'] = True
                    st.success("Queue paused")
                    
                if st.button("🗑️ Clear Queue", key="clear_queue", use_container_width=True):
                    st.session_state['application_queue_size'] = 0
                    st.success("Queue cleared")
            
            if st.session_state.get('queue_paused', False):
                if st.button("▶️ Resume Queue", key="resume_queue", use_container_width=True):
                    st.session_state['queue_paused'] = False
                    st.success("Queue resumed")
            
            # Advanced settings
            with st.expander("🔧 Advanced Settings"):
                # Document generation settings
                st.markdown("**Document Generation**")
                doc_template_quality = st.selectbox(
                    "Template Quality",
                    ["Standard", "High", "Premium"],
                    index=1,
                    help="Higher quality takes longer but produces better results"
                )
                st.session_state['doc_template_quality'] = doc_template_quality
                
                # Application retry settings
                st.markdown("**Application Retry Logic**")
                max_retries = st.number_input(
                    "Max retries per job",
                    min_value=0,
                    max_value=5,
                    value=st.session_state.get('max_retries', 2),
                    help="Number of automatic retries for failed applications"
                )
                st.session_state['max_retries'] = max_retries
                
                # Background processing
                st.markdown("**Background Processing**")
                enable_background = st.checkbox(
                    "Enable background orchestration",
                    value=st.session_state.get('enable_background', False),
                    help="Process applications in background with queue management"
                )
                st.session_state['enable_background'] = enable_background
        
        # Load data for selected profile
        with st.spinner("Loading dashboard data..."):
            df = load_job_data(selected_profile)
        
        # Main content tabs
        tabs = st.tabs([
            "📊 Overview", 
            "💼 Jobs", 
            "📈 Analytics", 
            "📄 Documents",
            "⚙️ Orchestration",
            "🖥️ CLI Interface",
            "📄 Logs",
            "🔧 Configuration"
        ])
        
        with tabs[0]:  # Overview
            try:
                display_enhanced_metrics(df)
                display_job_cards(df)
            except Exception as e:
                st.error(f"❌ Error in Overview tab: {e}")
                logger.error(f"Overview tab error: {e}")
        
        with tabs[1]:  # Jobs
            try:
                display_jobs_table(df, selected_profile)
            except Exception as e:
                st.error(f"❌ Error in Jobs tab: {e}")
                logger.error(f"Jobs tab error: {e}")
        
        with tabs[2]:  # Analytics
            try:
                display_analytics_tab(df)
            except Exception as e:
                st.error(f"❌ Error in Analytics tab: {e}")
                logger.error(f"Analytics tab error: {e}")
        
        with tabs[3]:  # Documents
            try:
                if HAS_DOCUMENT_COMPONENT:
                    render_document_generation_tab(selected_profile)
                else:
                    st.error("❌ Document Generation component not available")
                    st.info("The document generation service is not properly installed or configured.")
            except Exception as e:
                st.error(f"❌ Error in Documents tab: {e}")
                logger.error(f"Documents tab error: {e}")

        with tabs[4]:  # System / Orchestration
            try:
                display_system_tab(selected_profile)
            except Exception as e:
                st.error(f"❌ Error in System tab: {e}")
                logger.error(f"System tab error: {e}", exc_info=True)

        with tabs[5]:  # CLI Interface
            try:
                display_cli_tab(selected_profile)
            except Exception as e:
                st.error(f"❌ Error in CLI Interface tab: {e}")
                logger.error(f"CLI Interface tab error: {e}")

        with tabs[6]:  # Logs
            try:
                display_logs_tab()
            except Exception as e:
                st.error(f"❌ Error in Logs tab: {e}")
                logger.error(f"Logs tab error: {e}")

        with tabs[7]:  # Configuration
            try:
                display_configuration_tab()
            except Exception as e:
                st.error(f"❌ Error in Configuration tab: {e}")
                logger.error(f"Configuration tab error: {e}")
            
    except Exception as e:
        st.error(f"❌ Dashboard error: {e}")
        logger.error(f"Dashboard error: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
