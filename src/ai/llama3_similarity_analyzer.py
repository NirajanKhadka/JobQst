#!/usr/bin/env python3
"""
Llama3-based Job Similarity Analyzer
Advanced AI-powered job matching using Llama3 via Ollama
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """Result of similarity analysis"""
    overall_score: float
    skill_match_score: float
    experience_match_score: float
    location_match_score: float
    role_fit_score: float
    reasoning: str
    matched_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]
    confidence: float


class Llama3SimilarityAnalyzer:
    """
    Advanced job similarity analyzer using Llama3 for intelligent matching
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """
        Initialize the Llama3 similarity analyzer
        
        Args:
            ollama_url: URL for Ollama API endpoint
        """
        self.ollama_url = ollama_url
        self.model = "llama3:latest"
        
        # Setup session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"],  # Updated for newer urllib3
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test connection to Ollama"""
        try:
            response = self.session.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                llama3_available = any('llama3' in model.get('name', '') for model in models)
                if llama3_available:
                    logger.info("✅ Llama3 connection successful")
                    return True
                else:
                    logger.warning("⚠️ Llama3 model not found in Ollama")
                    return False
            else:
                logger.error(f"❌ Ollama connection failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Ollama connection error: {e}")
            return False
    
    def _call_llama3(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """
        Make API call to Llama3 via Ollama
        
        Args:
            prompt: The prompt to send to Llama3
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response or None if failed
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.1,  # Low temperature for consistent analysis
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            response = self.session.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.error(f"Llama3 API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Llama3 API call failed: {e}")
            return None
    
    def analyze_job_similarity(self, profile: Dict[str, Any], job: Dict[str, Any]) -> SimilarityResult:
        """
        Analyze job similarity using Llama3 AI
        
        Args:
            profile: User profile with skills, experience, location preferences
            job: Job posting details
            
        Returns:
            Detailed similarity analysis result
        """
        try:
            # Create comprehensive prompt for Llama3
            prompt = self._create_similarity_prompt(profile, job)
            
            # Get AI analysis
            response = self._call_llama3(prompt, max_tokens=1500)
            
            if not response:
                # Fallback to basic analysis
                return self._fallback_analysis(profile, job)
            
            # Parse AI response
            return self._parse_ai_response(response, profile, job)
            
        except Exception as e:
            logger.error(f"Similarity analysis failed: {e}")
            return self._fallback_analysis(profile, job)
    
    def _create_similarity_prompt(self, profile: Dict[str, Any], job: Dict[str, Any]) -> str:
        """Create detailed prompt for Llama3 analysis"""
        
        # Extract profile information
        profile_skills = profile.get('skills', [])
        profile_keywords = profile.get('keywords', [])
        profile_experience = profile.get('experience_level', 'Unknown')
        profile_location = profile.get('location', 'Unknown')
        profile_preferences = profile.get('preferences', {})
        
        # Extract job information
        job_title = job.get('title', 'Unknown')
        job_company = job.get('company', 'Unknown')
        job_location = job.get('location', 'Unknown')
        job_summary = job.get('summary', '')
        job_description = job.get('description', '')
        job_experience = job.get('experience_level', 'Unknown')
        job_salary = job.get('salary', 'Not specified')
        
        prompt = f"""
You are an expert career advisor and job matching specialist. Analyze the compatibility between this candidate profile and job posting.

CANDIDATE PROFILE:
- Skills: {', '.join(profile_skills)}
- Keywords/Interests: {', '.join(profile_keywords)}
- Experience Level: {profile_experience}
- Location: {profile_location}
- Preferences: {json.dumps(profile_preferences, indent=2)}

JOB POSTING:
- Title: {job_title}
- Company: {job_company}
- Location: {job_location}
- Experience Level: {job_experience}
- Salary: {job_salary}
- Summary: {job_summary}
- Description: {job_description}

ANALYSIS REQUIRED:
Provide a comprehensive analysis in the following JSON format:

{{
    "overall_score": <float 0.0-1.0>,
    "skill_match_score": <float 0.0-1.0>,
    "experience_match_score": <float 0.0-1.0>,
    "location_match_score": <float 0.0-1.0>,
    "role_fit_score": <float 0.0-1.0>,
    "confidence": <float 0.0-1.0>,
    "matched_skills": [<list of matching skills>],
    "missing_skills": [<list of required skills candidate lacks>],
    "reasoning": "<detailed explanation of the match>",
    "recommendations": [<list of actionable recommendations>]
}}

SCORING GUIDELINES:
- overall_score: Overall compatibility (weighted average of all factors)
- skill_match_score: How well candidate's skills match job requirements
- experience_match_score: How well experience levels align
- location_match_score: Geographic compatibility
- role_fit_score: How well the role matches career trajectory
- confidence: How confident you are in this analysis

Be thorough, accurate, and provide actionable insights. Consider both explicit and implicit requirements.
"""
        
        return prompt
    
    def _parse_ai_response(self, response: str, profile: Dict[str, Any], job: Dict[str, Any]) -> SimilarityResult:
        """Parse Llama3 response into structured result"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
                
                return SimilarityResult(
                    overall_score=float(parsed_data.get('overall_score', 0.0)),
                    skill_match_score=float(parsed_data.get('skill_match_score', 0.0)),
                    experience_match_score=float(parsed_data.get('experience_match_score', 0.0)),
                    location_match_score=float(parsed_data.get('location_match_score', 0.0)),
                    role_fit_score=float(parsed_data.get('role_fit_score', 0.0)),
                    reasoning=parsed_data.get('reasoning', 'AI analysis completed'),
                    matched_skills=parsed_data.get('matched_skills', []),
                    missing_skills=parsed_data.get('missing_skills', []),
                    recommendations=parsed_data.get('recommendations', []),
                    confidence=float(parsed_data.get('confidence', 0.8))
                )
            else:
                # Parse text-based response
                return self._parse_text_response(response, profile, job)
                
        except json.JSONDecodeError:
            # Fallback to text parsing
            return self._parse_text_response(response, profile, job)
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
            return self._fallback_analysis(profile, job)
    
    def _parse_text_response(self, response: str, profile: Dict[str, Any], job: Dict[str, Any]) -> SimilarityResult:
        """Parse text-based AI response"""
        try:
            # Extract scores using regex
            overall_score = self._extract_score(response, r'overall[_\s]score[:\s]*([0-9]*\.?[0-9]+)')
            skill_score = self._extract_score(response, r'skill[_\s]match[_\s]score[:\s]*([0-9]*\.?[0-9]+)')
            experience_score = self._extract_score(response, r'experience[_\s]match[_\s]score[:\s]*([0-9]*\.?[0-9]+)')
            location_score = self._extract_score(response, r'location[_\s]match[_\s]score[:\s]*([0-9]*\.?[0-9]+)')
            role_score = self._extract_score(response, r'role[_\s]fit[_\s]score[:\s]*([0-9]*\.?[0-9]+)')
            
            # Extract reasoning
            reasoning = self._extract_reasoning(response)
            
            # Extract skills
            matched_skills = self._extract_skills(response, 'matched')
            missing_skills = self._extract_skills(response, 'missing')
            
            # Extract recommendations
            recommendations = self._extract_recommendations(response)
            
            return SimilarityResult(
                overall_score=overall_score,
                skill_match_score=skill_score,
                experience_match_score=experience_score,
                location_match_score=location_score,
                role_fit_score=role_score,
                reasoning=reasoning,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                recommendations=recommendations,
                confidence=0.7  # Medium confidence for text parsing
            )
            
        except Exception as e:
            logger.error(f"Text parsing error: {e}")
            return self._fallback_analysis(profile, job)
    
    def _extract_score(self, text: str, pattern: str) -> float:
        """Extract numerical score from text"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                score = float(match.group(1))
                return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
            except ValueError:
                pass
        return 0.0
    
    def _extract_reasoning(self, text: str) -> str:
        """Extract reasoning from AI response"""
        # Look for reasoning patterns
        patterns = [
            r'reasoning[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'explanation[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'analysis[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # Fallback: return first paragraph
        lines = text.split('\n')
        for line in lines:
            if len(line.strip()) > 50:  # Substantial content
                return line.strip()
        
        return "AI analysis completed successfully"
    
    def _extract_skills(self, text: str, skill_type: str) -> List[str]:
        """Extract skills list from text"""
        pattern = f'{skill_type}[_\s]skills?[:\s]*\[(.*?)\]'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            skills_text = match.group(1)
            # Extract quoted strings
            skills = re.findall(r'"([^"]*)"', skills_text)
            if not skills:
                # Fallback: split by comma
                skills = [s.strip() for s in skills_text.split(',') if s.strip()]
            return skills
        return []
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from text"""
        pattern = r'recommendations?[:\s]*\[(.*?)\]'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            rec_text = match.group(1)
            # Extract quoted strings
            recommendations = re.findall(r'"([^"]*)"', rec_text)
            if not recommendations:
                # Fallback: split by comma
                recommendations = [r.strip() for r in rec_text.split(',') if r.strip()]
            return recommendations
        return []
    
    def _fallback_analysis(self, profile: Dict[str, Any], job: Dict[str, Any]) -> SimilarityResult:
        """Fallback analysis when AI fails"""
        try:
            # Basic skill matching
            profile_skills = [s.lower() for s in profile.get('skills', [])]
            job_text = f"{job.get('title', '')} {job.get('summary', '')} {job.get('description', '')}".lower()
            
            matched_skills = []
            for skill in profile_skills:
                if skill in job_text:
                    matched_skills.append(skill)
            
            skill_score = len(matched_skills) / max(len(profile_skills), 1)
            
            # Experience matching
            profile_exp = profile.get('experience_level', '').lower()
            job_exp = job.get('experience_level', '').lower()
            exp_score = 1.0 if profile_exp in job_exp or job_exp in profile_exp else 0.3
            
            # Location matching
            profile_loc = profile.get('location', '').lower()
            job_loc = job.get('location', '').lower()
            loc_score = 1.0 if profile_loc in job_loc or job_loc in profile_loc else 0.2
            
            # Overall score
            overall_score = (skill_score * 0.5 + exp_score * 0.3 + loc_score * 0.2)
            
            return SimilarityResult(
                overall_score=overall_score,
                skill_match_score=skill_score,
                experience_match_score=exp_score,
                location_match_score=loc_score,
                role_fit_score=skill_score * 0.8,  # Approximate
                reasoning="Fallback analysis due to AI unavailability",
                matched_skills=matched_skills,
                missing_skills=[],
                recommendations=["Consider improving AI connection for better analysis"],
                confidence=0.5
            )
            
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return SimilarityResult(
                overall_score=0.0,
                skill_match_score=0.0,
                experience_match_score=0.0,
                location_match_score=0.0,
                role_fit_score=0.0,
                reasoning="Analysis failed",
                matched_skills=[],
                missing_skills=[],
                recommendations=[],
                confidence=0.0
            )
    
    def batch_analyze(self, profile: Dict[str, Any], jobs: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], SimilarityResult]]:
        """
        Analyze multiple jobs in batch
        
        Args:
            profile: User profile
            jobs: List of job postings
            
        Returns:
            List of (job, similarity_result) tuples sorted by score
        """
        results = []
        
        for job in jobs:
            try:
                result = self.analyze_job_similarity(profile, job)
                results.append((job, result))
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Batch analysis error for job {job.get('title', 'Unknown')}: {e}")
                # Add failed job with zero score
                failed_result = SimilarityResult(
                    overall_score=0.0,
                    skill_match_score=0.0,
                    experience_match_score=0.0,
                    location_match_score=0.0,
                    role_fit_score=0.0,
                    reasoning="Analysis failed",
                    matched_skills=[],
                    missing_skills=[],
                    recommendations=[],
                    confidence=0.0
                )
                results.append((job, failed_result))
        
        # Sort by overall score (descending)
        results.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        return results


def test_llama3_analyzer():
    """Test the Llama3 similarity analyzer"""
    try:
        # Initialize analyzer
        analyzer = Llama3SimilarityAnalyzer()
        
        # Test profile
        profile = {
            'skills': ['Python', 'Machine Learning', 'SQL', 'Power BI', 'AWS'],
            'keywords': ['data analysis', 'python', 'machine learning'],
            'experience_level': 'Entry Level',
            'location': 'Toronto, ON',
            'preferences': {
                'remote_work': True,
                'salary_min': 60000,
                'company_size': 'medium'
            }
        }
        
        # Test job
        job = {
            'title': 'Data Analyst',
            'company': 'Microsoft',
            'location': 'Toronto, ON',
            'summary': 'Looking for a Data Analyst with Python, SQL, Power BI experience.',
            'description': 'We need someone with Python, SQL, Power BI, and machine learning skills for data analysis.',
            'experience_level': 'entry',
            'salary': '$65,000 - $75,000'
        }
        
        # Analyze
        result = analyzer.analyze_job_similarity(profile, job)
        
        print(f"Overall Score: {result.overall_score:.3f}")
        print(f"Skill Match: {result.skill_match_score:.3f}")
        print(f"Experience Match: {result.experience_match_score:.3f}")
        print(f"Location Match: {result.location_match_score:.3f}")
        print(f"Role Fit: {result.role_fit_score:.3f}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Matched Skills: {result.matched_skills}")
        print(f"Missing Skills: {result.missing_skills}")
        print(f"Reasoning: {result.reasoning}")
        print(f"Recommendations: {result.recommendations}")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    test_llama3_analyzer()
