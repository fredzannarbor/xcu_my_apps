# Design Document

## Overview

The LSI checkpoint system will provide resilient batch processing by maintaining cumulative LSI CSV files during pipeline execution. The system will integrate seamlessly with the existing book pipeline architecture, adding minimal overhead while ensuring data recovery capabilities for interrupted batch runs.

The design follows the principle of minimal code changes, leveraging existing patterns and infrastructure in the codebase. The checkpoint system will be implemented as a lightweight wrapper around existing LSI generation functionality.

## Architecture

### Core Components

The checkpoint system consists of three main components:

1. **Checkpoint Manager**: Handles cumulative file creation and updates
2. **Pipeline Integration**: Minimal modifications to existing pipeline stages
3. **Recovery Utilities**: Optional tools for checkpoint file management

### Integration Points

The system integrates at two key points in the existing pipeline:

- **Individual Book Processing** (Stage 4): After each book's LSI metadata is prepared
- **Batch LSI Generation**: During the final batch CSV creation process

## Components and Interfaces

### 1. Checkpoint Manager

```python
class LSICheckpointManager:
    """Manages cumulative LSI CSV checkpoint files during batch processing."""
    
    def __init__(self, checkpoint_dir: str = "data"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.current_checkpoint_file = None
        self.headers_written = False
    
    def create_checkpoint_file(self, imprint: str) -> Path:
        """Create a new timestamped checkpoint file."""
        
    def append_book_data(self, metadata: CodexMetadata) -> bool:
        """Append a single book's LSI data to the checkpoint file."""
        
    def finalize_checkpoint(self) -> bool:
        """Mark checkpoint as complete and optionally clean up."""
```

### 2. Pipeline Integration

The integration will be implemented through minimal code additions to existing functions:

**In `run_book_pipeline.py`:**
- Initialize checkpoint manager at batch start
- Add checkpoint call after each book's Stage 4 completion
- Finalize checkpoint after batch LSI generation

**In `generate_lsi_csv.py`:**
- Optional checkpoint support in batch processing function

### 3. File Management

**Checkpoint File Naming Convention:**
```
data/cumulative_checkpoint_YYYYMMDD_HHMM_{imprint}.csv
```

**File Structure:**
- Same CSV format as final batch LSI files
- Headers written once at file creation
- Data rows appended atomically for each processed book

## Data Models

### Checkpoint File Format

The checkpoint files will use the identical CSV structure as the existing LSI batch files:

```csv
Title,Author,ISBN13,Publisher,Publication Date,...[all LSI fields]
"Book Title 1","Author Name","9781234567890","Publisher Name","2025-03-15",...
"Book Title 2","Author Name","9781234567891","Publisher Name","2025-04-15",...
```

### Checkpoint Metadata

Each checkpoint operation will track:

```python
@dataclass
class CheckpointInfo:
    file_path: Path
    books_processed: int
    last_updated: datetime
    imprint: str
    pipeline_id: str
```

## Error Handling

### Graceful Degradation

The checkpoint system is designed to fail gracefully:

1. **File I/O Errors**: Log warnings but continue pipeline execution
2. **Disk Space Issues**: Detect and warn, but don't halt processing
3. **Permission Errors**: Fall back to pipeline-only mode

### Atomic Operations

All checkpoint file updates use atomic write operations:

1. Write to temporary file with `.tmp` extension
2. Validate write completion
3. Atomically rename to final checkpoint file
4. Handle concurrent access through file locking

### Error Recovery

```python
def safe_checkpoint_append(self, metadata: CodexMetadata) -> bool:
    """Safely append data with error handling."""
    try:
        temp_file = self.current_checkpoint_file.with_suffix('.tmp')
        # Atomic write operation
        with file_lock(self.current_checkpoint_file):
            # Write logic here
            temp_file.rename(self.current_checkpoint_file)
        return True
    except Exception as e:
        logger.warning(f"Checkpoint append failed: {e}")
        return False
```

## Testing Strategy

### Unit Tests

1. **Checkpoint Manager Tests**:
   - File creation and naming
   - Data appending functionality
   - Error handling scenarios
   - Atomic write operations

2. **Integration Tests**:
   - Pipeline integration points
   - End-to-end checkpoint creation
   - Recovery from interrupted runs

### Test Data

- Sample CodexMetadata objects
- Mock file system scenarios
- Simulated pipeline interruptions
- Various error conditions

### Performance Tests

- Checkpoint overhead measurement
- Large batch processing validation
- Concurrent access testing
- File size growth analysis

## Implementation Details

### Minimal Code Changes

The implementation follows the requirement for minimal code changes:

**Code Snippet Additions** (preferred):
```python
# In run_book_pipeline.py - main() function
checkpoint_manager = LSICheckpointManager("data") if not args.skip_lsi else None

# After Stage 4 completion for each book
if checkpoint_manager and book_summary.get("lsi_ready"):
    checkpoint_manager.append_book_data(book_summary["lsi_metadata"])
```

**New Method Addition** (if needed):
```python
# In existing LsiAcsGenerator class
def append_to_checkpoint(self, metadata: CodexMetadata, checkpoint_file: Path) -> bool:
    """Append single book data to checkpoint file."""
```

### File I/O Patterns

Reuse existing patterns from the codebase:
- CSV writing utilities from `LsiAcsGenerator`
- File path handling from existing pipeline code
- Logging patterns from `logging_config.py`
- Error handling from existing modules

### Configuration Integration

Leverage existing configuration systems:
- Use existing `data/` directory structure
- Integrate with imprint-specific settings
- Respect existing file naming conventions
- Follow established logging practices

## Performance Considerations

### Overhead Analysis

The checkpoint system adds minimal overhead:
- Single file append per book (< 1ms typical)
- No additional LLM calls or processing
- Reuses existing CSV generation logic
- Optional feature that can be disabled

### Scalability

The design scales with existing pipeline capabilities:
- Linear file growth with book count
- No memory accumulation (streaming writes)
- Efficient for batches of 10-1000+ books
- Disk space requirements: ~1KB per book

### Optimization Strategies

1. **Buffered Writes**: Group multiple books for batch writing if needed
2. **Compression**: Optional gzip compression for large checkpoints
3. **Cleanup**: Automatic removal of old checkpoint files
4. **Monitoring**: Integration with existing logging and monitoring

## Security and Data Integrity

### File Permissions

Checkpoint files inherit security from the `data/` directory:
- Standard file system permissions
- No additional security requirements
- Compatible with existing backup systems

### Data Validation

Checkpoint data validation reuses existing mechanisms:
- LSI field validation from `LsiAcsGenerator`
- Metadata validation from `CodexMetadata`
- CSV format validation from existing utilities

### Backup Integration

Checkpoint files integrate with existing backup strategies:
- Located in standard `data/` directory
- Standard CSV format for easy recovery
- Compatible with existing archival processes