"""
Automated Profile Creator

Creates job search profiles automatically from resume files.
Supports PDF, DOC, DOCX, and TXT formats.
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class AutoProfileCreator:
    """Creates profiles automatically from resume files."""
    
    def __init__(self):
        self.keywords_config = self._load_keywords_config()
        self.profile_template = self._load_profile_template()
        
    def _load_keywords_config(self) -> Dict[str, Any]:
        """Load keywords configuration from config file."""
        try:
            config_path = Path("config/keywords.json")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load keywords config: {e}")
        
        # Fallback to basic keywords
        return {
            "domains": {
                "general": {
                    "skills": ["communication", "teamwork", "problem solving", "leadership"],
                    "tools": ["Microsoft Office", "Email", "Internet"],
                    "certifications": [],
                    "roles": ["manager", "specialist", "coordinator", "assistant"]
                }
            }
        }
    
    def _load_profile_template(self) -> Dict[str, Any]:
        """Load profile template."""
        try:
            template_path = Path("profiles/profile_template.json")
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load profile template: {e}")
        
        # Fallback template
        return {
            "name": "",
            "email": "",
            "skills": [],
            "keywords": [],
            "experience_level": "entry"
        }

    def create_profile_from_resume(self, resume_path: str, profile_name: str) -> Dict[str, Any]:
        """
        Create a job search profile from a resume file using the template system.
        
        Args:
            resume_path: Path to the resume file
            profile_name: Name for the new profile
            
        Returns:
            Dict with success status and extracted data
        """
        try:
            # Extract text from resume
            text = self._extract_text_from_file(resume_path)
            if not text:
                return {'success': False, 'error': 'Could not extract text from resume'}
            
            # Analyze the text
            analysis = self._analyze_resume_text(text)
            
            # Create profile from template
            profile = self._create_profile_from_template(profile_name, analysis, resume_path)
            
            # Save profile
            profile_dir = Path("profiles") / profile_name
            profile_dir.mkdir(parents=True, exist_ok=True)
            
            profile_file = profile_dir / "profile.json"
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)
            
            return {
                'success': True,
                'profile_path': str(profile_file),
                'source_resume': resume_path,
                'keywords': analysis['keywords'],
                'skills': analysis['skills'],
                'experience_level': analysis['experience_level'],
                'detected_domains': analysis['detected_domains'],
                'email': analysis['email'],
                'phone': analysis['phone'],
                'certifications': analysis['certifications'],
                'confidence': self._calculate_confidence(analysis)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_profile_from_template(self, profile_name: str, analysis: Dict[str, Any], resume_path: str) -> Dict[str, Any]:
        """Create profile using the template system."""
        # Start with template
        profile = self.profile_template.copy()
        
        # Auto-fill fields as specified in template
        auto_fill_fields = profile.get("template_notes", {}).get("auto_fill", [])
        
        for field_path in auto_fill_fields:
            self._set_nested_field(profile, field_path, analysis, resume_path)
        
        # Set metadata
        profile["metadata"]["source_resume"] = resume_path
        profile["metadata"]["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        profile["metadata"]["generated_by"] = "resume-extractor"
        
        return profile
    
    def _set_nested_field(self, profile: Dict, field_path: str, analysis: Dict[str, Any], resume_path: str):
        """Set a nested field in the profile based on the field path."""
        keys = field_path.split('.')
        current = profile
        
        # Navigate to the parent of the target field
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final field
        final_key = keys[-1]
        
        # Map field paths to analysis data
        field_mapping = {
            'name': analysis.get('name', ''),
            'email': analysis.get('email', ''),
            'phone': analysis.get('phone', ''),
            'skills': analysis.get('skills', []),
            'keywords': analysis.get('keywords', []),
            'experience_level': analysis.get('experience_level', 'entry'),
            'work_experience': self._format_work_experience(analysis.get('work_experience', [])),
            'education': self._format_education(analysis.get('education', [])),
            'certifications': analysis.get('certifications', []),
            'links': self._extract_links(analysis.get('raw_text', '')),
            'source_resume': resume_path,
            'generated_at': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if final_key in field_mapping:
            current[final_key] = field_mapping[final_key]
    
    def _format_work_experience(self, work_exp: List[Dict]) -> List[Dict]:
        """Format work experience for the template."""
        formatted = []
        for exp in work_exp:
            formatted.append({
                "title": exp.get('title', ''),
                "company": exp.get('company', ''),
                "start_date": "",  # User will fill
                "end_date": "",    # User will fill
                "location": "",    # User will fill
                "description": exp.get('description', '')
            })
        return formatted
    
    def _format_education(self, education: List[str]) -> List[Dict]:
        """Format education for the template."""
        formatted = []
        for edu in education:
            formatted.append({
                "degree": edu,
                "school": "",      # User will fill
                "start_date": "",  # User will fill
                "end_date": "",    # User will fill
                "notes": ""        # User will fill
            })
        return formatted
    
    def _extract_links(self, text: str) -> Dict[str, str]:
        """Extract social media and portfolio links."""
        links = {"linkedin": "", "portfolio": "", "github": ""}
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            links["linkedin"] = "https://" + linkedin_match.group()
        
        # GitHub
        github_pattern = r'github\.com/[\w-]+'
        github_match = re.search(github_pattern, text, re.IGNORECASE)
        if github_match:
            links["github"] = "https://" + github_match.group()
        
        # Portfolio (look for personal websites)
        portfolio_patterns = [
            r'https?://[\w.-]+\.(?:com|net|org|io|dev)',
            r'www\.[\w.-]+\.(?:com|net|org|io|dev)'
        ]
        for pattern in portfolio_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and 'linkedin' not in match.group().lower() and 'github' not in match.group().lower():
                links["portfolio"] = match.group()
                break
        
        return links
    
    def _calculate_confidence(self, analysis: Dict[str, Any]) -> str:
        """Calculate confidence level based on extracted data quality."""
        score = 0
        
        # Check for key information
        if analysis.get('name') and analysis['name'] != 'Unknown':
            score += 20
        if analysis.get('email'):
            score += 20
        if analysis.get('phone'):
            score += 10
        if len(analysis.get('keywords', [])) >= 5:
            score += 20
        if len(analysis.get('skills', [])) >= 3:
            score += 15
        if analysis.get('work_experience'):
            score += 15
        
        if score >= 80:
            return "high"
        elif score >= 50:
            return "medium"
        else:
            return "low"

    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file formats."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        
        file_ext = file_path.suffix.lower()
        
        try:
            if file_ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_ext in ['.doc', '.docx']:
                return self._extract_from_docx(file_path)
            elif file_ext == '.txt':
                return self._extract_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
        except Exception as e:
            # Fallback: try to read as text file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except:
                raise e

    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber not available. Install with: pip install pdfplumber")
        
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file."""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not available. Install with: pip install python-docx")
        
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text

    def _extract_from_txt(self, file_path: Path) -> str:
        """Extract text from TXT file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def _analyze_resume_text(self, text: str) -> Dict[str, Any]:
        """Analyze resume text to extract key information using domain-specific keywords."""
        text_lower = text.lower()
        
        # Extract keywords and skills from all domains
        all_keywords = []
        all_skills = []
        detected_domains = []
        
        for domain_name, domain_data in self.keywords_config.get("domains", {}).items():
            domain_keywords = []
            domain_skills = []
            
            # Check skills
            for skill in domain_data.get("skills", []):
                if self._fuzzy_match(skill.lower(), text_lower):
                    domain_skills.append(skill)
                    all_skills.append(skill)
            
            # Check tools
            for tool in domain_data.get("tools", []):
                if self._fuzzy_match(tool.lower(), text_lower):
                    domain_keywords.append(tool)
                    all_keywords.append(tool)
            
            # Check roles
            for role in domain_data.get("roles", []):
                if self._fuzzy_match(role.lower(), text_lower):
                    domain_keywords.append(role)
                    all_keywords.append(role)
            
            # If we found keywords in this domain, mark it as detected
            if domain_keywords or domain_skills:
                detected_domains.append(domain_name)
        
        # Remove duplicates while preserving order
        all_keywords = list(dict.fromkeys(all_keywords))
        all_skills = list(dict.fromkeys(all_skills))
        
        # Extract basic information
        name = self._extract_name(text)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        experience_level = self._determine_experience_level(text_lower)
        education = self._extract_education(text)
        years_experience = self._extract_years_experience(text)
        work_experience = self._extract_work_experience(text)
        certifications = self._extract_certifications(text)
        
        return {
            'name': name,
            'email': email,
            'phone': phone,
            'keywords': all_keywords,
            'skills': all_skills,
            'experience_level': experience_level,
            'education': education,
            'years_experience': years_experience,
            'work_experience': work_experience,
            'certifications': certifications,
            'detected_domains': detected_domains,
            'raw_text': text
        }
    
    def _fuzzy_match(self, keyword: str, text: str) -> bool:
        """Check if keyword exists in text with fuzzy matching."""
        # Direct match
        if keyword in text:
            return True
        
        # Check synonyms
        synonyms = self.keywords_config.get("synonyms", {}).get(keyword, [])
        for synonym in synonyms:
            if synonym.lower() in text:
                return True
        
        # Word boundary match for multi-word keywords
        import re
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from resume text."""
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',
            r'\+1[-.\s]?\d{3}[-.]?\d{3}[-.]?\d{4}'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return ""
    
    def _extract_work_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience entries."""
        # This is a simplified extraction - could be enhanced with NLP
        experience = []
        lines = text.split('\n')
        
        current_job = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for job titles (lines with common job keywords)
            job_indicators = ['manager', 'engineer', 'analyst', 'specialist', 'coordinator', 
                            'developer', 'director', 'supervisor', 'assistant', 'lead']
            
            if any(indicator in line.lower() for indicator in job_indicators):
                if current_job:
                    experience.append(current_job)
                current_job = {'title': line, 'company': '', 'description': ''}
            
            # Look for company names (lines with "Inc", "LLC", "Corp", etc.)
            elif any(indicator in line for indicator in ['Inc', 'LLC', 'Corp', 'Company', 'Ltd']):
                if current_job:
                    current_job['company'] = line
        
        if current_job:
            experience.append(current_job)
        
        return experience[:5]  # Limit to 5 entries
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications from all domains."""
        certifications = []
        text_lower = text.lower()
        
        for domain_data in self.keywords_config.get("domains", {}).values():
            for cert in domain_data.get("certifications", []):
                if self._fuzzy_match(cert.lower(), text_lower):
                    certifications.append(cert)
        
        return list(dict.fromkeys(certifications))  # Remove duplicates

    def _extract_name(self, text: str) -> str:
        """Extract name from resume text."""
        lines = text.split('\n')
        
        # Look for name in first few lines
        for line in lines[:5]:
            line = line.strip()
            if len(line.split()) >= 2 and len(line) < 50:
                # Check if it looks like a name (not email, phone, etc.)
                if not re.search(r'[@\d]', line) and not any(word.lower() in line.lower() 
                    for word in ['resume', 'cv', 'curriculum', 'address', 'phone', 'email']):
                    return line
        
        return "Unknown"

    def _extract_email(self, text: str) -> str:
        """Extract email from resume text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else ""

    def _determine_experience_level(self, text_lower: str) -> str:
        """Determine experience level from resume text."""
        if any(word in text_lower for word in ['senior', 'lead', 'principal', 'director', 'manager']):
            return 'senior'
        elif any(word in text_lower for word in ['mid-level', 'intermediate', '3 years', '4 years', '5 years']):
            return 'mid'
        elif any(word in text_lower for word in ['junior', 'entry', 'intern', 'graduate', 'new grad']):
            return 'entry'
        else:
            return 'mid'  # Default

    def _extract_education(self, text: str) -> List[str]:
        """Extract education information."""
        education = []
        education_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college', 'certification']
        
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in education_keywords):
                education.append(line.strip())
        
        return education[:3]  # Limit to 3 entries

    def _extract_years_experience(self, text: str) -> int:
        """Extract years of experience."""
        # Look for patterns like "5 years", "3+ years", etc.
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*years?\s*in',
            r'experience\s*:\s*(\d+)\+?\s*years?'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                return int(matches[0])
        
        return 0



