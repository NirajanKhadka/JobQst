#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Controller
Main orchestration controller for the modularized dashboard with Configurable features.
"""

import logging
import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
import time

from .smart_cache_manager import (
    ConfigurableCacheManager, get_Configurable_cache
)
from .auto_healing_service_factory import (
    AutoHealingServiceFactory, get_auto_healing_factory
)

# Import services
try:
    from ..services.data_service import get_data_service
    from ..services.system_service import get_system_service
    from ..services.config_service import get_config_service
    from ..services.orchestration_service import get_orchestration_service
    from ..services.health_monitor import get_health_monitor
    HAS_SERVICES = True
except ImportError:
    HAS_SERVICES = False

logger = logging.getLogger(__name__)


class WorkflowPattern:
    """Track user workflow patterns for optimization."""
    
    def __init__(self):
        self.action_sequence = []
        self.timestamps = []
        self.common_patterns = {}
        self.shortcuts = {}
    
    def track_action(self, action: str, context: Dict[str, Any]) -> None:
        """Track user action for pattern analysis."""
        self.action_sequence.append(action)
        self.timestamps.append(datetime.now())
        
        # Keep only recent actions (last 50)
        if len(self.action_sequence) > 50:
            self.action_sequence = self.action_sequence[-50:]
            self.timestamps = self.timestamps[-50:]
        
        # Analyze patterns
        self._analyze_patterns()
    
    def _analyze_patterns(self) -> None:
        """Analyze user action patterns."""
        if len(self.action_sequence) < 3:
            return
        
        # Look for sequences of 3 actions
        for i in range(len(self.action_sequence) - 2):
            pattern = tuple(self.action_sequence[i:i+3])
            self.common_patterns[pattern] = (
                self.common_patterns.get(pattern, 0) + 1
            )
    
    def get_next_likely_action(self, recent_actions: List[str]) -> Optional[str]:
        """Predict next likely action based on patterns."""
        if len(recent_actions) < 2:
            return None
        
        # Look for patterns starting with recent actions
        search_pattern = tuple(recent_actions[-2:])
        
        for pattern, count in self.common_patterns.items():
            if pattern[:2] == search_pattern and count > 2:
                return pattern[2]
        
        return None
    
    def suggest_shortcut(self, current_context: Dict) -> Optional[str]:
        """Suggest workflow shortcut based on context."""
        # Simple heuristic-based shortcuts
        if current_context.get('tab') == 'jobs' and current_context.get('filter_active'):
            return "bulk_actions"
        
        if current_context.get('tab') == 'system' and current_context.get('services_down'):
            return "auto_heal_all"
        
        return None


class DashboardController:
    """
    Main dashboard controller with Configurable caching.
    
    Features:
    - Service management with auto-healing
    - Configurable caching for performance
    - Graceful error handling
    """
    
    def __init__(self):
        self.cache_manager = get_Configurable_cache()
        self.service_factory = get_auto_healing_factory()
        self.services = {}
        self.initialized = False
        
        logger.info("DashboardController initialized")
    
    @classmethod
    def create_with_enhancements(cls) -> 'DashboardController':
        """Create controller with Configurable enhancements enabled."""
        controller = cls()
        controller._setup_Configurable_features()
        return controller
    
    def _setup_Configurable_features(self) -> None:
        """Set up Configurable caching and auto-healing features."""
        # Set up cache invalidation rules for dashboard
        self.cache_manager.add_invalidation_rule(
            "job_status_change",
            ["job_table", "job_metrics", "dashboard_overview"]
        )
        
        self.cache_manager.add_invalidation_rule(
            "profile_change",
            ["job_table", "profile_settings", "user_preferences"]
        )
        
        logger.info("Configurable features configured")
    
    def initialize_dashboard(self) -> None:
        """Initialize dashboard with all services."""
        if self.initialized:
            return
        
        try:
            # Initialize services
            self._initialize_services()
            
            # Set up session state if not exists
            self._initialize_session_state()
            
            # Set up Configurable features
            self._setup_Configurable_caching_loaders()
            
            self.initialized = True
            logger.info("Dashboard initialization complete")
            
        except Exception as e:
            logger.error(f"Dashboard initialization failed: {e}")
            st.error(f"❌ Dashboard initialization failed: {e}")
    
    def _initialize_services(self) -> None:
        """Initialize all dashboard services."""
        if HAS_SERVICES:
            try:
                self.services = {
                    'data': get_data_service(),
                    'system': get_system_service(),
                    'config': get_config_service(),
                    'orchestration': get_orchestration_service(),
                    'health': get_health_monitor()
                }
                # Register services with health monitoring
                self._register_services_for_monitoring()
                logger.info("Dashboard services initialized")
            except Exception as e:
                logger.warning(f"Some services unavailable: {e}")
                self.services = {}
                # Register basic mock services for health display
                self._register_mock_services_for_monitoring()
        else:
            logger.warning("Dashboard services not available")
            self.services = {}
            # Register basic mock services for health display
            self._register_mock_services_for_monitoring()
    
    def _register_services_for_monitoring(self) -> None:
        """Register real services with the health monitor."""
        try:
            for service_name, service in self.services.items():
                if hasattr(service, 'health_check'):
                    self.service_factory.health_monitor.register_service(
                        service_name, service
                    )
                    logger.info(f"Registered {service_name} for health monitoring")
        except Exception as e:
            logger.warning(f"Could not register services for monitoring: {e}")
    
    def _register_mock_services_for_monitoring(self) -> None:
        """Register mock services to show health monitoring functionality."""
        class MockDatabaseService:
            def health_check(self):
                return True
            def get_status(self):
                return {'status': 'running', 'connections': 5}
            def start(self):
                return True
            def stop(self):
                return True
            def restart(self):
                return True
        
        class MockCacheService:
            def health_check(self):
                return True
            def get_status(self):
                return {'status': 'running', 'hit_rate': '85%'}
            def start(self):
                return True
            def stop(self):
                return True
            def restart(self):
                return True
        
        # Register mock services
        mock_services = {
            'database': MockDatabaseService(),
            'cache': MockCacheService(),
        }
        
        for name, service in mock_services.items():
            self.service_factory.health_monitor.register_service(name, service)
            logger.info(f"Registered mock {name} service for health monitoring")
    
    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state with Configurable defaults."""
        # Core session state
        if "auto_refresh" not in st.session_state:
            st.session_state["auto_refresh"] = True
        
        if "refresh_interval" not in st.session_state:
            st.session_state["refresh_interval"] = 30
        
        if "selected_profile" not in st.session_state:
            st.session_state["selected_profile"] = "Nirajan"
        
        # Workflow tracking
        if "workflow_history" not in st.session_state:
            st.session_state["workflow_history"] = []
        
        # Cache settings
        if "cache_enabled" not in st.session_state:
            st.session_state["cache_enabled"] = True
        
        logger.debug("Session state initialized")
    
    def _setup_Configurable_caching_loaders(self) -> None:
        """Set up Configurable caching data loaders."""
        # Define data loaders for common dashboard data
        cache_loaders = {
            'job_data': lambda: self._load_job_data_safe(),
            'system_metrics': lambda: self._load_system_metrics_safe(),
            'service_status': lambda: self._load_service_status_safe(),
            'profile_settings': lambda: self._load_profile_settings_safe()
        }
        
        # Start preloading frequent data
        threading.Thread(
            target=self.cache_manager.preload_frequent_data,
            args=(cache_loaders,),
            daemon=True
        ).start()
    
    def _load_job_data_safe(self) -> Any:
        """Safely load job data with fallback."""
        try:
            if 'data' in self.services:
                profile = st.session_state.get("selected_profile", "Nirajan")
                return self.services['data'].load_job_data(profile)
            return []
        except Exception as e:
            logger.warning(f"Failed to load job data: {e}")
            return []
    
    def _load_system_metrics_safe(self) -> Dict[str, Any]:
        """Safely load system metrics with fallback."""
        try:
            if 'system' in self.services:
                return self.services['system'].get_metrics()
            return {'status': 'unavailable'}
        except Exception as e:
            logger.warning(f"Failed to load system metrics: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _load_service_status_safe(self) -> Dict[str, Any]:
        """Safely load service status with fallback."""
        try:
            if 'health' in self.services:
                return self.services['health'].get_all_health_status()
            return {}
        except Exception as e:
            logger.warning(f"Failed to load service status: {e}")
            return {}
    
    def _load_profile_settings_safe(self) -> Dict[str, Any]:
        """Safely load profile settings with fallback."""
        try:
            if 'config' in self.services:
                profile = st.session_state.get("selected_profile", "Nirajan")
                return self.services['config'].get_profile_settings(profile)
            return {}
        except Exception as e:
            logger.warning(f"Failed to load profile settings: {e}")
            return {}
    
    def get_cached_data(self, key: str, loader_func: callable, 
                       ttl: Optional[int] = None) -> Any:
        """Get data with Configurable caching."""
        if not st.session_state.get("cache_enabled", True):
            return loader_func()
        
        return self.cache_manager.Configurable_get(key, loader_func, ttl)
    
    def invalidate_cache(self, trigger: str) -> None:
        """Invalidate cache based on trigger."""
        self.cache_manager.invalidate_Configurable(trigger)
        logger.debug(f"Cache invalidated for trigger: {trigger}")
    
    def track_user_action(self, action: str, context: Dict[str, Any]) -> None:
        """Track user action for optimization."""
        # Store in session state
        if "workflow_history" not in st.session_state:
            st.session_state["workflow_history"] = []
        
        st.session_state["workflow_history"].append({
            'action': action,
            'context': context,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only recent history
        if len(st.session_state["workflow_history"]) > 100:
            st.session_state["workflow_history"] = (
                st.session_state["workflow_history"][-50:]
            )
    
    def handle_profile_change(self, new_profile: str) -> None:
        """Handle profile change with Configurable updates."""
        old_profile = st.session_state.get("selected_profile", "")
        
        if old_profile != new_profile:
            # Update session state
            st.session_state["selected_profile"] = new_profile
            
            # Invalidate profile-specific cache
            self.invalidate_cache("profile_change")
            
            # Track workflow action
            self.track_user_action("profile_change", {
                'old_profile': old_profile,
                'new_profile': new_profile
            })
            
            logger.info(f"Profile changed: {old_profile} -> {new_profile}")
    
    def render_Configurable_dashboard(self) -> None:
        """Render the main dashboard with Configurable features."""
        try:
            # Initialize if needed
            if not self.initialized:
                self.initialize_dashboard()
            
            # Import and render main dashboard
            from ..unified_dashboard import main as render_main_dashboard
            render_main_dashboard()
            
        except Exception as e:
            logger.error(f"Error rendering dashboard: {e}")
            st.error(f"❌ Dashboard rendering error: {e}")
            st.info("💡 Try refreshing the page")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        return self.cache_manager.get_cache_stats()
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get service health status."""
        return self.service_factory.get_all_services_health()
    
    def shutdown(self) -> None:
        """Shutdown controller and cleanup resources."""
        logger.info("Shutting down DashboardController")
        
        try:
            # Stop auto-healing factory
            self.service_factory.shutdown()
            
            # Clear cache
            self.cache_manager.clear_cache()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("DashboardController shutdown complete")


# Global controller instance
_global_controller = None


def get_dashboard_controller() -> DashboardController:
    """Get global dashboard controller instance."""
    global _global_controller
    if _global_controller is None:
        _global_controller = DashboardController.create_with_enhancements()
    return _global_controller
