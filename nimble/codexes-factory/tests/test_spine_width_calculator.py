"""
Unit tests for SpineWidthCalculator class.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, mock_open

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.covers.spine_width_calculator import SpineWidthCalculator


class TestSpineWidthCalculator:
    """Test cases for SpineWidthCalculator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create mock Excel data
        self.mock_excel_data = {
            'Standard 70 perfect': pd.DataFrame({
                'Pages': [50, 100, 150, 200, 250, 300],
                'SpineWidth': [0.125, 0.25, 0.375, 0.5, 0.625, 0.75]
            }),
            'Standard Color 50 Perfect': pd.DataFrame({
                'Pages': [40, 80, 120, 160, 200, 240],
                'SpineWidth': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
            })
        }
        
        # Create calculator with mock file path
        self.calculator = SpineWidthCalculator("test_lookup.xlsx")
        
    def test_init_default_values(self):
        """Test calculator initialization with default values"""
        calc = SpineWidthCalculator()
        
        assert calc.default_paper_type == "Standard 70 perfect"
        assert calc.fallback_spine_width == 0.25
        assert calc.lookup_file_path == Path("resources/SpineWidthLookup.xlsx")
    
    def test_init_custom_path(self):
        """Test calculator initialization with custom path"""
        custom_path = "custom/path/lookup.xlsx"
        calc = SpineWidthCalculator(custom_path)
        
        assert calc.lookup_file_path == Path(custom_path)
    
    @patch('pandas.read_excel')
    def test_calculate_spine_width_exact_match(self, mock_read_excel):
        """Test spine width calculation with exact page count match"""
        mock_read_excel.return_value = self.mock_excel_data
        
        # Mock file existence
        with patch.object(Path, 'exists', return_value=True):
            spine_width = self.calculator.calculate_spine_width_from_lookup(150, 'Standard 70 perfect')
            
            assert spine_width == 0.375
    
    @patch('pandas.read_excel')
    def test_calculate_spine_width_interpolation(self, mock_read_excel):
        """Test spine width calculation with interpolation"""
        mock_read_excel.return_value = self.mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            # Page count between 150 and 200, should use 200's spine width
            spine_width = self.calculator.calculate_spine_width_from_lookup(175, 'Standard 70 perfect')
            
            assert spine_width == 0.5  # Next higher value
    
    @patch('pandas.read_excel')
    def test_calculate_spine_width_below_minimum(self, mock_read_excel):
        """Test spine width calculation below minimum page count"""
        mock_read_excel.return_value = self.mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            spine_width = self.calculator.calculate_spine_width_from_lookup(25, 'Standard 70 perfect')
            
            assert spine_width == 0.125  # Minimum value
    
    @patch('pandas.read_excel')
    def test_calculate_spine_width_above_maximum(self, mock_read_excel):
        """Test spine width calculation above maximum page count"""
        mock_read_excel.return_value = self.mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            spine_width = self.calculator.calculate_spine_width_from_lookup(400, 'Standard 70 perfect')
            
            assert spine_width == 0.75  # Maximum value
    
    @patch('pandas.read_excel')
    def test_calculate_spine_width_default_paper_type(self, mock_read_excel):
        """Test spine width calculation with default paper type"""
        mock_read_excel.return_value = self.mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            spine_width = self.calculator.calculate_spine_width_from_lookup(150)
            
            assert spine_width == 0.375  # Uses default paper type
    
    def test_calculate_spine_width_file_not_found(self):
        """Test spine width calculation when lookup file is not found"""
        with patch.object(Path, 'exists', return_value=False):
            spine_width = self.calculator.calculate_spine_width_from_lookup(150)
            
            assert spine_width == 0.25  # Fallback value
    
    @patch('pandas.read_excel')
    def test_calculate_spine_width_invalid_sheet(self, mock_read_excel):
        """Test spine width calculation with invalid sheet name"""
        mock_read_excel.return_value = self.mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            spine_width = self.calculator.calculate_spine_width_from_lookup(150, 'NonexistentSheet')
            
            assert spine_width == 0.25  # Fallback value
    
    def test_validate_calculation_valid_range(self):
        """Test validation of spine width in valid range"""
        is_valid = self.calculator.validate_calculation(0.5, 200)
        assert is_valid
    
    def test_validate_calculation_too_small(self):
        """Test validation of spine width that's too small"""
        is_valid = self.calculator.validate_calculation(0.01, 200)
        assert not is_valid
    
    def test_validate_calculation_too_large(self):
        """Test validation of spine width that's too large"""
        is_valid = self.calculator.validate_calculation(3.0, 200)
        assert not is_valid
    
    def test_validate_calculation_page_correlation(self):
        """Test validation of spine width correlation with page count"""
        # Very thick spine for few pages should be invalid
        is_valid = self.calculator.validate_calculation(1.5, 50)
        assert not is_valid
        
        # Very thin spine for many pages should be invalid
        is_valid = self.calculator.validate_calculation(0.1, 500)
        assert not is_valid
    
    def test_distribute_spine_width_dict_metadata(self):
        """Test distributing spine width to dictionary metadata"""
        metadata = {'title': 'Test Book'}
        
        self.calculator.distribute_spine_width(0.5, metadata)
        
        assert metadata['spine_width_in'] == 0.5
    
    def test_distribute_spine_width_object_metadata(self):
        """Test distributing spine width to object metadata"""
        # Mock metadata object
        metadata = Mock()
        metadata.spine_width_in = None
        
        self.calculator.distribute_spine_width(0.5, metadata)
        
        assert metadata.spine_width_in == 0.5
    
    def test_distribute_spine_width_with_cover_generator(self):
        """Test distributing spine width to cover generator"""
        metadata = {}
        cover_generator = Mock()
        
        self.calculator.distribute_spine_width(0.5, metadata, cover_generator)
        
        assert metadata['spine_width_in'] == 0.5
        cover_generator.set_spine_width.assert_called_once_with(0.5)
    
    @patch('pandas.read_excel')
    def test_get_available_paper_types(self, mock_read_excel):
        """Test getting available paper types"""
        mock_read_excel.return_value = self.mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            paper_types = self.calculator.get_available_paper_types()
            
            expected_types = ['Standard 70 perfect', 'Standard Color 50 Perfect']
            assert set(paper_types) == set(expected_types)
    
    @patch('pandas.read_excel')
    def test_calculate_spine_width_with_validation(self, mock_read_excel):
        """Test spine width calculation with validation"""
        mock_read_excel.return_value = self.mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            spine_width, is_valid = self.calculator.calculate_spine_width_with_validation(150)
            
            assert spine_width == 0.375
            assert is_valid
    
    @patch('pandas.read_excel')
    def test_get_spine_width_range(self, mock_read_excel):
        """Test getting spine width range for paper type"""
        mock_read_excel.return_value = self.mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            min_width, max_width = self.calculator.get_spine_width_range('Standard 70 perfect')
            
            assert min_width == 0.125
            assert max_width == 0.75
    
    def test_clear_cache(self):
        """Test clearing the sheets cache"""
        # Add something to cache
        self.calculator._sheets_cache['test'] = pd.DataFrame()
        
        self.calculator.clear_cache()
        
        assert len(self.calculator._sheets_cache) == 0
    
    @patch('pandas.read_excel')
    def test_load_lookup_sheets_xlsx_fallback(self, mock_read_excel):
        """Test loading sheets with .xls fallback"""
        mock_read_excel.return_value = self.mock_excel_data
        
        # Mock .xlsx not existing but .xls existing
        def mock_exists(self):
            return str(self).endswith('.xls')
        
        with patch.object(Path, 'exists', side_effect=mock_exists):
            self.calculator._load_lookup_sheets()
            
            assert len(self.calculator._sheets_cache) == 2
    
    @patch('pandas.read_excel')
    def test_error_handling_in_lookup(self, mock_read_excel):
        """Test error handling in spine width lookup"""
        # Mock pandas raising an exception
        mock_read_excel.side_effect = Exception("File read error")
        
        with patch.object(Path, 'exists', return_value=True):
            spine_width = self.calculator.calculate_spine_width_from_lookup(150)
            
            assert spine_width == 0.25  # Should return fallback
    
    def test_error_handling_in_validation(self):
        """Test error handling in validation"""
        # Pass invalid inputs that might cause errors
        is_valid = self.calculator.validate_calculation(None, 150)
        assert not is_valid
        
        is_valid = self.calculator.validate_calculation(0.5, None)
        assert not is_valid
    
    def test_error_handling_in_distribution(self):
        """Test error handling in spine width distribution"""
        # Pass None metadata (should not crash)
        self.calculator.distribute_spine_width(0.5, None)
        
        # Pass metadata without proper attributes
        metadata = Mock()
        del metadata.spine_width_in  # Remove attribute
        self.calculator.distribute_spine_width(0.5, metadata)
    
    @patch('pandas.read_excel')
    def test_sheets_caching(self, mock_read_excel):
        """Test that sheets are cached properly"""
        mock_read_excel.return_value = self.mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            # First call should load sheets
            self.calculator.calculate_spine_width_from_lookup(150)
            
            # Second call should use cache
            self.calculator.calculate_spine_width_from_lookup(200)
            
            # Should only call read_excel once due to caching
            assert mock_read_excel.call_count == 1
    
    def test_backward_compatibility_function(self):
        """Test backward compatibility function"""
        from codexes.modules.covers.spine_width_calculator import calculate_spinewidth
        
        with patch.object(SpineWidthCalculator, 'calculate_spine_width_from_lookup', return_value=0.5):
            result = calculate_spinewidth('Standard 70 perfect', 150)
            assert result == 0.5


if __name__ == "__main__":
    pytest.main([__file__])