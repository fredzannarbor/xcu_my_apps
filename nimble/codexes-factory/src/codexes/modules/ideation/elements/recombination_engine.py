"""
Story element recombination engine.
Combines selected elements to generate new story concepts.
"""

import logging
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional

from ..core.codex_object import CodexObject
from ..llm.ideation_llm_service import IdeationLLMService
from .element_extractor import StoryElement, ElementCategory

logger = logging.getLogger(__name__)


class RecombinationStrategy(Enum):
    """Strategies for recombining elements."""
    THEMATIC_COHERENCE = "thematic_coherence"
    CREATIVE_FUSION = "creative_fusion"
    STRUCTURED_BLEND = "structured_blend"
    EXPERIMENTAL_MIX = "experimental_mix"


@dataclass
class RecombinationConfiguration:
    """Configuration for element recombination."""
    strategy: RecombinationStrategy = RecombinationStrategy.THEMATIC_COHERENCE
    element_count_range: tuple = (3, 7)
    required_categories: List[ElementCategory] = field(default_factory=list)
    forbidden_combinations: List[tuple] = field(default_factory=list)
    creativity_level: float = 0.7
    coherence_threshold: float = 0.6


@dataclass
class RecombinationResult:
    """Result of element recombination."""
    result_uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_concept: Optional[CodexObject] = None
    source_elements: List[StoryElement] = field(default_factory=list)
    recombination_strategy: RecombinationStrategy = RecombinationStrategy.THEMATIC_COHERENCE
    coherence_score: float = 0.0
    creativity_score: float = 0.0
    success: bool = False
    error_message: str = ""
    recombination_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class RecombinationEngine:
    """
    Combines story elements to generate new concepts.
    Implements Requirements 3.4, 3.5, 3.6.
    """
    
    def __init__(self):
        """Initialize recombination engine."""
        self.llm_service = IdeationLLMService()
        self.recombination_history: List[RecombinationResult] = []
        logger.info("RecombinationEngine initialized")
    
    def recombine_elements(self, elements: List[StoryElement],
                         config: RecombinationConfiguration) -> RecombinationResult:
        """
        Recombine story elements into a new concept.
        Implements Requirement 3.4.
        
        Args:
            elements: Available elements for recombination
            config: Recombination configuration
            
        Returns:
            RecombinationResult with generated concept
        """
        try:
            result = RecombinationResult(
                source_elements=elements,
                recombination_strategy=config.strategy
            )
            
            # Validate element selection
            if not self._validate_element_selection(elements, config):
                result.error_message = "Element selection validation failed"
                return result
            
            # Prepare recombination context
            recombination_context = {
                "elements": [element.to_dict() for element in elements],
                "strategy": config.strategy.value,
                "creativity_level": config.creativity_level,
                "coherence_threshold": config.coherence_threshold,
                "element_count": len(elements)
            }
            
            # Generate new concept using LLM
            llm_response = self.llm_service.recombine_elements(recombination_context)
            
            if not llm_response.success or not llm_response.parsed_data:
                result.error_message = f"LLM recombination failed: {llm_response.error_message}"
                return result
            
            # Create new concept from LLM response
            concept_data = llm_response.parsed_data
            
            new_concept = CodexObject(
                title=concept_data.get("title", "Recombined Concept"),
                content=concept_data.get("content", ""),
                genre=concept_data.get("genre", ""),
                target_audience=concept_data.get("target_audience", "")
            )
            
            # Add recombination metadata
            new_concept.source_elements = [element.element_uuid for element in elements]
            new_concept.derived_from = [element.source_concept_uuid for element in elements]
            
            # Calculate scores
            result.coherence_score = concept_data.get("coherence_score", 0.7)
            result.creativity_score = concept_data.get("creativity_score", 0.7)
            result.generated_concept = new_concept
            result.success = True
            
            # Store in history
            self.recombination_history.append(result)
            
            logger.info(f"Successfully recombined {len(elements)} elements into: {new_concept.title}")
            return result
            
        except Exception as e:
            logger.error(f"Error recombining elements: {e}")
            result.error_message = str(e)
            return result
    
    def select_elements_for_recombination(self, available_elements: List[StoryElement],
                                        config: RecombinationConfiguration) -> List[StoryElement]:
        """
        Select optimal elements for recombination.
        Implements Requirement 3.5.
        
        Args:
            available_elements: Pool of available elements
            config: Recombination configuration
            
        Returns:
            Selected elements for recombination
        """
        try:
            # Filter elements based on configuration
            filtered_elements = self._filter_elements(available_elements, config)
            
            if not filtered_elements:
                logger.warning("No elements passed filtering criteria")
                return []
            
            # Determine target count
            min_count, max_count = config.element_count_range
            target_count = random.randint(min_count, min(max_count, len(filtered_elements)))
            
            # Select elements using strategy
            if config.strategy == RecombinationStrategy.THEMATIC_COHERENCE:
                selected = self._select_thematically_coherent(filtered_elements, target_count)
            elif config.strategy == RecombinationStrategy.CREATIVE_FUSION:
                selected = self._select_creative_fusion(filtered_elements, target_count)
            else:
                # Default to random selection
                selected = random.sample(filtered_elements, target_count)
            
            logger.info(f"Selected {len(selected)} elements for recombination using {config.strategy.value}")
            return selected
            
        except Exception as e:
            logger.error(f"Error selecting elements for recombination: {e}")
            return []
    
    def _validate_element_selection(self, elements: List[StoryElement], 
                                  config: RecombinationConfiguration) -> bool:
        """Validate that selected elements meet configuration requirements."""
        try:
            # Check element count
            min_count, max_count = config.element_count_range
            if not (min_count <= len(elements) <= max_count):
                return False
            
            # Check required categories
            if config.required_categories:
                element_categories = set(element.category for element in elements)
                required_categories = set(config.required_categories)
                if not required_categories.issubset(element_categories):
                    return False
            
            # Check forbidden combinations
            for forbidden_pair in config.forbidden_combinations:
                element_uuids = [element.element_uuid for element in elements]
                if forbidden_pair[0] in element_uuids and forbidden_pair[1] in element_uuids:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating element selection: {e}")
            return False
    
    def _filter_elements(self, elements: List[StoryElement], 
                        config: RecombinationConfiguration) -> List[StoryElement]:
        """Filter elements based on configuration criteria."""
        filtered = elements.copy()
        
        # Filter by reusability score
        filtered = [e for e in filtered if e.reusability_score >= 0.3]
        
        # Filter by extraction confidence
        filtered = [e for e in filtered if e.extraction_confidence >= 0.4]
        
        return filtered
    
    def _select_thematically_coherent(self, elements: List[StoryElement], 
                                    target_count: int) -> List[StoryElement]:
        """Select elements that work well together thematically."""
        # Simple implementation - select highest scoring elements
        sorted_elements = sorted(elements, key=lambda e: e.reusability_score + e.uniqueness_score, reverse=True)
        return sorted_elements[:target_count]
    
    def _select_creative_fusion(self, elements: List[StoryElement], 
                              target_count: int) -> List[StoryElement]:
        """Select elements for creative fusion approach."""
        # Mix high uniqueness with high reusability
        high_unique = [e for e in elements if e.uniqueness_score > 0.7]
        high_reusable = [e for e in elements if e.reusability_score > 0.7]
        
        selected = []
        
        # Add some high uniqueness elements
        selected.extend(random.sample(high_unique, min(target_count // 2, len(high_unique))))
        
        # Fill remaining with high reusability
        remaining_count = target_count - len(selected)
        if remaining_count > 0:
            remaining_elements = [e for e in high_reusable if e not in selected]
            selected.extend(random.sample(remaining_elements, min(remaining_count, len(remaining_elements))))
        
        # Fill any remaining slots with random elements
        if len(selected) < target_count:
            remaining_elements = [e for e in elements if e not in selected]
            remaining_count = target_count - len(selected)
            selected.extend(random.sample(remaining_elements, min(remaining_count, len(remaining_elements))))
        
        return selected[:target_count]
    
    def get_recombination_statistics(self) -> Dict[str, Any]:
        """Get statistics about recombination operations."""
        try:
            if not self.recombination_history:
                return {"total_recombinations": 0}
            
            successful_recombinations = [r for r in self.recombination_history if r.success]
            
            stats = {
                "total_recombinations": len(self.recombination_history),
                "successful_recombinations": len(successful_recombinations),
                "success_rate": len(successful_recombinations) / len(self.recombination_history),
                "average_coherence_score": sum(r.coherence_score for r in successful_recombinations) / len(successful_recombinations) if successful_recombinations else 0,
                "average_creativity_score": sum(r.creativity_score for r in successful_recombinations) / len(successful_recombinations) if successful_recombinations else 0,
                "strategy_usage": {}
            }
            
            # Count strategy usage
            for result in self.recombination_history:
                strategy = result.recombination_strategy.value
                stats["strategy_usage"][strategy] = stats["strategy_usage"].get(strategy, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting recombination statistics: {e}")
            return {"error": str(e)}