#!/usr/bin/env python3
"""
Modern Job Cards Component
Beautiful, UI-friendly job display with cards instead of basic tables
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

def render_modern_job_cards(df: pd.DataFrame, profile_name: str = "default") -> None:
    """
    Render jobs as beautiful, interactive cards with modern UI/UX.
    
    Args:
        df: DataFrame containing job data
        profile_name: Profile name for unique keys
    """
    if df.empty:
        render_empty_state()
        return
    
    # Add custom CSS for modern styling
    inject_custom_css()
    
    # Render filters and controls
    filtered_df = render_job_filters_modern(df)
    
    # Render job cards
    render_job_cards_grid(filtered_df, profile_name)

def inject_custom_css():
    """Inject custom CSS for modern job cards styling."""
    st.markdown("""
    <style>
    .job-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .job-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
    }
    
    .job-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 15px;
    }
    
    .job-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
        line-height: 1.3;
    }
    
    .job-company {
        font-size: 1.1rem;
        color: #e0e7ff;
        margin: 5px 0;
        font-weight: 500;
    }
    
    .job-location {
        font-size: 0.95rem;
        color: #c7d2fe;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    .job-status {
        background: rgba(255, 255, 255, 0.2);
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    .job-details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin: 15px 0;
    }
    
    .job-detail-item {
        background: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .job-detail-label {
        font-size: 0.8rem;
        color: #c7d2fe;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    
    .job-detail-value {
        font-size: 1rem;
        color: #ffffff;
        font-weight: 600;
    }
    
    .job-actions {
        display: flex;
        gap: 10px;
        margin-top: 15px;
        flex-wrap: wrap;
    }
    
    .job-action-btn {
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #ffffff;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    
    .job-action-btn:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: translateY(-1px);
    }
    
    .match-score {
        position: absolute;
        top: 15px;
        right: 15px;
        background: rgba(16, 185, 129, 0.9);
        color: white;
        padding: 8px 12px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 0.9rem;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    .salary-badge {
        background: linear-gradient(45deg, #f59e0b, #d97706);
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-top: 5px;
    }
    
    .remote-badge {
        background: linear-gradient(45deg, #10b981, #059669);
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .filter-container {
        background: rgba(15, 23, 42, 0.8);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid rgba(51, 65, 85, 0.5);
    }
    
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-bottom: 20px;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #1e293b, #334155);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid rgba(51, 65, 85, 0.5);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #3b82f6;
        margin-bottom: 5px;
    }
    
    .stat-label {
        color: #cbd5e1;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 20px;
        border: 1px solid rgba(51, 65, 85, 0.5);
    }
    
    .empty-icon {
        font-size: 4rem;
        margin-bottom: 20px;
    }
    
    .pagination-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
        margin-top: 30px;
        padding: 20px;
    }
    
    .pagination-btn {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: #3b82f6;
        padding: 10px 15px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .pagination-btn:hover {
        background: rgba(59, 130, 246, 0.2);
    }
    
    .pagination-btn.active {
        background: #3b82f6;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def render_empty_state():
    """Render beautiful empty state when no jobs are available."""
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">📭</div>
        <h2 style="color: #f1f5f9; margin-bottom: 10px;">No Jobs Found</h2>
        <p style="color: #cbd5e1; margin-bottom: 30px;">Start by scraping some job listings or adjust your filters.</p>
        <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
            <button class="job-action-btn" style="background: linear-gradient(135deg, #3b82f6, #6366f1);">
                🔍 Start Scraping
            </button>
            <button class="job-action-btn" style="background: rgba(51, 65, 85, 0.8);">
                ⚙️ Adjust Filters
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_job_filters_modern(df: pd.DataFrame) -> pd.DataFrame:
    """Render modern filter interface and return filtered dataframe."""
    
    # Job statistics - handle missing columns gracefully
    total_jobs = len(df)
    
    # Handle different possible column names for application status
    applied_jobs = 0
    for col in ['application_status', 'status_text', 'status']:
        if col in df.columns:
            # Use exact match for "applied" status, not substring match to avoid matching "not_applied"
            if col == 'application_status':
                applied_jobs = len(df[df[col].astype(str).str.lower() == 'applied'])
            else:
                applied_jobs = len(df[df[col].astype(str).str.lower() == 'applied'])
            break
    
    # Handle different possible column names for processing status
    processed_jobs = 0
    for col in ['status', 'status_text', 'processing_status']:
        if col in df.columns:
            processed_jobs = len(df[df[col].astype(str).str.contains('processed|Processed', case=False, na=False)])
            break
    
    # Handle match score
    high_match_jobs = 0
    if 'match_score' in df.columns:
        match_scores = pd.to_numeric(df['match_score'], errors='coerce').fillna(0)
        # Handle both 0-1 and 0-100 scales
        if match_scores.max() <= 1:
            high_match_jobs = len(df[match_scores >= 0.8])
        else:
            high_match_jobs = len(df[match_scores >= 80])
    
    # Statistics cards
    st.markdown("""
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-number">{}</div>
            <div class="stat-label">Total Jobs</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{}</div>
            <div class="stat-label">High Match</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{}</div>
            <div class="stat-label">Processed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{}</div>
            <div class="stat-label">Applied</div>
        </div>
    </div>
    """.format(total_jobs, high_match_jobs, processed_jobs, applied_jobs), unsafe_allow_html=True)
    
    # Filters in a modern container
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        st.markdown("### 🔍 **Configurable Filters**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Status filter
            status_options = ['All Status'] + list(df.get('status', pd.Series()).dropna().unique())
            selected_status = st.selectbox(
                "📊 Pipeline Status",
                status_options,
                key="modern_status_filter"
            )
        
        with col2:
            # Company filter
            companies = ['All Companies'] + sorted(df.get('company', pd.Series()).dropna().unique().tolist())
            selected_company = st.selectbox(
                "🏢 Company",
                companies,
                key="modern_company_filter"
            )
        
        with col3:
            # Match score filter
            match_score_options = [
                "All Scores",
                "Excellent (90%+)",
                "Great (80-89%)",
                "Good (70-79%)",
                "Fair (60-69%)",
                "Below 60%"
            ]
            selected_match = st.selectbox(
                "🎯 Match Score",
                match_score_options,
                key="modern_match_filter"
            )
        
        with col4:
            # Remote work filter
            remote_options = ['All Work Styles'] + sorted(df.get('remote_option', pd.Series()).dropna().unique().tolist())
            selected_remote = st.selectbox(
                "🏠 Work Style",
                remote_options,
                key="modern_remote_filter"
            )
        
        # Additional filters row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Search by job title
            search_term = st.text_input(
                "🔍 Search Jobs",
                placeholder="Search by title, company, or keywords...",
                key="modern_search"
            )
        
        with col2:
            # Salary filter
            has_salary = st.checkbox(
                "💰 Has Salary Info",
                key="modern_salary_filter"
            )
        
        with col3:
            # Date range
            date_options = ['All Time', 'Last 24 hours', 'Last 7 days', 'Last 30 days']
            selected_date = st.selectbox(
                "📅 Date Range",
                date_options,
                key="modern_date_filter"
            )
        
        with col4:
            # Sort options
            sort_options = [
                "Latest First",
                "Highest Match",
                "Company A-Z",
                "Salary High-Low"
            ]
            selected_sort = st.selectbox(
                "📈 Sort By",
                sort_options,
                key="modern_sort_filter"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered_df = df.copy()
    
    # Status filter
    if selected_status != 'All Status':
        filtered_df = filtered_df[filtered_df.get('status', '') == selected_status]
    
    # Company filter
    if selected_company != 'All Companies':
        filtered_df = filtered_df[filtered_df.get('company', '') == selected_company]
    
    # Match score filter
    if selected_match != "All Scores" and 'match_score' in filtered_df.columns:
        match_scores = filtered_df['match_score'].fillna(0)
        if selected_match == "Excellent (90%+)":
            filtered_df = filtered_df[match_scores >= 90]
        elif selected_match == "Great (80-89%)":
            filtered_df = filtered_df[(match_scores >= 80) & (match_scores < 90)]
        elif selected_match == "Good (70-79%)":
            filtered_df = filtered_df[(match_scores >= 70) & (match_scores < 80)]
        elif selected_match == "Fair (60-69%)":
            filtered_df = filtered_df[(match_scores >= 60) & (match_scores < 70)]
        elif selected_match == "Below 60%":
            filtered_df = filtered_df[match_scores < 60]
    
    # Remote work filter
    if selected_remote != 'All Work Styles':
        filtered_df = filtered_df[filtered_df.get('remote_option', '') == selected_remote]
    
    # Search filter
    if search_term:
        search_mask = (
            filtered_df.get('title', '').str.contains(search_term, case=False, na=False) |
            filtered_df.get('company', '').str.contains(search_term, case=False, na=False) |
            filtered_df.get('job_description', '').str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]
    
    # Salary filter
    if has_salary:
        filtered_df = filtered_df[filtered_df.get('salary_range', '').notna() & (filtered_df.get('salary_range', '') != '')]
    
    # Sort results
    if selected_sort == "Latest First":
        filtered_df = filtered_df.sort_values('scraped_at', ascending=False, na_position='last')
    elif selected_sort == "Highest Match":
        filtered_df = filtered_df.sort_values('match_score', ascending=False, na_position='last')
    elif selected_sort == "Company A-Z":
        filtered_df = filtered_df.sort_values('company', ascending=True, na_position='last')
    elif selected_sort == "Salary High-Low":
        # This would need salary parsing, for now just sort by salary_range presence
        filtered_df = filtered_df.sort_values('salary_range', ascending=False, na_position='last')
    
    # Show filter results
    if len(filtered_df) != len(df):
        st.info(f"🔍 Showing **{len(filtered_df)}** of **{len(df)}** jobs")
    
    return filtered_df

def render_job_cards_grid(df: pd.DataFrame, profile_name: str):
    """Render jobs as beautiful cards in a grid layout."""
    
    if df.empty:
        st.warning("No jobs match your current filters. Try adjusting the filters above.")
        return
    
    # Pagination
    jobs_per_page = 6
    total_pages = (len(df) - 1) // jobs_per_page + 1
    
    # Page selector
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            current_page = st.selectbox(
                f"📄 Page (showing {jobs_per_page} jobs per page)",
                range(1, total_pages + 1),
                key="job_cards_page"
            )
    else:
        current_page = 1
    
    # Get jobs for current page
    start_idx = (current_page - 1) * jobs_per_page
    end_idx = start_idx + jobs_per_page
    page_jobs = df.iloc[start_idx:end_idx]
    
    # Render jobs in 2-column grid
    for i in range(0, len(page_jobs), 2):
        col1, col2 = st.columns(2)
        
        with col1:
            if i < len(page_jobs):
                render_job_card(page_jobs.iloc[i], f"{profile_name}_{i}")
        
        with col2:
            if i + 1 < len(page_jobs):
                render_job_card(page_jobs.iloc[i + 1], f"{profile_name}_{i+1}")

def render_job_card(job: pd.Series, card_key: str):
    """Render a single job as a beautiful card."""
    
    # Extract job data with proper fallbacks and data cleaning
    title = str(job.get('title', job.get('job_title', 'Unknown Position'))).strip()
    company = str(job.get('company', job.get('company_name', 'Unknown Company'))).strip()
    location = str(job.get('location', job.get('job_location', 'Location not specified'))).strip()
    
    # Clean up any HTML entities or malformed data
    import html
    title = html.escape(title)
    company = html.escape(company)
    location = html.escape(location)
    
    # Handle different status column names
    status = job.get('status', job.get('status_text', job.get('pipeline_status', 'scraped')))
    if isinstance(status, str) and status.startswith('⚙️'):
        status = 'processed'
    elif isinstance(status, str) and status.startswith('✅'):
        status = 'applied'
    elif isinstance(status, str) and status.startswith('📄'):
        status = 'document_created'
    
    # Handle match score
    match_score = job.get('match_score', job.get('compatibility_score', 0))
    
    # Handle other fields
    salary_range = job.get('salary_range', job.get('salary', ''))
    remote_option = job.get('remote_option', job.get('work_style', ''))
    job_type = job.get('job_type', job.get('employment_type', ''))
    experience_level = job.get('experience_level', job.get('experience', ''))
    scraped_at = job.get('scraped_at', job.get('created_at', job.get('posted_date', '')))
    job_url = job.get('url', job.get('job_url', job.get('link', '')))
    
    # Format match score
    if isinstance(match_score, (int, float)) and match_score > 0:
        if match_score <= 1:
            match_score = int(match_score * 100)
        else:
            match_score = int(match_score)
    else:
        match_score = 0
    
    # Status styling
    status_colors = {
        'scraped': '#6366f1',
        'processed': '#f59e0b',
        'applied': '#10b981',
        'document_created': '#8b5cf6'
    }
    status_color = status_colors.get(status.lower(), '#6b7280')
    
    # Use Streamlit components instead of raw HTML to avoid rendering issues
    with st.container():
        # Match score badge
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {title}")
        with col2:
            st.markdown(f"**{match_score}%** match", help="Job compatibility score")
        
        # Company and location
        st.markdown(f"🏢 **{company}**")
        st.markdown(f"📍 {location}")
        
        # Job details in columns
        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            st.markdown(f"**Status:** {status.title()}")
        with detail_col2:
            st.markdown(f"**Experience:** {experience_level or 'Not specified'}")
        
        # Badges for salary and remote
        if salary_range or remote_option:
            badge_col1, badge_col2 = st.columns(2)
            with badge_col1:
                if salary_range:
                    st.markdown(f"💰 {salary_range}")
            with badge_col2:
                if remote_option:
                    st.markdown(f"🏠 {remote_option}")
        
        # Action buttons
        action_col1, action_col2, action_col3 = st.columns(3)
        with action_col1:
            if job_url and job_url != 'nan':
                st.link_button("🔗 View Job", job_url, use_container_width=True)
            else:
                st.button("🔗 No URL", disabled=True, use_container_width=True, key=f"no_url_{card_key}")
        
        with action_col2:
            if st.button("⚙️ Process", key=f"process_{card_key}", use_container_width=True):
                st.info("Processing feature coming soon!")
        
        with action_col3:
            if st.button("🎯 Apply", key=f"apply_{card_key}", use_container_width=True):
                st.info("Apply feature coming soon!")
        
        # Scraped date
        scraped_date = str(scraped_at)[:10] if scraped_at and not pd.isna(scraped_at) else 'Unknown'
        st.caption(f"📅 Scraped: {scraped_date}")
        
        # Add divider
        st.divider()
    
    # Add some spacing
    st.markdown("<br>", unsafe_allow_html=True)

def render_bulk_actions(df: pd.DataFrame):
    """Render bulk action controls for selected jobs."""
    st.markdown("### 🎛️ **Bulk Actions**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("⚙️ Process Selected", use_container_width=True):
            st.info("Bulk processing feature coming soon!")
    
    with col2:
        if st.button("📄 Generate Docs", use_container_width=True):
            st.info("Document generation feature coming soon!")
    
    with col3:
        if st.button("🎯 Apply to Jobs", use_container_width=True):
            st.info("Bulk application feature coming soon!")
    
    with col4:
        if st.button("📊 Export Data", use_container_width=True):
            st.info("Export feature coming soon!")