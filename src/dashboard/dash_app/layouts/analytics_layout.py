"""
Analytics layout for JobQst Dashboard
Beautiful charts and visualizations
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.dash_app.components.navigation import create_page_header


def create_analytics_layout():
    """Create the analytics dashboard layout"""

    return html.Div(
        [
            # Page header
            create_page_header("📊 Job Analytics", "Insights and trends from your job search data"),
            # KPI Cards
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_kpi_card(
                                "Success Rate",
                                "0%",
                                "fas fa-percentage",
                                "success",
                                "success-rate-kpi",
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            create_kpi_card(
                                "Avg Match Score", "0%", "fas fa-bullseye", "info", "avg-match-kpi"
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            create_kpi_card(
                                "Total Companies",
                                "0",
                                "fas fa-building",
                                "primary",
                                "companies-kpi",
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            create_kpi_card(
                                "Active Days", "0", "fas fa-calendar", "warning", "active-days-kpi"
                            )
                        ],
                        width=3,
                    ),
                ],
                className="mb-4",
            ),
            # Charts Row 1
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("📈 Jobs Over Time"),
                                    dbc.CardBody([dcc.Graph(id="jobs-timeline-chart")]),
                                ]
                            )
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("🥧 Status Distribution"),
                                    dbc.CardBody([dcc.Graph(id="status-pie-chart")]),
                                ]
                            )
                        ],
                        width=4,
                    ),
                ],
                className="mb-4",
            ),
            # Charts Row 2
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("🏢 Top Companies"),
                                    dbc.CardBody([dcc.Graph(id="companies-bar-chart")]),
                                ]
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("📍 Location Distribution"),
                                    dbc.CardBody([dcc.Graph(id="location-bar-chart")]),
                                ]
                            )
                        ],
                        width=6,
                    ),
                ],
                className="mb-4",
            ),
            # Charts Row 3
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("🎯 Match Score Distribution"),
                                    dbc.CardBody([dcc.Graph(id="match-score-histogram")]),
                                ]
                            )
                        ],
                        width=12,
                    )
                ]
            ),
        ]
    )


def create_kpi_card(title, value, icon, color, kpi_id):
    """Create a KPI card component"""
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H3(id=kpi_id, children=value, className="fw-bold mb-1"),
                                    html.P(title, className="text-muted mb-0"),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [html.I(className=f"{icon} fs-1 text-{color}")],
                                width=4,
                                className="text-end",
                            ),
                        ],
                        className="align-items-center",
                    )
                ]
            )
        ],
        className="shadow-sm border-0",
    )
