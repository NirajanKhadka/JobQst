"""
Metric Cards Components

This module provides reusable metric card components including KPI cards,
trend cards, comparison cards, and animated counters for the dashboard.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any, Union, Literal
import time
from datetime import datetime, timedelta
import pandas as pd


class MetricCard:
    """Base metric card component."""
    
    def __init__(self,
                 title: str,
                 value: Union[int, float, str],
                 subtitle: Optional[str] = None,
                 delta: Optional[Union[int, float]] = None,
                 delta_label: Optional[str] = None,
                 icon: Optional[str] = None,
                 color: str = "#3B82F6",
                 background_color: str = "#F8FAFC",
                 border_color: str = "#E2E8F0"):
        """
        Initialize metric card.
        
        Args:
            title: Card title
            value: Main metric value
            subtitle: Optional subtitle
            delta: Change value
            delta_label: Label for delta (e.g., "vs last month")
            icon: Unicode icon or emoji
            color: Primary color for accents
            background_color: Card background color
            border_color: Card border color
        """
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.delta = delta
        self.delta_label = delta_label
        self.icon = icon
        self.color = color
        self.background_color = background_color
        self.border_color = border_color
    
    def render(self, container: Optional[Any] = None):
        """Render the metric card."""
        target = container or st
        
        # Determine delta color and arrow
        delta_color = "#10B981" if self.delta and self.delta > 0 else "#EF4444" if self.delta and self.delta < 0 else "#6B7280"
        delta_arrow = "↗" if self.delta and self.delta > 0 else "↘" if self.delta and self.delta < 0 else ""
        
        # Format delta text
        delta_text = ""
        if self.delta is not None:
            delta_text = f"""
            <div style="
                color: {delta_color};
                font-size: 14px;
                margin-top: 4px;
            ">
                {delta_arrow} {self.delta:+.1f}{' ' + self.delta_label if self.delta_label else ''}
            </div>
            """
        
        # Icon display
        icon_html = ""
        if self.icon:
            icon_html = f"""
            <div style="
                font-size: 24px;
                margin-bottom: 8px;
            ">
                {self.icon}
            </div>
            """
        
        # Card HTML
        card_html = f"""
        <div style="
            background-color: {self.background_color};
            border: 1px solid {self.border_color};
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        ">
            {icon_html}
            <div style="
                color: #374151;
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 4px;
            ">
                {self.title}
            </div>
            <div style="
                color: {self.color};
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 4px;
            ">
                {self.value}
            </div>
            {f'<div style="color: #6B7280; font-size: 12px;">{self.subtitle}</div>' if self.subtitle else ''}
            {delta_text}
        </div>
        """
        
        target.markdown(card_html, unsafe_allow_html=True)


class KPICard(MetricCard):
    """Key Performance Indicator card with Improved formatting."""
    
    def __init__(self,
                 title: str,
                 value: Union[int, float],
                 target: Optional[Union[int, float]] = None,
                 unit: str = "",
                 format_string: str = "{:,.0f}",
                 **kwargs):
        """
        Initialize KPI card.
        
        Args:
            title: KPI title
            value: Current KPI value
            target: Target value (optional)
            unit: Unit of measurement
            format_string: Value formatting string
            **kwargs: Additional MetricCard arguments
        """
        formatted_value = format_string.format(value) + unit
        
        # Calculate progress if target is provided
        delta = None
        delta_label = None
        if target:
            delta = ((value / target) - 1) * 100
            delta_label = f"of {format_string.format(target)}{unit} target"
        
        super().__init__(
            title=title,
            value=formatted_value,
            delta=delta,
            delta_label=delta_label,
            **kwargs
        )
        
        self.raw_value = value
        self.target = target


class TrendCard:
    """Trend card with mini chart."""
    
    def __init__(self,
                 title: str,
                 current_value: Union[int, float],
                 trend_data: List[Union[int, float]],
                 trend_labels: Optional[List[str]] = None,
                 unit: str = "",
                 format_string: str = "{:,.0f}",
                 color: str = "#3B82F6",
                 positive_trend_color: str = "#10B981",
                 negative_trend_color: str = "#EF4444"):
        """
        Initialize trend card.
        
        Args:
            title: Card title
            current_value: Current value
            trend_data: List of historical values
            trend_labels: Labels for trend data points
            unit: Unit of measurement
            format_string: Value formatting string
            color: Primary color
            positive_trend_color: Color for positive trends
            negative_trend_color: Color for negative trends
        """
        self.title = title
        self.current_value = current_value
        self.trend_data = trend_data
        self.trend_labels = trend_labels or [f"Period {i+1}" for i in range(len(trend_data))]
        self.unit = unit
        self.format_string = format_string
        self.color = color
        self.positive_trend_color = positive_trend_color
        self.negative_trend_color = negative_trend_color
    
    def _create_mini_chart(self) -> go.Figure:
        """Create mini trend chart."""
        # Determine trend direction
        trend_direction = 1 if len(self.trend_data) >= 2 and self.trend_data[-1] > self.trend_data[0] else -1
        line_color = self.positive_trend_color if trend_direction > 0 else self.negative_trend_color
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=self.trend_labels,
            y=self.trend_data,
            mode='lines+markers',
            line=dict(color=line_color, width=2),
            marker=dict(size=4, color=line_color),
            hovertemplate='%{y}<extra></extra>'
        ))
        
        fig.update_layout(
            height=80,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        
        return fig
    
    def render(self, container: Optional[Any] = None):
        """Render the trend card."""
        target = container or st
        
        with target.container():
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Value and title
                st.markdown(f"""
                <div style="padding: 16px;">
                    <div style="color: #374151; font-size: 14px; font-weight: 500; margin-bottom: 4px;">
                        {self.title}
                    </div>
                    <div style="color: {self.color}; font-size: 24px; font-weight: 700;">
                        {self.format_string.format(self.current_value)}{self.unit}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Mini chart
                fig = self._create_mini_chart()
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


class ComparisonCard:
    """Comparison card showing multiple metrics."""
    
    def __init__(self,
                 title: str,
                 metrics: List[Dict[str, Union[str, int, float]]],
                 comparison_type: Literal["value", "percentage"] = "value"):
        """
        Initialize comparison card.
        
        Args:
            title: Card title
            metrics: List of metric dictionaries with 'label', 'value', and optional 'color'
            comparison_type: Type of comparison display
        """
        self.title = title
        self.metrics = metrics
        self.comparison_type = comparison_type
    
    def render(self, container: Optional[Any] = None):
        """Render the comparison card."""
        target = container or st
        
        with target.container():
            st.markdown(f"**{self.title}**")
            
            # Calculate max value for percentage comparison
            max_value = max(metric['value'] for metric in self.metrics) if self.comparison_type == "percentage" else 1
            
            for metric in self.metrics:
                label = metric['label']
                value = metric['value']
                color = metric.get('color', '#3B82F6')
                
                if self.comparison_type == "percentage":
                    percentage = (value / max_value) * 100 if max_value > 0 else 0
                    st.markdown(f"""
                    <div style="margin: 8px 0;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="font-size: 14px;">{label}</span>
                            <span style="font-size: 14px; font-weight: 600;">{value:,.0f}</span>
                        </div>
                        <div style="background-color: #E5E7EB; border-radius: 4px; height: 8px;">
                            <div style="
                                background-color: {color};
                                width: {percentage}%;
                                height: 100%;
                                border-radius: 4px;
                            "></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.metric(label, f"{value:,.0f}")


class AnimatedCounter:
    """Animated counter component."""
    
    def __init__(self,
                 title: str,
                 start_value: Union[int, float],
                 end_value: Union[int, float],
                 duration: float = 2.0,
                 prefix: str = "",
                 suffix: str = "",
                 format_string: str = "{:,.0f}"):
        """
        Initialize animated counter.
        
        Args:
            title: Counter title
            start_value: Starting value
            end_value: Ending value
            duration: Animation duration in seconds
            prefix: Value prefix
            suffix: Value suffix
            format_string: Value formatting
        """
        self.title = title
        self.start_value = start_value
        self.end_value = end_value
        self.duration = duration
        self.prefix = prefix
        self.suffix = suffix
        self.format_string = format_string
    
    def render(self, container: Optional[Any] = None, animate: bool = True):
        """Render the animated counter."""
        target = container or st
        
        if animate and self.start_value != self.end_value:
            placeholder = target.empty()
            
            steps = 30
            step_value = (self.end_value - self.start_value) / steps
            step_duration = self.duration / steps
            
            for i in range(steps + 1):
                current_value = self.start_value + (step_value * i)
                
                if isinstance(self.end_value, int):
                    current_value = int(current_value)
                
                formatted_value = f"{self.prefix}{self.format_string.format(current_value)}{self.suffix}"
                
                placeholder.metric(
                    label=self.title,
                    value=formatted_value
                )
                
                if i < steps:
                    time.sleep(step_duration)
        else:
            formatted_value = f"{self.prefix}{self.format_string.format(self.end_value)}{self.suffix}"
            target.metric(
                label=self.title,
                value=formatted_value
            )


class StatusCard:
    """Status card with health indicators."""
    
    def __init__(self,
                 title: str,
                 status: Literal["healthy", "warning", "error", "unknown"],
                 details: Optional[str] = None,
                 last_updated: Optional[datetime] = None):
        """
        Initialize status card.
        
        Args:
            title: Card title
            status: Status level
            details: Status details
            last_updated: Last update timestamp
        """
        self.title = title
        self.status = status
        self.details = details
        self.last_updated = last_updated or datetime.now()
        
        # Status configuration
        self.status_config = {
            "healthy": {"color": "#10B981", "icon": "✅", "label": "Healthy"},
            "warning": {"color": "#F59E0B", "icon": "⚠️", "label": "Warning"},
            "error": {"color": "#EF4444", "icon": "❌", "label": "Error"},
            "unknown": {"color": "#6B7280", "icon": "❓", "label": "Unknown"}
        }
    
    def render(self, container: Optional[Any] = None):
        """Render the status card."""
        target = container or st
        
        config = self.status_config[self.status]
        
        # Format last updated
        time_ago = datetime.now() - self.last_updated
        if time_ago.days > 0:
            time_str = f"{time_ago.days} days ago"
        elif time_ago.seconds > 3600:
            hours = time_ago.seconds // 3600
            time_str = f"{hours} hours ago"
        elif time_ago.seconds > 60:
            minutes = time_ago.seconds // 60
            time_str = f"{minutes} minutes ago"
        else:
            time_str = "Just now"
        
        status_html = f"""
        <div style="
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-left: 4px solid {config['color']};
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 20px; margin-right: 8px;">{config['icon']}</span>
                <div>
                    <div style="font-weight: 600; color: #374151;">{self.title}</div>
                    <div style="color: {config['color']}; font-size: 14px;">{config['label']}</div>
                </div>
            </div>
            {f'<div style="color: #6B7280; font-size: 14px; margin-bottom: 8px;">{self.details}</div>' if self.details else ''}
            <div style="color: #9CA3AF; font-size: 12px;">Last updated: {time_str}</div>
        </div>
        """
        
        target.markdown(status_html, unsafe_allow_html=True)


# Convenience functions
def show_metric_card(title: str, value: Union[int, float, str], **kwargs):
    """Quick metric card display."""
    card = MetricCard(title, value, **kwargs)
    card.render()


def show_kpi_card(title: str, value: Union[int, float], target: Optional[Union[int, float]] = None, **kwargs):
    """Quick KPI card display."""
    card = KPICard(title, value, target, **kwargs)
    card.render()


def show_trend_card(title: str, current_value: Union[int, float], trend_data: List[Union[int, float]], **kwargs):
    """Quick trend card display."""
    card = TrendCard(title, current_value, trend_data, **kwargs)
    card.render()


def show_status_card(title: str, status: str, details: Optional[str] = None):
    """Quick status card display."""
    card = StatusCard(title, status, details)
    card.render()
