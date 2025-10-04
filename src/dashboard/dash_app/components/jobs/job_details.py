"""
Enhanced job details component for comprehensive job information display
Focuses on what job seekers actually need to see
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import re


def create_salary_display(salary_info):
    """Create a formatted salary display component"""
    if not salary_info or salary_info in ["None", "N/A", ""]:
        return html.Div(
            [
                html.I(className="fas fa-dollar-sign me-2"),
                html.Span("Salary not disclosed", className="text-muted"),
            ],
            className="salary-info",
        )

    # Parse salary information
    salary_text = str(salary_info)

    # Try to extract salary range
    range_match = re.search(r"(\$[\d,]+)\s*-\s*(\$[\d,]+)", salary_text)
    if range_match:
        min_sal, max_sal = range_match.groups()
        return html.Div(
            [
                html.I(className="fas fa-dollar-sign me-2 text-success"),
                html.Strong(f"{min_sal} - {max_sal}", className="text-success"),
                html.Small(" /year", className="text-muted"),
            ],
            className="salary-info",
        )

    # Single salary value
    single_match = re.search(r"\$[\d,]+", salary_text)
    if single_match:
        salary = single_match.group()
        return html.Div(
            [
                html.I(className="fas fa-dollar-sign me-2 text-success"),
                html.Strong(salary, className="text-success"),
                html.Small(" /year", className="text-muted"),
            ],
            className="salary-info",
        )

    # Fallback - show raw text
    return html.Div(
        [
            html.I(className="fas fa-dollar-sign me-2"),
            html.Span(salary_text, className="text-muted"),
        ],
        className="salary-info",
    )


def create_skills_breakdown(description, required_skills=None):
    """Extract and display skills from job description"""
    if not description:
        return html.Div("No skills information available", className="text-muted")

    # Common technical skills to look for
    common_skills = [
        "Python",
        "JavaScript",
        "Java",
        "C++",
        "C#",
        "Ruby",
        "PHP",
        "Go",
        "Swift",
        "React",
        "Angular",
        "Vue",
        "Node.js",
        "Django",
        "Flask",
        "Spring",
        "SQL",
        "PostgreSQL",
        "MySQL",
        "MongoDB",
        "Redis",
        "AWS",
        "Azure",
        "GCP",
        "Docker",
        "Kubernetes",
        "Jenkins",
        "Git",
        "Agile",
        "Scrum",
        "DevOps",
        "CI/CD",
    ]

    # Find skills mentioned in description
    found_skills = []
    description_lower = description.lower()

    for skill in common_skills:
        if skill.lower() in description_lower:
            found_skills.append(skill)

    if not found_skills:
        return html.Div("Skills to be determined from job description", className="text-muted")

    # Create skill badges
    skill_badges = []
    for skill in found_skills[:10]:  # Limit to first 10 skills
        skill_badges.append(
            dbc.Badge(skill, color="primary", className="me-1 mb-1", style={"font-size": "0.8em"})
        )

    return html.Div(
        [
            html.H6("Required Skills:", className="mb-2"),
            html.Div(skill_badges, className="skills-container"),
        ]
    )


def create_company_info_panel(company_name, location=None):
    """Create company information panel"""
    if not company_name:
        return html.Div("Company information not available", className="text-muted")

    # Basic company info (could be enhanced with API calls)
    company_size = "Size not available"
    industry = "Industry not specified"

    # Try to infer some information from company name
    if any(term in company_name.lower() for term in ["inc", "corp", "ltd", "llc"]):
        company_size = "Established company"

    if any(term in company_name.lower() for term in ["tech", "software", "digital"]):
        industry = "Technology"
    elif any(term in company_name.lower() for term in ["bank", "financial", "finance"]):
        industry = "Financial Services"
    elif any(term in company_name.lower() for term in ["health", "medical", "pharma"]):
        industry = "Healthcare"

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H5(
                        [html.I(className="fas fa-building me-2"), company_name],
                        className="card-title",
                    ),
                    html.P(
                        [html.Strong("Industry: "), html.Span(industry, className="text-muted")],
                        className="mb-1",
                    ),
                    html.P(
                        [html.Strong("Size: "), html.Span(company_size, className="text-muted")],
                        className="mb-1",
                    ),
                    html.P(
                        [
                            html.Strong("Location: "),
                            html.Span(location or "Location not specified", className="text-muted"),
                        ],
                        className="mb-0",
                    ),
                ]
            )
        ],
        className="company-info-card",
    )


def create_work_arrangement_display(location, description=""):
    """Determine and display work arrangement"""
    if not location:
        location = ""

    location_lower = location.lower()
    desc_lower = description.lower() if description else ""

    # Determine work type
    if any(
        term in location_lower or term in desc_lower
        for term in ["remote", "work from home", "wfh", "telecommute"]
    ):
        work_type = "Remote"
        icon = "fas fa-home"
        color = "success"
    elif any(
        term in location_lower or term in desc_lower
        for term in ["hybrid", "flexible", "remote/office"]
    ):
        work_type = "Hybrid"
        icon = "fas fa-laptop-house"
        color = "warning"
    else:
        work_type = "On-site"
        icon = "fas fa-building"
        color = "info"

    return dbc.Badge(
        [html.I(className=f"{icon} me-1"), work_type],
        color=color,
        className="work-arrangement-badge",
    )


def create_application_process_info(job_url=None, company=None):
    """Create application process information"""
    if not job_url:
        return html.Div(
            [
                html.I(className="fas fa-info-circle me-2"),
                html.Span("Application process to be determined", className="text-muted"),
            ]
        )

    # Determine application type based on URL
    if any(site in job_url.lower() for site in ["indeed", "linkedin", "glassdoor"]):
        app_type = "Apply through job board"
        steps = ["Click Apply", "Complete profile", "Submit application"]
        icon = "fas fa-external-link-alt"
        color = "primary"
    else:
        app_type = "Apply on company website"
        steps = ["Visit company website", "Find careers page", "Submit application"]
        icon = "fas fa-globe"
        color = "info"

    step_items = [html.Li(step) for step in steps]

    return html.Div(
        [
            html.H6([html.I(className=f"{icon} me-2"), "Application Process"], className="mb-2"),
            html.P(app_type, className="text-muted mb-2"),
            html.Ol(step_items, className="small text-muted"),
        ]
    )


def create_enhanced_job_modal():
    """Create enhanced job modal with comprehensive information"""
    return dbc.Modal(
        [
            dbc.ModalHeader([dbc.ModalTitle("Job Details", id="enhanced-job-modal-title")]),
            dbc.ModalBody(
                [
                    # Top section - Basic info and salary
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(id="job-modal-title-display", className="mb-2"),
                                    html.Div(id="job-modal-company-display", className="mb-2"),
                                    html.Div(id="job-modal-location-display", className="mb-2"),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    html.Div(id="job-modal-salary-display", className="mb-2"),
                                    html.Div(id="job-modal-work-arrangement", className="mb-2"),
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-3",
                    ),
                    html.Hr(),
                    # Company information panel
                    html.Div(id="job-modal-company-info", className="mb-3"),
                    html.Hr(),
                    # Skills breakdown
                    html.Div(id="job-modal-skills-breakdown", className="mb-3"),
                    html.Hr(),
                    # Job description
                    html.H6("📄 Job Description"),
                    html.Div(
                        id="job-modal-description-display",
                        className="bg-light p-3 rounded mb-3",
                        style={"max-height": "300px", "overflow-y": "auto"},
                    ),
                    html.Hr(),
                    # Application process
                    html.Div(id="job-modal-application-process", className="mb-3"),
                    html.Hr(),
                    # Notes and status section
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H6("📝 Your Notes"),
                                    dcc.Textarea(
                                        id="enhanced-job-modal-notes",
                                        placeholder="Add your thoughts about this position...",
                                        style={"width": "100%", "height": 100},
                                    ),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    html.H6("🔄 Application Status"),
                                    dcc.Dropdown(
                                        id="enhanced-job-modal-status",
                                        options=[
                                            {"label": "🆕 Not Applied", "value": "new"},
                                            {"label": "🔖 Bookmarked", "value": "bookmarked"},
                                            {"label": "📤 Applied", "value": "applied"},
                                            {
                                                "label": "📞 Interview Scheduled",
                                                "value": "interview",
                                            },
                                            {"label": "✅ Offer Received", "value": "offer"},
                                            {"label": "❌ Rejected", "value": "rejected"},
                                        ],
                                        placeholder="Update status...",
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
                        [html.I(className="fas fa-save me-1"), "Save Notes"],
                        id="enhanced-job-modal-save",
                        color="success",
                        className="me-2",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-external-link-alt me-1"), "Apply Now"],
                        id="enhanced-job-modal-apply",
                        color="primary",
                        className="me-2",
                    ),
                    dbc.Button("Close", id="enhanced-job-modal-close", color="secondary"),
                ]
            ),
        ],
        id="enhanced-job-modal",
        size="xl",
        is_open=False,
    )


def format_job_for_enhanced_display(job_data):
    """Format job data for the enhanced display components"""
    return {
        "salary_display": create_salary_display(job_data.get("salary")),
        "skills_breakdown": create_skills_breakdown(
            job_data.get("description", ""), job_data.get("skills", [])
        ),
        "company_info": create_company_info_panel(
            job_data.get("company"), job_data.get("location")
        ),
        "work_arrangement": create_work_arrangement_display(
            job_data.get("location", ""), job_data.get("description", "")
        ),
        "application_process": create_application_process_info(
            job_data.get("job_url"), job_data.get("company")
        ),
    }
