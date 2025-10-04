"""
System Status & Intelligence Widget for JobQst Dashboard
Displays JobSpy scraping status, system health, and market intelligence.
"""

import logging

import dash_bootstrap_components as dbc
from dash import html, Input, Output, callback, no_update

logger = logging.getLogger(__name__)


def create_system_status_widget() -> dbc.Card:
    """Create the main system status widget."""
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H5(
                        [html.I(className="fas fa-heartbeat me-2 text-success"), "System Status"],
                        className="mb-0",
                    ),
                    dbc.Badge(
                        "Live", color="success", id="system-status-badge", className="ms-auto"
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col([create_jobspy_status_panel()], width=6),
                            dbc.Col([create_system_health_panel()], width=6),
                        ]
                    ),
                    html.Hr(),
                    create_quick_stats_row(),
                    html.Hr(),
                    create_market_intelligence_mini(),
                ]
            ),
        ],
        className="mb-4",
    )


def create_jobspy_status_panel() -> html.Div:
    """Create JobSpy scraping status panel."""
    return html.Div(
        [
            html.H6([html.I(className="fas fa-search me-2 text-primary"), "JobSpy Status"]),
            html.Div(
                id="jobspy-status-content",
                children=[
                    dbc.Alert(
                        [
                            html.Strong("Ready to Scrape"),
                            html.P(
                                "JobSpy is ready to discover new opportunities.",
                                className="mb-0 mt-1",
                            ),
                        ],
                        color="info",
                        className="mb-2",
                    ),
                    dbc.Progress(
                        id="jobspy-progress",
                        value=0,
                        striped=True,
                        animated=False,
                        className="mb-2",
                    ),
                    html.Small("Last run: Never", className="text-muted", id="jobspy-last-run"),
                ],
            ),
            dbc.ButtonGroup(
                [
                    dbc.Button(
                        [html.I(className="fas fa-play me-1"), "Start JobSpy"],
                        color="success",
                        size="sm",
                        id="start-jobspy-btn",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-stop me-1"), "Stop"],
                        color="danger",
                        size="sm",
                        id="stop-jobspy-btn",
                    ),
                ],
                className="mt-2",
            ),
        ]
    )


def create_system_health_panel() -> html.Div:
    """Create system health monitoring panel."""
    return html.Div(
        [
            html.H6([html.I(className="fas fa-server me-2 text-info"), "System Health"]),
            html.Div(
                id="system-health-content",
                children=[
                    # CPU Usage
                    html.Div(
                        [
                            html.Small("CPU Usage", className="text-muted"),
                            dbc.Progress(
                                value=25, color="success", className="mb-1", style={"height": "8px"}
                            ),
                        ],
                        className="mb-2",
                    ),
                    # Memory Usage
                    html.Div(
                        [
                            html.Small("Memory Usage", className="text-muted"),
                            dbc.Progress(
                                value=45, color="warning", className="mb-1", style={"height": "8px"}
                            ),
                        ],
                        className="mb-2",
                    ),
                    # Database Size
                    html.Div(
                        [
                            html.Small("Database Size", className="text-muted"),
                            dbc.Progress(
                                value=15, color="info", className="mb-1", style={"height": "8px"}
                            ),
                        ],
                        className="mb-2",
                    ),
                    # Cache Status
                    html.Div(
                        [
                            html.Small(
                                ["Cache: ", dbc.Badge("Active", color="success", size="sm")],
                                className="text-muted",
                            )
                        ]
                    ),
                ],
            ),
        ]
    )


def create_quick_stats_row() -> dbc.Row:
    """Create quick statistics row."""
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Div(
                        [
                            html.H4("0", id="total-jobs-today", className="text-primary mb-0"),
                            html.Small("Jobs Today", className="text-muted"),
                        ],
                        className="text-center",
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.H4("0", id="successful-scrapes", className="text-success mb-0"),
                            html.Small("Successful Scrapes", className="text-muted"),
                        ],
                        className="text-center",
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.H4("0", id="active-profiles", className="text-info mb-0"),
                            html.Small("Active Profiles", className="text-muted"),
                        ],
                        className="text-center",
                    )
                ],
                width=3,
            ),
            dbc.Col(
                [
                    html.Div(
                        [
                            html.H4("0", id="cache-hits", className="text-warning mb-0"),
                            html.Small("Cache Hits", className="text-muted"),
                        ],
                        className="text-center",
                    )
                ],
                width=3,
            ),
        ]
    )


def create_market_intelligence_mini() -> html.Div:
    """Create mini market intelligence panel."""
    return html.Div(
        [
            html.H6(
                [html.I(className="fas fa-chart-line me-2 text-warning"), "Market Intelligence"]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Strong("Top Skills"),
                                    html.Div(
                                        [
                                            dbc.Badge(
                                                "Python", color="primary", className="me-1 mb-1"
                                            ),
                                            dbc.Badge(
                                                "React", color="primary", className="me-1 mb-1"
                                            ),
                                            dbc.Badge(
                                                "AWS", color="primary", className="me-1 mb-1"
                                            ),
                                            dbc.Badge(
                                                "Docker", color="primary", className="me-1 mb-1"
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Strong("Hot Companies"),
                                    html.Div(
                                        [
                                            html.P("• TechCorp (15 jobs)", className="mb-1 small"),
                                            html.P("• StartupX (12 jobs)", className="mb-1 small"),
                                            html.P("• BigTech (8 jobs)", className="mb-0 small"),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                ]
            ),
        ]
    )


def register_system_status_callbacks(app):
    """Register callbacks for system status widget."""

    @callback(
        [
            Output("system-status-badge", "children"),
            Output("system-status-badge", "color"),
            Output("total-jobs-today", "children"),
            Output("successful-scrapes", "children"),
            Output("active-profiles", "children"),
            Output("cache-hits", "children"),
        ],
        [Input("auto-refresh-interval", "n_intervals")],
        prevent_initial_call=True,
    )
    def update_system_status(n_intervals):
        """Update all system status indicators."""
        try:
            # Simulate system status updates
            # In production, this would connect to actual monitoring services

            # System badge
            badge_text = "Live"
            badge_color = "success"

            # Quick stats
            jobs_today = "23"
            successful_scrapes = "15"
            active_profiles = "3"
            cache_hits = "89%"

            return (
                badge_text,
                badge_color,
                jobs_today,
                successful_scrapes,
                active_profiles,
                cache_hits,
            )

        except Exception as e:
            logger.error(f"Error updating system status: {e}")
            return (no_update, no_update, no_update, no_update, no_update, no_update)

    @callback(
        Output("jobspy-progress", "value"),
        [Input("start-jobspy-btn", "n_clicks")],
        prevent_initial_call=True,
    )
    def start_jobspy_scraping(n_clicks):
        """Handle JobSpy start button."""
        if n_clicks:
            # In production, this would trigger actual JobSpy
            return 75  # Simulate progress
        return no_update

    logger.info("System status callbacks registered successfully")
