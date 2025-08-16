#!/usr/bin/env python3
"""
Analytics Tab Module
Handles charts, insights, and data visualization.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging

logger = logging.getLogger(__name__)


def render_analytics_tab(df: pd.DataFrame) -> None:
    """Render the analytics tab with charts and insights."""
    
    if df.empty:
        render_analytics_empty_state()
        return
    
    # Analytics sections
    render_analytics_overview(df)
    render_analytics_charts(df)
    render_analytics_insights(df)


def render_analytics_empty_state():
    """Render empty state for analytics."""
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem; 
                background: #1e293b; border-radius: 1rem; 
                border: 1px solid #334155;'>
        <div style='font-size: 4rem; margin-bottom: 1rem;'>📊</div>
        <h3 style='color: #f1f5f9; margin-bottom: 1rem;'>No Data for Analytics</h3>
        <p style='color: #cbd5e1; margin-bottom: 2rem;'>
            Start scraping jobs to see analytics and insights.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_analytics_overview(df: pd.DataFrame) -> None:
    """Render analytics overview metrics."""
    
    st.markdown("## 📊 Analytics Overview")
    
    # Calculate metrics
    total_jobs = len(df)
    unique_companies = df['company'].nunique() if 'company' in df.columns else 0
    unique_locations = df['location'].nunique() if 'location' in df.columns else 0
    avg_match_score = df['match_score'].mean() if 'match_score' in df.columns else 0
    
    # Time-based metrics
    if 'scraped_at' in df.columns:
        df_copy = df.copy()
        df_copy['scraped_date'] = pd.to_datetime(
            df_copy['scraped_at'], errors='coerce'
        ).dt.date
        date_range = df_copy['scraped_date'].max() - df_copy['scraped_date'].min()
        days_active = date_range.days if date_range else 0
        jobs_per_day = total_jobs / max(days_active, 1)
    else:
        days_active = 0
        jobs_per_day = 0
    
    # Display metrics
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


def render_analytics_charts(df: pd.DataFrame) -> None:
    """Render analytics charts."""
    
    st.markdown("## 📈 Charts & Visualizations")
    
    # Create tabs for different chart categories
    chart_tab1, chart_tab2, chart_tab3 = st.tabs([
        "📊 Status & Progress", 
        "🏢 Companies & Locations", 
        "📅 Time Analysis"
    ])
    
    with chart_tab1:
        render_status_charts(df)
    
    with chart_tab2:
        render_company_charts(df)
    
    with chart_tab3:
        render_time_charts(df)


def render_status_charts(df: pd.DataFrame) -> None:
    """Render status-related charts."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'status' in df.columns:
            # Status distribution pie chart
            status_counts = df['status'].value_counts()
            
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Job Status Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'match_score' in df.columns:
            # Match score distribution
            fig = px.histogram(
                df,
                x='match_score',
                nbins=20,
                title="Match Score Distribution",
                color_discrete_sequence=['#3b82f6']
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)


def render_company_charts(df: pd.DataFrame) -> None:
    """Render company and location charts."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'company' in df.columns:
            # Top companies
            top_companies = df['company'].value_counts().head(10)
            
            fig = px.bar(
                x=top_companies.values,
                y=top_companies.index,
                orientation='h',
                title="Top 10 Companies by Job Count",
                color_discrete_sequence=['#10b981']
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'location' in df.columns:
            # Top locations
            top_locations = df['location'].value_counts().head(10)
            
            fig = px.bar(
                x=top_locations.values,
                y=top_locations.index,
                orientation='h',
                title="Top 10 Locations by Job Count",
                color_discrete_sequence=['#f59e0b']
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)


def render_time_charts(df: pd.DataFrame) -> None:
    """Render time-based charts."""
    
    if 'scraped_at' not in df.columns:
        st.info("No time data available for analysis")
        return
    
    # Prepare time data
    df_time = df.copy()
    df_time['scraped_date'] = pd.to_datetime(
        df_time['scraped_at'], errors='coerce'
    )
    df_time = df_time.dropna(subset=['scraped_date'])
    
    if df_time.empty:
        st.info("No valid time data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Jobs over time
        daily_jobs = df_time.groupby(
            df_time['scraped_date'].dt.date
        ).size().reset_index()
        daily_jobs.columns = ['date', 'count']
        
        fig = px.line(
            daily_jobs,
            x='date',
            y='count',
            title="Jobs Scraped Over Time",
            color_discrete_sequence=['#8b5cf6']
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Jobs by hour of day
        df_time['hour'] = df_time['scraped_date'].dt.hour
        hourly_jobs = df_time['hour'].value_counts().sort_index()
        
        fig = px.bar(
            x=hourly_jobs.index,
            y=hourly_jobs.values,
            title="Jobs Scraped by Hour of Day",
            color_discrete_sequence=['#ef4444']
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)


def render_analytics_insights(df: pd.DataFrame) -> None:
    """Render analytics insights and recommendations."""
    
    st.markdown("## 💡 Insights & Recommendations")
    
    insights = generate_insights(df)
    
    for insight in insights:
        st.markdown(f"""
        <div style='background: #1e293b; padding: 1.5rem; 
                    border-radius: 1rem; border-left: 4px solid {insight['color']}; 
                    margin-bottom: 1rem;'>
            <div style='display: flex; align-items: center; 
                        margin-bottom: 0.5rem;'>
                <span style='font-size: 1.5rem; margin-right: 0.5rem;'>
                    {insight['icon']}
                </span>
                <h4 style='color: #f1f5f9; margin: 0;'>
                    {insight['title']}
                </h4>
            </div>
            <p style='color: #cbd5e1; margin: 0;'>
                {insight['description']}
            </p>
        </div>
        """, unsafe_allow_html=True)


def generate_insights(df: pd.DataFrame) -> list:
    """Generate insights based on job data."""
    
    insights = []
    
    if df.empty:
        return insights
    
    # Match score insights
    if 'match_score' in df.columns:
        avg_match = df['match_score'].mean()
        high_match_jobs = len(df[df['match_score'] >= 80])
        
        if avg_match < 60:
            insights.append({
                'icon': '🎯',
                'title': 'Low Match Scores Detected',
                'description': f'Average match score is {avg_match:.1f}%. Consider refining your search criteria or job preferences.',
                'color': '#ef4444'
            })
        elif high_match_jobs > 5:
            insights.append({
                'icon': '🎉',
                'title': 'Great Match Opportunities',
                'description': f'Found {high_match_jobs} jobs with 80%+ match score. These are excellent candidates for application.',
                'color': '#10b981'
            })
    
    # Application insights
    if 'applied' in df.columns:
        applied_count = len(df[df['applied'] == 1])
        total_jobs = len(df)
        application_rate = (applied_count / total_jobs) * 100 if total_jobs > 0 else 0
        
        if application_rate < 10:
            insights.append({
                'icon': '📋',
                'title': 'Low Application Rate',
                'description': f'You\'ve applied to {application_rate:.1f}% of jobs. Consider increasing your application rate.',
                'color': '#f59e0b'
            })
    
    # Company diversity insights
    if 'company' in df.columns:
        unique_companies = df['company'].nunique()
        total_jobs = len(df)
        
        if unique_companies > total_jobs * 0.7:
            insights.append({
                'icon': '🏢',
                'title': 'Great Company Diversity',
                'description': f'Jobs from {unique_companies} different companies shows good market coverage.',
                'color': '#3b82f6'
            })
    
    return insights
