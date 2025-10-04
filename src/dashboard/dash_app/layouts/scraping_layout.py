"""
Scraping layout for JobQst Dashboard
Job scraping controls and monitoring
"""

import dash_bootstrap_components as dbc
from dash import html, dcc

from src.dashboard.dash_app.components.navigation import create_page_header


def create_scraping_layout():
    """Create the job scraping layout"""

    return html.Div(
        [
            # Page header
            create_page_header(
                "🔍 Job Scraping", "Search and scrape job listings from multiple sources"
            ),
            # Scraping status overview
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_status_card(
                                "Last Scrape", "Never", "fas fa-clock", "info", "last-scrape-status"
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            create_status_card(
                                "Active Scrapers",
                                "0",
                                "fas fa-spider",
                                "secondary",
                                "active-scrapers",
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            create_status_card(
                                "Jobs Found", "0", "fas fa-briefcase", "primary", "jobs-found-count"
                            )
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            create_status_card(
                                "Success Rate",
                                "0%",
                                "fas fa-percentage",
                                "success",
                                "scrape-success-rate",
                            )
                        ],
                        width=3,
                    ),
                ],
                className="mb-4",
            ),
            # Quick Actions
            dbc.Card(
                [
                    dbc.CardHeader("⚡ Quick Actions"),
                    dbc.CardBody(
                        [
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-play me-2"),
                                            "Start JobSpy Pipeline",
                                        ],
                                        color="primary",
                                        size="lg",
                                        id="start-jobspy-pipeline-btn",
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-search me-2"), "Quick Scrape"],
                                        color="success",
                                        size="lg",
                                        id="quick-scrape-btn",
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-sync me-2"), "Refresh Status"],
                                        color="outline-secondary",
                                        size="lg",
                                        id="refresh-scrape-status-btn",
                                    ),
                                ],
                                style={"width": "100%"},
                            )
                        ]
                    ),
                ],
                className="mb-4",
            ),
            # Scraping Configuration
            dbc.Card(
                [
                    dbc.CardHeader("⚙️ Scraping Configuration"),
                    dbc.CardBody(
                        [
                            # Job Sites Selection
                            html.H6("Select Job Sites", className="mb-3"),
                            dbc.Checklist(
                                id="scrape-sites-checkboxes",
                                options=[
                                    {"label": " Indeed", "value": "indeed"},
                                    {"label": " LinkedIn", "value": "linkedin"},
                                    {"label": " Glassdoor", "value": "glassdoor"},
                                    {"label": " ZipRecruiter", "value": "zip_recruiter"},
                                ],
                                value=["indeed", "linkedin"],
                                inline=True,
                                className="mb-3"
                            ),
                            
                            html.Hr(),
                            
                            # Keywords and Location
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Search Keywords", className="fw-semibold"),
                                            dbc.Textarea(
                                                id="scrape-keywords",
                                                placeholder=(
                                                    "Enter keywords separated by commas "
                                                    "(e.g., python, data analyst, machine learning)"
                                                ),
                                                rows=2,
                                                value="python, data analyst",
                                            ),
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Location", className="fw-semibold"),
                                            dbc.Input(
                                                id="scrape-location",
                                                placeholder="e.g., Toronto, ON",
                                                value="Toronto, ON",
                                                className="mb-2"
                                            ),
                                            html.Label("Country", className="fw-semibold"),
                                            dcc.Dropdown(
                                                id="scrape-country",
                                                options=[
                                                    {"label": "Canada", "value": "canada"},
                                                    {"label": "USA", "value": "usa"},
                                                    {"label": "UK", "value": "uk"},
                                                ],
                                                value="canada",
                                            ),
                                        ],
                                        width=6,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            
                            html.Hr(),
                            
                            # Scraping Options
                            html.H6("Scraping Options", className="mb-3"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Max Jobs per Site", className="fw-semibold"),
                                            dbc.Input(
                                                id="max-jobs-per-site",
                                                type="number",
                                                min=10,
                                                max=500,
                                                value=50,
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Minimum Salary (CAD)", className="fw-semibold"),
                                            dbc.Input(
                                                id="scrape-min-salary",
                                                type="number",
                                                min=0,
                                                max=200000,
                                                step=5000,
                                                value=60000,
                                                placeholder="Optional"
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Options", className="fw-semibold"),
                                            dbc.Checklist(
                                                id="scraping-options",
                                                options=[
                                                    {"label": "Remove duplicates", "value": "deduplication"},
                                                    {"label": "RCIP jobs only", "value": "rcip_only"},
                                                ],
                                                value=["deduplication"],
                                            ),
                                        ],
                                        width=4,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            
                            html.Hr(),
                            
                            # Start button
                            dbc.Button(
                                [html.I(className="fas fa-rocket me-2"), "Start Scraping"],
                                color="primary",
                                size="lg",
                                id="start-custom-scrape-btn",
                                style={"width": "100%"},
                            ),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            # Status Panel
            dbc.Card(
                [
                    dbc.CardHeader("📊 Scraping Status"),
                    dbc.CardBody(
                        [
                            # Progress bar
                            html.Div(
                                [
                                    html.H6("Progress", className="mb-2"),
                                    dbc.Progress(
                                        id="scraping-progress-bar",
                                        value=0,
                                        max=100,
                                        striped=True,
                                        animated=True,
                                        className="mb-3",
                                        style={"height": "25px"}
                                    ),
                                ],
                                className="mb-3"
                            ),
                            
                            # Status messages
                            html.Div(
                                [
                                    html.H6("Status Messages", className="mb-2"),
                                    html.Div(
                                        id="scraping-status-messages",
                                        style={
                                            "maxHeight": "150px",
                                            "overflowY": "auto",
                                            "backgroundColor": "#f8f9fa",
                                            "padding": "10px",
                                            "borderRadius": "4px",
                                            "fontFamily": "monospace",
                                            "fontSize": "12px"
                                        },
                                        children=[html.P("Ready to start scraping...", className="mb-0 text-muted")]
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            
            # Results Summary Panel
            dbc.Card(
                [
                    dbc.CardHeader("📈 Results Summary"),
                    dbc.CardBody(
                        [
                            html.Div(id="scraping-results-summary")
                        ]
                    ),
                ]
            ),
        ]
    )


def create_status_card(title, value, icon, color, card_id):
    """Create a status card component"""
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(className=f"{icon} fa-2x text-{color}"),
                            html.H4(value, className="mb-0", id=card_id),
                            html.P(title, className="text-muted mb-0"),
                        ],
                        className="text-center",
                    )
                ]
            )
        ],
        className="h-100",
    )
