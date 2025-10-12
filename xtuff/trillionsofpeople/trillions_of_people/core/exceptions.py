"""Custom exceptions for TrillionsOfPeople package."""


class TrillionsOfPeopleError(Exception):
    """Base exception for the TrillionsOfPeople package."""
    pass


class ConfigurationError(TrillionsOfPeopleError):
    """Raised when configuration is invalid or missing."""
    pass


class APIError(TrillionsOfPeopleError):
    """Raised when external API calls fail."""
    pass


class ValidationError(TrillionsOfPeopleError):
    """Raised when input validation fails."""
    pass


class DataError(TrillionsOfPeopleError):
    """Raised when data operations fail."""
    pass