"""
Output Manager component for organizing and writing batch processing results.

This module handles file organization, naming strategies, output writing,
and index file generation for batch processing results.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

from .batch_models import (
    OutputConfig,
    ImprintResult,
    BatchResult,
    NamingStrategy,
    OrganizationStrategy,
    ProcessingError,
    ProcessingContext
)


class OutputManager:
    """Manages output file organization and writing for batch processing results."""
    
    # Characters to remove/replace in filenames
    INVALID_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
    
    def __init__(self, config: OutputConfig):
        """
        Initialize OutputManager.
        
        Args:
            config: Output configuration
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        
        # Ensure base directory exists
        self.config.base_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Initialized OutputManager with base directory: {self.config.base_directory}")
    
    def generate_output_path(self, imprint_name: str, source_info: Dict[str, Any]) -> Path:
        """
        Generate output file path based on naming and organization strategies.
        
        Args:
            imprint_name: Name of the imprint
            source_info: Information about the source (file, row, etc.)
            
        Returns:
            Path for the output file
        """
        # Clean imprint name for filename
        clean_name = self._sanitize_filename(imprint_name)
        
        # Generate filename based on naming strategy
        filename = self._generate_filename(clean_name, source_info)
        
        # Generate directory path based on organization strategy
        directory = self._generate_directory_path(source_info)
        
        # Combine and ensure uniqueness
        full_path = directory / f"{filename}.json"
        unique_path = self.ensure_unique_naming(full_path)
        
        self.logger.debug(f"Generated output path: {unique_path}")
        return unique_path
    
    def _generate_filename(self, clean_name: str, source_info: Dict[str, Any]) -> str:
        """
        Generate filename based on naming strategy.
        
        Args:
            clean_name: Sanitized imprint name
            source_info: Source information
            
        Returns:
            Generated filename (without extension)
        """
        if self.config.naming_strategy == NamingStrategy.IMPRINT_NAME:
            return clean_name or "unnamed_imprint"
        
        elif self.config.naming_strategy == NamingStrategy.ROW_NUMBER:
            row_num = source_info.get('row_number', 1)
            source_file = source_info.get('source_file', 'unknown')
            if isinstance(source_file, Path):
                source_file = source_file.stem
            return f"{source_file}_row_{row_num}"
        
        elif self.config.naming_strategy == NamingStrategy.HYBRID:
            row_num = source_info.get('row_number', 1)
            if clean_name:
                return f"{clean_name}_row_{row_num}"
            else:
                source_file = source_info.get('source_file', 'unknown')
                if isinstance(source_file, Path):
                    source_file = source_file.stem
                return f"{source_file}_row_{row_num}"
        
        else:
            # Default to imprint name
            return clean_name or "unnamed_imprint"
    
    def _generate_directory_path(self, source_info: Dict[str, Any]) -> Path:
        """
        Generate directory path based on organization strategy.
        
        Args:
            source_info: Source information
            
        Returns:
            Directory path for output
        """
        base_dir = self.config.base_directory
        
        if self.config.organization_strategy == OrganizationStrategy.FLAT:
            return base_dir
        
        elif self.config.organization_strategy == OrganizationStrategy.BY_SOURCE:
            source_file = source_info.get('source_file', 'unknown')
            if isinstance(source_file, Path):
                source_name = source_file.stem
            else:
                source_name = str(source_file).replace('.csv', '')
            
            clean_source = self._sanitize_filename(source_name)
            return base_dir / clean_source
        
        elif self.config.organization_strategy == OrganizationStrategy.BY_IMPRINT:
            imprint_name = source_info.get('imprint_name', 'unknown')
            clean_imprint = self._sanitize_filename(imprint_name)
            return base_dir / clean_imprint
        
        else:
            # Default to flat
            return base_dir
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed"
        
        # Remove invalid characters
        sanitized = re.sub(self.INVALID_FILENAME_CHARS, '_', filename)
        
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "unnamed"
        
        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized.lower()
    
    def ensure_unique_naming(self, base_path: Path) -> Path:
        """
        Ensure unique file naming by adding suffixes if needed.
        
        Args:
            base_path: Base path for the file
            
        Returns:
            Unique file path
        """
        if not base_path.exists() or self.config.overwrite_existing:
            return base_path
        
        # Generate unique name with suffix
        counter = 1
        stem = base_path.stem
        suffix = base_path.suffix
        parent = base_path.parent
        
        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
            
            # Prevent infinite loop
            if counter > 1000:
                self.logger.warning(f"Could not generate unique name for {base_path}, using timestamp")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return parent / f"{stem}_{timestamp}{suffix}"
    
    def write_imprint_result(self, result: ImprintResult, output_path: Optional[Path] = None) -> Path:
        """
        Write imprint result to file.
        
        Args:
            result: Imprint processing result
            output_path: Optional specific output path
            
        Returns:
            Path where the result was written
            
        Raises:
            IOError: If writing fails
        """
        try:
            # Generate output path if not provided
            if output_path is None:
                imprint_name = self._extract_imprint_name(result)
                source_info = self._extract_source_info(result)
                output_path = self.generate_output_path(imprint_name, source_info)
            
            # Ensure directory exists
            if self.config.create_subdirectories:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for writing
            output_data = self._prepare_output_data(result)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Update result with output path
            result.output_path = output_path
            
            self.logger.debug(f"Wrote imprint result to: {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"Failed to write imprint result: {str(e)}"
            self.logger.error(error_msg)
            raise IOError(error_msg) from e
    
    def _extract_imprint_name(self, result: ImprintResult) -> str:
        """Extract imprint name from result."""
        if result.expanded_imprint:
            # Try to get name from branding
            if hasattr(result.expanded_imprint, 'branding'):
                branding = result.expanded_imprint.branding
                if isinstance(branding, dict) and 'imprint_name' in branding:
                    return branding['imprint_name']
                elif hasattr(branding, 'imprint_name'):
                    return branding.imprint_name
        
        # Fall back to display name from row
        return result.row.get_display_name()
    
    def _extract_source_info(self, result: ImprintResult) -> Dict[str, Any]:
        """Extract source information from result."""
        return {
            'source_file': result.row.source_file,
            'row_number': result.row.row_number,
            'imprint_name': self._extract_imprint_name(result)
        }
    
    def _prepare_output_data(self, result: ImprintResult) -> Dict[str, Any]:
        """
        Prepare data for output file.
        
        Args:
            result: Imprint processing result
            
        Returns:
            Dictionary ready for JSON serialization
        """
        output_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source_file': str(result.row.source_file),
                'row_number': result.row.row_number,
                'processing_time': result.processing_time,
                'success': result.success
            },
            'source_data': {
                'imprint_concept': result.row.imprint_concept,
                'additional_data': result.row.additional_data,
                'mapped_columns': result.row.mapped_columns
            }
        }
        
        # Add expanded imprint if available
        if result.expanded_imprint:
            if hasattr(result.expanded_imprint, 'to_dict'):
                output_data['expanded_imprint'] = result.expanded_imprint.to_dict()
            else:
                # Handle different types of expanded imprints
                output_data['expanded_imprint'] = self._serialize_expanded_imprint(result.expanded_imprint)
        
        # Add error information if present
        if result.error:
            output_data['error'] = {
                'type': type(result.error).__name__,
                'message': str(result.error)
            }
        
        # Add warnings if present
        if result.warnings:
            output_data['warnings'] = [w.to_dict() for w in result.warnings]
        
        return output_data
    
    def _serialize_expanded_imprint(self, expanded_imprint: Any) -> Dict[str, Any]:
        """
        Serialize expanded imprint to dictionary.
        
        Args:
            expanded_imprint: Expanded imprint object
            
        Returns:
            Serialized dictionary
        """
        try:
            # Try different serialization methods
            if hasattr(expanded_imprint, '__dict__'):
                data = {}
                for key, value in expanded_imprint.__dict__.items():
                    if not key.startswith('_'):
                        try:
                            # Try to serialize the value
                            json.dumps(value, default=str)
                            data[key] = value
                        except (TypeError, ValueError):
                            data[key] = str(value)
                return data
            else:
                return str(expanded_imprint)
                
        except Exception as e:
            self.logger.warning(f"Failed to serialize expanded imprint: {e}")
            return {"serialization_error": str(e)}
    
    def create_index_file(self, batch_result: BatchResult) -> Optional[Path]:
        """
        Create index file with batch processing summary.
        
        Args:
            batch_result: Batch processing result
            
        Returns:
            Path to created index file, or None if creation disabled
        """
        if not self.config.create_index:
            return None
        
        try:
            # Generate index filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            index_filename = f"batch_index_{timestamp}.json"
            index_path = self.config.base_directory / index_filename
            
            # Prepare index data
            index_data = {
                'batch_summary': {
                    'generated_at': datetime.now().isoformat(),
                    'total_processed': batch_result.total_processed,
                    'successful': batch_result.successful,
                    'failed': batch_result.failed,
                    'success_rate': batch_result.get_success_rate(),
                    'processing_time': batch_result.processing_time,
                    'source_files': [str(f) for f in batch_result.source_files]
                },
                'results': [],
                'errors': [e.to_dict() for e in batch_result.errors],
                'warnings': [w.to_dict() for w in batch_result.warnings]
            }
            
            # Add result summaries
            for result in batch_result.results:
                result_summary = {
                    'row_number': result.row.row_number,
                    'source_file': str(result.row.source_file),
                    'imprint_name': self._extract_imprint_name(result),
                    'success': result.success,
                    'processing_time': result.processing_time,
                    'output_path': str(result.output_path) if result.output_path else None,
                    'error': str(result.error) if result.error else None
                }
                index_data['results'].append(result_summary)
            
            # Write index file
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Created batch index file: {index_path}")
            return index_path
            
        except Exception as e:
            self.logger.error(f"Failed to create index file: {e}")
            return None
    
    def write_batch_results(self, batch_result: BatchResult) -> List[Path]:
        """
        Write all results from a batch processing operation.
        
        Args:
            batch_result: Batch processing result
            
        Returns:
            List of paths where results were written
        """
        written_paths = []
        
        for result in batch_result.results:
            try:
                if result.success and result.expanded_imprint:
                    output_path = self.write_imprint_result(result)
                    written_paths.append(output_path)
                else:
                    self.logger.debug(f"Skipping failed result for row {result.row.row_number}")
            except Exception as e:
                self.logger.error(f"Failed to write result for row {result.row.row_number}: {e}")
        
        # Create index file
        index_path = self.create_index_file(batch_result)
        if index_path:
            batch_result.index_file = index_path
            written_paths.append(index_path)
        
        self.logger.info(f"Wrote {len(written_paths)} files for batch processing results")
        return written_paths
    
    def get_output_summary(self, batch_result: BatchResult) -> Dict[str, Any]:
        """
        Get summary of output operations.
        
        Args:
            batch_result: Batch processing result
            
        Returns:
            Summary dictionary
        """
        successful_outputs = [r for r in batch_result.results if r.success and r.output_path]
        
        return {
            'base_directory': str(self.config.base_directory),
            'naming_strategy': self.config.naming_strategy.value,
            'organization_strategy': self.config.organization_strategy.value,
            'total_results': len(batch_result.results),
            'successful_outputs': len(successful_outputs),
            'output_files': [str(r.output_path) for r in successful_outputs],
            'index_file': str(batch_result.index_file) if batch_result.index_file else None,
            'subdirectories_created': self.config.create_subdirectories,
            'overwrite_existing': self.config.overwrite_existing
        }


def create_output_manager(config: OutputConfig) -> OutputManager:
    """
    Factory function to create an OutputManager instance.
    
    Args:
        config: Output configuration
        
    Returns:
        Configured OutputManager instance
    """
    return OutputManager(config)