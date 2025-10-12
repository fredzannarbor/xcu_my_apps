Core API Reference
==================

This section documents the core classes and functions for paper generation.

ArxivPaperGenerator
-------------------

.. autoclass:: arxiv_writer.core.generator.ArxivPaperGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   The main orchestrator class for academic paper generation. This class coordinates
   the entire paper generation workflow, from context collection to final output.

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer import ArxivPaperGenerator, PaperConfig

      config = PaperConfig.from_file("config.json")
      generator = ArxivPaperGenerator(config)
      
      context_data = {
          "title": "My Research Paper",
          "authors": ["John Doe"],
          "abstract": "This paper presents..."
      }
      
      result = generator.generate_paper(context_data)
      print(f"Generated: {result.output_path}")

SectionGenerator
----------------

.. autoclass:: arxiv_writer.core.section_generator.SectionGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Handles generation of individual paper sections using LLM providers.

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.core.section_generator import SectionGenerator
      from arxiv_writer.llm import LLMCaller
      from arxiv_writer.templates import TemplateManager

      llm_caller = LLMCaller(llm_config)
      template_manager = TemplateManager(template_config)
      
      generator = SectionGenerator(llm_caller, template_manager)
      
      section = generator.generate_section(
          section_config=section_config,
          context=context_data
      )

ContextCollector
----------------

.. autoclass:: arxiv_writer.core.context_collector.ContextCollector
   :members:
   :undoc-members:
   :show-inheritance:

   Collects and prepares context data for paper generation from various sources.

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.core.context_collector import ContextCollector

      collector = ContextCollector(context_config)
      
      # Collect from multiple sources
      sources = [
          {"type": "csv", "path": "data/results.csv"},
          {"type": "json", "path": "data/metadata.json"}
      ]
      
      context = collector.collect_context(sources)
      prepared_context = collector.prepare_context(context)

ContentValidator
----------------

.. autoclass:: arxiv_writer.core.validator.ContentValidator
   :members:
   :undoc-members:
   :show-inheritance:

   Validates generated content against academic writing standards and custom rules.

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.core.validator import ContentValidator

      validator = ContentValidator(validation_config)
      
      # Validate a section
      result = validator.validate_section(section_content, section_name)
      
      if result.is_valid:
          print("Section passed validation")
      else:
          print(f"Validation errors: {result.errors}")

PaperQualityAssessor
--------------------

.. autoclass:: arxiv_writer.core.quality_assessor.PaperQualityAssessor
   :members:
   :undoc-members:
   :show-inheritance:

   Assesses the quality of generated papers and provides improvement suggestions.

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.core.quality_assessor import PaperQualityAssessor

      assessor = PaperQualityAssessor(quality_config)
      
      # Assess paper quality
      assessment = assessor.assess_paper(paper_content)
      
      print(f"Overall quality score: {assessment.overall_score}")
      print(f"Suggestions: {assessment.suggestions}")

Data Models
-----------

Section
~~~~~~~

.. autoclass:: arxiv_writer.core.models.Section
   :members:
   :undoc-members:
   :show-inheritance:

   Represents a paper section with metadata and validation status.

   **Attributes:**

   - ``name`` (str): Section name (e.g., "introduction", "methodology")
   - ``content`` (str): Generated section content
   - ``word_count`` (int): Number of words in the section
   - ``generated_at`` (datetime): Timestamp of generation
   - ``model_used`` (str): LLM model used for generation
   - ``validation_status`` (ValidationStatus): Validation result
   - ``metadata`` (Dict[str, Any]): Additional metadata

PaperResult
~~~~~~~~~~~

.. autoclass:: arxiv_writer.core.models.PaperResult
   :members:
   :undoc-members:
   :show-inheritance:

   Result of complete paper generation with all sections and metadata.

   **Attributes:**

   - ``sections`` (Dict[str, Section]): Generated sections by name
   - ``complete_paper`` (str): Complete paper content
   - ``generation_summary`` (GenerationSummary): Generation metadata
   - ``output_files`` (List[str]): Paths to generated files
   - ``context_data`` (Dict[str, Any]): Context data used for generation

GenerationSummary
~~~~~~~~~~~~~~~~~~

.. autoclass:: arxiv_writer.core.models.GenerationSummary
   :members:
   :undoc-members:
   :show-inheritance:

   Summary of the paper generation process with timing and usage statistics.

   **Attributes:**

   - ``start_time`` (datetime): Generation start time
   - ``end_time`` (datetime): Generation end time
   - ``total_duration`` (timedelta): Total generation time
   - ``token_usage`` (TokenUsage): Token usage statistics
   - ``model_usage`` (Dict[str, int]): Models used and frequency
   - ``section_timings`` (Dict[str, float]): Time taken per section

ValidationResult
~~~~~~~~~~~~~~~~

.. autoclass:: arxiv_writer.core.models.ValidationResult
   :members:
   :undoc-members:
   :show-inheritance:

   Result of content validation with errors and suggestions.

   **Attributes:**

   - ``is_valid`` (bool): Whether content passed validation
   - ``score`` (float): Validation score (0.0-1.0)
   - ``errors`` (List[ValidationError]): Validation errors
   - ``warnings`` (List[ValidationWarning]): Validation warnings
   - ``suggestions`` (List[str]): Improvement suggestions

QualityAssessment
~~~~~~~~~~~~~~~~~

.. autoclass:: arxiv_writer.core.models.QualityAssessment
   :members:
   :undoc-members:
   :show-inheritance:

   Quality assessment result with scores and recommendations.

   **Attributes:**

   - ``overall_score`` (float): Overall quality score (0.0-1.0)
   - ``section_scores`` (Dict[str, float]): Scores by section
   - ``criteria_scores`` (Dict[str, float]): Scores by quality criteria
   - ``strengths`` (List[str]): Identified strengths
   - ``weaknesses`` (List[str]): Identified weaknesses
   - ``suggestions`` (List[str]): Improvement suggestions

Exceptions
----------

.. automodule:: arxiv_writer.core.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

   **Exception Hierarchy:**

   - ``ArxivWriterError`` - Base exception
     - ``ConfigurationError`` - Configuration-related errors
     - ``TemplateError`` - Template loading and rendering errors
     - ``LLMError`` - LLM integration errors
     - ``ValidationError`` - Content validation errors
     - ``GenerationError`` - Paper generation errors
     - ``PluginError`` - Plugin system errors

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.core.exceptions import ConfigurationError

      try:
          config = PaperConfig.from_file("invalid_config.json")
      except ConfigurationError as e:
          print(f"Configuration error: {e}")
          print(f"Suggestions: {e.suggestions}")

Utility Functions
-----------------

.. automodule:: arxiv_writer.core
   :members: create_default_config, validate_context_data, estimate_generation_time
   :undoc-members:

   **Utility Functions:**

   .. autofunction:: arxiv_writer.core.create_default_config

      Create a default configuration for common use cases.

      **Parameters:**

      - ``paper_type`` (str): Type of paper ("research", "survey", "technical")
      - ``llm_provider`` (str): LLM provider to use
      - ``output_format`` (str): Output format ("latex", "markdown")

      **Returns:**

      - ``PaperConfig``: Default configuration

   .. autofunction:: arxiv_writer.core.validate_context_data

      Validate context data structure and completeness.

      **Parameters:**

      - ``context_data`` (Dict[str, Any]): Context data to validate
      - ``required_fields`` (List[str]): Required field names

      **Returns:**

      - ``ValidationResult``: Validation result

   .. autofunction:: arxiv_writer.core.estimate_generation_time

      Estimate paper generation time based on configuration and context.

      **Parameters:**

      - ``config`` (PaperConfig): Paper configuration
      - ``context_data`` (Dict[str, Any]): Context data

      **Returns:**

      - ``timedelta``: Estimated generation time

Constants
---------

.. automodule:: arxiv_writer.core.constants
   :members:
   :undoc-members:

   **Available Constants:**

   - ``DEFAULT_SECTIONS`` - List of standard paper sections
   - ``SUPPORTED_OUTPUT_FORMATS`` - Supported output formats
   - ``QUALITY_THRESHOLDS`` - Default quality score thresholds
   - ``MAX_SECTION_WORDS`` - Maximum words per section by type
   - ``LATEX_PACKAGES`` - Required LaTeX packages

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.core.constants import DEFAULT_SECTIONS, QUALITY_THRESHOLDS

      print(f"Standard sections: {DEFAULT_SECTIONS}")
      print(f"Minimum quality score: {QUALITY_THRESHOLDS['minimum']}")

Type Definitions
----------------

.. automodule:: arxiv_writer.core.types
   :members:
   :undoc-members:

   **Type Aliases:**

   - ``ContextData`` - Type alias for context data dictionary
   - ``SectionConfig`` - Type alias for section configuration
   - ``ValidationRules`` - Type alias for validation rule configuration
   - ``QualityCriteria`` - Type alias for quality assessment criteria

   **Example Usage:**

   .. code-block:: python

      from arxiv_writer.core.types import ContextData, SectionConfig

      def process_context(context: ContextData) -> None:
          # Process context data with type hints
          pass

      def configure_section(config: SectionConfig) -> None:
          # Configure section with type hints
          pass