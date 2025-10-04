"""
Ranked Jobs Layout - Unified job browsing with RCIP support
Combines job listing, ranking, RCIP badges, and quick actions
Enhanced with smart daily overview, skill gap analysis, and success prediction
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd
from datetime import datetime
from src.dashboard.dash_app.components.rcip_components import (
    create_rcip_filter_controls,
    create_rcip_stats_card,
    create_rcip_info_modal,
)
from src.dashboard.dash_app.components.professional_stats import create_stats_row
from src.dashboard.dash_app.components.skill_gap_analyzer import create_skill_gap_analysis_card
from src.dashboard.dash_app.components.success_predictor import create_success_predictor_card
from src.dashboard.dash_app.components.home_widgets import (
    create_top_companies_widget,
    create_location_insights_widget,
    create_recent_jobs_widget,
    create_application_tracker_widget,
)


def create_ranked_jobs_layout():
    """
    Create the ranked jobs layout with RCIP integration.
    Primary job-seeker interface for browsing and discovering opportunities.
    Enhanced with smart daily overview, skill gap analysis, and success prediction.
    """
    return html.Div(
        [
            # Professional header with date/time and job count badge
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div([
                                html.H2(
                                    [html.I(className="fas fa-home me-3 text-primary-custom"), "Smart Daily Overview"],
                                    className="mb-1",
                                ),
                                html.P(
                                    [
                                        html.I(className="fas fa-calendar-alt me-2"),
                                        html.Span(id="current-date-time", children=datetime.now().strftime("%A, %B %d, %Y")),
                                        html.Span(" • ", className="mx-2"),
                                        html.Span(id="total-jobs-badge", className="badge bg-primary-custom", children="0 Jobs")
                                    ],
                                    className="text-muted mb-0",
                                ),
                            ])
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        [html.I(className="fas fa-sync-alt me-2"), "Refresh"],
                                        id="refresh-ranked-jobs",
                                        color="primary",
                                        outline=True,
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-download me-2"), "Export"],
                                        id="export-ranked-jobs",
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
            
            # Professional stats row (4 stat cards)
            html.Div(
                id="home-stats-row",
                className="mb-4",
                children=[
                    dbc.Spinner(
                        html.Div("Loading stats...", className="text-center text-muted"),
                        color="primary",
                        size="sm"
                    )
                ]
            ),
            
            # Analytics row: Skill gap analysis and success predictor
            dbc.Row([
                dbc.Col([
                    html.Div(
                        id="skill-gap-analysis-container",
                        children=[
                            dbc.Spinner(
                                html.Div("Analyzing skills...", className="text-center text-muted p-3"),
                                color="primary",
                                size="sm"
                            )
                        ]
                    )
                ], width=12, lg=6),
                dbc.Col([
                    html.Div(
                        id="success-predictor-container",
                        children=[
                            dbc.Spinner(
                                html.Div("Calculating predictions...", className="text-center text-muted p-3"),
                                color="primary",
                                size="sm"
                            )
                        ]
                    )
                ], width=12, lg=6),
            ], className="mb-4"),
            
            # Recommended actions card
            html.Div(
                id="recommended-actions-container",
                className="mb-4",
                children=[
                    dbc.Spinner(
                        html.Div("Loading recommendations...", className="text-center text-muted"),
                        color="primary",
                        size="sm"
                    )
                ]
            ),
            
            # Additional insights row - Top Companies, Locations, Application Pipeline
            dbc.Row([
                dbc.Col([create_top_companies_widget()], width=12, lg=4, className="mb-4"),
                dbc.Col([create_location_insights_widget()], width=12, lg=4, className="mb-4"),
                dbc.Col([create_application_tracker_widget()], width=12, lg=4, className="mb-4"),
            ], className="mb-4"),
            
            # Recent jobs widget
            dbc.Row([
                dbc.Col([create_recent_jobs_widget()], width=12, className="mb-4"),
            ], className="mb-4"),
            
            # Divider
            html.Hr(className="my-4"),
            
            # Original page header for job listings
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H3(
                                [html.I(className="fas fa-star me-3 text-warning"), "Your Ranked Jobs"],
                                className="mb-1",
                            ),
                            html.P(
                                "AI-ranked job opportunities with RCIP immigration advantages",
                                className="text-muted",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            # Filters and stats row
            dbc.Row(
                [
                    # Left: Filters
                    dbc.Col(
                        [
                            # RCIP Filters
                            create_rcip_filter_controls(),
                            # Additional filters
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [html.I(className="fas fa-sliders-h me-2"), "Filters"]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Score filter
                                            html.Label("Minimum Match Score", className="mb-2"),
                                            dcc.Slider(
                                                id="min-score-slider",
                                                min=0,
                                                max=100,
                                                step=5,
                                                value=0,
                                                marks={0: "0%", 50: "50%", 100: "100%"},
                                                className="mb-3",
                                            ),
                                            # Date filter
                                            html.Label("Posted Within", className="mb-2"),
                                            dcc.Dropdown(
                                                id="date-filter-dropdown",
                                                options=[
                                                    {"label": "Any time", "value": "all"},
                                                    {"label": "Last 24 hours", "value": "1"},
                                                    {"label": "Last 3 days", "value": "3"},
                                                    {"label": "Last week", "value": "7"},
                                                    {"label": "Last month", "value": "30"},
                                                ],
                                                value="all",
                                                className="mb-3",
                                            ),
                                            # Location type filter
                                            html.Label("Work Location", className="mb-2"),
                                            dbc.Checklist(
                                                id="location-type-filter",
                                                options=[
                                                    {"label": " Remote", "value": "remote"},
                                                    {"label": " Hybrid", "value": "hybrid"},
                                                    {"label": " On-site", "value": "onsite"},
                                                ],
                                                value=["remote", "hybrid", "onsite"],
                                                inline=False,
                                                switch=True,
                                            ),
                                            # Clear filters
                                            dbc.Button(
                                                [
                                                    html.I(className="fas fa-times me-2"),
                                                    "Clear All",
                                                ],
                                                id="clear-filters-btn",
                                                color="secondary",
                                                outline=True,
                                                size="sm",
                                                className="w-100 mt-3",
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Keyword search
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [html.I(className="fas fa-search me-2"), "Keyword Search"]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Input(
                                                id="keyword-search-input",
                                                placeholder="Search titles, companies, skills...",
                                                type="text",
                                                className="mb-2",
                                            ),
                                            html.Small(
                                                "Searches job title, company, and skills",
                                                className="text-muted",
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=3,
                    ),
                    # Right: Job listings and stats
                    dbc.Col(
                        [
                            # Stats row
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
                                                                        className="fas fa-briefcase fa-2x text-primary mb-2"
                                                                    ),
                                                                    html.H3(
                                                                        id="total-jobs-count",
                                                                        children="--",
                                                                        className="mb-0",
                                                                    ),
                                                                    html.P(
                                                                        "Total Jobs",
                                                                        className="text-muted mb-0",
                                                                    ),
                                                                ],
                                                                className="text-center",
                                                            )
                                                        ]
                                                    )
                                                ],
                                                className="shadow-sm",
                                            )
                                        ],
                                        width=3,
                                    ),
                                    dbc.Col(
                                        [create_rcip_stats_card(0, 0)],
                                        width=3,
                                        id="rcip-stats-container",
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
                                                                        className="fas fa-star fa-2x text-warning mb-2"
                                                                    ),
                                                                    html.H3(
                                                                        id="high-match-count",
                                                                        children="--",
                                                                        className="mb-0",
                                                                    ),
                                                                    html.P(
                                                                        "High Match (>70%)",
                                                                        className="text-muted mb-0",
                                                                    ),
                                                                ],
                                                                className="text-center",
                                                            )
                                                        ]
                                                    )
                                                ],
                                                className="shadow-sm",
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
                                                                        className="fas fa-eye fa-2x text-info mb-2"
                                                                    ),
                                                                    html.H3(
                                                                        id="new-jobs-count",
                                                                        children="--",
                                                                        className="mb-0",
                                                                    ),
                                                                    html.P(
                                                                        "New Today",
                                                                        className="text-muted mb-0",
                                                                    ),
                                                                ],
                                                                className="text-center",
                                                            )
                                                        ]
                                                    )
                                                ],
                                                className="shadow-sm",
                                            )
                                        ],
                                        width=3,
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Sort controls
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Sort by:", className="me-2"),
                                            dcc.Dropdown(
                                                id="sort-dropdown",
                                                options=[
                                                    {
                                                        "label": "Best Match (Default)",
                                                        "value": "match_desc",
                                                    },
                                                    {
                                                        "label": "RCIP Priority",
                                                        "value": "rcip_priority",
                                                    },
                                                    {"label": "Newest First", "value": "date_desc"},
                                                    {
                                                        "label": "Company A-Z",
                                                        "value": "company_asc",
                                                    },
                                                ],
                                                value="match_desc",
                                                clearable=False,
                                                className="w-100",
                                            ),
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.InputGroup(
                                                [
                                                    dbc.InputGroupText(
                                                        [
                                                            html.I(className="fas fa-list me-2"),
                                                            "View",
                                                        ]
                                                    ),
                                                    dbc.Select(
                                                        id="view-mode-select",
                                                        options=[
                                                            {
                                                                "label": "Detailed Cards",
                                                                "value": "cards",
                                                            },
                                                            {
                                                                "label": "Compact List",
                                                                "value": "list",
                                                            },
                                                            {
                                                                "label": "Table View",
                                                                "value": "table",
                                                            },
                                                        ],
                                                        value="cards",
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=6,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Job listings container
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="ranked-jobs-container",
                                                children=[
                                                    dbc.Spinner(
                                                        html.Div(
                                                            "Loading jobs...",
                                                            className="text-center p-5",
                                                        ),
                                                        color="primary",
                                                    )
                                                ],
                                                style={
                                                    "maxHeight": "calc(100vh - 400px)",
                                                    "overflowY": "auto",
                                                },
                                            )
                                        ],
                                        className="p-2",
                                    )
                                ],
                                className="shadow-sm",
                            ),
                        ],
                        width=9,
                    ),
                ]
            ),
            # RCIP Info Modal
            create_rcip_info_modal(),
            # Hidden stores
            dcc.Store(id="filtered-jobs-store", storage_type="memory"),
            dcc.Store(id="sort-settings-store", storage_type="session"),
        ]
    )


def create_recommended_actions_card(actions: list) -> dbc.Card:
    """
    Create recommended actions card with actionable suggestions.
    
    Args:
        actions: List of action dicts with keys:
            - title: str
            - description: str
            - icon: str (FontAwesome class)
            - priority: str (high/medium/low)
            - action_type: str (skill/apply/profile/search)
    
    Returns:
        dbc.Card with recommended actions
    """
    if not actions:
        actions = [
            {
                "title": "Update Your Profile",
                "description": "Add more skills to improve job matching accuracy",
                "icon": "fas fa-user-edit",
                "priority": "medium",
                "action_type": "profile"
            },
            {
                "title": "Apply to High Match Jobs",
                "description": "You have jobs with 70%+ match waiting for your application",
                "icon": "fas fa-paper-plane",
                "priority": "high",
                "action_type": "apply"
            },
            {
                "title": "Expand Your Search",
                "description": "Try searching in nearby cities to find more opportunities",
                "icon": "fas fa-search-plus",
                "priority": "low",
                "action_type": "search"
            }
        ]
    
    action_items = []
    for action in actions[:5]:  # Show max 5 actions
        priority = action.get("priority", "low")
        
        # Priority color
        if priority == "high":
            border_color = "danger"
            icon_color = "danger"
        elif priority == "medium":
            border_color = "warning"
            icon_color = "warning"
        else:
            border_color = "info"
            icon_color = "info"
        
        action_items.append(
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.I(className=f"{action.get('icon', 'fas fa-lightbulb')} fa-2x text-{icon_color}")
                        ], width=2, className="text-center"),
                        dbc.Col([
                            html.H6(action.get("title", "Action"), className="mb-1"),
                            html.P(action.get("description", ""), className="text-muted mb-0", style={"fontSize": "14px"})
                        ], width=10)
                    ])
                ])
            ], className=f"mb-2 border-start border-{border_color} border-3")
        )
    
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.I(className="fas fa-lightbulb me-2"),
                html.Span("Recommended Actions", className="font-weight-semibold")
            ], className="d-flex align-items-center")
        ], className="bg-light"),
        dbc.CardBody([
            html.P(
                "Smart suggestions to improve your job search success:",
                className="text-muted mb-3",
                style={"fontSize": "14px"}
            ),
            html.Div(action_items)
        ])
    ], className="professional-card")


def create_job_card(job, view_mode="cards"):
    """
    Create a job card component with RCIP badges and quick actions.

    Args:
        job: Job dictionary with all fields
        view_mode: 'cards', 'list', or 'table'
    """
    from src.dashboard.dash_app.components.rcip_components import (
        create_rcip_badge,
        create_immigration_priority_badge,
        create_rcip_city_tag,
    )

    if view_mode == "list":
        # Compact list view
        return dbc.ListGroupItem(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H6(job.get("title", "No Title"), className="mb-1"),
                                        html.Small(
                                            [
                                                html.I(className="fas fa-building me-1"),
                                                job.get("company", "Unknown"),
                                                html.Span(" • ", className="mx-2"),
                                                html.I(className="fas fa-map-marker-alt me-1"),
                                                job.get("location", "Unknown"),
                                            ],
                                            className="text-muted",
                                        ),
                                    ]
                                )
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                create_rcip_badge(job.get("is_rcip_city", False)),
                                create_immigration_priority_badge(
                                    job.get("is_immigration_priority", False)
                                ),
                            ],
                            width=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Badge(
                                    f"{job.get('fit_score', 0):.0f}% Match" if job.get("fit_score") and not pd.isna(job.get("fit_score")) else "Not Rated",
                                    color="success" if job.get("fit_score", 0) > 70 else "warning" if job.get("fit_score", 0) > 50 else "secondary",
                                    className="me-2",
                                ),
                                dbc.Button(
                                    html.I(className="fas fa-external-link-alt"),
                                    size="sm",
                                    color="primary",
                                    outline=True,
                                    href=job.get("url", "#"),
                                    target="_blank",
                                ),
                            ],
                            width=3,
                            className="text-end",
                        ),
                    ]
                )
            ]
        )

    # Default: Detailed card view
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    # Header row
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H5(job.get("title", "No Title"), className="mb-1"),
                                    html.Div(
                                        [
                                            html.I(className="fas fa-building me-2 text-primary"),
                                            html.Strong(job.get("company", "Unknown Company")),
                                            html.Span(" • ", className="mx-2"),
                                            html.I(
                                                className="fas fa-map-marker-alt me-2 text-success"
                                            ),
                                            job.get("location", "Unknown Location"),
                                        ],
                                        className="text-muted mb-2",
                                    ),
                                    # Badges row
                                    html.Div(
                                        [
                                            create_rcip_badge(job.get("is_rcip_city", False)),
                                            create_immigration_priority_badge(
                                                job.get("is_immigration_priority", False)
                                            ),
                                            create_rcip_city_tag(
                                                job.get("city_tags", "").split(",")
                                                if job.get("city_tags")
                                                else []
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    # Match score
                                    html.Div(
                                        [
                                            dbc.Progress(
                                                value=job.get("fit_score", 0) if job.get("fit_score") and not pd.isna(job.get("fit_score")) else 0,
                                                color=(
                                                    "success"
                                                    if job.get("fit_score", 0) > 70
                                                    else (
                                                        "warning"
                                                        if job.get("fit_score", 0) > 50
                                                        else "danger"
                                                    )
                                                ),
                                                className="mb-2",
                                                style={"height": "8px"},
                                            ),
                                            html.Small(
                                                f"{job.get('fit_score', 0):.0f}% Match" if job.get("fit_score") and not pd.isna(job.get("fit_score")) else "Not Rated",
                                                className="text-muted",
                                            ),
                                        ],
                                        className="text-center mb-2",
                                    ),
                                    # Quick actions
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                html.I(className="fas fa-eye"),
                                                size="sm",
                                                color="info",
                                                outline=True,
                                                id={"type": "view-job-btn", "index": job.get("id")},
                                                title="View Details",
                                            ),
                                            dbc.Button(
                                                html.I(className="fas fa-bookmark"),
                                                size="sm",
                                                color="warning",
                                                outline=True,
                                                id={"type": "save-job-btn", "index": job.get("id")},
                                                title="Save for Later",
                                            ),
                                            dbc.Button(
                                                html.I(className="fas fa-external-link-alt"),
                                                size="sm",
                                                color="primary",
                                                outline=True,
                                                href=job.get("url", "#"),
                                                target="_blank",
                                                title="Open Job Posting",
                                            ),
                                        ],
                                        size="sm",
                                        className="w-100",
                                    ),
                                ],
                                width=4,
                                className="text-end",
                            ),
                        ]
                    ),
                    html.Hr(className="my-2"),
                    # Summary
                    html.P(
                        job.get("summary", "No summary available")[:200] + "...",
                        className="text-muted small mb-2",
                    ),
                    # Skills/keywords
                    (
                        html.Div(
                            [
                                dbc.Badge(
                                    skill, color="secondary", className="me-1 mb-1", pill=True
                                )
                                for skill in (job.get("skills", "") or "").split(",")[:5]
                                if skill.strip()
                            ]
                        )
                        if job.get("skills")
                        else html.Small("No skills listed", className="text-muted")
                    ),
                ]
            )
        ],
        className="mb-3 shadow-sm hover-shadow",
    )
