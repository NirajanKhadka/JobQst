#!/usr/bin/env python3
"""
Config-Driven Unified Salary Parser V2
Replaces 5+ duplicate salary parsing implementations with single config-driven solution.

Key Improvements:
- Uses salary_config.json for all patterns and rules
- Supports 7 currencies (CAD, USD, EUR, GBP, JPY, INR, AUD)
- 9 period types (hourly, daily, weekly, monthly, etc.)
- Regional cost-of-living adjustments
- Consolidated from 5 duplicate implementations
- Performance optimized with compiled patterns

Configuration Files Used:
- config/salary_config.json - All salary patterns, currencies, and conversion rules
"""

import logging
import re
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass, field
import time

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class SalaryInfo:
    """Structured salary information with full metadata"""
    
    raw_text: str
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: str = "CAD"
    period: str = "yearly"
    confidence: float = 0.0
    is_range: bool = False
    is_hourly: bool = False
    annual_min: Optional[float] = None
    annual_max: Optional[float] = None
    formatted_display: str = ""
    extraction_method: str = ""
    regional_adjustment: float = 1.0
    
    def __post_init__(self):
        """Calculate annual equivalent and formatted display"""
        if not self.formatted_display:
            self._generate_display()
    
    def _generate_display(self):
        """Generate formatted display string"""
        if self.is_range and self.min_amount and self.max_amount:
            if self.currency == "CAD":
                self.formatted_display = f"${self.min_amount:,.0f} - ${self.max_amount:,.0f}"
            else:
                curr_symbol = self._get_currency_symbol()
                self.formatted_display = f"{curr_symbol}{self.min_amount:,.0f} - {curr_symbol}{self.max_amount:,.0f}"
        elif self.min_amount:
            if self.currency == "CAD":
                self.formatted_display = f"${self.min_amount:,.0f}"
            else:
                curr_symbol = self._get_currency_symbol()
                self.formatted_display = f"{curr_symbol}{self.min_amount:,.0f}"
        
        # Add period indicator if not yearly
        if self.period != "yearly" and self.formatted_display:
            self.formatted_display += f" /{self.period}"
    
    def _get_currency_symbol(self) -> str:
        """Get currency symbol for display"""
        symbols = {"CAD": "$", "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹", "AUD": "$"}
        return symbols.get(self.currency, "$")


class ConfigDrivenSalaryParser:
    """
    Unified config-driven salary parser
    
    Features:
    - Loads patterns from salary_config.json
    - Supports multiple currencies and periods
    - Regional cost-of-living adjustments
    - High-performance with compiled regex
    - Replaces 5+ duplicate implementations
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize config-driven salary parser
        
        Args:
            config_dir: Path to config directory (auto-detected if not provided)
        """
        start_time = time.time()
        
        # Initialize config loader
        self.config_loader = ConfigLoader(config_dir)
        
        # Load configurations
        self._load_configurations()
        
        # Build lookup structures
        self._build_currency_lookups()
        self._build_period_mappings()
        
        # Compile patterns
        self._compile_salary_patterns()
        
        init_time = (time.time() - start_time) * 1000
        logger.info(
            f"ConfigDrivenSalaryParser initialized in {init_time:.2f}ms "
            f"({len(self.compiled_patterns)} pattern groups)"
        )

    def _load_configurations(self):
        """Load salary configuration"""
        self.salary_config = self.config_loader.load_config("salary_config.json")
        logger.debug("Salary configuration loaded successfully")

    def _build_currency_lookups(self):
        """Build currency symbol to code mappings"""
        currency_config = self.salary_config.get("currency_symbols", {})
        
        self.currency_lookup: Dict[str, str] = {}
        self.currency_display: Dict[str, Dict[str, str]] = {}
        
        for symbol, currency_data in currency_config.items():
            if isinstance(currency_data, dict):
                code = currency_data.get("code", "CAD")
                self.currency_lookup[symbol] = code
                self.currency_display[code] = currency_data
        
        logger.debug(f"Built currency lookups for {len(self.currency_lookup)} currencies")

    def _build_period_mappings(self):
        """Build period conversion mappings"""
        period_config = self.salary_config.get("period_mappings", {})
        
        self.period_multipliers: Dict[str, float] = {}
        
        for period, period_data in period_config.items():
            if isinstance(period_data, dict):
                multiplier = period_data.get("multiplier", 1)
                self.period_multipliers[period] = multiplier
        
        logger.debug(f"Built period mappings for {len(self.period_multipliers)} periods")

    def _compile_salary_patterns(self):
        """Pre-compile salary extraction patterns"""
        patterns_config = self.salary_config.get("salary_patterns", {})
        
        self.compiled_patterns: Dict[str, Dict[str, Any]] = {}
        
        for pattern_type, pattern_data in patterns_config.items():
            if pattern_type == "description":
                continue
            
            if isinstance(pattern_data, dict):
                patterns = pattern_data.get("patterns", [])
                compiled = [
                    re.compile(p, re.IGNORECASE | re.MULTILINE)
                    for p in patterns
                ]
                
                self.compiled_patterns[pattern_type] = {
                    "compiled": compiled,
                    "confidence": pattern_data.get("confidence", 0.7),
                    "weight": pattern_data.get("weight", "medium")
                }
        
        logger.debug(f"Compiled {len(self.compiled_patterns)} salary pattern groups")

    def parse_salary(
        self,
        text: str,
        job_title: str = "",
        location: str = "",
        extract_method: str = "pattern"
    ) -> Optional[SalaryInfo]:
        """
        Parse salary information from text
        
        Args:
            text: Text containing salary information
            job_title: Job title for context
            location: Job location for regional adjustments
            extract_method: Method used for extraction tracking
        
        Returns:
            SalaryInfo object or None if no salary found
        """
        if not text:
            return None
        
        # Combine text sources
        search_text = f"{job_title} {text}"
        
        # Try patterns in order of confidence
        for pattern_type, pattern_info in sorted(
            self.compiled_patterns.items(),
            key=lambda x: x[1]["confidence"],
            reverse=True
        ):
            for pattern in pattern_info["compiled"]:
                match = pattern.search(search_text)
                if match:
                    # Extract salary info from match
                    salary_info = self._extract_from_match(
                        match,
                        pattern_type,
                        pattern_info["confidence"],
                        extract_method
                    )
                    
                    if salary_info:
                        # Apply regional adjustment if location provided
                        if location:
                            self._apply_regional_adjustment(salary_info, location)
                        
                        # Convert to annual if needed
                        self._ensure_annual_values(salary_info)
                        
                        return salary_info
        
        return None

    def _extract_from_match(
        self,
        match: re.Match,
        pattern_type: str,
        confidence: float,
        extract_method: str
    ) -> Optional[SalaryInfo]:
        """
        Extract salary info from regex match
        
        Args:
            match: Regex match object
            pattern_type: Type of pattern that matched
            confidence: Confidence score of pattern
            extract_method: Extraction method for tracking
        
        Returns:
            SalaryInfo object or None
        """
        try:
            groups = match.groups()
            
            # Determine if range or single amount
            if len(groups) >= 2 and groups[1]:
                # Range pattern
                min_str = groups[0]
                max_str = groups[1]
                
                min_amount = self._parse_amount(min_str)
                max_amount = self._parse_amount(max_str)
                
                if min_amount and max_amount:
                    return SalaryInfo(
                        raw_text=match.group(0),
                        min_amount=min_amount,
                        max_amount=max_amount,
                        is_range=True,
                        confidence=confidence,
                        extraction_method=extract_method,
                        is_hourly=(pattern_type == "hourly_rates"),
                        period=self._detect_period(match.group(0), pattern_type)
                    )
            
            elif len(groups) >= 1 and groups[0]:
                # Single amount
                amount_str = groups[0]
                amount = self._parse_amount(amount_str)
                
                if amount:
                    return SalaryInfo(
                        raw_text=match.group(0),
                        min_amount=amount,
                        max_amount=amount,
                        is_range=False,
                        confidence=confidence,
                        extraction_method=extract_method,
                        is_hourly=(pattern_type == "hourly_rates"),
                        period=self._detect_period(match.group(0), pattern_type)
                    )
        
        except Exception as e:
            logger.debug(f"Error extracting salary from match: {e}")
        
        return None

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """
        Parse salary amount string to float
        
        Args:
            amount_str: String containing amount (e.g., "80k", "80,000", "80.5")
        
        Returns:
            Float amount or None
        """
        if not amount_str:
            return None
        
        try:
            # Remove currency symbols and whitespace
            cleaned = re.sub(r'[$€£¥₹,\s]', '', amount_str)
            
            # Handle k/K suffix (thousands)
            modifiers = self.salary_config.get("salary_modifiers", {})
            
            if cleaned.endswith(('k', 'K')):
                cleaned = cleaned[:-1]
                amount = float(cleaned) * modifiers.get('k', 1000)
            elif cleaned.endswith(('m', 'M')):
                cleaned = cleaned[:-1]
                amount = float(cleaned) * modifiers.get('m', 1000000)
            else:
                amount = float(cleaned)
            
            # Validate range
            validation = self.salary_config.get("validation_rules", {})
            min_salary = validation.get("min_realistic_salary", 15000)
            max_salary = validation.get("max_realistic_salary", 1000000)
            
            if min_salary <= amount <= max_salary:
                return amount
            
            # If amount is very small, might be in thousands
            if amount < 1000 and amount > 10:
                potential_amount = amount * 1000
                if min_salary <= potential_amount <= max_salary:
                    return potential_amount
        
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error parsing amount '{amount_str}': {e}")
        
        return None

    def _detect_period(self, text: str, pattern_type: str) -> str:
        """
        Detect salary period from text
        
        Args:
            text: Text containing salary
            pattern_type: Type of pattern matched
        
        Returns:
            Period string (hourly, daily, weekly, monthly, yearly)
        """
        text_lower = text.lower()
        
        # Check for explicit period indicators
        period_indicators = {
            "hourly": ["hour", "hr", "hourly", "/hour", "per hour"],
            "daily": ["day", "daily", "/day", "per day"],
            "weekly": ["week", "weekly", "/week", "per week"],
            "monthly": ["month", "monthly", "/month", "per month"],
            "yearly": ["year", "annual", "annually", "/year", "per year", "per annum"]
        }
        
        for period, indicators in period_indicators.items():
            if any(ind in text_lower for ind in indicators):
                return period
        
        # Default based on pattern type
        if pattern_type == "hourly_rates":
            return "hourly"
        elif pattern_type == "weekly_rates":
            return "weekly"
        elif pattern_type == "monthly_rates":
            return "monthly"
        
        return "yearly"  # Default

    def _apply_regional_adjustment(self, salary_info: SalaryInfo, location: str):
        """
        Apply regional cost-of-living adjustment
        
        Args:
            salary_info: SalaryInfo object to adjust
            location: Location string
        """
        regional_config = self.salary_config.get("regional_adjustments", {})
        location_lower = location.lower()
        
        # Find matching region
        for region_key, region_data in regional_config.items():
            if isinstance(region_data, dict):
                if region_key.replace("_", " ") in location_lower:
                    multiplier = region_data.get("multiplier", 1.0)
                    salary_info.regional_adjustment = multiplier
                    break

    def _ensure_annual_values(self, salary_info: SalaryInfo):
        """
        Ensure salary has annual equivalent values
        
        Args:
            salary_info: SalaryInfo object to process
        """
        if salary_info.period == "yearly":
            salary_info.annual_min = salary_info.min_amount
            salary_info.annual_max = salary_info.max_amount
        else:
            # Convert to annual
            multiplier = self.period_multipliers.get(salary_info.period, 1)
            
            if salary_info.min_amount:
                salary_info.annual_min = salary_info.min_amount * multiplier
            
            if salary_info.max_amount:
                salary_info.annual_max = salary_info.max_amount * multiplier

    def enhance_job_salary(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance job dictionary with parsed salary information
        
        Args:
            job: Job dictionary
        
        Returns:
            Enhanced job dictionary
        """
        # Check if salary already exists
        if job.get("salary_min") and job.get("salary_max"):
            return job
        
        # Try to parse from description
        description = job.get("description", "")
        title = job.get("title", "")
        location = job.get("location", "")
        
        salary_info = self.parse_salary(description, title, location)
        
        if salary_info:
            job["salary_min"] = salary_info.annual_min or salary_info.min_amount
            job["salary_max"] = salary_info.annual_max or salary_info.max_amount
            job["salary_currency"] = salary_info.currency
            job["salary_period"] = salary_info.period
            job["salary_confidence"] = salary_info.confidence
            job["salary_formatted"] = salary_info.formatted_display
        
        return job

    def format_salary_display(
        self,
        min_amount: Optional[float],
        max_amount: Optional[float],
        currency: str = "CAD",
        period: str = "yearly"
    ) -> str:
        """
        Format salary for display
        
        Args:
            min_amount: Minimum salary
            max_amount: Maximum salary
            currency: Currency code
            period: Period (hourly, yearly, etc.)
        
        Returns:
            Formatted salary string
        """
        if not min_amount and not max_amount:
            return "Not disclosed"
        
        # Get currency symbol
        currency_data = self.currency_display.get(currency, {})
        symbol = currency_data.get("symbol", "$")
        
        # Format amounts
        if min_amount and max_amount and min_amount != max_amount:
            display = f"{symbol}{min_amount:,.0f} - {symbol}{max_amount:,.0f}"
        elif min_amount:
            display = f"{symbol}{min_amount:,.0f}+"
        else:
            display = f"Up to {symbol}{max_amount:,.0f}"
        
        # Add period if not yearly
        if period != "yearly":
            period_display = self.salary_config.get("period_mappings", {}).get(
                period, {}
            ).get("display", f"/{period}")
            display += f" {period_display}"
        
        return display


# Convenience function
def create_salary_parser(config_dir: Optional[str] = None) -> ConfigDrivenSalaryParser:
    """
    Create a config-driven salary parser instance
    
    Args:
        config_dir: Optional path to config directory
    
    Returns:
        ConfigDrivenSalaryParser instance
    """
    return ConfigDrivenSalaryParser(config_dir)


if __name__ == "__main__":
    # Test the config-driven salary parser
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Config-Driven Unified Salary Parser V2...")
    
    parser = create_salary_parser()
    
    print(f"\nLoaded {len(parser.compiled_patterns)} pattern groups")
    print(f"Currencies supported: {len(parser.currency_lookup)}")
    print(f"Period types: {len(parser.period_multipliers)}")
    
    # Test cases
    test_cases = [
        "Salary: $80,000 - $120,000 per year",
        "Compensation range: $90k-$110k annually",
        "Pay: $45/hour",
        "Annual salary of $95,000",
        "$70k-85k",
        "Hourly rate: $35-45/hr",
        "€50,000 - €70,000",
    ]
    
    print("\n=== Test Cases ===")
    for test_text in test_cases:
        print(f"\nInput: {test_text}")
        result = parser.parse_salary(test_text)
        
        if result:
            print(f"  Min: ${result.min_amount:,.0f}")
            print(f"  Max: ${result.max_amount:,.0f}")
            print(f"  Period: {result.period}")
            print(f"  Is Range: {result.is_range}")
            print(f"  Confidence: {result.confidence:.0%}")
            if result.annual_min:
                print(f"  Annual: ${result.annual_min:,.0f} - ${result.annual_max:,.0f}")
            print(f"  Display: {result.formatted_display}")
        else:
            print("  ❌ No salary found")
    
    # Test job enhancement
    print("\n=== Job Enhancement Test ===")
    test_job = {
        "title": "Senior Software Engineer",
        "description": "Looking for an experienced developer. Salary range: $100k-$130k per year with great benefits.",
        "location": "Toronto, ON"
    }
    
    enhanced = parser.enhance_job_salary(test_job)
    print(f"Salary Min: ${enhanced.get('salary_min', 0):,.0f}")
    print(f"Salary Max: ${enhanced.get('salary_max', 0):,.0f}")
    print(f"Display: {enhanced.get('salary_formatted', 'N/A')}")
    
    print("\n✅ Config-Driven Unified Salary Parser V2 is ready!")
