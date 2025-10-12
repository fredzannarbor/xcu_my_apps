"""
Mixed-Type Evaluation Component

Implements sophisticated algorithms for fair comparison and evaluation
of different content types within the same workflow.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType

logger = logging.getLogger(__name__)


class ComparisonMethod(Enum):
    """Methods for comparing mixed content types."""
    NORMALIZED_SCORING = "normalized_scoring"
    WEIGHTED_COMPARISON = "weighted_comparison"
    TYPE_AWARE_RANKING = "type_aware_ranking"
    DEVELOPMENTAL_SCALING = "developmental_scaling"


@dataclass
class TypeCharacteristics:
    """Characteristics of a content type for evaluation."""
    development_stage: float  # 0-10 scale
    typical_word_range: Tuple[int, int]
    evaluation_focus: List[str]
    complexity_factors: List[str]
    comparison_weight: float = 1.0


class MixedTypeEvaluator:
    """
    Advanced mixed-type evaluation system for fair comparison across content types.
    Implements sophisticated algorithms for handling different content types in workflows.
    """
    
    def __init__(self):
        """Initialize the mixed-type evaluator."""
        self.type_characteristics = self._initialize_type_characteristics()
        self.comparison_algorithms = self._initialize_comparison_algorithms()
        logger.info("MixedTypeEvaluator initialized")
    
    def analyze_content_mix(self, objects: List[CodexObject]) -> Dict[str, Any]:
        """
        Analyze the mix of content types and recommend evaluation strategies.
        
        Args:
            objects: List of CodexObjects to analyze
            
        Returns:
            Analysis results with recommendations
        """
        if not objects:
            return {"error": "No objects provided"}
        
        # Analyze type distribution
        type_counts = {}
        type_metrics = {}
        
        for obj in objects:
            obj_type = obj.object_type.value
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
            
            if obj_type not in type_metrics:
                type_metrics[obj_type] = {
                    "word_counts": [],
                    "development_scores": [],
                    "complexity_scores": []
                }
            
            type_metrics[obj_type]["word_counts"].append(obj.word_count)
            type_metrics[obj_type]["development_scores"].append(
                self.type_characteristics[obj_type].development_stage
            )
            type_metrics[obj_type]["complexity_scores"].append(
                self._calculate_complexity_score(obj)
            )
        
        # Calculate mixing complexity
        mixing_analysis = self._analyze_mixing_complexity(type_counts, type_metrics)
        
        # Recommend evaluation strategy
        recommended_strategy = self._recommend_evaluation_strategy(mixing_analysis)
        
        return {
            "type_distribution": type_counts,
            "type_metrics": type_metrics,
            "mixing_complexity": mixing_analysis,
            "recommended_strategy": recommended_strategy,
            "fairness_adjustments": self._calculate_fairness_adjustments(type_counts, type_metrics)
        }
    
    def create_fair_comparison_matrix(self, objects: List[CodexObject], 
                                    comparison_method: ComparisonMethod) -> Dict[str, Any]:
        """
        Create a fair comparison matrix for mixed content types.
        
        Args:
            objects: Objects to create comparison matrix for
            comparison_method: Method to use for comparison
            
        Returns:
            Comparison matrix and adjustment factors
        """
        if comparison_method == ComparisonMethod.NORMALIZED_SCORING:
            return self._create_normalized_scoring_matrix(objects)
        elif comparison_method == ComparisonMethod.WEIGHTED_COMPARISON:
            return self._create_weighted_comparison_matrix(objects)
        elif comparison_method == ComparisonMethod.TYPE_AWARE_RANKING:
            return self._create_type_aware_ranking_matrix(objects)
        elif comparison_method == ComparisonMethod.DEVELOPMENTAL_SCALING:
            return self._create_developmental_scaling_matrix(objects)
        else:
            return self._create_normalized_scoring_matrix(objects)
    
    def apply_fairness_adjustments(self, raw_scores: Dict[str, float], 
                                 objects: List[CodexObject],
                                 adjustment_method: str = "developmental") -> Dict[str, float]:
        """
        Apply fairness adjustments to raw evaluation scores.
        
        Args:
            raw_scores: Raw scores for each object
            objects: List of objects being evaluated
            adjustment_method: Method for applying adjustments
            
        Returns:
            Adjusted scores
        """
        if adjustment_method == "developmental":
            return self._apply_developmental_adjustments(raw_scores, objects)
        elif adjustment_method == "complexity":
            return self._apply_complexity_adjustments(raw_scores, objects)
        elif adjustment_method == "length_normalized":
            return self._apply_length_normalization(raw_scores, objects)
        else:
            return raw_scores
    
    def generate_mixed_type_insights(self, evaluation_results: Dict[str, Any], 
                                   objects: List[CodexObject]) -> List[str]:
        """
        Generate insights about mixed-type evaluation results.
        
        Args:
            evaluation_results: Results from mixed-type evaluation
            objects: Objects that were evaluated
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Analyze type performance
        type_performance = self._analyze_type_performance(evaluation_results, objects)
        
        # Generate performance insights
        if type_performance:
            best_type = max(type_performance.items(), key=lambda x: x[1]["avg_score"])
            worst_type = min(type_performance.items(), key=lambda x: x[1]["avg_score"])
            
            insights.append(f"Best performing content type: {best_type[0]} (avg: {best_type[1]['avg_score']:.3f})")
            insights.append(f"Lowest performing content type: {worst_type[0]} (avg: {worst_type[1]['avg_score']:.3f})")
            
            # Analyze fairness
            score_range = best_type[1]["avg_score"] - worst_type[1]["avg_score"]
            if score_range > 0.3:
                insights.append("Large performance gap detected - consider reviewing evaluation criteria")
            elif score_range < 0.1:
                insights.append("Very close performance across content types - evaluation appears well-balanced")
        
        # Analyze developmental stage impact
        dev_impact = self._analyze_developmental_impact(evaluation_results, objects)
        if dev_impact:
            insights.extend(dev_impact)
        
        # Analyze length bias
        length_bias = self._analyze_length_bias(evaluation_results, objects)
        if length_bias:
            insights.extend(length_bias)
        
        return insights
    
    def _initialize_type_characteristics(self) -> Dict[str, TypeCharacteristics]:
        """Initialize characteristics for different content types."""
        return {
            "idea": TypeCharacteristics(
                development_stage=1.0,
                typical_word_range=(10, 100),
                evaluation_focus=["originality", "potential", "clarity"],
                complexity_factors=["concept_strength", "market_viability"],
                comparison_weight=1.0
            ),
            "logline": TypeCharacteristics(
                development_stage=2.0,
                typical_word_range=(15, 50),
                evaluation_focus=["hook_strength", "genre_fit", "marketability"],
                complexity_factors=["brevity", "impact"],
                comparison_weight=1.1
            ),
            "synopsis": TypeCharacteristics(
                development_stage=4.0,
                typical_word_range=(100, 1000),
                evaluation_focus=["plot_structure", "character_development", "pacing"],
                complexity_factors=["narrative_coherence", "story_arc"],
                comparison_weight=1.2
            ),
            "outline": TypeCharacteristics(
                development_stage=6.0,
                typical_word_range=(500, 5000),
                evaluation_focus=["structural_soundness", "scene_flow", "development_potential"],
                complexity_factors=["organizational_clarity", "detail_level"],
                comparison_weight=1.3
            ),
            "draft": TypeCharacteristics(
                development_stage=8.0,
                typical_word_range=(5000, 100000),
                evaluation_focus=["prose_quality", "narrative_flow", "character_voice"],
                complexity_factors=["writing_craft", "story_execution"],
                comparison_weight=1.4
            ),
            "manuscript": TypeCharacteristics(
                development_stage=10.0,
                typical_word_range=(50000, 200000),
                evaluation_focus=["literary_merit", "commercial_appeal", "thematic_depth"],
                complexity_factors=["artistic_achievement", "market_readiness"],
                comparison_weight=1.5
            )
        }
    
    def _initialize_comparison_algorithms(self) -> Dict[str, callable]:
        """Initialize comparison algorithms."""
        return {
            "normalized_scoring": self._normalized_scoring_algorithm,
            "weighted_comparison": self._weighted_comparison_algorithm,
            "type_aware_ranking": self._type_aware_ranking_algorithm,
            "developmental_scaling": self._developmental_scaling_algorithm
        }
    
    def _calculate_complexity_score(self, obj: CodexObject) -> float:
        """Calculate complexity score for an object."""
        obj_type = obj.object_type.value
        characteristics = self.type_characteristics.get(obj_type, self.type_characteristics["idea"])
        
        # Base complexity on development stage and word count
        word_count = obj.word_count
        typical_min, typical_max = characteristics.typical_word_range
        
        # Normalize word count to typical range
        if typical_max > typical_min:
            word_complexity = (word_count - typical_min) / (typical_max - typical_min)
            word_complexity = max(0.0, min(1.0, word_complexity))
        else:
            word_complexity = 0.5
        
        # Combine with development stage
        stage_complexity = characteristics.development_stage / 10.0
        
        return (stage_complexity * 0.7) + (word_complexity * 0.3)
    
    def _analyze_mixing_complexity(self, type_counts: Dict[str, int], 
                                 type_metrics: Dict[str, Dict[str, List]]) -> Dict[str, Any]:
        """Analyze the complexity of mixing different content types."""
        if len(type_counts) == 1:
            return {"level": "none", "description": "Single content type"}
        
        # Calculate development stage spread
        all_stages = []
        for obj_type, metrics in type_metrics.items():
            all_stages.extend(metrics["development_scores"])
        
        stage_spread = max(all_stages) - min(all_stages) if all_stages else 0
        
        # Calculate word count variation
        all_word_counts = []
        for obj_type, metrics in type_metrics.items():
            all_word_counts.extend(metrics["word_counts"])
        
        if all_word_counts:
            word_variation = max(all_word_counts) / min(all_word_counts) if min(all_word_counts) > 0 else 1
        else:
            word_variation = 1
        
        # Determine complexity level
        if stage_spread <= 2 and word_variation <= 5:
            complexity_level = "low"
            description = "Similar content types with minimal variation"
        elif stage_spread <= 4 and word_variation <= 20:
            complexity_level = "medium"
            description = "Moderate variation in content development and length"
        else:
            complexity_level = "high"
            description = "Significant variation in content types and characteristics"
        
        return {
            "level": complexity_level,
            "description": description,
            "stage_spread": stage_spread,
            "word_variation": word_variation,
            "type_count": len(type_counts)
        }
    
    def _recommend_evaluation_strategy(self, mixing_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend evaluation strategy based on mixing analysis."""
        complexity_level = mixing_analysis["level"]
        
        if complexity_level == "none":
            return {
                "method": ComparisonMethod.NORMALIZED_SCORING,
                "adjustments": [],
                "reasoning": "Single content type requires no special handling"
            }
        elif complexity_level == "low":
            return {
                "method": ComparisonMethod.NORMALIZED_SCORING,
                "adjustments": ["length_normalization"],
                "reasoning": "Similar content types can use standard comparison with minor adjustments"
            }
        elif complexity_level == "medium":
            return {
                "method": ComparisonMethod.WEIGHTED_COMPARISON,
                "adjustments": ["developmental_scaling", "complexity_adjustment"],
                "reasoning": "Moderate variation requires weighted comparison with developmental scaling"
            }
        else:
            return {
                "method": ComparisonMethod.DEVELOPMENTAL_SCALING,
                "adjustments": ["full_normalization", "type_aware_weighting"],
                "reasoning": "High variation requires comprehensive normalization and type-aware evaluation"
            }
    
    def _calculate_fairness_adjustments(self, type_counts: Dict[str, int], 
                                      type_metrics: Dict[str, Dict[str, List]]) -> Dict[str, float]:
        """Calculate fairness adjustments for each content type."""
        adjustments = {}
        
        # Calculate baseline from most common type
        most_common_type = max(type_counts.items(), key=lambda x: x[1])[0]
        baseline_stage = self.type_characteristics[most_common_type].development_stage
        
        for obj_type in type_counts:
            characteristics = self.type_characteristics[obj_type]
            
            # Adjustment based on development stage difference
            stage_diff = characteristics.development_stage - baseline_stage
            stage_adjustment = stage_diff / 10.0  # Normalize to 0-1 range
            
            # Adjustment based on typical complexity
            complexity_adjustment = (characteristics.development_stage - 5.0) / 10.0
            
            # Combine adjustments
            total_adjustment = (stage_adjustment * 0.6) + (complexity_adjustment * 0.4)
            adjustments[obj_type] = total_adjustment
        
        return adjustments
    
    def _create_normalized_scoring_matrix(self, objects: List[CodexObject]) -> Dict[str, Any]:
        """Create normalized scoring matrix."""
        matrix = {}
        
        # Group objects by type
        type_groups = {}
        for obj in objects:
            obj_type = obj.object_type.value
            if obj_type not in type_groups:
                type_groups[obj_type] = []
            type_groups[obj_type].append(obj)
        
        # Calculate normalization factors
        normalization_factors = {}
        for obj_type, group in type_groups.items():
            characteristics = self.type_characteristics[obj_type]
            
            # Base normalization on development stage
            base_factor = 5.0 / characteristics.development_stage  # Normalize to middle stage
            normalization_factors[obj_type] = base_factor
        
        matrix["normalization_factors"] = normalization_factors
        matrix["method"] = "normalized_scoring"
        matrix["description"] = "Scores normalized based on content type development stage"
        
        return matrix
    
    def _create_weighted_comparison_matrix(self, objects: List[CodexObject]) -> Dict[str, Any]:
        """Create weighted comparison matrix."""
        matrix = {}
        
        # Calculate weights based on type characteristics
        type_weights = {}
        for obj in objects:
            obj_type = obj.object_type.value
            if obj_type not in type_weights:
                characteristics = self.type_characteristics[obj_type]
                type_weights[obj_type] = characteristics.comparison_weight
        
        matrix["type_weights"] = type_weights
        matrix["method"] = "weighted_comparison"
        matrix["description"] = "Comparison weighted by content type characteristics"
        
        return matrix
    
    def _create_type_aware_ranking_matrix(self, objects: List[CodexObject]) -> Dict[str, Any]:
        """Create type-aware ranking matrix."""
        matrix = {}
        
        # Create ranking adjustments for each type
        ranking_adjustments = {}
        for obj in objects:
            obj_type = obj.object_type.value
            if obj_type not in ranking_adjustments:
                characteristics = self.type_characteristics[obj_type]
                
                # Adjustment based on evaluation focus
                focus_bonus = len(characteristics.evaluation_focus) * 0.1
                complexity_bonus = len(characteristics.complexity_factors) * 0.05
                
                ranking_adjustments[obj_type] = focus_bonus + complexity_bonus
        
        matrix["ranking_adjustments"] = ranking_adjustments
        matrix["method"] = "type_aware_ranking"
        matrix["description"] = "Rankings adjusted for type-specific evaluation criteria"
        
        return matrix
    
    def _create_developmental_scaling_matrix(self, objects: List[CodexObject]) -> Dict[str, Any]:
        """Create developmental scaling matrix."""
        matrix = {}
        
        # Calculate scaling factors based on development stages
        scaling_factors = {}
        max_stage = max(self.type_characteristics[obj.object_type.value].development_stage for obj in objects)
        
        for obj in objects:
            obj_type = obj.object_type.value
            if obj_type not in scaling_factors:
                characteristics = self.type_characteristics[obj_type]
                
                # Scale based on maximum development stage
                scale_factor = max_stage / characteristics.development_stage
                scaling_factors[obj_type] = scale_factor
        
        matrix["scaling_factors"] = scaling_factors
        matrix["method"] = "developmental_scaling"
        matrix["description"] = "Scores scaled based on content development stage"
        
        return matrix
    
    def _apply_developmental_adjustments(self, raw_scores: Dict[str, float], 
                                       objects: List[CodexObject]) -> Dict[str, float]:
        """Apply developmental stage adjustments to scores."""
        adjusted_scores = {}
        
        # Find the median development stage
        stages = [self.type_characteristics[obj.object_type.value].development_stage for obj in objects]
        median_stage = np.median(stages)
        
        for obj in objects:
            obj_id = str(obj.uuid)
            if obj_id in raw_scores:
                obj_type = obj.object_type.value
                characteristics = self.type_characteristics[obj_type]
                
                # Adjustment factor based on difference from median
                stage_diff = characteristics.development_stage - median_stage
                adjustment_factor = 1.0 + (stage_diff / 20.0)  # Small adjustment
                
                adjusted_scores[obj_id] = raw_scores[obj_id] * adjustment_factor
            else:
                adjusted_scores[obj_id] = raw_scores.get(obj_id, 0.0)
        
        return adjusted_scores
    
    def _apply_complexity_adjustments(self, raw_scores: Dict[str, float], 
                                    objects: List[CodexObject]) -> Dict[str, float]:
        """Apply complexity-based adjustments to scores."""
        adjusted_scores = {}
        
        # Calculate complexity scores for all objects
        complexity_scores = [self._calculate_complexity_score(obj) for obj in objects]
        avg_complexity = np.mean(complexity_scores)
        
        for obj in objects:
            obj_id = str(obj.uuid)
            if obj_id in raw_scores:
                obj_complexity = self._calculate_complexity_score(obj)
                
                # Adjustment based on complexity difference
                complexity_diff = obj_complexity - avg_complexity
                adjustment_factor = 1.0 + (complexity_diff * 0.1)  # Small adjustment
                
                adjusted_scores[obj_id] = raw_scores[obj_id] * adjustment_factor
            else:
                adjusted_scores[obj_id] = raw_scores.get(obj_id, 0.0)
        
        return adjusted_scores
    
    def _apply_length_normalization(self, raw_scores: Dict[str, float], 
                                  objects: List[CodexObject]) -> Dict[str, float]:
        """Apply length-based normalization to scores."""
        adjusted_scores = {}
        
        # Calculate length normalization factors
        word_counts = [obj.word_count for obj in objects]
        median_length = np.median(word_counts)
        
        for obj in objects:
            obj_id = str(obj.uuid)
            if obj_id in raw_scores:
                # Normalize based on length relative to median
                if median_length > 0:
                    length_factor = min(2.0, max(0.5, obj.word_count / median_length))
                    # Apply logarithmic scaling to reduce extreme adjustments
                    adjustment_factor = 1.0 + (np.log(length_factor) * 0.1)
                else:
                    adjustment_factor = 1.0
                
                adjusted_scores[obj_id] = raw_scores[obj_id] * adjustment_factor
            else:
                adjusted_scores[obj_id] = raw_scores.get(obj_id, 0.0)
        
        return adjusted_scores
    
    def _analyze_type_performance(self, evaluation_results: Dict[str, Any], 
                                objects: List[CodexObject]) -> Dict[str, Dict[str, float]]:
        """Analyze performance by content type."""
        type_performance = {}
        
        # Group results by type
        for obj in objects:
            obj_type = obj.object_type.value
            obj_id = str(obj.uuid)
            
            if obj_type not in type_performance:
                type_performance[obj_type] = {"scores": [], "count": 0}
            
            # Extract score from results (this would depend on result structure)
            score = evaluation_results.get(obj_id, 0.0)
            if isinstance(score, dict):
                score = score.get("final_score", 0.0)
            
            type_performance[obj_type]["scores"].append(score)
            type_performance[obj_type]["count"] += 1
        
        # Calculate statistics
        for obj_type, data in type_performance.items():
            scores = data["scores"]
            if scores:
                type_performance[obj_type]["avg_score"] = np.mean(scores)
                type_performance[obj_type]["std_score"] = np.std(scores)
                type_performance[obj_type]["min_score"] = min(scores)
                type_performance[obj_type]["max_score"] = max(scores)
            else:
                type_performance[obj_type]["avg_score"] = 0.0
                type_performance[obj_type]["std_score"] = 0.0
                type_performance[obj_type]["min_score"] = 0.0
                type_performance[obj_type]["max_score"] = 0.0
        
        return type_performance
    
    def _analyze_developmental_impact(self, evaluation_results: Dict[str, Any], 
                                    objects: List[CodexObject]) -> List[str]:
        """Analyze impact of developmental stage on results."""
        insights = []
        
        # Group by development stage
        stage_groups = {}
        for obj in objects:
            obj_type = obj.object_type.value
            stage = self.type_characteristics[obj_type].development_stage
            stage_group = f"Stage {int(stage//2)*2}-{int(stage//2)*2+2}"  # Group into ranges
            
            if stage_group not in stage_groups:
                stage_groups[stage_group] = []
            
            obj_id = str(obj.uuid)
            score = evaluation_results.get(obj_id, 0.0)
            if isinstance(score, dict):
                score = score.get("final_score", 0.0)
            
            stage_groups[stage_group].append(score)
        
        # Analyze stage performance
        if len(stage_groups) > 1:
            stage_averages = {group: np.mean(scores) for group, scores in stage_groups.items()}
            best_stage = max(stage_averages.items(), key=lambda x: x[1])
            worst_stage = min(stage_averages.items(), key=lambda x: x[1])
            
            insights.append(f"Best performing development stage: {best_stage[0]} (avg: {best_stage[1]:.3f})")
            
            if best_stage[1] - worst_stage[1] > 0.2:
                insights.append("Significant developmental stage bias detected in evaluation")
        
        return insights
    
    def _analyze_length_bias(self, evaluation_results: Dict[str, Any], 
                           objects: List[CodexObject]) -> List[str]:
        """Analyze potential length bias in evaluation."""
        insights = []
        
        # Correlate word count with scores
        word_counts = []
        scores = []
        
        for obj in objects:
            obj_id = str(obj.uuid)
            score = evaluation_results.get(obj_id, 0.0)
            if isinstance(score, dict):
                score = score.get("final_score", 0.0)
            
            word_counts.append(obj.word_count)
            scores.append(score)
        
        if len(word_counts) > 2:
            # Calculate correlation
            correlation = np.corrcoef(word_counts, scores)[0, 1]
            
            if abs(correlation) > 0.5:
                if correlation > 0:
                    insights.append(f"Positive length bias detected (correlation: {correlation:.3f}) - longer content tends to score higher")
                else:
                    insights.append(f"Negative length bias detected (correlation: {correlation:.3f}) - shorter content tends to score higher")
            elif abs(correlation) < 0.2:
                insights.append("No significant length bias detected - evaluation appears length-neutral")
        
        return insights
    
    # Algorithm implementations
    def _normalized_scoring_algorithm(self, scores: Dict[str, float], objects: List[CodexObject]) -> Dict[str, float]:
        """Normalized scoring algorithm implementation."""
        return self._apply_developmental_adjustments(scores, objects)
    
    def _weighted_comparison_algorithm(self, scores: Dict[str, float], objects: List[CodexObject]) -> Dict[str, float]:
        """Weighted comparison algorithm implementation."""
        weighted_scores = {}
        
        for obj in objects:
            obj_id = str(obj.uuid)
            if obj_id in scores:
                obj_type = obj.object_type.value
                weight = self.type_characteristics[obj_type].comparison_weight
                weighted_scores[obj_id] = scores[obj_id] * weight
            else:
                weighted_scores[obj_id] = scores.get(obj_id, 0.0)
        
        return weighted_scores
    
    def _type_aware_ranking_algorithm(self, scores: Dict[str, float], objects: List[CodexObject]) -> Dict[str, float]:
        """Type-aware ranking algorithm implementation."""
        # This would implement sophisticated type-aware ranking
        return self._apply_complexity_adjustments(scores, objects)
    
    def _developmental_scaling_algorithm(self, scores: Dict[str, float], objects: List[CodexObject]) -> Dict[str, float]:
        """Developmental scaling algorithm implementation."""
        return self._apply_developmental_adjustments(scores, objects)