"""
Reusable Chart Components

This module provides reusable Plotly chart widgets with consistent styling
and configuration for the dashboard.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod


class BaseChart(ABC):
    """Base class for all chart components with consistent styling."""
    
    DEFAULT_THEME = {
        'background_color': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'font_family': 'Arial, sans-serif',
        'font_color': '#2E3440',
        'grid_color': '#E5E7EB',
        'line_color': '#6B7280'
    }
    
    DEFAULT_COLORS = [
        '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
        '#06B6D4', '#84CC16', '#F97316', '#EC4899', '#6366F1'
    ]
    
    def __init__(self, 
                 title: str = "",
                 theme: Optional[Dict] = None,
                 colors: Optional[List[str]] = None,
                 height: int = 400,
                 width: Optional[int] = None):
        """
        Initialize base chart with common properties.
        
        Args:
            title: Chart title
            theme: Custom theme dictionary
            colors: Custom color palette
            height: Chart height in pixels
            width: Chart width in pixels
        """
        self.title = title
        self.theme = {**self.DEFAULT_THEME, **(theme or {})}
        self.colors = colors or self.DEFAULT_COLORS
        self.height = height
        self.width = width
        
    def apply_theme(self, fig: go.Figure) -> go.Figure:
        """Apply consistent theme styling to figure."""
        fig.update_layout(
            title={
                'text': self.title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16, 'color': self.theme['font_color']}
            },
            plot_bgcolor=self.theme['background_color'],
            paper_bgcolor=self.theme['paper_bgcolor'],
            font={'family': self.theme['font_family'], 'color': self.theme['font_color']},
            height=self.height,
            width=self.width,
            margin={'l': 40, 'r': 40, 't': 60, 'b': 40},
            hovermode='closest'
        )
        
        fig.update_xaxes(
            gridcolor=self.theme['grid_color'],
            linecolor=self.theme['line_color']
        )
        
        fig.update_yaxes(
            gridcolor=self.theme['grid_color'],
            linecolor=self.theme['line_color']
        )
        
        return fig
    
    @abstractmethod
    def create_chart(self, data: pd.DataFrame, **kwargs) -> go.Figure:
        """Create the specific chart type."""
        pass
    
    def render(self, data: pd.DataFrame, container: Optional[Any] = None, **kwargs) -> go.Figure:
        """Render the chart in Streamlit."""
        fig = self.create_chart(data, **kwargs)
        fig = self.apply_theme(fig)
        
        if container:
            container.plotly_chart(fig, use_container_width=True)
        else:
            st.plotly_chart(fig, use_container_width=True)
            
        return fig


class LineChart(BaseChart):
    """Reusable line chart component."""
    
    def create_chart(self, 
                    data: pd.DataFrame, 
                    x: str, 
                    y: str, 
                    color: Optional[str] = None,
                    line_shape: str = 'linear',
                    markers: bool = False,
                    **kwargs) -> go.Figure:
        """
        Create a line chart.
        
        Args:
            data: DataFrame with chart data
            x: Column name for x-axis
            y: Column name for y-axis  
            color: Column name for color grouping
            line_shape: Line shape ('linear', 'spline', 'hv', 'vh')
            markers: Whether to show markers
        """
        fig = px.line(
            data, 
            x=x, 
            y=y, 
            color=color,
            color_discrete_sequence=self.colors,
            line_shape=line_shape,
            markers=markers,
            **kwargs
        )
        
        return fig


class BarChart(BaseChart):
    """Reusable bar chart component."""
    
    def create_chart(self, 
                    data: pd.DataFrame, 
                    x: str, 
                    y: str, 
                    color: Optional[str] = None,
                    orientation: str = 'v',
                    text_auto: bool = True,
                    **kwargs) -> go.Figure:
        """
        Create a bar chart.
        
        Args:
            data: DataFrame with chart data
            x: Column name for x-axis
            y: Column name for y-axis
            color: Column name for color grouping
            orientation: Chart orientation ('v' for vertical, 'h' for horizontal)
            text_auto: Whether to auto-display text on bars
        """
        fig = px.bar(
            data,
            x=x,
            y=y,
            color=color,
            color_discrete_sequence=self.colors,
            orientation=orientation,
            text_auto=text_auto,
            **kwargs
        )
        
        return fig


class PieChart(BaseChart):
    """Reusable pie chart component."""
    
    def create_chart(self, 
                    data: pd.DataFrame, 
                    values: str, 
                    names: str,
                    hole: float = 0.0,
                    **kwargs) -> go.Figure:
        """
        Create a pie chart.
        
        Args:
            data: DataFrame with chart data
            values: Column name for values
            names: Column name for labels
            hole: Size of center hole (0.0 for pie, >0 for donut)
        """
        fig = px.pie(
            data,
            values=values,
            names=names,
            color_discrete_sequence=self.colors,
            hole=hole,
            **kwargs
        )
        
        return fig


class ScatterChart(BaseChart):
    """Reusable scatter plot component."""
    
    def create_chart(self, 
                    data: pd.DataFrame, 
                    x: str, 
                    y: str, 
                    color: Optional[str] = None,
                    size: Optional[str] = None,
                    hover_data: Optional[List[str]] = None,
                    **kwargs) -> go.Figure:
        """
        Create a scatter plot.
        
        Args:
            data: DataFrame with chart data
            x: Column name for x-axis
            y: Column name for y-axis
            color: Column name for color grouping
            size: Column name for marker size
            hover_data: Additional columns to show on hover
        """
        fig = px.scatter(
            data,
            x=x,
            y=y,
            color=color,
            size=size,
            color_discrete_sequence=self.colors,
            hover_data=hover_data,
            **kwargs
        )
        
        return fig


class HeatmapChart(BaseChart):
    """Reusable heatmap component."""
    
    def create_chart(self, 
                    data: pd.DataFrame, 
                    x: Optional[str] = None, 
                    y: Optional[str] = None, 
                    z: Optional[str] = None,
                    colorscale: str = 'Blues',
                    **kwargs) -> go.Figure:
        """
        Create a heatmap.
        
        Args:
            data: DataFrame with chart data or correlation matrix
            x: Column name for x-axis (optional for correlation matrix)
            y: Column name for y-axis (optional for correlation matrix)
            z: Column name for values (optional for correlation matrix)
            colorscale: Color scale for heatmap
        """
        if x and y and z:
            # Pivot data for heatmap
            pivot_data = data.pivot(index=y, columns=x, values=z)
        else:
            # Use data as correlation matrix
            pivot_data = data
            
        fig = px.imshow(
            pivot_data,
            color_continuous_scale=colorscale,
            aspect='auto',
            **kwargs
        )
        
        return fig


class GaugeChart(BaseChart):
    """Reusable gauge chart component."""
    
    def create_chart(self, 
                    value: float, 
                    min_value: float = 0, 
                    max_value: float = 100,
                    threshold_ranges: Optional[List[Dict]] = None,
                    **kwargs) -> go.Figure:
        """
        Create a gauge chart.
        
        Args:
            value: Current value to display
            min_value: Minimum value for gauge
            max_value: Maximum value for gauge
            threshold_ranges: List of {'range': [min, max], 'color': 'color'} dicts
        """
        if not threshold_ranges:
            threshold_ranges = [
                {'range': [min_value, max_value * 0.6], 'color': '#10B981'},
                {'range': [max_value * 0.6, max_value * 0.8], 'color': '#F59E0B'},
                {'range': [max_value * 0.8, max_value], 'color': '#EF4444'}
            ]
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [min_value, max_value]},
                'bar': {'color': self.colors[0]},
                'steps': [
                    {'range': r['range'], 'color': r['color']} 
                    for r in threshold_ranges
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value * 0.9
                }
            }
        ))
        
        return fig


# Convenience functions for quick chart creation
def quick_line_chart(data: pd.DataFrame, x: str, y: str, title: str = "", **kwargs):
    """Quick line chart creation."""
    chart = LineChart(title=title)
    return chart.render(data, x=x, y=y, **kwargs)


def quick_bar_chart(data: pd.DataFrame, x: str, y: str, title: str = "", **kwargs):
    """Quick bar chart creation."""
    chart = BarChart(title=title)
    return chart.render(data, x=x, y=y, **kwargs)


def quick_pie_chart(data: pd.DataFrame, values: str, names: str, title: str = "", **kwargs):
    """Quick pie chart creation."""
    chart = PieChart(title=title)
    return chart.render(data, values=values, names=names, **kwargs)
