"""
Market Insights Layout - Analytics and market intelligence
RCIP job distribution, trending keywords, company insights, salary trends
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from src.dashboard.dash_app.components.rcip_components import create_rcip_summary_section
from src.dashboard.dash_app.components.salary_analyzer import create_salary_analyzer
from src.dashboard.dash_app.components.market_trends import create_market_trends


def create_market_insights_layout():
    """
    Create the market insights layout with RCIP analytics.
    Provides job market intelligence and trends for strategic job searching.
    """
    return html.Div(
        [
            # Page header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2(
                                [
                                    html.I(className="fas fa-chart-line me-3 text-info"),
                                    "Market Insights",
                                ],
                                className="mb-1",
                            ),
                            html.P(
                                "Job market analytics, trends, and RCIP opportunities",
                                className="text-muted",
                            ),
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        [html.I(className="fas fa-sync-alt me-2"), "Refresh"],
                                        id="refresh-insights",
                                        color="primary",
                                        outline=True,
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-download me-2"), "Export Report"],
                                        id="export-insights",
                                        color="success",
                                        outline=True,
                                    ),
                                ],
                                className="float-end",
                            )
                        ],
                        width=4,
                    ),
                ],
                className="mb-4",
            ),
            # Time range selector
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Label("Analysis Period:", className="me-2"),
                                            dcc.Dropdown(
                                                id="insights-time-range",
                                                options=[
                                                    {"label": "Last 7 days", "value": "7"},
                                                    {"label": "Last 30 days", "value": "30"},
                                                    {"label": "Last 90 days", "value": "90"},
                                                    {"label": "All time", "value": "all"},
                                                ],
                                                value="30",
                                                clearable=False,
                                                className="w-100",
                                            ),
                                        ],
                                        className="py-2",
                                    )
                                ]
                            )
                        ]
                    )
                ],
                className="mb-4",
            ),
            # Top row - Key metrics
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-briefcase fa-3x text-primary mb-3"
                                                    ),
                                                    html.H2(
                                                        id="insights-total-jobs",
                                                        children="--",
                                                        className="mb-0",
                                                    ),
                                                    html.P(
                                                        "Total Opportunities",
                                                        className="text-muted mb-0",
                                                    ),
                                                ],
                                                className="text-center",
                                            )
                                        ]
                                    )
                                ],
                                className="shadow-sm h-100",
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-building fa-3x text-success mb-3"
                                                    ),
                                                    html.H2(
                                                        id="insights-companies",
                                                        children="--",
                                                        className="mb-0",
                                                    ),
                                                    html.P(
                                                        "Unique Companies",
                                                        className="text-muted mb-0",
                                                    ),
                                                ],
                                                className="text-center",
                                            )
                                        ]
                                    )
                                ],
                                className="shadow-sm h-100",
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-map-marker-alt fa-3x text-warning mb-3"
                                                    ),
                                                    html.H2(
                                                        id="insights-locations",
                                                        children="--",
                                                        className="mb-0",
                                                    ),
                                                    html.P(
                                                        "Active Locations",
                                                        className="text-muted mb-0",
                                                    ),
                                                ],
                                                className="text-center",
                                            )
                                        ]
                                    )
                                ],
                                className="shadow-sm h-100",
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-dollar-sign fa-3x text-info mb-3"
                                                    ),
                                                    html.H2(
                                                        id="insights-avg-salary",
                                                        children="--",
                                                        className="mb-0",
                                                    ),
                                                    html.P(
                                                        "Avg. Salary Range",
                                                        className="text-muted mb-0",
                                                    ),
                                                ],
                                                className="text-center",
                                            )
                                        ]
                                    )
                                ],
                                className="shadow-sm h-100",
                            )
                        ],
                        width=3,
                    ),
                ],
                className="mb-4",
            ),
            # Salary Analysis Section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(id="salary-analysis-container")
                        ],
                        width=12
                    )
                ],
                className="mb-4",
            ),
            
            # Market Trends Section
            html.Div(id="market-trends-container", className="mb-4"),
            
            # RCIP Insights Section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_rcip_summary_section(
                                {
                                    "total_rcip_jobs": 0,
                                    "total_immigration_priority": 0,
                                    "rcip_percentage": 0,
                                }
                            )
                        ]
                    )
                ],
                className="mb-4",
                id="rcip-summary-container",
            ),
            # Charts row 1 - Company and Location Analysis
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(className="fas fa-building me-2"),
                                            "Top Companies Hiring",
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="top-companies-chart",
                                                config={"displayModeBar": False},
                                                style={"height": "350px"},
                                            )
                                        ]
                                    ),
                                ],
                                className="shadow-sm h-100",
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(className="fas fa-map-marked-alt me-2"),
                                            "Top Locations (with RCIP Highlight)",
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="top-locations-chart",
                                                config={"displayModeBar": False},
                                                style={"height": "350px"},
                                            )
                                        ]
                                    ),
                                ],
                                className="shadow-sm h-100",
                            )
                        ],
                        width=6,
                    ),
                ],
                className="mb-4",
            ),
            # Charts row 2 - Trending Keywords and Skills
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [html.I(className="fas fa-tag me-2"), "Trending Keywords"]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="trending-keywords-chart",
                                                config={"displayModeBar": False},
                                                style={"height": "300px"},
                                            )
                                        ]
                                    ),
                                ],
                                className="shadow-sm h-100",
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [html.I(className="fas fa-code me-2"), "In-Demand Skills"]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="top-skills-chart",
                                                config={"displayModeBar": False},
                                                style={"height": "300px"},
                                            )
                                        ]
                                    ),
                                ],
                                className="shadow-sm h-100",
                            )
                        ],
                        width=6,
                    ),
                ],
                className="mb-4",
            ),
            # Charts row 3 - Time series and distribution
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(className="fas fa-calendar-alt me-2"),
                                            "Jobs Posted Over Time",
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="jobs-timeline-chart",
                                                config={"displayModeBar": False},
                                                style={"height": "300px"},
                                            )
                                        ]
                                    ),
                                ],
                                className="shadow-sm h-100",
                            )
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(className="fas fa-chart-pie me-2"),
                                            "Job Type Distribution",
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="job-type-pie-chart",
                                                config={"displayModeBar": False},
                                                style={"height": "300px"},
                                            )
                                        ]
                                    ),
                                ],
                                className="shadow-sm h-100",
                            )
                        ],
                        width=4,
                    ),
                ],
                className="mb-4",
            ),
            # RCIP Geographic Distribution
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(className="fas fa-map me-2 text-success"),
                                            "RCIP Jobs by Province",
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="rcip-province-chart",
                                                config={"displayModeBar": False},
                                                style={"height": "350px"},
                                            )
                                        ]
                                    ),
                                ],
                                className="shadow-sm",
                            )
                        ]
                    )
                ],
                className="mb-4",
            ),
            # Insights summary table
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [html.I(className="fas fa-table me-2"), "Market Summary"]
                                    ),
                                    dbc.CardBody([html.Div(id="market-summary-table")]),
                                ],
                                className="shadow-sm",
                            )
                        ]
                    )
                ]
            ),
            # Hidden data stores
            dcc.Store(id="insights-data-store", storage_type="memory"),
            dcc.Interval(id="insights-refresh-interval", interval=60000, n_intervals=0),
        ]
    )


def create_insight_card(title, value, change_pct=None, icon="fa-chart-line", color="primary"):
    """Helper to create consistent insight cards"""
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(className=f"fas {icon} fa-2x text-{color} mb-2"),
                            html.H3(value, className="mb-0"),
                            html.P(title, className="text-muted small mb-1"),
                            (
                                html.Small(
                                    [
                                        html.I(
                                            className=f"fas fa-arrow-{'up' if change_pct > 0 else 'down'} me-1"
                                        ),
                                        f"{abs(change_pct)}% vs last period",
                                    ],
                                    className=f"text-{'success' if change_pct > 0 else 'danger'}",
                                )
                                if change_pct is not None
                                else html.Span()
                            ),
                        ],
                        className="text-center",
                    )
                ]
            )
        ],
        className="shadow-sm h-100",
    )
