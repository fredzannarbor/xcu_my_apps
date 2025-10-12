"""
Simple CodexObject for Stage-Agnostic UI

A lightweight version of CodexObject that doesn't depend on the full ideation module.
This allows the UI to work independently while we integrate with the existing system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


class CodexObjectType(Enum):
    """Enumeration of supported content types."""
    IDEA = "idea"
    LOGLINE = "logline"
    SUMMARY = "summary"
    SYNOPSIS = "synopsis"
    TREATMENT = "treatment"
    OUTLINE = "outline"
    DRAFT = "draft"
    MANUSCRIPT = "manuscript"
    BOOK_IDEA = "book_idea"
    IDEA_WITH_FIELDS = "idea_with_fields"


@dataclass
class SimpleCodexObject:
    """Simple CodexObject for UI use without external dependencies."""
    
    # Core fields
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    object_type: CodexObjectType = CodexObjectType.IDEA
    title: str = ""
    
    # Metadata fields
    word_count: int = 0
    created_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Content classification
    genre: str = ""
    target_audience: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Calculate word count if not provided
        if self.word_count == 0:
            self.word_count = len(self.content.split()) if self.content else 0
        
        # Ensure timestamps are set
        if not self.created_timestamp:
            self.created_timestamp = datetime.now().isoformat()
        if not self.modified_timestamp:
            self.modified_timestamp = self.created_timestamp
    
    def update_content(self, new_content: str):
        """Update the content and refresh metadata."""
        self.content = new_content
        self.word_count = len(new_content.split()) if new_content else 0
        self.modified_timestamp = datetime.now().isoformat()
    
    def add_tag(self, tag: str):
        """Add a tag if it doesn't already exist."""
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.modified_timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'uuid': self.uuid,
            'content': self.content,
            'object_type': self.object_type.value,
            'title': self.title,
            'word_count': self.word_count,
            'created_timestamp': self.created_timestamp,
            'modified_timestamp': self.modified_timestamp,
            'genre': self.genre,
            'target_audience': self.target_audience,
            'tags': self.tags,
            'metadata': self.metadata
        }