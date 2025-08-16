"""
Status Widgets Components

This module provides reusable status widgets including health status indicators,
progress bars, metric displays, and alert badges.
"""

import streamlit as st
import time
from typing import Dict, List, Optional, Any, Union, Literal
from enum import Enum
import plotly.graph_objects as go
from datetime import datetime, timedelta


class StatusType(Enum):
    """Status types for indicators."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    PENDING = "pending"


class StatusIndicator:
    """Reusable status indicator component."""
    
    STATUS_COLORS = {
        StatusType.SUCCESS: "#10B981",
        StatusType.WARNING: "#F59E0B", 
        StatusType.ERROR: "#EF4444",
        StatusType.INFO: "#3B82F6",
        StatusType.PENDING: "#6B7280"
    }
    
    STATUS_ICONS = {
        StatusType.SUCCESS: "✅",
        StatusType.WARNING: "⚠️",
        StatusType.ERROR: "❌", 
        StatusType.INFO: "ℹ️",
        StatusType.PENDING: "⏳"
    }
    
    def __init__(self, 
                 status: StatusType,
                 label: str,
                 description: Optional[str] = None,
                 show_icon: bool = True,
                 custom_color: Optional[str] = None):
        """
        Initialize status indicator.
        
        Args:
            status: Status type
            label: Status label text
            description: Optional description text
            show_icon: Whether to show status icon
            custom_color: Custom color override
        """
        self.status = status
        self.label = label
        self.description = description
        self.show_icon = show_icon
        self.color = custom_color or self.STATUS_COLORS[status]
        self.icon = self.STATUS_ICONS[status]
    
    def render(self, container: Optional[Any] = None):
        """Render the status indicator."""
        target = container or st
        
        icon_text = f"{self.icon} " if self.show_icon else ""
        
        target.markdown(
            f"""
            <div style="
                padding: 8px 12px;
                border-left: 4px solid {self.color};
                background-color: {self.color}20;
                border-radius: 4px;
                margin: 4px 0;
            ">
                <span style="color: {self.color}; font-weight: 600;">
                    {icon_text}{self.label}
                </span>
                {f'<br><small style="color: #6B7280;">{self.description}</small>' if self.description else ''}
            </div>
            """,
            unsafe_allow_html=True
        )


class ProgressBar:
    """Reusable progress bar component."""
    
    def __init__(self, 
                 value: float,
                 max_value: float = 100,
                 label: Optional[str] = None,
                 show_percentage: bool = True,
                 color: str = "#3B82F6",
                 height: int = 20):
        """
        Initialize progress bar.
        
        Args:
            value: Current progress value
            max_value: Maximum progress value
            label: Optional label text
            show_percentage: Whether to show percentage text
            color: Progress bar color
            height: Bar height in pixels
        """
        self.value = value
        self.max_value = max_value
        self.label = label
        self.show_percentage = show_percentage
        self.color = color
        self.height = height
        self.percentage = (value / max_value) * 100 if max_value > 0 else 0
    
    def render(self, container: Optional[Any] = None):
        """Render the progress bar."""
        target = container or st
        
        if self.label:
            target.text(self.label)
        
        # Use Streamlit's built-in progress bar
        progress_container = target.container()
        progress_container.progress(self.percentage / 100)
        
        if self.show_percentage:
            progress_container.caption(f"{self.percentage:.1f}% ({self.value}/{self.max_value})")


class MetricDisplay:
    """Reusable metric display component."""
    
    def __init__(self,
                 value: Union[int, float, str],
                 label: str,
                 delta: Optional[Union[int, float]] = None,
                 delta_color: str = "normal",
                 help_text: Optional[str] = None,
                 format_string: Optional[str] = None):
        """
        Initialize metric display.
        
        Args:
            value: Metric value to display
            label: Metric label
            delta: Change in value (optional)
            delta_color: Delta color ('normal', 'inverse', 'off')
            help_text: Help tooltip text
            format_string: Value formatting string
        """
        self.value = value
        self.label = label
        self.delta = delta
        self.delta_color = delta_color
        self.help_text = help_text
        self.format_string = format_string
    
    def render(self, container: Optional[Any] = None):
        """Render the metric display."""
        target = container or st
        
        formatted_value = self.value
        if self.format_string and isinstance(self.value, (int, float)):
            formatted_value = self.format_string.format(self.value)
        
        target.metric(
            label=self.label,
            value=formatted_value,
            delta=self.delta,
            delta_color=self.delta_color,
            help=self.help_text
        )


class HealthStatus:
    """Comprehensive health status widget."""
    
    def __init__(self,
                 services: Dict[str, StatusType],
                 overall_status: Optional[StatusType] = None,
                 title: str = "System Health"):
        """
        Initialize health status widget.
        
        Args:
            services: Dictionary of service names and their status
            overall_status: Overall system status (auto-calculated if None)
            title: Widget title
        """
        self.services = services
        self.title = title
        self.overall_status = overall_status or self._calculate_overall_status()
    
    def _calculate_overall_status(self) -> StatusType:
        """Calculate overall status based on service statuses."""
        statuses = list(self.services.values())
        
        if StatusType.ERROR in statuses:
            return StatusType.ERROR
        elif StatusType.WARNING in statuses:
            return StatusType.WARNING
        elif StatusType.PENDING in statuses:
            return StatusType.PENDING
        else:
            return StatusType.SUCCESS
    
    def render(self, container: Optional[Any] = None):
        """Render the health status widget."""
        target = container or st
        
        with target.expander(f"{self.title} - {self.overall_status.value.title()}", expanded=True):
            # Overall status
            overall_indicator = StatusIndicator(
                self.overall_status,
                f"Overall Status: {self.overall_status.value.title()}"
            )
            overall_indicator.render()
            
            st.divider()
            
            # Individual services
            col_count = min(len(self.services), 3)
            if col_count > 0:
                cols = st.columns(col_count)
                
                for idx, (service_name, status) in enumerate(self.services.items()):
                    col_idx = idx % col_count
                    with cols[col_idx]:
                        service_indicator = StatusIndicator(
                            status,
                            service_name,
                            f"Status: {status.value}"
                        )
                        service_indicator.render()


class AlertBadge:
    """Alert badge component."""
    
    def __init__(self,
                 count: int,
                 alert_type: StatusType = StatusType.ERROR,
                 label: str = "Alerts",
                 show_when_zero: bool = False):
        """
        Initialize alert badge.
        
        Args:
            count: Number of alerts
            alert_type: Type of alerts
            label: Badge label
            show_when_zero: Whether to show badge when count is zero
        """
        self.count = count
        self.alert_type = alert_type
        self.label = label
        self.show_when_zero = show_when_zero
    
    def render(self, container: Optional[Any] = None):
        """Render the alert badge."""
        if self.count == 0 and not self.show_when_zero:
            return
            
        target = container or st
        
        color = StatusIndicator.STATUS_COLORS[self.alert_type]
        
        target.markdown(
            f"""
            <div style="
                display: inline-block;
                padding: 4px 8px;
                background-color: {color};
                color: white;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                margin: 2px;
            ">
                {self.label}: {self.count}
            </div>
            """,
            unsafe_allow_html=True
        )


class CounterWidget:
    """Animated counter widget."""
    
    def __init__(self,
                 current_value: Union[int, float],
                 target_value: Union[int, float],
                 label: str,
                 prefix: str = "",
                 suffix: str = "",
                 animation_duration: float = 1.0):
        """
        Initialize counter widget.
        
        Args:
            current_value: Starting value
            target_value: Target value to count to
            label: Counter label
            prefix: Text prefix (e.g., "$")
            suffix: Text suffix (e.g., "%")
            animation_duration: Animation duration in seconds
        """
        self.current_value = current_value
        self.target_value = target_value
        self.label = label
        self.prefix = prefix
        self.suffix = suffix
        self.animation_duration = animation_duration
    
    def render(self, container: Optional[Any] = None, animate: bool = True):
        """Render the counter widget."""
        target = container or st
        
        if animate and self.current_value != self.target_value:
            # Create placeholder for animated counting
            placeholder = target.empty()
            
            # Calculate animation steps
            steps = 20
            step_size = (self.target_value - self.current_value) / steps
            step_duration = self.animation_duration / steps
            
            for i in range(steps + 1):
                current = self.current_value + (step_size * i)
                if isinstance(self.target_value, int):
                    current = int(current)
                
                placeholder.metric(
                    label=self.label,
                    value=f"{self.prefix}{current:,}{self.suffix}"
                )
                
                if i < steps:
                    time.sleep(step_duration)
        else:
            # Static display
            target.metric(
                label=self.label,
                value=f"{self.prefix}{self.target_value:,}{self.suffix}"
            )


# Convenience functions
def show_status(status: StatusType, label: str, description: Optional[str] = None):
    """Quick status indicator display."""
    indicator = StatusIndicator(status, label, description)
    indicator.render()


def show_progress(value: float, max_value: float = 100, label: Optional[str] = None):
    """Quick progress bar display."""
    progress = ProgressBar(value, max_value, label)
    progress.render()


def show_metric(value: Union[int, float, str], label: str, delta: Optional[Union[int, float]] = None):
    """Quick metric display."""
    metric = MetricDisplay(value, label, delta)
    metric.render()


def show_health(services: Dict[str, str], title: str = "System Health"):
    """Quick health status display."""
    # Convert string statuses to StatusType
    status_map = {
        'success': StatusType.SUCCESS,
        'warning': StatusType.WARNING,
        'error': StatusType.ERROR,
        'info': StatusType.INFO,
        'pending': StatusType.PENDING
    }
    
    converted_services = {
        name: status_map.get(status.lower(), StatusType.INFO)
        for name, status in services.items()
    }
    
    health = HealthStatus(converted_services, title=title)
    health.render()
