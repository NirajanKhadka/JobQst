"""
AI Integration Service for JobQst
Implements Phase 2 of AI_STRATEGY_ANALYSIS.md - Dashboard Integration
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from ..optimization import IntelligentCache, ProfileEmbedding, SemanticScorer
from ..core.job_database import get_job_db

logger = logging.getLogger(__name__)


class AIIntegrationService:
    """
    AI Integration Service for Dashboard Analytics
    
    Integrates semantic scoring, caching, and profile matching
    into the job processing pipeline for dashboard display.
    """
    
    def __init__(self, profile_name: str = "default"):
        """Initialize AI integration service"""
        self.profile_name = profile_name
        self.cache = IntelligentCache()
        self.embedder = ProfileEmbedding()
        self.scorer = SemanticScorer()
        self.db = get_job_db(profile_name)
        
        logger.info(f"AI Integration Service initialized for profile: {profile_name}")
    
    def enhance_job_with_ai(self, job_data: Dict[str, Any], 
                           profile_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enhance job data with AI-powered insights for dashboard
        
        Args:
            job_data: Job data dictionary
            profile_data: Optional profile data (will load if not provided)
            
        Returns:
            Enhanced job data with AI fields
        """
        try:
            # Load profile if not provided
            if profile_data is None:
                from ..utils.profile_helpers import load_profile
                profile_data = load_profile(self.profile_name) or {}
            
            # Generate text hash for caching
            text_hash = self.cache.text_hash(
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('description', job_data.get('summary', ''))
            )
            
            # Check cache status
            cache_status = "hit" if self.cache.get_cached_html(text_hash) else "miss"
            html_cached = 1 if cache_status == "hit" else 0
            
            # Calculate semantic score using our AI scorer
            scoring_result = self.scorer.calculate_job_score(
                self.profile_name, profile_data, job_data
            )
            
            # Extract AI insights
            semantic_score = scoring_result.get('semantic_score', 0.0)
            profile_similarity = scoring_result.get('profile_similarity', 0.0)
            embedding_cached = 1 if scoring_result.get('embedding_cached', False) else 0
            
            # Add AI fields to job data
            enhanced_job = job_data.copy()
            enhanced_job.update({
                'semantic_score': semantic_score,
                'cache_status': cache_status,
                'profile_similarity': profile_similarity,
                'embedding_cached': embedding_cached,
                'html_cached': html_cached,
                'ai_processed_at': str(datetime.now()),
                'ai_processing_method': 'semantic_scorer_v1'
            })
            
            logger.debug(f"Enhanced job {job_data.get('title', 'Unknown')} "
                        f"with semantic score: {semantic_score:.3f}")
            
            return enhanced_job
            
        except Exception as e:
            logger.error(f"Failed to enhance job with AI: {e}")
            # Return original job data with default AI values
            return {
                **job_data,
                'semantic_score': 0.0,
                'cache_status': 'error',
                'profile_similarity': 0.0,
                'embedding_cached': 0,
                'html_cached': 0,
                'ai_processing_error': str(e)
            }
    
    def batch_enhance_jobs(self, jobs_data: List[Dict[str, Any]], 
                          profile_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Enhance multiple jobs with AI insights in batch
        
        Args:
            jobs_data: List of job data dictionaries
            profile_data: Optional profile data
            
        Returns:
            List of enhanced job data
        """
        enhanced_jobs = []
        total_jobs = len(jobs_data)
        
        logger.info(f"Batch enhancing {total_jobs} jobs with AI insights...")
        
        for i, job_data in enumerate(jobs_data):
            try:
                enhanced_job = self.enhance_job_with_ai(job_data, profile_data)
                enhanced_jobs.append(enhanced_job)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Enhanced {i + 1}/{total_jobs} jobs")
                    
            except Exception as e:
                logger.error(f"Failed to enhance job {i+1}: {e}")
                enhanced_jobs.append(job_data)  # Add original job if enhancement fails
        
        logger.info(f"Batch enhancement complete: {len(enhanced_jobs)} jobs processed")
        return enhanced_jobs
    
    def update_existing_jobs_with_ai(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Update existing jobs in database with AI insights
        
        Args:
            limit: Optional limit on number of jobs to process
            
        Returns:
            Statistics about the update process
        """
        try:
            # Get jobs that haven't been AI-enhanced yet
            with self.db._get_connection() as conn:
                query = """
                    SELECT * FROM jobs 
                    WHERE semantic_score IS NULL OR semantic_score = 0.0
                    ORDER BY created_at DESC
                """
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor = conn.execute(query)
                jobs = [dict(row) for row in cursor.fetchall()]
            
            if not jobs:
                logger.info("No jobs found that need AI enhancement")
                return {'processed': 0, 'updated': 0, 'errors': 0}
            
            logger.info(f"Found {len(jobs)} jobs to enhance with AI")
            
            # Enhance jobs with AI
            enhanced_jobs = self.batch_enhance_jobs(jobs)
            
            # Update database with AI insights
            updated_count = 0
            error_count = 0
            
            for enhanced_job in enhanced_jobs:
                try:
                    with self.db._get_connection() as conn:
                        update_query = """
                            UPDATE jobs SET 
                                semantic_score = ?,
                                cache_status = ?,
                                profile_similarity = ?,
                                embedding_cached = ?,
                                html_cached = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """
                        conn.execute(update_query, (
                            enhanced_job.get('semantic_score', 0.0),
                            enhanced_job.get('cache_status', 'miss'),
                            enhanced_job.get('profile_similarity', 0.0),
                            enhanced_job.get('embedding_cached', 0),
                            enhanced_job.get('html_cached', 0),
                            enhanced_job.get('id')
                        ))
                        conn.commit()
                        updated_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to update job {enhanced_job.get('id')}: {e}")
                    error_count += 1
            
            stats = {
                'processed': len(jobs),
                'updated': updated_count,
                'errors': error_count
            }
            
            logger.info(f"AI enhancement complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to update existing jobs with AI: {e}")
            return {'processed': 0, 'updated': 0, 'errors': 1, 'error_message': str(e)}
    
    def get_ai_analytics(self) -> Dict[str, Any]:
        """
        Get AI analytics for dashboard display
        
        Returns:
            Dictionary with AI analytics data
        """
        try:
            with self.db._get_connection() as conn:
                # Get basic statistics
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_jobs,
                        COUNT(CASE WHEN semantic_score > 0 THEN 1 END) as ai_processed,
                        AVG(semantic_score) as avg_semantic_score,
                        COUNT(CASE WHEN semantic_score > 0.7 THEN 1 END) as high_scores,
                        COUNT(CASE WHEN semantic_score BETWEEN 0.4 AND 0.7 THEN 1 END) as medium_scores,
                        COUNT(CASE WHEN semantic_score < 0.4 AND semantic_score > 0 THEN 1 END) as low_scores,
                        COUNT(CASE WHEN cache_status = 'hit' THEN 1 END) as cache_hits,
                        COUNT(CASE WHEN cache_status = 'miss' THEN 1 END) as cache_misses
                    FROM jobs
                """)
                
                row = cursor.fetchone()
                stats = dict(row) if row else {}
                
                # Calculate cache efficiency
                total_cache_checks = stats.get('cache_hits', 0) + stats.get('cache_misses', 0)
                cache_efficiency = (stats.get('cache_hits', 0) / total_cache_checks * 100) if total_cache_checks > 0 else 0
                
                # Get distribution data
                cursor = conn.execute("""
                    SELECT 
                        semantic_score,
                        COUNT(*) as count
                    FROM jobs 
                    WHERE semantic_score > 0
                    GROUP BY ROUND(semantic_score, 1)
                    ORDER BY semantic_score
                """)
                
                score_distribution = [dict(row) for row in cursor.fetchall()]
                
                analytics = {
                    **stats,
                    'cache_efficiency': round(cache_efficiency, 2),
                    'ai_processing_coverage': round((stats.get('ai_processed', 0) / max(stats.get('total_jobs', 1), 1)) * 100, 2),
                    'score_distribution': score_distribution
                }
                
                return analytics
                
        except Exception as e:
            logger.error(f"Failed to get AI analytics: {e}")
            return {}


# Convenience function for easy access
def get_ai_integration_service(profile_name: str = "default") -> AIIntegrationService:
    """Get or create AI integration service instance"""
    return AIIntegrationService(profile_name)

