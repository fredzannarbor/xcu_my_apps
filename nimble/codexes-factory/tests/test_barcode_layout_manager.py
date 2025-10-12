"""
Tests for BarcodeLayoutManager class.

Tests positioning calculations, composite layout system, safety margin validation,
and back cover position calculation accounting for spine width.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.covers.barcode_layout_manager import (
    BarcodeLayoutManager,
    Position,
    Size,
    Rectangle,
    CoverSpecs,
    SafetyMargins,
    LayoutData
)


class TestBarcodeLayoutManager:
    """Test suite for BarcodeLayoutManager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.layout_manager = BarcodeLayoutManager()
        
        # Standard cover specs for testing
        self.standard_cover_specs = CoverSpecs(
            width=6.0,
            height=9.0,
            spine_width=0.5,
            bleed=0.125,
            back_cover_area=Rectangle(x=0, y=0, width=6.0, height=9.0, unit="inches"),
            unit="inches"
        )
        
        # Mock barcode and price block data
        self.mock_barcode_data = Mock()
        self.mock_barcode_data.dimensions = Size(width=3.0, height=1.5, unit="inches")
        
        self.mock_price_block = Mock()
        self.mock_price_block.dimensions = Size(width=0.75, height=1.5, unit="inches")
    
    def test_initialization(self):
        """Test BarcodeLayoutManager initialization"""
        manager = BarcodeLayoutManager()
        
        assert manager.standard_barcode_size.width == 3.0
        assert manager.standard_barcode_size.height == 1.5
        assert manager.standard_price_block_size.width == 0.75
        assert manager.standard_price_block_size.height == 1.5
        assert manager.barcode_price_gap == 0.1
        assert manager.preferred_position == "bottom_right"
    
    def test_initialization_with_config(self):
        """Test BarcodeLayoutManager initialization with custom config"""
        config = {"custom_setting": "value"}
        manager = BarcodeLayoutManager(config)
        
        assert manager.config == config
    
    def test_calculate_optimal_position_standard_cover(self):
        """Test optimal position calculation for standard cover size"""
        position = self.layout_manager.calculate_optimal_position(self.standard_cover_specs)
        
        # Should be in bottom-right corner with safety margins
        expected_total_width = 3.0 + 0.75 + 0.1  # barcode + price block + gap
        expected_x = 6.0 - expected_total_width - 0.125  # cover width - layout width - right margin
        expected_y = 0.125  # bottom margin
        
        assert position.x == pytest.approx(expected_x, abs=0.01)
        assert position.y == pytest.approx(expected_y, abs=0.01)
        assert position.unit == "inches"
    
    def test_calculate_optimal_position_small_cover(self):
        """Test optimal position calculation for small cover that requires adjustment"""
        small_cover_specs = CoverSpecs(
            width=4.0,  # Smaller width
            height=6.0,
            spine_width=0.3,
            bleed=0.125,
            back_cover_area=Rectangle(x=0, y=0, width=4.0, height=6.0, unit="inches"),
            unit="inches"
        )
        
        position = self.layout_manager.calculate_optimal_position(small_cover_specs)
        
        # Should adjust to fit within smaller cover
        assert position.x >= 0.125  # At least left margin
        assert position.y >= 0.125  # At least bottom margin
        assert position.unit == "inches"
    
    def test_create_composite_barcode_layout(self):
        """Test creation of composite barcode layout"""
        layout_data = self.layout_manager.create_composite_barcode_layout(
            self.mock_barcode_data,
            self.mock_price_block,
            self.standard_cover_specs
        )
        
        assert isinstance(layout_data, LayoutData)
        assert layout_data.barcode_data == self.mock_barcode_data
        assert layout_data.price_block == self.mock_price_block
        
        # Check positioning relationships
        assert layout_data.price_block_position.x > layout_data.barcode_position.x
        assert layout_data.price_block_position.y == layout_data.barcode_position.y
        
        # Check ISBN text position (should be centered below barcode)
        expected_text_x = layout_data.barcode_position.x + (3.0 / 2)  # Center of barcode
        assert layout_data.isbn_text_position.x == pytest.approx(expected_text_x, abs=0.01)
        assert layout_data.isbn_text_position.y < layout_data.barcode_position.y  # Below barcode
    
    def test_validate_positioning_valid(self):
        """Test positioning validation with valid position"""
        valid_position = Position(x=2.0, y=0.5, unit="inches")
        
        is_valid = self.layout_manager.validate_positioning(valid_position, self.standard_cover_specs)
        
        assert is_valid is True
    
    def test_validate_positioning_invalid_left_margin(self):
        """Test positioning validation with invalid left margin"""
        invalid_position = Position(x=0.05, y=0.5, unit="inches")  # Too close to left edge
        
        is_valid = self.layout_manager.validate_positioning(invalid_position, self.standard_cover_specs)
        
        assert is_valid is False
    
    def test_validate_positioning_invalid_right_margin(self):
        """Test positioning validation with invalid right margin"""
        invalid_position = Position(x=5.5, y=0.5, unit="inches")  # Too close to right edge
        
        is_valid = self.layout_manager.validate_positioning(invalid_position, self.standard_cover_specs)
        
        assert is_valid is False
    
    def test_validate_positioning_invalid_bottom_margin(self):
        """Test positioning validation with invalid bottom margin"""
        invalid_position = Position(x=2.0, y=0.05, unit="inches")  # Too close to bottom edge
        
        is_valid = self.layout_manager.validate_positioning(invalid_position, self.standard_cover_specs)
        
        assert is_valid is False
    
    def test_validate_positioning_invalid_top_margin(self):
        """Test positioning validation with invalid top margin"""
        invalid_position = Position(x=2.0, y=8.5, unit="inches")  # Too close to top edge
        
        is_valid = self.layout_manager.validate_positioning(invalid_position, self.standard_cover_specs)
        
        assert is_valid is False
    
    def test_generate_safety_margins_default(self):
        """Test generation of default safety margins"""
        margins = self.layout_manager.generate_safety_margins()
        
        assert margins.top == 0.125
        assert margins.bottom == 0.125
        assert margins.left == 0.125
        assert margins.right == 0.125
        assert margins.unit == "inches"
    
    def test_generate_safety_margins_custom(self):
        """Test generation of custom safety margins"""
        custom_margins = {
            'top': 0.25,
            'bottom': 0.25,
            'left': 0.2,
            'right': 0.2,
            'unit': 'inches'
        }
        
        margins = self.layout_manager.generate_safety_margins(custom_margins)
        
        assert margins.top == 0.25
        assert margins.bottom == 0.25
        assert margins.left == 0.2
        assert margins.right == 0.2
        assert margins.unit == "inches"
    
    def test_adjust_position_for_conflicts_no_conflicts(self):
        """Test position adjustment when there are no conflicts"""
        initial_position = Position(x=2.0, y=0.5, unit="inches")
        
        adjusted_position = self.layout_manager.adjust_position_for_conflicts(
            initial_position, 
            self.standard_cover_specs
        )
        
        assert adjusted_position.x == initial_position.x
        assert adjusted_position.y == initial_position.y
    
    def test_adjust_position_for_conflicts_with_text_area(self):
        """Test position adjustment when there are text area conflicts"""
        initial_position = Position(x=2.0, y=0.5, unit="inches")
        
        # Create conflicting text area
        text_areas = [
            Rectangle(x=1.5, y=0.3, width=2.0, height=1.0, unit="inches")
        ]
        
        adjusted_position = self.layout_manager.adjust_position_for_conflicts(
            initial_position, 
            self.standard_cover_specs,
            text_areas
        )
        
        # Position should be adjusted to avoid conflict
        assert adjusted_position.y != initial_position.y or adjusted_position.x != initial_position.x
    
    def test_get_layout_specifications(self):
        """Test getting layout specifications"""
        specs = self.layout_manager.get_layout_specifications()
        
        assert 'barcode_dimensions' in specs
        assert 'price_block_dimensions' in specs
        assert 'safety_margins' in specs
        assert 'gaps' in specs
        assert 'positioning' in specs
        
        assert specs['barcode_dimensions']['width'] == 3.0
        assert specs['barcode_dimensions']['height'] == 1.5
        assert specs['price_block_dimensions']['width'] == 0.75
        assert specs['gaps']['barcode_price_gap'] == 0.1


class TestCoverSpecs:
    """Test suite for CoverSpecs class"""
    
    def test_from_dict_standard(self):
        """Test CoverSpecs creation from dictionary"""
        specs_dict = {
            'width': 6.0,
            'height': 9.0,
            'spine_width': 0.5,
            'bleed': 0.125,
            'unit': 'inches'
        }
        
        cover_specs = CoverSpecs.from_dict(specs_dict)
        
        assert cover_specs.width == 6.0
        assert cover_specs.height == 9.0
        assert cover_specs.spine_width == 0.5
        assert cover_specs.bleed == 0.125
        assert cover_specs.unit == 'inches'
        assert cover_specs.back_cover_area.width == 6.0
        assert cover_specs.back_cover_area.height == 9.0
    
    def test_from_dict_defaults(self):
        """Test CoverSpecs creation with default values"""
        specs_dict = {}
        
        cover_specs = CoverSpecs.from_dict(specs_dict)
        
        assert cover_specs.width == 6.0  # Default
        assert cover_specs.height == 9.0  # Default
        assert cover_specs.spine_width == 0.5  # Default
        assert cover_specs.bleed == 0.125  # Default
        assert cover_specs.unit == 'inches'  # Default


class TestRectangle:
    """Test suite for Rectangle class"""
    
    def test_rectangle_properties(self):
        """Test Rectangle property calculations"""
        rect = Rectangle(x=1.0, y=2.0, width=3.0, height=4.0, unit="inches")
        
        assert rect.left == 1.0
        assert rect.right == 4.0
        assert rect.bottom == 2.0
        assert rect.top == 6.0
    
    def test_contains_point_inside(self):
        """Test point containment for point inside rectangle"""
        rect = Rectangle(x=1.0, y=2.0, width=3.0, height=4.0, unit="inches")
        
        assert rect.contains_point(2.0, 3.0) is True
        assert rect.contains_point(1.0, 2.0) is True  # Bottom-left corner
        assert rect.contains_point(4.0, 6.0) is True  # Top-right corner
    
    def test_contains_point_outside(self):
        """Test point containment for point outside rectangle"""
        rect = Rectangle(x=1.0, y=2.0, width=3.0, height=4.0, unit="inches")
        
        assert rect.contains_point(0.5, 3.0) is False  # Left of rectangle
        assert rect.contains_point(5.0, 3.0) is False  # Right of rectangle
        assert rect.contains_point(2.0, 1.0) is False  # Below rectangle
        assert rect.contains_point(2.0, 7.0) is False  # Above rectangle
    
    def test_overlaps_with_overlapping(self):
        """Test rectangle overlap detection for overlapping rectangles"""
        rect1 = Rectangle(x=1.0, y=1.0, width=3.0, height=3.0, unit="inches")
        rect2 = Rectangle(x=2.0, y=2.0, width=3.0, height=3.0, unit="inches")
        
        assert rect1.overlaps_with(rect2) is True
        assert rect2.overlaps_with(rect1) is True
    
    def test_overlaps_with_non_overlapping(self):
        """Test rectangle overlap detection for non-overlapping rectangles"""
        rect1 = Rectangle(x=1.0, y=1.0, width=2.0, height=2.0, unit="inches")
        rect2 = Rectangle(x=4.0, y=4.0, width=2.0, height=2.0, unit="inches")
        
        assert rect1.overlaps_with(rect2) is False
        assert rect2.overlaps_with(rect1) is False
    
    def test_overlaps_with_touching(self):
        """Test rectangle overlap detection for touching rectangles"""
        rect1 = Rectangle(x=1.0, y=1.0, width=2.0, height=2.0, unit="inches")
        rect2 = Rectangle(x=3.0, y=1.0, width=2.0, height=2.0, unit="inches")
        
        # Touching rectangles should not be considered overlapping
        assert rect1.overlaps_with(rect2) is False
        assert rect2.overlaps_with(rect1) is False


class TestSafetyMargins:
    """Test suite for SafetyMargins class"""
    
    def test_standard_margins(self):
        """Test standard safety margins creation"""
        margins = SafetyMargins.standard_margins()
        
        assert margins.top == 0.125
        assert margins.bottom == 0.125
        assert margins.left == 0.125
        assert margins.right == 0.125
        assert margins.unit == "inches"


if __name__ == "__main__":
    pytest.main([__file__])