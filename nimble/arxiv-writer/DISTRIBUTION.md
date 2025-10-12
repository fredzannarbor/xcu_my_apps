# Distribution Guide for arxiv-writer

This document provides comprehensive instructions for preparing and distributing the arxiv-writer package to PyPI.

## Overview

The arxiv-writer package is configured for distribution to PyPI using modern Python packaging standards:
- **Build System**: Hatchling (PEP 517/518 compliant)
- **Configuration**: pyproject.toml (PEP 621)
- **CI/CD**: GitHub Actions
- **Security**: Automated vulnerability scanning
- **Testing**: Multi-platform, multi-version testing

## Prerequisites

### System Requirements
- Python 3.8+ (3.11+ recommended for development)
- Git
- Docker (for isolated testing)
- GitHub account with appropriate repository access

### Required Accounts
- **PyPI Account**: For production releases
- **Test PyPI Account**: For testing releases
- **GitHub**: For CI/CD and releases

### Environment Setup
```bash
# Clone repository
git clone https://github.com/ailabforbooklovers/arxiv-writer.git
cd arxiv-writer

# Install development dependencies
pip install -e ".[dev,latex,docs]"

# Install build tools
pip install build twine

# Install security tools
pip install safety bandit semgrep
```

## Package Configuration

### pyproject.toml
The package is configured in `pyproject.toml` with:
- **Metadata**: Name, version, description, authors
- **Dependencies**: Core and optional dependencies
- **Build Configuration**: Hatchling backend
- **Tool Configuration**: pytest, mypy, ruff, black
- **Entry Points**: CLI command registration

### Version Management
Version is managed in two places:
- `pyproject.toml`: `project.version`
- `src/arxiv_writer/__init__.py`: `__version__`

Both must be kept in sync for releases.

## Build Process

### Manual Build
```bash
# Clean previous builds
make clean

# Build package
python -m build

# Verify build
twine check dist/*
```

### Automated Build
```bash
# Run comprehensive build and test
make prepare-release

# Or use the build script
python scripts/build_and_test.py
```

## Testing Infrastructure

### Local Testing
```bash
# Run test suite
make test

# Run linting
make lint

# Run security scans
make security

# Test CLI functionality
python scripts/test_cli_entry_point.py
```

### Isolated Testing
```bash
# Test in Docker containers
python scripts/test_isolated_install.py

# Test PyPI installation
python scripts/test_pypi_install.py
```

### CI/CD Testing
GitHub Actions automatically run:
- **Multi-platform testing**: Ubuntu, Windows, macOS
- **Multi-version testing**: Python 3.8-3.12
- **Security scanning**: Safety, Bandit, Semgrep, CodeQL
- **Build validation**: Package building and installation
- **Docker testing**: Alpine and Ubuntu containers

## Release Process

### 1. Pre-Release Validation
```bash
# Run release checklist
python scripts/release_checklist.py

# Run comprehensive validation
python scripts/validate_release.py
```

### 2. Version Update
Update version in both files:
```bash
# Update pyproject.toml
sed -i 's/version = "0.1.0"/version = "0.2.0"/' pyproject.toml

# Update __init__.py
sed -i 's/__version__ = "0.1.0"/__version__ = "0.2.0"/' src/arxiv_writer/__init__.py
```

### 3. Update Changelog
Add release notes to `CHANGELOG.md`:
```markdown
## [0.2.0] - 2024-01-15

### Added
- New feature descriptions

### Changed
- Changed feature descriptions

### Fixed
- Bug fix descriptions
```

### 4. Commit and Tag
```bash
# Commit changes
git add .
git commit -m "Release v0.2.0"

# Create and push tag
git tag v0.2.0
git push origin main
git push origin v0.2.0
```

### 5. Automated Release
GitHub Actions will automatically:
1. Run full test suite
2. Build package
3. Upload to Test PyPI
4. Test installation from Test PyPI
5. Upload to production PyPI (if tests pass)
6. Create GitHub release

## Manual PyPI Upload

If needed, you can manually upload to PyPI:

### Test PyPI
```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ arxiv-writer
```

### Production PyPI
```bash
# Upload to production PyPI
twine upload dist/*

# Test installation
pip install arxiv-writer
```

## Security Configuration

### API Tokens
Configure these secrets in GitHub repository settings:
- `PYPI_API_TOKEN`: Production PyPI token
- `TEST_PYPI_API_TOKEN`: Test PyPI token

### Security Scanning
Automated security scans include:
- **Safety**: Dependency vulnerability scanning
- **Bandit**: Code security analysis
- **Semgrep**: Static analysis for security issues
- **CodeQL**: GitHub's semantic code analysis
- **Dependency Review**: GitHub's dependency analysis

### Configuration Files
- `.bandit`: Bandit security scanner configuration
- `.semgrepignore`: Semgrep exclusions
- `.github/workflows/security.yml`: Security workflow

## Quality Assurance

### Test Coverage
- **Minimum Coverage**: 90%
- **Coverage Reports**: HTML, XML, and terminal
- **Coverage Tools**: pytest-cov

### Code Quality
- **Linting**: Ruff
- **Formatting**: Black
- **Type Checking**: MyPy
- **Import Sorting**: Ruff (isort rules)

### Documentation
- **API Documentation**: Sphinx with autodoc
- **User Guide**: RST format in docs/
- **Examples**: Working examples in examples/
- **README**: Comprehensive package overview

## Distribution Validation

### Pre-Release Checklist
- [ ] Version updated in all files
- [ ] CHANGELOG.md updated
- [ ] All tests pass locally
- [ ] Security scans pass
- [ ] Documentation builds successfully
- [ ] CLI functionality works
- [ ] Package builds without errors
- [ ] Installation test passes

### Post-Release Validation
- [ ] Test PyPI installation works
- [ ] Production PyPI installation works
- [ ] CLI entry point works after installation
- [ ] All imports work correctly
- [ ] Documentation is accessible
- [ ] GitHub release created

## Troubleshooting

### Common Issues

#### Build Failures
```bash
# Clean and retry
make clean
python -m build

# Check for syntax errors
python -m py_compile src/arxiv_writer/**/*.py
```

#### Test Failures
```bash
# Run specific test
pytest tests/test_specific.py -v

# Run with debugging
pytest --pdb tests/test_specific.py
```

#### Security Scan Issues
```bash
# Review security reports
cat safety-report.json
cat bandit-report.json

# Update dependencies
pip install --upgrade -r requirements.txt
```

#### CLI Entry Point Issues
```bash
# Reinstall package
pip install -e .

# Test CLI
python scripts/test_cli_entry_point.py
```

### GitHub Actions Issues

#### Workflow Failures
1. Check workflow logs in GitHub Actions tab
2. Review failed step output
3. Check for environment-specific issues
4. Verify secrets are configured correctly

#### PyPI Upload Failures
1. Verify API tokens are correct
2. Check package name availability
3. Ensure version number is unique
4. Verify package metadata is valid

## Monitoring and Maintenance

### Post-Release Monitoring
- Monitor PyPI download statistics
- Watch for user-reported issues
- Monitor security advisories
- Track dependency updates

### Regular Maintenance
- Update dependencies monthly
- Run security scans weekly
- Update documentation as needed
- Review and update CI/CD workflows

### Version Strategy
- **Major versions** (1.0.0): Breaking changes
- **Minor versions** (0.1.0): New features, backward compatible
- **Patch versions** (0.0.1): Bug fixes, backward compatible

## Resources

### Documentation
- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

### Tools
- [build](https://pypa-build.readthedocs.io/): Modern Python package builder
- [twine](https://twine.readthedocs.io/): PyPI upload tool
- [hatchling](https://hatch.pypa.io/): Modern build backend

### Security
- [Safety](https://pyup.io/safety/): Dependency vulnerability scanner
- [Bandit](https://bandit.readthedocs.io/): Security linter for Python
- [Semgrep](https://semgrep.dev/): Static analysis tool

## Support

For distribution-related issues:
1. Check this documentation
2. Review GitHub Actions logs
3. Consult PyPI documentation
4. Open an issue in the repository

For package-specific issues:
1. Check the main README.md
2. Review documentation in docs/
3. Check existing GitHub issues
4. Open a new issue with detailed information