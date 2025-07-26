#!/usr/bin/env python3
"""
Header component for the dashboard.
Displays title, subtitle, and navigation elements.
"""

import streamlit as st
from typing import Dict, Any, Optional
from .base import BaseComponent


class HeaderComponent(BaseComponent):
    """
    Dashboard header component with title, subtitle, and navigation.
    """
    
    def _setup(self):
        """Setup header configuration"""
        # Default configuration
        self.title = self.config.get('title', '🚀 AutoJobAgent Dashboard')
        self.subtitle = self.config.get('subtitle', 'Professional Job Application Management & Analytics')
        self.show_navigation = self.config.get('show_navigation', True)
        self.custom_css = self.config.get('custom_css', '')
        
    def _render_content(self, data: Optional[Dict[str, Any]] = None):
        """Render the header content"""
        
        # Apply custom CSS if provided
        if self.custom_css:
            st.markdown(self.custom_css, unsafe_allow_html=True)
        
        # Main header
        st.markdown(
            f"""
            <div class="dashboard-header">
                <h1 class="dashboard-title">{self.title}</h1>
                <p class="dashboard-subtitle">{self.subtitle}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Navigation if enabled
        if self.show_navigation:
            self._render_navigation(data)
    
    def _render_navigation(self, data: Optional[Dict[str, Any]] = None):
        """Render navigation elements"""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Profile selector
            profiles = data.get('profiles', []) if data else []
            if profiles:
                selected_profile = st.selectbox(
                    "🎯 Select Profile",
                    profiles,
                    index=0,
                    help="Choose the profile to view job data",
                    key=f"{self.name}_profile_select"
                )
                # Store selected profile in session state
                st.session_state[f'{self.name}_selected_profile'] = selected_profile
            else:
                st.warning("No profiles found")
        
        with col2:
            auto_refresh = st.checkbox(
                "🔄 Auto Refresh", 
                value=False,
                key=f"{self.name}_auto_refresh"
            )
            
        with col3:
            if st.button("🔄 Refresh Now", type="primary", key=f"{self.name}_refresh"):
                st.cache_resource.clear()
                st.rerun()
    
    def get_selected_profile(self) -> Optional[str]:
        """Get the currently selected profile"""
        return st.session_state.get(f'{self.name}_selected_profile')
    
    def is_auto_refresh_enabled(self) -> bool:
        """Check if auto refresh is enabled"""
        return st.session_state.get(f'{self.name}_auto_refresh', False)
