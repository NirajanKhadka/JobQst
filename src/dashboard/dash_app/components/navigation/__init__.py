"""
Navigation Components Package
Navigation-related dashboard components following DEVELOPMENT_STANDARDS.md
"""

# Import navigation components
from .sidebar import create_sidebar
from .navigation import create_page_header

__all__ = ["create_sidebar", "create_page_header"]
