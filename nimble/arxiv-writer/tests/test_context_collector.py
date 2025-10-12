"""
Tests for context collection system.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd

from src.arxiv_writer.core.context_collector import (
    ContextCollector,
    ContextConfig,
    FileDataSource,
    DirectoryDataSource,
    DictDataSource,
    CodexesFactoryDataSource,
    GenericCSVDataSource,
    GenericJSONDataSource,
    create_file_context_collector,
    create_directory_context_collector,
    create_codexes_factory_context_collector,
    create_csv_context_collector,
    create_json_context_collector
)
from src.arxiv_writer.core.exceptions import ValidationError


class TestContextConfig:
    """Test ContextConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ContextConfig()
        
        assert config.sources == []
        assert config.validation_enabled is True
        assert config.required_fields == []
        assert config.output_format == "dict"
        assert config.preprocessing_steps == []
    
    def test_custom_config(self):
        """Test custom configuration values."""
        sources = [{"name": "test", "type": "file"}]
        required_fields = ["field1", "field2"]
        preprocessing_steps = ["flatten_sources"]
        
        config = ContextConfig(
            sources=sources,
            validation_enabled=False,
            required_fields=required_fields,
            output_format="json",
            preprocessing_steps=preprocessing_steps
        )
        
        assert config.sources == sources
        assert config.validation_enabled is False
        assert config.required_fields == required_fields
        assert config.output_format == "json"
        assert config.preprocessing_steps == preprocessing_steps


class TestFileDataSource:
    """Test FileDataSource class."""
    
    def test_json_file_loading(self):
        """Test loading JSON files."""
        test_data = {"key": "value", "number": 42}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            source = FileDataSource({"path": temp_path})
            result = source.collect()
            
            assert result["key"] == "value"
            assert result["number"] == 42
            assert "source_file" in result
        finally:
            Path(temp_path).unlink()
    
    def test_csv_file_loading(self):
        """Test loading CSV files."""
        test_data = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "city": ["New York", "London", "Tokyo"]
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            source = FileDataSource({"path": temp_path})
            result = source.collect()
            
            assert "data" in result
            assert "statistics" in result
            assert result["statistics"]["row_count"] == 3
            assert result["statistics"]["column_count"] == 3
            assert "name" in result["statistics"]["columns"]
        finally:
            Path(temp_path).unlink()
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent files."""
        source = FileDataSource({"path": "/nonexistent/file.json"})
        result = source.collect()
        
        assert result == {}
    
    def test_validation_success(self):
        """Test successful validation."""
        source = FileDataSource({"name": "test_source"})
        data = {"field1": "value1", "field2": "value2"}
        
        result = source.validate(data)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.metrics["source"] == "test_source"
        assert result.metrics["fields_count"] == 2
    
    def test_validation_missing_required_fields(self):
        """Test validation with missing required fields."""
        source = FileDataSource({
            "name": "test_source",
            "required_fields": ["field1", "field2", "field3"]
        })
        data = {"field1": "value1"}
        
        result = source.validate(data)
        
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert "field2" in str(result.errors)
        assert "field3" in str(result.errors)


class TestDirectoryDataSource:
    """Test DirectoryDataSource class."""
    
    def test_directory_analysis(self):
        """Test directory structure analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "file1.txt").write_text("content1")
            (temp_path / "file2.json").write_text('{"key": "value"}')
            (temp_path / "subdir").mkdir()
            (temp_path / "subdir" / "file3.py").write_text("print('hello')")
            
            source = DirectoryDataSource({"path": str(temp_path)})
            result = source.collect()
            
            assert result["total_files"] == 3
            assert ".txt" in result["file_types"]
            assert ".json" in result["file_types"]
            assert ".py" in result["file_types"]
            assert "subdir" in result["subdirectories"]
            assert "analysis_timestamp" in result
    
    def test_nonexistent_directory(self):
        """Test handling of nonexistent directories."""
        source = DirectoryDataSource({"path": "/nonexistent/directory"})
        result = source.collect()
        
        assert result == {}


class TestDictDataSource:
    """Test DictDataSource class."""
    
    def test_dict_data_collection(self):
        """Test direct dictionary data collection."""
        test_data = {"key1": "value1", "key2": 42, "key3": [1, 2, 3]}
        source = DictDataSource({"data": test_data})
        
        result = source.collect()
        
        assert result == test_data
    
    def test_empty_dict_data(self):
        """Test empty dictionary data."""
        source = DictDataSource({})
        result = source.collect()
        
        assert result == {}


class TestContextCollector:
    """Test ContextCollector class."""
    
    def test_initialization(self):
        """Test context collector initialization."""
        sources = [
            {"name": "dict_source", "type": "dict", "data": {"key": "value"}},
            {"name": "disabled_source", "type": "dict", "enabled": False, "data": {"key": "value"}}
        ]
        config = ContextConfig(sources=sources)
        collector = ContextCollector(config)
        
        # Should only have one enabled source
        assert len(collector.sources) == 1
        assert collector.sources[0].name == "dict_source"
    
    def test_context_collection(self):
        """Test basic context collection."""
        sources = [
            {"name": "source1", "type": "dict", "data": {"field1": "value1"}},
            {"name": "source2", "type": "dict", "data": {"field2": "value2"}}
        ]
        config = ContextConfig(sources=sources, validation_enabled=False)
        collector = ContextCollector(config)
        
        context = collector.collect_context()
        
        assert "collection_metadata" in context
        assert "sources" in context
        assert "source1" in context["sources"]
        assert "source2" in context["sources"]
        assert context["sources"]["source1"]["field1"] == "value1"
        assert context["sources"]["source2"]["field2"] == "value2"
    
    def test_validation_enabled(self):
        """Test context collection with validation enabled."""
        sources = [
            {
                "name": "valid_source",
                "type": "dict",
                "data": {"field1": "value1"},
                "required_fields": ["field1"]
            }
        ]
        config = ContextConfig(sources=sources, validation_enabled=True)
        collector = ContextCollector(config)
        
        context = collector.collect_context()
        
        assert "validation_results" in context
        assert context["validation_results"]["valid_source"].is_valid is True
    
    def test_validation_failure(self):
        """Test context collection with validation failure."""
        sources = [
            {
                "name": "invalid_source",
                "type": "dict",
                "data": {"field1": "value1"},
                "required_fields": ["field1", "missing_field"]
            }
        ]
        config = ContextConfig(sources=sources, validation_enabled=True)
        collector = ContextCollector(config)
        
        with pytest.raises(ValidationError):
            collector.collect_context()
    
    def test_required_fields_validation(self):
        """Test required fields validation."""
        sources = [
            {"name": "source1", "type": "dict", "data": {"field1": "value1"}}
        ]
        config = ContextConfig(
            sources=sources,
            required_fields=["sources.source1.field1", "sources.source1.missing_field"]
        )
        collector = ContextCollector(config)
        
        with pytest.raises(ValidationError) as exc_info:
            collector.collect_context()
        
        assert "missing_field" in str(exc_info.value)
    
    def test_preprocessing_flatten_sources(self):
        """Test flatten_sources preprocessing step."""
        sources = [
            {"name": "source1", "type": "dict", "data": {"field1": "value1", "field2": "value2"}}
        ]
        config = ContextConfig(
            sources=sources,
            preprocessing_steps=["flatten_sources"],
            validation_enabled=False
        )
        collector = ContextCollector(config)
        
        context = collector.collect_context()
        
        assert "source1_field1" in context
        assert "source1_field2" in context
        assert context["source1_field1"] == "value1"
        assert context["source1_field2"] == "value2"
    
    def test_preprocessing_merge_statistics(self):
        """Test merge_statistics preprocessing step."""
        sources = [
            {
                "name": "source1",
                "type": "dict",
                "data": {"statistics": {"count": 10, "mean": 5.5}}
            }
        ]
        config = ContextConfig(
            sources=sources,
            preprocessing_steps=["merge_statistics"],
            validation_enabled=False
        )
        collector = ContextCollector(config)
        
        context = collector.collect_context()
        
        assert "merged_statistics" in context
        assert "source1" in context["merged_statistics"]
        assert context["merged_statistics"]["source1"]["count"] == 10
    
    def test_prepare_context(self):
        """Test context preparation for template rendering."""
        raw_context = {
            "sources": {
                "source1": {"field1": "value1", "field2": "value2"},
                "source2": {"field3": "value3"}
            }
        }
        
        config = ContextConfig()
        collector = ContextCollector(config)
        
        prepared = collector.prepare_context(
            raw_context,
            template_variables=["source1.field1", "source2.field3", "missing_var"]
        )
        
        assert "generation_metadata" in prepared
        assert "source1" in prepared
        assert "source2" in prepared
        assert "context_summary" in prepared
        assert "missing_template_variables" in prepared
        assert "missing_var" in prepared["missing_template_variables"]
    
    def test_field_exists_in_context(self):
        """Test field existence checking with dot notation."""
        config = ContextConfig()
        collector = ContextCollector(config)
        
        context = {
            "level1": {
                "level2": {
                    "field": "value"
                }
            }
        }
        
        assert collector._field_exists_in_context(context, "level1.level2.field") is True
        assert collector._field_exists_in_context(context, "level1.level2.missing") is False
        assert collector._field_exists_in_context(context, "missing.field") is False
    
    def test_additional_sources(self):
        """Test adding additional sources during collection."""
        sources = [
            {"name": "source1", "type": "dict", "data": {"field1": "value1"}}
        ]
        config = ContextConfig(sources=sources, validation_enabled=False)
        collector = ContextCollector(config)
        
        additional_sources = [
            {"name": "additional_source", "type": "dict", "data": {"field2": "value2"}}
        ]
        
        context = collector.collect_context(additional_sources=additional_sources)
        
        assert "source1" in context["sources"]
        assert "additional_source" in context["sources"]
        assert context["sources"]["additional_source"]["field2"] == "value2"


class TestCodexesFactoryDataSource:
    """Test CodexesFactoryDataSource class."""
    
    def test_collect_with_missing_workspace(self):
        """Test collection with missing workspace."""
        source = CodexesFactoryDataSource({
            "workspace_root": "/nonexistent/workspace",
            "collection_type": "technical_architecture"
        })
        
        result = source.collect()
        
        assert "technical_architecture_error" in result
        assert result["technical_architecture_error"] == "Source directory not found"
    
    def test_collect_performance_metrics(self):
        """Test performance metrics collection."""
        source = CodexesFactoryDataSource({
            "collection_type": "performance_metrics"
        })
        
        result = source.collect()
        
        assert "processing_efficiency_metrics" in result
        assert "quality_assessment_scores" in result
        assert "production_metrics" in result
        assert result["processing_efficiency_metrics"]["automation_rate"] == "85%"
    
    def test_unknown_collection_type(self):
        """Test handling of unknown collection type."""
        source = CodexesFactoryDataSource({
            "collection_type": "unknown_type"
        })
        
        result = source.collect()
        
        assert result == {}


class TestGenericCSVDataSource:
    """Test GenericCSVDataSource class."""
    
    def test_enhanced_csv_analysis(self):
        """Test enhanced CSV analysis features."""
        test_data = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie", "Alice"],
            "age": [25, 30, 35, 26],
            "salary": [50000, 60000, 70000, 52000],
            "department": ["Engineering", "Sales", "Engineering", "Marketing"],
            "hire_date": ["2020-01-15", "2019-06-20", "2018-03-10", "2021-09-05"]
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            source = GenericCSVDataSource({
                "path": temp_path,
                "analysis": {
                    "include_numeric_stats": True,
                    "include_categorical_stats": True,
                    "include_date_analysis": True,
                    "date_columns": ["hire_date"],
                    "aggregations": {
                        "avg_salary_by_dept": {
                            "column": "salary",
                            "operation": "mean",
                            "group_by": "department"
                        },
                        "total_salary": {
                            "column": "salary",
                            "operation": "sum"
                        }
                    }
                }
            })
            
            result = source.collect()
            
            # Check basic statistics
            assert result["basic_statistics"]["row_count"] == 4
            assert result["basic_statistics"]["column_count"] == 5
            
            # Check numeric statistics
            assert "numeric_statistics" in result
            assert "age" in result["numeric_statistics"]
            assert "salary" in result["numeric_statistics"]
            
            # Check categorical statistics
            assert "categorical_statistics" in result
            assert "name" in result["categorical_statistics"]
            assert result["categorical_statistics"]["name"]["unique_count"] == 3
            
            # Check date statistics
            assert "date_statistics" in result
            assert "hire_date" in result["date_statistics"]
            
            # Check custom aggregations
            assert "custom_aggregations" in result
            assert "avg_salary_by_dept" in result["custom_aggregations"]
            assert "total_salary" in result["custom_aggregations"]
            assert result["custom_aggregations"]["total_salary"] == 232000
            
        finally:
            Path(temp_path).unlink()
    
    def test_csv_with_minimal_analysis(self):
        """Test CSV with minimal analysis configuration."""
        test_data = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            source = GenericCSVDataSource({
                "path": temp_path,
                "analysis": {
                    "include_numeric_stats": False,
                    "include_categorical_stats": False,
                    "include_date_analysis": False
                }
            })
            
            result = source.collect()
            
            assert "basic_statistics" in result
            assert "numeric_statistics" not in result
            assert "categorical_statistics" not in result
            assert "date_statistics" not in result
            
        finally:
            Path(temp_path).unlink()


class TestGenericJSONDataSource:
    """Test GenericJSONDataSource class."""
    
    def test_dict_json_processing(self):
        """Test processing of dictionary JSON data."""
        test_data = {
            "config": {
                "name": "test_config",
                "settings": {
                    "enabled": True,
                    "timeout": 30
                }
            },
            "users": [
                {"name": "Alice", "role": "admin"},
                {"name": "Bob", "role": "user"}
            ],
            "version": "1.0.0"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            source = GenericJSONDataSource({
                "path": temp_path,
                "processing": {
                    "analyze_structure": True,
                    "extract_paths": ["config.name", "version", "users"]
                }
            })
            
            result = source.collect()
            
            assert result["data"] == test_data
            assert result["key_count"] == 3
            assert "config" in result["keys"]
            assert "users" in result["keys"]
            assert "version" in result["keys"]
            
            # Check structure analysis
            assert "structure_analysis" in result
            assert "config" in result["structure_analysis"]
            
            # Check extracted values
            assert "extracted_values" in result
            assert result["extracted_values"]["config.name"] == "test_config"
            assert result["extracted_values"]["version"] == "1.0.0"
            assert len(result["extracted_values"]["users"]) == 2
            
        finally:
            Path(temp_path).unlink()
    
    def test_list_json_processing(self):
        """Test processing of list JSON data."""
        test_data = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            source = GenericJSONDataSource({
                "path": temp_path,
                "processing": {
                    "analyze_list_items": True
                }
            })
            
            result = source.collect()
            
            assert result["data"] == test_data
            assert result["item_count"] == 3
            assert "sample_items" in result
            assert len(result["sample_items"]) == 3
            assert "item_types" in result
            assert all(item_type == "dict" for item_type in result["item_types"])
            
        finally:
            Path(temp_path).unlink()
    
    def test_extract_nested_value(self):
        """Test nested value extraction."""
        source = GenericJSONDataSource({})
        
        data = {
            "level1": {
                "level2": {
                    "level3": "target_value"
                }
            }
        }
        
        # Test successful extraction
        result = source._extract_nested_value(data, "level1.level2.level3")
        assert result == "target_value"
        
        # Test missing path
        with pytest.raises(KeyError):
            source._extract_nested_value(data, "level1.missing.level3")


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_file_context_collector(self):
        """Test file context collector creation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_path = f.name
        
        try:
            collector = create_file_context_collector([temp_path])
            
            assert len(collector.sources) == 1
            assert collector.sources[0].name.startswith("file_0_")
            assert collector.sources[0].config["type"] == "file"
            assert collector.sources[0].config["path"] == temp_path
        finally:
            Path(temp_path).unlink()
    
    def test_create_directory_context_collector(self):
        """Test directory context collector creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            collector = create_directory_context_collector([temp_dir])
            
            assert len(collector.sources) == 1
            assert collector.sources[0].name.startswith("directory_0_")
            assert collector.sources[0].config["type"] == "directory"
            assert collector.sources[0].config["path"] == temp_dir
    
    def test_create_codexes_factory_context_collector(self):
        """Test Codexes Factory context collector creation."""
        collector = create_codexes_factory_context_collector(
            workspace_root="/test/workspace",
            collection_types=["xynapse_traces", "performance_metrics"]
        )
        
        assert len(collector.sources) == 2
        assert collector.sources[0].name == "codexes_factory_xynapse_traces"
        assert collector.sources[1].name == "codexes_factory_performance_metrics"
        assert collector.sources[0].config["type"] == "codexes_factory"
        assert collector.sources[0].config["workspace_root"] == "/test/workspace"
    
    def test_create_csv_context_collector(self):
        """Test CSV context collector creation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]}).to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            collector = create_csv_context_collector(
                [temp_path],
                analysis_config={"include_numeric_stats": True}
            )
            
            assert len(collector.sources) == 1
            assert collector.sources[0].config["type"] == "csv"
            assert collector.sources[0].config["analysis"]["include_numeric_stats"] is True
        finally:
            Path(temp_path).unlink()
    
    def test_create_json_context_collector(self):
        """Test JSON context collector creation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_path = f.name
        
        try:
            collector = create_json_context_collector(
                [temp_path],
                processing_config={"analyze_structure": True}
            )
            
            assert len(collector.sources) == 1
            assert collector.sources[0].config["type"] == "json"
            assert collector.sources[0].config["processing"]["analyze_structure"] is True
        finally:
            Path(temp_path).unlink()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_source_type(self):
        """Test handling of invalid source types."""
        sources = [
            {"name": "invalid_source", "type": "invalid_type", "data": {"field": "value"}}
        ]
        config = ContextConfig(sources=sources)
        collector = ContextCollector(config)
        
        # Should have no sources due to invalid type
        assert len(collector.sources) == 0
    
    def test_enhanced_source_types(self):
        """Test that enhanced source types are recognized."""
        sources = [
            {"name": "csv_source", "type": "csv", "path": "/test.csv"},
            {"name": "json_source", "type": "json", "path": "/test.json"},
            {"name": "codexes_source", "type": "codexes_factory", "workspace_root": "/test"}
        ]
        config = ContextConfig(sources=sources)
        collector = ContextCollector(config)
        
        # All sources should be recognized (though they may fail to collect due to missing files)
        assert len(collector.sources) == 3
        assert any(source.name == "csv_source" for source in collector.sources)
        assert any(source.name == "json_source" for source in collector.sources)
        assert any(source.name == "codexes_source" for source in collector.sources)
    
    def test_source_collection_error(self):
        """Test handling of source collection errors."""
        # Mock a source that raises an exception
        mock_source = Mock()
        mock_source.name = "error_source"
        mock_source.enabled = True
        mock_source.collect.side_effect = Exception("Collection error")
        
        config = ContextConfig(validation_enabled=False)
        collector = ContextCollector(config)
        collector.sources = [mock_source]
        
        context = collector.collect_context()
        
        assert "error_source" in context["sources"]
        assert "error" in context["sources"]["error_source"]
        assert "Collection error" in context["sources"]["error_source"]["error"]
    
    def test_invalid_data_validation(self):
        """Test validation with invalid data types."""
        source = FileDataSource({"name": "test_source"})
        
        # Test with non-dict data
        result = source.validate("not a dict")
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "must be a dictionary" in result.errors[0]


if __name__ == "__main__":
    pytest.main([__file__])