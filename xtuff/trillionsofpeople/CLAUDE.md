# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trillions of People is a synthetic persona generation platform that creates realistic AI-generated people for historical, present, and future scenarios. The project aims to make past and future human lives feel more real through state-of-the-art scientific, historical, and artificial intelligence techniques.

## Common Development Commands

### Running the Application

```bash
# Start the Streamlit web interface
trillions-web
# Or with uv:
uv run streamlit run src/trillions_of_people/web/app.py

# Use the CLI interface
trillions --help
trillions generate --country "United States" --year 1850 --count 3
trillions browse --limit 10
trillions countries
```

### Testing

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/unit/test_people_utilities.py -v

# Run tests with coverage
uv run pytest tests/ --cov=trillions_of_people --cov-report=html
```

### Development Setup

```bash
# Install dependencies using uv (preferred)
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your OpenAI API key:
# OPENAI_API_KEY=sk-your-key-here
```

## Code Architecture

### Core Structure

The codebase follows a modular architecture centered around the `src/trillions_of_people/` directory:

- **`src/trillions_of_people/core/`** - Core functionality including:
  - `llm_caller.py` - LLM interaction wrapper using nimble-llm-caller
  - `logging_config.py` - Centralized logging configuration
  - `fallback_llm.py` - Fallback implementation for development

- **`src/trillions_of_people/modules/`** - Feature modules:
  - `people_utilities.py` - Core persona generation and management

- **`src/trillions_of_people/cli/`** - Command-line interface
  - `main.py` - CLI entry point with Click commands

- **`src/trillions_of_people/web/`** - Streamlit web interface
  - `app.py` - Main web application
  - `components.py` - UI components
  - `utils.py` - Web utility functions

### Key Workflows

1. **Persona Generation Pipeline**:
   - Uses `TrillionsLLMCaller` to interface with LLM providers via nimble-llm-caller
   - Converts structured requests to detailed prompts
   - Parses LLM responses into standardized persona data
   - Saves to CSV files for persistence

2. **CLI Interface**: Provides commands for:
   - `generate` - Create new synthetic personas
   - `browse` - View existing personas in database
   - `countries` - List available countries
   - `status` - Check system configuration

3. **Web Interface**: Streamlit-based UI for:
   - Interactive persona generation
   - Browsing and displaying persona cards
   - File upload for batch import
   - API key management

4. **Data Management**:
   - CSV-based storage for personas and countries
   - Automatic backup creation
   - Structured data validation

## Important Patterns

### LLM Integration
The project uses nimble-llm-caller for LLM provider abstraction:
```python
from trillions_of_people.core.llm_caller import TrillionsLLMCaller, PersonaGenerationRequest

caller = TrillionsLLMCaller(api_key="your-key")
request = PersonaGenerationRequest(country="France", year=1789, count=2)
personas = caller.generate_personas(request)
```

### Environment Configuration
- Uses `.env` file for API keys and settings
- Nimble-llm-caller for LLM provider abstraction
- Supports OpenAI as primary provider with fallback capability

### Logging
- Centralized logging through `get_logging_manager()`
- Environment-specific configurations (development/production)
- External library noise reduction
- Log files stored in `logs/` directory

### Fallback Handling
```python
try:
    from nimble_llm_caller import LLMCaller
except ImportError:
    from src.trillions_of_people.core.fallback_llm import LLMCaller
```

## Key Dependencies

- **click** - CLI framework
- **streamlit** - Web UI framework
- **nimble-llm-caller** - LLM provider abstraction
- **litellm** - LLM provider compatibility layer
- **pandas** - Data processing and CSV handling
- **PyMuPDF** (fitz) - PDF generation for persona cards
- **gibberish** - Text validation
- **python-dotenv** - Environment configuration
- **pydantic** - Data validation and serialization

## Data Architecture

### Storage
- **CSV files** for persona and country data in `people_data/` directory
- **JSON** for complex structured data within CSV fields
- **Backup system** for data safety during updates

### Persona Data Structure
Standard fields for each generated persona:
- Basic demographics (name, age, gender, born, country)
- Social context (occupation, family_situation, education)
- Personality (personality_traits, life_challenges)
- Cultural context (cultural_background, notable_events)
- Metadata (generated_year, invisible_comments with full LLM response)

## Testing Approach

- **Unit tests** in `tests/unit/` directory
- **Integration tests** in `tests/integration/` directory
- **Test data** in `tests/data/` directory
- Use pytest for test execution
- Mock LLM responses for deterministic testing
- Temporary directories for file system tests

## Current Development Focus

The project has been modernized from a legacy monolithic structure to follow current best practices:

### Recent Updates
- Migrated from direct OpenAI API calls to nimble-llm-caller
- Modular architecture replacing monolithic Streamlit app
- Comprehensive CLI interface with Click
- Proper logging and error handling
- Modern dependency management with pyproject.toml
- Comprehensive test suite

### Future Enhancements
- Geographic coordinate integration for location-aware personas
- Multi-language persona generation
- Historical event correlation
- Enhanced persona relationship modeling
- Integration with external demographic data sources

## API and Environment

### Required Environment Variables
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
LOG_LEVEL=INFO  # Optional: DEBUG, INFO, WARNING, ERROR
```

### Optional Configuration
- `people_data/` directory for data storage (created automatically)
- Custom country lists via `people_data/country.csv`
- Persona history in `people_data/people.csv`

## Error Handling

The application includes comprehensive error handling:
- API key validation before LLM calls
- Graceful degradation when services are unavailable
- Automatic fallback to mock data in development
- User-friendly error messages in both CLI and web interfaces
- Detailed logging for debugging

## Performance Considerations

- LLM calls are the primary performance bottleneck
- Batch persona generation recommended over single requests
- CSV operations optimized for large datasets
- Streaming responses for web interface
- Configurable request timeouts and retry logic