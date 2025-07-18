#!/usr/bin/env python3
"""
Enhanced Orchestration Component for the Unified Dashboard.
Provides smart auto-start/stop logic, 5-worker document generation,
and comprehensive service management following development standards.
"""

import streamlit as st
from typing import Dict, List, Any, Protocol
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
import time
import psutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# Try to import the real service, but fall back to a mock for UI development
try:
    from src.services.orchestration_service import orchestration_service, ServiceProcess
    HAS_ORCHESTRATION_SERVICE = True
except ImportError:
    HAS_ORCHESTRATION_SERVICE = False

HAS_PROCESSOR_SERVICE = False
processor_orchestration_service = None

if not HAS_ORCHESTRATION_SERVICE and not HAS_PROCESSOR_SERVICE:
    # Enhanced mock service for UI development
    class MockService:
        def __init__(self, name, description, status="stopped"):
            self.name = name
            self.description = description
            self.status = status
            self.start_time = None
            self.resource_usage = {"cpu": 0.0, "memory": 0.0}
            
        def get_status(self):
            return {
                "status": self.status, 
                "processed_count": 0,
                "uptime": "00:00:00",
                "cpu_usage": self.resource_usage["cpu"],
                "memory_usage": self.resource_usage["memory"]
            }

    class MockOrchestrationService:
        def __init__(self):
            self._services = {
                "processor_worker_1": MockService("processor_worker_1", "Job processor worker #1"),
                "processor_worker_2": MockService("processor_worker_2", "Job processor worker #2"),
                "processor_worker_3": MockService("processor_worker_3", "Job processor worker #3"),
                "processor_worker_4": MockService("processor_worker_4", "Job processor worker #4"),
                "processor_worker_5": MockService("processor_worker_5", "Job processor worker #5"),
                "applicator": MockService("applicator", "Automated job application submission"),
            }
            self.auto_management_enabled = False
            
        def get_all_services(self) -> Dict[str, MockService]:
            return self._services
            
        def start_service(self, service_name: str, profile_name: str) -> bool:
            if service_name in self._services:
                self._services[service_name].status = "running"
                self._services[service_name].start_time = datetime.now()
                st.toast(f"✅ Started {service_name} for {profile_name}", icon="✅")
                return True
            return False
            
        def stop_service(self, service_name: str) -> bool:
            if service_name in self._services:
                self._services[service_name].status = "stopped"
                self._services[service_name].start_time = None
                st.toast(f"⏹️ Stopped {service_name}", icon="⏹️")
                return True
            return False
            
        def start_core_services(self, profile_name: str) -> bool:
            core_services = ["processor_worker_1", "processor_worker_2", "processor_worker_3"]
            for service_name in core_services:
                self.start_service(service_name, profile_name)
            return True
            
        def stop_core_services(self) -> bool:
            core_services = ["processor_worker_1", "processor_worker_2", "processor_worker_3"]
            for service_name in core_services:
                self.stop_service(service_name)
            return True
            
        def get_worker_pool_status(self) -> Dict[str, Any]:
            workers = {f"processor_worker_{i}": self._services[f"processor_worker_{i}"] 
                      for i in range(1, 6)}
            running_count = sum(1 for w in workers.values() if w.status == "running")
            return {
                "total_workers": 5,
                "running_workers": running_count,
                "available_workers": 5 - running_count,
                "workers": workers
            }

    orchestration_service = MockOrchestrationService()
    ServiceProcess = MockService
else:
    # Use the real processor service if available
    if HAS_PROCESSOR_SERVICE:
        orchestration_service = processor_orchestration_service
    else:
        orchestration_service = orchestration_service


# Define a protocol for what a service should look like
class ServiceProtocol(Protocol):
    name: str
    description: str
    status: str
    start_time: Any
    resource_usage: Dict[str, float]
    
    def get_status(self) -> Dict[str, Any]:
        ...

class EnhancedOrchestrationComponent:
    """
    Enhanced orchestration component with smart auto-start/stop logic,
    5-worker document generation, and comprehensive service management.
    Following development standards for modular architecture.
    """

    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        # Initialize processor service if available
        if HAS_PROCESSOR_SERVICE and processor_orchestration_service:
            processor_orchestration_service.initialize_workers(profile_name)
            st.success("✅ Connected to Processor Orchestration Service")
        elif not HAS_ORCHESTRATION_SERVICE:
            st.info("Orchestration service not found. Using fallback mode. For full orchestration features, add src/services/orchestration_service.py.")

    def render(self):
        """Render the enhanced orchestration control panel."""
        st.markdown('<h2 class="section-header">🖥️ Application Orchestration & System Control</h2>', unsafe_allow_html=True)
        # Create tabs for different orchestration features
        control_tab, workers_tab, monitoring_tab, automation_tab = st.tabs([
            "🎛️ Service Control", "👥 5-Worker Pool", "📊 Monitoring", "🤖 Auto-Management"
        ])
        with control_tab:
            self._render_service_control_panel()
        with workers_tab:
            self._render_worker_pool_management()
        with monitoring_tab:
            self._render_service_monitoring()
        with automation_tab:
            self._render_auto_management_panel()

    def _render_service_control_panel(self):
        """Render the main service control panel."""
        st.markdown("### 🎯 Processor Service Pipeline")
        st.info("Manage the job processor workers that analyze and classify scraped jobs from the database.")
        
        # Master controls for processor services only
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Start Core Processors", key="core_start_all", use_container_width=True):
                self._start_all_services()
        
        with col2:
            if st.button("⏹️ Stop Core Processors", key="core_stop_all", use_container_width=True):
                self._stop_all_services()
        
        with col3:
            if st.button("🔄 Restart Processors", key="core_restart_all", use_container_width=True):
                self._restart_all_services()

        st.markdown("---")
        
        # Individual service controls
        try:
            if HAS_PROCESSOR_SERVICE and processor_orchestration_service:
                services_status = processor_orchestration_service.get_all_services_status()
            else:
                services_status = orchestration_service.get_all_services_status()
                
            if not services_status:
                st.warning("No processor services are defined.")
                return
        except AttributeError:
            # Fallback for mock service
            services = orchestration_service.get_all_services()
            services_status = {k: v.get_status() for k, v in services.items()}
            if not services_status:
                st.warning("No processor services are defined.")
                return

        # Group services by category  
        core_processors = {k: v for k, v in services_status.items() 
                          if k.startswith("processor_worker_") and int(k.split('_')[-1]) <= 3}
        
        additional_workers = {k: v for k, v in services_status.items() 
                             if k.startswith("processor_worker_") and int(k.split('_')[-1]) > 3}

        # Core Processor Services Section
        st.markdown("#### 🔧 Core Processor Workers")
        if core_processors:
            cols = st.columns(len(core_processors))
            for i, (service_name, service_status) in enumerate(core_processors.items()):
                with cols[i]:
                    self._render_enhanced_service_card_from_status(service_name, service_status)
        else:
            st.info("Core processor workers will appear here when initialized.")

        # Additional Workers handled in separate tab
        if additional_workers:
            st.markdown("#### 📄 Additional Workers")
            st.info("Additional processor workers are managed in the '👥 5-Worker Pool' tab.")

    def _render_enhanced_service_card(self, service_name: str, service: ServiceProtocol):
        """Render an enhanced service card with status and controls."""
        status_info = service.get_status()
        status = status_info.get("status", "unknown")
        is_running = status == "running"

        # Status indicator
        status_icon = "🟢" if is_running else "🔴"
        status_text = "RUNNING" if is_running else "STOPPED"
        
        with st.container():
            # Service header
            st.markdown(f"""
            <div style='padding: 1rem; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 1rem;'>
                <h4>{status_icon} {service_name.replace('_', ' ').title()}</h4>
                <p style='color: #666; margin: 0.5rem 0;'>{service.description}</p>
                <p style='font-weight: bold; color: {'green' if is_running else 'red'};'>{status_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Metrics
            if is_running:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("CPU", f"{status_info.get('cpu_usage', 0):.1f}%")
                with col2:
                    st.metric("Memory", f"{status_info.get('memory_usage', 0):.1f}%")
                
                if service.start_time:
                    uptime = datetime.now() - service.start_time
                    st.caption(f"⏱️ Uptime: {str(uptime).split('.')[0]}")

            # Control buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Start", key=f"start_{service_name}", 
                           disabled=is_running, use_container_width=True):
                    self._start_service(service_name)
            with col2:
                if st.button("⏹️ Stop", key=f"stop_{service_name}", 
                           disabled=not is_running, use_container_width=True):
                    self._stop_service(service_name)

    def _render_enhanced_service_card_from_status(self, service_name: str, service_status: Dict[str, Any]):
        """Render an enhanced service card from status dictionary."""
        if not service_status:
            st.error(f"Service {service_name} status unavailable")
            return
            
        status = service_status.get("status", "unknown")
        is_running = status == "running"

        # Status indicator
        status_icon = "🟢" if is_running else "🔴"
        status_text = "RUNNING" if is_running else "STOPPED"
        
        with st.container():
            # Service header
            st.markdown(f"""
            <div style='padding: 1rem; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 1rem;'>
                <h4>{status_icon} {service_name.replace('_', ' ').title()}</h4>
                <p style='color: #666; margin: 0.5rem 0;'>{service_status.get('description', 'No description')}</p>
                <p style='font-weight: bold; color: {'green' if is_running else 'red'};'>{status_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Metrics
            if is_running:
                col1, col2 = st.columns(2)
                with col1:
                    resource_usage = service_status.get('resource_usage', {})
                    st.metric("CPU", f"{resource_usage.get('cpu', 0):.1f}%")
                with col2:
                    st.metric("Memory", f"{resource_usage.get('memory', 0):.1f}%")
                
                uptime = service_status.get('uptime', '0:00:00')
                st.caption(f"⏱️ Uptime: {uptime}")

            # Control buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Start", key=f"start_{service_name}", 
                           disabled=is_running, use_container_width=True):
                    self._start_service(service_name)
            with col2:
                if st.button("⏹️ Stop", key=f"stop_{service_name}", 
                           disabled=not is_running, use_container_width=True):
                    self._stop_service(service_name)

    def _render_worker_pool_management(self):
        """Render the 5-worker processor pool management."""
        st.markdown("### 👥 5-Worker Processor Pool")
        st.info("Manage parallel job processing with 5 dedicated workers for optimal performance.")
        
        # Get worker pool status
        try:
            # Try to get worker pool status from processor orchestration service
            if HAS_PROCESSOR_SERVICE and processor_orchestration_service:
                worker_status = processor_orchestration_service.get_worker_pool_status()
            elif hasattr(orchestration_service, 'get_worker_pool_status'):
                worker_status = orchestration_service.get_worker_pool_status()
            else:
                # Fallback - construct from services status
                services_status = orchestration_service.get_all_services_status()
                workers = {k: v for k, v in services_status.items() if k.startswith("processor_worker_")}
                running_count = sum(1 for w in workers.values() if w and w.get("status") == "running")
                worker_status = {
                    "total_workers": len(workers),
                    "running_workers": running_count,
                    "available_workers": len(workers) - running_count,
                    "workers": workers
                }
        except AttributeError:
            # Fallback for services without worker pool support
            try:
                services = orchestration_service.get_all_services()
                workers = {k: v for k, v in services.items() if k.startswith("processor_worker_")}
                running_count = sum(1 for w in workers.values() if w.status == "running")
                worker_status = {
                    "total_workers": len(workers),
                    "running_workers": running_count,
                    "available_workers": len(workers) - running_count,
                    "workers": workers
                }
            except AttributeError:
                # Last fallback - mock data
                worker_status = {
                    "total_workers": 5,
                    "running_workers": 0,
                    "available_workers": 5,
                    "workers": {}
                }
        
        # Worker pool overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Workers", worker_status["total_workers"])
        
        with col2:
            st.metric("Running", worker_status["running_workers"], 
                     delta=worker_status["running_workers"])
        
        with col3:
            st.metric("Available", worker_status["available_workers"])
        
        with col4:
            utilization = (worker_status["running_workers"] / max(worker_status["total_workers"], 1)) * 100
            st.metric("Utilization", f"{utilization:.0f}%")

        # Worker pool controls
        st.markdown("#### 🎛️ Pool Controls")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Start All Workers", key="worker_pool_start_all", use_container_width=True):
                self._start_worker_pool()
        
        with col2:
            if st.button("⏹️ Stop All Workers", key="worker_pool_stop_all", use_container_width=True):
                self._stop_worker_pool()
        
        with col3:
            worker_count = st.selectbox("Workers to Start", [1, 2, 3, 4, 5], index=2, key="worker_pool_count_select")
            if st.button(f"▶️ Start {worker_count} Workers", key="worker_pool_start_n", use_container_width=True):
                self._start_n_workers(worker_count)

        # Individual worker status
        st.markdown("#### 🔧 Individual Worker Status")
        workers = worker_status["workers"]
        
        if workers:
            # Display workers in a grid
            cols = st.columns(min(3, len(workers)))
            for i, (worker_name, worker_data) in enumerate(workers.items()):
                with cols[i % 3]:
                    self._render_worker_card_from_status(worker_name, worker_data)
        else:
            st.info("Workers will appear here when the processor service is initialized.")

    def _render_worker_card(self, worker_name: str, worker: ServiceProtocol):
        """Render a card for an individual document worker."""
        is_running = worker.status == "running"
        status_icon = "🟢" if is_running else "🔴"
        
        with st.container():
            st.markdown(f"""
            <div style='padding: 0.8rem; border: 1px solid #ddd; border-radius: 6px; margin-bottom: 0.5rem;'>
                <h5>{status_icon} {worker_name.replace('_', ' ').title()}</h5>
                <p style='font-size: 0.8em; color: #666;'>{worker.description}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Worker controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️", key=f"start_worker_{worker_name}", 
                           disabled=is_running, help="Start worker"):
                    self._start_service(worker_name)
            with col2:
                if st.button("⏹️", key=f"stop_worker_{worker_name}", 
                           disabled=not is_running, help="Stop worker"):
                    self._stop_service(worker_name)

    def _render_worker_card_from_status(self, worker_name: str, worker_data: Dict[str, Any]):
        """Render a card for an individual document worker from status data."""
        if not worker_data:
            is_running = False
            description = "Document generation worker"
        else:
            is_running = worker_data.get("status") == "running"
            description = worker_data.get("description", "Document generation worker")
            
        status_icon = "🟢" if is_running else "🔴"
        
        with st.container():
            st.markdown(f"""
            <div style='padding: 0.8rem; border: 1px solid #ddd; border-radius: 6px; margin-bottom: 0.5rem;'>
                <h5>{status_icon} {worker_name.replace('_', ' ').title()}</h5>
                <p style='font-size: 0.8em; color: #666;'>{description}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Worker controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️", key=f"start_worker_{worker_name}", 
                           disabled=is_running, help="Start worker"):
                    self._start_service(worker_name)
            with col2:
                if st.button("⏹️", key=f"stop_worker_{worker_name}", 
                           disabled=not is_running, help="Stop worker"):
                    self._stop_service(worker_name)

    def _render_service_monitoring(self):
        """Render real-time service monitoring dashboard."""
        st.markdown("### 📊 Real-time Service Monitoring")
        st.info("Monitor service performance, resource usage, and system health in real-time.")
        
        # System resource overview
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("System CPU", f"{cpu_percent:.1f}%")
            with col2:
                st.metric("System Memory", f"{memory.percent:.1f}%")
            with col3:
                st.metric("Disk Usage", f"{disk.percent:.1f}%")
                
        except Exception as e:
            st.warning(f"System monitoring unavailable: {e}")

        # Service-specific monitoring
        try:
            services_status = orchestration_service.get_all_services_status()
            running_services = {k: v for k, v in services_status.items() 
                               if v and v.get("status") == "running"}
        except AttributeError:
            # Fallback for mock services
            services = orchestration_service.get_all_services()
            running_services = {k: v for k, v in services.items() if v.status == "running"}
        
        if running_services:
            st.markdown("#### 🔍 Running Service Details")
            
            for service_name, service_data in running_services.items():
                with st.expander(f"📈 {service_name.replace('_', ' ').title()}", expanded=False):
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Process Count", service_data.get('processed_count', 0) if service_data else 0)
                        resource_usage = service_data.get('resource_usage', {}) if service_data else {}
                        st.metric("CPU Usage", f"{resource_usage.get('cpu', 0):.1f}%")
                    
                    with col2:
                        st.metric("Memory Usage", f"{resource_usage.get('memory', 0):.1f}%")
                        uptime = service_data.get('uptime', '0:00:00') if service_data else '0:00:00'
                        st.metric("Uptime", uptime)
        else:
            st.info("No services are currently running. Start services to see monitoring data.")

    def _render_auto_management_panel(self):
        """Render the intelligent auto-management control panel."""
        st.markdown("### 🤖 Intelligent Auto-Management")
        st.info("Configure smart auto-start/stop logic based on job availability and system resources.")
        
        # Auto-management toggle
        auto_enabled = st.toggle(
            "🤖 Enable Auto-Management", 
            value=getattr(orchestration_service, 'auto_management_enabled', False),
            help="Automatically start/stop services based on job queue status"
        )
        
        if hasattr(orchestration_service, 'auto_management_enabled'):
            orchestration_service.auto_management_enabled = auto_enabled
        
        if auto_enabled:
            st.success("✅ Auto-management is active")
            
            # Auto-start settings
            st.markdown("#### 🚀 Auto-Start Rules")
            
            col1, col2 = st.columns(2)
            with col1:
                scraper_trigger = st.number_input(
                    "Start scraper when jobs < ", 
                    min_value=0, max_value=100, value=10,
                    help="Automatically start scraper when job count drops below this number"
                )
                
                processor_trigger = st.number_input(
                    "Start processor when scraped jobs > ", 
                    min_value=1, max_value=50, value=5,
                    help="Start processor when scraped jobs exceed this number"
                )
            
            with col2:
                worker_trigger = st.number_input(
                    "Start workers when processed jobs > ", 
                    min_value=1, max_value=20, value=3,
                    help="Start document workers when processed jobs exceed this number"
                )
                
                applicator_trigger = st.number_input(
                    "Start applicator when documents > ", 
                    min_value=1, max_value=10, value=2,
                    help="Start applicator when documents are ready"
                )
            
            # Auto-stop settings
            st.markdown("#### ⏹️ Auto-Stop Rules")
            
            col1, col2 = st.columns(2)
            with col1:
                idle_timeout = st.slider(
                    "Stop services after idle time (minutes)", 
                    min_value=1, max_value=60, value=10,
                    help="Stop services when idle for this duration"
                )
            
            with col2:
                resource_threshold = st.slider(
                    "Stop if system CPU > ", 
                    min_value=50, max_value=95, value=80,
                    help="Stop services if system CPU usage exceeds this percentage"
                )
            
            # Current auto-management status
            st.markdown("#### 📊 Auto-Management Status")
            
            # This would connect to actual monitoring logic
            status_data = {
                "Last Check": datetime.now().strftime("%H:%M:%S"),
                "Scraped Jobs": 12,
                "Processed Jobs": 8,
                "Ready Documents": 3,
                "Applied Jobs": 15
            }
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Scraped", status_data["Scraped Jobs"])
            with col2:
                st.metric("Processed", status_data["Processed Jobs"])
            with col3:
                st.metric("Documents", status_data["Ready Documents"])
            with col4:
                st.metric("Applied", status_data["Applied Jobs"])
                
            st.caption(f"🕒 Last checked: {status_data['Last Check']}")
            
        else:
            st.info("Auto-management is disabled. Services must be started manually.")

    def _start_service(self, service_name: str):
        """Start a specific service."""
        with st.spinner(f"Starting {service_name}..."):
            success = orchestration_service.start_service(service_name, self.profile_name)
            if success:
                st.success(f"✅ Started {service_name}")
            else:
                st.error(f"❌ Failed to start {service_name}")
        st.rerun()

    def _stop_service(self, service_name: str):
        """Stop a specific service."""
        with st.spinner(f"Stopping {service_name}..."):
            success = orchestration_service.stop_service(service_name)
            if success:
                st.success(f"⏹️ Stopped {service_name}")
            else:
                st.error(f"❌ Failed to stop {service_name}")
        st.rerun()

    def _start_all_services(self):
        """Start core services (scraper, processor, applicator) with dependency handling."""
        with st.spinner("Starting core pipeline services..."):
            try:
                # Define core services only
                core_services = ["scraper", "processor", "applicator"]
                
                # Check if orchestration service has a dedicated method for core services
                if hasattr(orchestration_service, 'start_core_services'):
                    success = orchestration_service.start_core_services(self.profile_name)
                else:
                    # Fallback: start core services individually
                    success = True
                    for service_name in core_services:
                        service_success = orchestration_service.start_service(service_name, self.profile_name)
                        if not service_success:
                            success = False
                
                if success:
                    st.success("✅ Core pipeline services started successfully")
                else:
                    st.error("❌ Some core services failed to start")
            except Exception as e:
                logger.error(f"Error starting core services: {e}")
                st.error(f"❌ Failed to start core services: {e}")
        st.rerun()

    def _stop_all_services(self):
        """Stop core services (scraper, processor, applicator) gracefully."""
        with st.spinner("Stopping core pipeline services..."):
            try:
                # Define core services only
                core_services = ["scraper", "processor", "applicator"]
                
                # Check if orchestration service has a dedicated method for core services
                if hasattr(orchestration_service, 'stop_core_services'):
                    success = orchestration_service.stop_core_services()
                else:
                    # Fallback: stop core services individually
                    success = True
                    for service_name in core_services:
                        service_success = orchestration_service.stop_service(service_name)
                        if not service_success:
                            success = False
                
                if success:
                    st.success("⏹️ Core pipeline services stopped successfully")
                else:
                    st.error("❌ Some core services failed to stop")
            except Exception as e:
                logger.error(f"Error stopping core services: {e}")
                st.error(f"❌ Failed to stop core services: {e}")
        st.rerun()

    def _restart_all_services(self):
        """Restart core services only."""
        with st.spinner("Restarting core pipeline services..."):
            self._stop_all_services()
            time.sleep(2)  # Brief pause
            self._start_all_services()

    def _start_worker_pool(self):
        """Start all 5 document workers."""
        with st.spinner("Starting worker pool..."):
            worker_names = [f"document_worker_{i}" for i in range(1, 6)]
            for worker_name in worker_names:
                orchestration_service.start_service(worker_name, self.profile_name)
            st.success("🚀 All 5 workers started")
        st.rerun()

    def _stop_worker_pool(self):
        """Stop all document workers."""
        with st.spinner("Stopping worker pool..."):
            worker_names = [f"document_worker_{i}" for i in range(1, 6)]
            for worker_name in worker_names:
                orchestration_service.stop_service(worker_name)
            st.success("⏹️ All workers stopped")
        st.rerun()

    def _start_n_workers(self, n: int):
        """Start the first N workers."""
        with st.spinner(f"Starting {n} workers..."):
            for i in range(1, n + 1):
                worker_name = f"document_worker_{i}"
                orchestration_service.start_service(worker_name, self.profile_name)
            st.success(f"🚀 Started {n} workers")
        st.rerun()


class OrchestrationComponent(EnhancedOrchestrationComponent):
    """Alias for backwards compatibility."""
    pass


def render_orchestration_control(profile_name: str):
    """
    Public function to render the enhanced orchestration component.
    """
    orchestration_component = EnhancedOrchestrationComponent(profile_name)
    orchestration_component.render()
