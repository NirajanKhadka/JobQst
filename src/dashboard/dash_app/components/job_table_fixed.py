"""
Job table component for JobQst Dashboard
Interactive DataTable for job management
"""

import dash_bootstrap_components as dbc
from dash import html, dash_table
import pandas as pd


def create_jobs_table(data=None):
    """Create an interactive jobs DataTable"""

    if data is None:
        data = []

    # Define table columns - including salary column prominently
    columns = [
        {"name": "Title", "id": "title", "type": "text", "presentation": "markdown"},
        {"name": "Company", "id": "company", "type": "text"},
        {"name": "Location", "id": "location", "type": "text"},
        {"name": "Salary", "id": "salary", "type": "text"},
        {"name": "Status", "id": "status", "type": "text", "presentation": "dropdown"},
        {
            "name": "Match Score",
            "id": "match_score",
            "type": "numeric",
            "format": {"specifier": ".0f"},
        },
        {
            "name": "AI Confidence",
            "id": "confidence_badge",
            "type": "text",
            "presentation": "markdown",
        },
        {
            "name": "Semantic Score",
            "id": "semantic_score",
            "type": "numeric",
            "format": {"specifier": ".2f"},
        },
        {"name": "Validation Method", "id": "validation_method", "type": "text"},
        {"name": "Posted Date", "id": "posted_date", "type": "text"},
        {"name": "Actions", "id": "actions", "type": "text", "presentation": "markdown"},
    ]

    return dash_table.DataTable(
        id="jobs-table",
        columns=columns,
        data=data,
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        column_selectable="single",
        row_selectable="multi",
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=25,
        style_table={
            "backgroundColor": "#343a40",
            "color": "white",
            "borderRadius": "8px",
            "overflow": "hidden",
        },
        style_header={
            "backgroundColor": "#495057",
            "color": "white",
            "fontWeight": "bold",
            "textAlign": "center",
            "border": "1px solid #6c757d",
        },
        style_cell={
            "backgroundColor": "#343a40",
            "color": "white",
            "textAlign": "left",
            "padding": "10px",
            "border": "1px solid #495057",
            "fontSize": "14px",
            "whiteSpace": "normal",
            "height": "auto",
            "minWidth": "100px",
        },
        style_data={
            "backgroundColor": "#343a40",
            "color": "white",
        },
        style_data_conditional=[
            {
                "if": {"state": "active"},
                "backgroundColor": "#495057",
                "border": "1px solid #007bff",
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "#007bff",
                "color": "white",
            },
            {"if": {"column_id": "match_score"}, "textAlign": "center", "fontWeight": "bold"},
        ],
        css=[
            {
                "selector": ".dash-table-tooltip",
                "rule": ("background-color: #2d3436; color: white; " "border: 1px solid #636e72;"),
            }
        ],
        tooltip_data=[
            {
                column: {"value": f"Click to edit {column}", "type": "markdown"}
                for column in ["title", "company", "location", "status"]
            }
            for row in data
        ],
        tooltip_duration=None,
    )


def create_table_controls():
    """Create table control buttons"""
    return dbc.ButtonGroup(
        [
            dbc.Button(
                [html.I(className="fas fa-table me-1"), "Table View"],
                id="table-view-btn",
                color="primary",
                size="sm",
                active=True,
            ),
            dbc.Button(
                [html.I(className="fas fa-th-large me-1"), "Card View"],
                id="card-view-btn",
                color="outline-primary",
                size="sm",
            ),
            dbc.Button(
                [html.I(className="fas fa-download me-1"), "Export"],
                id="export-jobs-btn",
                color="outline-secondary",
                size="sm",
            ),
            dbc.Button(
                [html.I(className="fas fa-trash me-1"), "Bulk Actions"],
                id="bulk-actions-btn",
                color="outline-warning",
                size="sm",
            ),
        ],
        className="mb-3",
    )


def format_job_data_for_table(df):
    """Format job DataFrame for display in DataTable"""
    if df.empty:
        return []

    # Create a copy to avoid modifying the original
    display_df = df.copy()

    # Ensure required columns exist
    required_columns = [
        "id",
        "title",
        "company",
        "location",
        "status",
        "salary",
        "match_score",
        "posted_date",
        "job_url",
    ]

    for col in required_columns:
        if col not in display_df.columns:
            if col == "id":
                display_df[col] = range(len(display_df))
            elif col == "salary":
                display_df[col] = "Not specified"
            elif col == "match_score":
                display_df[col] = 0
            elif col == "job_url":
                display_df[col] = "#"
            else:
                display_df[col] = "Unknown"

    # Format dates
    if "created_at" in display_df.columns:
        display_df["posted_date"] = pd.to_datetime(display_df["created_at"]).dt.strftime("%Y-%m-%d")
    elif "posted_date" not in display_df.columns:
        display_df["posted_date"] = "Unknown"

    # Format salary for display
    if "salary_display" in display_df.columns:
        display_df["salary"] = display_df["salary_display"]
    elif "salary" in display_df.columns:
        # Ensure salary is properly formatted
        display_df["salary"] = display_df["salary"].fillna("Not specified")
    else:
        display_df["salary"] = "Not specified"

    # Format status for display
    if "status" in display_df.columns:
        status_map = {
            "new": "🆕 New",
            "ready_to_apply": "✅ Ready to Apply",
            "applied": "📤 Applied",
            "needs_review": "🔍 Needs Review",
            "rejected": "❌ Rejected",
            "archived": "📁 Archived",
        }
        display_df["status"] = display_df["status"].map(status_map).fillna(display_df["status"])

    # Format confidence scores
    if "confidence_score" in display_df.columns:

        def format_confidence_badge(score):
            if pd.isna(score):
                return "❓ Unknown"
            elif score >= 0.8:
                return "🟢 HIGH"
            elif score >= 0.6:
                return "🟡 MEDIUM"
            elif score >= 0.4:
                return "🟠 LOW"
            else:
                return "🔴 POOR"

        display_df["confidence_badge"] = display_df["confidence_score"].apply(
            format_confidence_badge
        )
    elif "quality_score" in display_df.columns:
        # Fallback to quality_score if confidence_score not available
        def format_quality_badge(score):
            if pd.isna(score):
                return "❓ Unknown"
            elif score >= 0.8:
                return "🟢 HIGH"
            elif score >= 0.6:
                return "🟡 MEDIUM"
            elif score >= 0.4:
                return "🟠 LOW"
            else:
                return "🔴 POOR"

        display_df["confidence_badge"] = display_df["quality_score"].apply(format_quality_badge)
    else:
        # Default if no confidence data available
        display_df["confidence_badge"] = "❓ Unknown"

    # Format semantic scores
    if "semantic_score" not in display_df.columns:
        display_df["semantic_score"] = 0.0

    # Format validation methods
    if "validation_method" not in display_df.columns:
        display_df["validation_method"] = "standard"

    # Add validation method icons
    def format_validation_method(method):
        if pd.isna(method) or method == "standard":
            return "📋 Standard"
        elif method == "ai_semantic":
            return "🤖 AI Semantic"
        elif method == "exact_match":
            return "✅ Exact Match"
        elif method == "partial_matching":
            return "🔍 Partial"
        else:
            return f"❓ {method}"

    display_df["validation_method"] = display_df["validation_method"].apply(
        format_validation_method
    )

    # Add action buttons with external links (new tab) and modal triggers
    if "actions" not in display_df.columns:

        def create_action_buttons(row):
            job_id = row.get("id", row.name if hasattr(row, "name") else 0)
            job_url = row.get("job_url", "#")
            # Create external link for View (will open in new tab due to DataTable markdown)
            if job_url and job_url != "#":
                view_link = f"[👁️ View]({job_url})"
            else:
                view_link = "👁️ View"
            # Create modal trigger for notes
            notes_link = f"[📝 Notes](#{job_id})"
            return f"{view_link} | {notes_link}"

        display_df["actions"] = display_df.apply(create_action_buttons, axis=1)

    # Limit long text fields for better display
    text_columns = ["title", "company", "location"]
    for col in text_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].astype(str).str.slice(0, 50)

    return display_df.to_dict("records")
