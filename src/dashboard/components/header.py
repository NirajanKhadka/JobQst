import streamlit as st


def render_header():
    st.markdown(
        """
    <div class=\"main-header\">
        <h1>🤖 AutoJobAgent Dashboard</h1>
        <p>Intelligent Job Application Automation System</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
