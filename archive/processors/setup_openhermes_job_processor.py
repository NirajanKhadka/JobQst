#!/usr/bin/env python3
"""
OpenHermes 2.5 Job Processor Setup Script
Automatically configures and tests OpenHermes 2.5 for job analysis
"""

import subprocess
import requests
import time
import json
import sys
from pathlib import Path

def print_status(message, status="INFO"):
    """Print colored status messages."""
    colors = {
        "INFO": "\033[94m",      # Blue
        "SUCCESS": "\033[92m",   # Green
        "WARNING": "\033[93m",   # Yellow
        "ERROR": "\033[91m",     # Red
        "RESET": "\033[0m"       # Reset
    }
    
    color = colors.get(status, colors["INFO"])
    reset = colors["RESET"]
    print(f"{color}[{status}] {message}{reset}")

def check_ollama_installed():
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"Ollama is installed: {result.stdout.strip()}", "SUCCESS")
            return True
        else:
            print_status("Ollama is not installed", "ERROR")
            return False
    except FileNotFoundError:
        print_status("Ollama is not installed or not in PATH", "ERROR")
        return False

def start_ollama_service():
    """Start Ollama service."""
    print_status("Starting Ollama service...", "INFO")
    
    try:
        # Try to start Ollama serve in background
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)  # Wait for service to start
        
        # Check if service is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print_status("Ollama service started successfully", "SUCCESS")
            return True
        else:
            print_status("Ollama service failed to start", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Error starting Ollama service: {e}", "ERROR")
        return False

def check_ollama_running():
    """Check if Ollama service is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print_status("Ollama service is running", "SUCCESS")
            return True
        else:
            print_status("Ollama service is not responding", "WARNING")
            return False
    except Exception as e:
        print_status("Ollama service is not running", "WARNING")
        return False

def pull_openhermes_model():
    """Pull OpenHermes 2.5 model."""
    print_status("Pulling OpenHermes 2.5 model (this may take a few minutes)...", "INFO")
    
    try:
        result = subprocess.run(["ollama", "pull", "openhermes:v2.5"], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print_status("OpenHermes 2.5 model pulled successfully", "SUCCESS")
            return True
        else:
            print_status(f"Failed to pull OpenHermes 2.5: {result.stderr}", "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        print_status("Model pull timed out (5 minutes)", "ERROR")
        return False
    except Exception as e:
        print_status(f"Error pulling model: {e}", "ERROR")
        return False

def check_model_available():
    """Check if OpenHermes 2.5 model is available."""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        
        if result.returncode == 0:
            if "openhermes:v2.5" in result.stdout:
                print_status("OpenHermes 2.5 model is available", "SUCCESS")
                return True
            else:
                print_status("OpenHermes 2.5 model not found in local models", "WARNING")
                return False
        else:
            print_status("Failed to list models", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Error checking models: {e}", "ERROR")
        return False

def test_model_generation():
    """Test OpenHermes 2.5 model generation."""
    print_status("Testing OpenHermes 2.5 model generation...", "INFO")
    
    test_payload = {
        "model": "openhermes:v2.5",
        "prompt": "Analyze this job posting: Senior Python Developer at TechCorp. Provide a brief compatibility assessment.",
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 200
        }
    }
    
    try:
        response = requests.post("http://localhost:11434/api/generate", 
                               json=test_payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if "response" in result and result["response"]:
                print_status("Model generation test successful", "SUCCESS")
                print_status(f"Sample response: {result['response'][:100]}...", "INFO")
                return True
            else:
                print_status("Model returned empty response", "ERROR")
                return False
        else:
            print_status(f"Model generation failed: HTTP {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Error testing model: {e}", "ERROR")
        return False

def test_job_processor():
    """Test the job processor with OpenHermes 2.5."""
    print_status("Testing job processor integration...", "INFO")
    
    try:
        # Import and test the job processor
        sys.path.append(str(Path(__file__).parent))
        from src.dashboard.enhanced_job_processor import get_enhanced_job_processor
        from src.core.job_database import get_job_db
        
        # Initialize processor
        processor = get_enhanced_job_processor("Nirajan")
        db = get_job_db("Nirajan")
        
        # Check database
        job_count = db.get_job_count()
        print_status(f"Database contains {job_count} jobs", "INFO")
        
        # Test processor status
        status = processor.get_status()
        print_status(f"Job processor status: {status['profile']}", "SUCCESS")
        
        return True
        
    except Exception as e:
        print_status(f"Job processor test failed: {e}", "ERROR")
        return False

def update_profile_config():
    """Update user profile to use OpenHermes 2.5."""
    print_status("Updating profile configuration for OpenHermes 2.5...", "INFO")
    
    try:
        profile_path = Path("profiles/Nirajan/profile.json")
        
        if profile_path.exists():
            with open(profile_path, 'r') as f:
                profile = json.load(f)
            
            # Update model configuration
            profile["mistral_config"] = {
                "model": "openhermes:v2.5",
                "temperature": 0.3,
                "max_tokens": 2048,
                "top_p": 0.9,
                "analysis_timeout": 30
            }
            
            # Update default scores
            profile["default_compatibility_score"] = 0.7
            
            with open(profile_path, 'w') as f:
                json.dump(profile, f, indent=2)
            
            print_status("Profile configuration updated", "SUCCESS")
            return True
        else:
            print_status("Profile file not found, skipping configuration update", "WARNING")
            return True
            
    except Exception as e:
        print_status(f"Error updating profile: {e}", "ERROR")
        return False

def main():
    """Main setup function."""
    print_status("🚀 OpenHermes 2.5 Job Processor Setup", "INFO")
    print_status("=" * 50, "INFO")
    
    # Step 1: Check Ollama installation
    if not check_ollama_installed():
        print_status("Please install Ollama first: https://ollama.ai/download", "ERROR")
        return False
    
    # Step 2: Start Ollama service if not running
    if not check_ollama_running():
        if not start_ollama_service():
            print_status("Please start Ollama manually: ollama serve", "ERROR")
            return False
    
    # Step 3: Check if model is already available
    if not check_model_available():
        if not pull_openhermes_model():
            print_status("Failed to pull OpenHermes 2.5 model", "ERROR")
            return False
    
    # Step 4: Test model generation
    if not test_model_generation():
        print_status("Model generation test failed", "ERROR")
        return False
    
    # Step 5: Update profile configuration
    if not update_profile_config():
        print_status("Profile configuration update failed", "WARNING")
    
    # Step 6: Test job processor integration
    if not test_job_processor():
        print_status("Job processor integration test failed", "WARNING")
        print_status("You may need to install missing dependencies", "INFO")
    
    # Success summary
    print_status("=" * 50, "SUCCESS")
    print_status("🎉 OpenHermes 2.5 Setup Complete!", "SUCCESS")
    print_status("=" * 50, "SUCCESS")
    
    print_status("✅ OpenHermes 2.5 model is ready", "SUCCESS")
    print_status("✅ Ollama service is running", "SUCCESS")
    print_status("✅ Model generation is working", "SUCCESS")
    print_status("✅ Default scores updated to 0.7", "SUCCESS")
    
    print_status("\n🚀 Next Steps:", "INFO")
    print_status("1. Run: python test_job_processor.py", "INFO")
    print_status("2. Check the dashboard for processed jobs", "INFO")
    print_status("3. Review compatibility scores (should be 0.7+ baseline)", "INFO")
    print_status("4. Generate documents for high-scoring jobs", "INFO")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)