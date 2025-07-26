#!/usr/bin/env python3
"""
Modular Logging Component for Dashboard Integration
Provides real-time log viewing with filtering and search capabilities.
"""

import streamlit as st
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import re

class LogLevel:
    """Log level constants with colors."""
    DEBUG = {"name": "DEBUG", "color": "#6c757d", "icon": "🔍"}
    INFO = {"name": "INFO", "color": "#17a2b8", "icon": "ℹ️"}
    WARNING = {"name": "WARNING", "color": "#ffc107", "icon": "⚠️"}
    ERROR = {"name": "ERROR", "color": "#dc3545", "icon": "❌"}
    CRITICAL = {"name": "CRITICAL", "color": "#6f42c1", "icon": "🚨"}

class LogEntry:
    """Represents a single log entry."""
    def __init__(self, timestamp: str, level: str, message: str, source: str = ""):
        self.timestamp = timestamp
        self.level = level
        self.message = message
        self.source = source
        self.datetime = self._parse_timestamp(timestamp)
    
    def _parse_timestamp(self, timestamp: str) -> datetime:
        """Parse timestamp string to datetime object."""
        try:
            # Try common timestamp formats
            formats = [
                "%Y-%m-%d %H:%M:%S,%f",
                "%Y-%m-%d %H:%M:%S.%f", 
                "%Y-%m-%d %H:%M:%S",
                "%m/%d/%Y %H:%M:%S",
                "%d/%m/%Y %H:%M:%S"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp, fmt)
                except ValueError:
                    continue
                    
            # Fallback to current time
            return datetime.now()
        except:
            return datetime.now()

class LoggingComponent:
    """Modular logging component for dashboard integration."""
    
    def __init__(self):
        self.log_sources = {
            "application": "logs/application.log",
            "scraper": "logs/scraper.log", 
            "processor": "logs/processor.log",
            "error": "logs/error_logs.log",
            "gemini_api": "logs/gemini_api_call_log.json",
            "scheduler": "logs/scheduler/"
        }
        
        # Initialize session state for logs
        if "log_entries" not in st.session_state:
            st.session_state.log_entries = []
        if "log_auto_refresh" not in st.session_state:
            st.session_state.log_auto_refresh = True
        if "log_filter_level" not in st.session_state:
            st.session_state.log_filter_level = "ALL"
        if "log_filter_source" not in st.session_state:
            st.session_state.log_filter_source = "ALL"
    
    def render_logging_dashboard(self):
        """Render the main logging dashboard."""
        st.markdown("### 📋 System Logs")
        
        # Log controls
        self._render_log_controls()
        
        # Log display
        self._render_log_display()
    
    def render_compact_logs(self, max_entries: int = 10, sources: List[str] = None):
        """Render a compact log view for embedding in other components."""
        st.markdown("#### 📝 Recent Activity")
        
        logs = self._get_recent_logs(max_entries, sources)
        
        if logs:
            for log in logs[-max_entries:]:
                level_info = self._get_level_info(log.level)
                
                with st.container():
                    col1, col2 = st.columns([1, 6])
                    with col1:
                        st.markdown(f"{level_info['icon']} **{log.level}**")
                    with col2:
                        st.markdown(f"**{log.timestamp}** - {log.message[:100]}...")
                        if log.source:
                            st.caption(f"Source: {log.source}")
        else:
            st.info("No recent log entries found.")
    
    def _render_log_controls(self):
        """Render log filtering and control options."""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.session_state.log_auto_refresh = st.checkbox(
                "🔄 Auto Refresh", 
                value=st.session_state.log_auto_refresh,
                help="Automatically refresh logs every 5 seconds"
            )
        
        with col2:
            st.session_state.log_filter_level = st.selectbox(
                "📊 Level Filter",
                ["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                index=0 if st.session_state.log_filter_level == "ALL" else 
                      ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(st.session_state.log_filter_level) + 1
            )
        
        with col3:
            available_sources = ["ALL"] + list(self.log_sources.keys())
            st.session_state.log_filter_source = st.selectbox(
                "🎯 Source Filter",
                available_sources,
                index=available_sources.index(st.session_state.log_filter_source)
            )
        
        with col4:
            if st.button("🔄 Refresh Now", use_container_width=True):
                self._refresh_logs()
        
        with col5:
            if st.button("🗑️ Clear Display", use_container_width=True):
                st.session_state.log_entries = []
                st.rerun()
        
        # Search functionality
        search_term = st.text_input("🔍 Search logs", placeholder="Enter search term...")
        
        if search_term:
            st.session_state.log_search_term = search_term
        else:
            st.session_state.log_search_term = ""
    
    def _render_log_display(self):
        """Render the main log display area."""
        # Auto-refresh logic
        if st.session_state.log_auto_refresh:
            # Use a placeholder for auto-refresh
            placeholder = st.empty()
            with placeholder.container():
                self._display_filtered_logs()
        else:
            self._display_filtered_logs()
    
    def _display_filtered_logs(self):
        """Display logs with applied filters."""
        logs = self._get_filtered_logs()
        
        if not logs:
            st.info("No logs match the current filters.")
            return
        
        # Log statistics
        self._render_log_statistics(logs)
        
        # Log entries
        st.markdown("#### 📜 Log Entries")
        
        # Create a container for scrollable logs
        log_container = st.container()
        
        with log_container:
            # Show recent logs first (reverse chronological)
            for log in reversed(logs[-100:]):  # Show last 100 entries
                self._render_log_entry(log)
    
    def _render_log_statistics(self, logs: List[LogEntry]):
        """Render log statistics."""
        if not logs:
            return
            
        # Count by level
        level_counts = {}
        for log in logs:
            level_counts[log.level] = level_counts.get(log.level, 0) + 1
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📊 Total Entries", len(logs))
        
        with col2:
            st.metric("❌ Errors", level_counts.get("ERROR", 0))
        
        with col3:
            st.metric("⚠️ Warnings", level_counts.get("WARNING", 0))
        
        with col4:
            st.metric("ℹ️ Info", level_counts.get("INFO", 0))
        
        with col5:
            st.metric("🔍 Debug", level_counts.get("DEBUG", 0))
    
    def _render_log_entry(self, log: LogEntry):
        """Render a single log entry."""
        level_info = self._get_level_info(log.level)
        
        with st.expander(
            f"{level_info['icon']} {log.timestamp} - {log.message[:80]}...",
            expanded=False
        ):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.markdown(f"**Level:** {log.level}")
                st.markdown(f"**Time:** {log.timestamp}")
                if log.source:
                    st.markdown(f"**Source:** {log.source}")
            
            with col2:
                st.markdown("**Message:**")
                st.code(log.message, language="text")
    
    def _get_filtered_logs(self) -> List[LogEntry]:
        """Get logs with applied filters."""
        logs = self._get_all_logs()
        
        # Apply level filter
        if st.session_state.log_filter_level != "ALL":
            logs = [log for log in logs if log.level == st.session_state.log_filter_level]
        
        # Apply source filter
        if st.session_state.log_filter_source != "ALL":
            logs = [log for log in logs if log.source == st.session_state.log_filter_source]
        
        # Apply search filter
        if hasattr(st.session_state, 'log_search_term') and st.session_state.log_search_term:
            search_term = st.session_state.log_search_term.lower()
            logs = [log for log in logs if search_term in log.message.lower()]
        
        return logs
    
    def _get_all_logs(self) -> List[LogEntry]:
        """Get all available logs from various sources."""
        all_logs = []
        
        for source_name, source_path in self.log_sources.items():
            try:
                if source_path.endswith('.json'):
                    logs = self._parse_json_logs(source_path, source_name)
                elif source_path.endswith('/'):
                    logs = self._parse_directory_logs(source_path, source_name)
                else:
                    logs = self._parse_text_logs(source_path, source_name)
                
                all_logs.extend(logs)
            except Exception as e:
                # Add error log entry
                all_logs.append(LogEntry(
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    level="ERROR",
                    message=f"Failed to read {source_name} logs: {e}",
                    source="logging_component"
                ))
        
        # Sort by timestamp
        all_logs.sort(key=lambda x: x.datetime)
        return all_logs
    
    def _get_recent_logs(self, max_entries: int, sources: List[str] = None) -> List[LogEntry]:
        """Get recent logs for compact display."""
        logs = self._get_all_logs()
        
        if sources:
            logs = [log for log in logs if log.source in sources]
        
        return logs[-max_entries:] if logs else []
    
    def _parse_text_logs(self, file_path: str, source_name: str) -> List[LogEntry]:
        """Parse standard text log files."""
        logs = []
        
        if not os.path.exists(file_path):
            return logs
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines[-1000:]:  # Last 1000 lines
                line = line.strip()
                if not line:
                    continue
                
                # Try to parse log format: TIMESTAMP LEVEL MESSAGE
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    timestamp = f"{parts[0]} {parts[1]}"
                    level = parts[2] if len(parts) > 2 else "INFO"
                    message = ' '.join(parts[3:]) if len(parts) > 3 else line
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    level = "INFO"
                    message = line
                
                logs.append(LogEntry(timestamp, level, message, source_name))
        
        except Exception as e:
            logs.append(LogEntry(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                level="ERROR",
                message=f"Error parsing {file_path}: {e}",
                source=source_name
            ))
        
        return logs
    
    def _parse_json_logs(self, file_path: str, source_name: str) -> List[LogEntry]:
        """Parse JSON log files."""
        logs = []
        
        if not os.path.exists(file_path):
            return logs
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for entry in data[-100:]:  # Last 100 entries
                    timestamp = entry.get('timestamp', datetime.now().isoformat())
                    level = entry.get('level', 'INFO')
                    message = entry.get('message', str(entry))
                    
                    logs.append(LogEntry(timestamp, level, message, source_name))
            
            elif isinstance(data, dict):
                # Single entry or structured data
                timestamp = data.get('timestamp', datetime.now().isoformat())
                level = data.get('level', 'INFO')
                message = data.get('message', json.dumps(data, indent=2))
                
                logs.append(LogEntry(timestamp, level, message, source_name))
        
        except Exception as e:
            logs.append(LogEntry(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                level="ERROR",
                message=f"Error parsing JSON {file_path}: {e}",
                source=source_name
            ))
        
        return logs
    
    def _parse_directory_logs(self, dir_path: str, source_name: str) -> List[LogEntry]:
        """Parse logs from a directory."""
        logs = []
        
        if not os.path.exists(dir_path):
            return logs
        
        try:
            for file_path in Path(dir_path).glob("*.log"):
                file_logs = self._parse_text_logs(str(file_path), f"{source_name}/{file_path.name}")
                logs.extend(file_logs)
        
        except Exception as e:
            logs.append(LogEntry(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                level="ERROR",
                message=f"Error parsing directory {dir_path}: {e}",
                source=source_name
            ))
        
        return logs
    
    def _get_level_info(self, level: str) -> Dict[str, str]:
        """Get level information (color, icon)."""
        level_map = {
            "DEBUG": LogLevel.DEBUG,
            "INFO": LogLevel.INFO,
            "WARNING": LogLevel.WARNING,
            "ERROR": LogLevel.ERROR,
            "CRITICAL": LogLevel.CRITICAL
        }
        
        return level_map.get(level.upper(), LogLevel.INFO)
    
    def _refresh_logs(self):
        """Refresh logs manually."""
        # Clear cached logs
        if hasattr(st.session_state, 'log_entries'):
            st.session_state.log_entries = []
        
        st.rerun()

# Global logging component instance
logging_component = LoggingComponent()