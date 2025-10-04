"""
Tiered Company Validation System
Combines local database, domain validation, and web search for optimal speed/accuracy.
"""

from .enhanced_company_validator import validate_company_enhanced
from .domain_validator import validate_company_domain
from .web_search_validator import validate_company_bing
import logging

logger = logging.getLogger(__name__)


class TieredCompanyValidator:
    """Fast, comprehensive company validation using multiple methods."""

    def __init__(self, bing_api_key: str = None):
        self.bing_api_key = bing_api_key
        self.validation_cache = {}

    def validate_company_comprehensive(self, company: str) -> dict:
        """
        Comprehensive company validation using tiered approach:
        1. Local database (instant, 95% coverage)
        2. Domain validation (fast, additional verification)
        3. Web search (limited, for unknown companies)
        """
        if not company:
            return {"is_valid": False, "confidence": 0.0, "method": "empty_input"}

        # Check cache first
        if company in self.validation_cache:
            return self.validation_cache[company]

        # Tier 1: Local database validation (FASTEST)
        local_result = validate_company_enhanced(company)

        if local_result["confidence"] >= 0.8:
            # High confidence from local validation - we're done!
            result = {
                "is_valid": local_result["is_valid"],
                "confidence": local_result["confidence"],
                "primary_method": local_result["method"],
                "validation_tier": "local_database",
                "speed": "instant",
            }
            self.validation_cache[company] = result
            return result

        # Tier 2: Domain validation (FAST)
        domain_result = validate_company_domain(company)

        # Combine local + domain results
        combined_confidence = max(local_result["confidence"], domain_result["confidence"])

        if domain_result["is_valid"] and domain_result["confidence"] >= 0.7:
            # Good domain validation - combine with local
            result = {
                "is_valid": True,
                "confidence": min(combined_confidence + 0.1, 0.9),  # Boost for domain match
                "primary_method": f"{local_result['method']} + domain_check",
                "domain_found": domain_result.get("domain", ""),
                "validation_tier": "local_plus_domain",
                "speed": "fast",
            }
            self.validation_cache[company] = result
            return result

        # Tier 3: Web search (LIMITED) - only for completely unknown companies
        if (
            local_result["confidence"] < 0.6
            and domain_result["confidence"] < 0.6
            and self.bing_api_key
        ):

            web_result = validate_company_bing(company, self.bing_api_key)

            if web_result["confidence"] >= 0.7:
                result = {
                    "is_valid": web_result["is_valid"],
                    "confidence": web_result["confidence"],
                    "primary_method": "web_search",
                    "evidence": web_result.get("evidence", []),
                    "validation_tier": "web_search",
                    "speed": "moderate",
                }
                self.validation_cache[company] = result
                return result

        # Fallback: Use best available result
        if local_result["confidence"] >= domain_result["confidence"]:
            best_result = local_result
            tier = "local_fallback"
        else:
            best_result = domain_result
            tier = "domain_fallback"

        result = {
            "is_valid": best_result["is_valid"],
            "confidence": best_result["confidence"],
            "primary_method": best_result["method"],
            "validation_tier": tier,
            "speed": "fast",
        }

        self.validation_cache[company] = result
        return result

    def get_stats(self) -> dict:
        """Get validation statistics."""
        if not self.validation_cache:
            return {"total_validations": 0}

        methods = {}
        for result in self.validation_cache.values():
            tier = result.get("validation_tier", "unknown")
            methods[tier] = methods.get(tier, 0) + 1

        return {
            "total_validations": len(self.validation_cache),
            "cache_size": len(self.validation_cache),
            "method_breakdown": methods,
        }


# Integration with existing WebValidator
class EnhancedWebValidator:
    """Drop-in replacement for existing WebValidator with tiered validation."""

    def __init__(self, search_client=None, bing_api_key: str = None):
        self.tiered_validator = TieredCompanyValidator(bing_api_key)
        self.search_available = bing_api_key is not None

    def validate_company(self, company: str):
        """Validate company using tiered approach - compatible with existing interface."""
        result = self.tiered_validator.validate_company_comprehensive(company)

        # Convert to existing ValidationResult format
        from ..analysis.custom_extractor import ValidationResult

        return ValidationResult(
            is_valid=result["is_valid"],
            confidence=result["confidence"],
            validation_method=result["primary_method"],
            details=f"Tier: {result['validation_tier']}, Speed: {result['speed']}",
        )


# Convenience function
def validate_company_smart(company: str, bing_api_key: str = None) -> dict:
    """Smart company validation using optimal method for speed and accuracy."""
    validator = TieredCompanyValidator(bing_api_key)
    return validator.validate_company_comprehensive(company)
