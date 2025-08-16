#!/usr/bin/env python3
"""
Manual Application Tracking Component
Allows users to manually mark jobs as applied using checkboxes
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

def update_application_status(job_id: int, profile_name: str, status: str, notes: str = ""):
    """Update the application status for a job."""
    try:
        from src.core.job_database import get_job_db
        
        db = get_job_db(profile_name)
        
        with db._get_connection() as conn:
            # Update application status and date
            conn.execute("""
                UPDATE jobs 
                SET application_status = ?, 
                    application_date = ?,
                    processing_notes = COALESCE(processing_notes, '') || ?
                WHERE id = ?
            """, (
                status,
                datetime.now().isoformat(),
                f"\n[Manual] {notes}" if notes else f"\n[Manual] Marked as {status}",
                job_id
            ))
            conn.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update job {job_id}: {e}")
        return False

def render_manual_application_tracker(df: pd.DataFrame, profile_name: str):
    """Render the manual application tracking interface."""
    
    st.markdown("### ✅ Manual Application Tracker")
    st.markdown("Mark jobs as applied manually when you apply through the company website")
    
    if df.empty:
        st.info("No jobs available for application tracking")
        return
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Status filter
        status_options = ["All", "ready_to_apply", "needs_review", "scraped", "new"]
        selected_status = st.selectbox("Filter by Status", status_options, key="manual_status_filter")
    
    with col2:
        # Application status filter
        app_status_options = ["All", "not_applied", "applied", "rejected", "interview"]
        selected_app_status = st.selectbox("Application Status", app_status_options, key="manual_app_status_filter")
    
    with col3:
        # Company filter
        companies = ["All"] + sorted(df['company'].dropna().unique().tolist())
        selected_company = st.selectbox("Company", companies[:20], key="manual_company_filter")  # Limit to 20 for performance
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df.get('status', '') == selected_status]
    
    if selected_app_status != "All":
        filtered_df = filtered_df[filtered_df.get('application_status', 'not_applied') == selected_app_status]
    
    if selected_company != "All":
        filtered_df = filtered_df[filtered_df['company'] == selected_company]
    
    # Sort by priority: ready_to_apply first, then by match_score
    if not filtered_df.empty:
        # Create priority score for sorting
        def get_priority_score(row):
            status = row.get('status', '')
            match_score = row.get('match_score', 0)
            
            if status == 'ready_to_apply':
                return 1000 + match_score
            elif status == 'needs_review':
                return 500 + match_score
            else:
                return match_score
        
        filtered_df['priority_score'] = filtered_df.apply(get_priority_score, axis=1)
        filtered_df = filtered_df.sort_values('priority_score', ascending=False)
    
    st.write(f"**Found {len(filtered_df)} jobs** (filtered from {len(df)} total)")
    
    if filtered_df.empty:
        st.info("No jobs match the selected filters")
        return
    
    # Display jobs with checkboxes - limit to 50 for performance
    display_limit = 50
    if len(filtered_df) > display_limit:
        st.warning(f"Showing first {display_limit} jobs. Use filters to narrow down results.")
        filtered_df = filtered_df.head(display_limit)
    
    # Batch actions
    st.markdown("#### 🎯 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Mark Selected as Applied", key="bulk_apply"):
            st.session_state['bulk_action'] = 'apply'
    
    with col2:
        if st.button("❌ Mark Selected as Not Interested", key="bulk_reject"):
            st.session_state['bulk_action'] = 'reject'
    
    with col3:
        if st.button("🔄 Reset Selected", key="bulk_reset"):
            st.session_state['bulk_action'] = 'reset'
    
    # Initialize session state for selected jobs
    if 'selected_jobs' not in st.session_state:
        st.session_state['selected_jobs'] = set()
    
    # Job list with checkboxes
    st.markdown("#### 📋 Job List")
    
    # Header row
    col1, col2, col3, col4, col5, col6 = st.columns([0.5, 2, 1.5, 1, 1, 1])
    
    with col1:
        st.markdown("**Select**")
    with col2:
        st.markdown("**Job & Company**")
    with col3:
        st.markdown("**Status**")
    with col4:
        st.markdown("**Match**")
    with col5:
        st.markdown("**Applied**")
    with col6:
        st.markdown("**Actions**")
    
    st.markdown("---")
    
    # Job rows
    for idx, (_, job) in enumerate(filtered_df.iterrows()):
        job_id = job.get('id', idx)
        
        col1, col2, col3, col4, col5, col6 = st.columns([0.5, 2, 1.5, 1, 1, 1])
        
        with col1:
            # Checkbox for selection
            is_selected = st.checkbox("", key=f"select_{job_id}", value=job_id in st.session_state['selected_jobs'])
            if is_selected:
                st.session_state['selected_jobs'].add(job_id)
            else:
                st.session_state['selected_jobs'].discard(job_id)
        
        with col2:
            # Job info
            title = job.get('title', 'Unknown Title')
            company = job.get('company', 'Unknown Company')
            url = job.get('url', job.get('job_url', ''))
            
            st.markdown(f"**{title}**")
            st.markdown(f"🏢 {company}")
            
            if url:
                st.markdown(f"🔗 [View Job]({url})")
        
        with col3:
            # Status badges
            status = job.get('status', 'unknown')
            app_status = job.get('application_status', 'not_applied')
            
            status_colors = {
                'ready_to_apply': '🟢',
                'needs_review': '🟡',
                'scraped': '🔵',
                'new': '⚪',
                'filtered_out': '🔴'
            }
            
            app_colors = {
                'applied': '✅',
                'not_applied': '⏳',
                'rejected': '❌',
                'interview': '🎯'
            }
            
            st.markdown(f"{status_colors.get(status, '❓')} {status}")
            st.markdown(f"{app_colors.get(app_status, '❓')} {app_status}")
        
        with col4:
            # Match score
            match_score = job.get('match_score', 0)
            st.metric("", f"{match_score:.0f}%")
        
        with col5:
            # Quick apply checkbox
            current_applied = job.get('application_status', 'not_applied') == 'applied'
            
            if st.checkbox("Applied", key=f"applied_{job_id}", value=current_applied):
                if not current_applied:
                    # Mark as applied
                    success = update_application_status(job_id, profile_name, "applied", "Manually marked as applied")
                    if success:
                        st.success("✅ Marked as applied!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update")
            else:
                if current_applied:
                    # Unmark as applied
                    success = update_application_status(job_id, profile_name, "not_applied", "Unmarked from applied")
                    if success:
                        st.success("🔄 Unmarked as applied")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update")
        
        with col6:
            # Quick actions
            if st.button("👀", key=f"view_{job_id}", help="View details"):
                st.session_state[f'show_details_{job_id}'] = not st.session_state.get(f'show_details_{job_id}', False)
        
        # Show job details if expanded
        if st.session_state.get(f'show_details_{job_id}', False):
            with st.expander("Job Details", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Location:** {job.get('location', 'Not specified')}")
                    st.markdown(f"**Job Type:** {job.get('job_type', 'Not specified')}")
                    st.markdown(f"**Experience:** {job.get('experience_level', 'Not specified')}")
                
                with col2:
                    st.markdown(f"**Salary:** {job.get('salary_range', 'Not specified')}")
                    st.markdown(f"**Remote:** {job.get('remote_option', 'Not specified')}")
                    st.markdown(f"**Site:** {job.get('site', 'Not specified')}")
                
                if job.get('summary'):
                    st.markdown(f"**Summary:** {job['summary'][:300]}...")
                
                # Manual application form
                st.markdown("**Manual Application Form:**")
                notes = st.text_area("Application Notes", key=f"notes_{job_id}", placeholder="Add notes about your application...")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✅ Mark Applied", key=f"manual_apply_{job_id}"):
                        success = update_application_status(job_id, profile_name, "applied", notes)
                        if success:
                            st.success("✅ Marked as applied!")
                            st.rerun()
                
                with col2:
                    if st.button("❌ Not Interested", key=f"manual_reject_{job_id}"):
                        success = update_application_status(job_id, profile_name, "not_interested", notes)
                        if success:
                            st.success("❌ Marked as not interested")
                            st.rerun()
                
                with col3:
                    if st.button("📝 Save Notes", key=f"save_notes_{job_id}"):
                        success = update_application_status(job_id, profile_name, job.get('application_status', 'not_applied'), notes)
                        if success:
                            st.success("📝 Notes saved!")
        
        st.markdown("---")
    
    # Handle bulk actions
    if st.session_state.get('bulk_action') and st.session_state['selected_jobs']:
        action = st.session_state['bulk_action']
        selected_count = len(st.session_state['selected_jobs'])
        
        if action == 'apply':
            st.info(f"Marking {selected_count} jobs as applied...")
            success_count = 0
            for job_id in st.session_state['selected_jobs']:
                if update_application_status(job_id, profile_name, "applied", "Bulk action - marked as applied"):
                    success_count += 1
            
            st.success(f"✅ Successfully marked {success_count}/{selected_count} jobs as applied!")
            
        elif action == 'reject':
            st.info(f"Marking {selected_count} jobs as not interested...")
            success_count = 0
            for job_id in st.session_state['selected_jobs']:
                if update_application_status(job_id, profile_name, "not_interested", "Bulk action - not interested"):
                    success_count += 1
            
            st.success(f"❌ Successfully marked {success_count}/{selected_count} jobs as not interested!")
        
        elif action == 'reset':
            st.info(f"Resetting {selected_count} jobs...")
            success_count = 0
            for job_id in st.session_state['selected_jobs']:
                if update_application_status(job_id, profile_name, "not_applied", "Bulk action - reset"):
                    success_count += 1
            
            st.success(f"🔄 Successfully reset {success_count}/{selected_count} jobs!")
        
        # Clear bulk action and selections
        st.session_state['bulk_action'] = None
        st.session_state['selected_jobs'] = set()
        st.rerun()

if __name__ == "__main__":
    st.set_page_config(page_title="Manual Application Tracker", layout="wide")
    
    # Mock data for testing
    sample_data = pd.DataFrame([
        {"id": 1, "title": "Software Engineer", "company": "Tech Corp", "status": "ready_to_apply", "match_score": 85, "application_status": "not_applied"},
        {"id": 2, "title": "Data Analyst", "company": "Data Inc", "status": "needs_review", "match_score": 75, "application_status": "not_applied"},
    ])
    
    render_manual_application_tracker(sample_data, "test")
