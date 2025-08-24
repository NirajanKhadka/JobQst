"""
Scraping layout for JobLens Dashboard
Job scraping controls and monitoring
"""
import dash_bootstrap_components as dbc
from dash import html, dcc

from ..components.navigation import create_page_header


def create_scraping_layout():
    """Create the job scraping layout"""
    
    return html.Div([
        # Page header
        create_page_header(
            "🔍 Job Scraping",
            "Search and scrape job listings from multiple sources"
        ),
        
        # Scraping status overview
        dbc.Row([
            dbc.Col([
                create_status_card(
                    "Last Scrape", "Never", "fas fa-clock", "info",
                    "last-scrape-status"
                )
            ], width=3),
            dbc.Col([
                create_status_card(
                    "Active Scrapers", "0", "fas fa-spider", "secondary",
                    "active-scrapers"
                )
            ], width=3),
            dbc.Col([
                create_status_card(
                    "Jobs Found", "0", "fas fa-briefcase", "primary",
                    "jobs-found-count"
                )
            ], width=3),
            dbc.Col([
                create_status_card(
                    "Success Rate", "0%", "fas fa-percentage", "success",
                    "scrape-success-rate"
                )
            ], width=3)
        ], className="mb-4"),
        
        # Quick Actions
        dbc.Card([
            dbc.CardHeader("⚡ Quick Actions"),
            dbc.CardBody([
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-play me-2"),
                        "Start JobSpy Pipeline"
                    ], color="primary", size="lg",
                       id="start-jobspy-pipeline-btn"),
                    
                    dbc.Button([
                        html.I(className="fas fa-search me-2"),
                        "Quick Scrape"
                    ], color="success", size="lg",
                       id="quick-scrape-btn"),
                    
                    dbc.Button([
                        html.I(className="fas fa-sync me-2"),
                        "Refresh Status"
                    ], color="outline-secondary", size="lg",
                       id="refresh-scrape-status-btn")
                ], style={"width": "100%"})
            ])
        ], className="mb-4"),
        
        # Scraping Configuration
        dbc.Card([
            dbc.CardHeader("⚙️ Scraping Configuration"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Search Keywords",
                                   className="fw-semibold"),
                        dbc.Textarea(
                            id="scrape-keywords",
                            placeholder=("Enter keywords separated by commas "
                                         "(e.g., python, software engineer, "
                                         "machine learning)"),
                            rows=3,
                            value="python, software engineer, machine learning"
                        )
                    ], width=6),
                    
                    dbc.Col([
                        html.Label("Job Sites", className="fw-semibold"),
                        dcc.Dropdown(
                            id="scrape-sites",
                            options=[
                                {'label': 'Indeed', 'value': 'indeed'},
                                {'label': 'LinkedIn', 'value': 'linkedin'},
                                {'label': 'Glassdoor', 'value': 'glassdoor'},
                                {'label': 'ZipRecruiter', 'value': 'zip_recruiter'}
                            ],
                            value=['indeed', 'linkedin'],
                            multi=True
                        )
                    ], width=6)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        html.Label("Country/Region",
                                   className="fw-semibold"),
                        dcc.Dropdown(
                            id="scrape-country",
                            options=[
                                {'label': 'Canada', 'value': 'canada'},
                                {'label': 'USA', 'value': 'usa'},
                                {'label': 'UK', 'value': 'uk'}
                            ],
                            value='canada'
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Max Jobs per Site",
                                   className="fw-semibold"),
                        dbc.Input(
                            id="max-jobs-per-site",
                            type="number",
                            min=10,
                            max=500,
                            value=50
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("Location", className="fw-semibold"),
                        dbc.Input(
                            id="scrape-location",
                            placeholder="e.g., Toronto, ON",
                            value="Toronto, ON"
                        )
                    ], width=4)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Checklist(
                            id="scraping-options",
                            options=[
                                {'label': 'Auto-process after scraping',
                                 'value': 'auto_process'},
                                {'label': 'Remove duplicates',
                                 'value': 'remove_duplicates'},
                                {'label': 'Enable notifications',
                                 'value': 'notifications'}
                            ],
                            value=['auto_process', 'remove_duplicates'],
                            inline=True
                        )
                    ], width=12)
                ], className="mb-3"),
                
                dbc.Button([
                    html.I(className="fas fa-rocket me-2"),
                    "Start Custom Scrape"
                ], color="primary", size="lg",
                   id="start-custom-scrape-btn",
                   style={"width": "100%"})
            ])
        ], className="mb-4"),
        
        # Live Status and Logs
        dbc.Card([
            dbc.CardHeader("📊 Live Status & Logs"),
            dbc.CardBody([
                # Progress bars
                html.Div(id="scraping-progress"),
                
                # Live log output
                html.Div([
                    html.H6("Scraping Logs", className="mb-2"),
                    dcc.Textarea(
                        id="scraping-logs",
                        style={
                            'width': '100%',
                            'height': '200px',
                            'fontFamily': 'monospace',
                            'fontSize': '12px',
                            'backgroundColor': '#f8f9fa'
                        },
                        value="Ready to start scraping...",
                        disabled=True
                    )
                ])
            ])
        ])
    ])


def create_status_card(title, value, icon, color, card_id):
    """Create a status card component"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"{icon} fa-2x text-{color}"),
                html.H4(value, className="mb-0", id=card_id),
                html.P(title, className="text-muted mb-0")
            ], className="text-center")
        ])
    ], className="h-100")
