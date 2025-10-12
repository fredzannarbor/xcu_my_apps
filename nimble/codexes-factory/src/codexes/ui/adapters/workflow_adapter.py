"""
Workflow Adapter

Adapts workflows to handle mixed content types and provides unified interfaces
for different workflow systems (tournaments, reader panels, series generation).
"""

import logging
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType

logger = logging.getLogger(__name__)


class MixedTypeHandling(Enum):
    """Strategies for handling mixed content types in workflows."""
    ADAPTIVE = "adaptive"  # Adapt evaluation criteria for each type
    NORMALIZE = "normalize"  # Convert all to common type before processing
    TYPE_AWARE = "type_aware"  # Use type-specific evaluation but allow comparison
    SEPARATE = "separate"  # Process each type separately


@dataclass
class WorkflowAdaptation:
    """Configuration for workflow adaptation to mixed types."""
    handling_strategy: MixedTypeHandling
    type_weights: Dict[str, float]  # Weights for different content types
    evaluation_adjustments: Dict[str, Dict[str, float]]  # Type-specific evaluation adjustments
    comparison_method: str = "normalized_scoring"  # How to compare across types
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "handling_strategy": self.handling_strategy.value,
            "type_weights": self.type_weights,
            "evaluation_adjustments": self.evaluation_adjustments,
            "comparison_method": self.comparison_method
        }


class WorkflowAdapter:
    """
    Adapts workflows to handle mixed content types and provides unified interfaces.
    Implements Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6 for adaptive workflow configuration.
    """
    
    def __init__(self):
        """Initialize the workflow adapter."""
        self.type_characteristics = self._initialize_type_characteristics()
        self.evaluation_mappings = self._initialize_evaluation_mappings()
        logger.info("WorkflowAdapter initialized")
    
    def analyze_content_mix(self, objects: List[CodexObject]) -> Dict[str, Any]:
        """
        Analyze the mix of content types in a collection.
        
        Args:
            objects: List of CodexObjects to analyze
            
        Returns:
            Analysis of content type distribution and characteristics
        """
        if not objects:
            return {"error": "No objects provided"}
        
        # Count types
        type_counts = {}
        type_characteristics = {}
        
        for obj in objects:
            obj_type = obj.object_type.value
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
            
            # Analyze characteristics
            if obj_type not in type_characteristics:
                type_characteristics[obj_type] = {
                    "word_counts": [],
                    "complexity_scores": [],
                    "development_stages": []
                }
            
            type_characteristics[obj_type]["word_counts"].append(obj.word_count)
            type_characteristics[obj_type]["complexity_scores"].append(self._calculate_complexity_score(obj))
            type_characteristics[obj_type]["development_stages"].append(self._assess_development_stage(obj))
        
        # Calculate statistics
        total_objects = len(objects)
        type_distribution = {
            obj_type: {
                "count": count,
                "percentage": (count / total_objects) * 100,
                "avg_word_count": sum(type_characteristics[obj_type]["word_counts"]) / count,
                "avg_complexity": sum(type_characteristics[obj_type]["complexity_scores"]) / count,
                "development_range": {
                    "min": min(type_characteristics[obj_type]["development_stages"]),
                    "max": max(type_characteristics[obj_type]["development_stages"]),
                    "avg": sum(type_characteristics[obj_type]["development_stages"]) / count
                }
            }
            for obj_type, count in type_counts.items()
        }
        
        # Determine mixing complexity
        mixing_complexity = self._assess_mixing_complexity(type_distribution)
        
        # Recommend handling strategy
        recommended_strategy = self._recommend_handling_strategy(type_distribution, mixing_complexity)
        
        return {
            "total_objects": total_objects,
            "unique_types": len(type_counts),
            "type_distribution": type_distribution,
            "mixing_complexity": mixing_complexity,
            "recommended_strategy": recommended_strategy,
            "is_mixed": len(type_counts) > 1,
            "dominant_type": max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
        }
    
    def create_workflow_adaptation(self, objects: List[CodexObject], 
                                 workflow_type: str,
                                 user_preferences: Dict[str, Any] = None) -> WorkflowAdaptation:
        """
        Create adaptation configuration for a workflow with mixed content types.
        
        Args:
            objects: List of CodexObjects to process
            workflow_type: Type of workflow (tournament, reader_panel, series_generation)
            user_preferences: User-specified preferences for adaptation
            
        Returns:
            WorkflowAdaptation configuration
        """
        analysis = self.analyze_content_mix(objects)
        
        if not analysis.get("is_mixed", False):
            # Single type - no adaptation needed
            dominant_type = analysis.get("dominant_type", "idea")
            return WorkflowAdaptation(
                handling_strategy=MixedTypeHandling.ADAPTIVE,
                type_weights={dominant_type: 1.0},
                evaluation_adjustments={dominant_type: {}},
                comparison_method="direct"
            )
        
        # Mixed types - create adaptation
        handling_strategy = user_preferences.get("handling_strategy") if user_preferences else None
        if not handling_strategy:
            handling_strategy = MixedTypeHandling(analysis["recommended_strategy"])
        else:
            handling_strategy = MixedTypeHandling(handling_strategy)
        
        # Calculate type weights based on distribution and workflow type
        type_weights = self._calculate_type_weights(analysis["type_distribution"], workflow_type)
        
        # Create evaluation adjustments
        evaluation_adjustments = self._create_evaluation_adjustments(
            analysis["type_distribution"], 
            workflow_type,
            handling_strategy
        )
        
        # Determine comparison method
        comparison_method = self._select_comparison_method(handling_strategy, workflow_type)
        
        return WorkflowAdaptation(
            handling_strategy=handling_strategy,
            type_weights=type_weights,
            evaluation_adjustments=evaluation_adjustments,
            comparison_method=comparison_method
        )
    
    def adapt_tournament_evaluation(self, obj1: CodexObject, obj2: CodexObject,
                                  base_criteria: Dict[str, float],
                                  adaptation: WorkflowAdaptation) -> Dict[str, Any]:
        """
        Adapt tournament evaluation criteria for mixed content types.
        
        Args:
            obj1: First object to compare
            obj2: Second object to compare
            base_criteria: Base evaluation criteria
            adaptation: Workflow adaptation configuration
            
        Returns:
            Adapted evaluation configuration
        """
        if adaptation.handling_strategy == MixedTypeHandling.ADAPTIVE:
            return self._adaptive_tournament_evaluation(obj1, obj2, base_criteria, adaptation)
        elif adaptation.handling_strategy == MixedTypeHandling.NORMALIZE:
            return self._normalized_tournament_evaluation(obj1, obj2, base_criteria, adaptation)
        elif adaptation.handling_strategy == MixedTypeHandling.TYPE_AWARE:
            return self._type_aware_tournament_evaluation(obj1, obj2, base_criteria, adaptation)
        else:
            return {"criteria": base_criteria, "method": "standard"}
    
    def adapt_reader_panel_evaluation(self, objects: List[CodexObject],
                                    panel_config: Dict[str, Any],
                                    adaptation: WorkflowAdaptation) -> Dict[str, Any]:
        """
        Adapt reader panel evaluation for mixed content types.
        
        Args:
            objects: Objects to evaluate
            panel_config: Base panel configuration
            adaptation: Workflow adaptation configuration
            
        Returns:
            Adapted panel configuration
        """
        adapted_config = panel_config.copy()
        
        # Adjust evaluation focus based on content types
        type_distribution = {}
        for obj in objects:
            obj_type = obj.object_type.value
            type_distribution[obj_type] = type_distribution.get(obj_type, 0) + 1
        
        # Create type-specific evaluation instructions
        evaluation_instructions = {}
        for obj_type in type_distribution:
            evaluation_instructions[obj_type] = self._get_type_specific_evaluation_instructions(obj_type)
        
        adapted_config["evaluation_instructions"] = evaluation_instructions
        adapted_config["mixed_type_handling"] = adaptation.handling_strategy.value
        adapted_config["type_weights"] = adaptation.type_weights
        
        return adapted_config
    
    def adapt_series_generation(self, base_object: CodexObject,
                              series_config: Dict[str, Any],
                              adaptation: WorkflowAdaptation) -> Dict[str, Any]:
        """
        Adapt series generation for different content types.
        
        Args:
            base_object: Base object for series generation
            series_config: Base series configuration
            adaptation: Workflow adaptation configuration
            
        Returns:
            Adapted series configuration
        """
        adapted_config = series_config.copy()
        
        # Adjust consistency requirements based on content type
        obj_type = base_object.object_type.value
        type_adjustments = adaptation.evaluation_adjustments.get(obj_type, {})
        
        # Modify consistency requirements
        if "consistency_requirements" in adapted_config:
            consistency = adapted_config["consistency_requirements"]
            
            # Apply type-specific adjustments
            for requirement, adjustment in type_adjustments.items():
                if requirement in consistency:
                    consistency[requirement] *= (1 + adjustment)
                    consistency[requirement] = max(0.0, min(1.0, consistency[requirement]))
        
        # Add type-specific generation instructions
        adapted_config["base_type"] = obj_type
        adapted_config["type_specific_instructions"] = self._get_series_generation_instructions(obj_type)
        
        return adapted_config
    
    def _initialize_type_characteristics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize characteristics for different content types."""
        return {
            "idea": {
                "typical_word_range": (10, 100),
                "complexity_factors": ["originality", "clarity"],
                "development_stage": 1,
                "evaluation_focus": ["concept_strength", "market_potential"]
            },
            "logline": {
                "typical_word_range": (15, 50),
                "complexity_factors": ["hook_strength", "clarity"],
                "development_stage": 2,
                "evaluation_focus": ["hook_effectiveness", "genre_fit"]
            },
            "synopsis": {
                "typical_word_range": (100, 1000),
                "complexity_factors": ["plot_structure", "character_development"],
                "development_stage": 4,
                "evaluation_focus": ["story_structure", "character_appeal", "pacing"]
            },
            "outline": {
                "typical_word_range": (500, 5000),
                "complexity_factors": ["structural_detail", "scene_planning"],
                "development_stage": 6,
                "evaluation_focus": ["structural_soundness", "scene_flow", "character_arcs"]
            },
            "draft": {
                "typical_word_range": (5000, 100000),
                "complexity_factors": ["prose_quality", "narrative_flow"],
                "development_stage": 8,
                "evaluation_focus": ["writing_quality", "narrative_engagement", "character_voice"]
            },
            "manuscript": {
                "typical_word_range": (50000, 200000),
                "complexity_factors": ["prose_mastery", "thematic_depth"],
                "development_stage": 10,
                "evaluation_focus": ["literary_merit", "commercial_appeal", "thematic_resonance"]
            }
        }
    
    def _initialize_evaluation_mappings(self) -> Dict[str, Dict[str, str]]:
        """Initialize mappings between evaluation criteria and content types."""
        return {
            "originality": {
                "idea": "concept_uniqueness",
                "synopsis": "plot_originality",
                "outline": "structural_innovation",
                "draft": "narrative_originality",
                "manuscript": "literary_innovation"
            },
            "marketability": {
                "idea": "commercial_potential",
                "synopsis": "genre_appeal",
                "outline": "market_structure",
                "draft": "commercial_readability",
                "manuscript": "market_positioning"
            },
            "execution_potential": {
                "idea": "development_potential",
                "synopsis": "story_viability",
                "outline": "execution_feasibility",
                "draft": "completion_quality",
                "manuscript": "publication_readiness"
            },
            "emotional_impact": {
                "idea": "emotional_hook",
                "synopsis": "emotional_journey",
                "outline": "emotional_structure",
                "draft": "emotional_engagement",
                "manuscript": "emotional_resonance"
            }
        }
    
    def _calculate_complexity_score(self, obj: CodexObject) -> float:
        """Calculate complexity score for a CodexObject."""
        # Simple complexity calculation based on word count and type
        word_count = obj.word_count
        obj_type = obj.object_type.value
        
        type_characteristics = self.type_characteristics.get(obj_type, {})
        typical_range = type_characteristics.get("typical_word_range", (10, 100))
        
        # Normalize word count to typical range
        min_words, max_words = typical_range
        normalized_length = (word_count - min_words) / (max_words - min_words)
        normalized_length = max(0.0, min(1.0, normalized_length))
        
        # Base complexity on development stage and length
        development_stage = type_characteristics.get("development_stage", 1)
        complexity = (development_stage / 10) * 0.7 + normalized_length * 0.3
        
        return complexity
    
    def _assess_development_stage(self, obj: CodexObject) -> float:
        """Assess development stage of a CodexObject."""
        obj_type = obj.object_type.value
        return self.type_characteristics.get(obj_type, {}).get("development_stage", 1)
    
    def _assess_mixing_complexity(self, type_distribution: Dict[str, Dict[str, Any]]) -> str:
        """Assess complexity of mixing different content types."""
        if len(type_distribution) == 1:
            return "none"
        
        # Calculate development stage spread
        stages = [info["development_range"]["avg"] for info in type_distribution.values()]
        stage_spread = max(stages) - min(stages)
        
        # Calculate word count variation
        word_counts = [info["avg_word_count"] for info in type_distribution.values()]
        word_variation = max(word_counts) / min(word_counts) if min(word_counts) > 0 else 1
        
        if stage_spread <= 2 and word_variation <= 5:
            return "low"
        elif stage_spread <= 4 and word_variation <= 20:
            return "medium"
        else:
            return "high"
    
    def _recommend_handling_strategy(self, type_distribution: Dict[str, Dict[str, Any]], 
                                   complexity: str) -> str:
        """Recommend handling strategy based on type distribution and complexity."""
        if complexity == "none":
            return MixedTypeHandling.ADAPTIVE.value
        elif complexity == "low":
            return MixedTypeHandling.ADAPTIVE.value
        elif complexity == "medium":
            return MixedTypeHandling.TYPE_AWARE.value
        else:
            return MixedTypeHandling.NORMALIZE.value
    
    def _calculate_type_weights(self, type_distribution: Dict[str, Dict[str, Any]], 
                              workflow_type: str) -> Dict[str, float]:
        """Calculate weights for different content types."""
        weights = {}
        total_objects = sum(info["count"] for info in type_distribution.values())
        
        for obj_type, info in type_distribution.items():
            # Base weight on frequency
            frequency_weight = info["count"] / total_objects
            
            # Adjust based on workflow type
            if workflow_type == "tournament":
                # In tournaments, give slight preference to more developed content
                development_bonus = info["development_range"]["avg"] / 10 * 0.1
                weights[obj_type] = frequency_weight + development_bonus
            elif workflow_type == "reader_panel":
                # In reader panels, weight equally
                weights[obj_type] = frequency_weight
            elif workflow_type == "series_generation":
                # For series, prefer the most developed base concept
                weights[obj_type] = frequency_weight
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def _create_evaluation_adjustments(self, type_distribution: Dict[str, Dict[str, Any]],
                                     workflow_type: str,
                                     handling_strategy: MixedTypeHandling) -> Dict[str, Dict[str, float]]:
        """Create evaluation adjustments for different content types."""
        adjustments = {}
        
        for obj_type in type_distribution:
            type_adjustments = {}
            
            if handling_strategy == MixedTypeHandling.ADAPTIVE:
                # Adjust criteria based on type characteristics
                type_characteristics = self.type_characteristics.get(obj_type, {})
                evaluation_focus = type_characteristics.get("evaluation_focus", [])
                
                # Boost relevant criteria for this type
                for focus_area in evaluation_focus:
                    if "concept" in focus_area or "originality" in focus_area:
                        type_adjustments["originality"] = 0.1
                    elif "market" in focus_area or "commercial" in focus_area:
                        type_adjustments["marketability"] = 0.1
                    elif "structure" in focus_area or "execution" in focus_area:
                        type_adjustments["execution_potential"] = 0.1
                    elif "emotional" in focus_area or "engagement" in focus_area:
                        type_adjustments["emotional_impact"] = 0.1
            
            elif handling_strategy == MixedTypeHandling.NORMALIZE:
                # Normalize all types to similar evaluation standards
                development_stage = self.type_characteristics.get(obj_type, {}).get("development_stage", 1)
                normalization_factor = (5 - development_stage) / 10  # Boost less developed content
                
                type_adjustments = {
                    "originality": normalization_factor,
                    "marketability": normalization_factor * 0.5,
                    "execution_potential": -normalization_factor,  # Reduce execution expectations for early stage
                    "emotional_impact": normalization_factor * 0.3
                }
            
            adjustments[obj_type] = type_adjustments
        
        return adjustments
    
    def _select_comparison_method(self, handling_strategy: MixedTypeHandling, 
                                workflow_type: str) -> str:
        """Select appropriate comparison method for mixed types."""
        if handling_strategy == MixedTypeHandling.ADAPTIVE:
            return "adaptive_scoring"
        elif handling_strategy == MixedTypeHandling.NORMALIZE:
            return "normalized_scoring"
        elif handling_strategy == MixedTypeHandling.TYPE_AWARE:
            return "type_weighted_scoring"
        else:
            return "standard_scoring"
    
    def _adaptive_tournament_evaluation(self, obj1: CodexObject, obj2: CodexObject,
                                      base_criteria: Dict[str, float],
                                      adaptation: WorkflowAdaptation) -> Dict[str, Any]:
        """Create adaptive tournament evaluation for mixed types."""
        obj1_type = obj1.object_type.value
        obj2_type = obj2.object_type.value
        
        # Get type-specific adjustments
        obj1_adjustments = adaptation.evaluation_adjustments.get(obj1_type, {})
        obj2_adjustments = adaptation.evaluation_adjustments.get(obj2_type, {})
        
        # Create adapted criteria for each object
        obj1_criteria = base_criteria.copy()
        obj2_criteria = base_criteria.copy()
        
        for criterion, weight in base_criteria.items():
            obj1_adjustment = obj1_adjustments.get(criterion, 0)
            obj2_adjustment = obj2_adjustments.get(criterion, 0)
            
            obj1_criteria[criterion] = max(0.0, min(1.0, weight + obj1_adjustment))
            obj2_criteria[criterion] = max(0.0, min(1.0, weight + obj2_adjustment))
        
        return {
            "criteria": base_criteria,
            "obj1_criteria": obj1_criteria,
            "obj2_criteria": obj2_criteria,
            "method": "adaptive",
            "comparison_instructions": f"Compare {obj1_type} vs {obj2_type} using type-adapted criteria"
        }
    
    def _normalized_tournament_evaluation(self, obj1: CodexObject, obj2: CodexObject,
                                        base_criteria: Dict[str, float],
                                        adaptation: WorkflowAdaptation) -> Dict[str, Any]:
        """Create normalized tournament evaluation for mixed types."""
        # Use standard criteria but add normalization instructions
        return {
            "criteria": base_criteria,
            "method": "normalized",
            "normalization_instructions": "Evaluate both objects as if they were at the same development stage"
        }
    
    def _type_aware_tournament_evaluation(self, obj1: CodexObject, obj2: CodexObject,
                                        base_criteria: Dict[str, float],
                                        adaptation: WorkflowAdaptation) -> Dict[str, Any]:
        """Create type-aware tournament evaluation for mixed types."""
        obj1_type = obj1.object_type.value
        obj2_type = obj2.object_type.value
        
        # Get type weights
        obj1_weight = adaptation.type_weights.get(obj1_type, 1.0)
        obj2_weight = adaptation.type_weights.get(obj2_type, 1.0)
        
        return {
            "criteria": base_criteria,
            "obj1_weight": obj1_weight,
            "obj2_weight": obj2_weight,
            "method": "type_aware",
            "weighting_instructions": f"Apply type weights: {obj1_type}={obj1_weight:.2f}, {obj2_type}={obj2_weight:.2f}"
        }
    
    def _get_type_specific_evaluation_instructions(self, obj_type: str) -> Dict[str, str]:
        """Get evaluation instructions specific to a content type."""
        instructions = {
            "idea": {
                "focus": "Evaluate the core concept strength, originality, and market potential",
                "criteria": "Focus on the uniqueness of the idea and its commercial viability",
                "considerations": "Consider how well the idea could be developed into a full story"
            },
            "synopsis": {
                "focus": "Evaluate plot structure, character development, and story appeal",
                "criteria": "Focus on narrative coherence, character arcs, and genre fit",
                "considerations": "Consider pacing, conflict resolution, and reader engagement"
            },
            "outline": {
                "focus": "Evaluate structural soundness, scene flow, and development potential",
                "criteria": "Focus on story architecture, scene progression, and character development",
                "considerations": "Consider how well the structure supports the narrative goals"
            },
            "draft": {
                "focus": "Evaluate prose quality, narrative flow, and character voice",
                "criteria": "Focus on writing craft, story execution, and reader engagement",
                "considerations": "Consider both technical skill and storytelling effectiveness"
            },
            "manuscript": {
                "focus": "Evaluate literary merit, commercial appeal, and thematic depth",
                "criteria": "Focus on overall quality, market positioning, and artistic achievement",
                "considerations": "Consider publication readiness and long-term appeal"
            }
        }
        
        return instructions.get(obj_type, instructions["idea"])
    
    def _get_series_generation_instructions(self, obj_type: str) -> Dict[str, str]:
        """Get series generation instructions specific to a content type."""
        instructions = {
            "idea": {
                "expansion_focus": "Develop the core concept into multiple related scenarios",
                "consistency_elements": "Maintain thematic consistency and world-building elements",
                "variation_approach": "Create variations on the central premise"
            },
            "synopsis": {
                "expansion_focus": "Create related stories with similar structure and themes",
                "consistency_elements": "Maintain character types, setting, and narrative style",
                "variation_approach": "Vary specific conflicts while maintaining story formula"
            },
            "outline": {
                "expansion_focus": "Generate series with consistent structural patterns",
                "consistency_elements": "Maintain story architecture and pacing patterns",
                "variation_approach": "Vary plot details while keeping structural consistency"
            }
        }
        
        return instructions.get(obj_type, instructions["idea"])