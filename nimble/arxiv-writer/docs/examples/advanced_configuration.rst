Advanced Configuration Examples
===============================

This guide demonstrates advanced configuration patterns for complex paper generation scenarios.

Multi-Model Configuration
--------------------------

Using Different Models for Different Sections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use powerful models for complex sections and efficient models for simpler ones:

.. code-block:: json

   {
     "llm": {
       "provider": "openai",
       "model": "gpt-3.5-turbo",
       "temperature": 0.7,
       "api_key": "${OPENAI_API_KEY}"
     },
     "sections": {
       "abstract": {
         "enabled": true,
         "max_words": 250,
         "model_override": "gpt-3.5-turbo",
         "temperature_override": 0.5
       },
       "introduction": {
         "enabled": true,
         "max_words": 800,
         "model_override": "gpt-4",
         "temperature_override": 0.7
       },
       "methodology": {
         "enabled": true,
         "max_words": 1200,
         "model_override": "gpt-4",
         "temperature_override": 0.3
       },
       "results": {
         "enabled": true,
         "max_words": 1000,
         "model_override": "gpt-4",
         "temperature_override": 0.4
       },
       "discussion": {
         "enabled": true,
         "max_words": 800,
         "model_override": "gpt-4",
         "temperature_override": 0.6
       },
       "conclusion": {
         "enabled": true,
         "max_words": 400,
         "model_override": "gpt-3.5-turbo",
         "temperature_override": 0.5
       }
     }
   }

**Cost Analysis:**

.. code-block:: python

   # Estimate costs for multi-model configuration
   from arxiv_writer.utils import estimate_generation_cost

   config = PaperConfig.from_file("multi_model_config.json")
   context_data = load_context("context.json")

   cost_estimate = estimate_generation_cost(config, context_data)
   print(f"Estimated cost: ${cost_estimate:.2f}")
   print(f"GPT-4 usage: {cost_estimate.gpt4_tokens} tokens")
   print(f"GPT-3.5 usage: {cost_estimate.gpt35_tokens} tokens")

Provider Fallback Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure multiple providers with automatic fallback:

.. code-block:: json

   {
     "llm": {
       "providers": [
         {
           "name": "primary",
           "provider": "openai",
           "model": "gpt-4",
           "api_key": "${OPENAI_API_KEY}",
           "priority": 1
         },
         {
           "name": "fallback",
           "provider": "anthropic", 
           "model": "claude-3-sonnet-20240229",
           "api_key": "${ANTHROPIC_API_KEY}",
           "priority": 2
         },
         {
           "name": "local",
           "provider": "ollama",
           "model": "llama2:13b",
           "api_base": "http://localhost:11434",
           "priority": 3
         }
       ],
       "fallback_strategy": "automatic",
       "retry_with_fallback": true
     }
   }

**Python Implementation:**

.. code-block:: python

   from arxiv_writer import ArxivPaperGenerator, PaperConfig
   from arxiv_writer.core.exceptions import LLMError

   config = PaperConfig.from_file("fallback_config.json")
   generator = ArxivPaperGenerator(config)

   try:
       result = generator.generate_paper(context_data)
       print(f"Generated using: {result.primary_provider}")
       print(f"Fallback used: {result.fallback_usage}")
   except LLMError as e:
       print(f"All providers failed: {e}")

Advanced Template Configuration
-------------------------------

Custom Template Inheritance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a hierarchy of templates with inheritance:

**base_templates.json:**

.. code-block:: json

   {
     "base_academic": {
       "system_prompt": "You are an expert academic writer specializing in {field}. Write in a formal, scholarly tone with proper citations and technical accuracy.",
       "context_variables": ["field", "journal_style", "target_audience"],
       "validation_criteria": {
         "academic_style": true,
         "citation_format": "apa",
         "formality_level": "high"
       }
     },
     "base_technical": {
       "extends": "base_academic",
       "system_prompt": "You are an expert technical writer. Focus on implementation details, performance metrics, and practical applications.",
       "context_variables": ["technology_stack", "performance_metrics", "implementation_details"]
     }
   }

**research_templates.json:**

.. code-block:: json

   {
     "introduction": {
       "extends": "base_academic",
       "user_prompt": "Write an introduction for a {field} research paper titled '{title}'. The paper addresses {research_question} and makes the following contributions: {contributions}. Structure: motivation, problem statement, contributions, organization.",
       "max_words": 800,
       "required_elements": ["motivation", "problem_statement", "contributions", "paper_organization"]
     },
     "methodology": {
       "extends": "base_technical", 
       "user_prompt": "Describe the methodology for {research_question}. Include: {methodology_details}. Ensure reproducibility by providing sufficient implementation details.",
       "max_words": 1200,
       "required_elements": ["approach_overview", "implementation_details", "evaluation_metrics"]
     }
   }

**Configuration:**

.. code-block:: json

   {
     "templates": {
       "template_files": [
         "templates/base_templates.json",
         "templates/research_templates.json"
       ],
       "template_variables": {
         "field": "machine learning",
         "journal_style": "IEEE",
         "target_audience": "researchers",
         "technology_stack": "Python, PyTorch, CUDA"
       }
     }
   }

Dynamic Template Selection
~~~~~~~~~~~~~~~~~~~~~~~~~~

Select templates based on paper type and context:

.. code-block:: json

   {
     "templates": {
       "dynamic_selection": true,
       "selection_rules": [
         {
           "condition": "paper_type == 'survey'",
           "templates": "templates/survey_templates.json"
         },
         {
           "condition": "paper_type == 'experimental'",
           "templates": "templates/experimental_templates.json"
         },
         {
           "condition": "field == 'computer_vision'",
           "templates": "templates/cv_templates.json"
         }
       ],
       "default_templates": "templates/default_templates.json"
     }
   }

**Python Implementation:**

.. code-block:: python

   def select_templates(context_data):
       """Dynamically select templates based on context."""
       paper_type = context_data.get('paper_type', 'research')
       field = context_data.get('field', 'general')
       
       if paper_type == 'survey':
           return 'templates/survey_templates.json'
       elif field == 'computer_vision':
           return 'templates/cv_templates.json'
       else:
           return 'templates/default_templates.json'

   # Use in configuration
   template_file = select_templates(context_data)
   config.templates.prompts_file = template_file

Complex Validation Configuration
--------------------------------

Multi-Level Validation Rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure validation at multiple levels with custom rules:

.. code-block:: json

   {
     "validation": {
       "enabled": true,
       "strict_mode": false,
       "levels": {
         "section": {
           "rules": {
             "word_count": {
               "enabled": true,
               "tolerance": 0.1,
               "per_section": {
                 "abstract": {"min": 150, "max": 250},
                 "introduction": {"min": 600, "max": 1000},
                 "methodology": {"min": 800, "max": 1500}
               }
             },
             "academic_style": {
               "enabled": true,
               "check_citations": true,
               "check_formality": true,
               "check_tense": "past_for_results",
               "prohibited_words": ["I think", "maybe", "probably"]
             },
             "technical_accuracy": {
               "enabled": true,
               "check_equations": true,
               "check_units": true,
               "check_references": true
             }
           }
         },
         "paper": {
           "rules": {
             "structure": {
               "enabled": true,
               "required_sections": ["abstract", "introduction", "conclusion"],
               "section_order": ["abstract", "introduction", "related_work", "methodology", "results", "discussion", "conclusion"],
               "max_sections": 10
             },
             "coherence": {
               "enabled": true,
               "check_transitions": true,
               "check_consistency": true,
               "check_flow": true
             },
             "completeness": {
               "enabled": true,
               "require_bibliography": true,
               "min_references": 10,
               "require_figures": false
             }
           }
         }
       },
       "quality_thresholds": {
         "minimum_score": 0.7,
         "section_scores": {
           "abstract": 0.8,
           "introduction": 0.75,
           "methodology": 0.8,
           "results": 0.75,
           "discussion": 0.7,
           "conclusion": 0.75
         },
         "criteria_scores": {
           "academic_style": 0.8,
           "technical_accuracy": 0.85,
           "coherence": 0.7,
           "completeness": 0.75
         }
       },
       "custom_validators": [
         {
           "name": "domain_specific",
           "module": "validators.ml_validator",
           "class": "MachineLearningValidator",
           "config": {
             "check_ml_terminology": true,
             "require_evaluation_metrics": true,
             "check_dataset_description": true
           }
         }
       ]
     }
   }

Custom Validation Rules
~~~~~~~~~~~~~~~~~~~~~~~

Implement domain-specific validation:

.. code-block:: python

   # validators/ml_validator.py
   from arxiv_writer.core.validator import BaseValidator
   from arxiv_writer.core.models import ValidationResult

   class MachineLearningValidator(BaseValidator):
       def __init__(self, config):
           super().__init__(config)
           self.ml_terms = ['accuracy', 'precision', 'recall', 'F1-score']
           self.required_metrics = config.get('require_evaluation_metrics', True)
       
       def validate_section(self, content, section_name):
           errors = []
           warnings = []
           
           if section_name == 'results' and self.required_metrics:
               if not any(term in content.lower() for term in self.ml_terms):
                   errors.append("Results section missing evaluation metrics")
           
           if section_name == 'methodology':
               if 'dataset' not in content.lower():
                   warnings.append("Methodology should describe the dataset")
           
           score = 1.0 - (len(errors) * 0.2) - (len(warnings) * 0.1)
           
           return ValidationResult(
               is_valid=len(errors) == 0,
               score=max(0.0, score),
               errors=errors,
               warnings=warnings
           )

Advanced Output Configuration
-----------------------------

Multi-Format Output
~~~~~~~~~~~~~~~~~~~

Generate multiple output formats simultaneously:

.. code-block:: json

   {
     "output": {
       "formats": [
         {
           "name": "latex",
           "enabled": true,
           "directory": "./output/latex",
           "compile_pdf": true,
           "latex": {
             "document_class": "article",
             "packages": ["amsmath", "graphicx", "hyperref", "natbib"],
             "bibliography_style": "plain",
             "geometry": "margin=1in"
           }
         },
         {
           "name": "markdown",
           "enabled": true,
           "directory": "./output/markdown",
           "markdown": {
             "include_metadata": true,
             "math_renderer": "katex",
             "citation_style": "pandoc"
           }
         },
         {
           "name": "html",
           "enabled": true,
           "directory": "./output/html",
           "html": {
             "template": "templates/academic.html",
             "include_css": true,
             "math_renderer": "mathjax"
           }
         }
       ]
     }
   }

Journal-Specific Formatting
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure for specific journal requirements:

.. code-block:: json

   {
     "output": {
       "journal_configs": {
         "ieee": {
           "latex": {
             "document_class": "IEEEtran",
             "packages": ["cite", "amsmath", "algorithmic"],
             "bibliography_style": "IEEEtran",
             "column_mode": "twocolumn"
           },
           "sections": {
             "abstract": {"max_words": 150},
             "introduction": {"max_words": 600}
           }
         },
         "acm": {
           "latex": {
             "document_class": "acmart",
             "packages": ["booktabs", "ccicons"],
             "acm_format": "sigconf",
             "bibliography_style": "ACM-Reference-Format"
           }
         },
         "springer": {
           "latex": {
             "document_class": "svjour3",
             "packages": ["mathptmx", "helvet", "courier"],
             "bibliography_style": "spbasic"
           }
         }
       },
       "active_journal": "ieee"
     }
   }

**Usage:**

.. code-block:: python

   # Switch journal format
   config.output.active_journal = "acm"
   generator = ArxivPaperGenerator(config)
   result = generator.generate_paper(context_data)

Advanced Context Processing
---------------------------

Multi-Source Context Collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Collect context from multiple data sources:

.. code-block:: json

   {
     "context": {
       "sources": [
         {
           "name": "experimental_results",
           "type": "csv",
           "path": "data/results.csv",
           "description": "Experimental results with metrics",
           "preprocessing": {
             "normalize_columns": true,
             "generate_statistics": true,
             "create_visualizations": false
           }
         },
         {
           "name": "literature_review",
           "type": "json",
           "path": "data/literature.json",
           "description": "Related work and citations",
           "preprocessing": {
             "extract_key_papers": true,
             "categorize_papers": true,
             "generate_timeline": true
           }
         },
         {
           "name": "code_analysis",
           "type": "directory",
           "path": "src/",
           "description": "Source code for analysis",
           "preprocessing": {
             "extract_functions": true,
             "generate_complexity_metrics": true,
             "create_dependency_graph": false
           }
         },
         {
           "name": "documentation",
           "type": "markdown",
           "path": "docs/",
           "description": "Project documentation",
           "preprocessing": {
             "extract_sections": true,
             "generate_summary": true
           }
         }
       ],
       "processing": {
         "merge_strategy": "hierarchical",
         "conflict_resolution": "prioritize_by_source_order",
         "max_context_size": 50000,
         "summarization": {
           "enabled": true,
           "strategy": "extractive",
           "max_summary_ratio": 0.3
         }
       }
     }
   }

**Python Implementation:**

.. code-block:: python

   from arxiv_writer.core.context_collector import ContextCollector
   import pandas as pd

   collector = ContextCollector(config.context)

   # Collect from all sources
   context = collector.collect_context()

   # Access specific source data
   results_data = context['experimental_results']
   literature_data = context['literature_review']

   # Generate summaries
   context_summary = collector.generate_summary(context)

   print(f"Total context size: {len(str(context))} characters")
   print(f"Summary size: {len(context_summary)} characters")

Dynamic Context Adaptation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Adapt context based on section requirements:

.. code-block:: json

   {
     "context": {
       "adaptive_processing": true,
       "section_contexts": {
         "introduction": {
           "focus_areas": ["motivation", "problem_statement", "contributions"],
           "data_sources": ["literature_review", "problem_definition"],
           "max_context_size": 8000
         },
         "methodology": {
           "focus_areas": ["implementation", "algorithms", "evaluation"],
           "data_sources": ["code_analysis", "experimental_setup"],
           "max_context_size": 12000
         },
         "results": {
           "focus_areas": ["metrics", "comparisons", "analysis"],
           "data_sources": ["experimental_results", "statistical_analysis"],
           "max_context_size": 10000
         }
       }
     }
   }

**Python Implementation:**

.. code-block:: python

   def adapt_context_for_section(base_context, section_name, config):
       """Adapt context for specific section requirements."""
       section_config = config.context.section_contexts.get(section_name, {})
       
       # Filter relevant data sources
       focus_areas = section_config.get('focus_areas', [])
       data_sources = section_config.get('data_sources', [])
       max_size = section_config.get('max_context_size', 10000)
       
       adapted_context = {}
       
       # Include only relevant sources
       for source in data_sources:
           if source in base_context:
               adapted_context[source] = base_context[source]
       
       # Filter by focus areas
       if focus_areas:
           adapted_context = filter_by_focus_areas(adapted_context, focus_areas)
       
       # Truncate if necessary
       if len(str(adapted_context)) > max_size:
           adapted_context = truncate_context(adapted_context, max_size)
       
       return adapted_context

   # Use adapted context for section generation
   for section_name in ['introduction', 'methodology', 'results']:
       section_context = adapt_context_for_section(base_context, section_name, config)
       section_result = generator.generate_section(section_name, section_context)

Performance Optimization
------------------------

Parallel Generation Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure parallel section generation:

.. code-block:: json

   {
     "performance": {
       "parallel_generation": {
         "enabled": true,
         "max_workers": 4,
         "section_groups": [
           ["abstract", "conclusion"],
           ["introduction", "related_work"],
           ["methodology", "results"],
           ["discussion"]
         ]
       },
       "caching": {
         "enabled": true,
         "cache_directory": ".arxiv_writer_cache",
         "cache_llm_responses": true,
         "cache_context_processing": true,
         "ttl_hours": 24
       },
       "optimization": {
         "batch_requests": true,
         "request_batching_size": 3,
         "context_compression": true,
         "template_precompilation": true
       }
     }
   }

**Python Implementation:**

.. code-block:: python

   import asyncio
   from concurrent.futures import ThreadPoolExecutor
   from arxiv_writer import ArxivPaperGenerator

   async def generate_sections_parallel(generator, context_data, sections):
       """Generate sections in parallel."""
       loop = asyncio.get_event_loop()
       
       with ThreadPoolExecutor(max_workers=4) as executor:
           tasks = []
           
           for section_name in sections:
               task = loop.run_in_executor(
                   executor,
                   generator.generate_section,
                   section_name,
                   context_data
               )
               tasks.append((section_name, task))
           
           results = {}
           for section_name, task in tasks:
               results[section_name] = await task
           
           return results

   # Usage
   sections = ['abstract', 'introduction', 'methodology', 'results']
   results = await generate_sections_parallel(generator, context_data, sections)

Memory Management
~~~~~~~~~~~~~~~~~

Configure memory usage for large papers:

.. code-block:: json

   {
     "memory": {
       "max_memory_usage": "4GB",
       "context_chunking": {
         "enabled": true,
         "chunk_size": 10000,
         "overlap_size": 1000,
         "strategy": "semantic"
       },
       "garbage_collection": {
         "enabled": true,
         "frequency": "after_each_section",
         "force_gc": true
       },
       "streaming": {
         "enabled": true,
         "stream_large_sections": true,
         "threshold_words": 2000
       }
     }
   }

Environment-Specific Configurations
-----------------------------------

Development vs Production
~~~~~~~~~~~~~~~~~~~~~~~~~

**development.json:**

.. code-block:: json

   {
     "llm": {
       "provider": "openai",
       "model": "gpt-3.5-turbo",
       "temperature": 0.8
     },
     "validation": {
       "strict_mode": false,
       "quality_thresholds": {"minimum_score": 0.5}
     },
     "output": {
       "compile_pdf": false
     },
     "logging": {
       "level": "DEBUG",
       "log_file": "debug.log"
     }
   }

**production.json:**

.. code-block:: json

   {
     "llm": {
       "provider": "openai",
       "model": "gpt-4",
       "temperature": 0.7
     },
     "validation": {
       "strict_mode": true,
       "quality_thresholds": {"minimum_score": 0.8}
     },
     "output": {
       "compile_pdf": true
     },
     "logging": {
       "level": "INFO",
       "log_file": "production.log"
     }
   }

**Usage:**

.. code-block:: bash

   # Development
   arxiv-writer generate --config configs/development.json --context data.json

   # Production
   arxiv-writer generate --config configs/production.json --context data.json

CI/CD Integration
~~~~~~~~~~~~~~~~~

**GitHub Actions Configuration:**

.. code-block:: yaml

   name: Generate Papers
   on:
     push:
       paths: ['data/**', 'configs/**']
   
   jobs:
     generate:
       runs-on: ubuntu-latest
       strategy:
         matrix:
           paper: [paper1, paper2, paper3]
       
       steps:
         - uses: actions/checkout@v3
         
         - name: Setup Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         
         - name: Install LaTeX
           run: |
             sudo apt-get update
             sudo apt-get install -y texlive-full
         
         - name: Install ArXiv Writer
           run: pip install arxiv-writer
         
         - name: Generate Paper
           run: |
             arxiv-writer generate \
               --config configs/${{ matrix.paper }}.json \
               --context data/${{ matrix.paper }}.json \
               --output output/${{ matrix.paper }}
           env:
             OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
         
         - name: Upload Results
           uses: actions/upload-artifact@v3
           with:
             name: ${{ matrix.paper }}-output
             path: output/${{ matrix.paper }}/

Next Steps
----------

Explore more advanced topics:

1. :doc:`custom_templates` - Create sophisticated prompt templates
2. :doc:`plugin_development` - Build custom functionality
3. :doc:`llm_providers` - Advanced LLM provider configuration
4. :doc:`codexes_migration` - Migrate from Codexes Factory

For troubleshooting complex configurations, see :doc:`../troubleshooting`.