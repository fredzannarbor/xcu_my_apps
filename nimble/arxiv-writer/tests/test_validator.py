"""
Unit tests for the content validation framework.
"""

import pytest
from unittest.mock import Mock, patch

from src.arxiv_writer.core.validator import (
    ContentValidator, ValidationConfig, ValidationRule, ValidationSeverity,
    WordCountValidator, AcademicToneValidator, CitationValidator, StructureValidator
)
from src.arxiv_writer.core.exceptions import ValidationError
from src.arxiv_writer.core.models import ValidationResult


class TestValidationConfig:
    """Test ValidationConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ValidationConfig()
        
        assert config.min_word_count == 100
        assert config.max_word_count == 50000
        assert "abstract" in config.section_word_limits
        assert "introduction" in config.required_sections
        assert config.require_academic_tone is True
        assert config.require_citations is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = ValidationConfig(
            min_word_count=200,
            max_word_count=10000,
            strict_mode=True,
            fail_on_warnings=True
        )
        
        assert config.min_word_count == 200
        assert config.max_word_count == 10000
        assert config.strict_mode is True
        assert config.fail_on_warnings is True


class TestWordCountValidator:
    """Test WordCountValidator class."""
    
    def test_valid_word_count(self):
        """Test validation with valid word count."""
        config = ValidationConfig(min_word_count=10, max_word_count=100)
        validator = WordCountValidator(config)
        
        content = "This is a test content with exactly seventeen words to test the word count validation functionality."
        result = validator.validate(content)
        
        assert result.is_valid is True
        assert result.metrics["score"] == 1.0
        assert len(result.errors) == 0
        assert result.metrics["word_count"] == 16
    
    def test_content_too_short(self):
        """Test validation with content too short."""
        config = ValidationConfig(min_word_count=50, max_word_count=100)
        validator = WordCountValidator(config)
        
        content = "Short content."
        result = validator.validate(content)
        
        assert result.is_valid is False
        assert result.metrics["score"] < 1.0
        assert len(result.errors) > 0
        assert "too short" in result.errors[0]
        assert result.metrics["word_count"] == 2
    
    def test_content_too_long(self):
        """Test validation with content too long."""
        config = ValidationConfig(min_word_count=10, max_word_count=20)
        validator = WordCountValidator(config)
        
        content = " ".join(["word"] * 30)  # 30 words
        result = validator.validate(content)
        
        assert result.metrics["score"] < 1.0
        assert len(result.errors) > 0 or len(result.warnings) > 0
        assert result.metrics["word_count"] == 30
    
    def test_section_specific_limits(self):
        """Test validation with section-specific word limits."""
        config = ValidationConfig()
        validator = WordCountValidator(config)
        
        # Abstract should be 150-250 words
        short_abstract = " ".join(["word"] * 100)  # 100 words
        result = validator.validate(short_abstract, {"section_name": "abstract"})
        
        assert result.is_valid is False
        assert "too short" in result.errors[0]
        assert result.metrics["min_required"] == 150


class TestAcademicToneValidator:
    """Test AcademicToneValidator class."""
    
    def test_good_academic_tone(self):
        """Test validation with good academic tone."""
        config = ValidationConfig()
        validator = AcademicToneValidator(config)
        
        content = """
        This paper presents a comprehensive analysis of the methodology.
        Our approach demonstrates significant improvements in performance.
        The results show that our framework achieves better accuracy.
        We evaluate the system using standard benchmarks.
        """
        
        result = validator.validate(content)
        
        assert result.is_valid is True
        assert result.metrics["score"] > 0.8
        assert result.metrics["academic_score"] >= 2
    
    def test_informal_language(self):
        """Test validation with informal language."""
        config = ValidationConfig()
        validator = AcademicToneValidator(config)
        
        content = """
        I think this is a really good approach! Obviously, it works well.
        Actually, the results are pretty amazing. Basically, we're done.
        """
        
        result = validator.validate(content)
        
        assert result.metrics["score"] < 1.0
        assert len(result.errors) > 0 or len(result.warnings) > 0
        # Check if informal language is mentioned in errors or warnings
        all_messages = result.errors + result.warnings
        assert any("informal language" in msg.lower() for msg in all_messages)
    
    def test_technical_depth(self):
        """Test validation of technical depth."""
        config = ValidationConfig(check_technical_depth=True)
        validator = AcademicToneValidator(config)
        
        technical_content = """
        The methodology involves a comprehensive analysis of the system architecture.
        Our implementation uses advanced algorithms for performance optimization.
        The evaluation framework provides accurate assessment of the results.
        """
        
        result = validator.validate(technical_content)
        
        assert result.metrics["technical_score"] >= 3
        assert result.metrics["score"] >= 0.8
    
    def test_low_technical_depth(self):
        """Test validation with low technical depth."""
        config = ValidationConfig(check_technical_depth=True)
        validator = AcademicToneValidator(config)
        
        simple_content = """
        This is a simple test. We did some work.
        The results were good. Everything worked fine.
        """
        
        result = validator.validate(simple_content)
        
        assert result.metrics["technical_score"] < 3
        assert len(result.warnings) > 0


class TestCitationValidator:
    """Test CitationValidator class."""
    
    def test_sufficient_citations(self):
        """Test validation with sufficient citations."""
        config = ValidationConfig()
        validator = CitationValidator(config)
        
        content = """
        Previous work [1] has shown that this approach is effective.
        Smith et al. (2023) demonstrated similar results.
        According to Johnson (2024), this methodology is sound.
        Recent studies [2, 3] support our findings.
        """
        
        result = validator.validate(content, {"section_name": "introduction"})
        
        assert result.is_valid is True
        assert result.metrics["score"] == 1.0
        assert result.metrics["citation_count"] >= 3
    
    def test_insufficient_citations(self):
        """Test validation with insufficient citations."""
        config = ValidationConfig()
        validator = CitationValidator(config)
        
        content = """
        This is an introduction section without proper citations.
        We present our work here. The methodology is novel.
        """
        
        result = validator.validate(content, {"section_name": "introduction"})
        
        assert result.is_valid is False or result.metrics["score"] < 1.0
        assert result.metrics["citation_count"] < 3
        assert len(result.errors) > 0 or len(result.warnings) > 0
    
    def test_citations_disabled(self):
        """Test validation with citations disabled."""
        config = ValidationConfig(require_citations=False)
        validator = CitationValidator(config)
        
        content = "Content without any citations."
        result = validator.validate(content)
        
        assert result.is_valid is True
        assert result.metrics["score"] == 1.0
    
    def test_citation_patterns(self):
        """Test different citation patterns."""
        config = ValidationConfig()
        validator = CitationValidator(config)
        
        content = """
        Various citation formats: [1], (Smith, 2024), Johnson et al.,
        Brown et al. (2023), and Wilson (2024) all support this.
        """
        
        result = validator.validate(content)
        
        assert result.metrics["citation_count"] >= 4


class TestStructureValidator:
    """Test StructureValidator class."""
    
    def test_good_structure(self):
        """Test validation with good structure."""
        config = ValidationConfig()
        validator = StructureValidator(config)
        
        content = """This is the first paragraph with sufficient content to demonstrate proper paragraph structure and formatting.

This is the second paragraph that continues the discussion with appropriate length and structure.

The third paragraph concludes the section with proper academic formatting and style."""
        
        result = validator.validate(content)
        
        assert result.is_valid is True
        assert result.metrics["score"] >= 0.9
        assert result.metrics["paragraph_count"] == 3
    
    def test_poor_structure(self):
        """Test validation with poor structure."""
        config = ValidationConfig()
        validator = StructureValidator(config)
        
        content = "Single paragraph without proper structure or formatting."
        
        result = validator.validate(content)
        
        assert result.metrics["score"] < 1.0
        assert result.metrics["paragraph_count"] == 1
        assert len(result.warnings) > 0
    
    def test_long_paragraphs(self):
        """Test validation with very long paragraphs."""
        config = ValidationConfig()
        validator = StructureValidator(config)
        
        # Create a very long paragraph (>200 words)
        long_paragraph = " ".join(["word"] * 250)
        content = f"{long_paragraph}\n\nSecond paragraph."
        
        result = validator.validate(content)
        
        assert result.metrics["long_paragraphs"] == 1
        assert len(result.warnings) > 0
    
    def test_formatting_disabled(self):
        """Test validation with formatting checks disabled."""
        config = ValidationConfig(check_proper_formatting=False)
        validator = StructureValidator(config)
        
        content = "Poor structure."
        result = validator.validate(content)
        
        assert result.is_valid is True
        assert result.metrics["score"] == 1.0


class TestContentValidator:
    """Test ContentValidator main class."""
    
    def test_initialization(self):
        """Test ContentValidator initialization."""
        config = ValidationConfig()
        validator = ContentValidator(config)
        
        assert "word_count" in validator.validators
        assert "academic_tone" in validator.validators
        assert "citations" in validator.validators
        assert "structure" in validator.validators
    
    def test_validate_content(self):
        """Test content validation."""
        config = ValidationConfig(min_word_count=10, max_word_count=1000)
        validator = ContentValidator(config)
        
        content = """
        This paper presents a comprehensive analysis of our methodology.
        Previous work [1] has established the foundation for this research.
        Our approach demonstrates significant improvements in performance.
        
        The results show that our framework achieves better accuracy
        compared to traditional methods. We evaluate the system using
        standard benchmarks and provide detailed analysis.
        """
        
        results = validator.validate_content(content, "introduction")
        
        assert "word_count" in results
        assert "academic_tone" in results
        assert "citations" in results
        assert "structure" in results
        
        for result in results.values():
            assert isinstance(result, ValidationResult)
    
    def test_validate_sections(self):
        """Test validation of multiple sections."""
        config = ValidationConfig(min_word_count=10, max_word_count=1000)
        validator = ContentValidator(config)
        
        sections = {
            "abstract": """
            This paper presents a comprehensive analysis of AI-assisted publishing.
            Our approach demonstrates significant improvements in automation and efficiency.
            The results show measurable benefits for content generation workflows.
            """,
            "introduction": """
            The publishing industry faces significant challenges in content generation.
            Previous work [1, 2] has explored various automation approaches.
            Our methodology provides a novel framework for AI-assisted publishing.
            This paper presents our comprehensive analysis and evaluation results.
            """
        }
        
        results = validator.validate_sections(sections)
        
        assert "abstract" in results
        assert "introduction" in results
        
        for section_results in results.values():
            assert "word_count" in section_results
            assert "academic_tone" in section_results
    
    def test_empty_content_validation(self):
        """Test validation of empty content."""
        validator = ContentValidator()
        
        with pytest.raises(ValidationError):
            validator.validate_content("")
    
    def test_custom_rules(self):
        """Test custom validation rules."""
        def check_custom_requirement(content: str) -> bool:
            return "custom requirement" in content.lower()
        
        custom_rule = ValidationRule(
            name="custom_test",
            description="Test custom rule",
            severity=ValidationSeverity.WARNING,
            validator_func=check_custom_requirement,
            error_message="Custom requirement not found",
            suggestion="Add custom requirement to content"
        )
        
        config = ValidationConfig(custom_rules=[custom_rule])
        validator = ContentValidator(config)
        
        # Test content without custom requirement
        content = "This is test content without the requirement."
        results = validator.validate_content(content)
        
        assert "custom_custom_test" in results
        custom_result = results["custom_custom_test"]
        assert custom_result.is_valid is False
        assert "Custom requirement not found" in custom_result.warnings
    
    def test_overall_score_calculation(self):
        """Test overall score calculation."""
        config = ValidationConfig(min_word_count=10, max_word_count=1000)
        validator = ContentValidator(config)
        
        sections = {
            "section1": "This is a good academic content with proper structure and citations [1].",
            "section2": "Another section with academic tone and proper formatting."
        }
        
        results = validator.validate_sections(sections)
        overall_score = validator.get_overall_score(results)
        
        assert 0.0 <= overall_score <= 1.0
    
    def test_content_validity_check(self):
        """Test content validity checking."""
        config = ValidationConfig(min_word_count=5, max_word_count=1000)
        validator = ContentValidator(config)
        
        good_content = {
            "section1": """
            This paper presents a comprehensive methodology for academic research.
            Our approach demonstrates significant improvements in analysis quality.
            Previous work [1, 2] has established the theoretical foundation.
            """
        }
        
        results = validator.validate_sections(good_content)
        is_valid = validator.is_content_valid(results)
        
        assert is_valid is True
    
    def test_validation_summary(self):
        """Test validation summary generation."""
        config = ValidationConfig(min_word_count=10, max_word_count=1000)
        validator = ContentValidator(config)
        
        sections = {
            "abstract": "Short abstract content for testing validation summary generation.",
            "introduction": "Introduction section with proper academic tone and structure for testing."
        }
        
        results = validator.validate_sections(sections)
        summary = validator.get_validation_summary(results)
        
        assert "overall_score" in summary
        assert "is_valid" in summary
        assert "section_scores" in summary
        assert "total_issues" in summary
        assert "total_suggestions" in summary
        assert summary["sections_validated"] == 2
        assert summary["validators_used"] > 0
    
    def test_add_remove_validators(self):
        """Test adding and removing validators."""
        validator = ContentValidator()
        initial_count = len(validator.validators)
        
        # Add custom rule
        custom_rule = ValidationRule(
            name="test_rule",
            description="Test rule",
            severity=ValidationSeverity.INFO,
            validator_func=lambda x: True,
            error_message="Test error"
        )
        
        validator.add_custom_rule(custom_rule)
        assert len(validator.validators) == initial_count + 1
        
        # Remove validator
        validator.remove_validator("custom_test_rule")
        assert len(validator.validators) == initial_count
    
    def test_specific_validators_only(self):
        """Test running only specific validators."""
        config = ValidationConfig(min_word_count=10, max_word_count=1000)
        validator = ContentValidator(config)
        
        content = "Test content for specific validator testing."
        results = validator.validate_content(content, validators_to_run=["word_count", "structure"])
        
        assert "word_count" in results
        assert "structure" in results
        assert "academic_tone" not in results
        assert "citations" not in results


if __name__ == "__main__":
    pytest.main([__file__])