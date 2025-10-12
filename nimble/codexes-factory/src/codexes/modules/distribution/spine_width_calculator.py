#!/usr/bin/env python3

"""
Spine Width Calculator

This module provides accurate spine width calculation for books based on
page count, paper type, and binding specifications according to LSI standards.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PaperType(Enum):
    """Paper types with their thickness specifications."""
    WHITE = "white"
    CREAM = "cream"
    PREMIUM_WHITE = "premium_white"
    PREMIUM_CREAM = "premium_cream"


class BindingType(Enum):
    """Binding types that affect spine calculation."""
    PAPERBACK = "paperback"
    HARDCOVER = "hardcover"
    SPIRAL = "spiral"


@dataclass
class SpineCalculationResult:
    """Result of spine width calculation."""
    spine_width_inches: float
    page_count: int
    paper_type: str
    binding_type: str
    calculation_method: str
    notes: Optional[str] = None


class SpineWidthCalculator:
    """Calculator for book spine width based on LSI specifications."""
    
    def __init__(self):
        """Initialize spine width calculator with LSI standards."""
        # Paper thickness in inches per page (single sheet, both sides)
        self.paper_thickness = {
            PaperType.WHITE: 0.002252,      # Standard white paper
            PaperType.CREAM: 0.0025,        # Cream paper (slightly thicker)
            PaperType.PREMIUM_WHITE: 0.002,  # Premium white paper
            PaperType.PREMIUM_CREAM: 0.0023  # Premium cream paper
        }
        
        # Binding adjustments (additional thickness for binding)
        self.binding_adjustments = {
            BindingType.PAPERBACK: 0.0,     # No additional thickness
            BindingType.HARDCOVER: 0.125,   # Additional thickness for hardcover
            BindingType.SPIRAL: 0.25        # Additional thickness for spiral binding
        }
        
        # Minimum and maximum spine widths
        self.min_spine_width = 0.0625  # 1/16 inch minimum
        self.max_spine_width = 2.0     # 2 inches maximum
    
    def calculate_spine_width(self, page_count: int, paper_type: str = "white", 
                            binding_type: str = "paperback") -> SpineCalculationResult:
        """
        Calculate spine width based on page count and specifications.
        
        Args:
            page_count: Number of pages in the book
            paper_type: Type of paper (white, cream, premium_white, premium_cream)
            binding_type: Type of binding (paperback, hardcover, spiral)
            
        Returns:
            SpineCalculationResult with calculated width and details
        """
        # Validate inputs
        if page_count <= 0:
            raise ValueError("Page count must be positive")
        
        # Normalize paper type
        paper_type_enum = self._normalize_paper_type(paper_type)
        binding_type_enum = self._normalize_binding_type(binding_type)
        
        # Get paper thickness
        thickness_per_page = self.paper_thickness[paper_type_enum]
        
        # Calculate base spine width (page count * thickness per page)
        base_spine_width = page_count * thickness_per_page
        
        # Add binding adjustment
        binding_adjustment = self.binding_adjustments[binding_type_enum]
        calculated_width = base_spine_width + binding_adjustment
        
        # Apply minimum and maximum constraints
        final_width = max(self.min_spine_width, min(calculated_width, self.max_spine_width))
        
        # Create notes if adjustments were made
        notes = []
        if calculated_width < self.min_spine_width:
            notes.append(f"Adjusted to minimum spine width ({self.min_spine_width} inches)")
        elif calculated_width > self.max_spine_width:
            notes.append(f"Adjusted to maximum spine width ({self.max_spine_width} inches)")
        
        if binding_adjustment > 0:
            notes.append(f"Added {binding_adjustment} inches for {binding_type} binding")
        
        return SpineCalculationResult(
            spine_width_inches=final_width,
            page_count=page_count,
            paper_type=paper_type,
            binding_type=binding_type,
            calculation_method="LSI_STANDARD",
            notes="; ".join(notes) if notes else None
        )
    
    def _normalize_paper_type(self, paper_type: str) -> PaperType:
        """Normalize paper type string to enum."""
        paper_type_lower = paper_type.lower().strip()
        
        if paper_type_lower in ['white', 'standard_white', 'standard white']:
            return PaperType.WHITE
        elif paper_type_lower in ['cream', 'standard_cream', 'standard cream']:
            return PaperType.CREAM
        elif paper_type_lower in ['premium_white', 'premium white']:
            return PaperType.PREMIUM_WHITE
        elif paper_type_lower in ['premium_cream', 'premium cream']:
            return PaperType.PREMIUM_CREAM
        else:
            logger.warning(f"Unknown paper type '{paper_type}', defaulting to white")
            return PaperType.WHITE
    
    def _normalize_binding_type(self, binding_type: str) -> BindingType:
        """Normalize binding type string to enum."""
        binding_type_lower = binding_type.lower().strip()
        
        if binding_type_lower in ['paperback', 'pb', 'soft', 'softcover']:
            return BindingType.PAPERBACK
        elif binding_type_lower in ['hardcover', 'hc', 'hard', 'hardback']:
            return BindingType.HARDCOVER
        elif binding_type_lower in ['spiral', 'spiral_bound', 'spiral bound', 'coil']:
            return BindingType.SPIRAL
        else:
            logger.warning(f"Unknown binding type '{binding_type}', defaulting to paperback")
            return BindingType.PAPERBACK
    
    def calculate_from_metadata(self, metadata: Dict[str, Any]) -> SpineCalculationResult:
        """
        Calculate spine width from metadata dictionary.
        
        Args:
            metadata: Dictionary containing book metadata
            
        Returns:
            SpineCalculationResult with calculated spine width
        """
        # Extract required fields
        page_count = self._extract_page_count(metadata)
        paper_type = self._extract_paper_type(metadata)
        binding_type = self._extract_binding_type(metadata)
        
        return self.calculate_spine_width(page_count, paper_type, binding_type)
    
    def _extract_page_count(self, metadata: Dict[str, Any]) -> int:
        """Extract page count from metadata."""
        page_count_fields = ['page_count', 'Page Count', 'pages', 'Pages', 'pageCount']
        
        for field in page_count_fields:
            if field in metadata and metadata[field]:
                try:
                    return int(metadata[field])
                except (ValueError, TypeError):
                    continue
        
        raise ValueError("Page count not found or invalid in metadata")
    
    def _extract_paper_type(self, metadata: Dict[str, Any]) -> str:
        """Extract paper type from metadata."""
        paper_type_fields = ['paper_color', 'Paper Color', 'paper_type', 'Paper Type', 'paperColor']
        
        for field in paper_type_fields:
            if field in metadata and metadata[field]:
                return str(metadata[field])
        
        # Default to white if not specified
        return "white"
    
    def _extract_binding_type(self, metadata: Dict[str, Any]) -> str:
        """Extract binding type from metadata."""
        binding_type_fields = ['binding_type', 'Binding Type', 'binding', 'Binding', 'bindingType']
        
        for field in binding_type_fields:
            if field in metadata and metadata[field]:
                return str(metadata[field])
        
        # Default to paperback if not specified
        return "paperback"
    
    def override_spine_width_in_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate and override spine width in metadata dictionary.
        This ensures calculated spine width always takes precedence over configured values.
        
        Args:
            metadata: Dictionary containing book metadata
            
        Returns:
            Updated metadata dictionary with calculated spine width
        """
        try:
            # Calculate spine width
            result = self.calculate_from_metadata(metadata)
            
            # Override spine width fields
            spine_width_fields = [
                'spine_width', 'Spine Width', 'spineWidth',
                'spine_width_inches', 'Spine Width Inches'
            ]
            
            # Format spine width to 4 decimal places for precision
            formatted_width = f"{result.spine_width_inches:.4f}"
            
            # Update all possible spine width fields
            for field in spine_width_fields:
                if field in metadata:
                    original_value = metadata[field]
                    metadata[field] = formatted_width
                    
                    if str(original_value) != formatted_width:
                        logger.info(
                            f"Overrode spine width: {original_value} -> {formatted_width} "
                            f"(calculated from {result.page_count} pages, {result.paper_type} paper)"
                        )
            
            # Add spine width if not present
            if not any(field in metadata for field in spine_width_fields):
                metadata['Spine Width'] = formatted_width
                logger.info(f"Added calculated spine width: {formatted_width}")
            
            # Add calculation metadata for debugging
            metadata['_spine_calculation_method'] = result.calculation_method
            metadata['_spine_calculation_notes'] = result.notes
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error calculating spine width: {e}")
            # Return original metadata if calculation fails
            return metadata
    
    def validate_spine_width(self, spine_width: float, page_count: int, 
                           paper_type: str = "white") -> Dict[str, Any]:
        """
        Validate if a given spine width is reasonable for the book specifications.
        
        Args:
            spine_width: Spine width to validate
            page_count: Number of pages
            paper_type: Type of paper
            
        Returns:
            Dictionary with validation results
        """
        # Calculate expected spine width
        expected_result = self.calculate_spine_width(page_count, paper_type)
        expected_width = expected_result.spine_width_inches
        
        # Calculate tolerance (5% or minimum 0.01 inches)
        tolerance = max(expected_width * 0.05, 0.01)
        
        # Check if within tolerance
        difference = abs(spine_width - expected_width)
        is_valid = difference <= tolerance
        
        return {
            'is_valid': is_valid,
            'provided_width': spine_width,
            'expected_width': expected_width,
            'difference': difference,
            'tolerance': tolerance,
            'recommendation': 'ACCEPT' if is_valid else 'RECALCULATE',
            'message': (
                f"Spine width is within tolerance" if is_valid else
                f"Spine width differs by {difference:.4f} inches from expected {expected_width:.4f} inches"
            )
        }
    
    def get_spine_width_recommendations(self, page_count_range: tuple, 
                                     paper_type: str = "white") -> Dict[str, Any]:
        """
        Get spine width recommendations for a range of page counts.
        
        Args:
            page_count_range: Tuple of (min_pages, max_pages)
            paper_type: Type of paper
            
        Returns:
            Dictionary with spine width recommendations
        """
        min_pages, max_pages = page_count_range
        
        recommendations = []
        for page_count in range(min_pages, max_pages + 1, 10):  # Every 10 pages
            result = self.calculate_spine_width(page_count, paper_type)
            recommendations.append({
                'page_count': page_count,
                'spine_width': result.spine_width_inches,
                'formatted_width': f"{result.spine_width_inches:.4f}"
            })
        
        return {
            'paper_type': paper_type,
            'page_range': page_count_range,
            'recommendations': recommendations,
            'thickness_per_page': self.paper_thickness[self._normalize_paper_type(paper_type)]
        }


# Global calculator instance
_spine_calculator = None


def get_spine_calculator() -> SpineWidthCalculator:
    """Get the global spine width calculator instance."""
    global _spine_calculator
    if _spine_calculator is None:
        _spine_calculator = SpineWidthCalculator()
    return _spine_calculator


def calculate_spine_width(page_count: int, paper_type: str = "white", 
                        binding_type: str = "paperback") -> float:
    """
    Convenience function to calculate spine width.
    
    Args:
        page_count: Number of pages
        paper_type: Type of paper
        binding_type: Type of binding
        
    Returns:
        Calculated spine width in inches
    """
    calculator = get_spine_calculator()
    result = calculator.calculate_spine_width(page_count, paper_type, binding_type)
    return result.spine_width_inches


def override_spine_width_in_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to override spine width in metadata.
    
    Args:
        metadata: Dictionary containing book metadata
        
    Returns:
        Updated metadata with calculated spine width
    """
    calculator = get_spine_calculator()
    return calculator.override_spine_width_in_metadata(metadata)


def validate_spine_width(spine_width: float, page_count: int, 
                        paper_type: str = "white") -> bool:
    """
    Convenience function to validate spine width.
    
    Args:
        spine_width: Spine width to validate
        page_count: Number of pages
        paper_type: Type of paper
        
    Returns:
        True if spine width is valid, False otherwise
    """
    calculator = get_spine_calculator()
    validation = calculator.validate_spine_width(spine_width, page_count, paper_type)
    return validation['is_valid']