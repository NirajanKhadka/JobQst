"""
Base component for dashboard compatibility
"""

from typing import Any, Dict


class BaseComponent:
    """Base component class for dashboard compatibility"""

    def __init__(self, name: str):
        """Initialize base component"""
        self.name = name
        self.config = {}

    def render(self) -> Dict[str, Any]:
        """Render component"""
        return {"type": "component", "name": self.name, "config": self.config}

    def update(self, data: Dict[str, Any]) -> bool:
        """Update component with new data"""
        try:
            self.config.update(data)
            return True
        except Exception:
            return False
