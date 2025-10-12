<<<<<<< HEAD
---
inclusion: always
---

# Codexes Factory Technical Guidelines
=======
# Technical Stack & Development Guidelines
>>>>>>> e29a48fc86d6391ea6d370e7a1bbce540e80fcec

## Core Stack & Architecture

<<<<<<< HEAD
**Python 3.12+** with type hints, dataclasses, modern features
**Streamlit** UI in `src/codexes/pages/` - use session state for persistence
**LLM Integration** - ONLY use `src/codexes/core/llm_caller.py` or `enhanced_llm_caller.py`
**LaTeX/LuaLaTeX** - templates in `imprints/{imprint}/template.tex`, memoir class
**Pandas** - CSV/data processing with validation
=======
- **Python 3.12+**: Primary language - always use type hints, dataclasses, and modern Python features
- **Streamlit**: Web UI framework - pages in `src/codexes/pages/`, use session state for persistence
- **LiteLLM**: LLM abstraction layer - ALL interactions should be managed through importing nimble-llm-caller and using its abstractions.
- **LaTeX/LuaLaTeX**: Document generation - templates in `imprints/{imprint}/template.tex`, use memoir class
- **PyMuPDF**: PDF validation and manipulation - validate all generated PDFs
- **Pandas**: CSV/data processing for LSI and catalog generation - validate data integrity
>>>>>>> e29a48fc86d6391ea6d370e7a1bbce540e80fcec

## Code Standards

- **Naming**: snake_case functions/vars, PascalCase classes, UPPER_SNAKE_CASE constants
- **Patterns**: Strategy, Registry, Factory (see `modules/distribution/`)
- **Types**: ALL functions must have type hints - no exceptions
- **Errors**: Specific exception types, log to `logs/` with context
- **Docs**: Google-style docstrings for public methods/classes


## Critical Rules


### Configuration (MANDATORY)
- Multi-level config: `default_lsi_config.json` → `publishers/` → `imprints/` → `tranches/`
- Use `MultiLevelConfigLoader` from `src/codexes/modules/distribution/multi_level_config.py`
- Never hardcode values - use config files or environment variables

### LLM Integration (STRICT)
- Import and use nimble-LLM-caller methods for ALL LLM calls
- Structured prompts from `prompts/` directory - never inline
- Implement retry logic with exponential backoff
- Log ALL LLM interactions to `logs/` for debugging
- Use `llm_monitoring_config.json` for monitoring

### File Organization (NON-NEGOTIABLE)
- Core: `src/codexes/core/` (shared utilities, LLM callers)
- Modules: `src/codexes/modules/{ideation,distribution,covers,editing,metadata,prepress}/`
- Imprints: `imprints/{name}/` (templates, prompts, configs)
- Output: `output/{imprint}_build/` (temp), `data/` (final)

### Ideation System (NEW)
- Core objects: `src/codexes/modules/ideation/core/codex_object.py`
- Tournament engine: `src/codexes/modules/ideation/tournament/tournament_engine.py`
- UI components: `src/codexes/ui/components/` and `src/codexes/modules/ideation/ui/`
- Database: SQLite with migrations in `src/codexes/modules/ideation/storage/`

## Key Workflows

### Book Pipeline
Entry: `run_book_pipeline.py` - never bypass
Flow: JSON metadata → LSI CSV → LaTeX → PDF
Use `CodexMetadata` as single source of truth

### LSI Processing (CRITICAL)
- Use `FieldMappingRegistry` from `field_mapping_registry.py`
- Generate CSV ONLY through `generate_lsi_csv.py`
- Validate ALL fields before output
- Use `enhanced_llm_field_completer.py` for AI completion

### Imprint System
Each imprint needs: `template.tex`, `prompts.json`, config in `configs/imprints/`
Use `ImrintConfigLoader` - never modify global templates

## Command Execution
- ALWAYS use `uv run python script.py`
- ALWAYS use `uv run pytest` for tests
- Activate `.venv` before operations
- Mock external dependencies in tests

<<<<<<< HEAD
## Output Standards
- Work-in-progress: `output/{imprint}_build/`
- Final: `data/` directory
- PDFs: PDF/X-1a compliant, CMYK, embedded fonts
- LSI CSV: All ~119 columns validated
- Typography: Chicago Manual of Style 18th edition
=======
### Imprint System (MULTI-TENANT)
- Each imprint MUST have: `template.tex`, `prompts.json`, config in `configs/imprints/`
- Use `ImprintConfigLoader` from `src/codexes/modules/distribution/imprint_config_loader.py`
- Templates must support both English and international content (Korean, etc.)
- Never modify global templates - always work within imprint scope

### Error Recovery & Monitoring
- Prioritize fixing root cause over providing elaborate fallbacks
- Implement intelligent fallbacks using patterns from existing modules
- Log ALL errors with full context to `logs/` directory with timestamps
- Use structured logging with JSON format for machine readability
- Monitor LLM usage and costs through `llm_monitoring_config.json`
- Report LLM usage and costs at end of every log

## Deliverables & Quality Standards

### Output Requirements (NON-NEGOTIABLE)
- Work-in-progress: `output/{imprint}_build/` directory
- Final approved: `data/` directory for permanent storage
- Book interior: PDF/X-1a compliant, CMYK color space, embedded fonts
- Book cover: PDF/X-1a compliant, CMYK color space, embedded fonts
- LSI CSV: ALL ~119 columns present and validated
- Catalog CSV: Multi-language support where applicable

### Publishing Standards
- Chicago Manual of Style 18th edition compliance
- Fonts: Adobe Fonts or Google Fonts only (licensing compliance)
- LaTeX: Use memoir documentclass for book interiors
- Typography: Professional typesetting standards for commercial publishing

## Command Execution Rules
- ALWAYS use `uv run` prefix for Python scripts
- Never use bare `python` or `pytest` commands
- Activate virtual environment before any operations
- Use shell scripts in project root for complex workflows
>>>>>>> e29a48fc86d6391ea6d370e7a1bbce540e80fcec
