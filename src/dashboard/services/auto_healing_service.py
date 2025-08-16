#!/usr/bin/env python3
"""
Auto-Healing Service - Automatic component recovery and health monitoring
Part of Phase 4: Configurable Services implementation

This service provides automatic component health monitoring and recovery
without AI complexity. Uses strategy-based recovery patterns.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import psutil
import traceback

logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    """Component health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"
    RECOVERING = "recovering"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Available recovery strategies"""
    RESTART = "restart"
    RESET_CONFIG = "reset_config"
    CLEAR_CACHE = "clear_cache"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"
    FORCE_KILL = "force_kill"
    WAIT_AND_RETRY = "wait_and_retry"
    ESCALATE = "escalate"


@dataclass
class HealthMetric:
    """Individual health metric"""
    name: str
    value: Any
    threshold: Any
    status: ComponentStatus
    message: str
    timestamp: datetime


@dataclass
class ComponentHealth:
    """Health status for a component"""
    component_name: str
    status: ComponentStatus
    metrics: List[HealthMetric]
    last_check: datetime
    failure_count: int = 0
    recovery_attempts: int = 0
    last_failure: Optional[datetime] = None
    uptime_start: Optional[datetime] = None


@dataclass
class RecoveryAction:
    """Recovery action configuration"""
    strategy: RecoveryStrategy
    max_attempts: int = 3
    delay_seconds: int = 5
    timeout_seconds: int = 30
    escalation_strategy: Optional[RecoveryStrategy] = None


class HealthMonitor:
    """Component health monitoring system"""
    
    def __init__(self):
        self.component_health: Dict[str, ComponentHealth] = {}
        self.health_checks: Dict[str, Callable] = {}
        self.monitoring_active = False
        self._lock = threading.RLock()
    
    def register_component(self, component_name: str,
                          health_check: Callable[[], Dict[str, Any]]) -> None:
        """Register a component for health monitoring"""
        with self._lock:
            self.health_checks[component_name] = health_check
            self.component_health[component_name] = ComponentHealth(
                component_name=component_name,
                status=ComponentStatus.UNKNOWN,
                metrics=[],
                last_check=datetime.now(),
                uptime_start=datetime.now()
            )
            logger.info(f"Registered component for monitoring: {component_name}")
    
    def check_component_health(self, component_name: str) -> ComponentHealth:
        """Check health of a specific component"""
        if component_name not in self.health_checks:
            return ComponentHealth(
                component_name=component_name,
                status=ComponentStatus.UNKNOWN,
                metrics=[],
                last_check=datetime.now()
            )
        
        try:
            # Run health check
            health_data = self.health_checks[component_name]()
            metrics = []
            overall_status = ComponentStatus.HEALTHY
            
            # Process health data
            for metric_name, metric_info in health_data.items():
                value = metric_info.get('value')
                threshold = metric_info.get('threshold')
                status_str = metric_info.get('status', 'healthy')
                message = metric_info.get('message', '')
                
                # Convert status string to enum
                try:
                    status = ComponentStatus(status_str.lower())
                except ValueError:
                    status = ComponentStatus.UNKNOWN
                
                metric = HealthMetric(
                    name=metric_name,
                    value=value,
                    threshold=threshold,
                    status=status,
                    message=message,
                    timestamp=datetime.now()
                )
                metrics.append(metric)
                
                # Update overall status (worst status wins)
                if status.value == ComponentStatus.FAILED.value:
                    overall_status = ComponentStatus.FAILED
                elif (status.value == ComponentStatus.CRITICAL.value and 
                      overall_status.value != ComponentStatus.FAILED.value):
                    overall_status = ComponentStatus.CRITICAL
                elif (status.value == ComponentStatus.WARNING.value and 
                      overall_status.value in [ComponentStatus.HEALTHY.value]):
                    overall_status = ComponentStatus.WARNING
            
            # Update component health
            with self._lock:
                health = self.component_health[component_name]
                old_status = health.status
                health.status = overall_status
                health.metrics = metrics
                health.last_check = datetime.now()
                
                # Track failures
                if overall_status == ComponentStatus.FAILED:
                    if old_status != ComponentStatus.FAILED:
                        health.failure_count += 1
                        health.last_failure = datetime.now()
                elif overall_status == ComponentStatus.HEALTHY:
                    if old_status in [ComponentStatus.FAILED, 
                                     ComponentStatus.CRITICAL]:
                        # Component recovered
                        health.uptime_start = datetime.now()
            
            return self.component_health[component_name]
        
        except Exception as e:
            logger.error(f"Error checking health for {component_name}: {e}")
            with self._lock:
                self.component_health[component_name].status = (
                    ComponentStatus.UNKNOWN)
            return self.component_health[component_name]
    
    def get_all_health_status(self) -> Dict[str, ComponentHealth]:
        """Get health status for all monitored components"""
        with self._lock:
            return {name: self.check_component_health(name) 
                    for name in self.health_checks.keys()}


class RecoveryStrategies:
    """Collection of recovery strategies for different failure types"""
    
    def __init__(self):
        self.strategies: Dict[str, List[RecoveryAction]] = {}
        self._setup_default_strategies()
    
    def _setup_default_strategies(self) -> None:
        """Setup default recovery strategies"""
        # Database connection issues
        self.strategies["database"] = [
            RecoveryAction(RecoveryStrategy.WAIT_AND_RETRY, max_attempts=3),
            RecoveryAction(RecoveryStrategy.RESTART, max_attempts=2),
            RecoveryAction(RecoveryStrategy.ESCALATE)
        ]
        
        # Service unavailable
        self.strategies["service"] = [
            RecoveryAction(RecoveryStrategy.RESTART, max_attempts=2),
            RecoveryAction(RecoveryStrategy.CLEAR_CACHE, max_attempts=1),
            RecoveryAction(RecoveryStrategy.FORCE_KILL, max_attempts=1),
            RecoveryAction(RecoveryStrategy.ESCALATE)
        ]
        
        # Memory issues
        self.strategies["memory"] = [
            RecoveryAction(RecoveryStrategy.CLEAR_CACHE, max_attempts=1),
            RecoveryAction(RecoveryStrategy.GRACEFUL_SHUTDOWN, max_attempts=1),
            RecoveryAction(RecoveryStrategy.RESTART, max_attempts=1)
        ]
        
        # Network issues
        self.strategies["network"] = [
            RecoveryAction(RecoveryStrategy.WAIT_AND_RETRY, max_attempts=5),
            RecoveryAction(RecoveryStrategy.RESET_CONFIG, max_attempts=1),
            RecoveryAction(RecoveryStrategy.ESCALATE)
        ]
    
    def get_strategy_for_failure(self, failure_type: str) -> List[RecoveryAction]:
        """Get recovery strategy for specific failure type"""
        return self.strategies.get(failure_type, [
            RecoveryAction(RecoveryStrategy.RESTART, max_attempts=1),
            RecoveryAction(RecoveryStrategy.ESCALATE)
        ])
    
    def add_custom_strategy(self, failure_type: str, 
                           actions: List[RecoveryAction]) -> None:
        """Add custom recovery strategy"""
        self.strategies[failure_type] = actions


class AutoHealingService:
    """Service for automatic component recovery"""
    
    def __init__(self):
        self.health_monitor = HealthMonitor()
        self.recovery_strategies = RecoveryStrategies()
        self.recovery_handlers: Dict[str, Dict[RecoveryStrategy, Callable]] = {}
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        self.monitoring_interval = 30  # seconds
        self.recovery_history: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
    
    def register_component(self, component_name: str,
                          health_check: Callable[[], Dict[str, Any]],
                          recovery_handlers: Dict[RecoveryStrategy, 
                                                Callable] = None) -> None:
        """Register component with health monitoring and recovery handlers"""
        # Register with health monitor
        self.health_monitor.register_component(component_name, health_check)
        
        # Register recovery handlers
        if recovery_handlers:
            with self._lock:
                self.recovery_handlers[component_name] = recovery_handlers
        
        logger.info(f"Registered component with auto-healing: {component_name}")
    
    def monitor_component_health(self) -> Dict[str, ComponentHealth]:
        """Monitor all component health and return status"""
        return self.health_monitor.get_all_health_status()
    
    def auto_heal_component(self, component_name: str, 
                           failure_type: str = "service") -> bool:
        """Automatically heal failed component"""
        try:
            # Get current health status
            health = self.health_monitor.check_component_health(component_name)
            
            if health.status in [ComponentStatus.HEALTHY, 
                               ComponentStatus.WARNING]:
                logger.info(f"Component {component_name} is already healthy")
                return True
            
            # Get recovery strategy
            recovery_actions = (self.recovery_strategies
                              .get_strategy_for_failure(failure_type))
            
            if component_name not in self.recovery_handlers:
                logger.warning(f"No recovery handlers for {component_name}")
                return False
            
            handlers = self.recovery_handlers[component_name]
            
            # Execute recovery actions
            for action in recovery_actions:
                if action.strategy in handlers:
                    success = self._execute_recovery_action(
                        component_name, action, handlers[action.strategy])
                    
                    if success:
                        # Record successful recovery
                        self._record_recovery(component_name, action, True)
                        return True
                    else:
                        # Record failed recovery attempt
                        self._record_recovery(component_name, action, False)
                
                # Check if we should escalate
                if action.strategy == RecoveryStrategy.ESCALATE:
                    logger.error(f"Escalating recovery for {component_name}")
                    return False
            
            return False
        
        except Exception as e:
            logger.error(f"Error in auto-healing {component_name}: {e}")
            return False
    
    def _execute_recovery_action(self, component_name: str,
                                action: RecoveryAction,
                                handler: Callable) -> bool:
        """Execute a specific recovery action"""
        try:
            logger.info(f"Executing {action.strategy.value} for {component_name}")
            
            for attempt in range(action.max_attempts):
                try:
                    # Execute recovery handler
                    result = handler()
                    
                    # Wait for action to take effect
                    time.sleep(action.delay_seconds)
                    
                    # Check if component is now healthy
                    health = (self.health_monitor
                             .check_component_health(component_name))
                    
                    if health.status in [ComponentStatus.HEALTHY,
                                       ComponentStatus.WARNING]:
                        logger.info(f"Recovery successful for {component_name} "
                                  f"using {action.strategy.value}")
                        return True
                    
                    logger.warning(f"Recovery attempt {attempt + 1} failed for "
                                 f"{component_name}")
                
                except Exception as e:
                    logger.error(f"Recovery attempt {attempt + 1} error for "
                               f"{component_name}: {e}")
            
            return False
        
        except Exception as e:
            logger.error(f"Error executing recovery action: {e}")
            return False
    
    def _record_recovery(self, component_name: str, action: RecoveryAction,
                        success: bool) -> None:
        """Record recovery attempt in history"""
        recovery_record = {
            'component': component_name,
            'strategy': action.strategy.value,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'attempts': action.max_attempts
        }
        
        with self._lock:
            self.recovery_history.append(recovery_record)
            
            # Keep only last 100 records
            if len(self.recovery_history) > 100:
                self.recovery_history = self.recovery_history[-100:]
    
    def get_recovery_suggestions(self, component_name: str) -> List[str]:
        """Get recovery suggestions for failed component"""
        try:
            health = self.health_monitor.check_component_health(component_name)
            suggestions = []
            
            # Analyze health metrics for suggestions
            for metric in health.metrics:
                if metric.status == ComponentStatus.FAILED:
                    if "memory" in metric.name.lower():
                        suggestions.append("Clear cache and restart component")
                    elif "disk" in metric.name.lower():
                        suggestions.append("Free up disk space")
                    elif "network" in metric.name.lower():
                        suggestions.append("Check network connectivity")
                    elif "database" in metric.name.lower():
                        suggestions.append("Restart database connection")
                    else:
                        suggestions.append(f"Check {metric.name} configuration")
            
            # Add general suggestions based on failure history
            if health.failure_count > 3:
                suggestions.append("Consider component redesign - frequent failures")
            
            if not suggestions:
                suggestions.append("Restart component service")
                suggestions.append("Check component logs for errors")
            
            return suggestions[:5]  # Limit to 5 suggestions
        
        except Exception as e:
            logger.error(f"Error getting recovery suggestions: {e}")
            return ["Check component logs", "Restart component"]
    
    def start_monitoring(self) -> None:
        """Start continuous health monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Auto-healing monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop continuous health monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Auto-healing monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Continuous monitoring loop"""
        while self.monitoring_active:
            try:
                # Check all component health
                health_status = self.monitor_component_health()
                
                # Auto-heal failed components
                for component_name, health in health_status.items():
                    if health.status == ComponentStatus.FAILED:
                        logger.warning(f"Auto-healing triggered for "
                                     f"{component_name}")
                        self.auto_heal_component(component_name)
                
                time.sleep(self.monitoring_interval)
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Short delay on error
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get monitoring and recovery statistics"""
        with self._lock:
            health_status = self.monitor_component_health()
            
            # Count by status
            status_counts = defaultdict(int)
            for health in health_status.values():
                status_counts[health.status.value] += 1
            
            # Recovery statistics
            successful_recoveries = sum(1 for r in self.recovery_history 
                                      if r['success'])
            total_recoveries = len(self.recovery_history)
            
            return {
                'total_components': len(health_status),
                'monitoring_active': self.monitoring_active,
                'status_distribution': dict(status_counts),
                'recovery_success_rate': (successful_recoveries / 
                                        max(total_recoveries, 1)),
                'total_recovery_attempts': total_recoveries,
                'successful_recoveries': successful_recoveries,
                'recent_failures': [
                    r for r in self.recovery_history[-10:] if not r['success']
                ]
            }


# Global instance for easy access
_auto_healing_service = None

def get_auto_healing_service() -> AutoHealingService:
    """Get or create global auto-healing service instance"""
    global _auto_healing_service
    if _auto_healing_service is None:
        _auto_healing_service = AutoHealingService()
    return _auto_healing_service
