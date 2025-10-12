# Dependency Cleanup Analysis

## Overview
This document outlines the dependency cleanup performed for the TrillionsOfPeople package to prepare it for PyPI distribution.

## Original State
The original `requirements.txt` contained **186 dependencies**, many of which were:
- Unused Zope framework packages (50+ packages)
- Outdated or redundant packages
- Development tools mixed with runtime dependencies
- Packages with no version constraints

## Cleanup Actions

### 1. Removed Unused Dependencies (150+ packages)
**Zope Framework packages** (completely unused):
- All `zope.*` packages (25+ packages)
- Zope core packages: `ZODB`, `BTrees`, `Persistence`, etc.
- Zope web packages: `WebOb`, `WebTest`, `WSGIProxy2`, etc.

**Other unused packages**:
- `langchain`, `llama-index` (AI packages not currently used)
- `boto3`, `botocore` (AWS packages not used)
- `nibabel`, `nipype` (neuroimaging packages not relevant)
- `virtualenv*` packages (development environment tools)
- Many other packages with no imports found in codebase

### 2. Categorized Dependencies into Groups

#### Core Dependencies (Required)
- `click>=8.0.0` - CLI framework
- `pandas>=2.0.0` - Data manipulation
- `python-dotenv>=1.0.0` - Environment variable management
- `requests>=2.28.0` - HTTP requests
- `nimble-llm-caller>=0.1.0` - LLM integration
- `numpy>=1.24.0` - Numerical computing
- `python-dateutil>=2.8.0` - Date/time utilities
- `gibberish>=0.4.0` - Text generation
- `nltk>=3.8.0` - Natural language processing
- `ftfy>=6.1.0` - Text fixing
- `PyMuPDF>=1.22.0` - PDF processing
- `python-docx>=0.8.11` - Word document processing
- `Pillow>=9.5.0` - Image processing

#### Optional Dependencies
- **web**: `streamlit>=1.23.0` - Web interface
- **ai**: `openai>=0.27.0`, `spacy>=3.5.0` - AI/ML features
- **research**: `bibtexparser`, `isbnlib`, `pyzotero`, `openpyxl` - Research tools
- **image**: `html2image>=2.0.0` - Image generation
- **payment**: `stripe>=5.4.0` - Payment processing
- **commerce**: `streamlit-vibe-multicommerce>=0.1.0` - Commerce integration
- **dev**: Testing, linting, and development tools

### 3. Added Proper Version Constraints
- All dependencies now have minimum version constraints
- Removed exact version pinning to allow for security updates
- Used compatible release notation where appropriate

### 4. Updated pyproject.toml
- Moved core dependencies to main `dependencies` section
- Organized optional dependencies into logical groups
- Added `all` extra for installing all optional dependencies

## Benefits

### Size Reduction
- **Before**: 186 dependencies
- **After**: 13 core + optional dependencies as needed
- **Reduction**: ~93% fewer required dependencies

### Installation Speed
- Faster installation due to fewer packages
- Reduced dependency resolution complexity
- Smaller attack surface for security vulnerabilities

### Maintainability
- Clear separation between core and optional features
- Easier to identify and update dependencies
- Better dependency conflict resolution

### User Experience
- Users can install only what they need
- Clear documentation of what each extra provides
- Reduced disk space usage

## Migration Guide

### For Basic Usage
```bash
pip install trillions-of-people
```

### For Web Interface
```bash
pip install trillions-of-people[web]
```

### For AI Features
```bash
pip install trillions-of-people[ai]
```

### For All Features
```bash
pip install trillions-of-people[all]
```

### For Development
```bash
pip install trillions-of-people[dev]
```

## Validation
The cleanup was validated by:
1. Analyzing all Python files for import statements
2. Identifying which packages are actually used
3. Testing core functionality with minimal dependencies
4. Ensuring optional features work with their respective extras

## Future Maintenance
- Regular dependency audits using `pip-audit`
- Automated dependency updates via Dependabot
- Periodic review of optional dependencies usage
- Version constraint updates based on security advisories