"""
Enhanced Home Layout for JobQst Dashboard
Complete dashboard-centric experience with scheduling and automation
"""

import dash_bootstrap_components as dbc
from dash import html, dcc


def create_enhanced_home_layout():
    """Create the enhanced home dashboard with automation features"""

    return html.Div(
        [
            # Welcome banner with quick actions
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H3(
                                                "🚀 Welcome to JobQst",
                                                className="text-primary mb-0",
                                            ),
                                            html.P(
                                                "Your AI-powered job discovery platform",
                                                className="text-muted",
                                            ),
                                        ],
                                        width=8,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Button(
                                                "🎯 Start Job Search",
                                                id="quick-start-btn",
                                                color="success",
                                                size="lg",
                                                className="w-100",
                                            )
                                        ],
                                        width=4,
                                    ),
                                ]
                            )
                        ]
                    )
                ],
                className="mb-4",
            ),
            # Quick stats and status
            dbc.Row(
                [
                    dbc.Col(
                        [create_stat_card("📊 Total Jobs", "0", "jobs-total-count", "primary")],
                        width=3,
                    ),
                    dbc.Col(
                        [create_stat_card("⭐ High Matches", "0", "high-match-count", "success")],
                        width=3,
                    ),
                    dbc.Col(
                        [create_stat_card("📅 Scheduled", "0", "scheduled-count", "info")], width=3
                    ),
                    dbc.Col(
                        [create_stat_card("🎯 Applied", "0", "applied-count", "warning")], width=3
                    ),
                ],
                className="mb-4",
            ),
            # Main dashboard content
            dbc.Row(
                [
                    # Left column - Job feed and quick actions
                    dbc.Col(
                        [
                            # Quick filters
                            dbc.Card(
                                [
                                    dbc.CardHeader("🔍 Quick Filters"),
                                    dbc.CardBody(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dcc.Dropdown(
                                                                id="home-location-filter",
                                                                placeholder="Location",
                                                                options=[
                                                                    {
                                                                        "label": "Remote",
                                                                        "value": "remote",
                                                                    },
                                                                    {
                                                                        "label": "Toronto",
                                                                        "value": "toronto",
                                                                    },
                                                                    {
                                                                        "label": "Vancouver",
                                                                        "value": "vancouver",
                                                                    },
                                                                    {
                                                                        "label": "Montreal",
                                                                        "value": "montreal",
                                                                    },
                                                                ],
                                                            )
                                                        ],
                                                        width=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dcc.Dropdown(
                                                                id="home-salary-filter",
                                                                placeholder="Salary Range",
                                                                options=[
                                                                    {
                                                                        "label": "$50k+",
                                                                        "value": "50000",
                                                                    },
                                                                    {
                                                                        "label": "$75k+",
                                                                        "value": "75000",
                                                                    },
                                                                    {
                                                                        "label": "$100k+",
                                                                        "value": "100000",
                                                                    },
                                                                    {
                                                                        "label": "$150k+",
                                                                        "value": "150000",
                                                                    },
                                                                ],
                                                            )
                                                        ],
                                                        width=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Button(
                                                                "Apply Filters",
                                                                id="apply-filters-btn",
                                                                color="primary",
                                                                className="w-100",
                                                            )
                                                        ],
                                                        width=4,
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Job feed
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.H5(
                                                                "🎯 Latest Job Matches",
                                                                className="mb-0",
                                                            )
                                                        ],
                                                        width=8,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Button(
                                                                "🔄 Refresh",
                                                                id="refresh-jobs-btn",
                                                                size="sm",
                                                                outline=True,
                                                            )
                                                        ],
                                                        width=4,
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="home-job-feed",
                                                children=[create_placeholder_job_cards()],
                                            )
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=8,
                    ),
                    # Right column - Automation and scheduling
                    dbc.Col(
                        [
                            # Automation status
                            dbc.Card(
                                [
                                    dbc.CardHeader("🤖 Automation Status"),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="automation-status",
                                                children=[create_automation_status_display()],
                                            )
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Quick schedule creator
                            dbc.Card(
                                [
                                    dbc.CardHeader("⏰ Quick Schedule"),
                                    dbc.CardBody(
                                        [
                                            html.Label("Schedule Type", className="fw-semibold"),
                                            dcc.Dropdown(
                                                id="quick-schedule-type",
                                                options=[
                                                    {
                                                        "label": "📅 Daily at 9 AM",
                                                        "value": "daily_9am",
                                                    },
                                                    {
                                                        "label": "📅 Twice Daily (9 AM, 6 PM)",
                                                        "value": "twice_daily",
                                                    },
                                                    {
                                                        "label": "📅 Weekly Monday 9 AM",
                                                        "value": "weekly_monday",
                                                    },
                                                    {
                                                        "label": "📅 Custom Schedule",
                                                        "value": "custom",
                                                    },
                                                ],
                                                placeholder="Choose schedule...",
                                            ),
                                            html.Label(
                                                "Search Keywords", className="fw-semibold mt-3"
                                            ),
                                            dbc.Input(
                                                id="quick-schedule-keywords",
                                                placeholder="python, data scientist, remote",
                                            ),
                                            dbc.Button(
                                                "⚡ Start Automation",
                                                id="start-automation-btn",
                                                color="success",
                                                className="w-100 mt-3",
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Recent activity
                            dbc.Card(
                                [
                                    dbc.CardHeader("📈 Recent Activity"),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="recent-activity",
                                                children=[create_activity_timeline()],
                                            )
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=4,
                    ),
                ]
            ),
        ]
    )


def create_stat_card(title, value, id_suffix, color):
    """Create a statistics card"""
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4(value, id=f"stat-{id_suffix}", className=f"text-{color} mb-0"),
                    html.P(title, className="text-muted small mb-0"),
                ]
            )
        ]
    )


def create_placeholder_job_cards():
    """Create placeholder job cards for the feed"""
    return html.Div(
        [
            dbc.Alert(
                "🎯 Start your first job search to see matches here!",
                color="info",
                className="text-center",
            )
        ]
    )


def create_automation_status_display():
    """Create automation status display"""
    return html.Div(
        [
            dbc.Badge("⏸️ Stopped", color="secondary", className="mb-2 w-100"),
            html.P("No scheduled searches active", className="text-muted small mb-0"),
            dbc.Button(
                "⚙️ Setup Automation",
                id="setup-automation-btn",
                size="sm",
                outline=True,
                className="w-100 mt-2",
            ),
        ]
    )


def create_activity_timeline():
    """Create recent activity timeline"""
    return html.Div(
        [
            html.P("📊 Dashboard initialized", className="small mb-1"),
            html.P("⚙️ Ready to start job search", className="small text-muted mb-0"),
        ]
    )
