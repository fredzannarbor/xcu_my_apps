Release and Deployment Guide
============================

This guide covers the release process, versioning strategy, and deployment procedures for ArXiv Writer.

Release Strategy
----------------

Versioning
~~~~~~~~~~

ArXiv Writer follows Semantic Versioning (SemVer) 2.0.0:

- **MAJOR** (X.0.0) - Breaking changes that require user action
- **MINOR** (0.X.0) - New features that are backward compatible
- **PATCH** (0.0.X) - Bug fixes that are backward compatible

**Version Examples:**

.. code-block:: text

   1.0.0 → 1.0.1  # Bug fix release
   1.0.1 → 1.1.0  # New feature release
   1.1.0 → 2.0.0  # Breaking change release

**Pre-release Versions:**

.. code-block:: text

   1.1.0-alpha.1  # Alpha release
   1.1.0-beta.1   # Beta release
   1.1.0-rc.1     # Release candidate

Release Types
~~~~~~~~~~~~~

**Patch Releases (1.0.X)**
- Bug fixes
- Security patches
- Documentation updates
- Performance improvements (non-breaking)

**Minor Releases (1.X.0)**
- New features
- New LLM provider support
- New output formats
- Enhanced CLI commands
- Backward-compatible API changes

**Major Releases (X.0.0)**
- Breaking API changes
- Major architecture changes
- Removal of deprecated features
- Significant behavior changes

Release Process
---------------

Pre-Release Checklist
~~~~~~~~~~~~~~~~~~~~~

Before starting a release:

1. **Code Quality**
   - [ ] All tests pass on all supported platforms
   - [ ] Code coverage meets minimum threshold (90%)
   - [ ] No critical security vulnerabilities
   - [ ] Code review completed for all changes

2. **Documentation**
   - [ ] CHANGELOG.md updated with all changes
   - [ ] API documentation updated
   - [ ] User guide reflects new features
   - [ ] Migration guide updated (for breaking changes)

3. **Testing**
   - [ ] Integration tests pass with real LLM providers
   - [ ] Cross-platform compatibility verified
   - [ ] Performance benchmarks within acceptable range
   - [ ] Manual testing of new features completed

4. **Dependencies**
   - [ ] All dependencies up to date
   - [ ] Security audit of dependencies completed
   - [ ] Compatibility with supported Python versions verified

Release Steps
~~~~~~~~~~~~~

**Step 1: Prepare Release Branch**

.. code-block:: bash

   # Create release branch from develop
   git checkout develop
   git pull origin develop
   git checkout -b release/1.2.0

**Step 2: Update Version Numbers**

Update version in all relevant files:

.. code-block:: bash

   # pyproject.toml
   [project]
   version = "1.2.0"

   # src/arxiv_writer/__init__.py
   __version__ = "1.2.0"

   # docs/conf.py
   release = '1.2.0'

**Step 3: Update Changelog**

.. code-block:: markdown

   # CHANGELOG.md
   
   ## [1.2.0] - 2024-03-15
   
   ### Added
   - Support for Anthropic Claude-3 models
   - New plugin system for custom formatters
   - Advanced configuration validation
   
   ### Changed
   - Improved error messages with suggestions
   - Enhanced template inheritance system
   
   ### Fixed
   - LaTeX compilation issues on Windows
   - Memory leak in large context processing
   
   ### Deprecated
   - Old configuration format (will be removed in 2.0.0)

**Step 4: Run Full Test Suite**

.. code-block:: bash

   # Run all tests
   pytest tests/ -v
   
   # Run integration tests with real providers
   pytest tests/integration/ -v --real-llm
   
   # Run performance tests
   pytest tests/performance/ -v
   
   # Generate coverage report
   pytest --cov=src/arxiv_writer --cov-report=html

**Step 5: Build and Test Package**

.. code-block:: bash

   # Clean previous builds
   rm -rf dist/ build/ *.egg-info/
   
   # Build package
   python -m build
   
   # Test installation in clean environment
   python -m venv test_env
   source test_env/bin/activate
   pip install dist/arxiv_writer-1.2.0-py3-none-any.whl
   
   # Test basic functionality
   arxiv-writer --version
   python -c "import arxiv_writer; print(arxiv_writer.__version__)"

**Step 6: Create Release Commit**

.. code-block:: bash

   # Commit version updates
   git add .
   git commit -m "chore: prepare release 1.2.0"
   
   # Push release branch
   git push origin release/1.2.0

**Step 7: Create Pull Request**

Create PR from release branch to main:

.. code-block:: markdown

   ## Release 1.2.0
   
   ### Summary
   This release adds support for Anthropic Claude-3 models and introduces a new plugin system.
   
   ### Changes
   - [x] Version numbers updated
   - [x] Changelog updated
   - [x] Tests passing
   - [x] Documentation updated
   
   ### Testing
   - [x] Unit tests: ✅ 
   - [x] Integration tests: ✅
   - [x] Cross-platform tests: ✅
   - [x] Manual testing: ✅

**Step 8: Merge and Tag**

After PR approval:

.. code-block:: bash

   # Merge to main
   git checkout main
   git pull origin main
   
   # Create and push tag
   git tag -a v1.2.0 -m "Release version 1.2.0"
   git push origin v1.2.0
   
   # Merge back to develop
   git checkout develop
   git merge main
   git push origin develop

**Step 9: Publish Release**

.. code-block:: bash

   # Upload to PyPI
   python -m twine upload dist/*
   
   # Create GitHub release
   gh release create v1.2.0 \
     --title "ArXiv Writer v1.2.0" \
     --notes-file RELEASE_NOTES.md \
     --draft

Automated Release Pipeline
--------------------------

GitHub Actions Workflow
~~~~~~~~~~~~~~~~~~~~~~~

**.github/workflows/release.yml:**

.. code-block:: yaml

   name: Release
   
   on:
     push:
       tags:
         - 'v*'
   
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         
         - name: Install dependencies
           run: |
             python -m pip install --upgrade pip
             pip install -e ".[dev,test]"
         
         - name: Run tests
           run: |
             pytest tests/ -v --cov=src/arxiv_writer
   
     build:
       needs: test
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         
         - name: Install build dependencies
           run: |
             python -m pip install --upgrade pip
             pip install build twine
         
         - name: Build package
           run: python -m build
         
         - name: Check package
           run: twine check dist/*
         
         - name: Upload artifacts
           uses: actions/upload-artifact@v3
           with:
             name: dist
             path: dist/
   
     publish-pypi:
       needs: build
       runs-on: ubuntu-latest
       environment: release
       steps:
         - name: Download artifacts
           uses: actions/download-artifact@v3
           with:
             name: dist
             path: dist/
         
         - name: Publish to PyPI
           uses: pypa/gh-action-pypi-publish@release/v1
           with:
             password: ${{ secrets.PYPI_API_TOKEN }}
   
     create-release:
       needs: publish-pypi
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Extract release notes
           id: extract-notes
           run: |
             VERSION=${GITHUB_REF#refs/tags/v}
             sed -n "/## \[$VERSION\]/,/## \[/p" CHANGELOG.md | head -n -1 > RELEASE_NOTES.md
         
         - name: Create GitHub Release
           uses: actions/create-release@v1
           env:
             GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
           with:
             tag_name: ${{ github.ref }}
             release_name: ArXiv Writer ${{ github.ref }}
             body_path: RELEASE_NOTES.md
             draft: false
             prerelease: false

Package Configuration
---------------------

pyproject.toml
~~~~~~~~~~~~~~

.. code-block:: toml

   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   
   [project]
   name = "arxiv-writer"
   version = "1.2.0"
   description = "AI-assisted academic paper generation in arXiv format"
   readme = "README.md"
   license = {file = "LICENSE"}
   authors = [
       {name = "ArXiv Writer Contributors", email = "contributors@arxiv-writer.org"}
   ]
   maintainers = [
       {name = "ArXiv Writer Team", email = "maintainers@arxiv-writer.org"}
   ]
   keywords = ["academic", "paper", "generation", "ai", "llm", "latex", "arxiv"]
   classifiers = [
       "Development Status :: 4 - Beta",
       "Intended Audience :: Science/Research",
       "Intended Audience :: Education",
       "License :: OSI Approved :: MIT License",
       "Operating System :: OS Independent",
       "Programming Language :: Python :: 3",
       "Programming Language :: Python :: 3.8",
       "Programming Language :: Python :: 3.9",
       "Programming Language :: Python :: 3.10",
       "Programming Language :: Python :: 3.11",
       "Programming Language :: Python :: 3.12",
       "Topic :: Scientific/Engineering",
       "Topic :: Text Processing :: Markup :: LaTeX",
   ]
   requires-python = ">=3.8"
   dependencies = [
       "litellm>=1.72.0",
       "python-dotenv>=1.1.0",
       "pandas>=2.3.0",
       "pydantic>=2.0.0",
       "jinja2>=3.1.0",
       "click>=8.0.0",
       "rich>=13.0.0",
       "pyyaml>=6.0.0",
       "toml>=0.10.0",
   ]
   
   [project.optional-dependencies]
   dev = [
       "pytest>=8.0.0",
       "pytest-cov>=4.0.0",
       "pytest-xdist>=3.0.0",
       "black>=24.0.0",
       "isort>=5.12.0",
       "flake8>=7.0.0",
       "mypy>=1.8.0",
       "pre-commit>=3.0.0",
   ]
   test = [
       "pytest>=8.0.0",
       "pytest-cov>=4.0.0",
       "pytest-mock>=3.12.0",
       "responses>=0.24.0",
   ]
   docs = [
       "sphinx>=7.0.0",
       "sphinx-rtd-theme>=2.0.0",
       "myst-parser>=2.0.0",
   ]
   
   [project.urls]
   Homepage = "https://github.com/ailabforbooklovers/arxiv-writer"
   Documentation = "https://arxiv-writer.readthedocs.io"
   Repository = "https://github.com/ailabforbooklovers/arxiv-writer.git"
   Issues = "https://github.com/ailabforbooklovers/arxiv-writer/issues"
   Changelog = "https://github.com/ailabforbooklovers/arxiv-writer/blob/main/CHANGELOG.md"
   
   [project.scripts]
   arxiv-writer = "arxiv_writer.cli.main:main"

Distribution Channels
---------------------

PyPI Publication
~~~~~~~~~~~~~~~

**Manual Publication:**

.. code-block:: bash

   # Install publishing tools
   pip install build twine
   
   # Build package
   python -m build
   
   # Check package
   twine check dist/*
   
   # Upload to Test PyPI first
   twine upload --repository testpypi dist/*
   
   # Test installation from Test PyPI
   pip install --index-url https://test.pypi.org/simple/ arxiv-writer
   
   # Upload to production PyPI
   twine upload dist/*

**PyPI Configuration (.pypirc):**

.. code-block:: ini

   [distutils]
   index-servers =
       pypi
       testpypi
   
   [pypi]
   username = __token__
   password = pypi-your-api-token
   
   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-your-test-api-token

Docker Images
~~~~~~~~~~~~

**Dockerfile:**

.. code-block:: dockerfile

   FROM python:3.11-slim
   
   # Install LaTeX
   RUN apt-get update && apt-get install -y \
       texlive-latex-base \
       texlive-latex-extra \
       texlive-fonts-recommended \
       && rm -rf /var/lib/apt/lists/*
   
   # Install ArXiv Writer
   RUN pip install arxiv-writer
   
   # Create working directory
   WORKDIR /workspace
   
   # Set entrypoint
   ENTRYPOINT ["arxiv-writer"]

**Build and Publish Docker Image:**

.. code-block:: bash

   # Build image
   docker build -t arxivwriter/arxiv-writer:1.2.0 .
   docker build -t arxivwriter/arxiv-writer:latest .
   
   # Test image
   docker run --rm arxivwriter/arxiv-writer:1.2.0 --version
   
   # Push to Docker Hub
   docker push arxivwriter/arxiv-writer:1.2.0
   docker push arxivwriter/arxiv-writer:latest

Conda Package
~~~~~~~~~~~~

**meta.yaml for conda-forge:**

.. code-block:: yaml

   {% set name = "arxiv-writer" %}
   {% set version = "1.2.0" %}
   
   package:
     name: {{ name|lower }}
     version: {{ version }}
   
   source:
     url: https://pypi.io/packages/source/{{ name[0] }}/{{ name }}/arxiv_writer-{{ version }}.tar.gz
     sha256: {{ sha256 }}
   
   build:
     noarch: python
     script: {{ PYTHON }} -m pip install . -vv
     number: 0
   
   requirements:
     host:
       - python >=3.8
       - pip
       - hatchling
     run:
       - python >=3.8
       - litellm >=1.72.0
       - python-dotenv >=1.1.0
       - pandas >=2.3.0
       - pydantic >=2.0.0
       - jinja2 >=3.1.0
       - click >=8.0.0
   
   test:
     imports:
       - arxiv_writer
     commands:
       - arxiv-writer --help
   
   about:
     home: https://github.com/ailabforbooklovers/arxiv-writer
     summary: AI-assisted academic paper generation in arXiv format
     license: MIT
     license_file: LICENSE

Release Communication
---------------------

Release Notes Template
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: markdown

   # ArXiv Writer v1.2.0 Release Notes
   
   We're excited to announce ArXiv Writer v1.2.0! This release brings significant improvements to LLM provider support and introduces a powerful new plugin system.
   
   ## 🚀 New Features
   
   ### Anthropic Claude-3 Support
   - Full support for Claude-3 Opus, Sonnet, and Haiku models
   - Optimized prompt templates for Claude's capabilities
   - Automatic fallback between OpenAI and Anthropic providers
   
   ### Plugin System
   - Extensible plugin architecture for custom functionality
   - Built-in plugins for IEEE and ACM formatting
   - Plugin development guide and examples
   
   ### Enhanced Configuration
   - Improved validation with helpful error messages
   - Support for YAML and TOML configuration files
   - Environment-specific configuration profiles
   
   ## 🔧 Improvements
   
   - **Performance**: 30% faster paper generation through optimized context processing
   - **Error Handling**: More informative error messages with suggested fixes
   - **Documentation**: Comprehensive examples and tutorials
   - **CLI**: New commands for template management and validation
   
   ## 🐛 Bug Fixes
   
   - Fixed LaTeX compilation issues on Windows systems
   - Resolved memory leak in large context processing
   - Corrected citation formatting in bibliography generation
   
   ## 📖 Documentation
   
   - New migration guide for Codexes Factory users
   - Advanced configuration examples
   - Plugin development tutorial
   - Troubleshooting guide updates
   
   ## 🔄 Migration Guide
   
   This release is backward compatible with v1.1.x configurations. However, we recommend updating to the new configuration format for enhanced features.
   
   ### Updating from v1.1.x
   
   ```bash
   # Update package
   pip install --upgrade arxiv-writer
   
   # Migrate configuration (optional)
   arxiv-writer config migrate --input old_config.json --output new_config.json
   ```
   
   ## 📊 Statistics
   
   - 🧪 **Tests**: 450+ tests with 95% coverage
   - 🐍 **Python**: Support for Python 3.8-3.12
   - 🖥️ **Platforms**: Windows, macOS, Linux
   - 📦 **Dependencies**: 8 core dependencies
   
   ## 🙏 Contributors
   
   Special thanks to all contributors who made this release possible:
   - @contributor1 - Claude-3 integration
   - @contributor2 - Plugin system design
   - @contributor3 - Documentation improvements
   
   ## 🔗 Links
   
   - [Documentation](https://arxiv-writer.readthedocs.io)
   - [GitHub Repository](https://github.com/ailabforbooklovers/arxiv-writer)
   - [PyPI Package](https://pypi.org/project/arxiv-writer/)
   - [Issue Tracker](https://github.com/ailabforbooklovers/arxiv-writer/issues)
   
   ---
   
   **Full Changelog**: https://github.com/ailabforbooklovers/arxiv-writer/compare/v1.1.0...v1.2.0

Announcement Channels
~~~~~~~~~~~~~~~~~~~~

1. **GitHub Release** - Primary announcement with detailed notes
2. **PyPI Description** - Updated package description
3. **Documentation** - Release announcement on docs site
4. **Social Media** - Twitter/LinkedIn announcements
5. **Community Forums** - Reddit, Stack Overflow, relevant communities
6. **Email Newsletter** - For subscribers (if applicable)

Post-Release Activities
-----------------------

Monitoring
~~~~~~~~~~

After release, monitor:

1. **Download Statistics** - PyPI download counts
2. **Issue Reports** - New GitHub issues
3. **User Feedback** - Community discussions
4. **Performance Metrics** - Error rates, usage patterns
5. **Security Alerts** - Dependency vulnerabilities

**Monitoring Dashboard:**

.. code-block:: python

   # scripts/monitor_release.py
   import requests
   import json
   from datetime import datetime, timedelta

   def check_pypi_downloads(package_name, days=7):
       """Check PyPI download statistics."""
       url = f"https://pypistats.org/api/packages/{package_name}/recent"
       response = requests.get(url)
       data = response.json()
       
       recent_downloads = data['data']['last_week']
       print(f"Downloads in last week: {recent_downloads}")
       return recent_downloads

   def check_github_issues(repo, since_days=1):
       """Check for new GitHub issues."""
       since = (datetime.now() - timedelta(days=since_days)).isoformat()
       url = f"https://api.github.com/repos/{repo}/issues"
       params = {'since': since, 'state': 'open'}
       
       response = requests.get(url, params=params)
       issues = response.json()
       
       print(f"New issues in last {since_days} days: {len(issues)}")
       return issues

   if __name__ == "__main__":
       check_pypi_downloads("arxiv-writer")
       check_github_issues("ailabforbooklovers/arxiv-writer")

Hotfix Process
~~~~~~~~~~~~~~

For critical issues requiring immediate fixes:

.. code-block:: bash

   # Create hotfix branch from main
   git checkout main
   git checkout -b hotfix/1.2.1
   
   # Make minimal fix
   # Update version to 1.2.1
   # Update changelog
   
   # Test fix
   pytest tests/ -v
   
   # Commit and tag
   git commit -m "fix: critical issue with LaTeX compilation"
   git tag v1.2.1
   
   # Merge to main and develop
   git checkout main
   git merge hotfix/1.2.1
   git checkout develop
   git merge hotfix/1.2.1
   
   # Push and release
   git push origin main develop v1.2.1

Support and Maintenance
-----------------------

Long-term Support
~~~~~~~~~~~~~~~~

**Support Policy:**
- **Current Major Version**: Full support with new features and bug fixes
- **Previous Major Version**: Security fixes and critical bug fixes for 12 months
- **Older Versions**: Community support only

**Support Matrix:**

.. list-table::
   :header-rows: 1

   * - Version
     - Status
     - Support Until
     - Python Versions
   * - 2.x.x
     - Current
     - Active
     - 3.8-3.12
   * - 1.x.x
     - Maintenance
     - 2025-03-01
     - 3.8-3.11
   * - 0.x.x
     - End of Life
     - 2024-01-01
     - 3.8-3.10

Deprecation Policy
~~~~~~~~~~~~~~~~~

When deprecating features:

1. **Announce** deprecation in release notes
2. **Add warnings** in code with removal timeline
3. **Provide migration path** in documentation
4. **Remove** in next major version

**Deprecation Example:**

.. code-block:: python

   import warnings

   def old_function():
       warnings.warn(
           "old_function is deprecated and will be removed in v2.0.0. "
           "Use new_function instead.",
           DeprecationWarning,
           stacklevel=2
       )
       # Implementation

Security Updates
~~~~~~~~~~~~~~~

For security vulnerabilities:

1. **Assess severity** using CVSS scoring
2. **Create private fix** in security branch
3. **Coordinate disclosure** with security team
4. **Release patch** with security advisory
5. **Notify users** through security channels

This comprehensive release and deployment guide ensures consistent, reliable releases while maintaining high quality and user satisfaction.