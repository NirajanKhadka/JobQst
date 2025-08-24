# 🧪 JobQst Test Suite

> **Comprehensive testing infrastructure following TESTING_STANDARDS.md**

**Last Updated:** July 23, 2025  
**Status:** 🟢 **ACTIVE** - Fully Overhauled and Standardized  

## 🎯 **Testing Philosophy**

This test suite follows the **TESTING_STANDARDS.md** guidelines with:
- **Test What Matters**: Focus on business logic, user workflows, and integration points
- **Quality Gates**: All tests must pass before any commit or merge
- **Real Data Testing**: Use authentic profile data and realistic job scenarios
- **Performance Awareness**: Tests complete within reasonable time limits
- **Maintainable Tests**: Clear, well-documented, and maintainable test code

---

## 🏗️ **Test Architecture**

### **📁 Directory Structure**
```
tests/
├── unit/                    # Individual component tests (70% of suite)
│   ├── test_core/           # Core system components
│   ├── test_scrapers/       # Scraper-specific tests
│   ├── test_analysis/       # Job analysis and matching tests
│   └── test_utils/          # Utility function tests
├── integration/             # Multi-component interaction tests (25% of suite)
│   ├── test_workflows/      # End-to-end user workflows
│   ├── test_pipelines/      # Data processing pipelines
│   └── test_services/       # Service integration tests
├── performance/             # Performance and benchmarking tests (5% of suite)
├── dashboard/               # Dashboard component tests
├── e2e/                     # End-to-end tests (complete workflows)
├── fixtures/                # Test data and mock objects
├── conftest.py              # Pytest configuration and shared fixtures
└── README.md                # This documentation
```

### **🧪 Test Categories**

#### **Unit Tests** (70% of test suite)
- **Location**: `tests/unit/`
- **Purpose**: Test single functions or methods in isolation
- **Performance**: < 1 second each
- **Coverage Target**: 90% for core business logic

#### **Integration Tests** (25% of test suite)
- **Location**: `tests/integration/`
- **Purpose**: Test component and service interactions
- **Performance**: < 10 seconds each
- **Coverage**: Multi-component workflows

#### **Performance Tests** (5% of test suite)
- **Location**: `tests/performance/`
- **Purpose**: Benchmark critical performance metrics
- **Performance**: < 60 seconds each (marked as slow)
- **Coverage**: System behavior under load

---

## 🚀 **Quick Start**

### **Running Tests**

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v             # Integration tests only
pytest tests/performance/ -v             # Performance tests only

# Run tests by markers
pytest -m "unit" -v                      # Unit tests
pytest -m "integration" -v               # Integration tests
pytest -m "performance" -v               # Performance tests
pytest -m "scraping" -v                  # Scraping-related tests

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Skip slow tests
pytest tests/ --skip-slow

# Enable real scraping tests (slow)
pytest tests/ --real-scraping
```

### **Test Configuration**

Tests are configured via `pytest.ini` with:
- **Strict markers**: All markers must be registered
- **Async support**: Full asyncio test support
- **Performance monitoring**: Track slow tests
- **Real data fixtures**: No fabricated test content

---

## 📊 **Test Coverage Targets**

| Component | Target Coverage | Current Status |
|-----------|----------------|----------------|
| **Core Business Logic** | 90% | ✅ Achieved |
| **Scrapers** | 80% | ✅ Achieved |
| **Utils** | 85% | ✅ Achieved |
| **Dashboard** | 70% | ✅ Achieved |
| **Overall Project** | 80% | ✅ Achieved |

---

## 🛠️ **Test Development Guidelines**

### **📝 Test Naming Conventions**
```python
def test_function_scenario_expectedresult():
    """Test function behavior in specific scenario expecting specific result."""
    # AAA Pattern: Arrange, Act, Assert
    pass
```

### **🐍 Python Test Standards**
- Use clear, descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Use parameterized tests for multiple scenarios
- Limit test functions to 30 lines or less
- One test, one concern (single assertion focus)
- Use real data and realistic scenarios
- All test code must use type hints
- All public test functions/classes must have docstrings

### **🔧 Fixtures and Mocking**
```python
@pytest.fixture
def real_job_data(test_db):
    """Real job data from database (no fabricated content)."""
    return test_db.get_recent_jobs(limit=1)[0] if test_db else {}

@pytest.fixture
def mock_scraper():
    """Mock scraper for testing infrastructure without external calls."""
    return Mock(spec=ComprehensiveElutaScraper)
```

---

## 🚦 **Quality Gates**

### **✅ Mandatory Requirements**
- [ ] **Functionality**: Test passes and validates correct behavior
- [ ] **Isolation**: Test runs independently
- [ ] **Performance**: Completes within time limits
- [ ] **Real Data**: Uses authentic data, no fabricated content
- [ ] **Error Handling**: Tests both success and failure cases
- [ ] **Clean Code**: Follows code quality standards
- [ ] **Documentation**: Clear purpose from name and docstring
- [ ] **Mocking**: External dependencies properly mocked

### **⚡ Performance Requirements**
- **Unit Tests**: < 1 second each
- **Integration Tests**: < 10 seconds each
- **Performance Tests**: < 60 seconds each (marked as slow)
- **Full Test Suite**: < 5 minutes total execution time

---

## 🧩 **Key Test Fixtures**

### **Database Fixtures**
```python
@pytest.fixture
def test_db():
    """Test database with cleanup."""
    
@pytest.fixture
def real_job_data(test_db):
    """Real job data from database."""
    
@pytest.fixture
def real_job_list(test_db):
    """List of real jobs for batch testing."""
```

### **Profile Fixtures**
```python
@pytest.fixture
def real_profile():
    """Real user profile from actual profile files."""
    
@pytest.fixture
def test_config():
    """Global test configuration."""
```

### **Performance Fixtures**
```python
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    
@pytest.fixture
def performance_thresholds():
    """Performance thresholds for validation."""
```

---

## 🔍 **Test Categories by Marker**

### **Core Markers**
- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (medium speed)
- `@pytest.mark.performance` - Performance tests (slow)
- `@pytest.mark.e2e` - End-to-end tests (very slow)

### **Functional Markers**
- `@pytest.mark.scraping` - Web scraping tests
- `@pytest.mark.database` - Database-related tests
- `@pytest.mark.ai` - AI/ML model tests
- `@pytest.mark.dashboard` - Dashboard component tests

### **Special Markers**
- `@pytest.mark.slow` - Tests taking >5 seconds
- `@pytest.mark.real_world` - Tests using real external services
- `@pytest.mark.limited` - Tests with limited data processing

---

## 📈 **Current Test Status**

### **Test Suite Metrics**
- **Total Tests**: 110+ tests
- **Success Rate**: 95%+ (all critical tests passing)
- **Execution Time**: < 3 minutes for full suite
- **Coverage**: 80%+ overall project coverage

### **Recent Improvements**
- ✅ **Removed applier tests** - Eliminated tests for non-existent functionality
- ✅ **Organized structure** - Proper directory organization following standards
- ✅ **Improved fixtures** - Real data fixtures, no fabricated content
- ✅ **Performance monitoring** - Proper timing and threshold validation
- ✅ **Quality gates** - All tests follow AAA pattern and naming conventions

---

## 🛡️ **Troubleshooting**

### **Common Issues**

#### **Test Discovery Problems**
```bash
# Ensure proper Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run from project root
cd /path/to/automate_job
pytest tests/
```

#### **Database Test Failures**
```bash
# Check database availability
python -c "from src.core.job_database import get_job_db; print(get_job_db('test'))"

# Clear test database
python -c "from src.core.job_database import get_job_db; get_job_db('test').clear_all_jobs()"
```

#### **Performance Test Timeouts**
```bash
# Skip slow tests during development
pytest tests/ --skip-slow

# Run only fast unit tests
pytest tests/unit/ -m "not slow"
```

### **Test Environment Setup**
```bash
# Install test dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov pytest-asyncio

# Set up test environment
export TESTING=true
export AUTO_JOB_TEST_MODE=true
```

---

## 🔄 **Continuous Integration**

### **CI/CD Pipeline**
- All tests must pass before merge
- Coverage reports generated automatically
- Performance regression detection
- Flaky test identification and remediation

### **Pre-commit Hooks**
```bash
# Run tests before commit
pytest tests/unit/ -x  # Stop on first failure

# Check coverage
pytest tests/ --cov=src --cov-fail-under=80
```

---

## 📚 **Additional Resources**

- **TESTING_STANDARDS.md** - Comprehensive testing guidelines
- **DEVELOPMENT_STANDARDS.md** - Code quality standards
- **pytest.ini** - Test configuration
- **conftest.py** - Shared fixtures and configuration

---

## 🎯 **Test Suite Goals**

### **Achieved ✅**
- Comprehensive test coverage (80%+)
- Fast execution time (< 5 minutes)
- Real data testing (no fabricated content)
- Proper test organization and structure
- Quality gates and performance monitoring

### **Ongoing 🔄**
- Continuous coverage improvement
- Performance optimization
- Test reliability enhancement
- Documentation updates

---

*For detailed testing standards and guidelines, see `archive/old_documentation_july2025/standards/TESTING_STANDARDS.md`*

**Last Test Suite Overhaul:** July 23, 2025  
**Next Review:** Weekly maintenance and improvements