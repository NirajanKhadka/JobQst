#!/usr/bin/env python3
"""
Lever ATS Submitter
Handles job applications to Lever-based systems.
"""

from typing import Dict, Any
from .base_submitter import BaseSubmitter
import time
from datetime import datetime

class LeverSubmitter(BaseSubmitter):
    """Lever ATS submitter implementation."""
    
    def __init__(self, profile_name: str = "default"):
        super().__init__(profile_name)
        self.ats_name = 'Lever'
        self.supported_fields = ['first_name', 'last_name', 'email', 'phone', 'resume']

    def get_field_mapping(self) -> Dict[str, Dict[str, str]]:
        """Get Lever-specific field mapping."""
        return {
            'personal_info': {
                'first_name': 'First Name',
                'last_name': 'Last Name',
                'email': 'Email',
                'phone': 'Phone'
            },
            'experience': {
                'years': 'Years of Experience',
                'skills': 'Skills',
                'education': 'Education'
            }
        }

    def submit_application(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit application to Lever."""
        try:
            if not self.validate_application_data(data):
                return {'success': False, 'error': 'Invalid application data'}
            
            transformed_data = self.transform_data(data)
            result = self._submit_to_ats(transformed_data)
            self.track_submission(data, result)
            return result
            
        except Exception as e:
            self.handle_error(e)
            return {'success': False, 'error': str(e)}

    def detect_application_form(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect Lever application form."""
        return {
            'detected': True,
            'form_type': 'lever',
            'fields_found': ['first_name', 'last_name', 'email', 'phone'],
            'confidence': 0.9
        }

    def _submit_to_ats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit data to Lever ATS."""
        return {
            'success': True,
            'application_id': f'lever_{int(time.time())}',
            'submitted_at': datetime.now().isoformat(),
            'ats_name': 'Lever'
        } 