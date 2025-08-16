#!/usr/bin/env python3
"""
Auto Manager - Handles automated service lifecycle management
Single responsibility: Automated start/stop/restart logic based on conditions
Max 300 lines following development standards
"""

import logging
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .service_manager import get_service_manager
from .worker_pool_manager import get_worker_pool_manager
from .system_monitor import get_system_monitor

logger = logging.getLogger(__name__)

class AutoManagementPolicy(Enum):
    """Auto-management policy types."""
    DISABLED = "disabled"
    CONSERVATIVE = "conservative"  # Only restart failed services
    BALANCED = "balanced"         # Restart failed + scale based on load
    AGGRESSIVE = "aggressive"     # Full auto-scaling and optimization

@dataclass
class AutoManagementRule:
    """Auto-management rule definition."""
    name: str
    condition: Callable[[], bool]
    action: Callable[[], bool]
    cooldown_minutes: int = 5
    last_executed: Optional[datetime] = None
    enabled: bool = True

class AutoManager:
    """
    Manages automated service lifecycle operations.
    Follows single responsibility principle - only handles automation logic.
    """
    
    def __init__(self):
        """Initialize auto manager."""
        self.service_manager = get_service_manager()
        self.worker_pool_manager = get_worker_pool_manager()
        self.system_monitor = get_system_monitor()
        self.policy = AutoManagementPolicy.DISABLED
        self.rules: List[AutoManagementRule] = []
        self.auto_management_enabled = False
        self.last_check_time = datetime.now()
        self._setup_default_rules()
    
    def set_policy(self, policy: AutoManagementPolicy) -> None:
        """Set auto-management policy."""
        self.policy = policy
        self.auto_management_enabled = policy != AutoManagementPolicy.DISABLED
        logger.info(f"Auto-management policy set to: {policy.value}")
    
    def get_policy(self) -> AutoManagementPolicy:
        """Get current auto-management policy."""
        return self.policy
    
    def enable_auto_management(self) -> None:
        """Enable auto-management with current policy."""
        if self.policy == AutoManagementPolicy.DISABLED:
            self.policy = AutoManagementPolicy.CONSERVATIVE
        self.auto_management_enabled = True
        logger.info("Auto-management enabled")
    
    def disable_auto_management(self) -> None:
        """Disable auto-management."""
        self.auto_management_enabled = False
        logger.info("Auto-management disabled")
    
    def is_enabled(self) -> bool:
        """Check if auto-management is enabled."""
        return self.auto_management_enabled
    
    def run_auto_management_cycle(self, profile_name: str) -> Dict[str, Any]:
        """Run one cycle of auto-management checks and actions."""
        if not self.auto_management_enabled:
            return {"status": "disabled", "actions_taken": []}
        
        actions_taken = []
        current_time = datetime.now()
        
        # Get current system state
        health_summary = self.system_monitor.get_system_health_summary()
        
        # Execute applicable rules
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Check cooldown
            if rule.last_executed:
                time_since_last = current_time - rule.last_executed
                if time_since_last.total_seconds() < (rule.cooldown_minutes * 60):
                    continue
            
            # Check condition and execute action
            try:
                if rule.condition():
                    logger.info(f"Executing auto-management rule: {rule.name}")
                    success = rule.action()
                    rule.last_executed = current_time
                    
                    actions_taken.append({
                        "rule": rule.name,
                        "success": success,
                        "timestamp": current_time.isoformat()
                    })
                    
                    if success:
                        logger.info(f"Auto-management rule '{rule.name}' executed successfully")
                    else:
                        logger.error(f"Auto-management rule '{rule.name}' failed")
                        
            except Exception as e:
                logger.error(f"Error executing auto-management rule '{rule.name}': {e}")
                actions_taken.append({
                    "rule": rule.name,
                    "success": False,
                    "error": str(e),
                    "timestamp": current_time.isoformat()
                })
        
        self.last_check_time = current_time
        
        return {
            "status": "active",
            "policy": self.policy.value,
            "actions_taken": actions_taken,
            "next_check": (current_time + timedelta(minutes=1)).isoformat(),
            "system_health": health_summary["overall_health_score"]
        }
    
    def add_custom_rule(self, rule: AutoManagementRule) -> None:
        """Add a custom auto-management rule."""
        self.rules.append(rule)
        logger.info(f"Added custom auto-management rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove an auto-management rule by name."""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                logger.info(f"Removed auto-management rule: {rule_name}")
                return True
        return False
    
    def get_rules_status(self) -> List[Dict[str, Any]]:
        """Get status of all auto-management rules."""
        return [
            {
                "name": rule.name,
                "enabled": rule.enabled,
                "cooldown_minutes": rule.cooldown_minutes,
                "last_executed": rule.last_executed.isoformat() if rule.last_executed else None,
                "can_execute": self._can_rule_execute(rule)
            }
            for rule in self.rules
        ]
    
    def _setup_default_rules(self) -> None:
        """Setup default auto-management rules."""
        
        # Rule 1: Restart failed services
        def check_failed_services() -> bool:
            if self.policy == AutoManagementPolicy.DISABLED:
                return False
            health_metrics = self.system_monitor.get_service_health_metrics()
            return any(s.status == "failed" for s in health_metrics)
        
        def restart_failed_services() -> bool:
            health_metrics = self.system_monitor.get_service_health_metrics()
            failed_services = [s.service_name for s in health_metrics if s.status == "failed"]
            success_count = 0
            
            for service_name in failed_services:
                if self.service_manager.restart_service(service_name, "default"):
                    success_count += 1
            
            return success_count > 0
        
        self.rules.append(AutoManagementRule(
            name="restart_failed_services",
            condition=check_failed_services,
            action=restart_failed_services,
            cooldown_minutes=5
        ))
        
        # Rule 2: Scale worker pool based on queue size (balanced/aggressive only)
        def check_worker_scaling_needed() -> bool:
            if self.policy not in [AutoManagementPolicy.BALANCED, AutoManagementPolicy.AGGRESSIVE]:
                return False
            
            queue_status = self.worker_pool_manager.get_queue_status()
            pool_status = self.worker_pool_manager.get_worker_pool_status()
            
            # Scale up if queue is backing up
            return (queue_status["pending_jobs"] > 10 and 
                    pool_status["running_workers"] < pool_status["total_workers"])
        
        def scale_worker_pool() -> bool:
            return self.worker_pool_manager.start_worker_pool("default")
        
        self.rules.append(AutoManagementRule(
            name="auto_scale_workers",
            condition=check_worker_scaling_needed,
            action=scale_worker_pool,
            cooldown_minutes=10
        ))
        
        # Rule 3: Stop idle workers to save resources (aggressive only)
        def check_idle_workers() -> bool:
            if self.policy != AutoManagementPolicy.AGGRESSIVE:
                return False
            
            performance = self.worker_pool_manager.get_worker_performance_metrics()
            return (performance["active_workers"] > 2 and 
                    performance["average_cpu_usage"] < 10.0)
        
        def stop_idle_workers() -> bool:
            # Stop half of the idle workers
            worker_statuses = self.worker_pool_manager.get_individual_worker_status()
            idle_workers = [name for name, status in worker_statuses.items() 
                          if status.get("status") == "running" and status.get("cpu_usage", 0) < 5.0]
            
            workers_to_stop = idle_workers[:len(idle_workers)//2]
            success_count = 0
            
            for worker_name in workers_to_stop:
                if self.service_manager.stop_service(worker_name):
                    success_count += 1
            
            return success_count > 0
        
        self.rules.append(AutoManagementRule(
            name="stop_idle_workers",
            condition=check_idle_workers,
            action=stop_idle_workers,
            cooldown_minutes=15
        ))
    
    def _can_rule_execute(self, rule: AutoManagementRule) -> bool:
        """Check if a rule can execute (not in cooldown)."""
        if not rule.enabled or not self.auto_management_enabled:
            return False
        
        if rule.last_executed:
            time_since_last = datetime.now() - rule.last_executed
            return time_since_last.total_seconds() >= (rule.cooldown_minutes * 60)
        
        return True


# Global auto manager instance
_auto_manager = None

def get_auto_manager() -> AutoManager:
    """Get global auto manager instance."""
    global _auto_manager
    if _auto_manager is None:
        _auto_manager = AutoManager()
    return _auto_manager