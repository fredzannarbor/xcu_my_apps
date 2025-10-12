"""
Story element extraction system.
Extracts and categorizes story elements from CodexObjects.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional

from ..core.codex_object import CodexObject
from ..llm.ideation_llm_service import IdeationLLMService

logger = logging.getLogger(__name__)


class ElementCategory(Enum):
    """Categories of story elements."""
    CHARACTER = "character"
    SETTING = "setting"
    THEME = "theme"
    PLOT_DEVICE = "plot_device"
    TONE_ELEMENT = "tone_element"
    CONFLICT = "conflict"
    GENRE_ELEMENT = "genre_element"


@dataclass
class StoryElement:
    """Represents an extracted story element."""
    element_uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: ElementCategory = ElementCategory.THEME
    name: str = ""
    description: str = ""
    source_concept_uuid: str = ""
    uniqueness_score: float = 0.5
    reusability_score: float = 0.5
    extraction_confidence: float = 0.5
    tags: List[str] = field(default_factory=list)
    extracted_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "element_uuid": self.element_uuid,
            "category": self.category.value,
            "name": self.name,
            "description": self.description,
            "source_concept_uuid": self.source_concept_uuid,
            "uniqueness_score": self.uniqueness_score,
            "reusability_score": self.reusability_score,
            "extraction_confidence": self.extraction_confidence,
            "tags": self.tags,
            "extracted_timestamp": self.extracted_timestamp
        }


class ElementExtractor:
    """
    Extracts story elements from CodexObjects.
    Implements Requirements 3.1, 3.2, 3.3.
    """
    
    def __init__(self):
        """Initialize element extractor."""
        self.llm_service = IdeationLLMService()
        self.extracted_elements: Dict[str, List[StoryElement]] = {}
        logger.info("ElementExtractor initialized")
    
    def extract_elements_from_concept(self, codex_object: CodexObject) -> List[StoryElement]:
        """
        Extract story elements from a single CodexObject.
        Implements Requirement 3.1.
        
        Args:
            codex_object: CodexObject to extract elements from
            
        Returns:
            List of extracted StoryElement objects
        """
        try:
            extraction_context = {
                "title": codex_object.title,
                "content": codex_object.content,
                "genre": codex_object.genre,
                "target_audience": codex_object.target_audience
            }
            
            llm_response = self.llm_service.extract_story_elements(extraction_context)
            
            if not llm_response.success or not llm_response.parsed_data:
                logger.warning(f"Failed to extract elements from {codex_object.title}")
                return []
            
            elements = []
            element_data = llm_response.parsed_data
            
            # Process each category of elements
            for category_name, category_elements in element_data.items():
                try:
                    category = ElementCategory(category_name.lower())
                except ValueError:
                    logger.warning(f"Unknown element category: {category_name}")
                    continue
                
                for element_info in category_elements:
                    element = StoryElement(
                        category=category,
                        name=element_info.get("name", ""),
                        description=element_info.get("description", ""),
                        source_concept_uuid=codex_object.uuid,
                        uniqueness_score=element_info.get("uniqueness_score", 0.5),
                        reusability_score=element_info.get("reusability_score", 0.5),
                        extraction_confidence=element_info.get("confidence", 0.5),
                        tags=element_info.get("tags", [])
                    )
                    elements.append(element)
            
            # Store extracted elements
            if codex_object.uuid not in self.extracted_elements:
                self.extracted_elements[codex_object.uuid] = []
            self.extracted_elements[codex_object.uuid].extend(elements)
            
            logger.info(f"Extracted {len(elements)} elements from {codex_object.title}")
            return elements
            
        except Exception as e:
            logger.error(f"Error extracting elements from concept: {e}")
            return []
    
    def extract_elements_from_concepts(self, codex_objects: List[CodexObject]) -> List[StoryElement]:
        """
        Extract story elements from multiple CodexObjects.
        Implements Requirement 3.2.
        
        Args:
            codex_objects: List of CodexObjects to extract elements from
            
        Returns:
            List of all extracted StoryElement objects
        """
        try:
            all_elements = []
            
            for codex_object in codex_objects:
                elements = self.extract_elements_from_concept(codex_object)
                all_elements.extend(elements)
            
            logger.info(f"Extracted {len(all_elements)} total elements from {len(codex_objects)} concepts")
            return all_elements
            
        except Exception as e:
            logger.error(f"Error extracting elements from concepts: {e}")
            return []
    
    def categorize_elements(self, elements: List[StoryElement]) -> Dict[ElementCategory, List[StoryElement]]:
        """
        Categorize story elements by type.
        Implements Requirement 3.3.
        
        Args:
            elements: List of StoryElements to categorize
            
        Returns:
            Dictionary mapping categories to lists of elements
        """
        try:
            categorized = {}
            
            for element in elements:
                if element.category not in categorized:
                    categorized[element.category] = []
                categorized[element.category].append(element)
            
            logger.info(f"Categorized {len(elements)} elements into {len(categorized)} categories")
            return categorized
            
        except Exception as e:
            logger.error(f"Error categorizing elements: {e}")
            return {}
    
    def recombine_elements(self, elements: List[StoryElement]) -> CodexObject:
        """
        Recombine story elements into a new concept.
        
        Args:
            elements: List of StoryElements to recombine
            
        Returns:
            New CodexObject created from recombined elements
        """
        try:
            recombination_context = {
                "elements": [element.to_dict() for element in elements],
                "element_count": len(elements),
                "categories": list(set(element.category.value for element in elements))
            }
            
            llm_response = self.llm_service.recombine_elements(recombination_context)
            
            if not llm_response.success or not llm_response.parsed_data:
                logger.warning("Failed to recombine elements")
                return None
            
            recombined_data = llm_response.parsed_data
            
            new_concept = CodexObject(
                title=recombined_data.get("title", "Recombined Concept"),
                content=recombined_data.get("content", ""),
                genre=recombined_data.get("genre", ""),
                target_audience=recombined_data.get("target_audience", "")
            )
            
            # Add metadata about source elements
            new_concept.source_elements = [element.element_uuid for element in elements]
            
            logger.info(f"Recombined {len(elements)} elements into new concept: {new_concept.title}")
            return new_concept
            
        except Exception as e:
            logger.error(f"Error recombining elements: {e}")
            return None
    
    def get_element_statistics(self) -> Dict[str, Any]:
        """Get statistics about extracted elements."""
        try:
            total_elements = sum(len(elements) for elements in self.extracted_elements.values())
            
            category_counts = {}
            uniqueness_scores = []
            reusability_scores = []
            
            for elements in self.extracted_elements.values():
                for element in elements:
                    category = element.category.value
                    category_counts[category] = category_counts.get(category, 0) + 1
                    uniqueness_scores.append(element.uniqueness_score)
                    reusability_scores.append(element.reusability_score)
            
            stats = {
                "total_elements": total_elements,
                "total_concepts_processed": len(self.extracted_elements),
                "category_distribution": category_counts,
                "average_uniqueness": sum(uniqueness_scores) / len(uniqueness_scores) if uniqueness_scores else 0,
                "average_reusability": sum(reusability_scores) / len(reusability_scores) if reusability_scores else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting element statistics: {e}")
            return {"error": str(e)}
    
    def export_elements(self, format: str = "json") -> Dict[str, Any]:
        """Export extracted elements for storage or sharing."""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_concepts": len(self.extracted_elements),
                "elements_by_concept": {}
            }
            
            for concept_uuid, elements in self.extracted_elements.items():
                export_data["elements_by_concept"][concept_uuid] = [
                    element.to_dict() for element in elements
                ]
            
            export_data["statistics"] = self.get_element_statistics()
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting elements: {e}")
            return {"error": str(e)}