# Implementation Plan

- [x] 1. Enhance Stage 1 content generation to include back cover text generation
  - Add back cover text generation function to `llm_get_book_data.py`
  - Use existing LLM infrastructure to generate clean, final text
  - Store result in book data for later use during cover generation
  - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2_

- [ ] 2. Update back cover text prompt configuration
  - Modify existing `back_cover_text` prompt in `prompts.json`
  - Change prompt to generate final text instead of template with variables
  - Ensure prompt produces clean, publication-ready text
  - _Requirements: 1.1, 1.2, 3.3_

- [ ] 3. Implement back cover text generation in Stage 1 pipeline
  - Integrate back cover text generation into existing content generation workflow
  - Call LLM after quote generation when full context is available
  - Add error handling and fallback logic for failed generation
  - _Requirements: 1.1, 1.2, 1.4, 2.2, 4.3_

- [ ] 4. Add validation and fallback mechanisms
  - Implement response validation for generated back cover text
  - Create fallback text generation using book metadata
  - Add comprehensive logging for debugging and monitoring
  - _Requirements: 2.2, 2.4, 4.1, 4.4_

- [ ] 5. Simplify cover generator to use pre-generated text
  - Remove variable substitution logic from `cover_generator.py`
  - Update to use `back_cover_text` field directly from book data
  - Remove unused `substitute_template_variables()` function
  - _Requirements: 2.1, 2.3_

- [ ] 6. Update cover generation to handle pre-processed text
  - Modify cover generation to expect clean, final back cover text
  - Ensure LaTeX escaping still works correctly with generated text
  - Test cover compilation with LLM-generated back cover text
  - _Requirements: 1.4, 2.1, 2.3_

- [ ] 7. Create comprehensive tests for back cover text generation
  - Write unit tests for back cover text generation function
  - Test LLM integration with various book metadata scenarios
  - Test fallback behavior when LLM generation fails
  - _Requirements: 2.2, 4.3_

- [ ] 8. Test full pipeline integration
  - Run complete book pipeline from Stage 1 through cover generation
  - Verify back cover text is generated correctly in Stage 1
  - Confirm cover generation uses pre-generated text without issues
  - _Requirements: 2.1, 2.3, 2.4_

- [ ] 9. Add monitoring and configuration options
  - Add LLM usage tracking for back cover text generation
  - Implement configurable settings for text generation parameters
  - Add success/failure metrics for monitoring
  - _Requirements: 4.1, 4.2, 4.4_

- [ ] 10. Validate and optimize text quality
  - Test generated back cover text quality across different book types
  - Fine-tune prompt parameters for optimal results
  - Ensure generated text meets length and style requirements
  - _Requirements: 1.3, 3.3, 3.4_