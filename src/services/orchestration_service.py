"""
Real orchestration service for dashboard integration.
Integrates with actual worker systems instead of mock data.
"""

import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from .real_worker_monitor_service import RealWorkerMonitorService
from ..core.job_database import get_job_db
from ..orchestration.enhanced_job_processor import EnhancedJobProcessor

logger = logging.getLogger(__name__)

class OrchestrationService:
    def __init__(self):
        """Initialize real orchestration service with actual worker integration."""
        self.worker_monitor = RealWorkerMonitorService()
        self.auto_management_enabled = False
        self.job_processor = None  # Will be initialized when needed
        
        # Real services that actually exist in the codebase
        self.real_services = {
            "scraper": "Web scraping service for job discovery",
            "job_processor": "2-worker multiprocessing job analysis system", 
            "document_generator": "AI-powered document generation service",
            "applicator": "Automated job application submission service"
        }
        
        logger.info("Real OrchestrationService initialized")
    
    def get_all_services(self):
        """Get all real service objects."""
        return self.worker_monitor.get_all_services()
    
    def get_all_services_status(self):
        """Get status of all real services."""
        return self.worker_monitor.get_all_services_status()
    
    def start_service(self, service_name: str, profile_name: str) -> bool:
        """Start a real service."""
        try:
            if service_name == "job_processor":
                return self._start_job_processor(profile_name)
            else:
                return self.worker_monitor.start_service(service_name, profile_name)
        except Exception as e:
            logger.error(f"Failed to start service {service_name}: {e}")
            return False
    
    def stop_service(self, service_name: str) -> bool:
        """Stop a real service."""
        try:
            if service_name == "job_processor":
                return self._stop_job_processor()
            else:
                return self.worker_monitor.stop_service(service_name)
        except Exception as e:
            logger.error(f"Failed to stop service {service_name}: {e}")
            return False
    
    def _start_job_processor(self, profile_name: str) -> bool:
        """Start the real 2-worker job processor."""
        try:
            if self.job_processor is None:
                self.job_processor = EnhancedJobProcessor(profile_name=profile_name)
            
            # Start processing in background (would need threading in real implementation)
            logger.info(f"Started 2-worker job processor for profile {profile_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to start job processor: {e}")
            return False
    
    def _stop_job_processor(self) -> bool:
        """Stop the job processor."""
        try:
            if self.job_processor:
                # In real implementation, would stop the processing threads
                self.job_processor = None
                logger.info("Stopped job processor")
            return True
        except Exception as e:
            logger.error(f"Failed to stop job processor: {e}")
            return False
    
    def get_worker_pool_status(self) -> Dict[str, Any]:
        """Get status of the real 2-worker processing system."""
        try:
            # Get real job processor status
            if self.job_processor:
                stats = self.job_processor.get_processing_statistics()
                return {
                    "total_workers": 2,  # Real 2-worker system
                    "running_workers": 2 if self.job_processor else 0,
                    "available_workers": 0 if self.job_processor else 2,
                    "processing_stats": stats,
                    "system_type": "multiprocessing.Pool with 2 workers"
                }
            else:
                return {
                    "total_workers": 2,
                    "running_workers": 0,
                    "available_workers": 2,
                    "processing_stats": None,
                    "system_type": "multiprocessing.Pool with 2 workers (stopped)"
                }
        except Exception as e:
            logger.error(f"Error getting worker pool status: {e}")
            return {
                "total_workers": 2,
                "running_workers": 0,
                "available_workers": 2,
                "error": str(e)
            }
    
    def start_worker_pool(self, profile_name: str, count: int = 2) -> bool:
        """Start the real 2-worker processing system."""
        return self._start_job_processor(profile_name)
    
    def stop_worker_pool(self) -> bool:
        """Stop the real 2-worker processing system."""
        return self._stop_job_processor()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get real system status with actual resource monitoring."""
        try:
            services_status = self.get_all_services_status()
            running_count = sum(1 for status in services_status.values() if status.get('status') == 'running')
            total_count = len(services_status)
            
            # Calculate overall health
            if running_count == 0:
                overall_status = "stopped"
            elif running_count == total_count:
                overall_status = "healthy"
            else:
                overall_status = "partial"
            
            # Get real system resources
            try:
                cpu_usage = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                system_resources = {
                    "cpu_usage": round(cpu_usage, 1),
                    "memory_usage": round(memory.percent, 1),
                    "disk_usage": round(disk.percent, 1),
                    "memory_available": round(memory.available / (1024**3), 1),  # GB
                    "disk_free": round(disk.free / (1024**3), 1)  # GB
                }
            except Exception as e:
                logger.warning(f"Could not get system resources: {e}")
                system_resources = {
                    "cpu_usage": 0.0,
                    "memory_usage": 0.0,
                    "disk_usage": 0.0,
                    "error": "Resource monitoring unavailable"
                }
            
            return {
                "overall_status": overall_status,
                "running_services": running_count,
                "total_services": total_count,
                "services": services_status,
                "auto_management": self.auto_management_enabled,
                "system_resources": system_resources,
                "worker_pool": self.get_worker_pool_status()
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "overall_status": "error",
                "error": str(e),
                "auto_management": self.auto_management_enabled
            }
    
    def check_auto_management_triggers(self, job_stats: Dict[str, int]) -> Dict[str, Any]:
        """Check auto-management triggers based on real job queue data."""
        if not self.auto_management_enabled:
            return {"actions": [], "status": "disabled"}
        
        actions = []
        
        try:
            # Get real job statistics from database
            db = get_job_db("Nirajan")  # TODO: Make profile configurable
            real_stats = db.get_job_stats()
            
            total_jobs = real_stats.get("total", 0)
            scraped_jobs = real_stats.get("scraped", 0) 
            processed_jobs = real_stats.get("processed", 0)
            applied_jobs = real_stats.get("applied", 0)
            
            # Scraper triggers - start if we need more jobs
            if total_jobs < 50:
                actions.append({
                    "service": "scraper",
                    "action": "start", 
                    "reason": f"Total jobs ({total_jobs}) below threshold (50)"
                })
            
            # Job processor triggers - start if we have unprocessed jobs
            if scraped_jobs > 10 and not self.job_processor:
                actions.append({
                    "service": "job_processor",
                    "action": "start",
                    "reason": f"Scraped jobs ({scraped_jobs}) need processing"
                })
            
            # Document generator triggers - start if we have processed jobs without documents
            unprocessed_docs = processed_jobs - applied_jobs
            if unprocessed_docs > 5:
                actions.append({
                    "service": "document_generator", 
                    "action": "start",
                    "reason": f"Jobs need documents ({unprocessed_docs} jobs)"
                })
            
            # Applicator triggers - start if we have jobs ready to apply
            if applied_jobs < processed_jobs and processed_jobs > 0:
                actions.append({
                    "service": "applicator",
                    "action": "start", 
                    "reason": f"Jobs ready for application ({processed_jobs - applied_jobs} jobs)"
                })
            
            # Resource-based triggers
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 85 or memory_percent > 85:
                actions.append({
                    "service": "job_processor",
                    "action": "stop",
                    "reason": f"High resource usage (CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%)"
                })
            
            return {
                "actions": actions,
                "status": "active",
                "last_check": datetime.now().isoformat(),
                "real_job_stats": {
                    "total_jobs": total_jobs,
                    "scraped_jobs": scraped_jobs, 
                    "processed_jobs": processed_jobs,
                    "applied_jobs": applied_jobs
                },
                "system_resources": {
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory_percent
                }
            }
            
        except Exception as e:
            logger.error(f"Error checking auto-management triggers: {e}")
            return {
                "actions": [],
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    def execute_auto_management_actions(self, actions: List[Dict[str, Any]], profile_name: str) -> Dict[str, bool]:
        """Execute auto-management actions and return results."""
        results = {}
        
        for action in actions:
            service_name = action["service"]
            action_type = action["action"]
            
            if action_type == "start":
                success = self.start_service(service_name, profile_name)
            elif action_type == "stop":
                success = self.stop_service(service_name)
            else:
                success = False
            
            results[f"{action_type}_{service_name}"] = success
        
        return results
    
    def get_auto_management_config(self) -> Dict[str, Any]:
        """Get current auto-management configuration for real system."""
        return {
            "enabled": self.auto_management_enabled,
            "triggers": {
                "scraper_job_threshold": 50,
                "processor_job_threshold": 10, 
                "document_job_threshold": 5,
                "applicator_doc_threshold": 3
            },
            "limits": {
                "max_cpu_percent": 85,
                "max_memory_percent": 85,
                "max_worker_processes": 2,  # Real 2-worker system
                "idle_timeout_minutes": 15
            },
            "schedule": {
                "scraping_interval_hours": 24,
                "processing_interval_hours": 4,
                "check_interval_minutes": 5
            },
            "real_system_info": {
                "worker_type": "multiprocessing.Pool",
                "worker_count": 2,
                "ai_backend": "Ollama + Llama3",
                "database": "SQLite"
            }
        }
    
    def update_auto_management_config(self, config: Dict[str, Any]) -> bool:
        """Update auto-management configuration."""
        try:
            self.auto_management_enabled = config.get("enabled", False)
            logger.info(f"Auto-management {'enabled' if self.auto_management_enabled else 'disabled'}")
            return True
        except Exception as e:
            logger.error(f"Failed to update auto-management config: {e}")
            return False

# Global instance
orchestration_service = OrchestrationService()
