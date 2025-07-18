import streamlit as st
import pandas as pd


def render_metrics(df: pd.DataFrame):
    st.subheader("📊 Key Metrics")
    total_jobs = len(df) if not df.empty else 0
    # Handle missing 'status' column gracefully
    if not df.empty and "status" in df.columns:
        applied_jobs = len(df[df["status"] == "applied"])
        pending_jobs = len(df[df["status"] == "pending"])
    else:
        applied_jobs = 0
        pending_jobs = 0

    # Handle missing or non-numeric 'match_score' gracefully
    if not df.empty and "match_score" in df.columns:
        # Convert to numeric, coerce errors to NaN, then take mean (ignoring NaN)
        avg_match_score = pd.to_numeric(df["match_score"], errors="coerce").mean()
        if pd.isna(avg_match_score):
            avg_match_score = 0
    else:
        avg_match_score = 0
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Jobs", total_jobs)
    with col2:
        st.metric("Applied", applied_jobs)
    with col3:
        st.metric("Pending", pending_jobs)
    with col4:
        st.metric("Avg Match Score", f"{avg_match_score:.1f}%")
