"""
Integration system for connecting ideation workflows with existing CodexMetadata system.
Provides seamless conversion and integration between ideation and publishing pipelines.
"""

from .metadata_adapter import IdeationMetadataAdapter, ConversionResult
from .pipeline_integration import PipelineIntegrator, IntegrationConfiguration
from .validation_bridge import ValidationBridge, ValidationResult

__all__ = [
    'IdeationMetadataAdapter',
    'ConversionResult',
    'PipelineIntegrator',
    'IntegrationConfiguration',
    'ValidationBridge',
    'ValidationResult'
]