"""
Core data models for AutoJobAgent.
"""
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from urllib.parse import urlparse

class JobStatus(str, Enum):
    """Status of a job application."""
    NEW = "new"
    MATCHED = "matched"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    OFFER = "offer"
    ARCHIVED = "archived"

class ATSProvider(str, Enum):
    """Supported ATS providers."""
    WORKDAY = "workday"
    ICIMS = "icims"
    GREENHOUSE = "greenhouse"
    BAMBOOHR = "bamboohr"
    LEVER = "lever"
    UNKNOWN = "unknown"

class JobPosting(BaseModel):
    """Job posting model."""
    id: str = Field(..., description="Unique identifier for the job")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    description: str = Field(..., description="Job description")
    url: str = Field(..., description="URL to the job posting")
    posted_date: Optional[datetime] = Field(None, description="When the job was posted")
    status: JobStatus = Field(default=JobStatus.NEW, description="Application status")
    source: str = Field(..., description="Source website (e.g., 'indeed', 'workday')")
    ats: Optional[ATSProvider] = Field(None, description="Detected ATS provider")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")
    
    @validator('ats', pre=True, always=True)
    def detect_ats(cls, v, values):
        """Detect ATS provider from URL if not specified."""
        if v is not None:
            return v
            
        url = values.get('url', '').lower()
        if 'workday' in url:
            return ATSProvider.WORKDAY
        elif 'icims' in url:
            return ATSProvider.ICIMS
        elif 'greenhouse' in url:
            return ATSProvider.GREENHOUSE
        elif 'bamboohr' in url:
            return ATSProvider.BAMBOOHR
        elif 'lever' in url:
            return ATSProvider.LEVER
        return ATSProvider.UNKNOWN

class Resume(BaseModel):
    """Resume model."""
    file_path: Path
    content: Optional[str] = None
    file_type: str = "pdf"  # pdf, docx, txt
    
    @validator('file_type')
    def validate_file_type(cls, v):
        """Validate file type."""
        if v.lower() not in {"pdf", "docx", "txt"}:
            raise ValueError("Unsupported file type. Must be 'pdf', 'docx', or 'txt'")
        return v.lower()

class CoverLetter(BaseModel):
    """Cover letter model."""
    file_path: Path
    content: Optional[str] = None
    file_type: str = "pdf"  # pdf, docx, txt
    
    @validator('file_type')
    def validate_file_type(cls, v):
        """Validate file type."""
        if v.lower() not in {"pdf", "docx", "txt"}:
            raise ValueError("Unsupported file type. Must be 'pdf', 'docx', or 'txt'")
        return v.lower()

class JobApplication(BaseModel):
    """Job application model."""
    job: JobPosting
    resume: Resume
    cover_letter: Optional[CoverLetter] = None
    status: JobStatus = JobStatus.NEW
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)

class UserProfile(BaseModel):
    """User profile model."""
    name: str
    email: str
    location: str
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Dict] = Field(default_factory=list)
    education: List[Dict] = Field(default_factory=list)
    preferences: Dict = Field(default_factory=dict)
    
    @validator('email')
    def validate_email(cls, v):
        """Basic email validation."""
        if '@' not in v:
            raise ValueError("Invalid email address")
        return v.lower()
    
    @validator('linkedin', 'github', 'portfolio', pre=True)
    def validate_urls(cls, v):
        """Validate URLs if provided."""
        if not v:
            return v
        if not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v
