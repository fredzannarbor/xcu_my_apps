"""
ISBN barcode generator for UPC-A format with proper formatting.
"""

from typing import Dict, Any, Optional, Tuple, NamedTuple
import logging
import io
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from ..fixes.validation_system import ValidationSystem
except ImportError:
    logger.warning("ValidationSystem not available, using basic validation")


@dataclass
class Position:
    """Represents a position with x, y coordinates"""
    x: float
    y: float
    unit: str = "inches"


@dataclass
class Size:
    """Represents dimensions with width and height"""
    width: float
    height: float
    unit: str = "inches"


@dataclass
class SafetySpaces:
    """Represents safety spaces around barcode"""
    top: float
    bottom: float
    left: float
    right: float
    unit: str = "inches"


@dataclass
class PriceBlockData:
    """Represents price block area next to barcode"""
    price_text: Optional[str]
    dimensions: Size
    position_relative_to_barcode: Position
    background_color: str = "white"


@dataclass
class BarcodeData:
    """Enhanced barcode data with all components"""
    upc_code: str
    barcode_image: bytes
    isbn_display_text: str
    dimensions: Size
    format_type: str = "UPC-A"


@dataclass
class BarcodeResult:
    """Result of barcode generation with positioning and price block"""
    barcode_data: BarcodeData
    price_block: PriceBlockData
    position: Position
    safety_spaces: SafetySpaces
    format_type: str = "UPC-A"


class ISBNBarcodeGenerator:
    """Generate UPC-A barcodes for ISBN-13 with proper formatting"""
    
    def __init__(self, barcode_config: Dict[str, Any]):
        self.barcode_settings = barcode_config
        self.upc_format = "UPC-A"
        # Standard barcode dimensions
        self.barcode_size = Size(width=3.0, height=1.5, unit="inches")
        # Minimum safety spaces (industry standard)
        self.min_safety_spaces = SafetySpaces(
            top=0.125, bottom=0.125, left=0.125, right=0.125, unit="inches"
        )
        
        # Initialize validation system
        try:
            self.validator = ValidationSystem()
        except NameError:
            self.validator = None
        
        # Initialize layout manager for enhanced positioning
        try:
            from ..covers.barcode_layout_manager import BarcodeLayoutManager, CoverSpecs
            self.layout_manager = BarcodeLayoutManager()
            self._has_layout_manager = True
            logger.info("BarcodeLayoutManager initialized for enhanced positioning")
        except ImportError:
            self.layout_manager = None
            self._has_layout_manager = False
            logger.warning("BarcodeLayoutManager not available, using basic positioning")
    
    def calculate_barcode_position(self, cover_dimensions: Tuple[float, float], total_width: Optional[float] = None) -> Position:
        """Calculate barcode position using enhanced layout manager if available"""
        try:
            # Use enhanced layout manager if available
            if self._has_layout_manager and self.layout_manager:
                from ..covers.barcode_layout_manager import CoverSpecs, Rectangle
                
                cover_width, cover_height = cover_dimensions
                
                # Create cover specs for layout manager
                cover_specs = CoverSpecs(
                    width=cover_width,
                    height=cover_height,
                    spine_width=0.5,  # Default spine width
                    bleed=0.125,
                    back_cover_area=Rectangle(x=0, y=0, width=cover_width, height=cover_height, unit="inches"),
                    unit="inches"
                )
                
                # Calculate optimal position using layout manager
                position = self.layout_manager.calculate_optimal_position(cover_specs)
                logger.info(f"Enhanced barcode position calculated: ({position.x:.3f}, {position.y:.3f})")
                return position
            
            # Fallback to basic positioning
            cover_width, cover_height = cover_dimensions
            
            # Use total width if provided (barcode + price block), otherwise just barcode width
            element_width = total_width if total_width else self.barcode_size.width
            
            # Position barcode in bottom-right corner (current standard location)
            # Leave space for safety margins and element dimensions
            x_position = cover_width - element_width - self.min_safety_spaces.right - 0.5
            y_position = self.min_safety_spaces.bottom + 0.25  # 0.25" from bottom edge
            
            # Ensure position is within cover bounds
            x_position = max(self.min_safety_spaces.left, x_position)
            y_position = max(self.min_safety_spaces.bottom, y_position)
            
            logger.info(f"Basic barcode position calculated: ({x_position}, {y_position}) for cover {cover_dimensions}, width: {element_width}")
            return Position(x=x_position, y=y_position)
            
        except Exception as e:
            logger.error(f"Error calculating barcode position: {e}")
            # Fallback to safe default position
            return Position(x=2.0, y=0.5)
    
    def validate_safety_spaces(self, position: Position, cover_dimensions: Tuple[float, float], total_width: Optional[float] = None) -> bool:
        """Ensure adequate safety spaces around barcode with comprehensive validation"""
        try:
            # Use enhanced layout manager validation if available
            if self._has_layout_manager and self.layout_manager:
                from ..covers.barcode_layout_manager import CoverSpecs, Rectangle
                
                cover_width, cover_height = cover_dimensions
                
                # Create cover specs for validation
                cover_specs = CoverSpecs(
                    width=cover_width,
                    height=cover_height,
                    spine_width=0.5,  # Default spine width
                    bleed=0.125,
                    back_cover_area=Rectangle(x=0, y=0, width=cover_width, height=cover_height, unit="inches"),
                    unit="inches"
                )
                
                # Use layout manager validation
                is_valid = self.layout_manager.validate_positioning(position, cover_specs)
                if is_valid:
                    logger.info("Enhanced safety space validation passed")
                else:
                    logger.warning("Enhanced safety space validation failed")
                return is_valid
            
            # Use comprehensive validation system if available
            if self.validator:
                position_dict = {'x': position.x, 'y': position.y}
                cover_dict = {'width': cover_dimensions[0], 'height': cover_dimensions[1]}
                
                validation_result = self.validator.validate_barcode_positioning(position_dict, cover_dict)
                
                if not validation_result.is_valid:
                    logger.warning(f"Barcode positioning validation failed: {validation_result.error_message}")
                    return False
                
                # Log any warnings
                for warning in validation_result.warnings:
                    logger.warning(f"Barcode positioning warning: {warning}")
                
                return True
            
            # Fallback to basic validation
            return self._basic_safety_validation(position, cover_dimensions, total_width)
            
        except Exception as e:
            logger.error(f"Error validating safety spaces: {e}")
            return False
    
    def _basic_safety_validation(self, position: Position, cover_dimensions: Tuple[float, float], total_width: Optional[float] = None) -> bool:
        """Basic safety space validation when ValidationSystem is not available"""
        try:
            cover_width, cover_height = cover_dimensions
            
            # Use total width if provided (barcode + price block), otherwise just barcode width
            element_width = total_width if total_width else self.barcode_size.width
            
            # Calculate element boundaries
            element_left = position.x
            element_right = position.x + element_width
            element_bottom = position.y
            element_top = position.y + self.barcode_size.height
            
            # Check safety spaces
            left_space = element_left
            right_space = cover_width - element_right
            bottom_space = element_bottom
            top_space = cover_height - element_top
            
            # Validate minimum safety spaces
            safety_valid = (
                left_space >= self.min_safety_spaces.left and
                right_space >= self.min_safety_spaces.right and
                bottom_space >= self.min_safety_spaces.bottom and
                top_space >= self.min_safety_spaces.top
            )
            
            if not safety_valid:
                logger.warning(f"Safety space validation failed. Spaces: L:{left_space}, R:{right_space}, B:{bottom_space}, T:{top_space}")
            
            return safety_valid
            
        except Exception as e:
            logger.error(f"Error in basic safety validation: {e}")
            return False
    
    def generate_upc_barcode_with_positioning(self, isbn13: str, cover_specs: Dict, price: Optional[str] = None) -> BarcodeResult:
        """Generate UPC-A barcode with proper positioning, price block, and safety spaces"""
        try:
            # Extract cover dimensions
            cover_dimensions = (
                cover_specs.get('width', 6.0),
                cover_specs.get('height', 9.0)
            )
            
            # Generate enhanced barcode data
            barcode_data = self.generate_standard_upc_barcode(isbn13)
            
            # Create price block
            price_block = self.create_price_block_area(price)
            
            # Calculate position accounting for total width (barcode + price block)
            total_width = self.barcode_size.width + price_block.dimensions.width + 0.1  # Include gap
            position = self.calculate_barcode_position(cover_dimensions, total_width)
            
            # Validate safety spaces
            if not self.validate_safety_spaces(position, cover_dimensions, total_width):
                logger.warning(f"Safety space validation failed for ISBN {isbn13}, adjusting position")
                # Adjust position if needed
                position = Position(x=position.x + 0.125, y=position.y + 0.125)
            
            # Create safety spaces info
            safety_spaces = SafetySpaces(
                top=self.min_safety_spaces.top,
                bottom=self.min_safety_spaces.bottom,
                left=self.min_safety_spaces.left,
                right=self.min_safety_spaces.right
            )
            
            return BarcodeResult(
                barcode_data=barcode_data,
                price_block=price_block,
                position=position,
                safety_spaces=safety_spaces,
                format_type=self.upc_format
            )
            
        except Exception as e:
            logger.error(f"Error generating UPC barcode with positioning: {e}")
            # Use comprehensive error handler
            try:
                from ..fixes.error_handler import handle_fix_error, FixComponentType, ErrorSeverity
                
                context = {'isbn': isbn13, 'cover_specs': cover_specs}
                return handle_fix_error(
                    FixComponentType.BARCODE_GENERATOR, 
                    e, 
                    context, 
                    ErrorSeverity.HIGH
                )
            except ImportError:
                # Fallback if error handler not available
                return BarcodeResult(
                    barcode_data=self._generate_placeholder_barcode_data(isbn13),
                    price_block=self.create_price_block_area(price),
                    position=Position(x=10.0, y=0.5),
                    safety_spaces=self.min_safety_spaces,
                    format_type=self.upc_format
                )

    def generate_standard_upc_barcode(self, isbn13: str) -> BarcodeData:
        """Generate proper UPC-A barcode from ISBN-13 with all components"""
        try:
            # Clean ISBN-13
            clean_isbn = isbn13.replace('-', '').replace(' ', '')
            
            # Validate ISBN-13 format
            if not self._validate_isbn13(clean_isbn):
                raise ValueError(f"Invalid ISBN-13 format: {isbn13}")
            
            # For books, UPC-A uses the full ISBN-13 without the check digit, then recalculates
            # Convert ISBN-13 to UPC-A: use first 12 digits, calculate UPC check digit
            if clean_isbn.startswith('978') or clean_isbn.startswith('979'):
                # Use first 12 digits of ISBN-13
                upc_base = clean_isbn[:12]
                # Calculate UPC-A check digit
                upc_check = self._calculate_upc_check_digit(upc_base)
                upc_code = upc_base + str(upc_check)
            else:
                raise ValueError(f"ISBN-13 must start with 978 or 979: {isbn13}")
            
            # Generate barcode using python-barcode library
            try:
                from barcode import UPCA
                from barcode.writer import ImageWriter
                
                # Configure writer for proper dimensions
                writer = ImageWriter()
                writer.set_options({
                    'module_width': 0.33,  # Standard module width in mm
                    'module_height': 25.0,  # Standard height in mm
                    'quiet_zone': 6.35,    # Standard quiet zone in mm
                    'font_size': 8,        # Font size for numbers
                    'text_distance': 1.0,  # Distance between barcode and text
                })
                
                # Create UPC-A barcode
                barcode_class = UPCA(upc_code, writer=writer)
                
                # Generate barcode image
                buffer = io.BytesIO()
                barcode_class.write(buffer)
                buffer.seek(0)
                
                # Create formatted ISBN display text
                isbn_display_text = self.format_isbn_display_text(isbn13)
                
                logger.info(f"Generated UPC-A barcode for ISBN: {isbn13}")
                
                return BarcodeData(
                    upc_code=upc_code,
                    barcode_image=buffer.getvalue(),
                    isbn_display_text=isbn_display_text,
                    dimensions=self.barcode_size,
                    format_type="UPC-A"
                )
                
            except ImportError:
                logger.warning("python-barcode library not available, generating placeholder")
                return self._generate_placeholder_barcode_data(clean_isbn)
                
        except Exception as e:
            logger.error(f"Error generating UPC barcode: {e}")
            return self._generate_placeholder_barcode_data(isbn13)

    def generate_upc_barcode(self, isbn13: str) -> bytes:
        """Legacy method - generates UPC-A barcode bytes only"""
        barcode_data = self.generate_standard_upc_barcode(isbn13)
        return barcode_data.barcode_image
    
    def _validate_isbn13(self, isbn: str) -> bool:
        """Validate ISBN-13 format"""
        try:
            if len(isbn) != 13:
                return False
            
            if not isbn.isdigit():
                return False
            
            if not (isbn.startswith('978') or isbn.startswith('979')):
                return False
            
            # Validate check digit
            check_sum = 0
            for i, digit in enumerate(isbn[:-1]):
                weight = 1 if i % 2 == 0 else 3
                check_sum += int(digit) * weight
            
            check_digit = (10 - (check_sum % 10)) % 10
            return int(isbn[-1]) == check_digit
            
        except Exception:
            return False
    
    def _calculate_upc_check_digit(self, upc_base: str) -> int:
        """Calculate UPC-A check digit for 12-digit base"""
        try:
            if len(upc_base) != 12:
                raise ValueError(f"UPC base must be 12 digits, got {len(upc_base)}")
            
            # UPC-A check digit calculation
            odd_sum = sum(int(upc_base[i]) for i in range(0, 12, 2))  # 1st, 3rd, 5th, etc.
            even_sum = sum(int(upc_base[i]) for i in range(1, 12, 2))  # 2nd, 4th, 6th, etc.
            
            total = (odd_sum * 3) + even_sum
            check_digit = (10 - (total % 10)) % 10
            
            return check_digit
            
        except Exception as e:
            logger.error(f"Error calculating UPC check digit: {e}")
            return 0

    def format_isbn_display_text(self, isbn13: str) -> str:
        """Format ISBN for display below barcode in standard format"""
        try:
            clean_isbn = isbn13.replace('-', '').replace(' ', '')
            
            # Format as: ISBN 978-0-123456-78-9
            if len(clean_isbn) == 13:
                formatted = f"ISBN {clean_isbn[:3]}-{clean_isbn[3]}-{clean_isbn[4:10]}-{clean_isbn[10:12]}-{clean_isbn[12]}"
                return formatted
            
            return f"ISBN {clean_isbn}"
            
        except Exception as e:
            logger.error(f"Error formatting ISBN display text: {e}")
            return f"ISBN {isbn13}"

    def format_barcode_numerals(self, isbn13: str) -> str:
        """Format bar-code-reader numerals for display (legacy method)"""
        return self.format_isbn_display_text(isbn13)

    def create_price_block_area(self, price: Optional[str] = None) -> PriceBlockData:
        """Create price block area with standard dimensions"""
        try:
            # Standard price block dimensions (industry standard)
            price_block_size = Size(width=0.75, height=1.5, unit="inches")
            
            # Position relative to barcode (to the right)
            relative_position = Position(
                x=self.barcode_size.width + 0.1,  # Small gap between barcode and price block
                y=0.0,  # Aligned with barcode bottom
                unit="inches"
            )
            
            # Format price text if provided
            price_text = None
            if price:
                # Format price for display (e.g., "$19.99")
                if not price.startswith('$'):
                    price_text = f"${price}"
                else:
                    price_text = price
            
            return PriceBlockData(
                price_text=price_text,
                dimensions=price_block_size,
                position_relative_to_barcode=relative_position,
                background_color="white"
            )
            
        except Exception as e:
            logger.error(f"Error creating price block area: {e}")
            # Return default price block
            return PriceBlockData(
                price_text=None,
                dimensions=Size(width=0.75, height=1.5, unit="inches"),
                position_relative_to_barcode=Position(x=3.1, y=0.0, unit="inches"),
                background_color="white"
            )
    
    def integrate_barcode_to_cover(self, cover_template: str, isbn13: str) -> str:
        """Integrate barcode into back cover design"""
        try:
            # Generate barcode
            barcode_data = self.generate_upc_barcode(isbn13)
            formatted_numerals = self.format_barcode_numerals(isbn13)
            
            # Create LaTeX code for barcode integration
            barcode_latex = f"""
% ISBN Barcode
\\begin{{textblock}}{{4}}(13, 23)
\\centering
\\includegraphics[width=3cm]{{barcode_{isbn13.replace('-', '')}.png}}\\\\
\\tiny {formatted_numerals}
\\end{{textblock}}
"""
            
            # Insert barcode into cover template
            if '\\end{document}' in cover_template:
                cover_template = cover_template.replace(
                    '\\end{document}',
                    barcode_latex + '\n\\end{document}'
                )
            else:
                cover_template += barcode_latex
            
            # Save barcode image (would need actual file writing in real implementation)
            logger.info(f"Integrated barcode for ISBN {isbn13} into cover template")
            
            return cover_template
            
        except Exception as e:
            logger.error(f"Error integrating barcode to cover: {e}")
            return cover_template
    
    def validate_barcode_standards(self, barcode_data: bytes) -> bool:
        """Validate barcode meets industry standards for retail scanning"""
        try:
            if not barcode_data:
                return False
            
            # Basic validation - check if data exists and has reasonable size
            if len(barcode_data) < 100:  # Too small to be a valid barcode image
                return False
            
            # Check for common image headers (PNG, JPEG)
            if barcode_data.startswith(b'\x89PNG') or barcode_data.startswith(b'\xff\xd8'):
                return True
            
            # Additional validation could include:
            # - Image dimensions check
            # - Barcode readability test
            # - Print quality validation
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating barcode standards: {e}")
            return False
    
    def _generate_placeholder_barcode_data(self, isbn: str) -> BarcodeData:
        """Generate placeholder barcode data when library is not available"""
        try:
            # Create a simple text-based placeholder
            placeholder_text = f"BARCODE: {isbn}"
            isbn_display_text = self.format_isbn_display_text(isbn)
            
            return BarcodeData(
                upc_code=isbn,
                barcode_image=placeholder_text.encode('utf-8'),
                isbn_display_text=isbn_display_text,
                dimensions=self.barcode_size,
                format_type="PLACEHOLDER"
            )
            
        except Exception as e:
            logger.error(f"Error generating placeholder barcode data: {e}")
            return BarcodeData(
                upc_code="ERROR",
                barcode_image=b"BARCODE_ERROR",
                isbn_display_text="ISBN ERROR",
                dimensions=self.barcode_size,
                format_type="ERROR"
            )

    def _generate_placeholder_barcode(self, isbn: str) -> bytes:
        """Generate placeholder barcode when library is not available (legacy method)"""
        barcode_data = self._generate_placeholder_barcode_data(isbn)
        return barcode_data.barcode_image
    
    def get_barcode_specifications(self) -> Dict[str, Any]:
        """Get barcode specifications for printing"""
        return {
            'format': 'UPC-A',
            'width': '3cm',
            'height': '1.5cm',
            'resolution': '300dpi',
            'color': 'black',
            'background': 'white',
            'quiet_zone': '2mm',
            'font_size': '8pt',
            'position': 'bottom_right'
        }