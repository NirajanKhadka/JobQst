import psutil
from typing import Dict

def check_memory_usage(config: Dict) -> Dict:
    """Check system memory usage."""
    try:
        memory = psutil.virtual_memory()
        used_percent = memory.percent
        available_gb = memory.available / (1024**3)
        
        critical_threshold = config.get("critical_memory_usage_percent", 85)
        warning_threshold = 75

        if used_percent > critical_threshold:
            return {
                "status": "critical",
                "message": f"Memory usage critical: {used_percent:.1f}% used, {available_gb:.1f}GB available"
            }
        elif used_percent > warning_threshold:
            return {
                "status": "warning",
                "message": f"Memory usage high: {used_percent:.1f}% used, {available_gb:.1f}GB available"
            }
        else:
            return {
                "status": "healthy",
                "message": f"Memory usage normal: {used_percent:.1f}% used, {available_gb:.1f}GB available"
            }
            
    except Exception as e:
        return {"status": "error", "message": f"Memory check failed: {str(e)}"}

def check_memory(config: Dict) -> Dict:
    """Alias for check_memory_usage to match system health monitor expectations."""
    return check_memory_usage(config)