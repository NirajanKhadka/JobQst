#!/usr/bin/env python3
"""
Metrics component for displaying job statistics and KPIs.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, List
from .base import CachedComponent


class MetricsComponent(CachedComponent):
    """
    Component for displaying dashboard metrics and KPIs.
    """
    
    def _setup(self):
        """Setup metrics configuration"""
        self.metrics_config = self.config.get('metrics', {
            'total_jobs': {'label': 'Total Jobs', 'icon': '📊'},
            'applied_jobs': {'label': 'Applied', 'icon': '✅'},
            'pending_jobs': {'label': 'Pending', 'icon': '⏳'},
            'avg_match_score': {'label': 'Avg Match', 'icon': '🎯', 'format': '{:.1f}%'}
        })
        self.columns = self.config.get('columns', 4)
        
    def _render_content(self, data: Optional[Dict[str, Any]] = None):
        """Render metrics cards"""
        
        if not data or 'metrics' not in data:
            st.warning("⚠️ No metrics data available")
            return
            
        metrics = data['metrics']
        
        # Render metrics cards
        cols = st.columns(self.columns)
        
        for i, (metric_key, metric_config) in enumerate(self.metrics_config.items()):
            col_idx = i % self.columns
            with cols[col_idx]:
                self._render_metric_card(
                    metric_key,
                    metrics.get(metric_key, 0),
                    metric_config
                )
    
    def _render_metric_card(self, metric_key: str, value: Any, config: Dict[str, str]):
        """Render a single metric card"""
        
        # Format the value
        format_str = config.get('format', '{}')
        try:
            if '{' in format_str and '}' in format_str:
                formatted_value = format_str.format(value)
            else:
                formatted_value = str(value)
        except:
            formatted_value = str(value)
        
        # Render the card
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{config.get('icon', '')} {formatted_value}</div>
                <div class="metric-label">{config['label']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
