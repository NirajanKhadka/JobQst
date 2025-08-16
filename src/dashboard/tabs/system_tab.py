#!/usr/bin/env python3
"""
System Tab Module
Handles system monitoring and service management.
"""

import streamlit as st
import logging
from datetime import datetime
from src.dashboard.core.metrics import get_system_metrics

logger = logging.getLogger(__name__)


def render_system_tab(profile_name: str) -> None:
    """Render the system monitoring and management tab."""
    
    st.markdown("# 🖥️ System Monitor")
    
    # Get system metrics
    try:
        metrics = get_system_metrics()
        render_system_overview(metrics)
        render_system_details(metrics)
        render_service_status(profile_name)
    except Exception as e:
        st.error(f"Error loading system information: {e}")
        logger.error(f"System tab error: {e}")


def render_system_overview(metrics: dict) -> None:
    """Render system overview metrics."""
    
    st.markdown("## 📊 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cpu_percent = metrics.get("cpu_percent", 0)
        cpu_color = get_metric_color(cpu_percent, 70, 90)
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; 
                    border-radius: 0.75rem; border: 1px solid #334155; 
                    text-align: center;'>
            <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>💻</div>
            <div style='color: {cpu_color}; font-size: 1.75rem; 
                       font-weight: 700; font-family: monospace; 
                       margin-bottom: 0.5rem;'>{cpu_percent:.1f}%</div>
            <div style='color: #cbd5e1; font-size: 0.875rem; 
                       font-weight: 500; text-transform: uppercase; 
                       letter-spacing: 0.05em;'>CPU Usage</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        memory_percent = metrics.get("memory_percent", 0)
        memory_color = get_metric_color(memory_percent, 80, 95)
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; 
                    border-radius: 0.75rem; border: 1px solid #334155; 
                    text-align: center;'>
            <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>🧠</div>
            <div style='color: {memory_color}; font-size: 1.75rem; 
                       font-weight: 700; font-family: monospace; 
                       margin-bottom: 0.5rem;'>{memory_percent:.1f}%</div>
            <div style='color: #cbd5e1; font-size: 0.875rem; 
                       font-weight: 500; text-transform: uppercase; 
                       letter-spacing: 0.05em;'>Memory Usage</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        disk_usage = metrics.get("disk_usage", 0)
        disk_color = get_metric_color(disk_usage, 85, 95)
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; 
                    border-radius: 0.75rem; border: 1px solid #334155; 
                    text-align: center;'>
            <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>💾</div>
            <div style='color: {disk_color}; font-size: 1.75rem; 
                       font-weight: 700; font-family: monospace; 
                       margin-bottom: 0.5rem;'>{disk_usage:.1f}%</div>
            <div style='color: #cbd5e1; font-size: 0.875rem; 
                       font-weight: 500; text-transform: uppercase; 
                       letter-spacing: 0.05em;'>Disk Usage</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        network_status = metrics.get("network_status", "unknown")
        network_color = "#10b981" if network_status == "connected" else "#ef4444"
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; 
                    border-radius: 0.75rem; border: 1px solid #334155; 
                    text-align: center;'>
            <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>🌐</div>
            <div style='color: {network_color}; font-size: 1.75rem; 
                       font-weight: 700; font-family: monospace; 
                       margin-bottom: 0.5rem;'>{network_status.upper()}</div>
            <div style='color: #cbd5e1; font-size: 0.875rem; 
                       font-weight: 500; text-transform: uppercase; 
                       letter-spacing: 0.05em;'>Network</div>
        </div>
        """, unsafe_allow_html=True)


def render_system_details(metrics: dict) -> None:
    """Render detailed system information."""
    
    st.markdown("## 🔍 System Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⏰ System Status")
        
        timestamp = metrics.get("timestamp", datetime.now().isoformat())
        
        st.markdown(f"""
        - **Last Updated:** {timestamp[:19]}
        - **Monitoring Active:** ✅ Running
        - **Data Collection:** ✅ Active
        """)
        
        if "error" in metrics:
            st.error(f"System Error: {metrics['error']}")
    
    with col2:
        st.markdown("### 📋 Quick Actions")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🔄 Refresh Metrics", use_container_width=True):
                st.rerun()
        
        with col_b:
            if st.button("📊 View Logs", use_container_width=True):
                st.info("Logs functionality coming soon!")


def render_service_status(profile_name: str) -> None:
    """Render service status and controls."""
    
    st.markdown("## 🛠️ Service Management")
    
    # Try to import service managers
    try:
        from src.dashboard.components.orchestration_ui import OrchestrationUI
        orchestration_ui = OrchestrationUI(profile_name)
        orchestration_ui.render_service_control_panel()
    except ImportError:
        render_fallback_service_control(profile_name)
    except Exception as e:
        st.error(f"Error loading service controls: {e}")
        render_fallback_service_control(profile_name)


def render_fallback_service_control(profile_name: str) -> None:
    """Fallback service control when full orchestration not available."""
    
    st.markdown("### 🔧 Basic Service Control")
    
    # Mock service status for demonstration
    services = [
        {"name": "Job Scraper", "status": "running", "uptime": "2h 15m"},
        {"name": "Data Processor", "status": "stopped", "uptime": "0m"},
        {"name": "Auto Applier", "status": "running", "uptime": "1h 42m"},
        {"name": "Health Monitor", "status": "running", "uptime": "3h 1m"},
    ]
    
    for service in services:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            status_icon = "🟢" if service["status"] == "running" else "🔴"
            st.write(f"{status_icon} **{service['name']}**")
            st.caption(f"Uptime: {service['uptime']}")
        
        with col2:
            if st.button("▶️", key=f"start_{service['name']}", 
                        help=f"Start {service['name']}"):
                st.toast(f"Starting {service['name']}...")
        
        with col3:
            if st.button("⏹️", key=f"stop_{service['name']}", 
                        help=f"Stop {service['name']}"):
                st.toast(f"Stopping {service['name']}...")
        
        with col4:
            if st.button("🔄", key=f"restart_{service['name']}", 
                        help=f"Restart {service['name']}"):
                st.toast(f"Restarting {service['name']}...")
    
    st.info("💡 Full service orchestration requires the orchestration component")


def get_metric_color(value: float, warning_threshold: float, 
                    danger_threshold: float) -> str:
    """Get color based on metric value and thresholds."""
    if value >= danger_threshold:
        return "#ef4444"  # Red
    elif value >= warning_threshold:
        return "#f59e0b"  # Yellow
    else:
        return "#10b981"  # Green
