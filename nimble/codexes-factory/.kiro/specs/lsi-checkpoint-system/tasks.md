# Implementation Plan

- [ ] 1. Create LSI Checkpoint Manager class
  - Implement core checkpoint file management functionality
  - Create `src/codexes/modules/distribution/lsi_checkpoint_manager.py` with LSICheckpointManager class
  - Include methods for file creation, data appending, and atomic write operations
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.4, 3.2, 3.4_

- [ ] 2. Implement checkpoint file operations
  - Write method to create timestamped checkpoint files with proper naming convention
  - Implement atomic append functionality for individual book LSI data
  - Add error handling for file I/O operations that doesn't interrupt pipeline
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2_

- [ ] 3. Add CSV formatting and validation
  - Implement CSV header writing for new checkpoint files
  - Create method to convert CodexMetadata to CSV row format matching LSI structure
  - Ensure checkpoint files use same format as existing batch LSI files
  - _Requirements: 1.5, 2.5, 3.5_

- [ ] 4. Integrate checkpoint manager with main pipeline
  - Add checkpoint manager initialization in `run_book_pipeline.py` main function
  - Insert checkpoint call after Stage 4 completion for each book
  - Add finalization call after batch LSI generation
  - _Requirements: 1.1, 1.3, 4.1, 4.2, 4.3_

- [ ] 5. Add checkpoint support to batch processing
  - Modify `generate_lsi_csv.py` process_batch function to support checkpoints
  - Add optional checkpoint parameter to batch processing functions
  - Ensure checkpoint updates happen immediately after each book processing
  - _Requirements: 1.1, 1.3, 2.4, 4.1, 4.2_

- [ ] 6. Implement error handling and logging
  - Add comprehensive error handling that allows pipeline to continue on checkpoint failures
  - Integrate with existing logging system for checkpoint operations
  - Add warning messages for checkpoint failures without stopping pipeline
  - _Requirements: 3.1, 3.3, 4.4, 4.5_

- [-] 7. Create unit tests for checkpoint manager
  - Write tests for checkpoint file creation and naming
  - Test data appending functionality with sample CodexMetadata
  - Test error handling scenarios and atomic write operations
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.2_

- [ ] 8. Add integration tests for pipeline checkpoint functionality
  - Test end-to-end checkpoint creation during pipeline execution
  - Verify checkpoint files contain correct LSI data format
  - Test pipeline continuation after checkpoint errors
  - _Requirements: 1.4, 1.5, 2.5, 3.1_

- [ ] 9. Implement checkpoint file validation utilities
  - Create utility to verify checkpoint file completeness and format
  - Add method to compare checkpoint data with final batch LSI output
  - Implement checkpoint file analysis for recovery scenarios
  - _Requirements: 1.5, 2.2, 2.3_

- [ ] 10. Add configuration and command-line options
  - Add checkpoint enable/disable option to pipeline arguments
  - Integrate checkpoint directory configuration with existing config system
  - Add checkpoint-related logging configuration options
  - _Requirements: 2.4, 3.3, 4.1, 4.5_uv run python generate_lsi_csv.py --batch output/xynapse_traces_build/processed_json --output output/xynapse_traces_build/lsi_csv --tranche xynapse_tranche_1
