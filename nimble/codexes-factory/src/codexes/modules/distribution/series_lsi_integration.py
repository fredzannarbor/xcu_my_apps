"""
Series LSI Integration Module

This module provides integration between the Series Management system and the LSI ACS Generator.
It ensures that series information is properly included in LSI CSV files.
"""

import logging
import os
from typing import Dict, Any, Optional, List

from ..metadata.metadata_models import CodexMetadata
from .series_registry import SeriesRegistry
from .series_assigner import SeriesAssigner
from .field_mapping import MappingStrategy, MappingContext, ComputedMappingStrategy

logger = logging.getLogger(__name__)


class SeriesLSIIntegrator:
    """
    Integrates Series Management with LSI ACS Generator.
    
    This class provides functionality to ensure series information is properly
    included in LSI CSV files and manages the mapping of series data to LSI fields.
    """
    
    def __init__(self, series_registry_path: Optional[str] = None):
        """
        Initialize the Series LSI Integrator.
        
        Args:
            series_registry_path: Optional path to the series registry file
        """
        self.series_registry_path = series_registry_path or "data/series_registry.json"
        self.series_registry = SeriesRegistry(self.series_registry_path)
        self.series_assigner = SeriesAssigner(self.series_registry)
        logger.info(f"Series LSI Integrator initialized with registry at {self.series_registry_path}")
    
    def get_series_mapping_strategies(self) -> Dict[str, MappingStrategy]:
        """
        Get mapping strategies for series-related LSI fields.
        
        Returns:
            Dictionary mapping LSI field names to mapping strategies
        """
        strategies = {
            "Series Name": ComputedMappingStrategy(self._compute_series_name),
            "# in Series": ComputedMappingStrategy(self._compute_series_number),
            "Series ISSN": ComputedMappingStrategy(self._compute_series_issn),
            "Series Publisher": ComputedMappingStrategy(self._compute_series_publisher)
        }
        
        logger.info(f"Created {len(strategies)} series mapping strategies")
        return strategies
    
    def _compute_series_name(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Compute the series name for LSI CSV.
        
        Args:
            metadata: CodexMetadata object
            context: Mapping context
            
        Returns:
            Series name string
        """
        # First check if metadata already has series_name
        if hasattr(metadata, 'series_name') and metadata.series_name:
            return metadata.series_name
        
        # If not, check if book is in any series
        try:
            if hasattr(metadata, 'uuid') and metadata.uuid:
                series_info = self.series_assigner.get_book_series_info(metadata.uuid)
                if series_info:
                    # Use the first series found
                    return series_info[0]['name']
        except Exception as e:
            logger.warning(f"Error getting series name: {e}")
        
        return ""
    
    def _compute_series_number(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Compute the series number for LSI CSV.
        
        Args:
            metadata: CodexMetadata object
            context: Mapping context
            
        Returns:
            Series number string
        """
        # First check if metadata already has series_number
        if hasattr(metadata, 'series_number') and metadata.series_number:
            return str(metadata.series_number)
        
        # If not, check if book is in any series
        try:
            if hasattr(metadata, 'uuid') and metadata.uuid:
                series_info = self.series_assigner.get_book_series_info(metadata.uuid)
                if series_info:
                    # Use the first series found
                    return str(series_info[0]['sequence_number'])
        except Exception as e:
            logger.warning(f"Error getting series number: {e}")
        
        return ""
    
    def _compute_series_issn(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Compute the series ISSN for LSI CSV.
        
        Args:
            metadata: CodexMetadata object
            context: Mapping context
            
        Returns:
            Series ISSN string
        """
        # Check if metadata already has series_issn
        if hasattr(metadata, 'series_issn') and metadata.series_issn:
            return metadata.series_issn
        
        # Currently we don't track ISSN in the series registry
        # This could be extended in the future
        return ""
    
    def _compute_series_publisher(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Compute the series publisher for LSI CSV.
        
        Args:
            metadata: CodexMetadata object
            context: Mapping context
            
        Returns:
            Series publisher string
        """
        # First check if metadata already has series_publisher
        if hasattr(metadata, 'series_publisher') and metadata.series_publisher:
            return metadata.series_publisher
        
        # If not, check if book is in any series
        try:
            if hasattr(metadata, 'uuid') and metadata.uuid:
                series_info = self.series_assigner.get_book_series_info(metadata.uuid)
                if series_info:
                    # Get publisher ID from series info
                    publisher_id = series_info[0]['publisher_id']
                    # If publisher ID matches metadata publisher, use that
                    if publisher_id == metadata.publisher:
                        return metadata.publisher
                    # Otherwise, this is a multi-publisher series
                    return publisher_id
        except Exception as e:
            logger.warning(f"Error getting series publisher: {e}")
        
        # Default to the book's publisher
        return metadata.publisher if hasattr(metadata, 'publisher') and metadata.publisher else ""
    
    def ensure_series_data(self, metadata: CodexMetadata) -> CodexMetadata:
        """
        Ensure that series data is properly set in metadata.
        
        Args:
            metadata: CodexMetadata object to update
            
        Returns:
            Updated CodexMetadata object with series information
        """
        try:
            # Skip if no UUID
            if not hasattr(metadata, 'uuid') or not metadata.uuid:
                logger.warning("Cannot ensure series data: No UUID in metadata")
                return metadata
            
            # Check if book is in any series
            series_info = self.series_assigner.get_book_series_info(metadata.uuid)
            if not series_info:
                logger.info(f"Book {metadata.uuid} is not in any series")
                return metadata
            
            # Use the first series found
            first_series = series_info[0]
            
            # Update metadata with series information
            metadata.series_name = first_series['name']
            metadata.series_number = str(first_series['sequence_number'])
            
            # Add additional series metadata if not already present
            if not hasattr(metadata, 'series_publisher') or not metadata.series_publisher:
                metadata.series_publisher = first_series['publisher_id']
            
            logger.info(f"Updated metadata with series information: {metadata.series_name} #{metadata.series_number}")
            
        except Exception as e:
            logger.error(f"Error ensuring series data: {e}")
        
        return metadata
    
    def register_series_mapping_strategies(self, field_registry) -> None:
        """
        Register series mapping strategies with a field mapping registry.
        
        Args:
            field_registry: FieldMappingRegistry instance
        """
        strategies = self.get_series_mapping_strategies()
        for field_name, strategy in strategies.items():
            field_registry.register_strategy(field_name, strategy)
        
        logger.info(f"Registered {len(strategies)} series mapping strategies with field registry")


def integrate_series_with_lsi_generator(generator, series_registry_path: Optional[str] = None) -> None:
    """
    Integrate series management with an LSI ACS Generator instance.
    
    Args:
        generator: LsiAcsGenerator instance
        series_registry_path: Optional path to the series registry file
    """
    try:
        # Create series integrator
        integrator = SeriesLSIIntegrator(series_registry_path)
        
        # Register series mapping strategies with the generator's field registry
        integrator.register_series_mapping_strategies(generator.field_registry)
        
        # Store the integrator in the generator for future use
        generator.series_integrator = integrator
        
        logger.info("Series management integrated with LSI ACS Generator")
        
    except Exception as e:
        logger.error(f"Error integrating series with LSI generator: {e}")