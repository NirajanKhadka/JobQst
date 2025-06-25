import psutil
from typing import Dict

def check_disk_space(config: Dict) -> Dict:
    """Check available disk space."""
    try:
        disk_usage = psutil.disk_usage('.')
        used_percent = (disk_usage.used / disk_usage.total) * 100
        free_gb = disk_usage.free / (1024**3)
        
        critical_threshold = config.get("critical_disk_usage_percent", 90)
        warning_threshold = 80

        if used_percent > critical_threshold:
            return {
                "status": "critical",
                "message": f"Disk usage critical: {used_percent:.1f}% used, {free_gb:.1f}GB free"
            }
        elif used_percent > warning_threshold:
            return {
                "status": "warning",
                "message": f"Disk usage high: {used_percent:.1f}% used, {free_gb:.1f}GB free"
            }
        else:
            return {
                "status": "healthy",
                "message": f"Disk usage normal: {used_percent:.1f}% used, {free_gb:.1f}GB free"
            }
            
    except Exception as e:
        return {"status": "error", "message": f"Disk check failed: {str(e)}"}