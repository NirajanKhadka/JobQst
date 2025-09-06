"""
Domain-based Company Validation
Fast validation by checking if company websites exist.
"""

import socket
import requests
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class DomainValidator:
    """Validate companies by checking their domain existence."""
    
    def __init__(self):
        self.domain_cache = {}
        self.timeout = 3  # Fast timeout for speed
    
    def validate_company_domain(self, company: str) -> Dict[str, any]:
        """Validate company by checking if their domain exists."""
        if not company or len(company) < 2:
            return {
                "is_valid": False,
                "confidence": 0.0,
                "method": "invalid_input"
            }
        
        # First, check for obviously fake patterns
        fake_score = self._detect_fake_patterns(company)
        if fake_score > 0.7:
            return {
                "is_valid": False,
                "confidence": 0.9,
                "method": "fake_pattern_detected"
            }
        
        # Generate possible domain names
        domains = self._generate_domains(company)
        
        for domain in domains:
            if domain in self.domain_cache:
                result = self.domain_cache[domain]
                if result["exists"]:
                    # Adjust confidence based on fake score
                    confidence = max(0.8 - fake_score, 0.3)
                    return {
                        "is_valid": True,
                        "confidence": confidence,
                        "method": "domain_exists",
                        "domain": domain
                    }
        
        # Check domains that aren't cached
        for domain in domains:
            if domain not in self.domain_cache:
                exists = self._check_domain_exists(domain)
                self.domain_cache[domain] = {"exists": exists}
                
                if exists:
                    # Adjust confidence based on fake score
                    confidence = max(0.8 - fake_score, 0.3)
                    return {
                        "is_valid": True,
                        "confidence": confidence,
                        "method": "domain_exists",
                        "domain": domain
                    }
        
        return {
            "is_valid": False,
            "confidence": 0.4,
            "method": "no_domain_found"
        }
    
    def _detect_fake_patterns(self, company: str) -> float:
        """Detect fake company patterns. Returns score 0.0-1.0 (1.0 = definitely fake)."""
        company_lower = company.lower()
        fake_score = 0.0
        
        # Obvious fake indicators
        fake_keywords = [
            'urgent', 'hiring', 'apply', 'job', 'career', 'recruitment',
            'staffing', 'employment', 'temp', 'agency', 'solutions',
            'department', 'hr', 'human resources', 'now', 'today',
            'xyz', '123', 'inc temp', 'hiring corp'
        ]
        
        for keyword in fake_keywords:
            if keyword in company_lower:
                fake_score += 0.3
        
        # Suspicious patterns
        import re
        if re.search(r'[0-9]{3,}', company):  # Numbers like "123", "xyz123"
            fake_score += 0.4
        
        if re.search(r'[_]{2,}', company):  # Multiple underscores
            fake_score += 0.5
        
        if company.isupper() and len(company) > 8:  # ALL CAPS long names
            fake_score += 0.3
        
        # Generic patterns
        generic_patterns = ['company', 'corp', 'inc', 'ltd', 'llc']
        for pattern in generic_patterns:
            if pattern in company_lower:
                if len(company_lower.replace(pattern, '').strip()) < 4:
                    fake_score += 0.4  # Very short company name + suffix
        
        return min(fake_score, 1.0)

    def _generate_domains(self, company: str) -> list:
        """Generate possible domain names for a company."""
        company_clean = company.lower().strip()
        
        # Remove common suffixes
        suffixes = [
            ' inc', ' corp', ' ltd', ' llc', ' co', ' company', 
            ' technologies', ' tech', ' systems', ' solutions', 
            ' services', ' group'
        ]
        
        for suffix in suffixes:
            company_clean = company_clean.replace(suffix, '')
        
        # Clean company name for domain
        domain_base = ''.join(
            c for c in company_clean 
            if c.isalnum() or c in ['-', ' ']
        )
        domain_base = domain_base.replace(' ', '').replace('&', 'and')
        
        if not domain_base:
            return []
        
        # Generate possible domains
        domains = [
            f"{domain_base}.com",
            f"{domain_base}.ca",  # Canadian companies
            f"{domain_base}.org",
            f"{domain_base}inc.com",
            f"{domain_base}corp.com",
        ]
        
        # Add variations for multi-word companies
        if ' ' in company_clean:
            words = company_clean.split()
            if len(words) == 2:
                domains.extend([
                    f"{words[0]}{words[1]}.com",
                    f"{words[0]}-{words[1]}.com",
                    f"{words[0]}and{words[1]}.com"
                ])
        
        return list(set(domains))  # Remove duplicates
    
    def _check_domain_exists(self, domain: str) -> bool:
        """Check if a domain exists using DNS lookup."""
        try:
            # Fast DNS check
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False
        except Exception as e:
            logger.debug(f"Domain check error for {domain}: {e}")
            return False
    
    def _check_website_accessible(self, domain: str) -> bool:
        """Check if website is accessible (slower but more accurate)."""
        try:
            response = requests.head(f"https://{domain}", timeout=self.timeout)
            return response.status_code < 400
        except:
            try:
                response = requests.head(f"http://{domain}", timeout=self.timeout)
                return response.status_code < 400
            except:
                return False

# Convenience function
def validate_company_domain(company: str) -> Dict[str, any]:
    """Fast domain-based company validation."""
    validator = DomainValidator()
    return validator.validate_company_domain(company)
