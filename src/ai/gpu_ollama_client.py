"""
Compatibility stub for gpu_ollama_client expected by older tests.
Provides JobAnalysisResult dataclass and a minimal client interface.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class JobAnalysisResult:
    required_skills: List[str] = field(default_factory=list)
    job_requirements: List[str] = field(default_factory=list)
    compatibility_score: float = 0.0
    analysis_confidence: float = 0.0
    extracted_benefits: List[str] = field(default_factory=list)
    reasoning: str = ""
    processing_time: float = 0.0
    model_used: str = "mock"


class GpuOllamaClient:
    def is_available(self) -> bool:
        return True

    def analyze_job_content(self, job_data: Dict[str, Any]) -> JobAnalysisResult:
        # Return a deterministic placeholder analysis for tests
        return JobAnalysisResult(
            required_skills=["Python", "Machine Learning"],
            job_requirements=["3+ years experience"],
            compatibility_score=0.8,
            analysis_confidence=0.9,
            extracted_benefits=["Health Insurance"],
            reasoning="Stub analysis",
            processing_time=0.1,
            model_used="stub"
        )


def get_gpu_ollama_client() -> GpuOllamaClient:
    return GpuOllamaClient()
