#!/usr/bin/env python3
"""
Nimble Ultra Global Pipeline
Specialized tools for processing declassified documents, intelligence materials, and government publications.
"""

from .document_ingestion import DocumentIngestionPipeline
from .annotation_system import AnnotationManager
from .redaction_handler import RedactionProcessor
from .metadata_extractor import GovernmentDocumentExtractor
from .template_manager import NUGTemplateManager
from .workflow_automation import NUGWorkflowAutomation

__all__ = [
    'DocumentIngestionPipeline',
    'AnnotationManager',
    'RedactionProcessor',
    'GovernmentDocumentExtractor',
    'NUGTemplateManager',
    'NUGWorkflowAutomation'
]

__version__ = "1.0.0"