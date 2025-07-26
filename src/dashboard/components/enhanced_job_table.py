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

def render_enhanced_job_table(df: pd.DataFrame, profile_name: str = "default") -> Optional[Dict]:
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
    """Prepare job data for optimal display in the table."""
    display_df = df.copy()
    
    # Select and order columns for display
    display_columns = [
        'title', 'company', 'location', 'status_text', 
        'priority', 'match_score', 'created_at', 'url'
    ]
    
    # Only include columns that exist
    available_columns = [col for col in display_columns if col in display_df.columns]
    display_df = display_df[available_columns]
    
    # Format data for better display
    if 'match_score' in display_df.columns:
        # If match_score is a float between 0 and 1, convert to percentage
        if display_df['match_score'].dtype in [float, 'float64', 'float32']:
            display_df['match_score'] = (display_df['match_score'].fillna(0) * 100).astype(int)
        else:
            display_df['match_score'] = display_df['match_score'].fillna(0).astype(int)
    
    if 'created_at' in display_df.columns:
        display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d')
    
    # Add status indicators
    if 'status_text' in display_df.columns:
        status_emoji_map = {
            'New': '⭕ New',
            'Scraped': '🔍 Scraped', 
            'Processed': '⚙️ Processed',
            'Document Created': '📄 Documents Ready',
            'Applied': '✅ Applied'
        }
        display_df['status_text'] = display_df['status_text'].map(status_emoji_map).fillna('❓ Unknown')
    
    # Add priority indicators
    if 'priority' in display_df.columns:
        priority_emoji_map = {
            'High': '🔴 High',
            'Medium': '🟡 Medium', 
            'Low': '🟢 Low'
        }
        display_df['priority'] = display_df['priority'].map(priority_emoji_map).fillna('🟡 Medium')
    
    # Rename columns for display
    column_names = {
        'title': 'Job Title',
        'company': 'Company',
        'location': 'Location',
        'status_text': 'Status',
        'priority': 'Priority',
        'match_score': 'Match %',
        'created_at': 'Date Added',
        'url': 'Actions'
    }
    
    display_df = display_df.rename(columns=column_names)
    
    return display_df

def render_aggrid_table(df: pd.DataFrame, profile_name: str) -> Optional[Dict]:
    """Render the job table using AgGrid for professional appearance."""
    
    # Configure grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configure columns
    gb.configure_column("Job Title", 
                       headerName="Job Title",
                       width=300,
                       wrapText=True,
                       autoHeight=True)
    
    gb.configure_column("Company", 
                       headerName="Company",
                       width=200,
                       wrapText=True)
    
    gb.configure_column("Location", 
                       headerName="Location",
                       width=150)
    
    gb.configure_column("Status", 
                       headerName="Pipeline Status",
                       width=150,
                       cellStyle={'textAlign': 'center'})
    
    gb.configure_column("Priority", 
                       headerName="Priority",
                       width=120,
                       cellStyle={'textAlign': 'center'})
    
    gb.configure_column("Match %", 
                       headerName="Match",
                       width=100,
                       cellStyle={'textAlign': 'center'})
    
    gb.configure_column("Date Added", 
                       headerName="Added",
                       width=120,
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
    """Fallback table rendering when AgGrid is not available."""
    
    st.markdown("### 📋 Job Management Table")
    st.info("💡 Install streamlit-aggrid for enhanced table features: `pip install streamlit-aggrid`")
    
    # Display with enhanced styling
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=600,
        column_config={
            "Job Title": st.column_config.TextColumn(
                "Job Title",
                width="large",
            ),
            "Company": st.column_config.TextColumn(
                "Company",
                width="medium",
            ),
            "Location": st.column_config.TextColumn(
                "Location",
                width="medium",
            ),
            "Status": st.column_config.TextColumn(
                "Pipeline Status",
                width="medium",
            ),
            "Priority": st.column_config.TextColumn(
                "Priority",
                width="small",
            ),
            "Match %": st.column_config.NumberColumn(
                "Match %",
                width="small",
                format="%d%%"
            ),
            "Date Added": st.column_config.DateColumn(
                "Date Added",
                width="small",
            ),
        }
    )
    
    # Add manual job selection for actions
    if not df.empty:
        st.markdown("### 🎯 Job Actions")
        
        # Job selection
        job_options = []
        for idx, row in df.iterrows():
            job_title = row.get('Job Title', 'Unknown Job')
            company = row.get('Company', 'Unknown Company')
            job_options.append(f"{job_title} at {company}")
        
        selected_job_idx = st.selectbox(
            "Select a job for actions:",
            range(len(job_options)),
            format_func=lambda x: job_options[x],
            key=f"job_selector_{profile_name}"
        )
        
        if selected_job_idx is not None:
            selected_row = df.iloc[selected_job_idx]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔗 View Job", key=f"view_{profile_name}_{selected_job_idx}"):
                    job_url = selected_row.get('url', '')
                    if job_url:
                        st.markdown(f"**Job URL:** [Open in new tab]({job_url})")
                        # Use JavaScript to open in new tab
                        st.markdown(f"""
                        <script>
                        window.open('{job_url}', '_blank');
                        </script>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("No URL available for this job")
            
            with col2:
                if st.button("📄 Generate Docs", key=f"docs_{profile_name}_{selected_job_idx}"):
                    st.info("Document generation feature coming soon!")
            
            with col3:
                if st.button("🎯 Apply", key=f"apply_{profile_name}_{selected_job_idx}"):
                    st.info("Job application feature coming soon!")
            
            return selected_row.to_dict()
    
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