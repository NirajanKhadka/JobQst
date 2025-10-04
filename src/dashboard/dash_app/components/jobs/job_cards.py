"""
Job cards component for JobQst Dashboard
Card-based view for job listings with visual job ranking system
"""

import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from src.dashboard.analytics import compute_company_stats, compute_job_metrics


def create_rcip_badge(job):
    """Create RCIP badge if job is in an RCIP city."""
    if job.get("is_rcip_city") or job.get("rcip_eligible"):
        return dbc.Badge(
            [html.I(className="fas fa-maple-leaf me-1"), "🍁 RCIP City"],
            color="success",
            className="me-2 mb-2 fw-bold",
            style={"fontSize": "0.75rem"},
            title="Regional and Community Immigration Program city",
        )
    return None


def get_job_rank_color(match_score: float) -> tuple[str, str]:
    """
    Get color for job ranking based on match score.
    Returns (color_name, hex_color) tuple for high-fit job identification.

    Args:
        match_score: Job match score (0-100)

    Returns:
        Tuple of (color_name, hex_color)
    """
    if match_score >= 80:
        return ("success", "#28a745")  # Green - High fit
    elif match_score >= 60:
        return ("warning", "#ffc107")  # Yellow - Medium fit
    else:
        return ("secondary", "#6c757d")  # Gray - Lower fit


def create_job_ranking_bar(match_score: float) -> html.Div:
    """
    Create visual ranking bar component for immediate job fit recognition.

    Args:
        match_score: Job match score (0-100)

    Returns:
        Dash HTML component with color-coded ranking bar
    """
    color_name, hex_color = get_job_rank_color(match_score)

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        className="progress-bar",
                        style={
                            "width": f"{match_score}%",
                            "backgroundColor": hex_color,
                            "transition": "width 0.3s ease-in-out",
                        },
                    )
                ],
                className="progress mb-2",
                style={"height": "8px"},
            ),
            html.Small(f"Job Fit: {match_score:.0f}%", className=f"text-{color_name} fw-bold"),
        ],
        className="mb-2",
    )


def create_job_actions(job):
    """Create action buttons for a job card with bookmark functionality"""
    job_url = job.get("job_url")
    job_id = job.get("id", 0)
    is_bookmarked = job.get("is_bookmarked", False)
    has_valid_url = job_url and job_url != "#" and job_url != "None"

    # Create Apply button with job URL if available
    if has_valid_url:
        apply_button = html.A(
            dbc.Button(
                [html.I(className="fas fa-external-link-alt me-1"), "Apply"],
                size="sm",
                color="primary",
            ),
            href=job_url,
            target="_blank",
            style={"textDecoration": "none"},
        )
    else:
        apply_button = dbc.Button(
            [html.I(className="fas fa-paper-plane me-1"), "Apply"],
            size="sm",
            color="secondary",
            disabled=True,
        )

    # Bookmark button with dynamic styling and callback support
    bookmark_icon = "❤️" if is_bookmarked else "🤍"
    bookmark_color = "primary" if is_bookmarked else "outline-primary"

    bookmark_button = dbc.Button(
        bookmark_icon,
        size="sm",
        color=bookmark_color,
        id={"type": "bookmark-btn", "job_id": str(job_id)},
        title="Toggle bookmark",
        className="bookmark-btn",
    )

    return dbc.ButtonGroup(
        [
            dbc.Button(
                [html.I(className="fas fa-eye me-1"), "View"],
                size="sm",
                color="outline-primary",
                id=f"view-job-{job_id}",
            ),
            bookmark_button,
            apply_button,
            dbc.Button(
                [html.I(className="fas fa-edit me-1"), "Notes"],
                size="sm",
                color="outline-secondary",
                id=f"notes-job-{job_id}",
            ),
        ],
        size="sm",
        className="w-100",
    )


def create_job_card(job):
    """Create enhanced job card component with visual ranking system"""
    status_color = {
        "new": "primary",
        "ready_to_apply": "success",
        "applied": "warning",
        "needs_review": "info",
    }.get(job.get("status", "new"), "secondary")

    status_icon = {
        "new": "fas fa-plus-circle",
        "ready_to_apply": "fas fa-check-circle",
        "applied": "fas fa-paper-plane",
        "needs_review": "fas fa-eye",
    }.get(job.get("status", "new"), "fas fa-circle")

    # Get match score for ranking
    match_score = job.get("match_score", 0)

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    # Header with company and title (enhanced typography)
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H6(
                                        job.get("company", "Unknown Company"),
                                        className="text-primary mb-1 fw-bold",
                                        style={"fontSize": "0.95rem"},
                                    ),
                                    html.H5(
                                        job.get("title", "Unknown Position"),
                                        className="mb-2 fw-semibold",
                                        style={"fontSize": "1.1rem", "lineHeight": "1.3"},
                                    ),
                                ],
                                width=12,
                            )
                        ]
                    ),
                    # Visual Job Ranking Bar (NEW FEATURE)
                    create_job_ranking_bar(match_score),
                    # Location and status (enhanced layout)
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.P(
                                        [
                                            html.I(
                                                className="fas fa-map-marker-alt me-2 "
                                                "text-primary"
                                            ),
                                            job.get("location", "Location not specified"),
                                        ],
                                        className="mb-2 text-muted",
                                        style={"fontSize": "0.9rem"},
                                    )
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Badge(
                                        [
                                            html.I(className=f"{status_icon} me-1"),
                                            job.get("status", "new").replace("_", " ").title(),
                                        ],
                                        color=status_color,
                                        className="mb-2 w-100 text-center",
                                        style={"fontSize": "0.75rem"},
                                    )
                                ],
                                width=4,
                            ),
                        ]
                    ),
                    # RCIP and Immigration Priority Tags
                    html.Div(
                        [
                            # Use the helper function for RCIP badge
                            create_rcip_badge(job),
                            # Immigration Priority badge
                            (
                                dbc.Badge(
                                    [
                                        html.I(className="fas fa-flag-checkered me-1"),
                                        "Immigration Priority",
                                    ],
                                    color="warning",
                                    className="me-2 mb-2",
                                    style={"fontSize": "0.7rem"},
                                )
                                if job.get("is_immigration_priority")
                                else None
                            ),
                            # Additional city tags if available
                            (
                                html.Div(
                                    [
                                        dbc.Badge(
                                            tag.replace("_", " ").title(),
                                            color="info",
                                            outline=True,
                                            className="me-1 mb-1",
                                            style={"fontSize": "0.65rem"},
                                        )
                                        for tag in str(job.get("city_tags", "")).split(",")
                                        if tag.strip() and tag.strip() not in ["rcip", ""]
                                    ]
                                )
                                if job.get("city_tags")
                                else None
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Description preview (enhanced with better typography)
                    html.Div(
                        [
                            (
                                html.P(
                                    job.get("description", "")[:120]
                                    + ("..." if len(job.get("description", "")) > 120 else ""),
                                    className="text-muted mb-3",
                                    style={
                                        "fontSize": "0.85rem",
                                        "lineHeight": "1.4",
                                        "overflow": "hidden",
                                        "display": "-webkit-box",
                                        "WebkitLineClamp": "2",
                                        "WebkitBoxOrient": "vertical",
                                    },
                                )
                                if job.get("description")
                                else html.P(
                                    "No description available",
                                    className="text-muted fst-italic mb-3",
                                    style={"fontSize": "0.85rem"},
                                )
                            )
                        ]
                    ),
                    # Actions
                    create_job_actions(job),
                ]
            )
        ],
        className="mb-3 h-100 job-card border-0 shadow-sm",
        style={
            "borderLeft": f"4px solid {get_job_rank_color(match_score)[1]}",
            "transition": ("transform 0.2s ease-in-out, " "box-shadow 0.2s ease-in-out"),
        },
    )


def create_jobs_grid(jobs_data, max_cards=12):
    """Create a grid of job cards"""
    if not jobs_data:
        return dbc.Alert(
            [
                html.I(className="fas fa-info-circle me-2"),
                "No jobs found. Try adjusting your filters or run a new search.",
            ],
            color="info",
            className="text-center",
        )

    cards = []
    for job in jobs_data[:max_cards]:
        cards.append(dbc.Col(create_job_card(job), width=12, md=6, lg=4, xl=3, className="mb-3"))

    # Add "show more" card if there are more jobs
    if len(jobs_data) > max_cards:
        cards.append(
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-plus fs-1 " + "text-primary mb-3"
                                            ),
                                            html.H5(
                                                f"+{len(jobs_data) - max_cards} " + "more jobs"
                                            ),
                                            html.P(
                                                "Adjust filters or load more results",
                                                className="text-muted",
                                            ),
                                            dbc.Button(
                                                "Load More",
                                                color="primary",
                                                size="sm",
                                                id="load-more-jobs-btn",
                                            ),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        className="mb-3 shadow-sm border-0 h-100 "
                        + "d-flex align-items-center justify-content-center",
                    )
                ],
                width=12,
                md=6,
                lg=4,
                xl=3,
                className="mb-3",
            )
        )

    return dbc.Row(cards, className="jobs-grid")


def create_card_view_controls():
    """Create controls for card view"""
    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-th me-1"), "Grid 4"],
                                size="sm",
                                color="outline-primary",
                                active=True,
                                id="grid-4-btn",
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-th-large me-1"), "Grid 3"],
                                size="sm",
                                color="outline-primary",
                                id="grid-3-btn",
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-list me-1"), "List"],
                                size="sm",
                                color="outline-primary",
                                id="list-view-btn",
                            ),
                        ]
                    )
                ],
                width=6,
            ),
            dbc.Col(
                [
                    dbc.InputGroup(
                        [
                            dbc.Input(
                                placeholder="Cards per page...",
                                type="number",
                                value=12,
                                min=6,
                                max=50,
                                step=6,
                                id="cards-per-page-input",
                                size="sm",
                            ),
                            dbc.Button(
                                "Apply",
                                color="outline-secondary",
                                size="sm",
                                id="apply-cards-per-page-btn",
                            ),
                        ],
                        size="sm",
                    )
                ],
                width=6,
                className="text-end",
            ),
        ],
        className="mb-3",
    )


def create_job_quick_stats(jobs_data):
    """Create quick stats for jobs"""
    if not jobs_data:
        return html.Div()

    df = pd.DataFrame(jobs_data)

    # Use shared aggregation helpers
    job_metrics = compute_job_metrics(df)
    company_stats = compute_company_stats(df, top_n=1)

    # Calculate stats
    total_jobs = job_metrics.total_jobs
    avg_score = job_metrics.avg_match_score
    top_company = company_stats.companies[0] if company_stats.companies else "N/A"
    status_counts = job_metrics.status_counts

    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(f"{total_jobs:,}", className="text-primary mb-0"),
                                    html.Small("Total Jobs", className="text-muted"),
                                ]
                            )
                        ],
                        className="text-center shadow-sm border-0",
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
                                    html.H4(f"{avg_score:.1f}%", className="text-success mb-0"),
                                    html.Small("Avg Match", className="text-muted"),
                                ]
                            )
                        ],
                        className="text-center shadow-sm border-0",
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
                                    html.H4(top_company, className="text-info mb-0"),
                                    html.Small("Top Company", className="text-muted"),
                                ]
                            )
                        ],
                        className="text-center shadow-sm border-0",
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
                                        f"{status_counts.get('ready_to_apply', 0):,}",
                                        className="text-warning mb-0",
                                    ),
                                    html.Small("Ready to Apply", className="text-muted"),
                                ]
                            )
                        ],
                        className="text-center shadow-sm border-0",
                    )
                ],
                width=3,
            ),
        ],
        className="mb-4",
    )
