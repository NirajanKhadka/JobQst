"""
Document Generation Component for AutoJobAgent Dashboard
Provides UI interface for the Automated document generation service.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from src.services.document_generator import DocumentGenerator
    from src.utils.profile_helpers import load_profile, get_profile_path
    HAS_DOCUMENT_GENERATOR = True
except ImportError as e:
    HAS_DOCUMENT_GENERATOR = False
    DocumentGenerator = None
    load_profile = None


class DocumentGenerationComponent:
    """Dashboard component for AI document generation."""
    
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.profile = None
        self._load_profile()
    
    def _load_profile(self):
        """Load the user profile."""
        if HAS_DOCUMENT_GENERATOR:
            try:
                self.profile = load_profile(self.profile_name)
                if self.profile:
                    self.profile["profile_name"] = self.profile_name
            except Exception as e:
                st.error(f"Failed to load profile: {e}")
    
    def render(self):
        """Render the complete document generation interface."""
        if not HAS_DOCUMENT_GENERATOR:
            st.error("❌ Document Generator service not available")
            st.info("Please ensure the document generator service is properly installed.")
            return
            
        if not self.profile:
            st.error(f"❌ Profile '{self.profile_name}' not found")
            return
        
        st.header("📄 AI Document Generation")
        
        # Quick info section
        self._render_profile_info()
        
        # Action buttons section
        self._render_action_buttons()
        
        # Status section
        self._render_status_section()
        
        # Generated documents viewer
        self._render_document_viewer()
    
    def _render_profile_info(self):
        """Render profile information."""
        with st.expander("👤 Profile Information", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Name:** {self.profile.get('name', 'Not set')}")
                st.write(f"**Email:** {self.profile.get('email', 'Not set')}")
                st.write(f"**Location:** {self.profile.get('location', 'Not set')}")
            
            with col2:
                skills = self.profile.get('skills', [])
                keywords = self.profile.get('keywords', [])
                st.write(f"**Skills:** {', '.join(skills[:5])}{'...' if len(skills) > 5 else ''}")
                st.write(f"**Keywords:** {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}")
                st.write(f"**Experience Level:** {self.profile.get('experience_level', 'Entry Level')}")
    
    def _render_action_buttons(self):
        """Render action buttons for document generation."""
        st.subheader("🚀 Generate Documents")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🤖 Generate ALL Documents", 
                        help="Generate all 8 documents (4 resumes + 4 cover letters) using AI workers",
                        type="primary"):
                self._start_generation_all()
        
        with col2:
            if st.button("📝 Resumes Only", 
                        help="Generate 4 resume styles only"):
                self._start_generation_resumes()
        
        with col3:
            if st.button("💌 Cover Letters Only", 
                        help="Generate 4 cover letter styles only"):
                self._start_generation_cover_letters()
        
        # Improved options
        with st.expander("🎯 Improved Options", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                style_type = st.selectbox("Document Type", ["resume", "cover_letter"])
                
                if style_type == "resume":
                    style = st.selectbox("Resume Style", 
                                       ["professional", "technical", "creative", "minimalist"])
                else:
                    style = st.selectbox("Cover Letter Style", 
                                       ["standard", "enthusiastic", "technical", "concise"])
                
                if st.button(f"Generate {style.title()} {style_type.replace('_', ' ').title()}"):
                    self._start_generation_single(style_type, style)
            
            with col2:
                st.write("**Worker Settings**")
                max_workers = st.slider("Max Workers", 1, 5, 5, 
                                      help="Number of AI workers for parallel processing")
                
                if st.button("🔄 Regenerate All", 
                           help="Regenerate all documents with Improved prompts"):
                    self._start_regeneration(max_workers)
    
    def _render_status_section(self):
        """Render generation status."""
        st.subheader("📊 Generation Status")
        
        # Check if generation is in progress
        if 'generation_in_progress' in st.session_state and st.session_state.generation_in_progress:
            st.info("🔄 Document generation in progress...")
            
            # Progress placeholder
            progress_placeholder = st.empty()
            with progress_placeholder.container():
                st.progress(0.5)  # Indeterminate progress
                st.text("AI workers are generating documents...")
            
            # Auto-refresh to check status
            time.sleep(1)
            st.rerun()
        else:
            # Show last generation info
            self._show_last_generation_info()
    
    def _render_document_viewer(self):
        """Render document viewer section."""
        st.subheader("📁 Generated Documents")
        
        try:
            profile_path = get_profile_path(self.profile_name)
            if not profile_path:
                st.warning("❌ Profile path not found")
                return
            
            # Check main documents
            main_files = [
                f"{self.profile_name}_Resume.pdf",
                f"{self.profile_name}_CoverLetter.pdf",
                f"{self.profile_name}_Khadka_Resume.pdf",
                f"{self.profile_name}_Khadka_CoverLetter.pdf"
            ]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📄 Main Documents (Ready for Applications)**")
                for file_name in main_files:
                    file_path = profile_path / file_name
                    if file_path.exists():
                        size = file_path.stat().st_size
                        st.success(f"✅ {file_name} ({size:,} bytes)")
                        
                        # Download button
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label=f"⬇️ Download",
                                data=f.read(),
                                file_name=file_name,
                                mime="application/pdf",
                                key=f"download_{file_name}"
                            )
                    else:
                        st.info(f"⏳ {file_name} - Not generated yet")
            
            with col2:
                st.write("**📁 Document Variations**")
                generated_dir = profile_path / "generated_documents"
                
                if generated_dir.exists():
                    # Count documents
                    resume_files = list(generated_dir.glob("resume_*.pdf"))
                    cover_files = list(generated_dir.glob("cover_letter_*.pdf"))
                    
                    st.metric("Resume Styles", len(resume_files), "📝")
                    st.metric("Cover Letter Styles", len(cover_files), "💌")
                    
                    # Expandable file list
                    with st.expander("View All Variations"):
                        all_files = list(generated_dir.glob("*.pdf"))
                        for file_path in sorted(all_files):
                            size = file_path.stat().st_size
                            st.text(f"📄 {file_path.name} ({size:,} bytes)")
                else:
                    st.info("📁 No generated documents directory found")
                    
        except Exception as e:
            st.error(f"❌ Error loading documents: {e}")
    
    def _show_last_generation_info(self):
        """Show information about the last generation."""
        # Simple status display
        col1, col2, col3 = st.columns(3)
        
        try:
            profile_path = get_profile_path(self.profile_name)
            if profile_path:
                generated_dir = profile_path / "generated_documents"
                
                if generated_dir.exists():
                    # Count existing documents
                    txt_files = len(list(generated_dir.glob("*.txt")))
                    pdf_files = len(list(generated_dir.glob("*.pdf")))
                    
                    with col1:
                        st.metric("TXT Documents", txt_files, "📄")
                    with col2:
                        st.metric("PDF Documents", pdf_files, "📄")
                    with col3:
                        completion = (pdf_files / 8 * 100) if pdf_files > 0 else 0
                        st.metric("Completion", f"{completion:.0f}%", "✅")
                else:
                    st.info("ℹ️ No documents generated yet")
        except Exception as e:
            st.warning(f"Could not load document status: {e}")
    
    def _start_generation_all(self):
        """Start generation of all documents."""
        try:
            generator = DocumentGenerator(self.profile)
            
            st.session_state.generation_in_progress = True
            
            with st.spinner("🤖 Starting AI workers for document generation..."):
                # Run in background thread to avoid blocking UI
                def generate_docs():
                    try:
                        generator.generate_documents_with_workers(max_workers=5)
                        st.session_state.generation_in_progress = False
                        st.session_state.last_generation = {
                            'type': 'all_documents',
                            'status': 'completed',
                            'timestamp': datetime.now()
                        }
                    except Exception as e:
                        st.session_state.generation_in_progress = False
                        st.session_state.last_generation = {
                            'type': 'all_documents',
                            'status': 'failed',
                            'error': str(e),
                            'timestamp': datetime.now()
                        }
                
                # Start generation in thread
                thread = threading.Thread(target=generate_docs)
                thread.daemon = True
                thread.start()
                
                st.success("🚀 Document generation started! Workers are processing...")
                st.info("💡 Generation will complete in ~2-3 minutes. The page will update automatically.")
                
        except Exception as e:
            st.error(f"❌ Failed to start generation: {e}")
            st.session_state.generation_in_progress = False
    
    def _start_generation_resumes(self):
        """Start generation of resumes only."""
        try:
            generator = DocumentGenerator(self.profile)
            
            with st.spinner("📝 Generating resume documents..."):
                generator._generate_resume_documents_only()
                
            st.success("✅ Resume documents generated successfully!")
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ Failed to generate resumes: {e}")
    
    def _start_generation_cover_letters(self):
        """Start generation of cover letters only."""
        try:
            generator = DocumentGenerator(self.profile)
            
            with st.spinner("💌 Generating cover letter documents..."):
                generator._generate_cover_letter_documents_only()
                
            st.success("✅ Cover letter documents generated successfully!")
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ Failed to generate cover letters: {e}")
    
    def _start_generation_single(self, doc_type: str, style: str):
        """Start generation of a single document."""
        try:
            generator = DocumentGenerator(self.profile)
            output_dir = generator._get_output_dir()
            
            # Get style description
            style_descriptions = {
                "resume": {
                    "professional": "a standard, professional resume",
                    "technical": "a resume focused on technical skills and projects",
                    "creative": "a modern, creative-style resume",
                    "minimalist": "a clean, minimalist resume"
                },
                "cover_letter": {
                    "standard": "a standard, formal cover letter",
                    "enthusiastic": "a cover letter with an enthusiastic and passionate tone",
                    "technical": "a cover letter highlighting technical achievements",
                    "concise": "a brief and to-the-point cover letter"
                }
            }
            
            description = style_descriptions[doc_type][style]
            
            with st.spinner(f"🎯 Generating {style} {doc_type.replace('_', ' ')}..."):
                success = generator._generate_single_document(doc_type, style, description, output_dir)
                
            if success:
                st.success(f"✅ {style.title()} {doc_type.replace('_', ' ')} generated successfully!")
            else:
                st.error(f"❌ Failed to generate {style} {doc_type.replace('_', ' ')}")
                
        except Exception as e:
            st.error(f"❌ Generation failed: {e}")
    
    def _start_regeneration(self, max_workers: int):
        """Start regeneration of all documents."""
        try:
            generator = DocumentGenerator(self.profile)
            
            st.session_state.generation_in_progress = True
            
            with st.spinner("🔄 Regenerating all documents with Improved prompts..."):
                def regenerate_docs():
                    try:
                        generator.generate_documents_with_workers(max_workers=max_workers)
                        st.session_state.generation_in_progress = False
                        st.session_state.last_generation = {
                            'type': 'regeneration',
                            'status': 'completed',
                            'timestamp': datetime.now()
                        }
                    except Exception as e:
                        st.session_state.generation_in_progress = False
                        st.session_state.last_generation = {
                            'type': 'regeneration',
                            'status': 'failed',
                            'error': str(e),
                            'timestamp': datetime.now()
                        }
                
                # Start regeneration in thread
                thread = threading.Thread(target=regenerate_docs)
                thread.daemon = True
                thread.start()
                
                st.success("🔄 Document regeneration started!")
                st.info("💡 Regeneration will complete in ~2-3 minutes.")
                
        except Exception as e:
            st.error(f"❌ Failed to start regeneration: {e}")
            st.session_state.generation_in_progress = False


def render_document_generation_tab(profile_name: str):
    """Render the document generation tab (for integration into dashboard)."""
    doc_component = DocumentGenerationComponent(profile_name)
    doc_component.render()


# For standalone testing
if __name__ == "__main__":
    st.set_page_config(
        page_title="Document Generation Test",
        page_icon="📄",
        layout="wide"
    )
    
    # Test the component
    profile_name = st.sidebar.selectbox("Profile", ["Nirajan", "default"])
    render_document_generation_tab(profile_name)
