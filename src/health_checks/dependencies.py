from typing import Dict, List

def check_dependencies(config: Dict) -> Dict:
    """Check critical Python dependencies."""
    try:
        critical_modules: List[str] = config.get("critical_modules", [
            "playwright", "requests", "rich", "beautifulsoup4",
            "python-docx", "pandas", "psutil"
        ])
        
        missing_modules = []
        
        for module in critical_modules:
            try:
                __import__(module.replace("-", "_"))
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            return {
                "status": "critical",
                "message": f"Missing dependencies: {', '.join(missing_modules)}"
            }
        else:
            return {"status": "healthy", "message": "All dependencies available"}
            
    except Exception as e:
        return {"status": "error", "message": f"Dependency check failed: {str(e)}"}