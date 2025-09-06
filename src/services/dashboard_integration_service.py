"""
Dashboard Integration Service for AI-Enhanced Industry Standards

Provides API endpoints and data processing for dashboard integration
with AI-powered job validation and customizable scraper configuration.
"""
import logging
from typing import Dict, List, Any, Optional
from fastapi import HTTPException
from pydantic import BaseModel

from ..processing.extractors.industry_standards import IndustryStandardsDatabase
from ..config.customizable_scraper import get_scraper_manager, ScrapeConfig

logger = logging.getLogger(__name__)


class JobValidationRequest(BaseModel):
    """Request model for job validation."""
    job_title: str
    company: str = ""
    skills: List[str] = []
    location: str = ""
    description: str = ""


class ValidationResponse(BaseModel):
    """Response model for validation results."""
    job_title: Dict[str, Any]
    company: Dict[str, Any]
    skills: List[Dict[str, Any]]
    location: Dict[str, Any]
    overall_confidence: float


class ScraperConfigRequest(BaseModel):
    """Request model for scraper configuration."""
    keywords: List[str] = []
    job_titles: List[str] = []
    locations: List[str] = []
    sites: List[str] = ["indeed", "linkedin"]
    max_results: int = 50
    user_id: str = "default"
    config_name: str = "custom"


class DashboardIntegrationService:
    """Service for integrating AI standards with dashboard."""
    
    def __init__(self):
        """Initialize dashboard integration service."""
        self.industry_standards = IndustryStandardsDatabase(use_ai=True)
        self.scraper_manager = get_scraper_manager()
        
        logger.info("Dashboard integration service initialized")
    
    def validate_job_posting(self, request: JobValidationRequest) -> ValidationResponse:
        """
        Validate a complete job posting with AI-enhanced standards.
        
        Args:
            request: Job validation request
            
        Returns:
            Comprehensive validation response with confidence scores
        """
        try:
            # Validate job title
            job_title_result = self.industry_standards.validate_with_confidence(
                'job_title', request.job_title, request.description
            )
            
            # Validate company
            company_result = self.industry_standards.validate_with_confidence(
                'company', request.company, request.description
            )
            
            # Validate location
            location_result = self.industry_standards.validate_with_confidence(
                'location', request.location
            )
            
            # Validate skills
            skill_results = []
            for skill in request.skills:
                skill_result = self.industry_standards.validate_with_confidence(
                    'skill', skill, request.description
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
            confidences.extend([s['confidence'] for s in skill_results])
            
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return ValidationResponse(
                job_title={
                    'value': request.job_title,
                    'is_valid': job_title_result['is_valid'],
                    'confidence': job_title_result['confidence'],
                    'method': job_title_result['method'],
                    'matched_standard': job_title_result['matched_standard']
                },
                company={
                    'value': request.company,
                    'is_valid': company_result['is_valid'],
                    'confidence': company_result['confidence'],
                    'method': company_result['method'],
                    'matched_standard': company_result['matched_standard']
                },
                location={
                    'value': request.location,
                    'is_valid': location_result['is_valid'],
                    'confidence': location_result['confidence'],
                    'method': location_result['method'],
                    'matched_standard': location_result['matched_standard']
                },
                skills=skill_results,
                overall_confidence=overall_confidence
            )
            
        except Exception as e:
            logger.error(f"Error validating job posting: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_scraper_templates(self) -> Dict[str, Any]:
        """Get available scraper configuration templates."""
        try:
            templates = {}
            for template_name in self.scraper_manager.list_templates():
                template = self.scraper_manager.get_template(template_name)
                templates[template_name] = {
                    'name': template_name,
                    'keywords': template.keywords,
                    'job_titles': template.job_titles,
                    'locations': template.locations,
                    'sites': template.sites,
                    'max_results': template.max_results_per_site,
                    'description': self._get_template_description(template_name)
                }
            
            return {
                'templates': templates,
                'dashboard_options': self.scraper_manager.get_dashboard_options()
            }
            
        except Exception as e:
            logger.error(f"Error getting scraper templates: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def create_scraper_config(self, request: ScraperConfigRequest) -> Dict[str, Any]:
        """Create and validate a custom scraper configuration."""
        try:
            # Create the configuration
            config = self.scraper_manager.create_custom_config(
                keywords=request.keywords,
                job_titles=request.job_titles,
                locations=request.locations,
                sites=request.sites,
                max_results_per_site=request.max_results,
                user_id=request.user_id,
                config_name=request.config_name
            )
            
            # Validate the configuration
            validation = self.scraper_manager.validate_config(config)
            
            # Convert to JobSpy parameters
            jobspy_params = self.scraper_manager.convert_to_jobspy_params(config)
            
            return {
                'config': {
                    'keywords': config.keywords,
                    'job_titles': config.job_titles,
                    'locations': config.locations,
                    'sites': config.sites,
                    'max_results': config.max_results_per_site,
                    'user_id': config.user_id,
                    'config_name': config.config_name
                },
                'validation': validation,
                'jobspy_params': jobspy_params,
                'estimated_total_results': len(config.sites) * config.max_results_per_site
            }
            
        except Exception as e:
            logger.error(f"Error creating scraper config: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def save_scraper_config(self, config: ScrapeConfig) -> Dict[str, Any]:
        """Save a scraper configuration."""
        try:
            filepath = self.scraper_manager.save_config(config)
            return {
                'success': True,
                'filepath': filepath,
                'message': f"Configuration saved as {config.config_name}"
            }
            
        except Exception as e:
            logger.error(f"Error saving scraper config: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_user_configs(self, user_id: str) -> List[Dict[str, Any]]:
        """Get saved configurations for a user."""
        try:
            config_files = self.scraper_manager.list_saved_configs(user_id)
            configs = []
            
            for filename in config_files:
                config = self.scraper_manager.load_config(filename)
                if config:
                    configs.append({
                        'filename': filename,
                        'config_name': config.config_name,
                        'keywords': config.keywords,
                        'job_titles': config.job_titles,
                        'locations': config.locations,
                        'sites': config.sites,
                        'max_results': config.max_results_per_site,
                        'created_date': getattr(config, 'created_date', 'Unknown')
                    })
            
            return configs
            
        except Exception as e:
            logger.error(f"Error getting user configs: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get statistics about validation performance."""
        try:
            ai_stats = {}
            if self.industry_standards.use_ai and self.industry_standards.ai_standards:
                ai_stats = self.industry_standards.ai_standards.get_stats()
            
            traditional_stats = {
                'job_titles_count': len(self.industry_standards.job_titles),
                'companies_count': len(self.industry_standards.companies),
                'skills_count': len(self.industry_standards.skills),
                'locations_count': len(self.industry_standards.locations)
            }
            
            return {
                'ai_enabled': self.industry_standards.use_ai,
                'ai_stats': ai_stats,
                'traditional_stats': traditional_stats,
                'hybrid_approach': True,
                'validation_methods': ['exact_match', 'ai_semantic', 'partial_match']
            }
            
        except Exception as e:
            logger.error(f"Error getting validation stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _get_template_description(self, template_name: str) -> str:
        """Get description for a template."""
        descriptions = {
            'tech_comprehensive': 'Comprehensive tech roles including software engineering, data science, and DevOps',
            'data_science': 'Data science and analytics roles with ML/AI focus',
            'business_analyst': 'Business analysis and intelligence roles',
            'sales_marketing': 'Sales, marketing, and customer relationship roles',
            'remote_only': 'Remote work opportunities across various tech disciplines'
        }
        return descriptions.get(template_name, 'Custom configuration template')


# Global instance
_dashboard_service_instance = None


def get_dashboard_service() -> DashboardIntegrationService:
    """Get global dashboard integration service instance."""
    global _dashboard_service_instance
    if _dashboard_service_instance is None:
        _dashboard_service_instance = DashboardIntegrationService()
    return _dashboard_service_instance

