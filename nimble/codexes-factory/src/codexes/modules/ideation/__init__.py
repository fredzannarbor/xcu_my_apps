"""
Ideation module for continuous book idea generation and tournament evaluation.
"""

from .book_idea import BookIdea, IdeaSet

# Import from legacy_tournament.py file
try:
    from .legacy_tournament import Tournament, TournamentManager, ShowTournamentResults
except ImportError:
    # Fallback to avoid breaking everything if tournament not available
    Tournament = None
    TournamentManager = None
    ShowTournamentResults = None

from .continuous_generator import ContinuousIdeaGenerator, IntegratedIdeaGenerator
from .synthetic_reader import SyntheticReaderPanel, ReaderFeedback, SynthesizedInsights
from .pipeline_bridge import IdeationPipelineBridge

__all__ = [
    'BookIdea',
    'IdeaSet', 
    'Tournament',
    'TournamentManager',
    'ShowTournamentResults',
    'ContinuousIdeaGenerator',
    'IntegratedIdeaGenerator',
    'SyntheticReaderPanel',
    'ReaderFeedback',
    'SynthesizedInsights',
    'IdeationPipelineBridge'
]