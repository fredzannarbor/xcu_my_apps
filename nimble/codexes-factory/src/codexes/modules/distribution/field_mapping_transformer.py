#!/usr/bin/env python3

"""
Field Mapping Transformer

This module provides comprehensive field mapping and transformation capabilities
for converting metadata between different formats and fixing common mapping issues.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, InvalidOperation
from datetime import datetime

logger = logging.getLogger(__name__)


class TransformationType(Enum):
    """Types of field transformations."""
    DIRECT_COPY = "direct_copy"
    FORMAT_CONVERSION = "format_conversion"
    VALUE_MAPPING = "value_mapping"
    COMPUTED_FIELD = "computed_field"
    CONDITIONAL_MAPPING = "conditional_mapping"
    AGGREGATION = "aggregation"
    VALIDATION_TRANSFORM = "validation_transform"


@dataclass
class FieldMapping:
    """Defines how a field should be mapped and transformed."""
    source_field: str
    target_field: str
    transformation_type: TransformationType
    transformation_function: Optional[Callable] = None
    value_map: Optional[Dict[str, str]] = None
    default_value: Optional[Any] = None
    validation_rules: Optional[Dict[str, Any]] = None
    dependencies: Optional[List[str]] = None
    conditions: Optional[Dict[str, Any]] = None


@dataclass
class TransformationResult:
    """Result of a field transformation."""
    source_field: str
    target_field: str
    original_value: Any
    transformed_value: Any
    success: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class FieldMappingTransformer:
    """Handles field mapping and transformation operations."""
    
    def __init__(self):
        """Initialize the transformer with built-in mappings."""
        self.field_mappings = self._initialize_default_mappings()
        self.transformation_functions = self._initialize_transformation_functions()
        self.validation_cache = {}
    
    def transform_metadata(self, source_metadata: Dict[str, Any], 
                          mapping_profile: str = "lsi_standard") -> Dict[str, Any]:
        """Transform metadata using specified mapping profile."""
        target_metadata = {}
        transformation_results = []
        
        # Get mappings for the profile
        profile_mappings = self._get_profile_mappings(mapping_profile)
        
        for mapping in profile_mappings:
            try:
                result = self._transform_field(source_metadata, mapping)
                transformation_results.append(result)
                
                if result.success:
                    target_metadata[result.target_field] = result.transformed_value
                else:
                    logger.warning(f"Failed to transform {result.source_field}: {result.error_message}")
                    
                    # Use default value if available
                    if mapping.default_value is not None:
                        target_metadata[result.target_field] = mapping.default_value
                        logger.info(f"Used default value for {result.target_field}: {mapping.default_value}")
                
            except Exception as e:
                logger.error(f"Error transforming field {mapping.source_field}: {e}")
                if mapping.default_value is not None:
                    target_metadata[mapping.target_field] = mapping.default_value
        
        # Post-process computed fields
        target_metadata = self._process_computed_fields(target_metadata, source_metadata)
        
        # Validate transformed metadata
        validation_issues = self._validate_transformed_metadata(target_metadata)
        if validation_issues:
            logger.warning(f"Validation issues found: {len(validation_issues)}")
            for issue in validation_issues:
                logger.warning(f"  {issue}")
        
        return target_metadata
    
    def _transform_field(self, source_metadata: Dict[str, Any], 
                        mapping: FieldMapping) -> TransformationResult:
        """Transform a single field according to its mapping."""
        result = TransformationResult(
            source_field=mapping.source_field,
            target_field=mapping.target_field,
            original_value=source_metadata.get(mapping.source_field),
            transformed_value=None,
            success=False
        )
        
        # Check if source field exists
        if mapping.source_field not in source_metadata:
            if mapping.default_value is not None:
                result.transformed_value = mapping.default_value
                result.success = True
            else:
                result.error_message = f"Source field '{mapping.source_field}' not found"
            return result
        
        original_value = source_metadata[mapping.source_field]
        
        # Check conditions if specified
        if mapping.conditions and not self._check_conditions(source_metadata, mapping.conditions):
            result.error_message = "Mapping conditions not met"
            return result
        
        try:
            # Apply transformation based on type
            if mapping.transformation_type == TransformationType.DIRECT_COPY:
                result.transformed_value = original_value
                
            elif mapping.transformation_type == TransformationType.FORMAT_CONVERSION:
                result.transformed_value = self._apply_format_conversion(
                    original_value, mapping.transformation_function
                )
                
            elif mapping.transformation_type == TransformationType.VALUE_MAPPING:
                result.transformed_value = self._apply_value_mapping(
                    original_value, mapping.value_map, mapping.default_value
                )
                
            elif mapping.transformation_type == TransformationType.COMPUTED_FIELD:
                result.transformed_value = self._apply_computed_field(
                    source_metadata, mapping.transformation_function
                )
                
            elif mapping.transformation_type == TransformationType.CONDITIONAL_MAPPING:
                result.transformed_value = self._apply_conditional_mapping(
                    source_metadata, mapping
                )
                
            elif mapping.transformation_type == TransformationType.AGGREGATION:
                result.transformed_value = self._apply_aggregation(
                    source_metadata, mapping
                )
                
            elif mapping.transformation_type == TransformationType.VALIDATION_TRANSFORM:
                result.transformed_value = self._apply_validation_transform(
                    original_value, mapping.validation_rules
                )
            
            # Validate result if validation rules are specified
            if mapping.validation_rules:
                validation_result = self._validate_field_value(
                    result.transformed_value, mapping.validation_rules
                )
                if not validation_result['valid']:
                    result.warnings.extend(validation_result['warnings'])
                    if validation_result['errors']:
                        result.error_message = '; '.join(validation_result['errors'])
                        result.success = False
                        return result
            
            result.success = True
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Error transforming {mapping.source_field}: {e}")
        
        return result
    
    def _apply_format_conversion(self, value: Any, conversion_function: Callable) -> Any:
        """Apply format conversion to a value."""
        if conversion_function:
            return conversion_function(value)
        return value
    
    def _apply_value_mapping(self, value: Any, value_map: Dict[str, str], 
                           default_value: Any = None) -> Any:
        """Apply value mapping transformation."""
        if not value_map:
            return value
        
        str_value = str(value).strip()
        
        # Try exact match first
        if str_value in value_map:
            return value_map[str_value]
        
        # Try case-insensitive match
        for key, mapped_value in value_map.items():
            if str_value.lower() == key.lower():
                return mapped_value
        
        # Try partial match
        for key, mapped_value in value_map.items():
            if str_value.lower() in key.lower() or key.lower() in str_value.lower():
                return mapped_value
        
        # Return default or original value
        return default_value if default_value is not None else value
    
    def _apply_computed_field(self, metadata: Dict[str, Any], 
                            computation_function: Callable) -> Any:
        """Apply computed field transformation."""
        if computation_function:
            return computation_function(metadata)
        return None
    
    def _apply_conditional_mapping(self, metadata: Dict[str, Any], 
                                 mapping: FieldMapping) -> Any:
        """Apply conditional mapping based on other field values."""
        conditions = mapping.conditions or {}
        
        for condition_field, condition_value in conditions.items():
            if condition_field in metadata:
                if metadata[condition_field] == condition_value:
                    if mapping.transformation_function:
                        return mapping.transformation_function(metadata)
                    else:
                        return metadata.get(mapping.source_field, mapping.default_value)
        
        return mapping.default_value
    
    def _apply_aggregation(self, metadata: Dict[str, Any], mapping: FieldMapping) -> Any:
        """Apply aggregation transformation."""
        if not mapping.dependencies:
            return mapping.default_value
        
        values = []
        for field_name in mapping.dependencies:
            if field_name in metadata and metadata[field_name]:
                values.append(str(metadata[field_name]))
        
        if mapping.transformation_function:
            return mapping.transformation_function(values)
        else:
            # Default aggregation: join with semicolon
            return '; '.join(values) if values else mapping.default_value
    
    def _apply_validation_transform(self, value: Any, validation_rules: Dict[str, Any]) -> Any:
        """Apply validation and transformation rules."""
        if not validation_rules:
            return value
        
        transformed_value = value
        
        # Apply length limits
        if 'max_length' in validation_rules and isinstance(transformed_value, str):
            max_length = validation_rules['max_length']
            if len(transformed_value) > max_length:
                # Truncate at sentence boundary if possible
                truncated = self._truncate_at_sentence_boundary(transformed_value, max_length)
                transformed_value = truncated
        
        # Apply format rules
        if 'format' in validation_rules:
            format_rule = validation_rules['format']
            if format_rule == 'uppercase':
                transformed_value = str(transformed_value).upper()
            elif format_rule == 'lowercase':
                transformed_value = str(transformed_value).lower()
            elif format_rule == 'title_case':
                transformed_value = str(transformed_value).title()
            elif format_rule == 'sentence_case':
                transformed_value = self._to_sentence_case(str(transformed_value))
        
        # Apply numeric formatting
        if 'decimal_places' in validation_rules and isinstance(transformed_value, (int, float, Decimal)):
            decimal_places = validation_rules['decimal_places']
            transformed_value = f"{float(transformed_value):.{decimal_places}f}"
        
        # Apply pattern replacement
        if 'pattern_replacements' in validation_rules:
            for pattern, replacement in validation_rules['pattern_replacements'].items():
                transformed_value = re.sub(pattern, replacement, str(transformed_value))
        
        return transformed_value
    
    def _check_conditions(self, metadata: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """Check if mapping conditions are met."""
        for field_name, expected_value in conditions.items():
            if field_name not in metadata:
                return False
            
            actual_value = metadata[field_name]
            
            if isinstance(expected_value, dict):
                # Complex condition
                if 'equals' in expected_value:
                    if actual_value != expected_value['equals']:
                        return False
                if 'not_equals' in expected_value:
                    if actual_value == expected_value['not_equals']:
                        return False
                if 'in' in expected_value:
                    if actual_value not in expected_value['in']:
                        return False
                if 'not_empty' in expected_value and expected_value['not_empty']:
                    if not actual_value or (isinstance(actual_value, str) and not actual_value.strip()):
                        return False
            else:
                # Simple equality check
                if actual_value != expected_value:
                    return False
        
        return True
    
    def _process_computed_fields(self, target_metadata: Dict[str, Any], 
                               source_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process computed fields that depend on other transformed fields."""
        
        # Calculate spine width based on page count and paper type
        if 'Page Count' in target_metadata and 'Paper Color' in target_metadata:
            page_count = int(target_metadata.get('Page Count', 0))
            paper_color = target_metadata.get('Paper Color', 'White')
            
            # Standard spine width calculation
            if paper_color.lower() == 'cream':
                spine_width = page_count * 0.0025  # Cream paper is slightly thicker
            else:
                spine_width = page_count * 0.002252  # White paper standard thickness
            
            target_metadata['Spine Width'] = f"{spine_width:.4f}"
        
        # Calculate international prices if US price exists
        if 'US List Price' in target_metadata:
            us_price = float(target_metadata['US List Price'])
            
            # Exchange rates and fees (these would typically come from config)
            exchange_rates = {
                'CA': 1.35,  # USD to CAD
                'EU': 0.85,  # USD to EUR
                'AU': 1.45,  # USD to AUD
                'UK': 0.75   # USD to GBP
            }
            
            processing_fees = {
                'CA': 0.05,  # 5% processing fee
                'EU': 0.07,  # 7% processing fee
                'AU': 0.06,  # 6% processing fee
                'UK': 0.05   # 5% processing fee
            }
            
            for region, rate in exchange_rates.items():
                converted_price = us_price * rate
                fee = converted_price * processing_fees[region]
                final_price = converted_price + fee
                
                target_metadata[f'{region} List Price'] = f"{final_price:.2f}"
        
        # Generate file paths based on title and format
        if 'Title' in target_metadata:
            title = target_metadata['Title']
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            
            target_metadata['Interior File Path'] = f"{safe_title}_interior.pdf"
            target_metadata['Cover File Path'] = f"{safe_title}_cover.pdf"
        
        return target_metadata
    
    def _validate_field_value(self, value: Any, validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a field value against rules."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if value is None or value == '':
            if validation_rules.get('required', False):
                result['valid'] = False
                result['errors'].append("Required field is empty")
            return result
        
        str_value = str(value)
        
        # Length validation
        if 'min_length' in validation_rules:
            if len(str_value) < validation_rules['min_length']:
                result['valid'] = False
                result['errors'].append(f"Value too short (min: {validation_rules['min_length']})")
        
        if 'max_length' in validation_rules:
            if len(str_value) > validation_rules['max_length']:
                result['warnings'].append(f"Value too long (max: {validation_rules['max_length']})")
        
        # Pattern validation
        if 'pattern' in validation_rules:
            if not re.match(validation_rules['pattern'], str_value):
                result['valid'] = False
                result['errors'].append(f"Value doesn't match required pattern")
        
        # Allowed values validation
        if 'allowed_values' in validation_rules:
            if str_value not in validation_rules['allowed_values']:
                result['valid'] = False
                result['errors'].append(f"Value not in allowed list")
        
        return result
    
    def _validate_transformed_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate the complete transformed metadata."""
        issues = []
        
        # Check for required LSI fields
        required_fields = [
            'Title', 'ISBN', 'List Price', 'Binding Type', 
            'Trim Size', 'Page Count', 'Interior Color', 'Paper Color'
        ]
        
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                issues.append(f"Required field missing or empty: {field}")
        
        # Validate field relationships
        if 'Age Range From' in metadata and 'Age Range To' in metadata:
            try:
                age_from = int(metadata['Age Range From'])
                age_to = int(metadata['Age Range To'])
                if age_from >= age_to:
                    issues.append("Age Range From must be less than Age Range To")
            except (ValueError, TypeError):
                issues.append("Invalid age range values")
        
        # Validate BISAC codes
        bisac_fields = ['BISAC Category', 'BISAC Category 2', 'BISAC Category 3']
        for field in bisac_fields:
            if field in metadata and metadata[field]:
                bisac_code = metadata[field]
                if not re.match(r'^[A-Z]{3}\d{6}$', bisac_code):
                    issues.append(f"Invalid BISAC code format in {field}: {bisac_code}")
        
        # Validate prices
        price_fields = ['List Price', 'US List Price', 'CA List Price', 'EU List Price', 'AU List Price']
        for field in price_fields:
            if field in metadata and metadata[field]:
                try:
                    price = float(metadata[field])
                    if price < 0:
                        issues.append(f"Negative price in {field}: {price}")
                    elif price == 0:
                        issues.append(f"Zero price in {field} - confirm intentional")
                except (ValueError, TypeError):
                    issues.append(f"Invalid price format in {field}: {metadata[field]}")
        
        return issues
    
    def _truncate_at_sentence_boundary(self, text: str, max_length: int) -> str:
        """Truncate text at sentence boundary within max_length."""
        if len(text) <= max_length:
            return text
        
        # Find the last sentence boundary before max_length
        truncated = text[:max_length]
        
        # Look for sentence endings
        sentence_endings = ['. ', '! ', '? ']
        last_sentence_end = -1
        
        for ending in sentence_endings:
            pos = truncated.rfind(ending)
            if pos > last_sentence_end:
                last_sentence_end = pos + len(ending) - 1
        
        if last_sentence_end > max_length * 0.7:  # Only use if we don't lose too much
            return text[:last_sentence_end + 1].strip()
        else:
            # Truncate at word boundary
            words = truncated.split()
            if len(words) > 1:
                words.pop()  # Remove last potentially incomplete word
                return ' '.join(words) + '...'
            else:
                return truncated + '...'
    
    def _to_sentence_case(self, text: str) -> str:
        """Convert text to sentence case."""
        if not text:
            return text
        
        # Capitalize first letter and make rest lowercase
        sentences = re.split(r'([.!?]\s+)', text)
        result = []
        
        for sentence in sentences:
            if sentence and not re.match(r'^[.!?]\s+$', sentence):
                sentence = sentence.strip()
                if sentence:
                    sentence = sentence[0].upper() + sentence[1:].lower()
            result.append(sentence)
        
        return ''.join(result)
    
    def _get_profile_mappings(self, profile: str) -> List[FieldMapping]:
        """Get field mappings for a specific profile."""
        if profile == "lsi_standard":
            return self._get_lsi_standard_mappings()
        elif profile == "basic_metadata":
            return self._get_basic_metadata_mappings()
        else:
            return self.field_mappings.get(profile, [])
    
    def _get_lsi_standard_mappings(self) -> List[FieldMapping]:
        """Get standard LSI field mappings."""
        return [
            # Direct mappings
            FieldMapping(
                source_field='title',
                target_field='Title',
                transformation_type=TransformationType.DIRECT_COPY
            ),
            FieldMapping(
                source_field='isbn',
                target_field='ISBN',
                transformation_type=TransformationType.FORMAT_CONVERSION,
                transformation_function=self.transformation_functions['clean_isbn']
            ),
            FieldMapping(
                source_field='list_price',
                target_field='List Price',
                transformation_type=TransformationType.FORMAT_CONVERSION,
                transformation_function=self.transformation_functions['format_price']
            ),
            
            # Value mappings
            FieldMapping(
                source_field='binding',
                target_field='Binding Type',
                transformation_type=TransformationType.VALUE_MAPPING,
                value_map={
                    'paperback': 'Paperback',
                    'hardcover': 'Hardcover',
                    'spiral': 'Spiral Bound',
                    'pb': 'Paperback',
                    'hc': 'Hardcover'
                },
                default_value='Paperback'
            ),
            
            # Computed fields
            FieldMapping(
                source_field='page_count',
                target_field='Spine Width',
                transformation_type=TransformationType.COMPUTED_FIELD,
                transformation_function=self.transformation_functions['calculate_spine_width'],
                dependencies=['page_count', 'paper_color']
            ),
            
            # Validation transforms
            FieldMapping(
                source_field='short_description',
                target_field='Short Description',
                transformation_type=TransformationType.VALIDATION_TRANSFORM,
                validation_rules={
                    'max_length': 350,
                    'format': 'sentence_case'
                }
            ),
            FieldMapping(
                source_field='long_description',
                target_field='Long Description',
                transformation_type=TransformationType.VALIDATION_TRANSFORM,
                validation_rules={
                    'max_length': 4000,
                    'pattern_replacements': {
                        r'<[^>]+>': '',  # Remove HTML tags
                        r'\s+': ' '      # Normalize whitespace
                    }
                }
            )
        ]
    
    def _get_basic_metadata_mappings(self) -> List[FieldMapping]:
        """Get basic metadata field mappings."""
        return [
            FieldMapping(
                source_field='title',
                target_field='Title',
                transformation_type=TransformationType.DIRECT_COPY
            ),
            FieldMapping(
                source_field='author',
                target_field='Author',
                transformation_type=TransformationType.DIRECT_COPY
            ),
            FieldMapping(
                source_field='publisher',
                target_field='Publisher',
                transformation_type=TransformationType.DIRECT_COPY
            )
        ]
    
    def _initialize_default_mappings(self) -> Dict[str, List[FieldMapping]]:
        """Initialize default field mappings."""
        return {
            'lsi_standard': self._get_lsi_standard_mappings(),
            'basic_metadata': self._get_basic_metadata_mappings()
        }
    
    def _initialize_transformation_functions(self) -> Dict[str, Callable]:
        """Initialize transformation functions."""
        return {
            'clean_isbn': lambda isbn: re.sub(r'[-\s]', '', str(isbn)),
            'format_price': lambda price: f"{float(price):.2f}",
            'calculate_spine_width': self._calculate_spine_width,
            'format_date': lambda date_str: datetime.strptime(str(date_str), '%Y-%m-%d').strftime('%Y-%m-%d'),
            'normalize_whitespace': lambda text: re.sub(r'\s+', ' ', str(text).strip()),
            'remove_html': lambda text: re.sub(r'<[^>]+>', '', str(text)),
            'to_title_case': lambda text: str(text).title(),
            'join_with_semicolon': lambda values: '; '.join(str(v) for v in values if v)
        }
    
    def _calculate_spine_width(self, metadata: Dict[str, Any]) -> str:
        """Calculate spine width based on page count and paper type."""
        page_count = int(metadata.get('page_count', 0))
        paper_color = metadata.get('paper_color', 'White')
        
        if paper_color.lower() == 'cream':
            spine_width = page_count * 0.0025
        else:
            spine_width = page_count * 0.002252
        
        return f"{spine_width:.4f}"


def transform_metadata_for_lsi(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to transform metadata for LSI format."""
    transformer = FieldMappingTransformer()
    return transformer.transform_metadata(metadata, "lsi_standard")


def validate_field_mappings(mappings: List[FieldMapping]) -> List[str]:
    """Validate field mapping definitions."""
    issues = []
    
    target_fields = set()
    for mapping in mappings:
        # Check for duplicate target fields
        if mapping.target_field in target_fields:
            issues.append(f"Duplicate target field: {mapping.target_field}")
        target_fields.add(mapping.target_field)
        
        # Validate transformation type and function compatibility
        if mapping.transformation_type == TransformationType.COMPUTED_FIELD:
            if not mapping.transformation_function:
                issues.append(f"Computed field {mapping.target_field} missing transformation function")
        
        if mapping.transformation_type == TransformationType.VALUE_MAPPING:
            if not mapping.value_map:
                issues.append(f"Value mapping field {mapping.target_field} missing value map")
    
    return issues