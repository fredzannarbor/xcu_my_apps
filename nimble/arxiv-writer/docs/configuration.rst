Configuration Reference
=======================

ArXiv Writer uses a hierarchical configuration system that allows you to customize every aspect of paper generation. This guide covers all configuration options and how to use them effectively.

Configuration Sources
---------------------

Configuration can be loaded from multiple sources, in order of precedence:

1. **Direct instantiation** - Passed directly to ``PaperConfig()``
2. **Configuration files** - JSON, YAML, or TOML files
3. **Environment variables** - For sensitive data like API keys
4. **Default values** - Built-in sensible defaults

Configuration File Formats
---------------------------

JSON Format
~~~~~~~~~~~

.. code-block:: json

   {
     "llm": {
       "provider": "openai",
       "model": "gpt-4",
       "temperature": 0.7,
       "api_key": "${OPENAI_API_KEY}"
     },
     "templates": {
       "prompts_file": "templates/default_prompts.json"
     },
     "output": {
       "directory": "./output",
       "format": "latex",
       "compile_pdf": true
     }
   }

YAML Format
~~~~~~~~~~~

.. code-block:: yaml

   llm:
     provider: openai
     model: gpt-4
     temperature: 0.7
     api_key: ${OPENAI_API_KEY}
   
   templates:
     prompts_file: templates/default_prompts.json
   
   output:
     directory: ./output
     format: latex
     compile_pdf: true

TOML Format
~~~~~~~~~~~

.. code-block:: toml

   [llm]
   provider = "openai"
   model = "gpt-4"
   temperature = 0.7
   api_key = "${OPENAI_API_KEY}"
   
   [templates]
   prompts_file = "templates/default_prompts.json"
   
   [output]
   directory = "./output"
   format = "latex"
   compile_pdf = true

Configuration Sections
----------------------

LLM Configuration
~~~~~~~~~~~~~~~~~

Controls how the system interacts with Language Learning Models.

.. code-block:: json

   {
     "llm": {
       "provider": "openai",
       "model": "gpt-4",
       "temperature": 0.7,
       "max_tokens": 4000,
       "api_key": "${OPENAI_API_KEY}",
       "api_base": "https://api.openai.com/v1",
       "timeout": 60,
       "retry": {
         "max_attempts": 3,
         "base_delay": 1.0,
         "max_delay": 60.0,
         "exponential_base": 2.0,
         "jitter": true
       },
       "rate_limit": {
         "requests_per_minute": 60,
         "tokens_per_minute": 150000
       }
     }
   }

**Parameters:**

- ``provider`` (str): LLM provider name (``openai``, ``anthropic``, ``google``, etc.)
- ``model`` (str): Specific model to use
- ``temperature`` (float): Sampling temperature (0.0-2.0)
- ``max_tokens`` (int): Maximum tokens per request
- ``api_key`` (str): API key (supports environment variable substitution)
- ``api_base`` (str): Custom API endpoint
- ``timeout`` (int): Request timeout in seconds
- ``retry`` (dict): Retry configuration
- ``rate_limit`` (dict): Rate limiting configuration

Supported Providers
^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Provider
     - Models
     - API Key Environment Variable
   * - OpenAI
     - gpt-4, gpt-3.5-turbo, gpt-4-turbo
     - OPENAI_API_KEY
   * - Anthropic
     - claude-3-opus, claude-3-sonnet, claude-3-haiku
     - ANTHROPIC_API_KEY
   * - Google
     - gemini-pro, gemini-pro-vision
     - GOOGLE_API_KEY
   * - Cohere
     - command, command-light
     - COHERE_API_KEY
   * - Azure OpenAI
     - Custom deployments
     - AZURE_OPENAI_API_KEY

Template Configuration
~~~~~~~~~~~~~~~~~~~~~~

Controls prompt templates and paper structure.

.. code-block:: json

   {
     "templates": {
       "prompts_file": "templates/default_prompts.json",
       "custom_templates": {
         "introduction": "Write an introduction for a {field} paper about {topic}..."
       },
       "section_order": [
         "abstract",
         "introduction", 
         "related_work",
         "methodology",
         "results",
         "discussion",
         "conclusion"
       ],
       "template_variables": {
         "field": "machine learning",
         "journal_style": "IEEE"
       }
     }
   }

**Parameters:**

- ``prompts_file`` (str): Path to JSON file containing prompt templates
- ``custom_templates`` (dict): Override specific section templates
- ``section_order`` (list): Order of sections in the paper
- ``template_variables`` (dict): Global variables available to all templates

Section Configuration
~~~~~~~~~~~~~~~~~~~~~

Configure individual paper sections.

.. code-block:: json

   {
     "sections": {
       "abstract": {
         "enabled": true,
         "max_words": 250,
         "min_words": 150,
         "model_override": "gpt-3.5-turbo",
         "temperature_override": 0.5,
         "validation_rules": ["word_count", "academic_style"]
       },
       "introduction": {
         "enabled": true,
         "max_words": 800,
         "min_words": 400,
         "subsections": ["motivation", "contributions", "organization"]
       },
       "methodology": {
         "enabled": true,
         "max_words": 1200,
         "require_figures": true,
         "require_algorithms": false
       }
     }
   }

**Common Section Parameters:**

- ``enabled`` (bool): Whether to generate this section
- ``max_words`` (int): Maximum word count
- ``min_words`` (int): Minimum word count
- ``model_override`` (str): Use different model for this section
- ``temperature_override`` (float): Use different temperature
- ``validation_rules`` (list): Validation rules to apply
- ``subsections`` (list): Required subsections
- ``require_figures`` (bool): Whether figures are required
- ``require_algorithms`` (bool): Whether algorithms are required

Output Configuration
~~~~~~~~~~~~~~~~~~~~

Controls output format and file generation.

.. code-block:: json

   {
     "output": {
       "directory": "./output",
       "format": "latex",
       "compile_pdf": true,
       "filename_template": "{title}_{timestamp}",
       "latex": {
         "document_class": "article",
         "packages": ["amsmath", "graphicx", "hyperref"],
         "bibliography_style": "plain",
         "compile_options": ["-interaction=nonstopmode"]
       },
       "pdf": {
         "engine": "pdflatex",
         "compile_twice": true,
         "cleanup_aux": true
       }
     }
   }

**Parameters:**

- ``directory`` (str): Output directory path
- ``format`` (str): Output format (``latex``, ``markdown``, ``html``)
- ``compile_pdf`` (bool): Whether to compile LaTeX to PDF
- ``filename_template`` (str): Template for output filenames
- ``latex`` (dict): LaTeX-specific configuration
- ``pdf`` (dict): PDF compilation configuration

Validation Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

Configure content validation and quality assessment.

.. code-block:: json

   {
     "validation": {
       "enabled": true,
       "strict_mode": false,
       "rules": {
         "word_count": {
           "enabled": true,
           "tolerance": 0.1
         },
         "academic_style": {
           "enabled": true,
           "check_citations": true,
           "check_formality": true
         },
         "structure": {
           "enabled": true,
           "require_sections": ["abstract", "introduction", "conclusion"]
         }
       },
       "quality_thresholds": {
         "minimum_score": 0.7,
         "section_scores": {
           "abstract": 0.8,
           "introduction": 0.75
         }
       }
     }
   }

**Parameters:**

- ``enabled`` (bool): Enable validation
- ``strict_mode`` (bool): Fail generation if validation fails
- ``rules`` (dict): Specific validation rules
- ``quality_thresholds`` (dict): Minimum quality scores

Context Configuration
~~~~~~~~~~~~~~~~~~~~~

Configure data collection and context preparation.

.. code-block:: json

   {
     "context": {
       "data_sources": [
         {
           "type": "csv",
           "path": "data/results.csv",
           "description": "Experimental results"
         },
         {
           "type": "json",
           "path": "data/metadata.json",
           "description": "Project metadata"
         }
       ],
       "preprocessing": {
         "normalize_text": true,
         "extract_statistics": true,
         "generate_summaries": true
       }
     }
   }

Plugin Configuration
~~~~~~~~~~~~~~~~~~~~

Configure the plugin system and custom extensions.

.. code-block:: json

   {
     "plugins": {
       "enabled": true,
       "discovery_paths": ["./plugins", "~/.arxiv-writer/plugins"],
       "auto_load": true,
       "plugins": {
         "custom_formatter": {
           "enabled": true,
           "config": {
             "format": "ieee",
             "strict_formatting": true
           }
         }
       }
     }
   }

Environment Variables
---------------------

Sensitive configuration can be stored in environment variables:

.. code-block:: bash

   # API Keys
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   export GOOGLE_API_KEY="your-google-key"
   
   # Configuration overrides
   export ARXIV_WRITER_OUTPUT_DIR="/custom/output/path"
   export ARXIV_WRITER_LLM_MODEL="gpt-4-turbo"
   export ARXIV_WRITER_DEBUG="true"

Variable Substitution
~~~~~~~~~~~~~~~~~~~~~

Configuration files support environment variable substitution:

.. code-block:: json

   {
     "llm": {
       "api_key": "${OPENAI_API_KEY}",
       "model": "${LLM_MODEL:-gpt-4}"
     },
     "output": {
       "directory": "${OUTPUT_DIR:-./output}"
     }
   }

Syntax:
- ``${VAR}`` - Required variable (fails if not set)
- ``${VAR:-default}`` - Optional variable with default value

Configuration Validation
-------------------------

Validate your configuration before use:

.. code-block:: python

   from arxiv_writer import PaperConfig
   
   # Load and validate configuration
   try:
       config = PaperConfig.from_file("config.json")
       print("Configuration is valid!")
   except ValidationError as e:
       print(f"Configuration error: {e}")

Command-line validation:

.. code-block:: bash

   arxiv-writer validate --config config.json

Configuration Profiles
-----------------------

Create different profiles for different use cases:

**research_paper.json:**

.. code-block:: json

   {
     "llm": {"model": "gpt-4", "temperature": 0.7},
     "sections": {
       "related_work": {"enabled": true, "max_words": 800},
       "methodology": {"enabled": true, "max_words": 1200}
     }
   }

**survey_paper.json:**

.. code-block:: json

   {
     "llm": {"model": "gpt-4", "temperature": 0.5},
     "sections": {
       "related_work": {"enabled": true, "max_words": 2000},
       "methodology": {"enabled": false}
     }
   }

**conference_paper.json:**

.. code-block:: json

   {
     "sections": {
       "abstract": {"max_words": 150},
       "introduction": {"max_words": 600}
     },
     "output": {
       "latex": {"document_class": "IEEEtran"}
     }
   }

Best Practices
--------------

1. **Use environment variables** for sensitive data like API keys
2. **Create profiles** for different paper types
3. **Validate configuration** before long generation runs
4. **Use version control** for configuration files
5. **Document custom templates** and their required variables
6. **Test configurations** with small examples first
7. **Monitor token usage** to manage costs
8. **Use appropriate models** for different sections (e.g., cheaper models for formatting)

Example Configurations
----------------------

See the :doc:`examples/advanced_configuration` section for complete configuration examples for different use cases.