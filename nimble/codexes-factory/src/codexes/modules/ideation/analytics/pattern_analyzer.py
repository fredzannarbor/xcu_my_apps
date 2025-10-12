"""
Pattern analysis system for identifying successful idea characteristics.
Analyzes patterns in successful ideas and provides insights for improvement.
"""

import logging
import statistics
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ..core.codex_object import CodexObject
from ..tournament.tournament_engine import Tournament

logger = logging.getLogger(__name__)


@dataclass
class SuccessPattern:
    """Represents a pattern found in successful ideas."""
    pattern_id: str
    pattern_type: str  # "genre", "theme", "length", "tone", etc.
    pattern_value: str
    success_rate: float
    occurrence_count: int
    confidence_score: float
    supporting_examples: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)


@dataclass
class AnalysisResult:
    """Result of pattern analysis."""
    analysis_id: str
    total_concepts_analyzed: int
    success_patterns: List[SuccessPattern]
    failure_patterns: List[SuccessPattern]
    recommendations: List[str]
    confidence_score: float
    analysis_timestamp: datetime = field(default_factory=datetime.now)


class PatternAnalyzer:
    """Analyzes patterns in successful and unsuccessful ideas."""
    
    def __init__(self):
        """Initialize the pattern analyzer."""
        self.analysis_history: List[AnalysisResult] = []
        self.cached_patterns: Dict[str, List[SuccessPattern]] = {}
        logger.info("PatternAnalyzer initialized")
    
    def analyze_success_patterns(self, concepts: List[CodexObject], 
                               success_metrics: Dict[str, float]) -> AnalysisResult:
        """
        Analyze patterns in successful vs unsuccessful concepts.
        
        Args:
            concepts: List of concepts to analyze
            success_metrics: Dictionary mapping concept UUIDs to success scores
            
        Returns:
            AnalysisResult with identified patterns
        """
        try:
            # Categorize concepts by success
            successful_concepts, unsuccessful_concepts = self._categorize_by_success(
                concepts, success_metrics
            )
            
            if not successful_concepts:
                logger.warning("No successful concepts found for pattern analysis")
                return AnalysisResult(
                    analysis_id=f"analysis_{len(self.analysis_history)}",
                    total_concepts_analyzed=len(concepts),
                    success_patterns=[],
                    failure_patterns=[],
                    recommendations=["Need more successful concepts for meaningful analysis"],
                    confidence_score=0.0
                )
            
            # Analyze patterns in successful concepts
            success_patterns = self._extract_patterns(successful_concepts, "success")
            
            # Analyze patterns in unsuccessful concepts
            failure_patterns = []
            if unsuccessful_concepts:
                failure_patterns = self._extract_patterns(unsuccessful_concepts, "failure")
            
            # Generate recommendations
            recommendations = self._generate_recommendations(success_patterns, failure_patterns)
            
            # Calculate overall confidence
            confidence_score = self._calculate_analysis_confidence(
                len(successful_concepts), len(unsuccessful_concepts), success_patterns
            )
            
            # Create analysis result
            result = AnalysisResult(
                analysis_id=f"analysis_{len(self.analysis_history)}",
                total_concepts_analyzed=len(concepts),
                success_patterns=success_patterns,
                failure_patterns=failure_patterns,
                recommendations=recommendations,
                confidence_score=confidence_score
            )
            
            # Store result
            self.analysis_history.append(result)
            
            logger.info(f"Pattern analysis completed: {len(success_patterns)} success patterns, {len(failure_patterns)} failure patterns")
            return result
            
        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}")
            return AnalysisResult(
                analysis_id=f"error_analysis_{len(self.analysis_history)}",
                total_concepts_analyzed=len(concepts),
                success_patterns=[],
                failure_patterns=[],
                recommendations=[f"Analysis failed: {str(e)}"],
                confidence_score=0.0
            )
    
    def _categorize_by_success(self, concepts: List[CodexObject], 
                             success_metrics: Dict[str, float]) -> Tuple[List[CodexObject], List[CodexObject]]:
        """Categorize ideas into successful and unsuccessful based on metrics."""
        try:
            # Calculate success threshold (median or 70th percentile)
            all_scores = [score for score in success_metrics.values() if score is not None]
            
            if not all_scores:
                return concepts[:len(concepts)//2], concepts[len(concepts)//2:]
            
            threshold = statistics.median(all_scores)
            if len(all_scores) > 5:
                # Use 70th percentile for larger datasets
                threshold = statistics.quantiles(all_scores, n=10)[6]  # 70th percentile
            
            successful = []
            unsuccessful = []
            
            for concept in concepts:
                score = success_metrics.get(concept.uuid)
                if score is not None:
                    if score >= threshold:
                        successful.append(concept)
                    else:
                        unsuccessful.append(concept)
                else:
                    # No score available, categorize based on position
                    if len(successful) <= len(unsuccessful):
                        successful.append(concept)
                    else:
                        unsuccessful.append(concept)
            
            return successful, unsuccessful
            
        except Exception as e:
            logger.error(f"Error categorizing concepts: {e}")
            # Fallback: split in half
            mid = len(concepts) // 2
            return concepts[:mid], concepts[mid:]
    
    def _extract_patterns(self, concepts: List[CodexObject], pattern_category: str) -> List[SuccessPattern]:
        """Extract patterns from a group of concepts."""
        patterns = []
        
        try:
            # Analyze genre patterns
            genre_patterns = self._analyze_attribute_patterns(concepts, "genre", pattern_category)
            patterns.extend(genre_patterns)
            
            # Analyze theme patterns
            theme_patterns = self._analyze_theme_patterns(concepts, pattern_category)
            patterns.extend(theme_patterns)
            
            # Analyze length patterns
            length_patterns = self._analyze_length_patterns(concepts, pattern_category)
            patterns.extend(length_patterns)
            
            # Analyze content patterns
            content_patterns = self._analyze_content_patterns(concepts, pattern_category)
            patterns.extend(content_patterns)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            return []
    
    def _analyze_attribute_patterns(self, concepts: List[CodexObject], 
                                  attribute: str, category: str) -> List[SuccessPattern]:
        """Analyze patterns in a specific attribute."""
        patterns = []
        
        try:
            # Count attribute values
            attribute_counts = Counter()
            
            for concept in concepts:
                value = getattr(concept, attribute, None)
                if value:
                    attribute_counts[value] += 1
            
            # Create patterns for common attributes
            total_concepts = len(concepts)
            
            for value, count in attribute_counts.most_common(5):  # Top 5 patterns
                if count >= 2:  # Minimum occurrence threshold
                    success_rate = count / total_concepts
                    confidence = min(success_rate * 2, 1.0)  # Simple confidence calculation
                    
                    pattern = SuccessPattern(
                        pattern_id=f"{category}_{attribute}_{value}",
                        pattern_type=attribute,
                        pattern_value=value,
                        success_rate=success_rate,
                        occurrence_count=count,
                        confidence_score=confidence,
                        supporting_examples=[c.title for c in concepts if getattr(c, attribute, None) == value][:3]
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing {attribute} patterns: {e}")
            return []
    
    def _analyze_theme_patterns(self, concepts: List[CodexObject], category: str) -> List[SuccessPattern]:
        """Analyze theme patterns in concepts."""
        patterns = []
        
        try:
            # Collect all themes
            all_themes = []
            for concept in concepts:
                if hasattr(concept, 'themes') and concept.themes:
                    all_themes.extend(concept.themes)
            
            if not all_themes:
                return patterns
            
            # Count theme occurrences
            theme_counts = Counter(all_themes)
            total_concepts = len(concepts)
            
            for theme, count in theme_counts.most_common(5):
                if count >= 2:
                    success_rate = count / total_concepts
                    confidence = min(success_rate * 1.5, 1.0)
                    
                    supporting_examples = [
                        c.title for c in concepts 
                        if hasattr(c, 'themes') and c.themes and theme in c.themes
                    ][:3]
                    
                    pattern = SuccessPattern(
                        pattern_id=f"{category}_theme_{theme}",
                        pattern_type="theme",
                        pattern_value=theme,
                        success_rate=success_rate,
                        occurrence_count=count,
                        confidence_score=confidence,
                        supporting_examples=supporting_examples
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing theme patterns: {e}")
            return []
    
    def _analyze_length_patterns(self, concepts: List[CodexObject], category: str) -> List[SuccessPattern]:
        """Analyze content length patterns."""
        patterns = []
        
        try:
            # Categorize by content length
            length_categories = {"short": 0, "medium": 0, "long": 0}
            
            for concept in concepts:
                content_length = len(concept.content) if concept.content else 0
                
                if content_length < 100:
                    length_categories["short"] += 1
                elif content_length < 500:
                    length_categories["medium"] += 1
                else:
                    length_categories["long"] += 1
            
            total_concepts = len(concepts)
            
            for length_type, count in length_categories.items():
                if count > 0:
                    success_rate = count / total_concepts
                    confidence = min(success_rate * 1.2, 1.0)
                    
                    pattern = SuccessPattern(
                        pattern_id=f"{category}_length_{length_type}",
                        pattern_type="content_length",
                        pattern_value=length_type,
                        success_rate=success_rate,
                        occurrence_count=count,
                        confidence_score=confidence
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing length patterns: {e}")
            return []
    
    def _analyze_content_patterns(self, concepts: List[CodexObject], category: str) -> List[SuccessPattern]:
        """Analyze content-based patterns."""
        patterns = []
        
        try:
            # Simple keyword analysis
            all_words = []
            for concept in concepts:
                if concept.content:
                    words = concept.content.lower().split()
                    all_words.extend(words)
            
            if not all_words:
                return patterns
            
            # Find common words (excluding common stop words)
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
            filtered_words = [word for word in all_words if word not in stop_words and len(word) > 3]
            
            word_counts = Counter(filtered_words)
            total_concepts = len(concepts)
            
            for word, count in word_counts.most_common(3):  # Top 3 content patterns
                if count >= 2:
                    success_rate = count / total_concepts
                    confidence = min(success_rate, 0.8)  # Lower confidence for content patterns
                    
                    pattern = SuccessPattern(
                        pattern_id=f"{category}_content_{word}",
                        pattern_type="content_keyword",
                        pattern_value=word,
                        success_rate=success_rate,
                        occurrence_count=count,
                        confidence_score=confidence
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing content patterns: {e}")
            return []
    
    def _generate_recommendations(self, success_patterns: List[SuccessPattern], 
                                failure_patterns: List[SuccessPattern]) -> List[str]:
        """Generate actionable recommendations based on patterns."""
        recommendations = []
        
        try:
            # Recommendations based on success patterns
            high_confidence_success = [p for p in success_patterns if p.confidence_score > 0.7]
            
            for pattern in high_confidence_success[:3]:  # Top 3 recommendations
                if pattern.pattern_type == "genre":
                    recommendations.append(f"Consider focusing on {pattern.pattern_value} genre (success rate: {pattern.success_rate:.1%})")
                elif pattern.pattern_type == "theme":
                    recommendations.append(f"Include '{pattern.pattern_value}' theme in concepts (appears in {pattern.success_rate:.1%} of successful ideas)")
                elif pattern.pattern_type == "content_length":
                    recommendations.append(f"Aim for {pattern.pattern_value} content length (success rate: {pattern.success_rate:.1%})")
            
            # Recommendations based on failure patterns
            high_confidence_failure = [p for p in failure_patterns if p.confidence_score > 0.7]
            
            for pattern in high_confidence_failure[:2]:  # Top 2 avoidance recommendations
                if pattern.pattern_type == "genre":
                    recommendations.append(f"Consider avoiding {pattern.pattern_value} genre (appears frequently in unsuccessful concepts)")
                elif pattern.pattern_type == "theme":
                    recommendations.append(f"Be cautious with '{pattern.pattern_value}' theme (associated with lower success rates)")
            
            # General recommendations
            if not recommendations:
                recommendations.append("Generate more concepts to identify meaningful patterns")
            
            if len(success_patterns) < 3:
                recommendations.append("Increase sample size for more reliable pattern analysis")
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Unable to generate recommendations due to analysis error"]
    
    def _calculate_analysis_confidence(self, successful_count: int, unsuccessful_count: int, 
                                     patterns: List[SuccessPattern]) -> float:
        """Calculate overall confidence in the analysis."""
        try:
            # Base confidence on sample size
            total_concepts = successful_count + unsuccessful_count
            size_confidence = min(total_concepts / 20, 1.0)  # Full confidence at 20+ concepts
            
            # Factor in pattern strength
            if patterns:
                avg_pattern_confidence = sum(p.confidence_score for p in patterns) / len(patterns)
                pattern_confidence = avg_pattern_confidence
            else:
                pattern_confidence = 0.0
            
            # Balance confidence
            balance_confidence = 1.0
            if total_concepts > 0:
                balance_ratio = min(successful_count, unsuccessful_count) / total_concepts
                balance_confidence = min(balance_ratio * 2, 1.0)
            
            # Overall confidence
            overall_confidence = (size_confidence + pattern_confidence + balance_confidence) / 3
            return round(overall_confidence, 2)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    def get_analysis_history(self, limit: int = 10) -> List[AnalysisResult]:
        """Get recent analysis results."""
        return self.analysis_history[-limit:] if self.analysis_history else []
    
    def export_patterns(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Export patterns from a specific analysis."""
        try:
            analysis = next((a for a in self.analysis_history if a.analysis_id == analysis_id), None)
            
            if not analysis:
                return None
            
            return {
                "analysis_id": analysis_id,
                "export_timestamp": datetime.now().isoformat(),
                "analysis_data": {
                    "total_concepts": analysis.total_concepts_analyzed,
                    "success_patterns": [
                        {
                            "type": p.pattern_type,
                            "value": p.pattern_value,
                            "success_rate": p.success_rate,
                            "confidence": p.confidence_score,
                            "examples": p.supporting_examples
                        }
                        for p in analysis.success_patterns
                    ],
                    "failure_patterns": [
                        {
                            "type": p.pattern_type,
                            "value": p.pattern_value,
                            "failure_rate": p.success_rate,
                            "confidence": p.confidence_score
                        }
                        for p in analysis.failure_patterns
                    ],
                    "recommendations": analysis.recommendations,
                    "overall_confidence": analysis.confidence_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error exporting patterns: {e}")
            return {"error": str(e)}