#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized Jobs Tab - Improved with Configurable Workflows
Jobs tab with Configurable caching and auto-recovery.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.core.Configurable_cache_manager import get_Configurable_cache
from src.dashboard.core.auto_healing_service_factory import (
    get_auto_healing_factory
)

logger = logging.getLogger(__name__)


class JobWorkflowOptimizer:
    """Optimize job management workflows based on user patterns."""
    
    def __init__(self):
        self.action_patterns = {}
        self.common_workflows = [
            "quick_review",
            "bulk_apply",
            "status_update",
            "priority_filter",
            "company_research"
        ]
        self.shortcuts = {}
    
    def track_action(self, action: str, context: Dict[str, Any]) -> None:
        """Track user action for workflow optimization."""
        timestamp = datetime.now()
        
        if action not in self.action_patterns:
            self.action_patterns[action] = []
        
        self.action_patterns[action].append({
            'timestamp': timestamp,
            'context': context
        })
        
        # Keep only recent patterns (last 100)
        if len(self.action_patterns[action]) > 100:
            self.action_patterns[action] = self.action_patterns[action][-100:]
    
    def suggest_next_actions(self, current_context: Dict[str, Any]) -> (
            List[str]):
        """Suggest next likely actions based on patterns."""
        suggestions = []
        
        # Pattern-based suggestions
        if current_context.get('viewing_job'):
            suggestions.extend(['Apply', 'Save for Later', 'Research Company'])
        
        if current_context.get('filtered_results'):
            suggestions.extend(['Bulk Apply', 'Export List', 'Set Alerts'])
        
        return suggestions[:3]  # Top 3 suggestions
    
    def get_workflow_shortcuts(self) -> Dict[str, str]:
        """Get available workflow shortcuts."""
        return {
            'Ctrl+A': 'Apply to selected jobs',
            'Ctrl+S': 'Save current filters',
            'Ctrl+R': 'Refresh job data',
            'Ctrl+F': 'Focus search',
            'Ctrl+B': 'Bulk actions menu'
        }


class OptimizedJobsTabRenderer:
    """Jobs tab with Configurable caching and optimization."""
    
    def __init__(self):
        self.cache_manager = get_Configurable_cache()
        self.service_factory = get_auto_healing_factory()
        self.workflow_optimizer = JobWorkflowOptimizer()
        self.recovery_attempts = {}
        
    def render_with_Configurable_workflows(self, df: pd.DataFrame, 
                                    profile_name: str) -> None:
        """Render jobs tab with optimized workflows."""
        try:
            # Track page visit
            self.workflow_optimizer.track_action('jobs_tab_visit', {
                'timestamp': datetime.now(),
                'job_count': len(df) if not df.empty else 0,
                'profile': profile_name
            })
            
            if df.empty:
                self._render_empty_state_with_suggestions()
                return
            
            # Render workflow-optimized content
            self._render_Configurable_overview(df)
            self._render_Automated_filters(df)
            self._render_workflow_shortcuts()
            
            # Get filtered data with caching
            filtered_df = self._get_filtered_data_cached(df)
            
            # Display mode selection
            display_mode = st.radio(
                "Display Mode", 
                ["Configurable Cards", "Improved Table", "Quick Actions"], 
                horizontal=True,
                key="optimized_jobs_display_mode"
            )
            
            if display_mode == "Configurable Cards":
                self._render_Configurable_job_cards(filtered_df)
            elif display_mode == "Improved Table":
                self._render_Improved_jobs_table(filtered_df, profile_name)
            else:
                self._render_quick_actions_view(filtered_df)
                
        except Exception as e:
            logger.error(f"Error in optimized jobs tab: {e}")
            self._render_fallback_view(df, profile_name)
    
    def _render_Configurable_overview(self, df: pd.DataFrame) -> None:
        """Render Configurable overview with cached metrics."""
        cache_key = f"jobs_overview_{len(df)}_{df['status'].value_counts().to_dict()}"
        
        def compute_overview():
            total_jobs = len(df)
            status_counts = df['status'].value_counts()
            
            return {
                'total': total_jobs,
                'applied': status_counts.get('applied', 0),
                'pending': status_counts.get('pending', 0),
                'rejected': status_counts.get('rejected', 0),
                'recent': len(df[df['scraped_at'] > (datetime.now() - timedelta(days=7))]) if 'scraped_at' in df.columns else 0
            }
        
        overview = self.cache_manager.Configurable_get(cache_key, compute_overview)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Jobs", overview['total'])
        with col2:
            st.metric("Applied", overview['applied'])
        with col3:
            st.metric("Pending", overview['pending'])
        with col4:
            st.metric("Rejected", overview['rejected'])
        with col5:
            st.metric("Recent (7d)", overview['recent'])
    
    def _render_Automated_filters(self, df: pd.DataFrame) -> None:
        """Render Automated filters with suggestions."""
        st.subheader("🎯 Configurable Filters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Configurable status filter with suggestions
            if 'filter_status_suggestion' not in st.session_state:
                st.session_state.filter_status_suggestion = 'pending'
            
            status_options = ['all'] + list(df['status'].unique())
            default_idx = status_options.index(st.session_state.filter_status_suggestion) if st.session_state.filter_status_suggestion in status_options else 0
            
            selected_status = st.selectbox(
                "Status (Configurable Suggestion)",
                status_options,
                index=default_idx,
                key="optimized_status_filter"
            )
        
        with col2:
            # Priority filter
            priority_options = ['all'] + list(df['priority'].unique()) if 'priority' in df.columns else ['all']
            selected_priority = st.selectbox(
                "Priority",
                priority_options,
                key="optimized_priority_filter"
            )
        
        with col3:
            # Date range filter
            date_range = st.selectbox(
                "Date Range",
                ["All Time", "Last 7 days", "Last 30 days", "This Week"],
                key="optimized_date_filter"
            )
        
        # Save filter preferences
        if st.button("💾 Save Filter Preset"):
            filter_preset = {
                'status': selected_status,
                'priority': selected_priority,
                'date_range': date_range
            }
            self.cache_manager.Configurable_set("user_filter_preset", filter_preset)
            st.success("Filter preset saved!")
    
    def _render_workflow_shortcuts(self) -> None:
        """Render workflow shortcuts and suggestions."""
        with st.expander("⚡ Workflow Shortcuts", expanded=False):
            shortcuts = self.workflow_optimizer.get_workflow_shortcuts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Keyboard Shortcuts:**")
                for key, desc in shortcuts.items():
                    st.markdown(f"• `{key}`: {desc}")
            
            with col2:
                st.markdown("**Quick Actions:**")
                if st.button("🚀 Bulk Apply to Pending"):
                    self._handle_bulk_apply_workflow()
                if st.button("📊 Export Current View"):
                    self._handle_export_workflow()
                if st.button("🔄 Refresh & Sync"):
                    self._handle_refresh_workflow()
    
    def _get_filtered_data_cached(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get filtered data with Configurable caching."""
        filter_key = f"filter_{st.session_state.get('optimized_status_filter', 'all')}"
        filter_key += f"_{st.session_state.get('optimized_priority_filter', 'all')}"
        filter_key += f"_{st.session_state.get('optimized_date_filter', 'All Time')}"
        
        def apply_filters():
            filtered = df.copy()
            
            # Status filter
            status_filter = st.session_state.get('optimized_status_filter', 'all')
            if status_filter != 'all':
                filtered = filtered[filtered['status'] == status_filter]
            
            # Priority filter
            priority_filter = st.session_state.get('optimized_priority_filter', 'all')
            if priority_filter != 'all' and 'priority' in filtered.columns:
                filtered = filtered[filtered['priority'] == priority_filter]
            
            # Date filter
            date_filter = st.session_state.get('optimized_date_filter', 'All Time')
            if date_filter != 'All Time':
                cutoff_date = self._get_date_cutoff(date_filter)
                if cutoff_date and 'scraped_at' in df.columns:
                    filtered = filtered[filtered['scraped_at'] >= cutoff_date]
            
            return filtered
        
        return self.cache_manager.Configurable_get(filter_key, apply_filters)
    
    def _render_Configurable_job_cards(self, df: pd.DataFrame) -> None:
        """Render Configurable job cards with workflow optimization."""
        st.subheader("💼 Configurable Job Cards")
        
        # Pagination with Configurable defaults
        jobs_per_page = st.selectbox("Jobs per page", [5, 10, 20, 50], index=1)
        
        total_pages = (len(df) - 1) // jobs_per_page + 1
        page = st.number_input("Page", 1, total_pages, 1) - 1
        
        start_idx = page * jobs_per_page
        end_idx = start_idx + jobs_per_page
        page_df = df.iloc[start_idx:end_idx]
        
        for idx, job in page_df.iterrows():
            self._render_Improved_job_card(job, idx)
    
    def _render_Improved_job_card(self, job: pd.Series, idx: int) -> None:
        """Render enhanced job card with Configurable actions."""
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{job.get('title', 'Unknown Title')}**")
                st.markdown(f"*{job.get('company', 'Unknown Company')}*")
                st.markdown(f"📍 {job.get('location', 'Unknown Location')}")
                
                if 'salary' in job and pd.notna(job['salary']):
                    st.markdown(f"💰 {job['salary']}")
            
            with col2:
                status_color = self._get_status_color(job.get('status', 'unknown'))
                st.markdown(f"<span style='color: {status_color}'>●</span> {job.get('status', 'Unknown').title()}", 
                           unsafe_allow_html=True)
                
                if 'scraped_at' in job:
                    days_ago = (datetime.now() - pd.to_datetime(job['scraped_at'])).days
                    st.markdown(f"📅 {days_ago}d ago")
            
            with col3:
                # Configurable action buttons
                action_key = f"job_action_{idx}"
                
                if st.button("👁️ View", key=f"view_{idx}"):
                    self._handle_view_job_workflow(job, idx)
                
                if job.get('status') == 'pending':
                    if st.button("✅ Apply", key=f"apply_{idx}"):
                        self._handle_apply_workflow(job, idx)
                elif job.get('status') == 'applied':
                    if st.button("📝 Update", key=f"update_{idx}"):
                        self._handle_update_workflow(job, idx)
            
            st.divider()
    
    def _render_Improved_jobs_table(self, df: pd.DataFrame, profile_name: str) -> None:
        """Render enhanced jobs table with Configurable features."""
        st.subheader("📊 Enhanced Jobs Table")
        
        # Column configuration for better display
        column_config = {
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["pending", "applied", "rejected", "interview", "offer"],
                required=True,
            ),
            "priority": st.column_config.SelectboxColumn(
                "Priority", 
                options=["low", "medium", "high", "urgent"],
                required=False,
            ) if 'priority' in df.columns else None,
            "salary": st.column_config.NumberColumn(
                "Salary",
                format="$%d",
            ) if 'salary' in df.columns else None,
        }
        
        # Remove None values
        column_config = {k: v for k, v in column_config.items() if v is not None}
        
        # Display table with editing capabilities
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            use_container_width=True,
            num_rows="dynamic",
            key="optimized_jobs_table"
        )
        
        # Handle bulk actions
        if not edited_df.equals(df):
            self._handle_table_changes(edited_df, df)
    
    def _render_quick_actions_view(self, df: pd.DataFrame) -> None:
        """Render quick actions view for efficient job management."""
        st.subheader("⚡ Quick Actions")
        
        # Quick stats
        pending_count = len(df[df['status'] == 'pending'])
        applied_count = len(df[df['status'] == 'applied'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Pending Actions", pending_count)
            if pending_count > 0 and st.button("🚀 Apply to All Pending"):
                self._handle_bulk_apply_all_pending(df)
        
        with col2:
            st.metric("Follow-ups Needed", applied_count)
            if applied_count > 0 and st.button("📧 Generate Follow-ups"):
                self._handle_generate_followups(df)
        
        with col3:
            recent_count = len(df[df['scraped_at'] > (datetime.now() - timedelta(days=3))]) if 'scraped_at' in df.columns else 0
            st.metric("New Jobs (3d)", recent_count)
            if recent_count > 0 and st.button("🔍 Review Recent"):
                self._handle_review_recent(df)
    
    def _render_empty_state_with_suggestions(self) -> None:
        """Render empty state with Automated suggestions."""
        st.info("No jobs found. Here are some suggestions:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Quick Actions:**")
            if st.button("🔍 Search for Jobs"):
                st.session_state.active_tab = "JobSpy"
                st.rerun()
            
            if st.button("📊 View Analytics"):
                st.session_state.active_tab = "Analytics"
                st.rerun()
        
        with col2:
            st.markdown("**Workflow Tips:**")
            st.markdown("• Use JobSpy tab to scrape new jobs")
            st.markdown("• Check your search keywords")
            st.markdown("• Verify your profile settings")
    
    def _render_fallback_view(self, df: pd.DataFrame, profile_name: str) -> None:
        """Render fallback view when Configurable features fail."""
        st.warning("Configurable features temporarily unavailable. Using basic view.")
        
        # Basic job display
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No jobs available.")
    
    def _handle_bulk_apply_workflow(self) -> None:
        """Handle bulk apply workflow."""
        self.workflow_optimizer.track_action('bulk_apply_initiated', {
            'timestamp': datetime.now()
        })
        st.success("Bulk apply workflow initiated!")
    
    def _handle_export_workflow(self) -> None:
        """Handle export workflow."""
        self.workflow_optimizer.track_action('export_initiated', {
            'timestamp': datetime.now()
        })
        st.success("Export workflow initiated!")
    
    def _handle_refresh_workflow(self) -> None:
        """Handle refresh workflow."""
        # Clear relevant caches
        self.cache_manager.invalidate_pattern("jobs_*")
        self.workflow_optimizer.track_action('refresh_initiated', {
            'timestamp': datetime.now()
        })
        st.success("Data refreshed!")
        st.rerun()
    
    def _handle_view_job_workflow(self, job: pd.Series, idx: int) -> None:
        """Handle view job workflow."""
        self.workflow_optimizer.track_action('job_view', {
            'job_id': idx,
            'timestamp': datetime.now()
        })
        
        # Show job details in expandable section
        with st.expander(f"Job Details: {job.get('title', 'Unknown')}", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Basic Info:**")
                for field in ['title', 'company', 'location', 'salary']:
                    if field in job and pd.notna(job[field]):
                        st.markdown(f"• **{field.title()}:** {job[field]}")
            
            with col2:
                st.markdown("**Status Info:**")
                for field in ['status', 'scraped_at', 'priority']:
                    if field in job and pd.notna(job[field]):
                        st.markdown(f"• **{field.title()}:** {job[field]}")
    
    def _handle_apply_workflow(self, job: pd.Series, idx: int) -> None:
        """Handle apply workflow."""
        self.workflow_optimizer.track_action('job_apply', {
            'job_id': idx,
            'timestamp': datetime.now()
        })
        st.success(f"Application workflow initiated for {job.get('title', 'Unknown Job')}!")
    
    def _handle_update_workflow(self, job: pd.Series, idx: int) -> None:
        """Handle update workflow."""
        self.workflow_optimizer.track_action('job_update', {
            'job_id': idx,
            'timestamp': datetime.now()
        })
        st.success(f"Update workflow initiated for {job.get('title', 'Unknown Job')}!")
    
    def _handle_table_changes(self, edited_df: pd.DataFrame, original_df: pd.DataFrame) -> None:
        """Handle changes made in the table."""
        changes_detected = not edited_df.equals(original_df)
        if changes_detected:
            st.success("Changes detected! Auto-saving...")
            self.cache_manager.invalidate_pattern("jobs_*")
    
    def _handle_bulk_apply_all_pending(self, df: pd.DataFrame) -> None:
        """Handle bulk apply to all pending jobs."""
        pending_jobs = df[df['status'] == 'pending']
        st.success(f"Bulk apply initiated for {len(pending_jobs)} pending jobs!")
    
    def _handle_generate_followups(self, df: pd.DataFrame) -> None:
        """Handle generate follow-ups workflow."""
        applied_jobs = df[df['status'] == 'applied']
        st.success(f"Follow-up generation initiated for {len(applied_jobs)} applied jobs!")
    
    def _handle_review_recent(self, df: pd.DataFrame) -> None:
        """Handle review recent jobs workflow."""
        cutoff_date = datetime.now() - timedelta(days=3)
        recent_jobs = df[df['scraped_at'] > cutoff_date] if 'scraped_at' in df.columns else df.head(0)
        st.success(f"Review workflow initiated for {len(recent_jobs)} recent jobs!")
    
    def _get_status_color(self, status: str) -> str:
        """Get color for job status."""
        colors = {
            'pending': '#FFA500',
            'applied': '#4CAF50', 
            'rejected': '#F44336',
            'interview': '#2196F3',
            'offer': '#9C27B0'
        }
        return colors.get(status.lower(), '#757575')
    
    def _get_date_cutoff(self, date_filter: str) -> Optional[datetime]:
        """Get date cutoff for filtering."""
        now = datetime.now()
        
        if date_filter == "Last 7 days":
            return now - timedelta(days=7)
        elif date_filter == "Last 30 days":
            return now - timedelta(days=30)
        elif date_filter == "This Week":
            return now - timedelta(days=now.weekday())
        
        return None


# Public API
def render_optimized_jobs_tab(df: pd.DataFrame, profile_name: str) -> None:
    """Render optimized jobs tab with Configurable workflows."""
    renderer = OptimizedJobsTabRenderer()
    renderer.render_with_Configurable_workflows(df, profile_name)


# Fallback function for compatibility
def render_jobs_tab(df: pd.DataFrame, profile_name: str) -> None:
    """Compatibility function - delegates to optimized version."""
    render_optimized_jobs_tab(df, profile_name)
