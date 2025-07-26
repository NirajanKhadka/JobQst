"""
Sidebar component for the AutoJobAgent Dashboard.

This module provides sidebar functionality including profile selection,
quick actions, and navigation controls for the Streamlit dashboard.
"""

from typing import List, Optional
import streamlit as st


def render_sidebar(available_profiles: List[str]) -> Optional[str]:
    """
    Render the dashboard sidebar with profile selection and quick actions.
    
    Args:
        available_profiles: List of available user profiles to select from
        
    Returns:
        Selected profile name, or None if no profiles available
        
    Side Effects:
        - Updates streamlit session state with selected profile
        - Renders sidebar elements directly to Streamlit
    """
    st.sidebar.title("🎛️ Dashboard Controls")
    
    selected_profile: Optional[str] = None
    
    if available_profiles:
        selected_profile = st.sidebar.selectbox(
            "Select Profile", 
            available_profiles, 
            index=0,
            help="Choose which user profile to display data for"
        )
        if selected_profile:
            st.session_state["selected_profile"] = selected_profile
    else:
        st.sidebar.warning("No profiles found")
    
    # Quick Actions Section
    st.sidebar.markdown("### ⚡ Quick Actions")
    
    if st.sidebar.button("🔍 Start Scraping", help="Trigger job scraping process"):
        st.info("Scraping functionality would be triggered here")
    
    if st.sidebar.button("📝 Apply to Jobs", help="Start job application process"):
        st.info("Application functionality would be triggered here")
    
    return selected_profile
