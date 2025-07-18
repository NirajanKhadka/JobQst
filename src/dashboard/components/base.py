#!/usr/bin/env python3
"""
Base component class for modular dashboard architecture.
Provides common functionality and interface for all dashboard components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
import streamlit as st
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ComponentError(Exception):
    """Custom exception for component-related errors"""
    pass


class BaseComponent(ABC):
    """
    Abstract base class for all dashboard components.
    Follows the modular pattern similar to consumer architecture.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.is_initialized = False
        self.error_count = 0
        self.last_error = None
        self.logger = logging.getLogger(f"dashboard.{name}")
        
    def initialize(self) -> bool:
        """
        Initialize the component. Must be called before render().
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self._setup()
            self.is_initialized = True
            self.logger.info(f"✅ Component '{self.name}' initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize component '{self.name}': {e}")
            self.last_error = str(e)
            self.error_count += 1
            return False
    
    def render(self, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Render the component to the Streamlit interface.
        
        Args:
            data: Optional data to pass to the component
            
        Returns:
            bool: True if rendering successful, False otherwise
        """
        if not self.is_initialized:
            self.logger.warning(f"⚠️ Component '{self.name}' not initialized, attempting auto-initialization")
            if not self.initialize():
                st.error(f"❌ Failed to initialize component '{self.name}'")
                return False
        
        try:
            with st.container():
                self._render_content(data)
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to render component '{self.name}': {e}")
            self.last_error = str(e)
            self.error_count += 1
            self._render_error(e)
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the component.
        
        Returns:
            Dict containing health information
        """
        return {
            "name": self.name,
            "initialized": self.is_initialized,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "status": "healthy" if self.error_count == 0 else "degraded"
        }
    
    def reset_errors(self):
        """Reset error count and last error"""
        self.error_count = 0
        self.last_error = None
    
    @abstractmethod
    def _setup(self):
        """
        Component-specific setup logic.
        Implemented by each component.
        """
        pass
    
    @abstractmethod 
    def _render_content(self, data: Optional[Dict[str, Any]] = None):
        """
        Component-specific rendering logic.
        Implemented by each component.
        """
        pass
    
    def _render_error(self, error: Exception):
        """
        Render error message to Streamlit interface.
        
        Args:
            error: The exception that occurred
        """
        with st.expander(f"❌ Error in {self.name} component", expanded=False):
            st.error(f"Error: {str(error)}")
            if self.config.get('debug', False):
                import traceback
                st.code(traceback.format_exc())
    
    def validate_data(self, data: Any, required_fields: List[str]) -> bool:
        """
        Validate that required fields are present in data.
        
        Args:
            data: Data to validate
            required_fields: List of required field names
            
        Returns:
            bool: True if validation passes
        """
        if not data:
            self.logger.warning(f"No data provided to component '{self.name}'")
            return False
            
        if isinstance(data, dict):
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.logger.warning(f"Missing required fields in '{self.name}': {missing_fields}")
                return False
                
        elif isinstance(data, pd.DataFrame):
            missing_cols = [col for col in required_fields if col not in data.columns]
            if missing_cols:
                self.logger.warning(f"Missing required columns in '{self.name}': {missing_cols}")
                return False
        
        return True


class ContainerComponent(BaseComponent):
    """
    Base class for components that contain other components.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.children: List[BaseComponent] = []
        
    def add_component(self, component: BaseComponent):
        """Add a child component"""
        self.children.append(component)
        
    def initialize(self) -> bool:
        """Initialize this component and all children"""
        if not super().initialize():
            return False
            
        # Initialize all children
        for child in self.children:
            if not child.initialize():
                self.logger.warning(f"Child component '{child.name}' failed to initialize")
                
        return True
        
    def render(self, data: Optional[Dict[str, Any]] = None) -> bool:
        """Render this component and all children"""
        if not super().render(data):
            return False
            
        # Render all children
        for child in self.children:
            child.render(data)
            
        return True
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status including children"""
        status = super().get_health_status()
        status["children"] = [child.get_health_status() for child in self.children]
        
        # Aggregate health
        child_errors = sum(child.error_count for child in self.children)
        status["total_errors"] = status["error_count"] + child_errors
        
        if child_errors > 0:
            status["status"] = "degraded"
            
        return status


class CachedComponent(BaseComponent):
    """
    Base class for components that support caching.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.cache_ttl = config.get('cache_ttl', 300) if config else 300  # 5 minutes default
        self.last_cache_time = None
        self.cached_data = None
        
    def get_cached_data(self, data_key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if self.cached_data and self.last_cache_time:
            elapsed = (datetime.now() - self.last_cache_time).total_seconds()
            if elapsed < self.cache_ttl:
                return self.cached_data.get(data_key)
        return None
        
    def set_cached_data(self, data_key: str, data: Any):
        """Set data in cache"""
        if not self.cached_data:
            self.cached_data = {}
        self.cached_data[data_key] = data
        self.last_cache_time = datetime.now()
        
    def clear_cache(self):
        """Clear all cached data"""
        self.cached_data = None
        self.last_cache_time = None
