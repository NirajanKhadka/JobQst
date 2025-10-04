#!/usr/bin/env python3
"""
Config-Driven Fast + Smart Job Matcher V2
Balances speed with AI quality using external configuration.

Key Improvements over V1:
- All skills, patterns, and weights loaded from config files
- O(1) lookup using pre-built dictionaries
- Easy to add new industries/skills without code changes
- Performance optimized with caching
- Supports skill synonyms and variations

Configuration Files Used:
- config/job_matching_config.json - Matching weights, thresholds, skill synonyms
- config/skills_database.json - Industry skills and role patterns
- config/extraction_patterns.json - Experience and skill patterns
"""

import re
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
import logging

from src.utils.config_loader import ConfigLoader

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
    
    def __getitem__(self, key):
        """Make MatchResult subscriptable for backward compatibility"""
        return getattr(self, key)
    
    def to_dict(self):
        """Convert to dictionary for backward compatibility"""
        return {
            'overall_match': self.overall_score,
            'skill_match': self.skill_score,
            'experience_match': self.experience_score,
            'location_match': self.location_score,
            'salary_match': self.salary_score,
            'matched_skills': self.matched_skills,
            'missing_skills': self.missing_skills,
            'readiness_level': self.readiness_level
        }


class ConfigDrivenMatcher:
    """
    Config-Driven Job Matcher - All domain data in external configs
    
    Performance Optimizations:
    - O(1) skill lookups using pre-built dictionaries
    - Cached configuration loading
    - Pre-compiled regex patterns
    - Lazy loading of heavy resources
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize with config-driven approach
        
        Args:
            config_dir: Path to config directory (auto-detected if not provided)
        """
        start_time = time.time()
        
        # Initialize config loader
        self.config_loader = ConfigLoader(config_dir)
        
        # Load configurations (cached)
        self._load_configurations()
        
        # Build optimized lookup structures
        self._build_lookup_structures()
        
        # Pre-compile regex patterns
        self._compile_patterns()
        
        init_time = (time.time() - start_time) * 1000
        logger.info(
            f"ConfigDrivenMatcher initialized in {init_time:.2f}ms "
            f"({len(self.skill_lookup)} skills, {len(self.skill_variations)} variations)"
        )

    def _load_configurations(self):
        """Load all required configuration files"""
        # Core matching config
        self.matching_config = self.config_loader.load_config("job_matching_config.json")
        
        # Skills database
        self.skills_db = self.config_loader.load_config("skills_database.json")
        
        # Extraction patterns
        self.extraction_config = self.config_loader.load_config("extraction_patterns.json")
        
        logger.debug("All configurations loaded successfully")

    def _build_lookup_structures(self):
        """Build O(1) lookup dictionaries from config data"""
        
        # Build skill lookup: skill_lower -> (display_name, industry)
        self.skill_lookup: Dict[str, Tuple[str, str]] = {}
        
        for industry_key, industry_data in self.skills_db.get("industries", {}).items():
            skills = industry_data.get("skills", [])
            for skill in skills:
                self.skill_lookup[skill.lower()] = (skill, industry_key)
        
        # Build skill variations lookup from synonyms
        skill_synonyms = self.matching_config.get("skill_synonyms", {})
        self.skill_variations: Dict[str, str] = {}
        
        for canonical_name, variations in skill_synonyms.items():
            for variation in variations:
                self.skill_variations[variation.lower()] = canonical_name
        
        # Build location keywords lookup
        location_prefs = self.matching_config.get("location_preferences", {})
        self.location_keywords: Dict[str, Set[str]] = {}
        
        for loc_type, loc_data in location_prefs.items():
            if isinstance(loc_data, dict):
                keywords = loc_data.get("keywords", [])
                self.location_keywords[loc_type] = set(kw.lower() for kw in keywords)
        
        logger.debug(
            f"Lookup structures built: {len(self.skill_lookup)} skills, "
            f"{len(self.skill_variations)} variations, "
            f"{len(self.location_keywords)} location types"
        )

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        
        # Experience level patterns
        exp_patterns = self.matching_config.get("experience_level_patterns", {})
        self.experience_compiled: Dict[str, List[re.Pattern]] = {}
        
        for level, level_data in exp_patterns.items():
            if isinstance(level_data, dict):
                patterns = level_data.get("patterns", [])
                self.experience_compiled[level] = [
                    re.compile(pattern, re.IGNORECASE) for pattern in patterns
                ]
        
        logger.debug(f"Compiled {len(self.experience_compiled)} experience pattern sets")

    def calculate_match(
        self, 
        job: Dict[str, Any], 
        profile: Dict[str, Any]
    ) -> MatchResult:
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

            # Get matching weights from config
            weights = self.matching_config.get("matching_weights", {})
            
            # 1. Skills Analysis - Config-driven with O(1) lookups
            result.skill_score, result.matched_skills, result.missing_skills = (
                self._analyze_skills_config_driven(job_text, profile.get("skills", []))
            )

            # 2. Experience Level Analysis - Pattern matching from config
            result.experience_score, result.experience_fit = (
                self._analyze_experience_config_driven(job_text, job.get("title", ""), profile)
            )

            # 3. Location Analysis - Config-driven keyword matching
            result.location_score, result.location_fit = (
                self._analyze_location_config_driven(job, profile)
            )

            # 4. Salary Analysis - Config-driven range parsing
            result.salary_score, result.salary_fit = (
                self._analyze_salary_fit(job, profile)
            )

            # Calculate weighted overall score using config weights
            result.overall_score = (
                result.skill_score * weights.get("skill_match", 0.40)
                + result.experience_score * weights.get("experience_match", 0.25)
                + result.location_score * weights.get("location_match", 0.20)
                + result.salary_score * weights.get("salary_match", 0.15)
            )

            # Determine application readiness based on config criteria
            result.readiness_level, result.readiness_reasons = (
                self._determine_readiness_config_driven(result)
            )

            # Calculate confidence based on data availability
            result.confidence_level = self._calculate_confidence(job, result)

            # Record processing time
            result.processing_time_ms = (time.time() - start_time) * 1000

            logger.debug(
                f"Match calculated in {result.processing_time_ms:.1f}ms: "
                f"{result.overall_score:.2f} (skill:{result.skill_score:.2f}, "
                f"exp:{result.experience_score:.2f}, loc:{result.location_score:.2f})"
            )
            
            # Return as dict for backward compatibility with tests
            return result.to_dict()

        except Exception as e:
            logger.error(f"Error calculating match: {e}", exc_info=True)
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

    def _analyze_skills_config_driven(
        self, 
        job_text: str, 
        profile_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Config-driven skills analysis with O(1) lookups
        
        Uses:
        - skill_lookup dict for fast skill matching
        - skill_variations for synonym handling
        """
        if not profile_skills:
            return 0.0, [], []

        matched_skills = []
        profile_skills_normalized = []

        # Normalize profile skills
        for skill in profile_skills:
            if not skill or not skill.strip():
                continue
            skill_lower = skill.lower().strip()
            profile_skills_normalized.append((skill_lower, skill))

        # Fast O(1) skill matching using lookup dicts
        for skill_lower, skill_display in profile_skills_normalized:
            # Check direct match in skill database
            if skill_lower in self.skill_lookup:
                if self._skill_found_in_text_fast(skill_lower, job_text):
                    matched_skills.append(skill_display)
                continue
            
            # Check skill variations/synonyms
            canonical = self.skill_variations.get(skill_lower)
            if canonical and self._skill_found_in_text_fast(canonical, job_text):
                matched_skills.append(skill_display)
                continue
            
            # Fallback: direct text search for custom skills
            if self._skill_found_in_text_fast(skill_lower, job_text):
                matched_skills.append(skill_display)

        # Calculate score
        if profile_skills_normalized:
            score = min(len(matched_skills) / len(profile_skills_normalized), 1.0)
        else:
            score = 0.0

        # Identify missing critical skills (top 5)
        missing_skills = []
        critical_skills = profile_skills_normalized[:5]
        
        for skill_lower, skill_display in critical_skills:
            if skill_display not in matched_skills:
                missing_skills.append(skill_display)

        return score, matched_skills, missing_skills

    def _skill_found_in_text_fast(self, skill: str, text: str) -> bool:
        """
        Optimized skill matching with O(1) variations lookup
        
        Args:
            skill: Skill name (lowercase)
            text: Job text (lowercase)
        
        Returns:
            True if skill found in text
        """
        # Direct substring match (fastest)
        if skill in text:
            return True

        # Word boundary match for exact terms
        try:
            if re.search(rf"\b{re.escape(skill)}\b", text):
                return True
        except re.error:
            pass

        # Check variations from config
        canonical = self.skill_variations.get(skill)
        if canonical and canonical != skill:
            if canonical in text:
                return True
            try:
                if re.search(rf"\b{re.escape(canonical)}\b", text):
                    return True
            except re.error:
                pass

        return False

    def _analyze_experience_config_driven(
        self, 
        job_text: str, 
        job_title: str, 
        profile: Dict[str, Any]
    ) -> Tuple[float, str]:
        """
        Experience analysis using config-driven patterns
        
        Uses pre-compiled regex patterns from experience_level_patterns config
        """
        # Extract required experience from job
        job_experience_level = self._extract_experience_level_config_driven(
            job_text + " " + job_title
        )
        
        # Get profile experience
        profile_years = profile.get("years_of_experience", 0)
        profile_level = self._categorize_experience_years(profile_years)
        
        # Calculate match score
        level_hierarchy = ["entry_level", "mid_level", "senior_level", "executive_level"]
        
        try:
            job_idx = level_hierarchy.index(job_experience_level)
            profile_idx = level_hierarchy.index(profile_level)
            
            if profile_idx >= job_idx:
                score = 1.0  # Overqualified or perfect match
                fit_msg = f"✅ Good fit ({profile_years}y for {job_experience_level.replace('_', ' ')})"
            elif profile_idx == job_idx - 1:
                score = 0.75  # Slightly underqualified
                fit_msg = f"⚠️ Stretch role ({profile_years}y for {job_experience_level.replace('_', ' ')})"
            else:
                score = 0.50  # Underqualified
                fit_msg = f"❌ Underqualified ({profile_years}y for {job_experience_level.replace('_', ' ')})"
        except ValueError:
            score = 0.60  # Unknown levels
            fit_msg = f"Profile: {profile_years}y, Job level unclear"
        
        return score, fit_msg

    def _extract_experience_level_config_driven(self, text: str) -> str:
        """
        Extract experience level using config-driven patterns
        
        Uses pre-compiled regex patterns from matching_config
        """
        text_lower = text.lower()
        
        # Check each level's patterns (from config)
        for level, compiled_patterns in self.experience_compiled.items():
            for pattern in compiled_patterns:
                if pattern.search(text_lower):
                    return level
        
        return "mid_level"  # Default

    def _categorize_experience_years(self, years: int) -> str:
        """Categorize years into experience level"""
        if years <= 2:
            return "entry_level"
        elif years <= 5:
            return "mid_level"
        elif years <= 10:
            return "senior_level"
        else:
            return "executive_level"

    def _analyze_location_config_driven(
        self, 
        job: Dict[str, Any], 
        profile: Dict[str, Any]
    ) -> Tuple[float, str]:
        """
        Location analysis using config-driven keyword matching
        
        Uses location_preferences from matching_config
        """
        job_location = str(job.get("location", "")).lower()
        profile_location = str(profile.get("location", "")).lower()
        profile_remote_pref = profile.get("remote_preference", "").lower()
        
        # Check remote match (highest priority)
        if any(kw in job_location for kw in self.location_keywords.get("remote", set())):
            if profile_remote_pref in ["remote", "full remote", "100% remote"]:
                return 1.0, "🟢 Remote match"
            return 0.8, "🟡 Remote available"
        
        # Check location match
        if profile_location and profile_location in job_location:
            return 1.0, f"🟢 Location match: {profile_location}"
        
        # Check hybrid
        if any(kw in job_location for kw in self.location_keywords.get("hybrid", set())):
            if "hybrid" in profile_remote_pref or "flexible" in profile_remote_pref:
                return 0.9, "🟢 Hybrid match"
            return 0.7, "🟡 Hybrid available"
        
        # No clear match
        return 0.5, f"⚠️ Location: {job_location or 'Not specified'}"

    def _analyze_salary_fit(
        self, 
        job: Dict[str, Any], 
        profile: Dict[str, Any]
    ) -> Tuple[float, str]:
        """
        Salary analysis (placeholder - full implementation uses salary_config.json)
        
        TODO: Refactor to use config/salary_config.json patterns
        """
        # Get salary data
        job_salary_min = job.get("salary_min")
        job_salary_max = job.get("salary_max")
        expected_min = profile.get("expected_salary_min", 0)
        expected_max = profile.get("expected_salary_max", 999999)
        
        if not job_salary_min and not job_salary_max:
            return 0.5, "⚠️ Salary not disclosed"
        
        job_min = job_salary_min or 0
        job_max = job_salary_max or 999999
        
        # Check overlap
        if job_max >= expected_min and job_min <= expected_max:
            overlap = min(job_max, expected_max) - max(job_min, expected_min)
            total_range = max(job_max, expected_max) - min(job_min, expected_min)
            score = overlap / total_range if total_range > 0 else 0.5
            return score, f"🟢 Salary: ${job_min:,}-${job_max:,}"
        
        return 0.3, f"❌ Salary below expectations"

    def _determine_readiness_config_driven(
        self, 
        result: MatchResult
    ) -> Tuple[str, List[str]]:
        """
        Determine application readiness using config criteria
        
        Uses readiness_criteria from matching_config
        """
        criteria = self.matching_config.get("readiness_criteria", {})
        reasons = []
        
        # Check "apply_now" criteria
        apply_now = criteria.get("apply_now", {})
        if (result.overall_score >= apply_now.get("min_overall_score", 0.75) and
            result.skill_score >= apply_now.get("min_skill_match", 0.70) and
            len(result.missing_skills) <= apply_now.get("max_critical_missing", 1)):
            
            reasons.append(f"Strong overall match ({result.overall_score:.0%})")
            reasons.append(f"Good skill alignment ({result.skill_score:.0%})")
            if result.matched_skills:
                reasons.append(f"Matched {len(result.matched_skills)} skills")
            return "🟢 Apply Now", reasons
        
        # Check "consider" criteria
        consider = criteria.get("consider", {})
        if (result.overall_score >= consider.get("min_overall_score", 0.55) and
            result.skill_score >= consider.get("min_skill_match", 0.50)):
            
            reasons.append(f"Moderate match ({result.overall_score:.0%})")
            if result.missing_skills:
                reasons.append(f"Missing: {', '.join(result.missing_skills[:3])}")
            return "🟡 Consider", reasons
        
        # Skip
        reasons.append(f"Low match score ({result.overall_score:.0%})")
        if len(result.missing_skills) > 3:
            reasons.append(f"Missing {len(result.missing_skills)} critical skills")
        return "🔴 Skip", reasons

    def _calculate_confidence(self, job: Dict[str, Any], result: MatchResult) -> float:
        """Calculate match confidence based on data availability"""
        confidence_factors = self.matching_config.get("confidence_factors", {})
        required_fields = confidence_factors.get("required_fields", {})
        
        available_score = 0.0
        total_weight = 0.0
        
        for field, weight in required_fields.items():
            total_weight += weight
            if job.get(field):
                available_score += weight
        
        confidence = available_score / total_weight if total_weight > 0 else 0.5
        return min(confidence, 1.0)


# Convenience function for easy usage
def create_matcher(config_dir: Optional[str] = None) -> ConfigDrivenMatcher:
    """
    Create a config-driven matcher instance
    
    Args:
        config_dir: Optional path to config directory
    
    Returns:
        ConfigDrivenMatcher instance
    """
    return ConfigDrivenMatcher(config_dir)


if __name__ == "__main__":
    # Test the config-driven matcher
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Config-Driven Matcher V2...")
    
    matcher = create_matcher()
    
    # Sample test data
    test_job = {
        "title": "Senior Python Developer",
        "description": "Looking for an experienced Python developer with 5+ years of experience. Must have Django, PostgreSQL, and AWS skills.",
        "location": "Toronto, ON",
        "salary_min": 90000,
        "salary_max": 120000
    }
    
    test_profile = {
        "skills": ["Python", "Django", "PostgreSQL", "AWS", "Docker"],
        "years_of_experience": 6,
        "location": "Toronto",
        "remote_preference": "hybrid",
        "expected_salary_min": 85000,
        "expected_salary_max": 115000
    }
    
    result = matcher.calculate_match(test_job, test_profile)
    
    print(f"\n=== Match Results ===")
    print(f"Overall Score: {result.overall_score:.2%}")
    print(f"Skill Score: {result.skill_score:.2%}")
    print(f"Experience Score: {result.experience_score:.2%}")
    print(f"Location Score: {result.location_score:.2%}")
    print(f"Readiness: {result.readiness_level}")
    print(f"Matched Skills: {result.matched_skills}")
    print(f"Processing Time: {result.processing_time_ms:.2f}ms")
