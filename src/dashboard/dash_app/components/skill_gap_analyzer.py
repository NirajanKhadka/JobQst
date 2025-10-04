"""
Skill gap analyzer component for dashboard home tab.
Displays skill gaps with visual progress bars and explanations.
"""

from typing import Dict, List, Optional
import dash_bootstrap_components as dbc
from dash import html
import logging

logger = logging.getLogger(__name__)


def create_skill_gap_analysis_card(skill_gaps: List[Dict]) -> dbc.Card:
    """
    Create skill gap analysis card with progress bars and explanations.
    
    Args:
        skill_gaps: List of dicts with keys:
            - skill: str (skill name)
            - percentage: float (% of jobs requiring this skill)
            - jobs_count: int (number of jobs)
            - priority: str (high/medium/low)
            - rule_explanation: str (how it was detected)
            - example_keywords: List[str] (keywords that matched)
    
    Returns:
        dbc.Card with skill gap visualization
    """
    try:
        if not skill_gaps:
            return _create_no_skill_gaps_card()
        
        # Create skill gap items
        skill_gap_items = []
        
        for gap in skill_gaps:
            skill_gap_items.append(_create_skill_gap_item(gap))
        
        # Create card
        card = dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.I(className="fas fa-chart-line me-2"),
                    html.Span("Skill Gap Analysis", className="font-weight-semibold")
                ], className="d-flex align-items-center")
            ], className="bg-light"),
            dbc.CardBody([
                html.P(
                    "Based on your target jobs, here are the most in-demand skills you don't have yet:",
                    className="text-muted mb-3",
                    style={"fontSize": "14px"}
                ),
                html.Div(skill_gap_items)
            ])
        ], className="professional-card mb-4")
        
        return card
    
    except Exception as e:
        logger.error(f"Error creating skill gap analysis card: {e}", exc_info=True)
        return _create_error_card()


def _create_skill_gap_item(gap: Dict) -> html.Div:
    """
    Create a single skill gap item with progress bar.
    
    Args:
        gap: Skill gap dictionary
    
    Returns:
        html.Div containing the skill gap item
    """
    skill = gap.get("skill", "Unknown")
    percentage = gap.get("percentage", 0)
    jobs_count = gap.get("jobs_count", 0)
    priority = gap.get("priority", "low")
    rule_explanation = gap.get("rule_explanation", "")
    example_keywords = gap.get("example_keywords", [])
    
    # Determine color based on priority
    if priority == "high":
        color_class = "danger"
        badge_color = "danger"
    elif priority == "medium":
        color_class = "warning"
        badge_color = "warning"
    else:
        color_class = "info"
        badge_color = "info"
    
    # Create progress bar
    progress_bar = dbc.Progress(
        value=percentage,
        color=color_class,
        className="mb-2",
        style={"height": "8px"}
    )
    
    # Create keywords display
    keywords_display = html.Span([
        html.Small([
            "Keywords: ",
            html.Code(", ".join(example_keywords[:3]), className="text-muted")
        ], className="text-muted")
    ]) if example_keywords else None
    
    return html.Div([
        # Header with skill name and percentage
        html.Div([
            html.Div([
                html.Span(skill, className="skill-gap-name font-weight-medium"),
                html.Span(
                    priority.upper(),
                    className=f"badge badge-{badge_color} ms-2",
                    style={"fontSize": "10px"}
                )
            ]),
            html.Span(
                f"{percentage:.0f}%",
                className="skill-gap-percentage text-primary-custom font-weight-semibold"
            )
        ], className="skill-gap-header d-flex justify-content-between align-items-center mb-2"),
        
        # Progress bar
        progress_bar,
        
        # Explanation
        html.Div([
            html.Small([
                html.I(className="fas fa-info-circle me-1"),
                rule_explanation
            ], className="text-muted")
        ], className="skill-gap-explanation mb-2"),
        
        # Keywords
        keywords_display if keywords_display else html.Div(),
        
    ], className="skill-gap-item mb-4")


def _create_no_skill_gaps_card() -> dbc.Card:
    """
    Create card for when no skill gaps are found.
    
    Returns:
        dbc.Card with no data message
    """
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.I(className="fas fa-chart-line me-2"),
                html.Span("Skill Gap Analysis", className="font-weight-semibold")
            ], className="d-flex align-items-center")
        ], className="bg-light"),
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-check-circle text-success", 
                      style={"fontSize": "48px"}),
                html.H5("Great News!", className="mt-3 mb-2"),
                html.P(
                    "You have all the key skills mentioned in your target jobs! "
                    "Keep your skills updated and continue applying.",
                    className="text-muted"
                )
            ], className="empty-state text-center py-4")
        ])
    ], className="professional-card mb-4")


def _create_error_card() -> dbc.Card:
    """
    Create card for error state.
    
    Returns:
        dbc.Card with error message
    """
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.I(className="fas fa-chart-line me-2"),
                html.Span("Skill Gap Analysis", className="font-weight-semibold")
            ], className="d-flex align-items-center")
        ], className="bg-light"),
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-exclamation-triangle text-warning", 
                      style={"fontSize": "48px"}),
                html.P(
                    "Unable to load skill gap analysis. Please try refreshing the page.",
                    className="text-muted mt-3"
                )
            ], className="empty-state text-center py-4")
        ])
    ], className="professional-card mb-4")


def create_skill_recommendations_card(recommendations: List[Dict]) -> dbc.Card:
    """
    Create skill recommendations card with learning suggestions.
    
    Args:
        recommendations: List of recommendation dicts with:
            - skill: str
            - reason: str
            - priority: str
            - learning_resources: List[str]
            - jobs_count: int
    
    Returns:
        dbc.Card with skill recommendations
    """
    try:
        if not recommendations:
            return html.Div()  # Return empty div if no recommendations
        
        recommendation_items = []
        
        for i, rec in enumerate(recommendations[:5], 1):  # Limit to top 5
            skill = rec.get("skill", "Unknown")
            reason = rec.get("reason", "")
            priority = rec.get("priority", "low")
            jobs_count = rec.get("jobs_count", 0)
            
            # Priority badge
            if priority == "high":
                badge_color = "danger"
            elif priority == "medium":
                badge_color = "warning"
            else:
                badge_color = "info"
            
            recommendation_items.append(
                html.Div([
                    html.Div([
                        html.Span(f"{i}. ", className="text-muted me-1"),
                        html.Span(skill, className="font-weight-semibold"),
                        html.Span(
                            f"{jobs_count} jobs",
                            className=f"badge badge-{badge_color} ms-2",
                            style={"fontSize": "10px"}
                        )
                    ], className="mb-2"),
                    html.P(reason, className="text-muted mb-3", 
                          style={"fontSize": "13px"})
                ], className="mb-3")
            )
        
        card = dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.I(className="fas fa-lightbulb me-2"),
                    html.Span("Recommended Skills to Learn", className="font-weight-semibold")
                ], className="d-flex align-items-center")
            ], className="bg-light"),
            dbc.CardBody([
                html.P(
                    "Focus on these skills to maximize your job opportunities:",
                    className="text-muted mb-3",
                    style={"fontSize": "14px"}
                ),
                html.Div(recommendation_items)
            ])
        ], className="professional-card mb-4")
        
        return card
    
    except Exception as e:
        logger.error(f"Error creating skill recommendations card: {e}", exc_info=True)
        return html.Div()


def create_skill_coverage_badge(coverage_percentage: float) -> html.Div:
    """
    Create a badge showing skill coverage percentage.
    
    Args:
        coverage_percentage: Percentage of required skills user has (0-100)
    
    Returns:
        html.Div with coverage badge
    """
    if coverage_percentage >= 80:
        color = "success"
        icon = "fas fa-check-circle"
        label = "Excellent"
    elif coverage_percentage >= 60:
        color = "primary"
        icon = "fas fa-thumbs-up"
        label = "Good"
    elif coverage_percentage >= 40:
        color = "warning"
        icon = "fas fa-exclamation-circle"
        label = "Fair"
    else:
        color = "danger"
        icon = "fas fa-times-circle"
        label = "Needs Work"
    
    return html.Div([
        html.I(className=f"{icon} me-2"),
        html.Span(f"{coverage_percentage:.0f}% Skill Match", 
                 className="font-weight-semibold me-2"),
        html.Span(label, className=f"badge badge-{color}")
    ], className="d-flex align-items-center")
