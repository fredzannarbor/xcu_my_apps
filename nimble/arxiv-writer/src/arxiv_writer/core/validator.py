"""
Content Validation Framework

This module provides a comprehensive, configurable validation framework for
academic paper content, ensuring compliance with academic writing standards
and arxiv submission requirements.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

from .exceptions import ValidationError
from .models import ValidationResult

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationRule:
    """Represents a single validation rule."""
    name: str
    description: str
    severity: ValidationSeverity
    validator_func: Callable[[str], bool]
    error_message: str
    suggestion: Optional[str] = None
    enabled: bool = True


@dataclass
class ValidationConfig:
    """Configuration for content validation."""
    # Word count limits
    min_word_count: int = 100
    max_word_count: int = 50000
    
    # Section-specific word count limits
    section_word_limits: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "abstract": {"min": 150, "max": 250},
        "introduction": {"min": 800, "max": 1200},
        "methodology": {"min": 2000, "max": 3000},
        "results": {"min": 1500, "max": 2000},
        "discussion": {"min": 1000, "max": 1500},
        "conclusion": {"min": 500, "max": 800}
    })
    
    # Required sections
    required_sections: List[str] = field(default_factory=lambda: [
        "abstract", "introduction", "methodology", "results", "discussion", "conclusion"
    ])
    
    # Academic writing standards
    require_academic_tone: bool = True
    require_citations: bool = True
    min_citations_per_section: Dict[str, int] = field(default_factory=lambda: {
        "introduction": 3,
        "methodology": 2,
        "results": 1,
        "discussion": 5
    })
    
    # Content quality checks
    check_technical_depth: bool = True
    check_quantitative_data: bool = True
    check_proper_formatting: bool = True
    
    # Custom validation rules
    custom_rules: List[ValidationRule] = field(default_factory=list)
    
    # Validation strictness
    strict_mode: bool = False
    fail_on_warnings: bool = False


class BaseValidator(ABC):
    """Base class for all validators."""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.issues: List[Dict[str, Any]] = []
    
    @abstractmethod
    def validate(self, content: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate content and return results."""
        pass
    
    def _add_issue(self, severity: ValidationSeverity, message: str, 
                   suggestion: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Add a validation issue."""
        self.issues.append({
            "severity": severity.value,
            "message": message,
            "suggestion": suggestion,
            "metadata": metadata or {}
        })
    
    def _clear_issues(self):
        """Clear all issues."""
        self.issues = []


class WordCountValidator(BaseValidator):
    """Validates word count requirements."""
    
    def validate(self, content: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate word count requirements."""
        self._clear_issues()
        
        word_count = len(content.split())
        section_name = context.get("section_name", "unknown") if context else "unknown"
        
        # Get section-specific limits or use global limits
        if section_name in self.config.section_word_limits:
            limits = self.config.section_word_limits[section_name]
            min_words = limits["min"]
            max_words = limits["max"]
        else:
            min_words = self.config.min_word_count
            max_words = self.config.max_word_count
        
        # Check minimum word count
        if word_count < min_words:
            self._add_issue(
                ValidationSeverity.ERROR,
                f"Content too short: {word_count} words (minimum {min_words})",
                f"Expand content to meet minimum word count requirement",
                {"word_count": word_count, "min_required": min_words}
            )
        
        # Check maximum word count
        if word_count > max_words:
            severity = ValidationSeverity.ERROR if self.config.strict_mode else ValidationSeverity.WARNING
            self._add_issue(
                severity,
                f"Content too long: {word_count} words (maximum {max_words})",
                f"Consider condensing content to meet word count limits",
                {"word_count": word_count, "max_allowed": max_words}
            )
        
        # Calculate score based on word count compliance
        if min_words <= word_count <= max_words:
            score = 1.0
        elif word_count < min_words:
            score = max(0.0, word_count / min_words)
        else:  # word_count > max_words
            score = max(0.0, 1.0 - (word_count - max_words) / max_words)
        
        # Build metrics with additional context from issues
        metrics = {"word_count": word_count, "section": section_name, "score": score}
        
        # Add additional metadata from issues
        for issue in self.issues:
            if issue.get("metadata"):
                metrics.update(issue["metadata"])
        
        return ValidationResult(
            is_valid=len([i for i in self.issues if i["severity"] == "error"]) == 0,
            errors=[i["message"] for i in self.issues if i["severity"] == "error"],
            warnings=[i["message"] for i in self.issues if i["severity"] == "warning"],
            metrics=metrics
        )


class AcademicToneValidator(BaseValidator):
    """Validates academic tone and writing style."""
    
    def __init__(self, config: ValidationConfig):
        super().__init__(config)
        
        # Academic tone indicators
        self.academic_phrases = [
            "this paper", "this study", "our approach", "we demonstrate",
            "the results show", "analysis reveals", "findings indicate",
            "we propose", "this research", "our methodology", "we evaluate",
            "the data suggests", "we conclude", "our findings"
        ]
        
        # Informal language patterns to avoid
        self.informal_patterns = [
            r"\bi think\b", r"\bi believe\b", r"\bobviously\b", r"\bclearly\b",
            r"\bof course\b", r"\bbasically\b", r"\bactually\b", r"\breally\b",
            r"!", r"\?{2,}", r"\.{3,}"
        ]
        
        # Technical terms that indicate academic depth
        self.technical_terms = [
            "methodology", "implementation", "analysis", "evaluation", "framework",
            "approach", "system", "algorithm", "configuration", "architecture",
            "performance", "efficiency", "accuracy", "validation", "assessment"
        ]
    
    def validate(self, content: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate academic tone and writing style."""
        self._clear_issues()
        
        content_lower = content.lower()
        score = 1.0
        
        # Check for academic phrases
        academic_score = sum(1 for phrase in self.academic_phrases if phrase in content_lower)
        if academic_score < 2:
            self._add_issue(
                ValidationSeverity.WARNING,
                "Content lacks academic tone indicators",
                "Consider using more formal academic language and phrases",
                {"academic_phrases_found": academic_score}
            )
            score -= 0.2
        
        # Check for informal language
        informal_matches = []
        for pattern in self.informal_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            informal_matches.extend(matches)
        
        if informal_matches:
            self._add_issue(
                ValidationSeverity.WARNING,
                f"Informal language detected: {', '.join(informal_matches[:3])}",
                "Replace informal language with more academic alternatives",
                {"informal_matches": len(informal_matches)}
            )
            score -= 0.1 * min(len(informal_matches), 5)
        
        # Check for technical depth
        if self.config.check_technical_depth:
            technical_score = sum(1 for term in self.technical_terms if term in content_lower)
            if technical_score < 3:
                self._add_issue(
                    ValidationSeverity.INFO,
                    "Content could benefit from more technical terminology",
                    "Consider adding more technical depth and specific terminology",
                    {"technical_terms_found": technical_score}
                )
                score -= 0.05
        
        return ValidationResult(
            is_valid=len([i for i in self.issues if i["severity"] == "error"]) == 0,
            errors=[i["message"] for i in self.issues if i["severity"] == "error"],
            warnings=[i["message"] for i in self.issues if i["severity"] == "warning"],
            metrics={"academic_score": academic_score, "technical_score": technical_score, "score": max(0.0, score)}
        )


class CitationValidator(BaseValidator):
    """Validates citation requirements and patterns."""
    
    def __init__(self, config: ValidationConfig):
        super().__init__(config)
        
        # Citation patterns
        self.citation_patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\([^)]*\d{4}[^)]*\)',  # (Author, 2024)
            r'et al\.',  # et al.
            r'[A-Z][a-z]+ et al\.',  # Author et al.
            r'\([A-Z][a-z]+,?\s+\d{4}\)',  # (Smith, 2024)
            r'[A-Z][a-z]+\s+\(\d{4}\)'  # Smith (2024)
        ]
    
    def validate(self, content: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate citation requirements."""
        self._clear_issues()
        
        if not self.config.require_citations:
            return ValidationResult(is_valid=True, errors=[], warnings=[], metrics={"score": 1.0})
        
        section_name = context.get("section_name", "unknown") if context else "unknown"
        
        # Count citations
        citation_count = 0
        for pattern in self.citation_patterns:
            citation_count += len(re.findall(pattern, content))
        
        # Get required citations for this section
        required_citations = self.config.min_citations_per_section.get(section_name, 0)
        
        score = 1.0
        
        if required_citations > 0 and citation_count < required_citations:
            severity = ValidationSeverity.ERROR if self.config.strict_mode else ValidationSeverity.WARNING
            self._add_issue(
                severity,
                f"Insufficient citations: {citation_count} found, {required_citations} required",
                f"Add more citations to support claims and provide context",
                {"citations_found": citation_count, "citations_required": required_citations}
            )
            score = max(0.0, citation_count / required_citations)
        
        # Check for citation diversity (different years, authors)
        if citation_count > 0:
            year_matches = re.findall(r'\d{4}', content)
            unique_years = len(set(year_matches))
            
            if unique_years < max(1, citation_count // 3):
                self._add_issue(
                    ValidationSeverity.INFO,
                    "Citations could be more diverse in terms of publication years",
                    "Consider including citations from different time periods",
                    {"unique_years": unique_years}
                )
        
        return ValidationResult(
            is_valid=len([i for i in self.issues if i["severity"] == "error"]) == 0,
            errors=[i["message"] for i in self.issues if i["severity"] == "error"],
            warnings=[i["message"] for i in self.issues if i["severity"] == "warning"],
            metrics={"citation_count": citation_count, "section": section_name, "score": score}
        )


class StructureValidator(BaseValidator):
    """Validates content structure and formatting."""
    
    def validate(self, content: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate content structure and formatting."""
        self._clear_issues()
        
        score = 1.0
        
        if not self.config.check_proper_formatting:
            return ValidationResult(is_valid=True, errors=[], warnings=[], metrics={"score": 1.0})
        
        # Check for proper paragraph structure
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if len(paragraphs) < 2:
            self._add_issue(
                ValidationSeverity.WARNING,
                "Content appears to lack proper paragraph structure",
                "Break content into multiple paragraphs for better readability",
                {"paragraph_count": len(paragraphs)}
            )
            score -= 0.1
        
        # Check for very long paragraphs
        long_paragraphs = [p for p in paragraphs if len(p.split()) > 200]
        if long_paragraphs:
            self._add_issue(
                ValidationSeverity.WARNING,
                f"{len(long_paragraphs)} paragraphs are very long (>200 words)",
                "Consider breaking long paragraphs into smaller ones",
                {"long_paragraphs": len(long_paragraphs)}
            )
            score -= 0.05
        
        # Check for proper sentence structure
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Check for very short sentences (might indicate incomplete thoughts)
        short_sentences = [s for s in sentences if len(s.split()) < 5]
        if len(short_sentences) > len(sentences) * 0.3:
            self._add_issue(
                ValidationSeverity.INFO,
                "Many sentences are very short, which may affect readability",
                "Consider combining related short sentences",
                {"short_sentences": len(short_sentences)}
            )
        
        # Check for very long sentences
        long_sentences = [s for s in sentences if len(s.split()) > 40]
        if long_sentences:
            self._add_issue(
                ValidationSeverity.INFO,
                f"{len(long_sentences)} sentences are very long (>40 words)",
                "Consider breaking long sentences for better readability",
                {"long_sentences": len(long_sentences)}
            )
        
        # Build metrics with additional context from issues
        metrics = {
            "paragraph_count": len(paragraphs),
            "sentence_count": len(sentences),
            "avg_sentence_length": sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0,
            "score": max(0.0, score),
            "long_paragraphs": len(long_paragraphs)
        }
        
        # Add additional metadata from issues
        for issue in self.issues:
            if issue.get("metadata"):
                metrics.update(issue["metadata"])
        
        return ValidationResult(
            is_valid=len([i for i in self.issues if i["severity"] == "error"]) == 0,
            errors=[i["message"] for i in self.issues if i["severity"] == "error"],
            warnings=[i["message"] for i in self.issues if i["severity"] == "warning"],
            metrics=metrics
        )


class ContentValidator:
    """Main content validation framework with configurable rules."""
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        """Initialize validator with configuration."""
        self.config = config or ValidationConfig()
        
        # Initialize built-in validators
        self.validators = {
            "word_count": WordCountValidator(self.config),
            "academic_tone": AcademicToneValidator(self.config),
            "citations": CitationValidator(self.config),
            "structure": StructureValidator(self.config)
        }
        
        # Custom rule validators
        self._setup_custom_rules()
    
    def _setup_custom_rules(self):
        """Setup custom validation rules."""
        for rule in self.config.custom_rules:
            if rule.enabled:
                self.validators[f"custom_{rule.name}"] = self._create_custom_validator(rule)
    
    def _create_custom_validator(self, rule: ValidationRule) -> BaseValidator:
        """Create a validator from a custom rule."""
        class CustomValidator(BaseValidator):
            def __init__(self, config, rule):
                super().__init__(config)
                self.rule = rule
            
            def validate(self, content: str, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
                self._clear_issues()
                
                try:
                    is_valid = self.rule.validator_func(content)
                    if not is_valid:
                        self._add_issue(
                            self.rule.severity,
                            self.rule.error_message,
                            self.rule.suggestion
                        )
                    
                    return ValidationResult(
                        is_valid=is_valid,
                        errors=[i["message"] for i in self.issues if i["severity"] == "error"],
                        warnings=[i["message"] for i in self.issues if i["severity"] == "warning"],
                        metrics={"custom_rule": self.rule.name, "score": 1.0 if is_valid else 0.5}
                    )
                except Exception as e:
                    logger.error(f"Error in custom rule '{self.rule.name}': {e}")
                    return ValidationResult(
                        is_valid=False,
                        errors=[f"Custom rule '{self.rule.name}' failed: {str(e)}"],
                        warnings=[],
                        metrics={"error": str(e), "score": 0.0}
                    )
        
        return CustomValidator(self.config, rule)
    
    def validate_content(self, content: str, section_name: Optional[str] = None,
                        validators_to_run: Optional[List[str]] = None) -> Dict[str, ValidationResult]:
        """
        Validate content using specified validators.
        
        Args:
            content: Content to validate
            section_name: Name of the section being validated
            validators_to_run: List of validator names to run (None = all)
            
        Returns:
            Dictionary mapping validator names to validation results
        """
        if not content.strip():
            raise ValidationError("Cannot validate empty content")
        
        context = {"section_name": section_name} if section_name else {}
        
        # Determine which validators to run
        if validators_to_run is None:
            validators_to_run = list(self.validators.keys())
        
        results = {}
        
        for validator_name in validators_to_run:
            if validator_name not in self.validators:
                logger.warning(f"Unknown validator: {validator_name}")
                continue
            
            try:
                validator = self.validators[validator_name]
                result = validator.validate(content, context)
                results[validator_name] = result
                
                logger.debug(f"Validator '{validator_name}' completed with score: {result.metrics.get('score', 0.0):.2f}")
                
            except Exception as e:
                logger.error(f"Error running validator '{validator_name}': {e}")
                results[validator_name] = ValidationResult(
                    is_valid=False,
                    errors=[f"Validator error: {str(e)}"],
                    warnings=[],
                    metrics={"error": str(e), "score": 0.0}
                )
        
        return results
    
    def validate_sections(self, sections: Dict[str, str]) -> Dict[str, Dict[str, ValidationResult]]:
        """
        Validate multiple sections.
        
        Args:
            sections: Dictionary mapping section names to content
            
        Returns:
            Nested dictionary: {section_name: {validator_name: ValidationResult}}
        """
        all_results = {}
        
        for section_name, content in sections.items():
            logger.info(f"Validating section: {section_name}")
            section_results = self.validate_content(content, section_name)
            all_results[section_name] = section_results
        
        return all_results
    
    def get_overall_score(self, validation_results: Dict[str, Dict[str, ValidationResult]]) -> float:
        """Calculate overall validation score across all sections and validators."""
        all_scores = []
        
        for section_results in validation_results.values():
            for result in section_results.values():
                all_scores.append(result.metrics.get('score', 0.0))
        
        return sum(all_scores) / len(all_scores) if all_scores else 0.0
    
    def is_content_valid(self, validation_results: Dict[str, Dict[str, ValidationResult]]) -> bool:
        """Check if all content passes validation."""
        for section_results in validation_results.values():
            for result in section_results.values():
                if not result.is_valid:
                    if self.config.fail_on_warnings:
                        return False
                    # Only fail on errors, not warnings
                    if result.errors:  # Has error-level issues
                        return False
        
        return True
    
    def add_custom_rule(self, rule: ValidationRule):
        """Add a custom validation rule."""
        self.config.custom_rules.append(rule)
        if rule.enabled:
            self.validators[f"custom_{rule.name}"] = self._create_custom_validator(rule)
    
    def remove_validator(self, validator_name: str):
        """Remove a validator."""
        if validator_name in self.validators:
            del self.validators[validator_name]
    
    def get_validation_summary(self, validation_results: Dict[str, Dict[str, ValidationResult]]) -> Dict[str, Any]:
        """Generate a summary of validation results."""
        total_issues = 0
        total_suggestions = 0
        section_scores = {}
        
        for section_name, section_results in validation_results.items():
            section_score = sum(r.metrics.get('score', 0.0) for r in section_results.values()) / len(section_results)
            section_scores[section_name] = section_score
            
            for result in section_results.values():
                total_issues += len(result.errors) + len(result.warnings)
                # Note: suggestions are not directly available in ValidationResult, using warnings as proxy
                total_suggestions += len(result.warnings)
        
        overall_score = self.get_overall_score(validation_results)
        is_valid = self.is_content_valid(validation_results)
        
        return {
            "overall_score": overall_score,
            "is_valid": is_valid,
            "section_scores": section_scores,
            "total_issues": total_issues,
            "total_suggestions": total_suggestions,
            "sections_validated": len(validation_results),
            "validators_used": len(self.validators)
        }