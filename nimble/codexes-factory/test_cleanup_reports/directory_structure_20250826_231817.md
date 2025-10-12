# Repository Directory Structure

**Generated:** 2025-08-26 23:18:17
**Session:** cleanup_20250826_231817

## Overview

This document describes the current directory structure of the repository
after cleanup operations have been performed.

## Directory Structure

```
├── cleanup_reports
│   ├── cleanup_20250826_231817_initial_snapshot.json
│   ├── cleanup_report_20250826_231817.html
│   ├── cleanup_report_20250826_231817.json
│   ├── cleanup_report_20250826_231817.md
│   ├── directory_structure_20250826_231817.md
│   └── validation_summary_20250826_231817.md
├── configs
│   └── config.json
├── data
│   └── sample.csv
├── docs
│   └── README.md
├── logs
│   └── app.log
├── prompts
│   └── sample.json
├── src
│   └── codexes
│       ├── core
│       │   └── test_module.py
│       └── modules
│           └── test_feature.py
└── tests
    └── test_example.py
```

## Directory Descriptions

- **src/** - Source code directory containing the main application code
- **src/codexes/** - Main application package
- **src/codexes/core/** - Core functionality and utilities
- **src/codexes/modules/** - Feature modules organized by functionality
- **tests/** - Test suite including unit and integration tests
- **docs/** - Documentation including guides, API docs, and summaries
- **configs/** - Configuration files for different environments and components
- **data/** - Data files including catalogs and processed content
- **logs/** - Log files from application execution
- **prompts/** - LLM prompt templates and configurations

## File Organization Principles

The repository follows these organization principles:

1. **Source Code Separation** - All source code is in `src/`
2. **Test Isolation** - All tests are in `tests/`
3. **Documentation Centralization** - All docs are in `docs/`
4. **Configuration Hierarchy** - Configs follow inheritance patterns
5. **Resource Organization** - Static resources are properly categorized
6. **Clean Root Directory** - Minimal files in the root directory
