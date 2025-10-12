# BISAC Category Generator

A sophisticated Python module for intelligent BISAC (Book Industry Standards and Communications) category generation with LLM assistance, validation, and diversity optimization for the Codexes Factory publishing platform.

## Overview

The BISAC Category Generator is a core component of the Codexes Factory distribution system that automatically generates appropriate BISAC subject categories for books. It combines Large Language Model (LLM) intelligence with industry-standard BISAC validation, tranche configuration overrides, and category diversity optimization to ensure optimal book categorization for distribution platforms.

## Purpose and Role in Codexes Factory

This module serves as a critical component in the publishing workflow by:

- **Automated Categorization**: Intelligently assigns BISAC categories based on book metadata (title, description, keywords)
- **Quality Assurance**: Validates all generated categories against official BISAC standards
- **Flexibility**: Supports manual overrides through tranche configurations for specific publishing requirements
- **Diversity Optimization**: Ensures category selections span multiple top-level BISAC areas for broader market reach
- **Distribution Compliance**: Generates categories that meet requirements for major book distribution platforms

## Key Features and Capabilities

### 🤖 LLM-Powered Generation
- Leverages LLM models to analyze book content and suggest relevant BISAC categories
- Context-aware analysis using title, subtitle, description, and keywords
- Confidence scoring for generated suggestions

### 🎯 Tranche Configuration Override
- Supports publisher-specific category requirements through configuration overrides
- Multiple override field support (`required_bisac_subject`, `tranche_bisac_subject`, etc.)
- Automatic cleanup and validation of override values

### ✅ BISAC Validation & Formatting
- Validates categories against official BISAC code database
- Converts between BISAC codes and category names
- Suggests similar categories for invalid inputs
- Format standardization and cleanup

### 🌈 Diversity Optimization
- Ensures generated categories span multiple top-level BISAC areas
- Calculates and optimizes diversity scores
- Prevents over-concentration in single category areas

### 🚀 Performance Features
- Intelligent caching to avoid redundant generation
- Fallback category system for reliability
- Error recovery and graceful degradation

## Installation & Setup

### Prerequisites
- Python 3.12.6 or higher
- Access to LLM services (OpenAI, Anthropic, etc.)
- Required dependencies from `requirements.txt`

### Dependencies
```bash
# Core dependencies
litellm>=1.72.0
nimble-llm-caller>=0.1.0
python-dotenv>=1.1.0
pandas>=2.3.0

# Additional dependencies
tenacity>=8.2.0  # For retry logic
PyYAML>=6.0.1   # For configuration
```

### Environment Configuration
Set up your environment with appropriate API keys:

```bash
# .env file
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
# Add other LLM provider keys as needed
```

## Usage Examples

### Basic Usage

```python
from codexes.modules.distribution.bisac_category_generator import get_bisac_category_generator
from codexes.modules.metadata.metadata_models import CodexMetadata
from codexes.modules.distribution.field_mapping import MappingContext

# Initialize the generator
generator = get_bisac_category_generator(llm_completer=your_llm_completer)

# Prepare book metadata
metadata = CodexMetadata(
    title="The Art of Machine Learning",
    subtitle="A Practical Guide to AI Implementation",
    summary_long="A comprehensive guide covering machine learning techniques...",
    keywords="machine learning, artificial intelligence, programming"
)

# Create mapping context
context = MappingContext(
    field_name="bisac_categories",
    lsi_headers=[],
    current_row_data={},
    config={}
)

# Generate categories
result = generator.generate_categories(metadata, context, max_categories=3)

print(f"Generated Categories: {result.categories}")
print(f"Primary Category: {result.primary_category}")
print(f"Diversity Score: {result.diversity_score}")
```

### With Tranche Override Configuration

```python
# Configuration with tranche override
tranche_config = {
    "required_bisac_subject": "COMPUTERS / Machine Learning",
    "other_settings": "..."
}

context = MappingContext(
    field_name="bisac_categories",
    lsi_headers=[],
    current_row_data={},
    config=tranche_config
)

result = generator.generate_categories(metadata, context, max_categories=3)

if result.tranche_override_used:
    print(f"Tranche override applied: {result.primary_category}")
```

### Advanced Usage with Validation

```python
# Generate and validate categories
result = generator.generate_categories(metadata, context)

# Check validation results
for i, validation in enumerate(result.validation_results):
    category = result.categories[i]
    confidence = result.confidence_scores[i]

    print(f"Category: {category}")
    print(f"Valid: {validation.is_valid}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Message: {validation.message}")
    print("---")

# Analyze diversity
print(f"Top-level categories: {result.top_level_categories}")
print(f"Diversity score: {result.diversity_score}")
print(f"Fallback used: {result.fallback_used}")
```

## API Documentation

### Classes

#### `BISACCategoryGenerator`

Main class for generating BISAC categories.

**Constructor:**
```python
BISACCategoryGenerator(llm_completer=None)
```

**Key Methods:**

##### `generate_categories(metadata, context, max_categories=3)`
Generates BISAC categories with full processing pipeline.

**Parameters:**
- `metadata` (CodexMetadata): Book metadata containing title, description, etc.
- `context` (MappingContext): Configuration and context information
- `max_categories` (int): Maximum number of categories to generate (default: 3)

**Returns:** `BISACCategoryResult` object with generated categories and metadata

##### `apply_tranche_override(context)`
Checks for and applies tranche configuration overrides.

**Parameters:**
- `context` (MappingContext): Context containing configuration

**Returns:** Override category string or None

##### `validate_and_format_category(category)`
Validates and formats a single category.

**Parameters:**
- `category` (str): Category name or BISAC code

**Returns:** Formatted category name or None if invalid

##### `ensure_category_diversity(categories)`
Optimizes category list for maximum diversity across top-level categories.

**Parameters:**
- `categories` (List[str]): List of category names

**Returns:** Reordered list optimized for diversity

#### `BISACCategoryResult`

Result object containing generated categories and metadata.

**Attributes:**
- `categories` (List[str]): Generated category names
- `primary_category` (str): Most relevant category
- `confidence_scores` (List[float]): Confidence scores for each category
- `validation_results` (List[BISACValidationResult]): Validation results
- `top_level_categories` (List[str]): Top-level category prefixes
- `diversity_score` (float): Measure of category diversity (0.0-1.0)
- `tranche_override_used` (bool): Whether tranche override was applied
- `fallback_used` (bool): Whether fallback categories were used

### Global Functions

#### `get_bisac_category_generator(llm_completer=None)`
Factory function that returns the global BISAC category generator instance.

**Parameters:**
- `llm_completer`: Optional LLM field completer for category generation

**Returns:** `BISACCategoryGenerator` instance

## Configuration Options

### Tranche Override Fields

The module supports multiple configuration fields for category overrides:

```python
config = {
    "required_bisac_subject": "BUSINESS & ECONOMICS / Marketing",
    "tranche_bisac_subject": "Alternative field name",
    "bisac_override": "Another override option",
    "primary_bisac_category": "Yet another option"
}
```

### Fallback Categories

Default categories used when generation fails:
- `"GENERAL"`
- `"BUSINESS & ECONOMICS / General"`
- `"REFERENCE / General"`

### LLM Prompt Configuration

The module uses a specialized prompt key for LLM generation:
- `prompt_key`: `"generate_bisac_categories"`

## Known Limitations

1. **LLM Dependency**: Requires access to LLM services for optimal category generation
2. **BISAC Database Coverage**: Validation limited to categories in the built-in BISAC database
3. **Language Support**: Primarily designed for English-language books
4. **Cache Persistence**: Cache is in-memory only and doesn't persist between sessions
5. **Rate Limits**: Subject to LLM provider rate limits and quotas

## Error Handling

The module implements robust error handling:

- **LLM Failures**: Falls back to configured fallback categories
- **Validation Errors**: Attempts category name validation and suggestions
- **Configuration Issues**: Graceful handling of missing or invalid configs
- **Network Issues**: Retry logic through underlying LLM caller

## Integration Points

### Required Imports

```python
from .bisac_validator import get_bisac_validator, BISACValidationResult
from .field_mapping import MappingContext
from ..metadata.metadata_models import CodexMetadata
```

### Related Modules

- `bisac_validator.py`: BISAC code validation and suggestion
- `field_mapping.py`: Field mapping context and strategies
- `metadata_models.py`: Book metadata structures
- LLM completion modules for AI-powered generation

## Contributing Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Include comprehensive docstrings for all public methods
- Add logging statements for debugging and monitoring

### Testing
- Write unit tests for all public methods
- Include integration tests with mock LLM responses
- Test error conditions and edge cases
- Validate against official BISAC standards

### Pull Request Process
1. Create feature branch from main
2. Implement changes with tests
3. Update documentation as needed
4. Submit pull request with clear description
5. Address code review feedback

### Adding New Features
- Consider backward compatibility
- Update configuration options documentation
- Add appropriate error handling
- Include usage examples in documentation

## Logging

The module uses Python's standard logging framework:

```python
import logging
logger = logging.getLogger(__name__)
```

**Log Levels:**
- `DEBUG`: Cache hits, diversity optimization details
- `INFO`: Category generation progress, override applications
- `WARNING`: LLM failures, validation issues
- `ERROR`: Critical failures in category generation

## Performance Considerations

- **Caching**: Results are cached to avoid redundant LLM calls
- **Batch Processing**: Consider batching multiple books for efficiency
- **LLM Costs**: Monitor token usage for cost optimization
- **Memory Usage**: Cache grows with unique book metadata combinations

---

For more information about the Codexes Factory publishing platform, see the main project documentation.