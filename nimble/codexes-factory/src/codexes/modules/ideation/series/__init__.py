"""
Series generation and consistency management for ideation workflows.
Provides series generation, consistency tracking, and franchise management capabilities.
"""

from .series_generator import SeriesGenerator, SeriesConfiguration
from .consistency_manager import ConsistencyManager, ConsistencyTracker
from .franchise_manager import FranchiseManager, FranchiseConfiguration

__all__ = [
    'SeriesGenerator',
    'SeriesConfiguration',
    'ConsistencyManager',
    'ConsistencyTracker',
    'FranchiseManager',
    'FranchiseConfiguration'
]