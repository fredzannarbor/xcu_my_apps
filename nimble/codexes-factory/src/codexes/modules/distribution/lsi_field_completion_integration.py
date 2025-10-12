"""
LSI Field Completion Integration Module

This module provides integration between the LLM Field Completer and the LSI ACS Generator.
It ensures that field completion is properly integrated with the LSI generation process.
"""

import os
import logging
from typing import Dict, Any, Optional, List

from ..metadata.metadata_models import CodexMetadata
from .llm_field_completer import LLMFieldCompleter
from .lsi_field_completion_reporter import LSIFieldCompletionReporter
from .error_recovery_manager import ErrorRecoveryManager

logger = logging.getLogger(__name__)


class LSIFieldCompletionIntegrator:
    """
    Integrates LLM Field Completion with LSI ACS Generator.
    
    This class provides functionality to ensure field completion is properly
    integrated with the LSI generation process, including validation and reporting.
    """
    
    def __init__(self, model_name: str = "gemini/gemini-2.5-flash",
                prompts_path: str = "prompts/lsi_field_completion_prompts.json"):
        """
        Initialize the LSI Field Completion Integrator.
        
        Args:
            model_name: Name of the LLM model to use
            prompts_path: Path to the LSI field completion prompts file
        """
        self.field_completer = LLMFieldCompleter(model_name, prompts_path)
        self.error_recovery_manager = ErrorRecoveryManager()
        logger.info(f"LSI Field Completion Integrator initialized with model {model_name}")
    
    def complete_and_validate_metadata(self, metadata: CodexMetadata, book_content: Optional[str] = None,
                                     validation_func=None) -> Dict[str, Any]:
        """
        Complete missing fields and validate metadata.
        
        Args:
            metadata: CodexMetadata object to complete and validate
            book_content: Optional book content to use for field completion
            validation_func: Optional function to validate metadata
            
        Returns:
            Dictionary with completion and validation results
        """
        try:
            # Step 1: Complete missing fields
            logger.info(f"Completing missing fields for {metadata.title}")
            completed_metadata = self.field_completer.complete_missing_fields(
                metadata, book_content, save_to_disk=True
            )
            
            # Step 2: Validate metadata if validation function is provided
            validation_result = None
            if validation_func:
                logger.info(f"Validating metadata for {metadata.title}")
                validation_result = validation_func(completed_metadata)
                
                # Step 3: Attempt recovery if validation failed
                if validation_result and not validation_result.is_valid:
                    logger.info(f"Attempting recovery for {metadata.title}")
                    completed_metadata = self.error_recovery_manager.recover_from_validation_errors(
                        completed_metadata, validation_result
                    )
                    
                    # Re-validate after recovery
                    validation_result = validation_func(completed_metadata)
            
            # Return results
            return {
                "metadata": completed_metadata,
                "validation_result": validation_result,
                "success": validation_result.is_valid if validation_result else True,
                "recovery_suggestions": self.error_recovery_manager.get_recovery_suggestions(validation_result) if validation_result else []
            }
            
        except Exception as e:
            logger.error(f"Error completing and validating metadata: {e}")
            return {
                "metadata": metadata,
                "validation_result": None,
                "success": False,
                "error": str(e)
            }
    
    def generate_field_completion_report(self, metadata: CodexMetadata, lsi_headers: List[str],
                                       field_registry, output_dir: str = "output/reports") -> Dict[str, str]:
        """
        Generate a report on field completion status.
        
        Args:
            metadata: CodexMetadata object to analyze
            lsi_headers: List of LSI header names
            field_registry: FieldMappingRegistry instance
            output_dir: Directory to save reports
            
        Returns:
            Dictionary mapping format to output file path
        """
        try:
            # Create reporter
            reporter = LSIFieldCompletionReporter(field_registry)
            
            # Generate reports
            return reporter.generate_field_strategy_report(
                metadata, lsi_headers, output_dir, formats=["csv", "html", "json", "md"]
            )
            
        except Exception as e:
            logger.error(f"Error generating field completion report: {e}")
            return {}


def integrate_field_completion_with_lsi_generator(generator, model_name: str = "gemini/gemini-2.5-flash",
                                               prompts_path: str = "prompts/lsi_field_completion_prompts.json") -> None:
    """
    Integrate field completion with an LSI ACS Generator instance.
    
    Args:
        generator: LsiAcsGenerator instance
        model_name: Name of the LLM model to use
        prompts_path: Path to the LSI field completion prompts file
    """
    try:
        # Create field completion integrator
        integrator = LSIFieldCompletionIntegrator(model_name, prompts_path)
        
        # Store the integrator in the generator for future use
        generator.field_completion_integrator = integrator
        
        # Add pre-generation hook to complete fields
        original_generate_with_validation = generator.generate_with_validation
        
        def enhanced_generate_with_validation(metadata, output_path, book_content=None, **kwargs):
            # Complete and validate metadata
            result = integrator.complete_and_validate_metadata(
                metadata, book_content, generator.validate_metadata
            )
            
            # Generate report
            report_dir = os.path.join(os.path.dirname(output_path), "reports")
            integrator.generate_field_completion_report(
                result["metadata"], generator.get_lsi_headers(), generator.field_registry, report_dir
            )
            
            # Call original method with completed metadata
            return original_generate_with_validation(result["metadata"], output_path, **kwargs)
        
        # Replace the original method
        generator.generate_with_validation = enhanced_generate_with_validation
        
        logger.info("Field completion integrated with LSI ACS Generator")
        
    except Exception as e:
        logger.error(f"Error integrating field completion with LSI generator: {e}")