from typing import Dict
from .health_utils import check_disk_space as _check_disk_space


def check_disk(config: Dict) -> Dict:
    """Check available disk space using shared utilities."""
    result = _check_disk_space(config)
    return result.to_dict()


def check_disk_space(config: Dict) -> Dict:
    """Alias for check_disk to maintain backward compatibility."""
    result = _check_disk_space(config)
    return result.to_dict()

