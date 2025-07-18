from typing import Dict
from .health_utils import check_file_permissions as _check_file_permissions


def check_permissions(config: Dict) -> Dict:
    """Check file permissions using shared utilities."""
    result = _check_file_permissions(config)
    return result.to_dict()


def check_file_permissions(config: Dict) -> Dict:
    """Alias for check_permissions to maintain backward compatibility."""
    result = _check_file_permissions(config)
    return result.to_dict()
