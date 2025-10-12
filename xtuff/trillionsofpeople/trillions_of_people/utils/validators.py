"""Input validation utilities."""

import re
from typing import Dict, Any, List, Union, Optional
from pathlib import Path
from pydantic import ValidationError as PydanticValidationError

from ..core.models import Person, Config, Country, Species, Timeline, Realness
from ..core.exceptions import ValidationError


def validate_person_data(data: Dict[str, Any]) -> Person:
    """
    Validate person data dictionary and return a Person instance.
    
    Args:
        data: Dictionary containing person data
        
    Returns:
        Person: Validated Person instance
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        return Person(**data)
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            error_messages.append(f"{field}: {message}")
        raise ValidationError(f"Person validation failed: {'; '.join(error_messages)}")


def validate_config_data(data: Dict[str, Any]) -> Config:
    """
    Validate configuration data dictionary and return a Config instance.
    
    Args:
        data: Dictionary containing configuration data
        
    Returns:
        Config: Validated Config instance
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        return Config(**data)
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            error_messages.append(f"{field}: {message}")
        raise ValidationError(f"Config validation failed: {'; '.join(error_messages)}")


def validate_country_data(data: Dict[str, Any]) -> Country:
    """
    Validate country data dictionary and return a Country instance.
    
    Args:
        data: Dictionary containing country data
        
    Returns:
        Country: Validated Country instance
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        return Country(**data)
    except PydanticValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            error_messages.append(f"{field}: {message}")
        raise ValidationError(f"Country validation failed: {'; '.join(error_messages)}")


def validate_batch_person_data(data_list: List[Dict[str, Any]]) -> List[Person]:
    """
    Validate a batch of person data dictionaries.
    
    Args:
        data_list: List of dictionaries containing person data
        
    Returns:
        List[Person]: List of validated Person instances
        
    Raises:
        ValidationError: If any validation fails
    """
    validated_people = []
    errors = []
    
    for i, data in enumerate(data_list):
        try:
            person = validate_person_data(data)
            validated_people.append(person)
        except ValidationError as e:
            errors.append(f"Item {i}: {str(e)}")
    
    if errors:
        raise ValidationError(f"Batch validation failed: {'; '.join(errors)}")
    
    return validated_people


def sanitize_input(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input by removing potentially harmful characters.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized string
        
    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(value, str):
        raise ValidationError("Input must be a string")
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>&"\'`]', '', value)
    
    # Strip whitespace
    sanitized = sanitized.strip()
    
    # Check length
    if max_length and len(sanitized) > max_length:
        raise ValidationError(f"Input too long (max {max_length} characters)")
    
    return sanitized


def validate_file_path(path: Union[str, Path], must_exist: bool = False) -> Path:
    """
    Validate file path for security and existence.
    
    Args:
        path: File path to validate
        must_exist: Whether the file must exist
        
    Returns:
        Path: Validated Path object
        
    Raises:
        ValidationError: If path is invalid or unsafe
    """
    if isinstance(path, str):
        path = Path(path)
    
    # Check for directory traversal attempts
    if '..' in str(path) or str(path).startswith('/'):
        raise ValidationError("Invalid file path: directory traversal detected")
    
    # Check if file exists when required
    if must_exist and not path.exists():
        raise ValidationError(f"File does not exist: {path}")
    
    return path


def validate_api_key(api_key: str, service: str = "OpenAI") -> str:
    """
    Validate API key format.
    
    Args:
        api_key: API key to validate
        service: Service name for error messages
        
    Returns:
        str: Validated API key
        
    Raises:
        ValidationError: If API key format is invalid
    """
    if not isinstance(api_key, str):
        raise ValidationError(f"{service} API key must be a string")
    
    api_key = api_key.strip()
    
    if not api_key:
        raise ValidationError(f"{service} API key cannot be empty")
    
    # Service-specific validation
    if service.lower() == "openai":
        if not api_key.startswith('sk-'):
            raise ValidationError("OpenAI API key must start with 'sk-'")
        if len(api_key) < 20:
            raise ValidationError("OpenAI API key appears to be too short")
    
    return api_key


def validate_coordinates(latitude: float, longitude: float) -> tuple[float, float]:
    """
    Validate geographic coordinates.
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
        
    Returns:
        tuple: Validated (latitude, longitude) tuple
        
    Raises:
        ValidationError: If coordinates are invalid
    """
    if not isinstance(latitude, (int, float)):
        raise ValidationError("Latitude must be a number")
    
    if not isinstance(longitude, (int, float)):
        raise ValidationError("Longitude must be a number")
    
    if latitude < -90 or latitude > 90:
        raise ValidationError("Latitude must be between -90 and 90")
    
    if longitude < -180 or longitude > 180:
        raise ValidationError("Longitude must be between -180 and 180")
    
    return float(latitude), float(longitude)


def validate_year_range(start_year: int, end_year: int) -> tuple[int, int]:
    """
    Validate year range for historical data.
    
    Args:
        start_year: Starting year
        end_year: Ending year
        
    Returns:
        tuple: Validated (start_year, end_year) tuple
        
    Raises:
        ValidationError: If year range is invalid
    """
    if not isinstance(start_year, int) or not isinstance(end_year, int):
        raise ValidationError("Years must be integers")
    
    if start_year < -233000 or start_year > 100000:
        raise ValidationError("Start year must be between -233000 and 100000")
    
    if end_year < -233000 or end_year > 100000:
        raise ValidationError("End year must be between -233000 and 100000")
    
    if start_year > end_year:
        raise ValidationError("Start year must be less than or equal to end year")
    
    return start_year, end_year


def validate_enum_value(value: str, enum_class: type, field_name: str) -> str:
    """
    Validate that a string value is a valid enum member.
    
    Args:
        value: String value to validate
        enum_class: Enum class to validate against
        field_name: Field name for error messages
        
    Returns:
        str: Validated enum value
        
    Raises:
        ValidationError: If value is not a valid enum member
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    try:
        enum_class(value)
        return value
    except ValueError:
        valid_values = [e.value for e in enum_class]
        raise ValidationError(
            f"Invalid {field_name}: '{value}'. Must be one of: {', '.join(valid_values)}"
        )