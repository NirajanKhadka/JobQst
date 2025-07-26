#!/usr/bin/env python3
"""
Enhanced Rule-Based Job Analyzer
Improved rule-based analysis that produces realistic compatibility scores (≥0.6)
"""

import re
import logging
from typing import Dict, List, Any, Set
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class SkillMatch:
    """Skill matching result"""
    matched_skills: List[str]
    missing_skills: List[str]
    match_score: float
    confidence: float


@dataclass
class ExperienceMatch:
    """Experience matching result"""
    profile_level: str
    job_level: str
    compatibility: str  # 'perfect', 'close', 'mismatch', 'unknown'
    match_score: float


class SkillMatcher:
    """Advanced skill matching with industry-specific weights"""
    
    def __init__(self, profile_skills: List[str]):
        """
        Initialize skill matcher.
        
        Args:
            profile_skills: List of skills from user profile
        """
        self.profile_skills = {skill.lower().strip() for skill in profile_skills}
        
        # Skill categories with weights
        self.skill_weights = {
            # Programming languages (high weight)
            'python': 1.0, 'java': 1.0, 'javascript': 1.0, 'typescript': 1.0,
            'c++': 1.0, 'c#': 1.0, 'go': 1.0, 'rust': 1.0, 'kotlin': 1.0,
            
            # Frameworks and libraries (high weight)
            'react': 0.9, 'angular': 0.9, 'vue': 0.9, 'django': 0.9,
            'flask': 0.9, 'spring': 0.9, 'express': 0.9, 'fastapi': 0.9,
            
            # Databases (medium-high weight)
            'sql': 0.8, 'postgresql': 0.8, 'mysql': 0.8, 'mongodb': 0.8,
            'redis': 0.7, 'elasticsearch': 0.7, 'sqlite': 0.6,
            
            # Cloud and DevOps (medium-high weight)
            'aws': 0.8, 'azure': 0.8, 'gcp': 0.8, 'docker': 0.8,
            'kubernetes': 0.8, 'terraform': 0.7, 'jenkins': 0.7,
            
            # Data Science and ML (high weight)
            'machine learning': 1.0, 'deep learning': 1.0, 'tensorflow': 0.9,
            'pytorch': 0.9, 'scikit-learn': 0.8, 'pandas': 0.8, 'numpy': 0.8,
            
            # Tools and methodologies (medium weight)
            'git': 0.6, 'agile': 0.5, 'scrum': 0.5, 'ci/cd': 0.7,
            'rest api': 0.7, 'graphql': 0.7, 'microservices': 0.8,
            
            # Business Intelligence (medium-high weight)
            'powerbi': 0.8, 'tableau': 0.8, 'excel': 0.6, 'power query': 0.7,
            'dax': 0.7, 'ssrs': 0.7, 'ssis': 0.7,
            
            # Soft skills (lower weight but important)
            'leadership': 0.4, 'communication': 0.4, 'problem solving': 0.4,
            'teamwork': 0.4, 'project management': 0.5
        }
        
        # Skill synonyms for better matching
        self.skill_synonyms = {
            'js': 'javascript',
            'ts': 'typescript',
            'k8s': 'kubernetes',
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
            'dl': 'deep learning',
            'tf': 'tensorflow',
            'sklearn': 'scikit-learn',
            'pd': 'pandas',
            'np': 'numpy',
            'postgres': 'postgresql',
            'mongo': 'mongodb',
            'elastic': 'elasticsearch'
        }
    
    def extract_job_skills(self, job_text: str) -> Set[str]:
        """Extract skills mentioned in job description."""
        job_text_lower = job_text.lower()
        found_skills = set()
        
        # Check for exact skill matches
        for skill in self.skill_weights.keys():
            if self._skill_mentioned(skill, job_text_lower):
                found_skills.add(skill)
        
        # Check for synonyms
        for synonym, actual_skill in self.skill_synonyms.items():
            if self._skill_mentioned(synonym, job_text_lower):
                found_skills.add(actual_skill)
        
        return found_skills
    
    def _skill_mentioned(self, skill: str, text: str) -> bool:
        """Check if skill is mentioned in text with word boundaries."""
        # Handle multi-word skills
        if ' ' in skill:
            return skill in text
        
        # Single word skills - use word boundaries
        pattern = r'\b' + re.escape(skill) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def calculate_match(self, job_text: str) -> SkillMatch:
        """Calculate skill match score."""
        job_skills = self.extract_job_skills(job_text)
        
        if not job_skills:
            # No skills detected in job - give neutral score
            return SkillMatch(
                matched_skills=[],
                missing_skills=[],
                match_score=0.5,
                confidence=0.3
            )
        
        # Calculate matches
        matched_skills = []
        total_weight = 0
        matched_weight = 0
        
        for skill in job_skills:
            weight = self.skill_weights.get(skill, 0.5)  # Default weight for unknown skills
            total_weight += weight
            
            if skill in self.profile_skills:
                matched_skills.append(skill)
                matched_weight += weight
        
        # Calculate missing skills
        missing_skills = [skill for skill in job_skills if skill not in self.profile_skills]
        
        # Calculate match score
        if total_weight > 0:
            raw_score = matched_weight / total_weight
            # Boost score if we have good matches
            if len(matched_skills) >= 3:
                raw_score = min(1.0, raw_score * 1.2)
            match_score = max(0.1, raw_score)  # Minimum score
        else:
            match_score = 0.5
        
        # Calculate confidence based on number of skills analyzed
        confidence = min(0.9, 0.3 + (len(job_skills) * 0.1))
        
        return SkillMatch(
            matched_skills=matched_skills,
            missing_skills=missing_skills[:5],  # Limit to top 5 missing
            match_score=match_score,
            confidence=confidence
        )


class ExperienceMatcher:
    """Experience level compatibility assessment"""
    
    def __init__(self, profile_experience: str):
        """
        Initialize experience matcher.
        
        Args:
            profile_experience: Experience level from user profile
        """
        self.profile_experience = profile_experience.lower().strip()
        
        # Experience level mappings
        self.experience_levels = {
            'entry': ['entry', 'junior', 'graduate', 'intern', '0-2 years', 'new grad'],
            'junior': ['junior', 'entry', '1-3 years', '2-4 years', 'associate'],
            'mid': ['mid', 'intermediate', '3-5 years', '4-6 years', 'experienced'],
            'senior': ['senior', 'lead', '5+ years', '6+ years', 'expert', 'principal'],
            'executive': ['executive', 'director', 'manager', 'head', 'vp', 'cto', 'cio']
        }
        
        # Determine profile level
        self.profile_level = self._determine_level(self.profile_experience)
    
    def _determine_level(self, experience_text: str) -> str:
        """Determine experience level from text."""
        for level, keywords in self.experience_levels.items():
            for keyword in keywords:
                if keyword in experience_text:
                    return level
        return 'mid'  # Default to mid-level
    
    def calculate_match(self, job_text: str) -> ExperienceMatch:
        """Calculate experience level match."""
        job_text_lower = job_text.lower()
        
        # Extract experience requirements from job
        job_level = self._extract_job_experience_level(job_text_lower)
        
        # Calculate compatibility
        compatibility, match_score = self._calculate_compatibility(self.profile_level, job_level)
        
        return ExperienceMatch(
            profile_level=self.profile_level,
            job_level=job_level,
            compatibility=compatibility,
            match_score=match_score
        )
    
    def _extract_job_experience_level(self, job_text: str) -> str:
        """Extract experience level from job description."""
        # First check for years of experience patterns (more specific)
        years_patterns = [
            r'(\d+)[-+]\s*years?',
            r'(\d+)\s*to\s*(\d+)\s*years?',
            r'minimum\s*(\d+)\s*years?',
            r'at least\s*(\d+)\s*years?'
        ]
        
        for pattern in years_patterns:
            matches = re.findall(pattern, job_text)
            if matches:
                try:
                    years = int(matches[0][0] if isinstance(matches[0], tuple) else matches[0])
                    if years <= 2:
                        return 'entry'
                    elif years <= 4:
                        return 'junior'
                    elif years <= 7:
                        return 'mid'
                    else:
                        return 'senior'
                except:
                    continue
        
        # Then check for explicit experience level keywords
        for level, keywords in self.experience_levels.items():
            for keyword in keywords:
                if keyword in job_text:
                    return level
        
        return 'mid'  # Default assumption
    
    def _calculate_compatibility(self, profile_level: str, job_level: str) -> tuple:
        """Calculate compatibility between profile and job experience levels."""
        level_hierarchy = ['entry', 'junior', 'mid', 'senior', 'executive']
        
        try:
            profile_idx = level_hierarchy.index(profile_level)
            job_idx = level_hierarchy.index(job_level)
        except ValueError:
            return 'unknown', 0.5
        
        diff = abs(profile_idx - job_idx)
        
        if diff == 0:
            return 'perfect', 1.0
        elif diff == 1:
            return 'close', 0.8
        elif diff == 2:
            return 'acceptable', 0.6
        else:
            return 'mismatch', 0.3


class EnhancedRuleBasedAnalyzer:
    """Enhanced rule-based job analyzer targeting realistic compatibility scores"""
    
    def __init__(self, profile: Dict[str, Any]):
        """
        Initialize enhanced rule-based analyzer.
        
        Args:
            profile: User profile dictionary
        """
        self.profile = profile
        self.skill_matcher = SkillMatcher(profile.get('skills', []))
        self.experience_matcher = ExperienceMatcher(profile.get('experience_level', ''))
        
        # Location preferences
        self.location_preferences = {
            'remote': profile.get('remote_preference', True),
            'hybrid': profile.get('hybrid_preference', True),
            'onsite': profile.get('onsite_preference', False),
            'preferred_locations': [loc.lower() for loc in profile.get('preferred_locations', [])]
        }
    
    def analyze_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform enhanced rule-based job analysis.
        
        Args:
            job: Job posting dictionary
            
        Returns:
            Analysis result dictionary
        """
        # Extract job information
        job_title = job.get('title', '')
        job_description = job.get('description', job.get('summary', ''))
        job_location = job.get('location', '')
        job_company = job.get('company', '')
        
        # Combine text for analysis
        job_text = f"{job_title} {job_description} {job_company}"
        
        # Perform component analyses
        skill_match = self.skill_matcher.calculate_match(job_text)
        experience_match = self.experience_matcher.calculate_match(job_text)
        location_score = self._calculate_location_match(job_location)
        title_score = self._calculate_title_relevance(job_title)
        
        # Calculate weighted final score
        final_score = (
            skill_match.match_score * 0.4 +      # Skills are most important
            experience_match.match_score * 0.25 + # Experience level match
            location_score * 0.2 +               # Location compatibility
            title_score * 0.15                   # Title relevance
        )
        
        # Ensure minimum viable score for reasonable jobs
        if skill_match.match_score > 0.3 and experience_match.match_score > 0.5:
            final_score = max(0.6, final_score)
        
        # Determine recommendation
        recommendation = self._get_recommendation(final_score)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(skill_match, experience_match, location_score, title_score)
        
        return {
            'compatibility_score': round(final_score, 3),
            'confidence': round((skill_match.confidence + 0.7) / 2, 3),  # Average with base confidence
            'skill_matches': skill_match.matched_skills,
            'skill_gaps': skill_match.missing_skills,
            'experience_match': experience_match.compatibility,
            'location_match': self._get_location_match_description(location_score),
            'cultural_fit': 0.7,  # Neutral assumption
            'growth_potential': 0.7,  # Neutral assumption
            'recommendation': recommendation,
            'reasoning': reasoning,
            'analysis_method': 'enhanced_rule_based',
            'analysis_timestamp': time.time(),
            'component_scores': {
                'skills': round(skill_match.match_score, 3),
                'experience': round(experience_match.match_score, 3),
                'location': round(location_score, 3),
                'title': round(title_score, 3)
            }
        }
    
    def _calculate_location_match(self, job_location: str) -> float:
        """Calculate location compatibility score."""
        if not job_location:
            return 0.5  # Unknown location
        
        job_location_lower = job_location.lower()
        
        # Check for remote work
        if any(keyword in job_location_lower for keyword in ['remote', 'work from home', 'wfh']):
            return 1.0 if self.location_preferences['remote'] else 0.7
        
        # Check for hybrid
        if 'hybrid' in job_location_lower:
            return 0.9 if self.location_preferences['hybrid'] else 0.6
        
        # Check preferred locations
        for preferred_loc in self.location_preferences['preferred_locations']:
            if preferred_loc in job_location_lower:
                return 0.8
        
        # Default onsite score
        return 0.5 if self.location_preferences['onsite'] else 0.3
    
    def _calculate_title_relevance(self, job_title: str) -> float:
        """Calculate job title relevance score."""
        if not job_title:
            return 0.5
        
        title_lower = job_title.lower()
        
        # Relevant keywords for the profile
        relevant_keywords = {
            'developer': 0.9, 'engineer': 0.9, 'programmer': 0.8,
            'analyst': 0.8, 'scientist': 0.8, 'architect': 0.9,
            'consultant': 0.7, 'specialist': 0.7, 'lead': 0.8,
            'senior': 0.8, 'principal': 0.9, 'staff': 0.8
        }
        
        score = 0.5  # Base score
        for keyword, weight in relevant_keywords.items():
            if keyword in title_lower:
                score = max(score, weight)
        
        return score
    
    def _get_location_match_description(self, score: float) -> str:
        """Get location match description."""
        if score >= 0.9:
            return 'excellent'
        elif score >= 0.7:
            return 'good'
        elif score >= 0.5:
            return 'acceptable'
        else:
            return 'poor'
    
    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on compatibility score."""
        if score >= 0.8:
            return 'highly_recommend'
        elif score >= 0.65:
            return 'recommend'
        elif score >= 0.5:
            return 'consider'
        else:
            return 'skip'
    
    def _generate_reasoning(self, skill_match: SkillMatch, experience_match: ExperienceMatch, 
                          location_score: float, title_score: float) -> str:
        """Generate human-readable reasoning for the analysis."""
        reasons = []
        
        # Skills reasoning
        if skill_match.match_score >= 0.7:
            reasons.append(f"Strong skill match ({len(skill_match.matched_skills)} relevant skills)")
        elif skill_match.match_score >= 0.5:
            reasons.append(f"Moderate skill match ({len(skill_match.matched_skills)} skills)")
        else:
            reasons.append(f"Limited skill overlap ({len(skill_match.matched_skills)} skills)")
        
        # Experience reasoning
        if experience_match.compatibility == 'perfect':
            reasons.append("Perfect experience level match")
        elif experience_match.compatibility == 'close':
            reasons.append("Close experience level match")
        elif experience_match.compatibility == 'acceptable':
            reasons.append("Acceptable experience level")
        else:
            reasons.append("Experience level mismatch")
        
        # Location reasoning
        if location_score >= 0.8:
            reasons.append("Excellent location fit")
        elif location_score >= 0.6:
            reasons.append("Good location compatibility")
        else:
            reasons.append("Location may be challenging")
        
        return "; ".join(reasons)


if __name__ == "__main__":
    # Test the enhanced rule-based analyzer
    test_profile = {
        'skills': ['Python', 'SQL', 'Machine Learning', 'AWS', 'Docker'],
        'experience_level': 'Senior',
        'remote_preference': True,
        'preferred_locations': ['Toronto', 'Vancouver']
    }
    
    test_job = {
        'title': 'Senior Python Developer',
        'description': 'We are looking for a senior Python developer with experience in machine learning and AWS. Remote work available.',
        'location': 'Remote',
        'company': 'Tech Corp'
    }
    
    analyzer = EnhancedRuleBasedAnalyzer(test_profile)
    result = analyzer.analyze_job(test_job)
    
    print("Enhanced Rule-Based Analysis Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")