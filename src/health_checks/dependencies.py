from typing import Dict
from .health_utils import check_dependencies as _check_dependencies


def check_dependencies(config: Dict) -> Dict:
    """Check critical Python dependencies using shared utilities."""
    result = _check_dependencies(config)
    return result.to_dict()

