"""
Consistency management for book series.
Tracks and validates consistency across series entries.
"""

import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ..core.codex_object import CodexObject
from .series_generator import SeriesBlueprint, SeriesElement

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyViolation:
    """Represents a consistency violation in a series."""
    violation_type: str
    element_name: str
    expected_value: str
    actual_value: str
    severity: str  # low, medium, high
    book_uuid: str
    book_title: str
    violation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "violation_type": self.violation_type,
            "element_name": self.element_name,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "severity": self.severity,
            "book_uuid": self.book_uuid,
            "book_title": self.book_title,
            "violation_timestamp": self.violation_timestamp
        }


@dataclass
class ConsistencyReport:
    """Report on series consistency."""
    series_uuid: str
    series_name: str
    overall_consistency_score: float
    total_books_analyzed: int
    total_violations: int
    violations_by_severity: Dict[str, int] = field(default_factory=dict)
    violations_by_element: Dict[str, int] = field(default_factory=dict)
    detailed_violations: List[ConsistencyViolation] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    report_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "series_uuid": self.series_uuid,
            "series_name": self.series_name,
            "overall_consistency_score": self.overall_consistency_score,
            "total_books_analyzed": self.total_books_analyzed,
            "total_violations": self.total_violations,
            "violations_by_severity": self.violations_by_severity,
            "violations_by_element": self.violations_by_element,
            "detailed_violations": [v.to_dict() for v in self.detailed_violations],
            "recommendations": self.recommendations,
            "report_timestamp": self.report_timestamp
        }


class ConsistencyTracker:
    """
    Tracks consistency across series entries.
    Implements Requirements 2.5, 2.6 for consistency tracking.
    """
    
    def __init__(self):
        """Initialize consistency tracker."""
        self.tracked_series: Dict[str, Dict[str, Any]] = {}
        logger.info("ConsistencyTracker initialized")
    
    def track_series_entry(self, series_uuid: str, book: CodexObject, 
                          blueprint: SeriesBlueprint):
        """
        Track a series entry for consistency analysis.
        
        Args:
            series_uuid: UUID of the series
            book: CodexObject to track
            blueprint: Series blueprint with consistency requirements
        """
        try:
            if series_uuid not in self.tracked_series:
                self.tracked_series[series_uuid] = {
                    "books": [],
                    "element_values": {},
                    "consistency_history": []
                }
            
            # Add book to tracking
            book_data = {
                "uuid": book.uuid,
                "title": book.title,
                "entry_number": getattr(book, 'series_uuid', len(self.tracked_series[series_uuid]["books"]) + 1),
                "tracked_timestamp": datetime.now().isoformat()
            }
            
            self.tracked_series[series_uuid]["books"].append(book_data)
            
            # Track element values
            self._track_element_values(series_uuid, book, blueprint)
            
            logger.info(f"Tracked series entry: {book.title} in series {series_uuid}")
            
        except Exception as e:
            logger.error(f"Error tracking series entry: {e}")
    
    def _track_element_values(self, series_uuid: str, book: CodexObject, 
                            blueprint: SeriesBlueprint):
        """Track values for consistent elements."""
        element_values = self.tracked_series[series_uuid]["element_values"]
        
        for element in blueprint.consistent_elements:
            element_key = f"{element.element_type}_{element.element_name}"
            
            if element_key not in element_values:
                element_values[element_key] = {
                    "element": element,
                    "values": [],
                    "consistency_scores": []
                }
            
            # Extract current value for this element
            current_value = self._extract_element_value(book, element)
            
            if current_value:
                element_values[element_key]["values"].append({
                    "book_uuid": book.uuid,
                    "book_title": book.title,
                    "value": current_value,
                    "timestamp": datetime.now().isoformat()
                })
    
    def _extract_element_value(self, book: CodexObject, element: SeriesElement) -> str:
        """Extract the current value of an element from a book."""
        if element.element_type == "genre":
            return book.genre
        elif element.element_type == "tone":
            return getattr(book, 'tone', '')
        elif element.element_type == "theme":
            # Return first matching theme
            themes = getattr(book, 'themes', [])
            for theme in themes:
                if theme.lower() in element.description.lower():
                    return theme
            return ""
        else:
            return ""
    
    def calculate_consistency_score(self, series_uuid: str, 
                                  element_name: str) -> float:
        """Calculate consistency score for a specific element."""
        try:
            if series_uuid not in self.tracked_series:
                return 0.0
            
            element_values = self.tracked_series[series_uuid]["element_values"]
            
            matching_elements = [k for k in element_values.keys() if element_name in k]
            if not matching_elements:
                return 0.0
            
            element_key = matching_elements[0]
            values = element_values[element_key]["values"]
            
            if len(values) < 2:
                return 1.0  # Perfect consistency with only one value
            
            # Calculate similarity between values
            similarity_scores = []
            
            for i in range(len(values)):
                for j in range(i + 1, len(values)):
                    similarity = self._calculate_text_similarity(
                        values[i]["value"], values[j]["value"]
                    )
                    similarity_scores.append(similarity)
            
            return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating consistency score: {e}")
            return 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        if not text1 or not text2:
            return 0.0
        
        if text1.lower() == text2.lower():
            return 1.0
        
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_series_consistency_metrics(self, series_uuid: str) -> Dict[str, Any]:
        """Get comprehensive consistency metrics for a series."""
        try:
            if series_uuid not in self.tracked_series:
                return {"error": "Series not tracked"}
            
            series_data = self.tracked_series[series_uuid]
            metrics = {
                "series_uuid": series_uuid,
                "total_books": len(series_data["books"]),
                "element_consistency": {},
                "overall_consistency_score": 0.0,
                "consistency_trend": []
            }
            
            # Calculate consistency for each element
            element_scores = []
            
            for element_key, element_data in series_data["element_values"].items():
                element_name = element_key.split("_", 1)[1] if "_" in element_key else element_key
                consistency_score = self.calculate_consistency_score(series_uuid, element_name)
                
                metrics["element_consistency"][element_name] = {
                    "consistency_score": consistency_score,
                    "value_count": len(element_data["values"]),
                    "required_consistency": element_data["element"].consistency_level
                }
                
                element_scores.append(consistency_score)
            
            # Overall consistency score
            metrics["overall_consistency_score"] = sum(element_scores) / len(element_scores) if element_scores else 0.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting consistency metrics: {e}")
            return {"error": str(e)}


class ConsistencyManager:
    """
    Manages consistency validation and reporting for book series.
    Implements Requirements 2.5, 2.6 for consistency management.
    """
    
    def __init__(self):
        """Initialize consistency manager."""
        self.tracker = ConsistencyTracker()
        self.violation_thresholds = {
            "high": 0.3,    # Consistency score below 0.3 = high severity
            "medium": 0.6,  # Consistency score below 0.6 = medium severity
            "low": 0.8      # Consistency score below 0.8 = low severity
        }
        logger.info("ConsistencyManager initialized")
    
    def validate_series_consistency(self, series_uuid: str, 
                                  books: List[CodexObject],
                                  blueprint: SeriesBlueprint) -> ConsistencyReport:
        """
        Validate consistency across all books in a series.
        
        Args:
            series_uuid: UUID of the series
            books: List of books in the series
            blueprint: Series blueprint with consistency requirements
            
        Returns:
            ConsistencyReport with detailed analysis
        """
        try:
            # Track all books
            for book in books:
                self.tracker.track_series_entry(series_uuid, book, blueprint)
            
            # Get consistency metrics
            metrics = self.tracker.get_series_consistency_metrics(series_uuid)
            
            if "error" in metrics:
                raise ValueError(metrics["error"])
            
            # Identify violations
            violations = self._identify_violations(series_uuid, books, blueprint, metrics)
            
            # Calculate overall consistency score
            overall_score = metrics["overall_consistency_score"]
            
            # Generate recommendations
            recommendations = self._generate_consistency_recommendations(violations, metrics)
            
            # Create report
            report = ConsistencyReport(
                series_uuid=series_uuid,
                series_name=blueprint.series_name,
                overall_consistency_score=overall_score,
                total_books_analyzed=len(books),
                total_violations=len(violations),
                violations_by_severity=self._count_violations_by_severity(violations),
                violations_by_element=self._count_violations_by_element(violations),
                detailed_violations=violations,
                recommendations=recommendations
            )
            
            logger.info(f"Validated series consistency: {blueprint.series_name} (score: {overall_score:.2f}, {len(violations)} violations)")
            return report
            
        except Exception as e:
            logger.error(f"Error validating series consistency: {e}")
            raise
    
    def _identify_violations(self, series_uuid: str, books: List[CodexObject],
                           blueprint: SeriesBlueprint, metrics: Dict[str, Any]) -> List[ConsistencyViolation]:
        """Identify consistency violations."""
        violations = []
        
        try:
            element_consistency = metrics.get("element_consistency", {})
            
            for element in blueprint.consistent_elements:
                element_name = element.element_name
                
                if element_name in element_consistency:
                    consistency_data = element_consistency[element_name]
                    consistency_score = consistency_data["consistency_score"]
                    required_consistency = element.consistency_level
                    
                    # Check if consistency falls below required level
                    if consistency_score < required_consistency:
                        severity = self._determine_violation_severity(consistency_score)
                        
                        # Create a general violation for this element
                        violation = ConsistencyViolation(
                            violation_type="consistency_below_threshold",
                            element_name=element_name,
                            expected_value=f"Consistency >= {required_consistency:.2f}",
                            actual_value=f"Consistency = {consistency_score:.2f}",
                            severity=severity,
                            book_uuid="",
                            book_title="Series-wide issue"
                        )
                        violations.append(violation)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error identifying violations: {e}")
            return []
    
    def _determine_violation_severity(self, consistency_score: float) -> str:
        """Determine severity of a consistency violation."""
        if consistency_score < self.violation_thresholds["high"]:
            return "high"
        elif consistency_score < self.violation_thresholds["medium"]:
            return "medium"
        elif consistency_score < self.violation_thresholds["low"]:
            return "low"
        else:
            return "low"  # Default to low severity
    
    def _count_violations_by_severity(self, violations: List[ConsistencyViolation]) -> Dict[str, int]:
        """Count violations by severity level."""
        counts = {"high": 0, "medium": 0, "low": 0}
        
        for violation in violations:
            if violation.severity in counts:
                counts[violation.severity] += 1
        
        return counts
    
    def _count_violations_by_element(self, violations: List[ConsistencyViolation]) -> Dict[str, int]:
        """Count violations by element type."""
        counts = {}
        
        for violation in violations:
            element_name = violation.element_name
            counts[element_name] = counts.get(element_name, 0) + 1
        
        return counts
    
    def _generate_consistency_recommendations(self, violations: List[ConsistencyViolation],
                                            metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving consistency."""
        recommendations = []
        
        # Overall consistency recommendations
        overall_score = metrics.get("overall_consistency_score", 0)
        
        if overall_score < 0.5:
            recommendations.append("Series has significant consistency issues - consider major revisions")
        elif overall_score < 0.7:
            recommendations.append("Series consistency needs improvement - focus on key elements")
        
        # Element-specific recommendations
        violation_counts = self._count_violations_by_element(violations)
        
        for element_name, count in violation_counts.items():
            if count >= 1:
                recommendations.append(f"Address consistency issues with {element_name}")
        
        # Severity-based recommendations
        severity_counts = self._count_violations_by_severity(violations)
        
        if severity_counts["high"] > 0:
            recommendations.append("High-severity violations require immediate attention")
        
        if severity_counts["medium"] > 2:
            recommendations.append("Multiple medium-severity violations suggest systematic issues")
        
        # Limit recommendations
        return recommendations[:5]
    
    def export_consistency_report(self, report: ConsistencyReport) -> Dict[str, Any]:
        """Export consistency report for storage or sharing."""
        try:
            return {
                "export_timestamp": datetime.now().isoformat(),
                "report": report.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error exporting consistency report: {e}")
            return {"error": str(e)}