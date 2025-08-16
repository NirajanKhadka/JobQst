#!/usr/bin/env python3
"""
JobSpy Integration Component for Unified Dashboard
Provides interface for running JobSpy searches with Canadian cities parameters.
"""

import streamlit as st
import subprocess
import sys
import os
import time
from typing import List
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Orchestration controllers (optional)
try:
    from src.orchestration import OrchestratorConfig, run_jobspy_discovery
    HAS_ORCH = True
except Exception:
    HAS_ORCH = False

# Import JobSpy configuration
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
    from config.jobspy_integration_config import (
        JOBSPY_LOCATION_SETS,
        JOBSPY_SEARCH_TERM_SETS,
        JOBSPY_SITE_COMBINATIONS,
        JOBSPY_CONFIG_PRESETS
    )
    JOBSPY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"JobSpy configuration not available: {e}")
    JOBSPY_AVAILABLE = False


def render_jobspy_control():
    """Render JobSpy integration control panel with orchestration support."""
    st.header("🇨🇦 JobSpy Canadian Cities Integration")
    
    if not JOBSPY_AVAILABLE:
        st.error("JobSpy configuration not available. Please check installation.")
        return
    
    # Get orchestration service for real-time integration
    try:
        from src.dashboard.services.orchestration_service import OrchestrationService
        orchestration_service = OrchestrationService()
        has_orchestration = True
    except:
        orchestration_service = None
        has_orchestration = False
    
    # Status bar for orchestration
    if has_orchestration:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            try:
                import asyncio
                try:
                    # Try to get the queue status synchronously first
                    queue_status = getattr(orchestration_service, 'get_application_queue_status_sync', None)
                    if queue_status:
                        queue_data = queue_status()
                    else:
                        # Fallback to async call if sync version not available
                        queue_data = asyncio.run(orchestration_service.get_application_queue_status())
                    queue_length = queue_data.get("total_queued", 0)
                except Exception:
                    # If async fails, show a default value
                    queue_length = "N/A"
                st.metric("Job Queue", queue_length, delta=None)
            except Exception:
                st.metric("Job Queue", "N/A")
        
        with col2:
            try:
                # Check if JobSpy background search is running
                is_searching = orchestration_service.is_service_running("jobspy_search")
                search_status = "Running" if is_searching else "Idle"
                status_color = "🟢" if is_searching else "⚪"
                st.markdown(f"**Search Status:** {status_color} {search_status}")
            except:
                st.markdown("**Search Status:** ⚪ Unknown")
        
        with col3:
            try:
                # Get recent job discovery count
                recent_jobs = orchestration_service.get_recent_discoveries_count(hours=24)
                st.metric("Jobs Found (24h)", recent_jobs, delta=None)
            except:
                st.metric("Jobs Found (24h)", "N/A")
        
        with col4:
            # Manual job application trigger
            if st.button("🚀 Trigger Auto-Apply", use_container_width=True):
                try:
                    result = orchestration_service.trigger_job_application()
                    if result.get("success"):
                        st.success("Auto-apply triggered!")
                    else:
                        st.error(f"Failed: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Trigger failed: {e}")
    
    # Create tabs for different JobSpy functions
    jobspy_tabs = st.tabs([
        "🚀 Quick Launch", 
        "⚙️ Custom Search", 
        "🎯 Configurable Orchestration",
        "📊 Search History", 
        "📋 Configuration"
    ])
    
    with jobspy_tabs[0]:
        render_quick_launch()
    
    with jobspy_tabs[1]:
        render_custom_search()
    
    with jobspy_tabs[2]:
        render_Configurable_orchestration(orchestration_service if has_orchestration else None)
    
    with jobspy_tabs[3]:
        render_search_history()
    
    with jobspy_tabs[4]:
        render_configuration_info()


def render_Configurable_orchestration(orchestration_service):
    """Render Configurable orchestration controls for automated job discovery and application."""
    st.subheader("🎯 Configurable Orchestration")
    
    if not orchestration_service:
        st.warning("⚠️ Orchestration service not available")
        st.info("Configurable orchestration features require the orchestration service to be running.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔄 Automated Job Discovery")
        
        # Schedule configuration
        schedule_enabled = st.checkbox(
            "Enable Scheduled Discovery",
            value=False,
            help="Automatically run job searches at regular intervals"
        )
        
        if schedule_enabled:
            schedule_interval = st.selectbox(
                "Discovery Interval",
                options=[
                    ("4 hours", 4),
                    ("8 hours", 8), 
                    ("12 hours", 12),
                    ("Daily", 24),
                    ("Every 2 days", 48),
                    ("Weekly", 168)
                ],
                index=3,  # Default to daily
                format_func=lambda x: x[0]
            )
            
            max_jobs_per_search = st.number_input(
                "Max Jobs Per Search",
                min_value=50,
                max_value=1000,
                value=200,
                step=50,
                help="Limit jobs per scheduled search to manage processing load"
            )
            
            preferred_cities = st.multiselect(
                "Preferred Cities",
                options=["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa", "Edmonton", "Mississauga"],
                default=["Toronto", "Vancouver"],
                help="Focus discovery on these cities"
            )
            
            if st.button("💾 Save Schedule", use_container_width=True):
                try:
                    config = {
                        "enabled": schedule_enabled,
                        "interval_hours": schedule_interval[1],
                        "max_jobs": max_jobs_per_search,
                        "cities": preferred_cities
                    }
                    result = orchestration_service.configure_auto_discovery(config)
                    
                    if result.get("success"):
                        st.success("✅ Schedule saved successfully!")
                    else:
                        st.error(f"❌ Failed to save: {result.get('error')}")
                except Exception as e:
                    st.error(f"❌ Configuration error: {e}")
    
    with col2:
        st.markdown("### 🚀 Manual Discovery & Application")
        
        # Quick discovery with auto-apply
        discovery_preset = st.selectbox(
            "Discovery Preset",
            options=[
                "Tech Focus - Toronto/Vancouver",
                "All Major Cities - Comprehensive",
                "Remote-Friendly Positions",
                "Senior Level Positions",
                "Entry-Mid Level Focus"
            ],
            help="Pre-configured search targeting specific job types"
        )
        
        auto_apply_enabled = st.checkbox(
            "Auto-Apply After Discovery",
            value=False,
            help="Automatically trigger job applications for discovered positions"
        )
        
        if auto_apply_enabled:
            apply_delay = st.slider(
                "Application Delay (minutes)",
                min_value=5,
                max_value=60,
                value=15,
                help="Wait time between discovery and auto-application"
            )
            
            max_applications = st.number_input(
                "Max Applications",
                min_value=1,
                max_value=50,
                value=10,
                help="Maximum number of automatic applications per discovery session"
            )
        
        # Manual trigger buttons
        col2a, col2b = st.columns(2)
        
        with col2a:
            if st.button("🔍 Start Discovery", use_container_width=True):
                with st.spinner("Starting job discovery..."):
                    try:
                        discovery_config = {
                            "preset": discovery_preset,
                            "auto_apply": auto_apply_enabled,
                            "apply_delay": apply_delay if auto_apply_enabled else 0,
                            "max_applications": max_applications if auto_apply_enabled else 0
                        }
                        
                        result = orchestration_service.trigger_discovery_session(discovery_config)
                        
                        if result.get("success"):
                            session_id = result.get("session_id")
                            st.success(f"✅ Discovery started! Session: {session_id}")
                            
                            if auto_apply_enabled:
                                st.info(f"🔄 Auto-apply will trigger in {apply_delay} minutes")
                        else:
                            st.error(f"❌ Failed to start: {result.get('error')}")
                            
                    except Exception as e:
                        st.error(f"❌ Discovery error: {e}")
        
        with col2b:
            if st.button("⏹️ Stop Discovery", use_container_width=True):
                try:
                    result = orchestration_service.stop_discovery_session()
                    
                    if result.get("success"):
                        st.success("✅ Discovery stopped")
                    else:
                        st.warning(f"⚠️ {result.get('message', 'No active session')}")
                        
                except Exception as e:
                    st.error(f"❌ Stop error: {e}")
    
    st.markdown("---")
    
    # Real-time status monitoring
    st.markdown("### 📊 Live Status Monitoring")
    
    try:
        # Get current orchestration status
        orch_status = orchestration_service.get_orchestration_status()
        
        # Display active sessions
        active_sessions = orch_status.get("active_sessions", [])
        
        if active_sessions:
            st.markdown("**🔄 Active Sessions:**")
            
            for session in active_sessions:
                with st.expander(f"Session {session.get('id', 'Unknown')}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Status", session.get("status", "Unknown"))
                        st.metric("Progress", f"{session.get('progress', 0):.1%}")
                    
                    with col2:
                        st.metric("Jobs Found", session.get("jobs_found", 0))
                        st.metric("Applications", session.get("applications_sent", 0))
                    
                    with col3:
                        start_time = session.get("start_time", "Unknown")
                        if start_time != "Unknown":
                            try:
                                start_dt = datetime.fromisoformat(start_time)
                                elapsed = datetime.now() - start_dt
                                st.metric("Elapsed", f"{elapsed.seconds // 60}m {elapsed.seconds % 60}s")
                            except:
                                st.metric("Elapsed", "Unknown")
                        
                        estimated_completion = session.get("estimated_completion")
                        if estimated_completion:
                            st.metric("ETA", estimated_completion)
                    
                    # Session controls
                    if session.get("status") == "running":
                        if st.button(f"⏸️ Pause {session.get('id')}", key=f"pause_{session.get('id')}"):
                            orchestration_service.pause_session(session.get('id'))
                            st.rerun()
                    
                    elif session.get("status") == "paused":
                        if st.button(f"▶️ Resume {session.get('id')}", key=f"resume_{session.get('id')}"):
                            orchestration_service.resume_session(session.get('id'))
                            st.rerun()
        else:
            st.info("No active discovery sessions")
        
        # Queue status
        queue_status = orchestration_service.get_queue_status()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            discovery_queue = queue_status.get("discovery_queue", 0)
            st.metric("Discovery Queue", discovery_queue)
        
        with col2:
            processing_queue = queue_status.get("processing_queue", 0) 
            st.metric("Processing Queue", processing_queue)
        
        with col3:
            application_queue = queue_status.get("application_queue", 0)
            st.metric("Application Queue", application_queue)
        
        with col4:
            total_active = queue_status.get("total_active_jobs", 0)
            st.metric("Total Active", total_active)
        
    except Exception as e:
        st.error(f"❌ Status monitoring error: {e}")
    
    # Auto-refresh for live monitoring
    if st.checkbox("🔄 Auto-refresh (10s)", value=False):
        time.sleep(10)
        st.rerun()


def render_quick_launch():
    """Render quick launch presets for Canadian cities."""
    st.subheader("\U0001f680 Quick Launch Presets")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**Canadian Cities Presets**")
        
        # Preset selection
        preset_options = {
            "\U0001f1e8\U0001f1e6 Major Canadian Cities": "canadian_cities",
            "\U0001f30e Canada Comprehensive": "canada_comprehensive", 
            "\U0001f4bb Tech Hubs Only": "tech_hubs",
            "\U0001f3e2 Toronto Extended": "toronto",
            "\U0001f341 Quality Focused": "quality",
            "\u26a1 Fast Discovery": "fast",
            "\U0001f4ca Comprehensive": "comprehensive"
        }
        
        selected_preset = st.selectbox(
            "Choose Preset",
            options=list(preset_options.keys()),
            index=0,
            help="Pre-configured search settings optimized for different needs"
        )
        
        preset_key = preset_options[selected_preset]
        
        # Show preset details
        if preset_key in JOBSPY_CONFIG_PRESETS:
            config = JOBSPY_CONFIG_PRESETS[preset_key]()
            
            with st.expander("\U0001f4cb Preset Details", expanded=False):
                st.write(f"**Locations:** {len(config.jobspy_locations)} cities")
                if len(config.jobspy_locations) <= 10:
                    st.write("• " + "\n• ".join(config.jobspy_locations))
                else:
                    st.write("• " + "\n• ".join(config.jobspy_locations[:5]))
                    st.write(f"... and {len(config.jobspy_locations) - 5} more")
                
                st.write(f"**Search Terms:** {len(config.jobspy_search_terms)} terms")
                st.write("• " + "\n• ".join(config.jobspy_search_terms[:5]))
                if len(config.jobspy_search_terms) > 5:
                    st.write(f"... and {len(config.jobspy_search_terms) - 5} more")
                
                st.write(f"**Job Sites:** {', '.join(config.jobspy_sites)}")
                st.write(f"**Max Jobs:** {config.jobspy_max_jobs}")
    
    with col2:
        st.info("**Search Parameters**")
        
        # Additional parameters
        max_jobs = st.number_input(
            "Maximum Jobs",
            min_value=10,
            max_value=2000,
            value=500 if preset_key in ["canadian_cities", "canada_comprehensive"] else 100,
            step=50,
            help="Maximum number of jobs to find across all searches"
        )
        
        hours_old = st.selectbox(
            "Job Age (Hours)",
            options=[24, 48, 72, 168, 336, 720],  # 1 day to 30 days
            index=4,  # Default to 336 (14 days)
            format_func=lambda x: f"{x} hours ({x//24} days)" if x >= 24 else f"{x} hours",
            help="Maximum age of job postings to include"
        )
        
        jobspy_only = st.checkbox(
            "JobSpy Only (Fastest)",
            value=preset_key in ["canada_comprehensive"],
            help="Skip Eluta scraper for faster execution"
        )
        
        external_workers = st.slider(
            "Description Workers",
            min_value=2,
            max_value=12,
            value=8 if preset_key in ["canadian_cities", "canada_comprehensive"] else 6,
            help="Number of parallel workers for fetching job descriptions"
        )
        
        enable_processing = st.checkbox(
            "Enable AI Processing",
            value=True,
            help="Process jobs with OpenHermes 2.5 AI for compatibility scoring"
        )
    
    # Launch buttons
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        left, right = st.columns(2)
        with left:
            if st.button(
                f"\U0001f680 Launch {selected_preset}",
                type="primary",
                use_container_width=True,
                help=f"Start JobSpy search with {preset_key} preset via CLI"
            ):
                # Build command
                command = [
                    sys.executable, "main.py", "Nirajan",
                    "--action", "jobspy-pipeline",
                    "--jobspy-preset", preset_key,
                    "--max-jobs-total", str(max_jobs),
                    "--hours-old", str(hours_old),
                    "--external-workers", str(external_workers)
                ]
                
                if jobspy_only:
                    command.append("--jobspy-only")
                
                if not enable_processing:
                    command.extend(["--processing-method", "skip"])
                
                # Store command in session state for execution tracking
                st.session_state.jobspy_command = " ".join(command)
                st.session_state.jobspy_running = True
                st.session_state.jobspy_start_time = datetime.now()
                
                # Execute command
                execute_jobspy_command(command, selected_preset)
        with right:
            if HAS_ORCH and st.button(
                f"\U0001f527 Run via Orchestrator",
                use_container_width=True,
                help="Run discovery internally without launching CLI"
            ):
                cfg = OrchestratorConfig(
                    location_set=preset_key if preset_key in JOBSPY_LOCATION_SETS else "canada_comprehensive",
                    query_preset=preset_key if preset_key in JOBSPY_SEARCH_TERM_SETS else "comprehensive",
                    per_site_concurrency=4,
                    max_total_jobs=max_jobs,
                    fetch_descriptions=True,
                )
                summary = run_jobspy_discovery(cfg, "Nirajan")
                st.success(f"Discovered {summary.total_jobs} jobs (sites: {len(summary.dataframe_summary.get('sites', []))})")


def render_custom_search():
    """Render custom search configuration."""
    st.subheader("⚙️ Custom JobSpy Search")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Locations**")
        
        # Location set selection
        location_set = st.selectbox(
            "Base Location Set",
            options=list(JOBSPY_LOCATION_SETS.keys()),
            index=3,  # Default to major_canadian_cities
            help="Choose a base set of locations to search"
        )
        
        # Show selected locations
        selected_locations = JOBSPY_LOCATION_SETS[location_set]
        
        with st.expander(f"📍 {len(selected_locations)} Locations", expanded=False):
            # Allow users to select/deselect locations
            location_selections = {}
            for i, location in enumerate(selected_locations):
                location_selections[location] = st.checkbox(
                    location,
                    value=True,
                    key=f"loc_{i}"
                )
        
        # Custom locations
        custom_locations = st.text_area(
            "Additional Locations",
            placeholder="Enter additional locations (one per line)\nExample:\nOttawa, ON\nWaterloo, ON",
            help="Add custom locations not in the preset lists"
        )
        
        # Build final location list
        final_locations = [loc for loc, selected in location_selections.items() if selected]
        if custom_locations.strip():
            final_locations.extend([loc.strip() for loc in custom_locations.strip().split('\n') if loc.strip()])
    
    with col2:
        st.write("**Search Terms & Sites**")
        
        # Search term set selection
        term_set = st.multiselect(
            "Search Term Sets",
            options=list(JOBSPY_SEARCH_TERM_SETS.keys()),
            default=["python_focused", "general_development"],
            help="Choose categories of search terms"
        )
        
        # Build search terms
        search_terms = []
        for ts in term_set:
            search_terms.extend(JOBSPY_SEARCH_TERM_SETS[ts])
        
        # Remove duplicates while preserving order
        search_terms = list(dict.fromkeys(search_terms))
        
        with st.expander(f"🔍 {len(search_terms)} Search Terms", expanded=False):
            st.write("• " + "\n• ".join(search_terms))
        
        # Custom search terms
        custom_terms = st.text_area(
            "Additional Search Terms",
            placeholder="Enter additional search terms (one per line)\nExample:\ndata scientist\nmachine learning engineer",
            help="Add custom search terms"
        )
        
        if custom_terms.strip():
            search_terms.extend([term.strip() for term in custom_terms.strip().split('\n') if term.strip()])
        
        # Site selection
        site_combination = st.selectbox(
            "Job Sites",
            options=list(JOBSPY_SITE_COMBINATIONS.keys()),
            index=2,  # Default to comprehensive
            help="Choose which job sites to search"
        )
        
        selected_sites = JOBSPY_SITE_COMBINATIONS[site_combination]
        st.write(f"**Sites:** {', '.join(selected_sites)}")
    
    # Improved parameters
    st.divider()
    st.write("**Improved Parameters**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        max_jobs = st.number_input("Max Jobs", min_value=10, max_value=2000, value=300, step=25)
        hours_old = st.number_input("Hours Old", min_value=1, max_value=720, value=336, step=24)
    
    with col2:
        external_workers = st.slider("External Workers", min_value=2, max_value=12, value=8)
        processing_method = st.selectbox("Processing Method", ["auto", "gpu", "hybrid", "rule_based"])
    
    with col3:
        jobspy_only = st.checkbox("JobSpy Only", value=False)
        enable_dedup = st.checkbox("Enable Deduplication", value=True)
    
    # Launch custom search
    st.divider()
    
    if st.button("🚀 Launch Custom Search", type="primary", use_container_width=True):
        if not final_locations:
            st.error("Please select at least one location.")
            return
        
        if not search_terms:
            st.error("Please select at least one search term.")
            return
        
        # Create custom configuration and launch
        st.success(f"Launching custom search with {len(final_locations)} locations and {len(search_terms)} search terms...")
        
        # Build command for custom search
        command = [
            sys.executable, "main.py", "Nirajan",
            "--action", "jobspy-pipeline",
            "--max-jobs-total", str(max_jobs),
            "--hours-old", str(hours_old),
            "--external-workers", str(external_workers),
            "--processing-method", processing_method
        ]
        
        if jobspy_only:
            command.append("--jobspy-only")
        
        # Store custom config in session state
        st.session_state.custom_jobspy_config = {
            "locations": final_locations,
            "search_terms": search_terms,
            "sites": selected_sites,
            "max_jobs": max_jobs,
            "hours_old": hours_old
        }
        
        st.session_state.jobspy_command = " ".join(command)
        st.session_state.jobspy_running = True
        st.session_state.jobspy_start_time = datetime.now()
        
        execute_jobspy_command(command, "Custom Search")


def render_search_history():
    """Render search history and results."""
    st.subheader("📊 JobSpy Search History")
    
    # Check if there's a running search
    if st.session_state.get('jobspy_running', False):
        st.info("🔄 JobSpy search is currently running...")
        
        if 'jobspy_start_time' in st.session_state:
            elapsed = datetime.now() - st.session_state.jobspy_start_time
            st.write(f"⏱️ Elapsed time: {str(elapsed).split('.')[0]}")
        
        if 'jobspy_command' in st.session_state:
            with st.expander("Command Details", expanded=False):
                st.code(st.session_state.jobspy_command, language="bash")
        
        # Add stop button
        if st.button("⏹️ Stop Search", type="secondary"):
            st.session_state.jobspy_running = False
            st.warning("Search stopped by user.")
    else:
        st.success("✅ No active JobSpy searches.")
    
    # Show recent results from database
    try:
        # Import database here to avoid circular imports
        from core.job_database import get_job_db
        
        profile_name = "Nirajan"  # TODO: Make this configurable
        db = get_job_db(profile_name)
        
        # Get recent JobSpy jobs
        recent_jobs = db.get_jobs_by_status("scraped", limit=50)
        jobspy_jobs = [job for job in recent_jobs if job.get('data_source') == 'jobspy']
        
        if jobspy_jobs:
            st.subheader(f"📋 Recent JobSpy Results ({len(jobspy_jobs)} jobs)")
            
            # Convert to DataFrame for display
            df = pd.DataFrame(jobspy_jobs)
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Jobs", len(df))
            
            with col2:
                unique_companies = df['company'].nunique() if 'company' in df.columns else 0
                st.metric("Companies", unique_companies)
            
            with col3:
                unique_locations = df['location'].nunique() if 'location' in df.columns else 0
                st.metric("Locations", unique_locations)
            
            with col4:
                recent_count = len(df[df['created_at'] > (datetime.now() - timedelta(hours=24)).isoformat()]) if 'created_at' in df.columns else 0
                st.metric("Last 24h", recent_count)
            
            # Display jobs table
            display_columns = ['title', 'company', 'location', 'search_term', 'created_at']
            display_df = df[display_columns].copy() if all(col in df.columns for col in display_columns) else df
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No JobSpy results found. Run a search to see results here.")
    
    except Exception as e:
        st.error(f"Error loading search history: {e}")


def render_configuration_info():
    """Render JobSpy configuration information."""
    st.subheader("📋 JobSpy Configuration")
    
    # Available presets
    st.write("**Available Presets:**")
    
    preset_info = {
        "🇨🇦 Canadian Cities": {
            "preset": "canadian_cities",
            "locations": len(JOBSPY_LOCATION_SETS["major_canadian_cities"]),
            "description": "Major metropolitan areas across Canada including Toronto, Vancouver, Calgary, Edmonton, Ottawa, Waterloo, Halifax, Kitchener"
        },
        "🌎 Canada Comprehensive": {
            "preset": "canada_comprehensive",
            "locations": len(JOBSPY_LOCATION_SETS["canada_comprehensive"]),
            "description": "All major cities and provinces for maximum job coverage"
        },
        "💻 Tech Hubs": {
            "preset": "tech_hubs",
            "locations": len(JOBSPY_LOCATION_SETS["tech_hubs_canada"]),
            "description": "Focus on Canadian technology centers and innovation hubs"
        },
        "🏢 Toronto Extended": {
            "preset": "toronto",
            "locations": len(JOBSPY_LOCATION_SETS["toronto_extended"]),
            "description": "Greater Toronto Area including Mississauga, Brampton, Markham"
        },
        "⚡ Fast Discovery": {
            "preset": "fast",
            "locations": 5,
            "description": "Quick search for immediate results"
        },
        "📊 Comprehensive": {
            "preset": "comprehensive",
            "locations": 12,
            "description": "Balanced search with good coverage and quality"
        }
    }
    
    for name, info in preset_info.items():
        with st.expander(name, expanded=False):
            st.write(f"**Preset Key:** `{info['preset']}`")
            st.write(f"**Locations:** {info['locations']} cities")
            st.write(f"**Description:** {info['description']}")
            
            # Show command example
            st.code(f"python main.py Nirajan --action jobspy-pipeline --jobspy-preset {info['preset']}", language="bash")
    
    # Location sets info
    st.divider()
    st.write("**Available Location Sets:**")
    
    for set_name, locations in JOBSPY_LOCATION_SETS.items():
        with st.expander(f"{set_name} ({len(locations)} locations)", expanded=False):
            st.write("• " + "\n• ".join(locations))
    
    # Search term sets info
    st.divider()
    st.write("**Available Search Term Sets:**")
    
    for set_name, terms in JOBSPY_SEARCH_TERM_SETS.items():
        with st.expander(f"{set_name} ({len(terms)} terms)", expanded=False):
            st.write("• " + "\n• ".join(terms))


def execute_jobspy_command(command: List[str], search_name: str):
    """Execute JobSpy command and show progress."""
    try:
        # Show command being executed
        with st.expander("🔧 Command Details", expanded=True):
            st.code(" ".join(command), language="bash")
        
        # Create progress placeholder
        progress_placeholder = st.empty()
        
        with progress_placeholder.container():
            st.info(f"🚀 Starting {search_name}...")
            
            # Execute command
            with st.spinner("Running JobSpy search..."):
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    cwd=os.path.join(os.path.dirname(__file__), "..", "..", ".."),
                    timeout=3600  # 1 hour timeout
                )
            
            # Show results
            if result.returncode == 0:
                st.success(f"✅ {search_name} completed successfully!")
                
                if result.stdout:
                    with st.expander("📋 Output", expanded=False):
                        st.text(result.stdout)
            else:
                st.error(f"❌ {search_name} failed with exit code {result.returncode}")
                
                if result.stderr:
                    with st.expander("❌ Error Details", expanded=True):
                        st.text(result.stderr)
                
                if result.stdout:
                    with st.expander("📋 Output", expanded=False):
                        st.text(result.stdout)
        
        # Clear running status
        st.session_state.jobspy_running = False
        
        # Refresh page to show new results
        st.rerun()
    
    except subprocess.TimeoutExpired:
        st.error("⏰ JobSpy search timed out after 1 hour.")
        st.session_state.jobspy_running = False
    
    except Exception as e:
        st.error(f"❌ Error executing JobSpy command: {e}")
        st.session_state.jobspy_running = False


def show_jobspy_status():
    """Show JobSpy status in sidebar."""
    if st.session_state.get('jobspy_running', False):
        st.sidebar.warning("🔄 JobSpy Running")
        
        if 'jobspy_start_time' in st.session_state:
            elapsed = datetime.now() - st.session_state.jobspy_start_time
            st.sidebar.write(f"⏱️ {str(elapsed).split('.')[0]}")
    else:
        st.sidebar.success("✅ JobSpy Ready")


# Export functions for use in main dashboard
__all__ = ['render_jobspy_control', 'show_jobspy_status']
