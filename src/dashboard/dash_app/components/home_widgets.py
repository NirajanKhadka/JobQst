"""
Additional Home Tab Widgets - Company insights, location heatmap, and recent jobs
"""

import dash_bootstrap_components as dbc
from dash import html, dcc


def create_top_companies_widget():
    """Widget showing top hiring companies"""
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5(
                    [html.I(className="fas fa-building me-2"), "Top Hiring Companies"],
                    className="mb-0",
                )
            ),
            dbc.CardBody(
                [
                    html.Div(
                        id="top-companies-list",
                        children=[
                            dbc.Spinner(
                                html.Div("Loading companies...", className="text-center text-muted p-3"),
                                color="primary",
                                size="sm",
                            )
                        ],
                    )
                ]
            ),
        ],
        className="shadow-sm h-100",
    )


def create_location_insights_widget():
    """Widget showing top locations for jobs"""
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5(
                    [html.I(className="fas fa-map-marker-alt me-2"), "Top Locations"],
                    className="mb-0",
                )
            ),
            dbc.CardBody(
                [
                    html.Div(
                        id="top-locations-list",
                        children=[
                            dbc.Spinner(
                                html.Div("Loading locations...", className="text-center text-muted p-3"),
                                color="primary",
                                size="sm",
                            )
                        ],
                    )
                ]
            ),
        ],
        className="shadow-sm h-100",
    )


def create_recent_jobs_widget():
    """Widget showing most recently added jobs"""
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5(
                    [html.I(className="fas fa-clock me-2"), "Recently Added Jobs"],
                    className="mb-0",
                )
            ),
            dbc.CardBody(
                [
                    html.Div(
                        id="recent-jobs-list",
                        children=[
                            dbc.Spinner(
                                html.Div("Loading recent jobs...", className="text-center text-muted p-3"),
                                color="primary",
                                size="sm",
                            )
                        ],
                        style={"maxHeight": "400px", "overflowY": "auto"},
                    )
                ]
            ),
        ],
        className="shadow-sm h-100",
    )


def create_salary_insights_widget():
    """Widget showing salary distribution"""
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5(
                    [html.I(className="fas fa-dollar-sign me-2"), "Salary Insights"],
                    className="mb-0",
                )
            ),
            dbc.CardBody(
                [
                    html.Div(
                        id="salary-insights-content",
                        children=[
                            dbc.Spinner(
                                html.Div("Analyzing salaries...", className="text-center text-muted p-3"),
                                color="primary",
                                size="sm",
                            )
                        ],
                    )
                ]
            ),
        ],
        className="shadow-sm h-100",
    )


def create_quick_stats_widget():
    """Compact widget with quick statistics"""
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5(
                    [html.I(className="fas fa-chart-pie me-2"), "Quick Stats"],
                    className="mb-0",
                )
            ),
            dbc.CardBody(
                [
                    html.Div(
                        id="quick-stats-content",
                        children=[
                            dbc.Spinner(
                                html.Div("Loading stats...", className="text-center text-muted p-3"),
                                color="primary",
                                size="sm",
                            )
                        ],
                    )
                ]
            ),
        ],
        className="shadow-sm h-100",
    )


def create_application_tracker_widget():
    """Widget showing application status summary"""
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5(
                    [html.I(className="fas fa-tasks me-2"), "Application Pipeline"],
                    className="mb-0",
                )
            ),
            dbc.CardBody(
                [
                    html.Div(
                        id="application-pipeline-content",
                        children=[
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.Small("To Apply", className="text-muted"),
                                                    html.H4(
                                                        id="pipeline-to-apply",
                                                        children="--",
                                                        className="text-info",
                                                    ),
                                                ],
                                                className="text-center",
                                            )
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.Small("Applied", className="text-muted"),
                                                    html.H4(
                                                        id="pipeline-applied",
                                                        children="--",
                                                        className="text-success",
                                                    ),
                                                ],
                                                className="text-center",
                                            )
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.Small("Response", className="text-muted"),
                                                    html.H4(
                                                        id="pipeline-response",
                                                        children="--",
                                                        className="text-warning",
                                                    ),
                                                ],
                                                className="text-center",
                                            )
                                        ],
                                        width=4,
                                    ),
                                ]
                            )
                        ],
                    )
                ]
            ),
        ],
        className="shadow-sm h-100",
    )
