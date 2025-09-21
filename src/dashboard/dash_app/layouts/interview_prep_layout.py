"""
Interview Prep Layout - Help users prepare for job interviews
Company research, common questions, and preparation tools
"""
import dash_bootstrap_components as dbc
from dash import html, dcc


def create_interview_prep_header():
    """Create header for interview prep section"""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H2([
                            html.I(className="fas fa-user-tie me-3 text-primary"),
                            "Interview Preparation"
                        ], className="fw-bold mb-0"),
                        html.P("Prepare for your interviews with AI-powered insights",
                               className="text-muted mb-0")
                    ])
                ], md=8),
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-plus me-2"),
                            "Schedule Interview"
                        ], color="primary", size="sm"),
                        dbc.Button([
                            html.I(className="fas fa-download me-2"),
                            "Export Notes"
                        ], color="outline-info", size="sm")
                    ])
                ], md=4, className="d-flex justify-content-end align-items-center")
            ])
        ])
    ], className="mb-4 shadow-sm border-0")


def create_interview_calendar():
    """Create upcoming interviews calendar"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-calendar-alt me-2"),
                "Upcoming Interviews"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            html.Div(id="interview-calendar-content", children=[
                html.P("No upcoming interviews scheduled", 
                       className="text-muted text-center py-4")
            ])
        ])
    ], className="mb-4 shadow-sm border-0")


def create_company_research():
    """Create company research section"""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5([
                        html.I(className="fas fa-building me-2"),
                        "Company Research"
                    ], className="mb-0")
                ]),
                dbc.Col([
                    dbc.Input(
                        placeholder="Search company...",
                        id="company-search",
                        size="sm"
                    )
                ], md=4)
            ])
        ]),
        dbc.CardBody([
            dbc.Tabs([
                dbc.Tab(label="📊 Overview", tab_id="overview"),
                dbc.Tab(label="👥 Culture", tab_id="culture"),
                dbc.Tab(label="💰 Salary Info", tab_id="salary"),
                dbc.Tab(label="📈 Recent News", tab_id="news")
            ], id="company-research-tabs", active_tab="overview"),
            html.Div(id="company-research-content", className="mt-3")
        ])
    ], className="mb-4 shadow-sm border-0")


def create_interview_questions():
    """Create common interview questions section"""
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-question-circle me-2"),
                "Interview Questions & Preparation"
            ], className="mb-0")
        ]),
        dbc.CardBody([
            dbc.Tabs([
                dbc.Tab(label="🎯 Common Questions", tab_id="common"),
                dbc.Tab(label="💻 Technical", tab_id="technical"),
                dbc.Tab(label="🧠 Behavioral", tab_id="behavioral"),
                dbc.Tab(label="❓ Questions to Ask", tab_id="to-ask")
            ], id="questions-tabs", active_tab="common"),
            html.Div(id="questions-content", className="mt-3")
        ])
    ], className="mb-4 shadow-sm border-0")


def create_preparation_checklist():
    """Create interview preparation checklist"""
    checklist_items = [
        "Research the company and role",
        "Prepare STAR method examples",
        "Review your resume and portfolio",
        "Prepare questions to ask the interviewer",
        "Practice common technical questions",
        "Plan your outfit and route",
        "Prepare copies of documents",
        "Test video call setup (if virtual)"
    ]
    
    checklist = []
    for i, item in enumerate(checklist_items):
        checklist.append(
            dbc.Checklist(
                options=[{"label": item, "value": f"item_{i}"}],
                value=[],
                id=f"checklist-item-{i}",
                className="mb-2"
            )
        )
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-clipboard-check me-2"),
                "Preparation Checklist"
            ], className="mb-0")
        ]),
        dbc.CardBody(checklist)
    ], className="shadow-sm border-0")


def create_interview_prep_layout():
    """Create the complete interview prep layout"""
    return html.Div([
        # Header
        create_interview_prep_header(),
        
        # Main content
        dbc.Row([
            dbc.Col([
                # Interview calendar
                create_interview_calendar(),
                
                # Company research
                create_company_research(),
                
                # Interview questions
                create_interview_questions()
            ], md=8),
            
            dbc.Col([
                # Preparation checklist
                create_preparation_checklist()
            ], md=4)
        ]),
        
        # Storage
        dcc.Store(id="interview-prep-data"),
        
        # Custom CSS
        # Custom CSS - moved to external stylesheet
            .interview-card {
                transition: all 0.2s ease;
                border-radius: 8px !important;
            }
            .interview-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
            }
        """)
    ])


# Sample data for demonstration
def get_common_questions():
    """Get common interview questions by category"""
    return {
        "common": [
            "Tell me about yourself",
            "Why do you want to work here?",
            "What are your strengths and weaknesses?",
            "Where do you see yourself in 5 years?",
            "Why are you leaving your current job?"
        ],
        "technical": [
            "Explain your technical experience",
            "How do you stay updated with technology?",
            "Describe a challenging technical problem you solved",
            "What's your development process?",
            "How do you ensure code quality?"
        ],
        "behavioral": [
            "Describe a time you worked in a team",
            "Tell me about a time you failed",
            "How do you handle conflict?",
            "Describe a time you had to learn something new",
            "Tell me about a time you led a project"
        ],
        "to-ask": [
            "What does success look like in this role?",
            "What are the biggest challenges facing the team?",
            "How would you describe the company culture?",
            "What opportunities are there for growth?",
            "What do you enjoy most about working here?"
        ]
    }
