"""
Industry Standards Database

Hybrid approach combining traditional standards with AI-powered validation
for comprehensive job title, skills, companies, and location validation.
"""

from typing import Set, Optional, List, Tuple
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Try to import AI standards, fallback gracefully
try:
    from .ai_industry_standards import (
        get_ai_industry_standards
    )
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logger.warning("AI industry standards not available")


class IndustryStandardsDatabase:
    """
    Hybrid industry standards database combining traditional exact matching
    with AI-powered semantic validation for comprehensive coverage.
    """
    
    def __init__(self, use_ai: bool = True):
        """Initialize hybrid industry standards."""
        self.use_ai = use_ai and AI_AVAILABLE
        self.ai_standards = None
        
        if self.use_ai:
            try:
                self.ai_standards = get_ai_industry_standards()
                logger.info("AI-enhanced industry standards enabled")
            except Exception as e:
                logger.warning(f"Failed to load AI standards: {e}")
                self.use_ai = False
        
        # Load traditional standards as fallback
        self.job_titles = self._load_standard_job_titles()
        self.companies = self._load_known_companies()
        self.skills = self._load_standard_skills()
        self.locations = self._load_standard_locations()
        
        logger.info(
            f"Loaded {len(self.job_titles)} job titles, "
            f"{len(self.companies)} companies, {len(self.skills)} skills, "
            f"{len(self.locations)} locations (AI: {self.use_ai})"
        )
        
    def _load_standard_job_titles(self) -> Set[str]:
        """Load standard job titles from various sources."""
        return {
            # Software Engineering
            'software engineer', 'senior software engineer',
            'junior software engineer',
            'software developer', 'senior software developer',
            'junior software developer',
            'full stack developer', 'frontend developer', 'backend developer',
            'web developer', 'mobile developer', 'ios developer',
            'android developer',
            'devops engineer', 'site reliability engineer',
            'platform engineer',
            'software architect', 'technical lead', 'engineering manager',
            
            # Data & Analytics
            'data scientist', 'senior data scientist', 'data analyst',
            'data engineer',
            'machine learning engineer', 'ai engineer', 'research scientist',
            'business analyst', 'business intelligence analyst',
            'data architect',
            'sales analyst', 'marketing analyst', 'financial analyst',
            'operations analyst', 'systems analyst', 'research analyst',
            'reporting analyst', 'performance analyst', 'insights analyst',
            
            # Product & Design
            'product manager', 'senior product manager', 'product owner',
            'ux designer', 'ui designer', 'ux/ui designer', 'product designer',
            'graphic designer', 'web designer', 'interaction designer',
            
            # Management & Leadership
            'engineering manager', 'technical manager', 'team lead',
            'tech lead',
            'director of engineering', 'vp of engineering', 'cto',
            'head of engineering',
            'project manager', 'program manager', 'scrum master',
            
            # Quality & Testing
            'qa engineer', 'test engineer', 'automation engineer', 'sdet',
            'quality assurance analyst', 'test automation engineer',
            
            # Security & Infrastructure
            'security engineer', 'cybersecurity analyst',
            'information security analyst',
            'network engineer', 'systems administrator', 'cloud engineer',
            'infrastructure engineer', 'database administrator'
        }
    
    def _load_known_companies(self) -> Set[str]:
        """Load known technology companies."""
        return {
            # Big Tech
            'google', 'microsoft', 'amazon', 'apple', 'meta', 'facebook',
            'netflix', 'tesla', 'nvidia', 'intel', 'amd', 'qualcomm',
            
            # Canadian Tech
            'shopify', 'blackberry', 'corel', 'opentext',
            'constellation software',
            'cgi', 'manulife', 'rbc', 'td bank', 'scotiabank', 'bmo',
            
            # Startups & Scale-ups
            'stripe', 'airbnb', 'uber', 'lyft', 'doordash', 'instacart',
            'zoom', 'slack', 'atlassian', 'datadog', 'snowflake',
            
            # Consulting & Services
            'accenture', 'deloitte', 'pwc', 'kpmg', 'ey', 'mckinsey',
            'ibm', 'cognizant', 'infosys', 'tcs', 'wipro', 'capgemini'
        }
    
    def _load_standard_skills(self) -> Set[str]:
        """Load standard technical skills."""
        return {
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#',
            'go', 'rust', 'kotlin', 'swift',
            'php', 'ruby', 'scala', 'r', 'perl', 'objective-c',
            'matlab', 'fortran', 'cobol', 'assembly',
            'groovy', 'dart', 'elixir', 'clojure', 'haskell', 'lua',
            'erlang', 'f#', 'visual basic',
            'powershell', 'shell', 'bash', 'pl/sql', 'abap', 'sas',
            'vba', 'delphi', 'prolog', 'lisp',
            
            # Web Technologies
            'react', 'angular', 'vue', 'node.js', 'express', 'django',
            'flask', 'spring', 'asp.net',
            'laravel', 'rails', 'svelte', 'ember', 'backbone',
            'next.js', 'nuxt.js', 'gatsby', 'meteor',
            'bootstrap', 'material-ui', 'tailwind', 'foundation',
            'jquery', 'webassembly', 'three.js',
            'd3.js', 'redux', 'mobx', 'rxjs', 'graphql', 'apollo',
            'rest', 'soap', 'json', 'xml',
            'html', 'css', 'sass', 'less', 'stylus',
            
            # Databases
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'cassandra', 'dynamodb',
            'sqlite', 'oracle', 'sql server', 'db2', 'sybase',
            'informix', 'firebird', 'couchdb',
            'arangodb', 'neo4j', 'influxdb', 'hbase', 'memcached',
            'bigquery', 'redshift', 'snowflake',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'gitlab', 
            'github actions', 'ansible', 'chef', 'puppet', 'circleci', 'travis', 'teamcity', 'bamboo',
            'prometheus', 'grafana', 'datadog', 'new relic', 'splunk', 'elk', 'nginx', 'helm',
            
            # Data & ML
            'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'spark', 'hadoop', 'kafka', 
            'airflow', 'dbt', 'xgboost', 'lightgbm', 'catboost', 'mxnet', 'caffe', 'theano', 'keras', 
            'nltk', 'spacy', 'gensim', 'opencv', 'dlib', 'statsmodels', 'plotly', 'seaborn', 'matplotlib',
            
            # Tools & Frameworks
            'git', 'jira', 'confluence', 'slack', 'figma', 'sketch', 'microsoft teams', 'zoom', 
            'trello', 'asana', 'monday', 'notion', 'airtable', 'miro', 'lucidchart', 'draw.io', 
            'tableau', 'power bi', 'qlik', 'looker', 'superset', 'metabase'
        }
    
    def _load_standard_locations(self) -> Set[str]:
        """Load standard location formats."""
        return {
            # Canadian Cities
            'toronto, on', 'vancouver, bc', 'montreal, qc', 'calgary, ab',
            'ottawa, on', 'edmonton, ab', 'winnipeg, mb', 'quebec city, qc',
            'hamilton, on', 'kitchener, on', 'london, on', 'halifax, ns',
            
            # US Cities
            'new york, ny', 'san francisco, ca', 'seattle, wa', 'austin, tx',
            'boston, ma', 'chicago, il', 'los angeles, ca', 'denver, co',
            
            # Remote Options
            'remote', 'remote - canada', 'remote - north america',
            'hybrid', 'work from home', 'telecommute'
        }

    def is_valid_job_title(self, title: str, context: str = "") -> bool:
        """Check if a job title is valid using hybrid approach."""
        # First, try exact match (fast)
        if title.lower() in self.job_titles:
            return True
        
        # Then try AI validation if available
        if self.use_ai and self.ai_standards:
            result = self.ai_standards.validate_job_title(title, context)
            return result.is_valid
        
        # Fallback to partial matching
        return self._partial_match_job_title(title) is not None

    def is_valid_company(self, company: str, context: str = "") -> bool:
        """Check if a company is valid using hybrid approach."""
        # First, try exact match (fast)
        if company.lower() in self.companies:
            return True
        
        # Then try AI validation if available
        if self.use_ai and self.ai_standards:
            result = self.ai_standards.validate_company(company, context)
            return result.is_valid
        
        # Fallback to partial matching
        return self._partial_match_company(company) is not None

    def is_valid_skill(self, skill: str, context: str = "") -> bool:
        """Check if a skill is valid using hybrid approach."""
        # First, try exact match (fast)
        if skill.lower() in self.skills:
            return True
        
        # Then try AI validation if available
        if self.use_ai and self.ai_standards:
            result = self.ai_standards.validate_skill(skill, context)
            return result.is_valid
        
        # Fallback to partial matching
        return self._partial_match_skill(skill) is not None

    def is_valid_location(self, location: str) -> bool:
        """Check if a location is valid."""
        return location.lower() in self.locations

    def validate_with_confidence(self, item_type: str, value: str, 
                                context: str = "") -> dict:
        """
        Validate with confidence scores and detailed results.
        
        Args:
            item_type: 'job_title', 'skill', 'company', or 'location'
            value: The value to validate
            context: Additional context for AI validation
            
        Returns:
            Dict with validation results and confidence scores
        """
        result = {
            'value': value,
            'is_valid': False,
            'confidence': 0.0,
            'method': 'exact_match',
            'matched_standard': None,
            'ai_result': None
        }
        
        # Get the appropriate validation sets
        if item_type == 'job_title':
            standards_set = self.job_titles
            ai_validator = (self.ai_standards.validate_job_title 
                           if self.ai_standards else None)
            partial_matcher = self._partial_match_job_title
        elif item_type == 'skill':
            standards_set = self.skills
            ai_validator = (self.ai_standards.validate_skill 
                           if self.ai_standards else None)
            partial_matcher = self._partial_match_skill
        elif item_type == 'company':
            standards_set = self.companies
            ai_validator = (self.ai_standards.validate_company 
                           if self.ai_standards else None)
            partial_matcher = self._partial_match_company
        elif item_type == 'location':
            standards_set = self.locations
            ai_validator = None
            partial_matcher = None
        else:
            return result
        
        clean_value = value.lower().strip()
        
        # 1. Try exact match first (highest confidence)
        if clean_value in standards_set:
            result.update({
                'is_valid': True,
                'confidence': 1.0,
                'method': 'exact_match',
                'matched_standard': clean_value
            })
            return result
        
        # 2. Try AI validation if available
        if self.use_ai and ai_validator:
            try:
                ai_result = ai_validator(value, context)
                result['ai_result'] = ai_result
                
                if ai_result.is_valid:
                    result.update({
                        'is_valid': True,
                        'confidence': ai_result.confidence,
                        'method': 'ai_semantic',
                        'matched_standard': ai_result.matched_standard
                    })
                    return result
            except Exception as e:
                logger.error(f"AI validation error for {item_type} "
                           f"'{value}': {e}")
        
        # 3. Try partial matching as fallback
        if partial_matcher:
            partial_result = partial_matcher(value)
            if partial_result:
                match, similarity = partial_result
                result.update({
                    'is_valid': True,
                    'confidence': similarity,
                    'method': 'partial_match',
                    'matched_standard': match
                })
                return result
        
        return result
    
    def find_partial_job_title_match(self, title: str, 
                                   min_similarity: float = 0.6) -> Optional[Tuple[str, str, float]]:
        """
        Find partial/fuzzy match for job title.
        
        Args:
            title: The job title to match
            min_similarity: Minimum similarity score (0.0-1.0)
            
        Returns:
            Tuple of (original_title, matched_standard, similarity_score) or None
        """
        if not title:
            return None
            
        title_lower = title.lower().strip()
        best_match = None
        best_score = 0.0
        
        # First try exact match
        if title_lower in self.job_titles:
            return (title, title_lower, 1.0)
        
        # Try partial matches - check if any standard title is contained in the input
        for standard_title in self.job_titles:
            # Check if standard title words are in the input title
            standard_words = set(standard_title.split())
            title_words = set(title_lower.split())
            
            # Calculate word overlap
            overlap = len(standard_words.intersection(title_words))
            if overlap > 0:
                similarity = overlap / len(standard_words)
                if similarity >= min_similarity and similarity > best_score:
                    best_match = standard_title
                    best_score = similarity
        
        # Also try fuzzy string matching for typos
        if not best_match:
            for standard_title in self.job_titles:
                similarity = SequenceMatcher(None, title_lower, standard_title).ratio()
                if similarity >= min_similarity and similarity > best_score:
                    best_match = standard_title
                    best_score = similarity
        
        if best_match:
            return (title, best_match, best_score)
        return None
    
    def find_partial_skill_matches(self, text: str, 
                                 min_similarity: float = 0.8) -> List[Tuple[str, float]]:
        """
        Find skills mentioned in text with partial matching.
        
        Args:
            text: Text to search for skills
            min_similarity: Minimum similarity score
            
        Returns:
            List of (skill, similarity_score) tuples
        """
        found_skills = []
        text_lower = text.lower()
        
        for skill in self.skills:
            if skill in text_lower:
                found_skills.append((skill, 1.0))
            else:
                # Check for partial matches
                for word in text_lower.split():
                    similarity = SequenceMatcher(None, word, skill).ratio()
                    if similarity >= min_similarity:
                        found_skills.append((skill, similarity))
                        break
        
        # Remove duplicates and sort by similarity
        unique_skills = {}
        for skill, score in found_skills:
            if skill not in unique_skills or score > unique_skills[skill]:
                unique_skills[skill] = score
        
        return sorted(unique_skills.items(), key=lambda x: x[1], reverse=True)
    
    def get_job_title_keywords(self) -> Set[str]:
        """Get common job title keywords for partial matching."""
        keywords = set()
        for title in self.job_titles:
            keywords.update(title.split())
        return keywords

    def get_stats(self) -> dict:
        """Get statistics about the standards database."""
        return {
            'job_titles_count': len(self.job_titles),
            'companies_count': len(self.companies),
            'skills_count': len(self.skills),
            'locations_count': len(self.locations)
        }

