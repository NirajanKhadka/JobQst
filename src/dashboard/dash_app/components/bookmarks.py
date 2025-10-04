"""Bookmarks Component

Smart bookmarking system for JobQst Dashboard allowing users to save
and manage promising job opportunities with one-click actions.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import List, Dict, Any

from .job_cards import create_job_card


def create_bookmarks_header() -> dbc.Card:
    """Create header for bookmarks section with quick stats."""
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H3(
                                        [
                                            html.I(className="fas fa-bookmark me-2 text-warning"),
                                            "Saved Jobs",
                                        ],
                                        className="mb-2",
                                    ),
                                    html.P(
                                        "Your curated list of promising opportunities",
                                        className="text-muted mb-0",
                                    ),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [html.I(className="fas fa-trash-alt me-2"), "Clear All"],
                                        color="outline-danger",
                                        size="sm",
                                        id="clear-all-bookmarks-btn",
                                        className="float-end",
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
    )


def create_bookmark_filters() -> dbc.Card:
    """Create filtering options specific to bookmarked jobs."""
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H6(
                        [html.I(className="fas fa-filter me-2"), "Filter Saved Jobs"],
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
                                    html.Label("Sort by:", className="form-label small"),
                                    dcc.Dropdown(
                                        id="bookmark-sort-dropdown",
                                        options=[
                                            {
                                                "label": "📅 Date Saved (newest)",
                                                "value": "date_saved_desc",
                                            },
                                            {
                                                "label": "📅 Date Saved (oldest)",
                                                "value": "date_saved_asc",
                                            },
                                            {
                                                "label": "⭐ Match Score (highest)",
                                                "value": "match_score_desc",
                                            },
                                            {
                                                "label": "💰 Salary (highest)",
                                                "value": "salary_desc",
                                            },
                                            {"label": "🏢 Company A-Z", "value": "company_asc"},
                                        ],
                                        value="date_saved_desc",
                                        clearable=False,
                                        className="mb-2",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Filter by status:", className="form-label small"),
                                    dcc.Dropdown(
                                        id="bookmark-status-filter",
                                        options=[
                                            {"label": "📋 All Status", "value": "all"},
                                            {"label": "🆕 New", "value": "new"},
                                            {
                                                "label": "✅ Ready to Apply",
                                                "value": "ready_to_apply",
                                            },
                                            {"label": "📤 Applied", "value": "applied"},
                                            {"label": "👀 Needs Review", "value": "needs_review"},
                                        ],
                                        value="all",
                                        clearable=False,
                                        className="mb-2",
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    )
                ]
            ),
        ],
        className="mb-4",
    )


def create_bookmarks_grid(bookmarked_jobs: List[Dict[str, Any]]) -> html.Div:
    """Create grid layout for bookmarked jobs.

    Args:
        bookmarked_jobs: List of job dictionaries with bookmark data

    Returns:
        html.Div containing the bookmarks grid
    """
    if not bookmarked_jobs:
        return dbc.Alert(
            [
                html.Div(
                    [
                        html.I(className="fas fa-bookmark fa-3x text-muted mb-3"),
                        html.H5("No Saved Jobs Yet", className="text-muted"),
                        html.P(
                            [
                                "Start building your shortlist by clicking the ",
                                html.I(className="far fa-bookmark text-warning"),
                                " Save button on jobs that interest you.",
                            ],
                            className="text-muted",
                        ),
                    ],
                    className="text-center py-4",
                )
            ],
            color="light",
            className="border-0",
        )

    # Create job cards for bookmarked jobs
    cards = []
    for job in bookmarked_jobs:
        # Ensure the job shows as bookmarked
        job["is_bookmarked"] = True
        cards.append(dbc.Col(create_job_card(job), width=12, md=6, lg=4, xl=3, className="mb-3"))

    return html.Div(
        [
            dbc.Row(cards, className="g-3"),
            html.Hr(className="my-4"),
            html.Div(
                [
                    html.P(
                        [
                            html.Strong(f"{len(bookmarked_jobs)} saved jobs"),
                            " • Last updated: ",
                            html.Span(id="bookmarks-last-updated", className="text-muted"),
                        ],
                        className="text-center text-muted small mb-0",
                    )
                ]
            ),
        ]
    )


def create_bookmarks_layout() -> html.Div:
    """Create the complete bookmarks layout.

    Returns:
        html.Div containing the full bookmarks interface
    """
    return html.Div(
        [
            create_bookmarks_header(),
            create_bookmark_filters(),
            html.Div(
                id="bookmarks-grid-container",
                children=[
                    # Placeholder - will be populated by callback
                    create_bookmarks_grid([])
                ],
            ),
            # Hidden stores for bookmark data
            dcc.Store(id="bookmarks-store", data=[]),
            dcc.Store(id="bookmark-actions-store", data={}),
        ]
    )


def create_bookmark_status_badge(date_saved: str) -> dbc.Badge:
    """Create a badge showing when the job was bookmarked.

    Args:
        date_saved: ISO format date string when job was bookmarked

    Returns:
        dbc.Badge with relative time display
    """
    # This would typically calculate relative time
    # For now, just show "Saved" with date
    return dbc.Badge(
        [html.I(className="fas fa-clock me-1"), f"Saved {date_saved[:10]}"],  # Just show date part
        color="info",
        className="small",
    )
