import os
from pathlib import Path
from typing import Dict, List

def check_file_permissions(config: Dict) -> Dict:
    """Check file permissions for critical directories."""
    try:
        critical_paths: List[str] = config.get("critical_paths", 
            [".", "profiles", "temp", "customized_documents"])
        
        permission_issues = []
        
        for path_str in critical_paths:
            path = Path(path_str)
            if path.exists():
                if not os.access(path, os.R_OK | os.W_OK):
                    permission_issues.append(str(path))
        
        if permission_issues:
            return {
                "status": "critical",
                "message": f"Permission issues with: {', '.join(permission_issues)}"
            }
        else:
            return {"status": "healthy", "message": "File permissions normal"}
            
    except Exception as e:
        return {"status": "error", "message": f"Permission check failed: {str(e)}"}