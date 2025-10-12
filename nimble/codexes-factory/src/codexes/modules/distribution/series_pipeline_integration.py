"""
Series Pipeline Integration Module

This module provides integration between the Series Registry and the book pipeline.
"""

import logging
from typing import Optional, Dict, Any

from ..metadata.metadata_models import CodexMetadata
from .series_registry import SeriesRegistry
from .series_assigner import SeriesAssigner

logger = logging.getLogger(__name__)


def integrate_series_with_pipeline(metadata: CodexMetadata, series_registry_path: Optional[str] = None,
                                  series_name: Optional[str] = None, sequence_number: Optional[int] = None,
                                  book_data: Optional[Dict[str, Any]] = None) -> CodexMetadata:
    """
    Integrate series management with the book pipeline.
    
    Args:
        metadata: CodexMetadata object to update with series information
        series_registry_path: Optional path to the series registry file
        series_name: Optional name of the series to assign the book to
        sequence_number: Optional sequence number to assign to the book
        book_data: Optional book data from schedule JSON
        
    Returns:
        Updated CodexMetadata object with series information
    """
    # Check if series information is in the book_data (from schedule JSON)
    if book_data and not series_name:
        schedule_series_name = book_data.get('series_name')
        schedule_series_number = book_data.get('series_number')
        
        if schedule_series_name:
            series_name = schedule_series_name
            if schedule_series_number:
                try:
                    sequence_number = int(schedule_series_number)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid series number in schedule: {schedule_series_number}, will auto-assign")
    
    # Skip if no series name is provided
    if not series_name:
        logger.info("No series name provided, skipping series assignment")
        return metadata
    
    try:
        # Initialize series registry and assigner
        registry = SeriesRegistry(series_registry_path or "data/series_registry.json")
        assigner = SeriesAssigner(registry)
        
        # Assign book to series
        logger.info(f"Assigning book '{metadata.title}' to series '{series_name}'")
        _, assigned_sequence = assigner.assign_book_to_series(
            metadata, series_name, sequence_number, metadata.publisher
        )
        
        logger.info(f"Book assigned to series '{series_name}' with sequence number {assigned_sequence}")
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error integrating series with pipeline: {e}")
        # Don't fail the pipeline if series assignment fails
        return metadata


def get_series_options(publisher_id: str, series_registry_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get available series options for a publisher.
    
    Args:
        publisher_id: ID of the publisher
        series_registry_path: Optional path to the series registry file
        
    Returns:
        Dictionary with series options
    """
    try:
        # Initialize series registry and assigner
        registry = SeriesRegistry(series_registry_path or "data/series_registry.json")
        assigner = SeriesAssigner(registry)
        
        # Get series options
        return {
            "series_options": assigner.get_series_options(publisher_id),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting series options: {e}")
        return {
            "series_options": [],
            "error": str(e),
            "success": False
        }


# Example usage in the book pipeline
def example_pipeline_integration():
    """Example of how to integrate series management with the book pipeline."""
    # Create a sample metadata object
    metadata = CodexMetadata(
        title="Test Book",
        author="Test Author",
        publisher="test-publisher"
    )
    
    # Get series options for the publisher
    series_options = get_series_options(metadata.publisher)
    
    if series_options["success"]:
        # Print available series
        print(f"Available series for {metadata.publisher}:")
        for option in series_options["series_options"]:
            print(f"- {option['name']} ({option['book_count']} books)")
        
        # Assign book to a series
        metadata = integrate_series_with_pipeline(
            metadata,
            series_name="Test Series",
            sequence_number=1
        )
        
        print(f"Book assigned to series: {metadata.series_name} #{metadata.series_number}")
    else:
        print(f"Error getting series options: {series_options.get('error', 'Unknown error')}")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run example
    example_pipeline_integration()