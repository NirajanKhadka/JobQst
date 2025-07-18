import streamlit as st
from typing import List


def render_sidebar(available_profiles: List[str]) -> str:
    st.sidebar.title("🎛️ Dashboard Controls")
    selected_profile = ""
    if available_profiles:
        selected_profile = st.sidebar.selectbox("Select Profile", available_profiles, index=0)
        st.session_state["selected_profile"] = selected_profile
    else:
        st.sidebar.warning("No profiles found")
    st.sidebar.markdown("### ⚡ Quick Actions")
    if st.button("🔍 Start Scraping"):
        st.info("Scraping functionality would be triggered here")
    if st.button("📝 Apply to Jobs"):
        st.info("Application functionality would be triggered here")
    return selected_profile
