#!/usr/bin/env python3
"""
Jobs Tab Module
Handles the main jobs display and management functionality.
"""

import streamlit as st
import pandas as pd
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.core.styling import format_status_display

logger = logging.getLogger(__name__)


def render_jobs_tab(df: pd.DataFrame, profile_name: str) -> None:
    """Render the jobs tab with job cards and table."""
    
    if df.empty:
        render_empty_jobs_state()
        return
    
    # Jobs overview metrics
    render_jobs_overview(df)
    
    # Job filters
    filtered_df = render_job_filters(df)
    
    # Display options
    display_mode = st.radio(
        "Display Mode", 
        ["Cards", "Table"], 
        horizontal=True,
        key="jobs_display_mode"
    )
    
    if display_mode == "Cards":
        render_job_cards(filtered_df)
    else:
        render_jobs_table(filtered_df, profile_name)


def render_empty_jobs_state():
    """Render empty state when no jobs are available."""
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem; 
                background: #1e293b; border-radius: 1rem; 
                border: 1px solid #334155;'>
        <div style='font-size: 4rem; margin-bottom: 1rem;'>💼</div>
        <h3 style='color: #f1f5f9; margin-bottom: 1rem;'>No Jobs Found</h3>
        <p style='color: #cbd5e1; margin-bottom: 2rem;'>
            Start scraping jobs to see them here.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_jobs_overview(df: pd.DataFrame) -> None:
    """Render jobs overview metrics."""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Calculate metrics
    total_jobs = len(df)
    applied_jobs = len(df[df.get('applied', 0) == 1]) if 'applied' in df.columns else 0
    companies = df['company'].nunique() if 'company' in df.columns else 0
    
    # Recent jobs (last 7 days)
    if 'scraped_at' in df.columns:
        recent_jobs = len(df[
            pd.to_datetime(df['scraped_at'], errors='coerce') >= 
            pd.Timestamp.now() - pd.Timedelta(days=7)
        ])
    else:
        recent_jobs = 0
    
    # Average match score
    avg_match = df['match_score'].mean() if 'match_score' in df.columns else 0
    
    metrics = [
        ("📊", "Total Jobs", total_jobs, "#3b82f6"),
        ("✅", "Applied", applied_jobs, "#10b981"),
        ("🏢", "Companies", companies, "#f59e0b"),
        ("📅", "Recent (7d)", recent_jobs, "#8b5cf6"),
        ("🎯", "Avg Match", f"{avg_match:.1f}%", "#ef4444")
    ]
    
    for i, (icon, label, value, color) in enumerate(metrics):
        with [col1, col2, col3, col4, col5][i]:
            st.markdown(f"""
            <div style='background: #1e293b; padding: 1.5rem; 
                        border-radius: 0.75rem; border: 1px solid #334155; 
                        text-align: center;'>
                <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>{icon}</div>
                <div style='color: {color}; font-size: 1.75rem; 
                           font-weight: 700; font-family: monospace; 
                           margin-bottom: 0.5rem;'>{value}</div>
                <div style='color: #cbd5e1; font-size: 0.875rem; 
                           font-weight: 500; text-transform: uppercase; 
                           letter-spacing: 0.05em;'>{label}</div>
            </div>
            """, unsafe_allow_html=True)


def render_job_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render job filters and return filtered dataframe."""
    
    st.markdown("### 🔍 Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Status filter
        status_options = ["All"] + list(df['status'].unique()) if 'status' in df.columns else ["All"]
        selected_status = st.selectbox("Status", status_options, key="job_status_filter")
    
    with col2:
        # Company filter
        company_options = ["All"] + sorted(df['company'].dropna().unique()) if 'company' in df.columns else ["All"]
        selected_company = st.selectbox("Company", company_options[:20], key="job_company_filter")
    
    with col3:
        # Applied filter
        applied_filter = st.selectbox("Applied Status", ["All", "Applied", "Not Applied"], key="job_applied_filter")
    
    with col4:
        # Search
        search_term = st.text_input("Search Jobs", key="job_search_filter")
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df['status'] == selected_status]
    
    if selected_company != "All":
        filtered_df = filtered_df[filtered_df['company'] == selected_company]
    
    if applied_filter == "Applied":
        filtered_df = filtered_df[filtered_df.get('applied', 0) == 1]
    elif applied_filter == "Not Applied":
        filtered_df = filtered_df[filtered_df.get('applied', 0) == 0]
    
    if search_term:
        mask = (
            filtered_df['title'].str.contains(search_term, case=False, na=False) |
            filtered_df['company'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    st.info(f"Showing {len(filtered_df)} of {len(df)} jobs")
    
    return filtered_df


def render_job_cards(df: pd.DataFrame, limit: int = 12) -> None:
    """Render jobs as cards."""
    
    st.markdown("### 💼 Job Cards")
    
    # Pagination
    page_size = limit
    total_pages = (len(df) + page_size - 1) // page_size
    
    if total_pages > 1:
        page = st.slider("Page", 1, total_pages, 1, key="job_cards_page")
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        display_df = df.iloc[start_idx:end_idx]
    else:
        display_df = df.head(limit)
    
    # Display cards in grid
    cols = st.columns(3)
    
    for idx, (_, job) in enumerate(display_df.iterrows()):
        col_idx = idx % 3
        
        with cols[col_idx]:
            render_single_job_card(job)


def render_single_job_card(job: pd.Series) -> None:
    """Render a single job card."""
    
    status_info = format_status_display(job.get('status', 'scraped'))
    match_score = job.get('match_score', 0)
    
    # Determine card border color based on match score
    if match_score >= 80:
        border_color = "#10b981"  # Green
    elif match_score >= 60:
        border_color = "#f59e0b"  # Yellow
    else:
        border_color = "#334155"  # Default
    
    st.markdown(f"""
    <div style='background: #1e293b; padding: 1.5rem; 
                border-radius: 1rem; border: 2px solid {border_color}; 
                margin-bottom: 1rem; height: 280px; 
                display: flex; flex-direction: column;'>
        
        <div style='display: flex; justify-content: space-between; 
                    align-items: center; margin-bottom: 1rem;'>
            <span style='background: {status_info["color"]}; 
                        color: white; padding: 0.25rem 0.75rem; 
                        border-radius: 1rem; font-size: 0.8rem;'>
                {status_info["icon"]} {status_info["label"]}
            </span>
            <span style='color: #f59e0b; font-weight: 600;'>
                {match_score}% match
            </span>
        </div>
        
        <h4 style='color: #f1f5f9; margin-bottom: 0.5rem; 
                   font-size: 1.1rem; line-height: 1.3;'>
            {job.get('title', 'No Title')[:50]}...
        </h4>
        
        <p style='color: #3b82f6; font-weight: 600; 
                  margin-bottom: 0.5rem;'>
            {job.get('company', 'Unknown Company')}
        </p>
        
        <p style='color: #cbd5e1; font-size: 0.9rem; 
                  margin-bottom: 1rem;'>
            📍 {job.get('location', 'Unknown Location')}
        </p>
        
        <div style='margin-top: auto; padding-top: 1rem;'>
            <small style='color: #94a3b8;'>
                ID: {job.get('id', 'N/A')} | 
                {job.get('scraped_at', 'Unknown date')[:10]}
            </small>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_jobs_table(df: pd.DataFrame, profile_name: str) -> None:
    """Render jobs as a data table."""
    
    st.markdown("### 📋 Jobs Table")
    
    # Configure display columns
    display_columns = [
        'id', 'title', 'company', 'location', 'status', 
        'match_score', 'applied', 'scraped_at'
    ]
    
    # Filter to available columns
    available_columns = [col for col in display_columns if col in df.columns]
    
    if not available_columns:
        st.error("No valid columns found in job data")
        return
    
    # Prepare display dataframe
    display_df = df[available_columns].copy()
    
    # Format columns for display
    if 'scraped_at' in display_df.columns:
        display_df['scraped_at'] = pd.to_datetime(
            display_df['scraped_at'], errors='coerce'
        ).dt.strftime('%Y-%m-%d %H:%M')
    
    if 'applied' in display_df.columns:
        display_df['applied'] = display_df['applied'].map({1: '✅', 0: '❌'})
    
    # Display table
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "title": st.column_config.TextColumn("Job Title", width="medium"),
            "company": st.column_config.TextColumn("Company", width="medium"),
            "location": st.column_config.TextColumn("Location", width="medium"),
            "status": st.column_config.TextColumn("Status", width="small"),
            "match_score": st.column_config.NumberColumn("Match %", width="small"),
            "applied": st.column_config.TextColumn("Applied", width="small"),
            "scraped_at": st.column_config.TextColumn("Scraped", width="medium"),
        }
    )
    
    st.caption(f"Showing {len(display_df)} jobs")
