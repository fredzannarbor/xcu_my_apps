"""
Paper Quality Assessment System

This module provides comprehensive quality assessment for academic papers,
including arxiv submission compliance checking and quality scoring.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .validator import ContentValidator, ValidationConfig
from .models import ValidationResult
from .exceptions import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality metrics for paper assessment."""
    overall_score: float
    readability_score: float
    technical_depth_score: float
    academic_tone_score: float
    structure_score: float
    citation_score: float
    arxiv_compliance_score: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "overall_score": self.overall_score,
            "readability_score": self.readability_score,
            "technical_depth_score": self.technical_depth_score,
            "academic_tone_score": self.academic_tone_score,
            "structure_score": self.structure_score,
            "citation_score": self.citation_score,
            "arxiv_compliance_score": self.arxiv_compliance_score
        }


@dataclass
class QualityIssue:
    """Represents a quality issue found in the paper."""
    severity: str  # 'error', 'warning', 'info'
    section: str
    message: str
    suggestion: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class PaperQualityReport:
    """Comprehensive quality report for a paper."""
    overall_score: float
    metrics: QualityMetrics
    section_scores: Dict[str, float]
    issues: List[QualityIssue]
    recommendations: List[str]
    arxiv_readiness: bool
    word_count: int
    sections_analyzed: int
    generated_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "overall_score": self.overall_score,
            "metrics": self.metrics.to_dict(),
            "section_scores": self.section_scores,
            "issues": [
                {
                    "severity": issue.severity,
                    "section": issue.section,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                    "line_number": issue.line_number
                }
                for issue in self.issues
            ],
            "recommendations": self.recommendations,
            "arxiv_readiness": self.arxiv_readiness,
            "word_count": self.word_count,
            "sections_analyzed": self.sections_analyzed,
            "generated_at": self.generated_at
        }
    
    def save_to_file(self, output_path: str):
        """Save report to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class ArxivComplianceChecker:
    """Checks compliance with arXiv submission requirements."""
    
    def __init__(self):
        self.required_sections = ["abstract", "introduction", "conclusion"]
        self.recommended_sections = ["methodology", "results", "discussion", "related work"]
        self.max_abstract_words = 250
        self.min_abstract_words = 100
        self.max_total_words = 50000
        self.min_total_words = 3000
    
    def check_compliance(self, sections: Dict[str, str], complete_paper: str) -> Tuple[float, List[QualityIssue]]:
        """
        Check arXiv compliance and return score and issues.
        
        Returns:
            Tuple of (compliance_score, list_of_issues)
        """
        issues = []
        score = 1.0
        
        # Check required sections
        missing_sections = [sec for sec in self.required_sections if sec not in sections]
        if missing_sections:
            issues.append(QualityIssue(
                severity="error",
                section="structure",
                message=f"Missing required sections: {', '.join(missing_sections)}",
                suggestion="Add the missing sections to meet arXiv requirements"
            ))
            score -= 0.3
        
        # Check abstract length
        if "abstract" in sections:
            abstract_words = len(sections["abstract"].split())
            if abstract_words < self.min_abstract_words:
                issues.append(QualityIssue(
                    severity="error",
                    section="abstract",
                    message=f"Abstract too short: {abstract_words} words (minimum {self.min_abstract_words})",
                    suggestion="Expand abstract to meet arXiv minimum length requirement"
                ))
                score -= 0.2
            elif abstract_words > self.max_abstract_words:
                issues.append(QualityIssue(
                    severity="warning",
                    section="abstract",
                    message=f"Abstract too long: {abstract_words} words (maximum {self.max_abstract_words})",
                    suggestion="Shorten abstract to meet arXiv maximum length requirement"
                ))
                score -= 0.1
        
        # Check total word count
        total_words = sum(len(content.split()) for content in sections.values())
        if total_words < self.min_total_words:
            issues.append(QualityIssue(
                severity="warning",
                section="structure",
                message=f"Paper quite short: {total_words} words (recommended minimum {self.min_total_words})",
                suggestion="Consider expanding content for a more comprehensive paper"
            ))
            score -= 0.1
        elif total_words > self.max_total_words:
            issues.append(QualityIssue(
                severity="error",
                section="structure",
                message=f"Paper too long: {total_words} words (maximum {self.max_total_words})",
                suggestion="Reduce content to meet arXiv length requirements"
            ))
            score -= 0.2
        
        # Check for proper academic formatting
        if not self._has_proper_formatting(complete_paper):
            issues.append(QualityIssue(
                severity="warning",
                section="formatting",
                message="Paper lacks proper academic formatting",
                suggestion="Improve formatting with proper headers, lists, and emphasis"
            ))
            score -= 0.1
        
        # Check for references
        if not self._has_references(complete_paper):
            issues.append(QualityIssue(
                severity="error",
                section="references",
                message="No references section found",
                suggestion="Add a references/bibliography section"
            ))
            score -= 0.2
        
        return max(0.0, score), issues
    
    def _has_proper_formatting(self, content: str) -> bool:
        """Check for proper academic formatting."""
        import re
        formatting_indicators = [
            r'##\s+\w+',  # Section headers
            r'\*\*[^*]+\*\*',  # Bold text
            r'`[^`]+`',  # Code formatting
            r'^\s*-\s+',  # Lists
        ]
        
        return sum(1 for pattern in formatting_indicators if re.search(pattern, content, re.MULTILINE)) >= 3
    
    def _has_references(self, content: str) -> bool:
        """Check for references section."""
        import re
        return bool(re.search(r'##\s*(References|Bibliography)', content, re.IGNORECASE))


class PaperQualityAssessor:
    """Main class for comprehensive paper quality assessment."""
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        """Initialize with optional validation configuration."""
        self.config = config or ValidationConfig()
        self.content_validator = ContentValidator(self.config)
        self.arxiv_checker = ArxivComplianceChecker()
    
    def assess_paper_quality(self, sections: Dict[str, str], complete_paper: Optional[str] = None) -> PaperQualityReport:
        """
        Perform comprehensive quality assessment of the paper.
        
        Args:
            sections: Dictionary mapping section names to content
            complete_paper: Optional complete paper content (will be generated if not provided)
            
        Returns:
            PaperQualityReport with comprehensive assessment
        """
        logger.info("Starting comprehensive paper quality assessment...")
        
        if complete_paper is None:
            complete_paper = self._combine_sections(sections)
        
        # Validate content using the validation framework
        validation_results = self.content_validator.validate_sections(sections)
        
        # Check arXiv compliance
        arxiv_score, arxiv_issues = self.arxiv_checker.check_compliance(sections, complete_paper)
        
        # Calculate metrics
        metrics = self._calculate_metrics(validation_results, arxiv_score)
        
        # Extract section scores
        section_scores = {}
        for section_name, section_results in validation_results.items():
            section_score = sum(r.metrics.get('score', 0.0) for r in section_results.values()) / len(section_results)
            section_scores[section_name] = section_score
        
        # Collect all issues
        all_issues = self._collect_issues(validation_results, arxiv_issues)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(validation_results, all_issues, metrics)
        
        # Determine arXiv readiness
        arxiv_readiness = self._determine_arxiv_readiness(metrics, all_issues)
        
        # Calculate word count
        word_count = sum(len(content.split()) for content in sections.values())
        
        report = PaperQualityReport(
            overall_score=metrics.overall_score,
            metrics=metrics,
            section_scores=section_scores,
            issues=all_issues,
            recommendations=recommendations,
            arxiv_readiness=arxiv_readiness,
            word_count=word_count,
            sections_analyzed=len(sections),
            generated_at=datetime.now().isoformat()
        )
        
        logger.info(f"Paper quality assessment complete. Overall score: {metrics.overall_score:.2f}")
        logger.info(f"ArXiv readiness: {'Yes' if arxiv_readiness else 'No'}")
        
        return report
    
    def _combine_sections(self, sections: Dict[str, str]) -> str:
        """Combine sections into complete paper."""
        paper_parts = []
        for section_name, content in sections.items():
            paper_parts.append(f"## {section_name.title()}\n\n{content}\n")
        return "\n".join(paper_parts)
    
    def _calculate_metrics(self, validation_results: Dict[str, Dict[str, ValidationResult]], 
                          arxiv_score: float) -> QualityMetrics:
        """Calculate comprehensive quality metrics."""
        
        # Extract scores from validation results
        all_scores = []
        readability_scores = []
        technical_scores = []
        academic_scores = []
        structure_scores = []
        citation_scores = []
        
        for section_results in validation_results.values():
            for validator_name, result in section_results.items():
                score = result.metrics.get('score', 0.0)
                all_scores.append(score)
                
                # Categorize scores by validator type
                if validator_name == 'structure':
                    structure_scores.append(score)
                    readability_scores.append(score)
                elif validator_name == 'academic_tone':
                    academic_scores.append(score)
                    technical_scores.append(result.metrics.get('technical_score', 0) / 10.0)  # Normalize
                elif validator_name == 'citations':
                    citation_scores.append(score)
                elif validator_name == 'word_count':
                    readability_scores.append(score)
        
        # Calculate average scores
        overall_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
        readability_score = sum(readability_scores) / len(readability_scores) if readability_scores else 0.0
        technical_depth_score = sum(technical_scores) / len(technical_scores) if technical_scores else 0.0
        academic_tone_score = sum(academic_scores) / len(academic_scores) if academic_scores else 0.0
        structure_score = sum(structure_scores) / len(structure_scores) if structure_scores else 0.0
        citation_score = sum(citation_scores) / len(citation_scores) if citation_scores else 0.0
        
        return QualityMetrics(
            overall_score=overall_score,
            readability_score=readability_score,
            technical_depth_score=technical_depth_score,
            academic_tone_score=academic_tone_score,
            structure_score=structure_score,
            citation_score=citation_score,
            arxiv_compliance_score=arxiv_score
        )
    
    def _collect_issues(self, validation_results: Dict[str, Dict[str, ValidationResult]], 
                       arxiv_issues: List[QualityIssue]) -> List[QualityIssue]:
        """Collect all issues from validation results."""
        all_issues = list(arxiv_issues)  # Start with arXiv issues
        
        for section_name, section_results in validation_results.items():
            for validator_name, result in section_results.items():
                # Add errors as error-level issues
                for error in result.errors:
                    all_issues.append(QualityIssue(
                        severity="error",
                        section=section_name,
                        message=error,
                        suggestion=f"Fix this issue in the {section_name} section"
                    ))
                
                # Add warnings as warning-level issues
                for warning in result.warnings:
                    all_issues.append(QualityIssue(
                        severity="warning",
                        section=section_name,
                        message=warning,
                        suggestion=f"Consider improving this aspect in the {section_name} section"
                    ))
        
        return all_issues
    
    def _generate_recommendations(self, validation_results: Dict[str, Dict[str, ValidationResult]], 
                                 issues: List[QualityIssue], metrics: QualityMetrics) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Critical issues first
        critical_issues = [issue for issue in issues if issue.severity == "error"]
        if critical_issues:
            recommendations.append("Critical issues to address:")
            for issue in critical_issues[:5]:  # Top 5 critical issues
                recommendations.append(f"  - {issue.section}: {issue.message}")
        
        # Metric-based recommendations
        if metrics.overall_score < 0.7:
            recommendations.append("Overall quality needs improvement")
        
        if metrics.academic_tone_score < 0.7:
            recommendations.append("Improve academic tone and formal language usage")
        
        if metrics.technical_depth_score < 0.7:
            recommendations.append("Add more technical depth and specific terminology")
        
        if metrics.citation_score < 0.7:
            recommendations.append("Add more citations to support claims and provide context")
        
        if metrics.structure_score < 0.7:
            recommendations.append("Improve document structure and formatting")
        
        if metrics.arxiv_compliance_score < 0.8:
            recommendations.append("Address arXiv submission compliance issues")
        
        # Section-specific recommendations
        low_scoring_sections = [
            section for section, score in self._get_section_scores(validation_results).items()
            if score < 0.7
        ]
        
        if low_scoring_sections:
            recommendations.append(f"Focus on improving sections: {', '.join(low_scoring_sections)}")
        
        return recommendations
    
    def _get_section_scores(self, validation_results: Dict[str, Dict[str, ValidationResult]]) -> Dict[str, float]:
        """Get average scores for each section."""
        section_scores = {}
        for section_name, section_results in validation_results.items():
            scores = [r.metrics.get('score', 0.0) for r in section_results.values()]
            section_scores[section_name] = sum(scores) / len(scores) if scores else 0.0
        return section_scores
    
    def _determine_arxiv_readiness(self, metrics: QualityMetrics, issues: List[QualityIssue]) -> bool:
        """Determine if paper is ready for arXiv submission."""
        # Check for critical errors
        critical_errors = [issue for issue in issues if issue.severity == "error"]
        if critical_errors:
            return False
        
        # Check minimum quality thresholds
        min_thresholds = {
            "overall_score": 0.7,
            "arxiv_compliance_score": 0.8,
            "academic_tone_score": 0.6,
            "structure_score": 0.7
        }
        
        for metric_name, threshold in min_thresholds.items():
            if getattr(metrics, metric_name) < threshold:
                return False
        
        return True
    
    def assess_paper_file(self, paper_file: str, output_file: Optional[str] = None) -> PaperQualityReport:
        """
        Assess quality of a paper file.
        
        Args:
            paper_file: Path to the paper file (markdown format)
            output_file: Optional path to save the quality report
            
        Returns:
            PaperQualityReport with comprehensive assessment
        """
        paper_path = Path(paper_file)
        
        if not paper_path.exists():
            raise ValidationError(f"Paper file not found: {paper_file}")
        
        # Read paper content
        with open(paper_path, 'r', encoding='utf-8') as f:
            complete_paper = f.read()
        
        # Extract sections
        sections = self._extract_sections(complete_paper)
        
        # Perform quality assessment
        report = self.assess_paper_quality(sections, complete_paper)
        
        # Save report if output file specified
        if output_file:
            report.save_to_file(output_file)
            logger.info(f"Quality report saved to: {output_file}")
        
        return report
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from markdown content."""
        import re
        
        sections = {}
        section_pattern = r'##\s+([^#\n]+)\n+(.*?)(?=\n\s*##|\Z)'
        
        for match in re.finditer(section_pattern, content, re.DOTALL):
            section_name = match.group(1).strip().lower()
            section_content = match.group(2).strip()
            sections[section_name] = section_content
        
        return sections


def assess_paper_quality(sections: Dict[str, str], config: Optional[ValidationConfig] = None) -> PaperQualityReport:
    """
    Convenience function to assess paper quality.
    
    Args:
        sections: Dictionary mapping section names to content
        config: Optional validation configuration
        
    Returns:
        PaperQualityReport with comprehensive assessment
    """
    assessor = PaperQualityAssessor(config)
    return assessor.assess_paper_quality(sections)


def assess_paper_file(paper_file: str, output_file: Optional[str] = None, 
                     config: Optional[ValidationConfig] = None) -> PaperQualityReport:
    """
    Convenience function to assess quality of a paper file.
    
    Args:
        paper_file: Path to the paper file (markdown format)
        output_file: Optional path to save the quality report
        config: Optional validation configuration
        
    Returns:
        PaperQualityReport with comprehensive assessment
    """
    assessor = PaperQualityAssessor(config)
    return assessor.assess_paper_file(paper_file, output_file)