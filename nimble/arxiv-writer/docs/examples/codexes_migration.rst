Codexes Factory Migration Guide
===============================

This guide helps you migrate from the existing Codexes Factory arxiv paper generation functionality to the standalone ArXiv Writer package.

Overview
--------

The ArXiv Writer package provides a compatibility layer that allows you to:

1. **Drop-in replacement:** Use ArXiv Writer with minimal changes to existing workflows
2. **Configuration migration:** Convert Codexes Factory configurations automatically
3. **Identical output:** Generate papers that match existing Codexes Factory output
4. **Gradual migration:** Migrate incrementally while maintaining existing functionality

Migration Process
-----------------

Step 1: Install ArXiv Writer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install alongside Codexes Factory (no conflicts)
   pip install arxiv-writer
   
   # Or install in a separate environment
   python -m venv arxiv-writer-env
   source arxiv-writer-env/bin/activate
   pip install arxiv-writer

Step 2: Analyze Current Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, identify your current Codexes Factory configuration:

.. code-block:: bash

   # Find your current configuration files
   find . -name "*config*.json" -o -name "*imprint*.json"
   
   # Common locations:
   # - examples/configs/
   # - .codexes/
   # - config/

**Example Codexes Factory Configuration:**

.. code-block:: json

   {
     "llm_config": {
       "model": "gpt-4",
       "temperature": 0.7,
       "max_tokens": 4000
     },
     "paper_config": {
       "sections": ["abstract", "introduction", "methodology", "results", "conclusion"],
       "output_format": "latex",
       "compile_pdf": true
     },
     "context_sources": [
       {
         "type": "csv",
         "path": "data/results.csv"
       }
     ]
   }

Step 3: Automatic Configuration Migration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the built-in migration tool:

.. code-block:: bash

   # Migrate configuration automatically
   arxiv-writer config migrate \
     --input examples/configs/basic_config.json \
     --output arxiv_writer_config.json \
     --format codexes-factory

**Python API Migration:**

.. code-block:: python

   from arxiv_writer.core.codexes_factory_adapter import CodexesFactoryAdapter
   from arxiv_writer import PaperConfig

   # Load Codexes Factory configuration
   adapter = CodexesFactoryAdapter()
   codexes_config = adapter.load_codexes_config("examples/configs/basic_config.json")
   
   # Convert to ArXiv Writer format
   arxiv_config = adapter.migrate_config(codexes_config)
   
   # Save migrated configuration
   arxiv_config.save_to_file("arxiv_writer_config.json")
   
   print("✅ Configuration migrated successfully!")

Step 4: Verify Migration
~~~~~~~~~~~~~~~~~~~~~~~~

Compare outputs to ensure identical results:

.. code-block:: bash

   # Generate with original Codexes Factory
   python -m codexes_factory.generate_paper --config original_config.json
   
   # Generate with ArXiv Writer
   arxiv-writer generate --config arxiv_writer_config.json --context context.json
   
   # Compare outputs
   diff codexes_output/paper.tex arxiv_writer_output/paper.tex

Configuration Mapping
---------------------

Codexes Factory to ArXiv Writer Mapping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 40 20

   * - Codexes Factory
     - ArXiv Writer
     - Notes
   * - ``llm_config.model``
     - ``llm.model``
     - Direct mapping
   * - ``llm_config.temperature``
     - ``llm.temperature``
     - Direct mapping
   * - ``paper_config.sections``
     - ``sections``
     - Structure preserved
   * - ``paper_config.output_format``
     - ``output.format``
     - Direct mapping
   * - ``context_sources``
     - ``context.sources``
     - Enhanced structure
   * - ``validation_rules``
     - ``validation.rules``
     - Extended options
   * - ``template_config``
     - ``templates``
     - Improved flexibility

**Detailed Mapping Example:**

**Codexes Factory:**

.. code-block:: json

   {
     "llm_config": {
       "provider": "openai",
       "model": "gpt-4",
       "temperature": 0.7,
       "max_tokens": 4000,
       "api_key_env": "OPENAI_API_KEY"
     },
     "paper_config": {
       "title": "Research Paper",
       "sections": {
         "abstract": {"max_words": 250, "enabled": true},
         "introduction": {"max_words": 800, "enabled": true},
         "methodology": {"max_words": 1200, "enabled": true},
         "results": {"max_words": 1000, "enabled": true},
         "conclusion": {"max_words": 400, "enabled": true}
       },
       "output_format": "latex",
       "output_directory": "./output",
       "compile_pdf": true
     },
     "template_config": {
       "prompts_file": "templates/research_prompts.json",
       "style": "academic"
     },
     "validation_config": {
       "enabled": true,
       "strict_mode": false,
       "quality_threshold": 0.7
     }
   }

**ArXiv Writer (Migrated):**

.. code-block:: json

   {
     "llm": {
       "provider": "openai",
       "model": "gpt-4",
       "temperature": 0.7,
       "max_tokens": 4000,
       "api_key": "${OPENAI_API_KEY}"
     },
     "sections": {
       "abstract": {"enabled": true, "max_words": 250},
       "introduction": {"enabled": true, "max_words": 800},
       "methodology": {"enabled": true, "max_words": 1200},
       "results": {"enabled": true, "max_words": 1000},
       "conclusion": {"enabled": true, "max_words": 400}
     },
     "output": {
       "format": "latex",
       "directory": "./output",
       "compile_pdf": true
     },
     "templates": {
       "prompts_file": "templates/research_prompts.json",
       "style": "academic"
     },
     "validation": {
       "enabled": true,
       "strict_mode": false,
       "quality_thresholds": {
         "minimum_score": 0.7
       }
     }
   }

Compatibility Mode
------------------

Using Codexes Factory Adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For seamless integration, use the compatibility adapter:

.. code-block:: python

   from arxiv_writer.core.codexes_factory_adapter import CodexesFactoryAdapter
   from arxiv_writer import ArxivPaperGenerator

   # Initialize adapter
   adapter = CodexesFactoryAdapter()
   
   # Load Codexes Factory configuration directly
   config = adapter.load_and_convert_config("examples/configs/basic_config.json")
   
   # Use with ArXiv Writer
   generator = ArxivPaperGenerator(config)
   
   # Generate paper with Codexes Factory context format
   codexes_context = {
       "project_data": {...},
       "analysis_results": {...},
       "metadata": {...}
   }
   
   # Adapter handles context conversion
   result = adapter.generate_paper(generator, codexes_context)
   
   print(f"Generated paper: {result.output_path}")

Xynapse Traces Integration
~~~~~~~~~~~~~~~~~~~~~~~~~

Migrate xynapse traces configurations:

**Original xynapse_traces.json:**

.. code-block:: json

   {
     "imprint_config": {
       "analysis_type": "comprehensive",
       "include_performance_metrics": true,
       "generate_visualizations": false
     },
     "paper_structure": {
       "include_related_work": true,
       "methodology_detail_level": "high",
       "results_format": "tables_and_text"
     },
     "llm_settings": {
       "model": "gpt-4",
       "temperature": 0.6,
       "context_window": 8000
     }
   }

**Migrated ArXiv Writer Configuration:**

.. code-block:: json

   {
     "llm": {
       "model": "gpt-4",
       "temperature": 0.6,
       "max_tokens": 8000
     },
     "context": {
       "sources": [
         {
           "type": "xynapse_traces",
           "path": "examples/configs/imprints/xynapse_traces.json",
           "analysis_type": "comprehensive",
           "include_performance_metrics": true
         }
       ]
     },
     "sections": {
       "related_work": {"enabled": true, "max_words": 1000},
       "methodology": {"enabled": true, "max_words": 1500, "detail_level": "high"},
       "results": {"enabled": true, "format": "tables_and_text"}
     },
     "templates": {
       "custom_templates": {
         "results": "Present results in both tabular format and descriptive text. Include performance metrics: {performance_metrics}"
       }
     }
   }

**Migration Script:**

.. code-block:: python

   def migrate_xynapse_config(xynapse_path, output_path):
       """Migrate xynapse traces configuration."""
       adapter = CodexesFactoryAdapter()
       
       # Load xynapse configuration
       xynapse_config = adapter.load_xynapse_config(xynapse_path)
       
       # Convert to ArXiv Writer format
       arxiv_config = adapter.convert_xynapse_config(xynapse_config)
       
       # Save migrated configuration
       arxiv_config.save_to_file(output_path)
       
       return arxiv_config

   # Usage
   migrated_config = migrate_xynapse_config(
       "examples/configs/imprints/xynapse_traces.json",
       "arxiv_xynapse_config.json"
   )

Step-by-Step Migration Examples
-------------------------------

Example 1: Basic Research Paper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Original Codexes Factory Workflow:**

.. code-block:: python

   # Original Codexes Factory code
   from codexes_factory.paper_generator import PaperGenerator
   from codexes_factory.config import load_config

   config = load_config("examples/configs/basic_config.json")
   generator = PaperGenerator(config)
   
   context_data = {
       "project_name": "ML Research",
       "results_file": "data/results.csv",
       "metadata": {...}
   }
   
   paper = generator.generate_paper(context_data)

**Migrated ArXiv Writer Code:**

.. code-block:: python

   # Migrated ArXiv Writer code
   from arxiv_writer import ArxivPaperGenerator, PaperConfig
   from arxiv_writer.core.codexes_factory_adapter import CodexesFactoryAdapter

   # Option 1: Direct migration
   adapter = CodexesFactoryAdapter()
   config = adapter.load_and_convert_config("examples/configs/basic_config.json")
   generator = ArxivPaperGenerator(config)
   
   # Context format remains the same
   context_data = {
       "project_name": "ML Research",
       "results_file": "data/results.csv",
       "metadata": {...}
   }
   
   result = generator.generate_paper(context_data)

   # Option 2: Use migrated configuration file
   config = PaperConfig.from_file("migrated_config.json")
   generator = ArxivPaperGenerator(config)
   result = generator.generate_paper(context_data)

Example 2: Complex Multi-Source Paper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Original Codexes Factory Setup:**

.. code-block:: json

   {
     "context_sources": [
       {"type": "csv", "path": "data/experiments.csv"},
       {"type": "json", "path": "data/metadata.json"},
       {"type": "directory", "path": "analysis/"}
     ],
     "paper_config": {
       "sections": {
         "abstract": {"enabled": true},
         "introduction": {"enabled": true},
         "related_work": {"enabled": true},
         "methodology": {"enabled": true},
         "experiments": {"enabled": true},
         "results": {"enabled": true},
         "discussion": {"enabled": true},
         "conclusion": {"enabled": true}
       }
     }
   }

**Migrated ArXiv Writer Configuration:**

.. code-block:: json

   {
     "context": {
       "sources": [
         {
           "type": "csv",
           "path": "data/experiments.csv",
           "description": "Experimental results and metrics"
         },
         {
           "type": "json", 
           "path": "data/metadata.json",
           "description": "Project metadata and configuration"
         },
         {
           "type": "directory",
           "path": "analysis/",
           "description": "Analysis scripts and outputs"
         }
       ]
     },
     "sections": {
       "abstract": {"enabled": true, "max_words": 250},
       "introduction": {"enabled": true, "max_words": 800},
       "related_work": {"enabled": true, "max_words": 1000},
       "methodology": {"enabled": true, "max_words": 1200},
       "experiments": {"enabled": true, "max_words": 1000},
       "results": {"enabled": true, "max_words": 1200},
       "discussion": {"enabled": true, "max_words": 800},
       "conclusion": {"enabled": true, "max_words": 400}
     }
   }

Validation and Testing
----------------------

Ensuring Identical Output
~~~~~~~~~~~~~~~~~~~~~~~~~

Create a validation script to ensure migrated configurations produce identical results:

.. code-block:: python

   import difflib
   from pathlib import Path

   def validate_migration(codexes_output, arxiv_output):
       """Validate that migration produces identical output."""
       
       # Read both outputs
       with open(codexes_output, 'r') as f:
           codexes_content = f.read()
       
       with open(arxiv_output, 'r') as f:
           arxiv_content = f.read()
       
       # Compare content
       if codexes_content == arxiv_content:
           print("✅ Perfect match! Migration successful.")
           return True
       
       # Show differences
       diff = difflib.unified_diff(
           codexes_content.splitlines(keepends=True),
           arxiv_content.splitlines(keepends=True),
           fromfile='codexes_factory',
           tofile='arxiv_writer'
       )
       
       print("❌ Differences found:")
       for line in diff:
           print(line, end='')
       
       return False

   # Usage
   validate_migration(
       "codexes_output/paper.tex",
       "arxiv_writer_output/paper.tex"
   )

Regression Testing
~~~~~~~~~~~~~~~~~~

Set up automated regression tests:

.. code-block:: python

   import pytest
   from arxiv_writer.core.codexes_factory_adapter import CodexesFactoryAdapter
   from arxiv_writer import ArxivPaperGenerator

   class TestCodexesMigration:
       
       def test_basic_config_migration(self):
           """Test basic configuration migration."""
           adapter = CodexesFactoryAdapter()
           
           # Load and migrate
           config = adapter.load_and_convert_config(
               "examples/configs/basic_config.json"
           )
           
           # Verify key settings
           assert config.llm.model == "gpt-4"
           assert config.llm.temperature == 0.7
           assert config.output.format == "latex"
       
       def test_xynapse_traces_migration(self):
           """Test xynapse traces configuration migration."""
           adapter = CodexesFactoryAdapter()
           
           config = adapter.load_and_convert_config(
               "examples/configs/imprints/xynapse_traces.json"
           )
           
           # Verify xynapse-specific settings
           assert "xynapse_traces" in [s.type for s in config.context.sources]
       
       def test_output_compatibility(self):
           """Test that output matches Codexes Factory."""
           # This would require running both systems and comparing
           pass

   # Run tests
   pytest.run(["test_migration.py", "-v"])

Common Migration Issues
-----------------------

Template Compatibility
~~~~~~~~~~~~~~~~~~~~~~

**Issue:** Custom templates don't work after migration.

**Solution:**

.. code-block:: python

   # Update template format
   def migrate_templates(codexes_templates):
       """Migrate Codexes Factory templates to ArXiv Writer format."""
       
       migrated = {}
       
       for section, template in codexes_templates.items():
           # Convert Codexes Factory placeholders to ArXiv Writer format
           migrated_template = template.replace(
               "{project_data}", "{context_data}"
           ).replace(
               "{analysis_results}", "{results_summary}"
           )
           
           migrated[section] = {
               "user_prompt": migrated_template,
               "context_variables": extract_variables(migrated_template)
           }
       
       return migrated

Context Data Format
~~~~~~~~~~~~~~~~~~~

**Issue:** Context data structure differences.

**Solution:**

.. code-block:: python

   def adapt_context_data(codexes_context):
       """Adapt Codexes Factory context to ArXiv Writer format."""
       
       adapted = {}
       
       # Map common fields
       if "project_data" in codexes_context:
           adapted.update(codexes_context["project_data"])
       
       if "analysis_results" in codexes_context:
           adapted["results_summary"] = codexes_context["analysis_results"]
       
       if "metadata" in codexes_context:
           adapted.update(codexes_context["metadata"])
       
       return adapted

Performance Differences
~~~~~~~~~~~~~~~~~~~~~~~

**Issue:** Different generation times or token usage.

**Solution:**

.. code-block:: python

   # Monitor and compare performance
   def compare_performance(codexes_result, arxiv_result):
       """Compare performance metrics."""
       
       print(f"Codexes Factory:")
       print(f"  Time: {codexes_result.generation_time}")
       print(f"  Tokens: {codexes_result.token_usage}")
       
       print(f"ArXiv Writer:")
       print(f"  Time: {arxiv_result.generation_time}")
       print(f"  Tokens: {arxiv_result.token_usage}")
       
       # Adjust configuration if needed
       if arxiv_result.generation_time > codexes_result.generation_time * 1.2:
           print("⚠️  ArXiv Writer is slower, consider optimization")

Best Practices for Migration
----------------------------

1. **Incremental Migration**
   - Start with simple configurations
   - Test each component separately
   - Gradually migrate complex features

2. **Maintain Parallel Systems**
   - Keep Codexes Factory running during transition
   - Compare outputs regularly
   - Have rollback plan ready

3. **Documentation**
   - Document all configuration changes
   - Keep migration notes for team members
   - Update deployment procedures

4. **Testing**
   - Create comprehensive test suite
   - Test with real data and configurations
   - Validate output quality and format

5. **Team Training**
   - Train team on new ArXiv Writer features
   - Update development workflows
   - Share migration experiences

Post-Migration Optimization
---------------------------

After successful migration, take advantage of ArXiv Writer's enhanced features:

.. code-block:: json

   {
     "llm": {
       "providers": [
         {"provider": "openai", "model": "gpt-4", "priority": 1},
         {"provider": "anthropic", "model": "claude-3-sonnet", "priority": 2}
       ]
     },
     "validation": {
       "quality_thresholds": {
         "minimum_score": 0.8,
         "section_scores": {
           "methodology": 0.85,
           "results": 0.9
         }
       }
     },
     "plugins": {
       "enabled": true,
       "plugins": {
         "custom_formatter": {"enabled": true},
         "quality_enhancer": {"enabled": true}
       }
     }
   }

Support and Resources
---------------------

If you encounter issues during migration:

1. **Check the migration logs** for detailed error information
2. **Use the validation tools** to identify configuration problems
3. **Consult the troubleshooting guide** for common issues
4. **Create GitHub issues** for migration-specific problems
5. **Join community discussions** for migration tips and experiences

The migration process is designed to be smooth and maintain full compatibility with your existing Codexes Factory workflows while providing access to ArXiv Writer's enhanced features and capabilities.