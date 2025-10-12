Quick Start Guide
================

This guide will help you generate your first academic paper using ArXiv Writer in just a few minutes.

Prerequisites
-------------

Before starting, ensure you have:

1. Installed ArXiv Writer (see :doc:`installation`)
2. A LaTeX distribution installed
3. An API key for your preferred LLM provider
4. Basic familiarity with Python or command-line tools

Your First Paper
-----------------

Method 1: Python API
~~~~~~~~~~~~~~~~~~~~~

Create a simple Python script to generate a paper:

.. code-block:: python

   from arxiv_writer import ArxivPaperGenerator, PaperConfig
   import os
   
   # Set up your API key
   os.environ['OPENAI_API_KEY'] = 'your-api-key-here'
   
   # Create configuration
   config = PaperConfig(
       llm_config={
           'provider': 'openai',
           'model': 'gpt-4',
           'temperature': 0.7
       },
       output_config={
           'directory': './output',
           'format': 'latex',
           'compile_pdf': True
       }
   )
   
   # Initialize generator
   generator = ArxivPaperGenerator(config)
   
   # Prepare context data
   context_data = {
       'title': 'A Novel Approach to Machine Learning',
       'authors': ['Dr. Jane Smith', 'Prof. John Doe'],
       'abstract': 'This paper presents a novel approach to machine learning that improves accuracy by 15%.',
       'keywords': ['machine learning', 'neural networks', 'optimization'],
       'research_data': {
           'methodology': 'We used a combination of supervised and unsupervised learning techniques.',
           'results': 'Our approach achieved 95% accuracy on the test dataset.',
           'conclusions': 'The proposed method shows significant improvement over existing approaches.'
       }
   }
   
   # Generate the paper
   result = generator.generate_paper(context_data)
   
   print(f"Paper generated successfully!")
   print(f"LaTeX file: {result.latex_path}")
   print(f"PDF file: {result.pdf_path}")
   print(f"Quality score: {result.quality_score:.2f}")

Method 2: Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Create a configuration file** (``config.json``):

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
     "validation": {
       "enabled": true,
       "strict_mode": false
     }
   }

2. **Create a context data file** (``context.json``):

.. code-block:: json

   {
     "title": "A Novel Approach to Machine Learning",
     "authors": ["Dr. Jane Smith", "Prof. John Doe"],
     "abstract": "This paper presents a novel approach to machine learning that improves accuracy by 15%.",
     "keywords": ["machine learning", "neural networks", "optimization"],
     "research_data": {
       "methodology": "We used a combination of supervised and unsupervised learning techniques.",
       "results": "Our approach achieved 95% accuracy on the test dataset.",
       "conclusions": "The proposed method shows significant improvement over existing approaches."
     }
   }

3. **Generate the paper**:

.. code-block:: bash

   arxiv-writer generate --config config.json --context context.json

Understanding the Output
------------------------

After generation, you'll find several files in your output directory:

.. code-block:: text

   output/
   ├── paper.tex              # Main LaTeX file
   ├── paper.pdf              # Compiled PDF (if enabled)
   ├── sections/               # Individual section files
   │   ├── abstract.tex
   │   ├── introduction.tex
   │   ├── methodology.tex
   │   ├── results.tex
   │   └── conclusion.tex
   ├── bibliography.bib       # Bibliography file
   ├── generation_report.json # Generation metadata
   └── quality_report.json    # Quality assessment

Key Files Explained
~~~~~~~~~~~~~~~~~~~

**paper.tex**
   The main LaTeX document that includes all sections and can be compiled independently.

**paper.pdf**
   The compiled PDF output (if PDF compilation is enabled).

**sections/**
   Individual LaTeX files for each paper section, useful for manual editing.

**generation_report.json**
   Contains metadata about the generation process, including:
   
   - Model used for each section
   - Generation timestamps
   - Token usage statistics
   - Processing time

**quality_report.json**
   Quality assessment results including:
   
   - Overall quality score
   - Section-specific scores
   - Validation results
   - Improvement suggestions

Customizing Your Paper
----------------------

Section Configuration
~~~~~~~~~~~~~~~~~~~~~

Customize which sections to generate:

.. code-block:: python

   config = PaperConfig(
       sections={
           'abstract': {'enabled': True, 'max_words': 250},
           'introduction': {'enabled': True, 'max_words': 800},
           'related_work': {'enabled': True, 'max_words': 600},
           'methodology': {'enabled': True, 'max_words': 1000},
           'results': {'enabled': True, 'max_words': 800},
           'discussion': {'enabled': True, 'max_words': 600},
           'conclusion': {'enabled': True, 'max_words': 400},
           'acknowledgments': {'enabled': False}
       }
   )

Template Customization
~~~~~~~~~~~~~~~~~~~~~~

Use custom prompt templates:

.. code-block:: python

   config = PaperConfig(
       templates={
           'prompts_file': 'my_custom_prompts.json',
           'custom_templates': {
               'introduction': 'Write a compelling introduction for a {field} paper about {topic}...'
           }
       }
   )

LLM Provider Options
~~~~~~~~~~~~~~~~~~~~

Switch between different LLM providers:

.. code-block:: python

   # OpenAI GPT-4
   config = PaperConfig(
       llm_config={
           'provider': 'openai',
           'model': 'gpt-4',
           'temperature': 0.7
       }
   )
   
   # Anthropic Claude
   config = PaperConfig(
       llm_config={
           'provider': 'anthropic',
           'model': 'claude-3-opus-20240229',
           'temperature': 0.7
       }
   )
   
   # Google Gemini
   config = PaperConfig(
       llm_config={
           'provider': 'google',
           'model': 'gemini-pro',
           'temperature': 0.7
       }
   )

Common Workflows
----------------

Academic Research Paper
~~~~~~~~~~~~~~~~~~~~~~~

For a typical academic research paper:

.. code-block:: python

   context_data = {
       'title': 'Your Research Title',
       'authors': ['Author 1', 'Author 2'],
       'abstract': 'Brief summary of your research',
       'keywords': ['keyword1', 'keyword2', 'keyword3'],
       'research_question': 'What problem are you solving?',
       'methodology': 'How did you approach the problem?',
       'data_description': 'What data did you use?',
       'results_summary': 'What did you find?',
       'key_contributions': 'What are your main contributions?',
       'related_work': 'What existing work is relevant?',
       'limitations': 'What are the limitations of your work?'
   }

Survey Paper
~~~~~~~~~~~~

For a literature survey:

.. code-block:: python

   context_data = {
       'title': 'Survey of Machine Learning Techniques',
       'survey_scope': 'Machine learning applications in healthcare',
       'time_period': '2020-2024',
       'search_methodology': 'Systematic literature review using ACM, IEEE databases',
       'inclusion_criteria': 'Peer-reviewed papers with empirical results',
       'paper_categories': ['supervised learning', 'unsupervised learning', 'reinforcement learning'],
       'key_findings': 'Summary of main trends and findings',
       'research_gaps': 'Identified gaps in current research'
   }

Next Steps
----------

Now that you've generated your first paper, explore:

1. :doc:`configuration` - Learn about advanced configuration options
2. :doc:`examples/advanced_configuration` - See more complex examples
3. :doc:`examples/custom_templates` - Create custom prompt templates
4. :doc:`cli_usage` - Master the command-line interface
5. :doc:`api/core` - Dive into the Python API reference

Need help? Check the :doc:`troubleshooting` guide or :doc:`faq`.