"""
CUDA Setup and Detection Utility
Handles CUDA_HOME detection and environment setup following DEVELOPMENT_STANDARDS.md
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CudaInfo:
    """CUDA installation information."""
    cuda_home: Optional[str]
    version: Optional[str]
    available: bool
    gpu_count: int
    gpu_names: List[str]
    error_message: Optional[str]

class CudaSetupError(Exception):
    """Custom exception for CUDA setup errors."""
    pass

class CudaDetector:
    """
    CUDA detection and setup utility.
    
    Follows DEVELOPMENT_STANDARDS.md:
    - Defensive programming with input validation
    - Graceful error handling with context
    - Clear logging at appropriate levels
    - No hardcoded paths - uses environment detection
    """
    
    def __init__(self):
        """Initialize CUDA detector."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._cuda_info: Optional[CudaInfo] = None
    
    def detect_cuda_installation(self) -> CudaInfo:
        """
        Detect CUDA installation and return comprehensive information.
        
        Returns:
            CudaInfo with detection results
        """
        if self._cuda_info is not None:
            return self._cuda_info
        
        self.logger.info("🔍 Detecting CUDA installation...")
        
        try:
            # Check CUDA_HOME environment variable
            cuda_home = self._detect_cuda_home()
            
            # Check CUDA version
            cuda_version = self._detect_cuda_version()
            
            # Check GPU availability
            gpu_info = self._detect_gpu_info()
            
            # Determine overall availability
            cuda_available = (
                cuda_home is not None and 
                cuda_version is not None and 
                len(gpu_info['gpu_names']) > 0
            )
            
            self._cuda_info = CudaInfo(
                cuda_home=cuda_home,
                version=cuda_version,
                available=cuda_available,
                gpu_count=gpu_info['gpu_count'],
                gpu_names=gpu_info['gpu_names'],
                error_message=None
            )
            
            if cuda_available:
                self.logger.info(f"✅ CUDA detected: {cuda_version} at {cuda_home}")
                self.logger.info(f"🎯 GPUs found: {', '.join(gpu_info['gpu_names'])}")
            else:
                self.logger.warning("⚠️ CUDA not fully available")
            
            return self._cuda_info
            
        except Exception as e:
            error_msg = f"CUDA detection failed: {e}"
            self.logger.error(error_msg)
            
            self._cuda_info = CudaInfo(
                cuda_home=None,
                version=None,
                available=False,
                gpu_count=0,
                gpu_names=[],
                error_message=error_msg
            )
            
            return self._cuda_info
    
    def _detect_cuda_home(self) -> Optional[str]:
        """
        Detect CUDA_HOME from environment or common installation paths.
        
        Returns:
            CUDA_HOME path if found, None otherwise
        """
        # Check environment variable first
        cuda_home = os.environ.get('CUDA_HOME')
        if cuda_home and Path(cuda_home).exists():
            self.logger.debug(f"Found CUDA_HOME from environment: {cuda_home}")
            return cuda_home
        
        # Check CUDA_PATH (Windows alternative)
        cuda_path = os.environ.get('CUDA_PATH')
        if cuda_path and Path(cuda_path).exists():
            self.logger.debug(f"Found CUDA_PATH from environment: {cuda_path}")
            return cuda_path
        
        # Check common installation paths
        common_paths = self._get_common_cuda_paths()
        
        for path in common_paths:
            if Path(path).exists():
                # Verify it's a valid CUDA installation
                if self._is_valid_cuda_installation(path):
                    self.logger.debug(f"Found CUDA installation at: {path}")
                    return path
        
        self.logger.warning("CUDA_HOME not found in environment or common paths")
        return None
    
    def _get_common_cuda_paths(self) -> List[str]:
        """Get list of common CUDA installation paths by platform."""
        import platform
        
        system = platform.system().lower()
        
        if system == "windows":
            # Windows common paths
            program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
            return [
                f"{program_files}\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.0",
                f"{program_files}\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.8",
                f"{program_files}\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7",
                f"{program_files}\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.6",
                "C:\\cuda",
                "C:\\Program Files\\NVIDIA Corporation\\CUDA",
            ]
        elif system == "linux":
            # Linux common paths
            return [
                "/usr/local/cuda",
                "/usr/local/cuda-12.0",
                "/usr/local/cuda-11.8",
                "/usr/local/cuda-11.7",
                "/opt/cuda",
                "/usr/cuda",
            ]
        elif system == "darwin":
            # macOS common paths
            return [
                "/usr/local/cuda",
                "/Developer/NVIDIA/CUDA-12.0",
                "/Developer/NVIDIA/CUDA-11.8",
            ]
        else:
            self.logger.warning(f"Unknown platform: {system}")
            return []
    
    def _is_valid_cuda_installation(self, path: str) -> bool:
        """
        Verify if path contains a valid CUDA installation.
        
        Args:
            path: Path to check
            
        Returns:
            True if valid CUDA installation, False otherwise
        """
        try:
            cuda_path = Path(path)
            
            # Check for essential CUDA directories/files
            required_items = [
                "bin",
                "include",
                "lib",
            ]
            
            for item in required_items:
                if not (cuda_path / item).exists():
                    return False
            
            # Check for nvcc compiler
            nvcc_paths = [
                cuda_path / "bin" / "nvcc",
                cuda_path / "bin" / "nvcc.exe",
            ]
            
            if not any(nvcc_path.exists() for nvcc_path in nvcc_paths):
                return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Error validating CUDA path {path}: {e}")
            return False
    
    def _detect_cuda_version(self) -> Optional[str]:
        """
        Detect CUDA version using nvcc or nvidia-smi.
        
        Returns:
            CUDA version string if detected, None otherwise
        """
        # Try nvcc first
        version = self._get_version_from_nvcc()
        if version:
            return version
        
        # Try nvidia-smi as fallback
        version = self._get_version_from_nvidia_smi()
        if version:
            return version
        
        self.logger.warning("Could not detect CUDA version")
        return None
    
    def _get_version_from_nvcc(self) -> Optional[str]:
        """Get CUDA version from nvcc compiler."""
        try:
            result = subprocess.run(
                ['nvcc', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse version from nvcc output
                output = result.stdout
                for line in output.split('\n'):
                    if 'release' in line.lower():
                        # Extract version number (e.g., "release 11.8, V11.8.89")
                        import re
                        match = re.search(r'release\s+(\d+\.\d+)', line)
                        if match:
                            return match.group(1)
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.debug(f"nvcc not available: {e}")
        except Exception as e:
            self.logger.debug(f"Error getting version from nvcc: {e}")
        
        return None
    
    def _get_version_from_nvidia_smi(self) -> Optional[str]:
        """Get CUDA version from nvidia-smi."""
        try:
            result = subprocess.run(
                ['nvidia-smi'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse CUDA version from nvidia-smi output
                output = result.stdout
                for line in output.split('\n'):
                    if 'CUDA Version:' in line:
                        # Extract version (e.g., "CUDA Version: 11.8")
                        import re
                        match = re.search(r'CUDA Version:\s+(\d+\.\d+)', line)
                        if match:
                            return match.group(1)
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.debug(f"nvidia-smi not available: {e}")
        except Exception as e:
            self.logger.debug(f"Error getting version from nvidia-smi: {e}")
        
        return None
    
    def _detect_gpu_info(self) -> Dict[str, Any]:
        """
        Detect GPU information using nvidia-smi.
        
        Returns:
            Dictionary with GPU count and names
        """
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                gpu_names = [name.strip() for name in result.stdout.strip().split('\n') if name.strip()]
                return {
                    'gpu_count': len(gpu_names),
                    'gpu_names': gpu_names
                }
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.debug(f"nvidia-smi not available for GPU detection: {e}")
        except Exception as e:
            self.logger.debug(f"Error detecting GPU info: {e}")
        
        return {'gpu_count': 0, 'gpu_names': []}
    
    def setup_cuda_environment(self) -> bool:
        """
        Setup CUDA environment variables if CUDA is detected.
        
        Returns:
            True if setup successful, False otherwise
        """
        cuda_info = self.detect_cuda_installation()
        
        if not cuda_info.available or not cuda_info.cuda_home:
            self.logger.warning("Cannot setup CUDA environment - CUDA not available")
            return False
        
        try:
            # Set CUDA_HOME if not already set
            if not os.environ.get('CUDA_HOME'):
                os.environ['CUDA_HOME'] = cuda_info.cuda_home
                self.logger.info(f"Set CUDA_HOME={cuda_info.cuda_home}")
            
            # Set CUDA_PATH for Windows compatibility
            if not os.environ.get('CUDA_PATH'):
                os.environ['CUDA_PATH'] = cuda_info.cuda_home
                self.logger.info(f"Set CUDA_PATH={cuda_info.cuda_home}")
            
            # Add CUDA bin to PATH if not present
            cuda_bin = str(Path(cuda_info.cuda_home) / "bin")
            current_path = os.environ.get('PATH', '')
            
            if cuda_bin not in current_path:
                os.environ['PATH'] = f"{cuda_bin}{os.pathsep}{current_path}"
                self.logger.info(f"Added {cuda_bin} to PATH")
            
            self.logger.info("✅ CUDA environment setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup CUDA environment: {e}")
            return False
    
    def get_setup_instructions(self) -> List[str]:
        """
        Get setup instructions for CUDA installation.
        
        Returns:
            List of setup instruction strings
        """
        cuda_info = self.detect_cuda_installation()
        
        if cuda_info.available:
            return [
                "✅ CUDA is properly installed and configured",
                f"CUDA Version: {cuda_info.version}",
                f"CUDA Home: {cuda_info.cuda_home}",
                f"GPUs: {', '.join(cuda_info.gpu_names)}"
            ]
        
        instructions = [
            "❌ CUDA setup required for ExLlamaV2:",
            "",
            "1. Install NVIDIA GPU drivers:",
            "   - Download from: https://www.nvidia.com/drivers/",
            "",
            "2. Install CUDA Toolkit:",
            "   - Download from: https://developer.nvidia.com/cuda-downloads",
            "   - Recommended version: CUDA 11.8 or 12.0",
            "",
            "3. Set environment variables:",
            "   - CUDA_HOME=C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.8",
            "   - Add %CUDA_HOME%\\bin to PATH",
            "",
            "4. Verify installation:",
            "   - Run: nvcc --version",
            "   - Run: nvidia-smi",
        ]
        
        if cuda_info.error_message:
            instructions.extend([
                "",
                f"Error details: {cuda_info.error_message}"
            ])
        
        return instructions


# Convenience functions following DEVELOPMENT_STANDARDS.md
def detect_cuda() -> CudaInfo:
    """
    Convenience function to detect CUDA installation.
    
    Returns:
        CudaInfo with detection results
    """
    detector = CudaDetector()
    return detector.detect_cuda_installation()

def setup_cuda_environment() -> bool:
    """
    Convenience function to setup CUDA environment.
    
    Returns:
        True if setup successful, False otherwise
    """
    detector = CudaDetector()
    return detector.setup_cuda_environment()

def get_cuda_setup_instructions() -> List[str]:
    """
    Convenience function to get CUDA setup instructions.
    
    Returns:
        List of setup instruction strings
    """
    detector = CudaDetector()
    return detector.get_setup_instructions()

def check_cuda_requirements() -> bool:
    """
    Check if CUDA requirements are met for ExLlamaV2.
    
    Returns:
        True if requirements met, False otherwise
    """
    cuda_info = detect_cuda()
    
    if not cuda_info.available:
        logger.warning("CUDA not available - ExLlamaV2 will not work")
        return False
    
    # Check for RTX 3080 specifically
    rtx3080_found = any("3080" in gpu_name for gpu_name in cuda_info.gpu_names)
    
    if rtx3080_found:
        logger.info("🎯 RTX 3080 detected - optimal performance expected")
    else:
        logger.info(f"GPU detected: {', '.join(cuda_info.gpu_names)}")
    
    return True