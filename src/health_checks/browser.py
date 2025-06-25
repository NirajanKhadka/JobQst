import psutil
from typing import Dict

def check_browser_processes(config: Dict) -> Dict:
    """Check for zombie browser processes."""
    try:
        browser_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                if any(browser in proc.info['name'].lower() for browser in ['chrome', 'firefox', 'edge', 'opera']):
                    browser_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        process_limit = config.get("browser_process_limit", 20)
        if len(browser_processes) > process_limit:
            return {
                "status": "warning",
                "message": f"Many browser processes running: {len(browser_processes)}"
            }
        else:
            return {
                "status": "healthy",
                "message": f"Browser processes normal: {len(browser_processes)} running"
            }
            
    except Exception as e:
        return {"status": "error", "message": f"Browser process check failed: {str(e)}"}