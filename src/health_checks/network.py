import requests
from typing import Dict

def check_network_connectivity(config: Dict) -> Dict:
    """Check network connectivity."""
    try:
        test_urls = config.get("test_urls", ["https://www.google.com", "https://github.com"])
        successful_connections = 0
        
        for url in test_urls:
            try:
                response = requests.head(url, timeout=5)
                if response.status_code < 400:
                    successful_connections += 1
            except:
                continue
        
        if successful_connections == 0:
            return {"status": "critical", "message": "No network connectivity"}
        elif successful_connections < len(test_urls):
            return {"status": "warning", "message": "Limited network connectivity"}
        else:
            return {"status": "healthy", "message": "Network connectivity normal"}
            
    except Exception as e:
        return {"status": "error", "message": f"Network check failed: {str(e)}"}

def check_network(config: Dict) -> Dict:
    """Alias for check_network_connectivity to match system health monitor expectations."""
    return check_network_connectivity(config)