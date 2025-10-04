#!/usr/bin/env python3
"""
Production-Grade Resume Parser - Config-Based, Multi-Industry Support

Architecture:
- External JSON configs for skills, patterns, rules
- Dictionary/Set-based lookups for O(1) performance
- Caching to avoid repeated file loads
- Extensible: Add new industries without code changes

Usage:
    from src.utils.resume_parser_v2 import ResumeParserV2
    
    parser = ResumeParserV2()
    data = parser.parse_resume("resume.docx")
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from functools import lru_cache
from docx import Document

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class ResumeParserV2:
    """
    Production-grade resume parser with external configuration.
    
    Features:
    - Config-driven: All skills/patterns in JSON files
    - Fast: Uses sets/dicts for O(1) lookups
    - Scalable: Add industries without code changes
    - Cached: Configs loaded once, reused
    """
    
    def __init__(self, config_dir: str = "config"):
        """Initialize parser and load configurations."""
        self.config_dir = Path(config_dir)
        
        # Load configurations (cached)
        self.skills_db = self._load_skills_database()
        self.parsing_config = self._load_parsing_config()
        
        # Build fast lookup structures
        self._build_skill_sets()
        self._build_role_patterns()
    
    @lru_cache(maxsize=1)
    def _load_skills_database(self) -> Dict[str, Any]:
        """Load skills database from JSON (cached)."""
        config_path = self.config_dir / "skills_database.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Skills database not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @lru_cache(maxsize=1)
    def _load_parsing_config(self) -> Dict[str, Any]:
        """Load parsing configuration from JSON (cached)."""
        config_path = self.config_dir / "resume_parsing_config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Parsing config not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _build_skill_sets(self):
        """Build fast lookup sets for skills (O(1) lookups)."""
        self.skill_lookup = {}  # skill_lower -> (display_name, industry)
        
        for industry_key, industry_data in self.skills_db['industries'].items():
            for skill in industry_data['skills']:
                skill_lower = skill.lower()
                self.skill_lookup[skill_lower] = (skill, industry_key)
        
        # Build capitalization lookup
        self.uppercase_skills = set(
            s.lower() for s in self.skills_db['capitalization_rules']['uppercase']
        )
        self.preserve_skills = {
            s.lower(): s for s in self.skills_db['capitalization_rules']['preserve']
        }
    
    def _build_role_patterns(self):
        """Build role detection patterns for fast matching."""
        self.role_patterns = {}  # industry -> set of patterns
        
        for industry_key, industry_data in self.skills_db['industries'].items():
            patterns = industry_data.get('role_patterns', [])
            self.role_patterns[industry_key] = set(p.lower() for p in patterns)
    
    def parse_resume(self, resume_path: str) -> Dict[str, Any]:
        """
        Parse resume and extract structured data.
        
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
        
        # Extract basic info
        basic_info = {
            'raw_text': text,
            'name': self._extract_name(text),
            'email': self._extract_email(text),
            'phone': self._extract_phone(text),
            'location': self._extract_location(text),
        }
        
        # Extract skills (fast O(1) lookups)
        skills_data = self._extract_skills_fast(text)
        
        # Detect industry/role
        industry_scores = self._detect_industries(text, skills_data)
        primary_industry = max(industry_scores, key=industry_scores.get) if industry_scores else None
        
        # Extract sections
        sections = {
            'experience': self._extract_section(text, 'experience'),
            'education': self._extract_section(text, 'education'),
            'experience_level': self._detect_experience_level(text),
        }
        
        # Generate keywords based on detected industry
        keywords = self._generate_keywords(primary_industry, text)
        
        # Combine all results
        result = {
            **basic_info,
            'skills': skills_data['skills'],
            'skills_by_industry': skills_data['by_industry'],
            'primary_industry': primary_industry,
            'industry_scores': industry_scores,
            'job_role': self._get_job_role_label(primary_industry),
            'keywords': keywords,
            **sections
        }
        
        return result
    
    def _extract_skills_fast(self, text: str) -> Dict[str, Any]:
        """
        Extract skills using fast dictionary lookups (O(1) per skill check).
        
        Returns dict with:
        - skills: List of found skills (display names)
        - by_industry: Dict of industry -> skills
        """
        text_lower = text.lower()
        found_skills = set()
        by_industry = {}
        
        # Single pass through text for all skills (very efficient)
        for skill_lower, (display_name, industry) in self.skill_lookup.items():
            if skill_lower in text_lower:
                # Apply capitalization rules
                formatted_skill = self._format_skill_name(skill_lower, display_name)
                found_skills.add(formatted_skill)
                
                # Group by industry
                if industry not in by_industry:
                    by_industry[industry] = []
                by_industry[industry].append(formatted_skill)
        
        return {
            'skills': sorted(list(found_skills)),
            'by_industry': by_industry
        }
    
    def _format_skill_name(self, skill_lower: str, display_name: str) -> str:
        """Apply capitalization rules to skill names."""
        if skill_lower in self.uppercase_skills:
            return skill_lower.upper()
        elif skill_lower in self.preserve_skills:
            return self.preserve_skills[skill_lower]
        else:
            return display_name
    
    def _detect_industries(self, text: str, skills_data: Dict) -> Dict[str, float]:
        """
        Detect industries based on role patterns and skills.
        
        Returns dict of industry -> score
        """
        text_lower = text.lower()
        scores = {}
        
        # Score based on role patterns
        for industry, patterns in self.role_patterns.items():
            pattern_count = sum(1 for pattern in patterns if pattern in text_lower)
            
            # Score based on skills found
            skill_count = len(skills_data['by_industry'].get(industry, []))
            
            # Combined score (weighted)
            scores[industry] = (pattern_count * 2) + skill_count
        
        # Filter out zero scores
        return {k: v for k, v in scores.items() if v > 0}
    
    def _get_job_role_label(self, industry_key: Optional[str]) -> str:
        """Get human-readable job role label from industry key."""
        if not industry_key:
            return "General"
        
        industry_data = self.skills_db['industries'].get(industry_key, {})
        return industry_data.get('name', industry_key.replace('_', ' ').title())
    
    def _generate_keywords(self, industry_key: Optional[str], text: str) -> List[str]:
        """Generate job search keywords based on detected industry."""
        if not industry_key:
            return ["Specialist", "Coordinator", "Manager"]
        
        industry_data = self.skills_db['industries'].get(industry_key, {})
        return industry_data.get('keywords', [])
    
    def _extract_name(self, text: str) -> str:
        """Extract name from resume (usually first non-empty line)."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            first_line = lines[0]
            # Clean up if it's all caps
            if first_line.isupper() and len(first_line.split()) <= 4:
                return first_line.title()
            return first_line
        return ""
    
    def _extract_email(self, text: str) -> str:
        """Extract email address using configured pattern."""
        pattern = self.parsing_config['email_pattern']
        matches = re.findall(pattern, text)
        return matches[0] if matches else ""
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number using configured patterns."""
        for phone_config in self.parsing_config['phone_patterns']:
            pattern = phone_config['pattern']
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return ""
    
    def _extract_location(self, text: str) -> str:
        """Extract location using configured location patterns."""
        # Check Canada
        provinces = self.parsing_config['location_patterns']['canada']['provinces']
        for line in text.split('\n')[:10]:
            for prov in provinces:
                if prov in line:
                    match = re.search(r'([A-Za-z\s]+),\s*(' + prov + r')', line)
                    if match:
                        return match.group(0).strip()
        
        # Check USA
        states_abbr = self.parsing_config['location_patterns']['usa']['states_abbr']
        states_full = self.parsing_config['location_patterns']['usa']['states_full']
        
        for line in text.split('\n')[:10]:
            # Check abbreviations
            for state in states_abbr:
                if state in line:
                    match = re.search(r'([A-Za-z\s]+),\s*(' + state + r')', line)
                    if match:
                        return match.group(0).strip()
            
            # Check full names
            for state in states_full:
                if state in line:
                    match = re.search(r'([A-Za-z\s]+),\s*(' + state + r')', line)
                    if match:
                        return match.group(0).strip()
        
        return ""
    
    def _extract_section(self, text: str, section_type: str) -> str:
        """Extract a specific section from resume."""
        headers = self.parsing_config['section_headers'].get(section_type, [])
        lines = text.split('\n')
        
        # Find section start
        section_start = -1
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if any(header in line_lower for header in headers):
                section_start = i
                break
        
        if section_start == -1:
            return ""
        
        # Extract lines (30 for experience, 10 for others)
        max_lines = 30 if section_type == 'experience' else 10
        section_lines = []
        
        # Get other section headers to know when to stop
        all_headers = []
        for headers_list in self.parsing_config['section_headers'].values():
            all_headers.extend(headers_list)
        
        for i in range(section_start, min(section_start + max_lines, len(lines))):
            line = lines[i].strip()
            line_lower = line.lower()
            
            # Stop at next major section
            if i > section_start + 2 and any(h in line_lower for h in all_headers):
                break
            section_lines.append(line)
        
        return "\n".join(section_lines)
    
    def _detect_experience_level(self, text: str) -> str:
        """Detect experience level using configured rules."""
        text_lower = text.lower()
        
        # Try all patterns
        years = 0
        for pattern_config in self.parsing_config['experience_level_rules']['patterns']:
            pattern = pattern_config['pattern']
            group = pattern_config['group']
            
            matches = re.findall(pattern, text_lower)
            if matches:
                years = max(years, int(matches[0]))
        
        # Classify based on configured rules
        classifications = self.parsing_config['experience_level_rules']['classification']
        
        for level_key, level_config in classifications.items():
            if level_config['min'] <= years < level_config['max']:
                return level_config['label']
        
        return "Junior"  # Default


def parse_resume(resume_path: str) -> Dict[str, Any]:
    """
    Simple function to parse a resume (uses config-based parser).
    
    Usage:
        from src.utils.resume_parser_v2 import parse_resume
        
        data = parse_resume("resume.docx")
        print(f"Name: {data['name']}")
        print(f"Industry: {data['primary_industry']}")
        print(f"Skills: {data['skills'][:5]}")
        print(f"Keywords: {data['keywords'][:3]}")
    """
    parser = ResumeParserV2()
    return parser.parse_resume(resume_path)


if __name__ == "__main__":
    import sys
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
    else:
        resume_path = "profiles/Nirajan/Nirajan_Khadka_Resume.docx"
    
    console.print(f"\n[bold blue]🔍 Parsing Resume:[/bold blue] {resume_path}\n")
    
    try:
        data = parse_resume(resume_path)
        
        # Basic Info Table
        table = Table(title="📋 Extracted Information", show_header=True)
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="green")
        
        table.add_row("Name", data['name'])
        table.add_row("Email", data['email'])
        table.add_row("Phone", data['phone'])
        table.add_row("Location", data['location'])
        table.add_row("Primary Industry", data['job_role'])
        table.add_row("Experience Level", data['experience_level'])
        table.add_row("Skills Found", str(len(data['skills'])))
        
        console.print(table)
        
        # Skills by Industry
        if data['skills_by_industry']:
            console.print("\n[bold cyan]💼 Skills by Industry:[/bold cyan]")
            for industry, skills in data['skills_by_industry'].items():
                console.print(f"  [yellow]{industry}:[/yellow] {', '.join(skills[:5])}")
        
        # Top Keywords
        console.print(f"\n[bold cyan]🔑 Top Keywords:[/bold cyan]")
        for keyword in data['keywords'][:5]:
            console.print(f"  • {keyword}")
        
        # Industry Scores
        if data['industry_scores']:
            console.print(f"\n[bold cyan]📊 Industry Match Scores:[/bold cyan]")
            for industry, score in sorted(data['industry_scores'].items(), key=lambda x: x[1], reverse=True)[:3]:
                console.print(f"  {industry}: {score}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
