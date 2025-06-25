"""
SSL Certificate Fix Module for AutoJobAgent.

This module provides SSL certificate path fixing functionality
to resolve SSL-related issues in the application.
"""

import os
import ssl
import certifi
from pathlib import Path
from typing import Optional


def fix_ssl_cert_path() -> Optional[str]:
    """
    Fix SSL certificate path issues.
    
    Returns:
        str: Path to the SSL certificate file, or None if not found
    """
    try:
        # Try to use certifi's certificate path
        cert_path = certifi.where()
        if os.path.exists(cert_path):
            return cert_path
        
        # Fallback to system certificates
        system_certs = [
            "/etc/ssl/certs/ca-certificates.crt",  # Linux
            "/etc/pki/tls/certs/ca-bundle.crt",    # RHEL/CentOS
            "/usr/local/share/certs/ca-root-nss.crt",  # FreeBSD
            "/etc/ssl/cert.pem",  # macOS
        ]
        
        for cert in system_certs:
            if os.path.exists(cert):
                return cert
        
        return None
        
    except Exception as e:
        print(f"Warning: Could not fix SSL certificate path: {e}")
        return None


def configure_ssl_context() -> ssl.SSLContext:
    """
    Configure SSL context with proper certificate verification.
    
    Returns:
        ssl.SSLContext: Configured SSL context
    """
    context = ssl.create_default_context()
    
    # Try to set certificate path
    cert_path = fix_ssl_cert_path()
    if cert_path:
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cert_path)
    else:
        # Fallback to default behavior
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    
    return context


def is_ssl_available() -> bool:
    """
    Check if SSL is properly configured.
    
    Returns:
        bool: True if SSL is available and configured
    """
    try:
        cert_path = fix_ssl_cert_path()
        return cert_path is not None and os.path.exists(cert_path)
    except Exception:
        return False


# Auto-fix SSL when module is imported
if __name__ != "__main__":
    # Only auto-fix when imported as a module
    try:
        cert_path = fix_ssl_cert_path()
        if cert_path:
            os.environ['SSL_CERT_FILE'] = cert_path
            os.environ['REQUESTS_CA_BUNDLE'] = cert_path
    except Exception:
        pass 