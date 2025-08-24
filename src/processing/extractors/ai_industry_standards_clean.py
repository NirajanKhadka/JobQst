"""
AI-Enhanced Industry Standards

Uses transformer models and embeddings for intelligent validation
of job titles, skills, companies, and locations across all industries.
"""
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import torch
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of AI-based validation."""
    is_valid: bool
    confidence: float
    matched_standard: Optional[str] = None
    similarity_score: float = 0.0
    validation_method: str = "unknown"


class AIIndustryStandards:
    """
    AI-powered industry standards using transformer models for
    semantic understanding and validation across all industries.
    """
    
    def __init__(self, model_name: str = None):
        """Initialize AI industry standards."""
        self.model_name = (model_name or 
                          "sentence-transformers/all-MiniLM-L6-v2")
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Core embeddings cache
        self._job_title_embeddings = {}
        self._skill_embeddings = {}
        self._company_embeddings = {}
        
        # Confidence thresholds
        self.job_title_threshold = 0.7
        self.skill_threshold = 0.6
        self.company_threshold = 0.8
        
        # Initialize model and core standards
        self._initialize_model()
        self._load_core_standards()
        
        logger.info(f"AI Industry Standards initialized with "
                   f"{self.model_name} on {self.device}")
    
    def _initialize_model(self):
        """Initialize the transformer model."""
        try:
            self.model = SentenceTransformer(self.model_name)
            self.model.to(self.device)
            logger.info(f"Loaded model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            self.model = None
    
    def _load_core_standards(self):
        """Load and embed core industry standards as baseline."""
        # Core job title patterns (broader than before)
        job_title_patterns = [
            # Generic patterns that work across industries
            "analyst", "manager", "engineer", "specialist", "coordinator",
            "director", "supervisor", "representative", "consultant", 
            "administrator", "developer", "designer", "scientist", 
            "researcher", "technician", "assistant", "associate", 
            "executive", "officer", "lead",
            
            # Industry-agnostic roles
            "project manager", "business analyst", "data analyst", 
            "sales representative", "customer service representative", 
            "human resources manager", "marketing specialist", 
            "financial analyst", "operations manager", "quality assurance",
            "research and development", "account manager"
        ]
        
        # Generic skills (expandable across industries)
        skill_patterns = [
            # Transferable skills
            "communication", "leadership", "problem solving", 
            "project management", "data analysis", "customer service", 
            "teamwork", "time management", "microsoft office", "excel", 
            "powerpoint", "email", "telephone",
            
            # Technical skills (broad categories)
            "programming", "database", "software", "hardware", 
            "networking", "web development", "mobile development", 
            "cloud computing", "artificial intelligence", 
            "machine learning", "data science"
        ]
        
        # Industry-agnostic companies (major employers across sectors)
        company_patterns = [
            # Major corporations across industries
            "microsoft", "google", "amazon", "apple", "walmart", 
            "target", "mcdonalds", "starbucks", "fedex", "ups", 
            "boeing", "ford", "general motors", "johnson & johnson", 
            "pfizer", "coca cola", "pepsi", "nike", "adidas", "visa", 
            "mastercard", "jpmorgan", "bank of america", "wells fargo", 
            "citigroup", "goldman sachs"
        ]
        
        # Compute embeddings for core standards
        if self.model:
            self._job_title_embeddings = self._compute_embeddings(
                job_title_patterns)
            self._skill_embeddings = self._compute_embeddings(
                skill_patterns)
            self._company_embeddings = self._compute_embeddings(
                company_patterns)
            
            logger.info(f"Embedded {len(job_title_patterns)} job patterns, "
                       f"{len(skill_patterns)} skill patterns, "
                       f"{len(company_patterns)} company patterns")
    
    def _compute_embeddings(self, texts: List[str]) -> Dict[str, np.ndarray]:
        """Compute embeddings for a list of texts."""
        if not self.model:
            return {}
        
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return {text: emb for text, emb in zip(texts, embeddings)}
        except Exception as e:
            logger.error(f"Error computing embeddings: {e}")
            return {}
    
    def validate_job_title(self, title: str, 
                          context: str = "") -> ValidationResult:
        """
        Validate if a title is a legitimate job title using AI.
        
        Args:
            title: Job title to validate
            context: Job description context for better validation
            
        Returns:
            ValidationResult with confidence and matching info
        """
        if not self.model:
            return ValidationResult(False, 0.0, validation_method="no_model")
        
        try:
            # Clean and normalize the title
            clean_title = title.lower().strip()
            
            # Get embedding for the title
            title_embedding = self.model.encode([clean_title])
            
            # Check similarity against known job title patterns
            best_match, best_score = self._find_best_match(
                title_embedding[0], self._job_title_embeddings
            )
            
            # Use context if available for additional validation
            context_boost = 0.0
            if context:
                context_score = self._validate_with_context(title, context)
                context_boost = context_score * 0.2  # 20% boost from context
            
            final_confidence = min(best_score + context_boost, 1.0)
            is_valid = final_confidence >= self.job_title_threshold
            
            return ValidationResult(
                is_valid=is_valid,
                confidence=final_confidence,
                matched_standard=best_match if is_valid else None,
                similarity_score=best_score,
                validation_method="ai_semantic"
            )
            
        except Exception as e:
            logger.error(f"Error validating job title '{title}': {e}")
            return ValidationResult(False, 0.0, validation_method="error")
    
    def validate_skill(self, skill: str, 
                      context: str = "") -> ValidationResult:
        """Validate if a term is a legitimate skill."""
        if not self.model:
            return ValidationResult(False, 0.0, validation_method="no_model")
        
        try:
            clean_skill = skill.lower().strip()
            skill_embedding = self.model.encode([clean_skill])
            
            best_match, best_score = self._find_best_match(
                skill_embedding[0], self._skill_embeddings
            )
            
            # Skills are more varied, so use lower threshold
            is_valid = best_score >= self.skill_threshold
            
            return ValidationResult(
                is_valid=is_valid,
                confidence=best_score,
                matched_standard=best_match if is_valid else None,
                similarity_score=best_score,
                validation_method="ai_semantic"
            )
            
        except Exception as e:
            logger.error(f"Error validating skill '{skill}': {e}")
            return ValidationResult(False, 0.0, validation_method="error")
    
    def validate_company(self, company: str, 
                        context: str = "") -> ValidationResult:
        """Validate if a name is a legitimate company."""
        if not self.model:
            return ValidationResult(False, 0.0, validation_method="no_model")
        
        try:
            clean_company = company.lower().strip()
            company_embedding = self.model.encode([clean_company])
            
            best_match, best_score = self._find_best_match(
                company_embedding[0], self._company_embeddings
            )
            
            # Company names should be more precise
            is_valid = best_score >= self.company_threshold
            
            return ValidationResult(
                is_valid=is_valid,
                confidence=best_score,
                matched_standard=best_match if is_valid else None,
                similarity_score=best_score,
                validation_method="ai_semantic"
            )
            
        except Exception as e:
            logger.error(f"Error validating company '{company}': {e}")
            return ValidationResult(False, 0.0, validation_method="error")
    
    def _find_best_match(self, query_embedding: np.ndarray, 
                        reference_embeddings: Dict[str, np.ndarray]
                        ) -> Tuple[str, float]:
        """Find the best matching reference embedding."""
        if not reference_embeddings:
            return "", 0.0
        
        best_match = ""
        best_score = 0.0
        
        for ref_text, ref_embedding in reference_embeddings.items():
            # Compute cosine similarity
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1), 
                ref_embedding.reshape(1, -1)
            )[0, 0]
            
            if similarity > best_score:
                best_score = similarity
                best_match = ref_text
        
        return best_match, best_score
    
    def _validate_with_context(self, title: str, context: str) -> float:
        """Use job description context to boost validation confidence."""
        if not context or len(context) < 50:
            return 0.0
        
        # Look for job-related keywords in context
        job_indicators = [
            "responsibilities", "requirements", "experience", "skills",
            "qualifications", "duties", "role", "position", "candidate",
            "seeking", "looking for", "join our team", "opportunity"
        ]
        
        context_lower = context.lower()
        indicator_count = sum(1 for indicator in job_indicators 
                             if indicator in context_lower)
        
        # Normalize score (max boost of 0.3)
        context_score = min(indicator_count / len(job_indicators), 0.3)
        return context_score
    
    def add_custom_standards(self, job_titles: List[str] = None, 
                           skills: List[str] = None, 
                           companies: List[str] = None):
        """Add custom standards for specific industries or use cases."""
        if not self.model:
            logger.warning("No model available for adding custom standards")
            return
        
        try:
            if job_titles:
                new_embeddings = self._compute_embeddings(job_titles)
                self._job_title_embeddings.update(new_embeddings)
                logger.info(f"Added {len(job_titles)} custom job titles")
            
            if skills:
                new_embeddings = self._compute_embeddings(skills)
                self._skill_embeddings.update(new_embeddings)
                logger.info(f"Added {len(skills)} custom skills")
            
            if companies:
                new_embeddings = self._compute_embeddings(companies)
                self._company_embeddings.update(new_embeddings)
                logger.info(f"Added {len(companies)} custom companies")
                
        except Exception as e:
            logger.error(f"Error adding custom standards: {e}")
    
    def get_stats(self) -> Dict[str, any]:
        """Get statistics about loaded standards."""
        return {
            'job_title_patterns': len(self._job_title_embeddings),
            'skill_patterns': len(self._skill_embeddings),
            'company_patterns': len(self._company_embeddings),
            'model_available': self.model is not None,
            'device': self.device,
            'model_name': self.model_name
        }


# Global instance
_ai_standards_instance = None


def get_ai_industry_standards() -> AIIndustryStandards:
    """Get global AI industry standards instance."""
    global _ai_standards_instance
    if _ai_standards_instance is None:
        _ai_standards_instance = AIIndustryStandards()
    return _ai_standards_instance
