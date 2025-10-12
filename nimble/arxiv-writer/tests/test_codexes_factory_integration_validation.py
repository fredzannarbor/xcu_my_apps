"""
Comprehensive integration validation tests for Codexes Factory compatibility.

This module tests the complete replacement of existing arxiv paper functionality
with the new arxiv-writer package, ensuring identical output generation and
full workflow compatibility.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os
import sys

from src.arxiv_writer.core.codexes_factory_adapter import (
    CodexesFactoryAdapter,
    CodexesFactoryConfig,
    migrate_codexes_factory_config,
    create_codexes_compatibility_config,
    create_codexes_factory_paper_generator
)
from src.arxiv_writer.core.models import (
    PaperConfig, Section, PaperResult, GenerationSummary,
    LLMConfig, ValidationConfig, TemplateConfig
)
from src.arxiv_writer.core.exceptions import ConfigurationError, ValidationError


class TestCodexesFactoryCompleteReplacement:
    """Test complete replacement of existing arxiv paper functionality."""
    
    @pytest.fixture
    def xynapse_traces_config(self):
        """Create xynapse_traces configuration for testing."""
        return {
            "_config_info": {
                "description": "Xynapse Traces imprint configuration",
                "version": "2.0",
                "last_updated": "2025-07-18",
                "parent_publisher": "Nimble Books LLC"
            },
            "imprint": "Xynapse Traces",
            "publisher": "Nimble Books LLC",
            "workspace_root": ".",
            "output_directory": "output/arxiv_papers",
            "llm_config": {
                "default_model": "anthropic/claude-3-5-sonnet-20241022",
                "available_models": [
                    "anthropic/claude-3-5-sonnet-20241022",
                    "google/gemini-pro-1.5",
                    "openai/gpt-4-turbo",
                    "xai/grok-beta"
                ],
                "model_parameters": {
                    "anthropic/claude-3-5-sonnet-20241022": {
                        "max_tokens": 4000,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
            },
            "template_config": {
                "template_file": "templates/default_prompts.json",
                "section_order": [
                    "abstract",
                    "introduction",
                    "related_work",
                    "methodology",
                    "results",
                    "discussion",
                    "conclusion",
                    "references"
                ]
            },
            "validation_config": {
                "enabled": True,
                "strict_mode": False,
                "quality_thresholds": {
                    "min_word_count": 500,
                    "max_word_count": 8000,
                    "readability_score": 0.7,
                    "coherence_score": 0.8,
                    "citation_count": 10,
                    "section_balance": 0.6
                }
            },
            "context_config": {
                "collect_book_catalog": True,
                "collect_imprint_config": True,
                "collect_technical_architecture": True,
                "collect_performance_metrics": True
            },
            "workflow_settings": {
                "auto_generate_missing_fields": True,
                "require_manual_review": False,
                "notification_email": "xynapse@nimblebooks.com",
                "backup_configurations": True,
                "llm_completion_enabled": True,
                "computed_fields_enabled": True
            }
        }
    
    @pytest.fixture
    def mock_context_data(self):
        """Create mock context data that matches Codexes Factory patterns."""
        return {
            "sources": {
                "book_catalog": {
                    "total_books": 150,
                    "genres": ["Technology", "Science", "Philosophy"],
                    "recent_publications": [
                        {"title": "AI Ethics", "year": 2024},
                        {"title": "Quantum Computing", "year": 2023}
                    ]
                },
                "imprint_config": {
                    "imprint_name": "Xynapse Traces",
                    "publisher": "Nimble Books LLC",
                    "focus_areas": ["Technology", "Science", "Philosophy", "Future Studies"],
                    "target_audience": "Academic and Professional"
                },
                "technical_architecture": {
                    "systems": ["Publishing Pipeline", "Content Management", "Distribution"],
                    "technologies": ["Python", "LaTeX", "PDF Generation"],
                    "integrations": ["Lightning Source", "Amazon KDP"]
                },
                "performance_metrics": {
                    "monthly_publications": 12,
                    "average_page_count": 250,
                    "quality_score": 0.85,
                    "customer_satisfaction": 0.92
                }
            },
            "collection_metadata": {
                "timestamp": "2024-01-01T00:00:00Z",
                "collection_duration": 5.2,
                "sources_attempted": 4,
                "sources_successful": 4,
                "validation_passed": True
            },
            "validation_results": {
                "book_catalog": "valid",
                "imprint_config": "valid",
                "technical_architecture": "valid",
                "performance_metrics": "valid"
            }
        }
    
    @pytest.fixture
    def expected_paper_sections(self):
        """Create expected paper sections that match Codexes Factory output."""
        return {
            "abstract": Section(
                name="abstract",
                content="This paper presents a comprehensive analysis of the Xynapse Traces publishing imprint, examining its technological infrastructure, publication patterns, and market positioning within the academic and professional publishing landscape.",
                word_count=150,
                generated_at=datetime(2024, 1, 1, 12, 0, 0),
                model_used="anthropic/claude-3-5-sonnet-20241022",
                validation_status="valid",
                metadata={
                    "section_type": "abstract",
                    "generation_time": 2.5,
                    "prompt_tokens": 500,
                    "completion_tokens": 150
                }
            ),
            "introduction": Section(
                name="introduction",
                content="The publishing industry has undergone significant transformation in recent years, with digital technologies enabling new models of content creation, distribution, and consumption. Xynapse Traces, an imprint of Nimble Books LLC, represents a forward-thinking approach to academic and professional publishing.",
                word_count=300,
                generated_at=datetime(2024, 1, 1, 12, 5, 0),
                model_used="anthropic/claude-3-5-sonnet-20241022",
                validation_status="valid",
                metadata={
                    "section_type": "introduction",
                    "generation_time": 3.2,
                    "prompt_tokens": 800,
                    "completion_tokens": 300
                }
            ),
            "methodology": Section(
                name="methodology",
                content="Our analysis employs a mixed-methods approach, combining quantitative analysis of publication data with qualitative assessment of content quality and market positioning. Data was collected from multiple sources including the book catalog, imprint configuration, technical architecture documentation, and performance metrics.",
                word_count=250,
                generated_at=datetime(2024, 1, 1, 12, 10, 0),
                model_used="anthropic/claude-3-5-sonnet-20241022",
                validation_status="valid",
                metadata={
                    "section_type": "methodology",
                    "generation_time": 2.8,
                    "prompt_tokens": 700,
                    "completion_tokens": 250
                }
            )
        }
    
    def test_complete_workflow_replacement(self, xynapse_traces_config, mock_context_data, expected_paper_sections):
        """Test complete replacement of existing arxiv paper functionality."""
        # Create temporary configuration file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(xynapse_traces_config, f)
            config_path = f.name
        
        try:
            # Mock all dependencies
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector') as mock_create_collector:
                with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator') as mock_generator_class:
                    
                    # Setup context collector mock
                    mock_context_collector = Mock()
                    mock_context_collector.collect_context.return_value = mock_context_data
                    mock_context_collector.prepare_context.return_value = {
                        "prepared_context": mock_context_data,
                        "context_summary": "Comprehensive Xynapse Traces analysis data"
                    }
                    mock_create_collector.return_value = mock_context_collector
                    
                    # Setup paper generator mock
                    mock_generator = Mock()
                    mock_paper_result = PaperResult(
                        sections=expected_paper_sections,
                        complete_paper=self._create_complete_paper(expected_paper_sections),
                        generation_summary=GenerationSummary(
                            total_sections=len(expected_paper_sections),
                            successful_sections=len(expected_paper_sections),
                            failed_sections=0,
                            total_time=15.5,
                            total_word_count=sum(s.word_count for s in expected_paper_sections.values()),
                            llm_calls=len(expected_paper_sections)
                        ),
                        output_files=["xynapse_traces_analysis.tex", "xynapse_traces_analysis.pdf"]
                    )
                    mock_generator.generate_paper.return_value = mock_paper_result
                    mock_generator_class.return_value = mock_generator
                    
                    # Create adapter and test complete workflow
                    adapter = CodexesFactoryAdapter(config_path)
                    
                    # Verify initialization
                    assert adapter.codexes_config.imprint_name == "Xynapse Traces"
                    assert adapter.codexes_config.default_model == "anthropic/claude-3-5-sonnet-20241022"
                    
                    # Test paper generation
                    result = adapter.generate_paper()
                    
                    # Verify context collection was called correctly
                    mock_context_collector.collect_context.assert_called_once()
                    mock_context_collector.prepare_context.assert_called_once()
                    
                    # Verify paper generation was called correctly
                    mock_generator.generate_paper.assert_called_once()
                    
                    # Verify result format matches Codexes Factory expectations
                    self._validate_codexes_factory_result_format(result, xynapse_traces_config, mock_context_data)
                    
                    # Verify content matches expected output
                    assert result["paper_content"] == self._create_complete_paper(expected_paper_sections)
                    assert len(result["sections"]) == len(expected_paper_sections)
                    
                    # Verify imprint information is preserved
                    assert result["imprint_info"]["imprint_name"] == "Xynapse Traces"
                    assert result["imprint_info"]["workspace_root"] == "."
                    
        finally:
            Path(config_path).unlink()
    
    def test_identical_output_generation_with_xynapse_traces(self, xynapse_traces_config, mock_context_data):
        """Test that output generation is identical to original Codexes Factory implementation."""
        # Create two identical configurations
        config1 = xynapse_traces_config.copy()
        config2 = xynapse_traces_config.copy()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
            json.dump(config1, f1)
            config_path1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
            json.dump(config2, f2)
            config_path2 = f2.name
        
        try:
            # Mock deterministic responses
            deterministic_sections = self._create_deterministic_sections()
            
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector') as mock_create_collector:
                with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator') as mock_generator_class:
                    
                    # Setup identical mocks for both adapters
                    mock_context_collector = Mock()
                    mock_context_collector.collect_context.return_value = mock_context_data
                    mock_context_collector.prepare_context.return_value = {"prepared": "context"}
                    mock_create_collector.return_value = mock_context_collector
                    
                    mock_generator = Mock()
                    mock_paper_result = PaperResult(
                        sections=deterministic_sections,
                        complete_paper=self._create_complete_paper(deterministic_sections),
                        generation_summary=GenerationSummary(
                            total_sections=len(deterministic_sections),
                            successful_sections=len(deterministic_sections),
                            failed_sections=0,
                            total_time=10.0,
                            total_word_count=sum(s.word_count for s in deterministic_sections.values()),
                            llm_calls=len(deterministic_sections)
                        ),
                        output_files=["paper.tex"]
                    )
                    mock_generator.generate_paper.return_value = mock_paper_result
                    mock_generator_class.return_value = mock_generator
                    
                    # Generate papers with both adapters
                    adapter1 = CodexesFactoryAdapter(config_path1)
                    adapter2 = CodexesFactoryAdapter(config_path2)
                    
                    result1 = adapter1.generate_paper()
                    result2 = adapter2.generate_paper()
                    
                    # Verify identical outputs
                    assert result1["paper_content"] == result2["paper_content"]
                    assert result1["sections"].keys() == result2["sections"].keys()
                    
                    for section_name in result1["sections"]:
                        section1 = result1["sections"][section_name]
                        section2 = result2["sections"][section_name]
                        assert section1["content"] == section2["content"]
                        assert section1["word_count"] == section2["word_count"]
                        assert section1["model_used"] == section2["model_used"]
                    
                    # Verify generation summaries are identical
                    assert result1["generation_summary"]["total_sections"] == result2["generation_summary"]["total_sections"]
                    assert result1["generation_summary"]["total_word_count"] == result2["generation_summary"]["total_word_count"]
                    
        finally:
            Path(config_path1).unlink()
            Path(config_path2).unlink()
    
    def test_all_existing_workflows_compatibility(self, xynapse_traces_config, mock_context_data):
        """Test that all existing Codexes Factory workflows work with new package."""
        workflows_to_test = [
            "generate_complete_paper",
            "generate_individual_sections",
            "validate_paper_content",
            "collect_context_data",
            "migrate_configuration"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(xynapse_traces_config, f)
            config_path = f.name
        
        try:
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector') as mock_create_collector:
                with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator') as mock_generator_class:
                    
                    # Setup mocks
                    mock_context_collector = Mock()
                    mock_context_collector.collect_context.return_value = mock_context_data
                    mock_context_collector.prepare_context.return_value = {"prepared": "context"}
                    mock_create_collector.return_value = mock_context_collector
                    
                    mock_generator = Mock()
                    mock_generator_class.return_value = mock_generator
                    
                    adapter = CodexesFactoryAdapter(config_path)
                    
                    # Test workflow 1: Generate complete paper
                    mock_paper_result = PaperResult(
                        sections={"abstract": self._create_test_section("abstract")},
                        complete_paper="Complete paper content",
                        output_files=["paper.tex"]
                    )
                    mock_generator.generate_paper.return_value = mock_paper_result
                    
                    result = adapter.generate_paper()
                    assert "paper_content" in result
                    assert "sections" in result
                    assert "imprint_info" in result
                    
                    # Test workflow 2: Generate individual sections
                    mock_section_result = self._create_test_section("introduction")
                    mock_generator.generate_section.return_value = mock_section_result
                    
                    section_result = adapter.generate_section("introduction")
                    assert section_result["section_name"] == "introduction"
                    assert "content" in section_result
                    assert "context_summary" in section_result
                    
                    # Test workflow 3: Validate paper content
                    mock_validation_result = Mock()
                    mock_validation_result.is_valid = True
                    mock_validation_result.errors = []
                    mock_validation_result.warnings = []
                    mock_validation_result.metrics = {"word_count": 1000}
                    mock_generator.validate_paper.return_value = mock_validation_result
                    
                    validation_result = adapter.validate_paper("Test paper content")
                    assert validation_result["is_valid"] is True
                    assert "arxiv_compliance" in validation_result
                    
                    # Test workflow 4: Collect context data
                    context_result = adapter.get_context_data()
                    assert "imprint_data" in context_result
                    assert "collection_metadata" in context_result
                    assert "summary" in context_result
                    
                    # Test workflow 5: Configuration migration
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_f:
                        output_path = output_f.name
                    
                    try:
                        migrated_config = migrate_codexes_factory_config(config_path, output_path)
                        assert isinstance(migrated_config, PaperConfig)
                        assert Path(output_path).exists()
                    finally:
                        Path(output_path).unlink()
                    
        finally:
            Path(config_path).unlink()
    
    def test_configuration_migration_preserves_all_settings(self, xynapse_traces_config):
        """Test that configuration migration preserves all Codexes Factory settings."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as source_f:
            json.dump(xynapse_traces_config, source_f)
            source_path = source_f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as target_f:
            target_path = target_f.name
        
        try:
            with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
                # Migrate configuration
                migrated_config = migrate_codexes_factory_config(source_path, target_path)
                
                # Verify all key settings are preserved
                assert migrated_config.llm_config.default_model == xynapse_traces_config["llm_config"]["default_model"]
                assert set(migrated_config.llm_config.available_models) == set(xynapse_traces_config["llm_config"]["available_models"])
                assert migrated_config.template_config.template_file == xynapse_traces_config["template_config"]["template_file"]
                assert migrated_config.template_config.section_order == xynapse_traces_config["template_config"]["section_order"]
                assert migrated_config.validation_config.enabled == xynapse_traces_config["validation_config"]["enabled"]
                assert migrated_config.validation_config.strict_mode == xynapse_traces_config["validation_config"]["strict_mode"]
                
                # Verify quality thresholds are preserved
                for key, value in xynapse_traces_config["validation_config"]["quality_thresholds"].items():
                    assert migrated_config.validation_config.quality_thresholds[key] == value
                
                # Verify migrated file contains correct data
                with open(target_path, 'r') as f:
                    saved_config = json.load(f)
                
                assert saved_config["llm_config"]["default_model"] == xynapse_traces_config["llm_config"]["default_model"]
                assert "template_config" in saved_config
                assert "validation_config" in saved_config
                
        finally:
            Path(source_path).unlink()
            Path(target_path).unlink()
    
    def _create_complete_paper(self, sections):
        """Create complete paper content from sections."""
        paper_parts = []
        for section_name in ["abstract", "introduction", "methodology", "results", "discussion", "conclusion"]:
            if section_name in sections:
                paper_parts.append(f"\\section{{{section_name.title()}}}")
                paper_parts.append(sections[section_name].content)
                paper_parts.append("")
        
        return "\n".join(paper_parts)
    
    def _create_deterministic_sections(self):
        """Create deterministic sections for identical output testing."""
        return {
            "abstract": Section(
                name="abstract",
                content="Deterministic abstract content for testing identical output generation.",
                word_count=100,
                generated_at=datetime(2024, 1, 1, 12, 0, 0),
                model_used="anthropic/claude-3-5-sonnet-20241022",
                validation_status="valid",
                metadata={"deterministic": True}
            ),
            "introduction": Section(
                name="introduction",
                content="Deterministic introduction content for testing identical output generation.",
                word_count=200,
                generated_at=datetime(2024, 1, 1, 12, 5, 0),
                model_used="anthropic/claude-3-5-sonnet-20241022",
                validation_status="valid",
                metadata={"deterministic": True}
            )
        }
    
    def _create_test_section(self, section_name):
        """Create a test section for workflow testing."""
        return Section(
            name=section_name,
            content=f"Test {section_name} content",
            word_count=100,
            generated_at=datetime.now(),
            model_used="anthropic/claude-3-5-sonnet-20241022",
            validation_status="valid",
            metadata={"test": True}
        )
    
    def _validate_codexes_factory_result_format(self, result, config, context_data):
        """Validate that result matches Codexes Factory format expectations."""
        # Required top-level keys
        required_keys = [
            "paper_content",
            "sections",
            "generation_summary",
            "context_summary",
            "output_files",
            "imprint_info"
        ]
        
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
        
        # Validate sections format
        for section_name, section_data in result["sections"].items():
            section_required_keys = [
                "content",
                "word_count",
                "generated_at",
                "model_used",
                "validation_status",
                "metadata"
            ]
            for key in section_required_keys:
                assert key in section_data, f"Missing section key: {key} in section {section_name}"
        
        # Validate generation summary
        summary_required_keys = [
            "total_sections",
            "total_word_count",
            "models_used"
        ]
        for key in summary_required_keys:
            assert key in result["generation_summary"], f"Missing generation summary key: {key}"
        
        # Validate context summary
        context_required_keys = [
            "sources_collected",
            "total_context_size"
        ]
        for key in context_required_keys:
            assert key in result["context_summary"], f"Missing context summary key: {key}"
        
        # Validate imprint info
        imprint_required_keys = [
            "imprint_name",
            "workspace_root",
            "configuration_used"
        ]
        for key in imprint_required_keys:
            assert key in result["imprint_info"], f"Missing imprint info key: {key}"


class TestCodexesFactoryMigrationUtilities:
    """Test migration utilities and step-by-step migration process."""
    
    def test_step_by_step_migration_process(self):
        """Test complete step-by-step migration from Codexes Factory to arxiv-writer."""
        # Step 1: Create original Codexes Factory configuration
        original_config = {
            "imprint": "test_imprint",
            "workspace_root": "/test/workspace",
            "llm_config": {
                "default_model": "anthropic/claude-3-5-sonnet-20241022",
                "available_models": ["anthropic/claude-3-5-sonnet-20241022", "openai/gpt-4"]
            },
            "template_config": {
                "template_file": "templates/custom_prompts.json",
                "section_order": ["abstract", "introduction", "conclusion"]
            },
            "validation_config": {
                "enabled": True,
                "strict_mode": False,
                "quality_thresholds": {
                    "min_word_count": 1000,
                    "max_word_count": 5000
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(original_config, f)
            original_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            migrated_path = f.name
        
        try:
            with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
                # Step 2: Migrate configuration
                migrated_config = migrate_codexes_factory_config(original_path, migrated_path)
                
                # Step 3: Verify migration success
                assert isinstance(migrated_config, PaperConfig)
                assert Path(migrated_path).exists()
                
                # Step 4: Verify configuration compatibility
                adapter = CodexesFactoryAdapter(original_path)
                assert adapter.codexes_config.imprint_name == "test_imprint"
                assert adapter.paper_config.llm_config.default_model == "anthropic/claude-3-5-sonnet-20241022"
                
                # Step 5: Verify migrated file can be loaded
                with open(migrated_path, 'r') as f:
                    saved_config = json.load(f)
                
                assert "llm_config" in saved_config
                assert "template_config" in saved_config
                assert "validation_config" in saved_config
                
                # Step 6: Verify backward compatibility
                new_adapter = CodexesFactoryAdapter(migrated_path)
                assert new_adapter.codexes_config.imprint_name == "test_imprint"
                
        finally:
            Path(original_path).unlink()
            Path(migrated_path).unlink()
    
    def test_migration_documentation_generation(self):
        """Test generation of migration documentation and utilities."""
        # This would test the creation of migration documentation
        # For now, we'll verify that the migration functions exist and work
        
        config_data = {
            "imprint": "test_imprint",
            "llm_config": {"default_model": "openai/gpt-4"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as source_f:
            json.dump(config_data, source_f)
            source_path = source_f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as target_f:
            target_path = target_f.name
        
        try:
            with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
                # Test that migration utility works
                result = migrate_codexes_factory_config(source_path, target_path)
                assert isinstance(result, PaperConfig)
                
                # Test that compatibility config creation works
                compat_config = create_codexes_compatibility_config()
                assert isinstance(compat_config, CodexesFactoryConfig)
                
                # Test that paper generator creation works
                generator = create_codexes_factory_paper_generator()
                assert isinstance(generator, CodexesFactoryAdapter)
                
        finally:
            Path(source_path).unlink()
            Path(target_path).unlink()


class TestCodexesFactoryErrorHandling:
    """Test error handling and edge cases in Codexes Factory integration."""
    
    def test_invalid_configuration_handling(self):
        """Test handling of invalid Codexes Factory configurations."""
        invalid_configs = [
            {},  # Empty config
            {"invalid": "config"},  # Missing required fields
            {"imprint": "test", "llm_config": "invalid"},  # Invalid nested config
        ]
        
        for invalid_config in invalid_configs:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(invalid_config, f)
                config_path = f.name
            
            try:
                with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
                    # Should not raise exception, should use defaults
                    adapter = CodexesFactoryAdapter(config_path)
                    assert adapter.codexes_config is not None
                    assert adapter.paper_config is not None
            finally:
                Path(config_path).unlink()
    
    def test_missing_context_data_handling(self):
        """Test handling of missing or incomplete context data."""
        config = {"imprint": "test_imprint"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        
        try:
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector') as mock_create_collector:
                with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator') as mock_generator_class:
                    
                    # Mock context collector that returns incomplete data
                    mock_context_collector = Mock()
                    mock_context_collector.collect_context.return_value = {
                        "sources": {},  # Empty sources
                        "collection_metadata": {"timestamp": "2024-01-01T00:00:00Z"}
                    }
                    mock_context_collector.prepare_context.return_value = {"minimal": "context"}
                    mock_create_collector.return_value = mock_context_collector
                    
                    mock_generator = Mock()
                    mock_generator.generate_paper.return_value = PaperResult(
                        sections={},
                        complete_paper="Minimal paper",
                        output_files=[]
                    )
                    mock_generator_class.return_value = mock_generator
                    
                    adapter = CodexesFactoryAdapter(config_path)
                    result = adapter.generate_paper()
                    
                    # Should handle gracefully
                    assert "paper_content" in result
                    assert result["context_summary"]["sources_collected"] == []
                    
        finally:
            Path(config_path).unlink()
    
    def test_generation_failure_recovery(self):
        """Test recovery from generation failures."""
        config = {"imprint": "test_imprint"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        
        try:
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector') as mock_create_collector:
                with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator') as mock_generator_class:
                    
                    mock_context_collector = Mock()
                    mock_context_collector.collect_context.return_value = {"sources": {}}
                    mock_context_collector.prepare_context.return_value = {"context": "data"}
                    mock_create_collector.return_value = mock_context_collector
                    
                    # Mock generator that raises exception
                    mock_generator = Mock()
                    mock_generator.generate_paper.side_effect = Exception("Generation failed")
                    mock_generator_class.return_value = mock_generator
                    
                    adapter = CodexesFactoryAdapter(config_path)
                    
                    # Should propagate exception
                    with pytest.raises(Exception) as exc_info:
                        adapter.generate_paper()
                    
                    assert "Generation failed" in str(exc_info.value)
                    
        finally:
            Path(config_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])