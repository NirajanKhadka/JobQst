from typing import Dict
from .health_utils import check_browser_processes as _check_browser_processes


def check_browser(config: Dict) -> Dict:
    """Check for zombie browser processes using shared utilities."""
    result = _check_browser_processes(config)
    return result.to_dict()


def check_browser_processes(config: Dict) -> Dict:
    """Alias for check_browser to maintain backward compatibility."""
    result = _check_browser_processes(config)
    return result.to_dict()

