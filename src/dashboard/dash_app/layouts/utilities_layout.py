"""
Job Search Utilities Layout
Essential tools for job search management and productivity.
"""

from typing import Dict, List, Optional
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd


def create_utilities_layout() -> dbc.Container:
    """Create job search utilities dashboard layout."""

    return dbc.Container(
        [
            # Header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2(
                                [
                                    html.I(className="fas fa-tools me-3 text-primary"),
                                    "Job Search Utilities",
                                ],
                                className="mb-4",
                            ),
                            html.P(
                                "Essential tools to optimize your job search process and track progress.",
                                className="text-muted mb-4",
                            ),
                        ]
                    )
                ]
            ),
            # Quick Actions Row
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                [
                                                    html.I(className="fas fa-search me-2"),
                                                    "Quick Job Search",
                                                ],
                                                className="card-title",
                                            ),
                                            html.P(
                                                "Search jobs across all sources",
                                                className="card-text",
                                            ),
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(
                                                        id="quick-search-input",
                                                        placeholder="Enter keywords (e.g., python developer)",
                                                        type="text",
                                                    ),
                                                    dbc.Button(
                                                        "Search",
                                                        id="quick-search-btn",
                                                        color="primary",
                                                        n_clicks=0,
                                                    ),
                                                ]
                                            ),
                                            html.Div(id="quick-search-results", className="mt-3"),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                [
                                                    html.I(className="fas fa-download me-2"),
                                                    "Export Jobs",
                                                ],
                                                className="card-title",
                                            ),
                                            html.P("Download your job data", className="card-text"),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        "CSV Export",
                                                        id="export-csv-btn",
                                                        color="success",
                                                        size="sm",
                                                        n_clicks=0,
                                                    ),
                                                    dbc.Button(
                                                        "Excel Export",
                                                        id="export-excel-btn",
                                                        color="info",
                                                        size="sm",
                                                        n_clicks=0,
                                                    ),
                                                ],
                                                className="w-100",
                                            ),
                                            html.Div(id="export-status", className="mt-2"),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=6,
                    ),
                ],
                className="mb-4",
            ),
            # Job Application Tracker
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(className="fas fa-clipboard-list me-2"),
                                                    "Application Tracker",
                                                ],
                                                className="mb-0",
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Application status summary
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Card(
                                                                [
                                                                    dbc.CardBody(
                                                                        [
                                                                            html.H4(
                                                                                id="applied-count",
                                                                                children="0",
                                                                                className="text-primary mb-0",
                                                                            ),
                                                                            html.P(
                                                                                "Applied",
                                                                                className="text-muted mb-0",
                                                                            ),
                                                                        ],
                                                                        className="text-center",
                                                                    )
                                                                ],
                                                                color="primary",
                                                                outline=True,
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
                                                                            html.H4(
                                                                                id="interview-count",
                                                                                children="0",
                                                                                className="text-warning mb-0",
                                                                            ),
                                                                            html.P(
                                                                                "Interviews",
                                                                                className="text-muted mb-0",
                                                                            ),
                                                                        ],
                                                                        className="text-center",
                                                                    )
                                                                ],
                                                                color="warning",
                                                                outline=True,
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
                                                                            html.H4(
                                                                                id="offer-count",
                                                                                children="0",
                                                                                className="text-success mb-0",
                                                                            ),
                                                                            html.P(
                                                                                "Offers",
                                                                                className="text-muted mb-0",
                                                                            ),
                                                                        ],
                                                                        className="text-center",
                                                                    )
                                                                ],
                                                                color="success",
                                                                outline=True,
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
                                                                            html.H4(
                                                                                id="rejected-count",
                                                                                children="0",
                                                                                className="text-danger mb-0",
                                                                            ),
                                                                            html.P(
                                                                                "Rejected",
                                                                                className="text-muted mb-0",
                                                                            ),
                                                                        ],
                                                                        className="text-center",
                                                                    )
                                                                ],
                                                                color="danger",
                                                                outline=True,
                                                            )
                                                        ],
                                                        width=3,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            # Application timeline chart
                                            dcc.Graph(id="application-timeline-chart"),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    )
                ],
                className="mb-4",
            ),
            # Job Search Analytics
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(className="fas fa-chart-line me-2"),
                                                    "Search Analytics",
                                                ],
                                                className="mb-0",
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.H6("Jobs Found This Week"),
                                                            html.H4(
                                                                id="jobs-this-week",
                                                                children="0",
                                                                className="text-info",
                                                            ),
                                                        ],
                                                        width=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.H6("Average Match Score"),
                                                            html.H4(
                                                                id="avg-match-score",
                                                                children="0%",
                                                                className="text-success",
                                                            ),
                                                        ],
                                                        width=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.H6("Top Location"),
                                                            html.H4(
                                                                id="top-location",
                                                                children="--",
                                                                className="text-primary",
                                                            ),
                                                        ],
                                                        width=4,
                                                    ),
                                                ]
                                            ),
                                            html.Hr(),
                                            dcc.Graph(id="search-trends-chart"),
                                        ]
                                    ),
                                ]
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
                                            html.H5(
                                                [
                                                    html.I(className="fas fa-bullseye me-2"),
                                                    "Job Goals",
                                                ],
                                                className="mb-0",
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Weekly application goal
                                            html.H6("Weekly Application Goal"),
                                            dbc.Progress(
                                                id="weekly-goal-progress",
                                                value=0,
                                                max=10,
                                                striped=True,
                                                animated=True,
                                                className="mb-3",
                                            ),
                                            html.P(
                                                id="weekly-goal-text", children="0/10 applications"
                                            ),
                                            html.Hr(),
                                            # Quick goal setter
                                            html.H6("Set Weekly Goal"),
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(
                                                        id="goal-input",
                                                        type="number",
                                                        value=10,
                                                        min=1,
                                                        max=50,
                                                    ),
                                                    dbc.Button(
                                                        "Update",
                                                        id="update-goal-btn",
                                                        color="primary",
                                                        n_clicks=0,
                                                    ),
                                                ],
                                                size="sm",
                                            ),
                                            html.Hr(),
                                            # Motivation section
                                            html.H6("Daily Motivation"),
                                            html.P(
                                                id="daily-motivation",
                                                children="Keep pushing forward! Every application gets you closer to your dream job.",
                                                className="text-muted font-italic",
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=4,
                    ),
                ],
                className="mb-4",
            ),
            # Skill Gap Analysis
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(className="fas fa-graduation-cap me-2"),
                                                    "Skill Gap Analysis",
                                                ],
                                                className="mb-0",
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P(
                                                "Identify skills to improve based on job requirements"
                                            ),
                                            dbc.Button(
                                                "Analyze Skills",
                                                id="analyze-skills-btn",
                                                color="info",
                                                n_clicks=0,
                                                className="mb-3",
                                            ),
                                            html.Div(id="skill-analysis-results"),
                                        ]
                                    ),
                                ]
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
                                            html.H5(
                                                [
                                                    html.I(className="fas fa-calendar-check me-2"),
                                                    "Interview Scheduler",
                                                ],
                                                className="mb-0",
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P("Track upcoming interviews and preparation"),
                                            dbc.Form(
                                                [
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label("Company"),
                                                                    dbc.Input(
                                                                        id="interview-company",
                                                                        placeholder="Company name",
                                                                    ),
                                                                ],
                                                                width=6,
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label("Date"),
                                                                    dbc.Input(
                                                                        id="interview-date",
                                                                        type="date",
                                                                    ),
                                                                ],
                                                                width=6,
                                                            ),
                                                        ],
                                                        className="mb-2",
                                                    ),
                                                    dbc.Button(
                                                        "Add Interview",
                                                        id="add-interview-btn",
                                                        color="success",
                                                        size="sm",
                                                        n_clicks=0,
                                                    ),
                                                ]
                                            ),
                                            html.Div(id="interview-list", className="mt-3"),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                ]
            ),
        ],
        fluid=True,
    )


# Callback for quick job search
@callback(
    Output("quick-search-results", "children"),
    Input("quick-search-btn", "n_clicks"),
    State("quick-search-input", "value"),
    prevent_initial_call=True,
)
def perform_quick_search(n_clicks: int, search_term: str) -> html.Div:
    """Perform quick job search and display results."""
    if not search_term:
        return dbc.Alert("Please enter search keywords", color="warning")

    try:
        # Mock search results for now - replace with actual search
        results = [
            {
                "title": f"Python Developer - {search_term}",
                "company": "Tech Corp",
                "location": "Toronto",
            },
            {
                "title": f"Senior {search_term} Engineer",
                "company": "StartupXYZ",
                "location": "Vancouver",
            },
            {"title": f"{search_term} Specialist", "company": "BigTech Inc", "location": "Remote"},
        ]

        if results:
            result_cards = []
            for job in results[:3]:  # Show top 3
                result_cards.append(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H6(job["title"], className="card-title"),
                                    html.P(
                                        f"{job['company']} • {job['location']}",
                                        className="card-text text-muted",
                                    ),
                                ]
                            )
                        ],
                        className="mb-2",
                    )
                )

            return html.Div(
                [
                    dbc.Alert(f"Found {len(results)} jobs for '{search_term}'", color="success"),
                    html.Div(result_cards),
                ]
            )
        else:
            return dbc.Alert(f"No jobs found for '{search_term}'", color="info")

    except Exception as e:
        return dbc.Alert(f"Search error: {str(e)}", color="danger")


# Callback for application statistics
@callback(
    [
        Output("applied-count", "children"),
        Output("interview-count", "children"),
        Output("offer-count", "children"),
        Output("rejected-count", "children"),
        Output("application-timeline-chart", "figure"),
    ],
    Input("auto-refresh-interval", "n_intervals"),
    prevent_initial_call=False,
)
def update_application_stats(n_intervals: int) -> tuple:
    """Update application tracking statistics."""
    try:
        # Mock data - replace with actual database queries
        applied = 15
        interviews = 3
        offers = 1
        rejected = 5

        # Create timeline chart
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        applications = [
            0,
            1,
            0,
            2,
            1,
            0,
            0,
            3,
            1,
            2,
            0,
            1,
            0,
            0,
            2,
            1,
            0,
            1,
            3,
            0,
            1,
            0,
            2,
            1,
            0,
            0,
            1,
            2,
            0,
            1,
        ]

        fig = px.line(
            x=dates,
            y=applications,
            title="Daily Applications Submitted",
            labels={"x": "Date", "y": "Applications"},
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white"
        )

        return str(applied), str(interviews), str(offers), str(rejected), fig

    except Exception:
        return "0", "0", "0", "0", {}


# Callback for search analytics
@callback(
    [
        Output("jobs-this-week", "children"),
        Output("avg-match-score", "children"),
        Output("top-location", "children"),
        Output("search-trends-chart", "figure"),
    ],
    Input("auto-refresh-interval", "n_intervals"),
    prevent_initial_call=False,
)
def update_search_analytics(n_intervals: int) -> tuple:
    """Update job search analytics."""
    try:
        # Mock analytics data
        jobs_week = 47
        avg_score = 78
        top_loc = "Toronto"

        # Create trends chart
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        jobs_found = [12, 8, 15, 10, 18, 5, 3]

        fig = px.bar(
            x=days,
            y=jobs_found,
            title="Jobs Found This Week",
            labels={"x": "Day", "y": "Jobs Found"},
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white"
        )

        return str(jobs_week), f"{avg_score}%", top_loc, fig

    except Exception:
        return "0", "0%", "--", {}


# Callback for skill analysis
@callback(
    Output("skill-analysis-results", "children"),
    Input("analyze-skills-btn", "n_clicks"),
    prevent_initial_call=True,
)
def analyze_skills(n_clicks: int) -> html.Div:
    """Analyze skill gaps based on job requirements."""
    try:
        # Mock skill analysis
        missing_skills = [
            {"skill": "Docker", "frequency": 85, "priority": "High"},
            {"skill": "Kubernetes", "frequency": 72, "priority": "High"},
            {"skill": "AWS", "frequency": 68, "priority": "Medium"},
            {"skill": "React", "frequency": 45, "priority": "Medium"},
        ]

        skill_cards = []
        for skill in missing_skills:
            color = "danger" if skill["priority"] == "High" else "warning"
            skill_cards.append(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H6(skill["skill"], className="card-title"),
                                html.P(
                                    f"Appears in {skill['frequency']}% of jobs",
                                    className="card-text",
                                ),
                                dbc.Badge(skill["priority"], color=color),
                            ]
                        )
                    ],
                    className="mb-2",
                )
            )

        return html.Div(
            [
                dbc.Alert("Analysis complete! Focus on these skills:", color="info"),
                html.Div(skill_cards),
            ]
        )

    except Exception as e:
        return dbc.Alert(f"Analysis error: {str(e)}", color="danger")


# Callback for weekly goal progress
@callback(
    [Output("weekly-goal-progress", "value"), Output("weekly-goal-text", "children")],
    Input("auto-refresh-interval", "n_intervals"),
    prevent_initial_call=False,
)
def update_weekly_goal(n_intervals: int) -> tuple:
    """Update weekly application goal progress."""
    try:
        # Mock data - replace with actual tracking
        current_applications = 7
        weekly_goal = 10

        progress_text = f"{current_applications}/{weekly_goal} applications this week"

        return current_applications, progress_text

    except Exception:
        return 0, "0/10 applications this week"
