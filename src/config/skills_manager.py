"""
Dynamic skills and roles management configuration.

This module provides a flexible system for managing skills, job titles, and industry-specific
keywords that can be updated without code changes. Skills are loaded from JSON files that can
be easily maintained and extended.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional

logger = logging.getLogger(__name__)


class SkillsManager:
    """Manages dynamic loading and updating of skills, job titles, and keywords."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize skills manager with configuration directory.

        Args:
            config_dir: Directory containing skills JSON files. Defaults to config/skills/
        """
        if config_dir is None:
            # Default to project config/skills directory
            project_root = Path(__file__).parent.parent.parent.parent
            config_dir = project_root / "config" / "skills"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.skills: Set[str] = set()
        self.job_titles: Set[str] = set()
        self.industries: Dict[str, Dict[str, List[str]]] = {}

        self._initialize_default_configs()
        self.load_all_skills()

    def _initialize_default_configs(self) -> None:
        """Create default configuration files if they don't exist."""
        default_files = {
            "technology.json": self._get_technology_defaults(),
            "healthcare.json": self._get_healthcare_defaults(),
            "hospitality.json": self._get_hospitality_defaults(),
            "trades.json": self._get_trades_defaults(),
            "retail.json": self._get_retail_defaults(),
            "job_titles.json": self._get_job_titles_defaults(),
        }

        for filename, data in default_files.items():
            filepath = self.config_dir / filename
            if not filepath.exists():
                self._save_json(filepath, data)
                logger.info(f"Created default config: {filename}")

    def load_all_skills(self) -> None:
        """Load all skills from JSON configuration files."""
        self.skills.clear()
        self.job_titles.clear()
        self.industries.clear()

        # Load industry-specific skills
        for json_file in self.config_dir.glob("*.json"):
            if json_file.stem == "job_titles":
                continue

            try:
                data = self._load_json(json_file)
                industry_name = json_file.stem
                self.industries[industry_name] = data

                # Add all skills from this industry
                for category, skills_list in data.items():
                    if isinstance(skills_list, list):
                        self.skills.update(s.lower() for s in skills_list)

                logger.info(f"Loaded {len(data)} skill categories from {industry_name}")
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

        # Load job titles separately
        titles_file = self.config_dir / "job_titles.json"
        if titles_file.exists():
            try:
                titles_data = self._load_json(titles_file)
                for category, titles in titles_data.items():
                    if isinstance(titles, list):
                        self.job_titles.update(t.lower() for t in titles)
                logger.info(f"Loaded {len(self.job_titles)} job titles")
            except Exception as e:
                logger.error(f"Error loading job titles: {e}")

    def add_skills(self, industry: str, category: str, skills: List[str]) -> None:
        """Add new skills to an industry category.

        Args:
            industry: Industry name (e.g., 'healthcare', 'technology')
            category: Skill category (e.g., 'programming_languages', 'medical_procedures')
            skills: List of skills to add
        """
        filepath = self.config_dir / f"{industry}.json"

        # Load existing or create new
        if filepath.exists():
            data = self._load_json(filepath)
        else:
            data = {}

        # Add skills to category
        if category not in data:
            data[category] = []

        # Add new skills (avoid duplicates)
        existing = set(s.lower() for s in data[category])
        new_skills = [s for s in skills if s.lower() not in existing]
        data[category].extend(new_skills)

        # Save updated configuration
        self._save_json(filepath, data)

        # Reload all skills
        self.load_all_skills()

        logger.info(f"Added {len(new_skills)} skills to {industry}/{category}")

    def add_job_titles(self, category: str, titles: List[str]) -> None:
        """Add new job titles to a category.

        Args:
            category: Job category (e.g., 'healthcare', 'engineering')
            titles: List of job titles to add
        """
        filepath = self.config_dir / "job_titles.json"

        if filepath.exists():
            data = self._load_json(filepath)
        else:
            data = {}

        if category not in data:
            data[category] = []

        # Add new titles (avoid duplicates)
        existing = set(t.lower() for t in data[category])
        new_titles = [t for t in titles if t.lower() not in existing]
        data[category].extend(new_titles)

        self._save_json(filepath, data)
        self.load_all_skills()

        logger.info(f"Added {len(new_titles)} job titles to {category}")

    def get_skills_by_industry(self, industry: str) -> Dict[str, List[str]]:
        """Get all skills for a specific industry.

        Args:
            industry: Industry name

        Returns:
            Dictionary of skill categories and their skills
        """
        return self.industries.get(industry, {})

    def search_skills(self, query: str) -> List[str]:
        """Search for skills matching a query.

        Args:
            query: Search query

        Returns:
            List of matching skills
        """
        query_lower = query.lower()
        return [s for s in self.skills if query_lower in s]

    def _load_json(self, filepath: Path) -> Dict:
        """Load JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_json(self, filepath: Path, data: Dict) -> None:
        """Save JSON file with pretty formatting."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_technology_defaults(self) -> Dict[str, List[str]]:
        """Get default technology skills."""
        return {
            "programming_languages": [
                "Python",
                "Java",
                "JavaScript",
                "TypeScript",
                "C++",
                "C#",
                "Go",
                "Rust",
                "Kotlin",
                "Swift",
                "PHP",
                "Ruby",
                "Scala",
                "R",
            ],
            "web_technologies": [
                "React",
                "Angular",
                "Vue",
                "Node.js",
                "Django",
                "Flask",
                "Spring",
                "ASP.NET",
                "Laravel",
                "Rails",
                "HTML",
                "CSS",
                "SASS",
                "Tailwind",
            ],
            "databases": [
                "PostgreSQL",
                "MySQL",
                "MongoDB",
                "Redis",
                "Elasticsearch",
                "Oracle",
                "SQL Server",
                "DynamoDB",
                "Cassandra",
                "BigQuery",
                "Snowflake",
            ],
            "cloud_devops": [
                "AWS",
                "Azure",
                "GCP",
                "Docker",
                "Kubernetes",
                "Terraform",
                "Jenkins",
                "GitLab",
                "GitHub Actions",
                "Ansible",
                "Prometheus",
                "Grafana",
            ],
            "data_ml": [
                "Pandas",
                "NumPy",
                "Scikit-learn",
                "TensorFlow",
                "PyTorch",
                "Spark",
                "Hadoop",
                "Kafka",
                "Airflow",
                "Tableau",
                "Power BI",
            ],
        }

    def _get_healthcare_defaults(self) -> Dict[str, List[str]]:
        """Get default healthcare skills."""
        return {
            "clinical_skills": [
                "Patient Care",
                "Vital Signs",
                "Medication Administration",
                "IV Therapy",
                "Wound Care",
                "Catheterization",
                "Phlebotomy",
                "CPR",
                "BLS",
                "ACLS",
            ],
            "medical_software": [
                "EMR",
                "Electronic Medical Records",
                "Epic",
                "Cerner",
                "Meditech",
                "ICD-10",
                "CPT Coding",
                "Medical Billing",
            ],
            "specialties": [
                "Nursing",
                "Oncology",
                "Pediatrics",
                "Geriatrics",
                "Mental Health",
                "Physical Therapy",
                "Occupational Therapy",
                "Radiology",
                "Laboratory",
            ],
            "certifications": ["RN", "LPN", "CNA", "HIPAA", "First Aid", "PALS", "NRP"],
        }

    def _get_hospitality_defaults(self) -> Dict[str, List[str]]:
        """Get default hospitality skills."""
        return {
            "food_service": [
                "Cooking",
                "Baking",
                "Food Preparation",
                "Food Safety",
                "HACCP",
                "ServSafe",
                "Menu Planning",
                "Inventory Management",
                "Catering",
            ],
            "customer_service": [
                "Customer Service",
                "Table Service",
                "POS Systems",
                "Cash Handling",
                "Reservation Systems",
                "OpenTable",
                "Front Desk",
                "Concierge",
            ],
            "beverage": [
                "Bartending",
                "Mixology",
                "Wine Knowledge",
                "Sommelier",
                "Barista",
                "Coffee Preparation",
                "Espresso Machine",
                "Latte Art",
            ],
            "management": [
                "Hotel Management",
                "Restaurant Management",
                "Housekeeping",
                "Banquet Service",
                "Event Planning",
            ],
        }

    def _get_trades_defaults(self) -> Dict[str, List[str]]:
        """Get default trades skills."""
        return {
            "construction": [
                "Carpentry",
                "Framing",
                "Electrical",
                "Plumbing",
                "HVAC",
                "Welding",
                "Masonry",
                "Drywall",
                "Painting",
                "Roofing",
                "Blueprint Reading",
            ],
            "automotive": [
                "Automotive Repair",
                "Diagnostics",
                "Engine Repair",
                "Transmission",
                "Brakes",
                "Suspension",
                "Wheel Alignment",
                "Electrical Systems",
            ],
            "equipment": [
                "Forklift",
                "Crane Operation",
                "Heavy Equipment",
                "Excavator",
                "Backhoe",
                "Bulldozer",
                "Boom Lift",
                "Scissor Lift",
            ],
            "certifications": [
                "Red Seal",
                "Journeyman",
                "Apprenticeship",
                "Welding Certification",
                "Electrical License",
                "Class 1 License",
                "Class 3 License",
            ],
        }

    def _get_retail_defaults(self) -> Dict[str, List[str]]:
        """Get default retail skills."""
        return {
            "sales": [
                "Retail Sales",
                "Customer Service",
                "Upselling",
                "Cross-selling",
                "Sales Techniques",
                "Closing Sales",
                "Product Knowledge",
            ],
            "operations": [
                "Cash Register",
                "POS",
                "Inventory Management",
                "Stock Management",
                "Visual Merchandising",
                "Loss Prevention",
                "Store Operations",
            ],
            "software": ["Square", "Shopify", "Salesforce", "Microsoft Dynamics", "CRM"],
        }

    def _get_job_titles_defaults(self) -> Dict[str, List[str]]:
        """Get default job titles by category."""
        return {
            "software_engineering": [
                "Software Engineer",
                "Senior Software Engineer",
                "Junior Software Engineer",
                "Full Stack Developer",
                "Frontend Developer",
                "Backend Developer",
                "DevOps Engineer",
                "Site Reliability Engineer",
                "Software Architect",
            ],
            "data_science": [
                "Data Scientist",
                "Data Analyst",
                "Data Engineer",
                "ML Engineer",
                "AI Engineer",
                "Business Analyst",
                "Data Architect",
            ],
            "healthcare": [
                "Registered Nurse",
                "Licensed Practical Nurse",
                "Nursing Assistant",
                "Medical Assistant",
                "Physician",
                "Surgeon",
                "Pharmacist",
                "Physical Therapist",
                "Occupational Therapist",
                "Radiologist",
            ],
            "hospitality": [
                "Chef",
                "Sous Chef",
                "Line Cook",
                "Prep Cook",
                "Bartender",
                "Server",
                "Host",
                "Hotel Manager",
                "Front Desk Agent",
                "Concierge",
                "Housekeeper",
            ],
            "trades": [
                "Electrician",
                "Plumber",
                "Carpenter",
                "HVAC Technician",
                "Welder",
                "Automotive Technician",
                "Construction Worker",
                "Heavy Equipment Operator",
            ],
            "retail": [
                "Sales Associate",
                "Store Manager",
                "Assistant Manager",
                "Cashier",
                "Visual Merchandiser",
                "Inventory Specialist",
                "Loss Prevention Officer",
            ],
        }


# Global instance for easy access
_skills_manager: Optional[SkillsManager] = None


def get_skills_manager() -> SkillsManager:
    """Get global skills manager instance.

    Returns:
        Global SkillsManager instance
    """
    global _skills_manager
    if _skills_manager is None:
        _skills_manager = SkillsManager()
    return _skills_manager
