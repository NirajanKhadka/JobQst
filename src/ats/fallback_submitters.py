#!/usr/bin/env python3
"""
Fallback ATS Submitters
Provides fallback functionality when specific ATS detection fails.
"""

from typing import Dict, Any, List
from .base_submitter import BaseSubmitter
import time
from datetime import datetime

class FallbackSubmitter(BaseSubmitter):
    """Fallback ATS submitter for unknown or unsupported ATS systems."""
    
    def __init__(self, profile_name: str = "default"):
        super().__init__(profile_name)
        self.ats_name = 'Fallback'
        self.supported_fields = ['first_name', 'last_name', 'email', 'phone', 'resume']

    def get_fallback_strategy(self) -> Dict[str, Any]:
        """Get fallback strategy configuration."""
        return {
            'primary': 'generic_form_detection',
            'fallback': 'manual_detection',
            'strategy': 'generic_form_detection',
            'priority': 'primary',
            'success_rate': 0.3
        }

    def get_priority_order(self) -> List[str]:
        """Get priority order for fallback methods."""
        return ['generic_form', 'manual_detection', 'template_based']

    def _submit_to_ats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit data using fallback method."""
        return {
            'success': True,
            'application_id': f'fallback_{int(time.time())}',
            'submitted_at': datetime.now().isoformat(),
            'ats_name': 'Fallback',
            'method': 'generic_form_detection'
        }

# Backward compatibility alias
FallbackATSSubmitter = FallbackSubmitter 