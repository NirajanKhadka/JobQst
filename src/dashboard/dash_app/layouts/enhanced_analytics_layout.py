"""
Enhanced Analytics Layout for JobLens Dashboard
Comprehensive analytics with interactive charts and insights.
"""
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def create_enhanced_analytics_layout():
    """Create enhanced analytics dashboard layout with comprehensive insights."""
    
    return html.Div([
        # Header
        dbc.Row([
            dbc.Col([
                html.H2([
                    html.I(className="fas fa-chart-line me-2"),
                    "Job Search Analytics"
                ], className="text-primary"),
                html.P("Comprehensive insights into your job search performance", 
                       className="text-muted mb-4")
            ])
        ]),
        
        # Time Period Selector
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Label("Analysis Period:", className="form-label"),
                        dcc.Dropdown(
                            id="analytics-period-dropdown",
                            options=[
                                {"label": "Last 7 Days", "value": 7},
                                {"label": "Last 30 Days", "value": 30},
                                {"label": "Last 60 Days", "value": 60},
                                {"label": "Last 90 Days", "value": 90}
                            ],
                            value=30,
                            clearable=False
                        ),
                        dbc.Button(
                            "Refresh Analytics",
                            id="refresh-analytics-btn",
                            color="primary",
                            size="sm",
                            className="mt-2"
                        )
                    ])
                ])
            ], width=3),
            dbc.Col([
                html.Div(id="analytics-last-updated", className="text-muted small")
            ], width=9)
        ], className="mb-4"),
        
        # KPI Cards
        html.Div(id="analytics-kpi-cards", className="mb-4"),
        
        # Main Charts Row
        dbc.Row([
            # Job Discovery Trends
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-trending-up me-2"),
                            "Job Discovery Trends"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="jobs-timeline-chart", style={"height": "300px"})
                    ])
                ])
            ], width=8),
            
            # Location Types Distribution
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-map-marker-alt me-2"),
                            "Work Arrangements"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="location-types-chart", style={"height": "300px"})
                    ])
                ])
            ], width=4)
        ], className="mb-4"),
        
        # Second Row Charts
        dbc.Row([
            # Top Companies
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-building me-2"),
                            "Top Companies"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="top-companies-chart", style={"height": "350px"})
                    ])
                ])
            ], width=6),
            
            # Skills Analysis
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-cogs me-2"),
                            "In-Demand Skills"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="skills-chart", style={"height": "350px"})
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Third Row - More Detailed Analytics
        dbc.Row([
            # Match Score Distribution
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-bullseye me-2"),
                            "Match Score Analysis"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="match-scores-chart", style={"height": "300px"})
                    ])
                ])
            ], width=6),
            
            # Source Performance
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-globe me-2"),
                            "Source Performance"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Graph(id="source-performance-chart", style={"height": "300px"})
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Analytics Tables
        dbc.Row([
            # Keyword Effectiveness
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-search me-2"),
                            "Keyword Effectiveness"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="keyword-effectiveness-table")
                    ])
                ])
            ], width=6),
            
            # Top Locations
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-map me-2"),
                            "Popular Locations"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="top-locations-table")
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Export Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-download me-2"),
                            "Export Analytics"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P("Download your analytics data for further analysis:", 
                               className="mb-3"),
                        dbc.ButtonGroup([
                            dbc.Button(
                                [html.I(className="fas fa-file-csv me-2"), "Export CSV"],
                                id="export-csv-btn",
                                color="success",
                                outline=True
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-file-code me-2"), "Export JSON"],
                                id="export-json-btn",
                                color="info",
                                outline=True
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-file-pdf me-2"), "Generate Report"],
                                id="generate-report-btn",
                                color="primary",
                                outline=True
                            )
                        ])
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # Hidden div to store analytics data
        html.Div(id="analytics-data-store", style={"display": "none"})
    ])


def create_kpi_card(title, value, icon, color, id_suffix):
    """Create a KPI card component."""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.I(className=f"{icon} fa-2x text-{color}")
                ], className="col-auto"),
                html.Div([
                    html.H4(value, id=f"{id_suffix}-value", className="mb-0"),
                    html.P(title, className="text-muted mb-0 small")
                ], className="col")
            ], className="row align-items-center")
        ])
    ], className="h-100")


def generate_sample_charts():
    """Generate sample charts for demonstration."""
    
    # Sample timeline data
    dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
    jobs_count = [5, 8, 12, 6, 15, 20, 18, 10, 7, 14, 22, 16, 9, 11, 25, 
                 19, 13, 8, 17, 21, 12, 6, 18, 24, 15, 11, 9, 20, 16, 13]
    
    timeline_fig = px.line(
        x=dates, y=jobs_count,
        title="Jobs Found Over Time",
        labels={"x": "Date", "y": "Jobs Found"}
    )
    timeline_fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Jobs Found",
        showlegend=False
    )
    
    # Sample location types pie chart
    location_data = {"Remote": 45, "Hybrid": 30, "On-site": 20, "Unknown": 5}
    location_fig = px.pie(
        values=list(location_data.values()),
        names=list(location_data.keys()),
        title="Work Arrangement Distribution"
    )
    
    # Sample companies bar chart
    companies = ["Tech Corp", "Innovation Inc", "StartupXYZ", "Global Systems", "AI Solutions"]
    company_counts = [15, 12, 10, 8, 6]
    companies_fig = px.bar(
        x=company_counts, y=companies,
        orientation='h',
        title="Top Companies by Job Count"
    )
    companies_fig.update_layout(
        xaxis_title="Number of Jobs",
        yaxis_title="Company"
    )
    
    return timeline_fig, location_fig, companies_fig
