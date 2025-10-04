#!/usr/bin/env python3
"""
Resume Parser Utility - Extract structured data from resume files

Simple utility to extract text and basic information from resumes.
Can be used standalone or integrated into profile creation workflow.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from docx import Document

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class ResumeParser:
    """Parse resume files and extract structured information."""
    
    def __init__(self):
        self.data_analyst_terms = [
            'data analyst', 'business analyst', 'analytics', 'data science',
            'power bi', 'tableau', 'sql', 'excel', 'reporting', 'dashboard',
            'bi analyst', 'intelligence analyst', 'insights analyst'
        ]
        
        self.developer_terms = [
            'software developer', 'software engineer', 'programmer',
            'full stack', 'backend', 'frontend', 'web developer'
        ]
        
        self.agriculture_terms = [
            'greenhouse', 'farming', 'agriculture', 'cultivation', 'grower',
            'crop', 'horticulture', 'hydroponics', 'ipm', 'fertigation',
            'irrigation', 'pest management', 'organic farming'
        ]
        
        self.healthcare_terms = [
            'nurse', 'doctor', 'medical', 'healthcare', 'clinical',
            'patient care', 'hospital', 'medical records'
        ]
    
    def parse_resume(self, resume_path: str) -> Dict[str, Any]:
        """
        Parse resume and return structured data.
        
        Args:
            resume_path: Path to resume file (.docx or .pdf)
            
        Returns:
            Dictionary with extracted information
        """
        path = Path(resume_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Resume not found: {resume_path}")
        
        # Extract text
        if path.suffix.lower() == '.docx':
            text = self._extract_from_docx(path)
        elif path.suffix.lower() == '.pdf':
            text = self._extract_from_pdf(path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        # Parse the text
        return self._parse_text(text)
    
    def _extract_from_docx(self, path: Path) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(path)
            return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        except Exception as e:
            raise ValueError(f"Error reading DOCX: {e}")
    
    def _extract_from_pdf(self, path: Path) -> str:
        """Extract text from PDF file."""
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber not available. Install with: pip install pdfplumber")
        
        try:
            text = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            return "\n".join(text)
        except Exception as e:
            raise ValueError(f"Error reading PDF: {e}")
    
    def _parse_text(self, text: str) -> Dict[str, Any]:
        """Parse resume text and extract structured information."""
        
        result = {
            'raw_text': text,
            'name': self._extract_name(text),
            'email': self._extract_email(text),
            'phone': self._extract_phone(text),
            'location': self._extract_location(text),
            'skills': self._extract_skills(text),
            'experience': self._extract_experience_section(text),
            'education': self._extract_education(text),
            'job_role': self._detect_job_role(text),
            'experience_level': self._detect_experience_level(text),
            'keywords': self._generate_keywords(text),
        }
        
        return result
    
    def _extract_name(self, text: str) -> str:
        """Extract name from resume (usually first non-empty line)."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            # First line is usually the name
            first_line = lines[0]
            # Clean up if it's all caps
            if first_line.isupper() and len(first_line.split()) <= 4:
                return first_line.title()
            return first_line
        return ""
    
    def _extract_email(self, text: str) -> str:
        """Extract email address."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else ""
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number."""
        # Canadian/US phone patterns
        patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',    # (123) 456-7890
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return ""
    
    def _extract_location(self, text: str) -> str:
        """Extract location (city, province/state)."""
        # Look for Canadian provinces
        provinces = ['ON', 'BC', 'AB', 'QC', 'MB', 'SK', 'NS', 'NB', 'PE', 'NL', 'NT', 'YT', 'NU']
        
        # Look for US states (common ones)
        us_states = ['NY', 'CA', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI', 
                     'New York', 'California', 'Texas', 'Florida', 'Illinois']
        
        for line in text.split('\n')[:10]:  # Check first 10 lines
            # Canadian provinces
            for prov in provinces:
                if prov in line:
                    match = re.search(r'([A-Za-z\s]+),\s*(' + prov + r')', line)
                    if match:
                        return match.group(0).strip()
            
            # US states
            for state in us_states:
                if state in line:
                    # Match city, state pattern
                    match = re.search(r'([A-Za-z\s]+),\s*(' + state + r')', line)
                    if match:
                        return match.group(0).strip()
        
        return ""
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical and domain-specific skills."""
        skills = []
        text_lower = text.lower()
        
        # Tech/Data skills
        tech_skills = [
            'python', 'sql', 'java', 'javascript', 'c++', 'c#', 'r', 'scala',
            'power bi', 'tableau', 'excel', 'pandas', 'numpy', 'scikit-learn',
            'tensorflow', 'pytorch', 'keras', 'spark', 'hadoop',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'git', 'mysql', 'postgresql', 'mongodb', 'oracle',
            'machine learning', 'deep learning', 'nlp', 'computer vision',
            'data analysis', 'data visualization', 'statistical analysis',
            'fastapi', 'flask', 'django', 'react', 'node.js', 'streamlit',
            'dax', 'powerquery'
        ]
        
        # Agriculture/Greenhouse skills
        agriculture_skills = [
            'greenhouse', 'hydroponics', 'ipm', 'integrated pest management',
            'fertigation', 'irrigation', 'climate control', 'argus', 'priva',
            'crop management', 'pest control', 'organic farming',
            'sustainable farming', 'horticulture', 'cultivation',
            'leafy greens', 'crop yield', 'plant health', 'biological control',
            'ph management', 'ec management', 'root-zone management',
            'production planning', 'quality control'
        ]
        
        # Healthcare skills
        healthcare_skills = [
            'patient care', 'medical records', 'healthcare', 'nursing',
            'clinical', 'diagnosis', 'treatment', 'emr', 'ehr',
            'hipaa', 'medical coding', 'cpr', 'first aid'
        ]
        
        # Business/Management skills
        business_skills = [
            'project management', 'agile', 'scrum', 'jira', 'leadership',
            'team management', 'budgeting', 'forecasting', 'strategic planning',
            'stakeholder management', 'crm', 'salesforce', 'sap', 'erp'
        ]
        
        # Combine all skill patterns
        all_skills = tech_skills + agriculture_skills + healthcare_skills + business_skills
        
        for skill in all_skills:
            if skill.lower() in text_lower:
                # Capitalize properly
                if skill in ['ipm', 'nlp', 'aws', 'gcp', 'emr', 'ehr', 'hipaa', 'cpr', 'crm', 'sap', 'erp', 'ph', 'ec']:
                    skills.append(skill.upper())
                elif skill in ['power bi', 'node.js', 'scikit-learn']:
                    skills.append(skill)
                else:
                    skills.append(skill.title())
        
        return list(set(skills))  # Remove duplicates
    
    def _extract_experience_section(self, text: str) -> str:
        """Extract experience section text."""
        lines = text.split('\n')
        
        # Find experience section
        exp_start = -1
        for i, line in enumerate(lines):
            if re.search(r'\b(work\s+)?experience\b', line.lower()):
                exp_start = i
                break
        
        if exp_start == -1:
            return ""
        
        # Extract next 30 lines or until next major section
        exp_lines = []
        for i in range(exp_start, min(exp_start + 30, len(lines))):
            line = lines[i].strip()
            # Stop at next major section
            if re.search(r'\b(education|skills|projects|certifications)\b', line.lower()) and i > exp_start + 3:
                break
            exp_lines.append(line)
        
        return "\n".join(exp_lines)
    
    def _extract_education(self, text: str) -> str:
        """Extract education information."""
        lines = text.split('\n')
        
        # Find education section
        edu_start = -1
        for i, line in enumerate(lines):
            if re.search(r'\beducation\b', line.lower()):
                edu_start = i
                break
        
        if edu_start == -1:
            return ""
        
        # Extract next 10 lines
        edu_lines = []
        for i in range(edu_start, min(edu_start + 10, len(lines))):
            edu_lines.append(lines[i].strip())
        
        return "\n".join(edu_lines)
    
    def _detect_job_role(self, text: str) -> str:
        """Detect primary job role from resume."""
        text_lower = text.lower()
        
        # Count occurrences of different role types
        analyst_count = sum(1 for term in self.data_analyst_terms if term in text_lower)
        dev_count = sum(1 for term in self.developer_terms if term in text_lower)
        agri_count = sum(1 for term in self.agriculture_terms if term in text_lower)
        health_count = sum(1 for term in self.healthcare_terms if term in text_lower)
        
        # Determine primary role
        counts = {
            'Data Analyst': analyst_count,
            'Software Developer': dev_count,
            'Agriculture/Greenhouse Specialist': agri_count,
            'Healthcare Professional': health_count
        }
        
        max_role = max(counts, key=counts.get)
        max_count = counts[max_role]
        
        # If no clear winner, return mixed
        if max_count == 0:
            return "General"
        elif max_count < 3:
            return "Mixed Role"
        else:
            return max_role
    
    def _detect_experience_level(self, text: str) -> str:
        """Detect experience level from resume."""
        text_lower = text.lower()
        
        # Look for years of experience
        year_patterns = [
            r'(\d+)\+?\s*years?\s+of\s+experience',
            r'experience\s*:\s*(\d+)\+?\s*years?',
        ]
        
        years = 0
        for pattern in year_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                years = max(years, int(matches[0]))
        
        # Classify
        if years == 0:
            return "Junior"
        elif years <= 2:
            return "Junior"
        elif years <= 5:
            return "Mid Level"
        else:
            return "Senior"
    
    def _generate_keywords(self, text: str) -> List[str]:
        """Generate job search keywords based on resume content."""
        keywords = []
        job_role = self._detect_job_role(text)
        
        if "Data Analyst" in job_role:
            keywords = [
                "Data Analyst",
                "Business Analyst",
                "Analytics Specialist",
                "Data Science Analyst",
                "BI Analyst",
                "Reporting Analyst",
                "Junior Data Analyst",
                "Python Data Analyst",
                "SQL Analyst"
            ]
        elif "Developer" in job_role:
            keywords = [
                "Software Developer",
                "Python Developer",
                "Software Engineer",
                "Backend Developer",
                "Application Developer"
            ]
        elif "Agriculture" in job_role or "Greenhouse" in job_role:
            keywords = [
                "Greenhouse Specialist",
                "Growing Specialist",
                "Greenhouse Grower",
                "Cultivation Specialist",
                "Horticulture Specialist",
                "Greenhouse Manager",
                "IPM Specialist",
                "Agriculture Specialist",
                "Hydroponics Specialist"
            ]
        elif "Healthcare" in job_role:
            keywords = [
                "Healthcare Professional",
                "Medical Assistant",
                "Nurse",
                "Clinical Specialist",
                "Patient Care Coordinator"
            ]
        else:
            keywords = [
                "Specialist",
                "Coordinator",
                "Manager",
                "Assistant"
            ]
        
        return keywords


def parse_resume_simple(resume_path: str) -> Dict[str, Any]:
    """
    Simple function to parse a resume file.
    
    Usage:
        from src.utils.resume_parser import parse_resume_simple
        
        data = parse_resume_simple("profiles/Nirajan/Nirajan_Khadka_Resume.docx")
        print(f"Name: {data['name']}")
        print(f"Role: {data['job_role']}")
        print(f"Skills: {', '.join(data['skills'][:5])}")
    
    Args:
        resume_path: Path to resume file
        
    Returns:
        Dictionary with extracted data
    """
    parser = ResumeParser()
    return parser.parse_resume(resume_path)


if __name__ == "__main__":
    # Test the parser
    import sys
    
    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
    else:
        resume_path = "profiles/Nirajan/Nirajan_Khadka_Resume.docx"
    
    print(f"Parsing: {resume_path}")
    data = parse_resume_simple(resume_path)
    
    print(f"\nExtracted Data:")
    print(f"Name: {data['name']}")
    print(f"Email: {data['email']}")
    print(f"Phone: {data['phone']}")
    print(f"Location: {data['location']}")
    print(f"Job Role: {data['job_role']}")
    print(f"Experience Level: {data['experience_level']}")
    print(f"\nSkills ({len(data['skills'])}): {', '.join(data['skills'][:10])}")
    print(f"\nKeywords: {', '.join(data['keywords'][:5])}")
