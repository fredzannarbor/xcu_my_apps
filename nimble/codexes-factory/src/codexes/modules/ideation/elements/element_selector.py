"""
Element selection system for story element recombination.
Provides intelligent selection of elements for recombination.
"""

import logging
import random
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class SelectionStrategy(Enum):
    """Strategies for element selection."""
    RANDOM = "random"
    DIVERSITY_FOCUSED = "diversity_focused"
    COMPATIBILITY_FOCUSED = "compatibility_focused"
    BALANCED = "balanced"


@dataclass
class SelectionCriteria:
    """Criteria for element selection."""
    strategy: SelectionStrategy = SelectionStrategy.BALANCED
    target_element_count: int = 5
    diversity_weight: float = 0.7
    compatibility_weight: float = 0.8
    novelty_weight: float = 0.6
    required_categories: List[str] = field(default_factory=list)
    forbidden_combinations: List[Tuple[str, str]] = field(default_factory=list)
    min_elements_per_category: int = 1
    max_elements_per_category: int = 3


class ElementSelector:
    """Selects elements for recombination based on various criteria."""
    
    def __init__(self):
        """Initialize the element selector."""
        logger.info("ElementSelector initialized")
    
    def select_elements_for_recombination(self, available_elements: List[Dict[str, Any]], 
                                        criteria: SelectionCriteria) -> List[Dict[str, Any]]:
        """
        Select elements for recombination based on criteria.
        
        Args:
            available_elements: List of available elements
            criteria: Selection criteria
            
        Returns:
            List of selected elements
        """
        try:
            if not available_elements:
                return []
            
            if criteria.strategy == SelectionStrategy.RANDOM:
                return self._select_random(available_elements, criteria)
            elif criteria.strategy == SelectionStrategy.DIVERSITY_FOCUSED:
                return self._select_diversity_focused(available_elements, criteria)
            elif criteria.strategy == SelectionStrategy.COMPATIBILITY_FOCUSED:
                return self._select_compatibility_focused(available_elements, criteria)
            else:  # BALANCED
                return self._select_balanced(available_elements, criteria)
                
        except Exception as e:
            logger.error(f"Error selecting elements: {e}")
            # Fallback to random selection
            return random.sample(available_elements, 
                               min(criteria.target_element_count, len(available_elements)))
    
    def _select_random(self, elements: List[Dict[str, Any]], 
                      criteria: SelectionCriteria) -> List[Dict[str, Any]]:
        """Select elements randomly."""
        count = min(criteria.target_element_count, len(elements))
        return random.sample(elements, count)
    
    def _select_diversity_focused(self, elements: List[Dict[str, Any]], 
                                criteria: SelectionCriteria) -> List[Dict[str, Any]]:
        """Select elements focusing on diversity."""
        selected = []
        categories_used = set()
        
        # Group elements by category
        elements_by_category = {}
        for element in elements:
            category = element.get("category", "unknown")
            if category not in elements_by_category:
                elements_by_category[category] = []
            elements_by_category[category].append(element)
        
        # Select from different categories first
        for category, category_elements in elements_by_category.items():
            if len(selected) >= criteria.target_element_count:
                break
            
            if category not in categories_used:
                selected.append(random.choice(category_elements))
                categories_used.add(category)
        
        # Fill remaining slots
        remaining_elements = [e for e in elements if e not in selected]
        while len(selected) < criteria.target_element_count and remaining_elements:
            selected.append(remaining_elements.pop(random.randint(0, len(remaining_elements) - 1)))
        
        return selected
    
    def _select_compatibility_focused(self, elements: List[Dict[str, Any]], 
                                    criteria: SelectionCriteria) -> List[Dict[str, Any]]:
        """Select elements focusing on compatibility."""
        # Start with a seed element
        selected = [random.choice(elements)]
        remaining = [e for e in elements if e != selected[0]]
        
        # Add compatible elements
        while len(selected) < criteria.target_element_count and remaining:
            best_element = None
            best_compatibility = -1
            
            for element in remaining:
                compatibility = self._calculate_compatibility(selected[-1], element)
                if compatibility > best_compatibility:
                    best_compatibility = compatibility
                    best_element = element
            
            if best_element:
                selected.append(best_element)
                remaining.remove(best_element)
            else:
                # Fallback to random if no compatible element found
                selected.append(remaining.pop(random.randint(0, len(remaining) - 1)))
        
        return selected
    
    def _select_balanced(self, elements: List[Dict[str, Any]], 
                       criteria: SelectionCriteria) -> List[Dict[str, Any]]:
        """Select elements using a balanced approach."""
        # Score all elements
        scored_elements = []
        
        for element in elements:
            diversity_score = self._calculate_diversity_score(element, elements)
            compatibility_score = self._calculate_average_compatibility(element, elements)
            novelty_score = self._calculate_novelty_score(element)
            
            total_score = (
                diversity_score * criteria.diversity_weight +
                compatibility_score * criteria.compatibility_weight +
                novelty_score * criteria.novelty_weight
            )
            
            scored_elements.append((element, total_score))
        
        # Sort by score and select top elements
        scored_elements.sort(key=lambda x: x[1], reverse=True)
        selected = [element for element, score in scored_elements[:criteria.target_element_count]]
        
        return selected
    
    def _calculate_compatibility(self, element1: Dict[str, Any], 
                               element2: Dict[str, Any]) -> float:
        """Calculate compatibility between two elements."""
        try:
            # Simple compatibility based on category and genre
            category1 = element1.get("category", "")
            category2 = element2.get("category", "")
            
            # Same category elements are moderately compatible
            if category1 == category2:
                return 0.6
            
            # Different categories are generally compatible
            return 0.8
            
        except Exception as e:
            logger.error(f"Error calculating compatibility: {e}")
            return 0.5
    
    def _calculate_diversity_score(self, element: Dict[str, Any], 
                                 all_elements: List[Dict[str, Any]]) -> float:
        """Calculate diversity score for an element."""
        try:
            category = element.get("category", "unknown")
            category_count = sum(1 for e in all_elements if e.get("category") == category)
            total_elements = len(all_elements)
            
            # Higher score for less common categories
            if total_elements > 0:
                return 1.0 - (category_count / total_elements)
            return 0.5
            
        except Exception as e:
            logger.error(f"Error calculating diversity score: {e}")
            return 0.5
    
    def _calculate_average_compatibility(self, element: Dict[str, Any], 
                                       all_elements: List[Dict[str, Any]]) -> float:
        """Calculate average compatibility with all other elements."""
        try:
            if len(all_elements) <= 1:
                return 1.0
            
            total_compatibility = 0
            count = 0
            
            for other_element in all_elements:
                if other_element != element:
                    compatibility = self._calculate_compatibility(element, other_element)
                    total_compatibility += compatibility
                    count += 1
            
            return total_compatibility / count if count > 0 else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating average compatibility: {e}")
            return 0.5
    
    def _calculate_novelty_score(self, element: Dict[str, Any]) -> float:
        """Calculate novelty score for an element."""
        try:
            # Simple novelty based on description length and uniqueness
            description = element.get("description", "")
            
            # Longer descriptions might be more novel
            length_score = min(len(description) / 100, 1.0)
            
            # Add some randomness for novelty
            randomness = random.random() * 0.3
            
            return (length_score + randomness) / 1.3
            
        except Exception as e:
            logger.error(f"Error calculating novelty score: {e}")
            return 0.5
    
    def validate_selection(self, selected_elements: List[Dict[str, Any]], 
                         criteria: SelectionCriteria) -> Dict[str, Any]:
        """Validate that the selection meets the criteria."""
        try:
            validation_result = {
                "valid": True,
                "issues": [],
                "statistics": {}
            }
            
            # Check element count
            if len(selected_elements) != criteria.target_element_count:
                validation_result["issues"].append(
                    f"Element count mismatch: expected {criteria.target_element_count}, got {len(selected_elements)}"
                )
                validation_result["valid"] = False
            
            # Check category distribution
            categories = {}
            for element in selected_elements:
                category = element.get("category", "unknown")
                categories[category] = categories.get(category, 0) + 1
            
            validation_result["statistics"]["category_distribution"] = categories
            
            # Check required categories
            for required_category in criteria.required_categories:
                if required_category not in categories:
                    validation_result["issues"].append(
                        f"Missing required category: {required_category}"
                    )
                    validation_result["valid"] = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating selection: {e}")
            return {"valid": False, "error": str(e)}