# src/codexes/modules/distribution/field_mapping.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Callable
import logging
import os

from ..metadata.metadata_models import CodexMetadata
from .validation_utils import is_valid_rendition_booktype, get_closest_valid_rendition_booktype

logger = logging.getLogger(__name__)


@dataclass
class MappingContext:
    """
    Context information for field mapping operations.
    Provides additional data that mapping strategies might need.
    """
    field_name: str
    lsi_headers: List[str]
    current_row_data: Dict[str, str]
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[CodexMetadata] = None


class MappingStrategy(ABC):
    """
    Abstract base class for field mapping strategies.
    Each strategy defines how to map a specific field from CodexMetadata to LSI format.
    """
    
    @abstractmethod
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Maps a field from CodexMetadata to its LSI representation.
        
        Args:
            metadata: The source CodexMetadata object
            context: Additional context for the mapping operation
            
        Returns:
            String value for the LSI field
        """
        pass
    
    def validate_input(self, metadata: CodexMetadata, context: MappingContext) -> bool:
        """
        Validates that the input is suitable for this mapping strategy.
        Override in subclasses if validation is needed.
        
        Args:
            metadata: The source CodexMetadata object
            context: Additional context for the mapping operation
            
        Returns:
            True if input is valid, False otherwise
        """
        return True


class DirectMappingStrategy(MappingStrategy):
    """
    Strategy for direct field mappings from metadata to LSI fields.
    Maps a single metadata field directly to an LSI field with optional default value.
    """
    
    def __init__(self, metadata_field: str, default_value: str = ""):
        """
        Initialize direct mapping strategy.
        
        Args:
            metadata_field: Name of the field in CodexMetadata to map from
            default_value: Default value to use if the metadata field is empty
        """
        self.metadata_field = metadata_field
        self.default_value = default_value
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Map field directly from metadata with fallback to default."""
        try:
            value = getattr(metadata, self.metadata_field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                return self.default_value
            return str(value)
        except Exception as e:
            logger.warning(f"Error mapping field {self.metadata_field}: {e}")
            return self.default_value


class ComputedMappingStrategy(MappingStrategy):
    """
    Strategy for computed field mappings that require calculation or transformation.
    Uses a provided function to compute the field value from metadata.
    """
    
    def __init__(self, computation_func: Callable[[CodexMetadata, MappingContext], str]):
        """
        Initialize computed mapping strategy.
        
        Args:
            computation_func: Function that takes metadata and context, returns string value
        """
        self.computation_func = computation_func
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Compute field value using the provided function."""
        try:
            return self.computation_func(metadata, context)
        except Exception as e:
            logger.error(f"Error computing field {context.field_name}: {e}")
            return ""


class DefaultMappingStrategy(MappingStrategy):
    """
    Strategy that always returns a default value.
    Useful for fields that should have consistent default values.
    """
    
    def __init__(self, default_value: str):
        """
        Initialize default mapping strategy.
        
        Args:
            default_value: The default value to always return
        """
        self.default_value = default_value
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Return the configured default value."""
        return self.default_value


class ValidatedRenditionBooktypeStrategy(MappingStrategy):
    """
    Strategy for validating and mapping rendition booktype.
    Ensures the value is from the approved list in lsi_valid_rendition_booktypes.txt.
    """
    
    def __init__(self, metadata_field: str = "rendition_booktype", default_value: str = "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE"):
        """
        Initialize validated rendition booktype strategy.
        
        Args:
            metadata_field: Name of the field in CodexMetadata to map from
            default_value: Default value to use if the metadata field is empty or invalid
        """
        self.metadata_field = metadata_field
        
        # Ensure default value is valid
        if not is_valid_rendition_booktype(default_value):
            # Special case for "Perfect Bound" - map to a valid format
            if default_value == "Perfect Bound":
                self.default_value = "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE"
            else:
                self.default_value = get_closest_valid_rendition_booktype(default_value)
        else:
            self.default_value = default_value
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Map field from metadata with validation against approved list."""
        try:
            # Get value from metadata
            value = getattr(metadata, self.metadata_field, None)
            
            # If empty, use default
            if value is None or (isinstance(value, str) and not value.strip()):
                logger.debug(f"Using default rendition booktype: {self.default_value}")
                return self.default_value
            
            # Special case for "Perfect Bound" - map to a valid format
            if value == "Perfect Bound":
                logger.info(f"Converting 'Perfect Bound' to standard format: {self.default_value}")
                return self.default_value
            
            # Validate the value
            if not is_valid_rendition_booktype(value):
                corrected = get_closest_valid_rendition_booktype(value)
                logger.warning(f"Invalid rendition booktype '{value}'. Using '{corrected}' instead.")
                return corrected
            
            return value
        except Exception as e:
            logger.error(f"Error mapping rendition booktype: {e}")
            return self.default_value


class ConditionalMappingStrategy(MappingStrategy):
    """
    Strategy for conditional field mappings based on other field values.
    Evaluates conditions and returns different values based on the results.
    """
    
    def __init__(self, 
                 condition_func: Callable[[CodexMetadata, MappingContext], bool],
                 true_strategy: MappingStrategy,
                 false_strategy: MappingStrategy):
        """
        Initialize conditional mapping strategy.
        
        Args:
            condition_func: Function that evaluates the condition
            true_strategy: Strategy to use when condition is True
            false_strategy: Strategy to use when condition is False
        """
        self.condition_func = condition_func
        self.true_strategy = true_strategy
        self.false_strategy = false_strategy
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Evaluate condition and use appropriate strategy."""
        try:
            if self.condition_func(metadata, context):
                return self.true_strategy.map_field(metadata, context)
            else:
                return self.false_strategy.map_field(metadata, context)
        except Exception as e:
            logger.error(f"Error in conditional mapping for field {context.field_name}: {e}")
            return ""


class LLMCompletionStrategy(MappingStrategy):
    """
    Strategy for LLM-based field completion.
    Uses the LLMFieldCompleter to generate field values intelligently.
    
    This strategy first checks if the field has already been completed in the
    metadata.llm_completions dictionary, then checks if the field has a direct value,
    and finally attempts to complete the field using the LLMFieldCompleter.
    """
    
    def __init__(self, field_completer, metadata_field: str, prompt_key: str = None, fallback_value: str = ""):
        """
        Initialize LLM completion strategy.
        
        Args:
            field_completer: Instance of LLMFieldCompleter for intelligent completion
            metadata_field: Name of the metadata field to complete
            prompt_key: Optional key of the prompt to use for completion (if different from field mapping)
            fallback_value: Value to use if LLM completion fails
        """
        self.field_completer = field_completer
        self.metadata_field = metadata_field
        self.prompt_key = prompt_key
        self.fallback_value = fallback_value
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """Generate field value using LLM field completer with fallback."""
        try:
            # First check if we have a direct field value
            current_value = getattr(metadata, self.metadata_field, "")
            if current_value and isinstance(current_value, str) and current_value.strip():
                logger.debug(f"Using existing value for field {self.metadata_field}: {current_value[:50]}...")
                return current_value
            
            # Next check if we have a completion in llm_completions
            if hasattr(metadata, 'llm_completions') and metadata.llm_completions:
                # Find the appropriate prompt key for this field
                prompt_key = self.prompt_key
                if not prompt_key:
                    # Try to find the prompt key from the field completer's mapping
                    for key, fields in self.field_completer.prompt_field_mapping.items():
                        if isinstance(fields, str) and fields == self.metadata_field:
                            prompt_key = key
                            break
                        elif isinstance(fields, list) and self.metadata_field in fields:
                            prompt_key = key
                            break
                
                # If we found a prompt key and it exists in llm_completions
                if prompt_key and prompt_key in metadata.llm_completions:
                    result = metadata.llm_completions[prompt_key]
                    
                    # Extract the field value from the result
                    if isinstance(result, dict):
                        # Check for direct field match (case-insensitive)
                        for key, value in result.items():
                            if key.lower() == self.metadata_field.lower() or key.lower() in self.metadata_field.lower() or self.metadata_field.lower() in key.lower():
                                logger.info(f"Using existing LLM completion for field {self.metadata_field} from {prompt_key}")
                                return value
                        
                        # Check for field name match (e.g., "bio" in "contributor_one_bio")
                        field_name = self.metadata_field.split('_')[-1]
                        for key, value in result.items():
                            if field_name.lower() in key.lower():
                                logger.info(f"Using existing LLM completion for field {self.metadata_field} based on field name {field_name}")
                                return value
                        
                        # If we have a "value" key, use that
                        if "value" in result:
                            logger.info(f"Using 'value' from existing LLM completion for field {self.metadata_field}")
                            return result["value"]
                        
                        # If no matching key found, use the first non-metadata value
                        for key, value in result.items():
                            if not key.startswith("_"):  # Skip metadata keys
                                logger.info(f"Using first non-metadata value from existing LLM completion for field {self.metadata_field}")
                                return value
                    elif isinstance(result, str):
                        # If result is a string, use it directly
                        logger.info(f"Using existing LLM completion string for field {self.metadata_field}")
                        return result
            
            # If we get here, we need to complete the field
            completed_value = self.field_completer._complete_field(metadata, self.metadata_field)
            if completed_value:
                logger.info(f"LLM completed field {self.metadata_field}: {completed_value[:50]}...")
                return completed_value
            else:
                logger.warning(f"LLM completion failed for field {self.metadata_field}, using fallback")
                return self.fallback_value
        except Exception as e:
            logger.error(f"Error in LLM completion for field {self.metadata_field}: {e}")
            return self.fallback_value


class FieldMappingRegistry:
    """
    Registry for managing field mapping strategies.
    Provides centralized management of how fields are mapped from metadata to LSI format.
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._strategies: Dict[str, MappingStrategy] = {}
        self._field_order: List[str] = []
        self.context_config: Dict[str, Any] = {}
    
    def register_strategy(self, field_name: str, strategy: MappingStrategy) -> None:
        """
        Register a mapping strategy for a specific field.
        
        Args:
            field_name: Name of the LSI field this strategy handles
            strategy: MappingStrategy instance to use for this field
        """
        self._strategies[field_name] = strategy
        if field_name not in self._field_order:
            self._field_order.append(field_name)
        logger.debug(f"Registered strategy for field '{field_name}': {type(strategy).__name__}")
    
    def get_strategy(self, field_name: str) -> Optional[MappingStrategy]:
        """
        Get the mapping strategy for a specific field.
        
        Args:
            field_name: Name of the LSI field
            
        Returns:
            MappingStrategy instance or None if not found
        """
        return self._strategies.get(field_name)
    
    def has_strategy(self, field_name: str) -> bool:
        """
        Check if a strategy is registered for a field.
        
        Args:
            field_name: Name of the LSI field
            
        Returns:
            True if strategy exists, False otherwise
        """
        return field_name in self._strategies
    
    def get_registered_fields(self) -> List[str]:
        """
        Get list of all registered field names in registration order.
        
        Returns:
            List of field names that have registered strategies
        """
        return self._field_order.copy()
    
    def apply_mappings(self, metadata: CodexMetadata, lsi_headers: List[str]) -> Dict[str, str]:
        """
        Apply all registered mapping strategies to generate LSI field values.
        
        Args:
            metadata: Source CodexMetadata object
            lsi_headers: List of LSI header names in order
            
        Returns:
            Dictionary mapping LSI field names to their values
        """
        results = {}
        
        for header in lsi_headers:
            strategy = self.get_strategy(header)
            if strategy:
                try:
                    context = MappingContext(
                        field_name=header,
                        lsi_headers=lsi_headers,
                        current_row_data=results,
                        metadata=metadata,
                        config=self.context_config
                    )
                    
                    if strategy.validate_input(metadata, context):
                        value = strategy.map_field(metadata, context)
                        results[header] = value
                        logger.debug(f"Mapped field '{header}': '{value}'")
                    else:
                        logger.warning(f"Validation failed for field '{header}', using empty value")
                        results[header] = ""
                        
                except Exception as e:
                    logger.error(f"Error mapping field '{header}': {e}")
                    results[header] = ""
            else:
                # No strategy registered, use empty value
                results[header] = ""
                logger.debug(f"No strategy for field '{header}', using empty value")
        
        return results
    
    def apply_mappings_ordered(self, metadata: CodexMetadata, lsi_headers: List[str]) -> List[str]:
        """
        Apply mappings and return values in the order of lsi_headers.
        
        Args:
            metadata: Source CodexMetadata object
            lsi_headers: List of LSI header names in desired order
            
        Returns:
            List of string values in the same order as lsi_headers
        """
        field_values = self.apply_mappings(metadata, lsi_headers)
        return [field_values.get(header, "") for header in lsi_headers]
    
    def clear_registry(self) -> None:
        """Clear all registered strategies."""
        self._strategies.clear()
        self._field_order.clear()
        logger.info("Cleared all registered mapping strategies")
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current registry state.
        
        Returns:
            Dictionary with registry statistics
        """
        strategy_types = {}
        for strategy in self._strategies.values():
            strategy_type = type(strategy).__name__
            strategy_types[strategy_type] = strategy_types.get(strategy_type, 0) + 1
        
        return {
            "total_strategies": len(self._strategies),
            "registered_fields": len(self._field_order),
            "strategy_types": strategy_types
        }


def create_default_lsi_registry() -> FieldMappingRegistry:
    """
    Create a registry with default LSI field mapping strategies.
    This provides a starting point with common field mappings.
    
    Returns:
        FieldMappingRegistry with default strategies registered
    """
    registry = FieldMappingRegistry()
    
    # Basic book information
    registry.register_strategy("ISBN or SKU", DirectMappingStrategy("isbn13"))
    registry.register_strategy("Title", DirectMappingStrategy("title"))
    registry.register_strategy("Publisher", DirectMappingStrategy("publisher", "Nimble Books LLC"))
    registry.register_strategy("Imprint", DirectMappingStrategy("imprint", "Nimble Books LLC"))
    registry.register_strategy("Contributor One", DirectMappingStrategy("author", "AI Lab for Book-Lovers"))
    registry.register_strategy("Contributor One Role", DefaultMappingStrategy("Author"))
    registry.register_strategy("Pages", DirectMappingStrategy("page_count", "0"))
    registry.register_strategy("Pub Date", DirectMappingStrategy("publication_date"))
    
    # Content descriptions
    registry.register_strategy("Annotation / Summary", 
                             DirectMappingStrategy("summary_long"))
    registry.register_strategy("Short Description", 
                             DirectMappingStrategy("summary_short"))
    registry.register_strategy("Keywords", 
                             ComputedMappingStrategy(_format_keywords_computed))
    registry.register_strategy("Table of Contents", 
                             DirectMappingStrategy("table_of_contents"))
    registry.register_strategy("Review Quote(s)", 
                             DirectMappingStrategy("review_quotes"))
    
    # Classification
    registry.register_strategy("BISAC Category", DirectMappingStrategy("bisac_codes"))
    registry.register_strategy("Language Code", DirectMappingStrategy("language", "eng"))
    
    # Pricing
    registry.register_strategy("US Suggested List Price", 
                             ComputedMappingStrategy(_format_price_computed))
    registry.register_strategy("US Wholesale Discount", 
                             DirectMappingStrategy("us_wholesale_discount", "40%"))
    registry.register_strategy("Returnable", 
                             DirectMappingStrategy("returns_allowed", "Yes"))
    
    # Physical specifications
    registry.register_strategy("Rendition /Booktype", ValidatedRenditionBooktypeStrategy("rendition_booktype", "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE"))
    registry.register_strategy("Custom Trim Width (inches)", 
                             DirectMappingStrategy("trim_width_in", "6"))
    registry.register_strategy("Custom Trim Height (inches)", 
                             DirectMappingStrategy("trim_height_in", "9"))
    
    # Contributors
    registry.register_strategy("Contributor Two", DirectMappingStrategy("contributor_two"))
    registry.register_strategy("Contributor Two Role", DirectMappingStrategy("contributor_two_role"))
    registry.register_strategy("Contributor Three", DirectMappingStrategy("contributor_three"))
    registry.register_strategy("Contributor Three Role", DirectMappingStrategy("contributor_three_role"))
    
    # Series information
    registry.register_strategy("Series Name", DirectMappingStrategy("series_name"))
    registry.register_strategy("# in Series", DirectMappingStrategy("series_number"))
    
    # Age/Grade information
    registry.register_strategy("Min Age", DirectMappingStrategy("min_age"))
    registry.register_strategy("Max Age", DirectMappingStrategy("max_age"))
    registry.register_strategy("Min Grade", DirectMappingStrategy("min_grade"))
    registry.register_strategy("Max Grade", DirectMappingStrategy("max_grade"))
    registry.register_strategy("Audience", DirectMappingStrategy("audience"))
    
    # Illustrations
    registry.register_strategy("# Illustrations", DirectMappingStrategy("illustration_count", "0"))
    registry.register_strategy("Illustration Notes", DirectMappingStrategy("illustration_notes"))
    
    # Thema subjects
    registry.register_strategy("Thema Subject 1", DirectMappingStrategy("thema_subject_1"))
    registry.register_strategy("Thema Subject 2", DirectMappingStrategy("thema_subject_2"))
    registry.register_strategy("Thema Subject 3", DirectMappingStrategy("thema_subject_3"))
    registry.register_strategy("Regional Subjects", DirectMappingStrategy("regional_subjects"))
    
    logger.info(f"Created default LSI registry with {len(registry.get_registered_fields())} field strategies")
    return registry


def _format_keywords_computed(metadata: CodexMetadata, context: MappingContext) -> str:
    """Computed strategy function for formatting keywords."""
    keywords = metadata.keywords or ""
    if not keywords:
        return ""
    
    # Remove "#Bibliographic Key Phrases" if present
    formatted = keywords.replace('#Bibliographic Key Phrases', '').strip()
    
    # Add space after semicolons if missing
    formatted = formatted.replace(';', '; ').replace(';  ', '; ')
    
    return formatted


def _format_price_computed(metadata: CodexMetadata, context: MappingContext) -> str:
    """Computed strategy function for formatting price."""
    price = metadata.list_price_usd
    if not price:
        return "$19.99"  # Default price
    
    if isinstance(price, (int, float)):
        return f"${price:.2f}"
    
    # If already a string, ensure it starts with $
    price_str = str(price)
    if not price_str.startswith('$'):
        try:
            price_float = float(price_str)
            return f"${price_float:.2f}"
        except ValueError:
            return price_str
    
    return price_str