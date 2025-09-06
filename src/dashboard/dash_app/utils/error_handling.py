"""
Error handling and validation utilities for the dashboard
"""
import logging
import traceback
from typing import Any, Dict, Union
from functools import wraps
import dash
from dash import html, dcc

logger = logging.getLogger(__name__)

def handle_callback_errors(func):
    """Decorator to handle errors in Dash callbacks"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in callback {func.__name__}: {e}")
            logger.error(traceback.format_exc())
            
            # Return appropriate error response based on expected output
            callback_context = dash.callback_context
            if callback_context.outputs_list:
                # Try to determine expected output type and return appropriate error
                outputs = callback_context.outputs_list
                if len(outputs) == 1:
                    return create_error_component(str(e))
                else:
                    # Multiple outputs - return tuple of error components
                    return tuple(create_error_component(str(e)) for _ in outputs)
            else:
                return create_error_component(str(e))
    
    return wrapper

def create_error_component(error_message: str, error_type: str = "error"):
    """Create a standardized error component"""
    color_map = {
        "error": "danger",
        "warning": "warning", 
        "info": "info",
        "success": "success"
    }
    
    return html.Div([
        html.I(className="fas fa-exclamation-triangle me-2"),
        html.Span(error_message)
    ], className=f"alert alert-{color_map.get(error_type, 'danger')} m-3")

def validate_job_data(data: Any) -> Dict[str, Any]:
    """Validate job data structure"""
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "summary": {}
    }
    
    try:
        if not data:
            validation_result["is_valid"] = False
            validation_result["errors"].append("No data provided")
            return validation_result
        
        if not isinstance(data, (list, dict)):
            validation_result["is_valid"] = False
            validation_result["errors"].append("Data must be a list or dictionary")
            return validation_result
        
        # Convert to list if single job
        jobs_list = data if isinstance(data, list) else [data]
        
        required_fields = ['id', 'title', 'company']
        
        valid_jobs = 0
        total_jobs = len(jobs_list)
        
        for i, job in enumerate(jobs_list):
            if not isinstance(job, dict):
                validation_result["errors"].append(f"Job {i+1}: Must be a dictionary")
                continue
            
            # Check required fields
            missing_required = [field for field in required_fields if field not in job]
            if missing_required:
                validation_result["errors"].append(f"Job {i+1}: Missing required fields: {', '.join(missing_required)}")
                continue
            
            # Check for empty required fields
            empty_required = [field for field in required_fields if not job.get(field)]
            if empty_required:
                validation_result["warnings"].append(f"Job {i+1}: Empty required fields: {', '.join(empty_required)}")
            
            # Validate specific field types
            if 'match_score' in job and job['match_score'] is not None:
                try:
                    score = float(job['match_score'])
                    if not 0 <= score <= 100:
                        validation_result["warnings"].append(f"Job {i+1}: Match score should be between 0-100")
                except (ValueError, TypeError):
                    validation_result["warnings"].append(f"Job {i+1}: Invalid match score format")
            
            valid_jobs += 1
        
        validation_result["summary"] = {
            "total_jobs": total_jobs,
            "valid_jobs": valid_jobs,
            "invalid_jobs": total_jobs - valid_jobs,
            "error_rate": (total_jobs - valid_jobs) / total_jobs if total_jobs > 0 else 0
        }
        
        if valid_jobs == 0:
            validation_result["is_valid"] = False
            validation_result["errors"].append("No valid jobs found")
        
    except Exception as e:
        validation_result["is_valid"] = False
        validation_result["errors"].append(f"Validation error: {str(e)}")
        logger.error(f"Error validating job data: {e}")
    
    return validation_result

def validate_filter_params(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Validate filter parameters"""
    validation_result = {
        "is_valid": True,
        "errors": [],
        "sanitized_filters": {}
    }
    
    try:
        if not isinstance(filters, dict):
            validation_result["is_valid"] = False
            validation_result["errors"].append("Filters must be a dictionary")
            return validation_result
        
        # Validate search term
        if 'search' in filters:
            search = filters['search']
            if search and len(str(search).strip()) > 100:
                validation_result["errors"].append("Search term too long (max 100 characters)")
            else:
                validation_result["sanitized_filters"]['search'] = str(search).strip() if search else ""
        
        # Validate numeric filters
        numeric_filters = ['min_match_score', 'max_match_score', 'min_salary', 'max_salary']
        for filter_name in numeric_filters:
            if filter_name in filters and filters[filter_name] is not None:
                try:
                    value = float(filters[filter_name])
                    validation_result["sanitized_filters"][filter_name] = value
                except (ValueError, TypeError):
                    validation_result["errors"].append(f"Invalid numeric value for {filter_name}")
        
        # Validate date filters
        date_filters = ['start_date', 'end_date', 'created_after', 'created_before']
        for filter_name in date_filters:
            if filter_name in filters and filters[filter_name]:
                # Add date validation if needed
                validation_result["sanitized_filters"][filter_name] = filters[filter_name]
        
        # Validate choice filters
        choice_filters = ['status', 'company', 'location']
        for filter_name in choice_filters:
            if filter_name in filters and filters[filter_name]:
                value = str(filters[filter_name]).strip()
                if len(value) > 50:
                    validation_result["errors"].append(f"{filter_name} value too long (max 50 characters)")
                else:
                    validation_result["sanitized_filters"][filter_name] = value
        
        if validation_result["errors"]:
            validation_result["is_valid"] = False
    
    except Exception as e:
        validation_result["is_valid"] = False
        validation_result["errors"].append(f"Filter validation error: {str(e)}")
        logger.error(f"Error validating filters: {e}")
    
    return validation_result

def sanitize_input(value: Any, input_type: str = "text", max_length: int = 100) -> str:
    """Sanitize user input"""
    try:
        if value is None:
            return ""
        
        # Convert to string
        sanitized = str(value).strip()
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Type-specific sanitization
        if input_type == "search":
            # Remove special characters that might break search
            import re
            sanitized = re.sub(r'[<>"\';]', '', sanitized)
        
        elif input_type == "filename":
            # Remove characters invalid for filenames
            import re
            sanitized = re.sub(r'[<>:"/\\|?*]', '_', sanitized)
        
        elif input_type == "sql":
            # Basic SQL injection prevention
            sanitized = sanitized.replace("'", "''").replace(";", "")
        
        return sanitized
        
    except Exception as e:
        logger.error(f"Error sanitizing input: {e}")
        return ""

def log_user_action(action: str, details: Dict[str, Any] = None, user_id: str = None):
    """Log user actions for audit trail"""
    try:
        log_entry = {
            "action": action,
            "user_id": user_id or "anonymous",
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord("", 0, "", 0, "", (), None)) if logger.handlers else "",
            "details": details or {}
        }
        
        logger.info(f"User Action: {action}", extra=log_entry)
        
    except Exception as e:
        logger.error(f"Error logging user action: {e}")

def create_loading_component(message: str = "Loading..."):
    """Create a loading component"""
    return html.Div([
        dcc.Loading(
            id="loading",
            children=[html.Div(message)],
            type="default",
        )
    ], className="text-center p-4")

def create_empty_state(message: str = "No data available", icon: str = "fas fa-inbox"):
    """Create an empty state component"""
    return html.Div([
        html.Div([
            html.I(className=f"{icon} fa-3x text-muted mb-3"),
            html.H5(message, className="text-muted"),
            html.P("Try adjusting your filters or refresh the data.", className="text-muted small")
        ], className="text-center")
    ], className="d-flex align-items-center justify-content-center", style={"min-height": "200px"})

def safe_divide(numerator: Union[int, float], denominator: Union[int, float], default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if division by zero"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default

def safe_percentage(part: Union[int, float], total: Union[int, float], decimals: int = 1) -> str:
    """Safely calculate percentage as string"""
    try:
        if total == 0:
            return "0.0%"
        percentage = (part / total) * 100
        return f"{percentage:.{decimals}f}%"
    except (TypeError, ValueError):
        return "N/A"

def format_error_message(error: Exception, user_friendly: bool = True) -> str:
    """Format error message for display"""
    if user_friendly:
        # Map common errors to user-friendly messages
        error_messages = {
            "ConnectionError": "Unable to connect to the database. Please check your connection.",
            "FileNotFoundError": "Required file not found. Please check your configuration.",
            "PermissionError": "Permission denied. Please check file permissions.",
            "ValueError": "Invalid data format. Please check your input.",
            "KeyError": "Missing required data field."
        }
        
        error_type = type(error).__name__
        return error_messages.get(error_type, "An unexpected error occurred. Please try again.")
    else:
        return str(error)
