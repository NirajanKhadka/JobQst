#!/usr/bin/env python3
"""
Dashboard Styling Component
Provides consistent styling and CSS for Improved dashboard UI.
Edits require explicit user request.
"""

import streamlit as st
from pathlib import Path

class DashboardStyling:
    """Provides consistent styling for dashboard components using the unified CSS system."""
    
    @staticmethod
    def load_unified_css():
        """Load the unified CSS from the external file."""
        css_path = Path(__file__).parent.parent / "styles" / "unified_dashboard_styles.css"
        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            return f"<style>\n{css_content}\n</style>"
        except FileNotFoundError:
            # Fallback to basic CSS if file not found
            return """
            <style>
            /* Fallback CSS - Unified styles file not found */
            .stApp { background: #0f172a !important; color: #f1f5f9 !important; }
            .main { background: #0f172a !important; color: #f1f5f9 !important; }
            .stSidebar { background: #334155 !important; }
            .stButton > button { background: #3b82f6 !important; color: white !important; border-radius: 0.5rem !important; }
            .section-header { color: #f1f5f9; border-bottom: 2px solid #3b82f6; }
            </style>
            """
    
    @staticmethod
    def apply_global_styles():
        """Apply global CSS styles to the dashboard using the unified CSS system."""
        unified_css = DashboardStyling.load_unified_css()
        st.markdown(unified_css, unsafe_allow_html=True)
        
        # Additional component-specific styles that extend the unified CSS
        st.markdown("""
        <style>
        /* Component-Specific Extensions - Edits require explicit user request */
        
        /* Improved metric containers for Streamlit */
        [data-testid="metric-container"] {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-color) !important;
            padding: var(--spacing-md);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm) !important;
            transition: var(--transition-normal) !important;
        }
        
        [data-testid="metric-container"]:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md) !important;
            border-color: var(--accent-primary) !important;
        }
        
        /* Improved expander styling */
        .streamlit-expanderHeader {
            background: var(--bg-secondary) !important;
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--border-color) !important;
            font-weight: 600 !important;
            color: var(--text-primary) !important;
            transition: var(--transition-normal) !important;
        }
        
        .streamlit-expanderHeader:hover {
            background: var(--bg-hover) !important;
            border-color: var(--accent-primary) !important;
        }
        
        .streamlit-expanderContent {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-color) !important;
            border-top: none !important;
            border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
        }
        
        /* Improved progress bars */
        .stProgress > div > div {
            background: var(--bg-secondary) !important;
            border-radius: var(--radius-lg) !important;
        }
        
        .stProgress > div > div > div {
            background: var(--accent-primary) !important;
            border-radius: var(--radius-lg) !important;
        }
        
        /* Improved form elements */
        .stSelectbox > div > div {
            background: var(--bg-input) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: var(--radius-md) !important;
            color: var(--text-primary) !important;
        }
        
        .stTextInput > div > div > input {
            background: var(--bg-input) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: var(--radius-md) !important;
            color: var(--text-primary) !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: var(--border-focus) !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        }
        
        /* Improved checkbox styling */
        .stCheckbox > label {
            font-weight: 600 !important;
            color: var(--text-primary) !important;
        }
        
        /* Improved container spacing */
        .element-container {
            margin-bottom: var(--spacing-md);
        }
        
        .main > div {
            padding-top: var(--spacing-md);
        }
        
        /* Component-specific utility classes */
        .component-card {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: var(--radius-lg) !important;
            padding: var(--spacing-lg);
            margin: var(--spacing-sm) 0;
            box-shadow: var(--shadow-sm) !important;
            transition: var(--transition-normal) !important;
        }
        
        .component-card:hover {
            transform: translateY(-2px) !important;
            box-shadow: var(--shadow-md) !important;
        }
        
        /* Improved status indicators */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: var(--spacing-xs);
            padding: var(--spacing-xs) var(--spacing-sm);
            border-radius: var(--radius-full);
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-indicator.running {
            background: var(--success-bg);
            color: var(--success);
            border: 1px solid var(--success);
        }
        
        .status-indicator.stopped {
            background: var(--error-bg);
            color: var(--error);
            border: 1px solid var(--error);
        }
        
        .status-indicator.warning {
            background: var(--warning-bg);
            color: var(--warning);
            border: 1px solid var(--warning);
        }
        
        /* Improved resource usage indicators */
        .resource-indicator {
            font-weight: 600;
        }
        
        .resource-indicator.low {
            color: var(--success) !important;
        }
        
        .resource-indicator.medium {
            color: var(--warning) !important;
        }
        
        .resource-indicator.high {
            color: var(--error) !important;
        }
        
        /* Improved gradient headers */
        .component-gradient-header {
            background: var(--gradient-primary) !important;
            padding: var(--spacing-md);
            border-radius: var(--radius-lg) !important;
            margin-bottom: var(--spacing-md);
            text-align: center;
        }
        
        .component-gradient-header h2, 
        .component-gradient-header p {
            color: var(--text-primary) !important;
            margin: 0;
        }
        
        /* Hide Streamlit branding */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header { visibility: hidden; }
        
        /* End Component-Specific Extensions */
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_gradient_header(title: str, subtitle: str, gradient_colors: str = "90deg, #1f77b4, #ff7f0e"):
        """Create a gradient header with title and subtitle."""
        return f"""
        <div style="background: linear-gradient({gradient_colors}); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <h2 style="color: white; margin: 0; text-align: center;">{title}</h2>
            <p style="color: white; margin: 0.5rem 0 0 0; text-align: center; opacity: 0.9;">
                {subtitle}
            </p>
        </div>
        """
    
    @staticmethod
    def create_status_badge(status: str, text: str = None):
        """Create a status badge with appropriate styling."""
        if text is None:
            text = status.title()
            
        color_map = {
            "running": "#28a745",
            "stopped": "#dc3545", 
            "healthy": "#28a745",
            "partial": "#ffc107",
            "error": "#dc3545",
            "warning": "#ffc107",
            "info": "#17a2b8"
        }
        
        color = color_map.get(status.lower(), "#6c757d")
        
        return f"""
        <span style="
            background-color: {color};
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.875rem;
            font-weight: 600;
            display: inline-block;
        ">{text}</span>
        """
    
    @staticmethod
    def create_metric_card(title: str, value: str, delta: str = None, color: str = "#007bff"):
        """Create an Improved metric card."""
        delta_html = ""
        if delta:
            delta_color = "#28a745" if not delta.startswith("-") else "#dc3545"
            delta_html = f'<p style="color: {delta_color}; margin: 0; font-size: 0.875rem;">{delta}</p>'
        
        return f"""
        <div style="
            background: white;
            border: 1px solid #dee2e6;
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h4 style="margin: 0; color: #495057;">{title}</h4>
            <h2 style="margin: 0.25rem 0; color: {color};">{value}</h2>
            {delta_html}
        </div>
        """
    
    @staticmethod
    def create_service_card(name: str, status: str, description: str, metrics: dict = None):
        """Create an Improved service card."""
        status_color = "#28a745" if status == "running" else "#dc3545"
        status_icon = "🟢" if status == "running" else "🔴"
        
        metrics_html = ""
        if metrics:
            metrics_html = "<div style='margin-top: 0.5rem;'>"
            for key, value in metrics.items():
                metrics_html += f"<small><strong>{key}:</strong> {value}</small><br>"
            metrics_html += "</div>"
        
        return f"""
        <div style="
            background: white;
            border: 1px solid #dee2e6;
            border-left: 4px solid {status_color};
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        ">
            <h4 style="margin: 0; color: #495057;">{status_icon} {name}</h4>
            <p style="margin: 0.25rem 0; color: #6c757d; font-size: 0.875rem;">{description}</p>
            <span style="
                background-color: {status_color};
                color: white;
                padding: 0.25rem 0.5rem;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
            ">{status.upper()}</span>
            {metrics_html}
        </div>
        """

# Global styling instance
dashboard_styling = DashboardStyling()