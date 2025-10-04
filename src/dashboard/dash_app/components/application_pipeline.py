"""
Application Pipeline Component
Kanban-style pipeline visualization for job application tracking
"""

import dash_bootstrap_components as dbc
from dash import html
from typing import List, Dict, Optional
from datetime import datetime


# Pipeline stage configuration
PIPELINE_STAGES = [
    {
        "id": "interested",
        "name": "Interested",
        "icon": "fas fa-eye",
        "color": "info",
        "description": "Jobs you're considering"
    },
    {
        "id": "applied",
        "name": "Applied",
        "icon": "fas fa-paper-plane",
        "color": "primary",
        "description": "Applications submitted"
    },
    {
        "id": "interview",
        "name": "Interview",
        "icon": "fas fa-calendar-alt",
        "color": "warning",
        "description": "Interview scheduled"
    },
    {
        "id": "offer",
        "name": "Offer",
        "icon": "fas fa-trophy",
        "color": "success",
        "description": "Offer received"
    },
    {
        "id": "rejected",
        "name": "Rejected",
        "icon": "fas fa-times-circle",
        "color": "danger",
        "description": "Not selected"
    }
]


def create_pipeline_column(
    stage: Dict,
    applications: List[Dict],
    count: int
) -> dbc.Col:
    """
    Create a single pipeline column with applications.
    
    Args:
        stage: Stage configuration dict
        applications: List of applications in this stage
        count: Number of applications in this stage
    
    Returns:
        dbc.Col containing the pipeline column
    """
    stage_id = stage["id"]
    stage_name = stage["name"]
    stage_icon = stage["icon"]
    stage_color = stage["color"]
    
    # Create application cards for this stage
    app_cards = []
    for app in applications:
        app_cards.append(create_application_card(app, stage_color))
    
    # Empty state if no applications
    if not app_cards:
        app_cards = [
            html.Div([
                html.I(className=f"{stage_icon} fa-2x text-muted mb-2"),
                html.P("No applications yet", className="text-muted small mb-0")
            ], className="text-center py-4")
        ]
    
    return dbc.Col([
        dbc.Card([
            # Column header with color-coded styling
            dbc.CardHeader([
                html.Div([
                    html.I(className=f"{stage_icon} me-2"),
                    html.Span(stage_name, className="fw-semibold"),
                    dbc.Badge(
                        str(count),
                        color=stage_color,
                        className="ms-2",
                        pill=True
                    )
                ], className="d-flex align-items-center justify-content-between")
            ], className=f"bg-{stage_color} text-white"),
            
            # Column body with applications
            dbc.CardBody([
                html.Div(
                    app_cards,
                    className="pipeline-column-content",
                    style={
                        "minHeight": "400px",
                        "maxHeight": "600px",
                        "overflowY": "auto"
                    }
                )
            ], className="p-2")
        ], className="pipeline-column shadow-sm")
    ], width=12, lg=2, className="mb-3 mb-lg-0")


def create_application_card(app: Dict, stage_color: str) -> dbc.Card:
    """
    Create an application card for the pipeline.
    
    Args:
        app: Application dictionary
        stage_color: Color of the current stage
    
    Returns:
        dbc.Card component
    """
    app_id = app.get("id", "")
    job_title = app.get("job_title", "Unknown Position")
    company = app.get("company", "Unknown Company")
    date_applied = app.get("date_applied", "")
    deadline = app.get("deadline", "")
    notes = app.get("notes", "")
    
    # Calculate days since applied
    days_since = ""
    if date_applied:
        try:
            applied_date = datetime.strptime(date_applied, "%Y-%m-%d")
            days = (datetime.now() - applied_date).days
            if days == 0:
                days_since = "Today"
            elif days == 1:
                days_since = "Yesterday"
            else:
                days_since = f"{days} days ago"
        except:
            days_since = date_applied
    
    # Deadline indicator
    deadline_badge = None
    if deadline:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            days_until = (deadline_date - datetime.now()).days
            if days_until < 0:
                deadline_badge = dbc.Badge("Overdue", color="danger", className="me-1")
            elif days_until == 0:
                deadline_badge = dbc.Badge("Today", color="warning", className="me-1")
            elif days_until <= 3:
                deadline_badge = dbc.Badge(f"{days_until}d left", color="warning", className="me-1")
            else:
                deadline_badge = dbc.Badge(f"{days_until}d left", color="info", className="me-1")
        except:
            pass
    
    return dbc.Card([
        dbc.CardBody([
            html.H6(job_title, className="mb-1", style={"fontSize": "14px"}),
            html.P(company, className="text-muted small mb-2"),
            
            # Metadata
            html.Div([
                html.Small([
                    html.I(className="fas fa-clock me-1"),
                    days_since
                ], className="text-muted d-block mb-1"),
                
                deadline_badge if deadline_badge else html.Div()
            ]),
            
            # Notes preview
            (html.P(
                notes[:50] + "..." if len(notes) > 50 else notes,
                className="small text-muted mb-2 mt-2"
            ) if notes else html.Div()),
            
            # Action buttons
            dbc.ButtonGroup([
                dbc.Button(
                    html.I(className="fas fa-eye"),
                    size="sm",
                    color=stage_color,
                    outline=True,
                    id={"type": "view-application", "index": app_id},
                    title="View Details"
                ),
                dbc.Button(
                    html.I(className="fas fa-edit"),
                    size="sm",
                    color="secondary",
                    outline=True,
                    id={"type": "edit-application", "index": app_id},
                    title="Edit"
                )
            ], size="sm", className="w-100 mt-2")
        ])
    ], className="mb-2 application-card hover-lift", style={"cursor": "pointer"})


def create_application_pipeline(applications_by_stage: Dict[str, List[Dict]]) -> dbc.Row:
    """
    Create the full Kanban-style application pipeline.
    
    Args:
        applications_by_stage: Dict mapping stage IDs to lists of applications
    
    Returns:
        dbc.Row containing all pipeline columns
    """
    columns = []
    
    for stage in PIPELINE_STAGES:
        stage_id = stage["id"]
        apps = applications_by_stage.get(stage_id, [])
        count = len(apps)
        
        column = create_pipeline_column(stage, apps, count)
        columns.append(column)
    
    return dbc.Row(columns, className="pipeline-row")


def create_deadline_tracker(applications: List[Dict]) -> dbc.Card:
    """
    Create deadline tracker component showing upcoming deadlines.
    
    Args:
        applications: List of all applications
    
    Returns:
        dbc.Card with deadline timeline
    """
    # Filter applications with deadlines
    apps_with_deadlines = [
        app for app in applications
        if app.get("deadline")
    ]
    
    # Sort by deadline
    apps_with_deadlines.sort(
        key=lambda x: x.get("deadline", "9999-12-31")
    )
    
    # Create timeline items
    timeline_items = []
    for app in apps_with_deadlines[:10]:  # Show top 10
        deadline = app.get("deadline", "")
        job_title = app.get("job_title", "Unknown")
        company = app.get("company", "Unknown")
        
        # Calculate urgency
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            days_until = (deadline_date - datetime.now()).days
            
            if days_until < 0:
                urgency = "urgent"
                urgency_color = "danger"
                urgency_text = "Overdue"
            elif days_until == 0:
                urgency = "urgent"
                urgency_color = "danger"
                urgency_text = "Today"
            elif days_until <= 3:
                urgency = "soon"
                urgency_color = "warning"
                urgency_text = f"In {days_until} days"
            else:
                urgency = "normal"
                urgency_color = "info"
                urgency_text = f"In {days_until} days"
        except:
            urgency = "normal"
            urgency_color = "secondary"
            urgency_text = deadline
        
        timeline_items.append(
            html.Div([
                html.Div([
                    html.Div(className=f"timeline-dot bg-{urgency_color}"),
                    html.Div(className="timeline-line")
                ], className="timeline-marker"),
                html.Div([
                    html.Div([
                        dbc.Badge(urgency_text, color=urgency_color, className="me-2"),
                        html.Strong(job_title)
                    ], className="mb-1"),
                    html.P([
                        html.I(className="fas fa-building me-1"),
                        company,
                        html.Span(" • ", className="mx-2"),
                        html.I(className="fas fa-calendar me-1"),
                        deadline
                    ], className="text-muted small mb-0")
                ], className="timeline-content")
            ], className="timeline-item mb-3")
        )
    
    if not timeline_items:
        timeline_items = [
            html.Div([
                html.I(className="fas fa-calendar-check fa-2x text-muted mb-2"),
                html.P("No upcoming deadlines", className="text-muted mb-0")
            ], className="text-center py-4")
        ]
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-clock me-2"),
            "Upcoming Deadlines"
        ]),
        dbc.CardBody([
            html.Div(
                timeline_items,
                className="deadline-timeline",
                style={"maxHeight": "400px", "overflowY": "auto"}
            )
        ])
    ], className="professional-card")


def create_pipeline_stats_summary(applications: List[Dict]) -> dbc.Row:
    """
    Create summary statistics for the pipeline.
    
    Args:
        applications: List of all applications
    
    Returns:
        dbc.Row with stat cards
    """
    # Calculate stats
    total = len(applications)
    interested = len([a for a in applications if a.get("status") == "interested"])
    applied = len([a for a in applications if a.get("status") == "applied"])
    interview = len([a for a in applications if a.get("status") == "interview"])
    offer = len([a for a in applications if a.get("status") == "offer"])
    rejected = len([a for a in applications if a.get("status") == "rejected"])
    
    # Calculate success rate
    success_rate = (offer / applied * 100) if applied > 0 else 0
    interview_rate = (interview / applied * 100) if applied > 0 else 0
    
    stats = [
        {"label": "Total Applications", "value": total, "icon": "fas fa-paper-plane", "color": "primary"},
        {"label": "Active Interviews", "value": interview, "icon": "fas fa-calendar-alt", "color": "warning"},
        {"label": "Offers Received", "value": offer, "icon": "fas fa-trophy", "color": "success"},
        {"label": "Success Rate", "value": f"{success_rate:.1f}%", "icon": "fas fa-chart-line", "color": "info"}
    ]
    
    cards = []
    for stat in stats:
        cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className=f"{stat['icon']} fa-2x text-{stat['color']} mb-2"),
                            html.H3(str(stat['value']), className="mb-0"),
                            html.P(stat['label'], className="text-muted small mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm")
            ], width=6, md=3, className="mb-3")
        )
    
    return dbc.Row(cards)
