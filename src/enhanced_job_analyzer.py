#!/usr/bin/env python3
"""
Enhanced Job Analyzer with Llama3 Integration
Replaces current rule-based similarity logic with AI-powered analysis
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import json

from src.ai.llama_job_analyzer import LlamaJobAnalyzer, JobAnalysisResult

logger = logging.getLogger(__name__)

# --- Constants for Analysis ---
ANALYSIS_METHOD_LLAMA3 = 'llama3'
ANALYSIS_METHOD_RULE_BASED = 'rule_based'
ANALYSIS_METHOD_FAILED = 'failed'

MATCH_QUALITY_EXCELLENT = 'excellent'
MATCH_QUALITY_GOOD = 'good'
MATCH_QUALITY_FAIR = 'fair'
MATCH_QUALITY_POOR = 'poor'
MATCH_QUALITY_VERY_POOR = 'very_poor'

PRIORITY_HIGH = 'high'
PRIORITY_MEDIUM = 'medium'
PRIORITY_LOW = 'low'
PRIORITY_SKIP = 'skip'


class EnhancedJobAnalyzer:
    """Enhanced job analyzer that uses Llama3 for sophisticated matching"""

    def __init__(self, profile: Dict, use_llama: bool = True, fallback_to_rule_based: bool = True):
        """
        Initialize enhanced analyzer.

        Args:
            profile: User profile dict.
            use_llama: Whether to use Llama3 for analysis (default: True).
            fallback_to_rule_based: Fall back to rule-based if Llama3 fails (default: True).
        """
        self.profile = profile
        self.use_llama = use_llama
        self.fallback_to_rule_based = fallback_to_rule_based
        self.llama_analyzer = None
        self.rule_based_analyzer = None

        if self.use_llama:
            self._initialize_llama_analyzer()

        if self.fallback_to_rule_based or not self.llama_analyzer:
            self._initialize_rule_based_analyzer()

    def _initialize_llama_analyzer(self):
        """Initializes the Llama3 analyzer."""
        try:
            ollama_model = self.profile.get("ollama_model", "llama3:latest")
            self.llama_analyzer = LlamaJobAnalyzer(model=ollama_model)
            logger.info(f"✅ Ollama analyzer initialized with model: {ollama_model}")
        except Exception as e:
            logger.warning(f"⚠️ Ollama initialization failed: {e}")
            if not self.fallback_to_rule_based:
                raise

    def _initialize_rule_based_analyzer(self):
        """Initializes the rule-based analyzer."""
        from utils.job_analyzer import JobAnalyzer
        self.rule_based_analyzer = JobAnalyzer(self.profile)
        logger.info("✅ Rule-based analyzer initialized as fallback")

    def analyze_job(self, job: Dict) -> Dict[str, Any]:
        """
        Analyze job compatibility using the best available method.

        Args:
            job: Job posting dict.

        Returns:
            Enhanced analysis result dict.
        """
        if self.llama_analyzer:
            try:
                llama_result = self.llama_analyzer.analyze_job(self.profile, job)
                if llama_result:
                    return self._convert_llama_result(llama_result, job)
                logger.warning("Llama3 analysis returned None, falling back to rule-based")
            except Exception as e:
                logger.error(f"Llama3 analysis failed: {e}")

        if self.fallback_to_rule_based and self.rule_based_analyzer:
            logger.info("Using rule-based analysis as fallback")
            rule_result = self.rule_based_analyzer.analyze_job(job)
            return self._enhance_rule_based_result(rule_result, job)

        logger.error("No analysis method available")
        return self._create_failed_result()

    def _create_base_result(self) -> Dict[str, Any]:
        """Creates a base dictionary for analysis results."""
        return {
            'compatibility_score': 0.0,
            'relevance_score': 0.0,
            'confidence': 0.0,
            'skill_matches': [],
            'skill_gaps': [],
            'skill_match_ratio': 0.0,
            'experience_match': 'unknown',
            'location_match': 'unknown',
            'salary_assessment': 'unknown',
            'cultural_fit': 0.0,
            'growth_potential': 0.0,
            'recommendation': PRIORITY_SKIP,
            'reasoning': 'N/A',
            'match_quality': MATCH_QUALITY_POOR,
            'application_priority': PRIORITY_SKIP,
            'analysis_method': '',
            'analysis_timestamp': datetime.now().isoformat(),
            'match_factors': [],
            'extracted_skills': [],
            'insights': {
                'key_strengths': [],
                'improvement_areas': [],
                'career_fit': 'unknown',
                'competition_level': 'unknown'
            }
        }

    def _convert_llama_result(self, llama_result: JobAnalysisResult, job: Dict) -> Dict[str, Any]:
        """Convert Llama3 result to enhanced format."""
        result = self._create_base_result()
        result.update({
            'compatibility_score': llama_result.compatibility_score,
            'relevance_score': llama_result.compatibility_score,
            'confidence': llama_result.confidence,
            'skill_matches': llama_result.skill_matches,
            'skill_gaps': llama_result.skill_gaps,
            'skill_match_ratio': len(llama_result.skill_matches) / max(len(self.profile.get('skills', [])), 1),
            'experience_match': llama_result.experience_match,
            'location_match': llama_result.location_match,
            'salary_assessment': llama_result.salary_assessment,
            'cultural_fit': llama_result.cultural_fit,
            'growth_potential': llama_result.growth_potential,
            'recommendation': llama_result.recommendation,
            'reasoning': llama_result.reasoning,
            'match_quality': self._classify_match_quality(llama_result.compatibility_score),
            'application_priority': self._determine_priority(llama_result),
            'analysis_method': ANALYSIS_METHOD_LLAMA3,
            'match_factors': self._extract_match_factors(llama_result),
            'extracted_skills': llama_result.skill_matches,
            'insights': {
                'key_strengths': llama_result.skill_matches[:5],
                'improvement_areas': llama_result.skill_gaps[:3],
                'career_fit': 'excellent' if llama_result.growth_potential >= 0.8 else 'good' if llama_result.growth_potential >= 0.6 else 'fair',
                'competition_level': self._assess_competition(job)
            }
        })
        return result

    def _enhance_rule_based_result(self, rule_result: Dict, job: Dict) -> Dict[str, Any]:
        """Enhance rule-based result with additional insights."""
        base_score = max(rule_result.get('compatibility_score', 0), rule_result.get('relevance_score', 0))
        result = self._create_base_result()
        result.update({
            'compatibility_score': base_score,
            'relevance_score': base_score,
            'confidence': 0.6,
            'skill_matches': rule_result.get('extracted_skills', []),
            'skill_gaps': self._identify_skill_gaps(job),
            'skill_match_ratio': len(rule_result.get('extracted_skills', [])) / max(len(self.profile.get('skills', [])), 1),
            'experience_match': self._assess_experience_match(job),
            'location_match': self._assess_location_match(job),
            'cultural_fit': min(base_score + 0.1, 1.0),
            'growth_potential': 0.5,
            'recommendation': self._simple_recommendation(base_score),
            'reasoning': f"Rule-based analysis with {base_score:.1%} compatibility",
            'match_quality': self._classify_match_quality(base_score),
            'application_priority': PRIORITY_MEDIUM if base_score >= 0.3 else PRIORITY_LOW,
            'analysis_method': ANALYSIS_METHOD_RULE_BASED,
            'match_factors': rule_result.get('match_factors', []),
            'extracted_skills': rule_result.get('extracted_skills', []),
            'insights': {
                'key_strengths': rule_result.get('extracted_skills', [])[:3],
                'improvement_areas': ['More detailed analysis needed'],
                'career_fit': 'unknown',
                'competition_level': 'unknown'
            }
        })
        return result

    def _create_failed_result(self) -> Dict[str, Any]:
        """Create a result for when analysis fails completely."""
        result = self._create_base_result()
        result.update({
            'reasoning': 'Analysis failed',
            'analysis_method': ANALYSIS_METHOD_FAILED,
            'insights': {
                'improvement_areas': ['Analysis system unavailable'],
            }
        })
        return result

    def _classify_match_quality(self, score: float) -> str:
        """Classify match quality based on score."""
        if score >= 0.8:
            return MATCH_QUALITY_EXCELLENT
        if score >= 0.6:
            return MATCH_QUALITY_GOOD
        if score >= 0.4:
            return MATCH_QUALITY_FAIR
        if score >= 0.2:
            return MATCH_QUALITY_POOR
        return MATCH_QUALITY_VERY_POOR

    def _determine_priority(self, llama_result: JobAnalysisResult) -> str:
        """Determine application priority from Llama3 result."""
        recommendation_map = {
            'highly_recommend': PRIORITY_HIGH,
            'recommend': PRIORITY_MEDIUM,
            'consider': PRIORITY_LOW,
        }
        return recommendation_map.get(llama_result.recommendation, PRIORITY_SKIP)

    def _extract_match_factors(self, llama_result: JobAnalysisResult) -> List[str]:
        """Extract human-readable match factors for backward compatibility."""
        factors = []
        if llama_result.skill_matches:
            factors.append(f"Skills match: {len(llama_result.skill_matches)} skills found")
        if llama_result.experience_match in ['perfect', 'close']:
            factors.append(f"Experience level: {llama_result.experience_match}")
        if llama_result.location_match in ['perfect', 'nearby', 'remote_ok']:
            factors.append(f"Location: {llama_result.location_match}")
        if llama_result.cultural_fit >= 0.7:
            factors.append("Good cultural fit")
        if llama_result.growth_potential >= 0.7:
            factors.append("High growth potential")
        return factors

    def _assess_competition(self, job: Dict) -> str:
        """Assess competition level for the job based on simple heuristics."""
        company = job.get('company', '').lower()
        title = job.get('title', '').lower()

        if any(term in company for term in ['google', 'microsoft', 'apple', 'meta', 'amazon']):
            return 'very_high'
        if 'senior' in title or 'lead' in title:
            return 'high'
        if 'entry' in title or 'junior' in title:
            return 'medium'
        return 'unknown'

    def _identify_skill_gaps(self, job: Dict) -> List[str]:
        """Identify potential skill gaps using a simple rule-based approach."""
        text = f"{job.get('title', '')} {job.get('summary', '')} {job.get('description', '')}".lower()
        profile_skills = {skill.lower() for skill in self.profile.get('skills', [])}
        
        potential_skills = {
            'python', 'sql', 'java', 'javascript', 'react', 'node', 'aws', 'docker',
            'kubernetes', 'machine learning', 'tensorflow', 'pytorch', 'powerbi',
            'tableau', 'excel', 'git', 'agile', 'scrum'
        }
        
        return [skill for skill in potential_skills if skill in text and skill not in profile_skills][:5]

    def _assess_experience_match(self, job: Dict) -> str:
        """Assess experience level match using a simple rule-based approach."""
        profile_exp = self.profile.get('experience_level', '').lower()
        job_exp = job.get('experience_level', '').lower()

        if not profile_exp or not job_exp:
            return 'unknown'
        if profile_exp in job_exp or job_exp in profile_exp:
            return 'perfect'
        if ('entry' in profile_exp and 'junior' in job_exp) or \
           ('junior' in profile_exp and 'entry' in job_exp):
            return 'close'
        return 'mismatch'

    def _assess_location_match(self, job: Dict) -> str:
        """Assess location match using a simple rule-based approach."""
        profile_loc = self.profile.get('location', '').lower()
        job_loc = job.get('location', '').lower()

        if 'remote' in job_loc:
            return 'remote_ok'
        if not profile_loc or not job_loc:
            return 'unknown'
        if profile_loc in job_loc or job_loc in profile_loc:
            return 'perfect'
        if any(common in profile_loc and common in job_loc for common in ['ontario', 'bc', 'alberta']):
            return 'nearby'
        return 'mismatch'

    def _simple_recommendation(self, score: float) -> str:
        """Generate a simple recommendation based on a numerical score."""
        if score >= 0.7:
            return 'highly_recommend'
        if score >= 0.5:
            return 'recommend'
        if score >= 0.3:
            return 'consider'
        return 'skip'

    def batch_analyze_jobs(self, jobs: List[Dict], progress_callback=None) -> List[Dict]:
        """
        Analyze multiple jobs in batch.

        Args:
            jobs: List of job dicts.
            progress_callback: Optional callback for progress updates.

        Returns:
            List of analysis results.
        """
        results = []
        total_jobs = len(jobs)
        for i, job in enumerate(jobs):
            if progress_callback:
                progress_callback(i, total_jobs, job.get('title', 'Unknown'))
            
            analysis = self.analyze_job(job)
            results.append({'job': job, 'analysis': analysis})
        
        return results

    def get_recommendations(self, jobs: List[Dict], min_score: float = 0.3) -> List[Dict]:
        """
        Get job recommendations above a minimum score.

        Args:
            jobs: List of job dicts.
            min_score: Minimum compatibility score (default: 0.3).

        Returns:
            List of recommended jobs with analysis, sorted by score.
        """
        results = self.batch_analyze_jobs(jobs)
        
        recommendations = [
            result for result in results 
            if result['analysis']['compatibility_score'] >= min_score
        ]
        
        recommendations.sort(
            key=lambda x: x['analysis']['compatibility_score'], 
            reverse=True
        )
        
        return recommendations

# --- Backward Compatibility ---
class JobAnalyzer(EnhancedJobAnalyzer):
    """
    Backward compatible JobAnalyzer that leverages the new EnhancedJobAnalyzer.
    This ensures that older parts of the system can still use JobAnalyzer
    while benefiting from the Llama3 enhancements.
    """
    
    def __init__(self, profile: Dict):
        """
        Initializes the backward-compatible analyzer.
        
        Args:
            profile: User profile dict.
        """
        super().__init__(profile, use_llama=True, fallback_to_rule_based=True)
        
    def analyze_job(self, job: Dict) -> Dict[str, Any]:
        """
        Analyze a job using the enhanced capabilities but maintaining the
        expected output format for older components.
        
        Args:
            job: Job posting dict.
            
        Returns:
            Analysis result dict.
        """
        return super().analyze_job(job)
