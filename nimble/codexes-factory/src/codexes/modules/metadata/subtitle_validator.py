"""
Subtitle validator with length validation and LLM replacement for xynapse_traces titles.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from nimble_llm_caller.core.llm_caller import LLMCaller
from nimble_llm_caller.models.request import LLMRequest, ResponseFormat

logger = logging.getLogger(__name__)

try:
    from ..fixes.validation_system import ValidationSystem
except ImportError:
    logger.warning("ValidationSystem not available, using basic validation")


@dataclass
class ValidationResult:
    """Result of subtitle validation"""
    is_valid: bool
    current_length: int
    max_length: int
    needs_replacement: bool
    error_message: Optional[str] = None


class SubtitleValidator:
    """Validate subtitle length and generate replacements using LLM"""
    
    def __init__(self, llm_caller: Optional[LLMCaller] = None):
        """Initialize subtitle validator with LLM caller"""
        self.llm_caller = llm_caller or LLMCaller()
        
        # Imprint-specific character limits
        self.character_limits = {
            'xynapse_traces': 38,
            'default': 80  # Default limit for other imprints
        }
        
        # LLM configuration for subtitle generation
        self.llm_config = {
            'model': 'gpt-5-mini',
            'max_tokens': 50,
            'temperature': 0.7,
            'timeout': 30
        }
        
        # Initialize validation system
        try:
            self.validator = ValidationSystem()
        except NameError:
            self.validator = None
    
    def validate_subtitle_length(self, subtitle: str, imprint: str) -> ValidationResult:
        """Validate subtitle length against imprint-specific limits with comprehensive validation"""
        try:
            # Use comprehensive validation system if available
            if self.validator:
                max_length = self.character_limits.get(imprint, self.character_limits['default'])
                validation_result = self.validator.validate_subtitle_length(subtitle, imprint, max_length)
                
                # Convert to our ValidationResult format
                result = ValidationResult(
                    is_valid=validation_result.is_valid,
                    current_length=len(subtitle) if subtitle else 0,
                    max_length=max_length,
                    needs_replacement=not validation_result.is_valid and imprint == 'xynapse_traces',
                    error_message=validation_result.error_message
                )
                
                # Log any warnings
                for warning in validation_result.warnings:
                    logger.warning(f"Subtitle validation warning: {warning}")
                
                return result
            
            # Fallback to basic validation
            return self._basic_subtitle_validation(subtitle, imprint)
            
        except Exception as e:
            logger.error(f"Error validating subtitle length: {e}")
            return ValidationResult(
                is_valid=False,
                current_length=len(subtitle) if subtitle else 0,
                max_length=self.character_limits.get(imprint, self.character_limits['default']),
                needs_replacement=False,
                error_message=f"Validation error: {e}"
            )
    
    def _basic_subtitle_validation(self, subtitle: str, imprint: str) -> ValidationResult:
        """Basic subtitle validation when ValidationSystem is not available"""
        try:
            if not subtitle:
                return ValidationResult(
                    is_valid=True,
                    current_length=0,
                    max_length=self.character_limits.get(imprint, self.character_limits['default']),
                    needs_replacement=False
                )
            
            current_length = len(subtitle)
            max_length = self.character_limits.get(imprint, self.character_limits['default'])
            
            is_valid = current_length <= max_length
            needs_replacement = not is_valid and imprint == 'xynapse_traces'
            
            result = ValidationResult(
                is_valid=is_valid,
                current_length=current_length,
                max_length=max_length,
                needs_replacement=needs_replacement
            )
            
            if not is_valid:
                result.error_message = f"Subtitle exceeds {max_length} character limit: {current_length} characters"
                logger.warning(f"Subtitle validation failed for {imprint}: {result.error_message}")
            else:
                logger.info(f"Subtitle validation passed for {imprint}: {current_length}/{max_length} characters")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in basic subtitle validation: {e}")
            return ValidationResult(
                is_valid=False,
                current_length=len(subtitle) if subtitle else 0,
                max_length=self.character_limits.get(imprint, self.character_limits['default']),
                needs_replacement=False,
                error_message=f"Basic validation error: {e}"
            )
    
    def generate_replacement_subtitle(self, original_subtitle: str, book_metadata: Dict[str, Any]) -> str:
        """Generate replacement subtitle using nimble-llm-caller"""
        try:
            # Extract relevant metadata for context
            title = book_metadata.get('title', 'Unknown Title')
            subject = book_metadata.get('subject', book_metadata.get('stream', 'general topic'))
            imprint = book_metadata.get('imprint', 'xynapse_traces')
            
            # Get character limit for this imprint
            char_limit = self.character_limits.get(imprint, self.character_limits['default'])
            
            # Create prompt for subtitle generation
            prompt = self._create_subtitle_prompt(original_subtitle, title, subject, char_limit)
            
            # Create LLM request
            llm_request = LLMRequest(
                messages=[
                    {"role": "system", "content": "You are an expert book editor specializing in creating concise, compelling subtitles."},
                    {"role": "user", "content": prompt}
                ],
                model=self.llm_config['model'],
                max_tokens=self.llm_config['max_tokens'],
                temperature=self.llm_config['temperature']
            )
            
            # Make LLM call with retry logic
            response = self.llm_caller.call_llm(llm_request)
            
            if response and response.content:
                new_subtitle = response.content.strip().strip('"').strip("'")
                
                # Validate LLM response using validation system
                if self.validator:
                    llm_validation = self.validator.validate_llm_response(new_subtitle, char_limit)
                    
                    if llm_validation.is_valid:
                        logger.info(f"Generated replacement subtitle: '{new_subtitle}' ({len(new_subtitle)} chars)")
                        return new_subtitle
                    else:
                        logger.warning(f"LLM response validation failed: {llm_validation.error_message}")
                        return self._truncate_subtitle_safely(new_subtitle, char_limit)
                else:
                    # Fallback validation
                    if len(new_subtitle) <= char_limit:
                        logger.info(f"Generated replacement subtitle: '{new_subtitle}' ({len(new_subtitle)} chars)")
                        return new_subtitle
                    else:
                        logger.warning(f"Generated subtitle too long ({len(new_subtitle)} chars), truncating")
                        return self._truncate_subtitle_safely(new_subtitle, char_limit)
            else:
                logger.error("LLM returned empty response for subtitle generation")
                return self._fallback_subtitle_generation(original_subtitle, char_limit)
                
        except Exception as e:
            logger.error(f"Error generating replacement subtitle: {e}")
            return self._fallback_subtitle_generation(original_subtitle, char_limit)
    
    def _create_subtitle_prompt(self, original_subtitle: str, title: str, subject: str, char_limit: int) -> str:
        """Create prompt for LLM subtitle generation"""
        prompt = f"""
Create a new, shorter subtitle for this book that captures the essence of the original but fits within {char_limit} characters.

Book Title: {title}
Subject/Topic: {subject}
Original Subtitle: {original_subtitle}
Character Limit: {char_limit}

Requirements:
- Must be {char_limit} characters or fewer
- Should capture the key concept from the original subtitle
- Should be engaging and descriptive
- Should fit the academic/educational tone of xynapse traces books
- Do not include quotation marks in your response

New Subtitle:"""
        
        return prompt
    
    def _truncate_subtitle_safely(self, subtitle: str, max_length: int) -> str:
        """Safely truncate subtitle at word boundaries"""
        try:
            if len(subtitle) <= max_length:
                return subtitle
            
            # Try to truncate at word boundary
            truncated = subtitle[:max_length]
            last_space = truncated.rfind(' ')
            
            if last_space > max_length * 0.7:  # If we can keep at least 70% of the text
                return truncated[:last_space].rstrip('.,;:')
            else:
                # Truncate at character boundary and add ellipsis if space allows
                if max_length > 3:
                    return subtitle[:max_length-3] + "..."
                else:
                    return subtitle[:max_length]
                    
        except Exception as e:
            logger.error(f"Error truncating subtitle: {e}")
            return subtitle[:max_length] if len(subtitle) > max_length else subtitle
    
    def _fallback_subtitle_generation(self, original_subtitle: str, char_limit: int) -> str:
        """Generate fallback subtitle when LLM fails"""
        try:
            # Simple fallback: truncate original subtitle intelligently
            if len(original_subtitle) <= char_limit:
                return original_subtitle
            
            # Try to extract key words and create a shorter version
            words = original_subtitle.split()
            
            # Keep the most important words (first few and last few)
            if len(words) > 3:
                # Keep first 2 and last 1 words, add connecting words if they fit
                key_words = words[:2] + words[-1:]
                fallback = ' '.join(key_words)
                
                if len(fallback) <= char_limit:
                    logger.info(f"Generated fallback subtitle: '{fallback}'")
                    return fallback
            
            # Final fallback: safe truncation
            return self._truncate_subtitle_safely(original_subtitle, char_limit)
            
        except Exception as e:
            logger.error(f"Error in fallback subtitle generation: {e}")
            return original_subtitle[:char_limit] if len(original_subtitle) > char_limit else original_subtitle
    
    def process_xynapse_subtitle(self, subtitle: str, book_metadata: Dict[str, Any]) -> str:
        """Process xynapse_traces subtitle with length validation and replacement"""
        try:
            imprint = book_metadata.get('imprint', 'xynapse_traces')
            
            # Validate subtitle length
            validation_result = self.validate_subtitle_length(subtitle, imprint)
            
            if validation_result.is_valid:
                logger.info(f"Subtitle validation passed: '{subtitle}'")
                return subtitle
            
            if validation_result.needs_replacement:
                logger.info(f"Subtitle needs replacement due to length: {validation_result.current_length} > {validation_result.max_length}")
                
                # Generate replacement subtitle
                new_subtitle = self.generate_replacement_subtitle(subtitle, book_metadata)
                
                # Final validation of replacement
                final_validation = self.validate_subtitle_length(new_subtitle, imprint)
                
                if final_validation.is_valid:
                    logger.info(f"Successfully replaced subtitle: '{subtitle}' -> '{new_subtitle}'")
                    return new_subtitle
                else:
                    logger.error(f"Generated subtitle still invalid: {final_validation.error_message}")
                    # Force truncation as last resort
                    return self._truncate_subtitle_safely(new_subtitle, validation_result.max_length)
            else:
                # For non-xynapse_traces imprints, just log the issue
                logger.warning(f"Subtitle exceeds limit for {imprint} but replacement not enabled: '{subtitle}'")
                return subtitle
                
        except Exception as e:
            logger.error(f"Error processing xynapse subtitle: {e}")
            # Use comprehensive error handler
            try:
                from ..fixes.error_handler import handle_fix_error, FixComponentType, ErrorSeverity
                
                context = {
                    'subtitle': subtitle, 
                    'char_limit': self.character_limits.get(book_metadata.get('imprint', 'xynapse_traces'), 38),
                    'book_metadata': book_metadata
                }
                return handle_fix_error(
                    FixComponentType.SUBTITLE_VALIDATOR, 
                    e, 
                    context, 
                    ErrorSeverity.MEDIUM
                )
            except ImportError:
                # Fallback if error handler not available
                return subtitle
    
    def batch_validate_subtitles(self, subtitle_data: Dict[str, Dict[str, Any]]) -> Dict[str, ValidationResult]:
        """Validate multiple subtitles in batch"""
        try:
            results = {}
            
            for book_id, data in subtitle_data.items():
                subtitle = data.get('subtitle', '')
                imprint = data.get('imprint', 'default')
                
                validation_result = self.validate_subtitle_length(subtitle, imprint)
                results[book_id] = validation_result
            
            logger.info(f"Batch validated {len(results)} subtitles")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch subtitle validation: {e}")
            return {}
    
    def get_character_limit(self, imprint: str) -> int:
        """Get character limit for specific imprint"""
        return self.character_limits.get(imprint, self.character_limits['default'])
    
    def update_character_limits(self, limits: Dict[str, int]) -> None:
        """Update character limits for imprints"""
        try:
            self.character_limits.update(limits)
            logger.info(f"Updated character limits: {limits}")
        except Exception as e:
            logger.error(f"Error updating character limits: {e}")