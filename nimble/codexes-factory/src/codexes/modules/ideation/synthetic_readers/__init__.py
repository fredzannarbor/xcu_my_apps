"""
Synthetic reader system for ideation workflows.
Provides reader persona simulation and evaluation capabilities.
"""

from .reader_persona import ReaderPersona, ReaderPersonaFactory
from .reader_panel import SyntheticReaderPanel, PanelResults
from .evaluation_aggregator import EvaluationAggregator, AggregatedResults

__all__ = [
    'ReaderPersona',
    'ReaderPersonaFactory',
    'SyntheticReaderPanel',
    'PanelResults',
    'EvaluationAggregator',
    'AggregatedResults'
]