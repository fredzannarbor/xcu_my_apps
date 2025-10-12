"""
Tests for enhanced UPC-A barcode generation with price blocks and proper formatting.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.distribution.isbn_barcode_generator import (
    ISBNBarcodeGenerator, BarcodeData, PriceBlockData, BarcodeResult
)


class TestEnhancedBarcodeGeneration:
    """Test enhanced UPC-A barcode generation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.generator = ISBNBarcodeGenerator({})
        self.test_isbn = "9781608883684"
        self.test_cover_specs = {'width': 6.0, 'height': 9.0}
    
    def test_standard_upc_barcode_generation(self):
        """Test proper UPC-A barcode generation from ISBN-13"""
        barcode_data = self.generator.generate_standard_upc_barcode(self.test_isbn)
        
        assert isinstance(barcode_data, BarcodeData)
        assert barcode_data.format_type == "UPC-A"
        assert len(barcode_data.upc_code) == 13  # UPC-A is 12 digits + check digit
        assert barcode_data.upc_code.startswith("978")  # Should start with ISBN prefix
        assert barcode_data.isbn_display_text.startswith("ISBN")
        assert len(barcode_data.barcode_image) > 1000  # Should be a substantial image
        assert barcode_data.barcode_image.startswith(b'\x89PNG')  # Should be PNG format
    
    def test_upc_check_digit_calculation(self):
        """Test UPC-A check digit calculation"""
        # Test with known ISBN
        upc_base = "978160888368"  # First 12 digits of ISBN
        check_digit = self.generator._calculate_upc_check_digit(upc_base)
        
        assert isinstance(check_digit, int)
        assert 0 <= check_digit <= 9
        
        # The full UPC should be valid
        full_upc = upc_base + str(check_digit)
        assert len(full_upc) == 13
    
    def test_isbn_display_text_formatting(self):
        """Test ISBN display text formatting"""
        display_text = self.generator.format_isbn_display_text(self.test_isbn)
        
        assert display_text.startswith("ISBN")
        assert "978-1-608883-68-4" in display_text
        assert len(display_text.split("-")) == 5  # Should have 4 hyphens
    
    def test_price_block_creation(self):
        """Test price block area creation"""
        # Test with price
        price_block = self.generator.create_price_block_area("19.99")
        
        assert isinstance(price_block, PriceBlockData)
        assert price_block.price_text == "$19.99"
        assert price_block.dimensions.width == 0.75
        assert price_block.dimensions.height == 1.5
        assert price_block.position_relative_to_barcode.x > 3.0  # Should be to the right
        
        # Test without price
        empty_price_block = self.generator.create_price_block_area()
        assert empty_price_block.price_text is None
        assert empty_price_block.dimensions.width == 0.75
    
    def test_full_barcode_generation_with_positioning(self):
        """Test complete barcode generation with positioning and price block"""
        result = self.generator.generate_upc_barcode_with_positioning(
            self.test_isbn, self.test_cover_specs, "24.99"
        )
        
        assert isinstance(result, BarcodeResult)
        assert isinstance(result.barcode_data, BarcodeData)
        assert isinstance(result.price_block, PriceBlockData)
        
        # Check barcode data
        assert result.barcode_data.format_type == "UPC-A"
        assert result.barcode_data.upc_code.startswith("978")
        
        # Check price block
        assert result.price_block.price_text == "$24.99"
        
        # Check positioning
        assert result.position.x > 0
        assert result.position.y > 0
        assert result.position.x < self.test_cover_specs['width']
        assert result.position.y < self.test_cover_specs['height']
    
    def test_position_calculation_with_total_width(self):
        """Test position calculation accounting for barcode + price block width"""
        total_width = 3.85  # barcode (3.0) + gap (0.1) + price block (0.75)
        position = self.generator.calculate_barcode_position(
            (6.0, 9.0), total_width
        )
        
        # Should account for total width in positioning
        assert position.x < 6.0 - total_width
        assert position.y > 0
    
    def test_safety_space_validation_with_total_width(self):
        """Test safety space validation with total element width"""
        position = self.generator.calculate_barcode_position((6.0, 9.0), 3.85)
        is_valid = self.generator.validate_safety_spaces(position, (6.0, 9.0), 3.85)
        
        assert isinstance(is_valid, bool)
        # Should pass validation for reasonable cover dimensions
        assert is_valid
    
    def test_legacy_method_compatibility(self):
        """Test that legacy methods still work"""
        # Test legacy generate_upc_barcode method
        legacy_bytes = self.generator.generate_upc_barcode(self.test_isbn)
        
        # Test new method
        new_data = self.generator.generate_standard_upc_barcode(self.test_isbn)
        
        # Should produce same image data
        assert legacy_bytes == new_data.barcode_image
        
        # Test legacy format_barcode_numerals method
        legacy_format = self.generator.format_barcode_numerals(self.test_isbn)
        new_format = self.generator.format_isbn_display_text(self.test_isbn)
        
        assert legacy_format == new_format
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test invalid ISBN - should return placeholder, not raise
        result = self.generator.generate_standard_upc_barcode("invalid_isbn")
        assert result.format_type == "PLACEHOLDER"
        
        # Test ISBN not starting with 978/979 - should return placeholder
        result = self.generator.generate_standard_upc_barcode("1234567890123")
        assert result.format_type == "PLACEHOLDER"
    
    def test_placeholder_generation(self):
        """Test placeholder barcode generation"""
        placeholder = self.generator._generate_placeholder_barcode_data("test_isbn")
        
        assert isinstance(placeholder, BarcodeData)
        assert placeholder.format_type == "PLACEHOLDER"
        assert "test_isbn" in placeholder.upc_code
        assert placeholder.isbn_display_text.startswith("ISBN")


if __name__ == "__main__":
    pytest.main([__file__])