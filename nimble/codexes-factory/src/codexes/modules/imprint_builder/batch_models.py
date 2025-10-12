"""
Data models for batch processing of imprint concepts.

This module contains all the dataclasses and configuration models needed
for CSV batch processing and directory scanning functionality.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class NamingStrategy(Enum):
    """Output file naming strategies."""
    IMPRINT_NAME = "imprint_name"
    ROW_NUMBER = "row_number"
    HYBRID = "hybrid"


class OrganizationStrategy(Enum):
    """Output directory organization strategies."""
    FLAT = "flat"
    BY_SOURCE = "by_source"
    BY_IMPRINT = "by_imprint"


class ErrorHandlingMode(Enum):
    """Error handling modes for batch processing."""
    FAIL_FAST = "fail_fast"
    CONTINUE_ON_ERROR = "continue_on_error"
    COLLECT_ERRORS = "collect_errors"


@dataclass
class ProcessingOptions:
    """Configuration for processing behavior."""
    parallel_processing: bool = False
    max_workers: int = 4
    continue_on_error: bool = True
    validate_output: bool = True
    timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class ErrorHandlingConfig:
    """Configuration for error handling behavior."""
    mode: ErrorHandlingMode = ErrorHandlingMode.CONTINUE_ON_ERROR
    log_level: str = "INFO"
    create_error_report: bool = True
    include_stack_traces: bool = False
    max_errors_per_file: int = 100


@dataclass
class OutputConfig:
    """Configuration for output file organization."""
    base_directory: Path = field(default_factory=lambda: Path("output"))
    naming_strategy: NamingStrategy = NamingStrategy.IMPRINT_NAME
    organization_strategy: OrganizationStrategy = OrganizationStrategy.BY_SOURCE
    create_index: bool = True
    overwrite_existing: bool = False
    create_subdirectories: bool = True
    
    def __post_init__(self):
        """Ensure base_directory is a Path object."""
        if isinstance(self.base_directory, str):
            self.base_directory = Path(self.base_directory)


@dataclass
class BatchConfig:
    """Main configuration for batch processing."""
    column_mapping: Dict[str, str] = field(default_factory=dict)
    attributes: Optional[List[str]] = None
    subattributes: Optional[List[str]] = None
    output_config: OutputConfig = field(default_factory=OutputConfig)
    error_handling: ErrorHandlingConfig = field(default_factory=ErrorHandlingConfig)
    processing_options: ProcessingOptions = field(default_factory=ProcessingOptions)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of validation errors."""
        errors = []
        
        # Validate column mapping
        if not isinstance(self.column_mapping, dict):
            errors.append("column_mapping must be a dictionary")
        
        # Validate attributes
        if self.attributes is not None:
            if not isinstance(self.attributes, list):
                errors.append("attributes must be a list or None")
            elif not all(isinstance(attr, str) for attr in self.attributes):
                errors.append("all attributes must be strings")
        
        # Validate subattributes
        if self.subattributes is not None:
            if not isinstance(self.subattributes, list):
                errors.append("subattributes must be a list or None")
            elif not all(isinstance(attr, str) for attr in self.subattributes):
                errors.append("all subattributes must be strings")
        
        # Validate output directory
        if not self.output_config.base_directory.parent.exists():
            errors.append(f"Parent directory of output path does not exist: {self.output_config.base_directory.parent}")
        
        # Validate processing options
        if self.processing_options.max_workers < 1:
            errors.append("max_workers must be at least 1")
        
        if self.processing_options.timeout_seconds < 1:
            errors.append("timeout_seconds must be at least 1")
        
        return errors


@dataclass
class SourceInfo:
    """Information about the source of an imprint concept."""
    file_path: Path
    file_name: str
    row_number: int
    total_rows: int
    
    def __post_init__(self):
        """Ensure file_path is a Path object."""
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)


@dataclass
class ImprintRow:
    """Represents a single row from CSV containing imprint concept data."""
    row_number: int
    imprint_concept: str
    source_file: Path
    additional_data: Dict[str, Any] = field(default_factory=dict)
    mapped_columns: Dict[str, str] = field(default_factory=dict)
    source_info: Optional[SourceInfo] = None
    
    def __post_init__(self):
        """Ensure source_file is a Path object and create source_info if needed."""
        if isinstance(self.source_file, str):
            self.source_file = Path(self.source_file)
        
        if self.source_info is None:
            self.source_info = SourceInfo(
                file_path=self.source_file,
                file_name=self.source_file.name,
                row_number=self.row_number,
                total_rows=1  # Will be updated by processor
            )
    
    def get_display_name(self) -> str:
        """Get a display name for this imprint row."""
        # Try to extract imprint name from concept or use row number
        concept_words = self.imprint_concept.split()[:3]
        if concept_words:
            return "_".join(word.lower().replace(" ", "_") for word in concept_words)
        return f"imprint_row_{self.row_number}"


@dataclass
class ProcessingError:
    """Represents an error that occurred during processing."""
    error_type: str
    message: str
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    exception: Optional[Exception] = None
    recoverable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable,
            "exception_type": type(self.exception).__name__ if self.exception else None
        }


@dataclass
class ProcessingWarning:
    """Represents a warning that occurred during processing."""
    message: str
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ImprintResult:
    """Result of processing a single imprint concept."""
    row: ImprintRow
    expanded_imprint: Optional[Any] = None  # ExpandedImprint from existing module
    success: bool = False
    error: Optional[Exception] = None
    processing_time: float = 0.0
    output_path: Optional[Path] = None
    warnings: List[ProcessingWarning] = field(default_factory=list)
    
    def __post_init__(self):
        """Ensure output_path is a Path object if provided."""
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "row_number": self.row.row_number,
            "source_file": str(self.row.source_file),
            "success": self.success,
            "processing_time": self.processing_time,
            "output_path": str(self.output_path) if self.output_path else None,
            "error": str(self.error) if self.error else None,
            "warnings": [w.to_dict() for w in self.warnings],
            "imprint_name": getattr(self.expanded_imprint, 'branding', {}).get('imprint_name', 'Unknown') if self.expanded_imprint else None
        }


@dataclass
class ValidationResult:
    """Result of validating CSV structure or configuration."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.valid = False
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)


@dataclass
class ProcessingPlan:
    """Plan for processing multiple CSV files."""
    csv_files: List[Path]
    estimated_rows: int = 0
    processing_order: List[Path] = field(default_factory=list)
    total_files: int = field(init=False)
    
    def __post_init__(self):
        """Initialize processing order and total files if not provided."""
        if not self.processing_order:
            self.processing_order = sorted(self.csv_files)
        self.total_files = len(self.csv_files)


@dataclass
class BatchResult:
    """Result of processing a batch of imprint concepts."""
    source_files: List[Path]
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    results: List[ImprintResult] = field(default_factory=list)
    errors: List[ProcessingError] = field(default_factory=list)
    warnings: List[ProcessingWarning] = field(default_factory=list)
    processing_time: float = 0.0
    index_file: Optional[Path] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Ensure all paths are Path objects."""
        self.source_files = [Path(f) if isinstance(f, str) else f for f in self.source_files]
        if isinstance(self.index_file, str):
            self.index_file = Path(self.index_file)
    
    def add_result(self, result: ImprintResult):
        """Add a processing result and update counters."""
        self.results.append(result)
        self.total_processed += 1
        if result.success:
            self.successful += 1
        else:
            self.failed += 1
    
    def add_error(self, error: ProcessingError):
        """Add a processing error."""
        self.errors.append(error)
    
    def add_warning(self, warning: ProcessingWarning):
        """Add a processing warning."""
        self.warnings.append(warning)
    
    def finalize(self):
        """Finalize the batch result by setting end time."""
        self.end_time = datetime.now()
        if self.start_time:
            self.processing_time = (self.end_time - self.start_time).total_seconds()
    
    def get_success_rate(self) -> float:
        """Get the success rate as a percentage."""
        if self.total_processed == 0:
            return 0.0
        return (self.successful / self.total_processed) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source_files": [str(f) for f in self.source_files],
            "total_processed": self.total_processed,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": self.get_success_rate(),
            "processing_time": self.processing_time,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "index_file": str(self.index_file) if self.index_file else None,
            "results": [r.to_dict() for r in self.results],
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings]
        }


@dataclass
class ProcessingContext:
    """Context information for error handling and logging."""
    operation: str
    file_path: Optional[Path] = None
    row_number: Optional[int] = None
    imprint_name: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure file_path is a Path object if provided."""
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "operation": self.operation,
            "file_path": str(self.file_path) if self.file_path else None,
            "row_number": self.row_number,
            "imprint_name": self.imprint_name,
            **self.additional_info
        }


def create_default_config() -> BatchConfig:
    """Create a default batch configuration."""
    return BatchConfig(
        column_mapping={
            "concept": "imprint_concept",
            "description": "imprint_concept",
            "imprint_concept": "imprint_concept"
        },
        output_config=OutputConfig(
            base_directory=Path("output/batch_processing"),
            naming_strategy=NamingStrategy.IMPRINT_NAME,
            organization_strategy=OrganizationStrategy.BY_SOURCE,
            create_index=True
        ),
        processing_options=ProcessingOptions(
            continue_on_error=True,
            validate_output=True,
            timeout_seconds=300
        )
    )


def validate_config(config: BatchConfig) -> ValidationResult:
    """Validate a batch configuration."""
    result = ValidationResult(valid=True)
    
    try:
        errors = config.validate()
        for error in errors:
            result.add_error(error)
    except Exception as e:
        result.add_error(f"Configuration validation failed: {str(e)}")
    
    return result