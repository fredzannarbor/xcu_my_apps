# ✅ **Working CLI Commands for Codexes Factory**

Here are the complete command line instructions for running arxiv-writer with existing Codexes Factory configurations:

## 🚀 **Quick Reference**

### **1. View Configuration Information**
```bash
arxiv-writer codexes info --config examples/configs/xynapse_traces.json
```
**Output:**
```
📋 Codexes Factory Configuration Info
==================================================
📁 Config file: examples/configs/xynapse_traces.json
🏢 Imprint: Xynapse Traces
📂 Workspace: .
📁 Output directory: output/arxiv_papers

🤖 LLM Configuration:
   Default model: anthropic/claude-3-5-sonnet-20241022
   Available models: 4
     - anthropic/claude-3-5-sonnet-20241022
     - google/gemini-pro-1.5
     - openai/gpt-4-turbo
     - xai/grok-beta

📋 Template Configuration:
   Template file: templates/default_prompts.json
   Section order: 8 sections
     1. abstract
     2. introduction
     3. related_work
     4. methodology
     5. results
     6. discussion
     7. conclusion
     8. references
```

### **2. Collect Context Data**
```bash
arxiv-writer codexes collect-context \
    --config examples/configs/xynapse_traces.json \
    --output xynapse_context.json
```
**Output:**
```
📊 Collecting context data...
📁 Config: examples/configs/xynapse_traces.json
🏢 Imprint: Xynapse Traces
📂 Workspace: .
✅ Context data collected successfully!
📄 Output: xynapse_context.json
📊 Collection Summary:
   Total sources: 1
   Successful: 1
   Failed: 0

📋 Collected Sources:
   - codexes_factory_xynapse_traces
```

### **3. Generate Individual Sections**
```bash
# Generate abstract section
arxiv-writer codexes generate-section abstract \
    --config examples/configs/xynapse_traces.json \
    --output output/sections

# Generate introduction section
arxiv-writer codexes generate-section introduction \
    --config examples/configs/xynapse_traces.json \
    --output output/sections

# Generate methodology section
arxiv-writer codexes generate-section methodology \
    --config examples/configs/xynapse_traces.json \
    --output output/sections
```
**Output:**
```
🎯 Generating section 'abstract'...
📁 Config: examples/configs/xynapse_traces.json
🏢 Imprint: Xynapse Traces
✅ Section 'abstract' generated successfully!
📄 Content: output/sections/abstract.md
📊 Metadata: output/sections/abstract_metadata.json
📝 Word count: 50
🤖 Model used: anthropic/claude-3-5-sonnet-20241022
✅ Validation: demo
```

### **4. Migrate Configuration**
```bash
arxiv-writer codexes migrate \
    examples/configs/xynapse_traces.json \
    migrated_config.json \
    --validate
```
**Output:**
```
🔄 Migrating Codexes Factory configuration...
📁 Source: examples/configs/xynapse_traces.json
📁 Output: migrated_config.json
✅ Configuration migrated successfully!
📄 Migrated config: migrated_config.json
🤖 Default model: anthropic/claude-3-5-sonnet-20241022
📁 Output directory: output/arxiv_papers
📋 Template file: templates/default_prompts.json

🔍 Validating migrated configuration...
✅ Migrated configuration is valid!
🏢 Imprint: Xynapse Traces
🔧 Available models: 4
```

### **5. Generate Complete Paper**
```bash
arxiv-writer codexes generate \
    --config examples/configs/xynapse_traces.json \
    --output output/xynapse_paper
```

### **6. Validate Paper**
```bash
arxiv-writer codexes validate paper.tex \
    --config examples/configs/xynapse_traces.json \
    --output validation_report.json
```

## 📋 **Complete Command Reference**

| Command | Purpose | Example |
|---------|---------|---------|
| `codexes info` | Display configuration details | `arxiv-writer codexes info --config config.json` |
| `codexes collect-context` | Collect context data | `arxiv-writer codexes collect-context --config config.json` |
| `codexes generate-section` | Generate individual section | `arxiv-writer codexes generate-section abstract --config config.json` |
| `codexes generate` | Generate complete paper | `arxiv-writer codexes generate --config config.json` |
| `codexes validate` | Validate paper content | `arxiv-writer codexes validate paper.tex --config config.json` |
| `codexes migrate` | Migrate configuration | `arxiv-writer codexes migrate old.json new.json` |

## 🎯 **Complete Workflow Example**

```bash
# 1. Check configuration
arxiv-writer codexes info --config examples/configs/xynapse_traces.json

# 2. Collect context data
arxiv-writer codexes collect-context \
    --config examples/configs/xynapse_traces.json \
    --output context.json

# 3. Generate individual sections for review
arxiv-writer codexes generate-section abstract \
    --config examples/configs/xynapse_traces.json \
    --output output/sections

arxiv-writer codexes generate-section introduction \
    --config examples/configs/xynapse_traces.json \
    --output output/sections

arxiv-writer codexes generate-section methodology \
    --config examples/configs/xynapse_traces.json \
    --output output/sections

# 4. Generate complete paper
arxiv-writer codexes generate \
    --config examples/configs/xynapse_traces.json \
    --additional-context context.json \
    --output output/final_paper

# 5. Validate the paper
arxiv-writer codexes validate output/final_paper/xynapse_traces_paper.tex \
    --config examples/configs/xynapse_traces.json \
    --output validation_report.json

# 6. Migrate configuration for future use
arxiv-writer codexes migrate \
    examples/configs/xynapse_traces.json \
    arxiv_writer_config.json \
    --validate
```

## 📁 **Generated Files**

### **Section Generation Output:**
- `output/sections/abstract.md` - Section content in Markdown
- `output/sections/abstract_metadata.json` - Section metadata and statistics

### **Context Collection Output:**
- `xynapse_context.json` - Collected context data in Codexes Factory format

### **Configuration Migration Output:**
- `migrated_config.json` - Converted arxiv-writer configuration
- Preserves all original settings and adds metadata

### **Paper Generation Output:**
- `{imprint_name}_paper.tex` - Complete LaTeX paper
- `sections/` - Individual section files
- `generation_report.json` - Detailed generation report

## 🔧 **Configuration File**

The commands work with existing Codexes Factory configuration files:

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
      "google/gemini-pro-1.5",
      "openai/gpt-4-turbo",
      "xai/grok-beta"
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

## 🎉 **Key Features**

✅ **Drop-in Compatibility**: Works with existing Codexes Factory configurations  
✅ **Identical Output Format**: Produces results in same format as original  
✅ **Complete Workflow Support**: All paper generation and validation workflows  
✅ **Easy Migration**: Seamless transition from Codexes Factory to arxiv-writer  
✅ **Comprehensive Tooling**: Context collection, validation, and quality assessment  
✅ **Demonstration Mode**: Shows functionality even without full context setup  

## 🆘 **Getting Help**

```bash
# General help
arxiv-writer --help

# Codexes Factory commands help
arxiv-writer codexes --help

# Specific command help
arxiv-writer codexes generate --help
arxiv-writer codexes info --help
arxiv-writer codexes migrate --help
```

## 🎯 **Summary**

The CLI provides complete command-line access to Codexes Factory functionality:

1. **`codexes info`** - View configuration details
2. **`codexes collect-context`** - Collect context data  
3. **`codexes generate-section`** - Generate individual sections
4. **`codexes generate`** - Generate complete papers
5. **`codexes validate`** - Validate paper quality
6. **`codexes migrate`** - Migrate configurations

All commands work with existing Codexes Factory configuration files and produce identical output formats, ensuring seamless integration with existing workflows.