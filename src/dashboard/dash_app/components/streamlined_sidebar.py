"""
Streamlined Sidebar for JobQst Dashboard
Job-seeker focused 5-tab navigation: Home, Job Browser, Job Tracker, Market Insights, Settings
"""

import dash_bootstrap_components as dbc
from dash import html


def create_streamlined_sidebar():
    """Create the streamlined 5-tab sidebar navigation"""

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    # Logo and title
                    html.Div(
                        [
                            html.I(className="fas fa-rocket fs-1 text-success mb-3"),
                            html.H3("JobQst", className="fw-bold text-success"),
                            html.P("AI-Powered Job Discovery", className="text-light small mb-4"),
                        ],
                        className="text-center",
                    ),
                    html.Hr(className="border-secondary"),
                    # Current Profile Display
                    html.Div(
                        [
                            html.Label(
                                [html.I(className="fas fa-user me-2"), "Active Profile"],
                                className="fw-semibold mb-2 text-light small",
                            ),
                            dbc.Badge(
                                id="current-profile-display",
                                children="Loading...",
                                color="success",
                                className="mb-3 p-2 w-100 text-center",
                                pill=True,
                            ),
                        ]
                    ),
                    html.Hr(className="border-secondary"),
                    # Main Navigation - 5 Core Tabs
                    html.Div(
                        [
                            html.Label(
                                [html.I(className="fas fa-compass me-2"), "Navigation"],
                                className="fw-semibold mb-3 text-light",
                            ),
                            dbc.Nav(
                                [
                                    dbc.NavItem(
                                        dbc.NavLink(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(className="fas fa-home fa-lg mb-2"),
                                                        html.Div(
                                                            "Home", className="fw-semibold"
                                                        ),
                                                    ],
                                                    className="text-center py-2",
                                                )
                                            ],
                                            href="#",
                                            id="nav-home",
                                            active=True,
                                            className="py-3 mb-2 border rounded",
                                        )
                                    ),
                                    dbc.NavItem(
                                        dbc.NavLink(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(className="fas fa-briefcase fa-lg mb-2"),
                                                        html.Div(
                                                            "Job Browser", className="fw-semibold"
                                                        ),
                                                    ],
                                                    className="text-center py-2",
                                                )
                                            ],
                                            href="#",
                                            id="nav-job-browser",
                                            className="py-3 mb-2 border rounded",
                                        )
                                    ),
                                    dbc.NavItem(
                                        dbc.NavLink(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(className="fas fa-tasks fa-lg mb-2"),
                                                        html.Div(
                                                            "Job Tracker", className="fw-semibold"
                                                        ),
                                                    ],
                                                    className="text-center py-2",
                                                )
                                            ],
                                            href="#",
                                            id="nav-job-tracker",
                                            className="py-3 mb-2 border rounded",
                                        )
                                    ),
                                    dbc.NavItem(
                                        dbc.NavLink(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line fa-lg mb-2"
                                                        ),
                                                        html.Div(
                                                            "Market Insights",
                                                            className="fw-semibold",
                                                        ),
                                                    ],
                                                    className="text-center py-2",
                                                )
                                            ],
                                            href="#",
                                            id="nav-market-insights",
                                            className="py-3 mb-2 border rounded",
                                        )
                                    ),
                                    dbc.NavItem(
                                        dbc.NavLink(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(className="fas fa-robot fa-lg mb-2"),
                                                        html.Div(
                                                            "Scraper Control", className="fw-semibold"
                                                        ),
                                                    ],
                                                    className="text-center py-2",
                                                )
                                            ],
                                            href="#",
                                            id="nav-scraper",
                                            className="py-3 mb-2 border rounded",
                                        )
                                    ),
                                ],
                                vertical=True,
                                id="sidebar-nav",
                                className="mb-3",
                            ),
                        ]
                    ),
                    html.Hr(className="border-secondary"),
                    # Quick Stats
                    html.Div(
                        [
                            html.Label(
                                [html.I(className="fas fa-chart-bar me-2"), "Quick Stats"],
                                className="fw-semibold mb-2 text-light small",
                            ),
                            html.Div(
                                id="sidebar-quick-stats",
                                children=[
                                    html.Div(
                                        [
                                            html.Small("Total Jobs:", className="text-muted"),
                                            html.Div(
                                                "--",
                                                className="fs-5 fw-bold text-info",
                                                id="sidebar-stat-total",
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.Small("RCIP Jobs:", className="text-muted"),
                                            html.Div(
                                                "--",
                                                className="fs-5 fw-bold text-success",
                                                id="sidebar-stat-rcip",
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.Small("Tracked:", className="text-muted"),
                                            html.Div(
                                                "--",
                                                className="fs-5 fw-bold text-warning",
                                                id="sidebar-stat-tracked",
                                            ),
                                        ]
                                    ),
                                ],
                            ),
                        ]
                    ),
                    html.Hr(className="border-secondary"),
                    # Help Button
                    html.Div(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-question-circle me-2"), "Help"],
                                id="nav-help",
                                color="secondary",
                                outline=True,
                                size="sm",
                                className="w-100",
                            ),
                        ]
                    ),
                ],
                className="p-3",
            )
        ],
        className="h-100 shadow bg-dark border-secondary",
    )


def create_legacy_mode_toggle():
    """Create toggle for legacy/advanced features"""
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Switch(
                        id="enable-legacy-features",
                        label="Enable Advanced Features",
                        value=False,
                        className="mb-2",
                    ),
                    html.Small(
                        "Shows scraping, processing, and system tabs", className="text-muted"
                    ),
                ],
                className="p-2",
            )
        ],
        className="mt-2",
    )
