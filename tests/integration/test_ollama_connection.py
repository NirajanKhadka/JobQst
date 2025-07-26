#!/usr/bin/env python3
"""
Test script to verify Ollama connection and OpenHermes 2.5 availability
"""

import requests
import json

def test_ollama_connection():
    """Test Ollama connection and model availability."""
    
    ollama_url = "http://localhost:11434"
    
    print("🔌 Testing Ollama connection...")
    
    # Test basic connection
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Ollama is running and accessible")
            
            models = response.json().get("models", [])
            print(f"📦 Available models: {len(models)}")
            
            # Check for OpenHermes models
            openhermes_models = [m for m in models if "openhermes" in m.get("name", "").lower()]
            if openhermes_models:
                print("✅ OpenHermes models found:")
                for model in openhermes_models:
                    name = model.get("name", "Unknown")
                    size = model.get("size", 0)
                    size_gb = size / (1024**3) if size else 0
                    print(f"   - {name} ({size_gb:.1f} GB)")
            else:
                print("❌ No OpenHermes models found")
                
            # Check for other models
            other_models = [m for m in models if "openhermes" not in m.get("name", "").lower()]
            if other_models:
                print("📋 Other available models:")
                for model in other_models[:5]:  # Show first 5
                    name = model.get("name", "Unknown")
                    size = model.get("size", 0)
                    size_gb = size / (1024**3) if size else 0
                    print(f"   - {name} ({size_gb:.1f} GB)")
                    
        else:
            print(f"❌ Ollama connection failed: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama. Is it running?")
        print("💡 Try running: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        return False
    
    return True

def test_openhermes_generation():
    """Test OpenHermes 2.5 text generation."""
    
    print("\n🧠 Testing OpenHermes 2.5 generation...")
    
    ollama_url = "http://localhost:11434"
    
    test_prompt = """You are a helpful AI assistant. Respond with a simple JSON object containing:
{
    "status": "working",
    "model": "openhermes-2.5",
    "message": "Hello from OpenHermes!"
}

Respond with ONLY the JSON, no additional text."""
    
    payload = {
        "model": "openhermes:v2.5",
        "prompt": test_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": 200
        }
    }
    
    try:
        print("📤 Sending test prompt to OpenHermes 2.5...")
        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            
            print("✅ OpenHermes 2.5 responded successfully!")
            print(f"📝 Response: {generated_text[:200]}...")
            
            # Try to parse JSON from response
            try:
                import re
                json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed_json = json.loads(json_str)
                    print("✅ JSON parsing successful!")
                    print(f"📊 Parsed data: {parsed_json}")
                else:
                    print("⚠️ No JSON found in response")
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing failed: {e}")
                
            return True
        else:
            print(f"❌ OpenHermes generation failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ OpenHermes generation timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing OpenHermes generation: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Ollama and OpenHermes 2.5")
    print("=" * 50)
    
    # Test connection
    if test_ollama_connection():
        # Test generation
        test_openhermes_generation()
    
    print("\n" + "=" * 50)
    print("✅ Test completed")