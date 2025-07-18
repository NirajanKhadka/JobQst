# 🧪 AutoJobAgent Testing Standards

> **Under any circumstances, the user should ask the AI to edit these standards.**

**Last Updated:** July 13, 2025  
**Status:** 🟢 **ACTIVE** - Comprehensive Testing Guidelines  

> **NOTICE:** This document follows the modular standards approach defined in `DEVELOPMENT_STANDARDS.md` and must be maintained with the same rigor.

## 🎯 **Testing Philosophy**

- **Test What Matters**: Focus on business logic, user workflows, and integration points
- **Quality Gates**: All tests must pass before any commit or merge; zero tolerance for failing tests
- **Real Data Testing**: Use authentic profile data and realistic job scenarios
- **Performance Awareness**: Tests should complete within reasonable time limits
- **Maintainable Tests**: Write tests that are as clear and maintainable as production code

---

## 🏗️ **Test Architecture**

### **📁 Test Organization Structure**
```
tests/
├── unit/                    # Individual component tests
│   ├── test_core/           # Core system components
│   ├── test_scrapers/       # Scraper-specific tests
│   ├── test_analysis/       # Job analysis and matching
│   └── test_utils/          # Utility function tests
├── integration/             # Multi-component interaction tests
│   ├── test_workflows/      # End-to-end user workflows
│   ├── test_pipelines/      # Data processing pipelines
│   └── test_services/       # Service integration tests
├── performance/             # Performance and benchmarking tests
├── fixtures/                # Test data and mock objects
├── conftest.py              # Pytest configuration and shared fixtures
└── README.md                # Testing documentation and quick start
```

### **🧪 Test Types and Coverage**

#### **Unit Tests** (70% of test suite)
- Test single functions or methods in isolation
- Verify error handling and edge cases
- Test input validation and data processing logic

#### **Integration Tests** (25% of test suite)
- Test component and service interactions
- Test API calls, database operations, and third-party integrations (with mocking)

#### **Performance Tests** (5% of test suite)
- Benchmark critical performance metrics
- Test system behavior under load and for memory/resource management

---

## 💻 **Test Code Quality Standards**

### **🐍 Python Test Standards**
- Use clear, descriptive test names (e.g., `test_function_scenario_expectedresult`)
- Use the AAA pattern (Arrange, Act, Assert) in all tests
- Use parameterized tests for multiple scenarios
- Limit test functions to 30 lines or less
- One test, one concern (single assertion focus)
- Use real data and realistic scenarios
- All test code must use type hints
- All public test functions/classes must have docstrings

### **🚫 Testing Anti-Patterns to Avoid**
- Unclear or generic test names (e.g., `test_1`, `test_scraper`)
- Testing multiple things in one test
- Tests that depend on external services without mocking
- Fabricated or placeholder test data
- Flaky tests (tests that fail intermittently)

### **📝 Test Naming Conventions**
- Use `test_<function>_<scenario>_<expectedresult>`
- Use parameterization for input variations
- Use docstrings to describe the test's purpose

---

## 🛠️ **Test Configuration and Setup**

### **🧩 pytest.ini Configuration**
- All tests must be discoverable by pytest
- Use strict markers and config
- Mark slow, integration, and performance tests appropriately

### **🔧 Test Dependencies and Fixtures**
- Use fixtures for setup/teardown and shared test data
- Use mocking for all external dependencies (network, database, APIs, browser, etc.)
- All tests must be isolated and not depend on global state

---

## 🚦 **Quality Gates for Tests**

### **✅ Mandatory Test Requirements**
- [ ] **Functionality**: Test passes and validates correct behavior
- [ ] **Isolation**: Test runs independently and doesn't affect other tests
- [ ] **Performance**: Test completes within 30 seconds (mark slow tests)
- [ ] **Real Data**: Uses authentic profile data and realistic scenarios
- [ ] **Error Handling**: Tests both success and failure cases
- [ ] **Clean Code**: Follows same code quality standards as production
- [ ] **Documentation**: Test purpose is clear from name and docstring
- [ ] **Mocking**: External dependencies are properly mocked
- [ ] **CI/CD**: All tests must pass in CI before merge

### **🎯 Test Coverage Targets**
- **Core Business Logic**: 90% coverage minimum
- **Scrapers**: 80% coverage (focus on error handling)
- **Utils**: 85% coverage (critical utility functions)
- **Dashboard**: 70% coverage (UI components)
- **Overall Project**: 80% coverage target

### **⚡ Performance Requirements**
- **Unit Tests**: < 1 second each
- **Integration Tests**: < 10 seconds each
- **Performance Tests**: < 60 seconds each (marked as slow)
- **Full Test Suite**: < 5 minutes total execution time

---

## 🔄 **Test Workflow Standards**

### **📝 Writing and Reviewing Tests**
1. Write failing test first for new features (TDD encouraged)
2. Get test passing, then refactor for quality
3. Test edge cases and error scenarios
4. Use real user workflows and data
5. All new or changed tests must be reviewed for coverage, clarity, and isolation

### **🛡️ Flaky Test Management**
- All flaky tests must be fixed or removed before merge
- Use retries only for known external flakiness (e.g., network instability)
- Document any known test flakiness and mitigation

---

## 🚀 **CI/CD Integration**
- All tests must run and pass in CI before merge
- Test failures in CI are blocking and must be fixed before proceeding
- Test coverage reports must be generated and reviewed in CI
- Linting and formatting checks must run in CI

---

> For project-wide quality gates, see DEVELOPMENT_STANDARDS.md.
