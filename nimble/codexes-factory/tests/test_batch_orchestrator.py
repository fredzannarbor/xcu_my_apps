"""
Unit tests for BatchOrchestrator component.
"""

import pytest
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.imprint_builder.batch_orchestrator import BatchOrchestrator, create_batch_orchestrator
from codexes.modules.imprint_builder.batch_models import (
    BatchConfig,
    ImprintRow,
    ImprintResult,
    BatchResult,
    ProcessingOptions,
    OutputConfig,
    ErrorHandlingConfig,
    create_default_config
)
from codexes.modules.imprint_builder.imprint_concept import ImprintConcept
from codexes.modules.imprint_builder.imprint_expander import ExpandedImprint, DictWrapper


class TestBatchOrchestrator:
    """Test BatchOrchestrator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_caller = Mock()
        self.config = create_default_config()
        
        # Create mock expander
        self.mock_expander = Mock()
        self.mock_concept_parser = Mock()
        
        # Create orchestrator with mocked dependencies
        with patch('codexes.modules.imprint_builder.batch_orchestrator.ENHANCED_EXPANDER_AVAILABLE', False):
            with patch('codexes.modules.imprint_builder.batch_orchestrator.ImprintExpander') as mock_exp_class:
                with patch('codexes.modules.imprint_builder.batch_orchestrator.ImprintConceptParser') as mock_parser_class:
                    mock_exp_class.return_value = self.mock_expander
                    mock_parser_class.return_value = self.mock_concept_parser
                    
                    self.orchestrator = BatchOrchestrator(self.mock_llm_caller, self.config)
    
    def create_test_imprint_row(self, row_number: int = 1, concept: str = "Test Imprint") -> ImprintRow:
        """Create a test imprint row."""
        return ImprintRow(
            row_number=row_number,
            imprint_concept=concept,
            source_file=Path("test.csv"),
            additional_data={"extra": "data"}
        )
    
    def create_mock_expanded_imprint(self) -> ExpandedImprint:
        """Create a mock expanded imprint."""
        mock_concept = Mock(spec=ImprintConcept)
        mock_concept.name = "Test Imprint"
        
        branding = DictWrapper({
            "imprint_name": "Test Imprint",
            "mission_statement": "Test mission",
            "brand_values": ["Quality", "Innovation"]
        })
        
        design_specs = DictWrapper({
            "color_palette": {"primary": "#000000"},
            "typography": {"primary_font": "Arial"}
        })
        
        publishing_strategy = DictWrapper({
            "primary_genres": ["Fiction"],
            "target_readership": "General"
        })
        
        return ExpandedImprint(
            concept=mock_concept,
            branding=branding,
            design_specifications=design_specs,
            publishing_strategy=publishing_strategy,
            operational_framework=DictWrapper({}),
            marketing_approach=DictWrapper({}),
            financial_projections=DictWrapper({}),
            expanded_at=datetime.now()
        )
    
    def test_initialization(self):
        """Test BatchOrchestrator initialization."""
        assert self.orchestrator.llm_caller == self.mock_llm_caller
        assert self.orchestrator.config == self.config
        assert self.orchestrator.expander is not None
        assert self.orchestrator.concept_parser is not None
    
    def test_create_expander_standard(self):
        """Test creating standard expander."""
        with patch('codexes.modules.imprint_builder.batch_orchestrator.ENHANCED_EXPANDER_AVAILABLE', False):
            orchestrator = BatchOrchestrator(self.mock_llm_caller, self.config)
            # Should use standard expander
            assert orchestrator.expander is not None
    
    def test_process_single_imprint_success(self):
        """Test successful processing of single imprint."""
        # Setup mocks
        mock_concept = Mock(spec=ImprintConcept)
        mock_concept.name = "Test Imprint"
        mock_concept.description = "Test description"
        mock_expanded = self.create_mock_expanded_imprint()
        
        self.mock_concept_parser.parse_concept.return_value = mock_concept
        self.mock_expander.expand_concept.return_value = mock_expanded
        
        # Create test row
        row = self.create_test_imprint_row()
        
        # Process
        result = self.orchestrator.process_single_imprint(row)
        
        # Verify
        assert isinstance(result, ImprintResult)
        assert result.success is True
        assert result.row == row
        assert result.expanded_imprint == mock_expanded
        assert result.processing_time > 0
        assert result.error is None
    
    def test_process_single_imprint_parsing_failure(self):
        """Test processing with concept parsing failure."""
        # Setup mock to fail parsing but succeed expansion
        self.mock_concept_parser.parse_concept.side_effect = Exception("Parsing failed")
        mock_expanded = self.create_mock_expanded_imprint()
        self.mock_expander.expand_concept.return_value = mock_expanded
        
        # Create test row
        row = self.create_test_imprint_row()
        
        # Process
        result = self.orchestrator.process_single_imprint(row)
        
        # Should still succeed with basic concept
        assert result.success is True
        assert result.expanded_imprint == mock_expanded
    
    def test_process_single_imprint_expansion_failure(self):
        """Test processing with expansion failure."""
        # Setup mocks
        mock_concept = Mock(spec=ImprintConcept)
        mock_concept.name = "Test Imprint"
        mock_concept.description = "Test description"
        self.mock_concept_parser.parse_concept.return_value = mock_concept
        self.mock_expander.expand_concept.side_effect = Exception("Expansion failed")
        
        # Create test row
        row = self.create_test_imprint_row()
        
        # Process
        result = self.orchestrator.process_single_imprint(row)
        
        # Should fail
        assert result.success is False
        assert result.error is not None
        assert "Expansion failed" in str(result.error)
    
    def test_process_batch_sequential(self):
        """Test sequential batch processing."""
        # Setup mocks
        mock_concept = Mock(spec=ImprintConcept)
        mock_concept.name = "Test Imprint"
        mock_concept.description = "Test description"
        mock_expanded = self.create_mock_expanded_imprint()
        
        self.mock_concept_parser.parse_concept.return_value = mock_concept
        self.mock_expander.expand_concept.return_value = mock_expanded
        
        # Create test rows
        rows = [
            self.create_test_imprint_row(1, "Imprint 1"),
            self.create_test_imprint_row(2, "Imprint 2"),
            self.create_test_imprint_row(3, "Imprint 3")
        ]
        
        # Process
        batch_result = self.orchestrator.process_batch(rows)
        
        # Verify
        assert isinstance(batch_result, BatchResult)
        assert batch_result.total_processed == 3
        assert batch_result.successful == 3
        assert batch_result.failed == 0
        assert len(batch_result.results) == 3
    
    def test_process_batch_parallel(self):
        """Test parallel batch processing."""
        # Enable parallel processing
        self.config.processing_options.parallel_processing = True
        self.config.processing_options.max_workers = 2
        
        # Setup mocks
        mock_concept = Mock(spec=ImprintConcept)
        mock_concept.name = "Test Imprint"
        mock_concept.description = "Test description"
        mock_expanded = self.create_mock_expanded_imprint()
        
        self.mock_concept_parser.parse_concept.return_value = mock_concept
        self.mock_expander.expand_concept.return_value = mock_expanded
        
        # Create test rows
        rows = [
            self.create_test_imprint_row(1, "Imprint 1"),
            self.create_test_imprint_row(2, "Imprint 2")
        ]
        
        # Process
        batch_result = self.orchestrator.process_batch(rows)
        
        # Verify
        assert batch_result.total_processed == 2
        assert batch_result.successful == 2
        assert batch_result.failed == 0
    
    def test_process_batch_with_failures(self):
        """Test batch processing with some failures."""
        # Setup mocks - first succeeds, second fails
        mock_concept = Mock(spec=ImprintConcept)
        mock_concept.name = "Test Imprint"
        mock_concept.description = "Test description"
        mock_expanded = self.create_mock_expanded_imprint()
        
        self.mock_concept_parser.parse_concept.return_value = mock_concept
        self.mock_expander.expand_concept.side_effect = [mock_expanded, Exception("Failed")]
        
        # Create test rows
        rows = [
            self.create_test_imprint_row(1, "Success"),
            self.create_test_imprint_row(2, "Failure")
        ]
        
        # Process
        batch_result = self.orchestrator.process_batch(rows)
        
        # Verify
        assert batch_result.total_processed == 2
        assert batch_result.successful == 1
        assert batch_result.failed == 1
    
    def test_process_batch_continue_on_error(self):
        """Test batch processing continues on error when configured."""
        # Configure to continue on error
        self.config.processing_options.continue_on_error = True
        
        # Setup mocks to fail on second item
        mock_concept = Mock(spec=ImprintConcept)
        mock_concept.name = "Test Imprint"
        mock_concept.description = "Test description"
        mock_expanded = self.create_mock_expanded_imprint()
        
        self.mock_concept_parser.parse_concept.return_value = mock_concept
        self.mock_expander.expand_concept.side_effect = [mock_expanded, Exception("Failed"), mock_expanded]
        
        # Create test rows
        rows = [
            self.create_test_imprint_row(1, "Success 1"),
            self.create_test_imprint_row(2, "Failure"),
            self.create_test_imprint_row(3, "Success 2")
        ]
        
        # Process
        batch_result = self.orchestrator.process_batch(rows)
        
        # Should process all items
        assert batch_result.total_processed == 3
        assert batch_result.successful == 2
        assert batch_result.failed == 1
    
    def test_apply_attribute_filtering(self):
        """Test attribute filtering functionality."""
        # Configure attribute filtering
        self.config.attributes = ["branding", "design_specifications"]
        self.config.subattributes = ["imprint_name", "color_palette"]
        
        # Create expanded imprint
        expanded = self.create_mock_expanded_imprint()
        
        # Apply filtering
        filtered = self.orchestrator.apply_attribute_filtering(expanded)
        
        # Should still have the filtered attributes
        assert hasattr(filtered, 'branding')
        assert hasattr(filtered, 'design_specifications')
    
    def test_apply_attribute_filtering_no_config(self):
        """Test attribute filtering with no configuration."""
        # No filtering configured
        expanded = self.create_mock_expanded_imprint()
        
        # Apply filtering
        filtered = self.orchestrator.apply_attribute_filtering(expanded)
        
        # Should return unchanged
        assert filtered == expanded
    
    def test_has_meaningful_content(self):
        """Test meaningful content detection."""
        # Create expanded imprint with content
        expanded = self.create_mock_expanded_imprint()
        
        # Should have meaningful content
        assert self.orchestrator._has_meaningful_content(expanded) is True
        
        # Create empty expanded imprint
        empty_expanded = ExpandedImprint(
            concept=Mock(),
            branding=DictWrapper({}),
            design_specifications=DictWrapper({}),
            publishing_strategy=DictWrapper({}),
            operational_framework=DictWrapper({}),
            marketing_approach=DictWrapper({}),
            financial_projections=DictWrapper({}),
            expanded_at=datetime.now()
        )
        
        # Should not have meaningful content
        assert self.orchestrator._has_meaningful_content(empty_expanded) is False
    
    def test_get_processing_stats(self):
        """Test processing statistics generation."""
        # Create batch result with mixed results
        batch_result = BatchResult(source_files=[Path("test.csv")])
        
        # Add successful result
        success_result = ImprintResult(
            row=self.create_test_imprint_row(1),
            success=True,
            processing_time=1.5
        )
        batch_result.add_result(success_result)
        
        # Add failed result
        failed_result = ImprintResult(
            row=self.create_test_imprint_row(2),
            success=False,
            processing_time=0.5
        )
        batch_result.add_result(failed_result)
        
        batch_result.finalize()
        
        # Get stats
        stats = self.orchestrator.get_processing_stats(batch_result)
        
        # Verify stats
        assert stats["total_processed"] == 2
        assert stats["successful"] == 1
        assert stats["failed"] == 1
        assert stats["success_rate"] == 50.0
        assert stats["average_processing_time"] == 1.0  # (1.5 + 0.5) / 2
        assert stats["files_processed"] == 1
    
    def test_get_processing_stats_empty(self):
        """Test processing statistics with empty results."""
        batch_result = BatchResult(source_files=[])
        
        stats = self.orchestrator.get_processing_stats(batch_result)
        
        assert stats["total_processed"] == 0
        assert stats["successful"] == 0
        assert stats["failed"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["average_processing_time"] == 0.0


class TestParseImprintConcept:
    """Test imprint concept parsing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_caller = Mock()
        self.config = create_default_config()
        self.mock_concept_parser = Mock()
        
        with patch('codexes.modules.imprint_builder.batch_orchestrator.ENHANCED_EXPANDER_AVAILABLE', False):
            with patch('codexes.modules.imprint_builder.batch_orchestrator.ImprintExpander'):
                with patch('codexes.modules.imprint_builder.batch_orchestrator.ImprintConceptParser') as mock_parser_class:
                    mock_parser_class.return_value = self.mock_concept_parser
                    self.orchestrator = BatchOrchestrator(self.mock_llm_caller, self.config)
    
    def test_parse_imprint_concept_success(self):
        """Test successful concept parsing."""
        # Setup mock
        mock_concept = Mock(spec=ImprintConcept)
        self.mock_concept_parser.parse_concept.return_value = mock_concept
        
        # Create test row
        row = ImprintRow(1, "Test concept", Path("test.csv"))
        
        # Parse
        result = self.orchestrator._parse_imprint_concept(row)
        
        # Verify
        assert result == mock_concept
        self.mock_concept_parser.parse_concept.assert_called_once_with("Test concept")
    
    def test_parse_imprint_concept_failure(self):
        """Test concept parsing failure with fallback."""
        # Setup mock to fail
        self.mock_concept_parser.parse_concept.side_effect = Exception("Parsing failed")
        
        # Create test row
        row = ImprintRow(1, "Test concept", Path("test.csv"))
        
        # Parse
        result = self.orchestrator._parse_imprint_concept(row)
        
        # Should create basic concept
        assert isinstance(result, ImprintConcept)
        assert result.description == "Test concept"
        assert result.raw_input == "Test concept"


class TestExpandConcept:
    """Test concept expansion functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_caller = Mock()
        self.config = create_default_config()
        self.mock_expander = Mock()
        
        with patch('codexes.modules.imprint_builder.batch_orchestrator.ENHANCED_EXPANDER_AVAILABLE', False):
            with patch('codexes.modules.imprint_builder.batch_orchestrator.ImprintExpander') as mock_exp_class:
                with patch('codexes.modules.imprint_builder.batch_orchestrator.ImprintConceptParser'):
                    mock_exp_class.return_value = self.mock_expander
                    self.orchestrator = BatchOrchestrator(self.mock_llm_caller, self.config)
    
    def test_expand_concept_success(self):
        """Test successful concept expansion."""
        # Setup mocks
        mock_concept = Mock(spec=ImprintConcept)
        mock_concept.name = "Test Imprint"
        mock_concept.description = "Test description"
        mock_expanded = Mock(spec=ExpandedImprint)
        self.mock_expander.expand_concept.return_value = mock_expanded
        
        # Create test row
        row = ImprintRow(1, "Test", Path("test.csv"))
        
        # Expand
        result = self.orchestrator._expand_concept(mock_concept, row)
        
        # Verify
        assert result == mock_expanded
        self.mock_expander.expand_concept.assert_called_once_with(mock_concept)
    
    def test_expand_concept_failure(self):
        """Test concept expansion failure."""
        # Setup mock to fail
        mock_concept = Mock(spec=ImprintConcept)
        mock_concept.name = "Test Imprint"
        mock_concept.description = "Test description"
        self.mock_expander.expand_concept.side_effect = Exception("Expansion failed")
        
        # Create test row
        row = ImprintRow(1, "Test", Path("test.csv"))
        
        # Should raise exception
        with pytest.raises(Exception, match="Expansion failed"):
            self.orchestrator._expand_concept(mock_concept, row)


class TestFactoryFunction:
    """Test factory function."""
    
    def test_create_batch_orchestrator(self):
        """Test creating BatchOrchestrator with factory function."""
        mock_llm_caller = Mock()
        config = create_default_config()
        
        with patch('codexes.modules.imprint_builder.batch_orchestrator.ENHANCED_EXPANDER_AVAILABLE', False):
            with patch('codexes.modules.imprint_builder.batch_orchestrator.ImprintExpander'):
                with patch('codexes.modules.imprint_builder.batch_orchestrator.ImprintConceptParser'):
                    orchestrator = create_batch_orchestrator(mock_llm_caller, config)
                
                assert isinstance(orchestrator, BatchOrchestrator)
                assert orchestrator.llm_caller == mock_llm_caller
                assert orchestrator.config == config


if __name__ == "__main__":
    pytest.main([__file__])