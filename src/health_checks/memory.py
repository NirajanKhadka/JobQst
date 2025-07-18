from typing import Dict
from .health_utils import check_memory_usage as _check_memory_usage


def check_memory(config: Dict) -> Dict:
    """Check system memory usage using shared utilities."""
    result = _check_memory_usage(config)
    return result.to_dict()


def check_memory_usage(config: Dict) -> Dict:
    """Alias for check_memory to maintain backward compatibility."""
    result = _check_memory_usage(config)
    return result.to_dict()
