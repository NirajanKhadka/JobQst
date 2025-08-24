"""
Enhanced salary parsing utilities for JobLens Dashboard
Extracts and standardizes salary information from job descriptions
"""
import re
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SalaryInfo:
    """Structured salary information"""
    raw_text: str
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: str = "CAD"
    period: str = "yearly"
    confidence: float = 0.0
    is_range: bool = False
    formatted_display: str = ""


class SalaryParser:
    """Enhanced salary parser for dashboard display"""
    
    def __init__(self):
        self.salary_patterns = self._init_salary_patterns()
        self.currency_symbols = {'$': 'CAD', '€': 'EUR', '£': 'GBP'}
        
    def _init_salary_patterns(self) -> Dict[str, list]:
        """Initialize salary extraction patterns by confidence level"""
        return {
            'very_high': [
                # Explicit salary/compensation labels with ranges
                (r'(?i)(?:salary|compensation|pay)[:\s]*\$?([\d,]+(?:\.\d{2})?)'
                 r'\s*(?:k|,000)?\s*[-–]\s*\$?([\d,]+(?:\.\d{2})?)'
                 r'\s*(?:k|,000)?'),
                (r'(?i)annual\s+(?:salary|compensation)[:\s]*\$?'
                 r'([\d,]+(?:\.\d{2})?)\s*(?:k|,000)?\s*[-–]\s*\$?'
                 r'([\d,]+(?:\.\d{2})?)\s*(?:k|,000)?'),
            ],
            'high': [
                # Standard salary ranges
                (r'\$?([\d,]+(?:\.\d{2})?)\s*(?:k|,000)?\s*[-–]\s*\$?'
                 r'([\d,]+(?:\.\d{2})?)\s*(?:k|,000)?\s*'
                 r'(?:per\s*year|annually|/year)?'),
                (r'\$?([\d,]+(?:\.\d{2})?)\s*(?:k|,000)?\s*to\s*\$?'
                 r'([\d,]+(?:\.\d{2})?)\s*(?:k|,000)?\s*'
                 r'(?:per\s*year|annually|/year)?'),
            ],
            'medium': [
                # Single salary amounts with clear indicators
                (r'(?i)(?:salary|compensation|pay)[:\s]*\$?'
                 r'([\d,]+(?:\.\d{2})?)\s*(?:k|,000)?\s*'
                 r'(?:per\s*year|annually|/year)?'),
                (r'\$?([\d,]+(?:\.\d{2})?)\s*(?:k|,000)?\s*'
                 r'(?:per\s*year|annually|/year)'),
            ],
            'low': [
                # Hourly rates
                r'\$?([\d,]+(?:\.\d{2})?)\s*(?:per\s*hour|/hour|hourly)',
                # Less specific patterns
                r'\$[\d,]+(?:\.\d{2})?(?:k|,000)?',
            ]
        }
    
    def parse_salary(self, text: str,
                     job_title: str = "") -> Optional[SalaryInfo]:
        """
        Parse salary information from job text
        
        Args:
            text: Job description or salary text
            job_title: Job title for context
            
        Returns:
            SalaryInfo object or None if no salary found
        """
        if not text:
            return None
            
        # Combine text sources
        search_text = f"{job_title} {text}".lower()
        
        # Try patterns in order of confidence
        for confidence_level, patterns in self.salary_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    salary_info = self._process_match(
                        match, text, confidence_level
                    )
                    if salary_info and self._validate_salary(salary_info):
                        return salary_info
        
        return None
    
    def _process_match(self, match, original_text: str,
                       confidence_level: str) -> Optional[SalaryInfo]:
        """Process regex match into SalaryInfo"""
        try:
            groups = match.groups()
            
            if len(groups) >= 2 and groups[1]:
                # Range pattern
                min_val = self._parse_amount(groups[0])
                max_val = self._parse_amount(groups[1])
                
                if min_val and max_val:
                    return SalaryInfo(
                        raw_text=match.group(0),
                        min_amount=min_val,
                        max_amount=max_val,
                        is_range=True,
                        confidence=self._get_confidence_score(
                            confidence_level
                        ),
                        formatted_display=self._format_range(min_val, max_val)
                    )
            
            elif len(groups) >= 1:
                # Single amount
                amount = self._parse_amount(groups[0])
                if amount:
                    return SalaryInfo(
                        raw_text=match.group(0),
                        min_amount=amount,
                        max_amount=amount,
                        is_range=False,
                        confidence=self._get_confidence_score(
                            confidence_level
                        ),
                        formatted_display=self._format_single(amount)
                    )
                    
        except (ValueError, IndexError) as e:
            logger.debug(f"Error processing salary match: {e}")
            
        return None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse salary amount string to float"""
        if not amount_str:
            return None
            
        # Clean the string
        clean_amount = re.sub(r'[^\d.,k]', '', amount_str.lower())
        
        try:
            # Handle 'k' suffix (thousands)
            if 'k' in clean_amount:
                base_amount = float(
                    clean_amount.replace('k', '').replace(',', '')
                )
                return base_amount * 1000
            
            # Handle comma-separated numbers
            return float(clean_amount.replace(',', ''))
            
        except ValueError:
            return None
    
    def _validate_salary(self, salary_info: SalaryInfo) -> bool:
        """Validate salary information makes sense"""
        if not salary_info.min_amount:
            return False
            
        # Check reasonable ranges for Canadian market
        min_reasonable = 20000   # $20k minimum
        max_reasonable = 500000  # $500k maximum
        
        if salary_info.min_amount < min_reasonable:
            return False
            
        if salary_info.max_amount and salary_info.max_amount > max_reasonable:
            return False
            
        # Check range makes sense
        if (salary_info.is_range and salary_info.max_amount and
                salary_info.max_amount < salary_info.min_amount):
            return False
            
        return True
    
    def _get_confidence_score(self, confidence_level: str) -> float:
        """Convert confidence level to numeric score"""
        scores = {
            'very_high': 0.95,
            'high': 0.85,
            'medium': 0.70,
            'low': 0.50
        }
        return scores.get(confidence_level, 0.50)
    
    def _format_range(self, min_val: float, max_val: float) -> str:
        """Format salary range for display"""
        return f"${min_val:,.0f} - ${max_val:,.0f}"
    
    def _format_single(self, amount: float) -> str:
        """Format single salary amount for display"""
        return f"${amount:,.0f}"
    
    def enhance_job_salary_display(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance job data with better salary display
        
        Args:
            job_data: Job dictionary
            
        Returns:
            Enhanced job data with salary_display field
        """
        enhanced = job_data.copy()
        
        # Get existing salary field
        existing_salary = (job_data.get('salary') or 
                          job_data.get('salary_range') or 
                          job_data.get('compensation', ''))
        
        # Parse from description if no existing salary
        description = job_data.get('description', '')
        title = job_data.get('title', '')
        
        search_text = f"{existing_salary} {description}"
        salary_info = self.parse_salary(search_text, title)
        
        if salary_info:
            enhanced.update({
                'salary_display': salary_info.formatted_display,
                'salary_min': salary_info.min_amount,
                'salary_max': salary_info.max_amount,
                'salary_confidence': salary_info.confidence,
                'salary_is_range': salary_info.is_range,
                'salary_raw': salary_info.raw_text
            })
        else:
            # Fallback to existing data or default
            enhanced.update({
                'salary_display': existing_salary or 'Not specified',
                'salary_min': None,
                'salary_max': None,
                'salary_confidence': 0.0,
                'salary_is_range': False,
                'salary_raw': existing_salary
            })
            
        return enhanced


def enhance_jobs_data_with_salary(jobs_data: list) -> list:
    """
    Enhance a list of jobs with better salary parsing
    
    Args:
        jobs_data: List of job dictionaries
        
    Returns:
        Enhanced list with salary_display fields
    """
    if not jobs_data:
        return jobs_data
        
    parser = SalaryParser()
    enhanced_jobs = []
    
    for job in jobs_data:
        try:
            enhanced_job = parser.enhance_job_salary_display(job)
            enhanced_jobs.append(enhanced_job)
        except Exception as e:
            logger.error(f"Error enhancing salary for job {job.get('id', 'unknown')}: {e}")
            enhanced_jobs.append(job)  # Keep original if enhancement fails
            
    return enhanced_jobs


def get_salary_statistics(jobs_data: list) -> Dict[str, Any]:
    """
    Calculate salary statistics from jobs data
    
    Args:
        jobs_data: List of job dictionaries
        
    Returns:
        Statistics dictionary
    """
    if not jobs_data:
        return {}
        
    salaries = []
    salary_jobs = 0
    
    for job in jobs_data:
        salary_min = job.get('salary_min')
        salary_max = job.get('salary_max')
        
        if salary_min:
            salaries.append(salary_min)
            salary_jobs += 1
            
        if salary_max and salary_max != salary_min:
            salaries.append(salary_max)
    
    if not salaries:
        return {
            'jobs_with_salary': 0,
            'jobs_with_salary_percent': 0,
            'avg_salary': None,
            'min_salary': None,
            'max_salary': None,
            'median_salary': None
        }
    
    salaries.sort()
    n = len(salaries)
    
    return {
        'jobs_with_salary': salary_jobs,
        'jobs_with_salary_percent': round((salary_jobs / len(jobs_data)) * 100, 1),
        'avg_salary': round(sum(salaries) / n, 0),
        'min_salary': min(salaries),
        'max_salary': max(salaries),
        'median_salary': salaries[n // 2] if n % 2 == 1 else (salaries[n//2-1] + salaries[n//2]) / 2
    }
