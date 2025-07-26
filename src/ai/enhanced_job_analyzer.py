#!/usr/bin/env python3
"""
Enhanced Job Analyzer with Mistral 7B Integration
Replaces current rule-based similarity logic with AI-powered analysis using Mistral 7B
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import json
import time

from .llama_job_analyzer import LlamaJobAnalyzer, JobAnalysisResult

logger = logging.getLogger(__name__)

# --- Constants for Analysis ---
ANALYSIS_METHOD_OPENHERMES = 'openhermes_2_5'
ANALYSIS_METHOD_MISTRAL = 'mistral_7b'  # Legacy support
ANALYSIS_METHOD_LLAMA3 = 'llama3'
ANALYSIS_METHOD_RULE_BASED = 'rule_based'
ANALYSIS_METHOD_FAILED = 'failed'

MATCH_QUALITY_EXCELLENT = 'excellent'
MATCH_QUALITY_GOOD = 'good'
MATCH_QUALITY_FAIR = 'fair'
MATCH_QUALITY_POOR = 'poor'
MATCH_QUALITY_VERY_POOR = 'very_poor'

PRIORITY_HIGH = 'high'
PRIORITY_MEDIUM = 'medium'
PRIORITY_LOW = 'low'
PRIORITY_SKIP = 'skip'


class EnhancedJobAnalyzer:
    """Enhanced job analyzer that uses Mistral 7B for sophisticated matching"""

    def __init__(self, profile: Dict, use_openhermes: bool = True, fallback_to_llama: bool = True, fallback_to_rule_based: bool = True):
        """
        Initialize enhanced analyzer.

        Args:
            profile: User profile dict.
            use_openhermes: Whether to use OpenHermes 2.5 for analysis (default: True).
            fallback_to_llama: Fall back to Llama3 if OpenHermes fails (default: True).
            fallback_to_rule_based: Fall back to rule-based if AI fails (default: True).
        """
        self.profile = profile
        self.use_openhermes = use_openhermes
        self.fallback_to_llama = fallback_to_llama
        self.fallback_to_rule_based = fallback_to_rule_based
        
        # Initialize analyzers
        self.openhermes_analyzer = None
        self.llama_analyzer = None
        self.rule_based_analyzer = None

        if self.use_openhermes:
            self._initialize_openhermes_analyzer()

        if self.fallback_to_llama:
            self._initialize_llama_analyzer()

        if self.fallback_to_rule_based or (not self.openhermes_analyzer and not self.llama_analyzer):
            self._initialize_rule_based_analyzer()

    def _initialize_openhermes_analyzer(self):
        """Initializes the OpenHermes 2.5 analyzer."""
        try:
            # Get OpenHermes configuration from profile
            openhermes_config = self.profile.get("openhermes_config", {})
            model_name = openhermes_config.get("model", "openhermes:v2.5")
            
            # Create OpenHermes-specific analyzer
            self.openhermes_analyzer = OpenHermesJobAnalyzer(
                model=model_name,
                config=openhermes_config
            )
            logger.info(f"✅ OpenHermes 2.5 analyzer initialized with model: {model_name}")
        except Exception as e:
            logger.warning(f"⚠️ OpenHermes 2.5 initialization failed: {e}")
            self.openhermes_analyzer = None
            if not self.fallback_to_llama and not self.fallback_to_rule_based:
                raise

    def _initialize_llama_analyzer(self):
        """Initializes the Llama3 analyzer as fallback."""
        try:
            ollama_model = self.profile.get("ollama_model", "llama3:latest")
            self.llama_analyzer = LlamaJobAnalyzer(model=ollama_model)
            logger.info(f"✅ Llama3 analyzer initialized as fallback: {ollama_model}")
        except Exception as e:
            logger.warning(f"⚠️ Llama3 initialization failed: {e}")
            self.llama_analyzer = None

    def _initialize_rule_based_analyzer(self):
        """Initializes the rule-based analyzer."""
        try:
            from src.utils.job_analyzer import JobAnalyzer
            self.rule_based_analyzer = JobAnalyzer(self.profile)
            logger.info("✅ Rule-based analyzer initialized as fallback")
        except Exception as e:
            logger.warning(f"⚠️ Rule-based analyzer initialization failed: {e}")
            self.rule_based_analyzer = None

    def analyze_job(self, job: Dict) -> Dict[str, Any]:
        """
        Analyze job compatibility using the best available method.

        Args:
            job: Job posting dict.

        Returns:
            Enhanced analysis result dict.
        """
        # Try OpenHermes 2.5 analysis first
        if self.openhermes_analyzer:
            try:
                openhermes_result = self.openhermes_analyzer.analyze_job(self.profile, job)
                if openhermes_result:
                    return self._convert_openhermes_result(openhermes_result, job)
                logger.warning("OpenHermes 2.5 analysis returned None, falling back to Llama3")
            except Exception as e:
                logger.error(f"OpenHermes 2.5 analysis failed: {e}")

        # Fallback to Llama3
        if self.fallback_to_llama and self.llama_analyzer:
            try:
                llama_result = self.llama_analyzer.analyze_job(self.profile, job)
                if llama_result:
                    return self._convert_llama_result(llama_result, job)
                logger.warning("Llama3 analysis returned None, falling back to rule-based")
            except Exception as e:
                logger.error(f"Llama3 analysis failed: {e}")

        # Fallback to rule-based analysis
        if self.fallback_to_rule_based and self.rule_based_analyzer:
            logger.info("Using rule-based analysis as fallback")
            rule_result = self.rule_based_analyzer.analyze_job(job)
            return self._enhance_rule_based_result(rule_result, job)

        logger.error("No analysis method available")
        return self._create_failed_result()

    def _convert_openhermes_result(self, openhermes_result: Dict, job: Dict) -> Dict[str, Any]:
        """Convert OpenHermes 2.5 analysis result to standard format."""
        try:
            # OpenHermes 2.5 provides comprehensive analysis
            analysis = {
                'compatibility_score': openhermes_result.get('match_score', {}).get('overall', 0.7),
                'confidence': openhermes_result.get('confidence', 0.7),
                'skill_matches': openhermes_result.get('keyword_analysis', {}).get('technical_skills', []),
                'skill_gaps': openhermes_result.get('skill_gaps', []),
                'experience_match': openhermes_result.get('experience_analysis', {}).get('level', 'unknown'),
                'location_match': openhermes_result.get('location_analysis', {}).get('remote_policy', 'unknown'),
                'cultural_fit': openhermes_result.get('match_score', {}).get('cultural_fit', 0.7),
                'growth_potential': openhermes_result.get('match_score', {}).get('growth_potential', 0.7),
                'recommendation': self._get_recommendation(openhermes_result.get('match_score', {}).get('overall', 0.7)),
                'reasoning': openhermes_result.get('reasoning', 'Analysis completed by OpenHermes 2.5'),
                'analysis_method': ANALYSIS_METHOD_OPENHERMES,
                'analysis_timestamp': time.time(),
                'openhermes_analysis': openhermes_result  # Keep full OpenHermes analysis
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error converting OpenHermes result: {e}")
            return self._create_failed_result()

    def _convert_llama_result(self, llama_result: JobAnalysisResult, job: Dict) -> Dict[str, Any]:
        """Convert Llama3 analysis result to standard format."""
        try:
            analysis = {
                'compatibility_score': llama_result.compatibility_score,
                'confidence': llama_result.confidence,
                'skill_matches': llama_result.skill_matches,
                'skill_gaps': llama_result.skill_gaps,
                'experience_match': llama_result.experience_match,
                'location_match': llama_result.location_match,
                'cultural_fit': llama_result.cultural_fit,
                'growth_potential': llama_result.growth_potential,
                'recommendation': llama_result.recommendation,
                'reasoning': llama_result.reasoning,
                'analysis_method': ANALYSIS_METHOD_LLAMA3,
                'analysis_timestamp': time.time()
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error converting Llama result: {e}")
            return self._create_failed_result()

    def _enhance_rule_based_result(self, rule_result: Dict, job: Dict) -> Dict[str, Any]:
        """Enhance rule-based result with additional analysis."""
        try:
            enhanced_result = rule_result.copy()
            
            # Add missing fields
            enhanced_result.update({
                'analysis_method': ANALYSIS_METHOD_RULE_BASED,
                'analysis_timestamp': time.time(),
                'confidence': 0.6,  # Lower confidence for rule-based
                'cultural_fit': 0.5,
                'growth_potential': 0.5,
                'skill_matches': rule_result.get('match_factors', []),
                'skill_gaps': self._identify_skill_gaps(job),
                'experience_match': self._assess_experience_match(job),
                'location_match': self._assess_location_match(job),
                'recommendation': self._get_recommendation(rule_result.get('compatibility_score', 0.5))
            })
            
            return enhanced_result
        except Exception as e:
            logger.error(f"Error enhancing rule-based result: {e}")
            return self._create_failed_result()

    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on compatibility score."""
        if score >= 0.9:
            return 'highly_recommend'
        elif score >= 0.7:
            return 'recommend'
        elif score >= 0.5:
            return 'consider'
        else:
            return 'skip'

    def _identify_skill_gaps(self, job: Dict) -> List[str]:
        """Identify potential skill gaps using a simple rule-based approach."""
        text = f"{job.get('title', '')} {job.get('summary', '')} {job.get('description', '')}".lower()
        profile_skills = {skill.lower() for skill in self.profile.get('skills', [])}
        
        potential_skills = {
            'python', 'sql', 'java', 'javascript', 'react', 'node', 'aws', 'docker',
            'kubernetes', 'machine learning', 'tensorflow', 'pytorch', 'powerbi',
            'tableau', 'excel', 'git', 'agile', 'scrum'
        }
        
        return [skill for skill in potential_skills if skill in text and skill not in profile_skills][:5]

    def _assess_experience_match(self, job: Dict) -> str:
        """Assess experience level match using a simple rule-based approach."""
        profile_exp = self.profile.get('experience_level', '').lower()
        job_exp = job.get('experience_level', '').lower()

        if not profile_exp or not job_exp:
            return 'unknown'
        if profile_exp in job_exp or job_exp in profile_exp:
            return 'perfect'
        if ('entry' in profile_exp and 'junior' in job_exp) or \
           ('junior' in profile_exp and 'entry' in job_exp):
            return 'close'
        return 'mismatch'

    def _assess_location_match(self, job: Dict) -> str:
        """Assess location match using a simple rule-based approach."""
        profile_loc = self.profile.get('location', '').lower()
        job_loc = job.get('location', '').lower()

        if 'remote' in job_loc:
            return 'remote_ok'
        if not profile_loc or not job_loc:
            return 'unknown'
        if profile_loc in job_loc or job_loc in profile_loc:
            return 'perfect'
        if any(common in profile_loc and common in job_loc for common in ['ontario', 'bc', 'alberta']):
            return 'nearby'
        return 'mismatch'

    def _create_failed_result(self) -> Dict[str, Any]:
        """Create a failed analysis result."""
        return {
            'compatibility_score': 0.5,
            'confidence': 0.0,
            'skill_matches': [],
            'skill_gaps': [],
            'experience_match': 'unknown',
            'location_match': 'unknown',
            'cultural_fit': 0.5,
            'growth_potential': 0.5,
            'recommendation': 'consider',
            'reasoning': 'Analysis failed - using default values',
            'analysis_method': ANALYSIS_METHOD_FAILED,
            'analysis_timestamp': time.time()
        }


class OpenHermesJobAnalyzer:
    """OpenHermes 2.5 specific job analyzer with optimized prompts."""
    
    def __init__(self, model: str = "openhermes:v2.5", config: Dict = None):
        """
        Initialize OpenHermes 2.5 analyzer.
        
        Args:
            model: OpenHermes model name
            config: Configuration dictionary
        """
        self.model = model
        self.config = config or {}
        self.ollama_url = "http://localhost:11434"
        
        # Default OpenHermes 2.5 configuration
        self.default_config = {
            "temperature": 0.2,  # Lower temperature for more consistent analysis
            "max_tokens": 2048,
            "top_p": 0.9,
            "analysis_timeout": 30
        }
        
        # Update with provided config
        self.default_config.update(self.config)
        
        logger.info(f"✅ OpenHermesJobAnalyzer initialized with model: {model}")
    
    def analyze_job(self, profile: Dict, job: Dict) -> Optional[Dict[str, Any]]:
        """
        Analyze job using OpenHermes 2.5 with comprehensive prompts.
        
        Args:
            profile: User profile
            job: Job posting data
            
        Returns:
            Comprehensive analysis result or None if failed
        """
        try:
            # Create comprehensive analysis prompt
            prompt = self._create_comprehensive_analysis_prompt(profile, job)
            
            # Get analysis from OpenHermes 2.5
            response = self._call_openhermes_api(prompt)
            
            if response:
                return self._parse_openhermes_response(response, job)
            else:
                logger.warning("OpenHermes 2.5 API call failed")
                return None
                
        except Exception as e:
            logger.error(f"Error in OpenHermes 2.5 analysis: {e}")
            return None
    
    def _create_comprehensive_analysis_prompt(self, profile: Dict, job: Dict) -> str:
        """Create comprehensive analysis prompt for OpenHermes 2.5."""
        
        # Extract key information
        job_title = job.get('title', 'Unknown')
        job_company = job.get('company', 'Unknown')
        job_location = job.get('location', 'Unknown')
        job_description = job.get('description', job.get('summary', ''))
        
        # Profile information
        profile_skills = ', '.join(profile.get('skills', []))
        profile_experience = profile.get('experience_level', 'Unknown')
        profile_location = profile.get('location', 'Unknown')
        
        return f"""You are an expert job analysis AI powered by OpenHermes 2.5. Analyze this job posting comprehensively.

CANDIDATE PROFILE:
- Skills: {profile_skills}
- Experience Level: {profile_experience}
- Location: {profile_location}

JOB POSTING:
- Title: {job_title}
- Company: {job_company}
- Location: {job_location}
- Description: {job_description[:2000]}...

ANALYSIS TASK:
Provide a comprehensive analysis in JSON format with these exact fields:

{{
    "salary_analysis": {{
        "extracted_range": "salary range if found",
        "market_position": "below_average|average|above_average|unknown",
        "confidence": 0.0-1.0
    }},
    "experience_analysis": {{
        "level": "entry|junior|mid|senior|executive",
        "years_required": "years range if found",
        "progression_path": "next career step",
        "confidence": 0.0-1.0
    }},
    "location_analysis": {{
        "primary_location": "specific location",
        "remote_policy": "remote|hybrid|onsite|not_specified",
        "relocation_required": true/false,
        "confidence": 0.0-1.0
    }},
    "keyword_analysis": {{
        "technical_skills": ["skill1", "skill2"],
        "soft_skills": ["skill1", "skill2"],
        "emerging_tech": ["tech1", "tech2"],
        "confidence": 0.0-1.0
    }},
    "skill_gaps": ["gap1", "gap2"],
    "match_score": {{
        "overall": 0.0-1.0,
        "skill_match": 0.0-1.0,
        "experience_match": 0.0-1.0,
        "location_match": 0.0-1.0,
        "cultural_fit": 0.0-1.0,
        "growth_potential": 0.0-1.0
    }},
    "confidence": 0.0-1.0,
    "reasoning": "2-3 sentence explanation"
}}

SCORING GUIDELINES:
- Skill alignment: 40% weight
- Experience level match: 25% weight
- Location compatibility: 15% weight
- Cultural fit: 10% weight
- Growth potential: 10% weight

Return ONLY valid JSON, no additional text."""
    
    def _call_openhermes_api(self, prompt: str) -> Optional[str]:
        """Call OpenHermes 2.5 API."""
        try:
            import requests
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.default_config["temperature"],
                    "top_p": self.default_config["top_p"],
                    "num_predict": self.default_config["max_tokens"]
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.default_config["analysis_timeout"]
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                logger.error(f"OpenHermes API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling OpenHermes API: {e}")
            return None
    
    def _parse_openhermes_response(self, response: str, job: Dict) -> Optional[Dict[str, Any]]:
        """Parse OpenHermes 2.5 response into structured data."""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
                
                # Validate and clean data
                cleaned_data = {
                    "salary_analysis": parsed_data.get("salary_analysis", {}),
                    "experience_analysis": parsed_data.get("experience_analysis", {}),
                    "location_analysis": parsed_data.get("location_analysis", {}),
                    "keyword_analysis": parsed_data.get("keyword_analysis", {}),
                    "skill_gaps": parsed_data.get("skill_gaps", []),
                    "match_score": parsed_data.get("match_score", {}),
                    "confidence": parsed_data.get("confidence", 0.5),
                    "reasoning": parsed_data.get("reasoning", "Analysis completed by OpenHermes 2.5")
                }
                
                return cleaned_data
            else:
                logger.warning("Could not extract JSON from OpenHermes response")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in OpenHermes response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing OpenHermes response: {e}")
            return None
