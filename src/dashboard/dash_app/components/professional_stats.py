"""
Professional stat cards component for dashboard home tab.
Displays key metrics with icons and trend indicators.
"""

from typing import Optional
import dash_bootstrap_components as dbc
from dash import html
import logging

logger = logging.getLogger(__name__)


def create_professional_stat_card(
    title: str,
    value: str,
    icon: str,
    color: str = "primary",
    trend: Optional[str] = None,
    trend_direction: Optional[str] = None
) -> dbc.Col:
    """
    Create a professional stat card with icon and optional trend indicator.
    
    Args:
        title: Stat title (e.g., "Total Jobs")
        value: Stat value (e.g., "99")
        icon: FontAwesome icon class (e.g., "fas fa-briefcase")
        color: Color variant (primary, success, warning, info, danger)
        trend: Optional trend text (e.g., "+12 today")
        trend_direction: Optional trend direction (up, down, neutral)
    
    Returns:
        dbc.Col containing the stat card
    """
    try:
        # Determine trend icon and color
        trend_icon = ""
        trend_color = "muted"
        
        if trend_direction == "up":
            trend_icon = "fas fa-arrow-up"
            trend_color = "success"
        elif trend_direction == "down":
            trend_icon = "fas fa-arrow-down"
            trend_color = "danger"
        elif trend_direction == "neutral":
            trend_icon = "fas fa-minus"
            trend_color = "muted"
        
        # Create trend element if provided
        trend_element = None
        if trend:
            trend_element = html.Div([
                html.I(className=f"{trend_icon} me-1") if trend_icon else None,
                html.Span(trend)
            ], className=f"stat-card-trend text-{trend_color}")
        
        # Create the card
        card = dbc.Card([
            dbc.CardBody([
                # Icon
                html.Div([
                    html.I(className=f"{icon} text-{color}-custom stat-card-icon")
                ]),
                
                # Value
                html.Div([
                    html.H2(value, className=f"stat-card-value text-{color}-custom mb-0")
                ]),
                
                # Title
                html.Div([
                    html.P(title, className="stat-card-title mb-0")
                ]),
                
                # Trend (if provided)
                trend_element if trend_element else html.Div()
            ])
        ], className=f"stat-card stat-card-{color} hover-lift")
        
        return dbc.Col(card, xs=12, sm=6, md=6, lg=3, className="mb-3")
    
    except Exception as e:
        logger.error(f"Error creating stat card: {e}", exc_info=True)
        return dbc.Col(html.Div(), xs=12, sm=6, md=6, lg=3)


def create_stats_row(stats_data: dict) -> dbc.Row:
    """
    Create a row of stat cards.
    
    Args:
        stats_data: Dictionary with stat information:
            {
                "total_jobs": {"value": 150, "trend": "+12 today"},
                "new_today": {"value": 12, "trend": None},
                "high_match": {"value": 45, "trend": "+5 this week"},
                "rcip_jobs": {"value": 23, "trend": None}
            }
    
    Returns:
        dbc.Row containing stat cards
    """
    try:
        # Extract data with defaults
        total_jobs = stats_data.get("total_jobs", {})
        new_today = stats_data.get("new_today", {})
        high_match = stats_data.get("high_match", {})
        rcip_jobs = stats_data.get("rcip_jobs", {})
        
        # Create stat cards
        cards = [
            create_professional_stat_card(
                title="Total Jobs",
                value=str(total_jobs.get("value", 0)),
                icon="fas fa-briefcase",
                color="primary",
                trend=total_jobs.get("trend"),
                trend_direction=total_jobs.get("trend_direction", "neutral")
            ),
            create_professional_stat_card(
                title="New Today",
                value=str(new_today.get("value", 0)),
                icon="fas fa-plus-circle",
                color="success",
                trend=new_today.get("trend"),
                trend_direction=new_today.get("trend_direction", "up")
            ),
            create_professional_stat_card(
                title="High Match (70%+)",
                value=str(high_match.get("value", 0)),
                icon="fas fa-star",
                color="warning",
                trend=high_match.get("trend"),
                trend_direction=high_match.get("trend_direction", "neutral")
            ),
            create_professional_stat_card(
                title="RCIP Jobs",
                value=str(rcip_jobs.get("value", 0)),
                icon="fas fa-flag",
                color="info",
                trend=rcip_jobs.get("trend"),
                trend_direction=rcip_jobs.get("trend_direction", "neutral")
            )
        ]
        
        return dbc.Row(cards, className="mb-4")
    
    except Exception as e:
        logger.error(f"Error creating stats row: {e}", exc_info=True)
        return dbc.Row([])


def create_mini_stat_card(
    label: str,
    value: str,
    icon: Optional[str] = None,
    color: str = "primary"
) -> html.Div:
    """
    Create a mini stat card for inline display.
    
    Args:
        label: Stat label
        value: Stat value
        icon: Optional icon class
        color: Color variant
    
    Returns:
        html.Div with mini stat card
    """
    return html.Div([
        html.Div([
            html.I(className=f"{icon} me-2 text-{color}") if icon else None,
            html.Span(label, className="text-muted me-2", style={"fontSize": "13px"}),
            html.Span(value, className=f"font-weight-semibold text-{color}", 
                     style={"fontSize": "16px"})
        ], className="d-flex align-items-center")
    ], className="mb-2")


def create_stat_badge(
    value: str,
    label: str,
    color: str = "primary"
) -> html.Span:
    """
    Create a stat badge for compact display.
    
    Args:
        value: Stat value
        label: Stat label
        color: Color variant
    
    Returns:
        html.Span with badge
    """
    return html.Span([
        html.Span(value, className="font-weight-bold me-1"),
        html.Span(label, className="font-weight-normal")
    ], className=f"badge badge-{color} me-2", 
       style={"fontSize": "13px", "padding": "6px 12px"})


def create_comparison_stat(
    current_value: int,
    previous_value: int,
    label: str,
    period: str = "vs last week"
) -> html.Div:
    """
    Create a stat with comparison to previous period.
    
    Args:
        current_value: Current period value
        previous_value: Previous period value
        label: Stat label
        period: Comparison period description
    
    Returns:
        html.Div with comparison stat
    """
    # Calculate change
    if previous_value > 0:
        change = current_value - previous_value
        change_percent = (change / previous_value) * 100
    else:
        change = current_value
        change_percent = 100.0 if current_value > 0 else 0.0
    
    # Determine color and icon
    if change > 0:
        color = "success"
        icon = "fas fa-arrow-up"
        sign = "+"
    elif change < 0:
        color = "danger"
        icon = "fas fa-arrow-down"
        sign = ""
    else:
        color = "muted"
        icon = "fas fa-minus"
        sign = ""
    
    return html.Div([
        html.Div([
            html.H3(str(current_value), className="mb-1"),
            html.P(label, className="text-muted mb-2", style={"fontSize": "14px"})
        ]),
        html.Div([
            html.I(className=f"{icon} me-1 text-{color}"),
            html.Span(
                f"{sign}{change} ({sign}{change_percent:.1f}%)",
                className=f"text-{color} font-weight-medium me-2"
            ),
            html.Small(period, className="text-muted")
        ], className="d-flex align-items-center")
    ], className="p-3 border rounded mb-3")


def create_progress_stat(
    current: int,
    target: int,
    label: str,
    color: str = "primary"
) -> html.Div:
    """
    Create a stat with progress bar toward target.
    
    Args:
        current: Current value
        target: Target value
        label: Stat label
        color: Color variant
    
    Returns:
        html.Div with progress stat
    """
    # Calculate percentage
    if target > 0:
        percentage = min(100, (current / target) * 100)
    else:
        percentage = 0
    
    return html.Div([
        html.Div([
            html.Span(label, className="font-weight-medium"),
            html.Span(
                f"{current} / {target}",
                className="text-muted float-end"
            )
        ], className="mb-2"),
        dbc.Progress(
            value=percentage,
            color=color,
            style={"height": "8px"}
        ),
        html.Small(
            f"{percentage:.0f}% complete",
            className="text-muted mt-1 d-block"
        )
    ], className="mb-3")


def create_metric_grid(metrics: list) -> html.Div:
    """
    Create a grid of metrics.
    
    Args:
        metrics: List of metric dicts with:
            - label: str
            - value: str
            - icon: str (optional)
            - color: str (optional)
    
    Returns:
        html.Div with metric grid
    """
    metric_items = []
    
    for metric in metrics:
        label = metric.get("label", "")
        value = metric.get("value", "")
        icon = metric.get("icon")
        color = metric.get("color", "primary")
        
        metric_items.append(
            dbc.Col([
                html.Div([
                    html.I(className=f"{icon} text-{color} mb-2", 
                          style={"fontSize": "24px"}) if icon else None,
                    html.H4(value, className="mb-1"),
                    html.P(label, className="text-muted mb-0", 
                          style={"fontSize": "13px"})
                ], className="text-center p-3 border rounded")
            ], xs=6, md=3, className="mb-3")
        )
    
    return html.Div([
        dbc.Row(metric_items)
    ])
