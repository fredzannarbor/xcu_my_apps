# Implementation Plan

- [x] 1. Create LiteLLM logging filter
  - Create `src/codexes/core/logging_filters.py` with LiteLLMFilter class
  - Implement filter logic to suppress verbose LiteLLM messages
  - Add debug mode override for development
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Implement token usage tracking system
  - Create `src/codexes/core/token_usage_tracker.py` with TokenUsageTracker class
  - Implement usage recording with model, prompt, and token data
  - Add cost calculation using LiteLLM pricing information
  - Include error handling for missing cost data
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6_

- [x] 3. Create logging configuration manager
  - Create `src/codexes/core/logging_config.py` with LoggingConfigManager class
  - Implement centralized logging setup and configuration
  - Apply LiteLLM filter to appropriate loggers
  - Add environment-specific logging settings
  - Add logging configuration directions to tech.md
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 4. Enhance LLM caller with prompt name logging and token tracking
  - Modify `src/codexes/core/llm_caller.py` to accept optional prompt names parameter
  - Update logging format to include prompt names before success icons
  - Integrate TokenUsageTracker into LLM calls to collect usage data
  - Ensure consistent logging format across all LLM interactions
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 4.1, 4.2_

- [x] 5. Create statistics reporter for end-of-pipeline summaries
  - Create `src/codexes/core/statistics_reporter.py` with StatisticsReporter class
  - Implement pipeline statistics reporting with token usage and costs
  - Add model-specific and prompt-specific breakdowns
  - Format reports for readability with clear sections
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 6. Update LLM call sites to provide prompt names
  - Update `src/codexes/modules/distribution/llm_field_completer.py` to pass prompt names
  - Update `src/codexes/modules/builders/llm_get_book_data.py` to pass prompt names
  - Update other LLM calling modules to provide prompt names from existing prompt keys
  - Ensure consistent prompt name passing across all modules
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2_

- [x] 7. Integrate statistics reporting into pipeline execution
  - Update `run_book_pipeline.py` to initialize TokenUsageTracker
  - Add end-of-pipeline statistics reporting using StatisticsReporter
  - Ensure statistics are collected across all LLM operations
  - Handle cases where multiple pipelines run concurrently
  - _Requirements: 4.1, 4.2, 4.5_

- [x] 8. Apply logging configuration to application startup
  - Update application initialization to use LoggingConfigManager
  - Apply LiteLLM filtering by default in `run_book_pipeline.py` and other entry points
  - Configure appropriate logging levels for different environments
  - Test logging configuration in development and production modes
  - _Requirements: 1.1, 1.2, 1.3, 5.1, 5.2, 5.3, 5.4_

- [x] 9. Create comprehensive test suite for logging improvements
  - Write unit tests for LiteLLMFilter with various message patterns
  - Write unit tests for TokenUsageTracker with mock usage data
  - Write unit tests for StatisticsReporter with sample statistics
  - Write integration tests for complete logging flow
  - Test error handling and recovery scenarios
  - _Requirements: All requirements validation_

- [x] 10. Add configuration options for logging behavior
  - Create configuration file for logging settings
  - Add options to enable/disable LiteLLM filtering
  - Add options to control statistics reporting detail level
  - Add options for different logging formats and outputs
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 11. Performance optimization and validation
  - Profile logging performance impact on LLM operations
  - Optimize token tracking to minimize overhead
  - Validate that filtering doesn't miss critical error messages
  - Test logging behavior under high-volume scenarios
  - _Requirements: 1.5, performance validation_