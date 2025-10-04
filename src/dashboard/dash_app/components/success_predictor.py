"""
Application success predictor component for dashboard home tab.
Displays role-based success predictions with visual indicators.
"""

from typing import Dict, List
import dash_bootstrap_components as dbc
from dash import html
import logging

logger = logging.getLogger(__name__)


def create_success_predictor_card(predictions: List[Dict]) -> dbc.Card:
    """
    Create application success predictor card with role-based predictions.
    
    Args:
        predictions: List of dicts with keys:
            - job_type: str (e.g., "Data Analyst roles")
            - percentage: float (success probability 0-100)
            - reason: str (explanation of the prediction)
            - matched_skills: List[str]
            - missing_skills: List[str]
            - confidence: str (high/medium/low)
            - job_count: int
    
    Returns:
        dbc.Card with success predictions
    """
    try:
        if not predictions:
            return _create_no_predictions_card()
        
        # Create prediction items
        prediction_items = []
        
        for pred in predictions[:5]:  # Show top 5 roles
            prediction_items.append(_create_prediction_item(pred))
        
        # Create card
        card = dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.I(className="fas fa-bullseye me-2"),
                    html.Span("Application Success Predictor", className="font-weight-semibold")
                ], className="d-flex align-items-center")
            ], className="bg-light"),
            dbc.CardBody([
                html.P(
                    "Your estimated success rate for different job roles based on skill matching:",
                    className="text-muted mb-3",
                    style={"fontSize": "14px"}
                ),
                html.Div(prediction_items)
            ])
        ], className="professional-card mb-4")
        
        return card
    
    except Exception as e:
        logger.error(f"Error creating success predictor card: {e}", exc_info=True)
        return _create_error_card()


def _create_prediction_item(prediction: Dict) -> html.Div:
    """
    Create a single prediction item with progress bar.
    
    Args:
        prediction: Prediction dictionary
    
    Returns:
        html.Div containing the prediction item
    """
    job_type = prediction.get("job_type", "Unknown")
    percentage = prediction.get("percentage", 0)
    reason = prediction.get("reason", "")
    matched_skills = prediction.get("matched_skills", [])
    missing_skills = prediction.get("missing_skills", [])
    confidence = prediction.get("confidence", "low")
    job_count = prediction.get("job_count", 0)
    
    # Determine color based on percentage
    if percentage >= 70:
        color_class = "success"
        icon = "fas fa-check-circle"
    elif percentage >= 50:
        color_class = "warning"
        icon = "fas fa-exclamation-circle"
    else:
        color_class = "danger"
        icon = "fas fa-times-circle"
    
    # Confidence badge
    confidence_badges = {
        "high": ("success", "High Confidence"),
        "medium": ("warning", "Medium Confidence"),
        "low": ("info", "Low Confidence")
    }
    conf_color, conf_text = confidence_badges.get(confidence, ("secondary", "Unknown"))
    
    # Create progress bar
    progress_bar = dbc.Progress(
        value=percentage,
        color=color_class,
        className="mb-2",
        style={"height": "10px"}
    )
    
    # Skills display
    skills_display = []
    
    if matched_skills:
        skills_display.append(
            html.Div([
                html.Small([
                    html.I(className="fas fa-check text-success me-1"),
                    html.Span("You have: ", className="font-weight-medium"),
                    html.Span(", ".join(matched_skills[:5]), className="text-muted")
                ], className="d-block mb-1")
            ])
        )
    
    if missing_skills:
        skills_display.append(
            html.Div([
                html.Small([
                    html.I(className="fas fa-times text-danger me-1"),
                    html.Span("Consider learning: ", className="font-weight-medium"),
                    html.Span(", ".join(missing_skills[:5]), className="text-muted")
                ], className="d-block")
            ])
        )
    
    return html.Div([
        # Header with role and percentage
        html.Div([
            html.Div([
                html.I(className=f"{icon} me-2 text-{color_class}"),
                html.Span(job_type, className="success-prediction-role font-weight-medium"),
                html.Span(
                    f"{job_count} jobs",
                    className="badge badge-secondary ms-2",
                    style={"fontSize": "10px"}
                ),
                html.Span(
                    conf_text,
                    className=f"badge badge-{conf_color} ms-2",
                    style={"fontSize": "10px"}
                )
            ], className="d-flex align-items-center"),
            html.Span(
                f"{percentage:.0f}%",
                className=f"success-prediction-percentage text-{color_class} font-weight-bold"
            )
        ], className="success-prediction-header d-flex justify-content-between align-items-center mb-2"),
        
        # Progress bar
        progress_bar,
        
        # Reason
        html.Div([
            html.Small(reason, className="text-muted")
        ], className="success-prediction-reason mb-2"),
        
        # Skills
        html.Div(skills_display, className="mb-3") if skills_display else html.Div()
        
    ], className="success-prediction-item mb-4")


def _create_no_predictions_card() -> dbc.Card:
    """
    Create card for when no predictions are available.
    
    Returns:
        dbc.Card with no data message
    """
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.I(className="fas fa-bullseye me-2"),
                html.Span("Application Success Predictor", className="font-weight-semibold")
            ], className="d-flex align-items-center")
        ], className="bg-light"),
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-info-circle text-info", 
                      style={"fontSize": "48px"}),
                html.H5("No Data Available", className="mt-3 mb-2"),
                html.P(
                    "Add more jobs to your database to see success predictions for different roles.",
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
                html.I(className="fas fa-bullseye me-2"),
                html.Span("Application Success Predictor", className="font-weight-semibold")
            ], className="d-flex align-items-center")
        ], className="bg-light"),
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-exclamation-triangle text-warning", 
                      style={"fontSize": "48px"}),
                html.P(
                    "Unable to load success predictions. Please try refreshing the page.",
                    className="text-muted mt-3"
                )
            ], className="empty-state text-center py-4")
        ])
    ], className="professional-card mb-4")


def create_overall_success_card(overall_data: Dict) -> dbc.Card:
    """
    Create overall success score card.
    
    Args:
        overall_data: Dictionary with:
            - overall_score: float
            - high_match_count: int
            - medium_match_count: int
            - low_match_count: int
            - recommendation: str
    
    Returns:
        dbc.Card with overall success metrics
    """
    try:
        overall_score = overall_data.get("overall_score", 0)
        high_match = overall_data.get("high_match_count", 0)
        medium_match = overall_data.get("medium_match_count", 0)
        low_match = overall_data.get("low_match_count", 0)
        recommendation = overall_data.get("recommendation", "")
        
        # Determine color
        if overall_score >= 70:
            score_color = "success"
            score_icon = "fas fa-trophy"
        elif overall_score >= 50:
            score_color = "warning"
            score_icon = "fas fa-star"
        else:
            score_color = "danger"
            score_icon = "fas fa-chart-line"
        
        card = dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.I(className="fas fa-chart-bar me-2"),
                    html.Span("Overall Success Score", className="font-weight-semibold")
                ], className="d-flex align-items-center")
            ], className="bg-light"),
            dbc.CardBody([
                # Large score display
                html.Div([
                    html.I(className=f"{score_icon} text-{score_color}", 
                          style={"fontSize": "48px"}),
                    html.H1(
                        f"{overall_score:.0f}%",
                        className=f"text-{score_color} mt-2 mb-0",
                        style={"fontSize": "48px", "fontWeight": "bold"}
                    ),
                    html.P("Average Match Score", className="text-muted")
                ], className="text-center mb-4"),
                
                # Match breakdown
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.H4(str(high_match), className="text-success mb-0"),
                                html.Small("High Match", className="text-muted")
                            ], className="text-center")
                        ], width=4),
                        dbc.Col([
                            html.Div([
                                html.H4(str(medium_match), className="text-warning mb-0"),
                                html.Small("Medium Match", className="text-muted")
                            ], className="text-center")
                        ], width=4),
                        dbc.Col([
                            html.Div([
                                html.H4(str(low_match), className="text-muted mb-0"),
                                html.Small("Low Match", className="text-muted")
                            ], className="text-center")
                        ], width=4)
                    ], className="mb-3")
                ]),
                
                # Recommendation
                html.Div([
                    html.Hr(),
                    html.Div([
                        html.I(className="fas fa-lightbulb text-warning me-2"),
                        html.Span("Recommendation", className="font-weight-semibold")
                    ], className="mb-2"),
                    html.P(recommendation, className="text-muted mb-0", 
                          style={"fontSize": "14px"})
                ])
            ])
        ], className="professional-card mb-4")
        
        return card
    
    except Exception as e:
        logger.error(f"Error creating overall success card: {e}", exc_info=True)
        return html.Div()
