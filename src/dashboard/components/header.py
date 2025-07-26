"""
Header component for the AutoJobAgent Dashboard.

This module provides the main header rendering functionality for the Streamlit dashboard,
displaying the application title and description in a styled format.
"""

from typing import Optional
import streamlit as st


def render_header(title: Optional[str] = None, subtitle: Optional[str] = None) -> None:
    """
    Render the main dashboard header with title and subtitle.
    
    Args:
        title: Custom title to display. Defaults to "🤖 AutoJobAgent Dashboard"
        subtitle: Custom subtitle to display. Defaults to "Intelligent Job Application Automation System"
    
    Returns:
        None: Renders directly to Streamlit
    """
    default_title = "🤖 AutoJobAgent Dashboard"
    default_subtitle = "Intelligent Job Application Automation System"
    
    display_title = title or default_title
    display_subtitle = subtitle or default_subtitle
    
    st.markdown(
        f"""
    <div class="main-header">
        <h1>{display_title}</h1>
        <p>{display_subtitle}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
