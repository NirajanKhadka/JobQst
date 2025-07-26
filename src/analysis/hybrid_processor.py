"""
Hybrid Processing Engine for Enhanced Job Processing
Combines custom logic with LLM analysis for comprehensive job information extraction.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json

from .custom_data_extractor import CustomDataExtractor, ExtractionResult, get_custom_data_extractor
from .enhanced_custom_extractor import EnhancedCustomExtractor, EnhancedExtractionResult, get_enhanced_custom_extractor
from ..ai.gpu_ollama_client import GPUOllamaClient, JobAnalysisResult, get_gpu_ollama_client

logger = logging.getLogger(__name__)

@dataclass
class HybridProcessingResult:
    """Result of hybrid processing combining custom logic and LLM analysis."""
    # Core job information (from custom logic)
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None
    
    # Enhanced information (from LLM)
    required_skills: List[str] = None
    job_requirements: List[str] = None
    compatibility_score: float = 0.0
    analysis_confidence: float = 0.0
    extracted_benefits: List[str] = None
    reasoning: str = ""
    
    # Processing metadata
    custom_logic_confidence: float = 0.0
    llm_processing_time: float = 0.0
    total_processing_time: float = 0.0
    processing_method: str = "hybrid"
    fallback_used: bool = False
    
    def __post_init__(self):
        if self.required_skills is None:
            self.required_skills = []
        if self.job_requirements is None:
            self.job_requirements = []
        if self.extracted_benefits is None:
            self.extracted_benefits = []

class HybridProcessingEngine:
    """
    Combines custom logic with LLM analysis for comprehensive job processing.
    
    This engine uses a two-stage approach:
    1. Custom logic for reliable structured data extraction (original or enhanced)
    2. LLM analysis for advanced insights and information that can't be extracted manually
    """
    
    def __init__(self, 
                 ollama_client: Optional[GPUOllamaClient] = None,
                 custom_extractor: Optional[CustomDataExtractor] = None,
                 user_profile: Optional[Dict] = None,
                 use_enhanced_extractor: bool = True):
        """
        Initialize the hybrid processing engine.
        
        Args:
            ollama_client: GPU Ollama client for LLM analysis
            custom_extractor: Custom data extractor for structured data
            user_profile: User profile for compatibility scoring
            use_enhanced_extractor: Whether to use the enhanced extractor (default: True)
        """
        self.ollama_client = ollama_client or get_gpu_ollama_client()
        self.use_enhanced_extractor = use_enhanced_extractor
        
        # Choose extractor based on configuration
        if use_enhanced_extractor:
            self.enhanced_extractor = get_enhanced_custom_extractor()
            self.custom_extractor = self.enhanced_extractor  # For backward compatibility
            self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
            self.logger.info("Using enhanced custom data extractor for 100% reliability")
        else:
            self.custom_extractor = custom_extractor or get_custom_data_extractor()
            self.enhanced_extractor = None
            self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
            self.logger.info("Using original custom data extractor")
        
        self.user_profile = user_profile or {}
        
        # Validate LLM availability
        self._validate_llm_availability()
    
    def _validate_llm_availability(self) -> None:
        """Validate that LLM service is available for processing."""
        if not self.ollama_client.is_available():
            self.logger.warning("LLM service not available - will use custom logic only")
    
    def process_job(self, job_data: Dict[str, Any]) -> HybridProcessingResult:
        """
        Process job using hybrid custom logic + LLM approach.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            HybridProcessingResult with comprehensive analysis
        """
        start_time = time.time()
        job_title = job_data.get('title', 'Unknown Position')
        self.logger.info(f"Processing job: {job_title}")
        try:
            # Stage 1: Extract structured data using custom logic
            self.logger.debug("Starting custom logic extraction...")
            custom_result = self.extract_structured_data(job_data)

            # Stage 2: Enhance with LLM analysis
            self.logger.debug("Starting LLM enhancement...")
            enhanced_result = self.enhance_with_llm(job_data, custom_result)

            # Stage 3: Merge results
            final_result = self._merge_results(custom_result, enhanced_result, job_data)

            # Set processing metadata
            final_result.total_processing_time = max(time.time() - start_time, 0.001)
            final_result.custom_logic_confidence = custom_result.confidence


            self.logger.info(f"Hybrid processing completed in {final_result.total_processing_time:.2f}s")
            self.logger.info("Completed processing")

            return final_result

        except Exception as e:
            self.logger.error(f"Error during hybrid processing: {e}")
            fallback_result = self._create_fallback_result(job_data, max(time.time() - start_time, 0.001))
            fallback_result.processing_method = 'fallback'
            return fallback_result
    
    def extract_structured_data(self, job_data: Dict[str, Any]) -> ExtractionResult:
        """
        Extract structured data using custom logic (original or enhanced).
        
        Args:
            job_data: Job data dictionary
            
        Returns:
            ExtractionResult with structured data
        """
        try:
            if self.use_enhanced_extractor and self.enhanced_extractor:
                # Use enhanced extractor
                enhanced_result = self.enhanced_extractor.extract_job_data(job_data)
                
                # Convert enhanced result to standard ExtractionResult format
                result = ExtractionResult(
                    title=enhanced_result.title,
                    company=enhanced_result.company,
                    location=enhanced_result.location,
                    salary_range=enhanced_result.salary_range,
                    experience_level=enhanced_result.experience_level,
                    employment_type=enhanced_result.employment_type,
                    skills=enhanced_result.skills,
                    requirements=enhanced_result.requirements,
                    benefits=enhanced_result.benefits,
                    confidence=enhanced_result.overall_confidence,
                    extraction_method="enhanced_custom"
                )
                
                self.logger.debug(f"Enhanced extraction completed with confidence {result.confidence:.2f}")
                return result
            else:
                # Use original extractor
                result = self.custom_extractor.extract_job_data(job_data)
                self.logger.debug(f"Original extraction completed with confidence {result.confidence:.2f}")
                return result
            
        except Exception as e:
            self.logger.error(f"Custom extraction failed: {e}")
            # Return empty result
            return ExtractionResult(confidence=0.0)
    
    def enhance_with_llm(self, job_data: Dict[str, Any], structured_data: ExtractionResult) -> Optional[JobAnalysisResult]:
        """
        Enhance structured data with LLM analysis.
        
        Args:
            job_data: Original job data
            structured_data: Results from custom logic extraction
            
        Returns:
            JobAnalysisResult with LLM enhancements or None if LLM fails
        """
        if not self.ollama_client.is_available():
            self.logger.warning("LLM not available - skipping enhancement")
            return None
        
        try:
            # Prepare job information for LLM analysis
            job_title = structured_data.title or job_data.get('title', 'Unknown Position')
            job_description = job_data.get('description') or job_data.get('job_description', '')
            
            # Perform LLM analysis
            llm_result = self.ollama_client.analyze_job_content(
                job_description=job_description,
                job_title=job_title,
                user_profile=self.user_profile
            )
            
            self.logger.debug(f"LLM analysis completed in {llm_result.processing_time:.2f}s")
            return llm_result
            
        except Exception as e:
            self.logger.error(f"LLM enhancement failed: {e}")
            return None
    
    def _merge_results(self, custom_result: ExtractionResult, llm_result: Optional[JobAnalysisResult], job_data: Dict[str, Any] = None) -> HybridProcessingResult:
        """
        Merge custom logic and LLM results into final hybrid result.
        
        Args:
            custom_result: Results from custom logic extraction
            llm_result: Results from LLM analysis (may be None)
            
        Returns:
            HybridProcessingResult with merged data
        """
        # Prefer job_data values for title/company if available and more complete
        title = custom_result.title
        company = custom_result.company
        if job_data:
            job_company = job_data.get('company')
            if job_company and (not company or len(job_company) > len(company) or job_company.lower() == company.lower()):
                company = job_company
            job_title = job_data.get('title')
            if job_title and (not title or len(job_title) > len(title) or job_title.lower() == title.lower()):
                title = job_title
        hybrid_result = HybridProcessingResult(
            title=title,
            company=company,
            location=custom_result.location,
            salary_range=custom_result.salary_range,
            experience_level=custom_result.experience_level,
            employment_type=custom_result.employment_type,
            custom_logic_confidence=custom_result.confidence
        )
        
        # Merge LLM results if available
        if llm_result:
            hybrid_result.required_skills = self._merge_skills(custom_result.skills, llm_result.required_skills)
            hybrid_result.job_requirements = self._merge_requirements(custom_result.requirements, llm_result.job_requirements)
            hybrid_result.compatibility_score = llm_result.compatibility_score
            hybrid_result.analysis_confidence = llm_result.analysis_confidence
            hybrid_result.extracted_benefits = self._merge_benefits(custom_result.benefits, llm_result.extracted_benefits)
            hybrid_result.reasoning = llm_result.reasoning
            hybrid_result.llm_processing_time = llm_result.processing_time
            hybrid_result.fallback_used = False
        else:
            # Use custom logic only
            hybrid_result.required_skills = custom_result.skills
            hybrid_result.job_requirements = custom_result.requirements
            hybrid_result.compatibility_score = 0.5  # Neutral score when LLM unavailable
            hybrid_result.analysis_confidence = custom_result.confidence
            hybrid_result.extracted_benefits = custom_result.benefits
            hybrid_result.reasoning = "LLM analysis unavailable - using custom logic only"
            hybrid_result.llm_processing_time = 0.0
            hybrid_result.fallback_used = True
        
        return hybrid_result
    
    def _merge_skills(self, custom_skills: List[str], llm_skills: List[str]) -> List[str]:
        """
        Merge skills from custom logic and LLM analysis.
        
        Args:
            custom_skills: Skills extracted by custom logic
            llm_skills: Skills identified by LLM
            
        Returns:
            Merged and deduplicated skills list
        """
        # Combine and deduplicate skills
        all_skills = set()
        
        # Add custom skills (these are more reliable)
        for skill in custom_skills:
            all_skills.add(skill.strip())
        
        # Add LLM skills (check for duplicates case-insensitively)
        for skill in llm_skills:
            skill = skill.strip()
            # Check if skill already exists (case-insensitive)
            if not any(existing.lower() == skill.lower() for existing in all_skills):
                all_skills.add(skill)
        
        # Return sorted list, prioritizing custom skills
        custom_skills_lower = [s.lower() for s in custom_skills]
        sorted_skills = []
        
        # Add custom skills first
        for skill in all_skills:
            if skill.lower() in custom_skills_lower:
                sorted_skills.append(skill)
        
        # Add LLM skills
        for skill in all_skills:
            if skill.lower() not in custom_skills_lower:
                sorted_skills.append(skill)
        
        return sorted_skills[:15]  # Limit to top 15 skills
    
    def _merge_requirements(self, custom_requirements: List[str], llm_requirements: List[str]) -> List[str]:
        """
        Merge requirements from custom logic and LLM analysis.
        
        Args:
            custom_requirements: Requirements extracted by custom logic
            llm_requirements: Requirements identified by LLM
            
        Returns:
            Merged and deduplicated requirements list
        """
        # Combine requirements, prioritizing LLM analysis for requirements
        # as it's better at understanding context and nuance
        all_requirements = []
        
        # Add LLM requirements first (they're usually more comprehensive)
        for req in llm_requirements:
            req = req.strip()
            if len(req) > 5:  # Filter out very short requirements
                all_requirements.append(req)
        
        # Add custom requirements that don't overlap
        for req in custom_requirements:
            req = req.strip()
            if len(req) > 5:
                # Check for overlap with existing requirements
                if not any(self._requirements_overlap(req, existing) for existing in all_requirements):
                    all_requirements.append(req)
        
        return all_requirements[:12]  # Limit to top 12 requirements
    
    def _merge_benefits(self, custom_benefits: List[str], llm_benefits: List[str]) -> List[str]:
        """
        Merge benefits from custom logic and LLM analysis.
        
        Args:
            custom_benefits: Benefits extracted by custom logic
            llm_benefits: Benefits identified by LLM
            
        Returns:
            Merged and deduplicated benefits list
        """
        all_benefits = set()
        
        # Add custom benefits (these are more reliable for standard benefits)
        for benefit in custom_benefits:
            all_benefits.add(benefit.strip().title())
        
        # Add LLM benefits
        for benefit in llm_benefits:
            benefit = benefit.strip().title()
            # Check for duplicates case-insensitively
            if not any(existing.lower() == benefit.lower() for existing in all_benefits):
                all_benefits.add(benefit)
        
        return sorted(list(all_benefits))[:10]  # Limit to top 10 benefits
    
    def _requirements_overlap(self, req1: str, req2: str) -> bool:
        """
        Check if two requirements overlap significantly.
        
        Args:
            req1: First requirement
            req2: Second requirement
            
        Returns:
            True if requirements overlap significantly
        """
        # Normalize numbers and years
        import re
        def normalize(text):
            text = text.lower()
            text = re.sub(r"\b(\d+)\+?\s*years?\b", "years", text)
            return set(text.split())
        words1 = normalize(req1)
        words2 = normalize(req2)
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words1 -= stop_words
        words2 -= stop_words
        if not words1 or not words2:
            return False
        overlap = len(words1.intersection(words2))
        min_length = min(len(words1), len(words2))
        return overlap / min_length > 0.5  # Lower threshold for more robust matching
    
    def _create_fallback_result(self, job_data: Dict[str, Any], processing_time: float) -> HybridProcessingResult:
        """
        Create fallback result when processing fails.
        Args:
            job_data: Original job data
            processing_time: Time spent processing
        Returns:
            Fallback HybridProcessingResult
        """
        # Try to extract at least basic information
        try:
            custom_result = self.custom_extractor.extract_job_data(job_data)
            title = custom_result.title or job_data.get('title', 'Unknown Position')
            company = job_data.get('company', None) or custom_result.company
            location = custom_result.location
            salary_range = custom_result.salary_range
            experience_level = custom_result.experience_level
            employment_type = custom_result.employment_type
            required_skills = custom_result.skills
            job_requirements = custom_result.requirements
            extracted_benefits = custom_result.benefits
            custom_logic_confidence = custom_result.confidence
        except Exception:
            title = job_data.get('title', 'Unknown Position')
            company = job_data.get('company', None)
            location = None
            salary_range = None
            experience_level = None
            employment_type = None
            required_skills = []
            job_requirements = []
            extracted_benefits = []
            custom_logic_confidence = 0.0
        return HybridProcessingResult(
            title=title,
            company=company,
            location=location,
            salary_range=salary_range,
            experience_level=experience_level,
            employment_type=employment_type,
            required_skills=required_skills,
            job_requirements=job_requirements,
            compatibility_score=0.0,
            analysis_confidence=0.0,
            extracted_benefits=extracted_benefits,
            reasoning="Processing failed - using fallback extraction",
            custom_logic_confidence=custom_logic_confidence,
            llm_processing_time=0.0,
            total_processing_time=processing_time,
            processing_method="fallback",
            fallback_used=True
        )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics and health information.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            "custom_extractor_available": self.custom_extractor is not None,
            "llm_client_available": self.ollama_client.is_available(),
            "user_profile_configured": bool(self.user_profile),
            "llm_health": self.ollama_client.get_health_info() if self.ollama_client else None,
            "processing_method": "hybrid" if self.ollama_client.is_available() else "custom_only"
        }
    
    def update_user_profile(self, user_profile: Dict[str, Any]) -> None:
        """
        Update user profile for compatibility scoring.
        
        Args:
            user_profile: Updated user profile information
        """
        self.user_profile = user_profile
        self.logger.info("User profile updated for compatibility scoring")


# Convenience function for easy import
def get_hybrid_processing_engine(user_profile: Optional[Dict] = None) -> HybridProcessingEngine:
    """
    Get a configured hybrid processing engine instance.
    
    Args:
        user_profile: Optional user profile for compatibility scoring
        
    Returns:
        Configured HybridProcessingEngine instance
    """
    return HybridProcessingEngine(user_profile=user_profile)