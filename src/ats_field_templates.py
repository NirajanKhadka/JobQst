"""
ATS Field Templates and Login Requirements

This module provides standardized templates for interacting with various
Applicant Tracking Systems (ATS). Each template defines the necessary login
credentials and form fields required to automate job applications on that
platform.

The data is structured to be easily consumed by the JobApplier module.
"""

from typing import Dict, List, Any

# ATS_TEMPLATES defines the structure for different Applicant Tracking Systems.
# Each key represents an ATS (e.g., "indeed", "workday") and contains:
#   - "login": A list of fields required for user authentication.
#   - "fields": A list of common form fields for submitting an application.
#
# Each field is a dictionary with:
#   - "name": The internal key for the field.
#   - "prompt": A user-friendly string for interactive prompts.
#   - "type" (optional): Specifies the input type (e.g., "password").
ATS_TEMPLATES: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "indeed": {
        "login": [
            {"name": "email", "prompt": "Indeed Email"},
            {"name": "password", "prompt": "Indeed Password", "type": "password"}
        ],
        "fields": [
            {"name": "full_name", "prompt": "Full Name"},
            {"name": "email", "prompt": "Email Address"},
            {"name": "phone", "prompt": "Phone Number"},
            {"name": "resume", "prompt": "Resume File Path"},
            {"name": "cover_letter", "prompt": "Cover Letter File Path (optional)"},
            {"name": "work_authorization", "prompt": "Are you authorized to work in this country?"},
            {"name": "relocation", "prompt": "Are you willing to relocate?"},
        ]
    },
    "workday": {
        "login": [
            {"name": "email", "prompt": "Workday Email"},
            {"name": "password", "prompt": "Workday Password", "type": "password"}
        ],
        "fields": [
            {"name": "first_name", "prompt": "First Name"},
            {"name": "last_name", "prompt": "Last Name"},
            {"name": "email", "prompt": "Email Address"},
            {"name": "phone", "prompt": "Phone Number"},
            {"name": "resume", "prompt": "Resume File Path"},
            {"name": "cover_letter", "prompt": "Cover Letter File Path (optional)"},
            {"name": "address", "prompt": "Home Address"},
            {"name": "work_authorization", "prompt": "Are you authorized to work in this country?"},
            {"name": "salary_expectation", "prompt": "What is your salary expectation?"},
        ]
    },
    "greenhouse": {
        "login": [],  # Usually no login required for most jobs
        "fields": [
            {"name": "full_name", "prompt": "Full Name"},
            {"name": "email", "prompt": "Email Address"},
            {"name": "phone", "prompt": "Phone Number"},
            {"name": "resume", "prompt": "Resume File Path"},
            {"name": "cover_letter", "prompt": "Cover Letter File Path (optional)"},
            {"name": "linkedin", "prompt": "LinkedIn Profile URL (optional)"},
            {"name": "website", "prompt": "Personal Website (optional)"},
            {"name": "work_authorization", "prompt": "Are you authorized to work in this country?"},
        ]
    },
    "lever": {
        "login": [],  # Usually no login required
        "fields": [
            {"name": "full_name", "prompt": "Full Name"},
            {"name": "email", "prompt": "Email Address"},
            {"name": "phone", "prompt": "Phone Number"},
            {"name": "resume", "prompt": "Resume File Path"},
            {"name": "cover_letter", "prompt": "Cover Letter File Path (optional)"},
            {"name": "linkedin", "prompt": "LinkedIn Profile URL (optional)"},
            {"name": "website", "prompt": "Personal Website (optional)"},
            {"name": "work_authorization", "prompt": "Are you authorized to work in this country?"},
        ]
    }
}
