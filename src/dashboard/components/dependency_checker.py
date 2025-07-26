"""
Dependency Checker for Enhanced Dashboard Components
Checks for optional dependencies and provides installation guidance
"""

import streamlit as st
import importlib
import subprocess
import sys
from typing import Dict, List, Tuple

def check_optional_dependencies() -> Dict[str, bool]:
    """Check availability of optional dependencies for enhanced features."""
    
    dependencies = {
        'st_aggrid': False,
        'streamlit_elements': False,
        'streamlit_autorefresh': False,
        'plotly': False,
        'numpy': False,
        'pandas': False
    }
    
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            dependencies[dep] = True
        except ImportError:
            dependencies[dep] = False
    
    return dependencies

def get_missing_dependencies() -> List[str]:
    """Get list of missing optional dependencies."""
    deps = check_optional_dependencies()
    return [dep for dep, available in deps.items() if not available]

def get_installation_commands() -> Dict[str, str]:
    """Get pip installation commands for optional dependencies."""
    return {
        'st_aggrid': 'pip install streamlit-aggrid',
        'streamlit_elements': 'pip install streamlit-elements',
        'streamlit_autorefresh': 'pip install streamlit-autorefresh',
        'plotly': 'pip install plotly',
        'numpy': 'pip install numpy',
        'pandas': 'pip install pandas'
    }

def render_dependency_status() -> None:
    """Render dependency status in sidebar."""
    
    deps = check_optional_dependencies()
    missing = get_missing_dependencies()
    
    if not missing:
        st.sidebar.success("✅ All enhanced features available!")
        return
    
    st.sidebar.warning(f"⚠️ {len(missing)} optional dependencies missing")
    
    with st.sidebar.expander("📦 Dependency Status"):
        for dep, available in deps.items():
            status = "✅" if available else "❌"
            st.write(f"{status} {dep}")
        
        if missing:
            st.markdown("**Install missing dependencies:**")
            install_commands = get_installation_commands()
            
            for dep in missing:
                if dep in install_commands:
                    st.code(install_commands[dep])

def install_dependency(package_name: str) -> bool:
    """Install a dependency using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def render_enhancement_installer() -> None:
    """Render enhancement installer interface."""
    
    st.markdown("### 🚀 Dashboard Enhancements")
    
    missing = get_missing_dependencies()
    
    if not missing:
        st.success("✅ All enhancements are available!")
        return
    
    st.info(f"📦 {len(missing)} optional packages can enhance your dashboard experience")
    
    install_commands = get_installation_commands()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("**Available Enhancements:**")
        
        enhancements = {
            'st_aggrid': '📊 Advanced interactive tables with sorting, filtering, and selection',
            'streamlit_elements': '🎨 Modern UI components and layouts',
            'streamlit_autorefresh': '🔄 Automatic dashboard refresh capabilities',
            'plotly': '📈 Interactive charts and visualizations',
            'numpy': '🔢 Advanced numerical computations',
            'pandas': '📋 Enhanced data manipulation'
        }
        
        for dep in missing:
            if dep in enhancements:
                st.markdown(f"• **{dep}**: {enhancements[dep]}")
    
    with col2:
        if st.button("📦 Install All", key="install_all_deps"):
            with st.spinner("Installing enhancements..."):
                success_count = 0
                for dep in missing:
                    if dep in install_commands:
                        package = install_commands[dep].split()[-1]  # Extract package name
                        if install_dependency(package):
                            success_count += 1
                
                if success_count == len(missing):
                    st.success("✅ All enhancements installed!")
                    st.experimental_rerun()
                else:
                    st.warning(f"⚠️ {success_count}/{len(missing)} enhancements installed")
    
    # Individual installation
    st.markdown("**Or install individually:**")
    
    for dep in missing:
        if dep in install_commands:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.code(install_commands[dep])
            
            with col2:
                if st.button("Install", key=f"install_{dep}"):
                    package = install_commands[dep].split()[-1]
                    with st.spinner(f"Installing {package}..."):
                        if install_dependency(package):
                            st.success(f"✅ {package} installed!")
                            st.experimental_rerun()
                        else:
                            st.error(f"❌ Failed to install {package}")

def get_feature_availability() -> Dict[str, bool]:
    """Get availability status of enhanced features."""
    deps = check_optional_dependencies()
    
    return {
        'enhanced_tables': deps['st_aggrid'],
        'modern_ui': deps['streamlit_elements'],
        'auto_refresh': deps['streamlit_autorefresh'],
        'advanced_charts': deps['plotly'],
        'data_analysis': deps['numpy'] and deps['pandas']
    }