"""
Document Generator Module for AutoJobAgent
Provides document customization functionality with AI integration and fallback mechanisms.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime

from src.utils.error_tolerance_handler import with_retry, with_fallback, safe_execute

logger = logging.getLogger(__name__)

# Template placeholders that should be replaced
PLACEHOLDER_PATTERNS = [
    r'\{[^}]+\}',  # {placeholder}
    r'\[[^\]]+\]',  # [placeholder] 
    r'YOUR_\w+',   # YOUR_NAME, YOUR_EMAIL
    r'COMPANY_NAME',
    r'JOB_TITLE',
    r'HIRING_MANAGER'
]

@with_retry(max_attempts=3, exceptions=(Exception,))
def customize(document: Union[str, Dict[str, Any]], job_data: Dict[str, Any] = None, profile_data: Dict[str, Any] = None, **kwargs) -> Union[str, Dict[str, Any]]:
    """
    Customize a document (resume, cover letter, etc.) for a specific job application.
    
    This function integrates with AI services when available and provides fallback
    mechanisms for document customization.
    
    Args:
        document: The document content (string or dict)
        job_data: Job information including company, title, description, etc.
        profile_data: User profile information
        **kwargs: Additional customization parameters
    
    Returns:
        Customized document with job-specific modifications
    """
    if not document:
        logger.warning("No document content provided for customization")
        return document
    
    # Extract relevant data
    job_data = job_data or {}
    profile_data = profile_data or {}
    
    company = job_data.get('company', 'the company')
    job_title = job_data.get('title', job_data.get('job_title', 'the position'))
    job_description = job_data.get('description', job_data.get('job_description', ''))
    
    logger.info(f"Customizing document for {job_title} at {company}")
    
    try:
        # Try Automated customization first
        ai_result = _customize_with_ai(document, job_data, profile_data)
        if ai_result and _is_properly_customized(ai_result):
            logger.info("Successfully customized document using AI")
            return ai_result
    except Exception as e:
        logger.warning(f"AI customization failed: {e}")
    
    # Fallback to template-based customization
    try:
        template_result = _customize_with_templates(document, job_data, profile_data)
        if template_result and _is_properly_customized(template_result):
            logger.info("Successfully customized document using templates")
            return template_result
    except Exception as e:
        logger.warning(f"Template customization failed: {e}")
    
    # Final fallback to basic substitution
    try:
        basic_result = _basic_customization(document, job_data, profile_data)
        logger.info("Applied basic document customization")
        return basic_result
    except Exception as e:
        logger.error(f"All customization methods failed: {e}")
        return document

@with_fallback(fallback_value=None)
def _customize_with_ai(document: Union[str, Dict], job_data: Dict[str, Any], profile_data: Dict[str, Any]) -> Optional[Union[str, Dict]]:
    """
    Customize document using AI services (Gemini, OpenAI, etc.).
    
    Args:
        document: Document content to customize
        job_data: Job information
        profile_data: User profile information
    
    Returns:
        AI-customized document or None if AI is unavailable
    """
    try:
        # Try using the new DocumentModifier with AI capabilities
        from src.document_modifier.document_modifier import DocumentModifier
        
        # Get profile name from profile_data or use default
        profile_name = profile_data.get('profile_name', 'default')
        
        # Initialize DocumentModifier
        modifier = DocumentModifier(profile_name)
        
        # Check if we're generating a resume or cover letter
        doc_str = str(document).lower()
        
        if any(keyword in doc_str for keyword in ['cover letter', 'dear', 'sincerely']):
            # Generate AI cover letter
            result_path = modifier.generate_ai_cover_letter(job_data, profile_data)
            if result_path and Path(result_path).exists():
                # Read the generated content
                with open(result_path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        elif any(keyword in doc_str for keyword in ['resume', 'experience', 'skills', 'education']):
            # Generate AI resume
            result_path = modifier.generate_ai_resume(job_data, profile_data)
            if result_path and Path(result_path).exists():
                # Read the generated content
                with open(result_path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        # If no specific document type detected, try Gemini API directly
        from src.utils.gemini_client import GeminiClient
        
        gemini = GeminiClient()
        
        # Create a prompt for general document customization
        prompt = f"""
Please customize this document for a job application:

DOCUMENT TO CUSTOMIZE:
{document}

JOB DETAILS:
Company: {job_data.get('company', 'N/A')}
Position: {job_data.get('title', 'N/A')}
Description: {job_data.get('description', 'N/A')}

CANDIDATE PROFILE:
{json.dumps(profile_data, indent=2)}

Instructions:
1. Replace all placeholders with appropriate information
2. Tailor the content to the specific job and company
3. Maintain professional tone and formatting
4. Ensure all information is accurate and relevant

Return the customized document:
"""
        
        result = gemini.generate_content(prompt)
        
        if result and _validate_ai_result(result):
            return result
        
        logger.warning("AI service returned invalid result")
        return None
        
    except Exception as e:
        logger.warning(f"AI customization error: {e}")
        return None

def _customize_with_templates(document: Union[str, Dict], job_data: Dict[str, Any], profile_data: Dict[str, Any]) -> Union[str, Dict]:
    """
    Customize document using template-based substitution.
    
    Args:
        document: Document content to customize
        job_data: Job information
        profile_data: User profile information
    
    Returns:
        Template-customized document
    """
    # Define substitution mappings
    substitutions = _build_substitution_mappings(job_data, profile_data)
    
    if isinstance(document, str):
        return _apply_string_substitutions(document, substitutions)
    elif isinstance(document, dict):
        return _apply_dict_substitutions(document, substitutions)
    else:
        logger.warning(f"Unsupported document type: {type(document)}")
        return document

def _basic_customization(document: Union[str, Dict], job_data: Dict[str, Any], profile_data: Dict[str, Any]) -> Union[str, Dict]:
    """
    Apply basic customization without Improved AI or template features.
    
    Args:
        document: Document content to customize
        job_data: Job information
        profile_data: User profile information
    
    Returns:
        Basic customized document
    """
    # Basic substitutions that should always work
    basic_subs = {
        'COMPANY_NAME': job_data.get('company', '[Company Name]'),
        'JOB_TITLE': job_data.get('title', job_data.get('job_title', '[Job Title]')),
        'HIRING_MANAGER': job_data.get('hiring_manager', 'Hiring Manager'),
        'USER_NAME': profile_data.get('name', '[Your Name]'),
        'USER_EMAIL': profile_data.get('email', '[Your Email]'),
        'USER_PHONE': profile_data.get('phone', '[Your Phone]'),
        'TODAY_DATE': datetime.now().strftime('%B %d, %Y')
    }
    
    if isinstance(document, str):
        return _apply_string_substitutions(document, basic_subs)
    elif isinstance(document, dict):
        return _apply_dict_substitutions(document, basic_subs)
    else:
        return document

def _build_substitution_mappings(job_data: Dict[str, Any], profile_data: Dict[str, Any]) -> Dict[str, str]:
    """Build comprehensive substitution mappings from job and profile data."""
    mappings = {}
    
    # Job-related mappings
    if job_data:
        mappings.update({
            '{company}': job_data.get('company', '[Company Name]'),
            '{job_title}': job_data.get('title', job_data.get('job_title', '[Job Title]')),
            '{location}': job_data.get('location', '[Location]'),
            '{salary}': job_data.get('salary', '[Salary]'),
            '{department}': job_data.get('department', '[Department]'),
            'COMPANY_NAME': job_data.get('company', '[Company Name]'),
            'JOB_TITLE': job_data.get('title', job_data.get('job_title', '[Job Title]')),
        })
    
    # Profile-related mappings
    if profile_data:
        mappings.update({
            '{name}': profile_data.get('name', '[Your Name]'),
            '{email}': profile_data.get('email', '[Your Email]'),
            '{phone}': profile_data.get('phone', '[Your Phone]'),
            '{location}': profile_data.get('location', '[Your Location]'),
            'YOUR_NAME': profile_data.get('name', '[Your Name]'),
            'YOUR_EMAIL': profile_data.get('email', '[Your Email]'),
            'YOUR_PHONE': profile_data.get('phone', '[Your Phone]'),
        })
    
    # Date and time mappings
    now = datetime.now()
    mappings.update({
        '{date}': now.strftime('%B %d, %Y'),
        '{today}': now.strftime('%B %d, %Y'),
        'TODAY_DATE': now.strftime('%B %d, %Y'),
        'CURRENT_DATE': now.strftime('%B %d, %Y'),
    })
    
    return mappings

def _apply_string_substitutions(text: str, substitutions: Dict[str, str]) -> str:
    """Apply substitutions to a string document."""
    if not text:
        return text
    
    result = text
    for placeholder, replacement in substitutions.items():
        if placeholder in result:
            result = result.replace(placeholder, replacement)
            logger.debug(f"Replaced {placeholder} with {replacement}")
    
    return result

def _apply_dict_substitutions(doc_dict: Dict[str, Any], substitutions: Dict[str, str]) -> Dict[str, Any]:
    """Apply substitutions to a dictionary document recursively."""
    if not doc_dict:
        return doc_dict
    
    result = {}
    for key, value in doc_dict.items():
        if isinstance(value, str):
            result[key] = _apply_string_substitutions(value, substitutions)
        elif isinstance(value, dict):
            result[key] = _apply_dict_substitutions(value, substitutions)
        elif isinstance(value, list):
            result[key] = [
                _apply_string_substitutions(item, substitutions) if isinstance(item, str)
                else _apply_dict_substitutions(item, substitutions) if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result

def _is_properly_customized(document: Union[str, Dict]) -> bool:
    """
    Check if a document has been properly customized (no remaining placeholders).
    
    Args:
        document: Document to check
    
    Returns:
        True if document appears properly customized
    """
    if isinstance(document, str):
        content = document
    elif isinstance(document, dict):
        content = json.dumps(document)
    else:
        return True  # Can't verify other types
    
    # Check for common placeholder patterns
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, content):
            logger.debug(f"Found placeholder pattern: {pattern}")
            return False
    
    # Check for specific placeholder text
    placeholder_indicators = [
        '[Your Name]', '[Company Name]', '[Job Title]',
        '[Your Email]', '[Your Phone]', '[Date]',
        'PLACEHOLDER', 'TODO:', 'FIXME:'
    ]
    
    for indicator in placeholder_indicators:
        if indicator in content:
            logger.debug(f"Found placeholder indicator: {indicator}")
            return False
    
    return True

def _get_available_ai_service():
    """Try to get an available AI service for document customization."""
    try:
        # Try Gemini API first
        from src.ai_services.gemini_service import GeminiService
        service = GeminiService()
        if service.is_available():
            return service
    except ImportError:
        logger.debug("Gemini service not available")
    
    try:
        # Try OpenAI as fallback
        from src.ai_services.openai_service import OpenAIService
        service = OpenAIService()
        if service.is_available():
            return service
    except ImportError:
        logger.debug("OpenAI service not available")
    
    # No AI services available
    return None

def _prepare_ai_context(document: Union[str, Dict], job_data: Dict[str, Any], profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare context for Automated document customization."""
    return {
        'document': document,
        'job_data': job_data,
        'profile_data': profile_data,
        'task': 'customize_document',
        'requirements': [
            'Remove all placeholder text',
            'Customize content for the specific job and company',
            'Maintain professional tone',
            'Ensure accuracy and relevance'
        ]
    }

def _validate_ai_result(result: Any) -> bool:
    """Validate AI service result."""
    if not result:
        return False
    
    # Check if result contains the expected structure
    if isinstance(result, dict):
        return 'content' in result or 'document' in result
    elif isinstance(result, str):
        return len(result.strip()) > 0
    
    return False

# Compatibility functions for legacy code
def generate_ai_cover_letter(job_data: Dict[str, Any], profile_data: Dict[str, Any]) -> str:
    """Generate Automated cover letter (legacy compatibility function)."""
    logger.info("Legacy function called: generate_ai_cover_letter")
    
    # Basic cover letter template
    template = """Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company}. With my background in {skills}, I am confident I would be a valuable addition to your team.

{experience}

I am excited about the opportunity to contribute to {company} and would welcome the chance to discuss how my skills and experience align with your needs.

Sincerely,
{name}"""
    
    # Use the main customize function
    result = customize(template, job_data, profile_data)
    return result if isinstance(result, str) else str(result)

def generate_ai_resume(job_data: Dict[str, Any], profile_data: Dict[str, Any]) -> str:
    """Generate Automated resume summary (legacy compatibility function)."""
    logger.info("Legacy function called: generate_ai_resume")
    
    # Basic resume summary template
    template = """{name}
{email} | {phone}
{location}

PROFESSIONAL SUMMARY
{summary}

EXPERIENCE
{experience}

SKILLS
{skills}

EDUCATION
{education}"""
    
    # Use the main customize function
    result = customize(template, job_data, profile_data)
    return result if isinstance(result, str) else str(result) 