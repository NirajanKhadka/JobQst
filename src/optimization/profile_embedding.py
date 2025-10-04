"""
Profile Embedding System for Semantic Job Matching
Enhanced implementation following AI_STRATEGY_ANALYSIS.md
"""

import os
import json
import logging
import torch
import torch.nn.functional as F
from typing import Dict, Any, Optional, List
from sentence_transformers import SentenceTransformer
from .intelligent_cache import cache_embedding, get_cached_embedding

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# PERFORMANCE FIX: Check if heavy AI models are disabled
if (
    os.environ.get("DISABLE_SENTENCE_TRANSFORMERS") == "1"
    or os.environ.get("DISABLE_HEAVY_AI") == "1"
):
    logger.info(
        "Sentence transformers disabled via environment variable - using lightweight fallback"
    )
    model = None
    device = "cpu"
else:
    # Initialize model with error handling
    try:
        model = SentenceTransformer(MODEL_NAME)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        logger.info(f"Profile embedding model loaded: {MODEL_NAME} on {device}")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        model = None
        device = "cpu"


class ProfileEmbedding:
    """Enhanced profile embedding system with dashboard integration"""

    def __init__(self):
        """Initialize profile embedding system"""
        self.model = model
        self.device = device
        self._stats = {
            "profiles_embedded": 0,
            "jobs_embedded": 0,
            "similarity_calculations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def extract_profile_text(self, profile_data: Dict[str, Any]) -> str:
        """Extract meaningful text from profile for embedding"""
        try:
            text_parts = []

            # Personal information
            personal = profile_data.get("personal", {})
            if personal.get("desired_job_title"):
                text_parts.append(f"Desired job: {personal['desired_job_title']}")

            # Skills
            skills = profile_data.get("skills", {})
            if skills.get("technical"):
                text_parts.append(f"Technical skills: {', '.join(skills['technical'])}")
            if skills.get("soft"):
                text_parts.append(f"Soft skills: {', '.join(skills['soft'])}")

            # Experience
            experience = profile_data.get("experience", [])
            for exp in experience[:3]:  # Last 3 positions
                if exp.get("title") and exp.get("company"):
                    text_parts.append(f"Experience: {exp['title']} at {exp['company']}")

            # Education
            education = profile_data.get("education", [])
            for edu in education:
                if edu.get("degree") and edu.get("field"):
                    text_parts.append(f"Education: {edu['degree']} in {edu['field']}")

            return " ".join(text_parts)

        except Exception as e:
            logger.error(f"Error extracting profile text: {e}")
            return ""

    def calculate_semantic_similarity(
        self, profile_name: str, profile_data: Dict[str, Any], job_data: Dict[str, Any]
    ) -> float:
        """
        Calculate semantic similarity between profile and job

        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            if not self.model:
                return 0.0

            # Extract texts
            profile_text = self.extract_profile_text(profile_data)
            job_text = self._extract_job_text(job_data)

            if not profile_text or not job_text:
                return 0.0

            # Get embeddings (with caching)
            profile_emb = get_profile_embedding(profile_text)
            job_emb = self._get_job_embedding(job_text)

            if profile_emb is None or job_emb is None:
                return 0.0

            # Calculate cosine similarity
            if isinstance(profile_emb, torch.Tensor) and isinstance(job_emb, torch.Tensor):
                similarity = torch.cosine_similarity(profile_emb.unsqueeze(0), job_emb.unsqueeze(0))
                score = float(similarity.item())
            else:
                # NumPy arrays
                import numpy as np

                profile_emb = np.array(profile_emb)
                job_emb = np.array(job_emb)

                # Normalize vectors
                profile_emb = profile_emb / np.linalg.norm(profile_emb)
                job_emb = job_emb / np.linalg.norm(job_emb)

                # Calculate cosine similarity
                score = np.dot(profile_emb, job_emb)

            # Convert to 0-1 range
            score = (score + 1) / 2  # Convert from [-1, 1] to [0, 1]

            self._stats["similarity_calculations"] += 1
            return max(0.0, min(1.0, score))

        except Exception as e:
            logger.error(f"Failed to calculate semantic similarity: {e}")
            return 0.0

    def _extract_job_text(self, job_data: Dict[str, Any]) -> str:
        """Extract meaningful text from job posting"""
        try:
            text_parts = []

            if job_data.get("title"):
                text_parts.append(f"Job title: {job_data['title']}")
            if job_data.get("company"):
                text_parts.append(f"Company: {job_data['company']}")
            if job_data.get("description"):
                desc = job_data["description"][:1000]  # Limit length
                text_parts.append(f"Description: {desc}")

            return " ".join(text_parts)

        except Exception as e:
            logger.error(f"Error extracting job text: {e}")
            return job_data.get("title", "") + " " + job_data.get("company", "")

    def _get_job_embedding(self, job_text: str):
        """Get job embedding with caching"""
        if not self.model:
            return None

        cached = get_cached_embedding(job_text, MODEL_NAME)
        if cached is not None:
            self._stats["cache_hits"] += 1
            return cached

        try:
            emb = self.model.encode([job_text])[0]
            cache_embedding(job_text, MODEL_NAME, emb)
            self._stats["cache_misses"] += 1
            self._stats["jobs_embedded"] += 1
            return emb
        except Exception as e:
            logger.error(f"Failed to generate job embedding: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get embedding statistics for dashboard"""
        stats = self._stats.copy()
        total_requests = stats["cache_hits"] + stats["cache_misses"]
        stats["cache_hit_rate"] = stats["cache_hits"] / max(total_requests, 1)
        stats["model_name"] = MODEL_NAME
        stats["device"] = self.device
        return stats


# Global instance
_profile_embedding_instance = None


def get_profile_embedding_service() -> ProfileEmbedding:
    """Get global profile embedding service"""
    global _profile_embedding_instance
    if _profile_embedding_instance is None:
        _profile_embedding_instance = ProfileEmbedding()
    return _profile_embedding_instance


# Legacy compatibility function
def get_profile_embedding(profile_summary: str):
    """Legacy function - enhanced with caching and error handling"""
    if not model:
        return None

    cached = get_cached_embedding(profile_summary, MODEL_NAME)
    if cached is not None:
        return cached

    try:
        emb = model.encode([profile_summary])[0]
        cache_embedding(profile_summary, MODEL_NAME, emb)
        return emb
    except Exception as e:
        logger.error(f"Failed to generate profile embedding: {e}")
        return None
