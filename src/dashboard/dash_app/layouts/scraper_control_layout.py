"""
Scraper Control Layout - Interactive job scraping controls
Allows users to trigger job searches, configure scrapers, and monitor progress
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import datetime


def create_scraper_control_layout():
    """Create the scraper control panel with clickable actions"""
    
    return html.Div(
        [
            # Header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2(
                                [
                                    html.I(className="fas fa-robot me-3 text-primary"),
                                    "Job Scraper Control Panel"
                                ],
                                className="mb-1",
                            ),
                            html.P(
                                "Launch job searches, configure scrapers, and monitor scraping progress",
                                className="text-muted mb-0",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            
            # Quick Actions Row
            dbc.Row(
                [
                    # Quick Search Card
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(className="fas fa-search fa-3x text-primary mb-3"),
                                                    html.H4("Quick Job Search", className="mb-3"),
                                                    html.P(
                                                        "Search for jobs using your profile keywords across multiple sites",
                                                        className="text-muted small mb-3",
                                                    ),
                                                    dbc.Button(
                                                        [
                                                            html.I(className="fas fa-play me-2"),
                                                            "Start Job Search"
                                                        ],
                                                        id="btn-quick-search",
                                                        color="primary",
                                                        size="lg",
                                                        className="w-100",
                                                    ),
                                                ],
                                                className="text-center",
                                            )
                                        ]
                                    )
                                ],
                                className="h-100 shadow-sm",
                            )
                        ],
                        width=4,
                        className="mb-4",
                    ),
                    
                    # JobSpy Pipeline Card
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(className="fas fa-rocket fa-3x text-success mb-3"),
                                                    html.H4("JobSpy Pipeline", className="mb-3"),
                                                    html.P(
                                                        "Run comprehensive job discovery across Indeed, LinkedIn, Glassdoor & ZipRecruiter",
                                                        className="text-muted small mb-3",
                                                    ),
                                                    dbc.Button(
                                                        [
                                                            html.I(className="fas fa-bolt me-2"),
                                                            "Run Full Pipeline"
                                                        ],
                                                        id="btn-jobspy-pipeline",
                                                        color="success",
                                                        size="lg",
                                                        className="w-100",
                                                    ),
                                                ],
                                                className="text-center",
                                            )
                                        ]
                                    )
                                ],
                                className="h-100 shadow-sm",
                            )
                        ],
                        width=4,
                        className="mb-4",
                    ),
                    
                    # Process Jobs Card
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(className="fas fa-cogs fa-3x text-warning mb-3"),
                                                    html.H4("Process Jobs", className="mb-3"),
                                                    html.P(
                                                        "Analyze and score jobs using AI to find best matches",
                                                        className="text-muted small mb-3",
                                                    ),
                                                    dbc.Button(
                                                        [
                                                            html.I(className="fas fa-microchip me-2"),
                                                            "Analyze Jobs"
                                                        ],
                                                        id="btn-process-jobs",
                                                        color="warning",
                                                        size="lg",
                                                        className="w-100",
                                                    ),
                                                ],
                                                className="text-center",
                                            )
                                        ]
                                    )
                                ],
                                className="h-100 shadow-sm",
                            )
                        ],
                        width=4,
                        className="mb-4",
                    ),
                ],
                className="mb-4",
            ),
            
            # Configuration Section
            dbc.Row(
                [
                    # Scraper Configuration
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5(
                                            [
                                                html.I(className="fas fa-sliders-h me-2"),
                                                "Scraper Configuration"
                                            ],
                                            className="mb-0"
                                        )
                                    ),
                                    dbc.CardBody(
                                        [
                                            # JobSpy Preset Selection
                                            html.Div(
                                                [
                                                    html.Label("JobSpy Preset:", className="fw-bold mb-2"),
                                                    dcc.Dropdown(
                                                        id="jobspy-preset-select",
                                                        options=[
                                                            {"label": "🇨🇦 Canada Comprehensive", "value": "canada_comprehensive"},
                                                            {"label": "🇨🇦 Tech Hubs Canada", "value": "tech_hubs_canada"},
                                                            {"label": "🇨🇦 Mississauga Focused", "value": "mississauga_focused"},
                                                            {"label": "🇺🇸 USA Comprehensive", "value": "usa_comprehensive"},
                                                            {"label": "🇺🇸 USA Tech Hubs", "value": "usa_tech_hubs"},
                                                            {"label": "🇺🇸 USA Major Cities", "value": "usa_major_cities"},
                                                            {"label": "🌐 Remote Focused", "value": "remote_focused"},
                                                        ],
                                                        value="canada_comprehensive",
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                            
                                            # Number of Results
                                            html.Div(
                                                [
                                                    html.Label("Max Results per Site:", className="fw-bold mb-2"),
                                                    dcc.Slider(
                                                        id="max-results-slider",
                                                        min=10,
                                                        max=100,
                                                        step=10,
                                                        value=50,
                                                        marks={10: "10", 25: "25", 50: "50", 75: "75", 100: "100"},
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                            
                                            # Enable Cache Toggle
                                            html.Div(
                                                [
                                                    dbc.Switch(
                                                        id="enable-cache-toggle",
                                                        label="Enable Smart Caching (recommended)",
                                                        value=True,
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                            
                                            # Sites Selection
                                            html.Div(
                                                [
                                                    html.Label("Active Job Sites:", className="fw-bold mb-2"),
                                                    dbc.Checklist(
                                                        id="active-sites-checklist",
                                                        options=[
                                                            {"label": " Indeed", "value": "indeed"},
                                                            {"label": " LinkedIn", "value": "linkedin"},
                                                            {"label": " Glassdoor", "value": "glassdoor"},
                                                            {"label": " ZipRecruiter", "value": "ziprecruiter"},
                                                        ],
                                                        value=["indeed", "linkedin", "glassdoor", "ziprecruiter"],
                                                        inline=True,
                                                        className="mb-3",
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ],
                                className="shadow-sm mb-4",
                            )
                        ],
                        width=6,
                    ),
                    
                    # Status and Progress
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5(
                                            [
                                                html.I(className="fas fa-chart-bar me-2"),
                                                "Scraper Status"
                                            ],
                                            className="mb-0"
                                        )
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="scraper-status-container",
                                                children=[
                                                    dbc.Alert(
                                                        [
                                                            html.I(className="fas fa-info-circle me-2"),
                                                            "Ready to start job search. Click a button above to begin."
                                                        ],
                                                        color="info",
                                                        className="mb-3",
                                                    ),
                                                    
                                                    # Progress Bar
                                                    html.Div(
                                                        [
                                                            html.Label("Progress:", className="fw-bold mb-2"),
                                                            dbc.Progress(
                                                                id="scraper-progress",
                                                                value=0,
                                                                className="mb-3",
                                                                striped=True,
                                                                animated=True,
                                                            ),
                                                        ],
                                                        id="progress-container",
                                                        style={"display": "none"},
                                                    ),
                                                    
                                                    # Stats Display
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    html.Div(
                                                                        [
                                                                            html.Small("Jobs Found", className="text-muted"),
                                                                            html.H3(
                                                                                id="scraper-jobs-found",
                                                                                children="0",
                                                                                className="text-primary",
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
                                                                            html.Small("Processed", className="text-muted"),
                                                                            html.H3(
                                                                                id="scraper-jobs-processed",
                                                                                children="0",
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
                                                                            html.Small("Errors", className="text-muted"),
                                                                            html.H3(
                                                                                id="scraper-errors",
                                                                                children="0",
                                                                                className="text-danger",
                                                                            ),
                                                                        ],
                                                                        className="text-center",
                                                                    )
                                                                ],
                                                                width=4,
                                                            ),
                                                        ],
                                                        className="mb-3",
                                                    ),
                                                    
                                                    # Last Run Info
                                                    html.Div(
                                                        [
                                                            html.Hr(),
                                                            html.Small(
                                                                [
                                                                    html.I(className="fas fa-clock me-2"),
                                                                    "Last run: ",
                                                                    html.Span(
                                                                        id="scraper-last-run",
                                                                        children="Never",
                                                                        className="fw-bold"
                                                                    ),
                                                                ],
                                                                className="text-muted",
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),
                                ],
                                className="shadow-sm mb-4",
                            )
                        ],
                        width=6,
                    ),
                ],
                className="mb-4",
            ),
            
            # Recent Activity Log
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5(
                                            [
                                                html.I(className="fas fa-list me-2"),
                                                "Recent Activity"
                                            ],
                                            className="mb-0"
                                        )
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="scraper-activity-log",
                                                children=[
                                                    html.P(
                                                        "No recent activity. Start a job search to see logs here.",
                                                        className="text-muted text-center",
                                                    )
                                                ],
                                                style={"maxHeight": "300px", "overflowY": "auto"},
                                            )
                                        ]
                                    ),
                                ],
                                className="shadow-sm",
                            )
                        ],
                        width=12,
                    ),
                ],
            ),
            
            # Toast for notifications
            dbc.Toast(
                id="scraper-toast",
                header="Scraper Notification",
                is_open=False,
                dismissable=True,
                icon="info",
                duration=4000,
                style={"position": "fixed", "top": 66, "right": 10, "width": 350, "zIndex": 9999},
            ),
        ],
        className="p-4",
    )
