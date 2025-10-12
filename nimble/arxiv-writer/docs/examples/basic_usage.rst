Basic Usage Examples
====================

This guide provides practical examples for common ArXiv Writer use cases, from simple paper generation to more advanced scenarios.

Getting Started
---------------

First Example: Research Paper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's generate a simple research paper about machine learning:

**Step 1: Create configuration file** (``config.json``):

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
     },
     "sections": {
       "abstract": {"enabled": true, "max_words": 250},
       "introduction": {"enabled": true, "max_words": 800},
       "methodology": {"enabled": true, "max_words": 1000},
       "results": {"enabled": true, "max_words": 800},
       "discussion": {"enabled": true, "max_words": 600},
       "conclusion": {"enabled": true, "max_words": 400}
     }
   }

**Step 2: Create context data file** (``context.json``):

.. code-block:: json

   {
     "title": "Improving Neural Network Performance with Adaptive Learning Rates",
     "authors": ["Dr. Jane Smith", "Prof. John Doe"],
     "abstract": "This paper presents a novel adaptive learning rate algorithm that improves neural network training efficiency by 25%.",
     "keywords": ["machine learning", "neural networks", "optimization", "adaptive learning"],
     "research_question": "How can we automatically adjust learning rates during training to improve convergence speed and final accuracy?",
     "methodology": "We developed an adaptive learning rate algorithm that monitors gradient magnitudes and adjusts rates accordingly. We tested on CIFAR-10, ImageNet, and custom datasets.",
     "key_findings": "Our algorithm achieved 25% faster convergence and 3% higher accuracy compared to standard SGD with momentum. The method is particularly effective for deep networks with >50 layers.",
     "data_description": "Experiments conducted on CIFAR-10 (60,000 images), ImageNet (1.2M images), and three custom datasets with varying complexity.",
     "results_summary": "Adaptive learning rates reduced training time from 48 hours to 36 hours on ImageNet while achieving 78.2% top-1 accuracy vs 75.1% with fixed rates.",
     "related_work": "Previous work includes Adam optimizer (Kingma & Ba, 2014), AdaGrad (Duchi et al., 2011), and RMSprop (Hinton, 2012). Our approach differs by using gradient magnitude history.",
     "limitations": "The method requires additional memory to store gradient history and may not be suitable for very large models or limited memory environments.",
     "contributions": [
       "Novel adaptive learning rate algorithm based on gradient magnitude analysis",
       "Comprehensive evaluation on multiple datasets and architectures",
       "Open-source implementation with detailed documentation"
     ]
   }

**Step 3: Generate the paper**:

.. code-block:: bash

   # Set your API key
   export OPENAI_API_KEY="your-openai-api-key"
   
   # Generate the paper
   arxiv-writer generate --config config.json --context context.json

**Step 4: Review the output**:

.. code-block:: text

   output/
   ├── paper.tex              # Complete LaTeX document
   ├── paper.pdf              # Compiled PDF
   ├── sections/               # Individual sections
   │   ├── abstract.tex
   │   ├── introduction.tex
   │   ├── methodology.tex
   │   ├── results.tex
   │   ├── discussion.tex
   │   └── conclusion.tex
   ├── bibliography.bib       # Bibliography file
   ├── generation_report.json # Generation metadata
   └── quality_report.json    # Quality assessment

Python API Example
~~~~~~~~~~~~~~~~~~~

The same paper can be generated using the Python API:

.. code-block:: python

   from arxiv_writer import ArxivPaperGenerator, PaperConfig
   import json
   import os

   # Set API key
   os.environ['OPENAI_API_KEY'] = 'your-openai-api-key'

   # Load configuration
   with open('config.json', 'r') as f:
       config_dict = json.load(f)
   config = PaperConfig.from_dict(config_dict)

   # Load context data
   with open('context.json', 'r') as f:
       context_data = json.load(f)

   # Initialize generator
   generator = ArxivPaperGenerator(config)

   # Generate paper
   try:
       result = generator.generate_paper(context_data)
       
       print(f"✅ Paper generated successfully!")
       print(f"📄 LaTeX file: {result.latex_path}")
       print(f"📑 PDF file: {result.pdf_path}")
       print(f"⭐ Quality score: {result.quality_score:.2f}")
       print(f"⏱️  Generation time: {result.generation_time}")
       
       # Print section summaries
       for section_name, section in result.sections.items():
           print(f"📝 {section_name}: {section.word_count} words")
           
   except Exception as e:
       print(f"❌ Generation failed: {e}")

Common Use Cases
----------------

Survey Paper
~~~~~~~~~~~~

Generate a literature survey paper:

**Context data** (``survey_context.json``):

.. code-block:: json

   {
     "title": "A Comprehensive Survey of Transformer Architectures in Natural Language Processing",
     "authors": ["Dr. Alice Johnson", "Prof. Bob Wilson"],
     "survey_scope": "Transformer architectures and their applications in NLP from 2017-2024",
     "time_period": "2017-2024",
     "search_methodology": "Systematic literature review using Google Scholar, ACL Anthology, and arXiv. Keywords: transformer, attention, BERT, GPT, NLP.",
     "inclusion_criteria": "Peer-reviewed papers and high-impact preprints with novel transformer architectures or significant applications",
     "exclusion_criteria": "Papers without empirical evaluation, non-English papers, workshop papers without substantial contributions",
     "paper_categories": [
       "Encoder-only models (BERT family)",
       "Decoder-only models (GPT family)", 
       "Encoder-decoder models (T5, BART)",
       "Efficient transformers (Linformer, Performer)",
       "Multimodal transformers (CLIP, DALL-E)"
     ],
     "key_findings": "Transformers have revolutionized NLP with 95% of SOTA models using attention mechanisms. Scaling laws show consistent improvement with model size.",
     "research_gaps": "Limited work on interpretability, energy efficiency, and few-shot learning in specialized domains",
     "future_directions": "Efficient architectures, multimodal integration, and better theoretical understanding of attention mechanisms"
   }

**Configuration** (``survey_config.json``):

.. code-block:: json

   {
     "llm": {
       "provider": "openai",
       "model": "gpt-4",
       "temperature": 0.5
     },
     "sections": {
       "abstract": {"enabled": true, "max_words": 300},
       "introduction": {"enabled": true, "max_words": 1000},
       "related_work": {"enabled": true, "max_words": 2500},
       "methodology": {"enabled": false},
       "survey_analysis": {"enabled": true, "max_words": 2000},
       "discussion": {"enabled": true, "max_words": 1000},
       "conclusion": {"enabled": true, "max_words": 500}
     },
     "templates": {
       "custom_templates": {
         "survey_analysis": "Analyze the surveyed papers by categorizing them into {paper_categories}. For each category, discuss key innovations, performance metrics, and limitations. Include quantitative analysis where possible."
       }
     }
   }

**Generate the survey**:

.. code-block:: bash

   arxiv-writer generate --config survey_config.json --context survey_context.json

Conference Paper (Short Format)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generate a conference paper with strict length limits:

**Configuration** (``conference_config.json``):

.. code-block:: json

   {
     "llm": {
       "provider": "openai",
       "model": "gpt-4",
       "temperature": 0.6
     },
     "sections": {
       "abstract": {"enabled": true, "max_words": 150},
       "introduction": {"enabled": true, "max_words": 400},
       "methodology": {"enabled": true, "max_words": 600},
       "results": {"enabled": true, "max_words": 500},
       "conclusion": {"enabled": true, "max_words": 200}
     },
     "output": {
       "latex": {
         "document_class": "IEEEtran",
         "packages": ["cite", "amsmath", "algorithmic", "array"]
       }
     },
     "validation": {
       "strict_mode": true,
       "rules": {
         "word_count": {"enabled": true, "tolerance": 0.05}
       }
     }
   }

Technical Report
~~~~~~~~~~~~~~~~

Generate a detailed technical report:

**Context data** (``technical_context.json``):

.. code-block:: json

   {
     "title": "Implementation and Performance Analysis of Distributed Machine Learning System",
     "authors": ["Engineering Team"],
     "project_overview": "Development of a distributed ML training system capable of handling 100TB+ datasets across 1000+ nodes",
     "system_architecture": "Microservices architecture with Kubernetes orchestration, Redis for caching, PostgreSQL for metadata, and custom C++ training engines",
     "implementation_details": "Built using Python 3.11, FastAPI, Docker containers, with custom CUDA kernels for GPU acceleration",
     "performance_metrics": "Achieved 95% scaling efficiency up to 512 nodes, 40% faster training than baseline systems, 99.9% uptime over 6 months",
     "technical_challenges": "Network bottlenecks, fault tolerance, dynamic load balancing, memory management for large models",
     "solutions_implemented": "Gradient compression, asynchronous parameter updates, automatic failover, memory-mapped file systems",
     "deployment_details": "Deployed on AWS EKS with auto-scaling groups, monitoring via Prometheus/Grafana, CI/CD with GitHub Actions",
     "lessons_learned": "Importance of network optimization, need for comprehensive monitoring, value of gradual rollout strategies"
   }

**Configuration** (``technical_config.json``):

.. code-block:: json

   {
     "sections": {
       "abstract": {"enabled": true, "max_words": 200},
       "introduction": {"enabled": true, "max_words": 600},
       "system_design": {"enabled": true, "max_words": 1200},
       "implementation": {"enabled": true, "max_words": 1500},
       "performance_evaluation": {"enabled": true, "max_words": 1000},
       "deployment": {"enabled": true, "max_words": 800},
       "lessons_learned": {"enabled": true, "max_words": 600},
       "conclusion": {"enabled": true, "max_words": 300}
     }
   }

Working with Different LLM Providers
-------------------------------------

OpenAI GPT Models
~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "llm": {
       "provider": "openai",
       "model": "gpt-4-turbo",
       "temperature": 0.7,
       "max_tokens": 4000,
       "api_key": "${OPENAI_API_KEY}"
     }
   }

Anthropic Claude
~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "llm": {
       "provider": "anthropic",
       "model": "claude-3-opus-20240229",
       "temperature": 0.7,
       "max_tokens": 4000,
       "api_key": "${ANTHROPIC_API_KEY}"
     }
   }

Google Gemini
~~~~~~~~~~~~~

.. code-block:: json

   {
     "llm": {
       "provider": "google",
       "model": "gemini-pro",
       "temperature": 0.7,
       "api_key": "${GOOGLE_API_KEY}"
     }
   }

Local Models with Ollama
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "llm": {
       "provider": "ollama",
       "model": "llama2:13b",
       "api_base": "http://localhost:11434",
       "temperature": 0.7
     }
   }

**Setup Ollama:**

.. code-block:: bash

   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull a model
   ollama pull llama2:13b
   
   # Start Ollama server
   ollama serve

Section-by-Section Generation
------------------------------

Sometimes you want to generate sections individually for better control:

**Generate Abstract Only:**

.. code-block:: bash

   arxiv-writer section abstract \
     --config config.json \
     --context context.json \
     --output sections/abstract.tex

**Generate with Custom Parameters:**

.. code-block:: bash

   arxiv-writer section methodology \
     --config config.json \
     --context context.json \
     --model gpt-4-turbo \
     --temperature 0.3 \
     --max-words 1500

**Python API for Section Generation:**

.. code-block:: python

   from arxiv_writer import ArxivPaperGenerator

   generator = ArxivPaperGenerator(config)

   # Generate specific sections
   sections_to_generate = ['abstract', 'introduction', 'conclusion']
   
   for section_name in sections_to_generate:
       section_result = generator.generate_section(
           section_name=section_name,
           context_data=context_data
       )
       
       print(f"Generated {section_name}: {section_result.word_count} words")
       
       # Save section
       with open(f"sections/{section_name}.tex", "w") as f:
           f.write(section_result.content)

Quality Assessment and Validation
----------------------------------

**Assess Paper Quality:**

.. code-block:: bash

   # Generate quality report
   arxiv-writer quality output/paper.tex --format html --output quality_report.html

**Python API for Quality Assessment:**

.. code-block:: python

   from arxiv_writer.core.quality_assessor import PaperQualityAssessor

   assessor = PaperQualityAssessor(config.quality_config)
   
   # Read generated paper
   with open('output/paper.tex', 'r') as f:
       paper_content = f.read()
   
   # Assess quality
   assessment = assessor.assess_paper(paper_content)
   
   print(f"Overall Quality Score: {assessment.overall_score:.2f}")
   print(f"Section Scores:")
   for section, score in assessment.section_scores.items():
       print(f"  {section}: {score:.2f}")
   
   print(f"Strengths: {assessment.strengths}")
   print(f"Suggestions: {assessment.suggestions}")

**Validate Configuration:**

.. code-block:: bash

   # Validate before generation
   arxiv-writer validate --config config.json

**Validate Generated Content:**

.. code-block:: bash

   # Strict validation
   arxiv-writer validate --paper output/paper.tex --strict

Batch Processing
----------------

**Process Multiple Papers:**

.. code-block:: bash

   #!/bin/bash
   
   # Process all context files in data directory
   for context_file in data/*.json; do
       paper_name=$(basename "$context_file" .json)
       output_dir="output/$paper_name"
       
       echo "Generating paper: $paper_name"
       
       arxiv-writer generate \
         --config config.json \
         --context "$context_file" \
         --output "$output_dir"
       
       if [ $? -eq 0 ]; then
           echo "✅ Successfully generated $paper_name"
       else
           echo "❌ Failed to generate $paper_name"
       fi
   done

**Python Batch Processing:**

.. code-block:: python

   import os
   import json
   from pathlib import Path
   from arxiv_writer import ArxivPaperGenerator, PaperConfig

   # Load configuration
   config = PaperConfig.from_file("config.json")
   generator = ArxivPaperGenerator(config)

   # Process all context files
   context_dir = Path("data")
   output_dir = Path("output")

   for context_file in context_dir.glob("*.json"):
       print(f"Processing {context_file.name}...")
       
       try:
           # Load context data
           with open(context_file, 'r') as f:
               context_data = json.load(f)
           
           # Set output directory
           paper_output_dir = output_dir / context_file.stem
           config.output_config.directory = str(paper_output_dir)
           
           # Generate paper
           result = generator.generate_paper(context_data)
           
           print(f"✅ Generated {context_file.stem}")
           print(f"   Quality: {result.quality_score:.2f}")
           print(f"   Time: {result.generation_time}")
           
       except Exception as e:
           print(f"❌ Failed to generate {context_file.stem}: {e}")

Error Handling and Debugging
-----------------------------

**Robust Error Handling:**

.. code-block:: python

   from arxiv_writer import ArxivPaperGenerator, PaperConfig
   from arxiv_writer.core.exceptions import (
       ConfigurationError, 
       LLMError, 
       ValidationError,
       GenerationError
   )

   try:
       config = PaperConfig.from_file("config.json")
       generator = ArxivPaperGenerator(config)
       result = generator.generate_paper(context_data)
       
   except ConfigurationError as e:
       print(f"Configuration error: {e}")
       print(f"Suggestions: {e.suggestions}")
       
   except LLMError as e:
       print(f"LLM error: {e}")
       if "rate limit" in str(e).lower():
           print("Try reducing request frequency or upgrading API plan")
           
   except ValidationError as e:
       print(f"Validation error: {e}")
       print("Consider adjusting validation settings or improving context data")
       
   except GenerationError as e:
       print(f"Generation error: {e}")
       print("Check context data completeness and template configuration")
       
   except Exception as e:
       print(f"Unexpected error: {e}")
       print("Enable debug mode for more details")

**Debug Mode:**

.. code-block:: bash

   # Enable debug output
   arxiv-writer generate --config config.json --context context.json --debug

**Dry Run for Testing:**

.. code-block:: bash

   # Test configuration without generating
   arxiv-writer generate --config config.json --context context.json --dry-run

Next Steps
----------

Now that you've mastered basic usage, explore:

1. :doc:`advanced_configuration` - Complex configuration scenarios
2. :doc:`custom_templates` - Creating custom prompt templates  
3. :doc:`plugin_development` - Extending functionality with plugins
4. :doc:`llm_providers` - Working with different LLM providers
5. :doc:`codexes_migration` - Migrating from Codexes Factory

For troubleshooting, see the :doc:`../troubleshooting` guide.