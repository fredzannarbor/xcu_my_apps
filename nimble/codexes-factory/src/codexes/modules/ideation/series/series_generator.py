"""
Series generation system for creating related book concepts.
Manages formulaicness levels and consistency across series entries.
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


class SeriesType(Enum):
    """Types of series that can be generated."""
    STANDALONE_SERIES = "standalone_series"
    SEQUENTIAL_SERIES = "sequential_series"
    CHARACTER_SERIES = "character_series"
    ANTHOLOGY_SERIES = "anthology_series"
    FRANCHISE_SERIES = "franchise_series"


@dataclass
class SeriesConfiguration:
    """Configuration for series generation."""
    series_type: SeriesType = SeriesType.STANDALONE_SERIES
    formulaicness_level: float = 0.5
    target_book_count: int = 3
    consistency_requirements: Dict[str, float] = field(default_factory=lambda: {
        "setting": 0.8,
        "tone": 0.7,
        "genre": 0.9,
        "themes": 0.6,
        "character_types": 0.5
    })
    variation_allowances: Dict[str, float] = field(default_factory=lambda: {
        "plot_structure": 0.3,
        "character_names": 0.1,
        "specific_conflicts": 0.8,
        "subgenres": 0.4
    })
    franchise_mode: bool = False


@dataclass
class SeriesElement:
    """Represents an element that should be consistent across a series."""
    element_type: str
    element_name: str
    description: str
    consistency_level: float = 0.8
    variations: List[str] = field(default_factory=list)
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "element_type": self.element_type,
            "element_name": self.element_name,
            "description": self.description,
            "consistency_level": self.consistency_level,
            "variations": self.variations,
            "usage_count": self.usage_count
        }


@dataclass
class SeriesBlueprint:
    """Blueprint for a book series with consistency requirements."""
    series_uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    series_name: str = ""
    series_type: SeriesType = SeriesType.STANDALONE_SERIES
    formulaicness_level: float = 0.5
    target_book_count: int = 3
    books_generated: int = 0
    consistent_elements: List[SeriesElement] = field(default_factory=list)
    variable_elements: List[str] = field(default_factory=list)
    franchise_mode: bool = False
    created_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "series_uuid": self.series_uuid,
            "series_name": self.series_name,
            "series_type": self.series_type.value,
            "formulaicness_level": self.formulaicness_level,
            "target_book_count": self.target_book_count,
            "books_generated": self.books_generated,
            "consistent_elements": [e.to_dict() for e in self.consistent_elements],
            "variable_elements": self.variable_elements,
            "franchise_mode": self.franchise_mode,
            "created_timestamp": self.created_timestamp,
            "last_updated": self.last_updated
        }


class SeriesGenerator:
    """Generates book series with configurable consistency levels."""
    
    def __init__(self):
        """Initialize the series generator."""
        self.llm_service = IdeationLLMService()
        self.generated_series: Dict[str, SeriesBlueprint] = {}
        logger.info("SeriesGenerator initialized")
    
    def create_series_blueprint(self, base_concept: CodexObject, 
                              config: SeriesConfiguration) -> SeriesBlueprint:
        """Create a blueprint for a book series."""
        try:
            series_name = self._generate_series_name(base_concept, config)
            consistent_elements = self._extract_consistent_elements(base_concept, config)
            variable_elements = self._identify_variable_elements(base_concept, config)
            
            blueprint = SeriesBlueprint(
                series_name=series_name,
                series_type=config.series_type,
                formulaicness_level=config.formulaicness_level,
                consistent_elements=consistent_elements,
                variable_elements=variable_elements,
                target_book_count=config.target_book_count,
                franchise_mode=config.franchise_mode
            )
            
            self.generated_series[blueprint.series_uuid] = blueprint
            logger.info(f"Created series blueprint: {series_name}")
            return blueprint
            
        except Exception as e:
            logger.error(f"Error creating series blueprint: {e}")
            raise
    
    def generate_series_entry(self, blueprint: SeriesBlueprint, 
                            entry_number: int) -> CodexObject:
        """Generate a new entry in the series."""
        try:
            series_context = {
                "series_name": blueprint.series_name,
                "series_type": blueprint.series_type.value,
                "formulaicness_level": blueprint.formulaicness_level,
                "entry_number": entry_number,
                "total_planned_entries": blueprint.target_book_count,
                "consistent_elements": [e.to_dict() for e in blueprint.consistent_elements],
                "variable_elements": blueprint.variable_elements,
                "franchise_mode": blueprint.franchise_mode
            }
            
            llm_response = self.llm_service.generate_series_entry(series_context)
            
            if not llm_response.success or not llm_response.parsed_data:
                raise ValueError(f"Failed to generate series entry: {llm_response.error_message}")
            
            entry_data = llm_response.parsed_data
            
            series_entry = CodexObject(
                title=entry_data.get("title", f"{blueprint.series_name} Book {entry_number}"),
                content=entry_data.get("premise", ""),
                genre=entry_data.get("genre", ""),
                target_audience=entry_data.get("target_audience", "")
            )
            
            series_entry.series_uuid = blueprint.series_uuid
            blueprint.books_generated += 1
            blueprint.last_updated = datetime.now().isoformat()
            
            self._update_element_usage(blueprint, series_entry)
            
            logger.info(f"Generated series entry {entry_number}: {series_entry.title}")
            return series_entry
            
        except Exception as e:
            logger.error(f"Error generating series entry: {e}")
            raise
    
    def generate_complete_series(self, base_concept: CodexObject,
                               config: SeriesConfiguration) -> List[CodexObject]:
        """Generate a complete series from a base concept."""
        try:
            blueprint = self.create_series_blueprint(base_concept, config)
            series_entries = []
            
            for entry_num in range(1, config.target_book_count + 1):
                try:
                    entry = self.generate_series_entry(blueprint, entry_num)
                    series_entries.append(entry)
                    
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Failed to generate series entry {entry_num}: {e}")
                    continue
            
            logger.info(f"Generated complete series: {len(series_entries)}/{config.target_book_count} entries")
            return series_entries
            
        except Exception as e:
            logger.error(f"Error generating complete series: {e}")
            raise
    
    def get_series_statistics(self, series_uuid: str) -> Dict[str, Any]:
        """Get statistics for a series."""
        try:
            blueprint = self.generated_series.get(series_uuid)
            if not blueprint:
                return {"error": "Series not found"}
            
            stats = {
                "series_info": {
                    "series_uuid": blueprint.series_uuid,
                    "series_name": blueprint.series_name,
                    "series_type": blueprint.series_type.value,
                    "formulaicness_level": blueprint.formulaicness_level,
                    "franchise_mode": blueprint.franchise_mode
                },
                "progress": {
                    "books_generated": blueprint.books_generated,
                    "target_book_count": blueprint.target_book_count,
                    "completion_percentage": (blueprint.books_generated / blueprint.target_book_count) * 100 if blueprint.target_book_count > 0 else 0
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting series statistics: {e}")
            return {"error": str(e)}
    
    def _generate_series_name(self, base_concept: CodexObject, 
                            config: SeriesConfiguration) -> str:
        """Generate a name for the series."""
        try:
            context = {
                "base_title": base_concept.title,
                "genre": base_concept.genre,
                "content": base_concept.content,
                "series_type": config.series_type.value,
                "franchise_mode": config.franchise_mode
            }
            
            llm_response = self.llm_service.generate_series_name(context)
            
            if llm_response.success and llm_response.parsed_data:
                return llm_response.parsed_data.get("series_name", f"{base_concept.title} Series")
            else:
                return f"{base_concept.title} Series"
                
        except Exception as e:
            logger.error(f"Error generating series name: {e}")
            return f"{base_concept.title} Series"
    
    def _extract_consistent_elements(self, base_concept: CodexObject,
                                   config: SeriesConfiguration) -> List[SeriesElement]:
        """Extract elements that should remain consistent across the series."""
        elements = []
        
        if base_concept.genre and config.consistency_requirements.get("genre", 0) > 0:
            elements.append(SeriesElement(
                element_type="genre",
                element_name="primary_genre",
                description=base_concept.genre,
                consistency_level=config.consistency_requirements["genre"]
            ))
        
        return elements
    
    def _identify_variable_elements(self, base_concept: CodexObject,
                                  config: SeriesConfiguration) -> List[str]:
        """Identify elements that should vary across series entries."""
        variable_elements = []
        
        if config.variation_allowances.get("plot_structure", 0) > 0:
            variable_elements.append("plot_structure")
        
        if config.variation_allowances.get("specific_conflicts", 0) > 0:
            variable_elements.append("specific_conflicts")
        
        return variable_elements
    
    def _update_element_usage(self, blueprint: SeriesBlueprint, 
                            series_entry: CodexObject):
        """Update usage counts for series elements."""
        try:
            for element in blueprint.consistent_elements:
                element_used = False
                
                if element.element_type == "genre" and element.description.lower() in series_entry.genre.lower():
                    element_used = True
                
                if element_used:
                    element.usage_count += 1
                    
        except Exception as e:
            logger.error(f"Error updating element usage: {e}")