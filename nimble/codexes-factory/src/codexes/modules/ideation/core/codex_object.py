"""
CodexObject: Base class for all creative content objects in the ideation system.
Supports stage/length-agnostic processing from ideas to complete manuscripts.
"""

import uuid
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from codexes.modules.metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


class CodexObjectType(Enum):
    """Enumeration of supported content types."""
    IDEA = "idea"
    LOGLINE = "logline"
    SUMMARY = "summary"
    TREATMENT = "treatment"
    SYNOPSIS = "synopsis"
    OUTLINE = "outline"
    DETAILED_OUTLINE = "detailed_outline"
    DRAFT = "draft"
    MANUSCRIPT = "manuscript"
    SERIES = "series"
    UNKNOWN = "unknown"


class DevelopmentStage(Enum):
    """Enumeration of development stages."""
    CONCEPT = "concept"
    DEVELOPMENT = "development"
    DRAFT = "draft"
    REVISION = "revision"
    COMPLETE = "complete"
    PUBLISHED = "published"


@dataclass
class CodexObject:
    """
    Base class for all creative content objects in the ideation system.
    Supports stage/length-agnostic processing and seamless integration with CodexMetadata.
    """
    
    # Core identifiers
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    shortuuid: str = field(init=False)
    object_type: CodexObjectType = CodexObjectType.UNKNOWN
    development_stage: DevelopmentStage = DevelopmentStage.CONCEPT
    
    # Content fields
    title: str = ""
    content: str = ""
    logline: str = ""
    description: str = ""
    
    # Classification and metadata
    genre: str = ""
    target_audience: str = ""
    confidence_score: float = 0.0
    word_count: int = 0
    
    # Relationships and provenance
    parent_uuid: Optional[str] = None
    series_uuid: Optional[str] = None
    source_elements: List[str] = field(default_factory=list)
    derived_from: List[str] = field(default_factory=list)
    
    # Processing metadata
    created_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    processing_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # LLM interaction data
    llm_responses: Dict[str, Any] = field(default_factory=dict)
    generation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Tournament and evaluation data
    tournament_performance: Dict[str, Any] = field(default_factory=dict)
    reader_feedback: List[Dict[str, Any]] = field(default_factory=list)
    evaluation_scores: Dict[str, float] = field(default_factory=dict)
    
    # Status and workflow
    status: str = "created"  # created, classified, developed, evaluated, approved, rejected
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def __post_init__(self):
        """Initialize and validate the CodexObject."""
        self.shortuuid = self.uuid[:8]
        
        # Ensure we have some content
        if not any([self.title, self.content, self.logline, self.description]):
            logger.warning(f"CodexObject {self.shortuuid} created without any content")
        
        # Auto-detect word count if content is provided
        if self.content and self.word_count == 0:
            self.word_count = len(self.content.split())
        
        # Set initial processing history entry
        if not self.processing_history:
            self.processing_history.append({
                "action": "created",
                "timestamp": self.created_timestamp,
                "details": {"object_type": self.object_type.value}
            })
    
    def update_content(self, content: str, update_type: str = "manual_edit"):
        """Update the content and track the change."""
        old_word_count = self.word_count
        self.content = content
        self.word_count = len(content.split()) if content else 0
        self.last_modified = datetime.now().isoformat()
        
        # Add to processing history
        self.processing_history.append({
            "action": "content_updated",
            "timestamp": self.last_modified,
            "details": {
                "update_type": update_type,
                "old_word_count": old_word_count,
                "new_word_count": self.word_count
            }
        })
    
    def set_classification(self, object_type: CodexObjectType, confidence: float, 
                          classifier_info: Dict[str, Any] = None):
        """Set the classification for this object."""
        old_type = self.object_type
        self.object_type = object_type
        self.confidence_score = confidence
        self.last_modified = datetime.now().isoformat()
        
        # Add to processing history
        self.processing_history.append({
            "action": "classified",
            "timestamp": self.last_modified,
            "details": {
                "old_type": old_type.value,
                "new_type": object_type.value,
                "confidence": confidence,
                "classifier_info": classifier_info or {}
            }
        })
        
        # Update status if this is the first classification
        if self.status == "created":
            self.status = "classified"
    
    def add_evaluation_score(self, evaluator: str, score: float, details: Dict[str, Any] = None):
        """Add an evaluation score from a specific evaluator."""
        self.evaluation_scores[evaluator] = score
        self.last_modified = datetime.now().isoformat()
        
        # Add to processing history
        self.processing_history.append({
            "action": "evaluated",
            "timestamp": self.last_modified,
            "details": {
                "evaluator": evaluator,
                "score": score,
                "evaluation_details": details or {}
            }
        })
    
    def add_reader_feedback(self, feedback: Dict[str, Any]):
        """Add synthetic reader feedback."""
        feedback["timestamp"] = datetime.now().isoformat()
        self.reader_feedback.append(feedback)
        self.last_modified = datetime.now().isoformat()
        
        # Add to processing history
        self.processing_history.append({
            "action": "reader_feedback_added",
            "timestamp": self.last_modified,
            "details": {"feedback_id": len(self.reader_feedback)}
        })
    
    def transform_to_type(self, target_type: CodexObjectType, 
                         transformation_details: Dict[str, Any] = None) -> 'CodexObject':
        """Create a new CodexObject of the target type based on this one."""
        # Create new object with transformed content
        new_object = CodexObject(
            object_type=target_type,
            title=self.title,
            content=self.content,
            logline=self.logline,
            description=self.description,
            genre=self.genre,
            target_audience=self.target_audience,
            parent_uuid=self.uuid,
            series_uuid=self.series_uuid,
            derived_from=self.derived_from + [self.uuid],
            tags=self.tags.copy(),
            development_stage=DevelopmentStage.DEVELOPMENT
        )
        
        # Add transformation record to both objects
        transformation_record = {
            "action": "transformed",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "source_type": self.object_type.value,
                "target_type": target_type.value,
                "source_uuid": self.uuid,
                "target_uuid": new_object.uuid,
                "transformation_details": transformation_details or {}
            }
        }
        
        self.processing_history.append(transformation_record)
        new_object.processing_history.append(transformation_record)
        
        return new_object
    
    def to_codex_metadata(self) -> CodexMetadata:
        """Convert CodexObject to CodexMetadata for pipeline integration."""
        metadata = CodexMetadata()
        
        # Map core fields
        metadata.uuid = self.uuid
        metadata.title = self.title
        metadata.summary_short = self.logline or (self.content[:500] if len(self.content) > 500 else self.content)
        metadata.summary_long = self.description or self.content
        metadata.keywords = "; ".join(self.tags) if self.tags else ""
        
        # Map genre and audience
        if self.genre:
            metadata.bisac_text = self.genre
        if self.target_audience:
            metadata.audience = self.target_audience
        
        # Map word count and content info
        metadata.word_count = self.word_count
        
        # Store ideation-specific data in raw_llm_responses for preservation
        metadata.raw_llm_responses["ideation_data"] = {
            "object_type": self.object_type.value,
            "development_stage": self.development_stage.value,
            "confidence_score": self.confidence_score,
            "tournament_performance": self.tournament_performance,
            "reader_feedback": self.reader_feedback,
            "evaluation_scores": self.evaluation_scores,
            "processing_history": self.processing_history,
            "generation_metadata": self.generation_metadata,
            "parent_uuid": self.parent_uuid,
            "series_uuid": self.series_uuid,
            "source_elements": self.source_elements,
            "derived_from": self.derived_from
        }
        
        return metadata
    
    @classmethod
    def from_codex_metadata(cls, metadata: CodexMetadata) -> 'CodexObject':
        """Create CodexObject from existing CodexMetadata."""
        # Extract ideation data if available
        ideation_data = metadata.raw_llm_responses.get("ideation_data", {})
        
        # Determine object type from content length and structure
        object_type = CodexObjectType.UNKNOWN
        if ideation_data.get("object_type"):
            try:
                object_type = CodexObjectType(ideation_data["object_type"])
            except ValueError:
                object_type = CodexObjectType.UNKNOWN
        elif metadata.word_count:
            if metadata.word_count < 50:
                object_type = CodexObjectType.LOGLINE
            elif metadata.word_count < 500:
                object_type = CodexObjectType.SUMMARY
            elif metadata.word_count < 2000:
                object_type = CodexObjectType.SYNOPSIS
            elif metadata.word_count < 10000:
                object_type = CodexObjectType.OUTLINE
            else:
                object_type = CodexObjectType.MANUSCRIPT
        
        # Create CodexObject
        codex_object = cls(
            uuid=metadata.uuid,
            object_type=object_type,
            title=metadata.title,
            content=metadata.summary_long,
            logline=metadata.summary_short,
            description=metadata.summary_long,
            genre=metadata.bisac_text,
            target_audience=metadata.audience,
            word_count=metadata.word_count,
            tags=metadata.keywords.split("; ") if metadata.keywords else []
        )
        
        # Restore ideation-specific data if available
        if ideation_data:
            codex_object.confidence_score = ideation_data.get("confidence_score", 0.0)
            codex_object.tournament_performance = ideation_data.get("tournament_performance", {})
            codex_object.reader_feedback = ideation_data.get("reader_feedback", [])
            codex_object.evaluation_scores = ideation_data.get("evaluation_scores", {})
            codex_object.processing_history = ideation_data.get("processing_history", [])
            codex_object.generation_metadata = ideation_data.get("generation_metadata", {})
            codex_object.parent_uuid = ideation_data.get("parent_uuid")
            codex_object.series_uuid = ideation_data.get("series_uuid")
            codex_object.source_elements = ideation_data.get("source_elements", [])
            codex_object.derived_from = ideation_data.get("derived_from", [])
            
            # Set development stage
            try:
                codex_object.development_stage = DevelopmentStage(
                    ideation_data.get("development_stage", "concept")
                )
            except ValueError:
                codex_object.development_stage = DevelopmentStage.CONCEPT
        
        return codex_object
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert CodexObject to dictionary format."""
        data = asdict(self)
        
        # Convert enums to strings
        data["object_type"] = self.object_type.value
        data["development_stage"] = self.development_stage.value
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodexObject':
        """Create CodexObject from dictionary format."""
        # Convert string enums back to enum objects
        if "object_type" in data and isinstance(data["object_type"], str):
            try:
                data["object_type"] = CodexObjectType(data["object_type"])
            except ValueError:
                data["object_type"] = CodexObjectType.UNKNOWN
        
        if "development_stage" in data and isinstance(data["development_stage"], str):
            try:
                data["development_stage"] = DevelopmentStage(data["development_stage"])
            except ValueError:
                data["development_stage"] = DevelopmentStage.CONCEPT
        
        return cls(**data)
    
    def save_to_file(self, file_path: str):
        """Save CodexObject to JSON file."""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"CodexObject {self.shortuuid} saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save CodexObject to {file_path}: {e}")
            raise
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'CodexObject':
        """Load CodexObject from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load CodexObject from {file_path}: {e}")
            raise
    
    def is_specific_enough_for_development(self) -> bool:
        """Determine if this object has enough detail for further development."""
        # Check basic content requirements
        has_title = bool(self.title and len(self.title.strip()) > 5)
        has_content = bool(self.content and len(self.content.strip()) > 20)
        has_logline = bool(self.logline and len(self.logline.strip()) > 10)
        
        # Minimum requirements vary by type
        if self.object_type == CodexObjectType.IDEA:
            return has_title and (has_content or has_logline)
        elif self.object_type == CodexObjectType.LOGLINE:
            return has_logline and len(self.logline.strip()) > 20
        elif self.object_type in [CodexObjectType.SUMMARY, CodexObjectType.SYNOPSIS]:
            return has_title and has_content and len(self.content.strip()) > 100
        elif self.object_type in [CodexObjectType.OUTLINE, CodexObjectType.DETAILED_OUTLINE]:
            return has_title and has_content and len(self.content.strip()) > 500
        elif self.object_type in [CodexObjectType.DRAFT, CodexObjectType.MANUSCRIPT]:
            return has_title and has_content and len(self.content.strip()) > 1000
        else:
            # Unknown type - use basic heuristics
            return has_title and (has_content or has_logline)
    
    def get_development_suggestions(self) -> List[str]:
        """Get suggestions for developing this object further."""
        suggestions = []
        
        if not self.title:
            suggestions.append("Add a compelling title")
        
        if not self.logline:
            suggestions.append("Create a one-sentence logline")
        
        if not self.genre:
            suggestions.append("Specify the genre")
        
        if not self.target_audience:
            suggestions.append("Define the target audience")
        
        if self.word_count < 50 and self.object_type != CodexObjectType.LOGLINE:
            suggestions.append("Expand the content with more detail")
        
        if not self.tags:
            suggestions.append("Add relevant tags for categorization")
        
        # Type-specific suggestions
        if self.object_type == CodexObjectType.IDEA:
            suggestions.append("Develop into a synopsis or outline")
        elif self.object_type == CodexObjectType.SYNOPSIS:
            suggestions.append("Create a detailed outline")
        elif self.object_type == CodexObjectType.OUTLINE:
            suggestions.append("Develop into a detailed outline or first draft")
        
        return suggestions
    
    def __str__(self) -> str:
        """String representation of the CodexObject."""
        return f"CodexObject({self.object_type.value}): {self.title[:50]}..."
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"CodexObject(uuid='{self.shortuuid}', type='{self.object_type.value}', "
                f"title='{self.title[:30]}...', status='{self.status}')")