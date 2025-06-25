import requests
from typing import Dict

def check_ollama_service(config: Dict) -> Dict:
    """Check Ollama service availability."""
    try:
        ollama_url = config.get("ollama_url", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {
                "status": "healthy",
                "message": f"Ollama service running with {len(models)} models"
            }
        else:
            return {"status": "warning", "message": "Ollama service not responding"}
            
    except Exception as e:
        return {"status": "warning", "message": f"Ollama service check failed: {str(e)}"}