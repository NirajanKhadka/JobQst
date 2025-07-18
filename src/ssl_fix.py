#!/usr/bin/env python3
"""
SSL Fix Module for AutoJobAgent

This module fixes SSL certificate issues that commonly occur with Python packages
and Ollama integration. It should be imported at the start of the application.
"""

import os
import sys
from pathlib import Path
from typing import Optional


def find_cert_file(ssl_dir: str) -> Optional[str]:
    """Find the certificate file in the SSL directory."""
    potential_files = ["cacert.pem", "cert.pem", "ca-bundle.crt"]

    for cert_file in potential_files:
        cert_path = os.path.join(ssl_dir, cert_file)
        if os.path.exists(cert_path):
            return cert_path

    return None


def fix_ssl_cert_path():
    """Fix SSL certificate path issues."""
    # Get current SSL_CERT_FILE
    ssl_cert_file = os.environ.get("SSL_CERT_FILE", "")

    if not ssl_cert_file:
        # No SSL_CERT_FILE set - this is usually fine
        return True

    # Check if it's already a valid file
    if os.path.isfile(ssl_cert_file) and ssl_cert_file.endswith(".pem"):
        return True

    # If it's a directory, try to find the cert file
    if os.path.isdir(ssl_cert_file):
        cert_file = find_cert_file(ssl_cert_file)
        if cert_file:
            # Update environment variable
            os.environ["SSL_CERT_FILE"] = cert_file
            return True

    # Check for corrupted path (common conda issue)
    if "miniconda3" in ssl_cert_file or "anaconda3" in ssl_cert_file:
        # Try to reconstruct the correct path
        if "miniconda3" in ssl_cert_file:
            parts = ssl_cert_file.split("miniconda3")
            if len(parts) >= 2:
                base_path = parts[0] + "miniconda3"
                # Look for envs directory
                potential_paths = [
                    os.path.join(base_path, "envs", "auto_job", "Library", "ssl", "cacert.pem"),
                    os.path.join(base_path, "Library", "ssl", "cacert.pem"),
                ]

                for path in potential_paths:
                    if os.path.exists(path):
                        os.environ["SSL_CERT_FILE"] = path
                        return True

    # If SSL_CERT_FILE is invalid, unset it
    if "SSL_CERT_FILE" in os.environ:
        del os.environ["SSL_CERT_FILE"]

    return True


def test_ollama_import():
    """Test if Ollama can be imported after fixing SSL."""
    try:
        import ollama

        return True
    except ImportError:
        return False
    except Exception:
        return False


# Auto-fix SSL issues when module is imported
fix_ssl_cert_path()

# Test if the fix worked
if test_ollama_import():
    print("✅ SSL fix applied successfully - Ollama import working")
else:
    print("⚠️ SSL fix applied, but Ollama import may still have issues")

# Export the fix function for manual use
__all__ = ["fix_ssl_cert_path", "test_ollama_import"]
