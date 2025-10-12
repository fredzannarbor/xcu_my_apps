"""
Evaluation engine for tournament matches.
Handles LLM-powered evaluation of CodexObject competitions.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

from ..core.codex_object import CodexObject
from ..llm.ideation_llm_service import IdeationLLMService

logger = logging.getLogger(__name__)


@dataclass
class MatchEvaluation:
    """Represents the evaluation of a tournament match."""
    winner_uuid: str
    loser_uuid: str
    reasoning: str
    scores: Dict[str, Dict[str, float]] = field(default_factory=dict)
    strengths: Dict[str, list] = field(default_factory=dict)
    weaknesses: Dict[str, list] = field(default_factory=dict)
    evaluation_criteria: Dict[str, float] = field(default_factory=dict)
    confidence_score: float = 0.0
    evaluation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation to dictionary format."""
        return {
            "winner_uuid": self.winner_uuid,
            "loser_uuid": self.loser_uuid,
            "reasoning": self.reasoning,
            "scores": self.scores,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "evaluation_criteria": self.evaluation_criteria,
            "confidence_score": self.confidence_score,
            "evaluation_timestamp": self.evaluation_timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MatchEvaluation':
        """Create evaluation from dictionary format."""
        return cls(
            winner_uuid=data["winner_uuid"],
            loser_uuid=data["loser_uuid"],
            reasoning=data["reasoning"],
            scores=data.get("scores", {}),
            strengths=data.get("strengths", {}),
            weaknesses=data.get("weaknesses", {}),
            evaluation_criteria=data.get("evaluation_criteria", {}),
            confidence_score=data.get("confidence_score", 0.0),
            evaluation_timestamp=data.get("evaluation_timestamp", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )


class EvaluationEngine:
    """
    Handles LLM-powered evaluation of tournament matches.
    Implements Requirement 1.3 for LLM-powered evaluation.
    """
    
    def __init__(self):
        """Initialize evaluation engine."""
        self.llm_service = IdeationLLMService()
        logger.info("EvaluationEngine initialized")
    
    def evaluate_match(self, obj1: CodexObject, obj2: CodexObject,
                      evaluation_criteria: Dict[str, float] = None) -> Optional[MatchEvaluation]:
        """
        Evaluate a tournament match between two CodexObjects.
        
        Args:
            obj1: First CodexObject
            obj2: Second CodexObject
            evaluation_criteria: Criteria weights for evaluation
            
        Returns:
            Match evaluation result or None if evaluation failed
        """
        try:
            # Use default criteria if none provided
            if evaluation_criteria is None:
                evaluation_criteria = {
                    "originality": 0.3,
                    "marketability": 0.3,
                    "execution_potential": 0.2,
                    "emotional_impact": 0.2
                }
            
            # Validate criteria weights sum to 1.0
            total_weight = sum(evaluation_criteria.values())
            if abs(total_weight - 1.0) > 0.01:
                logger.warning(f"Evaluation criteria weights sum to {total_weight}, normalizing")
                evaluation_criteria = {k: v/total_weight for k, v in evaluation_criteria.items()}
            
            # Call LLM service for evaluation
            llm_response = self.llm_service.evaluate_tournament_match(obj1, obj2, evaluation_criteria)
            
            if not llm_response.success:
                logger.error(f"LLM evaluation failed: {llm_response.error_message}")
                return None
            
            # Parse LLM response into MatchEvaluation
            parsed_data = llm_response.parsed_data
            
            if not parsed_data or not parsed_data.get("winner_uuid"):
                logger.error("Invalid evaluation response from LLM")
                return None
            
            # Create match evaluation
            evaluation = MatchEvaluation(
                winner_uuid=parsed_data["winner_uuid"],
                loser_uuid=parsed_data["loser_uuid"],
                reasoning=parsed_data.get("reasoning", "No reasoning provided"),
                scores=parsed_data.get("scores", {}),
                strengths=parsed_data.get("strengths", {}),
                weaknesses=parsed_data.get("weaknesses", {}),
                evaluation_criteria=evaluation_criteria,
                confidence_score=self._calculate_confidence_score(parsed_data),
                metadata={
                    "llm_model": llm_response.model_used,
                    "evaluation_quality": parsed_data.get("evaluation_quality", "unknown"),
                    "participants": [obj1.uuid, obj2.uuid]
                }
            )
            
            # Update participant evaluation scores
            self._update_participant_scores(obj1, obj2, evaluation)
            
            logger.info(f"Match evaluation completed: {evaluation.winner_uuid} defeats {evaluation.loser_uuid}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating match: {e}")
            return None
    
    def batch_evaluate_matches(self, matches: list) -> list:
        """
        Evaluate multiple matches in batch.
        
        Args:
            matches: List of (obj1, obj2, criteria) tuples
            
        Returns:
            List of MatchEvaluation results
        """
        evaluations = []
        
        for i, (obj1, obj2, criteria) in enumerate(matches):
            try:
                logger.info(f"Evaluating batch match {i+1}/{len(matches)}")
                evaluation = self.evaluate_match(obj1, obj2, criteria)
                evaluations.append(evaluation)
                
            except Exception as e:
                logger.error(f"Error in batch evaluation {i+1}: {e}")
                evaluations.append(None)
        
        successful_evaluations = [e for e in evaluations if e is not None]
        logger.info(f"Batch evaluation completed: {len(successful_evaluations)}/{len(matches)} successful")
        
        return evaluations
    
    def evaluate_with_custom_criteria(self, obj1: CodexObject, obj2: CodexObject,
                                    custom_criteria: Dict[str, Any]) -> Optional[MatchEvaluation]:
        """
        Evaluate match with custom criteria configuration.
        
        Args:
            obj1: First CodexObject
            obj2: Second CodexObject
            custom_criteria: Custom evaluation configuration
            
        Returns:
            Match evaluation result
        """
        try:
            # Extract weights and any special instructions
            criteria_weights = custom_criteria.get("weights", {
                "originality": 0.25,
                "marketability": 0.25,
                "execution_potential": 0.25,
                "emotional_impact": 0.25
            })
            
            # Add any special evaluation instructions to metadata
            special_instructions = custom_criteria.get("instructions", "")
            focus_areas = custom_criteria.get("focus_areas", [])
            
            # Perform evaluation
            evaluation = self.evaluate_match(obj1, obj2, criteria_weights)
            
            if evaluation:
                # Add custom criteria metadata
                evaluation.metadata.update({
                    "custom_criteria": True,
                    "special_instructions": special_instructions,
                    "focus_areas": focus_areas,
                    "original_criteria": custom_criteria
                })
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in custom criteria evaluation: {e}")
            return None
    
    def re_evaluate_match(self, obj1: CodexObject, obj2: CodexObject,
                         previous_evaluation: MatchEvaluation,
                         reason: str = "re-evaluation requested") -> Optional[MatchEvaluation]:
        """
        Re-evaluate a match with the same criteria.
        
        Args:
            obj1: First CodexObject
            obj2: Second CodexObject
            previous_evaluation: Previous evaluation to compare against
            reason: Reason for re-evaluation
            
        Returns:
            New match evaluation result
        """
        try:
            logger.info(f"Re-evaluating match: {reason}")
            
            # Use same criteria as previous evaluation
            new_evaluation = self.evaluate_match(obj1, obj2, previous_evaluation.evaluation_criteria)
            
            if new_evaluation:
                # Add re-evaluation metadata
                new_evaluation.metadata.update({
                    "re_evaluation": True,
                    "re_evaluation_reason": reason,
                    "previous_winner": previous_evaluation.winner_uuid,
                    "previous_evaluation_timestamp": previous_evaluation.evaluation_timestamp,
                    "winner_changed": new_evaluation.winner_uuid != previous_evaluation.winner_uuid
                })
                
                # Log if winner changed
                if new_evaluation.winner_uuid != previous_evaluation.winner_uuid:
                    logger.warning(f"Re-evaluation changed winner: {previous_evaluation.winner_uuid} -> {new_evaluation.winner_uuid}")
            
            return new_evaluation
            
        except Exception as e:
            logger.error(f"Error in re-evaluation: {e}")
            return None
    
    def _calculate_confidence_score(self, parsed_data: Dict[str, Any]) -> float:
        """Calculate confidence score for evaluation."""
        try:
            # Base confidence from LLM response quality
            base_confidence = 0.5
            
            # Increase confidence based on available data
            if parsed_data.get("reasoning"):
                base_confidence += 0.2
            
            if parsed_data.get("scores"):
                base_confidence += 0.2
            
            if parsed_data.get("strengths") and parsed_data.get("weaknesses"):
                base_confidence += 0.1
            
            # Factor in evaluation quality if provided
            quality = parsed_data.get("evaluation_quality", "medium")
            if quality == "high":
                base_confidence += 0.1
            elif quality == "low":
                base_confidence -= 0.1
            
            # Ensure confidence is between 0 and 1
            return max(0.0, min(1.0, base_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5
    
    def _update_participant_scores(self, obj1: CodexObject, obj2: CodexObject, 
                                 evaluation: MatchEvaluation):
        """Update participant evaluation scores based on match result."""
        try:
            # Extract scores from evaluation
            obj1_scores = evaluation.scores.get(obj1.uuid, {})
            obj2_scores = evaluation.scores.get(obj2.uuid, {})
            
            # Update obj1 scores
            for criterion, score in obj1_scores.items():
                if criterion != "total":  # Skip total score
                    score_key = f"tournament_{criterion}"
                    obj1.add_evaluation_score(score_key, score, {
                        "match_uuid": f"{obj1.uuid}_vs_{obj2.uuid}",
                        "opponent": obj2.uuid,
                        "match_result": "win" if evaluation.winner_uuid == obj1.uuid else "loss"
                    })
            
            # Update obj2 scores
            for criterion, score in obj2_scores.items():
                if criterion != "total":  # Skip total score
                    score_key = f"tournament_{criterion}"
                    obj2.add_evaluation_score(score_key, score, {
                        "match_uuid": f"{obj1.uuid}_vs_{obj2.uuid}",
                        "opponent": obj1.uuid,
                        "match_result": "win" if evaluation.winner_uuid == obj2.uuid else "loss"
                    })
            
            # Update tournament performance tracking
            winner = obj1 if evaluation.winner_uuid == obj1.uuid else obj2
            loser = obj2 if evaluation.winner_uuid == obj1.uuid else obj1
            
            # Update winner's tournament performance
            if "tournament_wins" not in winner.tournament_performance:
                winner.tournament_performance["tournament_wins"] = 0
            winner.tournament_performance["tournament_wins"] += 1
            
            # Update loser's tournament performance
            if "tournament_losses" not in loser.tournament_performance:
                loser.tournament_performance["tournament_losses"] = 0
            loser.tournament_performance["tournament_losses"] += 1
            
            # Update both participants' match history
            match_record = {
                "opponent_uuid": obj2.uuid if winner == obj1 else obj1.uuid,
                "result": "win" if winner == obj1 else "loss",
                "evaluation_timestamp": evaluation.evaluation_timestamp,
                "scores": obj1_scores if winner == obj1 else obj2_scores
            }
            
            if "match_history" not in obj1.tournament_performance:
                obj1.tournament_performance["match_history"] = []
            obj1.tournament_performance["match_history"].append({
                **match_record,
                "result": "win" if evaluation.winner_uuid == obj1.uuid else "loss",
                "opponent_uuid": obj2.uuid
            })
            
            if "match_history" not in obj2.tournament_performance:
                obj2.tournament_performance["match_history"] = []
            obj2.tournament_performance["match_history"].append({
                **match_record,
                "result": "win" if evaluation.winner_uuid == obj2.uuid else "loss",
                "opponent_uuid": obj1.uuid
            })
            
        except Exception as e:
            logger.error(f"Error updating participant scores: {e}")
    
    def get_evaluation_statistics(self, evaluations: list) -> Dict[str, Any]:
        """
        Get statistics about a set of evaluations.
        
        Args:
            evaluations: List of MatchEvaluation objects
            
        Returns:
            Statistics dictionary
        """
        try:
            if not evaluations:
                return {"error": "No evaluations provided"}
            
            # Filter out None evaluations
            valid_evaluations = [e for e in evaluations if e is not None]
            
            if not valid_evaluations:
                return {"error": "No valid evaluations"}
            
            # Calculate statistics
            total_evaluations = len(valid_evaluations)
            avg_confidence = sum(e.confidence_score for e in valid_evaluations) / total_evaluations
            
            # Count evaluation qualities
            quality_counts = {}
            for evaluation in valid_evaluations:
                quality = evaluation.metadata.get("evaluation_quality", "unknown")
                quality_counts[quality] = quality_counts.get(quality, 0) + 1
            
            # Calculate average scores by criterion
            criterion_averages = {}
            criterion_counts = {}
            
            for evaluation in valid_evaluations:
                for participant_scores in evaluation.scores.values():
                    for criterion, score in participant_scores.items():
                        if criterion != "total":
                            if criterion not in criterion_averages:
                                criterion_averages[criterion] = 0
                                criterion_counts[criterion] = 0
                            criterion_averages[criterion] += score
                            criterion_counts[criterion] += 1
            
            # Calculate final averages
            for criterion in criterion_averages:
                criterion_averages[criterion] /= criterion_counts[criterion]
            
            return {
                "total_evaluations": total_evaluations,
                "average_confidence": avg_confidence,
                "quality_distribution": quality_counts,
                "criterion_averages": criterion_averages,
                "evaluation_success_rate": len(valid_evaluations) / len(evaluations) if evaluations else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating evaluation statistics: {e}")
            return {"error": str(e)}
    
    def validate_evaluation_criteria(self, criteria: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate evaluation criteria configuration.
        
        Args:
            criteria: Criteria weights to validate
            
        Returns:
            Validation results
        """
        try:
            validation = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "normalized_criteria": {}
            }
            
            # Check if criteria is empty
            if not criteria:
                validation["errors"].append("Criteria cannot be empty")
                validation["valid"] = False
                return validation
            
            # Check for negative weights
            for criterion, weight in criteria.items():
                if weight < 0:
                    validation["errors"].append(f"Negative weight for {criterion}: {weight}")
                    validation["valid"] = False
            
            # Check weight sum
            total_weight = sum(criteria.values())
            if total_weight == 0:
                validation["errors"].append("Total weight cannot be zero")
                validation["valid"] = False
                return validation
            
            # Normalize weights
            normalized = {k: v/total_weight for k, v in criteria.items()}
            validation["normalized_criteria"] = normalized
            
            # Warn if weights don't sum to 1
            if abs(total_weight - 1.0) > 0.01:
                validation["warnings"].append(f"Weights sum to {total_weight}, will be normalized")
            
            # Check for common criteria
            common_criteria = {"originality", "marketability", "execution_potential", "emotional_impact"}
            missing_common = common_criteria - set(criteria.keys())
            if missing_common:
                validation["warnings"].append(f"Missing common criteria: {missing_common}")
            
            return validation
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "normalized_criteria": {}
            }