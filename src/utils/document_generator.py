"""
[DEPRECATED] Document Generator Module for AutoJobAgent.

This module has been migrated to src/document_modifier/document_modifier.py as part of the modularization effort.
Please update your imports to use the new DocumentModifier class and customize function from the document_modifier module.

This file will be removed in a future release.
"""

# For backward compatibility, import from the new location
from src.document_modifier.document_modifier import DocumentModifier, customize

# Export for backward compatibility
__all__ = ['DocumentModifier', 'customize']
