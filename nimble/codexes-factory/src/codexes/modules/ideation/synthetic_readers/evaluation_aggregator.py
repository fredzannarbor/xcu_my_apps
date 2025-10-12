"""
Evaluation aggregation for synthetic reader panels.
Aggregates and analyzes results from multiple reader evaluations.
"""

import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from .reader_panel import ReaderEvaluation, ReaderPersona

logger = logging.getLogger(__name__)


@dataclass
class PanelResults:
    """Aggregated results from a synthetic reader panel."""
    panel_uuid: str
    object_uuid: str
    panel_size: int
    average_rating: float
    would_read_percentage: float
    consensus_patterns: Dict[str, Any] = field(default_factory=dict)
    individual_evaluations: List[Dict[str, Any]] = field(default_factory=list)
    demographic_breakdown: Dict[str, Any] = field(default_factory=dict)
    evaluation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary format."""
        return {
            "panel_uuid": self.panel_uuid,
            "object_uuid": self.object_uuid,
            "panel_size": self.panel_size,
            "average_rating": self.average_rating,
            "would_read_percentage": self.would_read_percentage,
            "consensus_patterns": self.consensus_patterns,
            "individual_evaluations": self.individual_evaluations,
            "demographic_breakdown": self.demographic_breakdown,
            "evaluation_timestamp": self.evaluation_timestamp
        }


@dataclass
class AggregatedResults:
    """Aggregated results from multiple panel evaluations."""
    object_uuid: str
    total_panels: int
    total_readers: int
    overall_rating: float
    overall_would_read_percentage: float
    confidence_score: float
    demographic_insights: Dict[str, Any] = field(default_factory=dict)
    consensus_analysis: Dict[str, Any] = field(default_factory=dict)
    market_recommendations: List[str] = field(default_factory=list)
    aggregation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class EvaluationAggregator:
    """
    Aggregates and analyzes results from multiple reader panel evaluations.
    Implements Requirements 5.4 and 5.5 for result aggregation and consensus analysis.
    """
    
    def __init__(self):
        """Initialize evaluation aggregator."""
        logger.info("EvaluationAggregator initialized")
    
    def aggregate_panel_results(self, panel_results: List[PanelResults]) -> AggregatedResults:
        """
        Aggregate results from multiple panel evaluations.
        
        Args:
            panel_results: List of panel evaluation results
            
        Returns:
            Aggregated results across all panels
        """
        try:
            if not panel_results:
                raise ValueError("No panel results provided for aggregation")
            
            # Verify all results are for the same object
            object_uuid = panel_results[0].object_uuid
            if not all(result.object_uuid == object_uuid for result in panel_results):
                raise ValueError("All panel results must be for the same object")
            
            # Collect all individual evaluations
            all_evaluations = []
            total_panels = len(panel_results)
            
            for panel_result in panel_results:
                all_evaluations.extend(panel_result.individual_evaluations)
            
            total_readers = len(all_evaluations)
            
            # Calculate overall metrics
            overall_rating = self._calculate_overall_rating(all_evaluations)
            overall_would_read = self._calculate_overall_would_read_percentage(all_evaluations)
            confidence_score = self._calculate_aggregation_confidence(panel_results, all_evaluations)
            
            # Generate insights
            demographic_insights = self._generate_demographic_insights(all_evaluations)
            consensus_analysis = self._analyze_cross_panel_consensus(panel_results)
            market_recommendations = self._generate_market_recommendations(all_evaluations, demographic_insights)
            
            aggregated = AggregatedResults(
                object_uuid=object_uuid,
                total_panels=total_panels,
                total_readers=total_readers,
                overall_rating=overall_rating,
                overall_would_read_percentage=overall_would_read,
                confidence_score=confidence_score,
                demographic_insights=demographic_insights,
                consensus_analysis=consensus_analysis,
                market_recommendations=market_recommendations
            )
            
            logger.info(f"Aggregated {total_panels} panels ({total_readers} readers): rating {overall_rating:.2f}, {overall_would_read:.1f}% would read")
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating panel results: {e}")
            raise
    
    def compare_panel_results(self, panel_results: List[PanelResults]) -> Dict[str, Any]:
        """
        Compare results across different panels.
        
        Args:
            panel_results: List of panel results to compare
            
        Returns:
            Comparison analysis
        """
        try:
            if len(panel_results) < 2:
                return {"error": "Need at least 2 panels for comparison"}
            
            comparison = {
                "panel_count": len(panel_results),
                "rating_comparison": {},
                "consensus_comparison": {},
                "demographic_differences": {},
                "reliability_analysis": {}
            }
            
            # Compare ratings across panels
            panel_ratings = []
            for i, panel in enumerate(panel_results):
                panel_ratings.append({
                    "panel_index": i,
                    "average_rating": panel.average_rating,
                    "would_read_percentage": panel.would_read_percentage,
                    "panel_size": panel.panel_size
                })
            
            comparison["rating_comparison"] = {
                "panel_ratings": panel_ratings,
                "rating_variance": statistics.variance([p["average_rating"] for p in panel_ratings]) if len(panel_ratings) > 1 else 0,
                "rating_range": {
                    "min": min(p["average_rating"] for p in panel_ratings),
                    "max": max(p["average_rating"] for p in panel_ratings)
                }
            }
            
            # Analyze consensus differences
            consensus_scores = []
            for panel in panel_results:
                consensus = panel.consensus_patterns.get("overall_consensus", "medium")
                consensus_scores.append(consensus)
            
            comparison["consensus_comparison"] = {
                "consensus_distribution": {level: consensus_scores.count(level) for level in set(consensus_scores)},
                "consistent_consensus": len(set(consensus_scores)) == 1
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing panel results: {e}")
            return {"error": str(e)}
    
    def validate_reader_consistency(self, reader_evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate consistency of reader evaluations.
        Implements Requirement 5.6 for consistency analysis.
        
        Args:
            reader_evaluations: List of evaluations from the same reader
            
        Returns:
            Consistency analysis
        """
        try:
            if len(reader_evaluations) < 2:
                return {"error": "Need at least 2 evaluations for consistency analysis"}
            
            # Analyze rating consistency
            ratings = [e.get("rating", 0) for e in reader_evaluations]
            rating_variance = statistics.variance(ratings) if len(ratings) > 1 else 0
            
            # Analyze would_read consistency
            would_read_decisions = [e.get("would_read", False) for e in reader_evaluations]
            would_read_consistency = max(would_read_decisions.count(True), would_read_decisions.count(False)) / len(would_read_decisions)
            
            # Analyze feedback quality consistency
            feedback_lengths = [len(e.get("feedback", "")) for e in reader_evaluations]
            avg_feedback_length = sum(feedback_lengths) / len(feedback_lengths)
            feedback_variance = statistics.variance(feedback_lengths) if len(feedback_lengths) > 1 else 0
            
            # Overall consistency score
            consistency_factors = [
                1.0 - min(rating_variance / 4.0, 1.0),  # Rating consistency (variance normalized)
                would_read_consistency,  # Decision consistency
                1.0 - min(feedback_variance / (avg_feedback_length ** 2), 1.0) if avg_feedback_length > 0 else 0.5  # Feedback consistency
            ]
            
            overall_consistency = sum(consistency_factors) / len(consistency_factors)
            
            return {
                "overall_consistency_score": overall_consistency,
                "rating_consistency": {
                    "variance": rating_variance,
                    "range": max(ratings) - min(ratings) if ratings else 0,
                    "consistency_level": "high" if rating_variance < 0.5 else "medium" if rating_variance < 1.5 else "low"
                },
                "decision_consistency": {
                    "would_read_consistency": would_read_consistency,
                    "consistency_level": "high" if would_read_consistency > 0.8 else "medium" if would_read_consistency > 0.6 else "low"
                },
                "feedback_consistency": {
                    "average_length": avg_feedback_length,
                    "length_variance": feedback_variance,
                    "quality_consistency": "high" if feedback_variance < 100 else "medium" if feedback_variance < 400 else "low"
                },
                "evaluation_count": len(reader_evaluations),
                "reliability_assessment": "reliable" if overall_consistency > 0.7 else "moderate" if overall_consistency > 0.5 else "unreliable"
            }
            
        except Exception as e:
            logger.error(f"Error validating reader consistency: {e}")
            return {"error": str(e)}
    
    def generate_panel_reliability_report(self, panel_results: List[PanelResults]) -> Dict[str, Any]:
        """
        Generate reliability report for reader panels.
        
        Args:
            panel_results: List of panel results to analyze
            
        Returns:
            Panel reliability report
        """
        try:
            if not panel_results:
                return {"error": "No panel results provided"}
            
            report = {
                "total_panels_analyzed": len(panel_results),
                "panel_reliability_scores": [],
                "overall_reliability": {},
                "recommendations": []
            }
            
            # Analyze each panel
            panel_reliabilities = []
            for i, panel in enumerate(panel_results):
                panel_reliability = self._assess_panel_reliability(panel)
                panel_reliabilities.append(panel_reliability)
                
                report["panel_reliability_scores"].append({
                    "panel_index": i,
                    "panel_uuid": panel.panel_uuid,
                    "reliability_score": panel_reliability["overall_score"],
                    "evaluation_success_rate": panel_reliability["evaluation_success_rate"],
                    "consensus_strength": panel_reliability["consensus_strength"]
                })
            
            # Calculate overall reliability
            overall_scores = [p["overall_score"] for p in panel_reliabilities]
            report["overall_reliability"] = {
                "average_reliability": sum(overall_scores) / len(overall_scores),
                "reliability_variance": statistics.variance(overall_scores) if len(overall_scores) > 1 else 0,
                "reliable_panels": sum(1 for score in overall_scores if score > 0.7),
                "unreliable_panels": sum(1 for score in overall_scores if score < 0.5)
            }
            
            # Generate recommendations
            avg_reliability = report["overall_reliability"]["average_reliability"]
            if avg_reliability < 0.6:
                report["recommendations"].append("Consider using more consistent reader personas")
                report["recommendations"].append("Review evaluation criteria and prompts")
            
            if report["overall_reliability"]["unreliable_panels"] > len(panel_results) * 0.3:
                report["recommendations"].append("Filter out unreliable panels from final analysis")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating reliability report: {e}")
            return {"error": str(e)}
    
    def _calculate_overall_rating(self, all_evaluations: List[Dict[str, Any]]) -> float:
        """Calculate overall rating across all evaluations."""
        valid_evaluations = [e for e in all_evaluations if not e.get("evaluation_failed", False)]
        
        if not valid_evaluations:
            return 0.0
        
        ratings = [e.get("rating", 0) for e in valid_evaluations]
        return sum(ratings) / len(ratings)
    
    def _calculate_overall_would_read_percentage(self, all_evaluations: List[Dict[str, Any]]) -> float:
        """Calculate overall would-read percentage."""
        valid_evaluations = [e for e in all_evaluations if not e.get("evaluation_failed", False)]
        
        if not valid_evaluations:
            return 0.0
        
        would_read_count = sum(1 for e in valid_evaluations if e.get("would_read", False))
        return (would_read_count / len(valid_evaluations)) * 100
    
    def _calculate_aggregation_confidence(self, panel_results: List[PanelResults], 
                                        all_evaluations: List[Dict[str, Any]]) -> float:
        """Calculate confidence in the aggregated results."""
        factors = []
        
        # Factor 1: Number of evaluations
        eval_count_factor = min(len(all_evaluations) / 20, 1.0)  # Max confidence at 20+ evaluations
        factors.append(eval_count_factor)
        
        # Factor 2: Panel diversity
        panel_count_factor = min(len(panel_results) / 3, 1.0)  # Max confidence at 3+ panels
        factors.append(panel_count_factor)
        
        # Factor 3: Evaluation success rate
        valid_evaluations = [e for e in all_evaluations if not e.get("evaluation_failed", False)]
        success_rate = len(valid_evaluations) / len(all_evaluations) if all_evaluations else 0
        factors.append(success_rate)
        
        # Factor 4: Consensus strength
        if panel_results:
            consensus_scores = []
            for panel in panel_results:
                consensus = panel.consensus_patterns.get("overall_consensus", "medium")
                score = {"high": 1.0, "medium": 0.6, "low": 0.3}.get(consensus, 0.5)
                consensus_scores.append(score)
            avg_consensus = sum(consensus_scores) / len(consensus_scores)
            factors.append(avg_consensus)
        
        return sum(factors) / len(factors)
    
    def _generate_demographic_insights(self, all_evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights across all demographic groups."""
        valid_evaluations = [e for e in all_evaluations if not e.get("evaluation_failed", False)]
        
        if not valid_evaluations:
            return {"error": "No valid evaluations"}
        
        # Group by demographics
        demographic_groups = {}
        
        for evaluation in valid_evaluations:
            demographics = evaluation.get("reader_demographics", {})
            
            for demo_type, demo_value in demographics.items():
                if demo_type not in demographic_groups:
                    demographic_groups[demo_type] = {}
                if demo_value not in demographic_groups[demo_type]:
                    demographic_groups[demo_type][demo_value] = []
                
                demographic_groups[demo_type][demo_value].append(evaluation)
        
        # Analyze each demographic dimension
        insights = {}
        
        for demo_type, groups in demographic_groups.items():
            insights[demo_type] = {}
            
            for group_name, group_evaluations in groups.items():
                ratings = [e.get("rating", 0) for e in group_evaluations]
                would_read = [e.get("would_read", False) for e in group_evaluations]
                
                insights[demo_type][group_name] = {
                    "sample_size": len(group_evaluations),
                    "average_rating": sum(ratings) / len(ratings) if ratings else 0,
                    "would_read_percentage": (sum(would_read) / len(would_read)) * 100 if would_read else 0,
                    "rating_variance": statistics.variance(ratings) if len(ratings) > 1 else 0
                }
        
        # Identify best and worst performing demographics
        best_demographics = self._identify_best_demographics(insights)
        worst_demographics = self._identify_worst_demographics(insights)
        
        return {
            "demographic_breakdown": insights,
            "best_performing_demographics": best_demographics,
            "worst_performing_demographics": worst_demographics,
            "demographic_diversity_score": self._calculate_demographic_diversity(demographic_groups)
        }
    
    def _analyze_cross_panel_consensus(self, panel_results: List[PanelResults]) -> Dict[str, Any]:
        """Analyze consensus patterns across multiple panels."""
        if len(panel_results) < 2:
            return {"error": "Need at least 2 panels for consensus analysis"}
        
        # Compare ratings across panels
        panel_ratings = [panel.average_rating for panel in panel_results]
        rating_variance = statistics.variance(panel_ratings) if len(panel_ratings) > 1 else 0
        
        # Compare would-read percentages
        would_read_percentages = [panel.would_read_percentage for panel in panel_results]
        would_read_variance = statistics.variance(would_read_percentages) if len(would_read_percentages) > 1 else 0
        
        # Analyze consensus patterns within each panel
        panel_consensus_levels = []
        for panel in panel_results:
            consensus_level = panel.consensus_patterns.get("overall_consensus", "medium")
            panel_consensus_levels.append(consensus_level)
        
        # Cross-panel consensus strength
        cross_panel_consensus = "high" if rating_variance < 0.5 and would_read_variance < 100 else \
                               "medium" if rating_variance < 1.0 and would_read_variance < 400 else "low"
        
        return {
            "cross_panel_consensus": cross_panel_consensus,
            "rating_variance_across_panels": rating_variance,
            "would_read_variance_across_panels": would_read_variance,
            "panel_consensus_distribution": {level: panel_consensus_levels.count(level) for level in set(panel_consensus_levels)},
            "agreement_strength": self._calculate_agreement_strength(panel_results)
        }
    
    def _generate_market_recommendations(self, all_evaluations: List[Dict[str, Any]], 
                                       demographic_insights: Dict[str, Any]) -> List[str]:
        """Generate market recommendations based on evaluation results."""
        recommendations = []
        
        # Overall performance recommendations
        avg_rating = sum(e.get("rating", 0) for e in all_evaluations) / len(all_evaluations) if all_evaluations else 0
        would_read_pct = (sum(1 for e in all_evaluations if e.get("would_read", False)) / len(all_evaluations)) * 100 if all_evaluations else 0
        
        if avg_rating >= 4.0 and would_read_pct >= 70:
            recommendations.append("Strong market potential - proceed with development")
        elif avg_rating >= 3.0 and would_read_pct >= 50:
            recommendations.append("Moderate market potential - consider refinements")
        else:
            recommendations.append("Weak market potential - significant revisions needed")
        
        # Demographic targeting recommendations
        best_demographics = demographic_insights.get("best_performing_demographics", {})
        if best_demographics:
            for demo_type, demo_data in best_demographics.items():
                if demo_data["average_rating"] >= 3.5:
                    recommendations.append(f"Target {demo_type}: {demo_data['group']} (avg rating: {demo_data['average_rating']:.1f})")
        
        # Content improvement recommendations
        common_concerns = []
        for evaluation in all_evaluations:
            concerns = evaluation.get("concerns", [])
            common_concerns.extend(concerns)
        
        if common_concerns:
            concern_frequency = {}
            for concern in common_concerns:
                concern_frequency[concern] = concern_frequency.get(concern, 0) + 1
            
            top_concerns = sorted(concern_frequency.items(), key=lambda x: x[1], reverse=True)[:2]
            for concern, count in top_concerns:
                if count >= len(all_evaluations) * 0.3:
                    recommendations.append(f"Address reader concern: {concern}")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _identify_best_demographics(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Identify best performing demographic groups."""
        best_demographics = {}
        
        for demo_type, groups in insights.items():
            if demo_type == "demographic_breakdown":
                continue
                
            best_group = None
            best_rating = 0
            
            for group_name, group_data in groups.items():
                avg_rating = group_data.get("average_rating", 0)
                sample_size = group_data.get("sample_size", 0)
                
                # Only consider groups with reasonable sample size
                if sample_size >= 2 and avg_rating > best_rating:
                    best_rating = avg_rating
                    best_group = group_name
            
            if best_group:
                best_demographics[demo_type] = {
                    "group": best_group,
                    "average_rating": best_rating,
                    "sample_size": groups[best_group]["sample_size"]
                }
        
        return best_demographics
    
    def _identify_worst_demographics(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Identify worst performing demographic groups."""
        worst_demographics = {}
        
        for demo_type, groups in insights.items():
            if demo_type == "demographic_breakdown":
                continue
                
            worst_group = None
            worst_rating = 5.0  # Start with max rating
            
            for group_name, group_data in groups.items():
                avg_rating = group_data.get("average_rating", 0)
                sample_size = group_data.get("sample_size", 0)
                
                # Only consider groups with reasonable sample size
                if sample_size >= 2 and avg_rating < worst_rating:
                    worst_rating = avg_rating
                    worst_group = group_name
            
            if worst_group:
                worst_demographics[demo_type] = {
                    "group": worst_group,
                    "average_rating": worst_rating,
                    "sample_size": groups[worst_group]["sample_size"]
                }
        
        return worst_demographics
    
    def _calculate_demographic_diversity(self, demographic_groups: Dict[str, Any]) -> float:
        """Calculate diversity score for demographic representation."""
        diversity_scores = []
        
        for demo_type, groups in demographic_groups.items():
            # Calculate entropy-like measure of diversity
            total_count = sum(len(group_evals) for group_evals in groups.values())
            
            if total_count == 0:
                continue
            
            # Calculate distribution entropy
            entropy = 0
            for group_evals in groups.values():
                if len(group_evals) > 0:
                    proportion = len(group_evals) / total_count
                    entropy -= proportion * (proportion.bit_length() - 1) if proportion > 0 else 0
            
            # Normalize entropy (0-1 scale)
            max_entropy = (len(groups).bit_length() - 1) if len(groups) > 1 else 1
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            diversity_scores.append(normalized_entropy)
        
        return sum(diversity_scores) / len(diversity_scores) if diversity_scores else 0
    
    def _assess_panel_reliability(self, panel_result: PanelResults) -> Dict[str, Any]:
        """Assess reliability of a single panel."""
        evaluations = panel_result.individual_evaluations
        valid_evaluations = [e for e in evaluations if not e.get("evaluation_failed", False)]
        
        evaluation_success_rate = len(valid_evaluations) / len(evaluations) if evaluations else 0
        
        # Assess consensus strength
        consensus_level = panel_result.consensus_patterns.get("overall_consensus", "medium")
        consensus_strength = {"high": 1.0, "medium": 0.6, "low": 0.3}.get(consensus_level, 0.5)
        
        # Overall reliability score
        overall_score = (evaluation_success_rate + consensus_strength) / 2
        
        return {
            "overall_score": overall_score,
            "evaluation_success_rate": evaluation_success_rate,
            "consensus_strength": consensus_strength,
            "reliability_level": "high" if overall_score > 0.7 else "medium" if overall_score > 0.5 else "low"
        }
    
    def _calculate_agreement_strength(self, panel_results: List[PanelResults]) -> float:
        """Calculate agreement strength across panels."""
        if len(panel_results) < 2:
            return 1.0
        
        # Compare average ratings
        ratings = [panel.average_rating for panel in panel_results]
        rating_agreement = 1.0 - min(statistics.variance(ratings) / 4.0, 1.0) if len(ratings) > 1 else 1.0
        
        # Compare would-read percentages
        would_read_pcts = [panel.would_read_percentage for panel in panel_results]
        would_read_agreement = 1.0 - min(statistics.variance(would_read_pcts) / 2500, 1.0) if len(would_read_pcts) > 1 else 1.0
        
        return (rating_agreement + would_read_agreement) / 2