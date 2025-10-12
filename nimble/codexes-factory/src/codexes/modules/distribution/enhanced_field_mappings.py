"""
Enhanced Field Mappings Module

This module provides enhanced field mapping strategies for LSI field generation.
"""

import logging
import re
from typing import Dict, Any, Optional, List

from .field_mapping import (
    FieldMappingRegistry, MappingStrategy, MappingContext,
    DirectMappingStrategy, ComputedMappingStrategy, DefaultMappingStrategy
)
from .computed_field_strategies import (
    PhysicalSpecsStrategy, DateComputationStrategy, PublicationDateStrategy, 
    StreetDateStrategy, CopyrightDateStrategy, FilePathStrategy,
    LSIFilePathStrategy, DetailedFilePathStrategy, OrganizedFilePathStrategy
)
from .pricing_strategy import (
    PricingMappingStrategy, USPricingStrategy, TerritorialPricingStrategy,
    MarketPricingStrategy, DiscountStrategy
)
from .enhanced_bisac_strategy import EnhancedBISACCategoryStrategy
from .contributor_role_mapping import ContributorRoleMappingStrategy
from .short_description_mapping import ShortDescriptionMappingStrategy
from .thema_subject_mapping import ThemaSubjectMappingStrategy
from .tranche_config_loader import TrancheConfigLoader
from ..metadata.metadata_models import CodexMetadata
from .enhanced_file_path_strategies import (
    EnhancedFilePathStrategy, EnhancedAnnotationStrategy, 
    EnhancedContributorBioStrategy, EnhancedTOCStrategy, BlankFieldStrategy
)
from .tranche_aware_series_strategy import TrancheAwareSeriesStrategy
from .tranche_override_strategy import TrancheOverrideStrategy
from .json_metadata_extractor import JSONMetadataExtractor
from .series_description_processor import SeriesDescriptionProcessor
from .tranche_override_manager import TrancheOverrideManager
from .tranche_override_wrapper import wrap_registry_with_tranche_overrides


logger = logging.getLogger(__name__)


def create_simple_toc(book_content: str) -> str:
    """
    Create a simple table of contents from book content.
    
    Args:
        book_content: Book content to extract TOC from
        
    Returns:
        Formatted table of contents
    """
    # Extract chapter headings using regex
    chapter_pattern = r"(?:Chapter|CHAPTER)\s+(\d+|[IVX]+)(?:\s*[:.-])?\s*([^\n]+)"
    chapters = re.findall(chapter_pattern, book_content)
    
    # Extract section headings
    section_pattern = r"(?:Part|PART|Section|SECTION)\s+(\d+|[IVX]+)(?:\s*[:.-])?\s*([^\n]+)"
    sections = re.findall(section_pattern, book_content)
    
    # Create TOC
    toc = []
    
    # Add sections
    for section_num, section_title in sections:
        toc.append(f"Part {section_num}: {section_title.strip()}")
    
    # Add chapters with page numbers (placeholder)
    page = 1
    for chapter_num, chapter_title in chapters:
        toc.append(f"  Chapter {chapter_num}: {chapter_title.strip()} {page}")
        page += 10  # Placeholder page increment
    
    # Add standard sections if not found
    if not any("Introduction" in line for line in toc):
        toc.insert(0, "Introduction i")
    
    if not any("Conclusion" in line for line in toc):
        toc.append(f"Conclusion {page}")
        page += 5
    
    if not any("References" in line for line in toc) and "reference" in book_content.lower():
        toc.append(f"References {page}")
        page += 3
    
    if not any("Index" in line for line in toc) and len(book_content) > 50000:
        toc.append(f"Index {page}")
    
    return "\n".join(toc)


def _format_keywords_computed(metadata: CodexMetadata, context: MappingContext) -> str:
    """Computed strategy function for formatting keywords."""
    keywords = metadata.keywords or ""
    # Ensure keywords are properly formatted with semicolons
    if keywords:
        # Split by common separators and rejoin with semicolons
        keyword_list = re.split(r'[,;|]', keywords)
        # Clean up each keyword
        keyword_list = [k.strip() for k in keyword_list if k.strip()]
        # Join with semicolons
        return "; ".join(keyword_list)
    return ""


def _format_toc_computed(metadata: CodexMetadata, context: MappingContext) -> str:
    """Computed strategy function for formatting table of contents."""
    toc = metadata.table_of_contents or ""
    
    # If TOC is empty and we have book content in context, try to create one
    if not toc and context and hasattr(context, 'config') and context.config and 'book_content' in context.config:
        toc = create_simple_toc(context.config['book_content'])
    
    # Ensure proper formatting
    if toc:
        # Ensure consistent formatting for page numbers
        dot_pattern = r'\.{3,}'
        toc = re.sub(dot_pattern, ' ', toc)
        
        # Ensure proper indentation for hierarchical structure
        lines = toc.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Check if this is a part/section header
            if re.match(r'^(?:Part|PART|Section|SECTION)', line):
                formatted_lines.append(line)
            # Check if this is a chapter
            elif re.match(r'^(?:Chapter|CHAPTER)', line):
                formatted_lines.append(f"  {line}")
            # Otherwise, assume it's a subsection or appendix
            elif line:
                if re.match(r'^(?:Appendix|APPENDIX)', line):
                    formatted_lines.append(line)
                else:
                    formatted_lines.append(f"    {line}")
        
        # Ensure it doesn't exceed 2000 characters
        result = "\n".join(formatted_lines)
        if len(result) > 2000:
            result = result[:1997] + "..."
        
        return result
    
    return toc


class ThemaSubjectStrategy(MappingStrategy):
    """Strategy for extracting and mapping thema subjects from JSON metadata."""
    
    def __init__(self, subject_number: int):
        """
        Initialize strategy for specific thema subject.
        
        Args:
            subject_number: Which thema subject to extract (1, 2, or 3)
        """
        self.subject_number = subject_number
        self.extractor = JSONMetadataExtractor()
        
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Extract thema subject from metadata."""
        try:
            # Get raw metadata dict from context
            raw_metadata = getattr(context, 'raw_metadata', {}) if context else {}
            if not raw_metadata and metadata:
                # Try to get from metadata object
                raw_metadata = getattr(metadata, '__dict__', {})
                
            subjects = self.extractor.extract_thema_subjects(raw_metadata)
            
            # Return the requested subject number (1-indexed)
            if len(subjects) >= self.subject_number:
                return subjects[self.subject_number - 1]
                
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting thema subject {self.subject_number}: {e}")
            return ""


class AgeRangeStrategy(MappingStrategy):
    """Strategy for extracting age range values from JSON metadata."""
    
    def __init__(self, age_type: str):
        """
        Initialize strategy for specific age type.
        
        Args:
            age_type: Either 'min' or 'max'
        """
        self.age_type = age_type
        self.extractor = JSONMetadataExtractor()
        
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Extract age value from metadata."""
        try:
            # Get raw metadata dict from context
            raw_metadata = getattr(context, 'raw_metadata', {}) if context else {}
            if not raw_metadata and metadata:
                raw_metadata = getattr(metadata, '__dict__', {})
                
            min_age, max_age = self.extractor.extract_age_range(raw_metadata)
            
            if self.age_type == 'min' and min_age is not None:
                return str(min_age)
            elif self.age_type == 'max' and max_age is not None:
                return str(max_age)
                
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting {self.age_type} age: {e}")
            return ""


class SeriesAwareDescriptionStrategy(MappingStrategy):
    """Strategy for processing descriptions with series context."""
    
    def __init__(self):
        """Initialize the series-aware description strategy."""
        self.processor = SeriesDescriptionProcessor()
        self.extractor = JSONMetadataExtractor()
        
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Process description with series context."""
        try:
            # Get the base description
            description = getattr(metadata, 'short_description', '') or ""
            
            # Get series name from metadata
            series_name = getattr(metadata, 'series_name', None)
            
            # If no series in metadata, try to extract from raw metadata
            if not series_name and context:
                raw_metadata = getattr(context, 'raw_metadata', {})
                series_name, _ = self.extractor.extract_series_info(raw_metadata)
                
            # Process description with series context
            return self.processor.process_description(description, series_name)
            
        except Exception as e:
            logger.error(f"Error processing series-aware description: {e}")
            return getattr(metadata, 'short_description', '') or ""


class BlankIngramPricingStrategy(MappingStrategy):
    """Strategy to ensure specific Ingram pricing fields remain blank."""
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Always return blank for Ingram pricing fields."""
        return ""


class TrancheFilePathStrategy(MappingStrategy):
    """Strategy for generating file paths from tranche configuration."""
    
    def __init__(self, path_type: str):
        """
        Initialize strategy for specific path type.
        
        Args:
            path_type: Either 'interior' or 'cover'
        """
        self.path_type = path_type
        
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Generate file path from tranche configuration."""
        try:
            # Get tranche config from context
            if not context or not hasattr(context, 'config'):
                return ""
                
            tranche_config = context.config.get('tranche_config', {})
            file_path_templates = tranche_config.get('file_path_templates', {})
            
            template = file_path_templates.get(self.path_type, "")
            if not template:
                return ""
                
            # Replace template variables
            title_slug = self._create_title_slug(metadata.title or "")
            isbn = getattr(metadata, 'isbn13', '') or getattr(metadata, 'isbn', '') or ""
            
            path = template.format(
                title_slug=title_slug,
                isbn=isbn,
                title=metadata.title or "",
                author=getattr(metadata, 'author', '') or ""
            )
            
            return self._sanitize_path(path)
            
        except Exception as e:
            logger.error(f"Error generating {self.path_type} file path: {e}")
            return ""
            
    def _create_title_slug(self, title: str) -> str:
        """Create URL-friendly slug from title."""
        if not title:
            return ""
            
        # Replace spaces and special characters with underscores
        slug = re.sub(r'[^\w\s-]', '', title)
        slug = re.sub(r'[-\s]+', '_', slug)
        return slug.strip('_')
        
    def _sanitize_path(self, path: str) -> str:
        """Sanitize file path for LSI requirements."""
        if not path:
            return ""
            
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"|?*]', '_', path)
        
        # Ensure path doesn't exceed reasonable length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
            
        return sanitized


def create_comprehensive_lsi_registry(config=None, llm_field_completer=None, tranche_name=None) -> FieldMappingRegistry:
    """
    Create a comprehensive field mapping registry for LSI with specialized strategies.
    
    Args:
        config: Optional LSIConfiguration instance for default values
        llm_field_completer: Optional LLMFieldCompleter for intelligent field completion
        tranche_name: Optional tranche name for tranche-specific settings
        
    Returns:
        FieldMappingRegistry with comprehensive mapping strategies
    """
    # Import here to avoid scoping issues
    from .tranche_config_loader import TrancheConfigLoader
    
    # Create the base registry
    registry = create_enhanced_field_mapping_registry(llm_field_completer)
    
    # Add tranche-specific BISAC subject if provided
    if tranche_name:
        tranche_loader = TrancheConfigLoader()
        tranche_bisac = tranche_loader.get_tranche_bisac_subject(tranche_name)
        if tranche_bisac:
            # Create context config for use by BisacCategoryMappingStrategy
            context_config = {'tranche_bisac_subject': tranche_bisac}
            # Add to registry context
            registry.context_config = context_config
    
    # If we have a configuration, update the strategies with config values
    if config and hasattr(config, 'get_default_value'):
        # Update LSI Account Information from config
        if config.get_default_value("lightning_source_account"):
            # Register with multiple possible field name variations
            account_value = config.get_default_value("lightning_source_account")
            registry.register_strategy("Lightning Source Account", DefaultMappingStrategy(account_value))
            registry.register_strategy("Lightning Source Account #", DefaultMappingStrategy(account_value))
            registry.register_strategy("LSI Account", DefaultMappingStrategy(account_value))
            registry.register_strategy("LSI Account Number", DefaultMappingStrategy(account_value))
            registry.register_strategy("Account Number", DefaultMappingStrategy(account_value))
            registry.register_strategy("Account ID", DefaultMappingStrategy(account_value))
        
        # Update submission methods from config
        if config.get_default_value("cover_submission_method"):
            cover_method = config.get_default_value("cover_submission_method")
            registry.register_strategy("Cover Submission Method", DefaultMappingStrategy(cover_method))
            registry.register_strategy("Cover/Jacket Submission Method", DefaultMappingStrategy(cover_method))
            registry.register_strategy("Cover Method", DefaultMappingStrategy(cover_method))
            registry.register_strategy("Jacket Submission Method", DefaultMappingStrategy(cover_method))
            registry.register_strategy("Cover Delivery Method", DefaultMappingStrategy(cover_method))
            registry.register_strategy("Jacket Path / Filename", DefaultMappingStrategy(""))  # Empty default
        
        if config.get_default_value("text_block_submission_method"):
            text_method = config.get_default_value("text_block_submission_method")
            registry.register_strategy("Text Block Submission Method", DefaultMappingStrategy(text_method))
            registry.register_strategy("Text Block SubmissionMethod", DefaultMappingStrategy(text_method))
            registry.register_strategy("Text Submission Method", DefaultMappingStrategy(text_method))
            registry.register_strategy("Interior Submission Method", DefaultMappingStrategy(text_method))
            registry.register_strategy("Text Delivery Method", DefaultMappingStrategy(text_method))
            # Removed - will be handled by enhanced strategy later
        
        # Update rendition/booktype from config
        if config.get_default_value("rendition_booktype"):
            booktype = config.get_default_value("rendition_booktype")
            registry.register_strategy("Rendition /Booktype", DefaultMappingStrategy(booktype))
            registry.register_strategy("Rendition/Booktype", DefaultMappingStrategy(booktype))
            registry.register_strategy("Book Type", DefaultMappingStrategy(booktype))
            registry.register_strategy("Binding Type", DefaultMappingStrategy(booktype))
            registry.register_strategy("Format", DefaultMappingStrategy(booktype))
            registry.register_strategy("Book Format", DefaultMappingStrategy(booktype))
        
        # Update carton pack quantity from config
        if config.get_default_value("carton_pack_quantity"):
            carton_qty = config.get_default_value("carton_pack_quantity")
            registry.register_strategy("Carton Pack Quantity", DefaultMappingStrategy(carton_qty))
            registry.register_strategy("Carton Quantity", DefaultMappingStrategy(carton_qty))
            registry.register_strategy("Pack Quantity", DefaultMappingStrategy(carton_qty))
            registry.register_strategy("Units Per Carton", DefaultMappingStrategy(carton_qty))
            registry.register_strategy("Carton Count", DefaultMappingStrategy(carton_qty))
        
        # Update territorial rights from config
        if config.get_default_value("territorial_rights"):
            rights = config.get_default_value("territorial_rights")
            registry.register_strategy("Territorial Rights", DefaultMappingStrategy(rights))
            registry.register_strategy("Distribution Rights", DefaultMappingStrategy(rights))
            registry.register_strategy("Sales Rights", DefaultMappingStrategy(rights))
            registry.register_strategy("Market Rights", DefaultMappingStrategy(rights))
            registry.register_strategy("Territory", DefaultMappingStrategy(rights))
        
        # Update returnability from config
        if config.get_default_value("returnability"):
            returns = config.get_default_value("returnability")
            registry.register_strategy("Returnable", DefaultMappingStrategy(returns))
            registry.register_strategy("Returns Allowed", DefaultMappingStrategy(returns))
            registry.register_strategy("Return Policy", DefaultMappingStrategy(returns))
            registry.register_strategy("Returns", DefaultMappingStrategy(returns))
            registry.register_strategy("Return Status", DefaultMappingStrategy(returns))
        
        # Update wholesale discounts from config
        if config.get_default_value("us_wholesale_discount"):
            us_discount = config.get_default_value("us_wholesale_discount")
            registry.register_strategy("US Wholesale Discount", DefaultMappingStrategy(us_discount))
            registry.register_strategy("US Wholesale Discount %", DefaultMappingStrategy(us_discount))
            registry.register_strategy("US Discount", DefaultMappingStrategy(us_discount))
            registry.register_strategy("US Trade Discount", DefaultMappingStrategy(us_discount))
            registry.register_strategy("United States Discount", DefaultMappingStrategy(us_discount))
        
        if config.get_default_value("uk_wholesale_discount"):
            uk_discount = config.get_default_value("uk_wholesale_discount")
            registry.register_strategy("UK Wholesale Discount (%)", DefaultMappingStrategy(uk_discount))
            registry.register_strategy("UK Wholesale Discount %", DefaultMappingStrategy(uk_discount))
            registry.register_strategy("UK Discount", DefaultMappingStrategy(uk_discount))
            registry.register_strategy("UK Trade Discount", DefaultMappingStrategy(uk_discount))
            registry.register_strategy("United Kingdom Discount", DefaultMappingStrategy(uk_discount))
        
        if config.get_default_value("eu_wholesale_discount"):
            eu_discount = config.get_default_value("eu_wholesale_discount")
            registry.register_strategy("EU Wholesale Discount % (Mode 2)", DefaultMappingStrategy(eu_discount))
            registry.register_strategy("EU Wholesale Discount %", DefaultMappingStrategy(eu_discount))
            registry.register_strategy("EU Discount", DefaultMappingStrategy(eu_discount))
            registry.register_strategy("EU Trade Discount", DefaultMappingStrategy(eu_discount))
            registry.register_strategy("Europe Discount", DefaultMappingStrategy(eu_discount))
            registry.register_strategy("European Union Discount", DefaultMappingStrategy(eu_discount))
        
        # Update edition information from config
        if config.get_default_value("edition_number"):
            edition_num = config.get_default_value("edition_number")
            registry.register_strategy("Edition Number", DefaultMappingStrategy(edition_num))
            registry.register_strategy("Edition", DefaultMappingStrategy(edition_num))
            registry.register_strategy("Edition #", DefaultMappingStrategy(edition_num))
            registry.register_strategy("Ed. Number", DefaultMappingStrategy(edition_num))
        
        if config.get_default_value("edition_description"):
            edition_desc = config.get_default_value("edition_description")
            registry.register_strategy("Edition Description", DefaultMappingStrategy(edition_desc))
            registry.register_strategy("Edition Type", DefaultMappingStrategy(edition_desc))
            registry.register_strategy("Edition Info", DefaultMappingStrategy(edition_desc))
            registry.register_strategy("Edition Details", DefaultMappingStrategy(edition_desc))
        
        # Update order type eligibility from config
        if config.get_default_value("order_type_eligibility"):
            order_type = config.get_default_value("order_type_eligibility")
            registry.register_strategy("Order Type Eligibility", DefaultMappingStrategy(order_type))
            registry.register_strategy("Order Type", DefaultMappingStrategy(order_type))
            registry.register_strategy("Order Eligibility", DefaultMappingStrategy(order_type))
            registry.register_strategy("Ordering Type", DefaultMappingStrategy(order_type))
            registry.register_strategy("Order Method", DefaultMappingStrategy(order_type))
        
        # Update stamped text fields from field overrides
        if config.get_field_override("stamped_text_left"):
            left_text = config.get_field_override("stamped_text_left")
            registry.register_strategy("Stamped Text LEFT", DefaultMappingStrategy(left_text))
            registry.register_strategy("Stamped Text Left", DefaultMappingStrategy(left_text))
        
        if config.get_field_override("stamped_text_center"):
            center_text = config.get_field_override("stamped_text_center")
            registry.register_strategy("Stamped Text CENTER", DefaultMappingStrategy(center_text))
            registry.register_strategy("Stamped Text Center", DefaultMappingStrategy(center_text))
        
        if config.get_field_override("stamped_text_right"):
            right_text = config.get_field_override("stamped_text_right")
            registry.register_strategy("Stamped Text RIGHT", DefaultMappingStrategy(right_text))
            registry.register_strategy("Stamped Text Right", DefaultMappingStrategy(right_text))
        
        # Update metadata contact dictionary from field overrides
        if config.get_field_override("metadata_contact_dictionary"):
            metadata_contact = config.get_field_override("metadata_contact_dictionary")
            registry.register_strategy("Metadata Contact Dictionary", DefaultMappingStrategy(metadata_contact))
        
        # Add default values for common fields that are often empty
        registry.register_strategy("ISBN or SKU", DirectMappingStrategy("isbn13"))
        registry.register_strategy("Pages", DirectMappingStrategy("page_count", "0"))
        registry.register_strategy("Pub Date", DirectMappingStrategy("publication_date"))
        registry.register_strategy("Street Date", DirectMappingStrategy("street_date"))
        # Removed - will be handled by enhanced strategy later
        # Removed - will be handled by enhanced strategy later
        # BISAC Category will be handled by enhanced strategy below
        registry.register_strategy("Language Code", DefaultMappingStrategy("eng"))
        
        # Add default values for physical properties
        registry.register_strategy("Custom Trim Width (inches)", DefaultMappingStrategy(""))
        registry.register_strategy("Custom Trim Height (inches)", DefaultMappingStrategy(""))
        registry.register_strategy("Weight(Lbs)", DefaultMappingStrategy(""))
        
        # Add default values for LSI special fields
        registry.register_strategy("LSI Special Category  (please consult LSI before using", DefaultMappingStrategy(""))
        registry.register_strategy("LSI FlexField1 (please consult LSI before using)", DefaultMappingStrategy(""))
        registry.register_strategy("LSI FlexField2 (please consult LSI before using)", DefaultMappingStrategy(""))
        registry.register_strategy("LSI FlexField3 (please consult LSI before using)", DefaultMappingStrategy(""))
        registry.register_strategy("LSI FlexField4 (please consult LSI before using)", DefaultMappingStrategy(""))
        registry.register_strategy("LSI FlexField5 (please consult LSI before using)", DefaultMappingStrategy(""))
        
        # Add default values for reserved fields
        registry.register_strategy("Reserved 1", DefaultMappingStrategy(""))
        registry.register_strategy("Reserved 2", DefaultMappingStrategy(""))
        registry.register_strategy("Reserved 3", DefaultMappingStrategy(""))
        registry.register_strategy("Reserved 4", DefaultMappingStrategy(""))
        registry.register_strategy("Reserved5", DefaultMappingStrategy(""))
        registry.register_strategy("Reserved6", DefaultMappingStrategy(""))
        registry.register_strategy("Reserved7", DefaultMappingStrategy(""))
        registry.register_strategy("Reserved8", DefaultMappingStrategy(""))
        registry.register_strategy("Reserved9", DefaultMappingStrategy(""))
        registry.register_strategy("Reserved10", DefaultMappingStrategy(""))
        registry.register_strategy("Reserved11", DefaultMappingStrategy(""))
        registry.register_strategy("Reserved12", DefaultMappingStrategy(""))
        registry.register_strategy("Reserved (Special Instructions)", DefaultMappingStrategy(""))
        
        # Add default values for marketing and reference fields
        # Removed - will be handled by enhanced strategy later
        registry.register_strategy("Publisher Reference ID", DefaultMappingStrategy(""))
        
        # Note: Territorial pricing fields are handled by specialized pricing strategies
        # registered later in create_enhanced_field_mapping_registry()
        # We only register discount fields here from territorial configs
        for territory_code in config._territorial_configs:
            territory_config = config._territorial_configs[territory_code]
            
            # Add wholesale discount fields only (pricing fields handled by pricing strategies)
            discount_field = f"{territory_code} Wholesale Discount % (Mode 2)"
            discount_value = territory_config.wholesale_discount_percent
            registry.register_strategy(discount_field, DefaultMappingStrategy(discount_value))
        
        # Add blank Ingram pricing fields (as per requirements)
        registry.register_strategy("US-Ingram-Only* Suggested List Price (mode 2)", BlankIngramPricingStrategy())
        registry.register_strategy("US-Ingram-Only* Wholesale Discount % (Mode 2)", BlankIngramPricingStrategy())
        registry.register_strategy("US - Ingram - GAP * Suggested List Price (mode 2)", BlankIngramPricingStrategy())
        registry.register_strategy("US - Ingram - GAP * Wholesale Discount % (Mode 2)", BlankIngramPricingStrategy())
        registry.register_strategy("SIBI - EDUC - US * Suggested List Price (mode 2)", BlankIngramPricingStrategy())
        registry.register_strategy("SIBI - EDUC - US * Wholesale Discount % (Mode 2)", BlankIngramPricingStrategy())
    
    # If we have an LLM field completer, register LLM completion strategies
    if llm_field_completer:
        from .llm_field_completer import LLMFieldCompleter
        from .field_mapping import LLMCompletionStrategy
        
        # Register LLM completion strategies for fields that benefit from AI assistance
        # BISAC Categories 2 and 3 will be handled by enhanced strategy below
        
        registry.register_strategy("Contributor One BIO", 
                                 LLMCompletionStrategy(llm_field_completer, "contributor_one_bio", "contributor_bio"))
        
        registry.register_strategy("Contributor One Affiliations", 
                                 LLMCompletionStrategy(llm_field_completer, "contributor_one_affiliations", "contributor_affiliations"))
        
        registry.register_strategy("Contributor One Professional Position", 
                                 LLMCompletionStrategy(llm_field_completer, "contributor_one_professional_position", "contributor_position"))
        
        registry.register_strategy("Contributor One Location", 
                                 LLMCompletionStrategy(llm_field_completer, "contributor_one_location", "contributor_location"))
        
        registry.register_strategy("Contributor One Prior Work", 
                                 LLMCompletionStrategy(llm_field_completer, "contributor_one_prior_work", "contributor_prior_work"))
        
        # Use enhanced strategies for thema subjects (extract from JSON)
        registry.register_strategy("Thema Subject 1", ThemaSubjectStrategy(1))
        registry.register_strategy("Thema Subject 2", ThemaSubjectStrategy(2))
        registry.register_strategy("Thema Subject 3", ThemaSubjectStrategy(3))
        
        # Use enhanced strategies for age range (extract from JSON)
        registry.register_strategy("Min Age", AgeRangeStrategy("min"))
        registry.register_strategy("Max Age", AgeRangeStrategy("max"))
        
        # Use series-aware description strategy
        registry.register_strategy("Short Description", SeriesAwareDescriptionStrategy())
        
        # Keep LLM completion for series info as fallback
        registry.register_strategy("Series Name", 
                                 LLMCompletionStrategy(llm_field_completer, "series_name", "series_info"))
        
        registry.register_strategy("# in Series", 
                                 LLMCompletionStrategy(llm_field_completer, "series_number", "series_info"))
    
    # Add file path strategies that honor tranche definitions
    registry.register_strategy("Interior Path / Filename", TrancheFilePathStrategy("interior"))
    registry.register_strategy("Cover Path / Filename", TrancheFilePathStrategy("cover"))
    
    # Apply tranche overrides to all strategies if tranche name is provided
    if tranche_name:
        try:
            from .tranche_config_loader import TrancheConfigLoader
            tranche_loader = TrancheConfigLoader()
            tranche_config = tranche_loader.get_tranche_override_config(tranche_name)
            if tranche_config:
                registry = wrap_registry_with_tranche_overrides(registry, tranche_config)
                logger.info(f"Applied tranche overrides for tranche: {tranche_name}")
        except Exception as e:
            logger.error(f"Failed to apply tranche overrides for {tranche_name}: {e}")
    
    return registry

def create_enhanced_field_mapping_registry(llm_field_completer=None) -> FieldMappingRegistry:
    """
    Create an enhanced field mapping registry with specialized strategies.
    
    Returns:
        FieldMappingRegistry with enhanced mapping strategies
    """
    registry = FieldMappingRegistry()
    
    # --- Core Identifiers ---
    registry.register_strategy("ISBN-13", DirectMappingStrategy("isbn13"))
    registry.register_strategy("ISBN-10", DirectMappingStrategy("isbn10"))
    registry.register_strategy("Publisher", DirectMappingStrategy("publisher"))
    registry.register_strategy("Imprint", DirectMappingStrategy("imprint"))
    
    # --- Basic Publication Information ---
    registry.register_strategy("Title", DirectMappingStrategy("title"))
    registry.register_strategy("Subtitle", DirectMappingStrategy("subtitle"))
    registry.register_strategy("Language", DirectMappingStrategy("language"))
    registry.register_strategy("Publication Date", DirectMappingStrategy("publication_date"))
    registry.register_strategy("On Sale Date", DirectMappingStrategy("street_date"))
    registry.register_strategy("Format", DirectMappingStrategy("format"))
    registry.register_strategy("Audience", DirectMappingStrategy("audience"))
    
    # --- Physical Properties ---
    registry.register_strategy("Trim Size", DirectMappingStrategy("trim_size"))
    registry.register_strategy("Page Count", DirectMappingStrategy("page_count"))
    registry.register_strategy("Spine Width", DirectMappingStrategy("spine_width_in"))
    registry.register_strategy("Cover Type", DirectMappingStrategy("cover_type"))
    registry.register_strategy("Interior Color", DirectMappingStrategy("interior_color"))
    registry.register_strategy("Interior Paper", DirectMappingStrategy("interior_paper"))
    registry.register_strategy("Binding", DirectMappingStrategy("binding"))
    registry.register_strategy("Weight (lbs)", DirectMappingStrategy("weight_lbs"))
    
    # --- Pricing ---
    registry.register_strategy("US Suggested List Price", USPricingStrategy())
    registry.register_strategy("US Wholesale Discount", DiscountStrategy())
    registry.register_strategy("UK Suggested List Price", TerritorialPricingStrategy())
    registry.register_strategy("UK Wholesale Discount %", DirectMappingStrategy("uk_wholesale_discount_percent"))
    
    # --- Content Descriptions ---
    registry.register_strategy("Short Description", ShortDescriptionMappingStrategy("summary_short", max_bytes=350))
    registry.register_strategy("Keywords", ComputedMappingStrategy(_format_keywords_computed))
    registry.register_strategy("Table of Contents", ComputedMappingStrategy(_format_toc_computed))
    registry.register_strategy("Review Quote(s)", DefaultMappingStrategy(""))  # Leave review quotes blank
    registry.register_strategy("Annotation", DirectMappingStrategy("annotation_summary"))
    
    # --- Classification Codes ---
    # Enhanced BISAC category strategies with LLM generation and tranche overrides
    registry.register_strategy("BISAC Category", EnhancedBISACCategoryStrategy(1, llm_field_completer))
    registry.register_strategy("BISAC Category 1", EnhancedBISACCategoryStrategy(1, llm_field_completer))
    registry.register_strategy("BISAC Category 2", EnhancedBISACCategoryStrategy(2, llm_field_completer))
    registry.register_strategy("BISAC Category 3", EnhancedBISACCategoryStrategy(3, llm_field_completer))
    registry.register_strategy("BISAC Text", DirectMappingStrategy("bisac_text"))
    registry.register_strategy("BIC Code", DirectMappingStrategy("bic_codes"))
    registry.register_strategy("Thema Subject 1", ThemaSubjectMappingStrategy("thema_subject_1"))
    registry.register_strategy("Thema Subject 2", ThemaSubjectMappingStrategy("thema_subject_2"))
    registry.register_strategy("Thema Subject 3", ThemaSubjectMappingStrategy("thema_subject_3"))
    registry.register_strategy("Regional Subject", DirectMappingStrategy("regional_subjects"))
    
    # --- Age/Grade Information ---
    registry.register_strategy("Min Age", DirectMappingStrategy("min_age"))
    registry.register_strategy("Max Age", DirectMappingStrategy("max_age"))
    registry.register_strategy("Min Grade", DirectMappingStrategy("min_grade"))
    registry.register_strategy("Max Grade", DirectMappingStrategy("max_grade"))
    
    # --- Contributors ---
    registry.register_strategy("Contributor One", DirectMappingStrategy("contributor_one"))
    registry.register_strategy("Contributor One Role", ContributorRoleMappingStrategy("contributor_one_role", "A"))
    registry.register_strategy("Contributor Two", DirectMappingStrategy("contributor_two"))
    registry.register_strategy("Contributor Two Role", ContributorRoleMappingStrategy("contributor_two_role", ""))
    registry.register_strategy("Contributor Three", DirectMappingStrategy("contributor_three"))
    registry.register_strategy("Contributor Three Role", ContributorRoleMappingStrategy("contributor_three_role", ""))
    
    # --- Series information ---
    registry.register_strategy("Series Name", DirectMappingStrategy("series_name"))
    registry.register_strategy("# in Series", DirectMappingStrategy("series_number"))
    registry.register_strategy("Volume Number", DirectMappingStrategy("volume_number"))
    
    # --- Contributors ---
    registry.register_strategy("Contributor Bio", DirectMappingStrategy("contributor_one_bio"))
    registry.register_strategy("Contributor Affiliations", DirectMappingStrategy("contributor_one_affiliations"))
    registry.register_strategy("Contributor Position", DirectMappingStrategy("contributor_one_professional_position"))
    registry.register_strategy("Contributor Location", DirectMappingStrategy("contributor_one_location"))
    registry.register_strategy("Contributor Prior Work", DirectMappingStrategy("contributor_one_prior_work"))
    
    # --- Illustrations ---
    registry.register_strategy("# Illustrations", DirectMappingStrategy("illustration_count"))
    registry.register_strategy("Illustration Notes", DirectMappingStrategy("illustration_notes"))
    
    # --- Distribution Settings ---
    registry.register_strategy("Availability", DirectMappingStrategy("availability"))
    registry.register_strategy("Discount Code", DirectMappingStrategy("discount_code"))
    registry.register_strategy("Tax Code", DirectMappingStrategy("tax_code"))
    registry.register_strategy("Returns Allowed", DirectMappingStrategy("returns_allowed"))
    
    # --- Shipping Information ---
    registry.register_strategy("Carton Quantity", DirectMappingStrategy("carton_quantity"))
    registry.register_strategy("Carton Weight", DirectMappingStrategy("carton_weight"))
    registry.register_strategy("Carton Length", DirectMappingStrategy("carton_length"))
    registry.register_strategy("Carton Width", DirectMappingStrategy("carton_width"))
    registry.register_strategy("Carton Height", DirectMappingStrategy("carton_height"))
    
    # --- LSI Account Information ---
    # Lightning Source Account is handled by DefaultMappingStrategy in config-based section above
    registry.register_strategy("Parent ISBN", DirectMappingStrategy("parent_isbn"))
    registry.register_strategy("Cover Submission Method", DirectMappingStrategy("cover_submission_method"))
    registry.register_strategy("Text Block Submission Method", DirectMappingStrategy("text_block_submission_method"))
    
    # --- Edition Information ---
    registry.register_strategy("Edition Number", DirectMappingStrategy("edition_number"))
    registry.register_strategy("Edition Description", DirectMappingStrategy("edition_description"))
    registry.register_strategy("Edition Statement", DirectMappingStrategy("edition_statement"))
    
    # --- Territorial Rights ---
    registry.register_strategy("Territorial Rights", DirectMappingStrategy("territorial_rights"))
    
    # --- File Paths ---
    registry.register_strategy("Jacket Path/Filename", DirectMappingStrategy("jacket_path_filename"))
    registry.register_strategy("Interior Path/Filename", DirectMappingStrategy("interior_path_filename"))
    registry.register_strategy("Cover Path/Filename", DirectMappingStrategy("cover_path_filename"))
    
    # --- Special LSI Fields ---
    registry.register_strategy("LSI Special Category", DirectMappingStrategy("lsi_special_category"))
    registry.register_strategy("Stamped Text Left", DirectMappingStrategy("stamped_text_left"))
    registry.register_strategy("Stamped Text Center", DirectMappingStrategy("stamped_text_center"))
    registry.register_strategy("Stamped Text Right", DirectMappingStrategy("stamped_text_right"))
    registry.register_strategy("Order Type Eligibility", DirectMappingStrategy("order_type_eligibility"))
    
    # --- LSI Flex Fields ---
    registry.register_strategy("LSI FlexField1", DirectMappingStrategy("lsi_flexfield1"))
    registry.register_strategy("LSI FlexField2", DirectMappingStrategy("lsi_flexfield2"))
    registry.register_strategy("LSI FlexField3", DirectMappingStrategy("lsi_flexfield3"))
    registry.register_strategy("LSI FlexField4", DirectMappingStrategy("lsi_flexfield4"))
    registry.register_strategy("LSI FlexField5", DirectMappingStrategy("lsi_flexfield5"))
    
    # --- Territorial Pricing Strategies ---
    registry.register_strategy("EU Suggested List Price (mode 2)", TerritorialPricingStrategy())
    registry.register_strategy("CA Suggested List Price (mode 2)", TerritorialPricingStrategy())
    registry.register_strategy("AU Suggested List Price (mode 2)", TerritorialPricingStrategy())
    
    # --- Market-specific pricing strategies (should equal US list price) ---
    registry.register_strategy("GC Suggested List Price (mode 2)", MarketPricingStrategy())
    registry.register_strategy("USBR1 Suggested List Price (mode 2)", MarketPricingStrategy())
    registry.register_strategy("USDE1 Suggested List Price (mode 2)", MarketPricingStrategy())
    registry.register_strategy("USRU1 Suggested List Price (mode 2)", MarketPricingStrategy())
    registry.register_strategy("USPL1 Suggested List Price (mode 2)", MarketPricingStrategy())
    registry.register_strategy("USKR1 Suggested List Price (mode 2)", MarketPricingStrategy())
    registry.register_strategy("USCN1 Suggested List Price (mode 2)", MarketPricingStrategy())
    registry.register_strategy("USIN1 Suggested List Price (mode 2)", MarketPricingStrategy())
    registry.register_strategy("USJP2 Suggested List Price(mode 2)", MarketPricingStrategy())
    registry.register_strategy("UAEUSD Suggested List Price (mode 2)", MarketPricingStrategy())
    registry.register_strategy("US-Ingram-Only* Suggested List Price (mode 2)", MarketPricingStrategy())
    registry.register_strategy("US - Ingram - GAP * Suggested List Price (mode 2)", MarketPricingStrategy())
    registry.register_strategy("SIBI - EDUC - US * Suggested List Price (mode 2)", MarketPricingStrategy())
    
    # --- Discount strategies ---
    registry.register_strategy("UK Wholesale Discount (%)", DiscountStrategy())
    registry.register_strategy("EU Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("AU Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("CA Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("GC Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("USBR1 Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("USDE1 Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("USRU1 Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("USPL1 Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("USKR1 Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("USCN1 Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("USIN1 Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("USJP2 Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("UAEUSD Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("US-Ingram-Only* Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("US - Ingram - GAP * Wholesale Discount % (Mode 2)", DiscountStrategy())
    registry.register_strategy("SIBI - EDUC - US * Wholesale Discount % (Mode 2)", DiscountStrategy())
    
    # --- Physical Specifications Strategies ---
    registry.register_strategy("Weight", 
                             PhysicalSpecsStrategy("weight", paper_type="standard"))
    
    registry.register_strategy("Spine Width", 
                             PhysicalSpecsStrategy("spine_width", paper_type="standard"))
    
    registry.register_strategy("Thickness", 
                             PhysicalSpecsStrategy("thickness", paper_type="standard"))
    
    # --- Date Computation Strategies ---
    registry.register_strategy("Publication Date", 
                             PublicationDateStrategy(offset_days=0, fallback_to_current=False))
    
    registry.register_strategy("Street Date", 
                             StreetDateStrategy(offset_days=7, fallback_to_current=False))
    
    registry.register_strategy("Copyright Date", 
                             CopyrightDateStrategy(fallback_to_current=False))
    
    registry.register_strategy("On Sale Date", 
                             StreetDateStrategy(offset_days=0, fallback_to_current=False))
    
    registry.register_strategy("Release Date", 
                             DateComputationStrategy("release_date", offset_days=0))
    
    # --- File Path Strategies ---
    registry.register_strategy("Cover Path / Filename", 
                             LSIFilePathStrategy("cover", base_path=""))
    
    registry.register_strategy("Interior Path / Filename", 
                             LSIFilePathStrategy("interior", base_path=""))
    
    registry.register_strategy("Jacket Path / Filename", 
                             LSIFilePathStrategy("jacket", base_path=""))
    
    registry.register_strategy("Cover File Path", 
                             FilePathStrategy("cover", base_path="covers"))
    
    registry.register_strategy("Interior File Path", 
                             FilePathStrategy("interior", base_path="interiors"))
    
    registry.register_strategy("Jacket File Path", 
                             FilePathStrategy("jacket", base_path="jackets"))
    
    registry.register_strategy("EPUB File Path", 
                             OrganizedFilePathStrategy("epub", organize_by_date=True))
    
    registry.register_strategy("PDF File Path", 
                             DetailedFilePathStrategy("pdf", base_path="pdfs", include_author=True))
    
    
    
    # --- FINAL ENHANCED STRATEGIES (MUST BE LAST TO AVOID OVERRIDE) ---
    
    # Enhanced File Path Strategies (Fix for blank paths)
    registry.register_strategy("Marketing Image", 
                             EnhancedFilePathStrategy("marketing_image"))
    
    registry.register_strategy("Interior Path / Filename", 
                             EnhancedFilePathStrategy("interior"))
    
    registry.register_strategy("Cover Path / Filename", 
                             EnhancedFilePathStrategy("cover"))
    
    # Enhanced Content Strategies
    registry.register_strategy("Annotation / Summary", 
                             EnhancedAnnotationStrategy())
    
    registry.register_strategy("Contributor One BIO", 
                             EnhancedContributorBioStrategy())
    
    registry.register_strategy("Table of Contents", 
                             EnhancedTOCStrategy())
    
    # Series Information (tranche-aware strategy)
    registry.register_strategy("Series Name", 
                             TrancheAwareSeriesStrategy())
    
    # Blank Mode 2 Pricing Fields (these should remain blank)
    mode2_fields = [
        "US-Ingram-Only* Suggested List Price (mode 2)",
        "US-Ingram-Only* Wholesale Discount % (Mode 2)",
        "US - Ingram - GAP * Suggested List Price (mode 2)",
        "US - Ingram - GAP * Wholesale Discount % (Mode 2)",
        "SIBI - EDUC - US * Suggested List Price (mode 2)",
        "SIBI - EDUC - US * Wholesale Discount % (Mode 2)"
    ]
    
    for field in mode2_fields:
        registry.register_strategy(field, BlankFieldStrategy())


    # --- TRANCHE FIELD OVERRIDES (HIGHEST PRIORITY) ---
    # These fields can be directly overridden in tranche configuration
    tranche_override_fields = [
        ("Contributor One BIO", "A respected expert in the field with extensive knowledge and experience."),
        ("Contributor One Affiliations", ""),
        ("Contributor One Professional Position", ""),
        ("Contributor One Location", ""),
        ("Contributor One Location Type Code", ""),
        ("Contributor One Prior Work", ""),
        ("Series Name", "Transcriptive Meditation"),
        ("Table of Contents", ""),
        ("Marketing Image", ""),
        ("Interior Path / Filename", ""),
        ("Cover Path / Filename", "")
    ]
    
    # Register tranche override strategies (these will override existing strategies)
    for field_name, fallback_value in tranche_override_fields:
        registry.register_strategy(field_name, TrancheOverrideStrategy(field_name, fallback_value))

    return registry