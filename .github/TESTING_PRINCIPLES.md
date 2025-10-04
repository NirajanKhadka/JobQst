# Testing Principles for JobLens

## Environment Management Rules

### ✅ PRIMARY RULE: Always Use Direct Python Execution

**NEVER use `conda run -n auto_job python ...`** - The environment is already activated.

```bash
# ❌ WRONG - Don't wrap commands with conda run
conda run -n auto_job python script.py

# ✅ CORRECT - Direct Python execution
python script.py
```

### Why This Matters

1. **Environment is Pre-Activated**: The `auto_job` conda environment is already active in the shell
2. **Conda Run Limitations**: `conda run` has issues with multi-line commands and complex arguments
3. **Simpler Execution**: Direct Python execution is faster and more reliable
4. **Error Handling**: Direct execution provides clearer error messages

### Environment Verification

```python
# Always verify environment at script start
import sys
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

# Expected output for auto_job environment:
# Python: C:\Users\Niraj\miniconda3\envs\auto_job\python.exe
# Version: 3.10.x
```

### Testing Best Practices

1. **Create Dedicated Test Scripts**: Write standalone `.py` files for testing
2. **Run Directly**: Execute with `python test_script.py`
3. **Check Environment First**: Verify you're in `auto_job` before running
4. **Use sys.path Properly**: Add project root to path in test scripts

### Example Test Script Template

```python
#!/usr/bin/env python3
"""
Test script template for JobLens
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def main():
    """Main test logic"""
    print(f"Running from: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    # Your test code here
    pass

if __name__ == "__main__":
    main()
```

## Testing the ProfileService Chain

The complete integration chain has been tested and verified:

```
DataLoader → DataService → ProfileService ✅
ConfigService → ProfileService ✅
```

Run the verification:
```bash
python test_profile_service_chain.py
```

Expected output:
- ✅ ProfileService: Found 3 profiles
- ✅ DataService: Found 3 profiles
- ✅ DataLoader: Found 3 profiles
- ✅ ConfigService: Found 3 profiles
- 📊 Cache: 300s TTL operational

## Common Testing Commands

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/dashboard/unit/test_profile_service.py

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run dashboard tests only
python -m pytest tests/dashboard/ -v

# Run integration tests
python -m pytest tests/integration/ -v
```

## VS Code Tasks

Use the built-in VS Code tasks (Ctrl+Shift+P → "Tasks: Run Task"):
- `Run all tests (pytest)` - Full test suite
- `Start Dash Dashboard` - Launch dashboard
- `Install Frontend Dependencies` - Setup dashboard frontend

These tasks already use the correct environment configuration.

## Environment Troubleshooting

If you see import errors:

1. **Check active environment**:
   ```bash
   conda env list
   # Look for * next to auto_job
   ```

2. **Activate if needed**:
   ```bash
   conda activate auto_job
   ```

3. **Verify Python path**:
   ```bash
   python -c "import sys; print(sys.executable)"
   # Should show: C:\Users\Niraj\miniconda3\envs\auto_job\python.exe
   ```

4. **Check installed packages**:
   ```bash
   python -m pip list | grep dashboard
   ```

## Summary

- ✅ Use direct `python` commands
- ❌ Don't use `conda run -n auto_job`
- 🔧 Environment is pre-activated
- 📝 Create standalone test scripts
- 🎯 Run tests with `python -m pytest`
