"""
Integration tests for BarcodeLayoutManager with ISBNBarcodeGenerator.

Tests the integration between the layout manager and barcode generator
to ensure proper positioning and composite layout functionality.
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

from codexes.modules.distribution.isbn_barcode_generator import (
    ISBNBarcodeGenerator,
    BarcodeData,
    PriceBlockData,
    BarcodeResult
)


class TestBarcodeLayoutIntegration:
    """Integration tests for barcode layout and generation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.layout_manager = BarcodeLayoutManager()
        
        # Mock barcode config for generator
        barcode_config = {
            'format': 'UPC-A',
            'width': '3cm',
            'height': '1.5cm'
        }
        self.barcode_generator = ISBNBarcodeGenerator(barcode_config)
        
        # Standard cover specs
        self.cover_specs = CoverSpecs(
            width=6.0,
            height=9.0,
            spine_width=0.5,
            bleed=0.125,
            back_cover_area=Rectangle(x=0, y=0, width=6.0, height=9.0, unit="inches"),
            unit="inches"
        )
        
        # Test ISBN
        self.test_isbn = "9781234567890"
    
    def test_layout_manager_with_generated_barcode(self):
        """Test layout manager using actual generated barcode data"""
        # Generate barcode data
        barcode_data = self.barcode_generator.generate_standard_upc_barcode(self.test_isbn)
        price_block = self.barcode_generator.create_price_block_area("19.99")
        
        # Create composite layout
        layout_data = self.layout_manager.create_composite_barcode_layout(
            barcode_data,
            price_block,
            self.cover_specs
        )
        
        # Verify layout data structure
        assert isinstance(layout_data, LayoutData)
        assert layout_data.barcode_data == barcode_data
        assert layout_data.price_block == price_block
        
        # Verify positioning is valid
        assert self.layout_manager.validate_positioning(
            layout_data.barcode_position, 
            self.cover_specs
        )
        
        # Verify price block is positioned correctly relative to barcode
        expected_price_x = (
            layout_data.barcode_position.x + 
            self.layout_manager.standard_barcode_size.width + 
            self.layout_manager.barcode_price_gap
        )
        assert layout_data.price_block_position.x == pytest.approx(expected_price_x, abs=0.01)
        assert layout_data.price_block_position.y == layout_data.barcode_position.y
    
    def test_barcode_generator_with_layout_positioning(self):
        """Test barcode generator using layout manager for positioning"""
        # Create cover specs dictionary for generator
        cover_specs_dict = {
            'width': self.cover_specs.width,
            'height': self.cover_specs.height,
            'spine_width': self.cover_specs.spine_width,
            'bleed': self.cover_specs.bleed
        }
        
        # Generate barcode with positioning
        barcode_result = self.barcode_generator.generate_upc_barcode_with_positioning(
            self.test_isbn,
            cover_specs_dict,
            "24.99"
        )
        
        # Verify result structure
        assert isinstance(barcode_result, BarcodeResult)
        assert barcode_result.barcode_data.upc_code.startswith('978')
        assert barcode_result.price_block.price_text == "$24.99"
        
        # Verify positioning is within cover bounds
        total_width = (
            self.layout_manager.standard_barcode_size.width +
            self.layout_manager.standard_price_block_size.width +
            self.layout_manager.barcode_price_gap
        )
        
        assert barcode_result.position.x >= self.layout_manager.safety_margins.left
        assert (barcode_result.position.x + total_width <= 
                self.cover_specs.width - self.layout_manager.safety_margins.right)
        assert barcode_result.position.y >= self.layout_manager.safety_margins.bottom
        assert (barcode_result.position.y + self.layout_manager.standard_barcode_size.height <= 
                self.cover_specs.height - self.layout_manager.safety_margins.top)
    
    def test_layout_validation_with_generator_data(self):
        """Test layout validation using generator-produced data"""
        # Generate barcode data
        barcode_data = self.barcode_generator.generate_standard_upc_barcode(self.test_isbn)
        price_block = self.barcode_generator.create_price_block_area()
        
        # Calculate optimal position
        optimal_position = self.layout_manager.calculate_optimal_position(self.cover_specs)
        
        # Validate the position
        is_valid = self.layout_manager.validate_positioning(optimal_position, self.cover_specs)
        assert is_valid is True
        
        # Create layout and verify total area fits
        layout_data = self.layout_manager.create_composite_barcode_layout(
            barcode_data,
            price_block,
            self.cover_specs
        )
        
        total_area = layout_data.get_total_area()
        assert total_area.left >= 0
        assert total_area.right <= self.cover_specs.width
        assert total_area.bottom >= 0
        assert total_area.top <= self.cover_specs.height
    
    def test_small_cover_adjustment_integration(self):
        """Test integration with small cover that requires position adjustment"""
        # Create small cover specs
        small_cover_specs = CoverSpecs(
            width=4.5,  # Smaller width that will require adjustment
            height=6.0,
            spine_width=0.3,
            bleed=0.125,
            back_cover_area=Rectangle(x=0, y=0, width=4.5, height=6.0, unit="inches"),
            unit="inches"
        )
        
        # Generate barcode with small cover
        cover_specs_dict = {
            'width': small_cover_specs.width,
            'height': small_cover_specs.height,
            'spine_width': small_cover_specs.spine_width,
            'bleed': small_cover_specs.bleed
        }
        
        barcode_result = self.barcode_generator.generate_upc_barcode_with_positioning(
            self.test_isbn,
            cover_specs_dict
        )
        
        # Verify position was adjusted to fit
        assert barcode_result.position.x >= self.layout_manager.safety_margins.left
        
        # Create layout using layout manager
        layout_data = self.layout_manager.create_composite_barcode_layout(
            barcode_result.barcode_data,
            barcode_result.price_block,
            small_cover_specs
        )
        
        # Verify layout fits within small cover
        total_area = layout_data.get_total_area()
        assert total_area.right <= small_cover_specs.width
        assert total_area.top <= small_cover_specs.height
    
    def test_isbn_text_positioning_integration(self):
        """Test ISBN text positioning in integrated layout"""
        # Generate barcode data
        barcode_data = self.barcode_generator.generate_standard_upc_barcode(self.test_isbn)
        price_block = self.barcode_generator.create_price_block_area("15.99")
        
        # Create layout
        layout_data = self.layout_manager.create_composite_barcode_layout(
            barcode_data,
            price_block,
            self.cover_specs
        )
        
        # Verify ISBN text is formatted correctly
        assert "ISBN" in barcode_data.isbn_display_text
        assert "978" in barcode_data.isbn_display_text
        
        # Verify ISBN text position is below barcode and centered
        barcode_center_x = (
            layout_data.barcode_position.x + 
            (self.layout_manager.standard_barcode_size.width / 2)
        )
        assert layout_data.isbn_text_position.x == pytest.approx(barcode_center_x, abs=0.01)
        assert layout_data.isbn_text_position.y < layout_data.barcode_position.y
    
    def test_price_block_integration(self):
        """Test price block creation and positioning integration"""
        # Test with price
        price_block_with_price = self.barcode_generator.create_price_block_area("29.99")
        assert price_block_with_price.price_text == "$29.99"
        
        # Test without price
        price_block_no_price = self.barcode_generator.create_price_block_area()
        assert price_block_no_price.price_text is None
        
        # Create layouts for both
        layout_with_price = self.layout_manager.create_composite_barcode_layout(
            self.barcode_generator.generate_standard_upc_barcode(self.test_isbn),
            price_block_with_price,
            self.cover_specs
        )
        
        layout_no_price = self.layout_manager.create_composite_barcode_layout(
            self.barcode_generator.generate_standard_upc_barcode(self.test_isbn),
            price_block_no_price,
            self.cover_specs
        )
        
        # Both should have same positioning structure
        assert layout_with_price.price_block_position.x == layout_no_price.price_block_position.x
        assert layout_with_price.price_block_position.y == layout_no_price.price_block_position.y
    
    def test_safety_margin_compliance_integration(self):
        """Test that integrated layout respects safety margins"""
        # Generate full barcode result
        cover_specs_dict = {
            'width': self.cover_specs.width,
            'height': self.cover_specs.height,
            'spine_width': self.cover_specs.spine_width,
            'bleed': self.cover_specs.bleed
        }
        
        barcode_result = self.barcode_generator.generate_upc_barcode_with_positioning(
            self.test_isbn,
            cover_specs_dict,
            "19.99"
        )
        
        # Create layout using layout manager
        layout_data = self.layout_manager.create_composite_barcode_layout(
            barcode_result.barcode_data,
            barcode_result.price_block,
            self.cover_specs
        )
        
        # Verify all safety margins are respected
        total_area = layout_data.get_total_area()
        
        # Left margin
        assert total_area.left >= self.layout_manager.safety_margins.left
        
        # Right margin
        assert (self.cover_specs.width - total_area.right >= 
                self.layout_manager.safety_margins.right)
        
        # Bottom margin
        assert total_area.bottom >= self.layout_manager.safety_margins.bottom
        
        # Top margin (barcode height)
        assert (self.cover_specs.height - total_area.top >= 
                self.layout_manager.safety_margins.top)


if __name__ == "__main__":
    pytest.main([__file__])