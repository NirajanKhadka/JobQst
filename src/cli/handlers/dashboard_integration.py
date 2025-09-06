"""
Dashboard Integration Handler for AutoJobAgent CLI.

Provides seamless integration between the improved scraping handler and dashboard:
- Real-time scraping status updates
- Performance metrics streaming
- Interactive scraping controls
- Unified architecture orchestration
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime
from pathlib import Path

from rich.console import Console

from .scraping_handler import ScrapingHandler, ScrapingOrchestrator
from src.core.session import SessionManager

console = Console()
logger = logging.getLogger(__name__)


class DashboardScrapingIntegration:
    """Integrates scraping operations with dashboard real-time updates."""
    
    def __init__(self, profile: Dict):
        self.profile = profile
        self.scraping_handler = ScrapingHandler(profile)
        self.session_manager = SessionManager()
        
        # Dashboard integration state
        self.active_operations = {}
        self.real_time_callbacks = []
        self.performance_metrics = {}
        
    def register_dashboard_callback(self, callback: Callable):
        """Register a dashboard callback for real-time updates."""
        self.real_time_callbacks.append(callback)
        
    def _notify_dashboard(self, event_type: str, data: Dict):
        """Send real-time updates to registered dashboard callbacks."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "profile": self.profile.get("profile_name", "default"),
            "data": data
        }
        
        for callback in self.real_time_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Dashboard callback error: {e}")
    
    def run_scraping_with_dashboard_updates(
        self,
        mode: str = "simple",
        jobs: int = 20,
        sites: Optional[List[str]] = None,
        **kwargs
    ) -> bool:
        """Run scraping with real-time dashboard updates."""
        
        operation_id = f"scrape_{int(time.time())}"
        
        # Notify dashboard of operation start
        self._notify_dashboard("scraping_started", {
            "operation_id": operation_id,
            "mode": mode,
            "target_jobs": jobs,
            "sites": sites or ["indeed", "linkedin"]
        })
        
        try:
            # Track operation
            self.active_operations[operation_id] = {
                "status": "running",
                "start_time": datetime.now(),
                "mode": mode,
                "target_jobs": jobs
            }
            
            # Run scraping with progress updates
            success = self._run_scraping_with_monitoring(
                operation_id, mode, jobs, sites, **kwargs
            )
            
            # Update final status
            self.active_operations[operation_id]["status"] = "completed" if success else "failed"
            self.active_operations[operation_id]["end_time"] = datetime.now()
            
            # Notify dashboard of completion
            self._notify_dashboard("scraping_completed", {
                "operation_id": operation_id,
                "success": success,
                "metrics": self.performance_metrics.get(operation_id, {})
            })
            
            return success
            
        except Exception as e:
            # Handle errors
            self.active_operations[operation_id]["status"] = "error"
            self.active_operations[operation_id]["error"] = str(e)
            
            self._notify_dashboard("scraping_error", {
                "operation_id": operation_id,
                "error": str(e)
            })
            
            raise
    
    def _run_scraping_with_monitoring(
        self, 
        operation_id: str, 
        mode: str, 
        jobs: int, 
        sites: Optional[List[str]], 
        **kwargs
    ) -> bool:
        """Run scraping with detailed monitoring and progress updates."""
        
        # Create a custom pipeline monitor
        pipeline_monitor = PipelineMonitor(operation_id, self._notify_dashboard)
        
        # Patch the scraping handler to include monitoring
        original_ultra_fast = self.scraping_handler._run_ultra_fast_pipeline
        
        def monitored_ultra_fast(mode: str, jobs: int) -> bool:
            return self._monitored_pipeline_execution(
                original_ultra_fast, pipeline_monitor, mode, jobs
            )
        
        # Temporarily replace the method
        self.scraping_handler._run_ultra_fast_pipeline = monitored_ultra_fast
        
        try:
            # Run the scraping operation
            if mode == "simple":
                result = self.scraping_handler._run_simple_scraping(
                    sites or ["indeed", "linkedin"], [], 14, 3, jobs
                )
            elif mode == "multi_worker":
                result = self.scraping_handler._run_multi_worker_scraping(
                    sites or ["indeed", "linkedin"], [], 14, 3, jobs
                )
            else:
                result = self.scraping_handler.run_scraping(
                    sites=sites, mode=mode, jobs=jobs, **kwargs
                )
            
            return result
            
        finally:
            # Restore original method
            self.scraping_handler._run_ultra_fast_pipeline = original_ultra_fast
    
    def _monitored_pipeline_execution(
        self, 
        original_method: Callable, 
        monitor: 'PipelineMonitor', 
        mode: str, 
        jobs: int
    ) -> bool:
        """Execute pipeline with monitoring hooks."""
        
        monitor.notify_stage("pipeline_started", {"mode": mode, "target_jobs": jobs})
        
        start_time = time.time()
        
        try:
            # Execute original method
            result = original_method(mode, jobs)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Capture performance metrics
            self.performance_metrics[monitor.operation_id] = {
                "duration": duration,
                "jobs_per_second": jobs / duration if duration > 0 else 0,
                "mode": mode,
                "success": result
            }
            
            monitor.notify_stage("pipeline_completed", {
                "success": result,
                "duration": duration,
                "jobs_per_second": jobs / duration if duration > 0 else 0
            })
            
            return result
            
        except Exception as e:
            monitor.notify_stage("pipeline_error", {"error": str(e)})
            raise
    
    def get_active_operations(self) -> Dict:
        """Get currently active scraping operations for dashboard display."""
        return self.active_operations.copy()
    
    def get_performance_summary(self) -> Dict:
        """Get performance metrics summary for dashboard analytics."""
        if not self.performance_metrics:
            return {"total_operations": 0, "average_performance": 0}
        
        total_ops = len(self.performance_metrics)
        avg_performance = sum(
            metrics.get("jobs_per_second", 0) 
            for metrics in self.performance_metrics.values()
        ) / total_ops
        
        return {
            "total_operations": total_ops,
            "average_performance": avg_performance,
            "recent_metrics": list(self.performance_metrics.values())[-5:]
        }


class PipelineMonitor:
    """Monitors pipeline execution stages for dashboard updates."""
    
    def __init__(self, operation_id: str, notify_callback: Callable):
        self.operation_id = operation_id
        self.notify_callback = notify_callback
        self.stages = []
    
    def notify_stage(self, stage: str, data: Dict):
        """Notify dashboard of pipeline stage progress."""
        stage_info = {
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
            "operation_id": self.operation_id,
            **data
        }
        
        self.stages.append(stage_info)
        
        self.notify_callback("pipeline_progress", stage_info)


class UnifiedScrapingOrchestrator(ScrapingOrchestrator):
    """Enhanced scraping orchestrator with dashboard integration."""
    
    def __init__(self, profile: Dict):
        super().__init__(profile)
        self.dashboard_integration = DashboardScrapingIntegration(profile)
        
    def run_scraping_with_dashboard(self, *args, **kwargs):
        """Run scraping with full dashboard integration."""
        self.log("Starting dashboard-integrated scraping session", "INFO")
        
        try:
            result = self.dashboard_integration.run_scraping_with_dashboard_updates(
                *args, **kwargs
            )
            self.log(f"Dashboard-integrated scraping completed: {result}", "INFO")
            return result
            
        except Exception as e:
            self.log(f"Dashboard-integrated scraping failed: {e}", "ERROR")
            raise
    
    def register_dashboard_listener(self, callback: Callable):
        """Register dashboard for real-time updates."""
        self.dashboard_integration.register_dashboard_callback(callback)
    
    def get_dashboard_status(self) -> Dict:
        """Get current status for dashboard display."""
        return {
            "active_operations": self.dashboard_integration.get_active_operations(),
            "performance_summary": self.dashboard_integration.get_performance_summary(),
            "profile": self.profile.get("profile_name", "default"),
            "last_updated": datetime.now().isoformat()
        }


def create_integrated_scraping_handler(profile: Dict) -> UnifiedScrapingOrchestrator:
    """Factory function to create integrated scraping handler."""
    return UnifiedScrapingOrchestrator(profile)


# Dashboard API endpoints for integration
class DashboardAPI:
    """API endpoints for dashboard-scraping integration."""
    
    def __init__(self, orchestrator: UnifiedScrapingOrchestrator):
        self.orchestrator = orchestrator
    
    def start_scraping(self, request_data: Dict) -> Dict:
        """API endpoint to start scraping from dashboard."""
        try:
            mode = request_data.get("mode", "simple")
            jobs = request_data.get("jobs", 20)
            sites = request_data.get("sites", ["indeed", "linkedin"])
            
            result = self.orchestrator.run_scraping_with_dashboard(
                mode=mode, jobs=jobs, sites=sites
            )
            
            return {
                "success": True,
                "result": result,
                "status": self.orchestrator.get_dashboard_status()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status": self.orchestrator.get_dashboard_status()
            }
    
    def get_status(self) -> Dict:
        """API endpoint to get current scraping status."""
        return self.orchestrator.get_dashboard_status()
    
    def get_performance_metrics(self) -> Dict:
        """API endpoint to get performance analytics."""
        return self.orchestrator.dashboard_integration.get_performance_summary()
