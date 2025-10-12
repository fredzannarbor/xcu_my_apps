"""
Batch Orchestrator component for coordinating imprint processing pipeline.

This module handles the coordination of batch processing, including
integration with existing ImprintExpander, attribute filtering,
and progress tracking.
"""

import logging
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .batch_models import (
    BatchConfig,
    ImprintRow,
    ImprintResult,
    BatchResult,
    ProcessingError,
    ProcessingWarning,
    ProcessingContext
)
from .imprint_expander import ImprintExpander, ExpandedImprint
from .imprint_concept import ImprintConcept, ImprintConceptParser

# Try to import enhanced expander if available
try:
    from tools.enhanced_imprint_expander import EnhancedImprintExpander
    ENHANCED_EXPANDER_AVAILABLE = True
except ImportError:
    ENHANCED_EXPANDER_AVAILABLE = False


class BatchOrchestrator:
    """Coordinates the batch processing pipeline for imprint concepts."""
    
    def __init__(self, llm_caller, config: BatchConfig):
        """
        Initialize BatchOrchestrator.
        
        Args:
            llm_caller: LLM caller instance for processing
            config: Batch processing configuration
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm_caller = llm_caller
        self.config = config
        
        # Create expander instance
        self.expander = self._create_expander(llm_caller)
        self.concept_parser = ImprintConceptParser(llm_caller)
        
        self.logger.info(f"Initialized BatchOrchestrator with {type(self.expander).__name__}")
    
    def _create_expander(self, llm_caller):
        """
        Create appropriate expander instance based on availability.
        
        Args:
            llm_caller: LLM caller instance
            
        Returns:
            Expander instance (Enhanced or standard)
        """
        if ENHANCED_EXPANDER_AVAILABLE:
            try:
                expander = EnhancedImprintExpander(llm_caller)
                self.logger.info("Using EnhancedImprintExpander")
                return expander
            except Exception as e:
                self.logger.warning(f"Failed to create EnhancedImprintExpander: {e}, falling back to standard")
        
        # Fall back to standard expander
        expander = ImprintExpander(llm_caller)
        self.logger.info("Using standard ImprintExpander")
        return expander
    
    def process_batch(self, imprint_rows: List[ImprintRow]) -> BatchResult:
        """
        Process a batch of imprint concepts.
        
        Args:
            imprint_rows: List of imprint rows to process
            
        Returns:
            BatchResult with processing results
        """
        self.logger.info(f"Starting batch processing of {len(imprint_rows)} imprint concepts")
        
        # Initialize batch result
        source_files = list(set(row.source_file for row in imprint_rows))
        batch_result = BatchResult(source_files=source_files)
        
        start_time = time.time()
        
        try:
            if self.config.processing_options.parallel_processing and len(imprint_rows) > 1:
                results = self._process_batch_parallel(imprint_rows, batch_result)
            else:
                results = self._process_batch_sequential(imprint_rows, batch_result)
            
            # Add all results to batch result
            for result in results:
                batch_result.add_result(result)
            
        except Exception as e:
            error = ProcessingError(
                error_type="BATCH_PROCESSING",
                message=f"Batch processing failed: {str(e)}",
                context={"total_rows": len(imprint_rows)},
                exception=e,
                recoverable=False
            )
            batch_result.add_error(error)
            self.logger.error(f"Batch processing failed: {e}", exc_info=True)
        
        finally:
            batch_result.finalize()
            processing_time = time.time() - start_time
            
            self.logger.info(
                f"Batch processing complete: {batch_result.successful}/{batch_result.total_processed} successful "
                f"in {processing_time:.2f}s"
            )
        
        return batch_result
    
    def _process_batch_sequential(self, imprint_rows: List[ImprintRow], batch_result: BatchResult) -> List[ImprintResult]:
        """
        Process imprint rows sequentially.
        
        Args:
            imprint_rows: List of imprint rows to process
            batch_result: Batch result to update with progress
            
        Returns:
            List of processing results
        """
        results = []
        
        for i, row in enumerate(imprint_rows, 1):
            self.logger.info(f"Processing imprint {i}/{len(imprint_rows)}: {row.get_display_name()}")
            
            try:
                result = self.process_single_imprint(row)
                results.append(result)
                
                # Log progress
                if i % 10 == 0 or i == len(imprint_rows):
                    success_count = sum(1 for r in results if r.success)
                    self.logger.info(f"Progress: {i}/{len(imprint_rows)} processed, {success_count} successful")
                
            except Exception as e:
                # Create failed result
                error_result = ImprintResult(
                    row=row,
                    success=False,
                    error=e,
                    processing_time=0.0
                )
                results.append(error_result)
                
                self.logger.error(f"Failed to process imprint {row.get_display_name()}: {e}")
                
                # Check if we should continue on error
                if not self.config.processing_options.continue_on_error:
                    self.logger.error("Stopping batch processing due to error")
                    break
        
        return results
    
    def _process_batch_parallel(self, imprint_rows: List[ImprintRow], batch_result: BatchResult) -> List[ImprintResult]:
        """
        Process imprint rows in parallel.
        
        Args:
            imprint_rows: List of imprint rows to process
            batch_result: Batch result to update with progress
            
        Returns:
            List of processing results
        """
        results = []
        max_workers = min(self.config.processing_options.max_workers, len(imprint_rows))
        
        self.logger.info(f"Processing {len(imprint_rows)} imprints with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_row = {
                executor.submit(self.process_single_imprint, row): row 
                for row in imprint_rows
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_row):
                row = future_to_row[future]
                completed += 1
                
                try:
                    result = future.result(timeout=self.config.processing_options.timeout_seconds)
                    results.append(result)
                    
                    if result.success:
                        self.logger.debug(f"Successfully processed: {row.get_display_name()}")
                    else:
                        self.logger.warning(f"Failed to process: {row.get_display_name()}")
                    
                except Exception as e:
                    # Create failed result
                    error_result = ImprintResult(
                        row=row,
                        success=False,
                        error=e,
                        processing_time=0.0
                    )
                    results.append(error_result)
                    
                    self.logger.error(f"Exception processing {row.get_display_name()}: {e}")
                
                # Log progress
                if completed % 10 == 0 or completed == len(imprint_rows):
                    success_count = sum(1 for r in results if r.success)
                    self.logger.info(f"Progress: {completed}/{len(imprint_rows)} completed, {success_count} successful")
        
        return results
    
    def process_single_imprint(self, row: ImprintRow) -> ImprintResult:
        """
        Process a single imprint concept.
        
        Args:
            row: Imprint row to process
            
        Returns:
            ImprintResult with processing outcome
        """
        start_time = time.time()
        warnings = []
        
        try:
            # Parse the imprint concept
            concept = self._parse_imprint_concept(row)
            
            # Expand the concept
            expanded_imprint = self._expand_concept(concept, row)
            
            # Apply attribute filtering if configured
            if self.config.attributes or self.config.subattributes:
                expanded_imprint = self.apply_attribute_filtering(expanded_imprint)
                if not self._has_meaningful_content(expanded_imprint):
                    warnings.append(ProcessingWarning(
                        message="Attribute filtering removed most content",
                        context={"row": row.row_number, "file": str(row.source_file)}
                    ))
            
            processing_time = time.time() - start_time
            
            result = ImprintResult(
                row=row,
                expanded_imprint=expanded_imprint,
                success=True,
                processing_time=processing_time,
                warnings=warnings
            )
            
            self.logger.debug(f"Successfully processed imprint in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            result = ImprintResult(
                row=row,
                success=False,
                error=e,
                processing_time=processing_time,
                warnings=warnings
            )
            
            self.logger.error(f"Failed to process imprint: {e}")
            return result
    
    def _parse_imprint_concept(self, row: ImprintRow) -> ImprintConcept:
        """
        Parse imprint concept from row data.
        
        Args:
            row: Imprint row containing concept text
            
        Returns:
            Parsed ImprintConcept
        """
        try:
            # Use the concept parser to parse the text
            concept = self.concept_parser.parse_concept(row.imprint_concept)
            return concept
            
        except Exception as e:
            # Create a basic concept if parsing fails
            self.logger.warning(f"Failed to parse concept, creating basic concept: {e}")
            
            concept = ImprintConcept(
                name=row.get_display_name(),
                description=row.imprint_concept,
                target_audience="General readers",
                genre_focus=["General"],
                unique_value_proposition="Quality publishing",
                brand_personality="Professional",
                target_books_per_year=12,
                priority_focus="Quality",
                budget_range="Medium",
                automation_level="Standard",
                raw_input=row.imprint_concept,
                parsed_at=datetime.now()
            )
            
            return concept
    
    def _expand_concept(self, concept: ImprintConcept, row: ImprintRow) -> ExpandedImprint:
        """
        Expand imprint concept using the expander.
        
        Args:
            concept: Parsed imprint concept
            row: Original imprint row
            
        Returns:
            Expanded imprint
        """
        try:
            # Use the expander to expand the concept
            if hasattr(self.expander, 'expand_concept'):
                expanded = self.expander.expand_concept(concept)
            else:
                # Handle enhanced expander interface
                expanded = self.expander.expand_concept(concept)
            
            return expanded
            
        except Exception as e:
            self.logger.error(f"Failed to expand concept: {e}")
            raise
    
    def apply_attribute_filtering(self, expanded_imprint: ExpandedImprint) -> ExpandedImprint:
        """
        Apply attribute and subattribute filtering to expanded imprint.
        
        Args:
            expanded_imprint: Expanded imprint to filter
            
        Returns:
            Filtered expanded imprint
        """
        if not self.config.attributes and not self.config.subattributes:
            return expanded_imprint
        
        self.logger.debug("Applying attribute filtering")
        
        # Create a copy to avoid modifying the original
        filtered_imprint = expanded_imprint
        
        # If specific attributes are requested, filter to those
        if self.config.attributes:
            filtered_attributes = {}
            
            for attr_name in self.config.attributes:
                if hasattr(expanded_imprint, attr_name):
                    attr_value = getattr(expanded_imprint, attr_name)
                    
                    # Apply subattribute filtering if specified
                    if self.config.subattributes and isinstance(attr_value, dict):
                        filtered_attr = {}
                        for subattr in self.config.subattributes:
                            if subattr in attr_value:
                                filtered_attr[subattr] = attr_value[subattr]
                        filtered_attributes[attr_name] = filtered_attr
                    else:
                        filtered_attributes[attr_name] = attr_value
            
            # Update the expanded imprint with filtered attributes
            for attr_name, attr_value in filtered_attributes.items():
                if hasattr(filtered_imprint, attr_name):
                    setattr(filtered_imprint, attr_name, attr_value)
        
        return filtered_imprint
    
    def _has_meaningful_content(self, expanded_imprint: ExpandedImprint) -> bool:
        """
        Check if expanded imprint has meaningful content after filtering.
        
        Args:
            expanded_imprint: Expanded imprint to check
            
        Returns:
            True if imprint has meaningful content
        """
        # Check if any of the main attributes have content
        main_attributes = ['branding', 'design_specifications', 'publishing_strategy']
        
        for attr_name in main_attributes:
            if hasattr(expanded_imprint, attr_name):
                attr_value = getattr(expanded_imprint, attr_name)
                if attr_value and (
                    (isinstance(attr_value, dict) and len(attr_value) > 0) or
                    (isinstance(attr_value, str) and len(attr_value.strip()) > 0) or
                    (isinstance(attr_value, list) and len(attr_value) > 0)
                ):
                    return True
        
        return False
    
    def get_processing_stats(self, batch_result: BatchResult) -> Dict[str, Any]:
        """
        Get detailed processing statistics.
        
        Args:
            batch_result: Batch result to analyze
            
        Returns:
            Dictionary with processing statistics
        """
        if not batch_result.results:
            return {
                "total_processed": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "average_processing_time": 0.0,
                "total_processing_time": 0.0
            }
        
        processing_times = [r.processing_time for r in batch_result.results if r.processing_time > 0]
        
        return {
            "total_processed": batch_result.total_processed,
            "successful": batch_result.successful,
            "failed": batch_result.failed,
            "success_rate": batch_result.get_success_rate(),
            "average_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0.0,
            "total_processing_time": batch_result.processing_time,
            "files_processed": len(batch_result.source_files),
            "warnings_count": len(batch_result.warnings),
            "errors_count": len(batch_result.errors)
        }


def create_batch_orchestrator(llm_caller, config: BatchConfig) -> BatchOrchestrator:
    """
    Factory function to create a BatchOrchestrator instance.
    
    Args:
        llm_caller: LLM caller instance
        config: Batch processing configuration
        
    Returns:
        Configured BatchOrchestrator instance
    """
    return BatchOrchestrator(llm_caller, config)