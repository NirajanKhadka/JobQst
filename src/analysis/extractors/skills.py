"""
Skills and requirements extraction.

Handles technical skills extraction with dynamic skill database
and pattern-based requirements extraction.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set

from .base import BaseExtractor, ExtractionConfidence, PatternMatch

logger = logging.getLogger(__name__)


class SkillsExtractor(BaseExtractor):
    """Extracts technical skills and job requirements with dynamic skill management."""

    def __init__(self, use_dynamic_skills: bool = True):
        """Initialize skills extractor with patterns and skill database.

        Args:
            use_dynamic_skills: If True, load skills from dynamic manager (JSON configs).
                              If False, use built-in comprehensive skills database.
        """
        super().__init__()
        self._init_skill_patterns()
        self._init_requirement_patterns()
        self.use_dynamic_skills = use_dynamic_skills

        if use_dynamic_skills:
            self._init_dynamic_skills()
        else:
            self._init_skills_database()

    def _init_skill_patterns(self) -> None:
        """Initialize skills extraction patterns."""
        self.skill_patterns = {}
        raw_patterns = {
            "very_high": [
                r"(?i)(?:required\s*)?(?:skills|technologies|tech\s*stack)[:\s]*([^.\n]{10,200})",
                r"(?i)technical\s*requirements[:\s]*([^.\n]{10,200})",
            ],
            "high": [
                r"(?i)experience\s*(?:with|in)[:\s]*([^.\n]{10,100})",
                r"(?i)proficiency\s*(?:with|in)[:\s]*([^.\n]{10,100})",
            ],
        }

        for level, patterns in raw_patterns.items():
            self.skill_patterns[level] = [
                re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns
            ]

    def _init_dynamic_skills(self) -> None:
        """Initialize skills from dynamic configuration manager."""
        try:
            # Try importing from config.skills_manager (absolute import)
            from config.skills_manager import get_skills_manager

            manager = get_skills_manager()
            self.standard_skills = manager.skills
            logger.info(f"Loaded {len(self.standard_skills)} skills from dynamic manager")
        except Exception as e:
            # Try loading from config files directly
            try:
                from utils.config_loader import ConfigLoader
                loader = ConfigLoader()
                config = loader.load_config("job_matching_config.json")
                
                # Extract all skills from skill_synonyms
                self.standard_skills = set()
                for industry_skills in config.get("skill_synonyms", {}).values():
                    self.standard_skills.update([s.lower() for s in industry_skills])
                
                logger.info(f"Loaded {len(self.standard_skills)} skills from config files")
            except Exception as config_error:
                logger.warning(
                    f"Failed to load dynamic skills: {e}, config fallback also failed: {config_error}. "
                    f"Falling back to built-in database."
                )
                self._init_skills_database()

    def reload_skills(self) -> None:
        """Reload skills from configuration (useful after adding new skills)."""
        if self.use_dynamic_skills:
            self._init_dynamic_skills()
        else:
            self._init_skills_database()
        logger.info(f"Reloaded {len(self.standard_skills)} skills")

    def _init_requirement_patterns(self) -> None:
        """Initialize requirements extraction patterns."""
        self.requirement_patterns = [
            re.compile(r"(?i)requirements?[:\s]*\n?([^.\n]{10,200})", re.MULTILINE),
            re.compile(r"(?i)qualifications?[:\s]*\n?([^.\n]{10,200})", re.MULTILINE),
            re.compile(r"(?i)must\s*have[:\s]*([^.\n]{10,200})", re.MULTILINE),
            re.compile(r"(?i)required[:\s]*([^.\n]{10,200})", re.MULTILINE),
        ]

    def _init_skills_database(self) -> None:
        """Initialize comprehensive skills database covering all industries in Canada."""
        self.standard_skills = {
            # Programming Languages
            "python",
            "java",
            "javascript",
            "typescript",
            "c++",
            "c#",
            "go",
            "rust",
            "kotlin",
            "swift",
            "php",
            "ruby",
            "scala",
            "r",
            "perl",
            "shell",
            "bash",
            "sql",
            "vb.net",
            "matlab",
            "fortran",
            "cobol",
            "assembly",
            # Web Technologies
            "react",
            "angular",
            "vue",
            "node.js",
            "express",
            "django",
            "flask",
            "spring",
            "asp.net",
            "laravel",
            "rails",
            "next.js",
            "redux",
            "graphql",
            "rest",
            "html",
            "css",
            "sass",
            "tailwind",
            "bootstrap",
            "jquery",
            "webpack",
            "babel",
            "typescript",
            "ajax",
            "json",
            "xml",
            # Databases
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "elasticsearch",
            "cassandra",
            "dynamodb",
            "sqlite",
            "oracle",
            "sql server",
            "bigquery",
            "snowflake",
            "mariadb",
            "neo4j",
            "firebase",
            "cosmos db",
            # Cloud & DevOps
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "terraform",
            "jenkins",
            "gitlab",
            "github actions",
            "ansible",
            "circleci",
            "prometheus",
            "grafana",
            "cloudformation",
            "helm",
            "vagrant",
            "puppet",
            "chef",
            # Data & ML
            "pandas",
            "numpy",
            "scikit-learn",
            "tensorflow",
            "pytorch",
            "spark",
            "hadoop",
            "kafka",
            "airflow",
            "jupyter",
            "tableau",
            "power bi",
            "excel",
            "sas",
            "spss",
            "looker",
            "qlik",
            "alteryx",
            # Healthcare Skills
            "nursing",
            "patient care",
            "vital signs",
            "medication administration",
            "emr",
            "electronic medical records",
            "epic",
            "cerner",
            "meditech",
            "icd-10",
            "cpt coding",
            "medical billing",
            "hipaa",
            "phipaa",
            "first aid",
            "cpr",
            "bls",
            "acls",
            "pals",
            "nrp",
            "wound care",
            "iv therapy",
            "catheterization",
            "phlebotomy",
            "medical terminology",
            "anatomy",
            "physiology",
            "pharmacology",
            "infection control",
            "sterile technique",
            "patient assessment",
            "clinical documentation",
            "telemetry",
            "ventilator management",
            "dialysis",
            "oncology",
            "pediatrics",
            "geriatrics",
            "mental health",
            "occupational therapy",
            "physical therapy",
            "respiratory therapy",
            "radiology",
            "ultrasound",
            "mri",
            "ct scan",
            "x-ray",
            "dental hygiene",
            "dental assisting",
            "orthodontics",
            "endodontics",
            "laboratory skills",
            "specimen collection",
            "blood work",
            # Food Services & Hospitality
            "food preparation",
            "cooking",
            "baking",
            "food safety",
            "haccp",
            "servsafe",
            "food handler",
            "kitchen management",
            "menu planning",
            "inventory management",
            "portion control",
            "knife skills",
            "food cost control",
            "recipe development",
            "catering",
            "banquet service",
            "fine dining",
            "short order cooking",
            "line cooking",
            "prep cook",
            "pastry",
            "confectionery",
            "butchery",
            "garde manger",
            "saucier",
            "sous chef",
            "bartending",
            "mixology",
            "sommelier",
            "wine knowledge",
            "coffee preparation",
            "barista",
            "latte art",
            "espresso machine",
            "customer service",
            "pos systems",
            "cash handling",
            "micros",
            "aloha",
            "square",
            "toast",
            "table service",
            "table management",
            "reservation systems",
            "opentable",
            "resy",
            "hotel management",
            "front desk",
            "concierge",
            "housekeeping",
            "laundry services",
            # Retail & Sales
            "retail sales",
            "customer service",
            "merchandising",
            "visual merchandising",
            "inventory management",
            "stock management",
            "cash register",
            "pos",
            "loss prevention",
            "product knowledge",
            "upselling",
            "cross-selling",
            "sales techniques",
            "closing sales",
            "crm",
            "salesforce",
            "hubspot",
            "microsoft dynamics",
            "cold calling",
            "lead generation",
            "account management",
            "b2b sales",
            "b2c sales",
            "retail management",
            "store operations",
            "opening/closing procedures",
            "shrinkage control",
            "planograms",
            "price tagging",
            "returns processing",
            # Trades & Construction
            "carpentry",
            "framing",
            "finishing",
            "cabinetry",
            "woodworking",
            "electrical",
            "wiring",
            "panel installation",
            "conduit bending",
            "plumbing",
            "pipefitting",
            "welding",
            "soldering",
            "brazing",
            "hvac",
            "refrigeration",
            "air conditioning",
            "heating systems",
            "construction",
            "blueprint reading",
            "building codes",
            "safety regulations",
            "masonry",
            "concrete work",
            "drywall",
            "painting",
            "flooring",
            "roofing",
            "siding",
            "landscaping",
            "hardscaping",
            "irrigation",
            "heavy equipment operation",
            "forklift",
            "boom lift",
            "scissor lift",
            "crane operation",
            "excavator",
            "backhoe",
            "bulldozer",
            "loader",
            "automotive repair",
            "diagnostics",
            "engine repair",
            "transmission",
            "brakes",
            "suspension",
            "electrical systems",
            "wheel alignment",
            "welding certification",
            "red seal",
            "journeyman",
            "apprenticeship",
            # Manufacturing & Production
            "cnc machining",
            "cnc programming",
            "lathe operation",
            "mill operation",
            "quality control",
            "quality assurance",
            "iso 9001",
            "six sigma",
            "lean manufacturing",
            "5s",
            "kaizen",
            "tpm",
            "root cause analysis",
            "assembly line",
            "production planning",
            "work instructions",
            "gmp",
            "good manufacturing practices",
            "sop",
            "batch records",
            "warehouse operations",
            "picking",
            "packing",
            "shipping",
            "receiving",
            "inventory control",
            "cycle counting",
            "wms",
            "sap",
            "oracle erp",
            # Transportation & Logistics
            "truck driving",
            "class 1 license",
            "class 3 license",
            "air brakes",
            "log books",
            "hours of service",
            "dot regulations",
            "cargo securing",
            "route planning",
            "gps navigation",
            "delivery",
            "courier services",
            "fleet management",
            "vehicle maintenance",
            "dispatch",
            "freight forwarding",
            "customs brokerage",
            "supply chain",
            "procurement",
            "vendor management",
            "purchasing",
            # Office & Administrative
            "microsoft office",
            "word",
            "excel",
            "powerpoint",
            "outlook",
            "google workspace",
            "gmail",
            "google docs",
            "google sheets",
            "data entry",
            "typing",
            "10-key",
            "filing",
            "scanning",
            "scheduling",
            "calendar management",
            "travel arrangements",
            "bookkeeping",
            "accounts payable",
            "accounts receivable",
            "quickbooks",
            "sage",
            "simply accounting",
            "payroll",
            "adp",
            "ceridian",
            "human resources",
            "recruiting",
            "onboarding",
            "employee relations",
            "performance management",
            "benefits administration",
            "transcription",
            "proofreading",
            "editing",
            "technical writing",
            # Customer Service & Call Center
            "phone etiquette",
            "active listening",
            "problem solving",
            "conflict resolution",
            "empathy",
            "patience",
            "communication",
            "call center",
            "inbound calls",
            "outbound calls",
            "telemarketing",
            "troubleshooting",
            "ticket management",
            "zendesk",
            "freshdesk",
            "intercom",
            "live chat",
            "email support",
            "help desk",
            "technical support",
            "remote support",
            "screen sharing",
            # Education & Training
            "teaching",
            "lesson planning",
            "curriculum development",
            "classroom management",
            "student assessment",
            "grading",
            "educational technology",
            "google classroom",
            "canvas",
            "moodle",
            "blackboard",
            "online teaching",
            "zoom",
            "microsoft teams",
            "tutoring",
            "mentoring",
            "coaching",
            "training delivery",
            "adult education",
            "esl",
            "special education",
            "early childhood education",
            # Security & Law Enforcement
            "security guard",
            "access control",
            "surveillance",
            "cctv",
            "patrol",
            "incident reporting",
            "first responder",
            "emergency response",
            "risk assessment",
            "threat assessment",
            "loss prevention",
            "law enforcement",
            "criminal investigation",
            "evidence collection",
            "report writing",
            "court testimony",
            "firearms",
            "defensive tactics",
            # Soft Skills (Important for all roles)
            "communication",
            "teamwork",
            "leadership",
            "time management",
            "organization",
            "multitasking",
            "attention to detail",
            "adaptability",
            "problem solving",
            "critical thinking",
            "decision making",
            "interpersonal skills",
            "work ethic",
            "reliability",
            "punctuality",
            "bilingual",
            "french",
            "english",
            "multilingual",
            # Tech Tools (General)
            "git",
            "jira",
            "confluence",
            "slack",
            "figma",
            "photoshop",
            "illustrator",
            "indesign",
            "autocad",
            "revit",
            "sketchup",
            "social media",
            "facebook",
            "instagram",
            "twitter",
            "linkedin",
            "content management",
            "wordpress",
            "drupal",
            "shopify",
            "seo",
            "google analytics",
            "google ads",
            "facebook ads",
            "email marketing",
            "mailchimp",
            "constant contact",
        }

    def extract(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract skills, requirements, and benefits from job data.
        
        This method implements the base class interface and returns a
        comprehensive extraction result.

        Args:
            job_data: Dictionary containing job posting data

        Returns:
            Dictionary with extracted skills, requirements, and benefits
        """
        return {
            "technical_skills": self.extract_skills(job_data),
            "requirements": self.extract_requirements(job_data),
            "benefits": self.extract_benefits(job_data),
        }

    def extract_skills(self, job_data: Dict[str, Any]) -> List[str]:
        """Extract technical skills from job data.

        Args:
            job_data: Dictionary containing job posting data

        Returns:
            List of extracted skills (limited to top 15)
        """
        content = self._prepare_content(job_data)
        all_skills: Set[str] = set()

        # Extract from skill patterns
        for confidence_level, patterns in self.skill_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(content)
                for match in matches:
                    skills_text = match.strip()
                    skills = self._parse_skills_from_text(skills_text)
                    all_skills.update(skills)

        # Look for individual skills in content (preserve case)
        for skill in self.standard_skills:
            match = re.search(r"\b" + re.escape(skill) + r"\b", content, re.IGNORECASE)
            if match:
                all_skills.add(match.group())

        # Validate and return top skills
        validated_skills = [skill for skill in all_skills if self._validate_skill(skill)]
        return sorted(validated_skills)[:15]

    def extract_requirements(self, job_data: Dict[str, Any]) -> List[str]:
        """Extract job requirements from job data.

        Args:
            job_data: Dictionary containing job posting data

        Returns:
            List of extracted requirements (limited to top 10)
        """
        content = self._prepare_content(job_data)
        requirements = []

        for pattern in self.requirement_patterns:
            matches = pattern.findall(content)
            for match in matches:
                req = match.strip()
                if len(req) > 10 and self._validate_requirement(req):
                    requirements.append(req)

        return requirements[:10]

    def extract_benefits(self, job_data: Dict[str, Any]) -> List[str]:
        """Extract job benefits with fuzzy matching.

        Args:
            job_data: Dictionary containing job posting data

        Returns:
            List of extracted benefits (limited to top 10)
        """
        content = self._prepare_content(job_data)
        benefits = set()

        # Expanded benefit keywords
        benefit_keywords = [
            "health",
            "insurance",
            "dental",
            "vision",
            "401k",
            "retirement",
            "pension",
            "paid time off",
            "pto",
            "vacation",
            "sick leave",
            "parental leave",
            "flexible",
            "remote",
            "work from home",
            "hybrid",
            "professional development",
            "training",
            "stock",
            "equity",
            "bonus",
            "gym",
            "wellness",
            "mental health",
            "commuter",
            "childcare",
            "education",
            "tuition",
            "relocation",
        ]

        # Fuzzy/partial matching
        for benefit in benefit_keywords:
            pattern = r"\b" + re.escape(benefit) + r"\b"
            if re.search(pattern, content, re.IGNORECASE):
                benefits.add(benefit.title())
            elif len(benefit) > 6 and benefit.lower() in content.lower():
                # Partial match for longer keywords
                benefits.add(benefit.title())

        return sorted(list(benefits))[:10]

    def _prepare_content(self, job_data: Dict[str, Any]) -> str:
        """Prepare content for extraction."""
        content_parts = []

        for field in ["description", "job_description", "summary", "requirements"]:
            value = job_data.get(field)
            if value and isinstance(value, str):
                content_parts.append(value)

        return "\n".join(content_parts)

    def _parse_skills_from_text(self, skills_text: str) -> List[str]:
        """Parse individual skills from skills text.

        Args:
            skills_text: Text containing comma/semicolon separated skills

        Returns:
            List of individual skills
        """
        skills = set()

        # Split by common delimiters
        skill_candidates = re.split(r"[,;•\n\r]+", skills_text)

        for candidate in skill_candidates:
            candidate = candidate.strip()
            if candidate and len(candidate) > 1:
                # Check if it's a known skill (preserve original case)
                if candidate.lower() in self.standard_skills:
                    skills.add(candidate)

        return list(skills)

    def _validate_skill(self, skill: str) -> bool:
        """Validate technical skill.

        Args:
            skill: Skill to validate

        Returns:
            True if valid skill
        """
        if not skill or len(skill) < 2:
            return False

        return skill.lower() in self.standard_skills

    def _validate_requirement(self, requirement: str) -> bool:
        """Validate job requirement.

        Args:
            requirement: Requirement to validate

        Returns:
            True if valid requirement
        """
        return 10 < len(requirement) < 200
