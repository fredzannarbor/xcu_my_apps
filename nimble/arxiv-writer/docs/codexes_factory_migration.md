# Codexes Factory Migration Guide

This guide provides step-by-step instructions for migrating from the existing Codexes Factory arxiv paper generation functionality to the new standalone arxiv-writer package.

## Overview

The arxiv-writer package provides a complete replacement for the arxiv paper generation functionality currently embedded in the Codexes Factory codebase. This migration allows you to:

- Use arxiv paper generation independently of Codexes Factory
- Maintain identical output and functionality
- Benefit from improved modularity and extensibility
- Access enhanced documentation and testing

## Migration Process

### Step 1: Install the arxiv-writer Package

```bash
pip install arxiv-writer
```

Or for development installation:

```bash
git clone https://github.com/your-org/arxiv-writer.git
cd arxiv-writer
pip install -e .
```

### Step 2: Identify Your Current Configuration

Locate your existing Codexes Factory configuration files. These are typically found in:

- `examples/configs/imprints/xynapse_traces.json` (for xynapse_traces imprint)
- Custom configuration files in your workspace
- Configuration embedded in your existing code

### Step 3: Migrate Configuration

Use the built-in migration utility to convert your Codexes Factory configuration:

```python
from arxiv_writer.core.codexes_factory_adapter import migrate_codexes_factory_config

# Migrate configuration file
migrated_config = migrate_codexes_factory_config(
    codexes_config_path="path/to/your/codexes_config.json",
    output_config_path="path/to/arxiv_writer_config.json"
)
```

Or use the CLI:

```bash
arxiv-writer migrate-config \
    --source path/to/codexes_config.json \
    --output path/to/arxiv_writer_config.json
```

### Step 4: Update Your Code

Replace your existing Codexes Factory arxiv generation code with the new adapter:

#### Before (Codexes Factory):
```python
# Old Codexes Factory code
from codexes_factory.arxiv import generate_arxiv_paper

result = generate_arxiv_paper(
    workspace_root=".",
    imprint_name="xynapse_traces",
    output_directory="output"
)
```

#### After (arxiv-writer):
```python
# New arxiv-writer code
from arxiv_writer.core.codexes_factory_adapter import CodexesFactoryAdapter

# Option 1: Use existing configuration file
adapter = CodexesFactoryAdapter("path/to/your/config.json")

# Option 2: Create compatibility configuration
from arxiv_writer.core.codexes_factory_adapter import create_codexes_compatibility_config
config = create_codexes_compatibility_config(
    workspace_root=".",
    imprint_name="xynapse_traces"
)
adapter = CodexesFactoryAdapter(config)

# Generate paper (identical API)
result = adapter.generate_paper()
```

### Step 5: Verify Output Compatibility

The arxiv-writer package is designed to produce identical output to the original Codexes Factory implementation. Verify this by:

1. **Running side-by-side comparison:**
```python
# Generate with both systems using identical configuration
old_result = generate_with_codexes_factory(config)
new_result = adapter.generate_paper()

# Compare outputs
assert old_result["paper_content"] == new_result["paper_content"]
assert old_result["sections"].keys() == new_result["sections"].keys()
```

2. **Validating paper quality:**
```python
# Use built-in validation
validation_result = adapter.validate_paper(new_result["paper_content"])
assert validation_result["is_valid"] == True
assert validation_result["arxiv_compliance"]["submission_ready"] == True
```

### Step 6: Update Dependencies

Remove Codexes Factory dependencies from your project and add arxiv-writer:

```bash
# Remove old dependencies (if applicable)
pip uninstall codexes-factory

# Add new dependency
pip install arxiv-writer
```

Update your `requirements.txt` or `pyproject.toml`:

```txt
# requirements.txt
arxiv-writer>=1.0.0
```

```toml
# pyproject.toml
[project]
dependencies = [
    "arxiv-writer>=1.0.0"
]
```

## Configuration Mapping

The migration process automatically maps Codexes Factory configuration to arxiv-writer format:

| Codexes Factory | arxiv-writer | Notes |
|----------------|--------------|-------|
| `imprint` | `imprint_name` | Direct mapping |
| `workspace_root` | `workspace_root` | Direct mapping |
| `llm_config.default_model` | `llm_config.default_model` | Direct mapping |
| `llm_config.available_models` | `llm_config.available_models` | Direct mapping |
| `template_config.template_file` | `template_config.template_file` | Direct mapping |
| `template_config.section_order` | `template_config.section_order` | Direct mapping |
| `validation_config.*` | `validation_config.*` | All validation settings preserved |
| `context_config.*` | Context collection settings | Mapped to context collector configuration |

## API Compatibility

The CodexesFactoryAdapter provides full API compatibility with the original implementation:

### Paper Generation
```python
# Generate complete paper
result = adapter.generate_paper(additional_context=None)

# Generate individual section
section_result = adapter.generate_section("abstract", additional_context=None)

# Validate paper content
validation_result = adapter.validate_paper(paper_content)

# Get context data
context_data = adapter.get_context_data()
```

### Result Format
The result format is identical to Codexes Factory:

```python
{
    "paper_content": "Complete LaTeX paper content",
    "sections": {
        "abstract": {
            "content": "Section content",
            "word_count": 150,
            "generated_at": "2024-01-01T12:00:00",
            "model_used": "anthropic/claude-3-5-sonnet-20241022",
            "validation_status": "valid",
            "metadata": {...}
        },
        # ... other sections
    },
    "generation_summary": {
        "total_sections": 8,
        "total_word_count": 3500,
        "generation_time": 45.2,
        "models_used": ["anthropic/claude-3-5-sonnet-20241022"],
        "quality_score": 0.85
    },
    "context_summary": {
        "sources_collected": ["book_catalog", "imprint_config", ...],
        "collection_timestamp": "2024-01-01T11:30:00",
        "total_context_size": 15000
    },
    "output_files": ["paper.tex", "paper.pdf"],
    "imprint_info": {
        "imprint_name": "Xynapse Traces",
        "workspace_root": ".",
        "configuration_used": {...}
    }
}
```

## Advanced Migration Scenarios

### Custom Templates
If you have custom prompt templates:

```python
# Migrate custom templates
custom_config = {
    "template_config": {
        "template_file": "path/to/custom_templates.json",
        "custom_templates": {
            "custom_section": "Your custom prompt template"
        }
    }
}

adapter = CodexesFactoryAdapter(custom_config)
```

### Custom Context Collection
For custom context collection logic:

```python
# Create custom context collector
from arxiv_writer.core.context_collector import create_codexes_factory_context_collector

context_collector = create_codexes_factory_context_collector(
    workspace_root=".",
    collection_types=["book_catalog", "custom_data"],
    validation_enabled=True
)

# Use with adapter
adapter.context_collector = context_collector
```

### Plugin Integration
Migrate custom functionality using the plugin system:

```python
from arxiv_writer.plugins.base import SectionPlugin

class CustomSectionPlugin(SectionPlugin):
    def generate_section(self, context):
        # Your custom section generation logic
        pass

# Register plugin
from arxiv_writer.plugins.registry import PluginRegistry
registry = PluginRegistry()
registry.register_plugin("custom_section", CustomSectionPlugin)
```

## Validation and Testing

### Automated Validation
Use the built-in validation tools to ensure migration success:

```python
from arxiv_writer.core.codexes_factory_adapter import validate_migration

# Validate that migration preserves functionality
validation_report = validate_migration(
    original_config_path="path/to/codexes_config.json",
    migrated_config_path="path/to/arxiv_writer_config.json",
    test_data_path="path/to/test_data"
)

print(validation_report)
```

### Manual Testing
1. Generate papers with both systems using identical configuration
2. Compare output files byte-by-byte
3. Validate LaTeX compilation and PDF generation
4. Test all workflow scenarios (individual sections, validation, etc.)

## Troubleshooting

### Common Issues

#### Configuration Not Found
```
ConfigurationError: Configuration file not found: path/to/config.json
```
**Solution:** Verify the configuration file path and ensure it exists.

#### Model Not Available
```
LLMError: Model 'custom/model' not available
```
**Solution:** Update your configuration to use supported models or configure custom model access.

#### Template Loading Failed
```
TemplateError: Failed to load template file: templates/custom.json
```
**Solution:** Ensure template files are accessible and in the correct format.

#### Context Collection Failed
```
ContextCollectionError: Failed to collect data from source 'custom_source'
```
**Solution:** Verify data sources are available and accessible.

### Getting Help

1. **Documentation:** Check the full documentation at [docs/](../docs/)
2. **Examples:** Review examples in [examples/](../examples/)
3. **Issues:** Report issues on GitHub
4. **Support:** Contact support at support@arxiv-writer.com

## Migration Checklist

- [ ] Install arxiv-writer package
- [ ] Identify current Codexes Factory configuration
- [ ] Run configuration migration utility
- [ ] Update code to use CodexesFactoryAdapter
- [ ] Verify output compatibility
- [ ] Update project dependencies
- [ ] Test all workflow scenarios
- [ ] Validate paper generation quality
- [ ] Update documentation and deployment scripts
- [ ] Train team on new API (if applicable)

## Post-Migration Benefits

After successful migration, you'll benefit from:

- **Independence:** Use arxiv generation without full Codexes Factory installation
- **Modularity:** Integrate with other projects and workflows
- **Extensibility:** Use plugin system for custom functionality
- **Testing:** Comprehensive test suite ensures reliability
- **Documentation:** Detailed documentation and examples
- **Maintenance:** Dedicated package with focused development
- **Performance:** Optimized for arxiv paper generation use case

## Rollback Plan

If you need to rollback to Codexes Factory:

1. Keep original Codexes Factory code until migration is fully validated
2. Use version control to track changes
3. Maintain parallel systems during transition period
4. Document any custom modifications for easy rollback

The migration is designed to be reversible, and the CodexesFactoryAdapter ensures compatibility with existing workflows.