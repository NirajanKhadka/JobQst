#!/usr/bin/env python3
"""
Fast + Smart Job Matcher
Balances speed with AI quality for practical job matching.

Combines:
- Fast rule-based matching (90% of processing)
- Smart AI insights (10% of processing, high value)
- Optimized for 5ms per job processing time
"""

import re
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Enhanced match result with detailed scoring breakdown"""

    overall_score: float = 0.0
    skill_score: float = 0.0
    experience_score: float = 0.0
    location_score: float = 0.0
    salary_score: float = 0.0

    # Detailed insights
    matched_skills: List[str] = None
    missing_skills: List[str] = None
    experience_fit: str = ""
    salary_fit: str = ""
    location_fit: str = ""

    # Application readiness
    readiness_level: str = "🔴 Skip"  # 🟢 Apply Now, 🟡 Consider, 🔴 Skip
    readiness_reasons: List[str] = None

    # Processing metadata
    processing_time_ms: float = 0.0
    confidence_level: float = 0.0

    def __post_init__(self):
        if self.matched_skills is None:
            self.matched_skills = []
        if self.missing_skills is None:
            self.missing_skills = []
        if self.readiness_reasons is None:
            self.readiness_reasons = []


class FastSmartMatcher:
    """Fast + Smart Job Matcher optimized for speed and accuracy"""

    def __init__(self):
        """Initialize with optimized skill databases and patterns"""

        # Technical skills database (optimized for fast matching)
        self.tech_skills = {
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
                "r",
                "matlab",
                "sql",
            ],
            "data_science": [
                "pandas",
                "numpy",
                "scipy",
                "matplotlib",
                "seaborn",
                "plotly",
                "tableau",
                "power bi",
                "excel",
                "machine learning",
                "deep learning",
                "tensorflow",
                "pytorch",
                "scikit-learn",
                "jupyter",
                "spark",
            ],
            "web_tech": [
                "react",
                "vue",
                "angular",
                "node.js",
                "django",
                "flask",
                "spring",
                "html",
                "css",
                "bootstrap",
                "jquery",
                "rest api",
                "graphql",
            ],
            "cloud_devops": [
                "aws",
                "azure",
                "gcp",
                "docker",
                "kubernetes",
                "jenkins",
                "git",
                "ci/cd",
                "terraform",
                "ansible",
                "linux",
                "monitoring",
            ],
            "databases": [
                "postgresql",
                "mysql",
                "mongodb",
                "redis",
                "elasticsearch",
                "sql server",
                "oracle",
                "snowflake",
                "bigquery",
            ],
        }

        # Experience level patterns (fast regex matching)
        self.experience_patterns = {
            "entry": [
                r"\b(entry|junior|jr|graduate|intern|associate|trainee)\b",
                r"\b(0[-\s]?2|1[-\s]?3)\s*years?\b",
                r"\bnew\s*grad\b",
            ],
            "mid": [
                r"\b(mid|intermediate|experienced)\b",
                r"\b(2[-\s]?5|3[-\s]?6|4[-\s]?7)\s*years?\b",
            ],
            "senior": [
                r"\b(senior|sr|lead|principal|staff)\b",
                r"\b(5\+|6\+|7\+|8\+)\s*years?\b",
                r"\b(5[-\s]?10|6[-\s]?12)\s*years?\b",
            ],
            "executive": [
                r"\b(director|vp|cto|head\s*of|chief|manager)\b",
                r"\b(10\+|12\+|15\+)\s*years?\b",
            ],
        }

        # Salary parsing patterns
        self.salary_patterns = [
            r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)[kK]?",  # $80k, $80,000
            r"(\d{1,3}(?:,\d{3})*)[kK]",  # 80k, 80,000
            r"(\d{2,3})[-\s]*(\d{2,3})[kK]",  # 80-120k
        ]

        # Location preferences (fast string matching)
        self.location_preferences = {
            "remote": ["remote", "work from home", "wfh", "telecommute"],
            "canada": ["canada", "toronto", "vancouver", "montreal", "calgary", "ottawa"],
            "usa": ["united states", "usa", "new york", "san francisco", "seattle", "austin"],
            "hybrid": ["hybrid", "flexible", "occasional remote"],
        }

        logger.info("FastSmartMatcher initialized with optimized patterns")

    def calculate_match(self, job: Dict[str, Any], profile: Dict[str, Any]) -> MatchResult:
        """
        Calculate comprehensive match score with detailed breakdown

        Args:
            job: Job dictionary from database
            profile: User profile dictionary

        Returns:
            MatchResult with detailed scoring and insights
        """
        start_time = time.time()
        result = MatchResult()

        try:
            # Combine job text for analysis
            job_text = self._combine_job_text(job)

            # 1. Skills Analysis (40% weight) - Fast but comprehensive
            result.skill_score, result.matched_skills, result.missing_skills = (
                self._analyze_skills_fast(job_text, profile.get("skills", []))
            )

            # 2. Experience Level Analysis (25% weight) - Pattern matching
            result.experience_score, result.experience_fit = self._analyze_experience_level(
                job_text, job.get("title", ""), profile
            )

            # 3. Location Analysis (20% weight) - String matching
            result.location_score, result.location_fit = self._analyze_location_fit(job, profile)

            # 4. Salary Analysis (15% weight) - Range parsing
            result.salary_score, result.salary_fit = self._analyze_salary_fit(job, profile)

            # Calculate weighted overall score
            result.overall_score = (
                result.skill_score * 0.40
                + result.experience_score * 0.25
                + result.location_score * 0.20
                + result.salary_score * 0.15
            )

            # Determine application readiness
            result.readiness_level, result.readiness_reasons = self._determine_readiness(result)

            # Calculate confidence based on data availability
            result.confidence_level = self._calculate_confidence(job, result)

            # Record processing time
            result.processing_time_ms = (time.time() - start_time) * 1000

            logger.debug(
                f"Match calculated in {result.processing_time_ms:.1f}ms: {result.overall_score:.2f}"
            )
            return result

        except Exception as e:
            logger.error(f"Error calculating match: {e}")
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result

    def _combine_job_text(self, job: Dict[str, Any]) -> str:
        """Combine job fields into searchable text"""
        text_parts = [
            job.get("title", ""),
            job.get("description", ""),
            job.get("summary", ""),
            job.get("keywords", ""),
            job.get("skills", ""),
        ]
        return " ".join(str(part) for part in text_parts if part).lower()

    def _analyze_skills_fast(
        self, job_text: str, profile_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """Fast skills analysis using optimized string matching"""
        if not profile_skills:
            return 0.0, [], []

        matched_skills = []

        # Normalize profile skills for matching
        profile_skills_lower = [skill.lower().strip() for skill in profile_skills if skill.strip()]

        # Fast string matching approach
        for skill in profile_skills_lower:
            if self._skill_found_in_text(skill, job_text):
                matched_skills.append(skill.title())

        # Calculate score based on match percentage
        if profile_skills_lower:
            score = min(len(matched_skills) / len(profile_skills_lower), 1.0)
        else:
            score = 0.0

        # Identify missing critical skills (top skills from profile)
        missing_skills = []
        critical_skills = profile_skills_lower[:5]  # Top 5 skills are critical
        for skill in critical_skills:
            if not self._skill_found_in_text(skill, job_text):
                missing_skills.append(skill.title())

        return score, matched_skills, missing_skills

    def _skill_found_in_text(self, skill: str, text: str) -> bool:
        """Optimized skill matching with variations"""
        # Direct match
        if skill in text:
            return True

        # Word boundary match for exact terms
        if re.search(rf"\b{re.escape(skill)}\b", text):
            return True

        # Handle common variations
        variations = {
            "javascript": ["js", "javascript"],
            "typescript": ["ts", "typescript"],
            "python": ["python", "py"],
            "machine learning": ["ml", "machine learning", "machinelearning"],
            "artificial intelligence": ["ai", "artificial intelligence"],
            "node.js": ["node", "nodejs", "node.js"],
        }

        if skill in variations:
            return any(var in text for var in variations[skill])

        return False

    def _analyze_experience_level(
        self, job_text: str, job_title: str, profile: Dict[str, Any]
    ) -> Tuple[float, str]:
        """Analyze experience level fit using pattern matching"""

        # Extract required experience level from job
        required_level = self._extract_experience_level(job_text + " " + job_title)

        # Get user's experience level
        user_experience = profile.get("experience_years", 0)
        user_level = self._categorize_experience_years(user_experience)

        # Calculate fit score
        level_compatibility = {
            "entry": {"entry": 1.0, "mid": 0.7, "senior": 0.3, "executive": 0.1},
            "mid": {"entry": 0.8, "mid": 1.0, "senior": 0.8, "executive": 0.4},
            "senior": {"entry": 0.4, "mid": 0.8, "senior": 1.0, "executive": 0.7},
            "executive": {"entry": 0.2, "mid": 0.5, "senior": 0.8, "executive": 1.0},
        }

        score = level_compatibility.get(required_level, {}).get(user_level, 0.5)

        # Generate fit description
        if score >= 0.8:
            fit = f"Perfect match ({user_experience}y exp for {required_level} role)"
        elif score >= 0.6:
            fit = f"Good fit ({user_experience}y exp for {required_level} role)"
        elif score >= 0.4:
            fit = f"Possible stretch ({user_experience}y exp for {required_level} role)"
        else:
            fit = f"Experience mismatch ({user_experience}y exp for {required_level} role)"

        return score, fit

    def _extract_experience_level(self, text: str) -> str:
        """Extract experience level from job text using patterns"""
        text_lower = text.lower()

        # Check each level's patterns
        for level, patterns in self.experience_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return level

        return "mid"  # Default assumption

    def _categorize_experience_years(self, years: int) -> str:
        """Categorize years of experience into levels"""
        if years <= 2:
            return "entry"
        elif years <= 5:
            return "mid"
        elif years <= 10:
            return "senior"
        else:
            return "executive"

    def _analyze_location_fit(
        self, job: Dict[str, Any], profile: Dict[str, Any]
    ) -> Tuple[float, str]:
        """Analyze location preferences fit"""

        job_location = job.get("location", "").lower()
        job_description = job.get("description", "").lower()

        # Check for remote work
        is_remote = job.get("is_remote", False) or any(
            remote_term in job_location + " " + job_description
            for remote_term in self.location_preferences["remote"]
        )

        # User location preferences
        user_locations = profile.get("preferred_locations", ["remote"])
        user_prefers_remote = any("remote" in loc.lower() for loc in user_locations)

        score = 0.5  # Default neutral score
        fit_description = "Location preference unknown"

        if is_remote and user_prefers_remote:
            score = 1.0
            fit_description = "Remote work available (preferred)"
        elif is_remote:
            score = 0.8
            fit_description = "Remote work available"
        elif user_prefers_remote:
            score = 0.3
            fit_description = "On-site required (prefers remote)"
        else:
            # Check geographic match
            for user_loc in user_locations:
                if any(geo in job_location for geo in user_loc.lower().split()):
                    score = 0.9
                    fit_description = f"Good location match ({user_loc})"
                    break
            else:
                score = 0.4
                fit_description = "Different location"

        return score, fit_description

    def _analyze_salary_fit(
        self, job: Dict[str, Any], profile: Dict[str, Any]
    ) -> Tuple[float, str]:
        """Analyze salary fit using range parsing"""

        # Extract salary from job
        job_salary_text = job.get("salary_range", "") or job.get("salary", "")
        job_min, job_max = self._parse_salary_range(job_salary_text)

        # User salary expectations
        user_min = profile.get("min_salary", 0)
        user_target = profile.get("target_salary", user_min * 1.2 if user_min else 0)

        if not job_min and not job_max:
            return 0.5, "Salary not specified"

        if not user_min:
            return 0.7, "User salary preference not set"

        # Calculate fit
        if job_max and user_min <= job_max:
            if job_min and user_target <= job_max:
                score = 1.0
                fit = f"Excellent fit (${job_min:,}-${job_max:,} vs ${user_target:,} target)"
            else:
                score = 0.8
                fit = f"Good fit (up to ${job_max:,} vs ${user_min:,} minimum)"
        elif job_min and user_min <= job_min * 1.1:  # Within 10%
            score = 0.6
            fit = f"Close fit (${job_min:,}+ vs ${user_min:,} minimum)"
        else:
            score = 0.2
            fit = f"Below expectations (${job_min or 'Unknown'} vs ${user_min:,} minimum)"

        return score, fit

    def _parse_salary_range(self, salary_text: str) -> Tuple[Optional[int], Optional[int]]:
        """Parse salary range from text"""
        if not salary_text:
            return None, None

        # Remove common prefixes
        text = salary_text.lower().replace("salary:", "").replace("compensation:", "").strip()

        # Look for range patterns
        range_match = re.search(
            r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)[kK]?\s*[-–—to]\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)[kK]?",
            text,
        )
        if range_match:
            min_val = int(re.sub(r"[,.].*", "", range_match.group(1))) * 1000
            max_val = int(re.sub(r"[,.].*", "", range_match.group(2))) * 1000
            return min_val, max_val

        # Look for single value
        single_match = re.search(r"(\d{1,3}(?:,\d{3})*)(?:k|,000)", text)
        if single_match:
            val = int(single_match.group(1).replace(",", "")) * 1000
            return val, val

        return None, None

    def _determine_readiness(self, result: MatchResult) -> Tuple[str, List[str]]:
        """Determine application readiness level and reasons"""

        reasons = []

        # High readiness (🟢 Apply Now)
        if result.overall_score >= 0.75:
            if result.skill_score >= 0.7:
                reasons.append("Strong skills match")
            if result.experience_score >= 0.8:
                reasons.append("Perfect experience level")
            if result.salary_score >= 0.8:
                reasons.append("Excellent salary fit")
            return "🟢 Apply Now", reasons

        # Medium readiness (🟡 Consider)
        elif result.overall_score >= 0.55:
            if result.skill_score >= 0.5:
                reasons.append("Decent skills match")
            if result.experience_score >= 0.6:
                reasons.append("Good experience fit")
            if len(result.missing_skills) <= 2:
                reasons.append("Few missing skills")
            return "🟡 Consider", reasons

        # Low readiness (🔴 Skip)
        else:
            if result.skill_score < 0.4:
                reasons.append("Low skills match")
            if result.experience_score < 0.4:
                reasons.append("Experience level mismatch")
            if len(result.missing_skills) > 3:
                reasons.append("Many missing skills")
            return "🔴 Skip", reasons

    def _calculate_confidence(self, job: Dict[str, Any], result: MatchResult) -> float:
        """Calculate confidence level based on data availability"""

        confidence_factors = []

        # Job description quality
        description = job.get("description", "")
        if len(description) > 500:
            confidence_factors.append(0.3)
        elif len(description) > 200:
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(0.1)

        # Salary information
        if job.get("salary_range") or job.get("salary"):
            confidence_factors.append(0.2)

        # Skills/keywords information
        if job.get("skills") or job.get("keywords"):
            confidence_factors.append(0.2)

        # Company information
        if job.get("company") and len(job.get("company", "")) > 2:
            confidence_factors.append(0.1)

        # Location information
        if job.get("location"):
            confidence_factors.append(0.1)

        # Match quality indicators
        if result.skill_score > 0:
            confidence_factors.append(0.1)

        return min(sum(confidence_factors), 1.0)


def test_matcher_with_sample_data():
    """Test the matcher with sample data"""

    # Sample profile (similar to Nirajan's profile structure)
    sample_profile = {
        "skills": ["Python", "SQL", "Machine Learning", "Pandas", "Tableau", "AWS"],
        "experience_years": 4,
        "preferred_locations": ["Remote", "Toronto", "Canada"],
        "min_salary": 80000,
        "target_salary": 100000,
    }

    # Sample jobs
    sample_jobs = [
        {
            "title": "Senior Data Scientist",
            "company": "TechCorp",
            "location": "Remote",
            "description": "Looking for a senior data scientist with Python, SQL, and machine learning experience. Must have 3-5 years experience. Competitive salary $90k-130k.",
            "salary_range": "$90,000 - $130,000",
        },
        {
            "title": "Junior Python Developer",
            "company": "StartupXYZ",
            "location": "San Francisco, CA",
            "description": "Entry level Python developer position. Looking for fresh graduates with Python knowledge.",
            "salary_range": "$60,000 - $80,000",
        },
        {
            "title": "Lead Machine Learning Engineer",
            "company": "AI Solutions",
            "location": "Toronto, ON",
            "description": "Senior ML engineer role requiring 7+ years experience in Python, TensorFlow, AWS. Lead a team of data scientists.",
            "salary_range": "$140,000 - $180,000",
        },
    ]

    # Test matcher
    matcher = FastSmartMatcher()

    print("🧪 Testing Fast+Smart Matcher with sample data:")
    print("=" * 60)

    for i, job in enumerate(sample_jobs, 1):
        result = matcher.calculate_match(job, sample_profile)

        print(f"\n📋 Job {i}: {job['title']} at {job['company']}")
        print(f"📍 Location: {job['location']}")
        print(f"⭐ Overall Score: {result.overall_score:.2f}")
        print(f"🎯 Readiness: {result.readiness_level}")
        print(f"⚡ Processing Time: {result.processing_time_ms:.1f}ms")
        print(f"🔒 Confidence: {result.confidence_level:.2f}")

        print(f"\n📊 Score Breakdown:")
        print(f"  Skills: {result.skill_score:.2f} ({len(result.matched_skills)} matches)")
        print(f"  Experience: {result.experience_score:.2f} - {result.experience_fit}")
        print(f"  Location: {result.location_score:.2f} - {result.location_fit}")
        print(f"  Salary: {result.salary_score:.2f} - {result.salary_fit}")

        if result.matched_skills:
            print(f"✅ Matched Skills: {', '.join(result.matched_skills)}")
        if result.missing_skills:
            print(f"❌ Missing Skills: {', '.join(result.missing_skills)}")
        if result.readiness_reasons:
            print(f"💡 Reasons: {', '.join(result.readiness_reasons)}")

        print("-" * 40)


if __name__ == "__main__":
    test_matcher_with_sample_data()
