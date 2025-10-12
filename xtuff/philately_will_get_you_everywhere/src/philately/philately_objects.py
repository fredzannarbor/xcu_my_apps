from dataclasses import dataclass
from typing import Optional, Union
from abc import ABC
import uuid

@dataclass
class CollectibleObjects(ABC):
    """
    Abstract base class for collectible items.
    Defines common attributes for all collectible types.
    """
    id: str
    name: str
    description: str
    estimated_value: str
    condition: str
    deacquired: bool

    def __post_init__(self):
        # Ensure id is set if not provided
        if not self.id:
            self.id = str(uuid.uuid4())

@dataclass
class PhilatelyObjects(CollectibleObjects):
    """
    Data class for philatelic items (stamps, covers, etc.).
    Encapsulates all fields required by consumer scripts for cataloging, UI display,
    and valuation.
    """
    album: str = ""
    page_filename: str = ""
    page_number_in_album: Optional[Union[int, float]] = None
    nationality: str = "Unknown"
    year: Union[str, int] = "Unknown"
    face_value: str = "Unknown"
    collectibility_notes: str = ""
    owner_notes: str = ""
    thumbnail_path: str = ""
    cropped_image_path: str = ""
    ai_model_used: str = ""
    philately_summary: Optional[str] = None
    collection_philately_summary: Optional[str] = None
    thumbnail_path_display: Optional[str] = None
    cropped_image_path_display: Optional[str] = None
    page_filename_display: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        # Normalize deacquired to boolean
        if isinstance(self.deacquired, str):
            self.deacquired = self.deacquired.upper() == "TRUE"
        # Default id to UUID if not provided
        if not self.id:
            self.id = str(uuid.uuid4())
        # Set name as common_name if not provided
        if not self.name:
            self.name = "Unnamed Stamp"

    @classmethod
    def from_dict(cls, data: dict) -> 'PhilatelyObjects':
        """Create an instance from a dictionary (e.g., from CSV or JSON)."""
        return cls(
            id=data.get("stamp_id", ""),
            name=data.get("common_name", "Unnamed Stamp"),
            description=data.get("description", ""),
            estimated_value=data.get("estimated_value", "Unknown"),
            condition=data.get("condition", "Unknown"),
            deacquired=data.get("deacquired", False),
            album=data.get("album", ""),
            page_filename=data.get("page_filename", ""),
            page_number_in_album=data.get("page_number_in_album"),
            nationality=data.get("nationality", "Unknown"),
            year=data.get("year", "Unknown"),
            face_value=data.get("face_value", "Unknown"),
            collectibility_notes=data.get("collectibility_notes", ""),
            owner_notes=data.get("owner_notes", ""),
            thumbnail_path=data.get("thumbnail_path", ""),
            cropped_image_path=data.get("cropped_image_path", ""),
            ai_model_used=data.get("ai_model_used", ""),
            philately_summary=data.get("philately_summary"),
            collection_philately_summary=data.get("collection_philately_summary"),
            thumbnail_path_display=data.get("thumbnail_path_display"),
            cropped_image_path_display=data.get("cropped_image_path_display"),
            page_filename_display=data.get("page_filename_display")
        )

    def to_dict(self) -> dict:
        """Convert instance to dictionary for serialization to CSV/JSON."""
        return {
            "stamp_id": self.id,
            "common_name": self.name,
            "description": self.description,
            "estimated_value": self.estimated_value,
            "condition": self.condition,
            "deacquired": self.deacquired,
            "album": self.album,
            "page_filename": self.page_filename,
            "page_number_in_album": self.page_number_in_album,
            "nationality": self.nationality,
            "year": self.year,
            "face_value": self.face_value,
            "collectibility_notes": self.collectibility_notes,
            "owner_notes": self.owner_notes,
            "thumbnail_path": self.thumbnail_path,
            "cropped_image_path": self.cropped_image_path,
            "ai_model_used": self.ai_model_used,
            "philately_summary": self.philately_summary,
            "collection_philately_summary": self.collection_philately_summary,
            "thumbnail_path_display": self.thumbnail_path_display,
            "cropped_image_path_display": self.cropped_image_path_display,
            "page_filename_display": self.page_filename_display
        }