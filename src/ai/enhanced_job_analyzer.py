#!/usr/bin/env python3
"""
Enhanced Job Analyzer with Llama3 Integration
Replaces current rule-based similarity logic with AI-powered analysis
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import json

from .llama_job_analyzer import LlamaJobAnalyzer, JobAnalysisResult

logger = logging.getLogger(__name__)

class EnhancedJobAnalyzer:
    """Enhanced job analyzer that uses Llama3 for sophisticated matching"""
    
    def __init__(self, profile: Dict, use_llama: bool = True, fallback_to_rule_based: bool = True):
        """
        Initialize enhanced analyzer
        
        Args:
            profile: User profile dict
            use_llama: Whether to use Llama3 for analysis (default: True)
            fallback_to_rule_based: Fall back to rule-based if Llama3 fails (default: True)
        """
        self.profile = profile
        self.use_llama = use_llama
        self.fallback_to_rule_based = fallback_to_rule_based
        
        # Initialize Llama3 analyzer if requested
        self.llama_analyzer = None
        if use_llama:
            try:
                # Get Ollama model from profile, default to llama3:latest (8B model)
                ollama_model = profile.get("ollama_model", "llama3:latest")
                self.llama_analyzer = LlamaJobAnalyzer(model=ollama_model)
                logger.info(f"✅ Ollama analyzer initialized with model: {ollama_model}")
            except Exception as e:
                logger.warning(f"⚠️ Ollama initialization failed: {e}")
                if not fallback_to_rule_based:
                    raise
        
        # Initialize rule-based analyzer as fallback
        if fallback_to_rule_based or not self.llama_analyzer:
            from ..utils.job_analyzer import JobAnalyzer
            self.rule_based_analyzer = JobAnalyzer(profile)
            logger.info("✅ Rule-based analyzer initialized as fallback")
    
    def analyze_job(self, job: Dict) -> Dict[str, Any]:
        """
        Analyze job compatibility using best available method
        
        Args:
            job: Job posting dict
            
        Returns:
            Enhanced analysis result dict
        """
        # Try Llama3 analysis first
        if self.llama_analyzer:
            try:
                llama_result = self.llama_analyzer.analyze_job(self.profile, job)
                if llama_result:
                    return self._convert_llama_result(llama_result, job)
                else:
                    logger.warning("Llama3 analysis returned None, falling back to rule-based")
            except Exception as e:
                logger.error(f"Llama3 analysis failed: {e}")
        
        # Fallback to rule-based analysis
        if self.fallback_to_rule_based and hasattr(self, 'rule_based_analyzer'):
            logger.info("Using rule-based analysis as fallback")
            return self._enhance_rule_based_result(
                self.rule_based_analyzer.analyze_job(job), job
            )
        
        # No analysis possible
        logger.error("No analysis method available")
        return self._create_empty_result()
    
    def _convert_llama_result(self, llama_result: JobAnalysisResult, job: Dict) -> Dict[str, Any]:
        """Convert Llama3 result to enhanced format"""
        
        # Create comprehensive result
        result = {
            # Core compatibility metrics
            'compatibility_score': llama_result.compatibility_score,
            'relevance_score': llama_result.compatibility_score,  # Alias for backward compatibility
            'confidence': llama_result.confidence,
            
            # Skill analysis
            'skill_matches': llama_result.skill_matches,
            'skill_gaps': llama_result.skill_gaps,
            'skill_match_ratio': len(llama_result.skill_matches) / max(len(self.profile.get('skills', [])), 1),
            
            # Experience and location
            'experience_match': llama_result.experience_match,
            'location_match': llama_result.location_match,
            'salary_assessment': llama_result.salary_assessment,
            
            # Cultural and growth factors
            'cultural_fit': llama_result.cultural_fit,
            'growth_potential': llama_result.growth_potential,
            
            # Recommendation
            'recommendation': llama_result.recommendation,
            'reasoning': llama_result.reasoning,
            
            # Classification
            'match_quality': self._classify_match_quality(llama_result.compatibility_score),
            'application_priority': self._determine_priority(llama_result),
            
            # Metadata
            'analysis_method': 'llama3',
            'analysis_timestamp': self._get_timestamp(),
            
            # Backward compatibility fields
            'match_factors': self._extract_match_factors(llama_result),
            'extracted_skills': llama_result.skill_matches,
            
            # Additional insights
            'insights': {
                'key_strengths': llama_result.skill_matches[:5],  # Top 5 strengths
                'improvement_areas': llama_result.skill_gaps[:3],  # Top 3 gaps
                'career_fit': 'excellent' if llama_result.growth_potential >= 0.8 else 'good' if llama_result.growth_potential >= 0.6 else 'fair',
                'competition_level': self._assess_competition(llama_result, job)
            }
        }
        
        return result
    
    def _enhance_rule_based_result(self, rule_result: Dict, job: Dict) -> Dict[str, Any]:
        """Enhance rule-based result with additional insights"""
        
        # Extract base scores
        base_score = max(
            rule_result.get('compatibility_score', 0),
            rule_result.get('relevance_score', 0)
        )
        
        # Enhanced result with additional analysis
        result = {
            # Base scores from rule-based system
            'compatibility_score': base_score,
            'relevance_score': base_score,
            'confidence': 0.6,  # Medium confidence for rule-based
            
            # Enhanced skill analysis
            'skill_matches': rule_result.get('extracted_skills', []),
            'skill_gaps': self._identify_skill_gaps(job),
            'skill_match_ratio': len(rule_result.get('extracted_skills', [])) / max(len(self.profile.get('skills', [])), 1),
            
            # Basic matching
            'experience_match': self._assess_experience_match(job),
            'location_match': self._assess_location_match(job),
            'salary_assessment': 'unknown',
            
            # Estimated factors
            'cultural_fit': min(base_score + 0.1, 1.0),  # Slight boost
            'growth_potential': 0.5,  # Neutral
            
            # Simple recommendation
            'recommendation': self._simple_recommendation(base_score),
            'reasoning': f"Rule-based analysis with {base_score:.1%} compatibility",
            
            # Classification
            'match_quality': self._classify_match_quality(base_score),
            'application_priority': 'medium' if base_score >= 0.3 else 'low',
            
            # Metadata
            'analysis_method': 'rule_based',
            'analysis_timestamp': self._get_timestamp(),
            
            # Backward compatibility
            'match_factors': rule_result.get('match_factors', []),
            'extracted_skills': rule_result.get('extracted_skills', []),
            
            # Basic insights
            'insights': {
                'key_strengths': rule_result.get('extracted_skills', [])[:3],
                'improvement_areas': ['More detailed analysis needed'],
                'career_fit': 'unknown',
                'competition_level': 'unknown'
            }
        }
        
        return result
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Create empty result when analysis fails"""
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
            'recommendation': 'skip',
            'reasoning': 'Analysis failed',
            'match_quality': 'poor',
            'application_priority': 'skip',
            'analysis_method': 'failed',
            'analysis_timestamp': self._get_timestamp(),
            'match_factors': [],
            'extracted_skills': [],
            'insights': {
                'key_strengths': [],
                'improvement_areas': ['Analysis system unavailable'],
                'career_fit': 'unknown',
                'competition_level': 'unknown'
            }
        }
    
    def _classify_match_quality(self, score: float) -> str:
        """Classify match quality based on score"""
        if score >= 0.8:
            return 'excellent'
        elif score >= 0.6:
            return 'good'
        elif score >= 0.4:
            return 'fair'
        elif score >= 0.2:
            return 'poor'
        else:
            return 'very_poor'
    
    def _determine_priority(self, llama_result: JobAnalysisResult) -> str:
        """Determine application priority"""
        if llama_result.recommendation == 'highly_recommend':
            return 'high'
        elif llama_result.recommendation == 'recommend':
            return 'medium'
        elif llama_result.recommendation == 'consider':
            return 'low'
        else:
            return 'skip'
    
    def _extract_match_factors(self, llama_result: JobAnalysisResult) -> List[str]:
        """Extract match factors for backward compatibility"""
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
    
    def _assess_competition(self, llama_result: JobAnalysisResult, job: Dict) -> str:
        """Assess competition level for the job"""
        # This could be enhanced with more sophisticated analysis
        company = job.get('company', '').lower()
        title = job.get('title', '').lower()
        
        if any(term in company for term in ['google', 'microsoft', 'apple', 'meta', 'amazon']):
            return 'very_high'
        elif 'senior' in title or 'lead' in title:
            return 'high'
        elif 'entry' in title.lower() or 'junior' in title.lower():
            return 'medium'
        else:
            return 'unknown'
    
    def _identify_skill_gaps(self, job: Dict) -> List[str]:
        """Identify potential skill gaps (simple rule-based)"""
        # This is a simplified version - Llama3 does this much better
        text = f"{job.get('title', '')} {job.get('summary', '')} {job.get('description', '')}".lower()
        
        profile_skills = [skill.lower() for skill in self.profile.get('skills', [])]
        
        # Common skills that might be mentioned in jobs
        potential_skills = [
            'python', 'sql', 'java', 'javascript', 'react', 'node', 'aws', 'docker',
            'kubernetes', 'machine learning', 'tensorflow', 'pytorch', 'powerbi',
            'tableau', 'excel', 'git', 'agile', 'scrum'
        ]
        
        gaps = []
        for skill in potential_skills:
            if skill in text and skill not in profile_skills:
                gaps.append(skill)
        
        return gaps[:5]  # Return top 5 gaps
    
    def _assess_experience_match(self, job: Dict) -> str:
        """Assess experience level match (simple rule-based)"""
        profile_exp = self.profile.get('experience_level', '').lower()
        job_exp = job.get('experience_level', '').lower()
        
        if profile_exp in job_exp or job_exp in profile_exp:
            return 'perfect'
        elif 'entry' in profile_exp and 'junior' in job_exp:
            return 'close'
        elif 'junior' in profile_exp and 'entry' in job_exp:
            return 'close'
        else:
            return 'mismatch'
    
    def _assess_location_match(self, job: Dict) -> str:
        """Assess location match (simple rule-based)"""
        profile_loc = self.profile.get('location', '').lower()
        job_loc = job.get('location', '').lower()
        
        if 'remote' in job_loc:
            return 'remote_ok'
        elif profile_loc in job_loc or job_loc in profile_loc:
            return 'perfect'
        elif any(common in profile_loc and common in job_loc for common in ['ontario', 'bc', 'alberta']):
            return 'nearby'
        else:
            return 'mismatch'
    
    def _simple_recommendation(self, score: float) -> str:
        """Simple recommendation based on score"""
        if score >= 0.7:
            return 'highly_recommend'
        elif score >= 0.5:
            return 'recommend'
        elif score >= 0.3:
            return 'consider'
        else:
            return 'skip'
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def batch_analyze_jobs(self, jobs: List[Dict], progress_callback=None) -> List[Dict]:
        """
        Analyze multiple jobs in batch
        
        Args:
            jobs: List of job dicts
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of analysis results
        """
        results = []
        
        for i, job in enumerate(jobs):
            if progress_callback:
                progress_callback(i, len(jobs), job.get('title', 'Unknown'))
            
            analysis = self.analyze_job(job)
            results.append({
                'job': job,
                'analysis': analysis
            })
        
        return results
    
    def get_recommendations(self, jobs: List[Dict], min_score: float = 0.3) -> List[Dict]:
        """
        Get job recommendations above minimum score
        
        Args:
            jobs: List of job dicts
            min_score: Minimum compatibility score (default: 0.3)
            
        Returns:
            List of recommended jobs with analysis
        """
        results = self.batch_analyze_jobs(jobs)
        
        # Filter and sort by score
        recommendations = [
            result for result in results 
            if result['analysis']['compatibility_score'] >= min_score
        ]
        
        recommendations.sort(
            key=lambda x: x['analysis']['compatibility_score'], 
            reverse=True
        )
        
        return recommendations

# Backward compatibility wrapper
class JobAnalyzer(EnhancedJobAnalyzer):
    """Backward compatible JobAnalyzer with Llama3 enhancement"""
    
    def __init__(self, profile: Dict):
        super().__init__(profile, use_llama=True, fallback_to_rule_based=True)
        
    def analyze_job(self, job: Dict) -> Dict[str, Any]:
        """Analyze job with enhanced capabilities"""
        return super().analyze_job(job)
