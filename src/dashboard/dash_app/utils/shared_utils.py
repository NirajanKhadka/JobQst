"""
Shared utility functions for dashboard enhancements.
Provides data formatting, error handling, and common helper functions.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Data Formatting Utilities
# ============================================================================

def format_currency(amount: Optional[Union[int, float]], currency: str = "CAD") -> str:
    """
    Format a number as currency.
    
    Args:
        amount: Amount to format
        currency: Currency code (default: CAD)
    
    Returns:
        Formatted currency string (e.g., "$75,000 CAD")
    """
    if amount is None:
        return "N/A"
    
    try:
        if currency == "CAD":
            return f"${amount:,.0f} CAD"
        elif currency == "USD":
            return f"${amount:,.0f} USD"
        else:
            return f"{amount:,.0f} {currency}"
    except (ValueError, TypeError):
        return "N/A"


def format_salary_range(min_salary: Optional[float], max_salary: Optional[float], 
                       currency: str = "CAD") -> str:
    """
    Format a salary range.
    
    Args:
        min_salary: Minimum salary
        max_salary: Maximum salary
        currency: Currency code
    
    Returns:
        Formatted salary range (e.g., "$60K - $80K CAD")
    """
    if min_salary is None and max_salary is None:
        return "Not specified"
    
    if min_salary is None:
        return f"Up to {format_currency(max_salary, currency)}"
    
    if max_salary is None:
        return f"From {format_currency(min_salary, currency)}"
    
    # Use K notation for cleaner display
    min_k = f"${min_salary/1000:.0f}K"
    max_k = f"${max_salary/1000:.0f}K"
    
    return f"{min_k} - {max_k} {currency}"


def format_percentage(value: Optional[float], decimals: int = 0) -> str:
    """
    Format a number as percentage.
    
    Args:
        value: Value to format (0-100)
        decimals: Number of decimal places
    
    Returns:
        Formatted percentage string (e.g., "75%")
    """
    if value is None:
        return "N/A"
    
    try:
        return f"{value:.{decimals}f}%"
    except (ValueError, TypeError):
        return "N/A"


def format_date(date: Optional[Union[datetime, str]], format_str: str = "%b %d, %Y") -> str:
    """
    Format a date object or string.
    
    Args:
        date: Date to format
        format_str: strftime format string
    
    Returns:
        Formatted date string
    """
    if date is None:
        return "N/A"
    
    try:
        if isinstance(date, str):
            # Try to parse common date formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    date = datetime.strptime(date, fmt)
                    break
                except ValueError:
                    continue
        
        if isinstance(date, datetime):
            return date.strftime(format_str)
        
        return str(date)
    except Exception as e:
        logger.warning(f"Error formatting date {date}: {e}")
        return "N/A"


def format_relative_time(date: Optional[Union[datetime, str]]) -> str:
    """
    Format a date as relative time (e.g., "2 days ago", "Just now").
    
    Args:
        date: Date to format
    
    Returns:
        Relative time string
    """
    if date is None:
        return "N/A"
    
    try:
        if isinstance(date, str):
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    date = datetime.strptime(date, fmt)
                    break
                except ValueError:
                    continue
        
        if not isinstance(date, datetime):
            return "N/A"
        
        now = datetime.now()
        diff = now - date
        
        if diff.days == 0:
            if diff.seconds < 60:
                return "Just now"
            elif diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = diff.days // 365
            return f"{years} year{'s' if years != 1 else ''} ago"
    
    except Exception as e:
        logger.warning(f"Error formatting relative time {date}: {e}")
        return "N/A"


def format_number(value: Optional[Union[int, float]], decimals: int = 0) -> str:
    """
    Format a number with thousand separators.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
    
    Returns:
        Formatted number string (e.g., "1,234")
    """
    if value is None:
        return "N/A"
    
    try:
        if decimals == 0:
            return f"{int(value):,}"
        else:
            return f"{value:,.{decimals}f}"
    except (ValueError, TypeError):
        return "N/A"


def truncate_text(text: Optional[str], max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if text is None:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


# ============================================================================
# Match Score Utilities
# ============================================================================

def get_match_score_color(score: Optional[float]) -> str:
    """
    Get color class for match score.
    
    Args:
        score: Match score (0-100)
    
    Returns:
        Color class name
    """
    if score is None:
        return "muted"
    
    if score >= 70:
        return "success"
    elif score >= 50:
        return "warning"
    else:
        return "danger"


def get_match_score_label(score: Optional[float]) -> str:
    """
    Get label for match score.
    
    Args:
        score: Match score (0-100)
    
    Returns:
        Label string
    """
    if score is None:
        return "Unknown"
    
    if score >= 90:
        return "Excellent Match"
    elif score >= 70:
        return "Good Match"
    elif score >= 50:
        return "Fair Match"
    else:
        return "Low Match"


def get_match_score_class(score: Optional[float]) -> str:
    """
    Get CSS class for match score card styling.
    
    Args:
        score: Match score (0-100)
    
    Returns:
        CSS class name
    """
    if score is None:
        return "match-low"
    
    if score >= 70:
        return "match-high"
    elif score >= 50:
        return "match-medium"
    else:
        return "match-low"


# ============================================================================
# Priority and Status Utilities
# ============================================================================

def get_priority_color(priority: str) -> str:
    """
    Get color for priority level.
    
    Args:
        priority: Priority level (high/medium/low/urgent)
    
    Returns:
        Color class name
    """
    priority_lower = priority.lower() if priority else ""
    
    if priority_lower in ["high", "urgent"]:
        return "danger"
    elif priority_lower == "medium":
        return "warning"
    else:
        return "info"


def get_status_color(status: str) -> str:
    """
    Get color for application status.
    
    Args:
        status: Application status
    
    Returns:
        Color class name
    """
    status_lower = status.lower() if status else ""
    
    status_colors = {
        "interested": "info",
        "applied": "primary",
        "interview": "warning",
        "offer": "success",
        "rejected": "danger",
        "accepted": "success",
        "declined": "secondary"
    }
    
    return status_colors.get(status_lower, "secondary")


def get_status_icon(status: str) -> str:
    """
    Get icon for application status.
    
    Args:
        status: Application status
    
    Returns:
        FontAwesome icon class
    """
    status_lower = status.lower() if status else ""
    
    status_icons = {
        "interested": "fas fa-star",
        "applied": "fas fa-paper-plane",
        "interview": "fas fa-comments",
        "offer": "fas fa-trophy",
        "rejected": "fas fa-times-circle",
        "accepted": "fas fa-check-circle",
        "declined": "fas fa-ban"
    }
    
    return status_icons.get(status_lower, "fas fa-circle")


# ============================================================================
# Error Handling Utilities
# ============================================================================

def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary.
    
    Args:
        dictionary: Dictionary to get value from
        key: Key to look up
        default: Default value if key not found
    
    Returns:
        Value or default
    """
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default


def safe_divide(numerator: Optional[float], denominator: Optional[float], 
                default: float = 0.0) -> float:
    """
    Safely divide two numbers.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division fails
    
    Returns:
        Result or default
    """
    try:
        if denominator is None or denominator == 0:
            return default
        if numerator is None:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def safe_percentage(part: Optional[float], total: Optional[float], 
                    decimals: int = 0) -> float:
    """
    Safely calculate percentage.
    
    Args:
        part: Part value
        total: Total value
        decimals: Number of decimal places
    
    Returns:
        Percentage (0-100)
    """
    result = safe_divide(part, total, 0.0) * 100
    return round(result, decimals)


def handle_error(error: Exception, context: str, default_return: Any = None) -> Any:
    """
    Handle an error with logging.
    
    Args:
        error: Exception that occurred
        context: Context description
        default_return: Default value to return
    
    Returns:
        Default return value
    """
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)
    return default_return


# ============================================================================
# List and Collection Utilities
# ============================================================================

def safe_list_get(lst: List, index: int, default: Any = None) -> Any:
    """
    Safely get an item from a list by index.
    
    Args:
        lst: List to get item from
        index: Index to access
        default: Default value if index out of range
    
    Returns:
        Item or default
    """
    try:
        return lst[index] if lst and 0 <= index < len(lst) else default
    except (TypeError, IndexError):
        return default


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Split a list into chunks.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deduplicate_list(lst: List, key: Optional[str] = None) -> List:
    """
    Remove duplicates from a list.
    
    Args:
        lst: List to deduplicate
        key: Optional key for dict items
    
    Returns:
        Deduplicated list
    """
    if not lst:
        return []
    
    if key is None:
        return list(dict.fromkeys(lst))
    
    seen = set()
    result = []
    for item in lst:
        item_key = item.get(key) if isinstance(item, dict) else item
        if item_key not in seen:
            seen.add(item_key)
            result.append(item)
    
    return result


# ============================================================================
# Validation Utilities
# ============================================================================

def is_valid_email(email: Optional[str]) -> bool:
    """
    Check if email is valid.
    
    Args:
        email: Email to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: Optional[str]) -> bool:
    """
    Check if URL is valid.
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False
    
    import re
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_value: Minimum value
        max_value: Maximum value
    
    Returns:
        Clamped value
    """
    return max(min_value, min(value, max_value))
