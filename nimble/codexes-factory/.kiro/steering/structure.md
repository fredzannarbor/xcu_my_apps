# Project Structure & Organization

## Directory Structure

```
codexes-factory/
├── .kiro/                  # Kiro AI assistant configuration
│   ├── specs/              # Feature specifications
│   └── steering/           # Steering rules for AI
├── configs/                # Configuration files
│   ├── default_lsi_config.json  # Default LSI configuration
│   ├── publishers/         # Publisher-specific configs
│   └── imprints/           # Imprint-specific configs
├── data/                   # Book data and catalogs
├── docs/                   # Documentation
├── imprints/               # Imprint-specific assets
│   └── xynapse_traces/     # Example imprint
│       ├── templates/      # LaTeX templates
│       └── prompts.json    # Imprint-specific prompts
├── logs/                   # Log files
│   └── lsi_generation/     # LSI generation logs
├── output/                 # Generated output files
├── prompts/                # LLM prompt templates
├── src/                    # Source code
│   └── codexes/            # Main package
│       ├── core/           # Core functionality
│       ├── modules/        # Feature modules
│       │   ├── covers/     # Cover generation
│       │   ├── distribution/  # Distribution tools
│       │   ├── editing/    # Editing tools
│       │   └── metadata/   # Metadata handling
│       └── pages/          # Streamlit UI pages
├── templates/              # Global templates
└── tests/                  # Test suite
```

## Code Organization

### Core Architecture

- **Modular Design**: Features are organized into modules under `src/codexes/modules/`
- **Strategy Pattern**: Used for field mapping and validation strategies
- **Registry Pattern**: Used for managing mapping strategies and validators
- **Factory Pattern**: Used for creating generators and processors

### Key Files

- `run_book_pipeline.py`: Main entry point for book processing pipeline
- `generate_lsi_csv.py`: Utility for generating LSI CSV files
- `src/codexes/modules/distribution/field_mapping_registry.py`: Registry for field mapping strategies
- `src/codexes/modules/distribution/llm_field_completer.py`: LLM-based field completion
- `src/codexes/core/llm_caller.py`: Abstraction for LLM API calls

## Naming Conventions

- **Classes**: PascalCase (e.g., `FieldMappingRegistry`)
- **Functions/Methods**: snake_case (e.g., `generate_with_validation`)
- **Variables**: snake_case (e.g., `field_completer`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_MODEL_NAME`)
- **Files**: snake_case (e.g., `field_mapping.py`)

## Testing Structure

- **Unit Tests**: Named with `test_` prefix (e.g., `test_field_mapping.py`)
- **Test Fixtures**: Located in test files or conftest.py
- **Test Data**: Sample data in `tests/test_data/`

## Configuration Structure

- **Default Config**: `configs/default_lsi_config.json`
- **Publisher Configs**: `configs/publishers/{publisher_name}.json`
- **Imprint Configs**: `configs/imprints/{imprint_name}.json`
- **Environment Variables**: `.env` file for sensitive configuration

## Documentation

- **User Guides**: Located in `docs/` directory (e.g., `LSI_FIELD_ENHANCEMENT_GUIDE.md`)
- **API Reference**: Located in `docs/` directory (e.g., `LSI_API_REFERENCE.md`)
- **Best Practices**: Located in `docs/` directory (e.g., `LSI_BEST_PRACTICES.md`)
- **Troubleshooting**: Located in `docs/` directory (e.g., `LSI_TROUBLESHOOTING_GUIDE.md`)