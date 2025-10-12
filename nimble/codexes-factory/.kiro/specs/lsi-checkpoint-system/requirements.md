# Requirements Document

## Introduction

The book pipeline currently saves individual LSI CSV files to the `data/` directory with timestamps, but does not maintain a cumulative "results so far" file during batch processing. When the pipeline is interrupted, users lose access to the LSI data for all books processed before the interruption, as only individual book CSV files exist rather than a consolidated batch file. This creates a significant data recovery problem for large batch runs.

## Requirements

### Requirement 1

**User Story:** As a publisher running large batch jobs, I want the pipeline to save cumulative LSI CSV checkpoints during processing, so that I can recover all processed LSI data if the pipeline is interrupted.

#### Acceptance Criteria

1. WHEN the pipeline processes each book THEN the system SHALL append the LSI data to a cumulative checkpoint file
2. WHEN the pipeline starts a batch run THEN the system SHALL create a new timestamped cumulative checkpoint file in the `data/` directory
3. WHEN the pipeline processes a book successfully THEN the system SHALL immediately update the cumulative checkpoint file with that book's LSI data
4. WHEN the pipeline is interrupted THEN the cumulative checkpoint file SHALL contain all LSI data for books processed up to that point
5. WHEN the pipeline completes successfully THEN the final cumulative checkpoint file SHALL contain the same data as the batch LSI file in the build directory

### Requirement 2

**User Story:** As a publisher recovering from an interrupted pipeline run, I want to easily identify and access the most recent cumulative LSI data, so that I can continue my workflow without losing processed data.

#### Acceptance Criteria

1. WHEN cumulative checkpoint files are created THEN they SHALL use a clear naming convention like `cumulative_checkpoint_YYYYMMDD_HHMM.csv`
2. WHEN multiple checkpoint files exist THEN users SHALL be able to identify the most recent one by timestamp
3. WHEN the pipeline resumes after interruption THEN it SHALL optionally detect and use existing checkpoint data to avoid reprocessing
4. WHEN checkpoint files are created THEN they SHALL be saved in the same `data/` directory as individual book CSV files
5. WHEN checkpoint files are created THEN they SHALL use the same CSV format and column structure as the final batch LSI files

### Requirement 3

**User Story:** As a system administrator, I want the checkpoint system to be robust and not impact pipeline performance, so that batch processing remains efficient while gaining resilience.

#### Acceptance Criteria

1. WHEN checkpoint files are updated THEN the system SHALL handle file I/O errors gracefully without stopping the pipeline
2. WHEN checkpoint files are written THEN the system SHALL use atomic write operations to prevent corruption
3. WHEN the pipeline processes books THEN checkpoint file updates SHALL not significantly impact processing speed
4. WHEN checkpoint files grow large THEN the system SHALL handle file size efficiently
5. WHEN checkpoint files are created THEN they SHALL include proper CSV headers and formatting for immediate use

### Requirement 4

**User Story:** As a developer and system administrator, I want the checkpoint system implementation to be minimal and non-intrusive, so that code maintainability is preserved and system complexity is minimized.

#### Acceptance Criteria

1. WHEN implementing checkpoint functionality THEN the system SHALL prefer code snippets over new methods
2. WHEN new functionality is required THEN the system SHALL prefer new methods over new classes
3. WHEN modifying existing code THEN the system SHALL minimize changes to existing method signatures
4. WHEN adding checkpoint features THEN the system SHALL reuse existing file I/O patterns and utilities
5. WHEN integrating with the pipeline THEN the system SHALL use existing error handling and logging mechanisms