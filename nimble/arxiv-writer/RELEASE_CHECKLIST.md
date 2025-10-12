# Release Checklist for arxiv-writer

This checklist ensures that all necessary steps are completed before releasing the arxiv-writer package to PyPI.

## Pre-Release Checklist

### Code Quality
- [ ] All tests pass locally (`make test`)
- [ ] Code coverage is >90% (`pytest --cov=arxiv_writer --cov-report=term-missing`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`mypy src`)
- [ ] Code formatting is correct (`black --check src tests`)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)

### Security
- [ ] Security scan passes (`make security`)
- [ ] No known vulnerabilities in dependencies (`safety check`)
- [ ] Bandit security scan passes (`bandit -r src`)
- [ ] Semgrep security scan passes (`semgrep --config=auto src`)

### Documentation
- [ ] README.md is up to date
- [ ] CHANGELOG.md includes new version
- [ ] API documentation is complete
- [ ] Examples work correctly
- [ ] Installation instructions are accurate

### Package Configuration
- [ ] Version number updated in `src/arxiv_writer/__init__.py`
- [ ] Version number updated in `pyproject.toml`
- [ ] Package metadata is correct in `pyproject.toml`
- [ ] Dependencies are properly specified
- [ ] Optional dependencies are correctly configured
- [ ] CLI entry points are properly defined

### Testing
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Cross-platform tests pass (Linux, macOS, Windows)
- [ ] Python version compatibility tests pass (3.8-3.12)
- [ ] CLI entry point tests pass
- [ ] Docker tests pass (`make docker-test`)

## Build and Distribution

### Package Build
- [ ] Clean build artifacts (`make clean`)
- [ ] Package builds successfully (`make build`)
- [ ] Package check passes (`twine check dist/*`)
- [ ] Wheel and source distribution created
- [ ] Package installs correctly in clean environment

### Test PyPI Release
- [ ] Upload to Test PyPI successful
- [ ] Package installs from Test PyPI (`pip install --index-url https://test.pypi.org/simple/ arxiv-writer`)
- [ ] CLI works after Test PyPI installation
- [ ] Core functionality works after Test PyPI installation
- [ ] All entry points work correctly

### Production Release
- [ ] Tag created with version number (`git tag v0.1.0`)
- [ ] Tag pushed to repository (`git push origin v0.1.0`)
- [ ] GitHub Actions release workflow triggered
- [ ] Upload to production PyPI successful
- [ ] GitHub release created with release notes

## Post-Release Validation

### Installation Testing
- [ ] Package installs from PyPI (`pip install arxiv-writer`)
- [ ] CLI entry point works (`arxiv-writer --help`)
- [ ] Package imports correctly (`python -c "import arxiv_writer"`)
- [ ] Core functionality works
- [ ] Examples run successfully

### Cross-Platform Validation
- [ ] Installation works on Linux
- [ ] Installation works on macOS  
- [ ] Installation works on Windows
- [ ] CLI works on all platforms
- [ ] Core functionality works on all platforms

### Python Version Validation
- [ ] Works with Python 3.8
- [ ] Works with Python 3.9
- [ ] Works with Python 3.10
- [ ] Works with Python 3.11
- [ ] Works with Python 3.12

## Release Commands

### Local Testing
```bash
# Run full test suite
make test

# Run security checks
make security

# Build package
make build

# Test installation
make test-install
```

### Docker Testing
```bash
# Test in Docker containers
make docker-test

# Test production installation
./scripts/test_production_install.sh
```

### Release Process
```bash
# Update version numbers
# Update CHANGELOG.md
# Commit changes
git add .
git commit -m "Prepare release v0.1.0"

# Create and push tag
git tag v0.1.0
git push origin main
git push origin v0.1.0

# GitHub Actions will handle the rest
```

### Manual Release (if needed)
```bash
# Build package
python -m build

# Check package
twine check dist/*

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ arxiv-writer

# Upload to production PyPI
twine upload dist/*
```

## Rollback Plan

If issues are discovered after release:

1. **Immediate Actions**
   - [ ] Document the issue
   - [ ] Assess impact and severity
   - [ ] Communicate with users if necessary

2. **Fix and Re-release**
   - [ ] Create hotfix branch
   - [ ] Fix the issue
   - [ ] Increment patch version
   - [ ] Follow full release process
   - [ ] Test thoroughly

3. **PyPI Management**
   - [ ] Consider yanking problematic version if severe
   - [ ] Update package description with fix information
   - [ ] Monitor for user reports

## Notes

- Always test in clean environments before release
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Keep detailed release notes
- Monitor PyPI download statistics
- Respond to user issues promptly
- Maintain backward compatibility when possible