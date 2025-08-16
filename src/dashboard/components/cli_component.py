#!/usr/bin/env python3
"""
CLI Component for Dashboard Integration
Provides a complete CLI interface within the dashboard.
Following modular architecture standards.
"""

import streamlit as st
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.cli_service import cli_service, CLICommand

logger = logging.getLogger(__name__)


class CLIComponent:
    """Dashboard component for CLI interface and command execution."""
    
    def __init__(self):
        self.name = "CLI Interface"
        self.cli_service = cli_service
        
    def render(self, profile_name: str) -> None:
        """Render the CLI interface tab."""
        st.markdown('<h2 class="section-header">🖥️ CLI Interface</h2>', unsafe_allow_html=True)
        
        # Create tabs for different CLI sections
        cmd_tab, history_tab, running_tab, custom_tab = st.tabs([
            "📋 Commands", "📜 History", "⚡ Running", "✏️ Custom"
        ])
        
        with cmd_tab:
            self._render_commands_section(profile_name)
        
        with history_tab:
            self._render_history_section()
        
        with running_tab:
            self._render_running_commands_section()
        
        with custom_tab:
            self._render_custom_commands_section(profile_name)
    
    def _render_commands_section(self, profile_name: str) -> None:
        """Render the main commands section."""
        st.markdown("### Available Commands")
        st.info("Execute CLI commands directly from the dashboard with real-time output.")
        
        # Get commands by category
        categories = self.cli_service.get_commands_by_category()
        
        # Command execution parameters
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown("#### ⚙️ Parameters")
            
            # Batch size for applicable commands
            batch_size = st.number_input(
                "Batch Size",
                min_value=1,
                max_value=50,
                value=5,
                help="Number of jobs to process in batch operations",
                key="cli_batch_size"
            )
            
            # Keywords for scraping
            keywords = st.text_input(
                "Keywords (comma-separated)",
                value="Python,Data Analyst,Software Engineer",
                help="Keywords for job scraping",
                key="cli_keywords"
            )
            
            # Sites selection for scraping
            available_sites = ["eluta", "indeed", "linkedin", "monster"]
            selected_sites = st.multiselect(
                "Sites to Scrape",
                available_sites,
                default=["eluta"],
                help="Select job sites for scraping",
                key="cli_sites"
            )
        
        with col1:
            # Render commands by category
            for category, commands in categories.items():
                with st.expander(f"📁 {category.title()} Commands", expanded=(category == "scraping")):
                    
                    for cmd in commands:
                        self._render_command_card(cmd, profile_name, {
                            "batch_size": batch_size,
                            "keywords": keywords,
                            "sites": ",".join(selected_sites)
                        })
    
    def _render_command_card(self, cmd: CLICommand, profile_name: str, params: Dict[str, Any]) -> None:
        """Render a command card with execution button."""
        
        # Check if command is currently running
        running_cmd = self.cli_service.get_command_status(cmd.name)
        is_running = running_cmd is not None
        
        # Command card container
        card_container = st.container()
        
        with card_container:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{cmd.description}**")
                
                # Show formatted command preview
                try:
                    formatted_cmd = self.cli_service.format_command(
                        cmd.name, profile_name, **params
                    )
                    st.code(formatted_cmd, language="bash")
                except ValueError as e:
                    st.error(f"Command formatting error: {e}")
                    return
            
            with col2:
                # Execution button
                button_text = "⏹️ Stop" if is_running else "▶️ Run"
                button_disabled = False
                
                if st.button(
                    button_text,
                    key=f"cmd_{cmd.name}",
                    disabled=button_disabled,
                    help=f"Execute {cmd.name}"
                ):
                    if is_running:
                        self._stop_command(cmd.name)
                    else:
                        self._execute_command(cmd.name, profile_name, params)
            
            with col3:
                # Status indicator
                if is_running:
                    st.markdown("🟡 **Running**")
                    if running_cmd:
                        elapsed = datetime.now() - running_cmd.start_time
                        st.caption(f"⏱️ {int(elapsed.total_seconds())}s")
                else:
                    st.markdown("🔵 **Ready**")
                    st.caption(f"⏱️ ~{cmd.estimated_duration}s")
        
        # Show real-time output for running commands
        if is_running and running_cmd:
            self._render_command_output(running_cmd)
    
    def _render_command_output(self, cmd: CLICommand) -> None:
        """Render real-time command output."""
        if cmd.output or cmd.error_output:
            with st.expander("📄 Live Output", expanded=True):
                output_container = st.container()
                
                with output_container:
                    if cmd.output:
                        st.text_area(
                            "Output",
                            value=cmd.output,
                            height=200,
                            disabled=True,
                            key=f"output_{cmd.name}_{id(cmd)}"
                        )
                    
                    if cmd.error_output:
                        st.text_area(
                            "Errors",
                            value=cmd.error_output,
                            height=100,
                            disabled=True,
                            key=f"error_{cmd.name}_{id(cmd)}"
                        )
    
    def _execute_command(self, command_name: str, profile_name: str, params: Dict[str, Any]) -> None:
        """Execute a command using the orchestration service."""
        
        # Map CLI commands to orchestration services
        command_mapping = {
            "scrape_eluta": "scraper",
            "scrape_indeed": "scraper", 
            "scrape_all": "scraper",
            "process_jobs": "processor",
            "generate_docs": "document_worker_1",  # Start first worker
            "apply_jobs": "applicator"
        }
        
        if command_name in command_mapping:
            service_name = command_mapping[command_name]
            
            # Import orchestration service
            try:
                from src.services.orchestration_service import orchestration_service
                
                # Start the corresponding service
                success = orchestration_service.start_service(service_name, profile_name)
                
                if success:
                    st.success(f"✅ Started {service_name} service")
                    
                    # Add to session state for tracking
                    if "running_services" not in st.session_state:
                        st.session_state.running_services = set()
                    st.session_state.running_services.add(service_name)
                else:
                    st.error(f"❌ Failed to start {service_name} service")
                    
            except ImportError:
                st.warning("⚠️ Improved orchestration features are loading. Using CLI fallback.")
                # Fallback to showing command for manual execution
                try:
                    formatted_cmd = self.cli_service.format_command(command_name, profile_name, **params)
                    st.code(formatted_cmd, language="bash")
                    st.info("💡 Copy and run this command in a terminal")
                except Exception as e:
                    st.error(f"Command formatting error: {e}")
        else:
            # For other commands, show for manual execution
            try:
                formatted_cmd = self.cli_service.format_command(command_name, profile_name, **params)
                st.code(formatted_cmd, language="bash")
                st.info("💡 Copy and run this command in a terminal")
            except Exception as e:
                st.error(f"Command formatting error: {e}")
        
        st.rerun()
    
    def _stop_command(self, command_name: str) -> None:
        """Stop a running command via orchestration service."""
        
        # Map CLI commands to orchestration services
        command_mapping = {
            "scrape_eluta": "scraper",
            "scrape_indeed": "scraper", 
            "scrape_all": "scraper",
            "process_jobs": "processor",
            "generate_docs": "document_worker_1",
            "apply_jobs": "applicator"
        }
        
        if command_name in command_mapping:
            service_name = command_mapping[command_name]
            
            try:
                from src.services.orchestration_service import orchestration_service
                
                success = orchestration_service.stop_service(service_name)
                
                if success:
                    st.success(f"⏹️ Stopped {service_name} service")
                    
                    # Remove from session state
                    if "running_services" in st.session_state:
                        st.session_state.running_services.discard(service_name)
                else:
                    st.error(f"❌ Failed to stop {service_name} service")
                    
            except ImportError:
                st.warning("⚠️ Improved orchestration features are loading. Service management unavailable.")
        else:
            st.warning(f"Cannot stop {command_name} - not a managed service")
            
        st.rerun()
    
    def _render_history_section(self) -> None:
        """Render command execution history."""
        st.markdown("### 📜 Command History")
        
        history = self.cli_service.get_command_history(limit=20)
        
        if not history:
            st.info("No commands have been executed yet.")
            return
        
        # History table
        history_data = []
        for cmd in history:
            duration = ""
            if cmd.start_time and cmd.end_time:
                duration = str(cmd.end_time - cmd.start_time).split('.')[0]
            elif cmd.start_time:
                duration = str(datetime.now() - cmd.start_time).split('.')[0]
            
            history_data.append({
                "Command": cmd.name,
                "Status": cmd.status.title(),
                "Started": cmd.start_time.strftime("%H:%M:%S") if cmd.start_time else "-",
                "Duration": duration,
                "Description": cmd.description[:50] + "..." if len(cmd.description) > 50 else cmd.description
            })
        
        st.dataframe(
            history_data,
            use_container_width=True,
            hide_index=True
        )
        
        # Clear history button
        if st.button("🗑️ Clear History", help="Clear command execution history"):
            self.cli_service.command_history.clear()
            st.success("Command history cleared!")
            st.rerun()
    
    def _render_running_commands_section(self) -> None:
        """Render currently running commands."""
        st.markdown("### ⚡ Running Commands")
        
        running_commands = self.cli_service.get_running_commands()
        
        if not running_commands:
            st.info("No commands are currently running.")
            return
        
        # Running commands details
        for execution_id, cmd in running_commands.items():
            with st.expander(f"🔄 {cmd.name} - {cmd.status.title()}", expanded=True):
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**Command:** `{cmd.command}`")
                    st.markdown(f"**Description:** {cmd.description}")
                
                with col2:
                    if cmd.start_time:
                        elapsed = datetime.now() - cmd.start_time
                        st.metric("Elapsed Time", f"{int(elapsed.total_seconds())}s")
                        
                        # Progress estimation
                        progress = min(elapsed.total_seconds() / cmd.estimated_duration, 1.0)
                        st.progress(progress)
                
                with col3:
                    if st.button(f"⏹️ Stop {cmd.name}", key=f"stop_{execution_id}"):
                        self._stop_command(cmd.name)
                
                # Real-time output
                self._render_command_output(cmd)
    
    def _render_custom_commands_section(self, profile_name: str) -> None:
        """Render custom command creation interface."""
        st.markdown("### ✏️ Custom Commands")
        st.info("Create and execute custom CLI commands.")
        
        with st.form("custom_command_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                cmd_name = st.text_input(
                    "Command Name",
                    placeholder="my_custom_command",
                    help="Unique name for your custom command"
                )
                
                cmd_command = st.text_area(
                    "Command",
                    placeholder="python main.py {profile} --action scrape --keywords 'AI,ML'",
                    help="Command to execute. Use {profile} for profile substitution."
                )
            
            with col2:
                cmd_description = st.text_area(
                    "Description",
                    placeholder="My custom scraping command for AI/ML jobs",
                    help="Description of what this command does"
                )
                
                cmd_category = st.selectbox(
                    "Category",
                    ["custom", "scraping", "processing", "documents", "applications", "system"],
                    help="Category for organizing commands"
                )
            
            submitted = st.form_submit_button("➕ Create Command")
            
            if submitted:
                if cmd_name and cmd_command:
                    try:
                        custom_cmd = self.cli_service.create_custom_command(
                            name=cmd_name,
                            command=cmd_command,
                            description=cmd_description,
                            category=cmd_category
                        )
                        st.success(f"✅ Created custom command: {cmd_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to create command: {e}")
                else:
                    st.error("Please provide both command name and command.")
        
        # Show existing custom commands
        custom_commands = [
            cmd for cmd in self.cli_service.commands.values() 
            if cmd.category == "custom"
        ]
        
        if custom_commands:
            st.markdown("#### Existing Custom Commands")
            for cmd in custom_commands:
                with st.expander(f"📝 {cmd.name}"):
                    st.code(cmd.command, language="bash")
                    st.markdown(f"**Description:** {cmd.description}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"▶️ Run", key=f"run_custom_{cmd.name}"):
                            self._execute_command(cmd.name, profile_name, {})
                    with col2:
                        if st.button(f"🗑️ Delete", key=f"delete_custom_{cmd.name}"):
                            del self.cli_service.commands[cmd.name]
                            st.success(f"Deleted command: {cmd.name}")
                            st.rerun()


def render_cli_tab(profile_name: str) -> None:
    """Render the CLI interface tab."""
    cli_component = CLIComponent()
    cli_component.render(profile_name)
