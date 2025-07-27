#!/usr/bin/env python3
"""
Test CUDA availability and GPU vs CPU performance
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_cuda_availability():
    """Test if CUDA is available for GPU acceleration"""
    print("🧪 Testing CUDA Availability...")
    
    try:
        import torch
        print(f"✅ PyTorch installed: {torch.__version__}")
        
        cuda_available = torch.cuda.is_available()
        print(f"🔧 CUDA Available: {'✅ Yes' if cuda_available else '❌ No'}")
        
        if cuda_available:
            device_count = torch.cuda.device_count()
            print(f"🎮 GPU Devices: {device_count}")
            
            for i in range(device_count):
                gpu_name = torch.cuda.get_device_name(i)
                print(f"   GPU {i}: {gpu_name}")
                
                # Test GPU memory
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                print(f"   Memory: {gpu_memory:.1f} GB")
        
        return cuda_available
        
    except ImportError:
        print("❌ PyTorch not installed")
        return False
    except Exception as e:
        print(f"❌ Error checking CUDA: {e}")
        return False

def test_transformers_availability():
    """Test if transformers library is available"""
    print("\n🧪 Testing Transformers Library...")
    
    try:
        import transformers
        print(f"✅ Transformers installed: {transformers.__version__}")
        
        # Test basic model loading
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        print("✅ Model tokenizer loaded successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Transformers not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing transformers: {e}")
        return False

def test_rule_based_performance():
    """Test rule-based performance"""
    print("\n🧪 Testing Rule-Based Performance...")
    
    try:
        from src.ai.enhanced_rule_based_analyzer import EnhancedRuleBasedAnalyzer
        from src.utils.profile_helpers import load_profile
        
        # Load profile
        profile = load_profile("Nirajan")
        analyzer = EnhancedRuleBasedAnalyzer(profile)
        
        # Test job
        test_job = {
            'title': 'Senior Data Analyst',
            'company': 'TechCorp',
            'description': 'Python, SQL, Machine Learning, AWS, pandas, numpy, scikit-learn, data analysis, statistics'
        }
        
        # Time multiple runs
        runs = 100
        start_time = time.time()
        
        for _ in range(runs):
            result = analyzer.analyze_job(test_job)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ Rule-Based Performance:")
        print(f"   Runs: {runs}")
        print(f"   Total Time: {total_time:.3f}s")
        print(f"   Avg per Job: {total_time/runs*1000:.2f}ms")
        print(f"   Jobs/Second: {runs/total_time:.1f}")
        
        return total_time / runs
        
    except Exception as e:
        print(f"❌ Rule-based test failed: {e}")
        return None

def test_simple_gpu_performance():
    """Test simple GPU performance with PyTorch"""
    print("\n🧪 Testing Simple GPU Performance...")
    
    try:
        import torch
        
        if not torch.cuda.is_available():
            print("❌ CUDA not available - skipping GPU test")
            return None
        
        device = torch.device("cuda")
        print(f"✅ Using device: {device}")
        
        # Simple tensor operations
        size = 1000
        runs = 100
        
        # CPU test
        cpu_device = torch.device("cpu")
        start_time = time.time()
        
        for _ in range(runs):
            a = torch.randn(size, size, device=cpu_device)
            b = torch.randn(size, size, device=cpu_device)
            c = torch.matmul(a, b)
        
        cpu_time = time.time() - start_time
        
        # GPU test
        start_time = time.time()
        
        for _ in range(runs):
            a = torch.randn(size, size, device=device)
            b = torch.randn(size, size, device=device)
            c = torch.matmul(a, b)
            torch.cuda.synchronize()  # Wait for GPU to finish
        
        gpu_time = time.time() - start_time
        
        print(f"✅ Tensor Operations Performance:")
        print(f"   CPU Time: {cpu_time:.3f}s")
        print(f"   GPU Time: {gpu_time:.3f}s")
        print(f"   GPU Speedup: {cpu_time/gpu_time:.1f}x faster")
        
        return gpu_time
        
    except Exception as e:
        print(f"❌ GPU test failed: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 CUDA and GPU Performance Test")
    print("=" * 50)
    
    # Test CUDA availability
    cuda_available = test_cuda_availability()
    
    # Test transformers
    transformers_available = test_transformers_availability()
    
    # Test rule-based performance
    rule_based_time = test_rule_based_performance()
    
    # Test simple GPU performance
    gpu_time = test_simple_gpu_performance()
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   CUDA Available: {'✅' if cuda_available else '❌'}")
    print(f"   Transformers Available: {'✅' if transformers_available else '❌'}")
    print(f"   Rule-Based Ready: {'✅' if rule_based_time else '❌'}")
    print(f"   GPU Performance: {'✅' if gpu_time else '❌'}")
    
    if rule_based_time:
        print(f"\n🏆 Rule-Based Analysis:")
        print(f"   Speed: {1/rule_based_time:.1f} jobs/second")
        print(f"   Time per job: {rule_based_time*1000:.2f}ms")
    
    if cuda_available and transformers_available:
        print(f"\n💡 GPU acceleration is possible but rule-based is already extremely fast!")
    elif not cuda_available:
        print(f"\n💡 No GPU available - rule-based CPU method is optimal!")
    else:
        print(f"\n💡 Rule-based method is recommended for speed and simplicity!")

if __name__ == "__main__":
    main()