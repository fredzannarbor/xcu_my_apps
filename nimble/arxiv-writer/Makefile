# Makefile for arxiv-writer package

.PHONY: help clean install install-dev test lint format security build test-install docker-test release

# Default target
help:
	@echo "Available targets:"
	@echo "  help             - Show this help message"
	@echo "  clean            - Clean build artifacts"
	@echo "  install          - Install package"
	@echo "  install-dev      - Install package in development mode"
	@echo "  test             - Run test suite"
	@echo "  lint             - Run linting and type checking"
	@echo "  format           - Format code with black"
	@echo "  security         - Run security checks"
	@echo "  build            - Build package"
	@echo "  test-install     - Test package installation"
	@echo "  docker-test      - Run tests in Docker"
	@echo "  release          - Full build and test for release"
	@echo "  release-checklist - Run release checklist validation"
	@echo "  validate-release - Run comprehensive release validation"
	@echo "  test-isolated    - Test installation in isolated environments"
	@echo "  prepare-release  - Run all release preparation steps"

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -f .coverage
	rm -f *.json

# Install package
install:
	pip install .

# Install package in development mode
install-dev:
	pip install -e ".[dev,latex,docs]"

# Run test suite
test:
	pytest -v --cov=arxiv_writer --cov-report=term-missing --cov-report=html --cov-report=xml

# Run linting and type checking
lint:
	ruff check src tests
	black --check src tests
	mypy src

# Format code
format:
	black src tests
	ruff check --fix src tests

# Run security checks
security:
	safety check
	bandit -r src
	semgrep --config=auto src

# Build package
build: clean
	python -m build
	twine check dist/*

# Test package installation
test-install: build
	python scripts/test_pypi_install.py

# Run tests in Docker
docker-test: build
	docker-compose -f docker/docker-compose.test.yml up --build --abort-on-container-exit

# Full build and test for release
release:
	python scripts/build_and_test.py

# Install build dependencies
install-build-deps:
	pip install build twine

# Install security tools
install-security-tools:
	pip install safety bandit semgrep

# Install all development dependencies
install-all-deps: install-dev install-build-deps install-security-tools

# Quick development setup
dev-setup: install-all-deps
	pre-commit install

# Run pre-commit hooks
pre-commit:
	pre-commit run --all-files

# Generate documentation
docs:
	cd docs && make html

# Serve documentation locally
docs-serve:
	cd docs/_build/html && python -m http.server 8000

# Test CLI functionality
test-cli:
	arxiv-writer --help
	arxiv-writer --version

# Run integration tests
test-integration:
	pytest tests/ -m integration -v

# Run unit tests only
test-unit:
	pytest tests/ -m "not integration" -v

# Performance tests
test-performance:
	pytest tests/ -m slow -v

# Test with different Python versions (requires pyenv or similar)
test-all-python:
	@echo "Testing with Python 3.8..."
	python3.8 -m pytest tests/ -v || echo "Python 3.8 tests failed"
	@echo "Testing with Python 3.9..."
	python3.9 -m pytest tests/ -v || echo "Python 3.9 tests failed"
	@echo "Testing with Python 3.10..."
	python3.10 -m pytest tests/ -v || echo "Python 3.10 tests failed"
	@echo "Testing with Python 3.11..."
	python3.11 -m pytest tests/ -v || echo "Python 3.11 tests failed"
	@echo "Testing with Python 3.12..."
	python3.12 -m pytest tests/ -v || echo "Python 3.12 tests failed"

# Release preparation targets
release-checklist: install-dev lint test security build
	@echo "Running release checklist..."
	python scripts/release_checklist.py

validate-release: install-dev
	@echo "Running comprehensive release validation..."
	python scripts/validate_release.py

test-isolated: build
	@echo "Testing installation in isolated environments..."
	python scripts/test_isolated_install.py

prepare-release: clean install-dev lint test security build validate-release
	@echo "Release preparation complete!"
	@echo "Review the validation report and run 'make test-isolated' if needed."
	@echo "If all checks pass, create a git tag and push to trigger release."