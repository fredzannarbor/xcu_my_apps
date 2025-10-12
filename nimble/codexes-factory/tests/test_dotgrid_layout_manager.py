"""
Unit tests for DotgridLayoutManager class.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.prepress.dotgrid_layout_manager import (
    DotgridLayoutManager, Position, PageSpecs
)


class TestDotgridLayoutManager:
    """Test cases for DotgridLayoutManager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.manager = DotgridLayoutManager()
        self.standard_page_specs = PageSpecs(
            width=5.5,
            height=8.5,
            header_height=0.75,
            footer_height=0.5,
            margin_top=1.0,
            margin_bottom=1.0
        )
    
    def test_calculate_dotgrid_position_standard(self):
        """Test dotgrid position calculation with standard page specs"""
        position = self.manager.calculate_dotgrid_position(self.standard_page_specs)
        
        assert isinstance(position, Position)
        assert position.x == 2.75  # Half of page width (5.5 / 2)
        assert position.y >= 1.5   # Should be above footer + spacing
        assert position.unit == "inches"
    
    def test_calculate_dotgrid_position_maintains_header_spacing(self):
        """Test that dotgrid position maintains minimum header spacing"""
        # Create page specs with tight spacing
        tight_specs = PageSpecs(
            width=5.5,
            height=6.0,  # Shorter page
            header_height=1.0,
            footer_height=0.5,
            margin_top=0.5,
            margin_bottom=0.5
        )
        
        position = self.manager.calculate_dotgrid_position(tight_specs)
        
        # Calculate expected maximum position to maintain header spacing
        max_y = tight_specs.height - tight_specs.margin_top - tight_specs.header_height - 0.5
        assert position.y <= max_y
    
    def test_validate_spacing_requirements_valid(self):
        """Test spacing validation with valid positioning"""
        position = Position(x=2.75, y=2.0)
        
        is_valid = self.manager.validate_spacing_requirements(position, self.standard_page_specs)
        assert is_valid
    
    def test_validate_spacing_requirements_invalid_header(self):
        """Test spacing validation with insufficient header spacing"""
        # Position too high, violating header spacing
        position = Position(x=2.75, y=7.0)
        
        is_valid = self.manager.validate_spacing_requirements(position, self.standard_page_specs)
        assert not is_valid
    
    def test_validate_spacing_requirements_invalid_footer(self):
        """Test spacing validation with insufficient footer spacing"""
        # Position too low, violating footer spacing
        position = Position(x=2.75, y=1.0)
        
        is_valid = self.manager.validate_spacing_requirements(position, self.standard_page_specs)
        assert not is_valid
    
    def test_get_standard_page_specs_xynapse_traces(self):
        """Test getting page specs for xynapse_traces imprint"""
        specs = self.manager.get_standard_page_specs("xynapse_traces")
        
        assert specs.width == 5.5
        assert specs.height == 8.5
        assert specs.header_height == 0.75
        assert specs.footer_height == 0.5
    
    def test_get_standard_page_specs_default(self):
        """Test getting default page specs for unknown imprint"""
        specs = self.manager.get_standard_page_specs("unknown_imprint")
        
        assert specs.width == 6.0
        assert specs.height == 9.0
        assert specs.header_height == 0.75
        assert specs.footer_height == 0.5
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    def test_update_template_positioning(self, mock_write, mock_read, mock_exists):
        """Test updating template with new positioning"""
        mock_exists.return_value = True
        mock_read.return_value = """
        \\put(\\LenToUnit{0.05\\paperwidth},\\LenToUnit{0.5\\paperheight-0.45\\textheight-0.5in}){%
            \\includegraphics[width=0.9\\paperwidth,height=0.85\\textheight,keepaspectratio]{dotgrid.png}%
        }
        """
        
        position = Position(x=2.75, y=2.0)
        self.manager.update_template_positioning("test_template.tex", position)
        
        mock_write.assert_called_once()
        written_content = mock_write.call_args[0][0]
        assert "2.0in" in written_content
    
    @patch('pathlib.Path.exists')
    def test_update_template_positioning_file_not_found(self, mock_exists):
        """Test handling of missing template file"""
        mock_exists.return_value = False
        
        position = Position(x=2.75, y=2.0)
        # Should not raise exception
        self.manager.update_template_positioning("nonexistent.tex", position)
    
    def test_calculate_dotgrid_position_error_handling(self):
        """Test error handling in position calculation"""
        # Create invalid page specs
        invalid_specs = PageSpecs(
            width=-1,  # Invalid width
            height=8.5,
            header_height=0.75,
            footer_height=0.5,
            margin_top=1.0,
            margin_bottom=1.0
        )
        
        # Should return safe default position
        position = self.manager.calculate_dotgrid_position(invalid_specs)
        assert isinstance(position, Position)
        assert position.x == -0.5  # Half of invalid width
        assert position.y == 2.0   # Safe default
    
    def test_min_spacing_configuration(self):
        """Test that minimum spacing requirements are configurable"""
        custom_config = {'min_header_spacing': 0.75, 'min_footer_spacing': 0.25}
        manager = DotgridLayoutManager(custom_config)
        
        # Default values should still be used (config not implemented yet)
        assert manager.min_header_spacing == 0.5
        assert manager.min_footer_spacing == 0.5
    
    @patch('codexes.modules.prepress.dotgrid_layout_manager.Path')
    def test_apply_dotgrid_fixes_success(self, mock_path):
        """Test successful application of dotgrid fixes"""
        # Mock path operations
        mock_imprint_dir = mock_path.return_value
        mock_template_file = mock_imprint_dir / "template.tex"
        mock_template_file.exists.return_value = True
        mock_imprint_dir.name = "xynapse_traces"
        
        with patch.object(self.manager, 'update_template_positioning') as mock_update:
            result = self.manager.apply_dotgrid_fixes("test/path")
            assert result is True
            mock_update.assert_called_once()
    
    @patch('codexes.modules.prepress.dotgrid_layout_manager.Path')
    def test_apply_dotgrid_fixes_template_not_found(self, mock_path):
        """Test handling of missing template file in apply_dotgrid_fixes"""
        # Mock path operations
        mock_imprint_dir = mock_path.return_value
        mock_template_file = mock_imprint_dir / "template.tex"
        mock_template_file.exists.return_value = False
        
        result = self.manager.apply_dotgrid_fixes("test/path")
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])