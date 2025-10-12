Installation
============

System Requirements
-------------------

ArXiv Writer requires:

* Python 3.8 or higher
* LaTeX distribution (for PDF compilation)
* Internet connection (for LLM API calls)

Python Version Support
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Python Version
     - Support Status
     - Notes
   * - 3.8
     - Supported
     - Minimum version
   * - 3.9
     - Supported
     - Full compatibility
   * - 3.10
     - Supported
     - Full compatibility
   * - 3.11
     - Supported
     - Full compatibility
   * - 3.12
     - Supported
     - Recommended

LaTeX Requirements
------------------

For PDF compilation, you need a LaTeX distribution installed:

**Linux (Ubuntu/Debian):**

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install texlive-full

**macOS:**

.. code-block:: bash

   # Using Homebrew
   brew install --cask mactex

   # Or download from: https://www.tug.org/mactex/

**Windows:**

Download and install MiKTeX from: https://miktex.org/download

Required LaTeX Packages
~~~~~~~~~~~~~~~~~~~~~~~

The following LaTeX packages are required for paper compilation:

* ``amsmath`` - Mathematical typesetting
* ``amsfonts`` - Mathematical fonts
* ``amssymb`` - Mathematical symbols
* ``graphicx`` - Graphics inclusion
* ``hyperref`` - Hyperlinks and references
* ``natbib`` - Bibliography management
* ``geometry`` - Page layout
* ``fancyhdr`` - Headers and footers
* ``booktabs`` - Professional tables
* ``algorithm2e`` - Algorithm typesetting

Most modern LaTeX distributions include these packages by default.

Installation Methods
--------------------

From PyPI (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install arxiv-writer

This installs the latest stable version with all required dependencies.

From Source
~~~~~~~~~~~

For the latest development version:

.. code-block:: bash

   git clone https://github.com/ailabforbooklovers/arxiv-writer.git
   cd arxiv-writer
   pip install -e .

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For development with all optional dependencies:

.. code-block:: bash

   git clone https://github.com/ailabforbooklovers/arxiv-writer.git
   cd arxiv-writer
   
   # Using uv (recommended)
   uv sync --dev
   
   # Or using pip
   pip install -e ".[dev,docs,test]"

Using Docker
~~~~~~~~~~~~

A Docker image is available for containerized usage:

.. code-block:: bash

   docker pull arxivwriter/arxiv-writer:latest
   docker run -v $(pwd):/workspace arxivwriter/arxiv-writer:latest

Verification
------------

Verify your installation:

.. code-block:: bash

   # Check package installation
   python -c "import arxiv_writer; print(arxiv_writer.__version__)"
   
   # Check CLI availability
   arxiv-writer --version
   
   # Test LaTeX installation
   pdflatex --version

Environment Setup
-----------------

API Keys
~~~~~~~~

Set up your LLM provider API keys:

.. code-block:: bash

   # OpenAI
   export OPENAI_API_KEY="your-openai-api-key"
   
   # Anthropic
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   
   # Google
   export GOOGLE_API_KEY="your-google-api-key"

Or create a ``.env`` file in your project directory:

.. code-block:: bash

   OPENAI_API_KEY=your-openai-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   GOOGLE_API_KEY=your-google-api-key

Configuration Directory
~~~~~~~~~~~~~~~~~~~~~~~

Create a configuration directory for your projects:

.. code-block:: bash

   mkdir ~/.arxiv-writer
   mkdir ~/.arxiv-writer/templates
   mkdir ~/.arxiv-writer/configs

Troubleshooting Installation
----------------------------

Common Issues
~~~~~~~~~~~~~

**ImportError: No module named 'arxiv_writer'**

Ensure you've activated the correct Python environment and the package is installed:

.. code-block:: bash

   pip list | grep arxiv-writer

**LaTeX compilation fails**

Check your LaTeX installation:

.. code-block:: bash

   which pdflatex
   pdflatex --version

**Permission errors on Linux/macOS**

Use ``--user`` flag for user-local installation:

.. code-block:: bash

   pip install --user arxiv-writer

**SSL certificate errors**

Update certificates or use trusted hosts:

.. code-block:: bash

   pip install --trusted-host pypi.org --trusted-host pypi.python.org arxiv-writer

Getting Help
~~~~~~~~~~~~

If you encounter installation issues:

1. Check the `troubleshooting guide <troubleshooting.html>`_
2. Search existing `GitHub issues <https://github.com/ailabforbooklovers/arxiv-writer/issues>`_
3. Create a new issue with your system details and error messages

Next Steps
----------

After installation, proceed to the :doc:`quickstart` guide to generate your first paper.