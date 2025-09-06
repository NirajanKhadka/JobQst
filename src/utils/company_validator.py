"""
Enhanced Company Database for Fast Local Validation
Provides comprehensive company validation without external API calls.
"""

import json
from pathlib import Path
from typing import Set, Dict, List

class CompanyValidator:
    """Fast local company validation with comprehensive database."""
    
    def __init__(self):
        self.companies_db = self._load_company_database()
        self.domain_cache = {}
    
    def _load_company_database(self) -> Set[str]:
        """Load comprehensive company database."""
        companies = set()
        
        # Fortune 500 companies
        fortune_500 = [
            "walmart", "amazon", "apple", "berkshire hathaway", "unitedhealth group",
            "mckesson", "cvs health", "exxon mobil", "alphabet", "comcast",
            "at&t", "microsoft", "johnson & johnson", "intel", "procter & gamble",
            "general motors", "ford motor", "cardinal health", "costco", "verizon",
            "chevron", "fannie mae", "general electric", "walgreens", "jpmorgan chase",
            "express scripts", "boeing", "facebook", "anthem", "dell technologies",
            "home depot", "ibm", "fedex", "humana", "wells fargo", "phillips 66",
            "valero energy", "bank of america", "kroger", "amerisourcebergen",
            "lockheed martin", "cigna", "freddie mac", "google", "energy transfer",
            "marathon petroleum", "caterpillar", "allstate", "state farm", "goldman sachs",
            "tesla", "netflix", "salesforce", "cisco", "oracle", "adobe", "nvidia",
            "paypal", "mastercard", "visa", "nike", "pfizer", "coca-cola", "pepsi",
            "walmart", "target", "best buy", "lowes", "starbucks", "mcdonalds",
            "uber", "airbnb", "spotify", "zoom", "slack", "shopify", "square"
        ]
        
        # Major Canadian Companies
        canadian_companies = [
            "shopify", "royal bank of canada", "toronto-dominion bank", "bank of nova scotia",
            "bank of montreal", "canadian imperial bank", "manulife", "sun life",
            "canadian national railway", "canadian pacific railway", "tc energy",
            "enbridge", "suncor", "canadian natural resources", "magna international",
            "loblaw", "canadian tire", "rogers communications", "bce", "telus",
            "alimentation couche-tard", "metro", "empire", "canadian national railway",
            "barrick gold", "franco-nevada", "agnico eagle", "kinross gold",
            "first quantum minerals", "teck resources", "nutrien", "potash corp",
            "blackberry", "constellation software", "cgi", "open text", "descartes"
        ]
        
        # Tech companies (common in job searches)
        tech_companies = [
            "google", "microsoft", "apple", "amazon", "facebook", "meta", "twitter", "x",
            "linkedin", "github", "gitlab", "atlassian", "slack", "zoom", "dropbox",
            "salesforce", "workday", "servicenow", "snowflake", "databricks", "palantir",
            "stripe", "square", "coinbase", "robinhood", "plaid", "twilio", "okta",
            "mongodb", "redis", "elastic", "datadog", "new relic", "splunk", "tableau",
            "looker", "dbt", "fivetran", "segment", "amplitude", "mixpanel", "heap",
            "docker", "kubernetes", "hashicorp", "terraform", "jenkins", "circleci",
            "travis ci", "github actions", "gitlab ci", "aws", "azure", "gcp",
            "cloudflare", "akamai", "fastly", "vercel", "netlify", "heroku", "digitalocean"
        ]
        
        # Financial services
        financial_companies = [
            "citi", "citigroup", "jpmorgan", "goldman sachs", "morgan stanley", "wells fargo",
            "bank of america", "charles schwab", "fidelity", "vanguard", "blackrock",
            "state street", "northern trust", "american express", "discover", "capital one",
            "ally financial", "synchrony", "credit karma", "mint", "personal capital",
            "betterment", "wealthfront", "acorns", "stash", "robinhood", "e*trade",
            "td ameritrade", "interactive brokers", "tastyworks", "webull", "m1 finance"
        ]
        
        # Healthcare & pharma
        healthcare_companies = [
            "johnson & johnson", "pfizer", "merck", "bristol myers squibb", "abbott",
            "medtronic", "thermo fisher", "danaher", "boston scientific", "stryker",
            "becton dickinson", "baxter", "edwards lifesciences", "intuitive surgical",
            "illumina", "regeneron", "gilead", "biogen", "amgen", "celgene", "genentech",
            "roche", "novartis", "sanofi", "glaxosmithkline", "astrazeneca", "bayer",
            "eli lilly", "takeda", "abbvie", "vertex", "moderna", "biontech", "crispr"
        ]
        
        # Consulting & professional services
        consulting_companies = [
            "mckinsey", "boston consulting group", "bain", "deloitte", "pwc", "ey", "kpmg",
            "accenture", "ibm consulting", "cognizant", "tcs", "infosys", "wipro", "hcl",
            "capgemini", "atos", "dxc technology", "booz allen hamilton", "oliver wyman",
            "a.t. kearney", "roland berger", "strategy&", "monitor deloitte", "l.e.k."
        ]
        
        # Add all companies to the set (lowercase for comparison)
        for company_list in [fortune_500, canadian_companies, tech_companies, 
                           financial_companies, healthcare_companies, consulting_companies]:
            companies.update(company.lower().strip() for company in company_list)
        
        return companies
    
    def validate_company_fast(self, company: str) -> dict:
        """Fast company validation with detailed results."""
        if not company or len(company) < 2:
            return {"is_valid": False, "confidence": 0.0, "method": "invalid_input"}
        
        company_clean = company.lower().strip()
        
        # Check against comprehensive database
        if company_clean in self.companies_db:
            return {"is_valid": True, "confidence": 0.95, "method": "database_match"}
        
        # Check partial matches for common variations
        for known_company in self.companies_db:
            if (known_company in company_clean or 
                company_clean in known_company or
                self._fuzzy_match(company_clean, known_company)):
                return {"is_valid": True, "confidence": 0.85, "method": "partial_match"}
        
        # Check against invalid patterns
        invalid_patterns = [
            'urgent', 'hiring now', 'apply today', 'job123', 'company xyz',
            'temp agency', 'staffing solution', 'recruitment firm', 'hr department'
        ]
        
        if any(pattern in company_clean for pattern in invalid_patterns):
            return {"is_valid": False, "confidence": 0.9, "method": "invalid_pattern"}
        
        # If no match but looks legitimate
        if self._looks_legitimate(company_clean):
            return {"is_valid": True, "confidence": 0.6, "method": "pattern_valid"}
        
        return {"is_valid": False, "confidence": 0.3, "method": "unknown"}
    
    def _fuzzy_match(self, company1: str, company2: str) -> bool:
        """Simple fuzzy matching for company names."""
        # Remove common suffixes/prefixes
        suffixes = [' inc', ' corp', ' ltd', ' llc', ' co', ' company', ' technologies']
        
        clean1 = company1
        clean2 = company2
        
        for suffix in suffixes:
            clean1 = clean1.replace(suffix, '')
            clean2 = clean2.replace(suffix, '')
        
        # Check if one is contained in the other after cleaning
        return clean1 in clean2 or clean2 in clean1
    
    def _looks_legitimate(self, company: str) -> bool:
        """Check if company name follows legitimate patterns."""
        # Basic legitimacy checks
        if len(company) < 2 or len(company) > 100:
            return False
        
        # Has reasonable word structure
        words = company.split()
        if len(words) > 10:  # Too many words
            return False
        
        # Contains mostly letters and reasonable punctuation
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-&.,()]+$', company):
            return False
        
        return True

# Convenience function
def validate_company_enhanced(company: str) -> dict:
    """Enhanced company validation - fast and comprehensive."""
    validator = CompanyValidator()
    return validator.validate_company_fast(company)
