"""
Trillions of People - Generate synthetic people data for historical, present, and future scenarios.

A tool to explore the human story through AI-generated personas.
"""

__version__ = "1.0.0"
__author__ = "Fred Zimmerman"
__email__ = "fredz@trillionsofpeople.info"

from .core.llm_caller import TrillionsLLMCaller
from .core.logging_config import get_logging_manager

__all__ = [
    "TrillionsLLMCaller",
    "get_logging_manager",
    "__version__",
]