"""
Enhanced Job Processing Pipeline with AI Validation and Rich Notes

Integrates AI-enhanced industry standards validation into the job processing
pipeline and generates detailed notes for dashboard analytics.
"""
import logging
from typing import Dict, List, Any
from datetime import datetime

from ..processing.extractors.industry_standards import (
    IndustryStandardsDatabase
)
from ..config.customizable_scraper import get_scraper_manager

logger = logging.getLogger(__name__)


class EnhancedJobProcessor:
    """
    Enhanced job processor with AI validation and rich note generation.
    Adds semantic validation, confidence scoring, and detailed analytics.
    """
    
    def __init__(self, use_ai: bool = True):
        """Initialize enhanced job processor."""
        self.industry_standards = IndustryStandardsDatabase(use_ai=use_ai)
        self.scraper_manager = get_scraper_manager()
        
        self.stats = {
            'jobs_processed': 0,
            'ai_validations': 0,
            'exact_matches': 0,
            'partial_matches': 0,
            'validation_errors': 0,
            'high_confidence_jobs': 0,  # >0.8 confidence
            'medium_confidence_jobs': 0,  # 0.5-0.8 confidence
            'low_confidence_jobs': 0,  # <0.5 confidence
        }
        
        logger.info("Enhanced job processor initialized with AI validation")
    
    def process_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single job with AI validation and note generation.
        
        Args:
            job_data: Raw job data from scraper
            
        Returns:
            Enhanced job data with validation results and notes
        """
        enhanced_job = job_data.copy()
        
        try:
            # Extract key fields
            job_title = job_data.get('title', '').strip()
            company = job_data.get('company', '').strip()
            location = job_data.get('location', '').strip()
            description = job_data.get('description', '')
            
            # Extract skills from description (basic extraction)
            extracted_skills = self._extract_skills_from_description(description)
            
            # Perform AI-enhanced validation
            validation_results = self._validate_job_components(
                job_title, company, location, extracted_skills, description
            )
            
            # Generate rich notes
            notes = self._generate_job_notes(validation_results, job_data)
            
            # Calculate overall job quality score
            quality_score = self._calculate_quality_score(validation_results)
            
            # Add enhanced fields to job data
            enhanced_job.update({
                # AI validation results
                'validation_results': validation_results,
                'job_title_confidence': validation_results['job_title']['confidence'],
                'company_confidence': validation_results['company']['confidence'],
                'location_confidence': validation_results['location']['confidence'],
                'overall_confidence': validation_results['overall_confidence'],
                'quality_score': quality_score,
                
                # Extracted and validated skills
                'extracted_skills': extracted_skills,
                'validated_skills': [
                    skill for skill in validation_results['skills'] 
                    if skill['is_valid']
                ],
                'skill_count': len([
                    skill for skill in validation_results['skills'] 
                    if skill['is_valid']
                ]),
                
                # Rich notes and analytics
                'notes': notes,
                'validation_method': self._get_primary_validation_method(validation_results),
                'ai_enhanced': self.industry_standards.use_ai,
                
                # Processing metadata
                'processed_date': datetime.now().isoformat(),
                'processor_version': '2.0_ai_enhanced',
                
                # Dashboard display fields
                'display_title': self._get_display_title(job_title, validation_results['job_title']),
                'display_company': self._get_display_company(company, validation_results['company']),
                'confidence_badge': self._get_confidence_badge(quality_score),
                'validation_status': self._get_validation_status(validation_results)
            })
            
            # Update statistics
            self._update_stats(validation_results, quality_score)
            
            logger.debug(f"Enhanced job processing completed for: {job_title} at {company}")
            
        except Exception as e:
            logger.error(f"Error in enhanced job processing: {e}")
            enhanced_job['processing_error'] = str(e)
            enhanced_job['notes'] = [f"Processing error: {str(e)}"]
            self.stats['validation_errors'] += 1
        
        return enhanced_job
    
    def process_job_batch(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of jobs with AI validation."""
        logger.info(f"Processing batch of {len(jobs)} jobs with AI validation")
        
        enhanced_jobs = []
        for job in jobs:
            enhanced_job = self.process_job(job)
            enhanced_jobs.append(enhanced_job)
        
        logger.info(f"Batch processing completed. Stats: {self.get_processing_stats()}")
        return enhanced_jobs
    
    def _validate_job_components(self, job_title: str, company: str, 
                                location: str, skills: List[str], 
                                description: str) -> Dict[str, Any]:
        """Validate all job components with AI-enhanced standards."""
        
        # Validate job title
        job_title_result = self.industry_standards.validate_with_confidence(
            'job_title', job_title, description
        )
        
        # Validate company
        company_result = self.industry_standards.validate_with_confidence(
            'company', company, description
        )
        
        # Validate location
        location_result = self.industry_standards.validate_with_confidence(
            'location', location
        )
        
        # Validate skills
        skill_results = []
        for skill in skills:
            skill_result = self.industry_standards.validate_with_confidence(
                'skill', skill, description
            )
            skill_results.append({
                'skill': skill,
                'is_valid': skill_result['is_valid'],
                'confidence': skill_result['confidence'],
                'method': skill_result['method'],
                'matched_standard': skill_result['matched_standard']
            })
        
        # Calculate overall confidence
        confidences = [
            job_title_result['confidence'],
            company_result['confidence'],
            location_result['confidence']
        ]
        
        if skill_results:
            skill_confidences = [s['confidence'] for s in skill_results]
            confidences.extend(skill_confidences)
        
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            'job_title': job_title_result,
            'company': company_result,
            'location': location_result,
            'skills': skill_results,
            'overall_confidence': overall_confidence,
            'validation_count': len(confidences)
        }
    
    def _extract_skills_from_description(self, description: str) -> List[str]:
        """Extract skills from job description using basic pattern matching."""
        if not description:
            return []
        
        # Get known skills from industry standards
        known_skills = self.industry_standards.skills
        extracted_skills = []
        
        description_lower = description.lower()
        
        # Look for exact skill matches in description
        for skill in known_skills:
            if skill in description_lower:
                extracted_skills.append(skill)
        
        # Common skill patterns not in the database
        additional_patterns = [
            'communication skills', 'leadership', 'problem solving',
            'teamwork', 'time management', 'customer service',
            'project management', 'analytical skills'
        ]
        
        for pattern in additional_patterns:
            if pattern in description_lower:
                extracted_skills.append(pattern)
        
        # Remove duplicates and return top 10
        return list(set(extracted_skills))[:10]
    
    def _generate_job_notes(self, validation_results: Dict[str, Any], 
                           job_data: Dict[str, Any]) -> List[str]:
        """Generate rich notes for job based on validation results."""
        notes = []
        
        # Job title validation notes
        job_title_result = validation_results['job_title']
        if job_title_result['is_valid']:
            if job_title_result['method'] == 'ai_semantic':
                notes.append(f"✅ Job title validated by AI (confidence: {job_title_result['confidence']:.2f})")
            elif job_title_result['method'] == 'exact_match':
                notes.append("✅ Job title exactly matches industry standards")
            elif job_title_result['method'] == 'partial_match':
                notes.append(f"⚠️ Job title partially matches: {job_title_result['matched_standard']}")
        else:
            notes.append("❌ Job title not recognized by validation system")
        
        # Company validation notes
        company_result = validation_results['company']
        if company_result['is_valid']:
            notes.append(f"✅ Company validated (confidence: {company_result['confidence']:.2f})")
        else:
            notes.append("⚠️ Company not in known database - may be new or small company")
        
        # Skill validation notes
        skills = validation_results['skills']
        valid_skills = [s for s in skills if s['is_valid']]
        if valid_skills:
            notes.append(f"🎯 Found {len(valid_skills)} validated skills")
            if len(valid_skills) >= 5:
                notes.append("💪 Rich skill set - high technical requirements")
        else:
            notes.append("⚠️ No validated skills found in description")
        
        # Overall confidence notes
        overall_conf = validation_results['overall_confidence']
        if overall_conf >= 0.8:
            notes.append("🌟 High-quality job posting with excellent validation scores")
        elif overall_conf >= 0.6:
            notes.append("👍 Good job posting quality with solid validation")
        elif overall_conf >= 0.4:
            notes.append("⚠️ Moderate quality - some validation concerns")
        else:
            notes.append("❗ Low quality posting - manual review recommended")
        
        # Salary and location notes
        if job_data.get('salary'):
            notes.append(f"💰 Salary information available: {job_data['salary']}")
        else:
            notes.append("💰 No salary information provided")
        
        location = job_data.get('location', '')
        if 'remote' in location.lower():
            notes.append("🏠 Remote work opportunity")
        
        # AI enhancement note
        if self.industry_standards.use_ai:
            notes.append("🤖 Enhanced with AI-powered validation")
        
        return notes
    
    def _calculate_quality_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall job quality score (0.0 - 1.0)."""
        
        # Base score from overall confidence
        base_score = validation_results['overall_confidence']
        
        # Bonuses for specific validations
        bonuses = 0.0
        
        # Job title validation bonus
        if validation_results['job_title']['is_valid']:
            if validation_results['job_title']['method'] == 'exact_match':
                bonuses += 0.1
            elif validation_results['job_title']['method'] == 'ai_semantic':
                bonuses += 0.05
        
        # Skills bonus
        valid_skills = [s for s in validation_results['skills'] if s['is_valid']]
        if len(valid_skills) >= 3:
            bonuses += 0.1
        elif len(valid_skills) >= 1:
            bonuses += 0.05
        
        # Company validation bonus
        if validation_results['company']['is_valid']:
            bonuses += 0.05
        
        # Calculate final score (max 1.0)
        final_score = min(base_score + bonuses, 1.0)
        return round(final_score, 3)
    
    def _get_primary_validation_method(self, validation_results: Dict[str, Any]) -> str:
        """Get the primary validation method used."""
        methods = [
            validation_results['job_title']['method'],
            validation_results['company']['method'],
            validation_results['location']['method']
        ]
        
        # Priority: ai_semantic > exact_match > partial_match > error
        if 'ai_semantic' in methods:
            return 'ai_semantic'
        elif 'exact_match' in methods:
            return 'exact_match'
        elif 'partial_match' in methods:
            return 'partial_match'
        else:
            return 'fallback'
    
    def _get_display_title(self, original_title: str, validation_result: Dict[str, Any]) -> str:
        """Get enhanced display title for dashboard."""
        if validation_result['is_valid'] and validation_result['matched_standard']:
            confidence = validation_result['confidence']
            if confidence >= 0.8:
                return f"{original_title} ✅"
            elif confidence >= 0.6:
                return f"{original_title} ⚠️"
        
        return original_title
    
    def _get_display_company(self, original_company: str, validation_result: Dict[str, Any]) -> str:
        """Get enhanced display company for dashboard."""
        if validation_result['is_valid']:
            return f"{original_company} ✅"
        
        return original_company
    
    def _get_confidence_badge(self, quality_score: float) -> str:
        """Get confidence badge for dashboard display."""
        if quality_score >= 0.8:
            return "HIGH"
        elif quality_score >= 0.6:
            return "MEDIUM"
        elif quality_score >= 0.4:
            return "LOW"
        else:
            return "POOR"
    
    def _get_validation_status(self, validation_results: Dict[str, Any]) -> str:
        """Get overall validation status."""
        overall_conf = validation_results['overall_confidence']
        
        if overall_conf >= 0.8:
            return "VALIDATED"
        elif overall_conf >= 0.6:
            return "PARTIAL"
        elif overall_conf >= 0.4:
            return "QUESTIONABLE"
        else:
            return "UNVALIDATED"
    
    def _update_stats(self, validation_results: Dict[str, Any], quality_score: float):
        """Update processing statistics."""
        self.stats['jobs_processed'] += 1
        
        # Count validation methods
        methods = [
            validation_results['job_title']['method'],
            validation_results['company']['method'],
            validation_results['location']['method']
        ]
        
        if 'ai_semantic' in methods:
            self.stats['ai_validations'] += 1
        if 'exact_match' in methods:
            self.stats['exact_matches'] += 1
        if 'partial_match' in methods:
            self.stats['partial_matches'] += 1
        
        # Count quality levels
        if quality_score >= 0.8:
            self.stats['high_confidence_jobs'] += 1
        elif quality_score >= 0.5:
            self.stats['medium_confidence_jobs'] += 1
        else:
            self.stats['low_confidence_jobs'] += 1
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics for analytics."""
        if self.stats['jobs_processed'] == 0:
            return self.stats
        
        total = self.stats['jobs_processed']
        
        return {
            **self.stats,
            'ai_validation_rate': self.stats['ai_validations'] / total,
            'exact_match_rate': self.stats['exact_matches'] / total,
            'partial_match_rate': self.stats['partial_matches'] / total,
            'high_quality_rate': self.stats['high_confidence_jobs'] / total,
            'error_rate': self.stats['validation_errors'] / total,
        }


# Global instance
_enhanced_processor_instance = None


def get_enhanced_job_processor() -> EnhancedJobProcessor:
    """Get global enhanced job processor instance."""
    global _enhanced_processor_instance
    if _enhanced_processor_instance is None:
        _enhanced_processor_instance = EnhancedJobProcessor()
    return _enhanced_processor_instance
