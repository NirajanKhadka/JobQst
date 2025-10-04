#!/usr/bin/env python3
"""
Config-Driven Skills Extractor V2
Replaces hardcoded skill lists with configuration-driven approach.

Key Improvements over V1:
- Loads 263 skills from skills_database.json (was 500+ hardcoded)
- Uses extraction_patterns.json for pattern-based extraction
- O(1) skill lookups using pre-built dictionaries
- Supports 9 industries with specialized extraction
- Easy to add new skills without code changes
- Performance optimized with caching

Configuration Files Used:
- config/skills_database.json - All industry skills and role patterns
- config/extraction_patterns.json - Extraction patterns and confidence levels
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import time

# Add project root to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class ConfigDrivenSkillsExtractor:
    """
    Config-driven skills extractor with pattern-based extraction
    
    Features:
    - Loads skills from skills_database.json
    - Uses extraction_patterns.json for pattern matching
    - O(1) skill lookups with dictionaries
    - Industry-specific skill extraction
    - Confidence-based pattern weighting
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize config-driven skills extractor
        
        Args:
            config_dir: Path to config directory (auto-detected if not provided)
        """
        start_time = time.time()
        
        # Initialize config loader
        self.config_loader = ConfigLoader(config_dir)
        
        # Load configurations
        self._load_configurations()
        
        # Build lookup structures
        self._build_skill_lookups()
        
        # Compile extraction patterns
        self._compile_extraction_patterns()
        
        init_time = (time.time() - start_time) * 1000
        logger.info(
            f"ConfigDrivenSkillsExtractor initialized in {init_time:.2f}ms "
            f"({len(self.skill_lookup)} skills, {len(self.extraction_patterns)} pattern groups)"
        )

    def _load_configurations(self):
        """Load all required configuration files"""
        # Load skills database
        self.skills_db = self.config_loader.load_config("skills_database.json")
        
        # Load extraction patterns
        self.extraction_config = self.config_loader.load_config("extraction_patterns.json")
        
        logger.debug("All configurations loaded successfully")

    def _build_skill_lookups(self):
        """Build O(1) lookup dictionaries for fast skill matching"""
        
        # Build skill lookup: skill_lower -> (display_name, industry, category)
        self.skill_lookup: Dict[str, Tuple[str, str]] = {}
        
        # Build industry skill sets for quick validation
        self.industry_skills: Dict[str, Set[str]] = {}
        
        # Build all skills set (normalized)
        self.all_skills_normalized: Set[str] = set()
        
        for industry_key, industry_data in self.skills_db.get("industries", {}).items():
            skills = industry_data.get("skills", [])
            
            # Store industry skills
            self.industry_skills[industry_key] = set(skill.lower() for skill in skills)
            
            # Build skill lookup
            for skill in skills:
                skill_lower = skill.lower()
                self.skill_lookup[skill_lower] = (skill, industry_key)
                self.all_skills_normalized.add(skill_lower)
        
        logger.debug(
            f"Skill lookups built: {len(self.skill_lookup)} skills, "
            f"{len(self.industry_skills)} industries"
        )

    def _compile_extraction_patterns(self):
        """Pre-compile extraction patterns for performance"""
        
        skills_extraction = self.extraction_config.get("skills_extraction", {})
        self.extraction_patterns: Dict[str, Dict[str, Any]] = {}
        
        for pattern_group, pattern_data in skills_extraction.items():
            if pattern_group == "description":
                continue
            
            if isinstance(pattern_data, dict):
                patterns = pattern_data.get("patterns", [])
                compiled = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns]
                
                self.extraction_patterns[pattern_group] = {
                    "compiled": compiled,
                    "confidence": pattern_data.get("confidence", 0.5),
                    "weight": pattern_data.get("weight", "medium")
                }
        
        logger.debug(f"Compiled {len(self.extraction_patterns)} pattern groups")

    def extract_skills(
        self,
        job_data: Dict[str, Any],
        max_skills: int = 15,
        industry_filter: Optional[str] = None
    ) -> List[str]:
        """
        Extract skills from job data using config-driven approach
        
        Args:
            job_data: Dictionary containing job posting data
            max_skills: Maximum number of skills to return
            industry_filter: Optional industry key to filter skills
        
        Returns:
            List of extracted skills (top N by confidence)
        """
        start_time = time.time()
        
        # Prepare content
        content = self._prepare_content(job_data)
        
        # Extract skills with confidence scores
        skill_scores: Dict[str, float] = {}
        
        # 1. Pattern-based extraction (high confidence)
        for pattern_group, pattern_info in self.extraction_patterns.items():
            confidence = pattern_info["confidence"]
            
            for pattern in pattern_info["compiled"]:
                matches = pattern.findall(content)
                for match in matches:
                    # Parse skills from matched text
                    skills = self._parse_skills_from_text(match)
                    for skill in skills:
                        skill_lower = skill.lower()
                        if skill_lower in self.skill_lookup:
                            # Add confidence score
                            current_score = skill_scores.get(skill_lower, 0.0)
                            skill_scores[skill_lower] = max(current_score, confidence)
        
        # 2. Direct skill matching in content (medium confidence)
        for skill_lower in self.all_skills_normalized:
            if skill_lower not in skill_scores:  # Only check if not already found
                if self._skill_found_in_content(skill_lower, content):
                    skill_scores[skill_lower] = 0.70  # Medium confidence
        
        # 3. Filter by industry if specified
        if industry_filter and industry_filter in self.industry_skills:
            industry_skill_set = self.industry_skills[industry_filter]
            skill_scores = {
                k: v for k, v in skill_scores.items()
                if k in industry_skill_set
            }
        
        # 4. Sort by confidence and return top skills
        sorted_skills = sorted(
            skill_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:max_skills]
        
        # Return display names (original case)
        result = [self.skill_lookup[skill][0] for skill, _ in sorted_skills]
        
        extract_time = (time.time() - start_time) * 1000
        logger.debug(
            f"Extracted {len(result)} skills in {extract_time:.2f}ms "
            f"(from {len(skill_scores)} candidates)"
        )
        
        return result

    def extract_skills_by_industry(
        self,
        job_data: Dict[str, Any],
        max_skills: int = 15
    ) -> Dict[str, List[str]]:
        """
        Extract skills grouped by industry
        
        Args:
            job_data: Dictionary containing job posting data
            max_skills: Maximum skills per industry
        
        Returns:
            Dictionary mapping industry -> list of skills
        """
        content = self._prepare_content(job_data)
        industry_results: Dict[str, List[Tuple[str, float]]] = {}
        
        # Extract all skills with confidence
        for skill_lower, (skill_display, industry_key) in self.skill_lookup.items():
            if self._skill_found_in_content(skill_lower, content):
                if industry_key not in industry_results:
                    industry_results[industry_key] = []
                
                # Calculate confidence based on context
                confidence = self._calculate_skill_confidence(skill_lower, content)
                industry_results[industry_key].append((skill_display, confidence))
        
        # Sort each industry's skills by confidence
        result = {}
        for industry_key, skills in industry_results.items():
            sorted_skills = sorted(skills, key=lambda x: x[1], reverse=True)
            result[industry_key] = [skill for skill, _ in sorted_skills[:max_skills]]
        
        return result

    def extract_requirements(
        self,
        job_data: Dict[str, Any],
        max_requirements: int = 10
    ) -> List[str]:
        """
        Extract job requirements using extraction patterns
        
        Args:
            job_data: Dictionary containing job posting data
            max_requirements: Maximum number of requirements
        
        Returns:
            List of extracted requirements
        """
        content = self._prepare_content(job_data)
        requirements = set()
        
        # Get requirement patterns from experience extraction config
        exp_config = self.extraction_config.get("experience_extraction", {})
        
        # Also check for qualifications/requirements sections
        requirement_patterns = [
            r"(?i)requirements?[:\s]*\n?([^.\n]{10,200})",
            r"(?i)qualifications?[:\s]*\n?([^.\n]{10,200})",
            r"(?i)must\s*have[:\s]*([^.\n]{10,200})",
            r"(?i)required[:\s]*([^.\n]{10,200})",
        ]
        
        for pattern_str in requirement_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
            matches = pattern.findall(content)
            for match in matches:
                req = match.strip()
                if self._validate_requirement(req):
                    requirements.add(req)
        
        return sorted(list(requirements))[:max_requirements]

    def extract_benefits(
        self,
        job_data: Dict[str, Any],
        max_benefits: int = 10
    ) -> List[str]:
        """
        Extract benefits using extraction patterns from config
        
        Args:
            job_data: Dictionary containing job posting data
            max_benefits: Maximum number of benefits
        
        Returns:
            List of extracted benefits
        """
        content = self._prepare_content(job_data)
        benefits = set()
        
        # Get benefits patterns from extraction config
        benefits_config = self.extraction_config.get("benefits_extraction", {})
        
        for benefit_type, benefit_data in benefits_config.items():
            if benefit_type == "description":
                continue
            
            if isinstance(benefit_data, dict):
                patterns = benefit_data.get("patterns", [])
                for pattern_str in patterns:
                    pattern = re.compile(pattern_str, re.IGNORECASE)
                    if pattern.search(content):
                        # Extract benefit name from pattern
                        benefit_name = benefit_type.replace("_", " ").title()
                        benefits.add(benefit_name)
        
        return sorted(list(benefits))[:max_benefits]

    def _prepare_content(self, job_data: Dict[str, Any]) -> str:
        """Prepare job content for extraction"""
        content_parts = []
        
        # Extract text from multiple fields
        for field in ["description", "job_description", "summary", "requirements", "title"]:
            value = job_data.get(field)
            if value and isinstance(value, str):
                content_parts.append(value)
        
        return "\n".join(content_parts)

    def _parse_skills_from_text(self, text: str) -> List[str]:
        """
        Parse individual skills from text
        
        Args:
            text: Text containing skills (comma/semicolon separated)
        
        Returns:
            List of normalized skill names
        """
        skills = set()
        
        # Split by common delimiters
        skill_candidates = re.split(r"[,;•\n\r\|/]+", text)
        
        for candidate in skill_candidates:
            candidate = candidate.strip()
            if not candidate or len(candidate) < 2:
                continue
            
            # Clean up common noise
            candidate = re.sub(r"^\d+[\.\)]\s*", "", candidate)  # Remove "1. ", "1) "
            candidate = re.sub(r"^[-\*]\s*", "", candidate)  # Remove "- ", "* "
            candidate = candidate.strip()
            
            if len(candidate) < 2 or len(candidate) > 50:
                continue
            
            # Check if it's a known skill
            candidate_lower = candidate.lower()
            if candidate_lower in self.skill_lookup:
                skills.add(candidate_lower)
        
        return list(skills)

    def _skill_found_in_content(self, skill: str, content: str) -> bool:
        """
        Check if skill is found in content with word boundaries
        
        Args:
            skill: Skill name (lowercase)
            content: Content to search in (lowercase)
        
        Returns:
            True if skill found
        """
        content_lower = content.lower()
        
        # Direct substring match (fastest)
        if skill in content_lower:
            # Verify with word boundaries
            try:
                pattern = r"\b" + re.escape(skill) + r"\b"
                if re.search(pattern, content_lower):
                    return True
            except re.error:
                return skill in content_lower
        
        return False

    def _calculate_skill_confidence(self, skill: str, content: str) -> float:
        """
        Calculate confidence score for a skill based on context
        
        Args:
            skill: Skill name (lowercase)
            content: Job content (lowercase)
        
        Returns:
            Confidence score (0.0 - 1.0)
        """
        content_lower = content.lower()
        base_confidence = 0.70
        
        # Boost confidence if skill appears in key sections
        high_confidence_keywords = [
            "required", "must have", "essential", "proficient",
            "experience with", "expertise in", "skills:"
        ]
        
        for keyword in high_confidence_keywords:
            if keyword in content_lower:
                # Check if skill appears near this keyword (within 100 chars)
                keyword_pos = content_lower.find(keyword)
                skill_pos = content_lower.find(skill)
                
                if abs(keyword_pos - skill_pos) < 100:
                    base_confidence = min(base_confidence + 0.15, 0.95)
                    break
        
        # Count occurrences (multiple mentions = higher confidence)
        occurrences = content_lower.count(skill)
        if occurrences > 1:
            base_confidence = min(base_confidence + 0.05 * (occurrences - 1), 0.95)
        
        return base_confidence

    def _validate_requirement(self, requirement: str) -> bool:
        """Validate job requirement"""
        if not requirement:
            return False
        
        # Length check
        if len(requirement) < 10 or len(requirement) > 200:
            return False
        
        # Must have some meaningful content (not just punctuation/numbers)
        alpha_count = sum(c.isalpha() for c in requirement)
        if alpha_count < 5:
            return False
        
        return True

    def get_industry_info(self, industry_key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific industry
        
        Args:
            industry_key: Industry key (e.g., "data_analytics")
        
        Returns:
            Dictionary with industry information or None
        """
        industries = self.skills_db.get("industries", {})
        return industries.get(industry_key)

    def list_industries(self) -> List[Dict[str, Any]]:
        """
        List all available industries
        
        Returns:
            List of dictionaries with industry information
        """
        industries = self.skills_db.get("industries", {})
        result = []
        
        for key, data in industries.items():
            result.append({
                "key": key,
                "name": data.get("name", key),
                "skill_count": len(data.get("skills", [])),
                "role_patterns": len(data.get("role_patterns", []))
            })
        
        return result

    def reload_configs(self):
        """Reload configurations (useful after updating config files)"""
        self.config_loader.clear_cache()
        self._load_configurations()
        self._build_skill_lookups()
        self._compile_extraction_patterns()
        logger.info("Configurations reloaded")


# Convenience function for easy usage
def create_skills_extractor(config_dir: Optional[str] = None) -> ConfigDrivenSkillsExtractor:
    """
    Create a config-driven skills extractor instance
    
    Args:
        config_dir: Optional path to config directory
    
    Returns:
        ConfigDrivenSkillsExtractor instance
    """
    return ConfigDrivenSkillsExtractor(config_dir)


if __name__ == "__main__":
    # Test the config-driven skills extractor
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Config-Driven Skills Extractor V2...")
    
    extractor = create_skills_extractor()
    
    print(f"\nLoaded {len(extractor.skill_lookup)} skills from config")
    print(f"Industries supported: {len(extractor.industry_skills)}")
    
    # List industries
    print("\nAvailable Industries:")
    for industry in extractor.list_industries():
        print(f"  • {industry['name']}: {industry['skill_count']} skills")
    
    # Test extraction
    test_job = {
        "title": "Senior Data Analyst",
        "description": """
        We're looking for a Data Analyst with strong Python and SQL skills.
        
        Requirements:
        - 3+ years of experience with Python, SQL, and Tableau
        - Experience with data visualization and statistical analysis
        - Proficiency in Excel, Pandas, and NumPy
        - Strong communication skills
        
        Benefits:
        - Health insurance
        - 401k matching
        - Remote work options
        """,
        "requirements": "Bachelor's degree in Computer Science or related field"
    }
    
    print("\n=== Test Job ===")
    print(f"Title: {test_job['title']}")
    
    skills = extractor.extract_skills(test_job, max_skills=10)
    print(f"\nExtracted Skills ({len(skills)}):")
    for i, skill in enumerate(skills, 1):
        print(f"  {i}. {skill}")
    
    requirements = extractor.extract_requirements(test_job)
    print(f"\nExtracted Requirements ({len(requirements)}):")
    for i, req in enumerate(requirements, 1):
        print(f"  {i}. {req[:80]}...")
    
    benefits = extractor.extract_benefits(test_job)
    print(f"\nExtracted Benefits ({len(benefits)}):")
    for i, benefit in enumerate(benefits, 1):
        print(f"  {i}. {benefit}")
    
    # Test industry-specific extraction
    print("\n=== Skills by Industry ===")
    by_industry = extractor.extract_skills_by_industry(test_job, max_skills=5)
    for industry, skills in by_industry.items():
        industry_info = extractor.get_industry_info(industry)
        industry_name = industry_info.get("name", industry) if industry_info else industry
        print(f"\n{industry_name}:")
        for skill in skills:
            print(f"  • {skill}")
    
    print("\n✅ Config-Driven Skills Extractor V2 is ready!")
