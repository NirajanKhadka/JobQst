# Enhanced Job Cards Component - Implementation Template

"""
Enhanced job cards with prominent keyword display for desktop users.
This is the hero feature of the dashboard enhancement.
"""

import dash_bootstrap_components as dbc
from dash import html
from typing import List, Dict, Any
from ..status_dropdown import create_status_dropdown


def create_enhanced_job_card(job_data: Dict[str, Any]) -> dbc.Card:
    """
    Create large desktop-optimized job card with prominent keyword display.

    Args:
        job_data: Dictionary containing job information
            Required keys: title, company, location
            Optional keys: salary, keywords, match_score, application_status, posted_date

    Returns:
        dbc.Card: Enhanced job card component
    """

    # Extract job information with defaults
    title = job_data.get("title", "No Title")
    company = job_data.get("company", "Unknown Company")
    location = job_data.get("location", "Location TBD")
    salary = job_data.get("salary", "Salary not listed")
    keywords = job_data.get("keywords", [])
    match_score = job_data.get("match_score", 0)
    application_status = job_data.get("application_status", "not_applied")
    posted_date = job_data.get("posted_date", "")
    job_id = job_data.get("id", "")

    # Create keyword badges
    keyword_badges = []
    if keywords:
        keyword_badges = [
            dbc.Badge(
                keyword.strip(),
                color="primary",
                className="me-2 mb-1 keyword-badge",
                style={"fontSize": "0.85rem", "padding": "0.4rem 0.8rem"},
            )
            for keyword in keywords[:8]  # Limit to 8 keywords for card space
        ]

    # Determine match score color
    if match_score >= 80:
        match_color = "success"
    elif match_score >= 60:
        match_color = "warning"
    else:
        match_color = "danger"

    # Application status indicator
    status_indicators = {
        "not_applied": ("Apply", "primary", "🎯"),
        "applied": ("Applied", "success", "✅"),
        "interview": ("Interview", "info", "📞"),
        "offer": ("Offer", "warning", "🎉"),
        "rejected": ("Rejected", "danger", "❌"),
        "withdrawn": ("Withdrawn", "secondary", "🚫"),
    }

    status_text, status_color, status_icon = status_indicators.get(
        application_status, ("Apply", "primary", "🎯")
    )

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H4(
                                        title,
                                        className="mb-1 job-title",
                                        style={"fontSize": "1.4rem", "fontWeight": "600"},
                                    ),
                                    html.P(
                                        [
                                            html.Strong(company, className="company-name"),
                                            html.Span(
                                                f" • {salary} • {location}", className="text-muted"
                                            ),
                                        ],
                                        className="mb-0",
                                        style={"fontSize": "1rem"},
                                    ),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                status_icon,
                                                style={
                                                    "fontSize": "1.2rem",
                                                    "marginRight": "0.5rem",
                                                },
                                            ),
                                            dbc.Badge(
                                                f"Match: {match_score}%",
                                                color=match_color,
                                                style={
                                                    "fontSize": "0.9rem",
                                                    "padding": "0.5rem 1rem",
                                                },
                                            ),
                                        ],
                                        className="text-end",
                                    )
                                ],
                                width=4,
                            ),
                        ]
                    )
                ],
                style={"backgroundColor": "#f8f9fa", "borderBottom": "1px solid #dee2e6"},
            ),
            dbc.CardBody(
                [
                    # Keywords section (prominent display)
                    (
                        html.Div(
                            [
                                html.H6(
                                    "Key Skills:",
                                    className="mb-2 text-muted",
                                    style={"fontSize": "0.9rem"},
                                ),
                                html.Div(
                                    (
                                        keyword_badges
                                        if keyword_badges
                                        else [
                                            html.Span(
                                                "No keywords available",
                                                className="text-muted fst-italic",
                                            )
                                        ]
                                    ),
                                    className="keywords-container mb-3",
                                ),
                            ]
                        )
                        if keywords
                        else html.Div()
                    ),
                    # RCIP and Location Tags section
                    html.Div(
                        [
                            (
                                dbc.Badge(
                                    [html.I(className="fas fa-maple-leaf me-1"), "RCIP City"],
                                    color="success",
                                    outline=True,
                                    className="me-2 mb-2",
                                    style={"fontSize": "0.8rem"},
                                )
                                if job_data.get("is_rcip_city")
                                else None
                            ),
                            (
                                dbc.Badge(
                                    [html.I(className="fas fa-star me-1"), "Immigration Priority"],
                                    color="warning",
                                    outline=True,
                                    className="me-2 mb-2",
                                    style={"fontSize": "0.8rem"},
                                )
                                if job_data.get("is_immigration_priority")
                                else None
                            ),
                            # Additional city tags
                            (
                                html.Div(
                                    [
                                        dbc.Badge(
                                            tag.replace("_", " ").title(),
                                            color="info",
                                            outline=True,
                                            className="me-1 mb-1",
                                            style={"fontSize": "0.7rem"},
                                        )
                                        for tag in str(job_data.get("city_tags", "")).split(",")
                                        if tag.strip() and tag.strip() not in ["rcip", ""]
                                    ]
                                )
                                if job_data.get("city_tags")
                                else None
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Job details preview
                    html.Div(
                        [
                            html.P(
                                (
                                    job_data.get("description", "")[:200] + "..."
                                    if len(job_data.get("description", "")) > 200
                                    else job_data.get("description", "No description available")
                                ),
                                className="job-description text-muted",
                                style={"fontSize": "0.95rem", "lineHeight": "1.4"},
                            )
                        ],
                        className="mb-3",
                    ),
                    # Action buttons and metadata
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Small(
                                        [
                                            html.Span("Posted: ", className="text-muted"),
                                            html.Span(
                                                posted_date or "Recently", className="fw-medium"
                                            ),
                                        ]
                                    )
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.ButtonGroup(
                                        [
                                            # Replace static status button with interactive dropdown
                                            create_status_dropdown(job_id, application_status),
                                            dbc.Button(
                                                "💾",
                                                id=f"bookmark-btn-{job_id}",
                                                color="outline-secondary",
                                                size="sm",
                                                title="Bookmark for later",
                                            ),
                                            dbc.Button(
                                                "🔗",
                                                id=f"link-btn-{job_id}",
                                                color="outline-info",
                                                size="sm",
                                                title="Open job posting",
                                            ),
                                            dbc.Button(
                                                "❌",
                                                id=f"hide-btn-{job_id}",
                                                color="outline-danger",
                                                size="sm",
                                                title="Not interested",
                                            ),
                                        ],
                                        className="d-flex",
                                    )
                                ],
                                width=6,
                                className="text-end",
                            ),
                        ],
                        align="center",
                    ),
                ],
                style={"padding": "1.5rem"},
            ),
        ],
        className="mb-4 job-card-enhanced shadow-sm",
        id=f"job-card-{job_id}",
        style={
            "border": "1px solid #e3e6ea",
            "borderRadius": "8px",
            "transition": "all 0.3s ease",
            "cursor": "pointer",
        },
    )


def create_job_cards_container(jobs_list: List[Dict[str, Any]]) -> html.Div:
    """
    Create container with multiple enhanced job cards.

    Args:
        jobs_list: List of job dictionaries

    Returns:
        html.Div: Container with job cards
    """

    if not jobs_list:
        return html.Div(
            [
                dbc.Alert(
                    [
                        html.H4("No jobs found", className="alert-heading"),
                        html.P(
                            "Try adjusting your search criteria or running JobSpy to discover new opportunities."
                        ),
                        dbc.Button("Run JobSpy", color="primary", className="mt-2"),
                    ],
                    color="info",
                    className="text-center",
                )
            ]
        )

    job_cards = [create_enhanced_job_card(job) for job in jobs_list]

    return html.Div(
        [
            html.Div(
                [
                    html.H5(f"Found {len(jobs_list)} jobs", className="mb-3"),
                    html.Div(job_cards, id="job-cards-container"),
                ]
            )
        ]
    )


# CSS styles to include in assets/enhanced_job_cards.css
ENHANCED_JOB_CARDS_CSS = """
.job-card-enhanced:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.15) !important;
    transform: translateY(-2px);
    border-color: #007bff !important;
}

.job-title {
    color: #2c3e50;
}

.company-name {
    color: #007bff;
}

.keyword-badge {
    background: linear-gradient(45deg, #007bff, #0056b3);
    border: none;
    font-weight: 500;
}

.keyword-badge:hover {
    background: linear-gradient(45deg, #0056b3, #004085);
    transform: scale(1.05);
}

.keywords-container {
    max-height: 100px;
    overflow-y: auto;
}

.job-description {
    border-left: 3px solid #e9ecef;
    padding-left: 1rem;
}

/* Desktop-optimized spacing */
@media (min-width: 1200px) {
    .job-card-enhanced {
        min-height: 250px;
    }
    
    .job-title {
        font-size: 1.5rem !important;
    }
    
    .keyword-badge {
        font-size: 0.9rem !important;
        padding: 0.5rem 1rem !important;
    }
}
"""
