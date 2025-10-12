"""
TrillionsOfPeople - Generate synthetic people data for historical, present, and future scenarios.

This package provides tools for creating synthetic personas across different time periods,
countries, and scenarios for research, planning, and creative purposes.
"""

__version__ = "0.1.0"
__author__ = "Fred Zimmerman"
__email__ = "fredz@trillionsofpeople.info"

from .core.models import Person, Config, Country, Species, Timeline, Realness, Gender
from .core.generator import PeopleGenerator
from .core.config import ConfigManager

__all__ = [
    "Person",
    "Config",
    "Country",
    "Species", 
    "Timeline",
    "Realness",
    "Gender",
    "PeopleGenerator",
    "ConfigManager",
]