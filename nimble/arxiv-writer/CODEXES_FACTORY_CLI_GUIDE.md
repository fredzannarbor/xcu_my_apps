# Codexes Factory CLI Commands

This guide shows you how to use the command line interface to run arxiv-writer with existing Codexes Factory configurations.

## 🚀 Quick Start

### 1. Generate Paper with Codexes Factory Config

```bash
# Generate complete paper using Xynapse Traces configuration
arxiv-writer codexes generate \
    --config examples/configs/xynapse_traces.json \
    --output output/xynapse_traces_paper

# With verbose output
arxiv-writer --verbose codexes generate \
    --config examples/configs/xynapse_traces.json \
    --output output/xynapse_traces_paper
```

### 2. Generate Individual Section

```bash
# Generate just the abstract section
arxiv-writer codexes generate-section abstract \
    --config examples/configs/xynapse_traces.json \
    --output output/sections

# Generate introduction with additional context
arxiv-writer codexes generate-section introduction \
    --config examples/configs/xynapse_traces.json \
    --additional-context additional_data.json \
    --output output/sections
```

### 3. Validate Paper with Codexes Factory Standards

```bash
# Validate a paper using Codexes Factory quality standards
arxiv-writer codexes validate paper.tex \
    --config examples/configs/xynapse_traces.json \
    --output validation_report.json
```

### 4. Collect Context Data

```bash
# Collect context data for paper generation
arxiv-writer codexes collect-context \
    --config examples/configs/xynapse_traces.json \
    --output xynapse_context.json
```

### 5. Migrate Configuration

```bash
# Migrate Codexes Factory config to arxiv-writer format
arxiv-writer codexes migrate \
    examples/configs/xynapse_traces.json \
    arxiv_writer_config.json \
    --validate
```

### 6. View Configuration Information

```bash
# Display detailed information about a Codexes Factory configuration
arxiv-writer codexes info \
    --config examples/configs/xynapse_traces.json
```

## 📋 Complete Command Reference

### `arxiv-writer codexes generate`

Generate a complete academic paper using Codexes Factory configuration.

**Usage:**
```bash
arxiv-writer codexes generate [OPTIONS]
```

**Options:**
- `--config, -c PATH` (required): Codexes Factory configuration file
- `--output, -o PATH`: Output directory (default: `output`)
- `--additional-context PATH`: Additional context data file (JSON)

**Example:**
```bash
arxiv-writer codexes generate \
    --config examples/configs/xynapse_traces.json \
    --output output/my_paper \
    --additional-context extra_context.json
```

**Output:**
- `{imprint_name}_paper.tex`: Complete LaTeX paper
- `sections/`: Individual section files
- `generation_report.json`: Detailed generation report

### `arxiv-writer codexes generate-section`

Generate a specific paper section using Codexes Factory configuration.

**Usage:**
```bash
arxiv-writer codexes generate-section SECTION_NAME [OPTIONS]
```

**Arguments:**
- `SECTION_NAME`: Name of section to generate (abstract, introduction, methodology, etc.)

**Options:**
- `--config, -c PATH` (required): Codexes Factory configuration file
- `--output, -o PATH`: Output directory (default: `output`)
- `--additional-context PATH`: Additional context data file (JSON)

**Example:**
```bash
arxiv-writer codexes generate-section methodology \
    --config examples/configs/xynapse_traces.json \
    --output output/sections
```

**Output:**
- `{section_name}.md`: Section content in Markdown
- `{section_name}_metadata.json`: Section metadata and statistics

### `arxiv-writer codexes validate`

Validate paper content using Codexes Factory quality standards.

**Usage:**
```bash
arxiv-writer codexes validate PAPER_FILE [OPTIONS]
```

**Arguments:**
- `PAPER_FILE`: Path to paper file to validate

**Options:**
- `--config, -c PATH` (required): Codexes Factory configuration file
- `--output, -o PATH`: Output file for validation report

**Example:**
```bash
arxiv-writer codexes validate paper.tex \
    --config examples/configs/xynapse_traces.json \
    --output validation_report.json
```

**Output:**
- Console: Validation results and quality metrics
- File: Detailed validation report (if `--output` specified)

### `arxiv-writer codexes collect-context`

Collect context data using Codexes Factory configuration patterns.

**Usage:**
```bash
arxiv-writer codexes collect-context [OPTIONS]
```

**Options:**
- `--config, -c PATH` (required): Codexes Factory configuration file
- `--output, -o PATH`: Output file for context data (default: `codexes_context.json`)

**Example:**
```bash
arxiv-writer codexes collect-context \
    --config examples/configs/xynapse_traces.json \
    --output xynapse_context.json
```

**Output:**
- JSON file with collected context data in Codexes Factory format

### `arxiv-writer codexes migrate`

Migrate Codexes Factory configuration to arxiv-writer format.

**Usage:**
```bash
arxiv-writer codexes migrate CODEXES_CONFIG OUTPUT_CONFIG [OPTIONS]
```

**Arguments:**
- `CODEXES_CONFIG`: Path to Codexes Factory configuration file
- `OUTPUT_CONFIG`: Path for migrated arxiv-writer configuration

**Options:**
- `--validate`: Validate migrated configuration after migration

**Example:**
```bash
arxiv-writer codexes migrate \
    examples/configs/xynapse_traces.json \
    arxiv_writer_config.json \
    --validate
```

**Output:**
- Migrated configuration file in arxiv-writer format
- Validation results (if `--validate` used)

### `arxiv-writer codexes info`

Display detailed information about Codexes Factory configuration.

**Usage:**
```bash
arxiv-writer codexes info [OPTIONS]
```

**Options:**
- `--config, -c PATH` (required): Codexes Factory configuration file

**Example:**
```bash
arxiv-writer codexes info \
    --config examples/configs/xynapse_traces.json
```

**Output:**
- Detailed configuration information including:
  - Imprint details
  - LLM configuration
  - Template settings
  - Validation thresholds
  - Context collection settings

## 🔧 Configuration File Format

The CLI commands work with existing Codexes Factory configuration files:

```json
{
  "_config_info": {
    "description": "Xynapse Traces imprint configuration",
    "version": "2.0",
    "parent_publisher": "Nimble Books LLC"
  },
  "imprint": "Xynapse Traces",
  "publisher": "Nimble Books LLC",
  "workspace_root": ".",
  "output_directory": "output/arxiv_papers",
  "llm_config": {
    "default_model": "anthropic/claude-3-5-sonnet-20241022",
    "available_models": [
      "anthropic/claude-3-5-sonnet-20241022",
      "openai/gpt-4-turbo"
    ]
  },
  "template_config": {
    "template_file": "templates/default_prompts.json",
    "section_order": ["abstract", "introduction", "methodology", "results", "conclusion"]
  },
  "validation_config": {
    "enabled": true,
    "quality_thresholds": {
      "min_word_count": 500,
      "readability_score": 0.7
    }
  },
  "context_config": {
    "collect_book_catalog": true,
    "collect_imprint_config": true,
    "collect_technical_architecture": true,
    "collect_performance_metrics": true
  }
}
```

## 📊 Example Workflows

### Complete Paper Generation Workflow

```bash
# 1. Check configuration
arxiv-writer codexes info --config examples/configs/xynapse_traces.json

# 2. Collect context data
arxiv-writer codexes collect-context \
    --config examples/configs/xynapse_traces.json \
    --output context.json

# 3. Generate complete paper
arxiv-writer codexes generate \
    --config examples/configs/xynapse_traces.json \
    --additional-context context.json \
    --output output/final_paper

# 4. Validate generated paper
arxiv-writer codexes validate output/final_paper/xynapse_traces_paper.tex \
    --config examples/configs/xynapse_traces.json \
    --output validation_report.json
```

### Section-by-Section Generation

```bash
# Generate sections individually for review
for section in abstract introduction methodology results discussion conclusion; do
    arxiv-writer codexes generate-section $section \
        --config examples/configs/xynapse_traces.json \
        --output output/sections
done

# Validate each section
for section_file in output/sections/*.md; do
    arxiv-writer codexes validate "$section_file" \
        --config examples/configs/xynapse_traces.json
done
```

### Configuration Migration Workflow

```bash
# 1. Migrate configuration
arxiv-writer codexes migrate \
    examples/configs/xynapse_traces.json \
    migrated_config.json \
    --validate

# 2. Test with migrated configuration
arxiv-writer codexes generate \
    --config migrated_config.json \
    --output output/migrated_test

# 3. Compare results (both should be identical)
diff output/original_paper output/migrated_test
```

## 🎯 Integration with Existing Workflows

### Using with Make/Scripts

```bash
# Makefile integration
generate-xynapse-paper:
	arxiv-writer codexes generate \
		--config examples/configs/xynapse_traces.json \
		--output output/xynapse_paper

validate-papers:
	find output -name "*.tex" -exec \
		arxiv-writer codexes validate {} \
		--config examples/configs/xynapse_traces.json \;
```

### Batch Processing

```bash
# Process multiple configurations
for config in examples/configs/*.json; do
    imprint_name=$(basename "$config" .json)
    arxiv-writer codexes generate \
        --config "$config" \
        --output "output/$imprint_name"
done
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Generate ArXiv Paper
  run: |
    arxiv-writer codexes generate \
      --config .github/configs/production.json \
      --output artifacts/paper
      
- name: Validate Paper Quality
  run: |
    arxiv-writer codexes validate artifacts/paper/*.tex \
      --config .github/configs/production.json \
      --output artifacts/validation_report.json
```

## 🔍 Troubleshooting

### Common Issues

1. **Configuration file not found:**
```bash
# Check file exists and path is correct
ls -la examples/configs/xynapse_traces.json
arxiv-writer codexes info --config examples/configs/xynapse_traces.json
```

2. **Context collection failures:**
```bash
# Run with verbose output to see detailed errors
arxiv-writer --verbose codexes collect-context \
    --config examples/configs/xynapse_traces.json
```

3. **Generation failures:**
```bash
# Check configuration and run individual sections
arxiv-writer codexes info --config examples/configs/xynapse_traces.json
arxiv-writer codexes generate-section abstract \
    --config examples/configs/xynapse_traces.json
```

4. **Validation errors:**
```bash
# Get detailed validation report
arxiv-writer codexes validate paper.tex \
    --config examples/configs/xynapse_traces.json \
    --output detailed_report.json
```

### Getting Help

```bash
# General help
arxiv-writer --help

# Codexes Factory commands help
arxiv-writer codexes --help

# Specific command help
arxiv-writer codexes generate --help
arxiv-writer codexes validate --help
```

## 🎉 Summary

The Codexes Factory CLI commands provide:

✅ **Drop-in compatibility** with existing Codexes Factory configurations  
✅ **Identical output format** to original implementation  
✅ **Complete workflow support** for paper generation and validation  
✅ **Easy migration path** from Codexes Factory to arxiv-writer  
✅ **Comprehensive tooling** for context collection and quality assessment  

Use these commands to seamlessly integrate arxiv-writer into your existing Codexes Factory workflows while maintaining full compatibility and gaining access to enhanced features.