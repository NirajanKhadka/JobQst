# 🛠️ Scripts Directory

Utility scripts for development, testing, maintenance, and automation tasks.

## 📁 Available Scripts

### 🔍 **Health & Monitoring**
- **`production_health_check.ps1`** - System health validation and monitoring
- **`file_size_audit.ps1`** - File size analysis and architecture compliance

### 🧪 **Testing & Validation**
- **`run_tests.bat`** - Windows batch script for test execution
- **`simple_test.ps1`** - Quick PowerShell testing script
- **`test_all_tools.ps1`** - Comprehensive tool validation

### 🚀 **Development & Deployment**
- **`start_dev_environment.ps1`** - Development environment setup
- **`update_docs.py`** - Documentation update automation

### 📊 **Analysis & Maintenance**
- **PowerShell Scripts**: System monitoring and maintenance utilities
- **Python Scripts**: Code analysis and documentation automation

## 🎯 **Quick Usage**

```powershell
# Health monitoring
.\production_health_check.ps1

# Run all tests
.\run_tests.bat

# Start development environment
.\start_dev_environment.ps1

# Update documentation
python update_docs.py
```

## � **Integration**

These scripts integrate with:
- **Microservices Architecture**: Health checking and monitoring
- **Test Framework**: Automated test execution and validation
- **Documentation System**: Automated documentation updates
- **Development Workflow**: Environment setup and maintenance

---

*For detailed usage instructions, see individual script documentation or run scripts with `--help` parameter.*
- **`update_docs.py`** - Update documentation automatically

### 🚀 Development Environment
- **`start_dev_environment.ps1`** - Start complete development environment
- **`fix_port_conflict.bat`** - Resolve port conflicts
- **`install_gemini.bat`** - Install Gemini AI dependencies

### 🕷️ Web Scraping
- **`launch_scrapers.bat`** - Windows batch scraper launcher
- **`launch_scrapers.ps1`** - PowerShell scraper launcher
- **`job_application_orchestrator.py`** - Orchestrate job application process

### 🧪 Testing
- **`run_tests.bat`** - Run all tests (Windows batch)
- **`simple_test.ps1`** - Simple PowerShell test runner
- **`test_all_tools.ps1`** - Test all development tools

## 🚀 Common Usage

### Start Development Environment
```powershell
# PowerShell - Full development setup
.\scripts\start_dev_environment.ps1

# Windows Command Prompt
scripts\install_gemini.bat
```

### Run Cleanup Operations
```bash
# Python-based cleanup
python scripts\cleanup_workspace.py

# Analyze duplicate code
python scripts\duplicate_analyzer.py

# Migrate test files
python scripts\test_file_migrator.py
```

### Testing & Validation
```bash
# Run all tests
scripts\run_tests.bat

# Validate refactoring
python scripts\validate_refactoring.py

# Test specific tools
.\scripts\test_all_tools.ps1
```

### Web Scraping Operations
```bash
# Launch scrapers
scripts\launch_scrapers.bat

# Orchestrate job applications
python scripts\job_application_orchestrator.py
```

## 🔧 Script Dependencies

### Python Scripts
- **Python 3.11+** required
- **Rich** library for console output
- **pathlib** for file operations
- **ast** for code analysis
- **importlib** for dynamic imports

### PowerShell Scripts
- **PowerShell 5.1+** (Windows)
- **Execution Policy**: Set to RemoteSigned or Unrestricted
- **Administrative privileges** may be required

### Batch Scripts
- **Windows Command Prompt**
- **Administrative privileges** for some operations

## 📋 Script Documentation

### Cleanup Scripts
- **Purpose**: Maintain clean workspace, remove temporary files
- **Frequency**: Run before commits or weekly
- **Safety**: Always backup before running cleanup

### Analysis Scripts
- **Purpose**: Code quality analysis, duplicate detection
- **Usage**: Part of code review process
- **Output**: Detailed reports and suggestions

### Development Scripts
- **Purpose**: Streamline development workflow
- **Setup**: One-time environment configuration
- **Maintenance**: Regular updates and testing

### Testing Scripts
- **Purpose**: Automated testing and validation
- **Integration**: CI/CD pipeline compatibility
- **Coverage**: Comprehensive test execution

## ⚙️ Configuration

### Environment Variables
```bash
# Set in your environment or .env file
PYTHONPATH=d:\automate_job
SCRAPER_HEADLESS=true
LOG_LEVEL=INFO
```

### Script Execution Policy (PowerShell)
```powershell
# Allow local script execution
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 🛡️ Safety Guidelines

### Before Running Scripts
1. **Backup your work** - Always commit or backup before cleanup
2. **Read script documentation** - Understand what each script does
3. **Test in development** - Never run untested scripts in production
4. **Check dependencies** - Ensure all required tools are installed

### Best Practices
- **Version Control**: Keep scripts under version control
- **Documentation**: Comment complex operations
- **Error Handling**: Include proper error handling
- **Logging**: Log important operations and results

## 🔄 Maintenance Schedule

### Daily
- `test_all_tools.ps1` - Verify development environment

### Weekly
- `cleanup_workspace.py` - Clean temporary files
- `validate_refactoring.py` - Check code quality

### Monthly
- `duplicate_analyzer.py` - Analyze code duplication
- `update_docs.py` - Refresh documentation

### As Needed
- `function_deduplicator.py` - Major refactoring
- `test_file_migrator.py` - Test organization
- `start_dev_environment.ps1` - New environment setup

## 🚨 Troubleshooting

### Common Issues
1. **PowerShell Execution Policy**: Run `Set-ExecutionPolicy RemoteSigned`
2. **Python Path Issues**: Ensure PYTHONPATH includes project root
3. **Port Conflicts**: Run `fix_port_conflict.bat`
4. **Missing Dependencies**: Run `install_gemini.bat`

### Debug Mode
```bash
# Run scripts with verbose output
python scripts\cleanup_workspace.py --verbose
.\scripts\test_all_tools.ps1 -Verbose
```

---

*These scripts are essential tools for maintaining the AutoJobAgent codebase. Use them regularly to ensure optimal development workflow.*
