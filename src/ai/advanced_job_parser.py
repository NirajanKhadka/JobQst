#!/usr/bin/env python3
"""
Advanced Job Parser with Multiple LLM Options
Optimized for extracting structured data from job descriptions and calculating similarity scores.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import requests
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers for job parsing."""
    QWEN_CODER = "qwen2.5-coder"  # Best for structured extraction
    GPT4O_MINI = "gpt-4o-mini"    # Best API option
    CLAUDE_HAIKU = "claude-3-haiku"  # Fast and accurate
    MISTRAL_NEMO = "mistral-nemo"  # Good balance
    LLAMA_31 = "llama3.1"         # Improved Llama
    GEMINI_FLASH = "gemini-1.5-flash"  # Fast Google option


@dataclass
class JobParsingResult:
    """Structured result from job parsing."""
    title: str
    company: str
    location: str
    salary_range: Optional[str]
    experience_level: str
    job_type: str  # full-time, part-time, contract, etc.
    remote_option: str  # remote, hybrid, onsite
    required_skills: List[str]
    preferred_skills: List[str]
    keywords: List[str]
    benefits: List[str]
    similarity_score: float
    confidence: float
    parsing_method: str
    raw_extracted_data: Dict[str, Any]


class AdvancedJobParser:
    """Advanced job parser with multiple LLM backends and embedding-based similarity."""
    
    def __init__(self, profile: Dict[str, Any], preferred_provider: LLMProvider = LLMProvider.QWEN_CODER):
        """
        Initialize advanced job parser.
        
        Args:
            profile: User profile dictionary
            preferred_provider: Preferred LLM provider
        """
        self.profile = profile
        self.preferred_provider = preferred_provider
        
        # Initialize embedding model for similarity scoring
        self.embedding_model = None
        self._initialize_embedding_model()
        
        # LLM configurations
        self.llm_configs = {
            LLMProvider.QWEN_CODER: {
                "endpoint": "http://localhost:11434",
                "model": "qwen2.5-coder:7b",
                "temperature": 0.1,
                "max_tokens": 2048,
                "timeout": 30
            },
            LLMProvider.GPT4O_MINI: {
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-4o-mini",
                "temperature": 0.1,
                "max_tokens": 2048,
                "timeout": 30
            },
            LLMProvider.CLAUDE_HAIKU: {
                "endpoint": "https://api.anthropic.com/v1/messages",
                "model": "claude-3-haiku-20240307",
                "temperature": 0.1,
                "max_tokens": 2048,
                "timeout": 30
            },
            LLMProvider.MISTRAL_NEMO: {
                "endpoint": "http://localhost:11434",
                "model": "mistral-nemo:latest",
                "temperature": 0.1,
                "max_tokens": 2048,
                "timeout": 30
            },
            LLMProvider.LLAMA_31: {
                "endpoint": "http://localhost:11434",
                "model": "llama3.1:8b",
                "temperature": 0.1,
                "max_tokens": 2048,
                "timeout": 30
            },
            LLMProvider.GEMINI_FLASH: {
                "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
                "model": "gemini-1.5-flash",
                "temperature": 0.1,
                "max_tokens": 2048,
                "timeout": 30
            }
        }
        
        # Profile embeddings for similarity calculation
        self.profile_embedding = None
        self._create_profile_embedding()
        
        logger.info(f"AdvancedJobParser initialized with {preferred_provider.value}")
    
    def _initialize_embedding_model(self):
        """Initialize sentence transformer for similarity scoring."""
        try:
            # Use a fast, accurate model for job similarity
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Embedding model initialized: all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize embedding model: {e}")
            logger.info("Install sentence-transformers: pip install sentence-transformers")
    
    def _create_profile_embedding(self):
        """Create embedding representation of user profile."""
        if not self.embedding_model:
            return
        
        try:
            # Combine profile information into text
            profile_text = self._profile_to_text(self.profile)
            self.profile_embedding = self.embedding_model.encode(profile_text)
            logger.info("✅ Profile embedding created")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create profile embedding: {e}")
    
    def _profile_to_text(self, profile: Dict[str, Any]) -> str:
        """Convert profile to text for embedding."""
        parts = []
        
        # Add skills
        skills = profile.get('skills', [])
        if skills:
            parts.append(f"Skills: {', '.join(skills)}")
        
        # Add keywords
        keywords = profile.get('keywords', [])
        if keywords:
            parts.append(f"Interests: {', '.join(keywords)}")
        
        # Add experience level
        experience = profile.get('experience_level', '')
        if experience:
            parts.append(f"Experience: {experience}")
        
        # Add location preference
        location = profile.get('location', '')
        if location:
            parts.append(f"Location: {location}")
        
        return '. '.join(parts)
    
    async def parse_job(self, job_description: str, job_metadata: Dict[str, Any] = None) -> JobParsingResult:
        """
        Parse job description and calculate similarity score.
        
        Args:
            job_description: Raw job description text
            job_metadata: Additional job metadata (title, company, etc.)
            
        Returns:
            Structured job parsing result
        """
        job_metadata = job_metadata or {}
        
        # Try preferred provider first
        result = await self._try_parse_with_provider(self.preferred_provider, job_description, job_metadata)
        
        if result:
            return result
        
        # Try fallback providers
        fallback_order = [
            LLMProvider.MISTRAL_NEMO,
            LLMProvider.LLAMA_31,
            LLMProvider.GPT4O_MINI,
            LLMProvider.GEMINI_FLASH
        ]
        
        for provider in fallback_order:
            if provider != self.preferred_provider:
                result = await self._try_parse_with_provider(provider, job_description, job_metadata)
                if result:
                    return result
        
        # Final fallback: rule-based parsing
        logger.warning("All LLM providers failed, using rule-based parsing")
        return self._rule_based_parse(job_description, job_metadata)
    
    async def _try_parse_with_provider(self, provider: LLMProvider, job_description: str, job_metadata: Dict[str, Any]) -> Optional[JobParsingResult]:
        """Try parsing with a specific LLM provider."""
        try:
            config = self.llm_configs[provider]
            
            # Create parsing prompt
            prompt = self._create_parsing_prompt(job_description, job_metadata)
            
            # Call LLM
            response = await self._call_llm(provider, prompt, config)
            
            if response:
                # Parse LLM response
                parsed_data = self._parse_llm_response(response)
                
                if parsed_data:
                    # Calculate similarity score
                    similarity_score = self._calculate_similarity_score(parsed_data, job_description)
                    
                    # Create result
                    return JobParsingResult(
                        title=parsed_data.get('title', job_metadata.get('title', 'Unknown')),
                        company=parsed_data.get('company', job_metadata.get('company', 'Unknown')),
                        location=parsed_data.get('location', job_metadata.get('location', 'Unknown')),
                        salary_range=parsed_data.get('salary_range'),
                        experience_level=parsed_data.get('experience_level', 'Unknown'),
                        job_type=parsed_data.get('job_type', 'Unknown'),
                        remote_option=parsed_data.get('remote_option', 'Unknown'),
                        required_skills=parsed_data.get('required_skills', []),
                        preferred_skills=parsed_data.get('preferred_skills', []),
                        keywords=parsed_data.get('keywords', []),
                        benefits=parsed_data.get('benefits', []),
                        similarity_score=similarity_score,
                        confidence=parsed_data.get('confidence', 0.8),
                        parsing_method=provider.value,
                        raw_extracted_data=parsed_data
                    )
            
        except Exception as e:
            logger.warning(f"Parsing failed with {provider.value}: {e}")
        
        return None
    
    def _create_parsing_prompt(self, job_description: str, job_metadata: Dict[str, Any]) -> str:
        """Create optimized parsing prompt for job extraction."""
        
        return f"""You are an expert job description parser. Extract structured information from this job posting.

JOB POSTING:
Title: {job_metadata.get('title', 'Not specified')}
Company: {job_metadata.get('company', 'Not specified')}
Location: {job_metadata.get('location', 'Not specified')}

Description:
{job_description[:3000]}

EXTRACT the following information and return ONLY valid JSON:

{{
    "title": "exact job title",
    "company": "company name",
    "location": "job location",
    "salary_range": "salary range if mentioned (e.g., '$80,000-$120,000', 'Competitive', null)",
    "experience_level": "entry|junior|mid|senior|executive",
    "job_type": "full-time|part-time|contract|internship|temporary",
    "remote_option": "remote|hybrid|onsite|not_specified",
    "required_skills": ["skill1", "skill2", "skill3"],
    "preferred_skills": ["skill1", "skill2"],
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "benefits": ["benefit1", "benefit2"],
    "confidence": 0.0-1.0
}}

EXTRACTION RULES:
- Extract ALL technical skills mentioned
- Include programming languages, frameworks, tools
- Identify soft skills and certifications
- Extract salary/compensation if mentioned
- Determine remote work policy
- List benefits and perks
- Keywords should include industry terms, technologies, methodologies

Return ONLY the JSON object, no additional text."""
    
    async def _call_llm(self, provider: LLMProvider, prompt: str, config: Dict[str, Any]) -> Optional[str]:
        """Call specific LLM provider."""
        try:
            if provider in [LLMProvider.QWEN_CODER, LLMProvider.MISTRAL_NEMO, LLMProvider.LLAMA_31]:
                return await self._call_ollama(prompt, config)
            elif provider == LLMProvider.GPT4O_MINI:
                return await self._call_openai(prompt, config)
            elif provider == LLMProvider.CLAUDE_HAIKU:
                return await self._call_claude(prompt, config)
            elif provider == LLMProvider.GEMINI_FLASH:
                return await self._call_gemini(prompt, config)
        except Exception as e:
            logger.error(f"LLM call failed for {provider.value}: {e}")
        
        return None
    
    async def _call_ollama(self, prompt: str, config: Dict[str, Any]) -> Optional[str]:
        """Call Ollama API."""
        try:
            payload = {
                "model": config["model"],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": config["temperature"],
                    "num_predict": config["max_tokens"]
                }
            }
            
            response = requests.post(
                f"{config['endpoint']}/api/generate",
                json=payload,
                timeout=config["timeout"]
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
        
        return None
    
    async def _call_openai(self, prompt: str, config: Dict[str, Any]) -> Optional[str]:
        """Call OpenAI API."""
        try:
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY not set")
                return None
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": config["temperature"],
                "max_tokens": config["max_tokens"]
            }
            
            response = requests.post(
                config["endpoint"],
                headers=headers,
                json=payload,
                timeout=config["timeout"]
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
        
        return None
    
    async def _call_claude(self, prompt: str, config: Dict[str, Any]) -> Optional[str]:
        """Call Claude API."""
        try:
            import os
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY not set")
                return None
            
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": config["model"],
                "max_tokens": config["max_tokens"],
                "temperature": config["temperature"],
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(
                config["endpoint"],
                headers=headers,
                json=payload,
                timeout=config["timeout"]
            )
            
            if response.status_code == 200:
                return response.json()["content"][0]["text"]
        except Exception as e:
            logger.error(f"Claude API error: {e}")
        
        return None
    
    async def _call_gemini(self, prompt: str, config: Dict[str, Any]) -> Optional[str]:
        """Call Gemini API."""
        try:
            import os
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.warning("GEMINI_API_KEY not set")
                return None
            
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": config["temperature"],
                    "maxOutputTokens": config["max_tokens"]
                }
            }
            
            response = requests.post(
                f"{config['endpoint']}?key={api_key}",
                headers=headers,
                json=payload,
                timeout=config["timeout"]
            )
            
            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
        
        return None
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response to extract JSON."""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
        
        return None
    
    def _calculate_similarity_score(self, parsed_data: Dict[str, Any], job_description: str) -> float:
        """Calculate similarity score using embeddings."""
        if not self.embedding_model or not self.profile_embedding:
            return self._rule_based_similarity(parsed_data)
        
        try:
            # Create job embedding
            job_text = self._job_data_to_text(parsed_data, job_description)
            job_embedding = self.embedding_model.encode(job_text)
            
            # Calculate cosine similarity
            similarity = np.dot(self.profile_embedding, job_embedding) / (
                np.linalg.norm(self.profile_embedding) * np.linalg.norm(job_embedding)
            )
            
            # Normalize to 0-1 range
            return max(0.0, min(1.0, (similarity + 1) / 2))
            
        except Exception as e:
            logger.warning(f"Embedding similarity failed: {e}")
            return self._rule_based_similarity(parsed_data)
    
    def _job_data_to_text(self, parsed_data: Dict[str, Any], job_description: str) -> str:
        """Convert job data to text for embedding."""
        parts = []
        
        # Add title and company
        if parsed_data.get('title'):
            parts.append(f"Job: {parsed_data['title']}")
        
        # Add skills
        required_skills = parsed_data.get('required_skills', [])
        preferred_skills = parsed_data.get('preferred_skills', [])
        all_skills = required_skills + preferred_skills
        if all_skills:
            parts.append(f"Skills: {', '.join(all_skills)}")
        
        # Add keywords
        keywords = parsed_data.get('keywords', [])
        if keywords:
            parts.append(f"Keywords: {', '.join(keywords)}")
        
        # Add experience level
        if parsed_data.get('experience_level'):
            parts.append(f"Level: {parsed_data['experience_level']}")
        
        # Add location and remote option
        if parsed_data.get('location'):
            parts.append(f"Location: {parsed_data['location']}")
        if parsed_data.get('remote_option'):
            parts.append(f"Remote: {parsed_data['remote_option']}")
        
        return '. '.join(parts)
    
    def _rule_based_similarity(self, parsed_data: Dict[str, Any]) -> float:
        """Calculate similarity using rule-based approach."""
        profile_skills = set(skill.lower() for skill in self.profile.get('skills', []))
        profile_keywords = set(keyword.lower() for keyword in self.profile.get('keywords', []))
        
        # Job skills and keywords
        job_skills = set(skill.lower() for skill in parsed_data.get('required_skills', []) + parsed_data.get('preferred_skills', []))
        job_keywords = set(keyword.lower() for keyword in parsed_data.get('keywords', []))
        
        # Calculate matches
        skill_matches = len(profile_skills.intersection(job_skills))
        keyword_matches = len(profile_keywords.intersection(job_keywords))
        
        # Calculate score
        total_profile_items = len(profile_skills) + len(profile_keywords)
        total_matches = skill_matches + keyword_matches
        
        if total_profile_items == 0:
            return 0.5
        
        return min(1.0, total_matches / total_profile_items)
    
    def _rule_based_parse(self, job_description: str, job_metadata: Dict[str, Any]) -> JobParsingResult:
        """Fallback rule-based parsing."""
        # Simple keyword extraction
        text = job_description.lower()
        
        # Extract skills
        common_skills = ['python', 'java', 'javascript', 'sql', 'react', 'node', 'aws', 'docker', 'git']
        found_skills = [skill for skill in common_skills if skill in text]
        
        # Extract experience level
        if any(word in text for word in ['senior', 'sr.', 'lead']):
            experience_level = 'senior'
        elif any(word in text for word in ['junior', 'jr.', 'entry']):
            experience_level = 'junior'
        elif any(word in text for word in ['mid', 'intermediate']):
            experience_level = 'mid'
        else:
            experience_level = 'unknown'
        
        # Extract remote option
        if 'remote' in text:
            remote_option = 'remote'
        elif 'hybrid' in text:
            remote_option = 'hybrid'
        else:
            remote_option = 'onsite'
        
        similarity_score = self._rule_based_similarity({
            'required_skills': found_skills,
            'preferred_skills': [],
            'keywords': found_skills
        })
        
        return JobParsingResult(
            title=job_metadata.get('title', 'Unknown'),
            company=job_metadata.get('company', 'Unknown'),
            location=job_metadata.get('location', 'Unknown'),
            salary_range=None,
            experience_level=experience_level,
            job_type='unknown',
            remote_option=remote_option,
            required_skills=found_skills,
            preferred_skills=[],
            keywords=found_skills,
            benefits=[],
            similarity_score=similarity_score,
            confidence=0.6,
            parsing_method='rule_based_fallback',
            raw_extracted_data={}
        )


# Convenience functions for easy integration
async def parse_job_with_qwen(job_description: str, profile: Dict[str, Any], job_metadata: Dict[str, Any] = None) -> JobParsingResult:
    """Parse job using Qwen2.5-Coder (recommended for structured extraction)."""
    parser = AdvancedJobParser(profile, LLMProvider.QWEN_CODER)
    return await parser.parse_job(job_description, job_metadata)


async def parse_job_with_gpt4o_mini(job_description: str, profile: Dict[str, Any], job_metadata: Dict[str, Any] = None) -> JobParsingResult:
    """Parse job using GPT-4o-mini (best API option)."""
    parser = AdvancedJobParser(profile, LLMProvider.GPT4O_MINI)
    return await parser.parse_job(job_description, job_metadata)


async def parse_job_with_mistral_nemo(job_description: str, profile: Dict[str, Any], job_metadata: Dict[str, Any] = None) -> JobParsingResult:
    """Parse job using Mistral-Nemo (good balance of speed and accuracy)."""
    parser = AdvancedJobParser(profile, LLMProvider.MISTRAL_NEMO)
    return await parser.parse_job(job_description, job_metadata)


if __name__ == "__main__":
    # Test the advanced job parser
    import asyncio
    
    test_profile = {
        'skills': ['Python', 'SQL', 'Machine Learning', 'Docker'],
        'keywords': ['Data Science', 'AI', 'Backend Development'],
        'experience_level': 'Senior',
        'location': 'Remote'
    }
    
    test_job_description = """
    Senior Python Developer - AI/ML Focus
    
    We're looking for a Senior Python Developer with strong experience in machine learning 
    and data science. You'll work on cutting-edge AI projects using Python, SQL, and modern 
    ML frameworks like TensorFlow and PyTorch.
    
    Requirements:
    - 5+ years Python development
    - Strong SQL skills
    - Experience with Docker and AWS
    - Machine Learning background
    - Remote work available
    
    Salary: $120,000 - $150,000
    Benefits: Health insurance, 401k, flexible PTO
    """
    
    test_metadata = {
        'title': 'Senior Python Developer',
        'company': 'AI Innovations Inc',
        'location': 'Remote'
    }
    
    async def test_parser():
        parser = AdvancedJobParser(test_profile, LLMProvider.QWEN_CODER)
        result = await parser.parse_job(test_job_description, test_metadata)
        
        print("Job Parsing Result:")
        print(f"Title: {result.title}")
        print(f"Company: {result.company}")
        print(f"Salary: {result.salary_range}")
        print(f"Experience Level: {result.experience_level}")
        print(f"Remote Option: {result.remote_option}")
        print(f"Required Skills: {result.required_skills}")
        print(f"Keywords: {result.keywords}")
        print(f"Similarity Score: {result.similarity_score:.3f}")
        print(f"Parsing Method: {result.parsing_method}")
        print(f"Confidence: {result.confidence:.3f}")
    
    asyncio.run(test_parser())