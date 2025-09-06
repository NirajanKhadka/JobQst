"""
Enhanced Analytics Callbacks for JobQst Dashboard
Handles data loading, chart generation, and user interactions for analytics.
"""
import logging
from dash import Input, Output, callback, html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


def register_enhanced_analytics_callbacks(app):
    """Register all analytics callbacks."""
    
    @app.callback(
        [
            Output("analytics-kpi-cards", "children"),
            Output("jobs-timeline-chart", "figure"),
            Output("location-types-chart", "figure"),
            Output("top-companies-chart", "figure"),
            Output("skills-chart", "figure"),
            Output("match-scores-chart", "figure"),
            Output("source-performance-chart", "figure"),
            Output("keyword-effectiveness-table", "children"),
            Output("top-locations-table", "children"),
            Output("analytics-data-store", "children"),
            Output("analytics-last-updated", "children")
        ],
        [
            Input("analytics-period-dropdown", "value"),
            Input("refresh-analytics-btn", "n_clicks")
        ]
    )
    def update_analytics_dashboard(period_days, refresh_clicks):
        """Update all analytics components."""
        try:
            # Load analytics data
            from src.services.job_analytics_service import JobAnalyticsService
            from src.core.job_database import get_job_db
            
            # Get database for current profile (you may need to pass this dynamically)
            profile_name = "Nirajan"  # This should be dynamic
            db = get_job_db(profile_name)
            
            # Generate analytics
            analytics_service = JobAnalyticsService(db)
            analytics_data = analytics_service.generate_comprehensive_report(period_days)
            
            if analytics_data.get('status') == 'no_data':
                return generate_no_data_components()
            
            # Generate all components
            kpi_cards = create_kpi_cards(analytics_data)
            timeline_chart = create_timeline_chart(analytics_data)
            location_chart = create_location_chart(analytics_data)
            companies_chart = create_companies_chart(analytics_data)
            skills_chart = create_skills_chart(analytics_data)
            match_scores_chart = create_match_scores_chart(analytics_data)
            sources_chart = create_sources_chart(analytics_data)
            keyword_table = create_keyword_table(analytics_data)
            locations_table = create_locations_table(analytics_data)
            
            last_updated = f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return (
                kpi_cards, timeline_chart, location_chart, companies_chart,
                skills_chart, match_scores_chart, sources_chart, keyword_table,
                locations_table, json.dumps(analytics_data), last_updated
            )
            
        except Exception as e:
            logger.error(f"Error updating analytics dashboard: {e}")
            return generate_error_components(str(e))
    
    @app.callback(
        Output("export-csv-btn", "href"),
        Input("export-csv-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def export_csv(n_clicks):
        """Handle CSV export."""
        if n_clicks:
            # Generate CSV download link
            return "/download/analytics.csv"
        return ""
    
    @app.callback(
        Output("export-json-btn", "href"),
        Input("export-json-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def export_json(n_clicks):
        """Handle JSON export."""
        if n_clicks:
            # Generate JSON download link
            return "/download/analytics.json"
        return ""


def create_kpi_cards(analytics_data):
    """Create KPI cards from analytics data."""
    overview = analytics_data.get('overview', {})
    
    cards = dbc.Row([
        dbc.Col([
            create_kpi_card(
                "Total Jobs",
                str(overview.get('total_jobs', 0)),
                "fas fa-briefcase",
                "primary"
            )
        ], width=3),
        dbc.Col([
            create_kpi_card(
                "Applied",
                str(overview.get('applied_jobs', 0)),
                "fas fa-paper-plane",
                "success"
            )
        ], width=3),
        dbc.Col([
            create_kpi_card(
                "Avg Match Score",
                f"{overview.get('avg_match_score', 0):.1%}",
                "fas fa-bullseye",
                "info"
            )
        ], width=3),
        dbc.Col([
            create_kpi_card(
                "Companies",
                str(overview.get('unique_companies', 0)),
                "fas fa-building",
                "warning"
            )
        ], width=3)
    ])
    
    return cards


def create_kpi_card(title, value, icon, color):
    """Create individual KPI card."""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.I(className=f"{icon} fa-2x text-{color}")
                ], className="col-auto"),
                html.Div([
                    html.H4(value, className="mb-0"),
                    html.P(title, className="text-muted mb-0 small")
                ], className="col")
            ], className="row align-items-center")
        ])
    ], className="h-100 border-left-5 border-left-" + color)


def create_timeline_chart(analytics_data):
    """Create jobs timeline chart."""
    trends = analytics_data.get('trends', {})
    daily_jobs = trends.get('daily_jobs', [])
    
    if not daily_jobs:
        return create_empty_chart("No job data available for timeline")
    
    df = pd.DataFrame(daily_jobs)
    
    fig = px.line(
        df, x='date', y='jobs_found',
        title="Jobs Found Over Time",
        labels={'jobs_found': 'Jobs Found', 'date': 'Date'}
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Jobs Found",
        showlegend=False,
        template="plotly_white"
    )
    
    return fig


def create_location_chart(analytics_data):
    """Create location types pie chart."""
    locations = analytics_data.get('locations', {})
    remote_jobs = locations.get('remote_jobs', 0)
    hybrid_jobs = locations.get('hybrid_jobs', 0)
    onsite_jobs = locations.get('onsite_jobs', 0)
    
    if remote_jobs + hybrid_jobs + onsite_jobs == 0:
        return create_empty_chart("No location data available")
    
    fig = px.pie(
        values=[remote_jobs, hybrid_jobs, onsite_jobs],
        names=['Remote', 'Hybrid', 'On-site'],
        title="Work Arrangement Distribution"
    )
    
    fig.update_layout(template="plotly_white")
    
    return fig


def create_companies_chart(analytics_data):
    """Create top companies bar chart."""
    companies = analytics_data.get('companies', {})
    top_companies = companies.get('top_companies', {})
    
    if not top_companies:
        return create_empty_chart("No company data available")
    
    # Take top 10 companies
    companies_list = list(top_companies.items())[:10]
    company_names = [item[0] for item in companies_list]
    job_counts = [item[1] for item in companies_list]
    
    fig = px.bar(
        x=job_counts, y=company_names,
        orientation='h',
        title="Top Companies by Job Count",
        labels={'x': 'Number of Jobs', 'y': 'Company'}
    )
    
    fig.update_layout(
        xaxis_title="Number of Jobs",
        yaxis_title="Company",
        template="plotly_white"
    )
    
    return fig


def create_skills_chart(analytics_data):
    """Create skills demand chart."""
    skills = analytics_data.get('skills', {})
    top_skills = skills.get('top_skills', {})
    
    if not top_skills:
        return create_empty_chart("No skills data available")
    
    # Take top 10 skills
    skills_list = list(top_skills.items())[:10]
    skill_names = [item[0] for item in skills_list]
    skill_counts = [item[1] for item in skills_list]
    
    fig = px.bar(
        x=skill_names, y=skill_counts,
        title="Most In-Demand Skills",
        labels={'x': 'Skill', 'y': 'Frequency'}
    )
    
    fig.update_layout(
        xaxis_title="Skill",
        yaxis_title="Frequency",
        template="plotly_white",
        xaxis_tickangle=-45
    )
    
    return fig


def create_match_scores_chart(analytics_data):
    """Create match scores distribution chart."""
    scores = analytics_data.get('match_scores', {})
    score_distribution = scores.get('score_distribution', {})
    
    if not score_distribution:
        return create_empty_chart("No match score data available")
    
    categories = list(score_distribution.keys())
    values = list(score_distribution.values())
    
    fig = px.bar(
        x=categories, y=values,
        title="Match Score Distribution",
        labels={'x': 'Score Category', 'y': 'Number of Jobs'}
    )
    
    fig.update_layout(
        xaxis_title="Score Category",
        yaxis_title="Number of Jobs",
        template="plotly_white"
    )
    
    return fig


def create_sources_chart(analytics_data):
    """Create job sources performance chart."""
    sources = analytics_data.get('sources', {})
    source_performance = sources.get('source_performance', {})
    
    if not source_performance:
        return create_empty_chart("No source data available")
    
    source_names = list(source_performance.keys())
    job_counts = list(source_performance.values())
    
    fig = px.pie(
        values=job_counts,
        names=source_names,
        title="Jobs by Source"
    )
    
    fig.update_layout(template="plotly_white")
    
    return fig


def create_keyword_table(analytics_data):
    """Create keyword effectiveness table."""
    keywords = analytics_data.get('keywords', {})
    keyword_performance = keywords.get('keyword_performance', {})
    
    if not keyword_performance:
        return html.P("No keyword data available", className="text-muted")
    
    # Create table rows
    rows = []
    for keyword, data in list(keyword_performance.items())[:10]:
        if isinstance(data, dict):
            jobs_found = data.get('jobs_found', 0)
            effectiveness = data.get('effectiveness_score', 0)
        else:
            jobs_found = data
            effectiveness = 0
        
        rows.append(
            html.Tr([
                html.Td(keyword),
                html.Td(str(jobs_found)),
                html.Td(f"{effectiveness:.2f}")
            ])
        )
    
    table = dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("Keyword"),
                html.Th("Jobs Found"),
                html.Th("Effectiveness")
            ])
        ]),
        html.Tbody(rows)
    ], striped=True, hover=True, size="sm")
    
    return table


def create_locations_table(analytics_data):
    """Create top locations table."""
    locations = analytics_data.get('locations', {})
    top_locations = locations.get('top_locations', {})
    
    if not top_locations:
        return html.P("No location data available", className="text-muted")
    
    # Create table rows
    rows = []
    for location, count in list(top_locations.items())[:10]:
        rows.append(
            html.Tr([
                html.Td(location),
                html.Td(str(count))
            ])
        )
    
    table = dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("Location"),
                html.Th("Job Count")
            ])
        ]),
        html.Tbody(rows)
    ], striped=True, hover=True, size="sm")
    
    return table


def create_empty_chart(message):
    """Create empty chart with message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16)
    )
    fig.update_layout(
        template="plotly_white",
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False)
    )
    return fig


def generate_no_data_components():
    """Generate components when no data is available."""
    no_data_message = dbc.Alert([
        html.H4("No Data Available", className="alert-heading"),
        html.P("No jobs found for the selected time period. Try running a scraping session first."),
        dbc.Button("Start Scraping", color="primary", href="/scraping")
    ], color="info")
    
    empty_chart = create_empty_chart("No data available")
    
    return (
        no_data_message, empty_chart, empty_chart, empty_chart,
        empty_chart, empty_chart, empty_chart,
        html.P("No data"), html.P("No data"),
        json.dumps({}), "No data available"
    )


def generate_error_components(error_message):
    """Generate error components."""
    error_alert = dbc.Alert([
        html.H4("Error Loading Analytics", className="alert-heading"),
        html.P(f"Error: {error_message}"),
        html.P("Please check the logs and try refreshing the page.")
    ], color="danger")
    
    empty_chart = create_empty_chart("Error loading data")
    
    return (
        error_alert, empty_chart, empty_chart, empty_chart,
        empty_chart, empty_chart, empty_chart,
        html.P("Error"), html.P("Error"),
        json.dumps({}), f"Error: {error_message}"
    )

