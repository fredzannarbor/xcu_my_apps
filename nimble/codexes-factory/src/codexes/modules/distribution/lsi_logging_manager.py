# src/codexes/modules/distribution/lsi_logging_manager.py

import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field, asdict

from ..metadata.metadata_models import CodexMetadata
from ..verifiers.validation_framework import ValidationResult, FieldValidationResult


@dataclass
class FieldMappingLog:
    """Log entry for a single field mapping operation"""
    field_name: str
    source_value: Any
    mapped_value: str
    mapping_strategy: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    processing_time_ms: float = 0.0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class ValidationLog:
    """Log entry for validation operations"""
    field_name: str
    is_valid: bool
    severity: str
    message: str
    suggested_value: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GenerationSession:
    """Complete log of an LSI generation session"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    total_duration_ms: float = 0.0
    
    # Source metadata summary
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Field mapping logs
    field_mappings: List[FieldMappingLog] = field(default_factory=list)
    
    # Validation logs
    validation_results: List[ValidationLog] = field(default_factory=list)
    
    # Performance metrics
    total_fields_processed: int = 0
    successful_mappings: int = 0
    failed_mappings: int = 0
    validation_errors: int = 0
    validation_warnings: int = 0
    
    # Generation outcome
    generation_successful: bool = False
    output_file_path: str = ""
    final_csv_size_bytes: int = 0
    
    # Error recovery
    recovery_attempts: List[Dict[str, Any]] = field(default_factory=list)
    
    # General logs
    info_messages: List[str] = field(default_factory=list)
    warning_messages: List[str] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)


class LSILoggingManager:
    """
    Comprehensive logging manager for LSI generation process.
    Provides structured logging, performance metrics, and detailed audit trails.
    """
    
    def __init__(self, log_directory: str = "logs/lsi_generation"):
        """
        Initialize the LSI logging manager.
        
        Args:
            log_directory: Directory to store detailed log files
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Current session
        self.current_session: Optional[GenerationSession] = None
        
        # Performance tracking
        self._operation_start_times: Dict[str, float] = {}
        
        # Configure structured logging
        self._setup_structured_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("LSI Logging Manager initialized")
    
    def _setup_structured_logging(self):
        """Setup structured logging configuration"""
        # Create formatter for structured logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler for LSI-specific logs
        log_file = self.log_directory / "lsi_generation.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Add handler to logger
        logger = logging.getLogger('lsi_generation')
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # Prevent duplicate logs
    
    def start_generation_session(self, metadata: CodexMetadata, output_path: str) -> str:
        """
        Start a new generation session with comprehensive logging.
        
        Args:
            metadata: Source metadata object
            output_path: Target output file path
            
        Returns:
            Session ID for tracking
        """
        session_id = f"lsi_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{metadata.shortuuid}"
        
        # Create new session
        self.current_session = GenerationSession(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            output_file_path=output_path
        )
        
        # Log source metadata summary
        self.current_session.source_metadata = {
            "title": metadata.title or "Unknown",
            "author": metadata.author or "Unknown", 
            "isbn13": metadata.isbn13 or "Unknown",
            "publisher": metadata.publisher or "Unknown",
            "imprint": metadata.imprint or "Unknown",
            "uuid": metadata.uuid,
            "shortuuid": metadata.shortuuid
        }
        
        # Log session start
        self.logger.info(f"Started LSI generation session: {session_id}")
        self.logger.info(f"Source metadata: {self.current_session.source_metadata}")
        self.logger.info(f"Target output: {output_path}")
        
        return session_id
    
    def log_field_mapping(self, field_name: str, source_value: Any, mapped_value: str, 
                         mapping_strategy: str, processing_time_ms: float = 0.0,
                         warnings: List[str] = None, errors: List[str] = None):
        """
        Log a field mapping operation with detailed information.
        
        Args:
            field_name: Name of the LSI field being mapped
            source_value: Original value from metadata
            mapped_value: Final mapped value
            mapping_strategy: Strategy used for mapping
            processing_time_ms: Time taken for mapping operation
            warnings: Any warnings generated during mapping
            errors: Any errors encountered during mapping
        """
        if not self.current_session:
            # Create a default session if one doesn't exist
            self.start_generation_session(None, "default_output.csv")
            self.logger.info("Created default logging session for field mapping")
        
        # Create field mapping log
        mapping_log = FieldMappingLog(
            field_name=field_name,
            source_value=source_value,
            mapped_value=mapped_value,
            mapping_strategy=mapping_strategy,
            processing_time_ms=processing_time_ms,
            warnings=warnings or [],
            errors=errors or []
        )
        
        # Add to session
        self.current_session.field_mappings.append(mapping_log)
        self.current_session.total_fields_processed += 1
        
        if errors:
            self.current_session.failed_mappings += 1
            self.logger.error(f"Field mapping failed for '{field_name}': {errors}")
        else:
            self.current_session.successful_mappings += 1
            self.logger.debug(f"Field mapped: '{field_name}' -> '{mapped_value}' ({mapping_strategy})")
        
        # Log warnings if any
        if warnings:
            for warning in warnings:
                self.logger.warning(f"Field mapping warning for '{field_name}': {warning}")
    
    def log_validation_result(self, field_result: FieldValidationResult):
        """
        Log validation result for a field.
        
        Args:
            field_result: Field validation result to log
        """
        if not self.current_session:
            self.logger.warning("No active session for validation log")
            return
        
        # Create validation log
        severity_str = field_result.severity.value if hasattr(field_result.severity, 'value') else str(field_result.severity)
        if hasattr(field_result.severity, 'name'):
            severity_str = field_result.severity.name
        
        validation_log = ValidationLog(
            field_name=field_result.field_name,
            is_valid=field_result.is_valid,
            severity=severity_str,
            message=field_result.error_message or field_result.warning_message or "Valid",
            suggested_value=getattr(field_result, 'suggested_value', None)
        )
        
        # Add to session
        self.current_session.validation_results.append(validation_log)
        
        # Update counters
        if not field_result.is_valid:
            self.current_session.validation_errors += 1
            self.logger.error(f"Validation error for '{field_result.field_name}': {validation_log.message}")
        elif hasattr(field_result, 'warning_message') and field_result.warning_message:
            self.current_session.validation_warnings += 1
            self.logger.warning(f"Validation warning for '{field_result.field_name}': {validation_log.message}")
        else:
            self.logger.debug(f"Field validation passed: '{field_result.field_name}'")
    
    def log_validation_summary(self, validation_result: ValidationResult):
        """
        Log overall validation summary.
        
        Args:
            validation_result: Complete validation result
        """
        if not self.current_session:
            self.logger.warning("No active session for validation summary")
            return
        
        # Log individual field results
        for field_result in validation_result.field_results:
            self.log_validation_result(field_result)
        
        # Log overall summary
        self.logger.info(f"Validation summary - Valid: {validation_result.is_valid}, "
                        f"Errors: {len(validation_result.errors)}, "
                        f"Warnings: {len(validation_result.warnings)}")
        
        # Log specific errors and warnings
        for error in validation_result.errors:
            self.logger.error(f"Validation error: {error}")
            self.current_session.error_messages.append(f"Validation: {error}")
        
        for warning in validation_result.warnings:
            self.logger.warning(f"Validation warning: {warning}")
            self.current_session.warning_messages.append(f"Validation: {warning}")
    
    def log_error_recovery_attempt(self, field_name: str, original_value: Any, 
                                  corrected_value: Any, recovery_method: str):
        """
        Log error recovery attempts.
        
        Args:
            field_name: Field that was corrected
            original_value: Original incorrect value
            corrected_value: Corrected value
            recovery_method: Method used for recovery
        """
        if not self.current_session:
            self.logger.warning("No active session for error recovery log")
            return
        
        recovery_log = {
            "field_name": field_name,
            "original_value": str(original_value),
            "corrected_value": str(corrected_value),
            "recovery_method": recovery_method,
            "timestamp": datetime.now().isoformat()
        }
        
        self.current_session.recovery_attempts.append(recovery_log)
        
        self.logger.info(f"Error recovery applied to '{field_name}': "
                        f"{original_value} -> {corrected_value} ({recovery_method})")
    
    def start_operation_timing(self, operation_name: str):
        """Start timing an operation for performance metrics."""
        self._operation_start_times[operation_name] = time.time()
    
    def end_operation_timing(self, operation_name: str) -> float:
        """
        End timing an operation and return duration.
        
        Args:
            operation_name: Name of the operation being timed
            
        Returns:
            Duration in milliseconds
        """
        if operation_name not in self._operation_start_times:
            self.logger.warning(f"No start time recorded for operation: {operation_name}")
            return 0.0
        
        start_time = self._operation_start_times.pop(operation_name)
        duration_ms = (time.time() - start_time) * 1000
        
        self.logger.debug(f"Operation '{operation_name}' completed in {duration_ms:.2f}ms")
        return duration_ms
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "ms"):
        """
        Log a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
        """
        self.logger.info(f"Performance metric - {metric_name}: {value:.2f}{unit}")
    
    def log_info(self, message: str):
        """Log an informational message."""
        self.logger.info(message)
        if self.current_session:
            self.current_session.info_messages.append(message)
    
    def log_warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)
        if self.current_session:
            self.current_session.warning_messages.append(message)
    
    def log_error(self, message: str):
        """Log an error message."""
        self.logger.error(message)
        if self.current_session:
            self.current_session.error_messages.append(message)
    
    def complete_generation_session(self, success: bool, final_file_size: int = 0):
        """
        Complete the current generation session with final metrics.
        
        Args:
            success: Whether generation was successful
            final_file_size: Size of generated file in bytes
        """
        if not self.current_session:
            self.logger.warning("No active session to complete")
            return
        
        # Update session completion info
        self.current_session.end_time = datetime.now().isoformat()
        self.current_session.generation_successful = success
        self.current_session.final_csv_size_bytes = final_file_size
        
        # Calculate total duration
        start_time = datetime.fromisoformat(self.current_session.start_time)
        end_time = datetime.fromisoformat(self.current_session.end_time)
        self.current_session.total_duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Log completion summary
        self.logger.info(f"Generation session completed: {self.current_session.session_id}")
        self.logger.info(f"Success: {success}, Duration: {self.current_session.total_duration_ms:.2f}ms")
        self.logger.info(f"Fields processed: {self.current_session.total_fields_processed}")
        self.logger.info(f"Successful mappings: {self.current_session.successful_mappings}")
        self.logger.info(f"Failed mappings: {self.current_session.failed_mappings}")
        self.logger.info(f"Validation errors: {self.current_session.validation_errors}")
        self.logger.info(f"Validation warnings: {self.current_session.validation_warnings}")
        self.logger.info(f"Recovery attempts: {len(self.current_session.recovery_attempts)}")
        
        # Save detailed session log to file
        self._save_session_log()
        
        # Clear current session
        self.current_session = None
    
    def _save_session_log(self):
        """Save detailed session log to JSON file."""
        if not self.current_session:
            return
        
        try:
            # Create session log file
            log_filename = f"{self.current_session.session_id}.json"
            log_file_path = self.log_directory / log_filename
            
            # Convert session to dictionary
            session_dict = asdict(self.current_session)
            
            # Save to JSON file
            with open(log_file_path, 'w', encoding='utf-8') as f:
                json.dump(session_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Detailed session log saved: {log_file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save session log: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current session.
        
        Returns:
            Dictionary with session summary
        """
        if not self.current_session:
            return {}
        
        return {
            "session_id": self.current_session.session_id,
            "start_time": self.current_session.start_time,
            "source_metadata": self.current_session.source_metadata,
            "fields_processed": self.current_session.total_fields_processed,
            "successful_mappings": self.current_session.successful_mappings,
            "failed_mappings": self.current_session.failed_mappings,
            "validation_errors": self.current_session.validation_errors,
            "validation_warnings": self.current_session.validation_warnings,
            "recovery_attempts": len(self.current_session.recovery_attempts)
        }
    
    def get_field_mapping_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about field mappings in current session.
        
        Returns:
            Dictionary with mapping statistics
        """
        if not self.current_session:
            return {}
        
        # Analyze mapping strategies
        strategy_counts = {}
        total_processing_time = 0.0
        
        for mapping in self.current_session.field_mappings:
            strategy = mapping.mapping_strategy
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            total_processing_time += mapping.processing_time_ms
        
        # Find most common strategies
        sorted_strategies = sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_mappings": len(self.current_session.field_mappings),
            "strategy_distribution": dict(sorted_strategies),
            "total_processing_time_ms": total_processing_time,
            "average_processing_time_ms": total_processing_time / len(self.current_session.field_mappings) if self.current_session.field_mappings else 0,
            "most_used_strategy": sorted_strategies[0][0] if sorted_strategies else None
        }
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about validation results in current session.
        
        Returns:
            Dictionary with validation statistics
        """
        if not self.current_session:
            return {}
        
        # Analyze validation results by severity
        severity_counts = {}
        fields_with_suggestions = 0
        
        for validation in self.current_session.validation_results:
            severity = validation.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            if validation.suggested_value:
                fields_with_suggestions += 1
        
        return {
            "total_validations": len(self.current_session.validation_results),
            "severity_distribution": severity_counts,
            "fields_with_suggestions": fields_with_suggestions,
            "error_rate": self.current_session.validation_errors / len(self.current_session.validation_results) if self.current_session.validation_results else 0,
            "warning_rate": self.current_session.validation_warnings / len(self.current_session.validation_results) if self.current_session.validation_results else 0
        }
    
    @classmethod
    def load_session_log(cls, log_file_path: str) -> Optional[GenerationSession]:
        """
        Load a session log from file.
        
        Args:
            log_file_path: Path to the session log file
            
        Returns:
            GenerationSession object or None if loading fails
        """
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Convert back to GenerationSession
            # Note: This is a simplified conversion - in production you might want
            # to handle nested dataclass conversion more robustly
            session = GenerationSession(**session_data)
            return session
            
        except Exception as e:
            logging.error(f"Failed to load session log from {log_file_path}: {e}")
            return None