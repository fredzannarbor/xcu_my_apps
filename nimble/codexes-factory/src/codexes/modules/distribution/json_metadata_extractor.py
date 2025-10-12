"""
JSON Metadata Extractor for LSI Field Mapping

This module extracts specific metadata fields from JSON book data,
including thema subjects and age ranges with proper validation.
"""

from typing import Dict, List, Optional, Tuple, Any
import logging
import json

logger = logging.getLogger(__name__)


class JSONMetadataExtractor:
    """Extracts and validates metadata from JSON book data."""
    
    def __init__(self):
        """Initialize the metadata extractor."""
        self.warnings = []
        self.errors = []
        
    def extract_thema_subjects(self, metadata: dict) -> List[str]:
        """
        Extract up to 3 thema subject codes from metadata.
        
        Args:
            metadata: Dictionary containing book metadata
            
        Returns:
            List of up to 3 thema subject codes
        """
        self.warnings.clear()
        thema_subjects = []
        
        try:
            # Look for thema data in various possible locations
            thema_data = None
            
            # Check direct thema field
            if 'thema' in metadata:
                thema_data = metadata['thema']
            elif 'thema_subjects' in metadata:
                thema_data = metadata['thema_subjects']
            elif 'subjects' in metadata and isinstance(metadata['subjects'], dict):
                thema_data = metadata['subjects'].get('thema')
                
            if not thema_data:
                logger.debug("No thema data found in metadata")
                return []
                
            # Handle different data formats
            if isinstance(thema_data, str):
                # Try to parse as JSON if it's a string
                try:
                    parsed_data = json.loads(thema_data)
                    if isinstance(parsed_data, dict):
                        # Extract values from JSON object
                        for key in ['thema_subject_1', 'thema_subject_2', 'thema_subject_3']:
                            if key in parsed_data and parsed_data[key]:
                                thema_subjects.append(str(parsed_data[key]))
                    elif isinstance(parsed_data, list):
                        thema_subjects = [str(item) for item in parsed_data[:3] if item]
                except json.JSONDecodeError:
                    # Treat as single subject code
                    thema_subjects = [thema_data]
                    
            elif isinstance(thema_data, list):
                # Direct list of subject codes
                thema_subjects = [str(item) for item in thema_data[:3] if item]
                
            elif isinstance(thema_data, dict):
                # Extract from dictionary structure
                for key in ['thema_subject_1', 'thema_subject_2', 'thema_subject_3']:
                    if key in thema_data and thema_data[key]:
                        thema_subjects.append(str(thema_data[key]))
                        
                # Also check for numbered keys
                for i in range(1, 4):
                    key = f'subject_{i}'
                    if key in thema_data and thema_data[key]:
                        thema_subjects.append(str(thema_data[key]))
                        
            # Validate and clean subject codes
            validated_subjects = []
            for subject in thema_subjects[:3]:  # Limit to 3
                if self._validate_thema_code(subject):
                    validated_subjects.append(subject.strip().upper())
                else:
                    self.warnings.append(f"Invalid thema code format: {subject}")
                    
            logger.debug(f"Extracted {len(validated_subjects)} thema subjects: {validated_subjects}")
            return validated_subjects
            
        except Exception as e:
            error_msg = f"Error extracting thema subjects: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return []
            
    def extract_age_range(self, metadata: dict) -> Tuple[Optional[int], Optional[int]]:
        """
        Extract and validate min/max age values.
        
        Args:
            metadata: Dictionary containing book metadata
            
        Returns:
            Tuple of (min_age, max_age) as integers or None
        """
        self.warnings.clear()
        min_age = None
        max_age = None
        
        try:
            # Extract min age
            if 'min_age' in metadata:
                min_age = self.validate_age_value(metadata['min_age'])
            elif 'age_range' in metadata and isinstance(metadata['age_range'], dict):
                min_age = self.validate_age_value(metadata['age_range'].get('min'))
                
            # Extract max age
            if 'max_age' in metadata:
                max_age = self.validate_age_value(metadata['max_age'])
            elif 'age_range' in metadata and isinstance(metadata['age_range'], dict):
                max_age = self.validate_age_value(metadata['age_range'].get('max'))
                
            # Handle JSON string format
            for field in ['min_age', 'max_age']:
                if field in metadata and isinstance(metadata[field], str):
                    try:
                        parsed_data = json.loads(metadata[field])
                        if field == 'min_age':
                            min_age = self.validate_age_value(parsed_data)
                        else:
                            max_age = self.validate_age_value(parsed_data)
                    except json.JSONDecodeError:
                        pass  # Will be handled by validate_age_value
                        
            # Validate age range logic
            if min_age is not None and max_age is not None:
                if min_age > max_age:
                    self.warnings.append(f"Min age ({min_age}) is greater than max age ({max_age})")
                    
            logger.debug(f"Extracted age range: min={min_age}, max={max_age}")
            return min_age, max_age
            
        except Exception as e:
            error_msg = f"Error extracting age range: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return None, None
            
    def validate_age_value(self, age: Any) -> Optional[int]:
        """
        Validate and convert age value to integer.
        
        Args:
            age: Age value to validate
            
        Returns:
            Validated age as integer or None if invalid
        """
        if age is None or age == "":
            return None
            
        try:
            # Handle string representations
            if isinstance(age, str):
                age = age.strip()
                if age.lower() in ['adult', 'all ages', 'general']:
                    return None  # These are not numeric ages
                    
            # Convert to integer
            age_int = int(float(age))  # Handle float strings like "18.0"
            
            # Validate range
            if age_int < 0:
                self.warnings.append(f"Negative age value: {age_int}")
                return None
            elif age_int > 150:
                self.warnings.append(f"Unrealistic age value: {age_int}")
                return None
                
            return age_int
            
        except (ValueError, TypeError) as e:
            self.warnings.append(f"Invalid age value format: {age} ({str(e)})")
            return None
            
    def _validate_thema_code(self, code: str) -> bool:
        """
        Validate thema subject code format.
        
        Args:
            code: Thema code to validate
            
        Returns:
            True if code appears to be valid format
        """
        if not code or not isinstance(code, str):
            return False
            
        code = code.strip()
        
        # Basic validation - thema codes are typically 2-4 uppercase letters
        # followed by optional numbers
        if len(code) < 2 or len(code) > 10:
            return False
            
        # Should start with letters
        if not code[0].isalpha():
            return False
            
        # Should contain only letters and numbers
        if not code.replace(' ', '').isalnum():
            return False
            
        return True
        
    def extract_series_info(self, metadata: dict) -> Tuple[Optional[str], Optional[int]]:
        """
        Extract series name and number from metadata.
        
        Args:
            metadata: Dictionary containing book metadata
            
        Returns:
            Tuple of (series_name, series_number)
        """
        series_name = None
        series_number = None
        
        try:
            # Look for series name
            if 'series_name' in metadata:
                series_name = metadata['series_name']
            elif 'series' in metadata:
                if isinstance(metadata['series'], str):
                    series_name = metadata['series']
                elif isinstance(metadata['series'], dict):
                    series_name = metadata['series'].get('name')
                    series_number = metadata['series'].get('number')
                    
            # Look for series number
            if series_number is None:
                if 'series_number' in metadata:
                    try:
                        series_number = int(metadata['series_number'])
                    except (ValueError, TypeError):
                        pass
                elif 'number_in_series' in metadata:
                    try:
                        series_number = int(metadata['number_in_series'])
                    except (ValueError, TypeError):
                        pass
                        
            # Clean series name
            if series_name:
                series_name = str(series_name).strip()
                if not series_name:
                    series_name = None
                    
            logger.debug(f"Extracted series info: name='{series_name}', number={series_number}")
            return series_name, series_number
            
        except Exception as e:
            error_msg = f"Error extracting series info: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return None, None
            
    def get_warnings(self) -> List[str]:
        """Get list of warnings from last extraction."""
        return self.warnings.copy()
        
    def get_errors(self) -> List[str]:
        """Get list of errors from last extraction."""
        return self.errors.copy()
        
    def clear_messages(self):
        """Clear warnings and errors."""
        self.warnings.clear()
        self.errors.clear()