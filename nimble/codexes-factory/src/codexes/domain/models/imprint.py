"""
Rich domain model for Imprint entities.

This module defines the core Imprint domain model with associated value objects
for branding and publishing focus specifications.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
import re


class ImprintStatus(Enum):
    """Status lifecycle of an imprint."""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


@dataclass
class BrandingSpecification:
    """
    Value object representing the branding identity of an imprint.

    Contains all visual and messaging elements that define the imprint's
    brand identity.
    """
    display_name: str
    tagline: Optional[str] = None
    mission_statement: Optional[str] = None
    brand_values: List[str] = field(default_factory=list)
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    logo_url: Optional[str] = None

    def is_complete(self) -> bool:
        """
        Validate that all required branding fields are populated.

        Returns:
            bool: True if all required fields have values
        """
        return bool(
            self.display_name and
            self.tagline and
            self.mission_statement and
            self.brand_values and
            self.primary_color and
            self.secondary_color
        )

    def get_css_variables(self) -> Dict[str, str]:
        """
        Generate CSS custom properties dictionary for theming.

        Returns:
            Dict[str, str]: Mapping of CSS variable names to values
        """
        variables = {}
        if self.primary_color:
            variables['--primary-color'] = self.primary_color
        if self.secondary_color:
            variables['--secondary-color'] = self.secondary_color
        if self.font_family:
            variables['--font-family'] = self.font_family
        return variables

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'display_name': self.display_name,
            'tagline': self.tagline,
            'mission_statement': self.mission_statement,
            'brand_values': self.brand_values,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'font_family': self.font_family,
            'logo_url': self.logo_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrandingSpecification':
        """Create instance from dictionary."""
        return cls(
            display_name=data.get('display_name', ''),
            tagline=data.get('tagline'),
            mission_statement=data.get('mission_statement'),
            brand_values=data.get('brand_values', []),
            primary_color=data.get('primary_color'),
            secondary_color=data.get('secondary_color'),
            font_family=data.get('font_family'),
            logo_url=data.get('logo_url'),
        )

    def __repr__(self) -> str:
        return f"BrandingSpecification(display_name='{self.display_name}', complete={self.is_complete()})"


@dataclass
class PublishingFocus:
    """
    Value object representing the editorial focus of an imprint.

    Defines what types of content the imprint publishes and its target market.
    """
    primary_genres: List[str] = field(default_factory=list)
    target_audience: Optional[str] = None
    price_point: Optional[str] = None
    books_per_year: Optional[int] = None

    def is_complete(self) -> bool:
        """
        Validate that publishing focus has minimum required information.

        Returns:
            bool: True if focus is sufficiently defined
        """
        return bool(
            self.primary_genres and
            self.target_audience
        )

    def matches_genre(self, genre: str) -> bool:
        """
        Check if a given genre is part of this imprint's focus.

        Args:
            genre: Genre name to check

        Returns:
            bool: True if genre matches any primary genre (case-insensitive)
        """
        genre_lower = genre.lower()
        return any(g.lower() == genre_lower for g in self.primary_genres)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'primary_genres': self.primary_genres,
            'target_audience': self.target_audience,
            'price_point': self.price_point,
            'books_per_year': self.books_per_year,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PublishingFocus':
        """Create instance from dictionary."""
        return cls(
            primary_genres=data.get('primary_genres', []),
            target_audience=data.get('target_audience'),
            price_point=data.get('price_point'),
            books_per_year=data.get('books_per_year'),
        )

    def __repr__(self) -> str:
        return f"PublishingFocus(genres={self.primary_genres}, audience='{self.target_audience}')"


class Imprint:
    """
    Rich domain model representing a publishing imprint.

    An imprint is a distinct editorial brand within a publishing house,
    with its own identity, focus, and publishing criteria.
    """

    def __init__(
        self,
        name: str,
        publisher: str,
        charter: str,
        branding: BrandingSpecification,
        publishing_focus: PublishingFocus,
        slug: Optional[str] = None,
        status: ImprintStatus = ImprintStatus.DRAFT,
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None,
        persona: Optional['PublisherPersona'] = None,
    ):
        """
        Initialize an Imprint.

        Args:
            name: Canonical name of the imprint
            publisher: Name of parent publisher
            charter: Mission and purpose statement
            branding: Branding specification
            publishing_focus: Editorial focus specification
            slug: URL-safe identifier (auto-generated if not provided)
            status: Current lifecycle status
            created_at: Creation timestamp
            modified_at: Last modification timestamp
            persona: Associated publisher persona
        """
        self._validate_name(name)

        self.name = name
        self.slug = slug or self._create_slug(name)
        self.publisher = publisher
        self.charter = charter
        self.branding = branding
        self.publishing_focus = publishing_focus
        self.status = status
        self.created_at = created_at or datetime.now()
        self.modified_at = modified_at or datetime.now()
        self._persona = persona

    @property
    def display_name(self) -> str:
        """Get the display name from branding or fall back to canonical name."""
        return self.branding.display_name or self.name

    @property
    def is_active(self) -> bool:
        """Check if imprint is currently active."""
        return self.status == ImprintStatus.ACTIVE

    @property
    def persona(self) -> Optional['PublisherPersona']:
        """Get associated publisher persona."""
        return self._persona

    def activate(self) -> None:
        """
        Activate the imprint for publishing.

        Raises:
            ValueError: If imprint is not valid for activation
        """
        if not self.is_valid():
            raise ValueError(
                f"Cannot activate imprint '{self.name}': validation failed. "
                "Ensure branding and publishing focus are complete."
            )
        self.status = ImprintStatus.ACTIVE
        self.modified_at = datetime.now()

    def set_persona(self, persona: 'PublisherPersona') -> None:
        """
        Associate a publisher persona with this imprint.

        Args:
            persona: PublisherPersona to associate
        """
        self._persona = persona
        self.modified_at = datetime.now()

    def is_valid(self) -> bool:
        """
        Validate that imprint meets minimum requirements for activation.

        Returns:
            bool: True if imprint is valid
        """
        return (
            bool(self.name) and
            bool(self.publisher) and
            bool(self.charter) and
            self.branding.is_complete() and
            self.publishing_focus.is_complete()
        )

    def get_config_path(self, base_path: Path) -> Path:
        """
        Get the path where this imprint's configuration should be stored.

        Args:
            base_path: Base directory for imprint configs

        Returns:
            Path: Full path to imprint's config file
        """
        return base_path / f"{self.slug}.json"

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize imprint to dictionary.

        Returns:
            Dict containing all imprint data
        """
        data = {
            'name': self.name,
            'slug': self.slug,
            'publisher': self.publisher,
            'charter': self.charter,
            'branding': self.branding.to_dict(),
            'publishing_focus': self.publishing_focus.to_dict(),
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
        }

        if self._persona:
            data['persona'] = self._persona.to_dict()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Imprint':
        """
        Deserialize imprint from dictionary.

        Args:
            data: Dictionary containing imprint data

        Returns:
            Imprint instance
        """
        # Import here to avoid circular dependency
        from .publisher_persona import PublisherPersona

        branding = BrandingSpecification.from_dict(data.get('branding', {}))
        publishing_focus = PublishingFocus.from_dict(data.get('publishing_focus', {}))

        persona = None
        if 'persona' in data:
            persona = PublisherPersona.from_dict(data['persona'])

        return cls(
            name=data['name'],
            slug=data.get('slug'),
            publisher=data['publisher'],
            charter=data['charter'],
            branding=branding,
            publishing_focus=publishing_focus,
            status=ImprintStatus(data.get('status', 'draft')),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else None,
            modified_at=datetime.fromisoformat(data['modified_at']) if 'modified_at' in data else None,
            persona=persona,
        )

    def _validate_name(self, name: str) -> None:
        """
        Validate imprint name.

        Args:
            name: Name to validate

        Raises:
            ValueError: If name is invalid
        """
        if not name or not name.strip():
            raise ValueError("Imprint name cannot be empty")

        if len(name) > 100:
            raise ValueError("Imprint name cannot exceed 100 characters")

    def _create_slug(self, name: str) -> str:
        """
        Generate URL-safe slug from imprint name.

        Converts to lowercase, replaces spaces with underscores,
        converts '&' to 'and', removes special characters.

        Args:
            name: Name to slugify

        Returns:
            str: URL-safe slug
        """
        # Convert to lowercase
        slug = name.lower()

        # Replace '&' with 'and'
        slug = slug.replace('&', 'and')

        # Replace spaces and hyphens with underscores
        slug = slug.replace(' ', '_').replace('-', '_')

        # Remove special characters, keep only alphanumeric and underscores
        slug = re.sub(r'[^a-z0-9_]', '', slug)

        # Remove multiple consecutive underscores
        slug = re.sub(r'_+', '_', slug)

        # Remove leading/trailing underscores
        slug = slug.strip('_')

        return slug

    def __repr__(self) -> str:
        return (
            f"Imprint(name='{self.name}', slug='{self.slug}', "
            f"status={self.status.value}, valid={self.is_valid()})"
        )

    def __str__(self) -> str:
        return f"{self.display_name} ({self.publisher})"
