"""
Synthetic reader panel system for evaluating CodexObjects.
Manages panels of synthetic readers and coordinates their evaluations.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ..core.codex_object import CodexObject
from ..llm.ideation_llm_service import IdeationLLMService
from .reader_persona import ReaderPersona, ReaderPersonaFactory

logger = logging.getLogger(__name__)


@dataclass
class ReaderEvaluation:
    """Individual reader evaluation of a CodexObject."""
    reader_uuid: str
    object_uuid: str
    rating: float
    appeal_score: float
    reasoning: str
    demographic_fit: float
    market_appeal: float
    concerns: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    evaluation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PanelResults:
    """Results from a synthetic reader panel evaluation."""
    panel_uuid: str
    object_uuid: str
    panel_size: int
    individual_evaluations: List[Dict[str, Any]] = field(default_factory=list)
    aggregated_results: Dict[str, Any] = field(default_factory=dict)
    consensus_patterns: Dict[str, Any] = field(default_factory=dict)
    demographic_breakdown: Dict[str, Any] = field(default_factory=dict)
    market_appeal_insights: Dict[str, Any] = field(default_factory=dict)
    evaluation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def average_rating(self) -> float:
        """Get average rating across all evaluations."""
        if not self.individual_evaluations:
            return 0.0
        
        ratings = [eval_data.get("rating", 0) for eval_data in self.individual_evaluations]
        return sum(ratings) / len(ratings) if ratings else 0.0
    
    @property
    def would_read_percentage(self) -> float:
        """Get percentage of readers who would read this content."""
        if not self.individual_evaluations:
            return 0.0
        
        would_read_count = sum(1 for eval_data in self.individual_evaluations 
                              if eval_data.get("would_read", False))
        return (would_read_count / len(self.individual_evaluations)) * 100
    
    @property
    def recommendation_score(self) -> float:
        """Get average recommendation likelihood."""
        if not self.individual_evaluations:
            return 0.0
        
        rec_scores = [eval_data.get("recommendation_likelihood", 0) 
                     for eval_data in self.individual_evaluations]
        return sum(rec_scores) / len(rec_scores) if rec_scores else 0.0


class SyntheticReaderPanel:
    """
    Manages synthetic reader panels and coordinates evaluations.
    Implements Requirements 5.3, 5.4, 5.5 for panel evaluation system.
    """
    
    def __init__(self, llm_service: Optional[IdeationLLMService] = None):
        """
        Initialize synthetic reader panel.
        
        Args:
            llm_service: LLM service for reader simulation
        """
        self.llm_service = llm_service or IdeationLLMService()
        self.persona_factory = ReaderPersonaFactory()
        self.active_panels = {}  # panel_uuid -> panel_data
        logger.info("SyntheticReaderPanel initialized")
    
    def create_panel(self, demographics: Dict[str, Any], 
                    panel_size: int) -> List[ReaderPersona]:
        """
        Create a diverse panel of synthetic readers.
        Implements Requirement 5.1.
        
        Args:
            demographics: Target demographics configuration
            panel_size: Number of readers in the panel
            
        Returns:
            List of reader personas
        """
        try:
            # Create diversity configuration from demographics
            diversity_config = self._parse_demographics_config(demographics)
            
            # Generate diverse panel
            panel = self.persona_factory.create_diverse_panel(panel_size, diversity_config)
            
            # Store panel for tracking
            panel_uuid = str(uuid.uuid4())
            self.active_panels[panel_uuid] = {
                "uuid": panel_uuid,
                "personas": panel,
                "demographics": demographics,
                "created_at": datetime.now().isoformat(),
                "evaluations_count": 0
            }
            
            logger.info(f"Created reader panel with {panel_size} personas: {panel_uuid}")
            return panel
            
        except Exception as e:
            logger.error(f"Error creating reader panel: {e}")
            raise
    
    def evaluate_content(self, codex_object: CodexObject, 
                        panel: List[ReaderPersona]) -> PanelResults:
        """
        Evaluate content with synthetic reader panel.
        Implements Requirements 5.3, 5.4, 5.5.
        
        Args:
            codex_object: Content to evaluate
            panel: List of reader personas
            
        Returns:
            Panel evaluation results
        """
        try:
            panel_uuid = str(uuid.uuid4())
            individual_evaluations = []
            
            logger.info(f"Starting panel evaluation with {len(panel)} readers for {codex_object.shortuuid}")
            
            # Evaluate with each reader
            for i, reader in enumerate(panel):
                try:
                    logger.debug(f"Evaluating with reader {i+1}/{len(panel)}: {reader.name}")
                    
                    # Get reader evaluation context
                    reader_context = reader.get_evaluation_context()
                    
                    # Call LLM service for evaluation
                    llm_response = self.llm_service.simulate_reader_evaluation(
                        codex_object, reader_context
                    )
                    
                    if llm_response.success and llm_response.parsed_data:
                        evaluation_data = llm_response.parsed_data.copy()
                        evaluation_data["reader_uuid"] = reader.uuid
                        evaluation_data["reader_name"] = reader.name
                        evaluation_data["reader_demographics"] = {
                            "age_group": reader.age_group.value,
                            "gender": reader.gender.value,
                            "reading_level": reader.reading_level.value,
                            "location": reader.location
                        }
                        individual_evaluations.append(evaluation_data)
                        
                        # Update reader usage
                        reader.update_usage()
                    else:
                        logger.warning(f"Failed to get evaluation from reader {reader.name}")
                        # Add placeholder evaluation
                        individual_evaluations.append({
                            "reader_uuid": reader.uuid,
                            "reader_name": reader.name,
                            "rating": 3,
                            "would_read": False,
                            "interest_level": "medium",
                            "feedback": "Evaluation failed",
                            "evaluation_failed": True
                        })
                
                except Exception as e:
                    logger.error(f"Error evaluating with reader {reader.name}: {e}")
                    # Add error placeholder
                    individual_evaluations.append({
                        "reader_uuid": reader.uuid,
                        "reader_name": reader.name,
                        "rating": 3,
                        "would_read": False,
                        "interest_level": "medium",
                        "feedback": f"Evaluation error: {str(e)}",
                        "evaluation_error": True
                    })
            
            # Create results object
            results = PanelResults(
                panel_uuid=panel_uuid,
                object_uuid=codex_object.uuid,
                panel_size=len(panel),
                individual_evaluations=individual_evaluations
            )
            
            # Aggregate results
            results.aggregated_results = self._aggregate_evaluations(individual_evaluations)
            results.consensus_patterns = self._identify_consensus_patterns(individual_evaluations)
            results.demographic_breakdown = self._analyze_demographic_breakdown(individual_evaluations)
            results.market_appeal_insights = self._generate_market_insights(individual_evaluations, codex_object)
            
            logger.info(f"Panel evaluation completed: avg rating {results.average_rating:.2f}, {results.would_read_percentage:.1f}% would read")
            return results
            
        except Exception as e:
            logger.error(f"Error in panel evaluation: {e}")
            raise
    
    def evaluate_with_targeted_demographics(self, codex_object: CodexObject,
                                          target_demographics: List[Dict[str, Any]],
                                          readers_per_demographic: int = 3) -> PanelResults:
        """
        Evaluate content with specific demographic targets.
        
        Args:
            codex_object: Content to evaluate
            target_demographics: List of demographic configurations
            readers_per_demographic: Number of readers per demographic
            
        Returns:
            Panel evaluation results
        """
        try:
            panel = []
            
            # Create readers for each demographic target
            for demo_config in target_demographics:
                for _ in range(readers_per_demographic):
                    reader = self.persona_factory.create_targeted_persona(demo_config)
                    panel.append(reader)
            
            # Evaluate with the targeted panel
            return self.evaluate_content(codex_object, panel)
            
        except Exception as e:
            logger.error(f"Error in targeted demographic evaluation: {e}")
            raise
    
    def batch_evaluate(self, codex_objects: List[CodexObject],
                      panel: List[ReaderPersona]) -> List[PanelResults]:
        """
        Evaluate multiple objects with the same panel.
        
        Args:
            codex_objects: List of content to evaluate
            panel: Reader panel to use for all evaluations
            
        Returns:
            List of panel results
        """
        results = []
        
        for i, obj in enumerate(codex_objects):
            try:
                logger.info(f"Batch evaluation {i+1}/{len(codex_objects)}: {obj.shortuuid}")
                result = self.evaluate_content(obj, panel)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch evaluation for {obj.shortuuid}: {e}")
                # Add error result
                error_result = PanelResults(
                    panel_uuid="error",
                    object_uuid=obj.uuid,
                    panel_size=len(panel),
                    individual_evaluations=[],
                    aggregated_results={"error": str(e)}
                )
                results.append(error_result)
        
        return results
    
    def _parse_demographics_config(self, demographics: Dict[str, Any]) -> Dict[str, Any]:
        """Parse demographics configuration into diversity config."""
        diversity_config = {
            "age_distribution": "balanced",
            "gender_distribution": "balanced",
            "reading_level_distribution": "balanced",
            "genre_diversity": "high"
        }
        
        # Override with specific requirements
        if "age_distribution" in demographics:
            diversity_config["age_distribution"] = demographics["age_distribution"]
        
        if "gender_distribution" in demographics:
            diversity_config["gender_distribution"] = demographics["gender_distribution"]
        
        if "reading_level_focus" in demographics:
            diversity_config["reading_level_distribution"] = demographics["reading_level_focus"]
        
        if "genre_diversity" in demographics:
            diversity_config["genre_diversity"] = demographics["genre_diversity"]
        
        return diversity_config
    
    def _aggregate_evaluations(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate individual evaluations into summary statistics."""
        if not evaluations:
            return {}
        
        # Filter out failed evaluations for aggregation
        valid_evaluations = [e for e in evaluations if not e.get("evaluation_failed", False)]
        
        if not valid_evaluations:
            return {"error": "No valid evaluations"}
        
        # Calculate aggregated metrics
        ratings = [e.get("rating", 0) for e in valid_evaluations]
        would_read_count = sum(1 for e in valid_evaluations if e.get("would_read", False))
        recommendation_scores = [e.get("recommendation_likelihood", 0) for e in valid_evaluations]
        
        # Interest level distribution
        interest_levels = [e.get("interest_level", "medium") for e in valid_evaluations]
        interest_distribution = {}
        for level in interest_levels:
            interest_distribution[level] = interest_distribution.get(level, 0) + 1
        
        return {
            "average_rating": sum(ratings) / len(ratings) if ratings else 0,
            "rating_distribution": self._calculate_distribution(ratings, [1, 2, 3, 4, 5]),
            "would_read_percentage": (would_read_count / len(valid_evaluations)) * 100,
            "average_recommendation_score": sum(recommendation_scores) / len(recommendation_scores) if recommendation_scores else 0,
            "interest_level_distribution": interest_distribution,
            "total_evaluations": len(evaluations),
            "valid_evaluations": len(valid_evaluations),
            "failed_evaluations": len(evaluations) - len(valid_evaluations)
        }
    
    def _identify_consensus_patterns(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify consensus patterns in evaluations."""
        if not evaluations:
            return {}
        
        valid_evaluations = [e for e in evaluations if not e.get("evaluation_failed", False)]
        
        if len(valid_evaluations) < 2:
            return {"insufficient_data": True}
        
        # Analyze agreement on key metrics
        ratings = [e.get("rating", 0) for e in valid_evaluations]
        would_read = [e.get("would_read", False) for e in valid_evaluations]
        interest_levels = [e.get("interest_level", "medium") for e in valid_evaluations]
        
        # Calculate consensus strength
        rating_variance = self._calculate_variance(ratings)
        would_read_consensus = max(would_read.count(True), would_read.count(False)) / len(would_read)
        
        # Most common interest level
        interest_mode = max(set(interest_levels), key=interest_levels.count)
        interest_consensus = interest_levels.count(interest_mode) / len(interest_levels)
        
        # Identify common themes in feedback
        common_themes = self._extract_common_themes(valid_evaluations)
        
        return {
            "rating_consensus": "high" if rating_variance < 1.0 else "medium" if rating_variance < 2.0 else "low",
            "rating_variance": rating_variance,
            "would_read_consensus": would_read_consensus,
            "interest_level_consensus": interest_consensus,
            "dominant_interest_level": interest_mode,
            "common_themes": common_themes,
            "overall_consensus": "high" if (rating_variance < 1.0 and would_read_consensus > 0.7) else "medium" if (rating_variance < 2.0 and would_read_consensus > 0.6) else "low"
        }
    
    def _analyze_demographic_breakdown(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze evaluation results by demographic groups."""
        if not evaluations:
            return {}
        
        valid_evaluations = [e for e in evaluations if not e.get("evaluation_failed", False)]
        
        breakdown = {
            "by_age_group": {},
            "by_gender": {},
            "by_reading_level": {},
            "by_location": {}
        }
        
        # Group evaluations by demographics
        for evaluation in valid_evaluations:
            demographics = evaluation.get("reader_demographics", {})
            rating = evaluation.get("rating", 0)
            would_read = evaluation.get("would_read", False)
            
            # Age group breakdown
            age_group = demographics.get("age_group", "unknown")
            if age_group not in breakdown["by_age_group"]:
                breakdown["by_age_group"][age_group] = {"ratings": [], "would_read": []}
            breakdown["by_age_group"][age_group]["ratings"].append(rating)
            breakdown["by_age_group"][age_group]["would_read"].append(would_read)
            
            # Gender breakdown
            gender = demographics.get("gender", "unknown")
            if gender not in breakdown["by_gender"]:
                breakdown["by_gender"][gender] = {"ratings": [], "would_read": []}
            breakdown["by_gender"][gender]["ratings"].append(rating)
            breakdown["by_gender"][gender]["would_read"].append(would_read)
            
            # Reading level breakdown
            reading_level = demographics.get("reading_level", "unknown")
            if reading_level not in breakdown["by_reading_level"]:
                breakdown["by_reading_level"][reading_level] = {"ratings": [], "would_read": []}
            breakdown["by_reading_level"][reading_level]["ratings"].append(rating)
            breakdown["by_reading_level"][reading_level]["would_read"].append(would_read)
        
        # Calculate averages for each group
        for category in breakdown:
            for group in breakdown[category]:
                ratings = breakdown[category][group]["ratings"]
                would_read = breakdown[category][group]["would_read"]
                
                breakdown[category][group] = {
                    "average_rating": sum(ratings) / len(ratings) if ratings else 0,
                    "would_read_percentage": (sum(would_read) / len(would_read)) * 100 if would_read else 0,
                    "sample_size": len(ratings)
                }
        
        return breakdown
    
    def _generate_market_insights(self, evaluations: List[Dict[str, Any]], 
                                 codex_object: CodexObject) -> Dict[str, Any]:
        """Generate market appeal insights from evaluations."""
        if not evaluations:
            return {}
        
        valid_evaluations = [e for e in evaluations if not e.get("evaluation_failed", False)]
        
        if not valid_evaluations:
            return {"error": "No valid evaluations for insights"}
        
        # Analyze appeal factors
        all_appeal_factors = []
        all_concerns = []
        
        for evaluation in valid_evaluations:
            appeal_factors = evaluation.get("appeal_factors", [])
            concerns = evaluation.get("concerns", [])
            all_appeal_factors.extend(appeal_factors)
            all_concerns.extend(concerns)
        
        # Count frequency of factors
        appeal_frequency = {}
        for factor in all_appeal_factors:
            appeal_frequency[factor] = appeal_frequency.get(factor, 0) + 1
        
        concern_frequency = {}
        for concern in all_concerns:
            concern_frequency[concern] = concern_frequency.get(concern, 0) + 1
        
        # Sort by frequency
        top_appeals = sorted(appeal_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        top_concerns = sorted(concern_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Market positioning insights
        average_rating = sum(e.get("rating", 0) for e in valid_evaluations) / len(valid_evaluations)
        would_read_percentage = (sum(1 for e in valid_evaluations if e.get("would_read", False)) / len(valid_evaluations)) * 100
        
        market_position = "strong" if average_rating >= 4.0 and would_read_percentage >= 70 else \
                         "moderate" if average_rating >= 3.0 and would_read_percentage >= 50 else "weak"
        
        return {
            "market_position": market_position,
            "overall_appeal_score": average_rating,
            "market_interest_percentage": would_read_percentage,
            "top_appeal_factors": [{"factor": factor, "mentions": count} for factor, count in top_appeals],
            "top_concerns": [{"concern": concern, "mentions": count} for concern, count in top_concerns],
            "genre_fit": self._assess_genre_fit(codex_object, valid_evaluations),
            "target_audience_insights": self._generate_audience_insights(valid_evaluations),
            "improvement_suggestions": self._generate_improvement_suggestions(top_concerns, valid_evaluations)
        }
    
    def _calculate_distribution(self, values: List[float], bins: List[int]) -> Dict[str, int]:
        """Calculate distribution of values across bins."""
        distribution = {str(bin_val): 0 for bin_val in bins}
        
        for value in values:
            # Find closest bin
            closest_bin = min(bins, key=lambda x: abs(x - value))
            distribution[str(closest_bin)] += 1
        
        return distribution
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def _extract_common_themes(self, evaluations: List[Dict[str, Any]]) -> List[str]:
        """Extract common themes from evaluation feedback."""
        # Simplified theme extraction - would use NLP in real implementation
        all_feedback = []
        for evaluation in evaluations:
            feedback = evaluation.get("feedback", "")
            if feedback and len(feedback) > 10:
                all_feedback.append(feedback.lower())
        
        # Look for common words/phrases
        common_words = ["interesting", "compelling", "boring", "confusing", "engaging", "predictable"]
        themes = []
        
        for word in common_words:
            count = sum(1 for feedback in all_feedback if word in feedback)
            if count >= len(all_feedback) * 0.3:  # 30% threshold
                themes.append(f"{word} ({count} mentions)")
        
        return themes[:5]  # Top 5 themes
    
    def _assess_genre_fit(self, codex_object: CodexObject, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess how well the content fits its stated genre."""
        genre = codex_object.genre or "Unknown"
        
        # Analyze demographic fit for genre
        genre_appropriate_ratings = []
        for evaluation in evaluations:
            demographics = evaluation.get("reader_demographics", {})
            # Simplified - would use actual genre preference data
            genre_appropriate_ratings.append(evaluation.get("rating", 0))
        
        avg_genre_rating = sum(genre_appropriate_ratings) / len(genre_appropriate_ratings) if genre_appropriate_ratings else 0
        
        return {
            "stated_genre": genre,
            "genre_fit_score": avg_genre_rating,
            "genre_fit_assessment": "good" if avg_genre_rating >= 3.5 else "moderate" if avg_genre_rating >= 2.5 else "poor"
        }
    
    def _generate_audience_insights(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights about target audience."""
        # Find demographics with highest ratings
        demo_ratings = {}
        
        for evaluation in evaluations:
            demographics = evaluation.get("reader_demographics", {})
            rating = evaluation.get("rating", 0)
            
            for demo_type, demo_value in demographics.items():
                if demo_type not in demo_ratings:
                    demo_ratings[demo_type] = {}
                if demo_value not in demo_ratings[demo_type]:
                    demo_ratings[demo_type][demo_value] = []
                demo_ratings[demo_type][demo_value].append(rating)
        
        # Find best performing demographics
        best_demographics = {}
        for demo_type, demo_groups in demo_ratings.items():
            best_group = None
            best_rating = 0
            
            for group, ratings in demo_groups.items():
                avg_rating = sum(ratings) / len(ratings)
                if avg_rating > best_rating:
                    best_rating = avg_rating
                    best_group = group
            
            if best_group:
                best_demographics[demo_type] = {
                    "group": best_group,
                    "average_rating": best_rating
                }
        
        return {
            "primary_target_demographics": best_demographics,
            "audience_size_estimate": "medium",  # Would calculate based on demographic data
            "market_penetration_potential": "moderate"  # Would calculate based on genre and demographics
        }
    
    def _generate_improvement_suggestions(self, top_concerns: List[Tuple[str, int]], 
                                        evaluations: List[Dict[str, Any]]) -> List[str]:
        """Generate improvement suggestions based on reader concerns."""
        suggestions = []
        
        for concern, count in top_concerns:
            if count >= len(evaluations) * 0.3:  # If 30% or more mentioned this concern
                if "predictable" in concern.lower():
                    suggestions.append("Consider adding unexpected plot twists or character developments")
                elif "boring" in concern.lower():
                    suggestions.append("Increase pacing and add more engaging conflict or tension")
                elif "confusing" in concern.lower():
                    suggestions.append("Clarify plot points and character motivations")
                elif "character" in concern.lower():
                    suggestions.append("Develop characters with more depth and relatable motivations")
                elif "pacing" in concern.lower():
                    suggestions.append("Review story pacing and consider restructuring for better flow")
        
        return suggestions[:3]  # Top 3 suggestions