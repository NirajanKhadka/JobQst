"""
Intelligent Search Term Generator
Analyzes resume and profile to create optimized job search terms.
Balances specificity with comprehensiveness to avoid missing opportunities.
"""

import json
import re
from typing import Dict, List, Set, Tuple, Any
from pathlib import Path
from rich.console import Console
from collections import Counter

console = Console()


class IntelligentSearchGenerator:
    """Generate intelligent search terms based on resume analysis."""

    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.profile_path = Path(f"profiles/{profile_name}")
        self.profile = self._load_profile()
        self.resume_text = self._extract_resume_text()

    def _load_profile(self) -> Dict[str, Any]:
        """Load user profile."""
        profile_file = self.profile_path / f"{self.profile_name}.json"
        if profile_file.exists():
            with open(profile_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _extract_resume_text(self) -> str:
        """Extract text from resume file."""
        try:
            # Try PDF first
            pdf_path = self.profile_path / f"{self.profile_name}_Khadka_Resume.pdf"
            if pdf_path.exists():
                return self._extract_from_pdf(pdf_path)

            # Try DOCX
            docx_path = self.profile_path / f"{self.profile_name}_Khadka_Resume.docx"
            if docx_path.exists():
                return self._extract_from_docx(docx_path)

            # Fallback to profile data
            return self._extract_from_profile()

        except Exception as e:
            console.print(f"[yellow]⚠️ Resume extraction failed: {e}[/yellow]")
            return self._extract_from_profile()

    def _extract_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF resume."""
        try:
            import PyPDF2

            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except ImportError:
            console.print("[yellow]⚠️ PyPDF2 not available, trying DOCX[/yellow]")
            return ""
        except Exception as e:
            console.print(f"[yellow]⚠️ PDF extraction failed: {e}[/yellow]")
            return ""

    def _extract_from_docx(self, docx_path: Path) -> str:
        """Extract text from DOCX resume."""
        try:
            from docx import Document

            doc = Document(docx_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            console.print("[yellow]⚠️ python-docx not available, using profile data[/yellow]")
            return ""
        except Exception as e:
            console.print(f"[yellow]⚠️ DOCX extraction failed: {e}[/yellow]")
            return ""

    def _extract_from_profile(self) -> str:
        """Extract text from profile JSON as fallback."""
        text_parts = []

        # Add experience descriptions
        for exp in self.profile.get("experience", []):
            text_parts.append(exp.get("description", ""))
            text_parts.extend(exp.get("achievements", []))

        # Add project descriptions
        for project in self.profile.get("projects", []):
            text_parts.append(project.get("description", ""))
            text_parts.extend(project.get("achievements", []))

        # Add skills and keywords
        text_parts.extend(self.profile.get("skills", []))
        text_parts.extend(self.profile.get("keywords", []))

        return " ".join(text_parts)

    def analyze_technical_skills(self) -> Dict[str, List[str]]:
        """Analyze technical skills from resume and categorize them."""
        text = self.resume_text.lower()

        # Define skill categories with variations
        skill_categories = {
            "programming_languages": {
                "python": ["python", "py"],
                "javascript": ["javascript", "js", "node.js", "nodejs"],
                "sql": ["sql", "postgresql", "mysql", "sqlite"],
                "html_css": ["html", "css", "html5", "css3"],
            },
            "frameworks": {
                "react": ["react", "reactjs", "react.js"],
                "fastapi": ["fastapi", "fast api"],
                "django": ["django"],
                "flask": ["flask"],
                "express": ["express", "express.js"],
            },
            "databases": {
                "postgresql": ["postgresql", "postgres"],
                "mongodb": ["mongodb", "mongo"],
                "mysql": ["mysql"],
                "sqlite": ["sqlite"],
            },
            "cloud_devops": {
                "aws": ["aws", "amazon web services"],
                "docker": ["docker", "containerization"],
                "git": ["git", "github", "version control"],
            },
            "specializations": {
                "api_development": ["api", "rest api", "restful", "microservices"],
                "web_development": ["web development", "web applications"],
                "full_stack": ["full stack", "fullstack", "full-stack"],
            },
        }

        found_skills = {}
        for category, skills in skill_categories.items():
            found_skills[category] = []
            for skill, variations in skills.items():
                if any(var in text for var in variations):
                    found_skills[category].append(skill)

        return found_skills

    def extract_job_titles_from_experience(self) -> List[str]:
        """Extract job titles from experience section."""
        titles = []

        # From profile experience
        for exp in self.profile.get("experience", []):
            title = exp.get("title", "").lower()
            if title:
                titles.append(title)

        # From resume text
        text = self.resume_text.lower()

        # Common job title patterns
        title_patterns = [
            r"software developer",
            r"python developer",
            r"web developer",
            r"application developer",
            r"software engineer",
            r"python engineer",
            r"full stack developer",
            r"backend developer",
            r"frontend developer",
            r"junior developer",
            r"senior developer",
        ]

        for pattern in title_patterns:
            if re.search(pattern, text):
                titles.append(pattern.replace(r"", ""))

        return list(set(titles))  # Remove duplicates

    def generate_intelligent_search_terms(self) -> Dict[str, List[str]]:
        """Generate intelligent search terms based on resume analysis."""
        console.print("[cyan]🧠 Analyzing resume for intelligent search terms...[/cyan]")

        # Analyze skills
        skills = self.analyze_technical_skills()
        job_titles = self.extract_job_titles_from_experience()

        # Generate search terms by category
        search_terms = {
            "primary_roles": [],  # Main job titles to search for
            "skill_based": [],  # Technology + developer combinations
            "industry_specific": [],  # Industry-specific roles
            "level_based": [],  # Experience level variations
            "company_types": [],  # Different company type preferences
            "technology_combinations": [],  # Specific tech stack combinations
        }

        # Primary roles based on experience
        experience_level = self.profile.get("experience_level", "").lower()

        if "senior" in experience_level:
            search_terms["primary_roles"] = [
                "Senior Python Developer",
                "Senior Software Developer",
                "Senior Software Engineer",
                "Python Software Engineer",
                "Senior Application Developer",
            ]
        elif "mid" in experience_level or "intermediate" in experience_level:
            search_terms["primary_roles"] = [
                "Python Developer",
                "Software Developer",
                "Software Engineer",
                "Application Developer",
                "Python Software Engineer",
            ]
        else:
            search_terms["primary_roles"] = [
                "Python Developer",
                "Software Developer",
                "Junior Python Developer",
                "Application Developer",
                "Web Developer",
            ]

        # Skill-based combinations
        programming_langs = skills.get("programming_languages", [])
        frameworks = skills.get("frameworks", [])

        for lang in programming_langs:
            if lang == "python":
                search_terms["skill_based"].extend(
                    ["Python Developer", "Python Programmer", "Python Software Engineer"]
                )
            elif lang == "javascript":
                search_terms["skill_based"].extend(["JavaScript Developer", "Node.js Developer"])

        for framework in frameworks:
            if framework in ["django", "flask", "fastapi"]:
                search_terms["skill_based"].append(f"{framework.title()} Developer")
            elif framework == "react":
                search_terms["skill_based"].append("React Developer")

        # Industry-specific roles
        if any(skill in skills.get("specializations", []) for skill in ["api_development"]):
            search_terms["industry_specific"].extend(
                [
                    "API Developer",
                    "Backend API Developer",
                    "Microservices Developer",
                    "REST API Developer",
                ]
            )

        if "web_development" in skills.get("specializations", []):
            search_terms["industry_specific"].extend(
                ["Web Application Developer", "Web Developer", "Full Stack Web Developer"]
            )

        # Technology combinations (specific to your stack)
        cloud_skills = skills.get("cloud_devops", [])
        if "aws" in cloud_skills and "docker" in cloud_skills:
            search_terms["technology_combinations"].extend(
                ["Python AWS Developer", "Python Docker Developer", "Cloud Python Developer"]
            )

        if "python" in programming_langs:
            search_terms["technology_combinations"].extend(
                ["Python API Developer", "Python Web Developer", "Python Application Developer"]
            )

            # Add framework-specific combinations
            if "fastapi" in frameworks:
                search_terms["technology_combinations"].append("FastAPI Developer")
            if "django" in frameworks:
                search_terms["technology_combinations"].append("Django Developer")
            if "flask" in frameworks:
                search_terms["technology_combinations"].append("Flask Developer")

        # Level-based variations
        if "mid" in experience_level or "intermediate" in experience_level:
            search_terms["level_based"] = [
                "Mid Level Python Developer",
                "Intermediate Software Developer",
                "Python Developer 2-5 years",
                "Software Developer Mid Level",
            ]
        elif "senior" in experience_level:
            search_terms["level_based"] = [
                "Senior Python Developer",
                "Senior Software Developer",
                "Lead Python Developer",
            ]

        # Company type variations (more specific)
        search_terms["company_types"] = [
            "Python Developer Startup",
            "Software Developer Tech Company",
            "Python Engineer SaaS",
            "Application Developer Fintech",
        ]

        # Remove duplicates and empty terms
        for category in search_terms:
            search_terms[category] = list(set(filter(None, search_terms[category])))

        return search_terms

    def create_optimized_keyword_list(self) -> List[str]:
        """Create final optimized keyword list."""
        search_terms = self.generate_intelligent_search_terms()

        # Prioritize terms by relevance
        final_keywords = []

        # Add primary roles first (highest priority)
        final_keywords.extend(search_terms["primary_roles"][:5])

        # Add skill-based terms (high priority)
        final_keywords.extend(search_terms["skill_based"][:6])

        # Add technology combinations (high priority)
        final_keywords.extend(search_terms["technology_combinations"][:5])

        # Add industry-specific terms (medium priority)
        final_keywords.extend(search_terms["industry_specific"][:4])

        # Add level-based terms (medium priority)
        final_keywords.extend(search_terms["level_based"][:3])

        # Add company type terms (lower priority)
        final_keywords.extend(search_terms["company_types"][:2])

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in final_keywords:
            if keyword.lower() not in seen:
                seen.add(keyword.lower())
                unique_keywords.append(keyword)

        return unique_keywords[:20]  # Limit to top 20 for efficiency

    def update_profile_keywords(self) -> bool:
        """Update profile with intelligent keywords."""
        try:
            optimized_keywords = self.create_optimized_keyword_list()

            # Update profile
            self.profile["keywords"] = optimized_keywords

            # Save updated profile
            profile_file = self.profile_path / f"{self.profile_name}.json"
            with open(profile_file, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, indent=2)

            console.print(
                f"[green]✅ Updated profile with {len(optimized_keywords)} intelligent keywords[/green]"
            )
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to update profile: {e}[/red]")
            return False

    def get_analysis_report(self) -> Dict[str, Any]:
        """Get detailed analysis report."""
        skills = self.analyze_technical_skills()
        search_terms = self.generate_intelligent_search_terms()

        return {
            "technical_skills": skills,
            "search_terms_by_category": search_terms,
            "optimized_keywords": self.create_optimized_keyword_list(),
            "experience_level": self.profile.get("experience_level", "Not specified"),
            "resume_analyzed": len(self.resume_text) > 100,
        }


def generate_intelligent_keywords(profile_name: str) -> List[str]:
    """Convenience function to generate intelligent keywords."""
    generator = IntelligentSearchGenerator(profile_name)
    return generator.create_optimized_keyword_list()


def update_profile_with_intelligent_keywords(profile_name: str) -> bool:
    """Update profile with intelligent keywords."""
    generator = IntelligentSearchGenerator(profile_name)
    return generator.update_profile_keywords()


if __name__ == "__main__":
    # Test with Nirajan profile
    generator = IntelligentSearchGenerator("Nirajan")
    report = generator.get_analysis_report()

    console.print("[bold blue]🧠 Intelligent Search Term Analysis[/bold blue]")
    console.print(f"Resume analyzed: {report['resume_analyzed']}")
    console.print(f"Experience level: {report['experience_level']}")
    console.print(f"Optimized keywords: {len(report['optimized_keywords'])}")

    for keyword in report["optimized_keywords"]:
        console.print(f"  • {keyword}")
