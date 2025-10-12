"""
Paper Validation and Quality Assurance Module

This module provides comprehensive validation and quality assurance for
generated academic papers, ensuring they meet arXiv submission standards
and academic writing requirements.
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    score: float  # 0.0 to 1.0
    issues: List[str]
    suggestions: List[str]
    metadata: Dict[str, Any]


@dataclass
class PaperQualityReport:
    """Comprehensive quality report for a paper."""
    overall_score: float
    section_scores: Dict[str, float]
    validation_results: Dict[str, ValidationResult]
    recommendations: List[str]
    arxiv_readiness: bool
    generated_at: str


class ContentValidator:
    """Validates content quality and academic standards."""
    
    def __init__(self):
        self.academic_terms = [
            "methodology", "implementation", "results", "discussion", "conclusion",
            "analysis", "evaluation", "framework", "approach", "system",
            "performance", "efficiency", "accuracy", "validation", "assessment"
        ]
        
        self.technical_terms = [
            "algorithm", "configuration", "architecture", "integration", "automation",
            "processing", "generation", "optimization", "scalability", "reliability"
        ]
    
    def validate_abstract(self, content: str) -> ValidationResult:
        """Validate abstract section."""
        issues = []
        suggestions = []
        score = 1.0
        
        # Check length (150-250 words for arXiv)
        word_count = len(content.split())
        if word_count < 150:
            issues.append(f"Abstract too short: {word_count} words (minimum 150)")
            score -= 0.3
        elif word_count > 250:
            issues.append(f"Abstract too long: {word_count} words (maximum 250)")
            score -= 0.2
        
        # Check for required opening
        required_opening = "The AI Lab for Book-Lovers demonstrates the use of AI"
        if not content.strip().startswith(required_opening):
            issues.append("Abstract does not start with required opening text")
            score -= 0.4
        
        # Check for key elements
        key_elements = ["AI", "imprint", "publishing", "technical", "results"]
        missing_elements = []
        content_lower = content.lower()
        
        for element in key_elements:
            if element.lower() not in content_lower:
                missing_elements.append(element)
        
        if missing_elements:
            issues.append(f"Missing key elements: {', '.join(missing_elements)}")
            score -= 0.1 * len(missing_elements)
        
        # Check academic tone
        if not self._has_academic_tone(content):
            suggestions.append("Consider using more formal academic language")
            score -= 0.1
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions,
            metadata={"word_count": word_count, "section": "abstract"}
        )
    
    def validate_introduction(self, content: str) -> ValidationResult:
        """Validate introduction section."""
        issues = []
        suggestions = []
        score = 1.0
        
        word_count = len(content.split())
        
        # Check length (800-1200 words)
        if word_count < 800:
            issues.append(f"Introduction too short: {word_count} words (minimum 800)")
            score -= 0.2
        elif word_count > 1200:
            suggestions.append(f"Introduction quite long: {word_count} words (target 800-1200)")
            score -= 0.1
        
        # Check for key introduction elements
        required_elements = {
            "context": ["publishing", "AI", "automation"],
            "problem": ["challenge", "problem", "limitation", "scalability"],
            "contribution": ["contribution", "novel", "first", "innovation"],
            "organization": ["paper", "section", "structure", "organization"]
        }
        
        content_lower = content.lower()
        missing_categories = []
        
        for category, terms in required_elements.items():
            if not any(term in content_lower for term in terms):
                missing_categories.append(category)
        
        if missing_categories:
            issues.append(f"Missing introduction elements: {', '.join(missing_categories)}")
            score -= 0.15 * len(missing_categories)
        
        # Check for citations (should have some references to related work)
        if not self._has_citations(content):
            suggestions.append("Consider adding citations to related work in introduction")
            score -= 0.1
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions,
            metadata={"word_count": word_count, "section": "introduction"}
        )
    
    def validate_methodology(self, content: str) -> ValidationResult:
        """Validate methodology section."""
        issues = []
        suggestions = []
        score = 1.0
        
        word_count = len(content.split())
        
        # Check length (2000-3000 words)
        if word_count < 2000:
            issues.append(f"Methodology too short: {word_count} words (minimum 2000)")
            score -= 0.3
        elif word_count > 3000:
            suggestions.append(f"Methodology quite long: {word_count} words (target 2000-3000)")
        
        # Check for technical depth
        technical_indicators = [
            "architecture", "system", "configuration", "implementation",
            "algorithm", "framework", "process", "workflow", "integration"
        ]
        
        content_lower = content.lower()
        technical_score = sum(1 for term in technical_indicators if term in content_lower)
        
        if technical_score < 5:
            issues.append("Insufficient technical depth in methodology")
            score -= 0.2
        
        # Check for code examples or technical details
        has_code = bool(re.search(r'```|`[^`]+`|\{[^}]+\}', content))
        if not has_code:
            suggestions.append("Consider adding code examples or configuration snippets")
            score -= 0.1
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions,
            metadata={"word_count": word_count, "technical_score": technical_score, "section": "methodology"}
        )
    
    def validate_results(self, content: str) -> ValidationResult:
        """Validate results section."""
        issues = []
        suggestions = []
        score = 1.0
        
        word_count = len(content.split())
        
        # Check length (1500-2000 words)
        if word_count < 1500:
            issues.append(f"Results too short: {word_count} words (minimum 1500)")
            score -= 0.2
        elif word_count > 2000:
            suggestions.append(f"Results quite long: {word_count} words (target 1500-2000)")
        
        # Check for quantitative data
        quantitative_indicators = [
            r'\d+%', r'\d+\.\d+', r'\d+ books?', r'\d+ minutes?',
            'table', 'figure', 'metric', 'measurement', 'statistic'
        ]
        
        quantitative_matches = sum(1 for pattern in quantitative_indicators 
                                 if re.search(pattern, content, re.IGNORECASE))
        
        if quantitative_matches < 3:
            issues.append("Insufficient quantitative data in results")
            score -= 0.3
        
        # Check for comparative analysis
        comparative_terms = ["compared", "versus", "traditional", "baseline", "improvement"]
        if not any(term in content.lower() for term in comparative_terms):
            suggestions.append("Consider adding comparative analysis with traditional methods")
            score -= 0.1
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions,
            metadata={"word_count": word_count, "quantitative_score": quantitative_matches, "section": "results"}
        )
    
    def _has_academic_tone(self, content: str) -> bool:
        """Check if content has appropriate academic tone."""
        academic_indicators = [
            "this paper", "this study", "our approach", "we demonstrate",
            "the results show", "analysis reveals", "findings indicate"
        ]
        
        content_lower = content.lower()
        return sum(1 for phrase in academic_indicators if phrase in content_lower) >= 2
    
    def _has_citations(self, content: str) -> bool:
        """Check if content has citation-like patterns."""
        citation_patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\([^)]*\d{4}[^)]*\)',  # (Author, 2024)
            r'et al\.',  # et al.
            r'[A-Z][a-z]+ et al\.'  # Author et al.
        ]
        
        return any(re.search(pattern, content) for pattern in citation_patterns)


class StructureValidator:
    """Validates paper structure and organization."""
    
    def validate_paper_structure(self, sections: Dict[str, str]) -> ValidationResult:
        """Validate overall paper structure."""
        issues = []
        suggestions = []
        score = 1.0
        
        # Required sections for arXiv paper
        required_sections = ["abstract", "introduction", "methodology", "results", "discussion", "conclusion"]
        missing_sections = [section for section in required_sections if section not in sections]
        
        if missing_sections:
            issues.append(f"Missing required sections: {', '.join(missing_sections)}")
            score -= 0.2 * len(missing_sections)
        
        # Check section order
        section_names = list(sections.keys())
        expected_order = ["abstract", "introduction", "methodology", "implementation", "results", "discussion", "conclusion"]
        
        # Filter to only sections that exist
        actual_order = [section for section in expected_order if section in section_names]
        
        if section_names != actual_order:
            suggestions.append("Consider reordering sections to follow standard academic structure")
            score -= 0.1
        
        # Check total word count
        total_words = sum(len(content.split()) for content in sections.values())
        
        if total_words < 8000:
            issues.append(f"Paper too short: {total_words} words (minimum ~8000 for comprehensive paper)")
            score -= 0.2
        elif total_words > 15000:
            suggestions.append(f"Paper quite long: {total_words} words (consider condensing)")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions,
            metadata={
                "total_word_count": total_words,
                "section_count": len(sections),
                "missing_sections": missing_sections
            }
        )


class ArxivComplianceValidator:
    """Validates compliance with arXiv submission requirements."""
    
    def validate_arxiv_compliance(self, paper_content: str, metadata: Dict[str, Any]) -> ValidationResult:
        """Validate arXiv submission compliance."""
        issues = []
        suggestions = []
        score = 1.0
        
        # Check title requirements
        if not self._has_descriptive_title(paper_content):
            issues.append("Title should be more descriptive and specific")
            score -= 0.1
        
        # Check abstract requirements
        abstract_match = re.search(r'## Abstract\s*\n\n(.*?)(?=\n##|\Z)', paper_content, re.DOTALL | re.IGNORECASE)
        if abstract_match:
            abstract_content = abstract_match.group(1).strip()
            abstract_words = len(abstract_content.split())
            
            if abstract_words < 100:
                issues.append(f"Abstract too short for arXiv: {abstract_words} words")
                score -= 0.2
            elif abstract_words > 300:
                issues.append(f"Abstract too long for arXiv: {abstract_words} words")
                score -= 0.1
        else:
            issues.append("No abstract section found")
            score -= 0.3
        
        # Check for appropriate subject classification
        if not self._has_appropriate_subject_classification(paper_content):
            suggestions.append("Ensure paper is suitable for cs.AI or related arXiv category")
        
        # Check for proper academic formatting
        if not self._has_proper_formatting(paper_content):
            suggestions.append("Consider improving formatting for academic presentation")
            score -= 0.05
        
        # Check for references/bibliography
        if not self._has_references(paper_content):
            issues.append("Paper should include references/bibliography section")
            score -= 0.2
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions,
            metadata={"arxiv_category": "cs.AI", "compliance_check": True}
        )
    
    def _has_descriptive_title(self, content: str) -> bool:
        """Check if title is descriptive enough."""
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if not title_match:
            return False
        
        title = title_match.group(1)
        return len(title.split()) >= 5 and any(word in title.lower() for word in ["ai", "assisted", "case", "study"])
    
    def _has_appropriate_subject_classification(self, content: str) -> bool:
        """Check if content is appropriate for cs.AI category."""
        ai_terms = ["artificial intelligence", "machine learning", "ai", "llm", "automation", "intelligent"]
        content_lower = content.lower()
        return sum(1 for term in ai_terms if term in content_lower) >= 3
    
    def _has_proper_formatting(self, content: str) -> bool:
        """Check for proper academic formatting."""
        formatting_indicators = [
            r'##\s+\w+',  # Section headers
            r'\*\*[^*]+\*\*',  # Bold text
            r'`[^`]+`',  # Code formatting
            r'^\s*-\s+',  # Lists
        ]
        
        return sum(1 for pattern in formatting_indicators if re.search(pattern, content, re.MULTILINE)) >= 3
    
    def _has_references(self, content: str) -> bool:
        """Check for references section."""
        return bool(re.search(r'##\s*(References|Bibliography)', content, re.IGNORECASE))


class PaperQualityAssessor:
    """Main class for comprehensive paper quality assessment."""
    
    def __init__(self):
        self.content_validator = ContentValidator()
        self.structure_validator = StructureValidator()
        self.arxiv_validator = ArxivComplianceValidator()
    
    def assess_paper_quality(self, sections: Dict[str, str], complete_paper: str) -> PaperQualityReport:
        """Perform comprehensive quality assessment of the paper."""
        logger.info("Starting comprehensive paper quality assessment...")
        
        validation_results = {}
        section_scores = {}
        
        # Validate individual sections
        section_validators = {
            "abstract": self.content_validator.validate_abstract,
            "introduction": self.content_validator.validate_introduction,
            "methodology": self.content_validator.validate_methodology,
            "results": self.content_validator.validate_results,
        }
        
        for section_name, content in sections.items():
            if section_name in section_validators:
                validator = section_validators[section_name]
                result = validator(content)
                validation_results[section_name] = result
                section_scores[section_name] = result.score
                
                logger.info(f"Section '{section_name}' score: {result.score:.2f}")
                if result.issues:
                    logger.warning(f"Issues in '{section_name}': {'; '.join(result.issues)}")
        
        # Validate overall structure
        structure_result = self.structure_validator.validate_paper_structure(sections)
        validation_results["structure"] = structure_result
        section_scores["structure"] = structure_result.score
        
        # Validate arXiv compliance
        arxiv_result = self.arxiv_validator.validate_arxiv_compliance(complete_paper, {})
        validation_results["arxiv_compliance"] = arxiv_result
        section_scores["arxiv_compliance"] = arxiv_result.score
        
        # Calculate overall score
        overall_score = sum(section_scores.values()) / len(section_scores)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(validation_results)
        
        # Determine arXiv readiness
        arxiv_readiness = (
            overall_score >= 0.7 and
            all(result.score >= 0.6 for result in validation_results.values()) and
            len([issue for result in validation_results.values() for issue in result.issues]) <= 3
        )
        
        report = PaperQualityReport(
            overall_score=overall_score,
            section_scores=section_scores,
            validation_results=validation_results,
            recommendations=recommendations,
            arxiv_readiness=arxiv_readiness,
            generated_at=str(datetime.now())
        )
        
        logger.info(f"Paper quality assessment complete. Overall score: {overall_score:.2f}")
        logger.info(f"ArXiv readiness: {'Yes' if arxiv_readiness else 'No'}")
        
        return report
    
    def _generate_recommendations(self, validation_results: Dict[str, ValidationResult]) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        # Collect all issues and suggestions
        all_issues = []
        all_suggestions = []
        
        for result in validation_results.values():
            all_issues.extend(result.issues)
            all_suggestions.extend(result.suggestions)
        
        # Prioritize critical issues
        if all_issues:
            recommendations.append("Address critical issues:")
            recommendations.extend([f"  - {issue}" for issue in all_issues[:5]])  # Top 5 issues
        
        # Add suggestions for improvement
        if all_suggestions:
            recommendations.append("Consider improvements:")
            recommendations.extend([f"  - {suggestion}" for suggestion in all_suggestions[:3]])  # Top 3 suggestions
        
        # Add general recommendations based on scores
        low_scoring_sections = [
            section for section, result in validation_results.items() 
            if result.score < 0.7
        ]
        
        if low_scoring_sections:
            recommendations.append(f"Focus on improving sections: {', '.join(low_scoring_sections)}")
        
        return recommendations


def validate_paper_file(paper_file: str, output_file: Optional[str] = None) -> PaperQualityReport:
    """
    Validate a paper file and generate quality report.
    
    Args:
        paper_file: Path to the paper file (markdown format)
        output_file: Optional path to save the quality report
        
    Returns:
        PaperQualityReport with comprehensive assessment
    """
    paper_path = Path(paper_file)
    
    if not paper_path.exists():
        raise FileNotFoundError(f"Paper file not found: {paper_file}")
    
    # Read paper content
    with open(paper_path, 'r') as f:
        complete_paper = f.read()
    
    # Extract sections
    sections = {}
    section_pattern = r'## ([^#\n]+)\n\n(.*?)(?=\n##|\Z)'
    
    for match in re.finditer(section_pattern, complete_paper, re.DOTALL):
        section_name = match.group(1).strip().lower()
        section_content = match.group(2).strip()
        sections[section_name] = section_content
    
    # Perform quality assessment
    assessor = PaperQualityAssessor()
    report = assessor.assess_paper_quality(sections, complete_paper)
    
    # Save report if output file specified
    if output_file:
        report_data = {
            "overall_score": report.overall_score,
            "section_scores": report.section_scores,
            "recommendations": report.recommendations,
            "arxiv_readiness": report.arxiv_readiness,
            "generated_at": report.generated_at,
            "validation_details": {
                section: {
                    "score": result.score,
                    "issues": result.issues,
                    "suggestions": result.suggestions,
                    "metadata": result.metadata
                }
                for section, result in report.validation_results.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Quality report saved to: {output_file}")
    
    return report


if __name__ == "__main__":
    # Example usage
    import sys
    from datetime import datetime
    
    if len(sys.argv) > 1:
        paper_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        try:
            report = validate_paper_file(paper_file, output_file)
            print(f"Paper Quality Assessment:")
            print(f"Overall Score: {report.overall_score:.2f}")
            print(f"ArXiv Ready: {'Yes' if report.arxiv_readiness else 'No'}")
            print(f"Recommendations: {len(report.recommendations)}")
            
            for rec in report.recommendations[:3]:
                print(f"  - {rec}")
                
        except Exception as e:
            print(f"Error validating paper: {e}")
    else:
        print("Usage: python paper_validator.py <paper_file> [output_file]")