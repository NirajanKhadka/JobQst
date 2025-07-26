"""
Gemini API Client for AutoJobAgent.

This module provides integration with Google's Gemini API for AI-powered
document generation including resumes and cover letters.
"""

import json
import logging
import os
from typing import Dict, Any, Optional
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GeminiConfig:
    """Configuration for Gemini API client."""
    api_key: str
    model: str = "gemini-1.5-flash"
    max_tokens: int = 2048
    temperature: float = 0.7


class GeminiClient:
    """Client for interacting with Google's Gemini API."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: The Gemini API key. If not provided, will look for environment variable.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', 'AIzaSyA-RFcsksKRxuKfcfgJ6AGZFoaZLQxbewI')
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.config = GeminiConfig(api_key=self.api_key)
        
    def generate_content(self, prompt: str, **kwargs) -> str:
        """
        Generate content using Gemini API.
        
        Args:
            prompt: The input prompt for content generation
            **kwargs: Additional parameters for the API call
            
        Returns:
            Generated content as string
        """
        try:
            url = f"{self.base_url}/{self.config.model}:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            params = {
                'key': self.api_key
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": kwargs.get('temperature', self.config.temperature),
                    "maxOutputTokens": kwargs.get('max_tokens', self.config.max_tokens),
                }
            }
            
            response = requests.post(url, headers=headers, params=params, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                logger.error(f"Unexpected API response format: {result}")
                return ""
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API request failed: {e}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected response format from Gemini API: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Gemini API call: {e}")
            raise
    
    def generate_resume(self, profile_data: Dict[str, Any], job_data: Dict[str, Any]) -> str:
        """
        Generate a tailored resume using Gemini API.
        
        Args:
            profile_data: User profile information
            job_data: Job posting details
            
        Returns:
            Generated resume content
        """
        prompt = self._create_resume_prompt(profile_data, job_data)
        return self.generate_content(prompt, temperature=0.6)
    
    def generate_cover_letter(self, profile_data: Dict[str, Any], job_data: Dict[str, Any]) -> str:
        """
        Generate a tailored cover letter using Gemini API.
        
        Args:
            profile_data: User profile information
            job_data: Job posting details
            
        Returns:
            Generated cover letter content
        """
        prompt = self._create_cover_letter_prompt(profile_data, job_data)
        return self.generate_content(prompt, temperature=0.7)
    
    def _create_resume_prompt(self, profile_data: Dict[str, Any], job_data: Dict[str, Any]) -> str:
        """Create a specialized prompt for resume generation."""
        company = job_data.get('company', 'the company')
        title = job_data.get('title', 'the position')
        description = job_data.get('description', 'No description provided')
        requirements = job_data.get('requirements', 'No requirements specified')
        
        prompt = f"""
You are an expert resume writer and career counselor. Create a professional, ATS-optimized resume tailored for this specific job application.

**CANDIDATE PROFILE:**
Name: {profile_data.get('name', 'N/A')}
Email: {profile_data.get('email', 'N/A')}
Phone: {profile_data.get('phone', 'N/A')}
Location: {profile_data.get('location', 'N/A')}
Current Summary: {profile_data.get('summary', 'N/A')}
Experience: {profile_data.get('experience', 'N/A')}
Skills: {profile_data.get('skills', 'N/A')}
Education: {profile_data.get('education', 'N/A')}
Certifications: {profile_data.get('certifications', 'N/A')}

**TARGET JOB:**
Company: {company}
Position: {title}
Job Description: {description}
Requirements: {requirements}

**INSTRUCTIONS:**
1. Create a professional resume that highlights relevant experience and skills for this specific role
2. Use strong action verbs and quantify achievements where possible
3. Ensure the resume is ATS-friendly with clear section headers
4. Tailor the professional summary to align with the job requirements
5. Emphasize skills and experience that match the job description
6. Keep it concise and professional (1-2 pages maximum)
7. Use consistent formatting and professional language

**FORMAT REQUIREMENTS:**
- Start with candidate's contact information
- Include a tailored professional summary
- List relevant work experience with bullet points
- Include a skills section with relevant keywords
- Add education and certifications
- Use clean, professional formatting suitable for ATS systems

Generate the complete resume content now:
"""
        return prompt
    
    def _create_cover_letter_prompt(self, profile_data: Dict[str, Any], job_data: Dict[str, Any]) -> str:
        """Create a specialized prompt for cover letter generation."""
        company = job_data.get('company', 'the company')
        title = job_data.get('title', 'the position')
        description = job_data.get('description', 'No description provided')
        
        prompt = f"""
You are an expert career counselor and professional writer. Create a compelling, personalized cover letter for this job application.

**CANDIDATE PROFILE:**
Name: {profile_data.get('name', 'N/A')}
Current Role/Summary: {profile_data.get('summary', 'N/A')}
Experience: {profile_data.get('experience', 'N/A')}
Skills: {profile_data.get('skills', 'N/A')}

**TARGET JOB:**
Company: {company}
Position: {title}
Job Description: {description}

**INSTRUCTIONS:**
1. Write a professional cover letter that demonstrates genuine interest in the role
2. Highlight specific achievements and skills that align with the job requirements
3. Show knowledge of the company and explain why you want to work there
4. Use a confident but humble tone
5. Include specific examples of relevant accomplishments
6. Keep it concise (3-4 paragraphs maximum)
7. End with a strong call to action

**FORMAT REQUIREMENTS:**
- Professional business letter format
- Address it to the hiring manager or team
- Include an engaging opening paragraph
- 2-3 body paragraphs highlighting relevant qualifications
- Professional closing paragraph with call to action
- Formal sign-off

Generate the complete cover letter content now:
"""
        return prompt
