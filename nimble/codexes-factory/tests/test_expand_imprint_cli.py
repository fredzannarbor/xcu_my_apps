"""
Unit tests for enhanced expand_imprint_cli.py
"""

import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace

# Add tools to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import CLI functions
from expand_imprint_cli import (
    validate_arguments,
    parse_column_mapping,
    parse_list_argument,
    create_batch_config
)
from codexes.modules.imprint_builder.batch_models import (
    NamingStrategy,
    OrganizationStrategy,
    ErrorHandlingMode
)


class TestArgumentValidation:
    """Test command line argument validation."""
    
    def test_validate_single_file_mode_valid(self):
        """Test valid single file mode arguments."""
        args = Namespace(
            input_file=Path("input.txt"),
            output_file=Path("output.json"),
            csv=None,
            directory=None,
            output_dir=None,
            column_mapping=None,
            max_workers=4,
            max_errors=100
        )
        
        errors = validate_arguments(args)
        assert len(errors) == 0
    
    def test_validate_single_file_mode_missing_output(self):
        """Test single file mode missing output file."""
        args = Namespace(
            input_file=Path("input.txt"),
            output_file=None,
            csv=None,
            directory=None,
            output_dir=None,
            column_mapping=None,
            max_workers=4,
            max_errors=100
        )
        
        errors = validate_arguments(args)
        assert any("requires --output-file" in error for error in errors)
    
    def test_validate_single_file_mode_with_output_dir(self):
        """Test single file mode with invalid output-dir."""
        args = Namespace(
            input_file=Path("input.txt"),
            output_file=Path("output.json"),
            csv=None,
            directory=None,
            output_dir=Path("output/"),
            column_mapping=None,
            max_workers=4,
            max_errors=100
        )
        
        errors = validate_arguments(args)
        assert any("cannot use --output-dir" in error for error in errors)
    
    def test_validate_csv_mode_valid(self):
        """Test valid CSV batch mode arguments."""
        args = Namespace(
            input_file=None,
            output_file=None,
            csv=Path("input.csv"),
            directory=None,
            output_dir=Path("output/"),
            column_mapping="concept:imprint_concept",
            max_workers=4,
            max_errors=100
        )
        
        errors = validate_arguments(args)
        assert len(errors) == 0
    
    def test_validate_csv_mode_missing_output_dir(self):
        """Test CSV mode missing output directory."""
        args = Namespace(
            input_file=None,
            output_file=None,
            csv=Path("input.csv"),
            directory=None,
            output_dir=None,
            column_mapping=None,
            max_workers=4,
            max_errors=100
        )
        
        errors = validate_arguments(args)
        assert any("requires --output-dir" in error for error in errors)
    
    def test_validate_directory_mode_valid(self):
        """Test valid directory batch mode arguments."""
        args = Namespace(
            input_file=None,
            output_file=None,
            csv=None,
            directory=Path("csv_files/"),
            output_dir=Path("output/"),
            column_mapping=None,
            max_workers=4,
            max_errors=100
        )
        
        errors = validate_arguments(args)
        assert len(errors) == 0
    
    def test_validate_invalid_column_mapping(self):
        """Test invalid column mapping format."""
        args = Namespace(
            input_file=None,
            output_file=None,
            csv=Path("input.csv"),
            directory=None,
            output_dir=Path("output/"),
            column_mapping="invalid_format",
            max_workers=4,
            max_errors=100
        )
        
        errors = validate_arguments(args)
        assert any("Invalid column mapping" in error for error in errors)
    
    def test_validate_invalid_max_workers(self):
        """Test invalid max workers value."""
        args = Namespace(
            input_file=Path("input.txt"),
            output_file=Path("output.json"),
            csv=None,
            directory=None,
            output_dir=None,
            column_mapping=None,
            max_workers=0,
            max_errors=100
        )
        
        errors = validate_arguments(args)
        assert any("max-workers must be at least 1" in error for error in errors)
    
    def test_validate_invalid_max_errors(self):
        """Test invalid max errors value."""
        args = Namespace(
            input_file=Path("input.txt"),
            output_file=Path("output.json"),
            csv=None,
            directory=None,
            output_dir=None,
            column_mapping=None,
            max_workers=4,
            max_errors=0
        )
        
        errors = validate_arguments(args)
        assert any("max-errors must be at least 1" in error for error in errors)


class TestColumnMappingParsing:
    """Test column mapping parsing functionality."""
    
    def test_parse_column_mapping_valid(self):
        """Test parsing valid column mapping."""
        mapping_str = "concept:imprint_concept,name:imprint_name"
        result = parse_column_mapping(mapping_str)
        
        expected = {
            "concept": "imprint_concept",
            "name": "imprint_name"
        }
        assert result == expected
    
    def test_parse_column_mapping_single(self):
        """Test parsing single column mapping."""
        mapping_str = "concept:imprint_concept"
        result = parse_column_mapping(mapping_str)
        
        expected = {"concept": "imprint_concept"}
        assert result == expected
    
    def test_parse_column_mapping_empty(self):
        """Test parsing empty column mapping."""
        result = parse_column_mapping("")
        assert result == {}
        
        result = parse_column_mapping(None)
        assert result == {}
    
    def test_parse_column_mapping_invalid_format(self):
        """Test parsing invalid column mapping format."""
        with pytest.raises(ValueError, match="Invalid mapping format"):
            parse_column_mapping("invalid_format")
    
    def test_parse_column_mapping_missing_colon(self):
        """Test parsing column mapping without colon."""
        with pytest.raises(ValueError, match="Invalid mapping format"):
            parse_column_mapping("concept_imprint_concept")
    
    def test_parse_column_mapping_empty_parts(self):
        """Test parsing column mapping with empty parts."""
        with pytest.raises(ValueError, match="Empty source or target"):
            parse_column_mapping(":imprint_concept")
        
        with pytest.raises(ValueError, match="Empty source or target"):
            parse_column_mapping("concept:")
    
    def test_parse_column_mapping_whitespace(self):
        """Test parsing column mapping with whitespace."""
        mapping_str = " concept : imprint_concept , name : imprint_name "
        result = parse_column_mapping(mapping_str)
        
        expected = {
            "concept": "imprint_concept",
            "name": "imprint_name"
        }
        assert result == expected


class TestListArgumentParsing:
    """Test list argument parsing functionality."""
    
    def test_parse_list_argument_valid(self):
        """Test parsing valid list argument."""
        result = parse_list_argument("branding,design_specifications,publishing_strategy")
        expected = ["branding", "design_specifications", "publishing_strategy"]
        assert result == expected
    
    def test_parse_list_argument_single(self):
        """Test parsing single item list."""
        result = parse_list_argument("branding")
        assert result == ["branding"]
    
    def test_parse_list_argument_empty(self):
        """Test parsing empty list argument."""
        result = parse_list_argument("")
        assert result is None
        
        result = parse_list_argument(None)
        assert result is None
    
    def test_parse_list_argument_whitespace(self):
        """Test parsing list argument with whitespace."""
        result = parse_list_argument(" branding , design_specifications , publishing_strategy ")
        expected = ["branding", "design_specifications", "publishing_strategy"]
        assert result == expected
    
    def test_parse_list_argument_empty_items(self):
        """Test parsing list argument with empty items."""
        result = parse_list_argument("branding,,design_specifications")
        expected = ["branding", "design_specifications"]
        assert result == expected


class TestBatchConfigCreation:
    """Test batch configuration creation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            self.temp_dir.rmdir()
    
    def test_create_batch_config_defaults(self):
        """Test creating batch config with default values."""
        args = Namespace(
            output_dir=self.temp_dir,
            column_mapping=None,
            attributes=None,
            subattributes=None,
            naming_strategy="imprint_name",
            organization_strategy="by_source",
            no_index=False,
            overwrite=False,
            parallel=False,
            max_workers=4,
            continue_on_error=True,
            error_mode="continue_on_error",
            max_errors=100,
            verbose=False
        )
        
        config = create_batch_config(args)
        
        assert config.column_mapping == {}
        assert config.attributes is None
        assert config.subattributes is None
        assert config.output_config.base_directory == self.temp_dir
        assert config.output_config.naming_strategy == NamingStrategy.IMPRINT_NAME
        assert config.output_config.organization_strategy == OrganizationStrategy.BY_SOURCE
        assert config.output_config.create_index is True
        assert config.output_config.overwrite_existing is False
        assert config.processing_options.parallel_processing is False
        assert config.processing_options.max_workers == 4
        assert config.error_handling.mode == ErrorHandlingMode.CONTINUE_ON_ERROR
        assert config.error_handling.max_errors_per_file == 100
    
    def test_create_batch_config_custom(self):
        """Test creating batch config with custom values."""
        args = Namespace(
            output_dir=self.temp_dir,
            column_mapping="concept:imprint_concept,name:imprint_name",
            attributes="branding,design_specifications",
            subattributes="imprint_name,color_palette",
            naming_strategy="hybrid",
            organization_strategy="by_imprint",
            no_index=True,
            overwrite=True,
            parallel=True,
            max_workers=8,
            continue_on_error=False,
            error_mode="fail_fast",
            max_errors=50,
            verbose=True
        )
        
        config = create_batch_config(args)
        
        assert config.column_mapping == {"concept": "imprint_concept", "name": "imprint_name"}
        assert config.attributes == ["branding", "design_specifications"]
        assert config.subattributes == ["imprint_name", "color_palette"]
        assert config.output_config.naming_strategy == NamingStrategy.HYBRID
        assert config.output_config.organization_strategy == OrganizationStrategy.BY_IMPRINT
        assert config.output_config.create_index is False
        assert config.output_config.overwrite_existing is True
        assert config.processing_options.parallel_processing is True
        assert config.processing_options.max_workers == 8
        assert config.error_handling.mode == ErrorHandlingMode.FAIL_FAST
        assert config.error_handling.max_errors_per_file == 50
        assert config.error_handling.log_level == "DEBUG"


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.cleanup_directory(self.temp_dir)
    
    def cleanup_directory(self, directory: Path):
        """Recursively clean up a directory."""
        if directory.exists():
            for item in directory.iterdir():
                if item.is_dir():
                    self.cleanup_directory(item)
                else:
                    item.unlink()
            directory.rmdir()
    
    @patch('expand_imprint_cli.BatchProcessor')
    @patch('expand_imprint_cli.create_llm_caller')
    def test_process_batch_csv_mode(self, mock_create_llm, mock_batch_processor):
        """Test batch processing in CSV mode."""
        from expand_imprint_cli import process_batch
        
        # Create test CSV file
        csv_file = self.temp_dir / "test.csv"
        csv_file.write_text("concept\nTest Imprint")
        
        # Set up mocks
        mock_llm_caller = Mock()
        mock_create_llm.return_value = mock_llm_caller
        
        mock_processor = Mock()
        mock_batch_processor.return_value = mock_processor
        
        # Mock successful result
        mock_result = Mock()
        mock_result.total_processed = 1
        mock_result.successful = 1
        mock_result.failed = 0
        mock_result.get_success_rate.return_value = 100.0
        mock_result.processing_time = 1.5
        mock_result.index_file = None
        mock_result.errors = []
        mock_result.warnings = []
        mock_processor.process_csv_file.return_value = mock_result
        mock_processor.get_processing_summary.return_value = {
            'processing': {'average_processing_time': 1.5},
            'output': {'base_directory': str(self.temp_dir), 'output_files': []},
            'errors': {'errors_by_type': {}}
        }
        
        # Create args
        args = Namespace(
            csv=csv_file,
            directory=None,
            output_dir=self.temp_dir,
            column_mapping=None,
            attributes=None,
            subattributes=None,
            naming_strategy="imprint_name",
            organization_strategy="by_source",
            no_index=False,
            overwrite=False,
            parallel=False,
            max_workers=4,
            continue_on_error=True,
            error_mode="continue_on_error",
            max_errors=100,
            verbose=False
        )
        
        # Process batch
        success = process_batch(args)
        
        # Verify calls
        mock_create_llm.assert_called_once_with(True)
        mock_batch_processor.assert_called_once()
        mock_processor.process_csv_file.assert_called_once_with(csv_file)
        
        assert success is True
    
    @patch('expand_imprint_cli.BatchProcessor')
    @patch('expand_imprint_cli.create_llm_caller')
    def test_process_batch_directory_mode(self, mock_create_llm, mock_batch_processor):
        """Test batch processing in directory mode."""
        from expand_imprint_cli import process_batch
        
        # Set up mocks
        mock_llm_caller = Mock()
        mock_create_llm.return_value = mock_llm_caller
        
        mock_processor = Mock()
        mock_batch_processor.return_value = mock_processor
        
        # Mock successful result
        mock_result = Mock()
        mock_result.total_processed = 2
        mock_result.successful = 2
        mock_result.failed = 0
        mock_result.get_success_rate.return_value = 100.0
        mock_result.processing_time = 3.0
        mock_result.index_file = self.temp_dir / "index.json"
        mock_result.errors = []
        mock_result.warnings = []
        mock_processor.process_directory.return_value = mock_result
        mock_processor.get_processing_summary.return_value = {
            'processing': {'average_processing_time': 1.5},
            'output': {'base_directory': str(self.temp_dir), 'output_files': []},
            'errors': {'errors_by_type': {}}
        }
        
        # Create args
        args = Namespace(
            csv=None,
            directory=self.temp_dir,
            output_dir=self.temp_dir / "output",
            column_mapping=None,
            attributes=None,
            subattributes=None,
            naming_strategy="imprint_name",
            organization_strategy="by_source",
            no_index=False,
            overwrite=False,
            parallel=False,
            max_workers=4,
            continue_on_error=True,
            error_mode="continue_on_error",
            max_errors=100,
            verbose=True
        )
        
        # Process batch
        success = process_batch(args)
        
        # Verify calls
        mock_processor.process_directory.assert_called_once_with(self.temp_dir)
        assert success is True


if __name__ == "__main__":
    pytest.main([__file__])