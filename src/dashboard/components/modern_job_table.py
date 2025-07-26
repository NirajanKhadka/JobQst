#!/usr/bin/env python3
"""
Modern Job Table Component
Consolidated, clean job management interface with dark theme
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

# Try to import AgGrid for enhanced tables
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False

logger = logging.getLogger(__name__)

def render_modern_job_table(df: pd.DataFrame, profile_name: str = "default") -> None:
    """
    Render modern job management interface with dark theme and clean design.
    
    Args:
        df: DataFrame containing job data
        profile_name: Profile name for database operations
    """
    
    if df.empty:
        render_empty_state()
        return
    
    # Job statistics overview
    render_job_statistics(df)
    
    # Smart filters
    filtered_df = render_job_filters(df)
    
    # Job table with actions
    render_job_table_with_actions(filtered_df, profile_name)

def render_empty_state():
    """Render empty state when no jobs are available."""
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem; background: #1e293b; border-radius: 1rem; border: 1px solid #334155;'>
        <div style='font-size: 4rem; margin-bottom: 1rem;'>📭</div>
        <h3 style='color: #f1f5f9; margin-bottom: 1rem;'>No Jobs Found</h3>
        <p style='color: #cbd5e1; margin-bottom: 2rem;'>Start by scraping some job listings or check your filters.</p>
        <div style='display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;'>
            <button style='background: linear-gradient(135deg, #3b82f6, #6366f1); color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; font-weight: 500;'>
                🔍 Start Scraping
            </button>
            <button style='background: #334155; color: #f1f5f9; border: 1px solid #475569; padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; font-weight: 500;'>
                ⚙️ Check Settings
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_job_statistics(df: pd.DataFrame):
    """Render job statistics overview."""
    
    # Calculate statistics
    total_jobs = len(df)
    applied_jobs = len(df[df.get('status_text', '') == 'Applied'])
    processed_jobs = len(df[df.get('status_text', '') == 'Processed'])
    scraped_jobs = len(df[df.get('status_text', '') == 'Scraped'])
    
    # Recent activity (last 24 hours)
    if 'scraped_at' in df.columns:
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_jobs = len(df[pd.to_datetime(df['scraped_at'], errors='coerce') > recent_cutoff])
    else:
        recent_jobs = 0
    
    # Display metrics in cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; text-align: center;'>
            <div style='font-size: 2rem; color: #3b82f6; font-weight: 700; font-family: monospace;'>{total_jobs}</div>
            <div style='color: #cbd5e1; font-size: 0.875rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.5rem;'>Total Jobs</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; text-align: center;'>
            <div style='font-size: 2rem; color: #10b981; font-weight: 700; font-family: monospace;'>{applied_jobs}</div>
            <div style='color: #cbd5e1; font-size: 0.875rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.5rem;'>Applied</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; text-align: center;'>
            <div style='font-size: 2rem; color: #f59e0b; font-weight: 700; font-family: monospace;'>{processed_jobs}</div>
            <div style='color: #cbd5e1; font-size: 0.875rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.5rem;'>Processed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; text-align: center;'>
            <div style='font-size: 2rem; color: #6366f1; font-weight: 700; font-family: monospace;'>{scraped_jobs}</div>
            <div style='color: #cbd5e1; font-size: 0.875rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.5rem;'>Scraped</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; text-align: center;'>
            <div style='font-size: 2rem; color: #ef4444; font-weight: 700; font-family: monospace;'>{recent_jobs}</div>
            <div style='color: #cbd5e1; font-size: 0.875rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.5rem;'>Last 24h</div>
        </div>
        """, unsafe_allow_html=True)

def render_job_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render smart job filters and return filtered dataframe."""
    
    st.markdown("### 🔍 Filters")
    
    # Filter container
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Status filter
            status_options = ['All'] + list(df.get('status_text', pd.Series()).unique())
            selected_status = st.selectbox(
                "Status",
                status_options,
                key="job_status_filter"
            )
        
        with col2:
            # Company filter
            companies = ['All'] + sorted(df.get('company', pd.Series()).dropna().unique().tolist())
            selected_company = st.selectbox(
                "Company",
                companies,
                key="job_company_filter"
            )
        
        with col3:
            # Location filter
            locations = ['All'] + sorted(df.get('location', pd.Series()).dropna().unique().tolist())
            selected_location = st.selectbox(
                "Location",
                locations,
                key="job_location_filter"
            )
        
        with col4:
            # Date range filter
            date_options = ['All Time', 'Last 24 hours', 'Last 7 days', 'Last 30 days']
            selected_date_range = st.selectbox(
                "Date Range",
                date_options,
                key="job_date_filter"
            )
    
    # Additional filters row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Match score filter
        if 'match_score' in df.columns:
            match_score_filter = st.selectbox(
                "Match Score",
                ["All Scores", "High (80%+)", "Medium (60-79%)", "Low (40-59%)", "Very Low (<40%)"],
                key="match_score_filter"
            )
        else:
            match_score_filter = "All Scores"
    
    with col2:
        # Job type filter
        if 'job_type' in df.columns:
            job_types = ['All Types'] + sorted(df.get('job_type', pd.Series()).dropna().unique().tolist())
            selected_job_type = st.selectbox(
                "Job Type",
                job_types,
                key="job_type_filter"
            )
        else:
            selected_job_type = "All Types"
    
    with col3:
        # Remote option filter
        if 'remote_option' in df.columns:
            remote_options = ['All Options'] + sorted(df.get('remote_option', pd.Series()).dropna().unique().tolist())
            selected_remote = st.selectbox(
                "Remote Option",
                remote_options,
                key="remote_filter"
            )
        else:
            selected_remote = "All Options"
    
    with col4:
        # Salary range filter
        if 'salary_range' in df.columns:
            has_salary = st.checkbox(
                "Has Salary Info",
                value=False,
                key="salary_filter"
            )
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_status != 'All':
        filtered_df = filtered_df[filtered_df.get('status_text', '') == selected_status]
    
    if selected_company != 'All':
        filtered_df = filtered_df[filtered_df.get('company', '') == selected_company]
    
    if selected_location != 'All':
        filtered_df = filtered_df[filtered_df.get('location', '') == selected_location]
    
    if selected_date_range != 'All Time' and 'scraped_at' in filtered_df.columns:
        now = datetime.now()
        if selected_date_range == 'Last 24 hours':
            cutoff = now - timedelta(hours=24)
        elif selected_date_range == 'Last 7 days':
            cutoff = now - timedelta(days=7)
        elif selected_date_range == 'Last 30 days':
            cutoff = now - timedelta(days=30)
        
        filtered_df = filtered_df[pd.to_datetime(filtered_df['scraped_at'], errors='coerce') > cutoff]
    
    # Apply additional filters
    if match_score_filter != "All Scores" and 'match_score' in filtered_df.columns:
        # Convert match_score to percentage if needed
        match_scores = filtered_df['match_score'].copy()
        if match_scores.max() <= 1.0:
            match_scores = match_scores * 100
        
        if match_score_filter == "High (80%+)":
            filtered_df = filtered_df[match_scores >= 80]
        elif match_score_filter == "Medium (60-79%)":
            filtered_df = filtered_df[(match_scores >= 60) & (match_scores < 80)]
        elif match_score_filter == "Low (40-59%)":
            filtered_df = filtered_df[(match_scores >= 40) & (match_scores < 60)]
        elif match_score_filter == "Very Low (<40%)":
            filtered_df = filtered_df[match_scores < 40]
    
    if selected_job_type != 'All Types' and 'job_type' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df.get('job_type', '') == selected_job_type]
    
    if selected_remote != 'All Options' and 'remote_option' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df.get('remote_option', '') == selected_remote]
    
    if has_salary and 'salary_range' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['salary_range'].notna() & (filtered_df['salary_range'] != '')]
    
    # Show filter results
    if len(filtered_df) != len(df):
        st.info(f"Showing {len(filtered_df)} of {len(df)} jobs")
    
    return filtered_df

def render_job_table_with_actions(df: pd.DataFrame, profile_name: str):
    """Render job table with bulk actions."""
    
    if df.empty:
        st.warning("No jobs match the current filters.")
        return
    
    # Bulk actions
    st.markdown("### 📋 Job Management")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Process Selected", help="Process selected jobs with AI analysis"):
            st.info("Processing functionality would be implemented here")
    
    with col2:
        if st.button("📄 Generate Docs", help="Generate documents for selected jobs"):
            st.info("Document generation functionality would be implemented here")
    
    with col3:
        if st.button("📤 Apply to Jobs", help="Submit applications for selected jobs"):
            st.info("Application functionality would be implemented here")
    
    with col4:
        if st.button("🗑️ Delete Selected", help="Delete selected jobs"):
            st.info("Delete functionality would be implemented here")
    
    # Job table
    if HAS_AGGRID:
        render_aggrid_table(df)
    else:
        render_standard_table(df)

def render_aggrid_table(df: pd.DataFrame):
    """Render enhanced job table using AgGrid with better styling."""
    
    # Prepare display columns with proper ordering and formatting
    display_columns = []
    column_config = {}
    
    # Essential columns
    if 'title' in df.columns:
        display_columns.append('title')
        column_config['title'] = {'headerName': 'Job Title', 'width': 300, 'pinned': 'left'}
    
    if 'company' in df.columns:
        display_columns.append('company')
        column_config['company'] = {'headerName': 'Company', 'width': 200}
    
    if 'location' in df.columns:
        display_columns.append('location')
        column_config['location'] = {'headerName': 'Location', 'width': 150}
    
    # Match score and compatibility
    if 'match_score' in df.columns:
        display_columns.append('match_score')
        column_config['match_score'] = {
            'headerName': 'Match %', 
            'width': 100,
            'type': 'numericColumn',
            'cellStyle': {'textAlign': 'center'},
            'valueFormatter': "value ? value.toFixed(1) + '%' : '0.0%'"
        }
    
    if 'compatibility_score' in df.columns:
        display_columns.append('compatibility_score')
        column_config['compatibility_score'] = {
            'headerName': 'Compatibility %', 
            'width': 120,
            'type': 'numericColumn',
            'cellStyle': {'textAlign': 'center'},
            'valueFormatter': "value ? value.toFixed(1) + '%' : '0.0%'"
        }
    
    # Status columns
    if 'status_text' in df.columns:
        display_columns.append('status_text')
        column_config['status_text'] = {
            'headerName': 'Status', 
            'width': 120,
            'cellStyle': {'textAlign': 'center'}
        }
    
    if 'application_status' in df.columns:
        display_columns.append('application_status')
        column_config['application_status'] = {
            'headerName': 'App Status', 
            'width': 120,
            'cellStyle': {'textAlign': 'center'}
        }
    
    # Additional useful columns
    if 'salary_range' in df.columns:
        display_columns.append('salary_range')
        column_config['salary_range'] = {'headerName': 'Salary', 'width': 150}
    
    if 'job_type' in df.columns:
        display_columns.append('job_type')
        column_config['job_type'] = {'headerName': 'Type', 'width': 100}
    
    if 'remote_option' in df.columns:
        display_columns.append('remote_option')
        column_config['remote_option'] = {'headerName': 'Remote', 'width': 100}
    
    if 'scraped_at' in df.columns:
        display_columns.append('scraped_at')
        column_config['scraped_at'] = {
            'headerName': 'Scraped', 
            'width': 150,
            'type': 'dateColumn'
        }
    
    # Create display dataframe
    display_df = df[display_columns].copy() if display_columns else df.copy()
    
    # Format data for better display
    if 'scraped_at' in display_df.columns:
        display_df['scraped_at'] = pd.to_datetime(display_df['scraped_at'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
    
    # Convert match scores to percentages if they're in 0-1 range
    if 'match_score' in display_df.columns:
        # Check if values are in 0-1 range (need to convert to percentage)
        max_score = display_df['match_score'].max()
        if max_score <= 1.0:
            display_df['match_score'] = display_df['match_score'] * 100
    
    if 'compatibility_score' in display_df.columns:
        max_score = display_df['compatibility_score'].max()
        if max_score <= 1.0:
            display_df['compatibility_score'] = display_df['compatibility_score'] * 100
    
    # Configure grid options
    gb = GridOptionsBuilder.from_dataframe(display_df)
    
    # Grid configuration
    gb.configure_pagination(paginationAutoPageSize=True, paginationPageSize=20)
    gb.configure_side_bar(filters_panel=True, columns_panel=True)
    gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren=True, groupSelectsFiltered=True)
    gb.configure_default_column(
        groupable=True, 
        value=True, 
        enableRowGroup=True, 
        editable=False,
        sortable=True,
        filter=True,
        resizable=True
    )
    
    # Apply column configurations
    for col, config in column_config.items():
        if col in display_df.columns:
            gb.configure_column(col, **config)
    
    # Grid theme and styling
    gridOptions = gb.build()
    
    # Custom CSS for dark theme
    custom_css = {
        ".ag-theme-streamlit": {
            "--ag-background-color": "#1e293b",
            "--ag-header-background-color": "#334155",
            "--ag-odd-row-background-color": "#1e293b",
            "--ag-even-row-background-color": "#334155",
            "--ag-row-hover-color": "#475569",
            "--ag-selected-row-background-color": "#3b82f6",
            "--ag-font-color": "#f1f5f9",
            "--ag-header-font-color": "#f1f5f9",
            "--ag-border-color": "#475569",
            "--ag-secondary-border-color": "#64748b"
        }
    }
    
    # Display grid
    grid_response = AgGrid(
        display_df,
        gridOptions=gridOptions,
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=False,
        theme='streamlit',
        custom_css=custom_css,
        enable_enterprise_modules=False,
        height=600,
        width='100%',
        reload_data=False
    )
    
    # Handle selection
    if grid_response['selected_rows'] is not None and len(grid_response['selected_rows']) > 0:
        selected_count = len(grid_response['selected_rows'])
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1rem; border-radius: 0.5rem; border: 1px solid #334155; margin-top: 1rem;'>
            <div style='color: #3b82f6; font-weight: 600;'>✓ Selected {selected_count} job{'' if selected_count == 1 else 's'}</div>
            <div style='color: #cbd5e1; font-size: 0.875rem; margin-top: 0.25rem;'>Use the action buttons above to process selected jobs</div>
        </div>
        """, unsafe_allow_html=True)

def render_standard_table(df: pd.DataFrame):
    """Render enhanced standard Streamlit table as fallback."""
    
    # Prepare display columns with better selection
    preferred_columns = [
        'title', 'company', 'location', 'match_score', 'compatibility_score', 
        'status_text', 'application_status', 'salary_range', 'job_type', 
        'remote_option', 'scraped_at'
    ]
    
    # Select available columns
    display_columns = [col for col in preferred_columns if col in df.columns]
    if not display_columns:
        display_columns = list(df.columns)[:10]  # Fallback to first 10 columns
    
    display_df = df[display_columns].copy()
    
    # Format columns for better display
    if 'scraped_at' in display_df.columns:
        display_df['scraped_at'] = pd.to_datetime(display_df['scraped_at'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
    
    # Format match scores as percentages
    for score_col in ['match_score', 'compatibility_score']:
        if score_col in display_df.columns:
            max_score = display_df[score_col].max()
            if max_score <= 1.0:
                display_df[score_col] = (display_df[score_col] * 100).round(1)
            display_df[score_col] = display_df[score_col].astype(str) + '%'
    
    # Rename columns for better display
    column_renames = {
        'title': 'Job Title',
        'company': 'Company',
        'location': 'Location',
        'match_score': 'Match %',
        'compatibility_score': 'Compatibility %',
        'status_text': 'Status',
        'application_status': 'App Status',
        'salary_range': 'Salary',
        'job_type': 'Type',
        'remote_option': 'Remote',
        'scraped_at': 'Scraped At'
    }
    
    display_df = display_df.rename(columns=column_renames)
    
    # Custom styling for the dataframe
    def style_dataframe(df):
        """Apply custom styling to the dataframe."""
        
        def highlight_status(val):
            """Color code status values."""
            if pd.isna(val):
                return ''
            
            val_str = str(val).lower()
            if 'applied' in val_str:
                return 'background-color: #064e3b; color: #10b981'
            elif 'processed' in val_str or 'document' in val_str:
                return 'background-color: #78350f; color: #f59e0b'
            elif 'scraped' in val_str:
                return 'background-color: #1e3a8a; color: #3b82f6'
            else:
                return 'background-color: #374151; color: #9ca3af'
        
        def highlight_match_score(val):
            """Color code match scores."""
            if pd.isna(val):
                return ''
            
            try:
                score = float(str(val).replace('%', ''))
                if score >= 80:
                    return 'background-color: #064e3b; color: #10b981; font-weight: bold'
                elif score >= 60:
                    return 'background-color: #78350f; color: #f59e0b; font-weight: bold'
                elif score >= 40:
                    return 'background-color: #1e3a8a; color: #3b82f6'
                else:
                    return 'background-color: #374151; color: #9ca3af'
            except:
                return ''
        
        # Apply styling
        styled_df = df.style
        
        # Style status columns
        for col in ['Status', 'App Status']:
            if col in df.columns:
                styled_df = styled_df.applymap(highlight_status, subset=[col])
        
        # Style score columns
        for col in ['Match %', 'Compatibility %']:
            if col in df.columns:
                styled_df = styled_df.applymap(highlight_match_score, subset=[col])
        
        # General styling
        styled_df = styled_df.set_properties(**{
            'background-color': '#1e293b',
            'color': '#f1f5f9',
            'border': '1px solid #475569'
        })
        
        return styled_df
    
    # Display styled table
    try:
        styled_df = style_dataframe(display_df)
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=600,
            hide_index=True
        )
    except Exception as e:
        # Fallback to unstyled table if styling fails
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600,
            hide_index=True
        )
        st.caption(f"Note: Advanced styling unavailable ({str(e)})")
    
    # Enhanced info message
    st.markdown("""
    <div style='background: #1e293b; padding: 1rem; border-radius: 0.5rem; border: 1px solid #334155; margin-top: 1rem;'>
        <div style='color: #3b82f6; font-weight: 600;'>💡 Enhanced Table Features</div>
        <div style='color: #cbd5e1; font-size: 0.875rem; margin-top: 0.25rem;'>
            Install <code>st-aggrid</code> for advanced features like multi-selection, filtering, and sorting:<br>
            <code>pip install streamlit-aggrid</code>
        </div>
    </div>
    """, unsafe_allow_html=True)