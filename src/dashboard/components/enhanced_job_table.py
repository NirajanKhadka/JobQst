"""
Enhanced Job Table Component with AgGrid
Professional-looking job table with interactive features
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any
import json

# Try to import streamlit-aggrid, fallback to regular dataframe if not available
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False
    st.warning("⚠️ streamlit-aggrid not installed. Install with: pip install streamlit-aggrid")

def render_Improved_job_table(df: pd.DataFrame, profile_name: str = "default") -> Optional[Dict]:
    """
    Render an enhanced job table with professional styling and interactive features.
    
    Args:
        df: DataFrame containing job data
        profile_name: Profile name for unique keys
        
    Returns:
        Selected row data if any row is selected
    """
    if df.empty:
        st.info("📋 No jobs found for the current filters")
        return None
    
    # Prepare data for display
    display_df = prepare_job_data_for_display(df)
    
    if HAS_AGGRID:
        return render_aggrid_table(display_df, profile_name)
    else:
        return render_fallback_table(display_df, profile_name)

def prepare_job_data_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare job data for optimal display in the table with all database fields."""
    display_df = df.copy()
    
    # Select and order columns for display - comprehensive set
    display_columns = [
        'title', 'company', 'location', 'status_text', 
        'match_score', 'compatibility_score', 'salary_range',
        'job_type', 'remote_option', 'experience_level',
        'application_status', 'processing_method', 'scraped_at', 'url'
    ]
    
    # Only include columns that exist
    available_columns = [col for col in display_columns if col in display_df.columns]
    display_df = display_df[available_columns]
    
    # Format data for better display
    for score_col in ['match_score', 'compatibility_score']:
        if score_col in display_df.columns:
            # Convert to percentage if needed
            if display_df[score_col].dtype in [float, 'float64', 'float32']:
                max_val = display_df[score_col].max()
                if max_val <= 1.0:  # Values are 0-1, convert to percentage
                    display_df[score_col] = (display_df[score_col].fillna(0) * 100).astype(int)
                else:
                    display_df[score_col] = display_df[score_col].fillna(0).astype(int)
    
    # Format dates
    for date_col in ['scraped_at', 'created_at', 'processed_at']:
        if date_col in display_df.columns:
            display_df[date_col] = pd.to_datetime(display_df[date_col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
    
    # Add status indicators with emojis
    if 'status_text' in display_df.columns:
        status_emoji_map = {
            'New': '⭕ New',
            'Scraped': '🔍 Scraped', 
            'Processed': '⚙️ Processed',
            'Document Created': '📄 Documents Ready',
            'Applied': '✅ Applied'
        }
        display_df['status_text'] = display_df['status_text'].map(status_emoji_map).fillna('❓ Unknown')
    
    # Format application status
    if 'application_status' in display_df.columns:
        app_status_map = {
            'not_applied': '⏳ Not Applied',
            'documents_ready': '📄 Docs Ready',
            'document_created': '📄 Docs Created',
            'applied': '✅ Applied',
            'interview_scheduled': '📅 Interview',
            'rejected': '❌ Rejected'
        }
        display_df['application_status'] = display_df['application_status'].map(app_status_map).fillna('⏳ Not Applied')
    
    # Format job type and remote option
    if 'job_type' in display_df.columns:
        display_df['job_type'] = display_df['job_type'].fillna('Not Specified')
    
    if 'remote_option' in display_df.columns:
        remote_map = {
            'remote': '🏠 Remote',
            'hybrid': '🏢🏠 Hybrid',
            'on-site': '🏢 On-site',
            'onsite': '🏢 On-site'
        }
        display_df['remote_option'] = display_df['remote_option'].map(remote_map).fillna('🏢 On-site')
    
    # Format experience level
    if 'experience_level' in display_df.columns:
        exp_map = {
            'entry': '🌱 Entry Level',
            'junior': '🌱 Junior',
            'mid': '🌿 Mid Level',
            'senior': '🌳 Senior',
            'lead': '👑 Lead',
            'principal': '🎯 Principal'
        }
        display_df['experience_level'] = display_df['experience_level'].map(exp_map).fillna('🌿 Mid Level')
    
    # Format processing method
    if 'processing_method' in display_df.columns:
        method_map = {
            'cpu_only': '💻 CPU',
            'gpu_accelerated': '🚀 GPU',
            'hybrid': '⚡ Hybrid',
            'unknown': '❓ Unknown'
        }
        display_df['processing_method'] = display_df['processing_method'].map(method_map).fillna('❓ Unknown')
    
    # Rename columns for display
    column_names = {
        'title': 'Job Title',
        'company': 'Company',
        'location': 'Location',
        'status_text': 'Pipeline Status',
        'match_score': 'Match %',
        'compatibility_score': 'Compatibility %',
        'salary_range': 'Salary Range',
        'job_type': 'Job Type',
        'remote_option': 'Work Style',
        'experience_level': 'Experience Level',
        'application_status': 'Application Status',
        'processing_method': 'Processing Method',
        'scraped_at': 'Scraped At',
        'url': 'Actions'
    }
    
    display_df = display_df.rename(columns=column_names)
    
    return display_df

def render_aggrid_table(df: pd.DataFrame, profile_name: str) -> Optional[Dict]:
    """Render the job table using AgGrid for professional appearance."""
    
    # Configure grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configure columns with comprehensive field set
    gb.configure_column("Job Title", 
                       headerName="Job Title",
                       width=250,
                       wrapText=True,
                       autoHeight=True,
                       pinned='left')
    
    gb.configure_column("Company", 
                       headerName="Company",
                       width=180,
                       wrapText=True)
    
    gb.configure_column("Location", 
                       headerName="Location",
                       width=140)
    
    gb.configure_column("Pipeline Status", 
                       headerName="Pipeline Status",
                       width=140,
                       cellStyle={'textAlign': 'center'})
    
    gb.configure_column("Match %", 
                       headerName="Match %",
                       width=90,
                       cellStyle={'textAlign': 'center'})
    
    gb.configure_column("Compatibility %", 
                       headerName="Compatibility %",
                       width=120,
                       cellStyle={'textAlign': 'center'})
    
    gb.configure_column("Salary Range", 
                       headerName="Salary",
                       width=140)
    
    gb.configure_column("Job Type", 
                       headerName="Type",
                       width=100,
                       cellStyle={'textAlign': 'center'})
    
    gb.configure_column("Work Style", 
                       headerName="Work Style",
                       width=110,
                       cellStyle={'textAlign': 'center'})
    
    gb.configure_column("Experience Level", 
                       headerName="Experience",
                       width=120,
                       cellStyle={'textAlign': 'center'})
    
    gb.configure_column("Application Status", 
                       headerName="App Status",
                       width=130,
                       cellStyle={'textAlign': 'center'})
    
    gb.configure_column("Processing Method", 
                       headerName="Processing",
                       width=110,
                       cellStyle={'textAlign': 'center'})
    
    gb.configure_column("Scraped At", 
                       headerName="Scraped",
                       width=130,
                       cellStyle={'textAlign': 'center'})
    
    # Add action buttons column
    if 'Actions' in df.columns:
        # JavaScript code for action buttons
        action_buttons = JsCode("""
        function(params) {
            return `
                <div style="display: flex; gap: 5px; justify-content: center;">
                    <button 
                        onclick="window.open('${params.data.url || '#'}', '_blank')"
                        style="
                            background: #007bff; 
                            color: white; 
                            border: none; 
                            padding: 4px 8px; 
                            border-radius: 4px; 
                            cursor: pointer;
                            font-size: 12px;
                        "
                        ${!params.data.url ? 'disabled' : ''}
                    >
                        🔗 View
                    </button>
                    <button 
                        onclick="alert('Apply feature coming soon!')"
                        style="
                            background: #28a745; 
                            color: white; 
                            border: none; 
                            padding: 4px 8px; 
                            border-radius: 4px; 
                            cursor: pointer;
                            font-size: 12px;
                        "
                    >
                        🎯 Apply
                    </button>
                </div>
            `;
        }
        """)
        
        gb.configure_column("Actions",
                           headerName="Actions",
                           width=150,
                           cellRenderer=action_buttons,
                           cellStyle={'textAlign': 'center'})
    
    # Configure grid options
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=25)
    gb.configure_side_bar()
    gb.configure_default_column(
        groupable=True,
        value=True,
        enableRowGroup=True,
        aggFunc='count',
        editable=False
    )
    
    # Enable selection
    gb.configure_selection('single', use_checkbox=True)
    
    # Build grid options
    gridOptions = gb.build()
    
    # Custom CSS for better styling
    custom_css = {
        ".ag-root-wrapper": {
            "border": "2px solid #e1e5e9",
            "border-radius": "10px"
        },
        ".ag-header": {
            "background": "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
            "color": "white",
            "font-weight": "bold"
        },
        ".ag-row-even": {
            "background": "#f8f9fa"
        },
        ".ag-row-hover": {
            "background": "#e3f2fd !important"
        }
    }
    
    # Display the grid
    st.markdown("### 📋 Job Management Table")
    
    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        theme='streamlit',
        custom_css=custom_css,
        height=600,
        allow_unsafe_jscode=True
    )
    
    # Handle selection
    selected_rows = grid_response['selected_rows']
    if selected_rows:
        return selected_rows[0]
    
    return None

def render_fallback_table(df: pd.DataFrame, profile_name: str) -> Optional[Dict]:
    """Improved fallback table rendering with modern UI/UX when AgGrid is not available."""
    
    # Add modern CSS styling
    st.markdown("""
    <style>
    .modern-table-container {
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid rgba(51, 65, 85, 0.5);
    }
    .table-header {
        color: #f1f5f9;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 20px;
        text-align: center;
    }
    .table-stats {
        display: flex;
        justify-content: space-around;
        margin-bottom: 20px;
        padding: 15px;
        background: rgba(59, 130, 246, 0.1);
        border-radius: 10px;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    .stat-item {
        text-align: center;
        color: #f1f5f9;
    }
    .stat-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #3b82f6;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #cbd5e1;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="modern-table-container">', unsafe_allow_html=True)
    st.markdown('<div class="table-header">📋 Job Management Dashboard</div>', unsafe_allow_html=True)
    
    # Display statistics
    total_jobs = len(df)
    applied_jobs = len(df[df.get('Application Status', '').str.contains('Applied', na=False)])
    processed_jobs = len(df[df.get('Pipeline Status', '').str.contains('Processed', na=False)])
    high_match = len(df[df.get('Match %', 0) >= 80])
    
    st.markdown(f"""
    <div class="table-stats">
        <div class="stat-item">
            <div class="stat-number">{total_jobs}</div>
            <div class="stat-label">Total Jobs</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{high_match}</div>
            <div class="stat-label">High Match</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{processed_jobs}</div>
            <div class="stat-label">Processed</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{applied_jobs}</div>
            <div class="stat-label">Applied</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Improved dataframe with better column configuration
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=500,
        column_config={
            "Job Title": st.column_config.TextColumn(
                "🎯 Job Title",
                width="large",
                help="Click to view job details"
            ),
            "Company": st.column_config.TextColumn(
                "🏢 Company",
                width="medium",
            ),
            "Location": st.column_config.TextColumn(
                "📍 Location",
                width="medium",
            ),
            "Pipeline Status": st.column_config.TextColumn(
                "📊 Status",
                width="medium",
            ),
            "Application Status": st.column_config.TextColumn(
                "🎯 App Status",
                width="medium",
            ),
            "Match %": st.column_config.NumberColumn(
                "🎯 Match",
                width="small",
                format="%d%%",
                help="Job compatibility score"
            ),
            "Compatibility %": st.column_config.NumberColumn(
                "⭐ Compatibility",
                width="small",
                format="%d%%",
                help="Profile compatibility score"
            ),
            "Salary Range": st.column_config.TextColumn(
                "💰 Salary",
                width="medium",
            ),
            "Work Style": st.column_config.TextColumn(
                "🏠 Work Style",
                width="small",
            ),
            "Experience Level": st.column_config.TextColumn(
                "👨‍💼 Experience",
                width="small",
            ),
            "Scraped At": st.column_config.DatetimeColumn(
                "📅 Scraped",
                width="small",
                format="MM/DD/YY",
            ),
        }
    )
    
    # Enhanced job actions section
    if not df.empty:
        st.markdown("### 🎯 Quick Actions")
        
        # Bulk actions
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("⚙️ Process All", use_container_width=True, key=f"process_all_{profile_name}"):
                st.info("🚀 Bulk processing feature coming soon!")
        
        with col2:
            if st.button("📄 Generate Docs", use_container_width=True, key=f"docs_all_{profile_name}"):
                st.info("📄 Document generation feature coming soon!")
        
        with col3:
            if st.button("🎯 Apply to Top", use_container_width=True, key=f"apply_top_{profile_name}"):
                st.info("🎯 Auto-apply feature coming soon!")
        
        with col4:
            if st.button("📊 Export Data", use_container_width=True, key=f"export_{profile_name}"):
                st.info("📊 Export feature coming soon!")
        
        # Individual job selection
        st.markdown("#### 🔍 Individual Job Actions")
        
        # Create a more user-friendly job selector
        job_options = []
        for idx, row in df.iterrows():
            job_title = row.get('Job Title', 'Unknown Job')
            company = row.get('Company', 'Unknown Company')
            match_score = row.get('Match %', 0)
            status = row.get('Pipeline Status', 'Unknown')
            job_options.append(f"🎯 {job_title} at {company} ({match_score}% match, {status})")
        
        selected_job_idx = st.selectbox(
            "🔍 Select a job for detailed actions:",
            range(len(job_options)),
            format_func=lambda x: job_options[x],
            key=f"job_selector_{profile_name}",
            help="Choose a job to view details and perform actions"
        )
        
        if selected_job_idx is not None:
            selected_row = df.iloc[selected_job_idx]
            
            # Display selected job details in an attractive format
            with st.expander("📋 Selected Job Details", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**🎯 Title:** {selected_row.get('Job Title', 'N/A')}")
                    st.markdown(f"**🏢 Company:** {selected_row.get('Company', 'N/A')}")
                    st.markdown(f"**📍 Location:** {selected_row.get('Location', 'N/A')}")
                    st.markdown(f"**💰 Salary:** {selected_row.get('Salary Range', 'Not specified')}")
                
                with col2:
                    st.markdown(f"**📊 Pipeline Status:** {selected_row.get('Pipeline Status', 'N/A')}")
                    st.markdown(f"**🎯 Application Status:** {selected_row.get('Application Status', 'N/A')}")
                    st.markdown(f"**⭐ Match Score:** {selected_row.get('Match %', 'N/A')}%")
                    st.markdown(f"**🏠 Work Style:** {selected_row.get('Work Style', 'Not specified')}")
            
            # Action buttons for selected job
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🔗 View Job", key=f"view_{profile_name}_{selected_job_idx}", use_container_width=True):
                    job_url = selected_row.get('Actions', selected_row.get('url', ''))
                    if job_url and job_url != 'Actions':
                        st.success(f"🔗 Opening job posting...")
                        st.markdown(f"**Job URL:** [Click here to open]({job_url})")
                        # JavaScript to open in new tab
                        st.markdown(f"""
                        <script>
                        setTimeout(function() {{
                            window.open('{job_url}', '_blank');
                        }}, 100);
                        </script>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("❌ No URL available for this job")
            
            with col2:
                if st.button("⚙️ Process Job", key=f"process_{profile_name}_{selected_job_idx}", use_container_width=True):
                    st.info("⚙️ Job processing feature coming soon!")
            
            with col3:
                if st.button("📄 Create Docs", key=f"docs_{profile_name}_{selected_job_idx}", use_container_width=True):
                    st.info("📄 Document generation feature coming soon!")
            
            with col4:
                if st.button("🎯 Apply Now", key=f"apply_{profile_name}_{selected_job_idx}", use_container_width=True):
                    st.info("🎯 Job application feature coming soon!")
            
            st.markdown('</div>', unsafe_allow_html=True)
            return selected_row.to_dict()
    
    st.markdown('</div>', unsafe_allow_html=True)
    return None

def display_job_details(job_data: Dict, original_df: pd.DataFrame):
    """Display detailed information for a selected job."""
    if not job_data:
        return
    
    st.markdown("### 📋 Selected Job Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**🎯 Title:** {job_data.get('Job Title', 'N/A')}")
        st.markdown(f"**🏢 Company:** {job_data.get('Company', 'N/A')}")
        st.markdown(f"**📍 Location:** {job_data.get('Location', 'N/A')}")
        st.markdown(f"**📅 Date Added:** {job_data.get('Date Added', 'N/A')}")
    
    with col2:
        st.markdown(f"**📊 Status:** {job_data.get('Status', 'N/A')}")
        st.markdown(f"**⭐ Priority:** {job_data.get('Priority', 'N/A')}")
        st.markdown(f"**🎯 Match:** {job_data.get('Match %', 'N/A')}%")
    
    # Find original job data for description
    job_title = job_data.get('Job Title', '')
    company = job_data.get('Company', '')
    
    if not original_df.empty:
        # Find matching row in original data
        mask = (
            (original_df['title'].str.contains(job_title.replace('🎯 ', ''), case=False, na=False)) &
            (original_df['company'].str.contains(company.replace('🏢 ', ''), case=False, na=False))
        )
        matching_jobs = original_df[mask]
        
        if not matching_jobs.empty:
            job_details = matching_jobs.iloc[0]
            
            if 'description' in job_details and job_details['description']:
                with st.expander("📄 Job Description", expanded=False):
                    st.text_area(
                        "",
                        value=job_details['description'],
                        height=200,
                        disabled=True,
                        key="job_description_display"
                    )
            
            if 'url' in job_details and job_details['url']:
                st.markdown(f"**🔗 Job URL:** [Open Job Posting]({job_details['url']})")