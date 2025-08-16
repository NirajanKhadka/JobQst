#!/usr/bin/env python3
"""
Automated Workflow Service - Service for optimizing user workflows
Part of Phase 4: Configurable Services implementation

This service provides workflow optimization without AI complexity.
Uses pattern-based analysis to improve user experience.
"""

import logging
import json
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    action: str
    context: Dict[str, Any]
    timestamp: datetime
    duration_ms: int = 0
    success: bool = True


@dataclass
class WorkflowPattern:
    """Detected workflow pattern"""
    pattern_id: str
    steps: List[str]
    frequency: int
    avg_duration_ms: int
    success_rate: float
    last_seen: datetime


@dataclass
class WorkflowOptimization:
    """Suggested workflow optimization"""
    original_steps: List[str]
    optimized_steps: List[str]
    estimated_time_savings_ms: int
    confidence: float
    description: str


class WorkflowPatternTracker:
    """Track user workflow patterns for optimization"""
    
    def __init__(self, max_sessions: int = 1000):
        self.sessions: Dict[str, List[WorkflowStep]] = {}
        self.patterns: Dict[str, WorkflowPattern] = {}
        self.max_sessions = max_sessions
        self.current_session_id: Optional[str] = None
        self._lock = threading.RLock()
    
    def start_session(self, session_id: str) -> None:
        """Start tracking a new workflow session"""
        with self._lock:
            if len(self.sessions) >= self.max_sessions:
                # Remove oldest session
                oldest_session = min(self.sessions.keys())
                del self.sessions[oldest_session]
            
            self.sessions[session_id] = []
            self.current_session_id = session_id
            logger.debug(f"Started workflow session: {session_id}")
    
    def track_action(self, action: str, context: Dict[str, Any] = None) -> None:
        """Track a user action in the current workflow"""
        if not self.current_session_id:
            # Auto-start session if none active
            self.start_session(f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        step = WorkflowStep(
            action=action,
            context=context or {},
            timestamp=datetime.now()
        )
        
        with self._lock:
            if self.current_session_id in self.sessions:
                self.sessions[self.current_session_id].append(step)
                
                # Analyze patterns if session has enough steps
                if len(self.sessions[self.current_session_id]) >= 3:
                    self._analyze_patterns(self.current_session_id)
    
    def end_session(self, session_id: Optional[str] = None) -> None:
        """End the current workflow session"""
        target_session = session_id or self.current_session_id
        
        if target_session and target_session in self.sessions:
            # Final pattern analysis
            self._analyze_patterns(target_session)
            logger.debug(f"Ended workflow session: {target_session}")
            
            if target_session == self.current_session_id:
                self.current_session_id = None
    
    def _analyze_patterns(self, session_id: str) -> None:
        """Analyze workflow patterns in a session"""
        if session_id not in self.sessions:
            return
        
        steps = self.sessions[session_id]
        if len(steps) < 3:
            return
        
        # Extract action sequences
        actions = [step.action for step in steps]
        
        # Find patterns of different lengths
        for pattern_length in range(3, min(len(actions) + 1, 6)):
            for i in range(len(actions) - pattern_length + 1):
                pattern_actions = actions[i:i + pattern_length]
                pattern_id = "_".join(pattern_actions)
                
                # Calculate pattern metrics
                pattern_steps = steps[i:i + pattern_length]
                total_duration = sum(step.duration_ms for step in pattern_steps)
                success_count = sum(1 for step in pattern_steps if step.success)
                success_rate = success_count / len(pattern_steps)
                
                with self._lock:
                    if pattern_id in self.patterns:
                        # Update existing pattern
                        pattern = self.patterns[pattern_id]
                        pattern.frequency += 1
                        pattern.avg_duration_ms = (
                            (pattern.avg_duration_ms + total_duration) // 2)
                        pattern.success_rate = (
                            (pattern.success_rate + success_rate) / 2)
                        pattern.last_seen = datetime.now()
                    else:
                        # Create new pattern
                        self.patterns[pattern_id] = WorkflowPattern(
                            pattern_id=pattern_id,
                            steps=pattern_actions,
                            frequency=1,
                            avg_duration_ms=total_duration,
                            success_rate=success_rate,
                            last_seen=datetime.now()
                        )
    
    def get_frequent_patterns(self, min_frequency: int = 3) -> List[WorkflowPattern]:
        """Get frequently occurring workflow patterns"""
        with self._lock:
            return [
                pattern for pattern in self.patterns.values()
                if pattern.frequency >= min_frequency
            ]
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of a workflow session"""
        if session_id not in self.sessions:
            return {}
        
        steps = self.sessions[session_id]
        total_duration = sum(step.duration_ms for step in steps)
        success_count = sum(1 for step in steps if step.success)
        
        return {
            'session_id': session_id,
            'total_steps': len(steps),
            'total_duration_ms': total_duration,
            'success_rate': success_count / len(steps) if steps else 0,
            'unique_actions': len(set(step.action for step in steps)),
            'start_time': steps[0].timestamp.isoformat() if steps else None,
            'end_time': steps[-1].timestamp.isoformat() if steps else None
        }


class WorkflowOptimizer:
    """Optimize user workflows based on patterns"""
    
    def __init__(self):
        self.optimization_rules: Dict[str, Callable] = {}
        self.shortcut_mappings: Dict[str, List[str]] = {}
        self._setup_default_optimizations()
    
    def _setup_default_optimizations(self) -> None:
        """Setup default workflow optimizations"""
        # Common job management optimizations
        self.shortcut_mappings.update({
            "view_jobs_apply_filter": ["view_jobs_filtered"],
            "jobs_tab_apply_job_details": ["quick_apply"],
            "overview_jobs_analytics": ["quick_dashboard"],
            "settings_profile_jobs": ["profile_dashboard"],
        })
    
    def analyze_workflow_efficiency(self, steps: List[str]) -> float:
        """Analyze workflow efficiency (0-1, higher is better)"""
        if not steps:
            return 0.0
        
        # Base efficiency metrics
        efficiency_score = 1.0
        
        # Penalize repetitive actions
        unique_ratio = len(set(steps)) / len(steps)
        efficiency_score *= unique_ratio
        
        # Penalize back-and-forth navigation
        navigation_penalty = 0
        for i in range(len(steps) - 2):
            if steps[i] == steps[i + 2]:  # Same action 2 steps apart
                navigation_penalty += 0.1
        
        efficiency_score -= min(navigation_penalty, 0.5)
        
        # Bonus for known efficient patterns
        for pattern_key in self.shortcut_mappings:
            if pattern_key.replace("_", " ") in " ".join(steps):
                efficiency_score += 0.1
        
        return max(0.0, min(1.0, efficiency_score))
    
    def suggest_optimizations(self, workflow: List[str]) -> List[WorkflowOptimization]:
        """Suggest workflow optimizations"""
        optimizations = []
        workflow_str = "_".join(workflow)
        
        # Check for shortcut opportunities
        for pattern, shortcut in self.shortcut_mappings.items():
            if pattern in workflow_str:
                # Find the pattern in workflow
                pattern_steps = pattern.split("_")
                optimized = workflow.copy()
                
                # Replace pattern with shortcut
                for i in range(len(optimized) - len(pattern_steps) + 1):
                    if optimized[i:i+len(pattern_steps)] == pattern_steps:
                        optimized[i:i+len(pattern_steps)] = shortcut
                        break
                
                if optimized != workflow:
                    time_savings = len(workflow) - len(optimized)
                    optimization = WorkflowOptimization(
                        original_steps=workflow.copy(),
                        optimized_steps=optimized,
                        estimated_time_savings_ms=time_savings * 1000,
                        confidence=0.8,
                        description=f"Use shortcut for {pattern.replace('_', ' ')}"
                    )
                    optimizations.append(optimization)
        
        # Suggest removing redundant steps
        if len(workflow) > len(set(workflow)):
            unique_workflow = []
            seen = set()
            for step in workflow:
                if step not in seen:
                    unique_workflow.append(step)
                    seen.add(step)
            
            if len(unique_workflow) < len(workflow):
                optimization = WorkflowOptimization(
                    original_steps=workflow.copy(),
                    optimized_steps=unique_workflow,
                    estimated_time_savings_ms=(len(workflow) - len(unique_workflow)) * 500,
                    confidence=0.9,
                    description="Remove redundant repeated actions"
                )
                optimizations.append(optimization)
        
        return optimizations
    
    def create_Configurable_shortcuts(self, common_patterns: Dict[str, int]) -> Dict[str, str]:
        """Create Configurable shortcuts for common workflows"""
        shortcuts = {}
        
        # Sort patterns by frequency
        sorted_patterns = sorted(common_patterns.items(), 
                               key=lambda x: x[1], reverse=True)
        
        for pattern, frequency in sorted_patterns[:10]:  # Top 10 patterns
            if frequency >= 5:  # Minimum frequency threshold
                # Create shortcut name
                steps = pattern.split("_")
                if len(steps) >= 2:
                    shortcut_name = f"quick_{steps[0]}_{steps[-1]}"
                    shortcuts[shortcut_name] = pattern
        
        return shortcuts


class AutomatedWorkflowService:
    """Service for optimizing user workflows"""
    
    def __init__(self, enable_persistence: bool = True):
        self.workflow_patterns = WorkflowPatternTracker()
        self.optimization_engine = WorkflowOptimizer()
        self.enable_persistence = enable_persistence
        self.data_dir = Path("workflow_data")
        self.shortcuts: Dict[str, str] = {}
        self.user_preferences: Dict[str, Any] = {}
        self._lock = threading.RLock()
        
        if self.enable_persistence:
            self.data_dir.mkdir(exist_ok=True)
            self._load_persistent_data()
    
    def track_user_workflow(self, action: str, context: Dict = None) -> None:
        """Track user workflow patterns"""
        self.workflow_patterns.track_action(action, context or {})
        
        # Periodically save data
        if self.enable_persistence:
            self._save_persistent_data()
    
    def start_workflow_session(self, session_id: str = None) -> str:
        """Start a new workflow tracking session"""
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.workflow_patterns.start_session(session_id)
        return session_id
    
    def end_workflow_session(self, session_id: str = None) -> Dict[str, Any]:
        """End workflow session and return summary"""
        self.workflow_patterns.end_session(session_id)
        
        target_session = session_id or self.workflow_patterns.current_session_id
        if target_session:
            return self.workflow_patterns.get_session_summary(target_session)
        return {}
    
    def suggest_workflow_shortcuts(self, current_context: Dict) -> List[str]:
        """Suggest workflow optimizations based on current context"""
        suggestions = []
        
        # Get current workflow if in session
        current_session = self.workflow_patterns.current_session_id
        if current_session and current_session in self.workflow_patterns.sessions:
            current_workflow = [
                step.action for step in 
                self.workflow_patterns.sessions[current_session]
            ]
            
            # Get optimization suggestions
            optimizations = (self.optimization_engine
                           .suggest_optimizations(current_workflow))
            
            for opt in optimizations:
                suggestions.append(
                    f"{opt.description} (saves ~{opt.estimated_time_savings_ms}ms)"
                )
        
        # Add context-aware suggestions
        if 'current_tab' in current_context:
            tab = current_context['current_tab']
            if tab == 'jobs':
                suggestions.append("Use bulk actions for multiple jobs")
                suggestions.append("Filter jobs before viewing details")
            elif tab == 'analytics':
                suggestions.append("Bookmark frequently viewed charts")
            elif tab == 'settings':
                suggestions.append("Save profile configurations for quick switching")
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def optimize_navigation(self, user_journey: List[str]) -> List[str]:
        """Optimize navigation based on patterns"""
        if not user_journey:
            return user_journey
        
        # Get optimization suggestions
        optimizations = (self.optimization_engine
                        .suggest_optimizations(user_journey))
        
        # Apply best optimization
        if optimizations:
            best_optimization = max(optimizations, key=lambda x: x.confidence)
            return best_optimization.optimized_steps
        
        return user_journey
    
    def get_workflow_analytics(self) -> Dict[str, Any]:
        """Get workflow analytics and insights"""
        with self._lock:
            patterns = self.workflow_patterns.get_frequent_patterns()
            
            # Calculate analytics
            total_sessions = len(self.workflow_patterns.sessions)
            total_patterns = len(patterns)
            avg_session_length = 0
            
            if self.workflow_patterns.sessions:
                session_lengths = [
                    len(steps) for steps in self.workflow_patterns.sessions.values()
                ]
                avg_session_length = sum(session_lengths) / len(session_lengths)
            
            # Most common actions
            action_counts = defaultdict(int)
            for steps in self.workflow_patterns.sessions.values():
                for step in steps:
                    action_counts[step.action] += 1
            
            top_actions = sorted(action_counts.items(), 
                               key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_sessions': total_sessions,
                'total_patterns': total_patterns,
                'avg_session_length': avg_session_length,
                'top_actions': top_actions,
                'frequent_patterns': [asdict(p) for p in patterns],
                'shortcuts_available': len(self.shortcuts),
                'optimization_opportunities': len([
                    p for p in patterns if p.frequency >= 5
                ])
            }
    
    def _save_persistent_data(self) -> None:
        """Save workflow data to disk"""
        try:
            # Save patterns
            patterns_file = self.data_dir / "patterns.json"
            patterns_data = {
                pattern_id: asdict(pattern)
                for pattern_id, pattern in self.workflow_patterns.patterns.items()
            }
            
            with open(patterns_file, 'w') as f:
                json.dump(patterns_data, f, default=str, indent=2)
            
            # Save shortcuts
            shortcuts_file = self.data_dir / "shortcuts.json"
            with open(shortcuts_file, 'w') as f:
                json.dump(self.shortcuts, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving workflow data: {e}")
    
    def _load_persistent_data(self) -> None:
        """Load workflow data from disk"""
        try:
            # Load patterns
            patterns_file = self.data_dir / "patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                
                for pattern_id, pattern_dict in patterns_data.items():
                    pattern = WorkflowPattern(
                        pattern_id=pattern_dict['pattern_id'],
                        steps=pattern_dict['steps'],
                        frequency=pattern_dict['frequency'],
                        avg_duration_ms=pattern_dict['avg_duration_ms'],
                        success_rate=pattern_dict['success_rate'],
                        last_seen=datetime.fromisoformat(pattern_dict['last_seen'])
                    )
                    self.workflow_patterns.patterns[pattern_id] = pattern
            
            # Load shortcuts
            shortcuts_file = self.data_dir / "shortcuts.json"
            if shortcuts_file.exists():
                with open(shortcuts_file, 'r') as f:
                    self.shortcuts = json.load(f)
        
        except Exception as e:
            logger.error(f"Error loading workflow data: {e}")


# Global instance for easy access
_Automated_workflow_service = None

def get_Automated_workflow_service(**kwargs) -> AutomatedWorkflowService:
    """Get or create global Automated workflow service instance"""
    global _Automated_workflow_service
    if _Automated_workflow_service is None:
        _Automated_workflow_service = AutomatedWorkflowService(**kwargs)
    return _Automated_workflow_service
