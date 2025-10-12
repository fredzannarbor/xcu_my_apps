"""
Enhanced spine width calculator with improved error handling and validation.
"""

import pandas as pd
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from ..fixes.validation_system import ValidationSystem
except ImportError:
    logger.warning("ValidationSystem not available, using basic validation")


class SpineWidthCalculator:
    """Enhanced spine width calculator with validation and error handling"""
    
    def __init__(self, lookup_file_path: str = "resources/data_tables/LSI/SpineWidthLookup.xlsx"):
        """Initialize with lookup file path"""
        self.lookup_file_path = Path(lookup_file_path)
        self.default_paper_type = "Standard 70 perfect"
        self.fallback_spine_width = 0.25  # Safe fallback width in inches
        
        # Cache for loaded sheets to improve performance
        self._sheets_cache = {}
        
        # Initialize validation system
        try:
            self.validator = ValidationSystem()
        except NameError:
            self.validator = None
        
    def calculate_spine_width_from_lookup(self, page_count: int, paper_type: str = None) -> float:
        """Calculate spine width using SpineWidthLookup.xlsx logic"""
        try:
            if paper_type is None:
                paper_type = self.default_paper_type
            
            logger.info(f"Calculating spine width for {page_count} pages, paper type: {paper_type}")
            
            # Load lookup data
            spine_width = self._lookup_spine_width(paper_type, page_count)
            
            if spine_width is not None:
                logger.info(f"Calculated spine width: {spine_width} inches")
                return spine_width
            else:
                logger.warning(f"Could not calculate spine width, using fallback: {self.fallback_spine_width}")
                return self.fallback_spine_width
                
        except Exception as e:
            logger.error(f"Error calculating spine width: {e}")
            # Use comprehensive error handler
            try:
                from ..fixes.error_handler import handle_fix_error, FixComponentType, ErrorSeverity
                
                context = {'page_count': page_count, 'paper_type': paper_type}
                return handle_fix_error(
                    FixComponentType.SPINE_WIDTH_CALCULATOR, 
                    e, 
                    context, 
                    ErrorSeverity.HIGH
                )
            except ImportError:
                # Fallback if error handler not available
                return self.fallback_spine_width
    
    def _lookup_spine_width(self, sheet_name: str, page_count: int) -> Optional[float]:
        """Look up spine width from Excel sheet"""
        try:
            # Check if we have cached sheets
            if sheet_name not in self._sheets_cache:
                self._load_lookup_sheets()
            
            if sheet_name not in self._sheets_cache:
                logger.error(f"Sheet '{sheet_name}' not found in lookup file")
                return None
            
            df = self._sheets_cache[sheet_name]
            
            # Ensure proper data types
            df["Pages"] = df["Pages"].astype(int)
            df["SpineWidth"] = df["SpineWidth"].astype(float)
            
            page_count = int(page_count)
            
            # Handle edge cases
            if page_count < df["Pages"].min():
                logger.warning(f"Page count {page_count} is less than minimum {df['Pages'].min()}, using minimum spine width")
                return float(df["SpineWidth"].min())
            elif page_count > df["Pages"].max():
                logger.warning(f"Page count {page_count} is greater than maximum {df['Pages'].max()}, using maximum spine width")
                return float(df["SpineWidth"].max())
            elif page_count in df["Pages"].values:
                # Exact match
                return float(df.loc[df["Pages"] == page_count, "SpineWidth"].iloc[0])
            else:
                # Find the next higher page count and use its spine width
                higher_pages = df[df["Pages"] >= page_count]
                if not higher_pages.empty:
                    return float(higher_pages["SpineWidth"].min())
                else:
                    return float(df["SpineWidth"].max())
                    
        except Exception as e:
            logger.error(f"Error looking up spine width: {e}")
            return None
    
    def _load_lookup_sheets(self) -> None:
        """Load all sheets from the lookup Excel file"""
        try:
            if not self.lookup_file_path.exists():
                logger.error(f"Spine width lookup file not found: {self.lookup_file_path}")
                return
            
            # Try both .xlsx and .xls extensions
            file_path = self.lookup_file_path
            if not file_path.exists():
                # Try .xls extension
                file_path = file_path.with_suffix('.xls')
            
            if not file_path.exists():
                logger.error(f"Spine width lookup file not found: {file_path}")
                return
            
            logger.info(f"Loading spine width lookup sheets from: {file_path}")
            
            # Load all sheets
            dict_of_sheets = pd.read_excel(file_path, sheet_name=None)
            
            # Process each sheet
            for sheet_name, df in dict_of_sheets.items():
                # Ensure consistent column names
                if len(df.columns) >= 2:
                    df.columns = ["Pages", "SpineWidth"] + list(df.columns[2:])
                    self._sheets_cache[sheet_name] = df
                    logger.debug(f"Loaded sheet '{sheet_name}' with {len(df)} rows")
                else:
                    logger.warning(f"Sheet '{sheet_name}' has insufficient columns, skipping")
            
            logger.info(f"Successfully loaded {len(self._sheets_cache)} sheets")
            
        except Exception as e:
            logger.error(f"Error loading spine width lookup sheets: {e}")
    
    def validate_calculation(self, spine_width: float, page_count: int) -> bool:
        """Validate calculated spine width against expected ranges with comprehensive validation"""
        try:
            # Use comprehensive validation system if available
            if self.validator:
                validation_result = self.validator.validate_spine_width_calculation(page_count, spine_width)
                
                if not validation_result.is_valid:
                    logger.warning(f"Spine width validation failed: {validation_result.error_message}")
                    return False
                
                # Log any warnings
                for warning in validation_result.warnings:
                    logger.warning(f"Spine width validation warning: {warning}")
                
                return True
            
            # Fallback to basic validation
            return self._basic_spine_validation(spine_width, page_count)
            
        except Exception as e:
            logger.error(f"Error validating spine width: {e}")
            return False
    
    def _basic_spine_validation(self, spine_width: float, page_count: int) -> bool:
        """Basic spine width validation when ValidationSystem is not available"""
        try:
            # Basic validation ranges (industry standards)
            min_spine_width = 0.0625  # 1/16 inch minimum
            max_spine_width = 2.0     # 2 inches maximum for typical books
            
            # Page count based validation
            expected_min = page_count * 0.0005  # Very thin paper estimate
            expected_max = page_count * 0.005   # Thick paper estimate
            
            # Check basic bounds
            if spine_width < min_spine_width or spine_width > max_spine_width:
                logger.warning(f"Spine width {spine_width} outside typical range [{min_spine_width}, {max_spine_width}]")
                return False
            
            # Check page count correlation
            if spine_width < expected_min or spine_width > expected_max:
                logger.warning(f"Spine width {spine_width} not correlated with page count {page_count}")
                return False
            
            logger.info(f"Spine width validation passed: {spine_width} inches for {page_count} pages")
            return True
            
        except Exception as e:
            logger.error(f"Error in basic spine validation: {e}")
            return False
    
    def distribute_spine_width(self, spine_width: float, metadata: Dict[str, Any], cover_generator: Any = None) -> None:
        """Distribute spine width to metadata and cover creator components"""
        try:
            # Update metadata with spine width
            if isinstance(metadata, dict):
                metadata['spine_width_in'] = spine_width
                logger.info(f"Updated metadata with spine width: {spine_width}")
            else:
                # Handle CodexMetadata object
                if hasattr(metadata, 'spine_width_in'):
                    metadata.spine_width_in = spine_width
                    logger.info(f"Updated CodexMetadata with spine width: {spine_width}")
                else:
                    logger.warning("Metadata object does not have spine_width_in attribute")
            
            # Update cover generator if provided
            if cover_generator is not None:
                if hasattr(cover_generator, 'set_spine_width'):
                    cover_generator.set_spine_width(spine_width)
                    logger.info(f"Updated cover generator with spine width: {spine_width}")
                else:
                    logger.debug("Cover generator does not have set_spine_width method")
            
            logger.info(f"Successfully distributed spine width {spine_width} to components")
            
        except Exception as e:
            logger.error(f"Error distributing spine width: {e}")
    
    def get_available_paper_types(self) -> list:
        """Get list of available paper types from lookup file"""
        try:
            if not self._sheets_cache:
                self._load_lookup_sheets()
            
            return list(self._sheets_cache.keys())
            
        except Exception as e:
            logger.error(f"Error getting available paper types: {e}")
            return []
    
    def calculate_spine_width_with_validation(self, page_count: int, paper_type: str = None) -> Tuple[float, bool]:
        """Calculate spine width with validation, returns (spine_width, is_valid)"""
        try:
            spine_width = self.calculate_spine_width_from_lookup(page_count, paper_type)
            is_valid = self.validate_calculation(spine_width, page_count)
            
            return spine_width, is_valid
            
        except Exception as e:
            logger.error(f"Error in spine width calculation with validation: {e}")
            return self.fallback_spine_width, False
    
    def get_spine_width_range(self, paper_type: str = None) -> Tuple[float, float]:
        """Get the range of spine widths for a given paper type"""
        try:
            if paper_type is None:
                paper_type = self.default_paper_type
            
            if paper_type not in self._sheets_cache:
                self._load_lookup_sheets()
            
            if paper_type not in self._sheets_cache:
                return self.fallback_spine_width, self.fallback_spine_width
            
            df = self._sheets_cache[paper_type]
            min_width = float(df["SpineWidth"].min())
            max_width = float(df["SpineWidth"].max())
            
            return min_width, max_width
            
        except Exception as e:
            logger.error(f"Error getting spine width range: {e}")
            return self.fallback_spine_width, self.fallback_spine_width
    
    def clear_cache(self) -> None:
        """Clear the sheets cache to force reload"""
        self._sheets_cache.clear()
        logger.info("Cleared spine width lookup cache")


# Backward compatibility function
def calculate_spinewidth(sheetname: str, finalpagecount: int) -> float:
    """Backward compatible function for existing code"""
    calculator = SpineWidthCalculator()
    return calculator.calculate_spine_width_from_lookup(finalpagecount, sheetname)