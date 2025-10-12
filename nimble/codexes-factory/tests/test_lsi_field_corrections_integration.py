"""
Integration tests for LSI field mapping corrections
"""

import pytest
import tempfile
import json
import csv
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from codexes.modules.distribution.lsi_acs_generator_new import LsiAcsGenerator
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestLSIFieldCorrectionsIntegration:
    """Integration tests for all LSI field mapping corrections."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create test template CSV
        self.template_path = self.temp_path / "test_template.csv"
        self.create_test_template()
        
        # Create test tranche config
        self.tranche_config_dir = self.temp_path / "configs" / "tranches"
        self.tranche_config_dir.mkdir(parents=True, exist_ok=True)
        self.create_test_tranche_config()
        
        # Create test metadata
        self.test_metadata = self.create_test_metadata()
        
    def create_test_template(self):
        """Create a test LSI template CSV."""
        headers = [
            "Lightning Source Account #",
            "ISBN or SKU",
            "Title",
            "Publisher",
            "Imprint",
            "Contributor One",
            "Contributor One Role",
            "Pages",
            "Pub Date",
            "Series Name",
            "# in Series",
            "Short Description",
            "Thema Subject 1",
            "Thema Subject 2", 
            "Thema Subject 3",
            "Min Age",
            "Max Age",
            "Interior Path / Filename",
            "Cover Path / Filename",
            "US-Ingram-Only* Suggested List Price (mode 2)",
            "US-Ingram-Only* Wholesale Discount % (Mode 2)",
            "US - Ingram - GAP * Suggested List Price (mode 2)",
            "US - Ingram - GAP * Wholesale Discount % (Mode 2)",
            "SIBI - EDUC - US * Suggested List Price (mode 2)",
            "SIBI - EDUC - US * Wholesale Discount % (Mode 2)"
        ]
        
        with open(self.template_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
    def create_test_tranche_config(self):
        """Create a test tranche configuration."""
        config = {
            "tranche_info": {"tranche_id": "test-tranche"},
            "publisher": "Test Publisher",
            "imprint": "Test Imprint",
            "field_overrides": {
                "Series Name": "Test Series Override",
                "annotation_boilerplate": " This is additional text."
            },
            "append_fields": ["annotation_boilerplate"],
            "file_path_templates": {
                "interior": "interior/{title_slug}_interior.pdf",
                "cover": "covers/{title_slug}_cover.pdf"
            },
            "blank_fields": [
                "US-Ingram-Only* Suggested List Price (mode 2)",
                "US-Ingram-Only* Wholesale Discount % (Mode 2)",
                "US - Ingram - GAP * Suggested List Price (mode 2)",
                "US - Ingram - GAP * Wholesale Discount % (Mode 2)",
                "SIBI - EDUC - US * Suggested List Price (mode 2)",
                "SIBI - EDUC - US * Wholesale Discount % (Mode 2)"
            ]
        }
        
        config_file = self.tranche_config_dir / "test_tranche.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
            
    def create_test_metadata(self):
        """Create test metadata with all relevant fields."""
        metadata = Mock(spec=CodexMetadata)
        metadata.title = "Test Book Title"
        metadata.author = "Test Author"
        metadata.publisher = "Test Publisher"
        metadata.imprint = "Test Imprint"
        metadata.isbn13 = "9781234567890"
        metadata.page_count = 200
        metadata.publication_date = "2025-01-01"
        metadata.short_description = "This book offers valuable insights into testing."
        metadata.series_name = "Original Series"  # Should be overridden
        
        # Add raw metadata dict for JSON extraction
        metadata.__dict__ = {
            'title': 'Test Book Title',
            'author': 'Test Author',
            'thema': ['TGBN', 'JNFH', 'JFFG'],
            'min_age': 18,
            'max_age': 65,
            'series_name': 'JSON Series',
            'short_description': 'This book offers valuable insights into testing.'
        }
        
        return metadata
        
    @patch('src.codexes.modules.distribution.lsi_acs_generator_new.TrancheConfigLoader')
    @patch('src.codexes.modules.distribution.enhanced_field_mappings.TrancheConfigLoader')
    def test_complete_field_corrections_integration(self, mock_tranche_loader1, mock_tranche_loader2):
        """Test complete integration of all field corrections."""
        # Mock tranche config loader
        mock_loader = Mock()
        mock_loader.get_tranche_override_config.return_value = {
            "field_overrides": {
                "Series Name": "Test Series Override",
                "annotation_boilerplate": " This is additional text."
            },
            "append_fields": ["annotation_boilerplate"],
            "file_path_templates": {
                "interior": "interior/{title_slug}_interior.pdf",
                "cover": "covers/{title_slug}_cover.pdf"
            },
            "blank_fields": [
                "US-Ingram-Only* Suggested List Price (mode 2)",
                "US-Ingram-Only* Wholesale Discount % (Mode 2)",
                "US - Ingram - GAP * Suggested List Price (mode 2)",
                "US - Ingram - GAP * Wholesale Discount % (Mode 2)",
                "SIBI - EDUC - US * Suggested List Price (mode 2)",
                "SIBI - EDUC - US * Wholesale Discount % (Mode 2)"
            ]
        }
        mock_loader.get_tranche_field_exclusions.return_value = []
        mock_loader.get_blank_fields.return_value = [
            "US-Ingram-Only* Suggested List Price (mode 2)",
            "US-Ingram-Only* Wholesale Discount % (Mode 2)",
            "US - Ingram - GAP * Suggested List Price (mode 2)",
            "US - Ingram - GAP * Wholesale Discount % (Mode 2)",
            "SIBI - EDUC - US * Suggested List Price (mode 2)",
            "SIBI - EDUC - US * Wholesale Discount % (Mode 2)"
        ]
        
        mock_tranche_loader1.return_value = mock_loader
        mock_tranche_loader2.return_value = mock_loader
        
        # Create generator with tranche
        with patch('src.codexes.modules.distribution.lsi_acs_generator_new.os.path.exists', return_value=True):
            generator = LsiAcsGenerator(
                template_path=str(self.template_path),
                tranche_name="test_tranche"
            )
        
        # Generate CSV
        output_path = self.temp_path / "test_output.csv"
        
        with patch.object(generator, 'validate_submission') as mock_validate:
            mock_validate.return_value = Mock(has_blocking_errors=lambda: False, warnings=[])
            
            generator.generate_with_validation(self.test_metadata, str(output_path))
        
        # Verify CSV was created
        assert output_path.exists()
        
        # Read and verify CSV content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            
            # Test 1: Tranche override priority
            assert row["Series Name"] == "Test Series Override"
            
            # Test 2: Thema subject extraction
            assert row["Thema Subject 1"] == "TGBN"
            assert row["Thema Subject 2"] == "JNFH"
            assert row["Thema Subject 3"] == "JFFG"
            
            # Test 3: Age range extraction
            assert row["Min Age"] == "18"
            assert row["Max Age"] == "65"
            
            # Test 4: Series-aware description
            assert "Test Series Override series" in row["Short Description"]
            
            # Test 5: Blank Ingram pricing fields
            assert row["US-Ingram-Only* Suggested List Price (mode 2)"] == ""
            assert row["US-Ingram-Only* Wholesale Discount % (Mode 2)"] == ""
            assert row["US - Ingram - GAP * Suggested List Price (mode 2)"] == ""
            assert row["US - Ingram - GAP * Wholesale Discount % (Mode 2)"] == ""
            assert row["SIBI - EDUC - US * Suggested List Price (mode 2)"] == ""
            assert row["SIBI - EDUC - US * Wholesale Discount % (Mode 2)"] == ""
            
            # Test 6: File path generation
            assert "interior/Test_Book_Title_interior.pdf" in row["Interior Path / Filename"]
            assert "covers/Test_Book_Title_cover.pdf" in row["Cover Path / Filename"]
            
    def test_thema_subject_extraction_edge_cases(self):
        """Test thema subject extraction with various edge cases."""
        test_cases = [
            # Case 1: Only 2 subjects
            (['TGBN', 'JNFH'], ['TGBN', 'JNFH', '']),
            # Case 2: More than 3 subjects (should limit to 3)
            (['TGBN', 'JNFH', 'JFFG', 'EXTRA'], ['TGBN', 'JNFH', 'JFFG']),
            # Case 3: No subjects
            ([], ['', '', '']),
            # Case 4: Invalid subjects mixed with valid
            (['TGBN', '123INVALID', 'JNFH'], ['TGBN', 'JNFH', '']),
        ]
        
        for input_subjects, expected_output in test_cases:
            metadata = self.create_test_metadata()
            metadata.__dict__['thema'] = input_subjects
            
            from codexes.modules.distribution.enhanced_field_mappings import ThemaSubjectStrategy
            from codexes.modules.distribution.field_mapping import MappingContext
            
            context = Mock(spec=MappingContext)
            context.raw_metadata = metadata.__dict__
            
            # Test each thema subject strategy
            for i in range(3):
                strategy = ThemaSubjectStrategy(i + 1)
                result = strategy.map_field(metadata, context)
                expected = expected_output[i] if i < len(expected_output) else ''
                assert result == expected, f"Thema Subject {i+1}: expected '{expected}', got '{result}'"
                
    def test_age_range_validation_edge_cases(self):
        """Test age range extraction with validation edge cases."""
        test_cases = [
            # Case 1: Valid range
            (18, 65, '18', '65'),
            # Case 2: Invalid negative age
            (-5, 25, '', '25'),
            # Case 3: Unrealistic age
            (25, 200, '25', ''),
            # Case 4: Non-numeric age
            ('adult', 65, '', '65'),
            # Case 5: None values
            (None, None, '', ''),
        ]
        
        for min_age, max_age, expected_min, expected_max in test_cases:
            metadata = self.create_test_metadata()
            metadata.__dict__['min_age'] = min_age
            metadata.__dict__['max_age'] = max_age
            
            from codexes.modules.distribution.enhanced_field_mappings import AgeRangeStrategy
            from codexes.modules.distribution.field_mapping import MappingContext
            
            context = Mock(spec=MappingContext)
            context.raw_metadata = metadata.__dict__
            
            min_strategy = AgeRangeStrategy("min")
            max_strategy = AgeRangeStrategy("max")
            
            min_result = min_strategy.map_field(metadata, context)
            max_result = max_strategy.map_field(metadata, context)
            
            assert min_result == expected_min, f"Min age: expected '{expected_min}', got '{min_result}'"
            assert max_result == expected_max, f"Max age: expected '{expected_max}', got '{max_result}'"
            
    def test_series_aware_description_processing(self):
        """Test series-aware description processing."""
        test_cases = [
            # Case 1: With series, has "This book"
            ("This book offers insights.", "Test Series", "This book in the Test Series series offers insights."),
            # Case 2: With series, has "this book" (lowercase)
            ("In conclusion, this book provides coverage.", "Test Series", "In conclusion, this book in the Test Series series provides coverage."),
            # Case 3: With series, no "this book"
            ("A comprehensive guide.", "Test Series", "A comprehensive guide."),
            # Case 4: No series, has "This book"
            ("This book offers insights.", None, "This book offers insights."),
            # Case 5: Empty series name
            ("This book offers insights.", "", "This book offers insights."),
        ]
        
        from codexes.modules.distribution.enhanced_field_mappings import SeriesAwareDescriptionStrategy
        from codexes.modules.distribution.field_mapping import MappingContext
        
        for description, series_name, expected in test_cases:
            metadata = Mock(spec=CodexMetadata)
            metadata.short_description = description
            metadata.series_name = series_name
            
            context = Mock(spec=MappingContext)
            context.raw_metadata = {'series_name': series_name}
            
            strategy = SeriesAwareDescriptionStrategy()
            result = strategy.map_field(metadata, context)
            
            assert result == expected, f"Description: expected '{expected}', got '{result}'"
            
    def test_file_path_generation(self):
        """Test file path generation from tranche templates."""
        from codexes.modules.distribution.enhanced_field_mappings import TrancheFilePathStrategy
        from codexes.modules.distribution.field_mapping import MappingContext
        
        metadata = Mock(spec=CodexMetadata)
        metadata.title = "Test Book: Special & Characters!"
        metadata.isbn13 = "9781234567890"
        
        context = Mock(spec=MappingContext)
        context.config = {
            'tranche_config': {
                'file_path_templates': {
                    'interior': 'interior/{title_slug}_interior.pdf',
                    'cover': 'covers/{title_slug}_cover.pdf'
                }
            }
        }
        
        # Test interior path
        interior_strategy = TrancheFilePathStrategy("interior")
        interior_result = interior_strategy.map_field(metadata, context)
        assert interior_result == "interior/Test_Book_Special_Characters_interior.pdf"
        
        # Test cover path
        cover_strategy = TrancheFilePathStrategy("cover")
        cover_result = cover_strategy.map_field(metadata, context)
        assert cover_result == "covers/Test_Book_Special_Characters_cover.pdf"
        
    def test_blank_ingram_pricing_strategy(self):
        """Test that Ingram pricing fields are always blank."""
        from codexes.modules.distribution.enhanced_field_mappings import BlankIngramPricingStrategy
        from codexes.modules.distribution.field_mapping import MappingContext
        
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        
        strategy = BlankIngramPricingStrategy()
        result = strategy.map_field(metadata, context)
        
        assert result == ""
        
    def test_performance_with_large_dataset(self):
        """Test performance with multiple books."""
        # Create multiple metadata objects
        metadata_list = []
        for i in range(10):
            metadata = self.create_test_metadata()
            metadata.title = f"Test Book {i}"
            metadata.__dict__['title'] = f"Test Book {i}"
            metadata_list.append(metadata)
        
        # Mock tranche config loader
        with patch('src.codexes.modules.distribution.lsi_acs_generator_new.TrancheConfigLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader.get_tranche_override_config.return_value = {}
            mock_loader.get_tranche_field_exclusions.return_value = []
            mock_loader.get_blank_fields.return_value = []
            mock_loader_class.return_value = mock_loader
            
            with patch('src.codexes.modules.distribution.lsi_acs_generator_new.os.path.exists', return_value=True):
                generator = LsiAcsGenerator(
                    template_path=str(self.template_path),
                    tranche_name="test_tranche"
                )
            
            # Generate batch CSV
            output_path = self.temp_path / "batch_output.csv"
            
            with patch.object(generator, 'validate_submission') as mock_validate:
                mock_validate.return_value = Mock(has_blocking_errors=lambda: False, warnings=[])
                
                import time
                start_time = time.time()
                generator.generate_batch_csv(metadata_list, str(output_path))
                end_time = time.time()
                
                # Should complete in reasonable time (less than 5 seconds for 10 books)
                assert (end_time - start_time) < 5.0
                
                # Verify output
                assert output_path.exists()
                
                # Count rows
                with open(output_path, 'r') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    # Should have header + 10 data rows
                    assert len(rows) == 11