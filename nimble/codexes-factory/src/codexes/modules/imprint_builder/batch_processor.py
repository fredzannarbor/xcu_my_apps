"""
Main Batch Processor coordinator for imprint CSV batch processing.

This module coordinates all components to provide a unified interface
for batch processing of imprint concepts from CSV files and directories.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional, Union, Dict, Any

from .batch_models import (
    BatchConfig,
    BatchResult,
    ImprintRow,
    ProcessingError,
    ProcessingContext,
    create_default_config
)
from .csv_reader import CSVReader
from .directory_scanner import DirectoryScanner
from .batch_orchestrator import BatchOrchestrator
from .output_manager import OutputManager
from .error_handler import ErrorHandler


class BatchProcessor:
    """Main coordinator for batch processing of imprint concepts."""
    
    def __init__(self, llm_caller, config: Optional[BatchConfig] = None):
        """
        Initialize BatchProcessor.
        
        Args:
            llm_caller: LLM caller instance for processing
            config: Batch processing configuration (uses default if None)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm_caller = llm_caller
        self.config = config or create_default_config()
        
        # Initialize components
        self.csv_reader = CSVReader(self.config.column_mapping)
        self.directory_scanner = DirectoryScanner()
        self.orchestrator = BatchOrchestrator(llm_caller, self.config)
        self.output_manager = OutputManager(self.config.output_config)
        self.error_handler = ErrorHandler(self.config.error_handling)
        
        self.logger.info("Initialized BatchProcessor with all components")
    
    def process_csv_file(self, csv_path: Union[str, Path]) -> BatchResult:
        """
        Process a single CSV file containing imprint concepts.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            BatchResult with processing results
        """
        csv_path = Path(csv_path)
        self.logger.info(f"Processing CSV file: {csv_path}")
        
        # Initialize batch result
        batch_result = BatchResult(source_files=[csv_path])
        
        try:
            # Read CSV file
            context = ProcessingContext(
                operation="csv_reading",
                file_path=csv_path
            )
            
            try:
                imprint_rows = self.csv_reader.read_csv(csv_path)
                self.logger.info(f"Read {len(imprint_rows)} imprint concepts from CSV")
                
            except Exception as e:
                if not self.error_handler.handle_error(e, context):
                    # Critical error, cannot continue
                    batch_result.add_error(ProcessingError(
                        error_type="CSV_READING_FAILED",
                        message=f"Failed to read CSV file: {str(e)}",
                        context=context.to_dict(),
                        exception=e,
                        recoverable=False
                    ))
                    batch_result.finalize()
                    return batch_result
                else:
                    # Error was handled, but we can't continue without data
                    imprint_rows = []
            
            # Process the imprint concepts
            if imprint_rows:
                processing_result = self.orchestrator.process_batch(imprint_rows)
                
                # Merge results
                for result in processing_result.results:
                    batch_result.add_result(result)
                
                # Merge errors and warnings
                for error in processing_result.errors:
                    batch_result.add_error(error)
                
                for warning in processing_result.warnings:
                    batch_result.add_warning(warning)
                
                # Write output files
                try:
                    written_paths = self.output_manager.write_batch_results(batch_result)
                    self.logger.info(f"Wrote {len(written_paths)} output files")
                    
                except Exception as e:
                    output_context = ProcessingContext(
                        operation="output_writing",
                        file_path=csv_path
                    )
                    self.error_handler.handle_error(e, output_context)
            
            else:
                self.logger.warning("No imprint concepts found to process")
            
        except Exception as e:
            # Unexpected error
            error_context = ProcessingContext(
                operation="batch_processing",
                file_path=csv_path
            )
            
            batch_result.add_error(ProcessingError(
                error_type="UNEXPECTED_ERROR",
                message=f"Unexpected error during batch processing: {str(e)}",
                context=error_context.to_dict(),
                exception=e,
                recoverable=False
            ))
            
            self.logger.error(f"Unexpected error processing {csv_path}: {e}", exc_info=True)
        
        finally:
            batch_result.finalize()
            
            # Generate error report if configured
            if self.config.error_handling.create_error_report and self.error_handler.errors:
                error_report_path = self.config.output_config.base_directory / f"error_report_{csv_path.stem}.json"
                self.error_handler.save_error_report(error_report_path)
        
        self.logger.info(f"Completed processing {csv_path}: {batch_result.successful}/{batch_result.total_processed} successful")
        return batch_result
    
    def process_directory(self, directory_path: Union[str, Path]) -> BatchResult:
        """
        Process all CSV files in a directory.
        
        Args:
            directory_path: Path to directory containing CSV files
            
        Returns:
            BatchResult with processing results from all files
        """
        directory_path = Path(directory_path)
        self.logger.info(f"Processing directory: {directory_path}")
        
        # Initialize batch result
        batch_result = BatchResult(source_files=[])
        
        try:
            # Scan directory for CSV files
            context = ProcessingContext(
                operation="directory_scanning",
                file_path=directory_path
            )
            
            try:
                scan_result = self.directory_scanner.scan_for_csv_files(directory_path)
                
                if scan_result.errors:
                    for error_msg in scan_result.errors:
                        batch_result.add_error(ProcessingError(
                            error_type="DIRECTORY_SCAN_ERROR",
                            message=error_msg,
                            context=context.to_dict(),
                            recoverable=False
                        ))
                
                if not scan_result.csv_files:
                    self.logger.warning(f"No CSV files found in {directory_path}")
                    batch_result.finalize()
                    return batch_result
                
                self.logger.info(f"Found {len(scan_result.csv_files)} CSV files to process")
                batch_result.source_files = scan_result.csv_files
                
            except Exception as e:
                if not self.error_handler.handle_error(e, context):
                    batch_result.add_error(ProcessingError(
                        error_type="DIRECTORY_SCAN_FAILED",
                        message=f"Failed to scan directory: {str(e)}",
                        context=context.to_dict(),
                        exception=e,
                        recoverable=False
                    ))
                    batch_result.finalize()
                    return batch_result
                else:
                    # Error handled but no files to process
                    batch_result.finalize()
                    return batch_result
            
            # Process each CSV file
            all_imprint_rows = []
            
            for csv_file in scan_result.csv_files:
                try:
                    file_context = ProcessingContext(
                        operation="csv_reading",
                        file_path=csv_file
                    )
                    
                    imprint_rows = self.csv_reader.read_csv(csv_file)
                    all_imprint_rows.extend(imprint_rows)
                    
                    self.logger.info(f"Read {len(imprint_rows)} concepts from {csv_file.name}")
                    
                except Exception as e:
                    if not self.error_handler.handle_error(e, file_context):
                        # Critical error for this file
                        batch_result.add_error(ProcessingError(
                            error_type="CSV_FILE_FAILED",
                            message=f"Failed to process {csv_file.name}: {str(e)}",
                            context=file_context.to_dict(),
                            exception=e,
                            recoverable=True
                        ))
                    
                    # Continue with other files
                    continue
            
            # Process all imprint concepts together
            if all_imprint_rows:
                self.logger.info(f"Processing {len(all_imprint_rows)} total imprint concepts")
                
                processing_result = self.orchestrator.process_batch(all_imprint_rows)
                
                # Merge results
                for result in processing_result.results:
                    batch_result.add_result(result)
                
                for error in processing_result.errors:
                    batch_result.add_error(error)
                
                for warning in processing_result.warnings:
                    batch_result.add_warning(warning)
                
                # Write output files
                try:
                    written_paths = self.output_manager.write_batch_results(batch_result)
                    self.logger.info(f"Wrote {len(written_paths)} output files")
                    
                except Exception as e:
                    output_context = ProcessingContext(
                        operation="output_writing",
                        file_path=directory_path
                    )
                    self.error_handler.handle_error(e, output_context)
            
            else:
                self.logger.warning("No imprint concepts found in any CSV files")
        
        except Exception as e:
            # Unexpected error
            error_context = ProcessingContext(
                operation="directory_processing",
                file_path=directory_path
            )
            
            batch_result.add_error(ProcessingError(
                error_type="UNEXPECTED_ERROR",
                message=f"Unexpected error during directory processing: {str(e)}",
                context=error_context.to_dict(),
                exception=e,
                recoverable=False
            ))
            
            self.logger.error(f"Unexpected error processing directory {directory_path}: {e}", exc_info=True)
        
        finally:
            batch_result.finalize()
            
            # Generate error report if configured
            if self.config.error_handling.create_error_report and self.error_handler.errors:
                error_report_path = self.config.output_config.base_directory / f"error_report_{directory_path.name}.json"
                self.error_handler.save_error_report(error_report_path)
        
        self.logger.info(f"Completed processing directory {directory_path}: {batch_result.successful}/{batch_result.total_processed} successful")
        return batch_result
    
    def process_single_file(self, text_path: Union[str, Path]) -> BatchResult:
        """
        Process a single text file (backward compatibility).
        
        Args:
            text_path: Path to text file containing imprint concept
            
        Returns:
            BatchResult with single processing result
        """
        text_path = Path(text_path)
        self.logger.info(f"Processing single text file: {text_path}")
        
        # Initialize batch result
        batch_result = BatchResult(source_files=[text_path])
        
        try:
            # Read text file
            if not text_path.exists():
                raise FileNotFoundError(f"Text file not found: {text_path}")
            
            with open(text_path, 'r', encoding='utf-8') as f:
                concept_text = f.read().strip()
            
            if not concept_text:
                raise ValueError("Text file is empty")
            
            # Create imprint row
            imprint_row = ImprintRow(
                row_number=1,
                imprint_concept=concept_text,
                source_file=text_path,
                additional_data={"file_type": "text"}
            )
            
            # Process single imprint
            processing_result = self.orchestrator.process_batch([imprint_row])
            
            # Merge results
            for result in processing_result.results:
                batch_result.add_result(result)
            
            for error in processing_result.errors:
                batch_result.add_error(error)
            
            for warning in processing_result.warnings:
                batch_result.add_warning(warning)
            
            # Write output files
            try:
                written_paths = self.output_manager.write_batch_results(batch_result)
                self.logger.info(f"Wrote {len(written_paths)} output files")
                
            except Exception as e:
                output_context = ProcessingContext(
                    operation="output_writing",
                    file_path=text_path
                )
                self.error_handler.handle_error(e, output_context)
        
        except Exception as e:
            error_context = ProcessingContext(
                operation="single_file_processing",
                file_path=text_path
            )
            
            batch_result.add_error(ProcessingError(
                error_type="SINGLE_FILE_ERROR",
                message=f"Failed to process single file: {str(e)}",
                context=error_context.to_dict(),
                exception=e,
                recoverable=False
            ))
            
            self.logger.error(f"Error processing single file {text_path}: {e}")
        
        finally:
            batch_result.finalize()
        
        self.logger.info(f"Completed processing single file {text_path}: {batch_result.successful}/{batch_result.total_processed} successful")
        return batch_result
    
    def get_processing_summary(self, batch_result: BatchResult) -> Dict[str, Any]:
        """
        Get comprehensive processing summary.
        
        Args:
            batch_result: Batch processing result
            
        Returns:
            Summary dictionary with detailed information
        """
        # Get orchestrator stats
        orchestrator_stats = self.orchestrator.get_processing_stats(batch_result)
        
        # Get output summary
        output_summary = self.output_manager.get_output_summary(batch_result)
        
        # Get error summary
        error_summary = self.error_handler.get_error_summary()
        
        return {
            "processing": orchestrator_stats,
            "output": output_summary,
            "errors": error_summary,
            "configuration": {
                "naming_strategy": self.config.output_config.naming_strategy.value,
                "organization_strategy": self.config.output_config.organization_strategy.value,
                "error_handling_mode": self.config.error_handling.mode.value,
                "parallel_processing": self.config.processing_options.parallel_processing,
                "max_workers": self.config.processing_options.max_workers
            }
        }
    
    def validate_configuration(self) -> List[str]:
        """
        Validate the current configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        return self.config.validate()
    
    def clear_state(self):
        """Clear all processing state (errors, warnings, etc.)."""
        self.error_handler.clear_errors()
        self.logger.info("Cleared all processing state")


def create_batch_processor(llm_caller, config: Optional[BatchConfig] = None) -> BatchProcessor:
    """
    Factory function to create a BatchProcessor instance.
    
    Args:
        llm_caller: LLM caller instance
        config: Optional batch configuration
        
    Returns:
        Configured BatchProcessor instance
    """
    return BatchProcessor(llm_caller, config)