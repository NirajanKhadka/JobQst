"""
SSL Certificate Path Fix Module

This module fixes the common SSL certificate path issue that prevents
Ollama and other packages from importing correctly. It should be imported
very early in the application startup process.
"""

import os


def fix_ssl_cert_path():
    """
    Fix SSL certificate path issue.
    
    This function checks if SSL_CERT_FILE environment variable is set incorrectly
    (pointing to a directory instead of a file) and fixes it automatically.
    
    Returns:
        bool: True if SSL path was fixed or is already correct, False otherwise
    """
    ssl_cert_file = os.environ.get('SSL_CERT_FILE', '')
    
    if not ssl_cert_file:
        # No SSL_CERT_FILE set - this is fine, Python will use defaults
        return True
    
    # Check if it's already a valid file
    if os.path.isfile(ssl_cert_file) and ssl_cert_file.endswith('.pem'):
        return True
    
    # If it's a directory, try to find the cert file
    if os.path.isdir(ssl_cert_file):
        potential_files = ['cacert.pem', 'cert.pem', 'ca-bundle.crt']
        
        for cert_file in potential_files:
            cert_path = os.path.join(ssl_cert_file, cert_file)
            if os.path.exists(cert_path):
                os.environ['SSL_CERT_FILE'] = cert_path
                return True
    
    # Check for corrupted conda path (common issue)
    if 'miniconda3' in ssl_cert_file or 'anaconda3' in ssl_cert_file:
        # Try to reconstruct the correct path
        if 'miniconda3' in ssl_cert_file:
            parts = ssl_cert_file.split('miniconda3')
            if len(parts) >= 2:
                base_path = parts[0] + 'miniconda3'
                potential_paths = [
                    os.path.join(base_path, 'envs', 'auto_job', 'Library', 'ssl', 'cacert.pem'),
                    os.path.join(base_path, 'Library', 'ssl', 'cacert.pem'),
                ]
                
                for path in potential_paths:
                    if os.path.exists(path):
                        os.environ['SSL_CERT_FILE'] = path
                        return True
    
    # If we can't fix it, unset it to use system defaults
    if 'SSL_CERT_FILE' in os.environ:
        del os.environ['SSL_CERT_FILE']
    
    return True


# Fix SSL certificate path immediately when this module is imported
fix_ssl_cert_path()
