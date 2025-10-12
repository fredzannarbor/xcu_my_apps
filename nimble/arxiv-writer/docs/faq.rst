Frequently Asked Questions
===========================

General Questions
-----------------

What is ArXiv Writer?
~~~~~~~~~~~~~~~~~~~~~

ArXiv Writer is a Python package that uses Large Language Models (LLMs) to generate academic papers in arXiv format. It provides a clean API for creating publication-ready LaTeX documents with configurable templates, multiple LLM provider support, and built-in validation.

How is this different from other AI writing tools?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ArXiv Writer is specifically designed for academic paper generation with:

- **Academic focus:** Templates and validation rules designed for scholarly writing
- **LaTeX output:** Generates publication-ready LaTeX with proper formatting
- **Multi-LLM support:** Works with OpenAI, Anthropic, Google, and other providers
- **Extensible:** Plugin architecture for custom functionality
- **Reproducible:** Configuration-driven approach for consistent results

Is ArXiv Writer free to use?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ArXiv Writer itself is open-source and free to use under the MIT license. However, you'll need API access to LLM providers (OpenAI, Anthropic, etc.), which have their own pricing structures.

Installation and Setup
----------------------

What are the system requirements?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Python 3.8 or higher
- LaTeX distribution (TeX Live, MiKTeX, or MacTeX)
- Internet connection for LLM API calls
- 4GB+ RAM recommended for large papers

Which LLM providers are supported?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ArXiv Writer supports all providers available through LiteLLM:

- **OpenAI:** GPT-4, GPT-3.5-turbo, GPT-4-turbo
- **Anthropic:** Claude-3 (Opus, Sonnet, Haiku)
- **Google:** Gemini Pro, Gemini Pro Vision
- **Cohere:** Command, Command-Light
- **Azure OpenAI:** Custom deployments
- **Local models:** Ollama, LM Studio, and others

Can I use local/offline models?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! ArXiv Writer supports local models through:

- **Ollama:** For running models locally
- **LM Studio:** Local model serving
- **Custom endpoints:** Any OpenAI-compatible API

Example configuration:

.. code-block:: json

   {
     "llm": {
       "provider": "ollama",
       "model": "llama2",
       "api_base": "http://localhost:11434"
     }
   }

Do I need to know LaTeX?
~~~~~~~~~~~~~~~~~~~~~~~~

No, ArXiv Writer generates LaTeX automatically. However, basic LaTeX knowledge is helpful for:

- Customizing output formatting
- Troubleshooting compilation issues
- Making manual edits to generated papers

Usage Questions
---------------

How long does it take to generate a paper?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generation time depends on:

- **Paper length:** 5-15 minutes for typical papers
- **LLM provider:** GPT-4 is slower but higher quality than GPT-3.5
- **Context size:** Larger context data takes longer to process
- **Sections:** More sections = longer generation time

Typical times:
- Abstract: 30-60 seconds
- Full 6-section paper: 5-10 minutes
- Survey paper: 10-20 minutes

What kind of papers can I generate?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ArXiv Writer works well for:

- **Research papers:** Original research with methodology and results
- **Survey papers:** Literature reviews and state-of-the-art summaries
- **Technical reports:** Detailed technical documentation
- **Conference papers:** Short-form academic papers
- **Thesis chapters:** Individual chapters with proper structure

Less suitable for:
- Creative writing
- Non-academic content
- Papers requiring extensive mathematical proofs
- Highly specialized domain knowledge without proper context

How much does it cost to generate a paper?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Costs depend on your LLM provider and paper length:

**OpenAI GPT-4 (typical 6-section paper):**
- Input tokens: ~20,000 ($0.60)
- Output tokens: ~8,000 ($2.40)
- **Total: ~$3.00**

**OpenAI GPT-3.5-turbo:**
- **Total: ~$0.30**

**Anthropic Claude-3:**
- **Total: ~$2.50**

Tips to reduce costs:
- Use GPT-3.5-turbo for simpler sections
- Optimize context data size
- Generate sections individually
- Use local models when possible

Quality and Validation
----------------------

How good is the generated content?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Quality depends on several factors:

- **Context quality:** Better input data = better output
- **Model choice:** GPT-4 generally produces higher quality than GPT-3.5
- **Template customization:** Well-crafted prompts improve results
- **Domain expertise:** Papers in well-represented domains perform better

ArXiv Writer includes quality assessment that typically scores:
- **0.8-1.0:** Publication-ready with minor edits
- **0.6-0.8:** Good foundation, needs revision
- **0.4-0.6:** Requires significant editing
- **<0.4:** May need regeneration with better context

Can I edit the generated content?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! ArXiv Writer generates:

- **Individual section files:** Edit specific sections
- **Complete LaTeX file:** Full document for comprehensive editing
- **Structured output:** Easy to modify and recompile

The LaTeX output is designed to be human-readable and editable.

How do I improve output quality?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Provide better context:**

   .. code-block:: json

      {
        "research_question": "Specific, focused question",
        "methodology": "Detailed methodology description",
        "key_findings": "Concrete results with numbers",
        "related_work": "Relevant citations and comparisons"
      }

2. **Customize templates:**

   .. code-block:: json

      {
        "templates": {
          "custom_templates": {
            "introduction": "Write a compelling introduction that..."
          }
        }
      }

3. **Use appropriate models:**

   - GPT-4 for complex sections (methodology, discussion)
   - GPT-3.5-turbo for simpler sections (abstract, conclusion)

4. **Iterate and refine:**

   - Generate sections individually
   - Refine context based on initial results
   - Use validation feedback

Technical Questions
-------------------

Can I integrate ArXiv Writer into my existing workflow?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! ArXiv Writer provides multiple integration options:

- **Python API:** Integrate into existing Python applications
- **CLI:** Use in shell scripts and CI/CD pipelines
- **Configuration files:** Version control your paper generation settings
- **Plugin system:** Extend functionality for specific needs

Example CI/CD integration:

.. code-block:: yaml

   # GitHub Actions
   - name: Generate Paper
     run: |
       arxiv-writer generate --config .github/paper-config.json
     env:
       OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

How do I handle sensitive data?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ArXiv Writer provides several security features:

- **Environment variables:** Store API keys securely
- **Configuration separation:** Keep sensitive data out of version control
- **Local processing:** Context data never leaves your system
- **API key rotation:** Easy to update credentials

Best practices:

.. code-block:: bash

   # Use .env files
   echo "OPENAI_API_KEY=your-key" > .env
   
   # Or environment variables
   export OPENAI_API_KEY="your-key"
   
   # Never commit API keys to version control
   echo ".env" >> .gitignore

Can I use ArXiv Writer for commercial purposes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, ArXiv Writer is released under the MIT license, which allows commercial use. However:

- Check your LLM provider's terms of service
- Ensure compliance with your organization's AI usage policies
- Consider data privacy implications for sensitive research

How do I backup and version control my work?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Recommended approach:

.. code-block:: text

   project/
   ├── configs/
   │   ├── base.json
   │   └── production.json
   ├── context/
   │   ├── paper1.json
   │   └── paper2.json
   ├── templates/
   │   └── custom_prompts.json
   ├── output/
   │   └── .gitignore  # Don't commit generated files
   └── .env.example    # Template for environment variables

Version control:
- Commit configuration files
- Commit context data (if not sensitive)
- Commit custom templates
- Don't commit API keys or generated outputs

Troubleshooting
---------------

Why is generation failing?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Common causes:

1. **API key issues:** Check environment variables and account status
2. **Rate limiting:** Reduce request frequency or upgrade API plan
3. **Invalid configuration:** Validate config file syntax
4. **Network issues:** Check internet connection and firewall settings
5. **LaTeX issues:** Verify LaTeX installation and required packages

Debug steps:

.. code-block:: bash

   # Validate configuration
   arxiv-writer validate --config config.json
   
   # Test with verbose output
   arxiv-writer generate --config config.json --verbose
   
   # Check API connectivity
   arxiv-writer generate --config config.json --dry-run

Why is LaTeX compilation failing?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Common LaTeX issues:

1. **Missing packages:** Install required LaTeX packages
2. **Encoding problems:** Use UTF-8 encoding
3. **Bibliography errors:** Ensure proper citation format
4. **Figure issues:** Check image paths and formats

Solutions:

.. code-block:: bash

   # Install full LaTeX distribution
   sudo apt-get install texlive-full  # Ubuntu
   brew install --cask mactex         # macOS
   
   # Test LaTeX installation
   pdflatex --version
   
   # Compile manually for debugging
   cd output
   pdflatex paper.tex

How do I get help with specific issues?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Check documentation:** This guide covers most common issues
2. **Search GitHub issues:** Someone may have had the same problem
3. **Create minimal reproduction:** Simplify your case to isolate the issue
4. **Provide debug information:** Include system info, config, and error messages

When creating an issue, include:

.. code-block:: bash

   # System information
   python --version
   arxiv-writer --version
   
   # Debug output
   arxiv-writer generate --config config.json --debug 2>&1 | tee debug.log

Advanced Usage
--------------

Can I create custom paper formats?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! ArXiv Writer supports:

- **Custom LaTeX templates:** Override document class and packages
- **Custom prompt templates:** Tailor content generation
- **Plugin system:** Add new functionality
- **Output formatters:** Support additional formats

Example custom format:

.. code-block:: json

   {
     "output": {
       "latex": {
         "document_class": "IEEEtran",
         "packages": ["cite", "amsmath", "algorithmic"],
         "custom_preamble": "\\usepackage{custom-style}"
       }
     }
   }

How do I create custom plugins?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the :doc:`examples/plugin_development` guide for detailed instructions. Basic plugin structure:

.. code-block:: python

   from arxiv_writer.plugins import BasePlugin
   
   class CustomFormatterPlugin(BasePlugin):
       def format_section(self, section_content, section_name):
           # Custom formatting logic
           return formatted_content

Can I use ArXiv Writer for non-English papers?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, but with limitations:

- **Supported:** Most European languages, Chinese, Japanese
- **Template customization:** May need language-specific prompts
- **LaTeX packages:** Might need additional packages for proper typography

Example configuration:

.. code-block:: json

   {
     "templates": {
       "language": "spanish",
       "custom_templates": {
         "introduction": "Escribe una introducción para un artículo sobre..."
       }
     },
     "output": {
       "latex": {
         "packages": ["babel", "inputenc"],
         "babel_options": "spanish"
       }
     }
   }

Still have questions?
---------------------

If your question isn't answered here:

1. Check the full documentation at :doc:`index`
2. Search existing GitHub issues
3. Create a new issue with the "question" label
4. Join our community discussions

We're always happy to help improve ArXiv Writer!