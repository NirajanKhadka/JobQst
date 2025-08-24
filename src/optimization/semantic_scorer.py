"""
Semantic Scorer for Job-Profile Matching
Implements semantic scoring from AI_STRATEGY_ANALYSIS.md
"""
import logging
from typing import Dict, Any, List, Tuple
from .profile_embedding import get_profile_embedding_service
from .intelligent_cache import get_cache

logger = logging.getLogger(__name__)


class SemanticScorer:
    """
    Semantic scoring system for job-profile matching
    
    Features:
    - Calculates semantic similarity scores
    - Integrates with caching system
    - Provides dashboard analytics
    - Profile-aware scoring
    """
    
    def __init__(self):
        """Initialize semantic scorer"""
        self.embedding_service = get_profile_embedding_service()
        self.cache = get_cache()
        self._stats = {
            'scores_calculated': 0,
            'high_scores': 0,  # > 0.7
            'medium_scores': 0,  # 0.4-0.7
            'low_scores': 0,  # < 0.4
            'cache_efficiency': 0.0
        }
        logger.info("Semantic scorer initialized")
    
    def calculate_job_score(self, profile_name: str,
                           profile_data: Dict[str, Any],
                           job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive semantic score for a job
        
        Args:
            profile_name: Name of the profile
            profile_data: Profile data dictionary
            job_data: Job data dictionary
            
        Returns:
            Dictionary with score and metadata
        """
        try:
            # Calculate semantic similarity
            semantic_score = self.embedding_service.calculate_semantic_similarity(
                profile_name, profile_data, job_data
            )
            
            # Add score to job data for caching
            job_data['semantic_score'] = semantic_score
            job_data['profile_similarity'] = semantic_score
            
            # Update statistics
            self._update_score_stats(semantic_score)
            
            # Determine match quality
            match_quality = self._determine_match_quality(semantic_score)
            
            result = {
                'semantic_score': semantic_score,
                'match_quality': match_quality,
                'profile_name': profile_name,
                'job_id': job_data.get('id', 'unknown'),
                'cache_hit': False,  # Updated by cache system
                'timestamp': self._get_timestamp()
            }
            
            logger.debug(f"Calculated semantic score: {semantic_score:.3f} "
                        f"for job {job_data.get('title', 'unknown')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate job score: {e}")
            return {
                'semantic_score': 0.0,
                'match_quality': 'error',
                'profile_name': profile_name,
                'job_id': job_data.get('id', 'unknown'),
                'cache_hit': False,
                'timestamp': self._get_timestamp(),
                'error': str(e)
            }
    
    def batch_score_jobs(self, profile_name: str,
                        profile_data: Dict[str, Any],
                        jobs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate scores for multiple jobs efficiently
        
        Args:
            profile_name: Name of the profile
            profile_data: Profile data dictionary
            jobs_data: List of job data dictionaries
            
        Returns:
            List of score dictionaries
        """
        try:
            scores = []
            
            for job_data in jobs_data:
                score_result = self.calculate_job_score(
                    profile_name, profile_data, job_data
                )
                scores.append(score_result)
            
            logger.info(f"Calculated {len(scores)} semantic scores "
                       f"for profile {profile_name}")
            
            return scores
            
        except Exception as e:
            logger.error(f"Failed to batch score jobs: {e}")
            return []
    
    def rank_jobs_by_score(self, scored_jobs: List[Dict[str, Any]],
                          min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Rank jobs by semantic score
        
        Args:
            scored_jobs: List of jobs with semantic scores
            min_score: Minimum score threshold
            
        Returns:
            Sorted list of jobs by semantic score (highest first)
        """
        try:
            # Filter by minimum score
            filtered_jobs = [
                job for job in scored_jobs
                if job.get('semantic_score', 0.0) >= min_score
            ]
            
            # Sort by semantic score (descending)
            ranked_jobs = sorted(
                filtered_jobs,
                key=lambda x: x.get('semantic_score', 0.0),
                reverse=True
            )
            
            logger.debug(f"Ranked {len(ranked_jobs)} jobs by semantic score")
            return ranked_jobs
            
        except Exception as e:
            logger.error(f"Failed to rank jobs by score: {e}")
            return scored_jobs
    
    def get_top_matches(self, profile_name: str,
                       profile_data: Dict[str, Any],
                       jobs_data: List[Dict[str, Any]],
                       top_k: int = 10,
                       min_score: float = 0.5) -> List[Dict[str, Any]]:
        """
        Get top K job matches for a profile
        
        Args:
            profile_name: Name of the profile
            profile_data: Profile data dictionary
            jobs_data: List of job data dictionaries
            top_k: Number of top matches to return
            min_score: Minimum similarity score
            
        Returns:
            List of top matching jobs with scores
        """
        try:
            # Calculate scores for all jobs
            scored_jobs = self.batch_score_jobs(
                profile_name, profile_data, jobs_data
            )
            
            # Rank jobs
            ranked_jobs = self.rank_jobs_by_score(scored_jobs, min_score)
            
            # Return top K
            top_matches = ranked_jobs[:top_k]
            
            logger.info(f"Found {len(top_matches)} top matches "
                       f"for profile {profile_name}")
            
            return top_matches
            
        except Exception as e:
            logger.error(f"Failed to get top matches: {e}")
            return []
    
    def _update_score_stats(self, score: float) -> None:
        """Update scoring statistics"""
        self._stats['scores_calculated'] += 1
        
        if score > 0.7:
            self._stats['high_scores'] += 1
        elif score >= 0.4:
            self._stats['medium_scores'] += 1
        else:
            self._stats['low_scores'] += 1
    
    def _determine_match_quality(self, score: float) -> str:
        """Determine match quality based on score"""
        if score >= 0.8:
            return 'excellent'
        elif score >= 0.6:
            return 'good'
        elif score >= 0.4:
            return 'fair'
        else:
            return 'poor'
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_scoring_stats(self) -> Dict[str, Any]:
        """Get scoring statistics for dashboard"""
        stats = self._stats.copy()
        
        total_scores = stats['scores_calculated']
        if total_scores > 0:
            stats['high_score_rate'] = stats['high_scores'] / total_scores
            stats['medium_score_rate'] = stats['medium_scores'] / total_scores
            stats['low_score_rate'] = stats['low_scores'] / total_scores
        else:
            stats['high_score_rate'] = 0.0
            stats['medium_score_rate'] = 0.0
            stats['low_score_rate'] = 0.0
        
        # Add cache stats
        cache_stats = self.cache.get_cache_stats()
        stats['cache_hit_rate'] = cache_stats.get('embedding_hit_rate', 0.0)
        stats['cache_size_mb'] = cache_stats.get('cache_size_mb', 0.0)
        
        # Add embedding stats
        embedding_stats = self.embedding_service.get_stats()
        stats.update(embedding_stats)
        
        return stats
    
    def analyze_score_distribution(self, scores: List[float]) -> Dict[str, Any]:
        """Analyze distribution of scores for dashboard analytics"""
        try:
            if not scores:
                return {
                    'mean': 0.0,
                    'median': 0.0,
                    'std': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'quartiles': [0.0, 0.0, 0.0],
                    'count': 0
                }
            
            import statistics
            
            scores_sorted = sorted(scores)
            n = len(scores)
            
            analysis = {
                'mean': statistics.mean(scores),
                'median': statistics.median(scores),
                'std': statistics.stdev(scores) if n > 1 else 0.0,
                'min': min(scores),
                'max': max(scores),
                'quartiles': [
                    scores_sorted[n // 4],
                    scores_sorted[n // 2],
                    scores_sorted[3 * n // 4]
                ],
                'count': n
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze score distribution: {e}")
            return {}
    
    def reset_stats(self) -> None:
        """Reset scoring statistics"""
        self._stats = {
            'scores_calculated': 0,
            'high_scores': 0,
            'medium_scores': 0,
            'low_scores': 0,
            'cache_efficiency': 0.0
        }
        logger.info("Scoring statistics reset")


# Global instance for dashboard integration
_semantic_scorer_instance = None


def get_semantic_scorer() -> SemanticScorer:
    """Get global semantic scorer instance"""
    global _semantic_scorer_instance
    if _semantic_scorer_instance is None:
        _semantic_scorer_instance = SemanticScorer()
    return _semantic_scorer_instance
