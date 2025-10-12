"""
Enhanced error handling system with detailed logging and recovery mechanisms.
"""

from typing import Dict, List, Any, Optional, Callable
import logging
import traceback
import json
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ErrorContext:
    """Context information for error handling"""
    operation: str
    timestamp: datetime
    input_data: Dict[str, Any] = field(default_factory=dict)
    system_state: Dict[str, Any] = field(default_factory=dict)
    error_type: str = "unknown"
    recovery_attempted: bool = False
    recovery_successful: bool = False


class EnhancedErrorHandler:
    """Comprehensive error handling with detailed logging and recovery"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.error_context: Dict[str, ErrorContext] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.error_counts: Dict[str, int] = {}
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """Register a recovery strategy for a specific error type"""
        self.recovery_strategies[error_type] = strategy
        self.logger.info(f"Registered recovery strategy for {error_type}")
    
    def handle_quote_verification_error(self, response: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quote verification failures with detailed logging"""
        try:
            error_context = ErrorContext(
                operation="quote_verification",
                timestamp=datetime.now(),
                input_data={"response": response, "context": context},
                error_type="quote_verification_failure"
            )
            
            # Log the error with full context
            self.log_error_with_context(
                Exception("Quote verification failed"),
                {
                    "response": response,
                    "context": context,
                    "expected_keys": ["verified_quotes"],
                    "actual_keys": list(response.keys()) if isinstance(response, dict) else []
                }
            )
            
            # Attempt recovery
            recovered_response = self._attempt_quote_verification_recovery(response, context)
            
            if recovered_response:
                error_context.recovery_attempted = True
                error_context.recovery_successful = True
                self.logger.info("Quote verification recovery successful")
                return recovered_response
            else:
                error_context.recovery_attempted = True
                error_context.recovery_successful = False
                self.logger.warning("Quote verification recovery failed")
                
                # Return safe fallback
                return {
                    'verified_quotes': [],
                    'verification_status': 'failed',
                    'error': 'Quote verification failed and recovery unsuccessful',
                    'original_response': response
                }
            
        except Exception as e:
            self.logger.error(f"Error in quote verification error handler: {e}")
            return {
                'verified_quotes': [],
                'verification_status': 'error',
                'error': f'Quote verification error handler failed: {e}'
            }
    
    def _attempt_quote_verification_recovery(self, response: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Attempt to recover from quote verification errors"""
        try:
            # Strategy 1: Check if verified_quotes is missing but other quote data exists
            if 'verified_quotes' not in response:
                # Look for alternative quote keys
                quote_keys = ['quotes', 'quote_list', 'validated_quotes', 'final_quotes']
                for key in quote_keys:
                    if key in response and isinstance(response[key], list):
                        self.logger.info(f"Recovered quotes from alternative key: {key}")
                        return {
                            'verified_quotes': response[key],
                            'verification_status': 'recovered',
                            'recovery_method': f'alternative_key_{key}'
                        }
            
            # Strategy 2: Check if response contains quote-like data in unexpected format
            if isinstance(response, dict):
                for key, value in response.items():
                    if isinstance(value, list) and len(value) > 0:
                        # Check if list items look like quotes
                        if all(isinstance(item, (str, dict)) for item in value):
                            self.logger.info(f"Recovered quotes from unexpected format in key: {key}")
                            return {
                                'verified_quotes': value,
                                'verification_status': 'recovered',
                                'recovery_method': f'format_recovery_{key}'
                            }
            
            # Strategy 3: Extract quotes from string content if response is malformed
            if isinstance(response, str):
                quotes = self._extract_quotes_from_string(response)
                if quotes:
                    self.logger.info("Recovered quotes from string response")
                    return {
                        'verified_quotes': quotes,
                        'verification_status': 'recovered',
                        'recovery_method': 'string_extraction'
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Quote verification recovery failed: {e}")
            return None
    
    def _extract_quotes_from_string(self, text: str) -> List[str]:
        """Extract quotes from string content"""
        try:
            import re
            
            # Look for quoted text patterns
            patterns = [
                r'"([^"]+)"',  # Double quotes
                r"'([^']+)'",  # Single quotes
                r'«([^»]+)»',  # French quotes
                r'"([^"]+)"',  # Smart quotes
            ]
            
            quotes = []
            for pattern in patterns:
                matches = re.findall(pattern, text)
                quotes.extend(matches)
            
            # Filter out very short matches (likely not real quotes)
            quotes = [q.strip() for q in quotes if len(q.strip()) > 10]
            
            return quotes[:90]  # Limit to reasonable number
            
        except Exception as e:
            self.logger.error(f"Error extracting quotes from string: {e}")
            return []
    
    def handle_field_completion_error(self, error: Exception, field_name: str, completer_obj: Any = None) -> Any:
        """Handle field completion errors with fallback behavior"""
        try:
            error_context = ErrorContext(
                operation="field_completion",
                timestamp=datetime.now(),
                input_data={"field_name": field_name, "error": str(error)},
                error_type="field_completion_failure"
            )
            
            self.log_error_with_context(error, {
                "field_name": field_name,
                "completer_object": str(type(completer_obj)) if completer_obj else None,
                "available_methods": dir(completer_obj) if completer_obj else []
            })
            
            # Attempt recovery
            fallback_value = self._attempt_field_completion_recovery(error, field_name, completer_obj)
            
            if fallback_value is not None:
                error_context.recovery_attempted = True
                error_context.recovery_successful = True
                self.logger.info(f"Field completion recovery successful for {field_name}")
                return fallback_value
            else:
                error_context.recovery_attempted = True
                error_context.recovery_successful = False
                self.logger.warning(f"Field completion recovery failed for {field_name}")
                return self._get_field_default_value(field_name)
            
        except Exception as e:
            self.logger.error(f"Error in field completion error handler: {e}")
            return None
    
    def _attempt_field_completion_recovery(self, error: Exception, field_name: str, completer_obj: Any) -> Any:
        """Attempt to recover from field completion errors"""
        try:
            if completer_obj is None:
                return None
            
            # Strategy 1: Try alternative method names
            alternative_methods = [
                'complete_field_safe',
                'complete_field_fallback',
                'get_field_value',
                'generate_field_content',
                f'complete_{field_name}',
                f'get_{field_name}'
            ]
            
            for method_name in alternative_methods:
                if hasattr(completer_obj, method_name):
                    try:
                        method = getattr(completer_obj, method_name)
                        if callable(method):
                            result = method(field_name) if method_name.endswith('_safe') or method_name.endswith('_fallback') else method()
                            self.logger.info(f"Field completion recovered using method: {method_name}")
                            return result
                    except Exception as method_error:
                        self.logger.debug(f"Alternative method {method_name} failed: {method_error}")
                        continue
            
            # Strategy 2: Try to get cached or default value
            if hasattr(completer_obj, 'get_cached_value'):
                try:
                    cached_value = completer_obj.get_cached_value(field_name)
                    if cached_value:
                        self.logger.info(f"Field completion recovered from cache for {field_name}")
                        return cached_value
                except Exception:
                    pass
            
            return None
            
        except Exception as e:
            self.logger.error(f"Field completion recovery failed: {e}")
            return None
    
    def _get_field_default_value(self, field_name: str) -> Any:
        """Get default value for a field when all else fails"""
        defaults = {
            'title': 'Untitled',
            'author': 'Unknown Author',
            'description': 'Description not available',
            'category': 'General',
            'price': '0.00',
            'isbn': '',
            'publisher': 'Unknown Publisher',
            'publication_date': datetime.now().strftime('%Y-%m-%d'),
            'language': 'en',
            'page_count': '0'
        }
        
        return defaults.get(field_name, '')
    
    def handle_validation_error(self, validation_result: Dict[str, Any]) -> None:
        """Handle validation errors with context and recovery suggestions"""
        try:
            error_context = ErrorContext(
                operation="validation",
                timestamp=datetime.now(),
                input_data=validation_result,
                error_type="validation_failure"
            )
            
            # Extract validation details
            errors = validation_result.get('errors', [])
            warnings = validation_result.get('warnings', [])
            field_errors = validation_result.get('field_errors', {})
            
            # Log detailed validation information
            self.log_error_with_context(
                Exception("Validation failed"),
                {
                    "total_errors": len(errors),
                    "total_warnings": len(warnings),
                    "field_errors": field_errors,
                    "validation_result": validation_result
                }
            )
            
            # Provide recovery suggestions
            suggestions = self._generate_validation_recovery_suggestions(validation_result)
            if suggestions:
                self.logger.info(f"Validation recovery suggestions: {suggestions}")
            
        except Exception as e:
            self.logger.error(f"Error handling validation error: {e}")
    
    def _generate_validation_recovery_suggestions(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate suggestions for recovering from validation errors"""
        suggestions = []
        
        try:
            errors = validation_result.get('errors', [])
            field_errors = validation_result.get('field_errors', {})
            
            for error in errors:
                if 'required field' in str(error).lower():
                    suggestions.append("Check that all required fields are populated")
                elif 'format' in str(error).lower():
                    suggestions.append("Verify field formats match expected patterns")
                elif 'length' in str(error).lower():
                    suggestions.append("Check field length constraints")
            
            for field, field_error in field_errors.items():
                if 'empty' in str(field_error).lower():
                    suggestions.append(f"Populate empty field: {field}")
                elif 'invalid' in str(field_error).lower():
                    suggestions.append(f"Fix invalid value in field: {field}")
            
        except Exception as e:
            self.logger.error(f"Error generating validation suggestions: {e}")
        
        return suggestions
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log errors with comprehensive context for debugging"""
        try:
            error_id = f"error_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            error_info = {
                'error_id': error_id,
                'timestamp': datetime.now().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc(),
                'context': context
            }
            
            # Log as structured JSON for better parsing
            self.logger.error(f"STRUCTURED_ERROR: {json.dumps(error_info, default=str)}")
            
            # Also log human-readable version
            self.logger.error(f"Error {error_id}: {error}")
            for key, value in context.items():
                self.logger.error(f"  {key}: {value}")
            
            # Track error counts
            error_type = type(error).__name__
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
            
        except Exception as logging_error:
            # Fallback logging if structured logging fails
            self.logger.error(f"Original error: {error}")
            self.logger.error(f"Logging error: {logging_error}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics"""
        try:
            total_errors = sum(self.error_counts.values())
            
            return {
                'total_errors_handled': total_errors,
                'error_counts_by_type': self.error_counts.copy(),
                'recovery_attempts': len([ctx for ctx in self.error_context.values() if ctx.recovery_attempted]),
                'successful_recoveries': len([ctx for ctx in self.error_context.values() if ctx.recovery_successful]),
                'registered_strategies': list(self.recovery_strategies.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Error getting error statistics: {e}")
            return {}
    
    def clear_error_history(self):
        """Clear error history and statistics"""
        try:
            self.error_context.clear()
            self.error_counts.clear()
            self.logger.info("Error history cleared")
        except Exception as e:
            self.logger.error(f"Error clearing error history: {e}")