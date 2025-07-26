#!/usr/bin/env python3
"""
Analytics Dashboard Component
Charts, insights, and performance metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import numpy as np

logger = logging.getLogger(__name__)

def render_analytics_dashboard(df: pd.DataFrame, profile_name: str = "default") -> None:
    """
    Render analytics dashboard with charts and insights.
    
    Args:
        df: DataFrame containing job data
        profile_name: Profile name for database operations
    """
    
    if df.empty:
        render_analytics_empty_state()
        return
    
    # Analytics overview
    render_analytics_overview(df)
    
    # Charts section
    render_analytics_charts(df)
    
    # Insights section
    render_analytics_insights(df)

def render_analytics_empty_state():
    """Render empty state for analytics."""
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem; background: #1e293b; border-radius: 1rem; border: 1px solid #334155;'>
        <div style='font-size: 4rem; margin-bottom: 1rem;'>📊</div>
        <h3 style='color: #f1f5f9; margin-bottom: 1rem;'>No Data for Analytics</h3>
        <p style='color: #cbd5e1; margin-bottom: 2rem;'>Start scraping jobs to see analytics and insights.</p>
    </div>
    """, unsafe_allow_html=True)

def render_analytics_overview(df: pd.DataFrame):
    """Render analytics overview metrics."""
    
    st.markdown("## 📊 Analytics Overview")
    
    # Calculate analytics metrics
    total_jobs = len(df)
    unique_companies = df['company'].nunique() if 'company' in df.columns else 0
    unique_locations = df['location'].nunique() if 'location' in df.columns else 0
    avg_match_score = df['match_score'].mean() if 'match_score' in df.columns else 0
    
    # Time-based metrics
    if 'scraped_at' in df.columns:
        df['scraped_date'] = pd.to_datetime(df['scraped_at'], errors='coerce').dt.date
        date_range = df['scraped_date'].max() - df['scraped_date'].min()
        days_active = date_range.days if date_range else 0
        jobs_per_day = total_jobs / max(days_active, 1)
    else:
        days_active = 0
        jobs_per_day = 0
    
    # Display overview metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    metrics = [
        ("🏢", "Companies", unique_companies, "#3b82f6"),
        ("📍", "Locations", unique_locations, "#10b981"),
        ("🎯", "Avg Match", f"{avg_match_score:.1f}%", "#f59e0b"),
        ("📅", "Days Active", days_active, "#6366f1"),
        ("⚡", "Jobs/Day", f"{jobs_per_day:.1f}", "#ef4444")
    ]
    
    for i, (icon, label, value, color) in enumerate(metrics):
        with [col1, col2, col3, col4, col5][i]:
            st.markdown(f"""
            <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; text-align: center;'>
                <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>{icon}</div>
                <div style='color: {color}; font-size: 1.75rem; font-weight: 700; font-family: monospace; margin-bottom: 0.5rem;'>{value}</div>
                <div style='color: #cbd5e1; font-size: 0.875rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

def render_analytics_charts(df: pd.DataFrame):
    """Render analytics charts."""
    
    st.markdown("## 📈 Charts & Visualizations")
    
    # Create tabs for different chart categories
    chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📊 Status & Progress", "🏢 Companies & Locations", "📅 Time Analysis"])
    
    with chart_tab1:
        render_status_charts(df)
    
    with chart_tab2:
        render_company_location_charts(df)
    
    with chart_tab3:
        render_time_analysis_charts(df)

def render_status_charts(df: pd.DataFrame):
    """Render status and progress charts."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Status distribution pie chart
        if 'status_text' in df.columns:
            status_counts = df['status_text'].value_counts()
            
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Job Status Distribution",
                color_discrete_sequence=['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#6366f1']
            )
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#f1f5f9',
                title_font_color='#f1f5f9',
                title_font_size=16,
                showlegend=True,
                legend=dict(
                    font=dict(color='#f1f5f9')
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Status data not available")
    
    with col2:
        # Match score distribution
        if 'match_score' in df.columns and df['match_score'].notna().any():
            fig = px.histogram(
                df,
                x='match_score',
                nbins=20,
                title="Match Score Distribution",
                color_discrete_sequence=['#3b82f6']
            )
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#f1f5f9',
                title_font_color='#f1f5f9',
                title_font_size=16,
                xaxis=dict(gridcolor='#334155'),
                yaxis=dict(gridcolor='#334155')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Match score data not available")

def render_company_location_charts(df: pd.DataFrame):
    """Render company and location analysis charts."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top companies
        if 'company' in df.columns:
            top_companies = df['company'].value_counts().head(10)
            
            fig = px.bar(
                x=top_companies.values,
                y=top_companies.index,
                orientation='h',
                title="Top 10 Companies",
                color=top_companies.values,
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#f1f5f9',
                title_font_color='#f1f5f9',
                title_font_size=16,
                xaxis=dict(gridcolor='#334155'),
                yaxis=dict(gridcolor='#334155'),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Company data not available")
    
    with col2:
        # Top locations
        if 'location' in df.columns:
            top_locations = df['location'].value_counts().head(10)
            
            fig = px.bar(
                x=top_locations.values,
                y=top_locations.index,
                orientation='h',
                title="Top 10 Locations",
                color=top_locations.values,
                color_continuous_scale='Greens'
            )
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#f1f5f9',
                title_font_color='#f1f5f9',
                title_font_size=16,
                xaxis=dict(gridcolor='#334155'),
                yaxis=dict(gridcolor='#334155'),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Location data not available")

def render_time_analysis_charts(df: pd.DataFrame):
    """Render time-based analysis charts."""
    
    if 'scraped_at' not in df.columns:
        st.info("Time data not available for analysis")
        return
    
    # Prepare time data
    df_time = df.copy()
    df_time['scraped_date'] = pd.to_datetime(df_time['scraped_at'], errors='coerce')
    df_time = df_time.dropna(subset=['scraped_date'])
    
    if df_time.empty:
        st.info("No valid time data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Jobs over time
        daily_jobs = df_time.groupby(df_time['scraped_date'].dt.date).size().reset_index()
        daily_jobs.columns = ['date', 'count']
        
        fig = px.line(
            daily_jobs,
            x='date',
            y='count',
            title="Jobs Scraped Over Time",
            color_discrete_sequence=['#3b82f6']
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9',
            title_font_color='#f1f5f9',
            title_font_size=16,
            xaxis=dict(gridcolor='#334155'),
            yaxis=dict(gridcolor='#334155')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Hourly distribution
        df_time['hour'] = df_time['scraped_date'].dt.hour
        hourly_dist = df_time['hour'].value_counts().sort_index()
        
        fig = px.bar(
            x=hourly_dist.index,
            y=hourly_dist.values,
            title="Jobs by Hour of Day",
            color=hourly_dist.values,
            color_continuous_scale='Oranges'
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9',
            title_font_color='#f1f5f9',
            title_font_size=16,
            xaxis=dict(gridcolor='#334155', title='Hour'),
            yaxis=dict(gridcolor='#334155', title='Job Count'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_analytics_insights(df: pd.DataFrame):
    """Render analytics insights and recommendations."""
    
    st.markdown("## 💡 Insights & Recommendations")
    
    insights = generate_insights(df)
    
    if not insights:
        st.info("No insights available yet. More data needed for analysis.")
        return
    
    # Display insights in cards
    for insight in insights:
        icon = insight.get('icon', '💡')
        title = insight.get('title', 'Insight')
        message = insight.get('message', '')
        insight_type = insight.get('type', 'info')
        
        # Color based on type
        colors = {
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#ef4444',
            'info': '#3b82f6'
        }
        color = colors.get(insight_type, '#3b82f6')
        
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #334155; margin-bottom: 1rem; border-left: 4px solid {color};'>
            <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;'>
                <div style='font-size: 1.5rem;'>{icon}</div>
                <div style='color: #f1f5f9; font-weight: 600; font-size: 1.125rem;'>{title}</div>
            </div>
            <div style='color: #cbd5e1; line-height: 1.5;'>{message}</div>
        </div>
        """, unsafe_allow_html=True)

def generate_insights(df: pd.DataFrame) -> List[Dict[str, str]]:
    """Generate insights based on job data analysis."""
    
    if df.empty:
        return []
    
    insights = []
    
    # Application success rate insight
    if 'status_text' in df.columns:
        applied_count = len(df[df['status_text'] == 'Applied'])
        total_count = len(df)
        success_rate = (applied_count / total_count * 100) if total_count > 0 else 0
        
        if success_rate > 20:
            insights.append({
                'icon': '🎯',
                'title': 'High Success Rate',
                'message': f'Your application success rate is {success_rate:.1f}%, which is above average. Keep up the good work!',
                'type': 'success'
            })
        elif success_rate < 5:
            insights.append({
                'icon': '⚠️',
                'title': 'Low Success Rate',
                'message': f'Your application success rate is {success_rate:.1f}%. Consider refining your job filters or improving your application materials.',
                'type': 'warning'
            })
    
    # Company diversity insight
    if 'company' in df.columns:
        unique_companies = df['company'].nunique()
        total_jobs = len(df)
        diversity_ratio = unique_companies / total_jobs if total_jobs > 0 else 0
        
        if diversity_ratio > 0.8:
            insights.append({
                'icon': '🏢',
                'title': 'High Company Diversity',
                'message': f'You\'re applying to {unique_companies} different companies out of {total_jobs} jobs. Great diversity in your job search!',
                'type': 'success'
            })
        elif diversity_ratio < 0.3:
            insights.append({
                'icon': '🔄',
                'title': 'Consider More Companies',
                'message': f'You\'re focusing on {unique_companies} companies. Consider expanding to more companies for better opportunities.',
                'type': 'info'
            })
    
    # Time-based insights
    if 'scraped_at' in df.columns:
        df_time = df.copy()
        df_time['scraped_date'] = pd.to_datetime(df_time['scraped_at'], errors='coerce')
        df_time = df_time.dropna(subset=['scraped_date'])
        
        if not df_time.empty:
            # Recent activity
            recent_cutoff = datetime.now() - timedelta(days=7)
            recent_jobs = len(df_time[df_time['scraped_date'] > recent_cutoff])
            
            if recent_jobs == 0:
                insights.append({
                    'icon': '📅',
                    'title': 'No Recent Activity',
                    'message': 'No jobs scraped in the last 7 days. Consider running the scraper to find new opportunities.',
                    'type': 'warning'
                })
            elif recent_jobs > 50:
                insights.append({
                    'icon': '🚀',
                    'title': 'High Activity',
                    'message': f'You\'ve scraped {recent_jobs} jobs in the last 7 days. Great momentum in your job search!',
                    'type': 'success'
                })
    
    # Match score insights
    if 'match_score' in df.columns and df['match_score'].notna().any():
        avg_match = df['match_score'].mean()
        high_match_jobs = len(df[df['match_score'] > 80])
        
        if avg_match > 70:
            insights.append({
                'icon': '🎯',
                'title': 'Good Job Matching',
                'message': f'Your average match score is {avg_match:.1f}%. You\'re finding well-matched opportunities!',
                'type': 'success'
            })
        elif high_match_jobs > 0:
            insights.append({
                'icon': '⭐',
                'title': 'High-Match Opportunities',
                'message': f'You have {high_match_jobs} jobs with >80% match score. Prioritize applying to these first!',
                'type': 'info'
            })
    
    return insights