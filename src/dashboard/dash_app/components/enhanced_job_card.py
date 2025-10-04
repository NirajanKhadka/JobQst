"""
Enhanced Job Card Component
Professional job cards with match score indicators, badges, and hover effects
"""

import dash_bootstrap_components as dbc
from dash import html
from typing import Dict, Optional
import pandas as pd


def get_match_score_color(score: float) -> str:
    """
    Get color class based on match score.
    
    Args:
        score: Match score (0-100)
    
    Returns:
        Color class name
    """
    if score >= 80:
        return "success"
    elif score >= 60:
        return "warning"
    elif score >= 40:
        return "info"
    else:
        return "secondary"


def get_match_score_border_color(score: float) -> str:
    """
    Get border color for match score indicator (top border).
    
    Args:
        score: Match score (0-100)
    
    Returns:
        CSS color value
    """
    if score >= 80:
        return "#28a745"  # success green
    elif score >= 60:
        return "#ffc107"  # warning yellow
    elif score >= 40:
        return "#17a2b8"  # info blue
    else:
        return "#6c757d"  # secondary gray


def create_enhanced_job_card(job: Dict, view_mode: str = "card") -> dbc.Card:
    """
    Create enhanced job card with professional styling and match score indicator.
    
    Args:
        job: Job dictionary with all fields
        view_mode: Display mode ('card', 'compact', 'detailed')
    
    Returns:
        dbc.Card component
    """
    # Extract job fields
    job_id = job.get("id", "")
    title = job.get("title", "No Title")
    company = job.get("company", "Unknown Company")
    location = job.get("location", "Unknown Location")
    fit_score = job.get("fit_score", 0)
    salary_range = job.get("salary_range", "")
    date_posted = job.get("date_posted", "")
    is_rcip = job.get("is_rcip_city", False)
    is_immigration_priority = job.get("is_immigration_priority", False)
    url = job.get("url", "#")
    summary = job.get("summary", "")
    
    # Handle NaN fit scores
    if pd.isna(fit_score):
        fit_score = 0
    
    # Get match score styling
    match_color = get_match_score_color(fit_score)
    border_color = get_match_score_border_color(fit_score)
    
    # Create match score badge
    if fit_score > 0:
        match_badge = dbc.Badge(
            f"{fit_score:.0f}% Match",
            color=match_color,
            className="me-2"
        )
    else:
        match_badge = dbc.Badge(
            "Not Rated",
            color="secondary",
            className="me-2"
        )
    
    # Create RCIP badges
    badges = []
    if is_rcip:
        badges.append(
            dbc.Badge(
                [html.I(className="fas fa-maple-leaf me-1"), "RCIP"],
                color="success",
                className="me-1"
            )
        )
    if is_immigration_priority:
        badges.append(
            dbc.Badge(
                [html.I(className="fas fa-star me-1"), "Priority"],
                color="info",
                className="me-1"
            )
        )
    if "remote" in location.lower():
        badges.append(
            dbc.Badge(
                [html.I(className="fas fa-home me-1"), "Remote"],
                color="warning",
                className="me-1"
            )
        )
    
    # Create salary badge
    salary_badge = None
    if salary_range:
        salary_badge = dbc.Badge(
            [html.I(className="fas fa-dollar-sign me-1"), salary_range],
            color="dark",
            className="me-1"
        )
    
    # Compact view
    if view_mode == "compact":
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6(title, className="mb-1"),
                        html.Small([
                            html.I(className="fas fa-building me-1"),
                            company,
                            html.Span(" • ", className="mx-2"),
                            html.I(className="fas fa-map-marker-alt me-1"),
                            location
                        ], className="text-muted")
                    ], width=8),
                    dbc.Col([
                        match_badge,
                        *badges
                    ], width=4, className="text-end")
                ])
            ])
        ], className="mb-2 hover-lift", style={
            "borderTop": f"3px solid {border_color}",
            "cursor": "pointer"
        })
    
    # Detailed view
    if view_mode == "detailed":
        return dbc.Card([
            dbc.CardBody([
                # Header with match score indicator
                html.Div([
                    html.H5(title, className="mb-2"),
                    html.Div([
                        html.I(className="fas fa-building me-2 text-primary"),
                        html.Strong(company),
                        html.Span(" • ", className="mx-2 text-muted"),
                        html.I(className="fas fa-map-marker-alt me-2 text-success"),
                        location
                    ], className="mb-3"),
                    
                    # Match score with progress bar
                    html.Div([
                        html.Div([
                            match_badge,
                            html.Small(f"Posted {date_posted}" if date_posted else "Recently posted",
                                     className="text-muted")
                        ], className="d-flex justify-content-between align-items-center mb-2"),
                        dbc.Progress(
                            value=fit_score,
                            color=match_color,
                            style={"height": "8px"},
                            className="mb-3"
                        )
                    ]),
                    
                    # Badges row
                    html.Div([
                        *badges,
                        salary_badge
                    ] if badges or salary_badge else [], className="mb-3"),
                    
                    # Summary
                    html.P(
                        summary[:200] + "..." if len(summary) > 200 else summary,
                        className="text-muted mb-3"
                    ) if summary else html.Div(),
                    
                    # Action buttons
                    dbc.ButtonGroup([
                        dbc.Button(
                            [html.I(className="fas fa-eye me-1"), "View Details"],
                            size="sm",
                            color="primary",
                            outline=True,
                            id={"type": "view-job-detail", "index": job_id}
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-bookmark me-1"), "Save"],
                            size="sm",
                            color="warning",
                            outline=True,
                            id={"type": "save-job", "index": job_id}
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-external-link-alt me-1"), "Apply"],
                            size="sm",
                            color="success",
                            href=url,
                            target="_blank"
                        )
                    ], className="w-100")
                ])
            ])
        ], className="mb-3 professional-card hover-lift", style={
            "borderTop": f"4px solid {border_color}"
        })
    
    # Default card view
    return dbc.Card([
        dbc.CardBody([
            # Header row
            dbc.Row([
                dbc.Col([
                    html.H5(title, className="mb-1"),
                    html.Div([
                        html.I(className="fas fa-building me-2 text-primary"),
                        html.Strong(company),
                        html.Span(" • ", className="mx-2 text-muted"),
                        html.I(className="fas fa-map-marker-alt me-2 text-success"),
                        location
                    ], className="text-muted mb-2")
                ], width=9),
                dbc.Col([
                    html.Div([
                        match_badge,
                        dbc.Progress(
                            value=fit_score,
                            color=match_color,
                            style={"height": "6px"},
                            className="mt-1"
                        )
                    ], className="text-end")
                ], width=3)
            ]),
            
            # Badges and salary
            html.Div([
                *badges,
                salary_badge
            ] if badges or salary_badge else [], className="mb-2"),
            
            # Summary preview
            html.P(
                summary[:150] + "..." if len(summary) > 150 else summary,
                className="text-muted small mb-2"
            ) if summary else html.Div(),
            
            # Footer with date and actions
            html.Div([
                html.Small(
                    f"Posted {date_posted}" if date_posted else "Recently posted",
                    className="text-muted"
                ),
                dbc.ButtonGroup([
                    dbc.Button(
                        [html.I(className="fas fa-eye")],
                        size="sm",
                        color="primary",
                        outline=True,
                        id={"type": "view-job-detail", "index": job_id},
                        title="View Details"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-bookmark")],
                        size="sm",
                        color="warning",
                        outline=True,
                        id={"type": "save-job", "index": job_id},
                        title="Save Job"
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-external-link-alt")],
                        size="sm",
                        color="success",
                        href=url,
                        target="_blank",
                        title="Apply Now"
                    )
                ], size="sm")
            ], className="d-flex justify-content-between align-items-center")
        ])
    ], className="mb-3 professional-card hover-lift", style={
        "borderTop": f"4px solid {border_color}"
    })


def create_job_card_skeleton() -> dbc.Card:
    """
    Create skeleton loading card for job cards.
    
    Returns:
        dbc.Card with skeleton content
    """
    return dbc.Card([
        dbc.CardBody([
            html.Div(className="skeleton skeleton-text mb-2", style={"width": "70%", "height": "24px"}),
            html.Div(className="skeleton skeleton-text mb-3", style={"width": "50%", "height": "16px"}),
            html.Div(className="skeleton skeleton-text mb-2", style={"width": "100%", "height": "14px"}),
            html.Div(className="skeleton skeleton-text mb-2", style={"width": "90%", "height": "14px"}),
            html.Div(className="d-flex gap-2 mt-3", children=[
                html.Div(className="skeleton", style={"width": "80px", "height": "32px", "borderRadius": "4px"}),
                html.Div(className="skeleton", style={"width": "80px", "height": "32px", "borderRadius": "4px"}),
                html.Div(className="skeleton", style={"width": "80px", "height": "32px", "borderRadius": "4px"})
            ])
        ])
    ], className="mb-3", style={"borderTop": "4px solid #e0e0e0"})
