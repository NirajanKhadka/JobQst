#!/usr/bin/env python3
"""
Orchestration UI - Streamlit UI components for orchestration
Single responsibility: Render orchestration UI components
Max 300 lines following development standards
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .service_manager import get_service_manager
from .worker_pool_manager import get_worker_pool_manager
from .system_monitor import get_system_monitor
from .auto_manager import get_auto_manager, AutoManagementPolicy
from src.core.job_database import get_job_db

# New centralized orchestration package (discovery/processing APIs)
try:
    from src.orchestration import OrchestratorConfig, run_jobspy_discovery, run_processing_batches
    HAS_CORE_ORCHESTRATION_APIS = True
except Exception:
    HAS_CORE_ORCHESTRATION_APIS = False

class OrchestrationUI:
    """
    Streamlit UI components for orchestration management.
    Follows single responsibility principle - only handles UI rendering.
    """
    
    def __init__(self, profile_name: str):
        """Initialize orchestration UI."""
        self.profile_name = profile_name
        self.service_manager = get_service_manager()
        self.worker_pool_manager = get_worker_pool_manager()
        self.system_monitor = get_system_monitor()
        self.auto_manager = get_auto_manager()
    
    def render_service_control_panel(self) -> None:
        """Render the service control panel."""
        st.markdown("### 🔧 Service Control Panel")
        
        # Get service statuses
        all_services = self.service_manager.get_all_services_status()
        
        # Service control buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Start All Services", key="orch_start_all_services"):
                for service_name in all_services.keys():
                    self.service_manager.start_service(service_name, self.profile_name)
                st.success("Started all services")
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop All Services", key="orch_stop_all_services"):
                stopped_count = self.service_manager.stop_all_services()
                st.success(f"Stopped {stopped_count} services")
                st.rerun()
        
        with col3:
            if st.button("🔄 Restart All Services", key="orch_restart_all_services"):
                for service_name in all_services.keys():
                    self.service_manager.restart_service(service_name, self.profile_name)
                st.success("Restarted all services")
                st.rerun()
        
        # Individual service controls
        st.markdown("#### Individual Service Controls")
        for service_name, status in all_services.items():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                status_color = "🟢" if status["status"] == "running" else "🔴"
                st.write(f"{status_color} **{service_name}** - {status.get('description', 'No description')}")
                st.caption(f"Uptime: {status.get('uptime', '00:00:00')} | Processed: {status.get('processed_count', 0)}")
            
            with col2:
                if st.button("▶️", key=f"orch_start_{service_name}", help=f"Start {service_name}"):
                    if self.service_manager.start_service(service_name, self.profile_name):
                        st.toast(f"✅ Started {service_name}")
                    st.rerun()
            
            with col3:
                if st.button("⏹️", key=f"orch_stop_{service_name}", help=f"Stop {service_name}"):
                    if self.service_manager.stop_service(service_name):
                        st.toast(f"⏹️ Stopped {service_name}")
                    st.rerun()
            
            with col4:
                if st.button("🔄", key=f"orch_restart_{service_name}", help=f"Restart {service_name}"):
                    if self.service_manager.restart_service(service_name, self.profile_name):
                        st.toast(f"🔄 Restarted {service_name}")
                    st.rerun()
    
    def render_worker_pool_management(self) -> None:
        """Render the worker pool management panel."""
        st.markdown("### 👥 5-Worker Pool Management")
        
        # Get worker pool status
        pool_status = self.worker_pool_manager.get_worker_pool_status()
        performance_metrics = self.worker_pool_manager.get_worker_performance_metrics()
        
        # Pool overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Workers", pool_status["total_workers"])
        
        with col2:
            st.metric("Running Workers", pool_status["running_workers"])
        
        with col3:
            st.metric("Queue Size", pool_status["queue_size"])
        
        with col4:
            st.metric("Efficiency Score", f"{performance_metrics['efficiency_score']:.1f}%")
        
        # Worker pool controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Start Worker Pool", key="orch_start_worker_pool"):
                results = self.worker_pool_manager.start_worker_pool(self.profile_name)
                success_count = sum(1 for success in results.values() if success)
                st.success(f"Started {success_count}/{len(results)} workers")
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop Worker Pool", key="orch_stop_worker_pool"):
                results = self.worker_pool_manager.stop_worker_pool()
                success_count = sum(1 for success in results.values() if success)
                st.success(f"Stopped {success_count}/{len(results)} workers")
                st.rerun()
        
        with col3:
            new_size = st.number_input("Scale Pool Size", min_value=1, max_value=10, 
                                     value=pool_status["total_workers"], key="orch_pool_size")
            if st.button("📏 Scale Pool", key="orch_scale_pool"):
                if self.worker_pool_manager.scale_worker_pool(new_size, self.profile_name):
                    st.success(f"Scaled pool to {new_size} workers")
                st.rerun()
        
        # Individual worker status
        st.markdown("#### Individual Worker Status")
        worker_statuses = self.worker_pool_manager.get_individual_worker_status()
        
        for worker_name, status in worker_statuses.items():
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                status_color = "🟢" if status["status"] == "running" else "🔴"
                st.write(f"{status_color} **{worker_name}**")
                st.caption(f"CPU: {status.get('cpu_usage', 0):.1f}% | Memory: {status.get('memory_usage', 0):.1f}%")
            
            with col2:
                st.metric("Processed", status.get('processed_count', 0))
            
            with col3:
                st.write(status.get('uptime', '00:00:00'))
        
        # Optionally expose quick job discovery/processing actions via the centralized APIs
        if HAS_CORE_ORCHESTRATION_APIS:
            with st.expander("Quick Orchestration Actions", expanded=False):
                profile = self.profile_name
                if st.button("Discover Jobs (JobSpy Controller)", key="orch_discover_jobs_quick"):
                    cfg = OrchestratorConfig()
                    summary = run_jobspy_discovery(cfg, profile)
                    st.success(f"Discovered {summary.total_jobs} jobs across {len(summary.dataframe_summary.get('sites', []))} sites")
                if st.button("Process Pending Jobs (Two-Stage)", key="orch_process_jobs_quick"):
                    # Fetch a small batch from DB to demo processing entrypoint (UI remains non-blocking)
                    try:
                        db = get_job_db(profile)
                        jobs = db.get_jobs_by_status('scraped', limit=50)
                    except Exception:
                        jobs = []
                    cfg = OrchestratorConfig()
                    results = run_processing_batches(jobs, cfg)
                    st.info(f"Processed {len(results)} jobs via controller")
    
    def render_system_monitoring(self) -> None:
        """Render the system monitoring panel."""
        st.markdown("### 📊 System Monitoring")
        
        # Get system health summary
        health_summary = self.system_monitor.get_system_health_summary()
        
        # Health overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Overall Health", f"{health_summary['overall_health_score']:.1f}%")
        
        with col2:
            st.metric("System Health", f"{health_summary['system_health_score']:.1f}%")
        
        with col3:
            st.metric("Service Health", f"{health_summary['service_health_score']:.1f}%")
        
        with col4:
            st.metric("Running Services", f"{health_summary['running_services']}/{health_summary['service_count']}")
        
        # System metrics chart
        metrics_history = self.system_monitor.get_metrics_history(30)
        if metrics_history:
            timestamps = [m.timestamp for m in metrics_history]
            cpu_data = [m.cpu_percent for m in metrics_history]
            memory_data = [m.memory_percent for m in metrics_history]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=timestamps, y=cpu_data, name="CPU %", line=dict(color="red")))
            fig.add_trace(go.Scatter(x=timestamps, y=memory_data, name="Memory %", line=dict(color="blue")))
            
            fig.update_layout(
                title="System Resource Usage (Last 30 minutes)",
                xaxis_title="Time",
                yaxis_title="Usage %",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Health alerts
        if health_summary["alerts"]:
            st.markdown("#### 🚨 Health Alerts")
            for alert in health_summary["alerts"]:
                if alert["level"] == "critical":
                    st.error(f"🔴 {alert['message']}")
                elif alert["level"] == "warning":
                    st.warning(f"🟡 {alert['message']}")
    
    def render_auto_management_panel(self) -> None:
        """Render the auto-management panel."""
        st.markdown("### 🤖 Auto-Management")
        
        # Auto-management controls
        col1, col2 = st.columns(2)
        
        with col1:
            current_policy = self.auto_manager.get_policy()
            policy_options = [policy.value for policy in AutoManagementPolicy]
            
            selected_policy = st.selectbox(
                "Auto-Management Policy",
                policy_options,
                index=policy_options.index(current_policy.value),
                key="auto_policy"
            )
            
            if selected_policy != current_policy.value:
                new_policy = AutoManagementPolicy(selected_policy)
                self.auto_manager.set_policy(new_policy)
                st.success(f"Policy changed to: {selected_policy}")
                st.rerun()
        
        with col2:
            is_enabled = self.auto_manager.is_enabled()
            
            if st.button("🟢 Enable" if not is_enabled else "🔴 Disable", key="orch_toggle_auto_mgmt"):
                if is_enabled:
                    self.auto_manager.disable_auto_management()
                    st.success("Auto-management disabled")
                else:
                    self.auto_manager.enable_auto_management()
                    st.success("Auto-management enabled")
                st.rerun()
        
        # Run manual cycle
        if st.button("🔄 Run Management Cycle", key="orch_run_auto_cycle"):
            result = self.auto_manager.run_auto_management_cycle(self.profile_name)
            
            if result["actions_taken"]:
                st.success(f"Executed {len(result['actions_taken'])} auto-management actions")
                for action in result["actions_taken"]:
                    status_icon = "✅" if action["success"] else "❌"
                    st.write(f"{status_icon} {action['rule']}")
            else:
                st.info("No auto-management actions needed")
        
        # Rules status
        st.markdown("#### Auto-Management Rules")
        rules_status = self.auto_manager.get_rules_status()
        
        for rule in rules_status:
            col1, col2, col3 = st.columns([3, 1, 2])
            
            with col1:
                enabled_icon = "🟢" if rule["enabled"] else "🔴"
                st.write(f"{enabled_icon} **{rule['name']}**")
            
            with col2:
                can_execute_icon = "✅" if rule["can_execute"] else "⏳"
                st.write(f"{can_execute_icon}")
            
            with col3:
                last_exec = rule["last_executed"]
                if last_exec:
                    exec_time = datetime.fromisoformat(last_exec).strftime("%H:%M:%S")
                    st.caption(f"Last: {exec_time}")
                else:
                    st.caption("Never executed")


# Factory function for the unified dashboard
def render_orchestration_control(profile_name: str) -> None:
    """Render the complete orchestration control interface."""
    orchestration_ui = OrchestrationUI(profile_name)
    
    # Create tabs for different orchestration aspects
    tabs = st.tabs(["🔧 Services", "👥 Workers", "📊 Monitoring", "🤖 Auto-Mgmt"])
    
    with tabs[0]:
        orchestration_ui.render_service_control_panel()
    
    with tabs[1]:
        orchestration_ui.render_worker_pool_management()
    
    with tabs[2]:
        orchestration_ui.render_system_monitoring()
    
    with tabs[3]:
        orchestration_ui.render_auto_management_panel()


# Improved orchestration component class for backward compatibility
class ImprovedOrchestrationComponent:
    """Backward compatibility wrapper for the old orchestration component."""
    
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.ui = OrchestrationUI(profile_name)
    
    def render(self) -> None:
        """Render the complete orchestration interface."""
        render_orchestration_control(self.profile_name)
    
    def _render_service_control_panel(self) -> None:
        """Render service control panel."""
        self.ui.render_service_control_panel()
    
    def _render_worker_pool_management(self) -> None:
        """Render worker pool management."""
        self.ui.render_worker_pool_management()
    
    def _render_service_monitoring(self) -> None:
        """Render service monitoring."""
        self.ui.render_system_monitoring()
    
    def _render_auto_management_panel(self) -> None:
        """Render auto-management panel."""
        self.ui.render_auto_management_panel()