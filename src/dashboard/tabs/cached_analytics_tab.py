#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cached Analytics Tab - Improved with Configurable Caching
Analytics tab with cached chart data, Configurable refresh, and fallback analytics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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


class CachedAnalyticsRenderer:
    """Analytics tab with Automated caching and Configurable refresh."""
    
    def __init__(self):
        self.cache_manager = get_Configurable_cache()
        self.service_factory = get_auto_healing_factory()
        self.chart_cache_ttl = 300  # 5 minutes
        
    def render_with_Configurable_caching(self, df: pd.DataFrame) -> None:
        """Render analytics with Configurable caching."""
        try:
            if df.empty:
                self._render_empty_analytics_state()
                return
            
            # Analytics overview
            self._render_cached_overview(df)
            
            # Chart sections with caching
            col1, col2 = st.columns(2)
            
            with col1:
                self._render_status_distribution_cached(df)
                self._render_timeline_analysis_cached(df)
            
            with col2:
                self._render_company_analysis_cached(df)
                self._render_salary_analysis_cached(df)
            
            # Improved analytics
            self._render_Improved_analytics_cached(df)
            
        except Exception as e:
            logger.error(f"Error in cached analytics tab: {e}")
            self._render_fallback_analytics(df)
    
    def _render_cached_overview(self, df: pd.DataFrame) -> None:
        """Render overview metrics with caching."""
        cache_key = f"analytics_overview_{len(df)}_{hash(str(df['status'].value_counts().to_dict()))}"
        
        def compute_overview_metrics():
            total_jobs = len(df)
            applied_rate = (len(df[df['status'] == 'applied']) / total_jobs * 100) if total_jobs > 0 else 0
            response_rate = (len(df[df['status'].isin(['interview', 'offer'])]) / len(df[df['status'] == 'applied']) * 100) if len(df[df['status'] == 'applied']) > 0 else 0
            
            # Calculate trends
            recent_jobs = df[df['scraped_at'] > (datetime.now() - timedelta(days=30))] if 'scraped_at' in df.columns else df
            trend = len(recent_jobs) / 30 if len(recent_jobs) > 0 else 0
            
            return {
                'total_jobs': total_jobs,
                'applied_rate': round(applied_rate, 1),
                'response_rate': round(response_rate, 1),
                'daily_trend': round(trend, 2)
            }
        
        metrics = self.cache_manager.Configurable_get(cache_key, compute_overview_metrics)
        
        st.subheader("📊 Analytics Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Jobs",
                metrics['total_jobs'],
                delta=None
            )
        
        with col2:
            st.metric(
                "Application Rate",
                f"{metrics['applied_rate']}%",
                delta=None
            )
        
        with col3:
            st.metric(
                "Response Rate",
                f"{metrics['response_rate']}%",
                delta=None
            )
        
        with col4:
            st.metric(
                "Daily Trend",
                f"{metrics['daily_trend']} jobs/day",
                delta=None
            )
    
    def _render_status_distribution_cached(self, df: pd.DataFrame) -> None:
        """Render status distribution chart with caching."""
        cache_key = f"status_chart_{hash(str(df['status'].value_counts().to_dict()))}"
        
        def create_status_chart():
            status_counts = df['status'].value_counts()
            
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Job Status Distribution",
                color_discrete_map={
                    'pending': '#FFA500',
                    'applied': '#4CAF50',
                    'rejected': '#F44336',
                    'interview': '#2196F3',
                    'offer': '#9C27B0'
                }
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            
            return fig
        
        fig = self.cache_manager.Configurable_get(cache_key, create_status_chart)
        
        st.subheader("📈 Status Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_timeline_analysis_cached(self, df: pd.DataFrame) -> None:
        """Render timeline analysis with caching."""
        if 'scraped_at' not in df.columns:
            st.info("Date information not available for timeline analysis.")
            return
        
        cache_key = f"timeline_chart_{hash(str(df['scraped_at'].dt.date.value_counts().to_dict()))}"
        
        def create_timeline_chart():
            # Convert to datetime if needed
            df_copy = df.copy()
            df_copy['scraped_at'] = pd.to_datetime(df_copy['scraped_at'])
            
            # Group by date
            daily_counts = df_copy.groupby(df_copy['scraped_at'].dt.date).size()
            
            fig = px.line(
                x=daily_counts.index,
                y=daily_counts.values,
                title="Job Applications Over Time",
                labels={'x': 'Date', 'y': 'Number of Jobs'}
            )
            
            fig.update_layout(height=400)
            
            return fig
        
        fig = self.cache_manager.Configurable_get(cache_key, create_timeline_chart)
        
        st.subheader("📅 Timeline Analysis")
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_company_analysis_cached(self, df: pd.DataFrame) -> None:
        """Render company analysis with caching."""
        if 'company' not in df.columns:
            st.info("Company information not available.")
            return
        
        cache_key = f"company_chart_{hash(str(df['company'].value_counts().head(10).to_dict()))}"
        
        def create_company_chart():
            company_counts = df['company'].value_counts().head(10)
            
            fig = px.bar(
                x=company_counts.values,
                y=company_counts.index,
                orientation='h',
                title="Top Companies (Job Count)",
                labels={'x': 'Number of Jobs', 'y': 'Company'}
            )
            
            fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            
            return fig
        
        fig = self.cache_manager.Configurable_get(cache_key, create_company_chart)
        
        st.subheader("🏢 Company Analysis")
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_salary_analysis_cached(self, df: pd.DataFrame) -> None:
        """Render salary analysis with caching."""
        if 'salary' not in df.columns or df['salary'].isna().all():
            st.info("Salary information not available for analysis.")
            return
        
        cache_key = f"salary_chart_{hash(str(df['salary'].dropna().describe().to_dict()))}"
        
        def create_salary_chart():
            salary_data = df['salary'].dropna()
            
            # Convert salary strings to numeric if needed
            if salary_data.dtype == 'object':
                # Simple extraction of numbers from salary strings
                salary_numeric = pd.to_numeric(
                    salary_data.astype(str).str.extract(r'(\d+)')[0], 
                    errors='coerce'
                )
                salary_data = salary_numeric.dropna()
            
            if len(salary_data) == 0:
                st.info("No valid salary data available.")
                return None
            
            fig = px.histogram(
                x=salary_data,
                title="Salary Distribution",
                labels={'x': 'Salary', 'y': 'Frequency'},
                nbins=20
            )
            
            fig.update_layout(height=400)
            
            return fig
        
        fig = self.cache_manager.Configurable_get(cache_key, create_salary_chart)
        
        if fig is not None:
            st.subheader("💰 Salary Analysis")
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_Improved_analytics_cached(self, df: pd.DataFrame) -> None:
        """Render Improved analytics with caching."""
        st.subheader("🔬 Improved Analytics")
        
        tab1, tab2, tab3 = st.tabs(["Success Metrics", "Location Analysis", "Priority Analysis"])
        
        with tab1:
            self._render_success_metrics_cached(df)
        
        with tab2:
            self._render_location_analysis_cached(df)
        
        with tab3:
            self._render_priority_analysis_cached(df)
    
    def _render_success_metrics_cached(self, df: pd.DataFrame) -> None:
        """Render success metrics with caching."""
        cache_key = f"success_metrics_{hash(str(df['status'].value_counts().to_dict()))}"
        
        def compute_success_metrics():
            total_applied = len(df[df['status'] == 'applied'])
            interviews = len(df[df['status'] == 'interview'])
            offers = len(df[df['status'] == 'offer'])
            
            interview_rate = (interviews / total_applied * 100) if total_applied > 0 else 0
            offer_rate = (offers / total_applied * 100) if total_applied > 0 else 0
            
            # Success funnel data
            funnel_data = {
                'Stage': ['Applied', 'Interview', 'Offer'],
                'Count': [total_applied, interviews, offers],
                'Rate': [100, interview_rate, offer_rate]
            }
            
            return funnel_data
        
        funnel_data = self.cache_manager.Configurable_get(cache_key, compute_success_metrics)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Success rates
            st.markdown("**Success Rates:**")
            st.metric("Interview Rate", f"{funnel_data['Rate'][1]:.1f}%")
            st.metric("Offer Rate", f"{funnel_data['Rate'][2]:.1f}%")
        
        with col2:
            # Funnel chart
            fig = go.Figure(go.Funnel(
                y=funnel_data['Stage'],
                x=funnel_data['Count'],
                textinfo="value+percent initial"
            ))
            
            fig.update_layout(title="Application Funnel", height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_location_analysis_cached(self, df: pd.DataFrame) -> None:
        """Render location analysis with caching."""
        if 'location' not in df.columns:
            st.info("Location information not available.")
            return
        
        cache_key = f"location_chart_{hash(str(df['location'].value_counts().head(10).to_dict()))}"
        
        def create_location_chart():
            location_counts = df['location'].value_counts().head(10)
            
            fig = px.bar(
                x=location_counts.index,
                y=location_counts.values,
                title="Job Distribution by Location",
                labels={'x': 'Location', 'y': 'Number of Jobs'}
            )
            
            fig.update_layout(height=400, xaxis_tickangle=-45)
            
            return fig
        
        fig = self.cache_manager.Configurable_get(cache_key, create_location_chart)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_priority_analysis_cached(self, df: pd.DataFrame) -> None:
        """Render priority analysis with caching."""
        if 'priority' not in df.columns:
            st.info("Priority information not available.")
            return
        
        cache_key = f"priority_chart_{hash(str(df['priority'].value_counts().to_dict()))}"
        
        def create_priority_chart():
            priority_counts = df['priority'].value_counts()
            
            # Create a stacked bar chart showing priority vs status
            priority_status = df.groupby(['priority', 'status']).size().unstack(fill_value=0)
            
            fig = px.bar(
                priority_status,
                title="Priority vs Status Distribution",
                labels={'value': 'Count', 'index': 'Priority'}
            )
            
            fig.update_layout(height=400)
            
            return fig
        
        fig = self.cache_manager.Configurable_get(cache_key, create_priority_chart)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_empty_analytics_state(self) -> None:
        """Render empty state with suggestions."""
        st.info("No data available for analytics. Start by adding some jobs!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Quick Actions:**")
            if st.button("🔍 Search Jobs"):
                st.session_state.active_tab = "JobSpy"
                st.rerun()
        
        with col2:
            st.markdown("**Analytics Tips:**")
            st.markdown("• Add more jobs to see meaningful analytics")
            st.markdown("• Update job statuses for better insights")
            st.markdown("• Use the Jobs tab to manage applications")
    
    def _render_fallback_analytics(self, df: pd.DataFrame) -> None:
        """Render fallback analytics when Configurable features fail."""
        st.warning("Configurable analytics temporarily unavailable. Using basic view.")
        
        if not df.empty:
            # Basic metrics
            st.subheader("Basic Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Jobs", len(df))
            
            with col2:
                applied_count = len(df[df['status'] == 'applied'])
                st.metric("Applied", applied_count)
            
            with col3:
                pending_count = len(df[df['status'] == 'pending'])
                st.metric("Pending", pending_count)
            
            # Basic status breakdown
            st.subheader("Status Breakdown")
            status_counts = df['status'].value_counts()
            st.bar_chart(status_counts)
        else:
            st.info("No data available for analysis.")
    
    def invalidate_analytics_cache(self) -> None:
        """Invalidate analytics-related cache entries."""
        self.cache_manager.invalidate_pattern("analytics_*")
        self.cache_manager.invalidate_pattern("*_chart_*")
        self.cache_manager.invalidate_pattern("success_metrics_*")


# Public API
def render_cached_analytics_tab(df: pd.DataFrame) -> None:
    """Render analytics tab with Configurable caching."""
    renderer = CachedAnalyticsRenderer()
    renderer.render_with_Configurable_caching(df)


# Fallback function for compatibility
def render_analytics_tab(df: pd.DataFrame) -> None:
    """Compatibility function - delegates to cached version."""
    render_cached_analytics_tab(df)
