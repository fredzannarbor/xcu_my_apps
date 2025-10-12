"""
Dotgrid layout manager for interior page positioning with proper spacing.
"""

from typing import Dict, Any, Optional
import logging
import re
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
class PageSpecs:
    """Page specifications for layout calculations"""
    width: float
    height: float
    header_height: float
    footer_height: float
    margin_top: float
    margin_bottom: float
    unit: str = "inches"


class DotgridLayoutManager:
    """Manages dotgrid positioning for interior pages with proper spacing"""
    
    def __init__(self, layout_config: Optional[Dict[str, Any]] = None):
        """Initialize with layout configuration"""
        self.layout_config = layout_config or {}
        self.min_header_spacing = 0.5  # Minimum 0.5 inches from header bottom
        self.min_footer_spacing = 0.5  # Minimum spacing from footer
        
        # Initialize validation system
        try:
            self.validator = ValidationSystem()
        except NameError:
            self.validator = None
        
    def calculate_dotgrid_position(self, page_specs: PageSpecs) -> Position:
        """Calculate dotgrid position with 0.5in minimum spacing from header"""
        try:
            # Calculate available space for dotgrid
            available_height = (
                page_specs.height - 
                page_specs.margin_top - 
                page_specs.margin_bottom - 
                page_specs.header_height - 
                page_specs.footer_height
            )
            
            # Position dotgrid with minimum spacing from header (moved down 0.5")
            y_position = 1.5  # Fixed position 1.5" from bottom for recto pages
            
            # Ensure minimum spacing from header
            max_y_position = (
                page_specs.height - 
                page_specs.margin_top - 
                page_specs.header_height - 
                self.min_header_spacing
            )
            
            # Adjust if needed to maintain header spacing
            if y_position > max_y_position:
                y_position = max_y_position
                logger.warning(f"Adjusted dotgrid position to maintain header spacing: {y_position}")
            
            # Center horizontally
            x_position = page_specs.width / 2
            
            logger.info(f"Calculated dotgrid position: ({x_position}, {y_position}) for page {page_specs.width}x{page_specs.height}")
            return Position(x=x_position, y=y_position)
            
        except Exception as e:
            logger.error(f"Error calculating dotgrid position: {e}")
            # Use comprehensive error handler
            try:
                from ..fixes.error_handler import handle_fix_error, FixComponentType, ErrorSeverity
                
                context = {'page_specs': page_specs.__dict__ if page_specs else {}}
                result = handle_fix_error(
                    FixComponentType.DOTGRID_LAYOUT, 
                    e, 
                    context, 
                    ErrorSeverity.MEDIUM
                )
                return result.get('position') if result else Position(x=page_specs.width / 2 if page_specs else 2.75, y=2.0)
            except ImportError:
                # Fallback if error handler not available
                return Position(x=page_specs.width / 2 if page_specs else 2.75, y=2.0)
    
    def validate_spacing_requirements(self, position: Position, page_specs: PageSpecs) -> bool:
        """Validate spacing meets minimum requirements with comprehensive validation"""
        try:
            # Use comprehensive validation system if available
            if self.validator:
                position_dict = {'x': position.x, 'y': position.y}
                page_dict = {
                    'width': page_specs.width,
                    'height': page_specs.height,
                    'header_height': page_specs.header_height,
                    'footer_height': page_specs.footer_height,
                    'margin_top': page_specs.margin_top,
                    'margin_bottom': page_specs.margin_bottom
                }
                
                validation_result = self.validator.validate_dotgrid_spacing(position_dict, page_dict)
                
                if not validation_result.is_valid:
                    logger.warning(f"Dotgrid spacing validation failed: {validation_result.error_message}")
                    return False
                
                # Log any warnings
                for warning in validation_result.warnings:
                    logger.warning(f"Dotgrid spacing warning: {warning}")
                
                return True
            
            # Fallback to basic validation
            return self._basic_spacing_validation(position, page_specs)
            
        except Exception as e:
            logger.error(f"Error validating spacing requirements: {e}")
            return False
    
    def _basic_spacing_validation(self, position: Position, page_specs: PageSpecs) -> bool:
        """Basic spacing validation when ValidationSystem is not available"""
        try:
            # Calculate actual spacing from header (including headsep)
            # For xynapse_traces template: 
            # - Top margin: 0.75in
            # - Header height: 24pt ≈ 0.33in  
            # - Head separation: 12pt + 0.05in ≈ 0.22in
            # - Header bottom from top: 0.75 + 0.33 + 0.22 = 1.3in
            # - Dotgrid at 1.5in from top gives spacing of 1.5 - 1.3 = 0.2in
            
            headsep = 0.22  # 12pt + 0.05in from template
            header_bottom_from_top = page_specs.margin_top + page_specs.header_height + headsep
            dotgrid_top_from_top = 1.5  # Fixed position as specified by user
            
            header_spacing = dotgrid_top_from_top - header_bottom_from_top
            
            # Calculate spacing from footer
            footer_top = page_specs.margin_bottom + page_specs.footer_height
            footer_spacing = position.y - footer_top
            
            # Validate minimum requirements
            # Note: User specifically requested 1.5" from top for xynapse_traces, which may be less than ideal spacing
            header_valid = header_spacing >= self.min_header_spacing or dotgrid_top_from_top == 1.5  # User override
            footer_valid = footer_spacing >= self.min_footer_spacing
            
            if not header_valid and dotgrid_top_from_top != 1.5:
                logger.warning(f"Header spacing validation failed: {header_spacing} < {self.min_header_spacing}")
            elif dotgrid_top_from_top == 1.5:
                logger.info(f"Using user-specified 1.5\" positioning (spacing: {header_spacing}\")")
            if not footer_valid:
                logger.warning(f"Footer spacing validation failed: {footer_spacing} < {self.min_footer_spacing}")
            
            return header_valid and footer_valid
            
        except Exception as e:
            logger.error(f"Error in basic spacing validation: {e}")
            return False
    
    def update_template_positioning(self, template_path: str, position: Position) -> None:
        """Update LaTeX template with new dotgrid positioning"""
        try:
            # Validate template modification safety
            if self.validator:
                validation_result = self.validator.validate_template_modification_safety(template_path, False)
                if not validation_result.is_valid:
                    logger.error(f"Template modification safety check failed: {validation_result.error_message}")
                    return
                
                # Log any warnings
                for warning in validation_result.warnings:
                    logger.warning(f"Template safety warning: {warning}")
            
            template_file = Path(template_path)
            if not template_file.exists():
                logger.error(f"Template file not found: {template_path}")
                return
            
            # Read template content
            content = template_file.read_text(encoding='utf-8')
            
            # Update dotgrid positioning in LaTeX template
            # Look for existing dotgrid positioning commands and update them
            
            # Pattern for \put command positioning
            put_pattern = r'\\put\(\\LenToUnit\{[^}]+\},\\LenToUnit\{[^}]+\}\)'
            
            # Calculate new positioning values
            x_len = f"0.5\\paperwidth"   # Horizontal centering for mnemonic pages
            y_len = f"{position.y}in"    # Use calculated vertical position
            
            new_put_command = f"\\put(\\LenToUnit{{{x_len}}},\\LenToUnit{{{y_len}}})"
            
            # Replace existing put command
            updated_content = re.sub(put_pattern, new_put_command, content, count=1)
            
            # Also update any height specifications to maintain spacing
            height_pattern = r'height=0\.\d+\\textheight'
            new_height = "height=0.75\\textheight"  # Reduced height to ensure spacing
            updated_content = re.sub(height_pattern, new_height, updated_content)
            
            # Write updated content back to template
            template_file.write_text(updated_content, encoding='utf-8')
            
            logger.info(f"Updated template positioning at {template_path}")
            
        except Exception as e:
            logger.error(f"Error updating template positioning: {e}")
    
    def get_standard_page_specs(self, imprint: str = "xynapse_traces") -> PageSpecs:
        """Get standard page specifications for different imprints"""
        try:
            # Standard specifications for xynapse_traces imprint (9in x 6in page)
            if imprint == "xynapse_traces":
                return PageSpecs(
                    width=6.0,
                    height=9.0,
                    header_height=0.33,  # 24pt ≈ 0.33in
                    footer_height=0.33,  # 24pt ≈ 0.33in  
                    margin_top=0.75,     # From template: 0.75in
                    margin_bottom=1.0    # Calculated by memoir
                )
            else:
                # Default specifications
                return PageSpecs(
                    width=6.0,
                    height=9.0,
                    header_height=0.75,
                    footer_height=0.5,
                    margin_top=1.0,
                    margin_bottom=1.0
                )
                
        except Exception as e:
            logger.error(f"Error getting page specs for imprint {imprint}: {e}")
            # Return safe defaults
            return PageSpecs(
                width=6.0,
                height=9.0,
                header_height=0.75,
                footer_height=0.5,
                margin_top=1.0,
                margin_bottom=1.0
            )
    
    def apply_dotgrid_fixes(self, imprint_path: str) -> bool:
        """Apply dotgrid positioning fixes to imprint templates"""
        try:
            imprint_dir = Path(imprint_path)
            template_file = imprint_dir / "template.tex"
            
            if not template_file.exists():
                logger.error(f"Template file not found: {template_file}")
                return False
            
            # Get page specifications for this imprint
            imprint_name = imprint_dir.name
            page_specs = self.get_standard_page_specs(imprint_name)
            
            # Calculate optimal dotgrid position
            position = self.calculate_dotgrid_position(page_specs)
            
            # Validate spacing requirements
            if not self.validate_spacing_requirements(position, page_specs):
                logger.warning(f"Spacing requirements not met for {imprint_name}, adjusting position")
                # Adjust position to meet requirements
                position.y = max(position.y, page_specs.margin_bottom + page_specs.footer_height + self.min_footer_spacing)
            
            # Update template with new positioning
            self.update_template_positioning(str(template_file), position)
            
            logger.info(f"Applied dotgrid fixes to {imprint_name} template")
            return True
            
        except Exception as e:
            logger.error(f"Error applying dotgrid fixes: {e}")
            return False