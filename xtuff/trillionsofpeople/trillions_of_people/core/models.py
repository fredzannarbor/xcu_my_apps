"""Data models for TrillionsOfPeople package."""

from enum import Enum
from typing import Optional, Tuple, List, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
import re


class Species(str, Enum):
    """Available species for person generation."""
    SAPIENS = "sapiens"
    NEANDERTHALENSIS = "neanderthalensis"
    DENISOVAN = "denisovan"
    FLORESIENSIS = "floresiensis"


class Timeline(str, Enum):
    """Available timelines for person generation."""
    OURS = "ours"
    RCP_85 = "RCP 8.5"
    EARTH_616 = "Earth-616"
    EARTH_1218 = "Earth-1218"
    ODNI2040 = "ODNI2040"


class Realness(str, Enum):
    """Realness classification for persons."""
    SYNTHETIC = "synthetic"
    AUTHENTICATED = "authenticated"
    FICTIONAL = "fictional"


class Gender(str, Enum):
    """Available gender options."""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non-binary"
    OTHER = "other"


class Country(BaseModel):
    """Country model with name and ISO code."""
    name: str = Field(..., min_length=1, max_length=100, description="Country name")
    code: str = Field(..., min_length=2, max_length=3, description="ISO country code")
    
    @field_validator('code')
    @classmethod
    def validate_country_code(cls, v):
        """Validate country code format."""
        if not re.match(r'^[A-Z]{2,3}$', v.upper()):
            raise ValueError('Country code must be 2-3 uppercase letters')
        return v.upper()
    
    @field_validator('name')
    @classmethod
    def validate_country_name(cls, v):
        """Validate country name."""
        if not v.strip():
            raise ValueError('Country name cannot be empty')
        return v.strip()


class Person(BaseModel):
    """Data model for a person with comprehensive validation."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Person's full name")
    birth_year: int = Field(..., ge=-233000, le=100000, description="Birth year (BCE as negative)")
    gender: str = Field(..., description="Person's gender")
    species: Species = Field(default=Species.SAPIENS, description="Species classification")
    timeline: Timeline = Field(default=Timeline.OURS, description="Timeline classification")
    realness: Realness = Field(default=Realness.SYNTHETIC, description="Realness classification")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    nearest_city: Optional[str] = Field(None, max_length=100, description="Nearest city name")
    country: str = Field(default="", max_length=100, description="Country name")
    backstory: str = Field(default="", max_length=10000, description="Person's backstory")
    four_words_name: str = Field(default="", max_length=100, description="Four-word description")
    image_url: Optional[str] = Field(None, description="URL to person's image")
    ocean_tuple: Optional[Tuple[float, float, float, float, float]] = Field(
        None, description="Ocean-related coordinates tuple"
    )
    source: str = Field(default="trillions_of_people", max_length=50, description="Data source")
    status: str = Field(default="active", max_length=20, description="Person status")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate person name."""
        if not v.strip():
            raise ValueError('Name cannot be empty')
        # Check for potentially harmful characters
        if any(char in v for char in ['<', '>', '&', '"', "'"]):
            raise ValueError('Name contains invalid characters')
        return v.strip()
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        """Validate gender field."""
        if not v.strip():
            raise ValueError('Gender cannot be empty')
        return v.strip().lower()
    
    @field_validator('image_url')
    @classmethod
    def validate_image_url(cls, v):
        """Validate image URL format."""
        if v is not None:
            if not v.startswith(('http://', 'https://', 'data:')):
                raise ValueError('Image URL must start with http://, https://, or data:')
        return v
    
    @field_validator('nearest_city')
    @classmethod
    def validate_nearest_city(cls, v):
        """Validate nearest city name."""
        if v is not None and v.strip():
            # Check for potentially harmful characters
            if any(char in v for char in ['<', '>', '&', '"', "'"]):
                raise ValueError('City name contains invalid characters')
            return v.strip()
        return v
    
    @field_validator('country')
    @classmethod
    def validate_country(cls, v):
        """Validate country name."""
        if v and any(char in v for char in ['<', '>', '&', '"', "'"]):
            raise ValueError('Country name contains invalid characters')
        return v.strip() if v else ""
    
    @field_validator('backstory')
    @classmethod
    def validate_backstory(cls, v):
        """Validate backstory content."""
        if v and len(v.strip()) > 10000:
            raise ValueError('Backstory too long (max 10000 characters)')
        return v.strip() if v else ""
    
    @model_validator(mode='after')
    def validate_coordinates(self) -> 'Person':
        """Validate that latitude and longitude are both provided or both None."""
        lat = self.latitude
        lon = self.longitude
        
        if (lat is None) != (lon is None):
            raise ValueError('Both latitude and longitude must be provided together or both be None')
        
        return self
    
    model_config = {
        "use_enum_values": True,
        "validate_assignment": True,
        "extra": "forbid"  # Prevent extra fields
    }


class Config(BaseModel):
    """Configuration model for the application with comprehensive validation."""
    
    # API Keys
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    replicate_api_key: Optional[str] = Field(None, description="Replicate API key")
    
    # Default settings
    default_country: str = Field(default="Random", max_length=100, description="Default country")
    default_year: int = Field(default=2100, ge=-233000, le=100000, description="Default year")
    max_people_per_request: int = Field(default=5, ge=1, le=1000, description="Max people per request")
    
    # Feature toggles
    enable_image_generation: bool = Field(default=True, description="Enable image generation")
    enable_telemetry: bool = Field(default=False, description="Enable usage telemetry")
    
    # Directories and paths
    data_directory: str = Field(default="data", description="Data directory path")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Performance settings
    cache_ttl: int = Field(default=3600, ge=0, description="Cache time-to-live in seconds")
    request_timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retries for failed requests")
    
    @field_validator('openai_api_key')
    @classmethod
    def validate_openai_api_key(cls, v):
        """Validate OpenAI API key format."""
        if v is not None:
            if not v.startswith('sk-'):
                raise ValueError('OpenAI API key must start with "sk-"')
            if len(v) < 20:
                raise ValueError('OpenAI API key appears to be too short')
            # Allow more flexible pattern for testing and different key formats
            if not re.match(r'^sk-[A-Za-z0-9_-]{20,}$', v):
                raise ValueError('OpenAI API key format is invalid')
        return v
    
    @field_validator('anthropic_api_key')
    @classmethod
    def validate_anthropic_api_key(cls, v):
        """Validate Anthropic API key format."""
        if v is not None:
            if not v.startswith('sk-ant-'):
                raise ValueError('Anthropic API key must start with "sk-ant-"')
            if len(v) < 10:  # More lenient for testing
                raise ValueError('Anthropic API key appears to be too short')
        return v
    
    @field_validator('replicate_api_key')
    @classmethod
    def validate_replicate_api_key(cls, v):
        """Validate Replicate API key format."""
        if v is not None:
            if not v.startswith('r8_'):
                raise ValueError('Replicate API key must start with "r8_"')
            if len(v) < 10:  # More lenient for testing
                raise ValueError('Replicate API key appears to be too short')
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {", ".join(valid_levels)}')
        return v.upper()
    
    @field_validator('data_directory')
    @classmethod
    def validate_data_directory(cls, v):
        """Validate data directory path."""
        if not v.strip():
            raise ValueError('Data directory cannot be empty')
        # Basic path validation to prevent directory traversal
        if '..' in v or v.startswith('/'):
            raise ValueError('Invalid data directory path')
        return v.strip()
    
    @field_validator('default_country')
    @classmethod
    def validate_default_country(cls, v):
        """Validate default country."""
        if not v.strip():
            raise ValueError('Default country cannot be empty')
        return v.strip()
    
    def has_valid_api_key(self) -> bool:
        """Check if at least one valid API key is configured."""
        return any([
            self.openai_api_key,
            self.anthropic_api_key,
            self.replicate_api_key
        ])
    
    def get_primary_api_key(self) -> Optional[str]:
        """Get the primary API key (OpenAI preferred)."""
        return self.openai_api_key or self.anthropic_api_key or self.replicate_api_key
    
    model_config = {
        "validate_assignment": True,
        "extra": "forbid"
    }