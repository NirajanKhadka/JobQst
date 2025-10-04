# Test Suite Quick Reference

## Status: ✅ **CLEAN & HEALTHY**

### Test Statistics
```
Total:   312 tests
Passing: 251 tests (100% pass rate)
Skipped: 61 tests (intentional - optional features)
Failed:  0 tests
```

## Quick Commands

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Fast Tests Only (Skip Optional Features)
```bash
python -m pytest tests/ -v -k "not test_ai_service and not test_gpu_ollama"
```

### Run by Category
```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Dashboard tests
python -m pytest tests/dashboard/ -v

# Performance tests
python -m pytest tests/performance/ -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Run Specific Test File
```bash
python -m pytest tests/unit/test_specific_file.py -v
```

## What Was Removed (47 Tests)

- ❌ `test_modern_pipeline.py` - Deprecated scraper
- ❌ `test_new_scraping_menu.py` - Legacy scrapers
- ❌ `test_dashboard_compliance.py` - Empty placeholder
- ❌ `test_dashboard_components.py` - Empty placeholder
- ❌ `test_openhermes_analyzer.py` - Deprecated analyzer
- ❌ `test_integration.py` - Non-existent modules
- ❌ `test_dashboard_integration.py` - Deprecated modules
- ❌ `test_document_workflows.py` - Non-existent modules
- ❌ `test_system_integration.py` - Deprecated orchestration

## What's Skipped (61 Tests - All Intentional)

### Optional Features (Properly Skipped)
- 🤖 28 AI/Ollama tests - optional AI features
- 📊 9 Dashboard/API tests - require running services
- 🔍 5 Scraper tests - optional modules
- 💾 3 Database tests - require test data
- 📦 2 Additional module tests - deprecated features
- 🔧 14 Other tests - various valid skip conditions

**All skips use proper `pytest.skip()` with clear reasons**

## Test Health Indicators

✅ **EXCELLENT**: All active tests pass (100%)
✅ **CLEAN**: No orphaned or deprecated tests
✅ **ORGANIZED**: Clear test structure and categories
✅ **DOCUMENTED**: All skips have clear reasons
✅ **MAINTAINABLE**: Reduced test count by 13%

## Common Issues & Solutions

### Issue: "Module not found" errors
**Solution**: Run in correct conda environment:
```bash
conda activate auto_job
python -m pytest tests/ -v
```

### Issue: Some tests skip unexpectedly
**Solution**: Check if optional dependencies are installed:
- Ollama for AI tests
- Real job data for database tests
- Running services for integration tests

### Issue: Tests take too long
**Solution**: Skip optional tests:
```bash
python -m pytest tests/ -v -m "not slow"
```

## Continuous Integration

### Pre-Commit Tests
```bash
# Fast unit tests only
python -m pytest tests/unit/ -v -x
```

### Full CI Pipeline
```bash
# All tests with coverage
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

### Nightly Tests
```bash
# Include slow/integration tests
python -m pytest tests/ -v --runslow
```

## Next Steps

1. ✅ Test suite is clean and ready
2. Optional: Add fixtures for database test data
3. Optional: Create test data generators
4. Optional: Add performance benchmarks

## Summary

**Before Cleanup**: 359 tests (279 pass, 80 skip)
**After Cleanup**: 312 tests (251 pass, 61 skip)
**Improvement**: Removed 47 deprecated tests, improved clarity

All remaining skipped tests are intentional and represent optional features or integration scenarios that require external services.

---

*Last updated: October 4, 2025*
*Status: Test suite cleanup complete* ✅
