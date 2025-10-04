"""
Export Component
One-click export functionality for job data
"""

import dash_bootstrap_components as dbc
from dash import html
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def create_export_button_group() -> dbc.ButtonGroup:
    """
    Create export button group with format options.

    Returns:
        dbc.ButtonGroup: Export buttons with dropdown
    """
    return dbc.ButtonGroup(
        [
            dbc.Button(
                [html.I(className="fas fa-download me-2"), "Export"],
                color="outline-secondary",
                size="sm",
                id="export-btn",
            ),
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(
                        [html.I(className="fas fa-file-excel me-2"), "Export to Excel (.xlsx)"],
                        id="export-excel-btn",
                    ),
                    dbc.DropdownMenuItem(
                        [html.I(className="fas fa-file-csv me-2"), "Export to CSV"],
                        id="export-csv-btn",
                    ),
                    dbc.DropdownMenuItem(
                        [html.I(className="fas fa-file-code me-2"), "Export to JSON"],
                        id="export-json-btn",
                    ),
                    dbc.DropdownMenuItem(divider=True),
                    dbc.DropdownMenuItem(
                        [html.I(className="fas fa-bookmark me-2"), "Export Bookmarked Jobs Only"],
                        id="export-bookmarks-btn",
                    ),
                ],
                label="",
                color="outline-secondary",
                size="sm",
                toggle_style={"border-left": "none"},
            ),
        ]
    )


def create_export_modal() -> dbc.Modal:
    """
    Create modal for export options and progress.

    Returns:
        dbc.Modal: Export configuration modal
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(
                [dbc.ModalTitle([html.I(className="fas fa-download me-2"), "Export Jobs Data"])]
            ),
            dbc.ModalBody(
                [
                    # Export format selection
                    html.Div(
                        [
                            html.Label("Export Format:", className="form-label"),
                            dbc.RadioItems(
                                options=[
                                    {
                                        "label": [
                                            html.I(className="fas fa-file-excel me-2"),
                                            "Excel (.xlsx) - Recommended",
                                        ],
                                        "value": "excel",
                                    },
                                    {
                                        "label": [
                                            html.I(className="fas fa-file-csv me-2"),
                                            "CSV - Universal format",
                                        ],
                                        "value": "csv",
                                    },
                                    {
                                        "label": [
                                            html.I(className="fas fa-file-code me-2"),
                                            "JSON - For developers",
                                        ],
                                        "value": "json",
                                    },
                                ],
                                value="excel",
                                id="export-format-radio",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Data selection
                    html.Div(
                        [
                            html.Label("Data to Export:", className="form-label"),
                            dbc.Checklist(
                                options=[
                                    {
                                        "label": "Job Title & Company",
                                        "value": "basic",
                                        "disabled": True,
                                    },
                                    {"label": "Salary Information", "value": "salary"},
                                    {"label": "Location Details", "value": "location"},
                                    {"label": "Job Description", "value": "description"},
                                    {"label": "Keywords & Skills", "value": "keywords"},
                                    {"label": "Application Status", "value": "status"},
                                    {"label": "Bookmark Status", "value": "bookmarks"},
                                    {"label": "Match Scores", "value": "scores"},
                                    {"label": "Job URLs", "value": "urls"},
                                    {"label": "Posted Dates", "value": "dates"},
                                ],
                                value=[
                                    "basic",
                                    "salary",
                                    "location",
                                    "keywords",
                                    "status",
                                    "scores",
                                    "urls",
                                ],
                                id="export-fields-checklist",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Filter options
                    html.Div(
                        [
                            html.Label("Export Filters:", className="form-label"),
                            dbc.Checklist(
                                options=[
                                    {"label": "Current filtered results only", "value": "filtered"},
                                    {"label": "Bookmarked jobs only", "value": "bookmarked"},
                                    {"label": "Applied jobs only", "value": "applied"},
                                    {
                                        "label": "High match scores (80%+) only",
                                        "value": "high_match",
                                    },
                                ],
                                value=[],
                                id="export-filters-checklist",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Export summary
                    html.Div(
                        [html.Hr(), html.Div(id="export-summary", className="text-muted small")]
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("Cancel", color="secondary", size="sm", id="export-cancel-btn"),
                    dbc.Button(
                        [html.I(className="fas fa-download me-2"), "Export Now"],
                        color="primary",
                        size="sm",
                        id="export-confirm-btn",
                    ),
                ]
            ),
        ],
        id="export-modal",
        size="lg",
        backdrop="static",
    )


def create_export_toast() -> dbc.Toast:
    """
    Create toast notification for export status.

    Returns:
        dbc.Toast: Export status notification
    """
    return dbc.Toast(
        id="export-toast",
        header="Export Status",
        is_open=False,
        dismissable=True,
        duration=4000,
        style={"position": "fixed", "top": 66, "right": 10, "width": 350},
    )


def prepare_export_data(
    jobs_data: List[Dict[str, Any]], selected_fields: List[str], export_filters: List[str] = None
) -> pd.DataFrame:
    """
    Prepare job data for export based on selected fields and filters.

    Args:
        jobs_data: List of job dictionaries
        selected_fields: List of field types to include
        export_filters: List of filter types to apply

    Returns:
        pd.DataFrame: Prepared data for export
    """
    if not jobs_data:
        return pd.DataFrame()

    # Apply filters first
    filtered_data = jobs_data.copy()

    if export_filters:
        if "bookmarked" in export_filters:
            filtered_data = [job for job in filtered_data if job.get("is_bookmarked", False)]

        if "applied" in export_filters:
            filtered_data = [
                job
                for job in filtered_data
                if job.get("application_status") in ["applied", "interview", "offer"]
            ]

        if "high_match" in export_filters:
            filtered_data = [job for job in filtered_data if job.get("match_score", 0) >= 80]

    # Define field mappings
    field_mappings = {
        "basic": {"Job Title": "title", "Company": "company"},
        "salary": {"Salary": "salary", "Salary Min": "salary_min", "Salary Max": "salary_max"},
        "location": {
            "Location": "location",
            "Remote": "is_remote",
            "City": "city",
            "State/Province": "state",
            "Country": "country",
        },
        "description": {"Description": "description", "Requirements": "requirements"},
        "keywords": {"Keywords": "keywords", "Skills Required": "skills"},
        "status": {"Application Status": "application_status", "Status Date": "status_date"},
        "bookmarks": {"Bookmarked": "is_bookmarked", "Bookmark Date": "bookmark_date"},
        "scores": {"Match Score": "match_score", "Relevance Score": "relevance_score"},
        "urls": {"Job URL": "url", "Apply URL": "apply_url"},
        "dates": {"Posted Date": "posted_date", "Scraped Date": "scraped_date"},
    }

    # Build export DataFrame
    export_dict = {}

    # Always include basic fields
    for display_name, field_name in field_mappings["basic"].items():
        export_dict[display_name] = [job.get(field_name, "") for job in filtered_data]

    # Add selected fields
    for field_group in selected_fields:
        if field_group in field_mappings:
            for display_name, field_name in field_mappings[field_group].items():
                if field_name == "keywords" and field_name in job:
                    # Handle keywords list
                    export_dict[display_name] = [
                        (
                            ", ".join(job.get(field_name, []))
                            if isinstance(job.get(field_name), list)
                            else str(job.get(field_name, ""))
                        )
                        for job in filtered_data
                    ]
                else:
                    export_dict[display_name] = [job.get(field_name, "") for job in filtered_data]

    # Add metadata
    export_dict["Export Date"] = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] * len(filtered_data)

    export_dict["Total Jobs"] = [len(filtered_data)] * len(filtered_data)

    return pd.DataFrame(export_dict)


def export_to_excel(df: pd.DataFrame, filename: str = None) -> str:
    """
    Export DataFrame to Excel format.

    Args:
        df: DataFrame to export
        filename: Optional filename override

    Returns:
        str: Path to the exported file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jobqst_export_{timestamp}.xlsx"

    try:
        # Create Excel file with multiple sheets if needed
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            # Main jobs data
            df.to_excel(writer, sheet_name="Jobs", index=False)

            # Summary sheet
            summary_data = {
                "Metric": [
                    "Total Jobs Exported",
                    "Export Date",
                    "Unique Companies",
                    "Avg Match Score",
                    "Bookmarked Jobs",
                    "Applied Jobs",
                ],
                "Value": [
                    len(df),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    df["Company"].nunique() if "Company" in df.columns else "N/A",
                    f"{df['Match Score'].mean():.1f}%" if "Match Score" in df.columns else "N/A",
                    len(df[df["Bookmarked"] == True]) if "Bookmarked" in df.columns else "N/A",
                    (
                        len(df[df["Application Status"].isin(["applied", "interview", "offer"])])
                        if "Application Status" in df.columns
                        else "N/A"
                    ),
                ],
            }

            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

        logger.info(f"Excel export completed: {filename}")
        return filename

    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        raise


def export_to_csv(df: pd.DataFrame, filename: str = None) -> str:
    """
    Export DataFrame to CSV format.

    Args:
        df: DataFrame to export
        filename: Optional filename override

    Returns:
        str: Path to the exported file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jobqst_export_{timestamp}.csv"

    try:
        df.to_csv(filename, index=False, encoding="utf-8")
        logger.info(f"CSV export completed: {filename}")
        return filename

    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        raise


def export_to_json(jobs_data: List[Dict[str, Any]], filename: str = None) -> str:
    """
    Export job data to JSON format.

    Args:
        jobs_data: List of job dictionaries
        filename: Optional filename override

    Returns:
        str: Path to the exported file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jobqst_export_{timestamp}.json"

    try:
        import json

        export_data = {
            "export_metadata": {
                "export_date": datetime.now().isoformat(),
                "total_jobs": len(jobs_data),
                "export_version": "1.0",
            },
            "jobs": jobs_data,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"JSON export completed: {filename}")
        return filename

    except Exception as e:
        logger.error(f"Error exporting to JSON: {str(e)}")
        raise
