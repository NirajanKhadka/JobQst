"""
Free Web Search Integration for Company Validation
Uses Bing Web Search API (1000 free queries/month)
"""

import requests
import logging
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

class BingWebValidator:
    """Company validation using Bing Web Search API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Bing API key."""
        self.api_key = api_key or os.getenv('BING_SEARCH_API_KEY')
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
        self.cache = {}
        self.monthly_usage = 0
        self.max_monthly_queries = 1000  # Free tier limit
    
    def validate_company_web(self, company: str) -> Dict[str, any]:
        """Validate company using Bing web search."""
        if not self.api_key:
            return {"is_valid": True, "confidence": 0.5, "method": "no_api_key", 
                   "details": "Bing API key not configured"}
        
        if self.monthly_usage >= self.max_monthly_queries:
            return {"is_valid": True, "confidence": 0.5, "method": "quota_exceeded", 
                   "details": "Monthly quota exceeded"}
        
        if company in self.cache:
            return self.cache[company]
        
        try:
            # Search for company
            query = f'"{company}" company official website'
            headers = {'Ocp-Apim-Subscription-Key': self.api_key}
            params = {
                'q': query,
                'count': 5,
                'mkt': 'en-CA',  # Canadian market
                'safesearch': 'Strict'
            }
            
            response = requests.get(self.base_url, headers=headers, params=params, timeout=5)
            self.monthly_usage += 1
            
            if response.status_code == 200:
                data = response.json()
                result = self._analyze_search_results(company, data)
                self.cache[company] = result
                return result
            else:
                logger.warning(f"Bing API error: {response.status_code}")
                return {"is_valid": True, "confidence": 0.5, "method": "api_error"}
                
        except Exception as e:
            logger.error(f"Bing search error for {company}: {e}")
            return {"is_valid": True, "confidence": 0.5, "method": "search_failed"}
    
    def _analyze_search_results(self, company: str, data: dict) -> Dict[str, any]:
        """Analyze Bing search results to validate company."""
        web_pages = data.get('webPages', {}).get('value', [])
        
        if not web_pages:
            return {"is_valid": False, "confidence": 0.6, "method": "no_results"}
        
        company_lower = company.lower()
        confidence_score = 0.5
        found_evidence = []
        
        for page in web_pages[:3]:  # Check top 3 results
            title = page.get('name', '').lower()
            snippet = page.get('snippet', '').lower()
            url = page.get('url', '').lower()
            
            # Check for company name in title, snippet, or URL
            if company_lower in title:
                confidence_score += 0.2
                found_evidence.append("company_in_title")
            
            if company_lower in snippet:
                confidence_score += 0.1
                found_evidence.append("company_in_snippet")
            
            if company_lower.replace(' ', '') in url:
                confidence_score += 0.3
                found_evidence.append("company_in_url")
            
            # Look for official indicators
            if any(indicator in title or indicator in snippet for indicator in 
                   ['official', 'careers', 'about us', 'company', 'corporation']):
                confidence_score += 0.1
                found_evidence.append("official_indicators")
        
        confidence_score = min(confidence_score, 0.95)  # Cap at 95%
        
        return {
            "is_valid": confidence_score > 0.7,
            "confidence": confidence_score,
            "method": "bing_search",
            "evidence": found_evidence,
            "details": f"Found {len(web_pages)} results"
        }
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get current usage statistics."""
        return {
            "monthly_usage": self.monthly_usage,
            "remaining_queries": self.max_monthly_queries - self.monthly_usage,
            "cache_size": len(self.cache)
        }

# Other free options
class DuckDuckGoValidator:
    """Simplified DuckDuckGo validation (no API key needed)."""
    
    def validate_company_ddg(self, company: str) -> Dict[str, any]:
        """Validate using DuckDuckGo instant search."""
        try:
            url = f"https://api.duckduckgo.com/"
            params = {
                'q': f"{company} company",
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(url, params=params, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we got meaningful results
                if data.get('Abstract') or data.get('RelatedTopics'):
                    return {"is_valid": True, "confidence": 0.7, "method": "duckduckgo"}
            
            return {"is_valid": False, "confidence": 0.4, "method": "ddg_no_results"}
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return {"is_valid": True, "confidence": 0.5, "method": "ddg_error"}

# Convenience functions
def validate_company_bing(company: str, api_key: str = None) -> Dict[str, any]:
    """Validate company using Bing search."""
    validator = BingWebValidator(api_key)
    return validator.validate_company_web(company)

def validate_company_duckduckgo(company: str) -> Dict[str, any]:
    """Validate company using DuckDuckGo."""
    validator = DuckDuckGoValidator()
    return validator.validate_company_ddg(company)
