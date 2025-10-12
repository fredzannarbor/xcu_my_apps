"""
Tests for Codexes Factory compatibility layer.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.arxiv_writer.core.codexes_factory_adapter import (
    CodexesFactoryAdapter,
    CodexesFactoryConfig,
    migrate_codexes_factory_config,
    create_codexes_compatibility_config,
    create_codexes_factory_paper_generator
)
from src.arxiv_writer.core.models import PaperConfig, Section, PaperResult, GenerationSummary
from src.arxiv_writer.core.exceptions import ConfigurationError


class TestCodexesFactoryConfig:
    """Test CodexesFactoryConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CodexesFactoryConfig()
        
        assert config.workspace_root == "."
        assert config.imprint_name == "xynapse_traces"
        assert config.output_directory == "output"
        assert config.default_model == "anthropic/claude-3-5-sonnet-20241022"
        assert len(config.available_models) == 4
        assert config.validation_enabled is True
        assert config.collect_book_catalog is True
    
    def test_from_dict(self):
        """Test configuration creation from dictionary."""
        data = {
            "workspace_root": "/test/workspace",
            "imprint": "test_imprint",
            "output_directory": "/test/output",
            "llm_config": {
                "default_model": "openai/gpt-4",
                "available_models": ["openai/gpt-4", "anthropic/claude-3"]
            },
            "template_config": {
                "template_file": "custom_templates.json",
                "section_order": ["abstract", "introduction", "conclusion"]
            },
            "validation_config": {
                "enabled": False,
                "strict_mode": True,
                "quality_thresholds": {"min_word_count": 1000}
            },
            "context_config": {
                "collect_book_catalog": False,
                "collect_performance_metrics": True
            }
        }
        
        config = CodexesFactoryConfig.from_dict(data)
        
        assert config.workspace_root == "/test/workspace"
        assert config.imprint_name == "test_imprint"
        assert config.output_directory == "/test/output"
        assert config.default_model == "openai/gpt-4"
        assert len(config.available_models) == 2
        assert config.template_file == "custom_templates.json"
        assert len(config.section_order) == 3
        assert config.validation_enabled is False
        assert config.strict_mode is True
        assert config.quality_thresholds["min_word_count"] == 1000
        assert config.collect_book_catalog is False
        assert config.collect_performance_metrics is True
    
    def test_from_file(self):
        """Test configuration loading from file."""
        config_data = {
            "workspace_root": "/test/workspace",
            "imprint": "test_imprint",
            "llm_config": {
                "default_model": "openai/gpt-4"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = CodexesFactoryConfig.from_file(temp_path)
            
            assert config.workspace_root == "/test/workspace"
            assert config.imprint_name == "test_imprint"
            assert config.default_model == "openai/gpt-4"
        finally:
            Path(temp_path).unlink()
    
    def test_from_file_not_found(self):
        """Test handling of missing configuration file."""
        with pytest.raises(ConfigurationError):
            CodexesFactoryConfig.from_file("/nonexistent/config.json")
    
    def test_to_dict(self):
        """Test configuration conversion to dictionary."""
        config = CodexesFactoryConfig(
            workspace_root="/test",
            imprint_name="test_imprint",
            default_model="openai/gpt-4"
        )
        
        result = config.to_dict()
        
        assert result["workspace_root"] == "/test"
        assert result["imprint"] == "test_imprint"
        assert result["llm_config"]["default_model"] == "openai/gpt-4"
        assert "template_config" in result
        assert "validation_config" in result
        assert "context_config" in result


class TestCodexesFactoryAdapter:
    """Test CodexesFactoryAdapter class."""
    
    def test_initialization_with_config_object(self):
        """Test adapter initialization with CodexesFactoryConfig object."""
        config = CodexesFactoryConfig(
            workspace_root="/test",
            imprint_name="test_imprint"
        )
        
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
            adapter = CodexesFactoryAdapter(config)
            
            assert adapter.codexes_config == config
            assert adapter.paper_config is not None
            assert adapter.context_collector is not None
    
    def test_initialization_with_dict(self):
        """Test adapter initialization with dictionary configuration."""
        config_dict = {
            "workspace_root": "/test",
            "imprint": "test_imprint",
            "llm_config": {
                "default_model": "openai/gpt-4"
            }
        }
        
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
            adapter = CodexesFactoryAdapter(config_dict)
            
            assert adapter.codexes_config.workspace_root == "/test"
            assert adapter.codexes_config.imprint_name == "test_imprint"
            assert adapter.codexes_config.default_model == "openai/gpt-4"
    
    def test_initialization_with_file_path(self):
        """Test adapter initialization with file path."""
        config_data = {
            "workspace_root": "/test",
            "imprint": "test_imprint"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
                adapter = CodexesFactoryAdapter(temp_path)
                
                assert adapter.codexes_config.workspace_root == "/test"
                assert adapter.codexes_config.imprint_name == "test_imprint"
        finally:
            Path(temp_path).unlink()
    
    def test_invalid_config_type(self):
        """Test handling of invalid configuration type."""
        with pytest.raises(ConfigurationError):
            CodexesFactoryAdapter(123)  # Invalid type
    
    def test_convert_to_paper_config(self):
        """Test conversion to PaperConfig."""
        codexes_config = CodexesFactoryConfig(
            workspace_root="/test",
            imprint_name="test_imprint",
            default_model="openai/gpt-4",
            available_models=["openai/gpt-4", "anthropic/claude-3"],
            template_file="custom_templates.json",
            section_order=["abstract", "introduction"],
            validation_enabled=True,
            strict_mode=False,
            quality_thresholds={"min_word_count": 500}
        )
        
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
            adapter = CodexesFactoryAdapter(codexes_config)
            paper_config = adapter.paper_config
            
            assert paper_config.output_directory == codexes_config.output_directory
            assert paper_config.llm_config.default_model == "openai/gpt-4"
            assert len(paper_config.llm_config.available_models) == 2
            assert paper_config.template_config.template_file == "custom_templates.json"
            assert len(paper_config.template_config.section_order) == 2
            assert paper_config.validation_config.enabled is True
            assert paper_config.validation_config.strict_mode is False
            assert paper_config.validation_config.quality_thresholds["min_word_count"] == 500
    
    @patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector')
    def test_create_context_collector_all_enabled(self, mock_create_collector):
        """Test context collector creation with all collection types enabled."""
        config = CodexesFactoryConfig(
            collect_book_catalog=True,
            collect_imprint_config=True,
            collect_technical_architecture=True,
            collect_performance_metrics=True
        )
        
        mock_collector = Mock()
        mock_create_collector.return_value = mock_collector
        
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
            adapter = CodexesFactoryAdapter(config)
            
            # Should use comprehensive xynapse_traces collection when all are enabled
            mock_create_collector.assert_called_once_with(
                workspace_root=config.workspace_root,
                collection_types=["xynapse_traces"],
                validation_enabled=config.validation_enabled
            )
    
    @patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector')
    def test_create_context_collector_selective(self, mock_create_collector):
        """Test context collector creation with selective collection types."""
        config = CodexesFactoryConfig(
            collect_book_catalog=True,
            collect_imprint_config=False,
            collect_technical_architecture=True,
            collect_performance_metrics=False
        )
        
        mock_collector = Mock()
        mock_create_collector.return_value = mock_collector
        
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
            adapter = CodexesFactoryAdapter(config)
            
            # Should use individual collection types
            mock_create_collector.assert_called_once_with(
                workspace_root=config.workspace_root,
                collection_types=["book_catalog", "technical_architecture"],
                validation_enabled=config.validation_enabled
            )
    
    def test_generate_paper(self):
        """Test paper generation workflow."""
        config = CodexesFactoryConfig()
        
        # Mock context collector
        mock_context_collector = Mock()
        mock_context_data = {
            "sources": {
                "test_source": {"data": "test_data"}
            },
            "collection_metadata": {"timestamp": "2024-01-01T00:00:00"}
        }
        mock_prepared_context = {"prepared": "context"}
        mock_context_collector.collect_context.return_value = mock_context_data
        mock_context_collector.prepare_context.return_value = mock_prepared_context
        
        # Mock paper generator
        mock_paper_generator = Mock()
        mock_section = Section(
            name="abstract",
            content="Test abstract content",
            word_count=50,
            generated_at=datetime.now(),
            model_used="openai/gpt-4",
            validation_status="valid",
            metadata={"test": "metadata"}
        )
        mock_paper_result = PaperResult(
            sections={"abstract": mock_section},
            complete_paper="Complete paper content",
            generation_summary=GenerationSummary(
                total_sections=1,
                successful_sections=1,
                failed_sections=0,
                total_time=10.0,
                total_word_count=50,
                llm_calls=1
            ),
            output_files=["paper.tex"]
        )
        mock_paper_generator.generate_paper.return_value = mock_paper_result
        
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator', return_value=mock_paper_generator):
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector', return_value=mock_context_collector):
                adapter = CodexesFactoryAdapter(config)
                
                result = adapter.generate_paper()
                
                # Verify calls
                mock_context_collector.collect_context.assert_called_once()
                mock_context_collector.prepare_context.assert_called_once_with(mock_context_data)
                mock_paper_generator.generate_paper.assert_called_once_with(mock_prepared_context)
                
                # Verify result format
                assert "paper_content" in result
                assert "sections" in result
                assert "generation_summary" in result
                assert "context_summary" in result
                assert "output_files" in result
                assert "imprint_info" in result
                
                assert result["paper_content"] == "Complete paper content"
                assert "abstract" in result["sections"]
                assert result["sections"]["abstract"]["content"] == "Test abstract content"
                assert result["imprint_info"]["imprint_name"] == config.imprint_name
    
    def test_generate_paper_with_additional_context(self):
        """Test paper generation with additional context."""
        config = CodexesFactoryConfig()
        additional_context = {"additional": "data"}
        
        # Mock context collector
        mock_context_collector = Mock()
        mock_context_data = {"sources": {"test": "data"}}
        mock_context_collector.collect_context.return_value = mock_context_data
        mock_context_collector.prepare_context.return_value = {"prepared": "context"}
        
        # Mock paper generator
        mock_paper_generator = Mock()
        mock_paper_result = PaperResult(
            sections={},
            complete_paper="Test paper",
            output_files=[]
        )
        mock_paper_generator.generate_paper.return_value = mock_paper_result
        
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator', return_value=mock_paper_generator):
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector', return_value=mock_context_collector):
                adapter = CodexesFactoryAdapter(config)
                
                result = adapter.generate_paper(additional_context)
                
                # Verify that additional context was merged
                expected_context = {**mock_context_data, **additional_context}
                mock_context_collector.prepare_context.assert_called_once_with(expected_context)
    
    def test_generate_section(self):
        """Test individual section generation."""
        config = CodexesFactoryConfig()
        section_name = "abstract"
        
        # Mock context collector
        mock_context_collector = Mock()
        mock_context_data = {"sources": {"test": "data"}}
        mock_context_collector.collect_context.return_value = mock_context_data
        mock_context_collector.prepare_context.return_value = {"prepared": "context"}
        
        # Mock paper generator
        mock_paper_generator = Mock()
        mock_section_result = Section(
            name=section_name,
            content="Test section content",
            word_count=100,
            generated_at=datetime.now(),
            model_used="openai/gpt-4",
            validation_status="valid",
            metadata={"test": "metadata"}
        )
        mock_paper_generator.generate_section.return_value = mock_section_result
        
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator', return_value=mock_paper_generator):
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector', return_value=mock_context_collector):
                adapter = CodexesFactoryAdapter(config)
                
                result = adapter.generate_section(section_name)
                
                # Verify calls
                mock_paper_generator.generate_section.assert_called_once_with(section_name, {"prepared": "context"})
                
                # Verify result format
                assert result["section_name"] == section_name
                assert result["content"] == "Test section content"
                assert result["word_count"] == 100
                assert result["model_used"] == "openai/gpt-4"
                assert result["validation_status"] == "valid"
                assert "context_summary" in result
    
    def test_validate_paper(self):
        """Test paper validation."""
        config = CodexesFactoryConfig()
        paper_content = "Test paper content"
        
        # Mock paper generator
        mock_paper_generator = Mock()
        mock_validation_result = Mock()
        mock_validation_result.is_valid = True
        mock_validation_result.errors = []
        mock_validation_result.warnings = ["Minor warning"]
        mock_validation_result.metrics = {"word_count": 1000}
        mock_paper_generator.validate_paper.return_value = mock_validation_result
        
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator', return_value=mock_paper_generator):
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector'):
                adapter = CodexesFactoryAdapter(config)
                
                result = adapter.validate_paper(paper_content)
                
                # Verify call
                mock_paper_generator.validate_paper.assert_called_once_with(paper_content)
                
                # Verify result format
                assert result["is_valid"] is True
                assert result["errors"] == []
                assert result["warnings"] == ["Minor warning"]
                assert result["quality_metrics"] == {"word_count": 1000}
                assert "arxiv_compliance" in result
                assert result["arxiv_compliance"]["meets_standards"] is True
                assert result["arxiv_compliance"]["submission_ready"] is True
    
    def test_get_context_data(self):
        """Test context data collection."""
        config = CodexesFactoryConfig()
        
        # Mock context collector
        mock_context_collector = Mock()
        mock_context_data = {
            "sources": {
                "source1": {"data": "value1"},
                "source2": {"error": "Failed to collect"}
            },
            "collection_metadata": {"timestamp": "2024-01-01T00:00:00"},
            "validation_results": {"source1": "valid"}
        }
        mock_context_collector.collect_context.return_value = mock_context_data
        
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector', return_value=mock_context_collector):
                adapter = CodexesFactoryAdapter(config)
                
                result = adapter.get_context_data()
                
                # Verify result format
                assert "imprint_data" in result
                assert "collection_metadata" in result
                assert "validation_results" in result
                assert "summary" in result
                
                assert result["imprint_data"] == mock_context_data["sources"]
                assert result["summary"]["total_sources"] == 2
                assert result["summary"]["successful_collections"] == 1
                assert result["summary"]["failed_collections"] == 1


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_migrate_codexes_factory_config(self):
        """Test configuration migration."""
        # Create source configuration
        source_config = {
            "workspace_root": "/test",
            "imprint": "test_imprint",
            "llm_config": {
                "default_model": "openai/gpt-4"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as source_file:
            json.dump(source_config, source_file)
            source_path = source_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as target_file:
            target_path = target_file.name
        
        try:
            with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
                paper_config = migrate_codexes_factory_config(source_path, target_path)
                
                # Verify conversion
                assert paper_config.output_directory == "output"
                assert paper_config.llm_config.default_model == "openai/gpt-4"
                
                # Verify file was created
                assert Path(target_path).exists()
                
                # Verify file content
                with open(target_path, 'r') as f:
                    saved_config = json.load(f)
                assert "llm_config" in saved_config
                assert saved_config["llm_config"]["default_model"] == "openai/gpt-4"
        finally:
            Path(source_path).unlink()
            Path(target_path).unlink()
    
    def test_create_codexes_compatibility_config(self):
        """Test compatibility configuration creation."""
        config = create_codexes_compatibility_config(
            workspace_root="/test/workspace",
            imprint_name="test_imprint"
        )
        
        assert config.workspace_root == "/test/workspace"
        assert config.imprint_name == "test_imprint"
        assert config.default_model == "anthropic/claude-3-5-sonnet-20241022"
        assert len(config.available_models) == 4
        assert config.collect_book_catalog is True
        assert config.collect_imprint_config is True
        assert config.collect_technical_architecture is True
        assert config.collect_performance_metrics is True
        assert config.validation_enabled is True
        assert "citation_count" in config.quality_thresholds
    
    def test_create_codexes_factory_paper_generator_with_config(self):
        """Test paper generator creation with existing configuration."""
        config_data = {
            "workspace_root": "/test",
            "imprint": "test_imprint"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
                generator = create_codexes_factory_paper_generator(config_path=temp_path)
                
                assert isinstance(generator, CodexesFactoryAdapter)
                assert generator.codexes_config.workspace_root == "/test"
                assert generator.codexes_config.imprint_name == "test_imprint"
        finally:
            Path(temp_path).unlink()
    
    def test_create_codexes_factory_paper_generator_without_config(self):
        """Test paper generator creation without existing configuration."""
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
            generator = create_codexes_factory_paper_generator(
                workspace_root="/test/workspace",
                imprint_name="test_imprint"
            )
            
            assert isinstance(generator, CodexesFactoryAdapter)
            assert generator.codexes_config.workspace_root == "/test/workspace"
            assert generator.codexes_config.imprint_name == "test_imprint"


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_generate_paper_error(self):
        """Test error handling during paper generation."""
        config = CodexesFactoryConfig()
        
        # Mock context collector to raise exception
        mock_context_collector = Mock()
        mock_context_collector.collect_context.side_effect = Exception("Collection failed")
        
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator'):
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector', return_value=mock_context_collector):
                adapter = CodexesFactoryAdapter(config)
                
                with pytest.raises(Exception) as exc_info:
                    adapter.generate_paper()
                
                assert "Collection failed" in str(exc_info.value)
    
    def test_generate_section_error(self):
        """Test error handling during section generation."""
        config = CodexesFactoryConfig()
        
        # Mock paper generator to raise exception
        mock_paper_generator = Mock()
        mock_paper_generator.generate_section.side_effect = Exception("Section generation failed")
        
        mock_context_collector = Mock()
        mock_context_collector.collect_context.return_value = {"sources": {}}
        mock_context_collector.prepare_context.return_value = {"prepared": "context"}
        
        with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator', return_value=mock_paper_generator):
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector', return_value=mock_context_collector):
                adapter = CodexesFactoryAdapter(config)
                
                with pytest.raises(Exception) as exc_info:
                    adapter.generate_section("abstract")
                
                assert "Section generation failed" in str(exc_info.value)
    
    def test_migration_error(self):
        """Test error handling during configuration migration."""
        with pytest.raises(ConfigurationError):
            migrate_codexes_factory_config("/nonexistent/config.json", "/output/config.json")


if __name__ == "__main__":
    pytest.main([__file__])