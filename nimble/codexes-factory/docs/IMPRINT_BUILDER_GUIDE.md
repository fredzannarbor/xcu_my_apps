# Streamlined Imprint Builder Guide

## Overview

The Streamlined Imprint Builder is a comprehensive system for creating professional publishing imprints from simple descriptions. It uses AI assistance to transform minimal input into complete imprint definitions with templates, prompts, configurations, and schedules.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [User Interfaces](#user-interfaces)
4. [API Reference](#api-reference)
5. [Configuration](#configuration)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Examples](#examples)

## Quick Start

### Using the Streamlit UI

1. **Start the UI**:
   ```bash
   PYTHONPATH=src uv run streamlit run src/codexes/pages/1_Home.py
   ```

2. **Navigate to Imprint Builder**: Look for the "🏢 Imprint Builder" section

3. **Create Your Imprint**:
   - Enter a description of your imprint vision
   - Click "🚀 Create Imprint"
   - Review and refine the results
   - Generate artifacts and schedules

### Using the CLI

1. **Create an imprint from text**:
   ```bash
   python tools/imprint_builder_cli.py create "A literary imprint focused on contemporary fiction for adult readers" my_imprint.json
   ```

2. **Generate artifacts**:
   ```bash
   python tools/imprint_builder_cli.py generate-artifacts my_imprint.json artifacts/
   ```

3. **Create a publication schedule**:
   ```bash
   python tools/imprint_builder_cli.py generate-schedule my_imprint.json schedule.json --books 12
   ```

### Using the Python API

```python
from codexes.modules.imprint_builder import (
    ImprintConceptParser, ImprintExpander, ImprintArtifactGenerator
)
from codexes.core.llm_integration import LLMCaller

# Initialize components
llm_caller = LLMCaller()
parser = ImprintConceptParser(llm_caller)
expander = ImprintExpander(llm_caller)
generator = ImprintArtifactGenerator(llm_caller)

# Create imprint
concept = parser.parse_concept("Your imprint description here")
expanded_imprint = expander.expand_concept(concept)

# Generate artifacts
results = generator.generate_all_artifacts(expanded_imprint, "output/")
```

## Core Concepts

### Imprint Concept

An `ImprintConcept` represents the initial user input and extracted information:

- **Raw Input**: The original description provided by the user
- **Extracted Themes**: Key themes and focus areas identified
- **Target Audience**: Primary readership
- **Publishing Focus**: Types of content to publish
- **Design Preferences**: Visual and branding preferences
- **Confidence Score**: How well the system understood the input

### Expanded Imprint

An `ExpandedImprint` is the complete imprint definition with all components:

- **Branding**: Name, mission, values, unique selling proposition
- **Design**: Colors, typography, layouts, trim sizes
- **Publishing**: Genres, audience, frequency, pricing
- **Production**: Workflow, quality standards, automation
- **Distribution**: Channels, territories, sales strategy
- **Marketing**: Channels, content strategy, campaigns

### Artifacts

Generated artifacts include:

- **LaTeX Templates**: Customized book templates
- **LLM Prompts**: Content generation prompts
- **Configuration Files**: Pipeline and system configs
- **Workflow Definitions**: Production process definitions
- **Documentation**: Style guides and procedures

## User Interfaces

### Streamlit Web UI

The web interface provides:

- **Create Imprint**: Single-field input with advanced options
- **Edit Imprint**: Interactive editor with undo/redo
- **Generate Artifacts**: Artifact generation with validation
- **Schedule Planning**: Publication timeline creation
- **Management**: Import/export and status tracking

#### Key Features:

- Real-time validation and feedback
- Visual preview of design elements
- Progress tracking and status indicators
- Export capabilities for all components

### Command Line Interface

The CLI supports:

- Single imprint creation
- Batch processing
- Artifact generation
- Schedule creation
- Validation and testing
- Template export

#### Common Commands:

```bash
# Create from text
python tools/imprint_builder_cli.py create "description" output.json

# Create from file
python tools/imprint_builder_cli.py create-from-file concept.txt output.json

# Batch create
python tools/imprint_builder_cli.py batch-create batch.json output_dir/

# Generate artifacts
python tools/imprint_builder_cli.py generate-artifacts imprint.json artifacts/

# Validate
python tools/imprint_builder_cli.py validate imprint.json

# List imprints
python tools/imprint_builder_cli.py list imprints_dir/
```

## API Reference

### ImprintConceptParser

Parses user input and extracts key concepts.

```python
parser = ImprintConceptParser(llm_caller)
concept = parser.parse_concept(user_input)
validation = parser.validate_concept(concept)
suggestions = parser.suggest_improvements(concept)
```

### ImprintExpander

Expands concepts into complete imprint definitions.

```python
expander = ImprintExpander(llm_caller)
expanded = expander.expand_concept(concept)
```

### ImprintEditor

Provides editing capabilities with change tracking.

```python
editor = ImprintEditor(llm_caller)
session = editor.create_editing_session(expanded_imprint)
editor.update_field(session, 'branding', 'imprint_name', 'New Name')
editor.undo_change(session)
validation = editor.validate_imprint(session)
```

### ImprintArtifactGenerator

Generates all production artifacts.

```python
generator = ImprintArtifactGenerator(llm_caller)
results = generator.generate_all_artifacts(imprint, output_dir)
template_results = generator.generate_latex_templates(imprint, template_dir)
prompt_results = generator.generate_llm_prompts(imprint, prompts_file)
```

### ImprintScheduleGenerator

Creates publication schedules and workflows.

```python
scheduler = ImprintScheduleGenerator(llm_caller)
schedules = scheduler.generate_initial_schedule(imprint, num_books=12)
workflow = scheduler.generate_workflow_config(imprint)
codex_types = scheduler.suggest_codex_types(imprint)
```

### ImprintValidator

Validates imprints and provides feedback.

```python
validator = ImprintValidator(llm_caller)
concept_validation = validator.validate_concept(concept)
imprint_validation = validator.validate_expanded_imprint(expanded_imprint)
template_validation = validator.validate_template_compilation(template_dir)
```

## Configuration

### LLM Configuration

Configure the LLM integration in your environment:

```python
# Using default configuration
llm_caller = LLMCaller()

# Using custom configuration
llm_caller = LLMCaller(config_path="custom_llm_config.json")
```

### Validation Rules

Customize validation rules by modifying the validator:

```python
validator = ImprintValidator()
validator.validation_rules['branding']['required_fields'] = ['imprint_name', 'mission_statement']
```

### Template Customization

Templates can be customized by:

1. Modifying base templates in the artifact generator
2. Creating custom template sets
3. Overriding specific template components

## Best Practices

### Writing Effective Concept Descriptions

**Good Examples:**

```
A literary imprint focused on contemporary fiction for educated adult readers aged 25-55. 
We specialize in diverse voices and innovative storytelling, with a sophisticated brand 
identity that appeals to book clubs and literary enthusiasts.
```

```
Young adult fantasy imprint targeting teens 13-18 with epic fantasy, urban fantasy, 
and magical realism. Modern, exciting brand connecting with teens through social media. 
Focus on diverse characters and contemporary themes.
```

**Tips:**

- Include target audience demographics
- Specify genres and content types
- Mention brand personality and style
- Include distribution preferences
- Specify any special requirements

### Iterative Refinement

1. **Start Simple**: Begin with a basic concept
2. **Review Results**: Examine the generated imprint
3. **Edit and Refine**: Use the editor to make adjustments
4. **Validate**: Check for issues and inconsistencies
5. **Generate Artifacts**: Create production materials
6. **Test and Iterate**: Refine based on results

### Quality Assurance

- Always validate generated artifacts
- Test template compilation
- Review prompt effectiveness
- Check configuration consistency
- Verify pipeline integration

## Troubleshooting

### Common Issues

#### Low Confidence Scores

**Problem**: Concept parsing results in low confidence scores

**Solutions**:
- Provide more detailed descriptions
- Include specific themes and audience information
- Mention design preferences and requirements
- Use the suggestion system for improvements

#### Template Compilation Errors

**Problem**: Generated LaTeX templates don't compile

**Solutions**:
- Check template validation results
- Verify font availability
- Review color definitions
- Test with minimal content first

#### LLM Integration Issues

**Problem**: LLM calls fail or return poor results

**Solutions**:
- Check LLM configuration and API keys
- Verify network connectivity
- Use fallback strategies
- Adjust prompt parameters

#### Validation Failures

**Problem**: Imprint validation shows many errors

**Solutions**:
- Review validation results carefully
- Use auto-fix capabilities where available
- Edit problematic fields manually
- Check for consistency across components

### Error Recovery

The system includes comprehensive error recovery:

- **Fallback Strategies**: When LLM calls fail
- **Auto-Fix Capabilities**: For common validation issues
- **Graceful Degradation**: Partial functionality when components fail
- **Detailed Error Reporting**: Clear error messages and suggestions

### Performance Optimization

- **Batch Processing**: Use CLI for multiple imprints
- **Caching**: Results are cached where appropriate
- **Parallel Processing**: Multiple operations can run concurrently
- **Resource Management**: Memory and CPU usage are optimized

## Examples

### Example 1: Literary Fiction Imprint

**Input:**
```
A premium literary imprint specializing in contemporary fiction and literary non-fiction 
for educated adult readers aged 25-55. We focus on diverse voices and innovative storytelling, 
with a sophisticated brand identity that appeals to book clubs and literary enthusiasts.
```

**Generated Imprint:**
- **Name**: Literary Voices Press
- **Mission**: Publishing exceptional contemporary literature that challenges and inspires
- **Genres**: Literary Fiction, Contemporary Fiction, Literary Non-Fiction
- **Audience**: Educated adults 25-55, book club members, literary enthusiasts
- **Brand**: Sophisticated, elegant, diverse, quality-focused

### Example 2: Young Adult Fantasy

**Input:**
```
A young adult fantasy imprint targeting readers aged 13-18 with epic fantasy, urban fantasy, 
and magical realism. Modern, exciting brand that connects with teens through social media.
```

**Generated Imprint:**
- **Name**: Mystic Realms YA
- **Mission**: Bringing magical worlds to young adult readers
- **Genres**: Epic Fantasy, Urban Fantasy, Magical Realism
- **Audience**: Teens 13-18, fantasy enthusiasts, social media active
- **Brand**: Modern, exciting, magical, teen-focused

### Example 3: Business Books

**Input:**
```
Professional business book imprint targeting entrepreneurs and business leaders. 
Focus on practical guides, leadership, innovation, and startup advice. 
Clean, professional brand identity.
```

**Generated Imprint:**
- **Name**: Executive Edge Publishing
- **Mission**: Empowering business leaders with practical insights
- **Genres**: Business, Leadership, Entrepreneurship, Innovation
- **Audience**: Entrepreneurs, executives, business professionals
- **Brand**: Professional, authoritative, practical, results-oriented

### Batch Processing Example

**batch_config.json:**
```json
{
  "description": "Multiple imprint creation",
  "imprints": [
    {
      "name": "Literary Fiction Imprint",
      "concept": "A literary imprint focused on contemporary fiction...",
      "config_file": "config_literary.json"
    },
    {
      "name": "YA Fantasy Imprint", 
      "concept": "Young adult fantasy imprint targeting teens...",
      "config_file": "config_ya.json"
    }
  ]
}
```

**Command:**
```bash
python tools/imprint_builder_cli.py batch-create batch_config.json output_dir/
```

## Integration with Existing Pipeline

The imprint builder integrates seamlessly with the existing codexes-factory pipeline:

### LSI CSV Generation

Generated imprints automatically work with the LSI CSV generation system:

```python
from codexes.modules.distribution.lsi_acs_generator import LsiAcsGenerator

# Use imprint configuration
generator = LsiAcsGenerator(imprint_config="configs/imprints/my_imprint.json")
```

### Template System

Generated templates integrate with the existing template system:

```
imprints/
  my_imprint/
    templates/
      template.tex
      cover.tex
      styles.sty
```

### Field Mapping

Imprint-specific field mappings are automatically created and integrated:

```python
from codexes.modules.distribution.field_mapping_registry import FieldMappingRegistry

registry = FieldMappingRegistry()
# Imprint-specific mappings are automatically loaded
```

## Support and Resources

### Documentation

- [API Reference](API_REFERENCE.md)
- [Best Practices](BEST_PRACTICES.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Examples Repository](examples/)

### Community

- GitHub Issues for bug reports
- Discussions for questions and ideas
- Wiki for community documentation

### Development

- Contributing guidelines
- Development setup
- Testing procedures
- Release process

---

*This guide covers the essential aspects of using the Streamlined Imprint Builder. For more detailed information, refer to the API documentation and examples.*