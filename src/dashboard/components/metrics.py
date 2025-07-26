"""
Metrics component for the AutoJobAgent Dashboard.

This module provides job metrics display functionality, calculating and showing
key statistics like total jobs, applications, and match scores.
"""

from typing import Dict, Any
import streamlit as st
import pandas as pd


def render_metrics(df: pd.DataFrame) -> None:
    """
    Render key metrics section displaying job statistics.
    
    Args:
        df: DataFrame containing job data with columns like 'status' and 'match_score'
        
    Returns:
        None: Renders metrics directly to Streamlit
        
    Note:
        Handles missing columns gracefully by defaulting to 0 values.
        Converts non-numeric match scores to numeric values safely.
    """
    st.subheader("📊 Key Metrics")
    
    # Calculate metrics with error handling
    metrics = _calculate_job_metrics(df)
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", metrics["total_jobs"])
    with col2:
        st.metric("Applied", metrics["applied_jobs"])
    with col3:
        st.metric("Pending", metrics["pending_jobs"])
    with col4:
        st.metric("Avg Match Score", f"{metrics['avg_match_score']:.1f}%")


def _calculate_job_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate job metrics from DataFrame with error handling.
    
    Args:
        df: DataFrame containing job data
        
    Returns:
        Dictionary containing calculated metrics
    """
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
    
    return {
        "total_jobs": total_jobs,
        "applied_jobs": applied_jobs,
        "pending_jobs": pending_jobs,
        "avg_match_score": avg_match_score,
    }
