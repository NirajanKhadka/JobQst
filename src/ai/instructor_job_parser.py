#!/usr/bin/env python3
"""
Instructor-based Job Parser - Production Ready
Uses Instructor library with multiple LLM providers for reliable structured job parsing.
"""

import asyncio
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging

import instructor
from pydantic import BaseModel, Field
from openai import OpenAI, AsyncOpenAI
from sentence_transformers import SentenceTransformer
import numpy as np

# Try different providers
try:
    from groq import Groq, AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from anthropic import Anthropic, AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExperienceLevel(str, Enum):
    """Experience level enumeration."""
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    EXECUTIVE = "executive"
    UNKNOWN = "unknown"


class JobType(str, Enum):
    """Job type enumeration."""
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


class RemoteOption(str, Enum):
    """Remote work option enumeration."""
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    NOT_SPECIFIED = "not_specified"


class JobData(BaseModel):
    """Structured job data model."""
    title: str = Field(description="Exact job title")
    company: str = Field(description="Company name")
    location: str = Field(description="Job location")
    salary_range: Optional[str] = Field(None, description="Salary range if mentioned")
    experience_level: ExperienceLevel = Field(description="Required experience level")
    job_type: JobType = Field(description="Employment type")
    remote_option: RemoteOption = Field(description="Remote work policy")
    required_skills: List[str] = Field(description="Required technical skills")
    preferred_skills: List[str] = Field(description="Preferred skills")
    keywords: List[str] = Field(description="Industry keywords and technologies")
    benefits: List[str] = Field(description="Benefits and perks mentioned")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence score")


class JobParsingResult(BaseModel):
    """Complete job parsing result with similarity scoring."""
    job_data: JobData
    similarity_score: float = Field(ge=0.0, le=1.0, description="Profile similarity score")
    parsing_method: str = Field(description="LLM provider used")
    processing_time: float = Field(description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now)


class LLMProvider(str, Enum):
    """Available LLM providers."""
    GPT4O_MINI = "gpt-4o-mini"
    CLAUDE_HAIKU = "claude-3-haiku"
    GROQ_LLAMA = "groq-llama"
    QWEN_LOCAL = "qwen-local"


class InstructorJobParser:
    """Production-ready job parser using Instructor with multiple LLM providers."""
    
    def __init__(self, profile: Dict[str, Any], preferred_provider: LLMProvider = LLMProvider.GPT4O_MINI):
        """
        Initialize the job parser.
        
        Args:
            profile: User profile dictionary
            preferred_provider: Preferred LLM provider
        """
        self.profile = profile
        self.preferred_provider = preferred_provider
        
        # Initialize embedding model for similarity scoring
        self.embedding_model = None
        self.profile_embedding = None
        self._initialize_embedding_model()
        
        # Initialize LLM clients
        self.clients = {}
        self._initialize_clients()
        
        logger.info(f"InstructorJobParser initialized with {preferred_provider.value}")
    
    def _initialize_embedding_model(self):
        """Initialize sentence transformer for similarity scoring."""
        try:
            # Use a fast, accurate model for job similarity
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Create profile embedding
            profile_text = self._profile_to_text()
            self.profile_embedding = self.embedding_model.encode(profile_text)
            
            logger.info("✅ Embedding model initialized: all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize embedding model: {e}")
            logger.info("Install sentence-transformers: pip install sentence-transformers")
    
    def _profile_to_text(self) -> str:
        """Convert profile to text for embedding."""
        parts = []
        
        # Add skills
        skills = self.profile.get('skills', [])
        if skills:
            parts.append(f"Skills: {', '.join(skills)}")
        
        # Add keywords
        keywords = self.profile.get('keywords', [])
        if keywords:
            parts.append(f"Interests: {', '.join(keywords)}")
        
        # Add experience level
        experience = self.profile.get('experience_level', '')
        if experience:
            parts.append(f"Experience: {experience}")
        
        return '. '.join(parts)
    
    def _initialize_clients(self):
        """Initialize LLM clients with Instructor."""
        # OpenAI GPT-4o-mini
        if os.getenv('OPENAI_API_KEY'):
            try:
                openai_client = OpenAI()
                self.clients[LLMProvider.GPT4O_MINI] = instructor.from_openai(openai_client)
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI client failed: {e}")
        
        # Anthropic Claude
        if ANTHROPIC_AVAILABLE and os.getenv('ANTHROPIC_API_KEY'):
            try:
                anthropic_client = Anthropic()
                self.clients[LLMProvider.CLAUDE_HAIKU] = instructor.from_anthropic(anthropic_client)
                logger.info("✅ Anthropic client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Anthropic client failed: {e}")
        
        # Groq
        if GROQ_AVAILABLE and os.getenv('GROQ_API_KEY'):
            try:
                groq_client = Groq()
                self.clients[LLMProvider.GROQ_LLAMA] = instructor.from_groq(groq_client)
                logger.info("✅ Groq client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Groq client failed: {e}")
        
        # Local Ollama (Qwen)
        try:
            import requests
            # Test if Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                from openai import OpenAI as OllamaClient
                ollama_client = OllamaClient(
                    base_url="http://localhost:11434/v1",
                    api_key="ollama"  # Dummy key for Ollama
                )
                self.clients[LLMProvider.QWEN_LOCAL] = instructor.from_openai(ollama_client)
                logger.info("✅ Ollama client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Ollama client failed: {e}")
    
    async def parse_job(self, job_description: str, job_metadata: Dict[str, Any] = None) -> JobParsingResult:
        """
        Parse job description with structured output and similarity scoring.
        
        Args:
            job_description: Raw job description text
            job_metadata: Additional metadata (title, company, etc.)
            
        Returns:
            Complete job parsing result
        """
        start_time = datetime.now()
        job_metadata = job_metadata or {}
        
        # Try preferred provider first
        result = await self._try_parse_with_provider(self.preferred_provider, job_description, job_metadata)
        
        if not result:
            # Try fallback providers
            fallback_order = [
                LLMProvider.GPT4O_MINI,
                LLMProvider.CLAUDE_HAIKU,
                LLMProvider.GROQ_LLAMA,
                LLMProvider.QWEN_LOCAL
            ]
            
            for provider in fallback_order:
                if provider != self.preferred_provider and provider in self.clients:
                    result = await self._try_parse_with_provider(provider, job_description, job_metadata)
                    if result:
                        break
        
        if not result:
            # Final fallback: rule-based parsing
            logger.warning("All LLM providers failed, using rule-based parsing")
            result = self._rule_based_parse(job_description, job_metadata)
        
        # Calculate similarity score
        similarity_score = self._calculate_similarity_score(result, job_description)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return JobParsingResult(
            job_data=result,
            similarity_score=similarity_score,
            parsing_method=result.parsing_method if hasattr(result, 'parsing_method') else 'rule_based',
            processing_time=processing_time
        )
    
    async def _try_parse_with_provider(self, provider: LLMProvider, job_description: str, job_metadata: Dict[str, Any]) -> Optional[JobData]:
        """Try parsing with a specific provider."""
        if provider not in self.clients:
            return None
        
        try:
            client = self.clients[provider]
            
            # Create parsing prompt
            prompt = self._create_parsing_prompt(job_description, job_metadata)
            
            # Provider-specific parameters
            if provider == LLMProvider.GPT4O_MINI:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_model=JobData,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2048
                )
            elif provider == LLMProvider.CLAUDE_HAIKU:
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    response_model=JobData,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2048
                )
            elif provider == LLMProvider.GROQ_LLAMA:
                response = client.chat.completions.create(
                    model="llama3-70b-8192",
                    response_model=JobData,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2048
                )
            elif provider == LLMProvider.QWEN_LOCAL:
                response = client.chat.completions.create(
                    model="qwen2.5-coder:7b",
                    response_model=JobData,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2048
                )
            
            # Add parsing method to response
            response.parsing_method = provider.value
            return response
            
        except Exception as e:
            logger.warning(f"Parsing failed with {provider.value}: {e}")
            return None
    
    def _create_parsing_prompt(self, job_description: str, job_metadata: Dict[str, Any]) -> str:
        """Create optimized parsing prompt."""
        return f"""Extract structured information from this job posting. Be precise and comprehensive.

JOB POSTING:
Title: {job_metadata.get('title', 'Not specified')}
Company: {job_metadata.get('company', 'Not specified')}
Location: {job_metadata.get('location', 'Not specified')}

Description:
{job_description[:4000]}

EXTRACTION REQUIREMENTS:
- Extract ALL technical skills, programming languages, frameworks, tools
- Identify experience level from context (entry/junior/mid/senior/executive)
- Determine job type (full-time/part-time/contract/internship)
- Identify remote work policy (remote/hybrid/onsite)
- Extract salary/compensation if mentioned
- List benefits and perks
- Include industry keywords and technologies
- Provide confidence score (0.0-1.0) for extraction quality

Return structured data following the JobData model exactly."""
    
    def _calculate_similarity_score(self, job_data: JobData, job_description: str) -> float:
        """Calculate similarity score using embeddings."""
        if not self.embedding_model or self.profile_embedding is None:
            return self._rule_based_similarity(job_data)
        
        try:
            # Create job embedding
            job_text = self._job_data_to_text(job_data, job_description)
            job_embedding = self.embedding_model.encode(job_text)
            
            # Calculate cosine similarity
            similarity = np.dot(self.profile_embedding, job_embedding) / (
                np.linalg.norm(self.profile_embedding) * np.linalg.norm(job_embedding)
            )
            
            # Normalize to 0-1 range
            return max(0.0, min(1.0, (similarity + 1) / 2))
            
        except Exception as e:
            logger.warning(f"Embedding similarity failed: {e}")
            return self._rule_based_similarity(job_data)
    
    def _job_data_to_text(self, job_data: JobData, job_description: str) -> str:
        """Convert job data to text for embedding."""
        parts = []
        
        # Add title and company
        parts.append(f"Job: {job_data.title}")
        
        # Add skills
        all_skills = job_data.required_skills + job_data.preferred_skills
        if all_skills:
            parts.append(f"Skills: {', '.join(all_skills)}")
        
        # Add keywords
        if job_data.keywords:
            parts.append(f"Keywords: {', '.join(job_data.keywords)}")
        
        # Add experience level
        parts.append(f"Level: {job_data.experience_level}")
        
        # Add location and remote option
        parts.append(f"Location: {job_data.location}")
        parts.append(f"Remote: {job_data.remote_option}")
        
        return '. '.join(parts)
    
    def _rule_based_similarity(self, job_data: JobData) -> float:
        """Calculate similarity using rule-based approach."""
        profile_skills = set(skill.lower() for skill in self.profile.get('skills', []))
        profile_keywords = set(keyword.lower() for keyword in self.profile.get('keywords', []))
        
        # Job skills and keywords
        job_skills = set(skill.lower() for skill in job_data.required_skills + job_data.preferred_skills)
        job_keywords = set(keyword.lower() for keyword in job_data.keywords)
        
        # Calculate matches
        skill_matches = len(profile_skills.intersection(job_skills))
        keyword_matches = len(profile_keywords.intersection(job_keywords))
        
        # Calculate score
        total_profile_items = len(profile_skills) + len(profile_keywords)
        total_matches = skill_matches + keyword_matches
        
        if total_profile_items == 0:
            return 0.5
        
        return min(1.0, total_matches / total_profile_items)
    
    def _rule_based_parse(self, job_description: str, job_metadata: Dict[str, Any]) -> JobData:
        """Fallback rule-based parsing."""
        text = job_description.lower()
        
        # Extract skills
        common_skills = ['python', 'java', 'javascript', 'sql', 'react', 'node', 'aws', 'docker', 'git']
        found_skills = [skill for skill in common_skills if skill in text]
        
        # Extract experience level
        if any(word in text for word in ['senior', 'sr.', 'lead']):
            experience_level = ExperienceLevel.SENIOR
        elif any(word in text for word in ['junior', 'jr.', 'entry']):
            experience_level = ExperienceLevel.JUNIOR
        elif any(word in text for word in ['mid', 'intermediate']):
            experience_level = ExperienceLevel.MID
        else:
            experience_level = ExperienceLevel.UNKNOWN
        
        # Extract remote option
        if 'remote' in text:
            remote_option = RemoteOption.REMOTE
        elif 'hybrid' in text:
            remote_option = RemoteOption.HYBRID
        else:
            remote_option = RemoteOption.ONSITE
        
        return JobData(
            title=job_metadata.get('title', 'Unknown'),
            company=job_metadata.get('company', 'Unknown'),
            location=job_metadata.get('location', 'Unknown'),
            salary_range=None,
            experience_level=experience_level,
            job_type=JobType.UNKNOWN,
            remote_option=remote_option,
            required_skills=found_skills,
            preferred_skills=[],
            keywords=found_skills,
            benefits=[],
            confidence=0.6
        )


# Convenience functions for easy integration
async def parse_job_with_instructor(
    job_description: str, 
    profile: Dict[str, Any], 
    job_metadata: Dict[str, Any] = None,
    provider: LLMProvider = LLMProvider.GPT4O_MINI
) -> JobParsingResult:
    """Parse job using Instructor with specified provider."""
    parser = InstructorJobParser(profile, provider)
    return await parser.parse_job(job_description, job_metadata)


if __name__ == "__main__":
    # Test the instructor job parser
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
        result = await parse_job_with_instructor(
            test_job_description, 
            test_profile, 
            test_metadata,
            LLMProvider.GPT4O_MINI
        )
        
        print("Job Parsing Result:")
        print(f"Title: {result.job_data.title}")
        print(f"Company: {result.job_data.company}")
        print(f"Salary: {result.job_data.salary_range}")
        print(f"Experience Level: {result.job_data.experience_level}")
        print(f"Remote Option: {result.job_data.remote_option}")
        print(f"Required Skills: {result.job_data.required_skills}")
        print(f"Keywords: {result.job_data.keywords}")
        print(f"Similarity Score: {result.similarity_score:.3f}")
        print(f"Parsing Method: {result.parsing_method}")
        print(f"Processing Time: {result.processing_time:.2f}s")
        print(f"Confidence: {result.job_data.confidence:.3f}")
    
    asyncio.run(test_parser())