"""
Element categorization system for story elements.
Categorizes extracted elements into meaningful groups.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ElementCategory(Enum):
    """Categories for story elements."""
    CHARACTER = "character"
    SETTING = "setting"
    THEME = "theme"
    PLOT_DEVICE = "plot_device"
    TONE = "tone"
    CONFLICT = "conflict"
    UNKNOWN = "unknown"


@dataclass
class CategoryConfiguration:
    """Configuration for element categorization."""
    confidence_threshold: float = 0.7
    allow_multiple_categories: bool = False
    default_category: ElementCategory = ElementCategory.UNKNOWN
    category_weights: Dict[str, float] = field(default_factory=lambda: {
        "character": 1.0,
        "setting": 1.0,
        "theme": 1.0,
        "plot_device": 1.0,
        "tone": 1.0,
        "conflict": 1.0
    })


class ElementCategorizer:
    """Categorizes story elements into meaningful groups."""
    
    def __init__(self, config: Optional[CategoryConfiguration] = None):
        """Initialize the element categorizer."""
        self.config = config or CategoryConfiguration()
        logger.info("ElementCategorizer initialized")
    
    def categorize_element(self, element_text: str, element_type: str = "") -> ElementCategory:
        """
        Categorize a story element.
        
        Args:
            element_text: Text description of the element
            element_type: Optional type hint
            
        Returns:
            ElementCategory for the element
        """
        try:
            # Use type hint if provided
            if element_type:
                for category in ElementCategory:
                    if category.value in element_type.lower():
                        return category
            
            # Analyze text content
            text_lower = element_text.lower()
            
            # Character indicators
            character_keywords = ["character", "protagonist", "hero", "villain", "person", "man", "woman"]
            if any(keyword in text_lower for keyword in character_keywords):
                return ElementCategory.CHARACTER
            
            # Setting indicators
            setting_keywords = ["place", "location", "world", "city", "forest", "castle", "space"]
            if any(keyword in text_lower for keyword in setting_keywords):
                return ElementCategory.SETTING
            
            # Theme indicators
            theme_keywords = ["theme", "message", "moral", "lesson", "meaning", "purpose"]
            if any(keyword in text_lower for keyword in theme_keywords):
                return ElementCategory.THEME
            
            # Plot device indicators
            plot_keywords = ["plot", "twist", "device", "structure", "conflict", "resolution"]
            if any(keyword in text_lower for keyword in plot_keywords):
                return ElementCategory.PLOT_DEVICE
            
            # Tone indicators
            tone_keywords = ["tone", "mood", "atmosphere", "feeling", "dark", "light", "serious", "funny"]
            if any(keyword in text_lower for keyword in tone_keywords):
                return ElementCategory.TONE
            
            # Conflict indicators
            conflict_keywords = ["conflict", "struggle", "fight", "battle", "war", "tension"]
            if any(keyword in text_lower for keyword in conflict_keywords):
                return ElementCategory.CONFLICT
            
            return self.config.default_category
            
        except Exception as e:
            logger.error(f"Error categorizing element: {e}")
            return self.config.default_category
    
    def categorize_elements_batch(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Categorize a batch of elements.
        
        Args:
            elements: List of element dictionaries
            
        Returns:
            List of elements with category information added
        """
        categorized_elements = []
        
        for element in elements:
            try:
                element_text = element.get("description", "")
                element_type = element.get("type", "")
                
                category = self.categorize_element(element_text, element_type)
                
                categorized_element = element.copy()
                categorized_element["category"] = category.value
                categorized_element["category_confidence"] = self.config.confidence_threshold
                
                categorized_elements.append(categorized_element)
                
            except Exception as e:
                logger.error(f"Error categorizing element in batch: {e}")
                # Add element with unknown category
                categorized_element = element.copy()
                categorized_element["category"] = ElementCategory.UNKNOWN.value
                categorized_element["category_confidence"] = 0.0
                categorized_elements.append(categorized_element)
        
        return categorized_elements
    
    def get_category_statistics(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about element categories."""
        try:
            category_counts = {}
            total_elements = len(elements)
            
            for element in elements:
                category = element.get("category", ElementCategory.UNKNOWN.value)
                category_counts[category] = category_counts.get(category, 0) + 1
            
            statistics = {
                "total_elements": total_elements,
                "category_counts": category_counts,
                "category_percentages": {}
            }
            
            # Calculate percentages
            for category, count in category_counts.items():
                percentage = (count / total_elements) * 100 if total_elements > 0 else 0
                statistics["category_percentages"][category] = round(percentage, 2)
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting category statistics: {e}")
            return {"error": str(e)}