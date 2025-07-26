#!/usr/bin/env python3
"""
Dashboard Overview Component
Main overview with key metrics, quick actions, and system status
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import psutil
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

def render_dashboard_overview(df: pd.DataFrame, profile_name: str = "default") -> None:
    """
    Render the main dashboard overview with key metrics and quick actions.
    
    Args:
        df: DataFrame containing job data
        profile_name: Profile name for database operations
    """
    
    # System status header
    render_system_status()
    
    # Key metrics
    render_key_metrics(df)
    
    # Quick actions
    render_quick_actions(profile_name)
    
    # Recent activity
    render_recent_activity(df)
    
    # System health
    render_system_health()

def render_system_status():
    """Render system status header."""
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 2rem; border-radius: 1rem; border: 1px solid #475569;'>
            <h1 style='color: #f1f5f9; margin: 0; font-size: 2.5rem; font-weight: 700;'>🚀 AutoJobAgent</h1>
            <p style='color: #cbd5e1; margin: 0.5rem 0 0 0; font-size: 1.125rem;'>Intelligent Job Application Automation</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # System time
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; text-align: center;'>
            <div style='color: #3b82f6; font-size: 1.5rem; font-weight: 700; font-family: monospace;'>{current_time}</div>
            <div style='color: #cbd5e1; font-size: 0.875rem; margin-top: 0.25rem;'>{current_date}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # System status indicator
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            status_color = "#10b981" if cpu_percent < 70 else "#f59e0b" if cpu_percent < 90 else "#ef4444"
            status_text = "Healthy" if cpu_percent < 70 else "Busy" if cpu_percent < 90 else "High Load"
        except:
            cpu_percent = 0
            status_color = "#6b7280"
            status_text = "Unknown"
        
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; text-align: center;'>
            <div style='color: {status_color}; font-size: 1.25rem; font-weight: 600;'>● {status_text}</div>
            <div style='color: #cbd5e1; font-size: 0.875rem; margin-top: 0.25rem;'>CPU: {cpu_percent:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

def render_key_metrics(df: pd.DataFrame):
    """Render key performance metrics."""
    
    st.markdown("## 📊 Key Metrics")
    
    # Calculate metrics
    total_jobs = len(df) if not df.empty else 0
    applied_jobs = len(df[df.get('status_text', '') == 'Applied']) if not df.empty else 0
    processed_jobs = len(df[df.get('status_text', '') == 'Processed']) if not df.empty else 0
    success_rate = (applied_jobs / total_jobs * 100) if total_jobs > 0 else 0
    
    # Recent activity (last 24 hours)
    if not df.empty and 'scraped_at' in df.columns:
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_jobs = len(df[pd.to_datetime(df['scraped_at'], errors='coerce') > recent_cutoff])
    else:
        recent_jobs = 0
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    metrics = [
        ("📊", "Total Jobs", total_jobs, "#3b82f6", "0"),
        ("✅", "Applied", applied_jobs, "#10b981", f"+{applied_jobs}"),
        ("⚡", "Processed", processed_jobs, "#f59e0b", f"+{processed_jobs}"),
        ("🎯", "Success Rate", f"{success_rate:.1f}%", "#6366f1", f"{success_rate:.1f}%"),
        ("🔥", "Last 24h", recent_jobs, "#ef4444", f"+{recent_jobs}")
    ]
    
    for i, (icon, label, value, color, delta) in enumerate(metrics):
        with [col1, col2, col3, col4, col5][i]:
            st.markdown(f"""
            <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; text-align: center; position: relative; overflow: hidden;'>
                <div style='position: absolute; top: 0; left: 0; right: 0; height: 4px; background: {color};'></div>
                <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>{icon}</div>
                <div style='color: {color}; font-size: 2rem; font-weight: 700; font-family: monospace; margin-bottom: 0.5rem;'>{value}</div>
                <div style='color: #cbd5e1; font-size: 0.875rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;'>{label}</div>
                <div style='color: {color}; font-size: 0.75rem; margin-top: 0.5rem; font-weight: 600;'>{delta}</div>
            </div>
            """, unsafe_allow_html=True)

def render_quick_actions(profile_name: str):
    """Render quick action buttons for common tasks."""
    
    st.markdown("## ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Start Scraping", use_container_width=True, help="Begin job scraping process"):
            try:
                from src.services.orchestration_service import orchestration_service
                success = orchestration_service.start_service("scraper", profile_name)
                if success:
                    st.success("✅ Scraper started!")
                else:
                    st.error("❌ Failed to start scraper")
            except ImportError:
                st.info("💡 Orchestration service not available - would start scraper")
            st.rerun()
    
    with col2:
        if st.button("⚡ Process Jobs", use_container_width=True, help="Process scraped jobs with AI"):
            try:
                from src.services.orchestration_service import orchestration_service
                success = orchestration_service.start_service("processor_worker_1", profile_name)
                if success:
                    st.success("✅ Processor started!")
                else:
                    st.error("❌ Failed to start processor")
            except ImportError:
                st.info("💡 Orchestration service not available - would start processor")
            st.rerun()
    
    with col3:
        if st.button("📄 Generate Docs", use_container_width=True, help="Generate resumes and cover letters"):
            try:
                from src.services.orchestration_service import orchestration_service
                success = orchestration_service.start_service("processor_worker_2", profile_name)
                if success:
                    st.success("✅ Document generator started!")
                else:
                    st.error("❌ Failed to start document generator")
            except ImportError:
                st.info("💡 Orchestration service not available - would start document generator")
            st.rerun()
    
    with col4:
        if st.button("📤 Apply to Jobs", use_container_width=True, help="Submit job applications"):
            try:
                from src.services.orchestration_service import orchestration_service
                success = orchestration_service.start_service("applicator", profile_name)
                if success:
                    st.success("✅ Applicator started!")
                else:
                    st.error("❌ Failed to start applicator")
            except ImportError:
                st.info("💡 Orchestration service not available - would start applicator")
            st.rerun()
    
    # Service status indicators
    st.markdown("### 🔧 Service Status")
    
    try:
        from src.services.orchestration_service import orchestration_service
        services_status = orchestration_service.get_all_services_status()
        
        # Display service status in a compact format
        status_cols = st.columns(6)
        service_names = ["scraper", "processor_worker_1", "processor_worker_2", "processor_worker_3", "processor_worker_4", "applicator"]
        
        for i, service_name in enumerate(service_names):
            with status_cols[i]:
                status = services_status.get(service_name, {}).get('status', 'stopped')
                status_icon = "🟢" if status == "running" else "🔴"
                status_color = "#10b981" if status == "running" else "#6b7280"
                
                st.markdown(f"""
                <div style='background: #1e293b; padding: 0.75rem; border-radius: 0.5rem; border: 1px solid #334155; text-align: center;'>
                    <div style='font-size: 1.25rem;'>{status_icon}</div>
                    <div style='color: {status_color}; font-size: 0.75rem; font-weight: 500; margin-top: 0.25rem;'>{service_name.replace('_', ' ').title()}</div>
                </div>
                """, unsafe_allow_html=True)
                
    except ImportError:
        st.info("💡 Service status will appear here when orchestration service is available")

def render_recent_activity(df: pd.DataFrame):
    """Render recent activity feed."""
    
    st.markdown("## 📈 Recent Activity")
    
    if df.empty:
        st.info("No recent activity to display")
        return
    
    # Get recent jobs (last 7 days)
    if 'scraped_at' in df.columns:
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_df = df[pd.to_datetime(df['scraped_at'], errors='coerce') > recent_cutoff].copy()
        recent_df = recent_df.sort_values('scraped_at', ascending=False).head(10)
    else:
        recent_df = df.head(10)
    
    if recent_df.empty:
        st.info("No recent activity in the last 7 days")
        return
    
    # Activity timeline
    for _, job in recent_df.iterrows():
        status = job.get('status_text', 'Unknown')
        title = job.get('title', 'Unknown Job')
        company = job.get('company', 'Unknown Company')
        scraped_time = job.get('scraped_at', datetime.now())
        
        # Format time
        if isinstance(scraped_time, str):
            try:
                scraped_time = pd.to_datetime(scraped_time)
            except:
                scraped_time = datetime.now()
        
        time_ago = datetime.now() - scraped_time
        if time_ago.days > 0:
            time_str = f"{time_ago.days}d ago"
        elif time_ago.seconds > 3600:
            time_str = f"{time_ago.seconds // 3600}h ago"
        else:
            time_str = f"{time_ago.seconds // 60}m ago"
        
        # Status color
        status_colors = {
            'Applied': '#10b981',
            'Document Created': '#6366f1',
            'Processed': '#f59e0b',
            'Scraped': '#3b82f6'
        }
        status_color = status_colors.get(status, '#6b7280')
        
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1rem; border-radius: 0.5rem; border: 1px solid #334155; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 1rem;'>
            <div style='width: 8px; height: 40px; background: {status_color}; border-radius: 4px;'></div>
            <div style='flex: 1;'>
                <div style='color: #f1f5f9; font-weight: 600; margin-bottom: 0.25rem;'>{title}</div>
                <div style='color: #cbd5e1; font-size: 0.875rem;'>{company}</div>
            </div>
            <div style='text-align: right;'>
                <div style='color: {status_color}; font-size: 0.75rem; font-weight: 500; padding: 0.25rem 0.5rem; background: rgba({int(status_color[1:3], 16)}, {int(status_color[3:5], 16)}, {int(status_color[5:7], 16)}, 0.1); border-radius: 0.25rem; margin-bottom: 0.25rem;'>{status}</div>
                <div style='color: #9ca3af; font-size: 0.75rem;'>{time_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_system_health():
    """Render system health monitoring."""
    
    st.markdown("## 🏥 System Health")
    
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/' if sys.platform != 'win32' else 'C:\\')
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cpu_color = "#10b981" if cpu_percent < 70 else "#f59e0b" if cpu_percent < 90 else "#ef4444"
            st.markdown(f"""
            <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155;'>
                <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;'>
                    <div style='font-size: 1.25rem;'>🖥️</div>
                    <div style='color: #f1f5f9; font-weight: 600;'>CPU Usage</div>
                </div>
                <div style='color: {cpu_color}; font-size: 2rem; font-weight: 700; font-family: monospace;'>{cpu_percent:.1f}%</div>
                <div style='background: #334155; height: 8px; border-radius: 4px; margin-top: 0.5rem; overflow: hidden;'>
                    <div style='background: {cpu_color}; height: 100%; width: {cpu_percent}%; transition: width 0.3s ease;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            memory_color = "#10b981" if memory.percent < 70 else "#f59e0b" if memory.percent < 90 else "#ef4444"
            st.markdown(f"""
            <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155;'>
                <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;'>
                    <div style='font-size: 1.25rem;'>💾</div>
                    <div style='color: #f1f5f9; font-weight: 600;'>Memory Usage</div>
                </div>
                <div style='color: {memory_color}; font-size: 2rem; font-weight: 700; font-family: monospace;'>{memory.percent:.1f}%</div>
                <div style='background: #334155; height: 8px; border-radius: 4px; margin-top: 0.5rem; overflow: hidden;'>
                    <div style='background: {memory_color}; height: 100%; width: {memory.percent}%; transition: width 0.3s ease;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            disk_color = "#10b981" if disk.percent < 80 else "#f59e0b" if disk.percent < 95 else "#ef4444"
            st.markdown(f"""
            <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155;'>
                <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;'>
                    <div style='font-size: 1.25rem;'>💿</div>
                    <div style='color: #f1f5f9; font-weight: 600;'>Disk Usage</div>
                </div>
                <div style='color: {disk_color}; font-size: 2rem; font-weight: 700; font-family: monospace;'>{disk.percent:.1f}%</div>
                <div style='background: #334155; height: 8px; border-radius: 4px; margin-top: 0.5rem; overflow: hidden;'>
                    <div style='background: {disk_color}; height: 100%; width: {disk.percent}%; transition: width 0.3s ease;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Unable to get system metrics: {e}")
        st.info("System health monitoring requires psutil package")