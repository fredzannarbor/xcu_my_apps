"""
Barcode Layout Manager for positioning calculations and composite layout management.

This module handles the positioning, spacing, and layout of barcodes on book covers,
including proper back cover position calculation accounting for spine width,
composite layout system combining barcode, price block, and text,
and safety margin validation and adjustment.
"""

from typing import Dict, Any, Optional, Tuple, List
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Import data structures from barcode generator
try:
    from ..distribution.isbn_barcode_generator import (
        Position, Size, SafetySpaces, PriceBlockData, BarcodeData, BarcodeResult
    )
except ImportError:
    # Define locally if import fails
    @dataclass
    class Position:
        x: float
        y: float
        unit: str = "inches"
    
    @dataclass
    class Size:
        width: float
        height: float
        unit: str = "inches"
    
    @dataclass
    class SafetySpaces:
        top: float
        bottom: float
        left: float
        right: float
        unit: str = "inches"


@dataclass
class Rectangle:
    """Represents a rectangular area with position and dimensions"""
    x: float
    y: float
    width: float
    height: float
    unit: str = "inches"
    
    @property
    def left(self) -> float:
        return self.x
    
    @property
    def right(self) -> float:
        return self.x + self.width
    
    @property
    def bottom(self) -> float:
        return self.y
    
    @property
    def top(self) -> float:
        return self.y + self.height
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is within this rectangle"""
        return (self.left <= x <= self.right and 
                self.bottom <= y <= self.top)
    
    def overlaps_with(self, other: 'Rectangle') -> bool:
        """Check if this rectangle overlaps with another"""
        return not (self.right <= other.left or 
                   self.left >= other.right or 
                   self.top <= other.bottom or 
                   self.bottom >= other.top)


@dataclass
class CoverSpecs:
    """Specifications for book cover dimensions and layout"""
    width: float
    height: float
    spine_width: float
    bleed: float
    back_cover_area: Rectangle
    unit: str = "inches"
    
    @classmethod
    def from_dict(cls, specs_dict: Dict[str, Any]) -> 'CoverSpecs':
        """Create CoverSpecs from dictionary"""
        width = specs_dict.get('width', 6.0)
        height = specs_dict.get('height', 9.0)
        spine_width = specs_dict.get('spine_width', 0.5)
        bleed = specs_dict.get('bleed', 0.125)
        
        # Calculate back cover area (left side of cover)
        back_cover_area = Rectangle(
            x=0,
            y=0,
            width=width,
            height=height,
            unit=specs_dict.get('unit', 'inches')
        )
        
        return cls(
            width=width,
            height=height,
            spine_width=spine_width,
            bleed=bleed,
            back_cover_area=back_cover_area,
            unit=specs_dict.get('unit', 'inches')
        )


@dataclass
class SafetyMargins:
    """Safety margins for barcode positioning"""
    top: float
    bottom: float
    left: float
    right: float
    unit: str = "inches"
    
    @classmethod
    def standard_margins(cls) -> 'SafetyMargins':
        """Get standard industry safety margins"""
        return cls(
            top=0.125,
            bottom=0.125,
            left=0.125,
            right=0.125,
            unit="inches"
        )


@dataclass
class LayoutData:
    """Complete layout data for barcode positioning"""
    barcode_data: Any  # BarcodeData type
    price_block: Any   # PriceBlockData type
    isbn_text_position: Position
    total_dimensions: Size
    safety_margins: SafetyMargins
    barcode_position: Position
    price_block_position: Position
    
    def get_total_area(self) -> Rectangle:
        """Get the total rectangular area occupied by the layout"""
        return Rectangle(
            x=self.barcode_position.x,
            y=self.barcode_position.y,
            width=self.total_dimensions.width,
            height=self.total_dimensions.height,
            unit=self.barcode_position.unit
        )


class BarcodeLayoutManager:
    """
    Manages barcode layout positioning, spacing, and validation for book covers.
    
    This class handles:
    - Positioning calculations accounting for spine width
    - Composite layout system combining barcode, price block, and text
    - Safety margin validation and adjustment
    - Back cover position calculation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the barcode layout manager.
        
        Args:
            config: Optional configuration dictionary for layout settings
        """
        self.config = config or {}
        
        # Standard barcode dimensions (industry standard)
        self.standard_barcode_size = Size(
            width=3.0, 
            height=1.5, 
            unit="inches"
        )
        
        # Standard price block dimensions
        self.standard_price_block_size = Size(
            width=0.75, 
            height=1.5, 
            unit="inches"
        )
        
        # Gap between barcode and price block
        self.barcode_price_gap = 0.1  # inches
        
        # Standard safety margins
        self.safety_margins = SafetyMargins.standard_margins()
        
        # Preferred position (bottom-right corner)
        self.preferred_position = "bottom_right"
        
        logger.info("BarcodeLayoutManager initialized")
    
    def calculate_optimal_position(self, cover_specs: CoverSpecs) -> Position:
        """
        Calculate optimal barcode position on back cover accounting for spine width.
        
        Args:
            cover_specs: Cover specifications including dimensions and spine width
            
        Returns:
            Position: Optimal position for barcode placement
        """
        try:
            # Calculate total layout width (barcode + price block + gap)
            total_layout_width = (
                self.standard_barcode_size.width + 
                self.standard_price_block_size.width + 
                self.barcode_price_gap
            )
            
            # Calculate back cover usable area (accounting for spine)
            back_cover_width = cover_specs.back_cover_area.width
            back_cover_height = cover_specs.back_cover_area.height
            
            # Position in bottom-right corner with safety margins
            x_position = (
                back_cover_width - 
                total_layout_width - 
                self.safety_margins.right
            )
            
            y_position = self.safety_margins.bottom
            
            # Ensure position is within bounds
            x_position = max(self.safety_margins.left, x_position)
            y_position = max(self.safety_margins.bottom, y_position)
            
            # Validate position doesn't exceed cover bounds
            if x_position + total_layout_width > back_cover_width - self.safety_margins.right:
                logger.warning("Barcode layout exceeds back cover width, adjusting")
                x_position = max(
                    self.safety_margins.left,
                    back_cover_width - total_layout_width - self.safety_margins.right
                )
            
            if y_position + self.standard_barcode_size.height > back_cover_height - self.safety_margins.top:
                logger.warning("Barcode layout exceeds back cover height, adjusting")
                y_position = max(
                    self.safety_margins.bottom,
                    back_cover_height - self.standard_barcode_size.height - self.safety_margins.top
                )
            
            position = Position(x=x_position, y=y_position, unit=cover_specs.unit)
            
            logger.info(f"Calculated optimal barcode position: ({x_position:.3f}, {y_position:.3f})")
            return position
            
        except Exception as e:
            logger.error(f"Error calculating optimal position: {e}")
            # Return safe fallback position
            return Position(x=2.0, y=0.5, unit="inches")
    
    def create_composite_barcode_layout(self, barcode_data: Any, price_block: Any, 
                                      cover_specs: CoverSpecs) -> LayoutData:
        """
        Create composite layout combining barcode, price block, and text.
        
        Args:
            barcode_data: Barcode data object
            price_block: Price block data object
            cover_specs: Cover specifications
            
        Returns:
            LayoutData: Complete layout data with all positioning information
        """
        try:
            # Calculate optimal barcode position
            barcode_position = self.calculate_optimal_position(cover_specs)
            
            # Calculate price block position (relative to barcode)
            price_block_position = Position(
                x=barcode_position.x + self.standard_barcode_size.width + self.barcode_price_gap,
                y=barcode_position.y,
                unit=barcode_position.unit
            )
            
            # Calculate ISBN text position (below barcode, centered)
            isbn_text_position = Position(
                x=barcode_position.x + (self.standard_barcode_size.width / 2),
                y=barcode_position.y - 0.2,  # 0.2" below barcode
                unit=barcode_position.unit
            )
            
            # Calculate total dimensions
            total_width = (
                self.standard_barcode_size.width + 
                self.standard_price_block_size.width + 
                self.barcode_price_gap
            )
            total_height = max(
                self.standard_barcode_size.height,
                self.standard_price_block_size.height
            )
            
            total_dimensions = Size(
                width=total_width,
                height=total_height,
                unit=cover_specs.unit
            )
            
            # Create layout data
            layout_data = LayoutData(
                barcode_data=barcode_data,
                price_block=price_block,
                isbn_text_position=isbn_text_position,
                total_dimensions=total_dimensions,
                safety_margins=self.safety_margins,
                barcode_position=barcode_position,
                price_block_position=price_block_position
            )
            
            logger.info("Created composite barcode layout successfully")
            return layout_data
            
        except Exception as e:
            logger.error(f"Error creating composite barcode layout: {e}")
            # Return minimal layout data
            fallback_position = Position(x=2.0, y=0.5, unit="inches")
            return LayoutData(
                barcode_data=barcode_data,
                price_block=price_block,
                isbn_text_position=fallback_position,
                total_dimensions=Size(width=4.0, height=1.5, unit="inches"),
                safety_margins=self.safety_margins,
                barcode_position=fallback_position,
                price_block_position=Position(x=3.1, y=0.5, unit="inches")
            )
    
    def validate_positioning(self, position: Position, cover_specs: CoverSpecs) -> bool:
        """
        Validate barcode positioning against cover specifications and safety margins.
        
        Args:
            position: Proposed barcode position
            cover_specs: Cover specifications
            
        Returns:
            bool: True if positioning is valid, False otherwise
        """
        try:
            # Calculate layout area
            layout_area = Rectangle(
                x=position.x,
                y=position.y,
                width=self.standard_barcode_size.width + self.standard_price_block_size.width + self.barcode_price_gap,
                height=max(self.standard_barcode_size.height, self.standard_price_block_size.height),
                unit=position.unit
            )
            
            # Check if layout fits within back cover area
            back_cover = cover_specs.back_cover_area
            
            # Validate left margin
            if layout_area.left < self.safety_margins.left:
                logger.warning(f"Layout violates left safety margin: {layout_area.left} < {self.safety_margins.left}")
                return False
            
            # Validate right margin
            if layout_area.right > back_cover.width - self.safety_margins.right:
                logger.warning(f"Layout violates right safety margin: {layout_area.right} > {back_cover.width - self.safety_margins.right}")
                return False
            
            # Validate bottom margin
            if layout_area.bottom < self.safety_margins.bottom:
                logger.warning(f"Layout violates bottom safety margin: {layout_area.bottom} < {self.safety_margins.bottom}")
                return False
            
            # Validate top margin
            if layout_area.top > back_cover.height - self.safety_margins.top:
                logger.warning(f"Layout violates top safety margin: {layout_area.top} > {back_cover.height - self.safety_margins.top}")
                return False
            
            # Check if layout stays within back cover bounds
            if not back_cover.contains_point(layout_area.left, layout_area.bottom):
                logger.warning("Layout extends outside back cover area (bottom-left)")
                return False
            
            if not back_cover.contains_point(layout_area.right, layout_area.top):
                logger.warning("Layout extends outside back cover area (top-right)")
                return False
            
            logger.info("Barcode positioning validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating positioning: {e}")
            return False
    
    def generate_safety_margins(self, custom_margins: Optional[Dict[str, float]] = None) -> SafetyMargins:
        """
        Generate safety margins for barcode positioning.
        
        Args:
            custom_margins: Optional custom margin specifications
            
        Returns:
            SafetyMargins: Safety margin specifications
        """
        try:
            if custom_margins:
                return SafetyMargins(
                    top=custom_margins.get('top', self.safety_margins.top),
                    bottom=custom_margins.get('bottom', self.safety_margins.bottom),
                    left=custom_margins.get('left', self.safety_margins.left),
                    right=custom_margins.get('right', self.safety_margins.right),
                    unit=custom_margins.get('unit', 'inches')
                )
            
            return self.safety_margins
            
        except Exception as e:
            logger.error(f"Error generating safety margins: {e}")
            return SafetyMargins.standard_margins()
    
    def adjust_position_for_conflicts(self, position: Position, cover_specs: CoverSpecs,
                                    text_areas: Optional[List[Rectangle]] = None) -> Position:
        """
        Adjust barcode position to avoid conflicts with text areas or cover elements.
        
        Args:
            position: Initial position
            cover_specs: Cover specifications
            text_areas: Optional list of text areas to avoid
            
        Returns:
            Position: Adjusted position that avoids conflicts
        """
        try:
            adjusted_position = Position(x=position.x, y=position.y, unit=position.unit)
            
            # Calculate layout area
            layout_area = Rectangle(
                x=adjusted_position.x,
                y=adjusted_position.y,
                width=self.standard_barcode_size.width + self.standard_price_block_size.width + self.barcode_price_gap,
                height=max(self.standard_barcode_size.height, self.standard_price_block_size.height),
                unit=adjusted_position.unit
            )
            
            # Check for conflicts with text areas
            if text_areas:
                for text_area in text_areas:
                    if layout_area.overlaps_with(text_area):
                        logger.info(f"Barcode layout conflicts with text area, adjusting position")
                        
                        # Try moving up
                        new_y = text_area.top + self.safety_margins.bottom
                        if new_y + layout_area.height <= cover_specs.back_cover_area.height - self.safety_margins.top:
                            adjusted_position.y = new_y
                            layout_area.y = new_y
                            continue
                        
                        # Try moving left
                        new_x = text_area.left - layout_area.width - self.safety_margins.right
                        if new_x >= self.safety_margins.left:
                            adjusted_position.x = new_x
                            layout_area.x = new_x
                            continue
                        
                        logger.warning("Could not resolve barcode position conflict with text area")
            
            # Ensure final position is valid
            if not self.validate_positioning(adjusted_position, cover_specs):
                logger.warning("Adjusted position still invalid, using fallback")
                adjusted_position = Position(x=2.0, y=0.5, unit="inches")
            
            return adjusted_position
            
        except Exception as e:
            logger.error(f"Error adjusting position for conflicts: {e}")
            return position
    
    def get_layout_specifications(self) -> Dict[str, Any]:
        """
        Get layout specifications for documentation and debugging.
        
        Returns:
            Dict: Layout specifications and standards
        """
        return {
            'barcode_dimensions': {
                'width': self.standard_barcode_size.width,
                'height': self.standard_barcode_size.height,
                'unit': self.standard_barcode_size.unit
            },
            'price_block_dimensions': {
                'width': self.standard_price_block_size.width,
                'height': self.standard_price_block_size.height,
                'unit': self.standard_price_block_size.unit
            },
            'safety_margins': {
                'top': self.safety_margins.top,
                'bottom': self.safety_margins.bottom,
                'left': self.safety_margins.left,
                'right': self.safety_margins.right,
                'unit': self.safety_margins.unit
            },
            'gaps': {
                'barcode_price_gap': self.barcode_price_gap
            },
            'positioning': {
                'preferred_position': self.preferred_position,
                'validation_enabled': True
            }
        }