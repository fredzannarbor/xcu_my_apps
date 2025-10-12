"""
Unit tests for BatchProcessor component.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.imprint_builder.batch_processor import BatchProcessor, create_batch_processor
from codexes.modules.imprint_builder.batch_models import (
    BatchConfig,
    BatchResult,
    ImprintRow,
    ImprintResult,
    create_default_config
)


class TestBatchProcessor:
    """Test BatchProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_caller = Mock()
        self.config = create_default_config()
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Update config to use temp directory
        self.config.output_config.base_directory = self.temp_dir
        
        # Create processor with mocked components
        with patch('codexes.modules.imprint_builder.batch_processor.CSVReader') as mock_csv:
            with patch('codexes.modules.imprint_builder.batch_processor.DirectoryScanner') as mock_scanner:
                with patch('codexes.modules.imprint_builder.batch_processor.BatchOrchestrator') as mock_orchestrator:
                    with patch('codexes.modules.imprint_builder.batch_processor.OutputManager') as mock_output:
                        with patch('codexes.modules.imprint_builder.batch_processor.ErrorHandler') as mock_error:
                            
                            # Set up mocks
                            self.mock_csv_reader = Mock()
                            self.mock_directory_scanner = Mock()
                            self.mock_orchestrator = Mock()
                            self.mock_output_manager = Mock()
                            self.mock_error_handler = Mock()
                            
                            mock_csv.return_value = self.mock_csv_reader
                            mock_scanner.return_value = self.mock_directory_scanner
                            mock_orchestrator.return_value = self.mock_orchestrator
                            mock_output.return_value = self.mock_output_manager
                            mock_error.return_value = self.mock_error_handler
                            
                            self.processor = BatchProcessor(self.mock_llm_caller, self.config)
    
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
    
    def create_test_csv(self, filename: str, content: str = "header\ndata") -> Path:
        """Create a test CSV file."""
        csv_path = self.temp_dir / filename
        csv_path.write_text(content)
        return csv_path
    
    def create_test_imprint_row(self, row_number: int = 1) -> ImprintRow:
        """Create a test imprint row."""
        return ImprintRow(
            row_number=row_number,
            imprint_concept="Test Imprint",
            source_file=Path("test.csv")
        )
    
    def test_initialization(self):
        """Test BatchProcessor initialization."""
        assert self.processor.llm_caller == self.mock_llm_caller
        assert self.processor.config == self.config
        assert self.processor.csv_reader == self.mock_csv_reader
        assert self.processor.directory_scanner == self.mock_directory_scanner
        assert self.processor.orchestrator == self.mock_orchestrator
        assert self.processor.output_manager == self.mock_output_manager
        assert self.processor.error_handler == self.mock_error_handler
    
    def test_process_csv_file_success(self):
        """Test successful CSV file processing."""
        # Create test CSV file
        csv_path = self.create_test_csv("test.csv")
        
        # Set up mocks
        test_rows = [self.create_test_imprint_row()]
        self.mock_csv_reader.read_csv.return_value = test_rows
        
        # Mock orchestrator result
        mock_batch_result = BatchResult(source_files=[csv_path])
        test_result = ImprintResult(row=test_rows[0], success=True)
        mock_batch_result.add_result(test_result)
        self.mock_orchestrator.process_batch.return_value = mock_batch_result
        
        # Mock output manager
        self.mock_output_manager.write_batch_results.return_value = [Path("output.json")]
        
        # Mock error handler
        self.mock_error_handler.errors = []
        
        # Process CSV file
        result = self.processor.process_csv_file(csv_path)
        
        # Verify calls
        self.mock_csv_reader.read_csv.assert_called_once_with(csv_path)
        self.mock_orchestrator.process_batch.assert_called_once_with(test_rows)
        self.mock_output_manager.write_batch_results.assert_called_once()
        
        # Verify result
        assert isinstance(result, BatchResult)
        assert result.total_processed == 1
        assert result.successful == 1
    
    def test_process_csv_file_read_error(self):
        """Test CSV file processing with read error."""
        csv_path = self.create_test_csv("test.csv")
        
        # Mock CSV reader to raise exception
        self.mock_csv_reader.read_csv.side_effect = ValueError("Invalid CSV")
        
        # Mock error handler to not continue
        self.mock_error_handler.handle_error.return_value = False
        self.mock_error_handler.errors = []
        
        # Process CSV file
        result = self.processor.process_csv_file(csv_path)
        
        # Should have error and no processing
        assert result.total_processed == 0
        assert len(result.errors) == 1
        assert "Failed to read CSV file" in result.errors[0].message
    
    def test_process_csv_file_no_concepts(self):
        """Test CSV file processing with no concepts found."""
        csv_path = self.create_test_csv("empty.csv")
        
        # Mock CSV reader to return empty list
        self.mock_csv_reader.read_csv.return_value = []
        self.mock_error_handler.errors = []
        
        # Process CSV file
        result = self.processor.process_csv_file(csv_path)
        
        # Should complete but with no processing
        assert result.total_processed == 0
        assert len(result.errors) == 0
    
    def test_process_directory_success(self):
        """Test successful directory processing."""
        # Create test CSV files
        csv1 = self.create_test_csv("test1.csv")
        csv2 = self.create_test_csv("test2.csv")
        
        # Mock directory scanner
        mock_scan_result = Mock()
        mock_scan_result.csv_files = [csv1, csv2]
        mock_scan_result.errors = []
        self.mock_directory_scanner.scan_for_csv_files.return_value = mock_scan_result
        
        # Mock CSV reader
        test_rows = [self.create_test_imprint_row(1), self.create_test_imprint_row(2)]
        self.mock_csv_reader.read_csv.side_effect = [[test_rows[0]], [test_rows[1]]]
        
        # Mock orchestrator
        mock_batch_result = BatchResult(source_files=[csv1, csv2])
        for row in test_rows:
            result = ImprintResult(row=row, success=True)
            mock_batch_result.add_result(result)
        self.mock_orchestrator.process_batch.return_value = mock_batch_result
        
        # Mock output manager
        self.mock_output_manager.write_batch_results.return_value = [Path("output1.json"), Path("output2.json")]
        
        # Mock error handler
        self.mock_error_handler.errors = []
        
        # Process directory
        result = self.processor.process_directory(self.temp_dir)
        
        # Verify calls
        self.mock_directory_scanner.scan_for_csv_files.assert_called_once_with(self.temp_dir)
        assert self.mock_csv_reader.read_csv.call_count == 2
        self.mock_orchestrator.process_batch.assert_called_once()
        
        # Verify result
        assert result.total_processed == 2
        assert result.successful == 2
    
    def test_process_directory_no_csv_files(self):
        """Test directory processing with no CSV files."""
        # Mock directory scanner to return no files
        mock_scan_result = Mock()
        mock_scan_result.csv_files = []
        mock_scan_result.errors = []
        self.mock_directory_scanner.scan_for_csv_files.return_value = mock_scan_result
        
        # Process directory
        result = self.processor.process_directory(self.temp_dir)
        
        # Should complete with no processing
        assert result.total_processed == 0
        assert len(result.source_files) == 0
    
    def test_process_directory_scan_error(self):
        """Test directory processing with scan error."""
        # Mock directory scanner to raise exception
        self.mock_directory_scanner.scan_for_csv_files.side_effect = PermissionError("Access denied")
        
        # Mock error handler to not continue
        self.mock_error_handler.handle_error.return_value = False
        
        # Process directory
        result = self.processor.process_directory(self.temp_dir)
        
        # Should have error
        assert result.total_processed == 0
        assert len(result.errors) == 1
    
    def test_process_single_file_success(self):
        """Test successful single file processing."""
        # Create test text file
        text_path = self.temp_dir / "concept.txt"
        text_path.write_text("Test imprint concept")
        
        # Mock orchestrator
        test_row = ImprintRow(
            row_number=1,
            imprint_concept="Test imprint concept",
            source_file=text_path,
            additional_data={"file_type": "text"}
        )
        
        mock_batch_result = BatchResult(source_files=[text_path])
        test_result = ImprintResult(row=test_row, success=True)
        mock_batch_result.add_result(test_result)
        self.mock_orchestrator.process_batch.return_value = mock_batch_result
        
        # Mock output manager
        self.mock_output_manager.write_batch_results.return_value = [Path("output.json")]
        
        # Process single file
        result = self.processor.process_single_file(text_path)
        
        # Verify orchestrator was called with correct row
        self.mock_orchestrator.process_batch.assert_called_once()
        called_rows = self.mock_orchestrator.process_batch.call_args[0][0]
        assert len(called_rows) == 1
        assert called_rows[0].imprint_concept == "Test imprint concept"
        assert called_rows[0].additional_data["file_type"] == "text"
        
        # Verify result
        assert result.total_processed == 1
        assert result.successful == 1
    
    def test_process_single_file_not_found(self):
        """Test single file processing with file not found."""
        non_existent = self.temp_dir / "missing.txt"
        
        # Process non-existent file
        result = self.processor.process_single_file(non_existent)
        
        # Should have error
        assert result.total_processed == 0
        assert len(result.errors) == 1
        assert "not found" in result.errors[0].message.lower()
    
    def test_process_single_file_empty(self):
        """Test single file processing with empty file."""
        # Create empty text file
        text_path = self.temp_dir / "empty.txt"
        text_path.write_text("")
        
        # Process empty file
        result = self.processor.process_single_file(text_path)
        
        # Should have error
        assert result.total_processed == 0
        assert len(result.errors) == 1
        assert "empty" in result.errors[0].message.lower()
    
    def test_get_processing_summary(self):
        """Test getting processing summary."""
        # Create mock batch result
        batch_result = BatchResult(source_files=[Path("test.csv")])
        
        # Mock component summaries
        self.mock_orchestrator.get_processing_stats.return_value = {
            "total_processed": 5,
            "successful": 4,
            "failed": 1
        }
        
        self.mock_output_manager.get_output_summary.return_value = {
            "output_files": ["file1.json", "file2.json"],
            "base_directory": str(self.temp_dir)
        }
        
        self.mock_error_handler.get_error_summary.return_value = {
            "total_errors": 1,
            "total_warnings": 2
        }
        
        # Get summary
        summary = self.processor.get_processing_summary(batch_result)
        
        # Verify structure
        assert "processing" in summary
        assert "output" in summary
        assert "errors" in summary
        assert "configuration" in summary
        
        # Verify content
        assert summary["processing"]["total_processed"] == 5
        assert summary["output"]["base_directory"] == str(self.temp_dir)
        assert summary["errors"]["total_errors"] == 1
        assert summary["configuration"]["naming_strategy"] == self.config.output_config.naming_strategy.value
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        # Mock config validation
        self.config.validate = Mock(return_value=["Test error"])
        
        errors = self.processor.validate_configuration()
        
        assert errors == ["Test error"]
        self.config.validate.assert_called_once()
    
    def test_clear_state(self):
        """Test clearing processing state."""
        self.processor.clear_state()
        
        self.mock_error_handler.clear_errors.assert_called_once()


class TestBatchProcessorIntegration:
    """Integration tests with real components (mocked LLM only)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_caller = Mock()
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create config with temp directory
        self.config = create_default_config()
        self.config.output_config.base_directory = self.temp_dir
    
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
    
    def test_initialization_with_real_components(self):
        """Test initialization with real components."""
        processor = BatchProcessor(self.mock_llm_caller, self.config)
        
        # Verify components are created
        assert processor.csv_reader is not None
        assert processor.directory_scanner is not None
        assert processor.orchestrator is not None
        assert processor.output_manager is not None
        assert processor.error_handler is not None
    
    def test_process_csv_file_file_not_found(self):
        """Test processing non-existent CSV file."""
        processor = BatchProcessor(self.mock_llm_caller, self.config)
        
        non_existent = self.temp_dir / "missing.csv"
        result = processor.process_csv_file(non_existent)
        
        # Should handle error gracefully
        assert isinstance(result, BatchResult)
        assert result.total_processed == 0
        assert len(result.errors) > 0


class TestFactoryFunction:
    """Test factory function."""
    
    def test_create_batch_processor_default_config(self):
        """Test creating BatchProcessor with default config."""
        mock_llm_caller = Mock()
        
        processor = create_batch_processor(mock_llm_caller)
        
        assert isinstance(processor, BatchProcessor)
        assert processor.llm_caller == mock_llm_caller
        assert processor.config is not None
    
    def test_create_batch_processor_custom_config(self):
        """Test creating BatchProcessor with custom config."""
        mock_llm_caller = Mock()
        config = create_default_config()
        
        processor = create_batch_processor(mock_llm_caller, config)
        
        assert isinstance(processor, BatchProcessor)
        assert processor.llm_caller == mock_llm_caller
        assert processor.config == config


if __name__ == "__main__":
    pytest.main([__file__])