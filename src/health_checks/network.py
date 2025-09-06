from typing import Dict
from .health_utils import check_network_connectivity as _check_network_connectivity


def check_network(config: Dict) -> Dict:
    """Check network connectivity using shared utilities."""
    result = _check_network_connectivity(config)
    return result.to_dict()


def check_network_connectivity(config: Dict) -> Dict:
    """Alias for check_network to maintain backward compatibility."""
    result = _check_network_connectivity(config)
    return result.to_dict()

