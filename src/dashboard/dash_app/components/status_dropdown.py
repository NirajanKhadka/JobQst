"""
Application Status Dropdown Component
Interactive status tracking for job applications
"""

import dash_bootstrap_components as dbc
from dash import html
from typing import Dict, Any


def create_status_dropdown(job_id: str, current_status: str = "not_applied") -> dbc.DropdownMenu:
    """
    Create interactive status dropdown for job applications.

    Args:
        job_id: Unique identifier for the job
        current_status: Current application status

    Returns:
        dbc.DropdownMenu: Interactive status dropdown
    """

    # Status options with icons and colors
    status_options = {
        "not_applied": {"label": "🎯 Not Applied", "color": "secondary"},
        "interested": {"label": "💡 Interested", "color": "info"},
        "applied": {"label": "📤 Applied", "color": "success"},
        "interview": {"label": "📞 Interview", "color": "warning"},
        "offer": {"label": "🎉 Offer", "color": "danger"},
        "rejected": {"label": "❌ Rejected", "color": "dark"},
        "withdrawn": {"label": "🚫 Withdrawn", "color": "secondary"},
    }

    # Get current status info
    current_info = status_options.get(current_status, status_options["not_applied"])

    # Create dropdown items
    dropdown_items = []
    for status_key, status_info in status_options.items():
        is_current = status_key == current_status
        dropdown_items.append(
            dbc.DropdownMenuItem(
                [
                    status_info["label"],
                    html.Span(" ✓" if is_current else "", className="float-end"),
                ],
                id={"type": "status-option", "status": status_key, "job_id": job_id},
                active=is_current,
                className="status-option",
            )
        )

    return dbc.DropdownMenu(
        dropdown_items,
        label=current_info["label"],
        color=current_info["color"],
        size="sm",
        id={"type": "status-dropdown", "index": job_id},
        className="status-dropdown",
        style={"minWidth": "120px"},
    )


def create_status_filter_dropdown() -> dbc.Select:
    """
    Create status filter dropdown for the jobs filter section.

    Returns:
        dbc.Select: Status filter dropdown
    """

    return dbc.Select(
        id="jobs-status-filter",
        options=[
            {"label": "📊 All Applications", "value": "all"},
            {"label": "🎯 Not Applied", "value": "not_applied"},
            {"label": "💡 Interested", "value": "interested"},
            {"label": "📤 Applied", "value": "applied"},
            {"label": "📞 Interview", "value": "interview"},
            {"label": "🎉 Offer", "value": "offer"},
            {"label": "❌ Rejected", "value": "rejected"},
            {"label": "🚫 Withdrawn", "value": "withdrawn"},
        ],
        value="all",
        size="sm",
    )


def create_application_tracking_card(job_data: Dict[str, Any]) -> dbc.Card:
    """
    Create dedicated application tracking card with status timeline.

    Args:
        job_data: Job information including status history

    Returns:
        dbc.Card: Application tracking card
    """

    job_id = job_data.get("id", "")
    title = job_data.get("title", "No Title")
    company = job_data.get("company", "Unknown Company")
    current_status = job_data.get("application_status", "not_applied")
    status_history = job_data.get("status_history", [])

    # Status timeline
    timeline_items = []
    if status_history:
        for entry in status_history[-3:]:  # Show last 3 status changes
            timeline_items.append(
                html.Li(
                    [
                        html.Strong(entry.get("status", "").replace("_", " ").title()),
                        html.Small(f" - {entry.get('date', '')}", className="text-muted ms-2"),
                    ],
                    className="timeline-item",
                )
            )

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H6(title, className="mb-0"),
                                    html.Small(company, className="text-muted"),
                                ],
                                width=8,
                            ),
                            dbc.Col([create_status_dropdown(job_id, current_status)], width=4),
                        ]
                    )
                ]
            ),
            dbc.CardBody(
                [
                    # Status timeline
                    (
                        html.Div(
                            [
                                html.H6("Recent Activity:", className="mb-2 text-muted"),
                                html.Ul(
                                    (
                                        timeline_items
                                        if timeline_items
                                        else [
                                            html.Li(
                                                "No activity yet", className="text-muted fst-italic"
                                            )
                                        ]
                                    ),
                                    className="timeline-list list-unstyled",
                                ),
                            ]
                        )
                        if status_history
                        else html.Div()
                    ),
                    # Quick actions
                    dbc.ButtonGroup(
                        [
                            dbc.Button("📝 Add Note", size="sm", color="outline-secondary"),
                            dbc.Button("📎 Attach File", size="sm", color="outline-info"),
                            dbc.Button("🔗 Open Job", size="sm", color="outline-primary"),
                        ],
                        size="sm",
                        className="mt-2",
                    ),
                ]
            ),
        ],
        className="mb-3 application-card",
    )


# CSS styles for status components
STATUS_DROPDOWN_CSS = """
.status-dropdown .dropdown-toggle {
    border: 1px solid #dee2e6;
    font-weight: 500;
}

.status-dropdown .dropdown-toggle:focus {
    box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
}

.status-option:hover {
    background-color: #f8f9fa !important;
}

.application-card {
    border-left: 4px solid #007bff;
    transition: all 0.3s ease;
}

.application-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    transform: translateY(-1px);
}

.timeline-list {
    border-left: 2px solid #e9ecef;
    padding-left: 1rem;
}

.timeline-item {
    position: relative;
    padding: 0.5rem 0;
}

.timeline-item::before {
    content: '•';
    position: absolute;
    left: -1.4rem;
    color: #007bff;
    font-weight: bold;
    background: white;
    width: 1rem;
    text-align: center;
}
"""
