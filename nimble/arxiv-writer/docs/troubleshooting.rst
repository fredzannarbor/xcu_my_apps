Troubleshooting Guide
====================

This guide helps you diagnose and resolve common issues when using ArXiv Writer.

Installation Issues
-------------------

Package Installation Fails
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** ``pip install arxiv-writer`` fails with errors.

**Solutions:**

1. **Update pip and setuptools:**

   .. code-block:: bash

      pip install --upgrade pip setuptools wheel

2. **Use virtual environment:**

   .. code-block:: bash

      python -m venv arxiv-writer-env
      source arxiv-writer-env/bin/activate  # Linux/macOS
      # or
      arxiv-writer-env\Scripts\activate     # Windows
      pip install arxiv-writer

3. **Install from source:**

   .. code-block:: bash

      git clone https://github.com/ailabforbooklovers/arxiv-writer.git
      cd arxiv-writer
      pip install -e .

4. **Check Python version:**

   .. code-block:: bash

      python --version  # Should be 3.8 or higher

Import Errors
~~~~~~~~~~~~~

**Problem:** ``ImportError: No module named 'arxiv_writer'``

**Solutions:**

1. **Verify installation:**

   .. code-block:: bash

      pip list | grep arxiv-writer

2. **Check Python path:**

   .. code-block:: python

      import sys
      print(sys.path)

3. **Reinstall package:**

   .. code-block:: bash

      pip uninstall arxiv-writer
      pip install arxiv-writer

LaTeX Installation Issues
~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** LaTeX compilation fails or ``pdflatex`` not found.

**Solutions:**

1. **Install LaTeX distribution:**

   .. code-block:: bash

      # Ubuntu/Debian
      sudo apt-get install texlive-full
      
      # macOS (Homebrew)
      brew install --cask mactex
      
      # Windows: Download MiKTeX from https://miktex.org/

2. **Verify LaTeX installation:**

   .. code-block:: bash

      pdflatex --version
      which pdflatex

3. **Install missing packages:**

   .. code-block:: bash

      # Ubuntu/Debian
      sudo apt-get install texlive-latex-extra texlive-fonts-recommended
      
      # MiKTeX (Windows)
      # Packages are installed automatically on first use

Configuration Issues
--------------------

Invalid Configuration File
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Configuration validation fails.

**Diagnosis:**

.. code-block:: bash

   arxiv-writer validate --config config.json

**Common Issues:**

1. **JSON syntax errors:**

   .. code-block:: bash

      # Use a JSON validator
      python -m json.tool config.json

2. **Missing required fields:**

   .. code-block:: json

      {
        "llm": {
          "provider": "openai",  // Required
          "model": "gpt-4"       // Required
        }
      }

3. **Invalid values:**

   .. code-block:: json

      {
        "llm": {
          "temperature": 2.5  // Should be 0.0-2.0
        }
      }

Environment Variable Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** API keys not recognized.

**Solutions:**

1. **Check environment variables:**

   .. code-block:: bash

      echo $OPENAI_API_KEY
      env | grep API_KEY

2. **Set variables correctly:**

   .. code-block:: bash

      export OPENAI_API_KEY="your-key-here"
      
      # Or use .env file
      echo "OPENAI_API_KEY=your-key-here" > .env

3. **Verify variable substitution:**

   .. code-block:: bash

      arxiv-writer config show --config config.json

API and LLM Issues
------------------

API Key Authentication Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** ``401 Unauthorized`` or ``403 Forbidden`` errors.

**Solutions:**

1. **Verify API key:**

   .. code-block:: bash

      # Test OpenAI API key
      curl -H "Authorization: Bearer $OPENAI_API_KEY" \
           https://api.openai.com/v1/models

2. **Check API key format:**

   - OpenAI: Starts with ``sk-``
   - Anthropic: Starts with ``sk-ant-``
   - Google: Various formats

3. **Verify account status:**

   - Check billing and usage limits
   - Ensure API access is enabled

Rate Limiting Issues
~~~~~~~~~~~~~~~~~~~~

**Problem:** ``429 Too Many Requests`` errors.

**Solutions:**

1. **Configure rate limiting:**

   .. code-block:: json

      {
        "llm": {
          "rate_limit": {
            "requests_per_minute": 30,
            "tokens_per_minute": 50000
          }
        }
      }

2. **Use retry configuration:**

   .. code-block:: json

      {
        "llm": {
          "retry": {
            "max_attempts": 5,
            "base_delay": 2.0,
            "max_delay": 120.0
          }
        }
      }

3. **Upgrade API plan:**

   - Check your provider's rate limits
   - Consider upgrading to higher tier

Model Not Available
~~~~~~~~~~~~~~~~~~~

**Problem:** ``Model not found`` or ``Model not available`` errors.

**Solutions:**

1. **Check available models:**

   .. code-block:: python

      from arxiv_writer.llm import LLMCaller
      caller = LLMCaller(config)
      print(caller.list_available_models())

2. **Use correct model names:**

   .. code-block:: json

      {
        "llm": {
          "provider": "openai",
          "model": "gpt-4"  // Not "gpt4" or "GPT-4"
        }
      }

3. **Check model access:**

   - Some models require special access
   - Verify your account has access to the model

Generation Issues
-----------------

Poor Quality Output
~~~~~~~~~~~~~~~~~~~

**Problem:** Generated content is low quality or irrelevant.

**Solutions:**

1. **Improve context data:**

   .. code-block:: json

      {
        "title": "Specific, descriptive title",
        "research_question": "Clear, focused research question",
        "methodology": "Detailed methodology description",
        "key_findings": "Specific results and findings"
      }

2. **Adjust model parameters:**

   .. code-block:: json

      {
        "llm": {
          "temperature": 0.3,  // Lower for more focused output
          "max_tokens": 2000   // Increase for longer sections
        }
      }

3. **Use better prompts:**

   - Customize prompt templates
   - Add more specific instructions
   - Include examples in prompts

Incomplete Generation
~~~~~~~~~~~~~~~~~~~~~

**Problem:** Generation stops early or sections are missing.

**Solutions:**

1. **Check token limits:**

   .. code-block:: json

      {
        "llm": {
          "max_tokens": 4000  // Increase if needed
        }
      }

2. **Verify section configuration:**

   .. code-block:: json

      {
        "sections": {
          "introduction": {
            "enabled": true,
            "max_words": 800
          }
        }
      }

3. **Check for errors:**

   .. code-block:: bash

      arxiv-writer generate --config config.json --verbose

Validation Failures
~~~~~~~~~~~~~~~~~~~~

**Problem:** Generated content fails validation.

**Solutions:**

1. **Adjust validation settings:**

   .. code-block:: json

      {
        "validation": {
          "strict_mode": false,
          "quality_thresholds": {
            "minimum_score": 0.6  // Lower threshold
          }
        }
      }

2. **Check specific validation errors:**

   .. code-block:: bash

      arxiv-writer validate --paper output/paper.tex --verbose

3. **Disable problematic rules:**

   .. code-block:: json

      {
        "validation": {
          "rules": {
            "word_count": {"enabled": false}
          }
        }
      }

LaTeX and PDF Issues
--------------------

LaTeX Compilation Errors
~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** LaTeX compilation fails with errors.

**Common Errors and Solutions:**

1. **Missing packages:**

   .. code-block:: latex

      ! LaTeX Error: File `amsmath.sty' not found.

   **Solution:**

   .. code-block:: bash

      # Ubuntu/Debian
      sudo apt-get install texlive-latex-extra
      
      # MiKTeX: Install package manager

2. **Encoding issues:**

   .. code-block:: latex

      ! Package inputenc Error: Unicode character

   **Solution:**

   .. code-block:: json

      {
        "output": {
          "latex": {
            "packages": ["inputenc", "fontenc"],
            "encoding": "utf8"
          }
        }
      }

3. **Bibliography errors:**

   .. code-block:: latex

      ! Undefined control sequence \cite

   **Solution:**

   .. code-block:: bash

      # Compile with bibliography
      arxiv-writer compile paper.tex --twice

PDF Generation Issues
~~~~~~~~~~~~~~~~~~~~~

**Problem:** PDF is not generated or is corrupted.

**Solutions:**

1. **Check LaTeX engine:**

   .. code-block:: json

      {
        "output": {
          "pdf": {
            "engine": "pdflatex"  // Try "xelatex" or "lualatex"
          }
        }
      }

2. **Enable verbose compilation:**

   .. code-block:: bash

      arxiv-writer compile paper.tex --verbose

3. **Manual compilation:**

   .. code-block:: bash

      cd output
      pdflatex paper.tex
      bibtex paper
      pdflatex paper.tex
      pdflatex paper.tex

Performance Issues
------------------

Slow Generation
~~~~~~~~~~~~~~~

**Problem:** Paper generation takes too long.

**Solutions:**

1. **Use faster models:**

   .. code-block:: json

      {
        "sections": {
          "abstract": {
            "model_override": "gpt-3.5-turbo"
          }
        }
      }

2. **Reduce context size:**

   .. code-block:: json

      {
        "context": {
          "max_context_length": 8000
        }
      }

3. **Generate sections in parallel:**

   .. code-block:: bash

      arxiv-writer section abstract --config config.json &
      arxiv-writer section introduction --config config.json &
      wait

Memory Issues
~~~~~~~~~~~~~

**Problem:** Out of memory errors during generation.

**Solutions:**

1. **Reduce batch size:**

   .. code-block:: json

      {
        "llm": {
          "batch_size": 1
        }
      }

2. **Process sections individually:**

   .. code-block:: bash

      for section in abstract introduction methodology results conclusion; do
          arxiv-writer section $section --config config.json
      done

3. **Increase system memory:**

   - Close other applications
   - Use a machine with more RAM

Plugin Issues
-------------

Plugin Not Loading
~~~~~~~~~~~~~~~~~~

**Problem:** Custom plugins are not recognized.

**Solutions:**

1. **Check plugin path:**

   .. code-block:: json

      {
        "plugins": {
          "discovery_paths": ["./plugins", "/path/to/plugins"]
        }
      }

2. **Verify plugin structure:**

   .. code-block:: text

      plugins/
      └── my_plugin/
          ├── __init__.py
          ├── plugin.py
          └── config.json

3. **Check plugin registration:**

   .. code-block:: bash

      arxiv-writer plugin list

Plugin Conflicts
~~~~~~~~~~~~~~~~~

**Problem:** Multiple plugins conflict with each other.

**Solutions:**

1. **Disable conflicting plugins:**

   .. code-block:: json

      {
        "plugins": {
          "plugins": {
            "conflicting_plugin": {"enabled": false}
          }
        }
      }

2. **Check plugin priorities:**

   .. code-block:: json

      {
        "plugins": {
          "plugins": {
            "plugin1": {"priority": 10},
            "plugin2": {"priority": 20}
          }
        }
      }

Getting Help
------------

Debug Information
~~~~~~~~~~~~~~~~~

When reporting issues, include:

1. **System information:**

   .. code-block:: bash

      python --version
      pip list | grep arxiv-writer
      arxiv-writer --version

2. **Configuration (sanitized):**

   .. code-block:: bash

      arxiv-writer config show --config config.json

3. **Error logs:**

   .. code-block:: bash

      arxiv-writer generate --config config.json --debug 2>&1 | tee debug.log

4. **Minimal reproduction:**

   Create a minimal example that reproduces the issue.

Support Channels
~~~~~~~~~~~~~~~~

1. **Documentation:** Check this documentation first
2. **GitHub Issues:** https://github.com/ailabforbooklovers/arxiv-writer/issues
3. **Discussions:** https://github.com/ailabforbooklovers/arxiv-writer/discussions
4. **Stack Overflow:** Tag questions with ``arxiv-writer``

Issue Template
~~~~~~~~~~~~~~

When creating an issue, use this template:

.. code-block:: text

   **Environment:**
   - OS: [e.g., Ubuntu 22.04]
   - Python version: [e.g., 3.11.0]
   - ArXiv Writer version: [e.g., 0.1.0]
   - LaTeX distribution: [e.g., TeX Live 2023]

   **Configuration:**
   ```json
   {
     // Your configuration (remove API keys)
   }
   ```

   **Expected behavior:**
   A clear description of what you expected to happen.

   **Actual behavior:**
   A clear description of what actually happened.

   **Steps to reproduce:**
   1. Step 1
   2. Step 2
   3. Step 3

   **Error messages:**
   ```
   Full error message and stack trace
   ```

   **Additional context:**
   Any other context about the problem.

Frequently Asked Questions
--------------------------

See the :doc:`faq` section for answers to common questions.