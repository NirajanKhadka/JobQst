"""
Job modal component for detailed job view and actions
"""

import dash_bootstrap_components as dbc
from dash import html, dcc


def create_job_modal():
    """Create a modal for viewing job details and taking actions"""
    return dbc.Modal(
        [
            dbc.ModalHeader([dbc.ModalTitle("Job Details", id="job-modal-title")]),
            dbc.ModalBody(
                [
                    # Job header with key info
                    html.Div(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H4(id="job-modal-title-header", className="mb-1"),
                                            html.P(
                                                [
                                                    html.Strong(id="job-modal-company-header"),
                                                    " • ",
                                                    html.Span(
                                                        id="job-modal-location-header",
                                                        className="text-muted",
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                            html.Div(
                                                id="job-modal-badges-container", className="mb-3"
                                            ),
                                        ],
                                        width=8,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.H5(
                                                        id="job-modal-salary-display",
                                                        className="text-success mb-2",
                                                    ),
                                                    html.P(
                                                        [
                                                            html.Strong("Match Score: "),
                                                            html.Span(
                                                                id="job-modal-match-display",
                                                                className="badge bg-primary",
                                                            ),
                                                        ],
                                                        className="mb-1",
                                                    ),
                                                    html.P(
                                                        [
                                                            html.Strong("Posted: "),
                                                            html.Span(
                                                                id="job-modal-posted-display",
                                                                className="text-muted",
                                                            ),
                                                        ],
                                                        className="mb-1",
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=4,
                                    ),
                                ]
                            )
                        ],
                        className="border-bottom pb-3 mb-4",
                    ),
                    # Detailed information sections for large monitors
                    dbc.Row(
                        [
                            # Left column - Job details
                            dbc.Col(
                                [
                                    # Job description
                                    html.H6("📄 Job Description", className="fw-bold mb-2"),
                                    html.Div(
                                        id="job-modal-description",
                                        className="bg-light p-3 rounded mb-4",
                                        style={
                                            "max-height": "300px",
                                            "overflow-y": "auto",
                                            "font-size": "14px",
                                            "line-height": "1.5",
                                        },
                                    ),
                                    # Required skills
                                    html.H6("🛠️ Required Skills", className="fw-bold mb-2"),
                                    html.Div(id="job-modal-skills-container", className="mb-4"),
                                    # Company information
                                    html.H6("🏢 Company Details", className="fw-bold mb-2"),
                                    html.Div(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Strong("Company:"),
                                                            html.P(
                                                                id="job-modal-company-details",
                                                                className="text-muted mb-2",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Strong("Industry:"),
                                                            html.P(
                                                                id="job-modal-industry-text",
                                                                className="text-muted mb-2",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ]
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Strong("Company Size:"),
                                                            html.P(
                                                                id="job-modal-company-size-text",
                                                                className="text-muted mb-2",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Strong("Website:"),
                                                            html.A(
                                                                id="job-modal-company-website",
                                                                href="#",
                                                                target="_blank",
                                                                className="text-decoration-none",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className="bg-light p-3 rounded mb-4",
                                    ),
                                ],
                                width=8,
                            ),
                            # Right column - Application tracking and actions
                            dbc.Col(
                                [
                                    # Quality indicators
                                    html.H6("🎯 Quality Indicators", className="fw-bold mb-2"),
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Strong("Confidence Score:"),
                                                    html.Span(
                                                        id="job-modal-confidence-badge",
                                                        className="ms-2",
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong("Validation Method:"),
                                                    html.Span(
                                                        id="job-modal-validation-badge",
                                                        className="ms-2",
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong("Semantic Score:"),
                                                    html.Span(
                                                        id="job-modal-semantic-display",
                                                        className="ms-2 badge bg-info",
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                        ],
                                        className="bg-light p-3 rounded mb-4",
                                    ),
                                    # User feedback section
                                    html.H6("👍 Your Feedback", className="fw-bold mb-2"),
                                    html.Div(
                                        [
                                            html.P(
                                                "How relevant is this job to you?",
                                                className="small text-muted mb-2",
                                            ),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        "👍",
                                                        color="success",
                                                        size="sm",
                                                        id="job-modal-thumbs-up",
                                                    ),
                                                    dbc.Button(
                                                        "👎",
                                                        color="danger",
                                                        size="sm",
                                                        id="job-modal-thumbs-down",
                                                    ),
                                                    dbc.Button(
                                                        "⭐",
                                                        color="warning",
                                                        size="sm",
                                                        id="job-modal-bookmark",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            html.Div(
                                                [
                                                    html.Strong("Interest Level:"),
                                                    dcc.Slider(
                                                        id="job-modal-interest-slider",
                                                        min=1,
                                                        max=5,
                                                        step=1,
                                                        value=3,
                                                        marks={i: str(i) for i in range(1, 6)},
                                                        tooltip={"placement": "bottom"},
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                        ],
                                        className="bg-light p-3 rounded mb-4",
                                    ),
                                    # Application tracking
                                    html.H6("📋 Application Tracking", className="fw-bold mb-2"),
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Strong("Current Status:"),
                                                    html.P(
                                                        id="job-modal-current-status",
                                                        className="text-muted mb-2",
                                                    ),
                                                ]
                                            ),
                                            dcc.Dropdown(
                                                id="job-modal-status-dropdown",
                                                options=[
                                                    {"label": "🆕 New", "value": "new"},
                                                    {
                                                        "label": "✅ Ready to Apply",
                                                        "value": "ready_to_apply",
                                                    },
                                                    {"label": "📤 Applied", "value": "applied"},
                                                    {
                                                        "label": "⚠️ Needs Review",
                                                        "value": "needs_review",
                                                    },
                                                    {"label": "❌ Rejected", "value": "rejected"},
                                                ],
                                                placeholder="Update status...",
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                "Update Status",
                                                id="job-modal-update-status-btn",
                                                color="primary",
                                                size="sm",
                                                className="w-100 mb-3",
                                            ),
                                        ],
                                        className="bg-light p-3 rounded mb-4",
                                    ),
                                    # Notes section
                                    html.H6("📝 Personal Notes", className="fw-bold mb-2"),
                                    dcc.Textarea(
                                        id="job-modal-notes",
                                        placeholder="Add notes about this position...",
                                        style={
                                            "width": "100%",
                                            "height": 100,
                                            "resize": "vertical",
                                        },
                                        className="mb-3",
                                    ),
                                ],
                                width=4,
                            ),
                        ]
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Save Notes",
                        id="job-modal-save-notes-btn",
                        color="success",
                        className="me-2",
                    ),
                    dbc.Button(
                        "Open Job URL", id="job-modal-open-url-btn", color="info", className="me-2"
                    ),
                    dbc.Button("Close", id="job-modal-close-btn", color="secondary"),
                ]
            ),
        ],
        id="job-modal",
        size="lg",
        is_open=False,
    )


def create_job_notes_storage():
    """Create a component to store job notes"""
    return dcc.Store(id="job-notes-store", data={})


def create_job_modal_store():
    """Create a component to store current job data"""
    return dcc.Store(id="job-modal-store", data={})
