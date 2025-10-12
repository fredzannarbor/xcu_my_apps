"""
Unit tests for the paper quality assessment system.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.arxiv_writer.core.quality_assessor import (
    PaperQualityAssessor, ArxivComplianceChecker, QualityMetrics, QualityIssue,
    PaperQualityReport, assess_paper_quality, assess_paper_file
)
from src.arxiv_writer.core.validator import ValidationConfig
from src.arxiv_writer.core.exceptions import ValidationError


class TestQualityMetrics:
    """Test QualityMetrics class."""
    
    def test_quality_metrics_creation(self):
        """Test creating quality metrics."""
        metrics = QualityMetrics(
            overall_score=0.85,
            readability_score=0.9,
            technical_depth_score=0.8,
            academic_tone_score=0.85,
            structure_score=0.9,
            citation_score=0.7,
            arxiv_compliance_score=0.95
        )
        
        assert metrics.overall_score == 0.85
        assert metrics.readability_score == 0.9
        assert metrics.technical_depth_score == 0.8
    
    def test_quality_metrics_to_dict(self):
        """Test converting quality metrics to dictionary."""
        metrics = QualityMetrics(
            overall_score=0.85,
            readability_score=0.9,
            technical_depth_score=0.8,
            academic_tone_score=0.85,
            structure_score=0.9,
            citation_score=0.7,
            arxiv_compliance_score=0.95
        )
        
        metrics_dict = metrics.to_dict()
        
        assert isinstance(metrics_dict, dict)
        assert metrics_dict["overall_score"] == 0.85
        assert metrics_dict["readability_score"] == 0.9
        assert len(metrics_dict) == 7


class TestQualityIssue:
    """Test QualityIssue class."""
    
    def test_quality_issue_creation(self):
        """Test creating quality issues."""
        issue = QualityIssue(
            severity="error",
            section="abstract",
            message="Abstract too short",
            suggestion="Expand the abstract",
            line_number=5
        )
        
        assert issue.severity == "error"
        assert issue.section == "abstract"
        assert issue.message == "Abstract too short"
        assert issue.suggestion == "Expand the abstract"
        assert issue.line_number == 5
    
    def test_quality_issue_optional_fields(self):
        """Test quality issue with optional fields."""
        issue = QualityIssue(
            severity="warning",
            section="introduction",
            message="Could use more citations"
        )
        
        assert issue.severity == "warning"
        assert issue.section == "introduction"
        assert issue.message == "Could use more citations"
        assert issue.suggestion is None
        assert issue.line_number is None


class TestPaperQualityReport:
    """Test PaperQualityReport class."""
    
    def test_quality_report_creation(self):
        """Test creating quality report."""
        metrics = QualityMetrics(
            overall_score=0.85,
            readability_score=0.9,
            technical_depth_score=0.8,
            academic_tone_score=0.85,
            structure_score=0.9,
            citation_score=0.7,
            arxiv_compliance_score=0.95
        )
        
        issues = [
            QualityIssue("warning", "abstract", "Could be longer"),
            QualityIssue("info", "introduction", "Good structure")
        ]
        
        report = PaperQualityReport(
            overall_score=0.85,
            metrics=metrics,
            section_scores={"abstract": 0.8, "introduction": 0.9},
            issues=issues,
            recommendations=["Improve abstract", "Add more citations"],
            arxiv_readiness=True,
            word_count=5000,
            sections_analyzed=5,
            generated_at="2024-01-01T12:00:00"
        )
        
        assert report.overall_score == 0.85
        assert report.arxiv_readiness is True
        assert report.word_count == 5000
        assert len(report.issues) == 2
        assert len(report.recommendations) == 2
    
    def test_quality_report_to_dict(self):
        """Test converting quality report to dictionary."""
        metrics = QualityMetrics(
            overall_score=0.85,
            readability_score=0.9,
            technical_depth_score=0.8,
            academic_tone_score=0.85,
            structure_score=0.9,
            citation_score=0.7,
            arxiv_compliance_score=0.95
        )
        
        issues = [QualityIssue("warning", "abstract", "Could be longer")]
        
        report = PaperQualityReport(
            overall_score=0.85,
            metrics=metrics,
            section_scores={"abstract": 0.8},
            issues=issues,
            recommendations=["Improve abstract"],
            arxiv_readiness=True,
            word_count=5000,
            sections_analyzed=1,
            generated_at="2024-01-01T12:00:00"
        )
        
        report_dict = report.to_dict()
        
        assert isinstance(report_dict, dict)
        assert report_dict["overall_score"] == 0.85
        assert report_dict["arxiv_readiness"] is True
        assert len(report_dict["issues"]) == 1
        assert report_dict["issues"][0]["severity"] == "warning"
    
    def test_quality_report_save_to_file(self):
        """Test saving quality report to file."""
        metrics = QualityMetrics(
            overall_score=0.85,
            readability_score=0.9,
            technical_depth_score=0.8,
            academic_tone_score=0.85,
            structure_score=0.9,
            citation_score=0.7,
            arxiv_compliance_score=0.95
        )
        
        report = PaperQualityReport(
            overall_score=0.85,
            metrics=metrics,
            section_scores={"abstract": 0.8},
            issues=[],
            recommendations=[],
            arxiv_readiness=True,
            word_count=5000,
            sections_analyzed=1,
            generated_at="2024-01-01T12:00:00"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            report.save_to_file(temp_path)
            
            # Verify file was created and contains correct data
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["overall_score"] == 0.85
            assert saved_data["arxiv_readiness"] is True
            
        finally:
            Path(temp_path).unlink()


class TestArxivComplianceChecker:
    """Test ArxivComplianceChecker class."""
    
    def test_compliance_checker_initialization(self):
        """Test compliance checker initialization."""
        checker = ArxivComplianceChecker()
        
        assert "abstract" in checker.required_sections
        assert "introduction" in checker.required_sections
        assert "conclusion" in checker.required_sections
        assert checker.max_abstract_words == 250
        assert checker.min_abstract_words == 100
    
    def test_check_compliance_good_paper(self):
        """Test compliance checking with a good paper."""
        checker = ArxivComplianceChecker()
        
        sections = {
            "abstract": " ".join(["word"] * 150),  # 150 words
            "introduction": " ".join(["word"] * 500),
            "methodology": " ".join(["word"] * 800),
            "results": " ".join(["word"] * 600),
            "conclusion": " ".join(["word"] * 300)
        }
        
        complete_paper = """
        ## Abstract
        This is an abstract.
        
        ## Introduction
        This is the introduction.
        
        ## References
        [1] Some reference
        """
        
        score, issues = checker.check_compliance(sections, complete_paper)
        
        assert score >= 0.8
        assert len([issue for issue in issues if issue.severity == "error"]) == 0
    
    def test_check_compliance_missing_sections(self):
        """Test compliance checking with missing sections."""
        checker = ArxivComplianceChecker()
        
        sections = {
            "introduction": " ".join(["word"] * 500),
            "methodology": " ".join(["word"] * 800)
        }
        
        complete_paper = "Some content"
        
        score, issues = checker.check_compliance(sections, complete_paper)
        
        assert score < 1.0
        error_issues = [issue for issue in issues if issue.severity == "error"]
        assert len(error_issues) > 0
        assert any("missing required sections" in issue.message.lower() for issue in error_issues)
    
    def test_check_compliance_abstract_too_short(self):
        """Test compliance checking with short abstract."""
        checker = ArxivComplianceChecker()
        
        sections = {
            "abstract": " ".join(["word"] * 50),  # 50 words (too short)
            "introduction": " ".join(["word"] * 500),
            "conclusion": " ".join(["word"] * 300)
        }
        
        complete_paper = "Some content with ## References section"
        
        score, issues = checker.check_compliance(sections, complete_paper)
        
        assert score < 1.0
        error_issues = [issue for issue in issues if issue.severity == "error"]
        assert any("abstract too short" in issue.message.lower() for issue in error_issues)
    
    def test_check_compliance_abstract_too_long(self):
        """Test compliance checking with long abstract."""
        checker = ArxivComplianceChecker()
        
        sections = {
            "abstract": " ".join(["word"] * 300),  # 300 words (too long)
            "introduction": " ".join(["word"] * 500),
            "conclusion": " ".join(["word"] * 300)
        }
        
        complete_paper = "Some content with ## References section"
        
        score, issues = checker.check_compliance(sections, complete_paper)
        
        assert score < 1.0
        warning_issues = [issue for issue in issues if issue.severity == "warning"]
        assert any("abstract too long" in issue.message.lower() for issue in warning_issues)
    
    def test_check_compliance_no_references(self):
        """Test compliance checking without references."""
        checker = ArxivComplianceChecker()
        
        sections = {
            "abstract": " ".join(["word"] * 150),
            "introduction": " ".join(["word"] * 500),
            "conclusion": " ".join(["word"] * 300)
        }
        
        complete_paper = "Some content without references"
        
        score, issues = checker.check_compliance(sections, complete_paper)
        
        assert score < 1.0
        error_issues = [issue for issue in issues if issue.severity == "error"]
        assert any("no references section" in issue.message.lower() for issue in error_issues)


class TestPaperQualityAssessor:
    """Test PaperQualityAssessor class."""
    
    def test_assessor_initialization(self):
        """Test assessor initialization."""
        assessor = PaperQualityAssessor()
        
        assert assessor.content_validator is not None
        assert assessor.arxiv_checker is not None
        assert assessor.config is not None
    
    def test_assessor_initialization_with_config(self):
        """Test assessor initialization with custom config."""
        config = ValidationConfig(min_word_count=50, max_word_count=5000)
        assessor = PaperQualityAssessor(config)
        
        assert assessor.config == config
        assert assessor.config.min_word_count == 50
    
    def test_assess_paper_quality(self):
        """Test paper quality assessment."""
        assessor = PaperQualityAssessor()
        
        sections = {
            "abstract": """
            This paper presents a comprehensive analysis of AI-assisted publishing.
            Our approach demonstrates significant improvements in automation and efficiency.
            The results show measurable benefits for content generation workflows.
            We evaluate the system using standard benchmarks and provide detailed analysis.
            The methodology involves advanced algorithms and frameworks for optimization.
            """,
            "introduction": """
            The publishing industry faces significant challenges in content generation.
            Previous work [1, 2] has explored various automation approaches.
            Our methodology provides a novel framework for AI-assisted publishing.
            This paper presents our comprehensive analysis and evaluation results.
            We demonstrate the effectiveness of our approach through extensive testing.
            """
        }
        
        report = assessor.assess_paper_quality(sections)
        
        assert isinstance(report, PaperQualityReport)
        assert 0.0 <= report.overall_score <= 1.0
        assert isinstance(report.metrics, QualityMetrics)
        assert len(report.section_scores) == len(sections)
        assert report.word_count > 0
        assert report.sections_analyzed == len(sections)
    
    def test_assess_paper_quality_with_complete_paper(self):
        """Test paper quality assessment with complete paper provided."""
        assessor = PaperQualityAssessor()
        
        sections = {
            "abstract": "Short abstract content for testing.",
            "introduction": "Introduction content with proper structure."
        }
        
        complete_paper = """
        ## Abstract
        Short abstract content for testing.
        
        ## Introduction
        Introduction content with proper structure.
        
        ## References
        [1] Some reference
        """
        
        report = assessor.assess_paper_quality(sections, complete_paper)
        
        assert isinstance(report, PaperQualityReport)
        assert report.word_count > 0
    
    def test_combine_sections(self):
        """Test combining sections into complete paper."""
        assessor = PaperQualityAssessor()
        
        sections = {
            "abstract": "This is the abstract.",
            "introduction": "This is the introduction."
        }
        
        combined = assessor._combine_sections(sections)
        
        assert "## Abstract" in combined
        assert "## Introduction" in combined
        assert "This is the abstract." in combined
        assert "This is the introduction." in combined
    
    def test_determine_arxiv_readiness_ready(self):
        """Test determining arXiv readiness for a ready paper."""
        assessor = PaperQualityAssessor()
        
        metrics = QualityMetrics(
            overall_score=0.85,
            readability_score=0.9,
            technical_depth_score=0.8,
            academic_tone_score=0.85,
            structure_score=0.9,
            citation_score=0.7,
            arxiv_compliance_score=0.95
        )
        
        issues = [
            QualityIssue("warning", "abstract", "Could be longer"),
            QualityIssue("info", "introduction", "Good structure")
        ]
        
        ready = assessor._determine_arxiv_readiness(metrics, issues)
        
        assert ready is True
    
    def test_determine_arxiv_readiness_not_ready_errors(self):
        """Test determining arXiv readiness with critical errors."""
        assessor = PaperQualityAssessor()
        
        metrics = QualityMetrics(
            overall_score=0.85,
            readability_score=0.9,
            technical_depth_score=0.8,
            academic_tone_score=0.85,
            structure_score=0.9,
            citation_score=0.7,
            arxiv_compliance_score=0.95
        )
        
        issues = [
            QualityIssue("error", "abstract", "Missing abstract"),
            QualityIssue("warning", "introduction", "Could be longer")
        ]
        
        ready = assessor._determine_arxiv_readiness(metrics, issues)
        
        assert ready is False
    
    def test_determine_arxiv_readiness_not_ready_low_scores(self):
        """Test determining arXiv readiness with low scores."""
        assessor = PaperQualityAssessor()
        
        metrics = QualityMetrics(
            overall_score=0.5,  # Too low
            readability_score=0.9,
            technical_depth_score=0.8,
            academic_tone_score=0.4,  # Too low
            structure_score=0.5,  # Too low
            citation_score=0.7,
            arxiv_compliance_score=0.6  # Too low
        )
        
        issues = []  # No critical errors
        
        ready = assessor._determine_arxiv_readiness(metrics, issues)
        
        assert ready is False
    
    def test_extract_sections(self):
        """Test extracting sections from markdown content."""
        assessor = PaperQualityAssessor()
        
        content = """
        ## Abstract
        
        This is the abstract content.
        
        ## Introduction
        
        This is the introduction content.
        
        ## Conclusion
        
        This is the conclusion.
        """
        
        sections = assessor._extract_sections(content)
        
        assert "abstract" in sections
        assert "introduction" in sections
        assert "conclusion" in sections
        assert "This is the abstract content." in sections["abstract"]
        assert "This is the introduction content." in sections["introduction"]
    
    def test_assess_paper_file(self):
        """Test assessing paper from file."""
        assessor = PaperQualityAssessor()
        
        paper_content = """
        ## Abstract
        
        This paper presents a comprehensive analysis of AI systems.
        Our approach demonstrates significant improvements in performance.
        The results show measurable benefits for various applications.
        
        ## Introduction
        
        The field of AI faces many challenges in system design.
        Previous work [1, 2] has explored various approaches.
        Our methodology provides a novel framework for optimization.
        
        ## References
        
        [1] Smith et al. (2023)
        [2] Johnson (2024)
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(paper_content)
            temp_path = f.name
        
        try:
            report = assessor.assess_paper_file(temp_path)
            
            assert isinstance(report, PaperQualityReport)
            assert report.sections_analyzed > 0
            assert report.word_count > 0
            
        finally:
            Path(temp_path).unlink()
    
    def test_assess_paper_file_not_found(self):
        """Test assessing paper file that doesn't exist."""
        assessor = PaperQualityAssessor()
        
        with pytest.raises(ValidationError):
            assessor.assess_paper_file("nonexistent_file.md")
    
    def test_assess_paper_file_with_output(self):
        """Test assessing paper file with output report."""
        assessor = PaperQualityAssessor()
        
        paper_content = """
        ## Abstract
        
        This is a test paper for quality assessment.
        
        ## Introduction
        
        This is the introduction section.
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(paper_content)
            paper_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            report = assessor.assess_paper_file(paper_path, output_path)
            
            assert isinstance(report, PaperQualityReport)
            
            # Verify output file was created
            assert Path(output_path).exists()
            
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert "overall_score" in saved_data
            assert "arxiv_readiness" in saved_data
            
        finally:
            Path(paper_path).unlink()
            Path(output_path).unlink()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_assess_paper_quality_function(self):
        """Test assess_paper_quality convenience function."""
        sections = {
            "abstract": "This is a test abstract with sufficient content for analysis.",
            "introduction": "This is the introduction with proper academic tone and structure."
        }
        
        report = assess_paper_quality(sections)
        
        assert isinstance(report, PaperQualityReport)
        assert report.sections_analyzed == len(sections)
    
    def test_assess_paper_quality_function_with_config(self):
        """Test assess_paper_quality with custom config."""
        sections = {
            "abstract": "Short abstract.",
            "introduction": "Short introduction."
        }
        
        config = ValidationConfig(min_word_count=1, max_word_count=1000)
        report = assess_paper_quality(sections, config)
        
        assert isinstance(report, PaperQualityReport)
        assert report.sections_analyzed == len(sections)
    
    def test_assess_paper_file_function(self):
        """Test assess_paper_file convenience function."""
        paper_content = """
        ## Abstract
        
        This is a test paper for the convenience function.
        
        ## Introduction
        
        This is the introduction section with proper content.
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(paper_content)
            temp_path = f.name
        
        try:
            report = assess_paper_file(temp_path)
            
            assert isinstance(report, PaperQualityReport)
            assert report.sections_analyzed > 0
            
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__])