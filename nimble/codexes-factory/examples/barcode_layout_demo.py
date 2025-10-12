#!/usr/bin/env python3
"""
Demonstration of BarcodeLayoutManager functionality.

This script shows how to use the BarcodeLayoutManager for proper barcode positioning
on book covers, including composite layout with price blocks and safety margin validation.
"""

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
    SafetyMargins
)

from codexes.modules.distribution.isbn_barcode_generator import (
    ISBNBarcodeGenerator
)


def demonstrate_basic_positioning():
    """Demonstrate basic barcode positioning calculations"""
    print("=== Basic Barcode Positioning Demo ===")
    
    # Initialize layout manager
    layout_manager = BarcodeLayoutManager()
    
    # Define standard cover specifications
    cover_specs = CoverSpecs(
        width=6.0,
        height=9.0,
        spine_width=0.5,
        bleed=0.125,
        back_cover_area=Rectangle(x=0, y=0, width=6.0, height=9.0, unit="inches"),
        unit="inches"
    )
    
    # Calculate optimal position
    optimal_position = layout_manager.calculate_optimal_position(cover_specs)
    
    print(f"Cover dimensions: {cover_specs.width}\" x {cover_specs.height}\"")
    print(f"Spine width: {cover_specs.spine_width}\"")
    print(f"Optimal barcode position: ({optimal_position.x:.3f}\", {optimal_position.y:.3f}\")")
    
    # Validate positioning
    is_valid = layout_manager.validate_positioning(optimal_position, cover_specs)
    print(f"Position validation: {'PASSED' if is_valid else 'FAILED'}")
    
    print()


def demonstrate_composite_layout():
    """Demonstrate composite layout with barcode, price block, and text"""
    print("=== Composite Layout Demo ===")
    
    # Initialize components
    layout_manager = BarcodeLayoutManager()
    barcode_generator = ISBNBarcodeGenerator({'format': 'UPC-A'})
    
    # Test ISBN and cover specs
    test_isbn = "9781234567890"
    cover_specs = CoverSpecs.from_dict({
        'width': 6.0,
        'height': 9.0,
        'spine_width': 0.5,
        'bleed': 0.125
    })
    
    # Generate barcode and price block data
    barcode_data = barcode_generator.generate_standard_upc_barcode(test_isbn)
    price_block = barcode_generator.create_price_block_area("24.99")
    
    # Create composite layout
    layout_data = layout_manager.create_composite_barcode_layout(
        barcode_data,
        price_block,
        cover_specs
    )
    
    print(f"ISBN: {test_isbn}")
    print(f"UPC Code: {barcode_data.upc_code}")
    print(f"ISBN Display Text: {barcode_data.isbn_display_text}")
    print(f"Price: {price_block.price_text}")
    print()
    print("Layout Positioning:")
    print(f"  Barcode position: ({layout_data.barcode_position.x:.3f}\", {layout_data.barcode_position.y:.3f}\")")
    print(f"  Price block position: ({layout_data.price_block_position.x:.3f}\", {layout_data.price_block_position.y:.3f}\")")
    print(f"  ISBN text position: ({layout_data.isbn_text_position.x:.3f}\", {layout_data.isbn_text_position.y:.3f}\")")
    print(f"  Total layout dimensions: {layout_data.total_dimensions.width:.3f}\" x {layout_data.total_dimensions.height:.3f}\"")
    
    print()


def demonstrate_small_cover_adjustment():
    """Demonstrate position adjustment for small covers"""
    print("=== Small Cover Adjustment Demo ===")
    
    layout_manager = BarcodeLayoutManager()
    
    # Small cover that will require adjustment
    small_cover_specs = CoverSpecs(
        width=4.5,  # Smaller width
        height=6.0,
        spine_width=0.3,
        bleed=0.125,
        back_cover_area=Rectangle(x=0, y=0, width=4.5, height=6.0, unit="inches"),
        unit="inches"
    )
    
    # Calculate position for small cover
    position = layout_manager.calculate_optimal_position(small_cover_specs)
    
    print(f"Small cover dimensions: {small_cover_specs.width}\" x {small_cover_specs.height}\"")
    print(f"Adjusted barcode position: ({position.x:.3f}\", {position.y:.3f}\")")
    
    # Validate the adjusted position
    is_valid = layout_manager.validate_positioning(position, small_cover_specs)
    print(f"Adjusted position validation: {'PASSED' if is_valid else 'FAILED'}")
    
    # Show safety margins
    margins = layout_manager.generate_safety_margins()
    print(f"Safety margins: L:{margins.left}\" R:{margins.right}\" B:{margins.bottom}\" T:{margins.top}\"")
    
    print()


def demonstrate_conflict_resolution():
    """Demonstrate position adjustment for text area conflicts"""
    print("=== Conflict Resolution Demo ===")
    
    layout_manager = BarcodeLayoutManager()
    
    cover_specs = CoverSpecs.from_dict({
        'width': 6.0,
        'height': 9.0,
        'spine_width': 0.5,
        'bleed': 0.125
    })
    
    # Initial position
    initial_position = Position(x=2.0, y=0.5, unit="inches")
    
    # Define conflicting text areas (e.g., back cover blurb)
    text_areas = [
        Rectangle(x=1.5, y=0.3, width=2.5, height=1.2, unit="inches"),  # Overlaps with barcode area
    ]
    
    print(f"Initial position: ({initial_position.x:.3f}\", {initial_position.y:.3f}\")")
    print(f"Text area conflict: {text_areas[0].x:.1f}\", {text_areas[0].y:.1f}\" - {text_areas[0].width:.1f}\" x {text_areas[0].height:.1f}\"")
    
    # Adjust position to avoid conflicts
    adjusted_position = layout_manager.adjust_position_for_conflicts(
        initial_position,
        cover_specs,
        text_areas
    )
    
    print(f"Adjusted position: ({adjusted_position.x:.3f}\", {adjusted_position.y:.3f}\")")
    
    # Validate final position
    is_valid = layout_manager.validate_positioning(adjusted_position, cover_specs)
    print(f"Final position validation: {'PASSED' if is_valid else 'FAILED'}")
    
    print()


def demonstrate_integration_with_generator():
    """Demonstrate integration with ISBNBarcodeGenerator"""
    print("=== Integration with Barcode Generator Demo ===")
    
    # Initialize barcode generator (it will automatically use layout manager if available)
    barcode_generator = ISBNBarcodeGenerator({'format': 'UPC-A'})
    
    # Test with different cover sizes
    test_cases = [
        {'name': 'Standard Trade', 'width': 6.0, 'height': 9.0, 'spine': 0.5},
        {'name': 'Mass Market', 'width': 4.25, 'height': 6.875, 'spine': 0.375},
        {'name': 'Large Format', 'width': 8.5, 'height': 11.0, 'spine': 0.75},
    ]
    
    test_isbn = "9781234567890"
    
    for case in test_cases:
        print(f"{case['name']} ({case['width']}\" x {case['height']}\"):")
        
        cover_specs_dict = {
            'width': case['width'],
            'height': case['height'],
            'spine_width': case['spine'],
            'bleed': 0.125
        }
        
        # Generate barcode with positioning
        barcode_result = barcode_generator.generate_upc_barcode_with_positioning(
            test_isbn,
            cover_specs_dict,
            "19.99"
        )
        
        print(f"  Position: ({barcode_result.position.x:.3f}\", {barcode_result.position.y:.3f}\")")
        print(f"  UPC Code: {barcode_result.barcode_data.upc_code}")
        print(f"  Price: {barcode_result.price_block.price_text}")
        print()


def demonstrate_layout_specifications():
    """Show layout specifications and standards"""
    print("=== Layout Specifications ===")
    
    layout_manager = BarcodeLayoutManager()
    specs = layout_manager.get_layout_specifications()
    
    print("Barcode Dimensions:")
    print(f"  Width: {specs['barcode_dimensions']['width']}\"")
    print(f"  Height: {specs['barcode_dimensions']['height']}\"")
    
    print("\nPrice Block Dimensions:")
    print(f"  Width: {specs['price_block_dimensions']['width']}\"")
    print(f"  Height: {specs['price_block_dimensions']['height']}\"")
    
    print("\nSafety Margins:")
    print(f"  Top: {specs['safety_margins']['top']}\"")
    print(f"  Bottom: {specs['safety_margins']['bottom']}\"")
    print(f"  Left: {specs['safety_margins']['left']}\"")
    print(f"  Right: {specs['safety_margins']['right']}\"")
    
    print("\nGaps and Spacing:")
    print(f"  Barcode-Price Gap: {specs['gaps']['barcode_price_gap']}\"")
    
    print(f"\nPreferred Position: {specs['positioning']['preferred_position']}")
    print(f"Validation Enabled: {specs['positioning']['validation_enabled']}")
    
    print()


def main():
    """Run all demonstrations"""
    print("BarcodeLayoutManager Demonstration")
    print("=" * 50)
    print()
    
    try:
        demonstrate_basic_positioning()
        demonstrate_composite_layout()
        demonstrate_small_cover_adjustment()
        demonstrate_conflict_resolution()
        demonstrate_integration_with_generator()
        demonstrate_layout_specifications()
        
        print("All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()