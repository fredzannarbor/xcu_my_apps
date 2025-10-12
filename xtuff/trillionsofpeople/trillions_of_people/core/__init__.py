"""Core functionality for TrillionsOfPeople package."""

from .models import Person, Config, Country, Species, Timeline, Realness, Gender
from .generator import PeopleGenerator
from .config import ConfigManager
from .exceptions import (
    TrillionsOfPeopleError,
    ConfigurationError,
    APIError,
    ValidationError,
    DataError,
)

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
    "TrillionsOfPeopleError",
    "ConfigurationError",
    "APIError",
    "ValidationError",
    "DataError",
]