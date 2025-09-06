"""
Profile Management UI Components for JobQst Dashboard
Visual profile editor and resume upload functionality
"""
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
import json
import os
from pathlib import Path


def create_profile_management_section():
    """Create the profile management UI section"""
    
    return html.Div([
        # Profile selection and creation
        dbc.Card([
            dbc.CardHeader("👤 Profile Management"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Current Profile", className="fw-semibold"),
                        dcc.Dropdown(
                            id="profile-selector",
                            placeholder="Select or create a profile...",
                            options=get_profile_options()
                        )
                    ], width=8),
                    dbc.Col([
                        dbc.Button(
                            "➕ New Profile",
                            id="new-profile-btn",
                            color="success",
                            className="w-100"
                        )
                    ], width=4)
                ])
            ])
        ], className="mb-4"),
        
        # Profile editor
        html.Div(id="profile-editor-container")
    ])


def create_profile_editor(profile_data=None):
    """Create the visual profile editor"""
    
    if profile_data is None:
        profile_data = get_default_profile_structure()
    
    return dbc.Card([
        dbc.CardHeader("✏️ Edit Profile"),
        dbc.CardBody([
            dbc.Tabs([
                dbc.Tab(
                    label="📝 Basic Info",
                    tab_id="basic-info",
                    children=create_basic_info_tab(profile_data)
                ),
                dbc.Tab(
                    label="💼 Skills & Experience", 
                    tab_id="skills",
                    children=create_skills_tab(profile_data)
                ),
                dbc.Tab(
                    label="📍 Preferences",
                    tab_id="preferences", 
                    children=create_preferences_tab(profile_data)
                ),
                dbc.Tab(
                    label="📄 Resume",
                    tab_id="resume",
                    children=create_resume_tab(profile_data)
                )
            ], id="profile-tabs", active_tab="basic-info")
        ])
    ])


def create_basic_info_tab(profile_data):
    """Create basic information tab"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Full Name", className="fw-semibold"),
                dbc.Input(
                    id="profile-name",
                    value=profile_data.get('name', ''),
                    placeholder="Enter your full name"
                ),
                
                html.Label("Email", className="fw-semibold mt-3"),
                dbc.Input(
                    id="profile-email",
                    type="email",
                    value=profile_data.get('email', ''),
                    placeholder="your.email@example.com"
                ),
                
                html.Label("Phone", className="fw-semibold mt-3"),
                dbc.Input(
                    id="profile-phone",
                    value=profile_data.get('phone', ''),
                    placeholder="+1 (555) 123-4567"
                )
            ], width=6),
            
            dbc.Col([
                html.Label("LinkedIn Profile", className="fw-semibold"),
                dbc.Input(
                    id="profile-linkedin",
                    value=profile_data.get('linkedin', ''),
                    placeholder="linkedin.com/in/yourname"
                ),
                
                html.Label("GitHub Profile", className="fw-semibold mt-3"),
                dbc.Input(
                    id="profile-github",
                    value=profile_data.get('github', ''),
                    placeholder="github.com/yourusername"
                ),
                
                html.Label("Portfolio Website", className="fw-semibold mt-3"),
                dbc.Input(
                    id="profile-portfolio",
                    value=profile_data.get('portfolio', ''),
                    placeholder="https://yourwebsite.com"
                )
            ], width=6)
        ])
    ])


def create_skills_tab(profile_data):
    """Create skills and experience tab"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Job Title/Role", className="fw-semibold"),
                dbc.Input(
                    id="profile-title",
                    value=profile_data.get('title', ''),
                    placeholder="e.g. Senior Data Scientist"
                ),
                
                html.Label("Years of Experience", className="fw-semibold mt-3"),
                dcc.Slider(
                    id="profile-experience",
                    min=0,
                    max=20,
                    step=1,
                    value=profile_data.get('experience', 3),
                    marks={i: f"{i}y" for i in range(0, 21, 2)},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                
                html.Label("Industry", className="fw-semibold mt-4"),
                dcc.Dropdown(
                    id="profile-industry",
                    value=profile_data.get('industry', ''),
                    options=[
                        {'label': 'Technology', 'value': 'technology'},
                        {'label': 'Finance', 'value': 'finance'},
                        {'label': 'Healthcare', 'value': 'healthcare'},
                        {'label': 'Education', 'value': 'education'},
                        {'label': 'Consulting', 'value': 'consulting'},
                        {'label': 'Marketing', 'value': 'marketing'},
                        {'label': 'Sales', 'value': 'sales'},
                        {'label': 'Other', 'value': 'other'}
                    ],
                    placeholder="Select your industry"
                )
            ], width=6),
            
            dbc.Col([
                html.Label("Technical Skills", className="fw-semibold"),
                dcc.Dropdown(
                    id="profile-tech-skills",
                    value=profile_data.get('tech_skills', []),
                    multi=True,
                    options=[
                        {'label': 'Python', 'value': 'python'},
                        {'label': 'JavaScript', 'value': 'javascript'},
                        {'label': 'React', 'value': 'react'},
                        {'label': 'Node.js', 'value': 'nodejs'},
                        {'label': 'SQL', 'value': 'sql'},
                        {'label': 'AWS', 'value': 'aws'},
                        {'label': 'Docker', 'value': 'docker'},
                        {'label': 'Machine Learning', 'value': 'ml'},
                        {'label': 'Data Analysis', 'value': 'data_analysis'},
                        {'label': 'API Development', 'value': 'api_dev'}
                    ],
                    placeholder="Select your technical skills"
                ),
                
                html.Label("Soft Skills", className="fw-semibold mt-3"),
                dcc.Dropdown(
                    id="profile-soft-skills",
                    value=profile_data.get('soft_skills', []),
                    multi=True,
                    options=[
                        {'label': 'Leadership', 'value': 'leadership'},
                        {'label': 'Communication', 'value': 'communication'},
                        {'label': 'Problem Solving', 'value': 'problem_solving'},
                        {'label': 'Project Management', 'value': 'project_mgmt'},
                        {'label': 'Team Collaboration', 'value': 'collaboration'},
                        {'label': 'Analytical Thinking', 'value': 'analytical'},
                        {'label': 'Creativity', 'value': 'creativity'},
                        {'label': 'Adaptability', 'value': 'adaptability'}
                    ],
                    placeholder="Select your soft skills"
                ),
                
                html.Label("Certifications", className="fw-semibold mt-3"),
                dbc.Textarea(
                    id="profile-certifications",
                    value=profile_data.get('certifications', ''),
                    placeholder="List your certifications (one per line)",
                    rows=3
                )
            ], width=6)
        ])
    ])


def create_preferences_tab(profile_data):
    """Create job preferences tab"""
    prefs = profile_data.get('job_preferences', {})
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Preferred Locations", className="fw-semibold"),
                dcc.Dropdown(
                    id="profile-locations",
                    value=prefs.get('locations', []),
                    multi=True,
                    options=[
                        {'label': 'Remote', 'value': 'remote'},
                        {'label': 'Toronto, ON', 'value': 'toronto'},
                        {'label': 'Vancouver, BC', 'value': 'vancouver'},
                        {'label': 'Montreal, QC', 'value': 'montreal'},
                        {'label': 'Calgary, AB', 'value': 'calgary'},
                        {'label': 'Ottawa, ON', 'value': 'ottawa'},
                        {'label': 'New York, NY', 'value': 'new_york'},
                        {'label': 'San Francisco, CA', 'value': 'san_francisco'},
                        {'label': 'Seattle, WA', 'value': 'seattle'}
                    ],
                    placeholder="Select preferred locations"
                ),
                
                html.Label("Job Types", className="fw-semibold mt-3"),
                dbc.Checklist(
                    id="profile-job-types",
                    value=prefs.get('job_types', ['full_time']),
                    options=[
                        {'label': 'Full-time', 'value': 'full_time'},
                        {'label': 'Part-time', 'value': 'part_time'},
                        {'label': 'Contract', 'value': 'contract'},
                        {'label': 'Freelance', 'value': 'freelance'},
                        {'label': 'Internship', 'value': 'internship'}
                    ]
                )
            ], width=6),
            
            dbc.Col([
                html.Label("Salary Range", className="fw-semibold"),
                dcc.RangeSlider(
                    id="profile-salary-range",
                    min=30000,
                    max=200000,
                    step=5000,
                    value=prefs.get('salary_range', [60000, 120000]),
                    marks={
                        30000: '$30k',
                        60000: '$60k', 
                        100000: '$100k',
                        150000: '$150k',
                        200000: '$200k'
                    },
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                
                html.Label("Company Size", className="fw-semibold mt-4"),
                dbc.Checklist(
                    id="profile-company-size",
                    value=prefs.get('company_size', []),
                    options=[
                        {'label': 'Startup (1-50)', 'value': 'startup'},
                        {'label': 'Small (51-200)', 'value': 'small'},
                        {'label': 'Medium (201-1000)', 'value': 'medium'},
                        {'label': 'Large (1000+)', 'value': 'large'},
                        {'label': 'Enterprise (5000+)', 'value': 'enterprise'}
                    ]
                ),
                
                html.Label("Work Style", className="fw-semibold mt-3"),
                dcc.Dropdown(
                    id="profile-work-style",
                    value=prefs.get('work_style', 'hybrid'),
                    options=[
                        {'label': 'Remote', 'value': 'remote'},
                        {'label': 'Hybrid', 'value': 'hybrid'},
                        {'label': 'On-site', 'value': 'onsite'},
                        {'label': 'Flexible', 'value': 'flexible'}
                    ]
                )
            ], width=6)
        ])
    ])


def create_resume_tab(profile_data):
    """Create resume upload and management tab"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Resume Upload", className="fw-semibold"),
                dcc.Upload(
                    id="resume-upload",
                    children=html.Div([
                        '📄 Drag and Drop or ',
                        html.A('Select a Resume File')
                    ]),
                    style={
                        'width': '100%',
                        'height': '100px',
                        'lineHeight': '100px',
                        'borderWidth': '2px',
                        'borderStyle': 'dashed',
                        'borderRadius': '10px',
                        'textAlign': 'center',
                        'margin': '10px 0',
                        'cursor': 'pointer'
                    },
                    multiple=False,
                    accept='.pdf,.doc,.docx'
                ),
                
                html.Div(id="resume-upload-status"),
                
                html.Label("Resume Summary", className="fw-semibold mt-3"),
                dbc.Textarea(
                    id="profile-summary",
                    value=profile_data.get('summary', ''),
                    placeholder="Write a brief professional summary...",
                    rows=4
                )
            ], width=12)
        ])
    ])


def get_profile_options():
    """Get available profile options"""
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        return []
    
    options = []
    for profile_file in profiles_dir.glob("*.json"):
        profile_name = profile_file.stem
        options.append({
            'label': profile_name.replace('_', ' ').title(),
            'value': profile_name
        })
    
    return options


def get_default_profile_structure():
    """Get default profile structure"""
    return {
        'name': '',
        'email': '',
        'phone': '',
        'linkedin': '',
        'github': '',
        'portfolio': '',
        'title': '',
        'experience': 3,
        'industry': '',
        'tech_skills': [],
        'soft_skills': [],
        'certifications': '',
        'summary': '',
        'job_preferences': {
            'locations': ['remote'],
            'job_types': ['full_time'],
            'salary_range': [60000, 120000],
            'company_size': [],
            'work_style': 'hybrid'
        }
    }
