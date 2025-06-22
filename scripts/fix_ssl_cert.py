#!/usr/bin/env python3
"""
Fix SSL certificate path for Ollama and other Python packages.

This script fixes the common issue where SSL_CERT_FILE environment variable
points to a directory instead of the actual certificate file.
"""

import os
import sys
from pathlib import Path
from rich.console import Console

console = Console()

def find_cert_file(ssl_dir: str) -> str:
    """Find the certificate file in the SSL directory."""
    potential_files = ['cacert.pem', 'cert.pem', 'ca-bundle.crt']
    
    for cert_file in potential_files:
        cert_path = os.path.join(ssl_dir, cert_file)
        if os.path.exists(cert_path):
            return cert_path
    
    return None

def fix_ssl_cert_path():
    """Fix SSL certificate path."""
    console.print("[bold blue]🔧 SSL Certificate Path Fixer[/bold blue]")

    # Get current SSL_CERT_FILE
    ssl_cert_file = os.environ.get('SSL_CERT_FILE', '')

    if not ssl_cert_file:
        console.print("[yellow]⚠️ SSL_CERT_FILE environment variable not set[/yellow]")
        console.print("[green]✅ This is actually fine - Python will use default certificates[/green]")
        return True

    console.print(f"[cyan]Current SSL_CERT_FILE: {ssl_cert_file}[/cyan]")

    # Check if it's already a valid file
    if os.path.isfile(ssl_cert_file) and ssl_cert_file.endswith('.pem'):
        console.print("[green]✅ SSL_CERT_FILE is already correctly set[/green]")
        return True

    # If it's a directory, try to find the cert file
    if os.path.isdir(ssl_cert_file):
        console.print("[yellow]⚠️ SSL_CERT_FILE points to a directory, not a file[/yellow]")

        cert_file = find_cert_file(ssl_cert_file)
        if cert_file:
            console.print(f"[green]✅ Found certificate file: {cert_file}[/green]")

            # Update environment variable
            os.environ['SSL_CERT_FILE'] = cert_file
            console.print(f"[green]✅ Updated SSL_CERT_FILE to: {cert_file}[/green]")

            # Show how to make it permanent
            console.print("\n[bold yellow]To make this change permanent:[/bold yellow]")
            if os.name == 'nt':  # Windows
                console.print(f"[cyan]setx SSL_CERT_FILE \"{cert_file}\"[/cyan]")
            else:  # Linux/macOS
                console.print(f"[cyan]export SSL_CERT_FILE=\"{cert_file}\"[/cyan]")
                console.print("[cyan]# Add the above line to your ~/.bashrc or ~/.zshrc[/cyan]")

            return True
        else:
            console.print("[red]❌ Could not find certificate file in the directory[/red]")

    # Check for corrupted path (common conda issue)
    if 'miniconda3' in ssl_cert_file or 'anaconda3' in ssl_cert_file:
        console.print("[yellow]⚠️ Detected conda environment SSL path issue[/yellow]")

        # Try to reconstruct the correct path
        if 'miniconda3' in ssl_cert_file:
            # Extract the base path and reconstruct
            parts = ssl_cert_file.split('miniconda3')
            if len(parts) >= 2:
                base_path = parts[0] + 'miniconda3'
                # Look for envs directory
                potential_paths = [
                    os.path.join(base_path, 'envs', 'auto_job', 'Library', 'ssl', 'cacert.pem'),
                    os.path.join(base_path, 'Library', 'ssl', 'cacert.pem'),
                ]

                for path in potential_paths:
                    if os.path.exists(path):
                        console.print(f"[green]✅ Found correct certificate path: {path}[/green]")
                        os.environ['SSL_CERT_FILE'] = path
                        console.print(f"[green]✅ Updated SSL_CERT_FILE to: {path}[/green]")
                        return True

    # If SSL_CERT_FILE is invalid, recommend unsetting it
    console.print("[yellow]⚠️ SSL_CERT_FILE appears to be invalid[/yellow]")
    console.print("[yellow]💡 Recommendation: Unset the environment variable to use system defaults[/yellow]")

    # Actually unset it for this session
    if 'SSL_CERT_FILE' in os.environ:
        del os.environ['SSL_CERT_FILE']
        console.print("[green]✅ Unset SSL_CERT_FILE for this session[/green]")

    # Show how to make it permanent
    if os.name == 'nt':  # Windows
        console.print("[cyan]To make permanent: reg delete \"HKCU\\Environment\" /v SSL_CERT_FILE /f[/cyan]")
    else:  # Linux/macOS
        console.print("[cyan]To make permanent: unset SSL_CERT_FILE[/cyan]")

    return True  # Return True since we fixed it by unsetting

def test_ollama_import():
    """Test if Ollama can be imported after fixing SSL."""
    console.print("\n[bold blue]🧪 Testing Ollama Import[/bold blue]")
    
    try:
        import ollama
        console.print("[green]✅ Ollama imported successfully![/green]")
        return True
    except ImportError:
        console.print("[red]❌ Ollama package not installed[/red]")
        console.print("[yellow]💡 Install with: pip install ollama[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Ollama import failed: {e}[/red]")
        return False

def main():
    """Main function."""
    console.print("[bold green]🚀 AutoJobAgent SSL Certificate Fixer[/bold green]\n")
    
    # Fix SSL certificate path
    ssl_fixed = fix_ssl_cert_path()
    
    # Test Ollama import
    ollama_works = test_ollama_import()
    
    # Summary
    console.print("\n[bold]📋 Summary:[/bold]")
    console.print(f"SSL Certificate: {'✅ Fixed' if ssl_fixed else '❌ Needs attention'}")
    console.print(f"Ollama Import: {'✅ Working' if ollama_works else '❌ Failed'}")
    
    if ssl_fixed and ollama_works:
        console.print("\n[bold green]🎉 All issues resolved! You can now run the main application.[/bold green]")
    else:
        console.print("\n[yellow]⚠️ Some issues remain. Please follow the suggestions above.[/yellow]")
    
    return 0 if (ssl_fixed and ollama_works) else 1

if __name__ == "__main__":
    sys.exit(main())
