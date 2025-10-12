"""
Tests for Enhanced Field Mapping Strategies
"""

import pytest
from unittest.mock import Mock, patch
from codexes.modules.distribution.enhanced_field_mappings import (
    ThemaSubjectStrategy, AgeRangeStrategy, SeriesAwareDescriptionStrategy,
    BlankIngramPricingStrategy, TrancheFilePathStrategy
)
from codexes.modules.distribution.field_mapping import MappingContext
from codexes.modules.metadata.metadata_models import CodexMetadata


class TestThemaSubjectStrategy:
    """Test cases for ThemaSubjectStrategy."""
    
    def test_extract_first_subject(self):
        """Test extracting first thema subject."""
        strategy = ThemaSubjectStrategy(1)
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.raw_metadata = {'thema': ['TGBN', 'JNFH', 'JFFG']}
        
        result = strategy.map_field(metadata, context)
        assert result == 'TGBN'
        
    def test_extract_second_subject(self):
        """Test extracting second thema subject."""
        strategy = ThemaSubjectStrategy(2)
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.raw_metadata = {'thema': ['TGBN', 'JNFH', 'JFFG']}
        
        result = strategy.map_field(metadata, context)
        assert result == 'JNFH'
        
    def test_extract_missing_subject(self):
        """Test extracting subject that doesn't exist."""
        strategy = ThemaSubjectStrategy(3)
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.raw_metadata = {'thema': ['TGBN']}  # Only one subject
        
        result = strategy.map_field(metadata, context)
        assert result == ""
        
    def test_no_thema_data(self):
        """Test with no thema data."""
        strategy = ThemaSubjectStrategy(1)
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.raw_metadata = {}
        
        result = strategy.map_field(metadata, context)
        assert result == ""


class TestAgeRangeStrategy:
    """Test cases for AgeRangeStrategy."""
    
    def test_extract_min_age(self):
        """Test extracting minimum age."""
        strategy = AgeRangeStrategy("min")
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.raw_metadata = {'min_age': 18, 'max_age': 65}
        
        result = strategy.map_field(metadata, context)
        assert result == "18"
        
    def test_extract_max_age(self):
        """Test extracting maximum age."""
        strategy = AgeRangeStrategy("max")
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.raw_metadata = {'min_age': 18, 'max_age': 65}
        
        result = strategy.map_field(metadata, context)
        assert result == "65"
        
    def test_missing_age(self):
        """Test with missing age data."""
        strategy = AgeRangeStrategy("min")
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.raw_metadata = {}
        
        result = strategy.map_field(metadata, context)
        assert result == ""
        
    def test_invalid_age(self):
        """Test with invalid age data."""
        strategy = AgeRangeStrategy("max")
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.raw_metadata = {'max_age': 'adult'}
        
        result = strategy.map_field(metadata, context)
        assert result == ""


class TestSeriesAwareDescriptionStrategy:
    """Test cases for SeriesAwareDescriptionStrategy."""
    
    def test_process_with_series(self):
        """Test processing description with series."""
        strategy = SeriesAwareDescriptionStrategy()
        metadata = Mock(spec=CodexMetadata)
        metadata.short_description = "This book offers valuable insights."
        metadata.series_name = "Test Series"
        context = Mock(spec=MappingContext)
        
        result = strategy.map_field(metadata, context)
        expected = "This book in the Test Series series offers valuable insights."
        assert result == expected
        
    def test_process_without_series(self):
        """Test processing description without series."""
        strategy = SeriesAwareDescriptionStrategy()
        metadata = Mock(spec=CodexMetadata)
        metadata.short_description = "This book offers valuable insights."
        metadata.series_name = None
        context = Mock(spec=MappingContext)
        
        result = strategy.map_field(metadata, context)
        assert result == "This book offers valuable insights."
        
    def test_extract_series_from_context(self):
        """Test extracting series from context when not in metadata."""
        strategy = SeriesAwareDescriptionStrategy()
        metadata = Mock(spec=CodexMetadata)
        metadata.short_description = "This book is great."
        metadata.series_name = None
        context = Mock(spec=MappingContext)
        context.raw_metadata = {'series_name': 'Context Series'}
        
        result = strategy.map_field(metadata, context)
        expected = "This book in the Context Series series is great."
        assert result == expected
        
    def test_no_this_book_pattern(self):
        """Test description without 'This book' pattern."""
        strategy = SeriesAwareDescriptionStrategy()
        metadata = Mock(spec=CodexMetadata)
        metadata.short_description = "A comprehensive guide to advanced topics."
        metadata.series_name = "Guide Series"
        context = Mock(spec=MappingContext)
        
        result = strategy.map_field(metadata, context)
        assert result == "A comprehensive guide to advanced topics."


class TestBlankIngramPricingStrategy:
    """Test cases for BlankIngramPricingStrategy."""
    
    def test_always_returns_blank(self):
        """Test that strategy always returns blank."""
        strategy = BlankIngramPricingStrategy()
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        
        result = strategy.map_field(metadata, context)
        assert result == ""


class TestTrancheFilePathStrategy:
    """Test cases for TrancheFilePathStrategy."""
    
    def test_generate_interior_path(self):
        """Test generating interior file path."""
        strategy = TrancheFilePathStrategy("interior")
        metadata = Mock(spec=CodexMetadata)
        metadata.title = "Test Book Title"
        metadata.isbn13 = "9781234567890"
        
        context = Mock(spec=MappingContext)
        context.config = {
            'tranche_config': {
                'file_path_templates': {
                    'interior': 'interior/{title_slug}_interior.pdf'
                }
            }
        }
        
        result = strategy.map_field(metadata, context)
        assert result == "interior/Test_Book_Title_interior.pdf"
        
    def test_generate_cover_path(self):
        """Test generating cover file path."""
        strategy = TrancheFilePathStrategy("cover")
        metadata = Mock(spec=CodexMetadata)
        metadata.title = "Another Test"
        
        context = Mock(spec=MappingContext)
        context.config = {
            'tranche_config': {
                'file_path_templates': {
                    'cover': 'covers/{title_slug}_cover.pdf'
                }
            }
        }
        
        result = strategy.map_field(metadata, context)
        assert result == "covers/Another_Test_cover.pdf"
        
    def test_no_template_configured(self):
        """Test with no template configured."""
        strategy = TrancheFilePathStrategy("interior")
        metadata = Mock(spec=CodexMetadata)
        context = Mock(spec=MappingContext)
        context.config = {'tranche_config': {}}
        
        result = strategy.map_field(metadata, context)
        assert result == ""
        
    def test_sanitize_special_characters(self):
        """Test sanitizing special characters in paths."""
        strategy = TrancheFilePathStrategy("interior")
        metadata = Mock(spec=CodexMetadata)
        metadata.title = "Test: Book & More!"
        
        context = Mock(spec=MappingContext)
        context.config = {
            'tranche_config': {
                'file_path_templates': {
                    'interior': 'interior/{title_slug}.pdf'
                }
            }
        }
        
        result = strategy.map_field(metadata, context)
        assert result == "interior/Test_Book_More.pdf"
        
    def test_create_title_slug(self):
        """Test title slug creation."""
        strategy = TrancheFilePathStrategy("interior")
        
        # Test normal title
        slug = strategy._create_title_slug("Test Book Title")
        assert slug == "Test_Book_Title"
        
        # Test title with special characters
        slug = strategy._create_title_slug("Test: Book & More!")
        assert slug == "Test_Book_More"
        
        # Test empty title
        slug = strategy._create_title_slug("")
        assert slug == ""
        
    def test_sanitize_path(self):
        """Test path sanitization."""
        strategy = TrancheFilePathStrategy("interior")
        
        # Test path with invalid characters
        sanitized = strategy._sanitize_path("path/with<invalid>chars|here?.pdf")
        assert sanitized == "path/with_invalid_chars_here_.pdf"
        
        # Test very long path
        long_path = "a" * 300 + ".pdf"
        sanitized = strategy._sanitize_path(long_path)
        assert len(sanitized) <= 255