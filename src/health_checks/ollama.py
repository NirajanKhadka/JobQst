from typing import Dict
from .health_utils import check_ollama_service as _check_ollama_service


def check_ollama(config: Dict) -> Dict:
    """Check Ollama service using shared utilities."""
    result = _check_ollama_service(config)
    return result.to_dict()


def check_ollama_service(config: Dict) -> Dict:
    """Alias for check_ollama to maintain backward compatibility."""
    result = _check_ollama_service(config)
    return result.to_dict()
