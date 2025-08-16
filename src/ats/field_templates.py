"""
ATS Field Templates and Login Requirements

This module provides standardized templates for interacting with various
Applicant Tracking Systems (ATS). Each template defines the necessary login
credentials and form fields required to automate job applications on that
platform.

The data is structured to be easily consumed by the JobApplier module.
Moved from src/ats_field_templates.py for better organization.
"""

from typing import Dict, List, Any

# ATS_TEMPLATES defines the structure for different Applicant Tracking Systems.
# Each key represents an ATS (e.g., "indeed", "workday") and contains:
#   - "login": A list of fields required for user authentication.
#   - "fields": A list of common form fields for submitting an application.
#
# Each field is a dictionary with:
#   - "name": The internal key for the field.
#   - "label": The human-readable label for the field.
#   - "type": The input type (text, email, password, select, etc.).
#   - "required": Whether the field is mandatory.
#   - "options": For select fields, the available options.

ATS_TEMPLATES = {
    "workday": {
        "login": [
            {"name": "username", "label": "Username/Email", "type": "email", "required": True},
            {"name": "password", "label": "Password", "type": "password", "required": True}
        ],
        "fields": [
            {"name": "first_name", "label": "First Name", "type": "text", "required": True},
            {"name": "last_name", "label": "Last Name", "type": "text", "required": True},
            {"name": "email", "label": "Email Address", "type": "email", "required": True},
            {"name": "phone", "label": "Phone Number", "type": "tel", "required": True},
            {"name": "address", "label": "Address", "type": "text", "required": False},
            {"name": "city", "label": "City", "type": "text", "required": False},
            {"name": "state", "label": "State/Province", "type": "text", "required": False},
            {"name": "postal_code", "label": "Postal Code", "type": "text", "required": False},
            {"name": "country", "label": "Country", "type": "select", "required": True, 
             "options": ["Canada", "United States", "Other"]},
            {"name": "resume", "label": "Resume", "type": "file", "required": True},
            {"name": "cover_letter", "label": "Cover Letter", "type": "file", "required": False}
        ]
    },
    
    "greenhouse": {
        "login": [
            {"name": "email", "label": "Email", "type": "email", "required": True},
            {"name": "password", "label": "Password", "type": "password", "required": True}
        ],
        "fields": [
            {"name": "first_name", "label": "First Name", "type": "text", "required": True},
            {"name": "last_name", "label": "Last Name", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "email", "required": True},
            {"name": "phone", "label": "Phone", "type": "tel", "required": True},
            {"name": "resume", "label": "Resume", "type": "file", "required": True},
            {"name": "cover_letter", "label": "Cover Letter", "type": "file", "required": False},
            {"name": "linkedin", "label": "LinkedIn Profile", "type": "url", "required": False},
            {"name": "website", "label": "Personal Website", "type": "url", "required": False}
        ]
    },
    
    "bamboohr": {
        "login": [
            {"name": "email", "label": "Email Address", "type": "email", "required": True},
            {"name": "password", "label": "Password", "type": "password", "required": True}
        ],
        "fields": [
            {"name": "first_name", "label": "First Name", "type": "text", "required": True},
            {"name": "last_name", "label": "Last Name", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "email", "required": True},
            {"name": "phone", "label": "Phone Number", "type": "tel", "required": True},
            {"name": "address", "label": "Street Address", "type": "text", "required": False},
            {"name": "city", "label": "City", "type": "text", "required": False},
            {"name": "state", "label": "State", "type": "text", "required": False},
            {"name": "zip_code", "label": "ZIP Code", "type": "text", "required": False},
            {"name": "resume", "label": "Resume", "type": "file", "required": True}
        ]
    },
    
    "lever": {
        "login": [
            {"name": "email", "label": "Email", "type": "email", "required": True},
            {"name": "password", "label": "Password", "type": "password", "required": True}
        ],
        "fields": [
            {"name": "name", "label": "Full Name", "type": "text", "required": True},
            {"name": "email", "label": "Email", "type": "email", "required": True},
            {"name": "phone", "label": "Phone", "type": "tel", "required": False},
            {"name": "resume", "label": "Resume", "type": "file", "required": True},
            {"name": "cover_letter", "label": "Cover Letter", "type": "file", "required": False},
            {"name": "linkedin", "label": "LinkedIn URL", "type": "url", "required": False}
        ]
    },
    
    "icims": {
        "login": [
            {"name": "username", "label": "Username", "type": "text", "required": True},
            {"name": "password", "label": "Password", "type": "password", "required": True}
        ],
        "fields": [
            {"name": "first_name", "label": "First Name", "type": "text", "required": True},
            {"name": "last_name", "label": "Last Name", "type": "text", "required": True},
            {"name": "email", "label": "Email Address", "type": "email", "required": True},
            {"name": "phone", "label": "Phone Number", "type": "tel", "required": True},
            {"name": "address1", "label": "Address Line 1", "type": "text", "required": False},
            {"name": "address2", "label": "Address Line 2", "type": "text", "required": False},
            {"name": "city", "label": "City", "type": "text", "required": False},
            {"name": "state", "label": "State", "type": "text", "required": False},
            {"name": "postal_code", "label": "Postal Code", "type": "text", "required": False},
            {"name": "resume", "label": "Resume", "type": "file", "required": True}
        ]
    }
}

def get_ats_template(ats_name: str) -> Dict[str, Any]:
    """
    Get the template for a specific ATS.
    
    Args:
        ats_name: Name of the ATS (e.g., 'workday', 'greenhouse')
        
    Returns:
        Dictionary containing login and field templates for the ATS
    """
    return ATS_TEMPLATES.get(ats_name.lower(), {})

def get_available_ats() -> List[str]:
    """
    Get list of available ATS templates.
    
    Returns:
        List of ATS names that have templates defined
    """
    return list(ATS_TEMPLATES.keys())

def validate_ats_data(ats_name: str, data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate data against ATS template requirements.
    
    Args:
        ats_name: Name of the ATS
        data: Data to validate
        
    Returns:
        Dictionary with 'missing' and 'invalid' field lists
    """
    template = get_ats_template(ats_name)
    if not template:
        return {"missing": [], "invalid": [f"Unknown ATS: {ats_name}"]}
    
    missing = []
    invalid = []
    
    # Check required fields
    for field in template.get("fields", []):
        if field["required"] and field["name"] not in data:
            missing.append(field["name"])
    
    # Check field types (basic validation)
    for field_name, value in data.items():
        field_def = next((f for f in template.get("fields", []) if f["name"] == field_name), None)
        if field_def:
            if field_def["type"] == "email" and "@" not in str(value):
                invalid.append(f"{field_name}: Invalid email format")
            elif field_def["type"] == "file" and not value:
                invalid.append(f"{field_name}: File required")
    
    return {"missing": missing, "invalid": invalid}