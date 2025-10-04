#!/usr/bin/env python3
"""
Resume Keyword Extractor
Extracts comprehensive keywords from a long resume for better job matching.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)


class ResumeKeywordExtractor:
    """Extracts keywords from resume text for job search optimization."""

    def __init__(self):
        # Common technical skills and keywords
        self.technical_skills = {
            "programming": [
                "python",
                "java",
                "javascript",
                "typescript",
                "c++",
                "c#",
                "php",
                "ruby",
                "go",
                "rust",
                "swift",
                "kotlin",
                "scala",
            ],
            "databases": [
                "sql",
                "mysql",
                "postgresql",
                "mongodb",
                "redis",
                "elasticsearch",
                "oracle",
                "sqlite",
                "dynamodb",
                "cassandra",
            ],
            "cloud": [
                "aws",
                "azure",
                "gcp",
                "docker",
                "kubernetes",
                "terraform",
                "jenkins",
                "gitlab",
                "github",
                "ci/cd",
            ],
            "data_science": [
                "pandas",
                "numpy",
                "scikit-learn",
                "tensorflow",
                "pytorch",
                "matplotlib",
                "seaborn",
                "jupyter",
                "r",
                "spark",
            ],
            "web_tech": [
                "html",
                "css",
                "react",
                "angular",
                "vue",
                "node.js",
                "django",
                "flask",
                "spring",
                "express",
            ],
            "tools": [
                "git",
                "linux",
                "bash",
                "powershell",
                "excel",
                "power bi",
                "tableau",
                "jira",
                "confluence",
                "slack",
            ],
            "methodologies": [
                "agile",
                "scrum",
                "kanban",
                "waterfall",
                "devops",
                "lean",
                "six sigma",
                "tdd",
                "bdd",
            ],
        }

        # Job titles and roles
        self.job_titles = [
            "data analyst",
            "data scientist",
            "business analyst",
            "software engineer",
            "developer",
            "data engineer",
            "machine learning engineer",
            "product manager",
            "project manager",
            "business intelligence analyst",
            "analytics engineer",
            "data architect",
            "database administrator",
            "systems analyst",
            "operations analyst",
            "financial analyst",
            "market analyst",
            "research analyst",
            "policy analyst",
            "process analyst",
            "quality analyst",
        ]

        # Industries and domains
        self.industries = [
            "finance",
            "healthcare",
            "technology",
            "retail",
            "manufacturing",
            "consulting",
            "education",
            "government",
            "non-profit",
            "media",
            "telecommunications",
            "energy",
            "transportation",
            "real estate",
            "insurance",
            "banking",
            "e-commerce",
            "logistics",
        ]

    def extract_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract keywords from resume text."""
        text = text.lower()

        extracted = {
            "technical_skills": [],
            "job_titles": [],
            "industries": [],
            "custom_keywords": [],
            "tools_platforms": [],
        }

        # Extract technical skills
        for category, skills in self.technical_skills.items():
            for skill in skills:
                if skill in text:
                    extracted["technical_skills"].append(skill)

        # Extract job titles
        for title in self.job_titles:
            if title in text:
                extracted["job_titles"].append(title)

        # Extract industries
        for industry in self.industries:
            if industry in text:
                extracted["industries"].append(industry)

        # Extract custom keywords (words that appear multiple times)
        words = re.findall(r"\b[a-z]{3,}\b", text)
        word_freq = {}
        for word in words:
            if word not in [
                "the",
                "and",
                "for",
                "with",
                "from",
                "this",
                "that",
                "have",
                "will",
                "been",
                "they",
                "their",
            ]:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get words that appear at least 2 times
        custom_keywords = [word for word, freq in word_freq.items() if freq >= 2]
        extracted["custom_keywords"] = custom_keywords[:20]  # Top 20

        # Extract tools and platforms (capitalized words)
        tools = re.findall(r"\b[A-Z][a-zA-Z0-9]*\b", text)
        extracted["tools_platforms"] = list(set(tools))[:15]  # Top 15 unique

        return extracted

    def extract_from_file(self, file_path: str) -> Dict[str, List[str]]:
        """Extract keywords from a resume file."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Resume file not found: {file_path}")

            # Read file content
            if file_path.suffix.lower() == ".pdf":
                # For PDF files, you might need to install pdfplumber or similar
                try:
                    import pdfplumber

                    with pdfplumber.open(file_path) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() or ""
                except ImportError:
                    logger.warning("pdfplumber not installed. Install with: pip install pdfplumber")
                    return self._extract_from_txt_fallback(file_path)
            else:
                # Assume text file
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()

            return self.extract_from_text(text)

        except Exception as e:
            logger.error(f"Error extracting keywords from file: {e}")
            return {"error": str(e)}

    def _extract_from_txt_fallback(self, file_path: Path) -> Dict[str, List[str]]:
        """Fallback method for text extraction."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            return self.extract_from_text(text)
        except Exception as e:
            return {"error": f"Could not read file: {e}"}

    def generate_job_keywords(self, extracted: Dict[str, List[str]]) -> List[str]:
        """Generate job search keywords from extracted data."""
        keywords = []

        # Add job titles
        keywords.extend(extracted.get("job_titles", []))

        # Add technical skills
        keywords.extend(extracted.get("technical_skills", []))

        # Add industry-specific keywords
        industries = extracted.get("industries", [])
        for industry in industries:
            keywords.append(f"{industry} analyst")
            keywords.append(f"{industry} data")

        # Add custom keywords (filter out common words)
        custom = extracted.get("custom_keywords", [])
        filtered_custom = [kw for kw in custom if len(kw) > 3 and kw not in keywords]
        keywords.extend(filtered_custom[:10])

        # Add tools and platforms
        tools = extracted.get("tools_platforms", [])
        keywords.extend(tools[:5])

        # Remove duplicates and limit
        unique_keywords = list(dict.fromkeys(keywords))  # Preserve order
        return unique_keywords[:20]  # Return top 20 keywords

    def save_keywords_to_profile(self, profile_name: str, keywords: List[str]) -> bool:
        """Save extracted keywords to a profile."""
        try:
            profile_dir = Path("profiles") / profile_name
            profile_dir.mkdir(parents=True, exist_ok=True)

            profile_file = profile_dir / f"{profile_name}.json"

            # Load existing profile or create new one
            if profile_file.exists():
                with open(profile_file, "r", encoding="utf-8") as f:
                    profile = json.load(f)
            else:
                profile = {
                    "name": profile_name,
                    "profile_name": profile_name,
                    "email": "",
                    "keywords": [],
                    "skills": [],
                    "resume_path": "",
                    "cover_letter_path": "",
                }

            # Update keywords
            profile["keywords"] = keywords

            # Save updated profile
            with open(profile_file, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Keywords saved to profile: {profile_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving keywords to profile: {e}")
            return False


def extract_keywords_from_resume(resume_path: str, profile_name: str = None) -> Dict:
    """
    Extract keywords from resume and optionally save to profile.

    Args:
        resume_path: Path to resume file
        profile_name: Optional profile name to save keywords to

    Returns:
        Dictionary with extracted keywords and generated job keywords
    """
    import logging

    logger = logging.getLogger(__name__)

    extractor = ResumeKeywordExtractor()

    logger.info("🔍 Extracting keywords from: %s", resume_path)

    # Extract keywords
    extracted = extractor.extract_from_file(resume_path)

    if "error" in extracted:
        logger.error("❌ Error: %s", extracted["error"])
        return extracted

    # Generate job keywords
    job_keywords = extractor.generate_job_keywords(extracted)

    # Log results
    logger.info("\n📊 Extracted Keywords:")
    logger.info("=" * 50)

    for category, keywords in extracted.items():
        if keywords:
            logger.info("\n%s:", category.replace("_", " ").title())
            logger.info(", ".join(keywords[:10]))  # Show first 10

    logger.info("\n🎯 Generated Job Keywords (%d):", len(job_keywords))
    logger.info("=" * 50)
    for i, keyword in enumerate(job_keywords, 1):
        logger.info("%2d. %s", i, keyword)

    # Save to profile if requested
    if profile_name:
        logger.info("\n💾 Saving keywords to profile: %s", profile_name)
        success = extractor.save_keywords_to_profile(profile_name, job_keywords)
        if success:
            logger.info("✅ Keywords saved successfully!")
        else:
            logger.error("❌ Failed to save keywords")

    return {
        "extracted": extracted,
        "job_keywords": job_keywords,
        "profile_saved": profile_name is not None,
    }


# CLI usage moved to proper CLI module
# To use: from src.utils.resume_keyword_extractor import extract_keywords_from_resume
