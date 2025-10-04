#!/usr/bin/env python3
"""
Real Ollama Client Implementation for JobQst
Provides actual LLM-powered job analysis using Ollama API
"""
import logging
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

from ..services.ollama_connection_checker import get_ollama_checker


# Job analysis result dataclass
@dataclass
class JobAnalysisResult:
    required_skills: List[str] = field(default_factory=list)
    job_requirements: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    experience_requirements: List[str] = field(default_factory=list)
    education_requirements: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    technical_skills: List[str] = field(default_factory=list)
    salary_info: Optional[str] = None
    remote_work: Optional[bool] = None
    benefits: List[str] = field(default_factory=list)


logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Configuration for Ollama client"""

    base_url: str = "http://localhost:11434"
    model: str = "llama3.2:1b"  # Fast, small model for job analysis
    timeout: int = 30
    temperature: float = 0.1
    max_tokens: int = 500


class OllamaClient:
    """Real Ollama client for job content analysis"""

    def __init__(self, config: Optional[OllamaConfig] = None):
        """Initialize Ollama client with configuration."""
        self.config = config or OllamaConfig()
        self.connection_checker = get_ollama_checker(self.config.base_url)
        self._available = None
        self._last_check = 0

    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        return self.connection_checker.is_available()

    def analyze_job_content(self, job_data: Dict[str, Any]) -> JobAnalysisResult:
        """
        Analyze job content using Ollama LLM.

        Args:
            job_data: Dictionary containing job information

        Returns:
            JobAnalysisResult with extracted insights
        """
        if not self.is_available():
            logger.warning("Ollama not available, returning empty analysis")
            return JobAnalysisResult()

        try:
            # Extract key fields for analysis
            title = job_data.get("title", "")
            description = job_data.get("description", "")
            company = job_data.get("company", "")

            # Create analysis prompt
            prompt = self._create_analysis_prompt(title, description, company)

            # Call Ollama API
            response = self._call_ollama(prompt)

            if response:
                return self._parse_analysis_response(response)
            else:
                return JobAnalysisResult()

        except Exception as e:
            logger.error(f"Error in Ollama job analysis: {e}")
            return JobAnalysisResult()

    def _create_analysis_prompt(self, title: str, description: str, company: str) -> str:
        """Create a focused prompt for job analysis."""
        prompt = f"""
Analyze this job posting and extract key information:

Job Title: {title}
Company: {company}
Description: {description[:1000]}...

Please provide:
1. Required skills (list)
2. Key requirements (list)  
3. Compatibility score (0-100)
4. Analysis confidence (0-100)
5. Benefits mentioned (list)
6. Brief reasoning

Format as JSON:
{{
    "required_skills": ["skill1", "skill2"],
    "job_requirements": ["req1", "req2"],
    "compatibility_score": 75,
    "analysis_confidence": 80,
    "extracted_benefits": ["benefit1", "benefit2"],
    "reasoning": "Brief explanation"
}}
"""
        return prompt

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Make API call to Ollama."""
        try:
            response = requests.post(
                f"{self.config.base_url}/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens,
                    },
                },
                timeout=self.config.timeout,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.warning(f"Ollama API returned status {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            return None

    def _parse_analysis_response(self, response: str) -> JobAnalysisResult:
        """Parse Ollama response into JobAnalysisResult."""
        try:
            import json
            import re

            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                return JobAnalysisResult(
                    required_skills=data.get("required_skills", []),
                    job_requirements=data.get("job_requirements", []),
                    compatibility_score=float(data.get("compatibility_score", 0)) / 100.0,
                    analysis_confidence=float(data.get("analysis_confidence", 0)) / 100.0,
                    extracted_benefits=data.get("extracted_benefits", []),
                    reasoning=data.get("reasoning", ""),
                    processing_time=0.0,  # Could add timing if needed
                )
            else:
                # Fallback parsing if JSON extraction fails
                return self._fallback_parse(response)

        except Exception as e:
            logger.error(f"Error parsing Ollama response: {e}")
            return JobAnalysisResult()

    def _fallback_parse(self, response: str) -> JobAnalysisResult:
        """Fallback parsing when JSON extraction fails."""
        # Basic text analysis as fallback
        skills = []
        requirements = []

        # Simple keyword extraction
        common_skills = ["python", "java", "sql", "javascript", "react", "aws", "docker"]
        for skill in common_skills:
            if skill.lower() in response.lower():
                skills.append(skill)

        return JobAnalysisResult(
            required_skills=skills,
            job_requirements=requirements,
            compatibility_score=0.5,  # Neutral score
            analysis_confidence=0.3,  # Low confidence for fallback
            extracted_benefits=[],
            reasoning="Fallback analysis due to parsing issues",
            processing_time=0.0,
        )


def get_ollama_client(config: Optional[OllamaConfig] = None) -> OllamaClient:
    """Factory function to get Ollama client."""
    return OllamaClient(config)


def get_gpu_ollama_client() -> OllamaClient:
    """
    Get Ollama client optimized for GPU usage.
    Note: This function name is kept for compatibility with existing tests.
    """
    config = OllamaConfig(
        model="llama3.2:3b",  # Larger model for better analysis
        timeout=45,
        temperature=0.05,  # Lower temperature for more consistent results
    )
    return OllamaClient(config)
