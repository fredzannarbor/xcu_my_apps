# ArXiv Writer Migration Plan

This document outlines the migration from the specialized `src/codexes/modules/arxiv_paper/` module to the standalone `arxiv-writer` package.

## Migration Strategy

### Phase 1: Package Installation ✅
- [x] Identify the preferred arxiv-writer location: `/Users/fred/my-organizations/nimble/repos/arxiv-writer`
- [x] Add arxiv-writer as a dependency in pyproject.toml
- [x] Create bridge module for compatibility: `src/codexes/modules/arxiv_bridge.py`

### Phase 2: Import Replacement 🔄
- [x] Update test files to use new import strategy
  - [x] `tests/test_arxiv_submission.py`
  - [x] `tests/integration/test_data_collection.py`
- [ ] Replace internal module imports within arxiv_paper directory
- [ ] Create integration test script

### Phase 3: Configuration and Path Management 📋
- [ ] Configure arxiv-writer to accept caller-specified paths (NO hard-coding)
- [ ] Update file path handling to be completely configurable:
  - Input data sources (caller specifies: "imprints/xynapse_traces/")
  - Output directories (caller specifies: "output/arxiv_paper/", "output/arxiv_submission/")
  - Template files (caller specifies: "prompts/arxiv_paper_prompts.json")
  - Configuration files (caller specifies: "configs/imprints/xynapse_traces.json")
- [ ] Ensure NO files are read/written from site-packages directory

### Phase 4: Testing and Validation 🧪
- [ ] Test paper generation workflow
- [ ] Validate output file compatibility
- [ ] Test CLI commands work with codexes-factory data
- [ ] Verify LaTeX compilation and PDF generation

### Phase 5: Cleanup 🧹
- [ ] Deprecate old arxiv_paper module (keep for reference)
- [ ] Update documentation and CLI guides
- [ ] Remove duplicate functionality

## Key Integration Points

### File Paths Configuration
The arxiv-writer package must accept ALL paths from the calling project:

```python
# Caller (codexes-factory) specifies ALL paths - NO defaults in site-packages
config = {
    "working_directory": "/Users/fred/my-organizations/nimble/repos/codexes-factory",
    "input_data": {
        "imprint_dir": "imprints/xynapse_traces/",
        "books_file": "imprints/xynapse_traces/books.csv",
        "config_file": "configs/imprints/xynapse_traces.json"
    },
    "output": {
        "paper_dir": "output/arxiv_paper/",
        "submission_dir": "output/arxiv_submission/"
    },
    "templates": {
        "prompts_file": "prompts/arxiv_paper_prompts.json"
    }
}

# arxiv-writer resolves all paths relative to working_directory
# NO files read from or written to site-packages
```

### Bridge Module Usage
Use the bridge module for seamless transition:

```python
# Instead of:
from src.codexes.modules.arxiv_paper.paper_generator import generate_arxiv_paper

# Use:
from codexes.modules.arxiv_bridge import generate_arxiv_paper
```

### CLI Integration
The arxiv-writer package provides path-configurable CLI commands:

```bash
# Generate paper with caller-specified paths (working directory = cwd)
arxiv-writer generate --config configs/imprints/xynapse_traces.json --output output/arxiv_paper/

# Validate existing paper (all paths from caller)
arxiv-writer validate output/arxiv_paper/complete_paper.md

# Collect context data with caller-specified sources
arxiv-writer collect-context --imprint-dir imprints/xynapse_traces/ --output context.json

# All files read from and written to calling project directory, NEVER site-packages
```

## Files to Update

### External References (High Priority)
1. `tests/test_arxiv_submission.py` ✅
2. `tests/integration/test_data_collection.py` ✅
3. Any Streamlit pages or CLI scripts that import arxiv_paper

### Internal Module References (Medium Priority)
Files within `src/codexes/modules/arxiv_paper/` that import from each other:
- `generate_paper_cli.py`
- `test_paper_generation.py`
- `prepare_arxiv_submission.py`
- Section generation scripts (7_1, 7_2, 7_3, 7_4)

### Configuration Files (Low Priority)
- Update any hardcoded paths in configuration files
- Update documentation and README files

## Benefits of Migration

1. **Cleaner Architecture**: Separate package with well-defined API
2. **Better Testing**: Comprehensive test suite in arxiv-writer
3. **Reusability**: Package can be used in other projects
4. **Maintenance**: Easier to maintain and update
5. **Distribution**: Can be published to PyPI for broader use

## Rollback Plan

If migration issues arise:
1. The bridge module will automatically fall back to the legacy module
2. All existing functionality remains available
3. No breaking changes to existing workflows

## Next Steps

1. **Immediate**: Test the bridge module functionality
2. **Short-term**: Configure paths and test paper generation
3. **Medium-term**: Update all internal references
4. **Long-term**: Deprecate legacy module and publish package

## Notes

- The arxiv-writer package has 65 Python files vs 48 in the specialized module
- It includes advanced features like plugin system, quality assessment, and CLI
- Backward compatibility is maintained through the CodexesFactoryAdapter
- Output file formats and structures should remain identical