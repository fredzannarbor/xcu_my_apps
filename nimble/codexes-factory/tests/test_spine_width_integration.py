"""
Integration tests for spine width calculation and distribution.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.covers.spine_width_calculator import SpineWidthCalculator


class TestSpineWidthIntegration:
    """Test integration of spine width calculation with book processing pipeline"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.calculator = SpineWidthCalculator()
        
        # Test book data
        self.test_book_data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'page_count': 200,
            'imprint': 'xynapse_traces'
        }
        
        # Mock metadata object
        self.mock_metadata = Mock()
        self.mock_metadata.page_count = 200
        self.mock_metadata.final_page_count = None
        self.mock_metadata.spine_width_in = None
    
    @patch('pandas.read_excel')
    def test_spine_width_calculation_and_distribution(self, mock_read_excel):
        """Test complete spine width calculation and distribution workflow"""
        # Mock Excel data
        import pandas as pd
        mock_excel_data = {
            'Standard 70 perfect': pd.DataFrame({
                'Pages': [50, 100, 150, 200, 250, 300],
                'SpineWidth': [0.125, 0.25, 0.375, 0.5, 0.625, 0.75]
            })
        }
        mock_read_excel.return_value = mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            # Calculate spine width
            spine_width, is_valid = self.calculator.calculate_spine_width_with_validation(200)
            
            # Distribute to metadata
            metadata = {'title': 'Test Book'}
            self.calculator.distribute_spine_width(spine_width, metadata)
            
            # Verify results
            assert spine_width == 0.5
            assert is_valid
            assert metadata['spine_width_in'] == 0.5
    
    @patch('pandas.read_excel')
    def test_spine_width_integration_with_cover_data(self, mock_read_excel):
        """Test spine width integration with cover generation data"""
        # Mock Excel data
        import pandas as pd
        mock_excel_data = {
            'Standard 70 perfect': pd.DataFrame({
                'Pages': [200],
                'SpineWidth': [0.5]
            })
        }
        mock_read_excel.return_value = mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            # Simulate cover generation data preparation
            cover_data = self.test_book_data.copy()
            
            # Calculate and add spine width
            spine_width = self.calculator.calculate_spine_width_from_lookup(
                cover_data['page_count'], 
                "Standard 70 perfect"
            )
            cover_data['spine_width_in'] = spine_width
            
            # Verify cover data has spine width
            assert 'spine_width_in' in cover_data
            assert cover_data['spine_width_in'] == 0.5
    
    def test_spine_width_fallback_behavior(self):
        """Test spine width fallback when lookup fails"""
        # Test with non-existent lookup file
        with patch.object(Path, 'exists', return_value=False):
            spine_width = self.calculator.calculate_spine_width_from_lookup(200)
            
            # Should return fallback value
            assert spine_width == 0.25
    
    @patch('pandas.read_excel')
    def test_spine_width_validation_integration(self, mock_read_excel):
        """Test spine width validation in integration context"""
        # Mock Excel data with extreme values
        import pandas as pd
        mock_excel_data = {
            'Standard 70 perfect': pd.DataFrame({
                'Pages': [200],
                'SpineWidth': [5.0]  # Unrealistically large spine width
            })
        }
        mock_read_excel.return_value = mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            spine_width, is_valid = self.calculator.calculate_spine_width_with_validation(200)
            
            # Should calculate the value but validation should fail
            assert spine_width == 5.0
            assert not is_valid
    
    def test_metadata_object_integration(self):
        """Test integration with CodexMetadata-like objects"""
        # Mock metadata object with attributes
        metadata = Mock()
        metadata.spine_width_in = None
        
        # Distribute spine width
        self.calculator.distribute_spine_width(0.5, metadata)
        
        # Verify attribute was set
        assert metadata.spine_width_in == 0.5
    
    def test_cover_generator_integration(self):
        """Test integration with cover generator objects"""
        metadata = {}
        cover_generator = Mock()
        
        # Distribute spine width to both metadata and cover generator
        self.calculator.distribute_spine_width(0.5, metadata, cover_generator)
        
        # Verify both were updated
        assert metadata['spine_width_in'] == 0.5
        cover_generator.set_spine_width.assert_called_once_with(0.5)
    
    @patch('pandas.read_excel')
    def test_page_count_edge_cases(self, mock_read_excel):
        """Test spine width calculation with edge case page counts"""
        # Mock Excel data
        import pandas as pd
        mock_excel_data = {
            'Standard 70 perfect': pd.DataFrame({
                'Pages': [50, 100, 200, 300],
                'SpineWidth': [0.125, 0.25, 0.5, 0.75]
            })
        }
        mock_read_excel.return_value = mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            # Test below minimum
            spine_width = self.calculator.calculate_spine_width_from_lookup(25)
            assert spine_width == 0.125  # Minimum value
            
            # Test above maximum
            spine_width = self.calculator.calculate_spine_width_from_lookup(500)
            assert spine_width == 0.75  # Maximum value
            
            # Test exact match
            spine_width = self.calculator.calculate_spine_width_from_lookup(100)
            assert spine_width == 0.25
            
            # Test interpolation
            spine_width = self.calculator.calculate_spine_width_from_lookup(150)
            assert spine_width == 0.5  # Next higher value
    
    def test_error_handling_in_integration(self):
        """Test error handling during integration scenarios"""
        # Test with invalid metadata
        invalid_metadata = None
        
        # Should not raise exception
        self.calculator.distribute_spine_width(0.5, invalid_metadata)
        
        # Test with metadata that raises exception
        problematic_metadata = Mock()
        problematic_metadata.__setattr__ = Mock(side_effect=Exception("Test error"))
        
        # Should handle exception gracefully
        self.calculator.distribute_spine_width(0.5, problematic_metadata)
    
    @patch('pandas.read_excel')
    def test_different_paper_types(self, mock_read_excel):
        """Test spine width calculation with different paper types"""
        # Mock Excel data for different paper types
        import pandas as pd
        mock_excel_data = {
            'Standard 70 perfect': pd.DataFrame({
                'Pages': [200],
                'SpineWidth': [0.5]
            }),
            'Standard Color 50 Perfect': pd.DataFrame({
                'Pages': [200],
                'SpineWidth': [0.4]
            })
        }
        mock_read_excel.return_value = mock_excel_data
        
        with patch.object(Path, 'exists', return_value=True):
            # Test default paper type
            spine_width1 = self.calculator.calculate_spine_width_from_lookup(200)
            assert spine_width1 == 0.5
            
            # Test specific paper type
            spine_width2 = self.calculator.calculate_spine_width_from_lookup(200, 'Standard Color 50 Perfect')
            assert spine_width2 == 0.4
    
    def test_caching_behavior_in_integration(self):
        """Test that caching works properly in integration scenarios"""
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock Excel data
            import pandas as pd
            mock_excel_data = {
                'Standard 70 perfect': pd.DataFrame({
                    'Pages': [200],
                    'SpineWidth': [0.5]
                })
            }
            mock_read_excel.return_value = mock_excel_data
            
            with patch.object(Path, 'exists', return_value=True):
                # First calculation should load data
                spine_width1 = self.calculator.calculate_spine_width_from_lookup(200)
                
                # Second calculation should use cache
                spine_width2 = self.calculator.calculate_spine_width_from_lookup(200)
                
                # Should only call read_excel once due to caching
                assert mock_read_excel.call_count == 1
                assert spine_width1 == spine_width2 == 0.5
    
    def test_spine_width_range_functionality(self):
        """Test spine width range functionality for validation"""
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock Excel data
            import pandas as pd
            mock_excel_data = {
                'Standard 70 perfect': pd.DataFrame({
                    'Pages': [50, 100, 200, 300],
                    'SpineWidth': [0.125, 0.25, 0.5, 0.75]
                })
            }
            mock_read_excel.return_value = mock_excel_data
            
            with patch.object(Path, 'exists', return_value=True):
                min_width, max_width = self.calculator.get_spine_width_range()
                
                assert min_width == 0.125
                assert max_width == 0.75
    
    def test_available_paper_types_functionality(self):
        """Test getting available paper types for configuration"""
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock Excel data
            import pandas as pd
            mock_excel_data = {
                'Standard 70 perfect': pd.DataFrame({'Pages': [200], 'SpineWidth': [0.5]}),
                'Standard Color 50 Perfect': pd.DataFrame({'Pages': [200], 'SpineWidth': [0.4]}),
                'Premium 80 Perfect': pd.DataFrame({'Pages': [200], 'SpineWidth': [0.6]})
            }
            mock_read_excel.return_value = mock_excel_data
            
            with patch.object(Path, 'exists', return_value=True):
                paper_types = self.calculator.get_available_paper_types()
                
                expected_types = ['Standard 70 perfect', 'Standard Color 50 Perfect', 'Premium 80 Perfect']
                assert set(paper_types) == set(expected_types)


if __name__ == "__main__":
    pytest.main([__file__])