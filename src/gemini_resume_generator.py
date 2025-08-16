"""
Compatibility shim for moved GeminiResumeGenerator
This file provides backward compatibility for imports that expect GeminiResumeGenerator.
The actual implementation is now in src/utils/gemini_document_generator.py
"""

# Import the actual implementation and alias it for compatibility
try:
    from .utils.gemini_document_generator import GeminiDocumentGenerator as GeminiResumeGenerator
except ImportError:
    # Fallback for absolute imports
    from src.utils.gemini_document_generator import GeminiDocumentGenerator as GeminiResumeGenerator

# Export for direct imports
__all__ = ['GeminiResumeGenerator']
