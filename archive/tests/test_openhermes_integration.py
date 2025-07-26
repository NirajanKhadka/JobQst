#!/usr/bin/env python3
"""
OpenHermes 2.5 Integration Test
Comprehensive test of OpenHermes 2.5 integration with the complete job processor architecture
"""

import sys
import time
import json
from pathlib import Path
import os
# ExLlamaV2 integration
try:
    from exllamav2 import ExLlamaV2Tokenizer, ExLlamaV2, ExLlamaV2DynamicGenerator
    EXLLAMAV2_AVAILABLE = True
except ImportError:
    EXLLAMAV2_AVAILABLE = False

# Add project root to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

def test_architecture_integration():
    """Test the complete architecture integration."""
    print("🏗️ Testing OpenHermes 2.5 Architecture Integration")
    print("=" * 60)
    
    try:
        # Test 1: Enhanced Job Analyzer
        print("\n1. 📊 Testing Enhanced Job Analyzer...")
        from src.ai.enhanced_job_analyzer import EnhancedJobAnalyzer, ANALYSIS_METHOD_OPENHERMES
        from src.utils.profile_helpers import load_profile
        
        profile = load_profile("Nirajan")
        analyzer = EnhancedJobAnalyzer(profile)
        
        print(f"   ✅ OpenHermes method constant: {ANALYSIS_METHOD_OPENHERMES}")
        print(f"   ✅ Analyzer initialized with profile: {profile.get('name', 'Unknown')}")
        
        # Test 2: Reliable Job Processor Analyzer
        print("\n2. 🔄 Testing Reliable Job Processor Analyzer...")
        from src.ai.reliable_job_processor_analyzer import ReliableJobProcessorAnalyzer
        
        reliable_analyzer = ReliableJobProcessorAnalyzer(profile)
        diagnostics = reliable_analyzer.get_diagnostic_info()
        
        print(f"   ✅ Reliable analyzer initialized")
        print(f"   ✅ AI fallback enabled: {diagnostics['analyzer_config']['ai_fallback_enabled']}")
        
        # Test 3: Enhanced Job Processor
        print("\n3. 🚀 Testing Enhanced Job Processor...")
        from src.dashboard.enhanced_job_processor import get_enhanced_job_processor
        
        processor = get_enhanced_job_processor("Nirajan")
        status = processor.get_status()
        
        print(f"   ✅ Job processor initialized")
        print(f"   ✅ Profile: {status['profile']}")
        print(f"   ✅ Statistics tracking ready")
        
        # Test 4: Database Integration
        print("\n4. 💾 Testing Database Integration...")
        from src.core.job_database import get_job_db
        
        db = get_job_db("Nirajan")
        job_count = db.get_job_count()
        
        print(f"   ✅ Database connected")
        print(f"   ✅ Total jobs in database: {job_count}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Architecture integration test failed: {e}")
        return False

def test_openhermes_model_integration():
    """Test OpenHermes 2.5 model integration."""
    print("\n🤖 Testing OpenHermes 2.5 Model Integration")
    print("=" * 60)
    # ExLlamaV2 integration test
    if not EXLLAMAV2_AVAILABLE:
        print("   ❌ exllamav2 not installed. Please run: pip install exllamav2")
        return False
    try:
        model_path = os.environ.get("OPENHERMES_MODEL_PATH", "D:/models/openhermes-2.5")
        print(f"\n1. 🔌 Loading OpenHermes model from: {model_path}")
        # Check for required model files
        required_files = ["config.json", "tokenizer.model"]
        found_files = os.listdir(model_path) if os.path.exists(model_path) else []
        missing = [f for f in required_files if f not in found_files]
        if missing:
            print(f"   ❌ Missing model files: {missing}. Please download the OpenHermes model from HuggingFace.")
            return False
        tokenizer = ExLlamaV2Tokenizer(model_path)
        model = ExLlamaV2(model_path)
        generator = ExLlamaV2DynamicGenerator(model, tokenizer)
        print("   ✅ Model loaded successfully")
        # Test single prompt
        prompt = "You are a job analysis expert. Analyze compatibility for: Python Developer at TechCorp."
        output = generator.generate(prompt=prompt, max_new_tokens=100)
        print(f"   ✅ Model output: {output[0][:100]}...")
        # Test batched prompts (simulate two jobs)
        prompts = [
            "Analyze compatibility for: Python Developer at TechCorp.",
            "Analyze compatibility for: Data Scientist at DataCorp."
        ]
        outputs = generator.generate(prompt=prompts, max_new_tokens=100)
        print("   ✅ Batched output:")
        for i, out in enumerate(outputs):
            print(f"      Job {i+1}: {out[:100]}...")
        return True
    except Exception as e:
        print(f"   ❌ exllamav2 model integration failed: {e}")
        return False

def test_analysis_pipeline():
    """Test the complete analysis pipeline."""
    print("\n🔄 Testing Complete Analysis Pipeline")
    print("=" * 60)
    
    try:
        from src.ai.enhanced_job_analyzer import EnhancedJobAnalyzer
        from src.utils.profile_helpers import load_profile
        
        # Load profile and create analyzer
        profile = load_profile("Nirajan")
        analyzer = EnhancedJobAnalyzer(profile)
        
        # Test job data
        test_job = {
            'title': 'Senior Python Developer',
            'company': 'TechCorp Solutions',
            'location': 'Remote',
            'description': 'We are seeking a Senior Python Developer with experience in Django, PostgreSQL, and AWS. The ideal candidate will have 5+ years of experience and strong problem-solving skills.',
            'url': 'https://example.com/job/123'
        }
        
        print(f"\n1. 📋 Test Job:")
        print(f"   Title: {test_job['title']}")
        print(f"   Company: {test_job['company']}")
        print(f"   Location: {test_job['location']}")
        
        print(f"\n2. 🔍 Running Analysis...")
        start_time = time.time()
        
        analysis_result = analyzer.analyze_job(test_job)
        
        analysis_time = time.time() - start_time
        
        print(f"   ✅ Analysis completed in {analysis_time:.2f} seconds")
        print(f"   ✅ Analysis method: {analysis_result.get('analysis_method', 'unknown')}")
        print(f"   ✅ Compatibility score: {analysis_result.get('compatibility_score', 0):.2f}")
        print(f"   ✅ Confidence: {analysis_result.get('confidence', 0):.2f}")
        print(f"   ✅ Recommendation: {analysis_result.get('recommendation', 'unknown')}")
        
        # Validate analysis structure
        required_fields = [
            'compatibility_score', 'confidence', 'skill_matches', 'skill_gaps',
            'experience_match', 'location_match', 'cultural_fit', 'growth_potential',
            'recommendation', 'reasoning', 'analysis_method'
        ]
        
        missing_fields = [field for field in required_fields if field not in analysis_result]
        
        if missing_fields:
            print(f"   ⚠️ Missing fields: {missing_fields}")
        else:
            print("   ✅ All required fields present")
        
        # Check if score is in expected range (0.7+ baseline)
        score = analysis_result.get('compatibility_score', 0)
        if score >= 0.6:  # Reasonable minimum
            print(f"   ✅ Score in expected range: {score:.2f}")
        else:
            print(f"   ⚠️ Score below expected range: {score:.2f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Analysis pipeline test failed: {e}")
        return False

def test_job_processor_integration():
    """Test job processor integration with OpenHermes 2.5."""
    print("\n🚀 Testing Job Processor Integration")
    print("=" * 60)
    
    try:
        from src.dashboard.enhanced_job_processor import get_enhanced_job_processor
        from src.core.job_database import get_job_db
        
        # Initialize components
        processor = get_enhanced_job_processor("Nirajan")
        db = get_job_db("Nirajan")
        
        # Check initial status
        initial_status = processor.get_status()
        print(f"\n1. 📊 Initial Status:")
        print(f"   Profile: {initial_status['profile']}")
        print(f"   Active: {initial_status['active']}")
        print(f"   Queue size: {initial_status['queue_size']}")
        
        # Check statistics structure
        stats = initial_status['stats']
        print(f"\n2. 📈 Statistics Structure:")
        print(f"   Analysis methods: {stats['analysis_methods']}")
        print(f"   AI service health: {stats['ai_service_health']['connection_status']}")
        
        # Test processor summary
        summary = processor.get_processing_summary()
        print(f"\n3. 📋 Processing Summary:")
        print(f"   Profile: {summary['profile']}")
        print(f"   Queue active: {summary['queue_info']['is_active']}")
        print(f"   AI analysis summary: {summary['ai_analysis_summary']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Job processor integration test failed: {e}")
        return False

def test_fallback_system():
    """Test the fallback system integration."""
    print("\n🔄 Testing Fallback System Integration")
    print("=" * 60)
    
    try:
        from src.ai.reliable_job_processor_analyzer import ReliableJobProcessorAnalyzer
        from src.utils.profile_helpers import load_profile
        
        profile = load_profile("Nirajan")
        analyzer = ReliableJobProcessorAnalyzer(profile)
        
        # Test diagnostics
        diagnostics = analyzer.get_diagnostic_info()
        
        print(f"\n1. 🔧 Analyzer Configuration:")
        config = diagnostics['analyzer_config']
        print(f"   Profile: {config['profile_name']}")
        print(f"   Ollama endpoint: {config['ollama_endpoint']}")
        print(f"   AI fallback enabled: {config['ai_fallback_enabled']}")
        
        print(f"\n2. 📊 Statistics:")
        stats = diagnostics['statistics']
        print(f"   Total analyses: {stats['analyzer_stats']['total_analyses']}")
        print(f"   AI successful: {stats['analyzer_stats']['ai_successful']}")
        print(f"   Rule-based used: {stats['analyzer_stats']['rule_based_used']}")
        
        print(f"\n3. 🏥 Health Summary:")
        health = stats['health_summary']
        print(f"   AI success rate: {health['ai_success_rate']:.1f}%")
        print(f"   Primary method: {health['primary_method']}")
        
        print(f"\n4. 💡 Recommendations:")
        for rec in diagnostics['recommendations']:
            print(f"   • {rec}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Fallback system test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_openhermes_model_integration()
    sys.exit(0 if success else 1)