Testing Guide
=============

This guide covers the testing strategy, tools, and best practices for ArXiv Writer development.

Testing Philosophy
------------------

Our testing approach follows these principles:

1. **Test Pyramid** - More unit tests, fewer integration tests, minimal end-to-end tests
2. **Fast Feedback** - Tests should run quickly to enable rapid development
3. **Deterministic** - Tests should produce consistent results
4. **Isolated** - Tests should not depend on external services or each other
5. **Maintainable** - Tests should be easy to understand and modify

Test Structure
--------------

Directory Organization
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   tests/
   ├── unit/                        # Unit tests (fast, isolated)
   │   ├── test_core/
   │   │   ├── test_generator.py
   │   │   ├── test_section_generator.py
   │   │   ├── test_context_collector.py
   │   │   └── test_validator.py
   │   ├── test_llm/
   │   │   ├── test_caller.py
   │   │   ├── test_enhanced_caller.py
   │   │   └── test_models.py
   │   ├── test_config/
   │   │   └── test_loader.py
   │   ├── test_templates/
   │   │   ├── test_manager.py
   │   │   └── test_renderer.py
   │   └── test_plugins/
   │       ├── test_registry.py
   │       └── test_manager.py
   ├── integration/                 # Integration tests (slower, real components)
   │   ├── test_paper_generation/
   │   │   ├── test_end_to_end.py
   │   │   └── test_section_integration.py
   │   ├── test_llm_providers/
   │   │   ├── test_openai_integration.py
   │   │   └── test_anthropic_integration.py
   │   └── test_plugins/
   │       └── test_plugin_loading.py
   ├── system/                      # System tests (slowest, full system)
   │   ├── test_cli_commands.py
   │   ├── test_cross_platform.py
   │   └── test_performance.py
   ├── fixtures/                    # Test data and fixtures
   │   ├── configs/
   │   │   ├── test_config.json
   │   │   └── minimal_config.json
   │   ├── templates/
   │   │   └── test_prompts.json
   │   ├── context_data/
   │   │   ├── sample_context.json
   │   │   └── large_context.json
   │   └── expected_outputs/
   │       ├── sample_paper.tex
   │       └── sample_sections/
   └── conftest.py                  # Pytest configuration and shared fixtures

Test Categories
---------------

Unit Tests
~~~~~~~~~~

Unit tests focus on individual components in isolation.

**Example Unit Test:**

.. code-block:: python

   import pytest
   from unittest.mock import Mock, patch
   from arxiv_writer.core.section_generator import SectionGenerator
   from arxiv_writer.core.models import Section, SectionConfig

   class TestSectionGenerator:
       
       @pytest.fixture
       def mock_llm_caller(self):
           """Mock LLM caller for testing."""
           mock = Mock()
           mock.call_llm.return_value = Mock(
               content="Generated section content",
               model="gpt-4",
               token_usage={"input": 100, "output": 200}
           )
           return mock
       
       @pytest.fixture
       def mock_template_manager(self):
           """Mock template manager for testing."""
           mock = Mock()
           mock.render_template.return_value = "Rendered prompt template"
           return mock
       
       @pytest.fixture
       def section_config(self):
           """Sample section configuration."""
           return SectionConfig(
               name="introduction",
               max_words=800,
               min_words=400,
               enabled=True,
               validation_rules=["word_count", "academic_style"]
           )
       
       def test_generate_section_success(
           self, 
           mock_llm_caller, 
           mock_template_manager, 
           section_config
       ):
           """Test successful section generation."""
           generator = SectionGenerator(mock_llm_caller, mock_template_manager)
           
           context_data = {
               "title": "Test Paper",
               "field": "machine learning",
               "research_question": "How to test effectively?"
           }
           
           result = generator.generate_section(section_config, context_data)
           
           # Verify result structure
           assert isinstance(result, Section)
           assert result.name == "introduction"
           assert result.content == "Generated section content"
           assert result.model_used == "gpt-4"
           assert result.word_count > 0
           
           # Verify interactions
           mock_template_manager.render_template.assert_called_once_with(
               "introduction", context_data
           )
           mock_llm_caller.call_llm.assert_called_once()
       
       def test_generate_section_llm_error(
           self, 
           mock_llm_caller, 
           mock_template_manager, 
           section_config
       ):
           """Test handling of LLM errors."""
           from arxiv_writer.core.exceptions import LLMError
           
           mock_llm_caller.call_llm.side_effect = LLMError("API rate limit exceeded")
           
           generator = SectionGenerator(mock_llm_caller, mock_template_manager)
           
           with pytest.raises(LLMError) as exc_info:
               generator.generate_section(section_config, {})
           
           assert "API rate limit exceeded" in str(exc_info.value)
       
       @pytest.mark.parametrize("word_count,expected_valid", [
           (500, True),   # Within range
           (300, False),  # Below minimum
           (1000, False), # Above maximum
       ])
       def test_word_count_validation(
           self, 
           mock_llm_caller, 
           mock_template_manager, 
           section_config,
           word_count,
           expected_valid
       ):
           """Test word count validation with different values."""
           mock_llm_caller.call_llm.return_value = Mock(
               content=" ".join(["word"] * word_count),
               model="gpt-4"
           )
           
           generator = SectionGenerator(mock_llm_caller, mock_template_manager)
           result = generator.generate_section(section_config, {})
           
           assert (result.validation_status.is_valid) == expected_valid

Integration Tests
~~~~~~~~~~~~~~~~

Integration tests verify that components work together correctly.

**Example Integration Test:**

.. code-block:: python

   import pytest
   from pathlib import Path
   from arxiv_writer import ArxivPaperGenerator, PaperConfig
   from arxiv_writer.core.exceptions import ConfigurationError

   class TestPaperGenerationIntegration:
       
       @pytest.fixture
       def integration_config(self, tmp_path):
           """Configuration for integration testing."""
           return PaperConfig(
               llm_config={
                   "provider": "mock",  # Use mock provider for integration tests
                   "model": "mock-gpt-4",
                   "temperature": 0.7
               },
               output_config={
                   "directory": str(tmp_path / "output"),
                   "format": "latex",
                   "compile_pdf": False  # Skip PDF compilation in tests
               },
               sections={
                   "abstract": {"enabled": True, "max_words": 250},
                   "introduction": {"enabled": True, "max_words": 800},
                   "conclusion": {"enabled": True, "max_words": 400}
               }
           )
       
       @pytest.fixture
       def sample_context(self):
           """Sample context data for testing."""
           return {
               "title": "Integration Test Paper",
               "authors": ["Test Author"],
               "abstract": "This is a test abstract for integration testing.",
               "research_question": "How do we test integration effectively?",
               "key_findings": "Integration tests are essential for quality.",
               "methodology": "We use pytest and mock providers.",
               "results_summary": "All tests pass successfully."
           }
       
       @pytest.mark.integration
       def test_complete_paper_generation(self, integration_config, sample_context):
           """Test complete paper generation workflow."""
           generator = ArxivPaperGenerator(integration_config)
           
           result = generator.generate_paper(sample_context)
           
           # Verify result structure
           assert result.sections
           assert "abstract" in result.sections
           assert "introduction" in result.sections
           assert "conclusion" in result.sections
           
           # Verify content quality
           assert result.quality_score > 0.5
           assert result.complete_paper
           assert len(result.output_files) > 0
           
           # Verify files were created
           output_dir = Path(integration_config.output_config.directory)
           assert (output_dir / "paper.tex").exists()
           assert (output_dir / "generation_report.json").exists()
       
       @pytest.mark.integration
       def test_section_generation_order(self, integration_config, sample_context):
           """Test that sections are generated in correct order."""
           generator = ArxivPaperGenerator(integration_config)
           
           result = generator.generate_paper(sample_context)
           
           # Verify section order in complete paper
           paper_content = result.complete_paper
           abstract_pos = paper_content.find("\\section{Abstract}")
           intro_pos = paper_content.find("\\section{Introduction}")
           conclusion_pos = paper_content.find("\\section{Conclusion}")
           
           assert abstract_pos < intro_pos < conclusion_pos
       
       @pytest.mark.integration
       def test_configuration_validation_integration(self, tmp_path):
           """Test configuration validation in integration context."""
           invalid_config = {
               "llm": {
                   "provider": "nonexistent",  # Invalid provider
                   "model": "invalid-model"
               }
           }
           
           with pytest.raises(ConfigurationError) as exc_info:
               PaperConfig.from_dict(invalid_config)
           
           assert "nonexistent" in str(exc_info.value)

System Tests
~~~~~~~~~~~~

System tests verify the complete system behavior, including CLI and cross-platform compatibility.

**Example System Test:**

.. code-block:: python

   import pytest
   import subprocess
   import json
   from pathlib import Path

   class TestCLISystem:
       
       @pytest.fixture
       def cli_config_file(self, tmp_path):
           """Create CLI configuration file."""
           config = {
               "llm": {
                   "provider": "mock",
                   "model": "mock-gpt-4",
                   "temperature": 0.7
               },
               "output": {
                   "directory": str(tmp_path / "output"),
                   "format": "latex"
               }
           }
           
           config_file = tmp_path / "config.json"
           with open(config_file, "w") as f:
               json.dump(config, f)
           
           return config_file
       
       @pytest.fixture
       def cli_context_file(self, tmp_path):
           """Create CLI context file."""
           context = {
               "title": "CLI Test Paper",
               "authors": ["CLI Test Author"],
               "abstract": "Testing CLI functionality"
           }
           
           context_file = tmp_path / "context.json"
           with open(context_file, "w") as f:
               json.dump(context, f)
           
           return context_file
       
       @pytest.mark.system
       def test_cli_generate_command(self, cli_config_file, cli_context_file):
           """Test CLI paper generation command."""
           result = subprocess.run([
               "arxiv-writer", "generate",
               "--config", str(cli_config_file),
               "--context", str(cli_context_file)
           ], capture_output=True, text=True)
           
           assert result.returncode == 0
           assert "Paper generated successfully" in result.stdout
           
           # Verify output files exist
           output_dir = cli_config_file.parent / "output"
           assert (output_dir / "paper.tex").exists()
       
       @pytest.mark.system
       def test_cli_validate_command(self, cli_config_file):
           """Test CLI configuration validation."""
           result = subprocess.run([
               "arxiv-writer", "validate",
               "--config", str(cli_config_file)
           ], capture_output=True, text=True)
           
           assert result.returncode == 0
           assert "Configuration is valid" in result.stdout
       
       @pytest.mark.system
       def test_cli_help_commands(self):
           """Test CLI help functionality."""
           commands = ["generate", "validate", "template", "config"]
           
           for command in commands:
               result = subprocess.run([
                   "arxiv-writer", command, "--help"
               ], capture_output=True, text=True)
               
               assert result.returncode == 0
               assert "Usage:" in result.stdout

Test Fixtures and Utilities
----------------------------

Shared Fixtures
~~~~~~~~~~~~~~~

**conftest.py:**

.. code-block:: python

   import pytest
   import json
   from pathlib import Path
   from unittest.mock import Mock
   from arxiv_writer import PaperConfig
   from arxiv_writer.llm.models import LLMResponse

   @pytest.fixture
   def sample_config():
       """Standard configuration for testing."""
       return PaperConfig(
           llm_config={
               "provider": "mock",
               "model": "mock-gpt-4",
               "temperature": 0.7
           },
           output_config={
               "directory": "./test_output",
               "format": "latex",
               "compile_pdf": False
           },
           sections={
               "abstract": {"enabled": True, "max_words": 250},
               "introduction": {"enabled": True, "max_words": 800},
               "methodology": {"enabled": True, "max_words": 1000},
               "results": {"enabled": True, "max_words": 800},
               "conclusion": {"enabled": True, "max_words": 400}
           }
       )

   @pytest.fixture
   def sample_context():
       """Standard context data for testing."""
       return {
           "title": "Test Research Paper",
           "authors": ["Dr. Test Author", "Prof. Example Researcher"],
           "abstract": "This paper presents a comprehensive test of the system.",
           "keywords": ["testing", "research", "automation"],
           "research_question": "How can we effectively test paper generation?",
           "methodology": "We use automated testing with mock providers.",
           "key_findings": "Automated testing improves reliability significantly.",
           "results_summary": "All test cases pass with 95% coverage.",
           "limitations": "Testing with mocks may not catch all real-world issues.",
           "contributions": [
               "Comprehensive test suite for paper generation",
               "Mock providers for reliable testing",
               "Integration test framework"
           ]
       }

   @pytest.fixture
   def mock_llm_response():
       """Standard mock LLM response."""
       return LLMResponse(
           content="This is a generated section with appropriate academic content.",
           model="mock-gpt-4",
           token_usage={"input_tokens": 150, "output_tokens": 300},
           finish_reason="stop"
       )

   @pytest.fixture
   def temp_output_dir(tmp_path):
       """Temporary output directory for tests."""
       output_dir = tmp_path / "test_output"
       output_dir.mkdir()
       return output_dir

   @pytest.fixture(scope="session")
   def test_data_dir():
       """Directory containing test data files."""
       return Path(__file__).parent / "fixtures"

   @pytest.fixture
   def load_test_config():
       """Factory fixture for loading test configurations."""
       def _load_config(config_name: str) -> PaperConfig:
           config_path = Path(__file__).parent / "fixtures" / "configs" / f"{config_name}.json"
           return PaperConfig.from_file(str(config_path))
       return _load_config

Mock Providers
~~~~~~~~~~~~~~

**Mock LLM Provider for Testing:**

.. code-block:: python

   from arxiv_writer.llm.base import LLMProvider
   from arxiv_writer.llm.models import LLMResponse, Message

   class MockLLMProvider(LLMProvider):
       """Mock LLM provider for testing."""
       
       def __init__(self, responses: Dict[str, str] = None):
           self.responses = responses or {}
           self.default_response = "This is a mock response for testing purposes."
           self.call_count = 0
           self.last_messages = []
       
       def call_llm(self, messages: List[Message], **kwargs) -> LLMResponse:
           """Mock LLM call with predetermined responses."""
           self.call_count += 1
           self.last_messages = messages
           
           # Generate response key from messages
           key = self._generate_response_key(messages)
           content = self.responses.get(key, self.default_response)
           
           return LLMResponse(
               content=content,
               model=kwargs.get("model", "mock-model"),
               token_usage={
                   "input_tokens": sum(len(m.content.split()) for m in messages),
                   "output_tokens": len(content.split())
               },
               finish_reason="stop"
           )
       
       def get_available_models(self) -> List[str]:
           """Return mock available models."""
           return ["mock-gpt-4", "mock-gpt-3.5-turbo", "mock-claude-3"]
       
       def _generate_response_key(self, messages: List[Message]) -> str:
           """Generate key for response lookup."""
           # Use last user message as key
           for message in reversed(messages):
               if message.role == "user":
                   return message.content[:50]  # First 50 chars
           return "default"

Test Data Management
~~~~~~~~~~~~~~~~~~~~

**Test Data Structure:**

.. code-block:: text

   tests/fixtures/
   ├── configs/
   │   ├── minimal_config.json      # Minimal valid configuration
   │   ├── full_config.json         # Complete configuration example
   │   ├── invalid_config.json      # Invalid configuration for error testing
   │   └── research_config.json     # Research paper specific config
   ├── templates/
   │   ├── test_prompts.json        # Test prompt templates
   │   └── custom_prompts.json      # Custom template examples
   ├── context_data/
   │   ├── minimal_context.json     # Minimal context data
   │   ├── research_context.json    # Research paper context
   │   ├── survey_context.json      # Survey paper context
   │   └── large_context.json       # Large context for performance testing
   └── expected_outputs/
       ├── minimal_paper.tex        # Expected output for minimal input
       ├── research_paper.tex       # Expected research paper output
       └── sections/                # Expected individual sections
           ├── abstract.tex
           ├── introduction.tex
           └── conclusion.tex

**Loading Test Data:**

.. code-block:: python

   @pytest.fixture
   def load_test_data():
       """Factory for loading test data files."""
       def _load_data(category: str, filename: str) -> Dict[str, Any]:
           data_path = Path(__file__).parent / "fixtures" / category / filename
           with open(data_path, "r") as f:
               return json.load(f)
       return _load_data

   # Usage in tests
   def test_with_research_context(load_test_data):
       context = load_test_data("context_data", "research_context.json")
       # Use context in test

Running Tests
-------------

Test Execution
~~~~~~~~~~~~~~

**Basic Test Execution:**

.. code-block:: bash

   # Run all tests
   pytest
   
   # Run with verbose output
   pytest -v
   
   # Run specific test file
   pytest tests/unit/test_core/test_generator.py
   
   # Run specific test method
   pytest tests/unit/test_core/test_generator.py::TestArxivPaperGenerator::test_generate_paper_success

**Test Categories:**

.. code-block:: bash

   # Run only unit tests (fast)
   pytest tests/unit/
   
   # Run only integration tests
   pytest tests/integration/
   
   # Run only system tests
   pytest tests/system/
   
   # Run tests by marker
   pytest -m "not slow"
   pytest -m "integration"
   pytest -m "system"

**Parallel Execution:**

.. code-block:: bash

   # Install pytest-xdist for parallel execution
   pip install pytest-xdist
   
   # Run tests in parallel
   pytest -n auto
   
   # Run with specific number of workers
   pytest -n 4

Coverage Reporting
~~~~~~~~~~~~~~~~~~

**Generate Coverage Reports:**

.. code-block:: bash

   # Install coverage tools
   pip install pytest-cov
   
   # Run tests with coverage
   pytest --cov=src/arxiv_writer --cov-report=html --cov-report=term
   
   # Generate detailed coverage report
   pytest --cov=src/arxiv_writer --cov-report=html --cov-branch
   
   # View coverage report
   open htmlcov/index.html

**Coverage Configuration (.coveragerc):**

.. code-block:: ini

   [run]
   source = src/arxiv_writer
   omit = 
       */tests/*
       */test_*
       */__pycache__/*
       */venv/*
       */build/*
   
   [report]
   exclude_lines =
       pragma: no cover
       def __repr__
       raise AssertionError
       raise NotImplementedError
       if __name__ == .__main__.:
   
   [html]
   directory = htmlcov

Performance Testing
-------------------

Performance Test Examples
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   import time
   from arxiv_writer import ArxivPaperGenerator

   class TestPerformance:
       
       @pytest.mark.performance
       def test_paper_generation_time(self, sample_config, sample_context):
           """Test paper generation performance."""
           generator = ArxivPaperGenerator(sample_config)
           
           start_time = time.time()
           result = generator.generate_paper(sample_context)
           end_time = time.time()
           
           generation_time = end_time - start_time
           
           # Assert reasonable generation time (adjust based on requirements)
           assert generation_time < 30.0  # 30 seconds max
           assert result.quality_score > 0.6
       
       @pytest.mark.performance
       def test_large_context_handling(self, sample_config, load_test_data):
           """Test performance with large context data."""
           large_context = load_test_data("context_data", "large_context.json")
           generator = ArxivPaperGenerator(sample_config)
           
           start_time = time.time()
           result = generator.generate_paper(large_context)
           end_time = time.time()
           
           # Should handle large context within reasonable time
           assert (end_time - start_time) < 60.0  # 1 minute max
           assert result.sections
       
       @pytest.mark.performance
       def test_memory_usage(self, sample_config, sample_context):
           """Test memory usage during generation."""
           import psutil
           import os
           
           process = psutil.Process(os.getpid())
           initial_memory = process.memory_info().rss
           
           generator = ArxivPaperGenerator(sample_config)
           result = generator.generate_paper(sample_context)
           
           final_memory = process.memory_info().rss
           memory_increase = final_memory - initial_memory
           
           # Memory increase should be reasonable (adjust based on requirements)
           assert memory_increase < 100 * 1024 * 1024  # 100MB max increase

Continuous Integration
----------------------

GitHub Actions Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**.github/workflows/test.yml:**

.. code-block:: yaml

   name: Tests
   
   on:
     push:
       branches: [ main, develop ]
     pull_request:
       branches: [ main, develop ]
   
   jobs:
     test:
       runs-on: ${{ matrix.os }}
       strategy:
         matrix:
           os: [ubuntu-latest, windows-latest, macos-latest]
           python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
       
       steps:
       - uses: actions/checkout@v3
       
       - name: Set up Python ${{ matrix.python-version }}
         uses: actions/setup-python@v4
         with:
           python-version: ${{ matrix.python-version }}
       
       - name: Install LaTeX (Ubuntu)
         if: matrix.os == 'ubuntu-latest'
         run: |
           sudo apt-get update
           sudo apt-get install -y texlive-latex-base texlive-latex-extra
       
       - name: Install LaTeX (macOS)
         if: matrix.os == 'macos-latest'
         run: |
           brew install --cask basictex
           eval "$(/usr/libexec/path_helper)"
           sudo tlmgr update --self
           sudo tlmgr install collection-latexextra
       
       - name: Install LaTeX (Windows)
         if: matrix.os == 'windows-latest'
         run: |
           choco install miktex
       
       - name: Install dependencies
         run: |
           python -m pip install --upgrade pip
           pip install -e ".[dev,test]"
       
       - name: Run unit tests
         run: |
           pytest tests/unit/ -v --cov=src/arxiv_writer --cov-report=xml
       
       - name: Run integration tests
         run: |
           pytest tests/integration/ -v
       
       - name: Upload coverage to Codecov
         uses: codecov/codecov-action@v3
         with:
           file: ./coverage.xml
           flags: unittests
           name: codecov-umbrella

Test Quality Metrics
---------------------

Quality Gates
~~~~~~~~~~~~

Set up quality gates to ensure test quality:

.. code-block:: python

   # pytest.ini
   [tool:pytest]
   minversion = 6.0
   addopts = 
       -ra 
       --strict-markers 
       --strict-config 
       --cov=src/arxiv_writer 
       --cov-branch 
       --cov-report=term-missing:skip-covered 
       --cov-report=html 
       --cov-report=xml
       --cov-fail-under=90
   testpaths = tests
   markers =
       slow: marks tests as slow (deselect with '-m "not slow"')
       integration: marks tests as integration tests
       system: marks tests as system tests
       performance: marks tests as performance tests

**Quality Metrics to Track:**

1. **Code Coverage** - Minimum 90% line coverage
2. **Test Execution Time** - Unit tests < 30 seconds total
3. **Test Reliability** - No flaky tests
4. **Test Maintainability** - Clear, readable test code
5. **Test Documentation** - All test methods documented

Best Practices Summary
----------------------

1. **Write Tests First** - TDD approach when possible
2. **Keep Tests Simple** - One assertion per test when possible
3. **Use Descriptive Names** - Test names should explain what they test
4. **Mock External Dependencies** - Keep tests isolated and fast
5. **Test Edge Cases** - Include boundary conditions and error cases
6. **Maintain Test Data** - Keep test fixtures up to date
7. **Review Test Code** - Apply same quality standards as production code
8. **Monitor Test Performance** - Keep tests fast and reliable
9. **Document Complex Tests** - Explain non-obvious test logic
10. **Clean Up Resources** - Use fixtures and context managers properly

This comprehensive testing strategy ensures high code quality, reliability, and maintainability of the ArXiv Writer package.