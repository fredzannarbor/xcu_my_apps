Command Line Interface
======================

ArXiv Writer provides a comprehensive command-line interface (CLI) for all paper generation tasks. This guide covers all available commands and their options.

Installation and Setup
----------------------

After installing ArXiv Writer, the ``arxiv-writer`` command becomes available:

.. code-block:: bash

   # Check installation
   arxiv-writer --version
   
   # Get help
   arxiv-writer --help

Global Options
--------------

These options are available for all commands:

.. code-block:: bash

   arxiv-writer [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]

**Global Options:**

- ``--config PATH`` - Configuration file path
- ``--verbose, -v`` - Increase verbosity (can be used multiple times)
- ``--quiet, -q`` - Suppress output
- ``--debug`` - Enable debug mode
- ``--help`` - Show help message

Main Commands
-------------

generate
~~~~~~~~

Generate a complete academic paper.

.. code-block:: bash

   arxiv-writer generate [OPTIONS]

**Options:**

- ``--config PATH`` - Configuration file (required)
- ``--context PATH`` - Context data file (JSON/YAML)
- ``--output DIR`` - Output directory (overrides config)
- ``--sections TEXT`` - Comma-separated list of sections to generate
- ``--model TEXT`` - Override LLM model
- ``--temperature FLOAT`` - Override temperature
- ``--compile/--no-compile`` - Enable/disable PDF compilation
- ``--validate/--no-validate`` - Enable/disable validation
- ``--dry-run`` - Show what would be generated without actually generating

**Examples:**

.. code-block:: bash

   # Basic generation
   arxiv-writer generate --config config.json --context data.json
   
   # Generate specific sections only
   arxiv-writer generate --config config.json --sections "abstract,introduction,conclusion"
   
   # Override model and temperature
   arxiv-writer generate --config config.json --model gpt-4-turbo --temperature 0.5
   
   # Dry run to preview
   arxiv-writer generate --config config.json --context data.json --dry-run

section
~~~~~~~

Generate individual paper sections.

.. code-block:: bash

   arxiv-writer section [OPTIONS] SECTION_NAME

**Options:**

- ``--config PATH`` - Configuration file
- ``--context PATH`` - Context data file
- ``--output PATH`` - Output file path
- ``--model TEXT`` - LLM model to use
- ``--temperature FLOAT`` - Sampling temperature
- ``--max-words INT`` - Maximum word count
- ``--template TEXT`` - Custom template override

**Examples:**

.. code-block:: bash

   # Generate introduction section
   arxiv-writer section introduction --config config.json --context data.json
   
   # Generate with custom parameters
   arxiv-writer section methodology --config config.json --max-words 1500 --temperature 0.3

validate
~~~~~~~~

Validate configuration files, generated content, or paper structure.

.. code-block:: bash

   arxiv-writer validate [OPTIONS] [TARGET]

**Options:**

- ``--config PATH`` - Configuration file to validate
- ``--paper PATH`` - Paper file to validate
- ``--strict`` - Use strict validation mode
- ``--rules TEXT`` - Comma-separated validation rules
- ``--output PATH`` - Save validation report

**Examples:**

.. code-block:: bash

   # Validate configuration
   arxiv-writer validate --config config.json
   
   # Validate generated paper
   arxiv-writer validate --paper output/paper.tex
   
   # Strict validation with specific rules
   arxiv-writer validate --paper output/paper.tex --strict --rules "word_count,citations,structure"

template
~~~~~~~~

Manage prompt templates.

.. code-block:: bash

   arxiv-writer template [SUBCOMMAND] [OPTIONS]

**Subcommands:**

- ``list`` - List available templates
- ``show`` - Show template content
- ``validate`` - Validate template syntax
- ``test`` - Test template with sample data
- ``create`` - Create new template

**Examples:**

.. code-block:: bash

   # List all templates
   arxiv-writer template list
   
   # Show specific template
   arxiv-writer template show introduction
   
   # Validate template file
   arxiv-writer template validate --file my_templates.json
   
   # Test template with sample data
   arxiv-writer template test introduction --context sample_data.json

config
~~~~~~

Configuration management utilities.

.. code-block:: bash

   arxiv-writer config [SUBCOMMAND] [OPTIONS]

**Subcommands:**

- ``show`` - Display current configuration
- ``validate`` - Validate configuration file
- ``create`` - Create configuration template
- ``migrate`` - Migrate from Codexes Factory format

**Examples:**

.. code-block:: bash

   # Show current configuration
   arxiv-writer config show --config config.json
   
   # Create configuration template
   arxiv-writer config create --output new_config.json --profile research
   
   # Migrate from Codexes Factory
   arxiv-writer config migrate --input codexes_config.json --output arxiv_config.json

quality
~~~~~~~

Assess paper quality and generate improvement suggestions.

.. code-block:: bash

   arxiv-writer quality [OPTIONS] PAPER_PATH

**Options:**

- ``--config PATH`` - Configuration file
- ``--output PATH`` - Save quality report
- ``--format TEXT`` - Report format (json, html, text)
- ``--sections TEXT`` - Assess specific sections only
- ``--threshold FLOAT`` - Quality threshold for pass/fail

**Examples:**

.. code-block:: bash

   # Assess paper quality
   arxiv-writer quality output/paper.tex
   
   # Generate detailed HTML report
   arxiv-writer quality output/paper.tex --format html --output quality_report.html
   
   # Check specific sections
   arxiv-writer quality output/paper.tex --sections "abstract,introduction"

compile
~~~~~~~

Compile LaTeX files to PDF.

.. code-block:: bash

   arxiv-writer compile [OPTIONS] LATEX_FILE

**Options:**

- ``--output PATH`` - Output PDF path
- ``--engine TEXT`` - LaTeX engine (pdflatex, xelatex, lualatex)
- ``--twice`` - Compile twice for references
- ``--cleanup`` - Remove auxiliary files
- ``--verbose`` - Show compilation output

**Examples:**

.. code-block:: bash

   # Basic compilation
   arxiv-writer compile paper.tex
   
   # Use XeLaTeX engine
   arxiv-writer compile paper.tex --engine xelatex
   
   # Compile twice and cleanup
   arxiv-writer compile paper.tex --twice --cleanup

plugin
~~~~~~

Manage plugins and extensions.

.. code-block:: bash

   arxiv-writer plugin [SUBCOMMAND] [OPTIONS]

**Subcommands:**

- ``list`` - List installed plugins
- ``install`` - Install plugin from path or URL
- ``uninstall`` - Uninstall plugin
- ``enable`` - Enable plugin
- ``disable`` - Disable plugin
- ``info`` - Show plugin information

**Examples:**

.. code-block:: bash

   # List all plugins
   arxiv-writer plugin list
   
   # Install plugin from path
   arxiv-writer plugin install ./my_plugin
   
   # Show plugin information
   arxiv-writer plugin info custom_formatter

Working with Configuration Files
--------------------------------

Environment-Specific Configs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create different configurations for different environments:

.. code-block:: bash

   # Development configuration
   arxiv-writer generate --config configs/dev.json --context data.json
   
   # Production configuration
   arxiv-writer generate --config configs/prod.json --context data.json
   
   # Testing configuration
   arxiv-writer generate --config configs/test.json --context data.json

Configuration Inheritance
~~~~~~~~~~~~~~~~~~~~~~~~~

Use base configurations with overrides:

.. code-block:: bash

   # Base configuration with model override
   arxiv-writer generate --config base.json --model gpt-3.5-turbo
   
   # Base configuration with output override
   arxiv-writer generate --config base.json --output /tmp/papers

Batch Processing
----------------

Process Multiple Papers
~~~~~~~~~~~~~~~~~~~~~~~

Use shell scripting for batch processing:

.. code-block:: bash

   #!/bin/bash
   
   # Process multiple context files
   for context_file in data/*.json; do
       output_dir="output/$(basename "$context_file" .json)"
       arxiv-writer generate \
           --config config.json \
           --context "$context_file" \
           --output "$output_dir"
   done

Parallel Processing
~~~~~~~~~~~~~~~~~~~

Process papers in parallel:

.. code-block:: bash

   # Using GNU parallel
   parallel arxiv-writer generate --config config.json --context {} --output output/{/.} ::: data/*.json
   
   # Using xargs
   ls data/*.json | xargs -I {} -P 4 arxiv-writer generate --config config.json --context {} --output output/{/.}

Pipeline Integration
--------------------

CI/CD Integration
~~~~~~~~~~~~~~~~~

Integrate with continuous integration:

.. code-block:: yaml

   # GitHub Actions example
   name: Generate Papers
   on: [push]
   jobs:
     generate:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Setup Python
           uses: actions/setup-python@v2
           with:
             python-version: '3.11'
         - name: Install dependencies
           run: |
             pip install arxiv-writer
             sudo apt-get install texlive-full
         - name: Generate papers
           run: |
             arxiv-writer generate --config .github/config.json --context data/
           env:
             OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

Makefile Integration
~~~~~~~~~~~~~~~~~~~~

Use with Make for reproducible builds:

.. code-block:: makefile

   # Makefile
   .PHONY: papers clean validate
   
   papers: output/paper.pdf
   
   output/paper.pdf: config.json data.json
   	arxiv-writer generate --config config.json --context data.json
   
   validate: output/paper.tex
   	arxiv-writer validate --paper output/paper.tex --strict
   
   clean:
   	rm -rf output/

Debugging and Troubleshooting
------------------------------

Verbose Output
~~~~~~~~~~~~~~

Use verbose flags for debugging:

.. code-block:: bash

   # Basic verbose output
   arxiv-writer generate --config config.json --verbose
   
   # Maximum verbosity
   arxiv-writer generate --config config.json -vvv
   
   # Debug mode
   arxiv-writer generate --config config.json --debug

Dry Run Mode
~~~~~~~~~~~~

Test configurations without generating:

.. code-block:: bash

   # Preview what would be generated
   arxiv-writer generate --config config.json --context data.json --dry-run

Log Files
~~~~~~~~~

Enable logging to files:

.. code-block:: bash

   # Set log file via environment variable
   export ARXIV_WRITER_LOG_FILE=arxiv-writer.log
   arxiv-writer generate --config config.json --context data.json

Common Issues and Solutions
---------------------------

Configuration Errors
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Validate configuration first
   arxiv-writer validate --config config.json
   
   # Show resolved configuration
   arxiv-writer config show --config config.json

API Key Issues
~~~~~~~~~~~~~~

.. code-block:: bash

   # Test API key
   export OPENAI_API_KEY="your-key"
   arxiv-writer generate --config config.json --dry-run

LaTeX Compilation Issues
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Test LaTeX installation
   arxiv-writer compile --help
   
   # Compile with verbose output
   arxiv-writer compile paper.tex --verbose

Performance Optimization
------------------------

Parallel Section Generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Generate sections in parallel
   arxiv-writer section abstract --config config.json --context data.json &
   arxiv-writer section introduction --config config.json --context data.json &
   arxiv-writer section conclusion --config config.json --context data.json &
   wait

Model Selection
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Use faster model for simple sections
   arxiv-writer section abstract --model gpt-3.5-turbo
   
   # Use powerful model for complex sections
   arxiv-writer section methodology --model gpt-4

For more advanced usage patterns, see the :doc:`examples/advanced_configuration` guide.