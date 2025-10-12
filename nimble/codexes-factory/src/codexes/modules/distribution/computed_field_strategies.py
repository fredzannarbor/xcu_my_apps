"""Computed Field Strategies Module

This module provides strategies for computing LSI fields based on existing metadata.
These strategies derive values from existing metadata to ensure a higher field population rate.
"""

import re
import math
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..metadata.metadata_models import CodexMetadata
from .field_mapping import MappingStrategy, MappingContext, ComputedMappingStrategy

logger = logging.getLogger(__name__)


class TerritorialPricingStrategy(ComputedMappingStrategy):
    """
    Strategy for computing territorial pricing based on US price and exchange rates.
    
    This strategy calculates prices for different territories based on the US price
    and exchange rates. It supports various pricing formats and rounding rules.
    """
    
    def __init__(self, territory_code: str, exchange_rate: float = None, 
                 base_price_field: str = "list_price_usd", 
                 markup_percentage: float = 0.0,
                 rounding_rule: str = "nearest",
                 price_format: str = "${price}"):
        """
        Initialize territorial pricing strategy.
        
        Args:
            territory_code: Territory code (e.g., "CA", "UK", "AU")
            exchange_rate: Exchange rate from USD to territory currency
            base_price_field: Field name for the base price (default: "list_price_usd")
            markup_percentage: Additional markup percentage (default: 0.0)
            rounding_rule: Rounding rule ("nearest", "up", "down", "nearest_99")
            price_format: Format string for the price (e.g., "${price}", "£{price}")
        """
        self.territory_code = territory_code
        self.exchange_rate = exchange_rate
        self.base_price_field = base_price_field
        self.markup_percentage = markup_percentage
        self.rounding_rule = rounding_rule
        self.price_format = price_format
        
        # Default exchange rates if none provided
        self.default_exchange_rates = {
            "CA": 1.35,  # Canadian Dollar
            "UK": 0.78,  # British Pound
            "AU": 1.48,  # Australian Dollar
            "EU": 0.91,  # Euro
            "NZ": 1.60,  # New Zealand Dollar
            "JP": 150.0, # Japanese Yen
            "IN": 83.0,  # Indian Rupee
            "ZA": 18.0,  # South African Rand
            "MX": 17.0,  # Mexican Peso
            "BR": 5.0    # Brazilian Real
        }
        
        # Currency symbols for price formatting
        self.currency_symbols = {
            "CA": "$",   # Canadian Dollar
            "UK": "£",   # British Pound
            "AU": "$",   # Australian Dollar
            "EU": "€",   # Euro
            "NZ": "$",   # New Zealand Dollar
            "JP": "¥",   # Japanese Yen
            "IN": "₹",   # Indian Rupee
            "ZA": "R",   # South African Rand
            "MX": "$",   # Mexican Peso
            "BR": "R$"   # Brazilian Real
        }
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Calculate territorial pricing based on US price and exchange rate.
        
        Args:
            metadata: CodexMetadata object with book metadata
            context: MappingContext with additional context
            
        Returns:
            Formatted price for the specified territory
        """
        try:
            # Get the base price from metadata
            base_price = self._get_base_price(metadata)
            if base_price is None:
                logger.warning(f"Base price not found for {self.territory_code} pricing calculation")
                return ""
            
            # Get the exchange rate (use default if not provided)
            exchange_rate = self.exchange_rate
            if exchange_rate is None:
                exchange_rate = self.default_exchange_rates.get(self.territory_code)
                if exchange_rate is None:
                    logger.warning(f"No exchange rate found for territory {self.territory_code}")
                    return ""
            
            # Calculate the price in the territory's currency
            territory_price = base_price * exchange_rate
            
            # Apply markup if specified
            if self.markup_percentage > 0:
                territory_price *= (1 + self.markup_percentage / 100)
            
            # Apply rounding rule
            territory_price = self._apply_rounding(territory_price)
            
            # Format the price
            formatted_price = self._format_price(territory_price)
            
            logger.info(f"Calculated {self.territory_code} price: {formatted_price} (base: ${base_price:.2f}, rate: {exchange_rate})")
            return formatted_price
            
        except Exception as e:
            logger.error(f"Error calculating {self.territory_code} price: {e}")
            return ""
    
    def _get_base_price(self, metadata: CodexMetadata) -> Optional[float]:
        """
        Get the base price from metadata.
        
        Args:
            metadata: CodexMetadata object with book metadata
            
        Returns:
            Base price as a float, or None if not found
        """
        # Try to get the base price from the specified field
        base_price_str = getattr(metadata, self.base_price_field, None)
        
        # If not found, try common alternative field names
        if not base_price_str:
            alternative_fields = [
                "list_price_usd", "us_list_price", "us_suggested_list_price",
                "list_price", "price_usd", "price"
            ]
            
            for field in alternative_fields:
                base_price_str = getattr(metadata, field, None)
                if base_price_str:
                    break
        
        # If still not found, check if there's a "price" attribute with "usd" in the key
        if not base_price_str:
            for attr_name in dir(metadata):
                if "price" in attr_name.lower() and "usd" in attr_name.lower():
                    base_price_str = getattr(metadata, attr_name, None)
                    if base_price_str:
                        break
        
        # If we found a price string, convert it to float
        if base_price_str:
            # Remove currency symbols and commas
            price_str = str(base_price_str).replace("$", "").replace(",", "").strip()
            
            try:
                return float(price_str)
            except ValueError:
                logger.warning(f"Could not convert price '{base_price_str}' to float")
                return None
        
        return None
    
    def _apply_rounding(self, price: float) -> float:
        """
        Apply rounding rule to the price.
        
        Args:
            price: Price to round
            
        Returns:
            Rounded price
        """
        if self.rounding_rule == "nearest":
            # Round to nearest whole number
            return round(price)
        elif self.rounding_rule == "up":
            # Round up to next whole number
            return math.ceil(price)
        elif self.rounding_rule == "down":
            # Round down to previous whole number
            return math.floor(price)
        elif self.rounding_rule == "nearest_99":
            # Round to nearest .99
            return math.floor(price) + 0.99
        elif self.rounding_rule == "nearest_95":
            # Round to nearest .95
            return math.floor(price) + 0.95
        elif self.rounding_rule == "nearest_50":
            # Round to nearest .50
            base = math.floor(price)
            fraction = price - base
            if fraction < 0.25:
                return base
            elif fraction < 0.75:
                return base + 0.5
            else:
                return base + 1.0
        else:
            # Default to nearest
            return round(price)
    
    def _format_price(self, price: float) -> str:
        """
        Format the price according to the price format.
        
        Args:
            price: Price to format
            
        Returns:
            Formatted price string
        """
        # If a specific format is provided, use it
        if self.price_format:
            return self.price_format.format(price=price)
        
        # Otherwise, use the currency symbol for the territory
        currency_symbol = self.currency_symbols.get(self.territory_code, "$")
        
        # Format with 2 decimal places for most currencies, 0 for JPY
        if self.territory_code == "JP":
            return f"{currency_symbol}{int(price)}"
        else:
            return f"{currency_symbol}{price:.2f}"


class PhysicalSpecsStrategy(ComputedMappingStrategy):
    """
    Strategy for computing physical specifications based on page count and trim size.
    
    This strategy calculates physical specifications like weight and spine width
    based on page count, trim size, and paper type.
    """
    
    def __init__(self, spec_type: str, paper_type: str = "standard"):
        """
        Initialize physical specifications strategy.
        
        Args:
            spec_type: Type of specification to calculate ("weight", "spine_width", "thickness")
            paper_type: Type of paper ("standard", "premium", "lightweight")
        """
        self.spec_type = spec_type
        self.paper_type = paper_type
        
        # Paper specifications (weight per page in grams)
        self.paper_specs = {
            "standard": {
                "weight_per_page": 0.8,  # grams per page
                "thickness_per_page": 0.002,  # inches per page
                "density": 0.4  # g/cm³
            },
            "premium": {
                "weight_per_page": 1.2,  # grams per page
                "thickness_per_page": 0.003,  # inches per page
                "density": 0.5  # g/cm³
            },
            "lightweight": {
                "weight_per_page": 0.6,  # grams per page
                "thickness_per_page": 0.0015,  # inches per page
                "density": 0.35  # g/cm³
            }
        }
        
        # Cover weight (approximate)
        self.cover_weight = {
            "paperback": 15,  # grams
            "hardcover": 150  # grams
        }
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Calculate physical specifications based on page count and trim size.
        
        Args:
            metadata: CodexMetadata object with book metadata
            context: MappingContext with additional context
            
        Returns:
            Calculated physical specification
        """
        try:
            # Get page count
            page_count = self._get_page_count(metadata)
            if page_count is None:
                logger.warning(f"Page count not found for {self.spec_type} calculation")
                return ""
            
            # Get trim size
            trim_size = self._get_trim_size(metadata)
            
            # Get binding type
            binding_type = self._get_binding_type(metadata)
            
            # Calculate the requested specification
            if self.spec_type == "weight":
                return self._calculate_weight(page_count, trim_size, binding_type)
            elif self.spec_type == "spine_width":
                return self._calculate_spine_width(page_count)
            elif self.spec_type == "thickness":
                return self._calculate_thickness(page_count)
            else:
                logger.warning(f"Unknown specification type: {self.spec_type}")
                return ""
                
        except Exception as e:
            logger.error(f"Error calculating {self.spec_type}: {e}")
            return ""
    
    def _get_page_count(self, metadata: CodexMetadata) -> Optional[int]:
        """
        Get the page count from metadata.
        
        Args:
            metadata: CodexMetadata object with book metadata
            
        Returns:
            Page count as an integer, or None if not found
        """
        # Try different field names for page count
        page_count_fields = [
            "page_count", "pages", "total_pages", "number_of_pages",
            "page_extent", "extent"
        ]
        
        for field in page_count_fields:
            page_count_str = getattr(metadata, field, None)
            if page_count_str:
                try:
                    # Handle string values like "256 pages"
                    page_count_str = str(page_count_str).lower()
                    # Extract numbers from the string
                    numbers = re.findall(r'\d+', page_count_str)
                    if numbers:
                        return int(numbers[0])
                except ValueError:
                    continue
        
        return None
    
    def _get_trim_size(self, metadata: CodexMetadata) -> Dict[str, float]:
        """
        Get the trim size from metadata.
        
        Args:
            metadata: CodexMetadata object with book metadata
            
        Returns:
            Dictionary with width and height in inches
        """
        # Default trim size (6" x 9")
        default_size = {"width": 6.0, "height": 9.0}
        
        # Try different field names for trim size
        trim_size_fields = [
            "trim_size", "book_size", "dimensions", "size"
        ]
        
        for field in trim_size_fields:
            trim_size_str = getattr(metadata, field, None)
            if trim_size_str:
                # Parse trim size string like "6 x 9" or "6\" x 9\""
                trim_size_str = str(trim_size_str).lower()
                # Look for patterns like "6 x 9", "6.0 x 9.0", "6\" x 9\""
                pattern = r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)'
                match = re.search(pattern, trim_size_str)
                if match:
                    try:
                        width = float(match.group(1))
                        height = float(match.group(2))
                        return {"width": width, "height": height}
                    except ValueError:
                        continue
        
        return default_size
    
    def _get_binding_type(self, metadata: CodexMetadata) -> str:
        """
        Get the binding type from metadata.
        
        Args:
            metadata: CodexMetadata object with book metadata
            
        Returns:
            Binding type ("paperback" or "hardcover")
        """
        # Try different field names for binding type
        binding_fields = [
            "binding", "binding_type", "format", "book_format"
        ]
        
        for field in binding_fields:
            binding_str = getattr(metadata, field, None)
            if binding_str:
                binding_str = str(binding_str).lower()
                if "hard" in binding_str or "cloth" in binding_str:
                    return "hardcover"
                elif "paper" in binding_str or "soft" in binding_str:
                    return "paperback"
        
        # Default to paperback
        return "paperback"
    
    def _calculate_weight(self, page_count: int, trim_size: Dict[str, float], binding_type: str) -> str:
        """
        Calculate the weight of the book.
        
        Args:
            page_count: Number of pages
            trim_size: Dictionary with width and height
            binding_type: Type of binding
            
        Returns:
            Formatted weight string
        """
        # Get paper specifications
        paper_spec = self.paper_specs.get(self.paper_type, self.paper_specs["standard"])
        
        # Calculate text block weight
        text_weight = page_count * paper_spec["weight_per_page"]
        
        # Add cover weight
        cover_weight = self.cover_weight.get(binding_type, self.cover_weight["paperback"])
        
        # Total weight in grams
        total_weight_grams = text_weight + cover_weight
        
        # Convert to ounces (1 gram = 0.035274 ounces)
        total_weight_ounces = total_weight_grams * 0.035274
        
        # Format based on weight
        if total_weight_ounces < 1:
            return f"{total_weight_grams:.0f}g"
        else:
            return f"{total_weight_ounces:.1f}oz"
    
    def _calculate_spine_width(self, page_count: int) -> str:
        """
        Calculate the spine width of the book.
        
        Args:
            page_count: Number of pages
            
        Returns:
            Formatted spine width string
        """
        # Get paper specifications
        paper_spec = self.paper_specs.get(self.paper_type, self.paper_specs["standard"])
        
        # Calculate spine width (thickness per page * number of pages)
        spine_width_inches = page_count * paper_spec["thickness_per_page"]
        
        # Add cover thickness (approximate)
        cover_thickness = 0.02 if spine_width_inches > 0.125 else 0.01
        spine_width_inches += cover_thickness
        
        # Format to appropriate precision
        if spine_width_inches < 0.1:
            return f"{spine_width_inches:.3f}\""
        else:
            return f"{spine_width_inches:.2f}\""
    
    def _calculate_thickness(self, page_count: int) -> str:
        """
        Calculate the thickness of the book.
        
        Args:
            page_count: Number of pages
            
        Returns:
            Formatted thickness string
        """
        # Get paper specifications
        paper_spec = self.paper_specs.get(self.paper_type, self.paper_specs["standard"])
        
        # Calculate thickness (same as spine width for most purposes)
        thickness_inches = page_count * paper_spec["thickness_per_page"]
        
        # Format to appropriate precision
        if thickness_inches < 0.1:
            return f"{thickness_inches:.3f}\""
        else:
            return f"{thickness_inches:.2f}\""


class DateComputationStrategy(ComputedMappingStrategy):
    """
    Strategy for computing dates based on available date information.
    
    This strategy calculates dates like street date and publication date
    based on available date information. It supports various date formats
    and can apply offsets for calculating related dates.
    """
    
    def __init__(self, date_type: str, offset_days: int = 0, 
                 preferred_base_field: str = None,
                 fallback_to_current: bool = False):
        """
        Initialize date computation strategy.
        
        Args:
            date_type: Type of date to calculate ("pub_date", "street_date", "copyright_date")
            offset_days: Number of days to offset from the base date
            preferred_base_field: Preferred field to use as base date
            fallback_to_current: Whether to use current date as fallback
        """
        self.date_type = date_type
        self.offset_days = offset_days
        self.preferred_base_field = preferred_base_field
        self.fallback_to_current = fallback_to_current
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Calculate dates based on available date information.
        
        Args:
            metadata: CodexMetadata object with book metadata
            context: MappingContext with additional context
            
        Returns:
            Calculated date in YYYY-MM-DD format
        """
        try:
            # Get the base date from metadata
            base_date = self._get_base_date(metadata)
            if base_date is None:
                logger.warning(f"Base date not found for {self.date_type} calculation")
                return ""
            
            # Apply offset
            if self.offset_days != 0:
                calculated_date = base_date + timedelta(days=self.offset_days)
            else:
                calculated_date = base_date
            
            # Format the date
            return calculated_date.strftime("%Y-%m-%d")
            
        except Exception as e:
            logger.error(f"Error calculating {self.date_type}: {e}")
            return ""
    
    def _get_base_date(self, metadata: CodexMetadata) -> Optional[datetime]:
        """
        Get the base date from metadata.
        
        Args:
            metadata: CodexMetadata object with book metadata
            
        Returns:
            Base date as a datetime object, or None if not found
        """
        # If a preferred base field is specified, try it first
        if self.preferred_base_field:
            date_str = getattr(metadata, self.preferred_base_field, None)
            if date_str:
                parsed_date = self._parse_date(str(date_str))
                if parsed_date:
                    return parsed_date
        
        # Try different field names for dates in priority order
        date_fields = [
            "publication_date", "pub_date", "publish_date",
            "street_date", "release_date", "on_sale_date",
            "copyright_date", "created_date", "date",
            "available_date", "embargo_date"
        ]
        
        for field in date_fields:
            date_str = getattr(metadata, field, None)
            if date_str:
                # Try to parse the date
                parsed_date = self._parse_date(str(date_str))
                if parsed_date:
                    return parsed_date
        
        # If fallback to current date is enabled and no date found
        if self.fallback_to_current:
            logger.info(f"No base date found for {self.date_type}, using current date as fallback")
            return datetime.now()
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse a date string into a datetime object.
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Parsed datetime object, or None if parsing fails
        """
        # Common date formats to try
        date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None


class PublicationDateStrategy(DateComputationStrategy):
    """
    Specialized strategy for computing publication dates.
    
    This strategy prioritizes publication-related date fields and can
    calculate publication dates based on other available dates.
    """
    
    def __init__(self, offset_days: int = 0, fallback_to_current: bool = False):
        """
        Initialize publication date strategy.
        
        Args:
            offset_days: Number of days to offset from the base date
            fallback_to_current: Whether to use current date as fallback
        """
        super().__init__(
            date_type="publication_date",
            offset_days=offset_days,
            preferred_base_field="publication_date",
            fallback_to_current=fallback_to_current
        )
    
    def _get_base_date(self, metadata: CodexMetadata) -> Optional[datetime]:
        """
        Get the base date from metadata, prioritizing publication-related fields.
        
        Args:
            metadata: CodexMetadata object with book metadata
            
        Returns:
            Base date as a datetime object, or None if not found
        """
        # Priority order for publication date fields
        pub_date_fields = [
            "publication_date", "pub_date", "publish_date",
            "copyright_date", "release_date", "street_date",
            "on_sale_date", "available_date"
        ]
        
        for field in pub_date_fields:
            date_str = getattr(metadata, field, None)
            if date_str:
                parsed_date = self._parse_date(str(date_str))
                if parsed_date:
                    return parsed_date
        
        # If fallback to current date is enabled and no date found
        if self.fallback_to_current:
            logger.info(f"No publication date found, using current date as fallback")
            return datetime.now()
        
        return None


class StreetDateStrategy(DateComputationStrategy):
    """
    Specialized strategy for computing street dates (on-sale dates).
    
    This strategy can calculate street dates based on publication dates
    with configurable offsets for different distribution channels.
    """
    
    def __init__(self, offset_days: int = 7, fallback_to_current: bool = False):
        """
        Initialize street date strategy.
        
        Args:
            offset_days: Number of days after publication date (default: 7)
            fallback_to_current: Whether to use current date as fallback
        """
        super().__init__(
            date_type="street_date",
            offset_days=offset_days,
            preferred_base_field="street_date",
            fallback_to_current=fallback_to_current
        )
    
    def _get_base_date(self, metadata: CodexMetadata) -> Optional[datetime]:
        """
        Get the base date from metadata, prioritizing street date fields.
        
        Args:
            metadata: CodexMetadata object with book metadata
            
        Returns:
            Base date as a datetime object, or None if not found
        """
        # Priority order for street date fields
        street_date_fields = [
            "street_date", "on_sale_date", "release_date",
            "available_date", "publication_date", "pub_date"
        ]
        
        for field in street_date_fields:
            date_str = getattr(metadata, field, None)
            if date_str:
                parsed_date = self._parse_date(str(date_str))
                if parsed_date:
                    # If this is a publication date, add the offset
                    if field in ["publication_date", "pub_date"] and self.offset_days > 0:
                        return parsed_date + timedelta(days=self.offset_days)
                    return parsed_date
        
        # If fallback to current date is enabled and no date found
        if self.fallback_to_current:
            logger.info(f"No street date found, using current date as fallback")
            return datetime.now()
        
        return None


class CopyrightDateStrategy(DateComputationStrategy):
    """
    Specialized strategy for computing copyright dates.
    
    This strategy prioritizes copyright-related date fields and can
    extract copyright years from various formats.
    """
    
    def __init__(self, fallback_to_current: bool = False):
        """
        Initialize copyright date strategy.
        
        Args:
            fallback_to_current: Whether to use current date as fallback
        """
        super().__init__(
            date_type="copyright_date",
            offset_days=0,
            preferred_base_field="copyright_date",
            fallback_to_current=fallback_to_current
        )
    
    def _get_base_date(self, metadata: CodexMetadata) -> Optional[datetime]:
        """
        Get the base date from metadata, prioritizing copyright-related fields.
        
        Args:
            metadata: CodexMetadata object with book metadata
            
        Returns:
            Base date as a datetime object, or None if not found
        """
        # Priority order for copyright date fields
        copyright_date_fields = [
            "copyright_date", "copyright_year", "copyright",
            "publication_date", "pub_date", "created_date"
        ]
        
        for field in copyright_date_fields:
            date_str = getattr(metadata, field, None)
            if date_str:
                # Handle copyright year format (just a year)
                if field in ["copyright_year", "copyright"] and str(date_str).isdigit():
                    try:
                        year = int(date_str)
                        if 1900 <= year <= datetime.now().year + 10:  # Reasonable year range
                            return datetime(year, 1, 1)
                    except ValueError:
                        continue
                
                # Try to parse as regular date
                parsed_date = self._parse_date(str(date_str))
                if parsed_date:
                    return parsed_date
        
        # If fallback to current date is enabled and no date found
        if self.fallback_to_current:
            logger.info(f"No copyright date found, using current date as fallback")
            return datetime.now()
        
        return None


class FilePathStrategy(ComputedMappingStrategy):
    """
    Strategy for computing file paths based on ISBN and standard naming conventions.
    
    This strategy calculates file paths for cover, interior, and jacket files
    based on ISBN and standard naming conventions. It supports various naming
    patterns and can include additional metadata in the filename.
    """
    
    def __init__(self, file_type: str, base_path: str = "", 
                 naming_pattern: str = "{isbn}_{file_type}",
                 include_title: bool = False,
                 max_title_length: int = 50):
        """
        Initialize file path strategy.
        
        Args:
            file_type: Type of file ("cover", "interior", "jacket", "epub", "mobi")
            base_path: Base path for files (optional)
            naming_pattern: Pattern for filename (default: "{isbn}_{file_type}")
            include_title: Whether to include title in filename
            max_title_length: Maximum length for title in filename
        """
        self.file_type = file_type
        self.base_path = base_path
        self.naming_pattern = naming_pattern
        self.include_title = include_title
        self.max_title_length = max_title_length
        
        # File extensions for different file types
        self.file_extensions = {
            "cover": ".pdf",
            "interior": ".pdf",
            "jacket": ".pdf",
            "dust_jacket": ".pdf",
            "spine": ".pdf",
            "back_cover": ".pdf",
            "epub": ".epub",
            "mobi": ".mobi",
            "pdf": ".pdf",
            "audiobook": ".mp3",
            "thumbnail": ".jpg",
            "preview": ".pdf"
        }
        
        # LSI-specific naming conventions
        self.lsi_naming_conventions = {
            "cover": "Cover",
            "interior": "Text",
            "jacket": "Jacket",
            "dust_jacket": "DustJacket",
            "spine": "Spine",
            "back_cover": "BackCover"
        }
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Calculate file paths based on ISBN and standard naming conventions.
        
        Args:
            metadata: CodexMetadata object with book metadata
            context: MappingContext with additional context
            
        Returns:
            Calculated file path
        """
        try:
            # Get the ISBN
            isbn = self._get_isbn(metadata)
            if not isbn:
                logger.warning(f"ISBN not found for {self.file_type} file path calculation")
                return ""
            
            # Get the file extension
            extension = self.file_extensions.get(self.file_type, ".pdf")
            
            # Get additional metadata for filename
            title = self._get_clean_title(metadata) if self.include_title else ""
            
            # Use LSI naming convention if available
            lsi_file_type = self.lsi_naming_conventions.get(self.file_type, self.file_type)
            
            # Build filename using pattern
            filename_parts = {
                "isbn": isbn,
                "file_type": self.file_type,
                "lsi_file_type": lsi_file_type,
                "title": title
            }
            
            # Apply naming pattern
            filename_base = self.naming_pattern.format(**filename_parts)
            
            # Clean the filename
            filename_base = self._clean_filename(filename_base)
            
            # Add extension
            filename = f"{filename_base}{extension}"
            
            # Construct full path
            if self.base_path:
                file_path = f"{self.base_path}/{filename}"
            else:
                file_path = filename
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error calculating {self.file_type} file path: {e}")
            return ""
    
    def _get_isbn(self, metadata: CodexMetadata) -> Optional[str]:
        """
        Get the ISBN from metadata.
        
        Args:
            metadata: CodexMetadata object with book metadata
            
        Returns:
            ISBN as a string, or None if not found
        """
        # Try different field names for ISBN in priority order
        isbn_fields = [
            "isbn13", "isbn_13", "isbn",
            "isbn10", "isbn_10", "sku", "product_id"
        ]
        
        for field in isbn_fields:
            isbn_str = getattr(metadata, field, None)
            if isbn_str:
                # Clean the ISBN (remove hyphens, spaces, and other separators)
                isbn_clean = str(isbn_str).replace("-", "").replace(" ", "").replace(".", "")
                
                # Validate ISBN length
                if len(isbn_clean) == 13 or len(isbn_clean) == 10:
                    return isbn_clean
                elif len(isbn_clean) > 13:
                    # Take first 13 characters if longer
                    return isbn_clean[:13]
                elif len(isbn_clean) >= 10:
                    return isbn_clean
        
        return None
    
    def _get_clean_title(self, metadata: CodexMetadata) -> str:
        """
        Get a clean title for use in filenames.
        
        Args:
            metadata: CodexMetadata object with book metadata
            
        Returns:
            Clean title string suitable for filenames
        """
        title = getattr(metadata, "title", "")
        if not title:
            return ""
        
        # Clean the title for filename use
        title_clean = self._clean_filename(str(title))
        
        # Truncate if too long
        if len(title_clean) > self.max_title_length:
            title_clean = title_clean[:self.max_title_length]
        
        return title_clean
    
    def _clean_filename(self, filename: str) -> str:
        """
        Clean a filename by removing or replacing invalid characters.
        
        Args:
            filename: Raw filename string
            
        Returns:
            Clean filename string
        """
        # Remove or replace invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        
        # Replace multiple spaces/underscores with single underscore
        filename = re.sub(r'[_\s]+', '_', filename)
        
        # Remove leading/trailing underscores and spaces
        filename = filename.strip('_ ')
        
        # Ensure filename is not empty
        if not filename:
            filename = "unknown"
        
        return filename


class LSIFilePathStrategy(FilePathStrategy):
    """
    Specialized file path strategy for LSI (Lightning Source Inc.) naming conventions.
    
    This strategy follows LSI-specific naming patterns and file organization.
    """
    
    def __init__(self, file_type: str, base_path: str = ""):
        """
        Initialize LSI file path strategy.
        
        Args:
            file_type: Type of file ("cover", "interior", "jacket")
            base_path: Base path for files (optional)
        """
        # Use LSI-specific naming pattern
        super().__init__(
            file_type=file_type,
            base_path=base_path,
            naming_pattern="{isbn}_{lsi_file_type}",
            include_title=False
        )


class DetailedFilePathStrategy(FilePathStrategy):
    """
    File path strategy that includes additional metadata in the filename.
    
    This strategy creates more descriptive filenames including title and other metadata.
    """
    
    def __init__(self, file_type: str, base_path: str = "", include_author: bool = False):
        """
        Initialize detailed file path strategy.
        
        Args:
            file_type: Type of file
            base_path: Base path for files (optional)
            include_author: Whether to include author in filename
        """
        pattern = "{isbn}_{title}_{file_type}" if not include_author else "{isbn}_{title}_{author}_{file_type}"
        
        super().__init__(
            file_type=file_type,
            base_path=base_path,
            naming_pattern=pattern,
            include_title=True,
            max_title_length=30
        )
        
        self.include_author = include_author
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Calculate detailed file paths with additional metadata.
        
        Args:
            metadata: CodexMetadata object with book metadata
            context: MappingContext with additional context
            
        Returns:
            Calculated file path with detailed naming
        """
        try:
            # Get the ISBN
            isbn = self._get_isbn(metadata)
            if not isbn:
                logger.warning(f"ISBN not found for {self.file_type} file path calculation")
                return ""
            
            # Get the file extension
            extension = self.file_extensions.get(self.file_type, ".pdf")
            
            # Get metadata for filename
            title = self._get_clean_title(metadata)
            author = self._get_clean_author(metadata) if self.include_author else ""
            
            # Build filename parts
            filename_parts = {
                "isbn": isbn,
                "file_type": self.file_type,
                "title": title,
                "author": author
            }
            
            # Apply naming pattern
            filename_base = self.naming_pattern.format(**filename_parts)
            
            # Clean the filename
            filename_base = self._clean_filename(filename_base)
            
            # Add extension
            filename = f"{filename_base}{extension}"
            
            # Construct full path
            if self.base_path:
                file_path = f"{self.base_path}/{filename}"
            else:
                file_path = filename
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error calculating detailed {self.file_type} file path: {e}")
            return ""
    
    def _get_clean_author(self, metadata: CodexMetadata) -> str:
        """
        Get a clean author name for use in filenames.
        
        Args:
            metadata: CodexMetadata object with book metadata
            
        Returns:
            Clean author string suitable for filenames
        """
        # Try different field names for author
        author_fields = ["author", "contributor_one", "primary_author", "first_author"]
        
        for field in author_fields:
            author = getattr(metadata, field, "")
            if author:
                # Clean the author name for filename use
                author_clean = self._clean_filename(str(author))
                
                # Truncate if too long
                if len(author_clean) > 20:
                    author_clean = author_clean[:20]
                
                return author_clean
        
        return ""


class OrganizedFilePathStrategy(FilePathStrategy):
    """
    File path strategy that organizes files into subdirectories by type and date.
    
    This strategy creates an organized directory structure for better file management.
    """
    
    def __init__(self, file_type: str, organize_by_date: bool = True, 
                 organize_by_imprint: bool = False):
        """
        Initialize organized file path strategy.
        
        Args:
            file_type: Type of file
            organize_by_date: Whether to organize by publication date
            organize_by_imprint: Whether to organize by imprint
        """
        super().__init__(
            file_type=file_type,
            base_path="",  # Will be constructed dynamically
            naming_pattern="{isbn}_{file_type}"
        )
        
        self.organize_by_date = organize_by_date
        self.organize_by_imprint = organize_by_imprint
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Calculate organized file paths with dynamic directory structure.
        
        Args:
            metadata: CodexMetadata object with book metadata
            context: MappingContext with additional context
            
        Returns:
            Calculated file path with organized directory structure
        """
        try:
            # Get the ISBN
            isbn = self._get_isbn(metadata)
            if not isbn:
                logger.warning(f"ISBN not found for {self.file_type} file path calculation")
                return ""
            
            # Build dynamic base path
            path_parts = []
            
            # Add file type directory
            path_parts.append(f"{self.file_type}s")
            
            # Add imprint directory if requested
            if self.organize_by_imprint:
                imprint = getattr(metadata, "imprint", "unknown_imprint")
                if imprint:
                    path_parts.append(self._clean_filename(str(imprint)))
            
            # Add date directory if requested
            if self.organize_by_date:
                pub_date = self._get_publication_year(metadata)
                if pub_date:
                    path_parts.append(str(pub_date))
            
            # Construct base path
            base_path = "/".join(path_parts) if path_parts else ""
            
            # Get the file extension
            extension = self.file_extensions.get(self.file_type, ".pdf")
            
            # Build filename
            filename = f"{isbn}_{self.file_type}{extension}"
            
            # Construct full path
            if base_path:
                file_path = f"{base_path}/{filename}"
            else:
                file_path = filename
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error calculating organized {self.file_type} file path: {e}")
            return ""
    
    def _get_publication_year(self, metadata: CodexMetadata) -> Optional[int]:
        """
        Get the publication year from metadata.
        
        Args:
            metadata: CodexMetadata object with book metadata
            
        Returns:
            Publication year as integer, or None if not found
        """
        # Try different date fields
        date_fields = ["publication_date", "pub_date", "copyright_date", "street_date"]
        
        for field in date_fields:
            date_str = getattr(metadata, field, None)
            if date_str:
                try:
                    # Try to extract year from date string
                    date_str = str(date_str)
                    
                    # Look for 4-digit year
                    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
                    if year_match:
                        year = int(year_match.group())
                        if 1900 <= year <= datetime.now().year + 10:
                            return year
                except (ValueError, AttributeError):
                    continue
        
        return None