# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Codexes Factory is an AI-assisted publishing lifecycle platform that streamlines book production using Large Language Models. It provides tools for manuscript analysis, metadata generation, and distribution-ready file creation.

## Common Development Commands

### Running the Application
```bash
# Start the Streamlit UI (main interface)
./start_streamlit.sh
# Or directly with uv:
PYTHONPATH="${PWD}/src:${PYTHONPATH}" uv run streamlit run src/codexes/codexes-factory-home-ui.py --server.port 8502

# Run the book processing pipeline
uv run python run_book_pipeline.py --schedule-file <csv_file> --output-dir <output_dir>

# Generate LSI CSV for distribution
uv run python generate_lsi_csv.py
```

### Testing
```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/<test_file.py> -v

# Run tests with coverage
uv run pytest tests/ --cov
```

### Development Setup
```bash
# Install dependencies using uv (preferred)
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Code Architecture

### Core Structure
The codebase follows a modular architecture centered around the `src/codexes/` directory:

- **`src/codexes/core/`** - Core functionality including:
  - `llm_caller.py` - LLM interaction wrapper
  - `logging_config.py` - Centralized logging configuration
  - `token_usage_tracker.py` - Track LLM token usage
  - `statistics_reporter.py` - Generate usage statistics

- **`src/codexes/modules/`** - Feature modules:
  - `builders/` - Book content generation (llm_get_book_data.py)
  - `distribution/` - LSI/ACS generation, ISBN management
  - `metadata/` - Metadata models and processing
  - `prepress/` - PDF generation and LaTeX processing
  - `covers/` - Cover generation utilities
  - `ideation/` - Content ideation tools
  - `verifiers/` - Quote and content verification

- **`src/codexes/pages/`** - Streamlit UI pages
- **`src/codexes/ui/`** - UI components and utilities

### Key Workflows

1. **Book Pipeline Processing**: `run_book_pipeline.py` orchestrates the entire book production:
   - Loads schedule from CSV
   - Generates book metadata via LLM
   - Creates distribution files (LSI/ACS)
   - Manages ISBN assignment
   - Produces final PDFs

2. **Imprint Management**: Each publishing brand has its own directory under `imprints/` with:
   - Custom prompts and templates
   - Prepress pipeline scripts
   - Brand-specific LaTeX templates

3. **Distribution Integration**:
   - LSI (Lightning Source/IngramSpark) CSV generation
   - Field mapping and validation
   - Automated metadata completion
- 4. **Streamlit UI Mirrors Command Line** create fully-featured Streamlit UI to control command line workflows for production and user interaction workflows

## Important Patterns

### Import Handling
The codebase uses fallback imports to handle both package and direct execution:
```python
try:
    from codexes.modules.builders import llm_get_book_data
except ModuleNotFoundError:
    from src.codexes.modules.builders import llm_get_book_data
```

### Environment Configuration
- Uses `.env` file for API keys and settings
- LiteLLM for LLM provider abstraction
- Supports multiple LLM providers (OpenAI, Anthropic, etc.)

### Logging
- Centralized logging through `get_logging_manager()`
- Environment-specific configurations (development/production)
- LiteLLM filter to reduce noise
- Centralize all log files to 'logs/{source}'

## Key Dependencies
- **streamlit** - Web UI framework
- **litellm** - LLM provider abstraction
- **PyMuPDF** (fitz) - PDF manipulation
- **pandas** - Data processing
- **python-docx** - Word document handling
- **stripe** - Payment processing
- **isbnlib** - ISBN validation
- **nimble-llm-caller** - proprietary tool for managing calls to litellm

## Database and Storage
- SQLite databases for ISBN management (`resources/data_tables/ISBNdb.db`)
- CSV files for book catalogs and schedules, with optional transform to JSON to facilitate editing long text
- JSON configuration files in `configs/`
- LaTeX templates in `templates/` and imprint directories

## Testing Approach
- Unit tests in `tests/` directory
- Test data in `test_output/` and 'tests/data' directories
- Use pytest for test execution
- Mock LLM responses for deterministic testing

## Current Development Focus
Based on the git status, the current branch `finish-xynapse-traces-imprint` is focused on:
- AR7 climate report generation (`prompts/ar7_climate_report_prompts.json`)
- ArXiv paper submission infrastructure
- LSI checkpoint management improvements