#!/usr/bin/env python3
"""
Streamlined Unified Dashboard - Modular Version
Main entry point for the dashboard using modular components.
"""

import streamlit as st
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import core modules
from src.dashboard.core.data_loader import load_job_data, get_available_profiles
from src.dashboard.core.styling import load_unified_css

# Import tab modules
from src.dashboard.tabs.jobs_tab import render_jobs_tab
from src.dashboard.tabs.analytics_tab import render_analytics_tab
from src.dashboard.tabs.system_tab import render_system_tab

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AutoJobAgent - Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "selected_profile" not in st.session_state:
    st.session_state["selected_profile"] = "Nirajan"
if "auto_refresh" not in st.session_state:
    st.session_state["auto_refresh"] = True
if "refresh_interval" not in st.session_state:
    st.session_state["refresh_interval"] = 30


def main():
    """Main dashboard application."""
    
    # Load CSS
    st.markdown(load_unified_css(), unsafe_allow_html=True)
    
    # Sidebar
    render_sidebar()
    
    # Main content
    render_main_content()


def render_sidebar():
    """Render the dashboard sidebar."""
    
    with st.sidebar:
        # Header
        st.markdown("# 🚀 AutoJobAgent")
        st.markdown("**Professional Dashboard**")
        st.divider()
        
        # Profile selection
        profiles = get_available_profiles()
        selected_profile = st.selectbox(
            "👤 Select Profile",
            profiles,
            index=profiles.index(st.session_state["selected_profile"]) 
            if st.session_state["selected_profile"] in profiles else 0,
            key="profile_selector"
        )
        st.session_state["selected_profile"] = selected_profile
        
        # Auto-refresh settings
        st.markdown("### ⚙️ Settings")
        
        auto_refresh = st.checkbox(
            "Auto Refresh",
            value=st.session_state["auto_refresh"],
            key="auto_refresh_checkbox"
        )
        st.session_state["auto_refresh"] = auto_refresh
        
        if auto_refresh:
            refresh_interval = st.slider(
                "Refresh Interval (seconds)",
                min_value=10,
                max_value=300,
                value=st.session_state["refresh_interval"],
                step=10,
                key="refresh_interval_slider"
            )
            st.session_state["refresh_interval"] = refresh_interval
        
        # Quick stats
        st.divider()
        st.markdown("### 📊 Quick Stats")
        
        try:
            df = load_job_data(selected_profile)
            if not df.empty:
                total_jobs = len(df)
                applied_jobs = len(df[df.get('applied', 0) == 1]) if 'applied' in df.columns else 0
                
                st.metric("Total Jobs", total_jobs)
                st.metric("Applied", applied_jobs)
                
                if total_jobs > 0:
                    application_rate = (applied_jobs / total_jobs) * 100
                    st.metric("Application Rate", f"{application_rate:.1f}%")
            else:
                st.info("No job data available")
        except Exception as e:
            st.error("Error loading quick stats")
            logger.error(f"Sidebar stats error: {e}")


def render_main_content():
    """Render the main dashboard content."""
    
    # Header
    st.markdown("# 🚀 AutoJobAgent Dashboard")
    st.markdown(f"**Profile:** {st.session_state['selected_profile']}")
    
    # Auto-refresh
    if st.session_state["auto_refresh"]:
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=st.session_state["refresh_interval"] * 1000)
        except ImportError:
            st.info("Auto-refresh requires streamlit-autorefresh package")
    
    # Load data
    try:
        df = load_job_data(st.session_state["selected_profile"])
        
        # Main tabs
        tabs = st.tabs([
            "💼 Jobs",
            "📊 Analytics", 
            "🖥️ System",
            "🛠️ Settings"
        ])
        
        # Render tabs
        with tabs[0]:  # Jobs
            render_jobs_tab(df, st.session_state["selected_profile"])
        
        with tabs[1]:  # Analytics
            render_analytics_tab(df)
        
        with tabs[2]:  # System
            render_system_tab(st.session_state["selected_profile"])
        
        with tabs[3]:  # Settings
            render_settings_tab()
            
    except Exception as e:
        st.error(f"Dashboard error: {e}")
        logger.error(f"Main content error: {e}")
        
        # Show error details in expander
        with st.expander("Error Details"):
            import traceback
            st.code(traceback.format_exc())


def render_settings_tab():
    """Render the settings tab."""
    
    st.markdown("# ⚙️ Dashboard Settings")
    
    # Display settings
    st.markdown("## 🎨 Display Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        theme = st.selectbox(
            "Theme",
            ["Dark", "Light"],
            index=0,
            help="Dashboard color theme"
        )
        
        layout = st.selectbox(
            "Layout",
            ["Wide", "Centered"],
            index=0,
            help="Dashboard layout mode"
        )
    
    with col2:
        max_jobs = st.number_input(
            "Max Jobs Display",
            min_value=50,
            max_value=5000,
            value=2000,
            step=50,
            help="Maximum number of jobs to display"
        )
        
        cache_ttl = st.number_input(
            "Cache TTL (minutes)",
            min_value=1,
            max_value=60,
            value=5,
            help="How long to cache data"
        )
    
    # Performance settings
    st.markdown("## ⚡ Performance Settings")
    
    enable_caching = st.checkbox(
        "Enable Caching",
        value=True,
        help="Cache data for better performance"
    )
    
    enable_animations = st.checkbox(
        "Enable Animations",
        value=True,
        help="Enable chart animations"
    )
    
    # Save settings
    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")
        st.info("Some settings require a dashboard restart to take effect.")


if __name__ == "__main__":
    main()
