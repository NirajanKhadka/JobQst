#!/usr/bin/env python3
"""
Core Styling Module
Handles CSS loading and styling utilities for the dashboard.
"""

from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_unified_css() -> str:
    """Load the unified CSS from the external file."""
    css_path = Path(__file__).parent.parent / "styles" / "unified_dashboard_styles.css"
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        return f"<style>\n{css_content}\n</style>"
    except FileNotFoundError:
        logger.warning("Unified CSS file not found, using fallback")
        return get_fallback_css()


def get_fallback_css() -> str:
    """Fallback CSS when main file is not found."""
    return """
    <style>
    /* Fallback CSS - Unified styles file not found */
    .stApp { 
        background: #0f172a !important; 
        color: #f1f5f9 !important; 
    }
    .main { 
        background: #0f172a !important; 
        color: #f1f5f9 !important; 
    }
    .stSidebar { 
        background: #334155 !important; 
    }
    .stButton > button { 
        background: #3b82f6 !important; 
        color: white !important; 
        border-radius: 0.5rem !important; 
    }
    .section-header { 
        color: #f1f5f9; 
        border-bottom: 2px solid #3b82f6; 
    }
    </style>
    """


def get_status_color(status: str) -> str:
    """Get color for job status."""
    status_colors = {
        "scraped": "#3b82f6",
        "processed": "#10b981", 
        "applied": "#8b5cf6",
        "interview": "#f59e0b",
        "rejected": "#ef4444",
        "hired": "#059669"
    }
    return status_colors.get(status.lower(), "#64748b")


def format_status_display(status: str) -> dict:
    """Format status for display with color and icon."""
    status_config = {
        "scraped": {"icon": "🔍", "color": "#3b82f6", "label": "Scraped"},
        "processed": {"icon": "⚡", "color": "#10b981", "label": "Processed"},
        "applied": {"icon": "📋", "color": "#8b5cf6", "label": "Applied"},
        "interview": {"icon": "💼", "color": "#f59e0b", "label": "Interview"},
        "rejected": {"icon": "❌", "color": "#ef4444", "label": "Rejected"},
        "hired": {"icon": "🎉", "color": "#059669", "label": "Hired"}
    }
    
    default = {"icon": "📄", "color": "#64748b", "label": status.title()}
    return status_config.get(status.lower(), default)
