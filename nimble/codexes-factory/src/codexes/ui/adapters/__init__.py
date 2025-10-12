"""
UI Adapters Package

Contains adapter classes that bridge between UI components and backend systems,
handling type conversions, mixed-type processing, and workflow adaptations.
"""

from .workflow_adapter import WorkflowAdapter, MixedTypeHandling, WorkflowAdaptation

__all__ = [
    'WorkflowAdapter',
    'MixedTypeHandling', 
    'WorkflowAdaptation'
]