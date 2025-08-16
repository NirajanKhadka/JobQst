#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Dashboard - Simplified version to isolate key conflicts
"""

import streamlit as st
import logging
from pathlib import Path
import sys

# Page configuration MUST be first
st.set_page_config(
    page_title="Debug Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

def main():
    """Debug dashboard main function."""
    st.title("🔧 Debug Dashboard")
    st.markdown("Simplified dashboard to test for key conflicts")
    
    # Initialize session state
    if "selected_profile" not in st.session_state:
        st.session_state["selected_profile"] = "Nirajan"
    
    # Simple tabs
    tabs = st.tabs([
        "🔍 Test",
        "⚙️ Processing", 
        "🎛️ Orchestration"
    ])
    
    with tabs[0]:
        st.markdown("### 🔍 Test Tab")
        st.success("Basic tab working!")
        
        if st.button("Test Button 1", key="test_btn_1"):
            st.info("Button 1 clicked!")
            
        if st.button("Test Button 2", key="test_btn_2"):
            st.info("Button 2 clicked!")
    
    with tabs[1]:
        st.markdown("### ⚙️ Processing Tab")
        
        # Simple processing test without orchestration
        profile_name = st.session_state.get("selected_profile", "default")
        st.metric("Profile", profile_name)
        
        if st.button("🚀 Simple Process Test", key="simple_process"):
            st.success("Simple processing test successful!")
    
    with tabs[2]:
        st.markdown("### 🎛️ Orchestration Test")
        
        # Test orchestration component separately
        try:
            from src.dashboard.components.orchestration_component import (
                render_orchestration_control
            )
            profile_name = st.session_state.get("selected_profile", "default")
            render_orchestration_control(profile_name)
            
        except ImportError as e:
            st.error(f"Import Error: {e}")
        except Exception as e:
            st.error(f"Orchestration Error: {e}")
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
