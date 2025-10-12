# Scripts Directory

This directory contains various scripts for building, testing, and releasing the arxiv-writer package.

## Release Preparation Scripts

### `release_checklist.py`
Runs a comprehensive checklist to validate that the package is ready for release.

**Usage:**
```bash
python scripts/release_checklist.py
```

**Checks:**
- Version consistency across files
- Git repository status
- Package metadata validation
- Documentation completeness
- Test suite execution
- Security scans
- Build artifacts validation
- CLI functionality

### `validate_release.py`
Performs comprehensive release validation including all quality checks.

**Usage:**
```bash
python scripts/validate_release.py
```

**Features:**
- Package structure validation
- Dependency validation
- CLI functionality testing
- Test coverage validation
- Security scanning
- Build and installation testing
- Documentation validation
- Generates detailed JSON report

### `build_and_test.py`
Comprehensive build and test script that handles the complete build pipeline.

**Usage:**
```bash
python scripts/build_and_test.py
```

**Features:**
- Cleans build artifacts
- Runs linting and formatting checks
- Executes test suite with coverage
- Performs security scans
- Builds package (wheel and sdist)
- Tests package installation
- Generates build report

## Testing Scripts

### `test_pypi_install.py`
Tests package installation from both Test PyPI and production PyPI.

**Usage:**
```bash
python scripts/test_pypi_install.py
```

**Features:**
- Tests Test PyPI installation
- Tests production PyPI installation
- Validates CLI functionality
- Tests package imports
- Creates isolated virtual environments

### `test_isolated_install.py`
Tests package installation in isolated Docker environments across multiple Python versions.

**Usage:**
```bash
python scripts/test_isolated_install.py
```

**Requirements:**
- Docker must be installed and running

**Features:**
- Tests Python 3.8-3.12 in standard images
- Tests Alpine Linux compatibility
- Validates CLI functionality in containers
- Tests package imports and basic functionality
- Generates detailed test report

### `test_cli_entry_point.py`
Comprehensive testing of CLI entry point installation and functionality.

**Usage:**
```bash
python scripts/test_cli_entry_point.py
```

**Features:**
- Tests CLI installation in clean environment
- Validates CLI commands and options
- Tests configuration file handling
- Tests error handling
- Validates module invocation

## Quality Assurance Scripts

### `quality_assurance.py`
Comprehensive quality assurance checks for the package.

**Usage:**
```bash
python scripts/quality_assurance.py
```

**Features:**
- Code quality metrics
- Test coverage analysis
- Documentation completeness
- Performance benchmarks
- Security vulnerability assessment

### `validate_codexes_integration.py`
Validates integration with Codexes Factory for backward compatibility.

**Usage:**
```bash
python scripts/validate_codexes_integration.py
```

**Features:**
- Tests Codexes Factory adapter
- Validates configuration migration
- Tests compatibility mode
- Verifies identical output generation

## Usage Examples

### Complete Release Preparation
```bash
# Run all release preparation steps
make prepare-release

# Or manually:
python scripts/build_and_test.py
python scripts/validate_release.py
python scripts/test_isolated_install.py
```

### Quick Quality Check
```bash
# Run basic quality checks
python scripts/release_checklist.py

# Run comprehensive validation
python scripts/validate_release.py
```

### Test PyPI Release
```bash
# After uploading to Test PyPI
python scripts/test_pypi_install.py

# Test in isolated environments
python scripts/test_isolated_install.py
```

### CLI Testing
```bash
# Test CLI functionality
python scripts/test_cli_entry_point.py

# Test with different configurations
python scripts/test_cli_entry_point.py --config examples/configs/basic_config.json
```

## Integration with CI/CD

These scripts are integrated with GitHub Actions workflows:

- **CI Workflow** (`.github/workflows/ci.yml`): Runs `build_and_test.py`
- **Release Workflow** (`.github/workflows/release.yml`): Uses `validate_release.py`
- **Security Workflow** (`.github/workflows/security.yml`): Runs security scans
- **Test PyPI Workflow** (`.github/workflows/test-pypi-release.yml`): Uses `test_pypi_install.py`

## Configuration Files

### `.bandit`
Configuration for Bandit security scanner:
- Excludes test directories
- Configures severity levels
- Defines test coverage

### Security Reports
Scripts generate various security reports:
- `safety-report.json` - Dependency vulnerability report
- `bandit-report.json` - Code security scan report
- `semgrep-report.json` - Static analysis report

## Output Files

Scripts generate various output files:
- `build-report.json` - Build process report
- `release-validation-report.json` - Release validation report
- `isolated-test-results.json` - Docker test results
- `coverage.xml` - Test coverage report
- `htmlcov/` - HTML coverage report

## Requirements

### System Requirements
- Python 3.8+
- Git
- Docker (for isolated testing)
- Make (optional, for Makefile targets)

### Python Dependencies
Scripts automatically install required dependencies:
- `build` - Package building
- `twine` - Package validation and upload
- `safety` - Dependency security scanning
- `bandit` - Code security scanning
- `semgrep` - Static analysis
- `pytest` - Testing framework
- `coverage` - Test coverage

## Troubleshooting

### Common Issues

1. **Docker not available**
   ```bash
   # Install Docker or skip isolated tests
   python scripts/validate_release.py  # Skips Docker tests
   ```

2. **Security scan failures**
   ```bash
   # Review security reports
   cat safety-report.json
   cat bandit-report.json
   ```

3. **Build failures**
   ```bash
   # Clean and rebuild
   make clean
   python scripts/build_and_test.py
   ```

4. **CLI entry point issues**
   ```bash
   # Reinstall package
   pip install -e .
   python scripts/test_cli_entry_point.py
   ```

### Getting Help

For issues with specific scripts:
1. Check the script's help output: `python scripts/script_name.py --help`
2. Review the generated report files
3. Check GitHub Actions logs for CI/CD issues
4. Consult the main project documentation

## Contributing

When adding new scripts:
1. Follow the existing naming convention
2. Include comprehensive error handling
3. Generate appropriate reports/logs
4. Add documentation to this README
5. Include the script in relevant Makefile targets
6. Add appropriate GitHub Actions integration