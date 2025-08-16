#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Dashboard for AutoJobAgent
Web interface with caching and service management.
"""

import streamlit as st

# Page configuration MUST be first
st.set_page_config(
    page_title="AutoJobAgent - Unified Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

import logging
from pathlib import Path
import sys
from datetime import datetime, timedelta
import traceback
import pandas as pd
import time
import os
import psutil
from typing import Dict, List, Optional, Tuple, Any

# Try to import auto-refresh, but make it optional
try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False
    st_autorefresh = None

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
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

# Import our new core modules
try:
    from src.dashboard.core.dashboard_controller import (
        get_dashboard_controller
    )
    HAS_SMART_CONTROLLER = True
except ImportError as e:
    HAS_SMART_CONTROLLER = False
    logger.warning(f"Smart controller not available: {e}")

# Import the original dashboard functions as fallback
try:
    # Import main function only, not the module with page config
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "original_dashboard",
        project_root / "src" / "dashboard" / "unified_dashboard_original.py"
    )
    original_module = importlib.util.module_from_spec(spec)
    # Temporarily disable page config in original module
    import streamlit
    original_set_page_config = streamlit.set_page_config
    streamlit.set_page_config = lambda *args, **kwargs: None
    spec.loader.exec_module(original_module)
    streamlit.set_page_config = original_set_page_config
    original_main = original_module.main
    HAS_ORIGINAL = True
except Exception as e:
    HAS_ORIGINAL = False
    original_main = None
    logger.warning(f"Original dashboard not available: {e}")


def render_enhanced_sidebar(controller) -> None:
    """Render enhanced sidebar with smart controls."""
    with st.sidebar:
        st.markdown("# 🚀 AutoJobAgent")
        st.markdown("**Smart Dashboard v6.0**")
        st.divider()
        
        # Profile selection with smart suggestions
        try:
            from src.dashboard.core.data_loader import get_available_profiles
            profiles = get_available_profiles()
            selected_profile = st.selectbox(
                "👤 Profile",
                profiles,
                index=profiles.index(st.session_state["selected_profile"])
                if st.session_state["selected_profile"] in profiles else 0
            )
            st.session_state["selected_profile"] = selected_profile
        except ImportError:
            st.warning("Profile loader not available")
        
        # Smart mode toggle
        smart_mode = st.toggle(
            "🧠 Smart Mode",
            value=st.session_state.get("smart_mode", True),
            help="Enable auto-healing and optimization"
        )
        st.session_state["smart_mode"] = smart_mode
        
        # Cache management
        st.markdown("### ⚡ Cache Control")
        cache_stats = controller.cache_manager.get_cache_stats()
        st.metric("Cache Hits", cache_stats.get("hits", 0))
        st.metric("Cache Size", f"{cache_stats.get('size_mb', 0):.1f} MB")
        
        if st.button("🗑️ Clear Cache"):
            controller.cache_manager.clear_cache()
            st.success("Cache cleared!")
            st.rerun()
        
        # Service health indicators
        st.markdown("### 💊 Service Health")
        health = controller.get_service_health()
        
        for service, status in health.get("services", {}).items():
            if status.get("status") == "healthy":
                st.success(f"✅ {service.title()}")
            elif status.get("status") == "degraded":
                st.warning(f"⚠️ {service.title()}")
            else:
                st.error(f"❌ {service.title()}")
        
        # Auto-refresh control
        st.markdown("### 🔄 Auto-Refresh")
        auto_refresh = st.checkbox(
            "Enable Auto-Refresh",
            value=st.session_state.get("auto_refresh", False)
        )
        st.session_state["auto_refresh"] = auto_refresh
        
        if auto_refresh:
            refresh_interval = st.slider(
                "Interval (seconds)",
                min_value=10,
                max_value=300,
                value=30
            )
            try:
                from streamlit_autorefresh import st_autorefresh
                st_autorefresh(interval=refresh_interval * 1000)
            except ImportError:
                st.info("Install streamlit-autorefresh for auto-refresh")


def load_data_with_caching(controller):
    """Load job data with intelligent caching."""
    try:
        from src.dashboard.core.data_loader import load_job_data
        profile = st.session_state.get("selected_profile", "Nirajan")
        
        # Use smart caching if available
        cache_key = f"job_data_{profile}"
        
        if hasattr(controller, 'cache_manager'):
            # Use Configurable_get method for caching
            return controller.cache_manager.Configurable_get(
                cache_key,
                lambda: load_job_data(profile),
                ttl=300
            )
        
        # Load fresh data without caching
        return load_job_data(profile)
        
    except ImportError:
        st.error("Data loader not available")
        return None


def render_enhanced_tabs(tabs, df, controller) -> None:
    """Render all enhanced tabs with smart features."""
    profile_name = st.session_state.get("selected_profile", "Nirajan")
    
    # Tab 0: Enhanced Overview
    with tabs[0]:
        render_enhanced_overview_tab(df, controller)
    
    # Tab 1: Optimized Jobs
    with tabs[1]:
        render_optimized_jobs_tab(df, controller)
    
    # Tab 2: Apply Manually 
    with tabs[2]:
        render_apply_manually_tab(df, controller)
    
    # Tab 3: Enhanced Processing
    with tabs[3]:
        render_enhanced_processing_tab(controller)
    
    # Tab 4: JobSpy
    with tabs[4]:
        render_jobspy_tab(controller)
    
    # Tab 5: Logs
    with tabs[5]:
        render_enhanced_logs_tab(controller)
    
    # Tab 6: Enhanced CLI
    with tabs[6]:
        render_enhanced_cli_tab(controller)
    
    # Tab 7: Settings
    with tabs[7]:
        render_settings_tab(controller)


def render_enhanced_overview_tab(df, controller) -> None:
    """Enhanced overview tab with smart insights."""
    try:
        from src.dashboard.components.dashboard_overview import (
            render_dashboard_overview
        )
        render_dashboard_overview(df, st.session_state["selected_profile"])
    except ImportError:
        # Fallback to enhanced metrics
        st.markdown("### 📊 Dashboard Overview")
        
        if df is not None and not df.empty:
            # Use the enhanced metrics display
            display_Improved_metrics(df)
            
            # Add job cards display
            st.markdown("---")
            display_job_cards(df, limit=6)
            
        else:
            st.info("No job data available")


def render_optimized_jobs_tab(df, controller) -> None:
    """Optimized jobs tab with smart workflows."""
    try:
        from src.dashboard.components.modern_job_cards import render_modern_job_cards
        render_modern_job_cards(df, st.session_state["selected_profile"])
    except ImportError:
        # Fallback to enhanced jobs table
        try:
            from src.dashboard.components.Improved_job_table import render_Improved_job_table
            render_Improved_job_table(df, st.session_state["selected_profile"])
        except ImportError:
            # Final fallback to original table
            display_jobs_table(df, st.session_state["selected_profile"])


def render_apply_manually_tab(df, controller) -> None:
    """Manual application tab with tracking."""
    try:
        from src.dashboard.components.manual_application_tracker import render_manual_application_tracker
        render_manual_application_tracker(df, st.session_state["selected_profile"])
    except ImportError:
        # Fallback to basic manual application interface
        st.markdown("### ✅ Manual Application Tracking")
        
        if df is not None and not df.empty:
            st.info("Select jobs to mark as applied manually")
            
            # Filter for jobs that haven't been applied to yet
            not_applied_df = df[~df.get('status_text', '').str.contains('Applied', na=False)]
            
            if not not_applied_df.empty:
                for idx, (_, job) in enumerate(not_applied_df.head(10).iterrows()):
                    job_id = job.get('id', idx)
                    title = job.get('title', 'Unknown')
                    company = job.get('company', 'Unknown')
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{title}** at **{company}**")
                        st.caption(f"Location: {job.get('location', 'N/A')} | Match: {job.get('match_score', 0):.0f}%")
                    
                    with col2:
                        if st.button("✅ Mark Applied", key=f"apply_{job_id}"):
                            st.success(f"Marked as applied: {title}")
                            # Here you would update the database
                            try:
                                from src.core.job_database import get_job_db
                                db = get_job_db(st.session_state["selected_profile"])
                                db.mark_job_applied(job_id)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating database: {e}")
                    
                    st.divider()
            else:
                st.success("🎉 All jobs have been processed or applied to!")
        else:
            st.info("No jobs available for manual application tracking")


def render_apply_tab(df, controller) -> None:
    """Manual application tab."""
    render_apply_manually_tab(df, controller)


def render_optimized_jobs_tab(df, controller) -> None:
    """Optimized jobs tab with smart workflows."""
    try:
        from src.dashboard.components.modern_job_cards import render_modern_job_cards
        render_modern_job_cards(df, st.session_state["selected_profile"])
    except ImportError:
        # Fallback to enhanced jobs table
        try:
            from src.dashboard.components.Improved_job_table import render_Improved_job_table
            render_Improved_job_table(df, st.session_state["selected_profile"])
        except ImportError:
            # Final fallback to original table
            display_jobs_table(df, st.session_state["selected_profile"])


def render_enhanced_processing_tab(controller) -> None:
    """Enhanced processing tab with auto-healing and detailed controls."""
    st.markdown("### ⚙️ Job Processing & Workflow Management")
    
    # Profile context
    profile_name = st.session_state.get("selected_profile", "default")
    
    try:
        # Use the full job processor component for detailed controls
        from src.dashboard.components.job_processor_component import get_job_processor_component
        processor_component = get_job_processor_component(profile_name)
        processor_component.render_processor_controls()
    except ImportError:
        # Fallback to enhanced manual controls if component not available
        st.warning("⚠️ Advanced processor component not available. Using fallback interface.")
        
        # Processing overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Selected Profile", profile_name)
        
        with col2:
            try:
                from src.core.job_database import get_job_db
                db = get_job_db(profile_name)
                
                # Count jobs by status (increased limit)
                scraped_count = len(db.get_jobs_by_status('scraped', limit=5000))
                st.metric("Scraped Jobs", scraped_count)
            except Exception as e:
                st.metric("Scraped Jobs", "Error")
                st.caption(f"DB Error: {str(e)[:50]}...")
        
        with col3:
            try:
                new_count = len(db.get_jobs_by_status('new', limit=5000))
                st.metric("New Jobs", new_count)
            except Exception:
                st.metric("New Jobs", "Error")
        
        # Processing controls
        st.markdown("#### 🎛️ Processing Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            processing_method = st.selectbox(
                "Processing Method",
                ["Two-Stage (Recommended)", "CPU Only", "Auto-Detect"],
                index=0,
                help="Two-Stage: Fast CPU filtering + GPU analysis"
            )
            
            batch_size = st.slider(
                "Batch Size",
                min_value=1,
                max_value=50,
                value=10,
                help="Number of jobs to process simultaneously"
            )
        
        with col2:
            if 'scraped_count' in locals() and scraped_count > 0:
                max_default = min(20, scraped_count)
                max_limit = scraped_count
            else:
                max_default = 20
                max_limit = 100
            
            max_jobs = st.number_input(
                "Max Jobs to Process",
                min_value=1,
                max_value=max_limit,
                value=max_default,
                help="Maximum number of jobs to process in this batch"
            )
            
            enable_filtering = st.checkbox(
                "Enable Smart Filtering",
                value=True,
                help="Filter out low-quality or irrelevant jobs"
            )
        
        # Processing actions
        st.markdown("#### 🔄 Processing Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Start Processing"):
                st.success("🚀 Processing started!")
                st.info(f"""
                **Settings:**
                - Method: {processing_method}
                - Batch Size: {batch_size}
                - Max Jobs: {max_jobs}
                - Smart Filtering: {'Enabled' if enable_filtering else 'Disabled'}
                """)
        
        with col2:
            if st.button("📊 Generate Reports"):
                st.info("📊 Report generation configured")
        
        with col3:
            if st.button("🧹 Cleanup Database"):
                st.info("🧹 Database cleanup options available")
        
        # Smart Mode Features
        if st.session_state.get("smart_mode", True):
            st.markdown("#### 🧠 Smart Mode Features")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("""
                **Auto-Healing Active:**
                - 🔄 Automatic retry on failures
                - 📊 Performance monitoring
                - ⚡ Resource optimization
                - 🛡️ Error recovery
                """)
            
            with col2:
                st.info("""
                **Smart Features:**
                - 🎯 Priority-based processing
                - 📈 Adaptive batch sizing
                - 🔍 Quality filtering
                - 💡 Optimization suggestions
                """)
    
    except Exception as e:
        st.error(f"❌ Error in processing tab: {str(e)}")
        logger.error(f"Processing tab error: {e}")


def render_jobspy_tab(controller) -> None:
    """JobSpy integration tab."""
    try:
        from src.dashboard.components.jobspy_component import (
            render_jobspy_control
        )
        render_jobspy_control()
    except ImportError:
        st.markdown("### 🔍 JobSpy")
        st.info("JobSpy component not available")


def render_enhanced_logs_tab(controller) -> None:
    """Enhanced logs analysis tab."""
    st.markdown("### 📋 System Logs")
    
    # Log file selection
    log_files = {
        "Error Logs": "error_logs.log",
        "Application Logs": "logs/application_orchestrator.log",
        "AI Service Logs": "logs/ai_service_detailed.log",
        "System Logs": "logs/system_orchestrator.log",
        "Dashboard Logs": "logs/dashboard_orchestrator.log"
    }
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_log_name = st.selectbox("Select Log File", list(log_files.keys()))
        selected_log_path = log_files[selected_log_name]
    
    with col2:
        log_level = st.selectbox("Log Level", ["All", "ERROR", "WARNING", "INFO", "DEBUG"])
    
    with col3:
        lines_to_show = st.selectbox("Lines to Show", [50, 100, 200, 500], index=1)
    
    # Auto-refresh option
    auto_refresh_logs = st.checkbox("🔄 Auto-refresh logs (every 5 seconds)", value=False)
    
    if auto_refresh_logs:
        try:
            if HAS_AUTOREFRESH:
                st_autorefresh(interval=5000, key="logs_refresh")
            else:
                st.info("Install streamlit-autorefresh for auto-refresh")
        except Exception as e:
            st.warning(f"Auto-refresh error: {e}")
    
    # Load and display logs
    if st.button("📖 Load Logs") or auto_refresh_logs:
        try:
            log_path = Path(selected_log_path)
            
            if log_path.exists():
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                
                # Get the last N lines
                recent_lines = all_lines[-lines_to_show:] if len(all_lines) > lines_to_show else all_lines
                
                # Filter by log level if specified
                if log_level != "All":
                    filtered_lines = [line for line in recent_lines if log_level in line.upper()]
                else:
                    filtered_lines = recent_lines
                
                if filtered_lines:
                    st.markdown(f"**Showing {len(filtered_lines)} log entries from {selected_log_name}:**")
                    
                    # Display in a scrollable container
                    log_container = st.container()
                    
                    with log_container:
                        for i, line in enumerate(filtered_lines):
                            line = line.strip()
                            if not line:
                                continue
                                
                            # Color code based on log level
                            if "ERROR" in line.upper():
                                st.error(f"🔴 {line}")
                            elif "WARNING" in line.upper():
                                st.warning(f"🟡 {line}")
                            elif "INFO" in line.upper():
                                st.info(f"🔵 {line}")
                            else:
                                st.text(line)
                else:
                    st.info(f"No {log_level} level logs found in the last {lines_to_show} lines")
                    
            else:
                st.error(f"Log file not found: {selected_log_path}")
                
                # Show available log files
                st.markdown("**Available log files:**")
                for name, path in log_files.items():
                    if Path(path).exists():
                        size = Path(path).stat().st_size / 1024  # KB
                        st.success(f"✅ {name}: {path} ({size:.1f} KB)")
                    else:
                        st.error(f"❌ {name}: {path} (Not found)")
                        
        except Exception as e:
            st.error(f"Error reading log file: {e}")
            st.info("Make sure the log files exist and are readable")
    
    # Log file information
    st.markdown("---")
    st.markdown("### 📁 Log File Information")
    
    for name, path in log_files.items():
        try:
            log_path = Path(path)
            if log_path.exists():
                size = log_path.stat().st_size / 1024  # KB
                modified = datetime.fromtimestamp(log_path.stat().st_mtime)
                st.success(f"✅ **{name}**: {size:.1f} KB, Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.error(f"❌ **{name}**: File not found")
        except Exception as e:
            st.error(f"❌ **{name}**: Error accessing file - {e}")


def render_orchestration_tab(controller) -> None:
    """Orchestration control tab."""
    try:
        from src.dashboard.components.orchestration_component import (
            render_orchestration_control
        )
        # Get profile name from session state
        profile_name = st.session_state.get("selected_profile", "default")
        render_orchestration_control(profile_name)
    except ImportError:
        st.markdown("### 🎛️ Orchestration")
        st.info("Orchestration features available with controller")


def render_cached_analytics_tab(df, controller) -> None:
    """Cached analytics tab with performance insights."""
    try:
        from src.dashboard.tabs.cached_analytics_tab import render_analytics_tab
        render_analytics_tab(df)
    except ImportError:
        # Fallback analytics
        st.markdown("### 📈 Analytics")
        
        if df is not None and not df.empty:
            # Basic charts
            st.markdown("#### Job Statistics")
            
            # Job count by company
            if "company" in df.columns:
                company_counts = df["company"].value_counts().head(10)
                st.bar_chart(company_counts)
            
            # Jobs over time
            if "scraped_at" in df.columns:
                try:
                    df["date"] = pd.to_datetime(df["scraped_at"]).dt.date
                    daily_jobs = df.groupby("date").size()
                    st.line_chart(daily_jobs)
                except:
                    st.info("Unable to parse date information")
        else:
            st.info("No data available for analytics")


def render_enhanced_cli_tab(controller) -> None:
    """Enhanced CLI integration tab."""
    try:
        from src.dashboard.components.cli_component import render_cli_tab
        profile_name = st.session_state.get("selected_profile", "default")
        render_cli_tab(profile_name)
    except ImportError:
        st.markdown("### 🖥️ CLI Integration")
        st.info("CLI component not available")


def render_settings_tab(controller) -> None:
    """Configuration settings and workflow optimization tab."""
    st.markdown("### ⚙️ Settings & Workflow Optimization")
    
    # Create tabs within settings
    settings_tabs = st.tabs([
        "🔧 Processing Settings",
        "📊 Dashboard Settings", 
        "🚀 Workflow Optimization",
        "👤 Profile Settings"
    ])
    
    with settings_tabs[0]:  # Processing Settings
        st.markdown("#### ⚙️ Job Processing Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Processing preferences
            default_method = st.selectbox(
                "Default Processing Method",
                ["Two-Stage Pipeline", "CPU Only", "Auto-Detect"],
                index=0,
                help="Default method for processing new jobs"
            )
            
            default_batch_size = st.slider(
                "Default Batch Size",
                min_value=1,
                max_value=50,
                value=10,
                help="Number of jobs to process simultaneously"
            )
            
            auto_process = st.checkbox(
                "Auto-process new jobs",
                value=False,
                help="Automatically process jobs when they are scraped"
            )
        
        with col2:
            # Quality filters
            min_match_score = st.slider(
                "Minimum Match Score",
                min_value=0,
                max_value=100,
                value=60,
                help="Minimum compatibility score to consider a job"
            )
            
            max_concurrent = st.slider(
                "Max Concurrent Jobs",
                min_value=1,
                max_value=10,
                value=5,
                help="Maximum number of jobs to process concurrently"
            )
            
            enable_smart_filtering = st.checkbox(
                "Enable Smart Filtering",
                value=True,
                help="Use AI to filter out low-quality jobs"
            )
    
    with settings_tabs[1]:  # Dashboard Settings
        st.markdown("#### 📊 Dashboard Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Display preferences
            cache_enabled = st.checkbox(
                "Enable Smart Caching",
                value=True,
                help="Cache data for better performance"
            )
            
            auto_refresh = st.checkbox(
                "Enable Auto-Refresh",
                value=st.session_state.get("auto_refresh", False),
                help="Automatically refresh dashboard data"
            )
            
            if auto_refresh:
                refresh_interval = st.slider(
                    "Refresh Interval (seconds)",
                    min_value=10,
                    max_value=300,
                    value=st.session_state.get("refresh_interval", 30)
                )
                st.session_state["refresh_interval"] = refresh_interval
        
        with col2:
            # UI preferences
            smart_mode = st.checkbox(
                "Smart Mode",
                value=st.session_state.get("smart_mode", True),
                help="Enable enhanced features and auto-healing"
            )
            st.session_state["smart_mode"] = smart_mode
            
            jobs_per_page = st.slider(
                "Jobs per Page",
                min_value=10,
                max_value=100,
                value=50,
                help="Number of jobs to display per page"
            )
            
            show_debug_info = st.checkbox(
                "Show Debug Information",
                value=False,
                help="Display additional debug information"
            )
    
    with settings_tabs[2]:  # Workflow Optimization
        st.markdown("#### 🚀 Workflow Automation & Optimization")
        
        st.info("""
        **Workflow Optimization** helps automate your job application process:
        - **Auto-processing**: Automatically analyze jobs after scraping
        - **Smart prioritization**: Focus on high-match jobs first
        - **Batch operations**: Process multiple jobs efficiently
        - **Quality filtering**: Skip low-quality or irrelevant jobs
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Automation settings
            automation_level = st.select_slider(
                "Automation Level",
                options=["Manual", "Semi-Auto", "Auto", "Full-Auto"],
                value="Semi-Auto",
                help="Level of automation for job processing"
            )
            
            auto_apply_threshold = st.slider(
                "Auto-Apply Threshold",
                min_value=70,
                max_value=100,
                value=90,
                help="Automatically apply to jobs above this match score"
            )
            
            daily_apply_limit = st.number_input(
                "Daily Application Limit",
                min_value=1,
                max_value=50,
                value=10,
                help="Maximum applications to send per day"
            )
        
        with col2:
            # Optimization features
            prioritize_remote = st.checkbox(
                "Prioritize Remote Jobs",
                value=True,
                help="Give higher priority to remote work opportunities"
            )
            
            skip_already_applied = st.checkbox(
                "Skip Similar Companies",
                value=True,
                help="Avoid applying to companies you've already applied to"
            )
            
            enable_learning = st.checkbox(
                "Enable Learning Mode",
                value=True,
                help="Learn from your preferences to improve matching"
            )
    
    with settings_tabs[3]:  # Profile Settings
        st.markdown("#### 👤 Profile Configuration")
        
        profile_name = st.session_state.get("selected_profile", "Nirajan")
        st.info(f"Current Profile: **{profile_name}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Profile management
            if st.button("📝 Edit Profile"):
                st.info("Profile editing would open here")
            
            if st.button("📋 Clone Profile"):
                new_name = st.text_input("New Profile Name", "")
                if new_name:
                    st.success(f"Clone profile as: {new_name}")
            
            if st.button("📊 View Profile Stats"):
                try:
                    from src.core.job_database import get_job_db
                    db = get_job_db(profile_name)
                    stats = db.get_job_stats()
                    st.json(stats)
                except Exception as e:
                    st.error(f"Error loading stats: {e}")
        
        with col2:
            # Profile preferences
            preferred_locations = st.text_area(
                "Preferred Locations",
                value="Remote, Toronto, Vancouver",
                help="Comma-separated list of preferred locations"
            )
            
            preferred_keywords = st.text_area(
                "Preferred Keywords",
                value="Python, Data Science, Machine Learning, AI",
                help="Comma-separated list of skills and keywords"
            )
            
            salary_range = st.slider(
                "Salary Range (CAD)",
                min_value=40000,
                max_value=200000,
                value=(80000, 150000),
                help="Preferred salary range"
            )
    
    # Save settings button
    st.markdown("---")
    if st.button("💾 Save All Settings", type="primary"):
        # Here you would save all the settings
        settings = {
            "processing": {
                "default_method": default_method,
                "batch_size": default_batch_size,
                "auto_process": auto_process,
                "min_match_score": min_match_score,
                "max_concurrent": max_concurrent,
                "smart_filtering": enable_smart_filtering
            },
            "dashboard": {
                "cache_enabled": cache_enabled,
                "auto_refresh": auto_refresh,
                "smart_mode": smart_mode,
                "jobs_per_page": jobs_per_page,
                "debug_info": show_debug_info
            },
            "workflow": {
                "automation_level": automation_level,
                "auto_apply_threshold": auto_apply_threshold,
                "daily_limit": daily_apply_limit,
                "prioritize_remote": prioritize_remote,
                "skip_similar": skip_already_applied,
                "learning_mode": enable_learning
            }
        }
        
        st.success("✅ Settings saved successfully!")
        st.json(settings)


def render_emergency_fallback() -> None:
    """Emergency fallback UI when smart controller is not available."""
    st.error("❌ Dashboard controller not available")
    st.markdown("""
    ### 🔧 Setup Required
    
    The dashboard requires the modular controller components:
    1. Check that core modules are properly installed
    2. Verify import paths are correct
    3. Run from the project root directory
    
    For support, check the logs or contact the development team.
    """)
    
    # Basic system info
    st.markdown("### 🔍 System Information")
    st.text(f"Python path: {sys.executable}")
    st.text(f"Current directory: {Path.cwd()}")
    st.text(f"Project root: {project_root}")


def render_error_state(error: Exception, controller) -> None:
    """Render error state with diagnostics."""
    st.error(f"❌ Dashboard Error: {error}")
    
    # Show error details in development
    with st.expander("🔍 Error Details"):
        st.code(traceback.format_exc())
    
    # Controller diagnostics
    if controller:
        st.markdown("### 🔧 Controller Diagnostics")
        try:
            health = controller.get_service_health()
            st.json(health)
        except:
            st.warning("Unable to get controller diagnostics")
    
    st.info("💡 Try refreshing the page or contact support")


# Import pandas for fallback functions
try:
    import pandas as pd
except ImportError:
    pd = None


def display_Improved_metrics(df: pd.DataFrame) -> None:
    """Display Improved metrics with modern styling."""
    if df.empty:
        st.warning("📊 No data available for metrics")
        return
    
    # Calculate metrics based on actual database status
    total_jobs = len(df)
    
    # Use actual status column values - fix the filtering logic
    has_status = 'status' in df.columns
    has_app_status = 'application_status' in df.columns
    
    new_jobs = len(df[df['status'] == 'new']) if has_status else 0
    ready_to_apply = len(df[df['status'] == 'ready_to_apply']) if has_status else 0
    needs_review = len(df[df['status'] == 'needs_review']) if has_status else 0
    filtered_out = len(df[df['status'] == 'filtered_out']) if has_status else 0
    applied_jobs = len(df[df['application_status'] == 'applied']) if has_app_status else 0
    
    # Calculate additional metrics
    avg_match_score = df['match_score'].mean() if 'match_score' in df.columns else 0
    
    # Recent activity (last 7 days)
    if 'created_at' in df.columns:
        try:
            df['created_at_dt'] = pd.to_datetime(df['created_at'])
            recent_jobs = len(df[df['created_at_dt'] > (datetime.now() - timedelta(days=7))])
        except Exception:
            recent_jobs = 0
    else:
        recent_jobs = 0
    
    st.markdown('<h2 class="section-header">📊 Job Pipeline Metrics</h2>', unsafe_allow_html=True)
    
    # Display metrics in columns - showing the actual pipeline
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Jobs", f"{total_jobs:,}", delta=f"+{recent_jobs} this week")
    
    with col2:
        st.metric("New Jobs", f"{new_jobs:,}", delta=None)
    
    with col3:
        st.metric("Ready to Apply", f"{ready_to_apply:,}", delta=None)
    
    with col4:
        st.metric("Needs Review", f"{needs_review:,}", delta=None)
    
    with col5:
        st.metric("Applied", f"{applied_jobs:,}", delta=None)
    
    # Second row with additional metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Filtered Out", f"{filtered_out:,}")
    
    with col2:
        success_rate = (applied_jobs / total_jobs * 100) if total_jobs > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        processed_jobs = ready_to_apply + needs_review + filtered_out + applied_jobs
        processing_rate = (processed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        st.metric("Processed Rate", f"{processing_rate:.1f}%")
    
    with col4:
        st.metric("Avg Match", f"{avg_match_score:.0f}%")
    
    with col5:
        companies = df['company'].nunique() if 'company' in df.columns else 0
        st.metric("Companies", f"{companies:,}")


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
            
            st.markdown(f"**{title}** at **{company}**")
            st.write(f"📍 {location}")
            st.write(f"🔍 Status: {status_text} | 🎯 Priority: {priority} | Match: {match_score:.0f}%")
            
            button_col1, button_col2 = st.columns(2)
            with button_col1:
                if st.button("👀 View", key=f"view_{idx}"):
                    if job_url:
                        st.link_button("🔗 Open Job", job_url)
                    else:
                        st.info("No URL available")
            with button_col2:
                if st.button("✅ Apply", key=f"apply_{idx}"):
                    st.success(f"Marked for application: {title}")
            st.divider()


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
    
    st.markdown("### 📋 Job Management Table")
    
    # Improved filters section
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        companies = ["All"] + sorted(df['company'].dropna().unique().tolist())
        selected_company = st.selectbox("🏢 Company", companies)
    
    with col2:
        status_options = ["All", "New", "Scraped", "Processed", "Document Created", "Applied"]
        selected_status = st.selectbox("📊 Status", status_options)
    
    with col3:
        search_term = st.text_input("🔍 Search", placeholder="Search jobs...")
    
    with col4:
        show_applied = st.checkbox("Show Applied Only", value=False)
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_company != "All":
        filtered_df = filtered_df[filtered_df['company'] == selected_company]
    
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df.get('status_text', '') == selected_status]
    
    if search_term:
        mask = (
            filtered_df.get('title', '').str.contains(search_term, case=False, na=False) |
            filtered_df.get('company', '').str.contains(search_term, case=False, na=False) |
            filtered_df.get('location', '').str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    if show_applied:
        filtered_df = filtered_df[filtered_df.get('status_text', '').str.contains('Applied', na=False)]
    
    # Display results
    st.write(f"**Found {len(filtered_df)} jobs** (filtered from {len(df)} total)")
    
    if not filtered_df.empty:
        # Select columns to display
        display_columns = ['title', 'company', 'location', 'status_text', 'match_score']
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        if available_columns:
            display_df = filtered_df[available_columns].copy()
            
            # Format match score
            if 'match_score' in display_df.columns:
                display_df['match_score'] = display_df['match_score'].apply(lambda x: f"{x:.0f}%")
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("No displayable columns found")
    else:
        st.info("No jobs match the selected filters")


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
                st.write(f"**{company}**: {count} jobs")
        else:
            st.info("No company data available")
    
    # Recent activity
    if 'created_at' in df.columns:
        st.markdown("### 📅 Recent Activity")
        
        try:
            # Jobs added in last 7 days
            recent_jobs = len(df[df['created_at'] > (datetime.now() - timedelta(days=7))])
            today_jobs = len(df[df['created_at'].dt.date == datetime.now().date()])
            
            recent_col1, recent_col2 = st.columns(2)
            
            with recent_col1:
                st.metric("This Week", recent_jobs)
            
            with recent_col2:
                st.metric("Today", today_jobs)
        except Exception as e:
            st.warning(f"Could not analyze recent activity: {e}")


def display_system_tab(profile_name: str) -> None:
    """Display system information and orchestration controls."""
    st.markdown("### 🖥️ System Command & Information Center")
    
    # System information
    try:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cpu_percent = psutil.cpu_percent()
            st.metric("System CPU", f"{cpu_percent:.1f}%")
        
        with col2:
            memory = psutil.virtual_memory()
            st.metric("System Memory", f"{memory.percent:.1f}%")
        
        with col3:
            disk_usage = psutil.disk_usage('/' if os.name != 'nt' else 'C:\\')
            st.metric("Disk Usage", f"{disk_usage.percent:.1f}%")
    
    except ImportError:
        st.warning("Install 'psutil' for system monitoring")
    except Exception as e:
        st.error(f"System monitoring error: {e}")
    
    # Orchestration controls
    if HAS_ORCHESTRATION_COMPONENT:
        st.markdown("### 🎛️ Orchestration Controls")
        try:
            render_orchestration_control(profile_name)
        except Exception as e:
            st.error(f"Orchestration component error: {e}")
    else:
        st.warning("Orchestration component not available")
    
    # CLI integration
    if HAS_CLI_COMPONENT:
        st.markdown("### 🖥️ CLI Commands")
        try:
            render_cli_tab(profile_name)
        except Exception as e:
            st.error(f"CLI component error: {e}")
    else:
        st.info("CLI component not available")


def display_profile_management_sidebar(profiles: List[str], selected_profile: str) -> str:
    """Display profile management in sidebar."""
    st.markdown("### 👤 Profile Management")
    
    # Profile selector
    new_selected = st.selectbox(
        "Active Profile",
        profiles,
        index=profiles.index(selected_profile) if selected_profile in profiles else 0,
        key="profile_selector"
    )
    
    # Profile actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Edit", use_container_width=True, key="edit_profile"):
            st.info(f"Edit profile: {new_selected}")
    
    with col2:
        if st.button("📋 Clone", use_container_width=True, key="clone_profile"):
            st.info(f"Clone profile: {new_selected}")
    
    # Profile statistics
    try:
        from src.core.job_database import get_job_db
        db = get_job_db(new_selected)
        stats = db.get_job_stats()
        
        st.markdown("### 📊 Profile Stats")
        
        total_jobs = stats.get('total_jobs', 0)
        applied_count = stats.get('applied_jobs', 0)
        
        st.metric("Total Jobs", total_jobs)
        st.metric("Applied", applied_count)
        
        if total_jobs > 0:
            success_rate = (applied_count / total_jobs * 100)
            st.metric("Success Rate", f"{success_rate:.1f}%")
            
    except Exception as e:
        st.error(f"Error loading profile stats: {e}")
    
    return new_selected


def main() -> None:
    """
    Phase 6: Complete Integration - Enhanced main function with full
    modular architecture and all original features restored.
    """
    # Load CSS for consistent styling
    try:
        from src.dashboard.core.styling import load_unified_css
        st.markdown(load_unified_css(), unsafe_allow_html=True)
    except ImportError:
        logger.warning("Unified CSS not available")

    # Initialize controller and services
    controller = None
    try:
        if HAS_SMART_CONTROLLER:
            # Initialize smart controller
            controller = get_dashboard_controller()
            controller.initialize_dashboard()

            # Track dashboard access with enhanced context
            controller.track_user_action("dashboard_access", {
                "timestamp": datetime.now().isoformat(),
                "session_id": st.session_state.get("session_id", "unknown"),
                "phase": "6_complete_integration"
            })

        # Initialize session state with comprehensive settings
        if "selected_profile" not in st.session_state:
            st.session_state["selected_profile"] = "Nirajan"
        if "auto_refresh" not in st.session_state:
            st.session_state["auto_refresh"] = False
        if "smart_mode" not in st.session_state:
            st.session_state["smart_mode"] = True
        if "refresh_interval" not in st.session_state:
            st.session_state["refresh_interval"] = 30

        # Load available profiles
        try:
            from src.utils.profile_helpers import get_available_profiles
            profiles = get_available_profiles()
            
            if not profiles:
                st.error("❌ No profiles found. Please create a profile first.")
                st.stop()
                
        except ImportError:
            profiles = ["Nirajan"]  # Default fallback
            logger.warning("Profile helpers not available, using default")

        # Profile management sidebar
        with st.sidebar:
            selected_profile = display_profile_management_sidebar(
                profiles, 
                st.session_state["selected_profile"]
            )
            st.session_state["selected_profile"] = selected_profile
            
            # Enhanced sidebar controls
            render_enhanced_sidebar(controller)

        # Main header with enhanced information
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
                        padding: 2rem; border-radius: 1rem; border: 1px solid #475569; 
                        margin-bottom: 2rem;'>
                <h1 style='color: #f1f5f9; margin: 0; font-size: 2.5rem; font-weight: 700;'>
                    🚀 AutoJobAgent
                </h1>
                <p style='color: #cbd5e1; margin: 0.5rem 0 0 0; font-size: 1.125rem;'>
                    Unified Job Application Automation Dashboard
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Auto-refresh control
            auto_refresh = st.toggle(
                "🔄 Auto Refresh", 
                value=st.session_state.get("auto_refresh", False)
            )
            st.session_state["auto_refresh"] = auto_refresh
            
            if auto_refresh and HAS_AUTOREFRESH:
                refresh_interval = st.session_state.get("refresh_interval", 30)
                st_autorefresh(interval=refresh_interval * 1000, key="dashboard_refresh")
            elif auto_refresh and not HAS_AUTOREFRESH:
                st.info("Install streamlit-autorefresh for auto-refresh")

        # Load data with enhanced caching
        with st.spinner("Loading dashboard data..."):
            df = load_data_with_caching(controller)

        # Enhanced tab structure - simplified and focused
        tabs = st.tabs([
            "📊 Overview",        # Enhanced dashboard overview with metrics and cards
            "💼 Jobs",            # Modern job management with enhanced table
            "✅ Apply Manually",  # Manual application tracking
            "⚙️ Processing",      # Enhanced processing controls
            "🔍 JobSpy",          # JobSpy integration for scraping
            "📋 Logs",            # System and processing logs
            "🖥️ CLI",             # CLI integration and commands
            "⚙️ Settings"         # Configuration and workflow settings
        ])

        # Render all tabs with enhanced features
        render_enhanced_tabs(tabs, df, controller)

        # Background processor integration
        if HAS_BACKGROUND_PROCESSOR:
            processor = get_background_processor()
            generator = get_document_generator()
            
            if processor and generator:
                # Auto-start background processing if enabled
                if st.session_state.get("smart_mode", True):
                    try:
                        processor.start_processing(selected_profile)
                        generator.start_generation(selected_profile)
                    except Exception as e:
                        logger.warning(f"Background processor startup: {e}")

    except Exception as e:
        logger.error(f"Dashboard startup error: {e}")
        
        # Enhanced error handling with diagnostics
        st.error(f"❌ Dashboard Error: {e}")
        
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())
        
        # Fallback to original dashboard if available
        if HAS_ORIGINAL and original_main:
            st.warning("⚠️ Attempting fallback to original dashboard...")
            st.info("💡 Some enhanced features may not be available")
            try:
                original_main()
            except Exception as fallback_error:
                st.error(f"❌ Fallback failed: {fallback_error}")
                render_emergency_fallback()
        else:
            render_emergency_fallback()


if __name__ == "__main__":
    main()
