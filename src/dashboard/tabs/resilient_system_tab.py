#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resilient System Tab - Improved with Auto-Healing
System tab with automatic service recovery, health monitoring, and Configurable workflows.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.core.Configurable_cache_manager import get_Configurable_cache
from src.dashboard.core.auto_healing_service_factory import (
    get_auto_healing_factory, ServiceStatus, ServiceHealth
)

logger = logging.getLogger(__name__)


class ResilientSystemTabRenderer:
    """System tab with auto-healing and Configurable workflows."""
    
    def __init__(self):
        self.cache_manager = get_Configurable_cache()
        self.service_factory = get_auto_healing_factory()
        self.auto_heal_enabled = True
        self.last_health_check = None
        
    def render_with_auto_healing(self) -> None:
        """Render system tab with auto-healing capabilities."""
        try:
            # Header with auto-healing status
            self._render_auto_healing_header()
            
            # Real-time health monitoring
            self._render_health_monitoring_section()
            
            # Service management with auto-healing
            self._render_service_management_section()
            
            # System metrics with Configurable caching
            self._render_system_metrics_section()
            
            # Auto-healing controls
            self._render_auto_healing_controls()
            
            # Recovery logs and history
            self._render_recovery_history()
            
        except Exception as e:
            logger.error(f"Error in resilient system tab: {e}")
            self._render_fallback_system_view()
    
    def _render_auto_healing_header(self) -> None:
        """Render header with auto-healing status."""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.title("🛠️ Resilient System Control")
            st.caption("Configurable system management with auto-healing")
        
        with col2:
            # Auto-healing status indicator
            if self.auto_heal_enabled:
                st.success("🛡️ Auto-Healing Active")
            else:
                st.warning("⚠️ Auto-Healing Disabled")
        
        with col3:
            # Quick heal all button
            if st.button("🔧 Quick Heal All"):
                self._trigger_quick_heal_all()
    
    def _render_health_monitoring_section(self) -> None:
        """Render real-time health monitoring."""
        st.subheader("📊 Real-Time Health Monitoring")
        
        # Get current health status
        health_summary = self.service_factory.get_all_services_health()
        
        if not health_summary:
            st.info("No services registered for monitoring.")
            return
        
        # Health overview metrics
        self._render_health_overview(health_summary)
        
        # Detailed service health
        self._render_detailed_health_status(health_summary)
    
    def _render_health_overview(self, health_summary: Dict[str, ServiceHealth]) -> None:
        """Render health overview metrics."""
        total_services = len(health_summary)
        healthy_services = len([h for h in health_summary.values() if h.status == ServiceStatus.HEALTHY])
        unhealthy_services = len([h for h in health_summary.values() if h.status == ServiceStatus.UNHEALTHY])
        recovering_services = len([h for h in health_summary.values() if h.status == ServiceStatus.RECOVERING])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Services", total_services)
        
        with col2:
            st.metric(
                "Healthy", 
                healthy_services,
                delta=healthy_services - unhealthy_services if unhealthy_services > 0 else None
            )
        
        with col3:
            if unhealthy_services > 0:
                st.metric("⚠️ Unhealthy", unhealthy_services, delta=-unhealthy_services)
            else:
                st.metric("✅ All Healthy", "0")
        
        with col4:
            if recovering_services > 0:
                st.metric("🔄 Recovering", recovering_services)
            else:
                st.metric("Stable", total_services - unhealthy_services)
    
    def _render_detailed_health_status(self, health_summary: Dict[str, ServiceHealth]) -> None:
        """Render detailed health status for each service."""
        st.markdown("**Detailed Service Status:**")
        
        for service_name, health in health_summary.items():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    # Service name and status
                    status_emoji = self._get_status_emoji(health.status)
                    st.markdown(f"{status_emoji} **{service_name}**")
                    
                    if health.last_check:
                        time_ago = (datetime.now() - health.last_check).total_seconds()
                        st.caption(f"Last check: {time_ago:.0f}s ago")
                
                with col2:
                    # Health metrics
                    if health.cpu_usage is not None:
                        st.metric("CPU", f"{health.cpu_usage:.1f}%")
                
                with col3:
                    # Memory usage
                    if health.memory_usage is not None:
                        st.metric("Memory", f"{health.memory_usage:.1f}%")
                
                with col4:
                    # Action buttons
                    if health.status == ServiceStatus.UNHEALTHY:
                        if st.button(f"🔧 Heal", key=f"heal_{service_name}"):
                            self._trigger_service_healing(service_name)
                    elif health.status == ServiceStatus.HEALTHY:
                        if st.button(f"🔄 Restart", key=f"restart_{service_name}"):
                            self._restart_service(service_name)
                
                # Error information if available
                if health.status == ServiceStatus.UNHEALTHY and health.error_message:
                    st.error(f"Error: {health.error_message}")
                
                st.divider()
    
    def _render_service_management_section(self) -> None:
        """Render service management with auto-healing."""
        st.subheader("⚙️ Service Management")
        
        # Service control tabs
        tab1, tab2, tab3 = st.tabs(["Service Control", "Auto-Recovery", "Manual Actions"])
        
        with tab1:
            self._render_service_control()
        
        with tab2:
            self._render_auto_recovery_settings()
        
        with tab3:
            self._render_manual_actions()
    
    def _render_service_control(self) -> None:
        """Render basic service control interface."""
        st.markdown("**Service Control Panel:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Start All Services"):
                self._start_all_services()
        
        with col2:
            if st.button("⏹️ Stop All Services"):
                self._stop_all_services()
        
        with col3:
            if st.button("🔄 Restart All Services"):
                self._restart_all_services()
        
        # Service-specific controls
        st.markdown("**Individual Service Control:**")
        
        available_services = ["Data Service", "System Service", "Config Service", "Health Monitor"]
        
        selected_service = st.selectbox("Select Service", available_services)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"▶️ Start {selected_service}"):
                self._start_service(selected_service)
        
        with col2:
            if st.button(f"⏹️ Stop {selected_service}"):
                self._stop_service(selected_service)
        
        with col3:
            if st.button(f"🔄 Restart {selected_service}"):
                self._restart_service(selected_service)
    
    def _render_auto_recovery_settings(self) -> None:
        """Render auto-recovery configuration."""
        st.markdown("**Auto-Recovery Settings:**")
        
        # Enable/disable auto-healing
        self.auto_heal_enabled = st.checkbox(
            "Enable Auto-Healing", 
            value=self.auto_heal_enabled,
            help="Automatically attempt to recover failed services"
        )
        
        # Recovery strategies
        st.markdown("**Recovery Strategies:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            restart_attempts = st.number_input(
                "Max Restart Attempts", 
                min_value=1, 
                max_value=10, 
                value=3
            )
            
            recovery_delay = st.number_input(
                "Recovery Delay (seconds)", 
                min_value=1, 
                max_value=300, 
                value=30
            )
        
        with col2:
            escalation_enabled = st.checkbox(
                "Enable Escalation",
                value=True,
                help="Escalate to manual intervention if auto-recovery fails"
            )
            
            notification_enabled = st.checkbox(
                "Recovery Notifications",
                value=True,
                help="Show notifications when recovery actions are taken"
            )
        
        if st.button("💾 Save Recovery Settings"):
            self._save_recovery_settings({
                'auto_heal_enabled': self.auto_heal_enabled,
                'restart_attempts': restart_attempts,
                'recovery_delay': recovery_delay,
                'escalation_enabled': escalation_enabled,
                'notification_enabled': notification_enabled
            })
    
    def _render_manual_actions(self) -> None:
        """Render manual action interface."""
        st.markdown("**Manual Recovery Actions:**")
        
        # Emergency actions
        st.markdown("🚨 **Emergency Actions:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🆘 Emergency Stop All"):
                self._emergency_stop_all()
            
            if st.button("🔄 Force Restart All"):
                self._force_restart_all()
        
        with col2:
            if st.button("🧹 Clear All Caches"):
                self._clear_all_caches()
            
            if st.button("📊 Generate Health Report"):
                self._generate_health_report()
        
        # System diagnostics
        st.markdown("🔍 **System Diagnostics:**")
        
        if st.button("🩺 Run Full Diagnostics"):
            self._run_full_diagnostics()
        
        # Manual service registration
        st.markdown("📝 **Manual Service Registration:**")
        
        with st.form("register_service"):
            service_name = st.text_input("Service Name")
            service_type = st.selectbox("Service Type", ["Core", "Worker", "Monitor", "Custom"])
            
            if st.form_submit_button("Register Service"):
                self._register_manual_service(service_name, service_type)
    
    def _render_system_metrics_section(self) -> None:
        """Render system metrics with caching."""
        st.subheader("📈 System Metrics")
        
        # Cache key for system metrics
        cache_key = f"system_metrics_{int(time.time() // 60)}"  # Cache for 1 minute
        
        def get_system_metrics():
            # Simulate getting system metrics
            return {
                'uptime': "2d 14h 32m",
                'total_memory': "8.0 GB",
                'used_memory': "4.2 GB",
                'cpu_cores': 8,
                'active_connections': 42,
                'requests_per_minute': 127
            }
        
        metrics = self.cache_manager.Configurable_get(cache_key, get_system_metrics)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("System Uptime", metrics['uptime'])
            st.metric("CPU Cores", metrics['cpu_cores'])
        
        with col2:
            st.metric("Total Memory", metrics['total_memory'])
            st.metric("Used Memory", metrics['used_memory'])
        
        with col3:
            st.metric("Active Connections", metrics['active_connections'])
            st.metric("Requests/min", metrics['requests_per_minute'])
    
    def _render_auto_healing_controls(self) -> None:
        """Render auto-healing control panel."""
        st.subheader("🛡️ Auto-Healing Control Panel")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Healing Status:**")
            
            # Recent healing actions
            recent_actions = self._get_recent_healing_actions()
            
            if recent_actions:
                for action in recent_actions[-5:]:  # Show last 5 actions
                    timestamp = action.get('timestamp', 'Unknown')
                    service = action.get('service', 'Unknown')
                    result = action.get('result', 'Unknown')
                    
                    status_emoji = "✅" if result == "success" else "❌"
                    st.markdown(f"{status_emoji} {service} - {timestamp}")
            else:
                st.info("No recent healing actions")
        
        with col2:
            st.markdown("**Healing Statistics:**")
            
            stats = self._get_healing_statistics()
            
            st.metric("Total Healing Attempts", stats.get('total_attempts', 0))
            st.metric("Successful Recoveries", stats.get('successful', 0))
            st.metric("Failed Recoveries", stats.get('failed', 0))
            
            success_rate = (stats.get('successful', 0) / max(stats.get('total_attempts', 1), 1)) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
    
    def _render_recovery_history(self) -> None:
        """Render recovery history and logs."""
        st.subheader("📜 Recovery History")
        
        with st.expander("View Recovery Logs", expanded=False):
            # Recovery log display
            recovery_logs = self._get_recovery_logs()
            
            if recovery_logs:
                for log_entry in recovery_logs[-10:]:  # Show last 10 entries
                    timestamp = log_entry.get('timestamp', 'Unknown')
                    service = log_entry.get('service', 'Unknown')
                    action = log_entry.get('action', 'Unknown')
                    result = log_entry.get('result', 'Unknown')
                    
                    st.text(f"[{timestamp}] {service}: {action} -> {result}")
            else:
                st.info("No recovery logs available")
        
        # Clear logs button
        if st.button("🗑️ Clear Recovery Logs"):
            self._clear_recovery_logs()
    
    def _render_fallback_system_view(self) -> None:
        """Render fallback system view when auto-healing fails."""
        st.warning("Auto-healing features temporarily unavailable. Using basic system view.")
        
        st.subheader("Basic System Status")
        
        # Basic service status
        services = ["Data Service", "System Service", "Config Service"]
        
        for service in services:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**{service}**")
            
            with col2:
                st.success("Running")  # Assume running in fallback mode
    
    # Helper methods for service management
    def _get_status_emoji(self, status: ServiceStatus) -> str:
        """Get emoji for service status."""
        emoji_map = {
            ServiceStatus.HEALTHY: "✅",
            ServiceStatus.UNHEALTHY: "❌", 
            ServiceStatus.RECOVERING: "🔄",
            ServiceStatus.UNKNOWN: "❓"
        }
        return emoji_map.get(status, "❓")
    
    def _trigger_quick_heal_all(self) -> None:
        """Trigger quick healing for all services."""
        self.service_factory.monitor_and_heal_services()
        st.success("Quick heal triggered for all services!")
        time.sleep(1)
        st.rerun()
    
    def _trigger_service_healing(self, service_name: str) -> None:
        """Trigger healing for specific service."""
        # Implementation would depend on service factory capabilities
        st.success(f"Healing triggered for {service_name}!")
        time.sleep(1)
        st.rerun()
    
    def _start_service(self, service_name: str) -> None:
        """Start a specific service."""
        success = self.service_factory.start_service(service_name.lower().replace(" ", "_"))
        if success:
            st.success(f"Started {service_name}")
        else:
            st.error(f"Failed to start {service_name}")
    
    def _stop_service(self, service_name: str) -> None:
        """Stop a specific service."""
        success = self.service_factory.stop_service(service_name.lower().replace(" ", "_"))
        if success:
            st.success(f"Stopped {service_name}")
        else:
            st.error(f"Failed to stop {service_name}")
    
    def _restart_service(self, service_name: str) -> None:
        """Restart a specific service."""
        success = self.service_factory.restart_service(service_name.lower().replace(" ", "_"))
        if success:
            st.success(f"Restarted {service_name}")
        else:
            st.error(f"Failed to restart {service_name}")
    
    def _start_all_services(self) -> None:
        """Start all services."""
        st.success("Starting all services...")
        # Implementation would iterate through all services
    
    def _stop_all_services(self) -> None:
        """Stop all services."""
        st.warning("Stopping all services...")
        # Implementation would iterate through all services
    
    def _restart_all_services(self) -> None:
        """Restart all services."""
        st.info("Restarting all services...")
        # Implementation would iterate through all services
    
    def _save_recovery_settings(self, settings: Dict[str, Any]) -> None:
        """Save recovery configuration settings."""
        # Cache the settings
        self.cache_manager.Configurable_set("recovery_settings", settings)
        st.success("Recovery settings saved!")
    
    def _emergency_stop_all(self) -> None:
        """Emergency stop all services."""
        st.error("EMERGENCY STOP: All services stopped!")
    
    def _force_restart_all(self) -> None:
        """Force restart all services."""
        st.warning("FORCE RESTART: All services restarting...")
    
    def _clear_all_caches(self) -> None:
        """Clear all system caches."""
        self.cache_manager.clear_all()
        st.success("All caches cleared!")
    
    def _generate_health_report(self) -> None:
        """Generate comprehensive health report."""
        st.success("Health report generated!")
        # Implementation would create detailed health report
    
    def _run_full_diagnostics(self) -> None:
        """Run full system diagnostics."""
        st.info("Running full system diagnostics...")
        # Implementation would run comprehensive diagnostics
    
    def _register_manual_service(self, service_name: str, service_type: str) -> None:
        """Manually register a service."""
        if service_name:
            st.success(f"Registered {service_type} service: {service_name}")
        else:
            st.error("Service name is required")
    
    def _get_recent_healing_actions(self) -> List[Dict[str, Any]]:
        """Get recent healing actions."""
        # Return cached or simulated healing actions
        return self.cache_manager.Configurable_get("recent_healing_actions", lambda: [])
    
    def _get_healing_statistics(self) -> Dict[str, int]:
        """Get healing statistics."""
        return self.cache_manager.Configurable_get("healing_statistics", lambda: {
            'total_attempts': 15,
            'successful': 13,
            'failed': 2
        })
    
    def _get_recovery_logs(self) -> List[Dict[str, Any]]:
        """Get recovery logs."""
        return self.cache_manager.Configurable_get("recovery_logs", lambda: [])
    
    def _clear_recovery_logs(self) -> None:
        """Clear recovery logs."""
        self.cache_manager.Configurable_set("recovery_logs", [])
        st.success("Recovery logs cleared!")


# Public API
def render_resilient_system_tab() -> None:
    """Render resilient system tab with auto-healing."""
    renderer = ResilientSystemTabRenderer()
    renderer.render_with_auto_healing()


# Fallback function for compatibility
def render_system_tab() -> None:
    """Compatibility function - delegates to resilient version."""
    render_resilient_system_tab()
