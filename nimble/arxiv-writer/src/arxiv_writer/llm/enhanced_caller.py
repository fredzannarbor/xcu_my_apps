"""
Enhanced LLM caller with exponential backoff and retry logic.
Handles rate limiting, high traffic, and other transient errors gracefully.
"""

import logging
import time
import random
import json
from typing import Dict, Any, Optional, List
import litellm
from litellm import completion

logger = logging.getLogger(__name__)

class EnhancedLLMCaller:
    """Enhanced LLM caller with retry logic and error handling."""
    
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        Initialize the enhanced LLM caller.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds between retries
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        # Configure litellm
        litellm.set_verbose = False
        
        # Rate limiting errors that should trigger retry
        self.retryable_errors = [
            "rate_limit_exceeded",
            "quota_exceeded", 
            "service_unavailable",
            "timeout",
            "internal_server_error",
            "bad_gateway",
            "service_temporarily_unavailable",
            "too_many_requests"
        ]
    
    def call_llm_with_retry(self, 
                           model: str, 
                           messages: List[Dict[str, str]], 
                           **kwargs) -> Optional[Dict[str, Any]]:
        """
        Call LLM with exponential backoff retry logic.
        
        Args:
            model: The model to use
            messages: List of message dictionaries
            **kwargs: Additional parameters for the LLM call
            
        Returns:
            LLM response or None if all retries failed
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"LLM call attempt {attempt + 1}/{self.max_retries + 1} for model {model}")
                
                # Make the LLM call
                response = completion(
                    model=model,
                    messages=messages,
                    **kwargs
                )
                
                # Success - return the response
                if attempt > 0:
                    logger.info(f"LLM call succeeded on attempt {attempt + 1} after {attempt} retries")
                
                # Extract content safely
                content = None
                if response.choices and len(response.choices) > 0:
                    choice = response.choices[0]
                    if hasattr(choice, 'message') and choice.message:
                        content = choice.message.content
                    elif hasattr(choice, 'text'):
                        content = choice.text
                    
                    # Check finish reason
                    if hasattr(choice, 'finish_reason') and choice.finish_reason == 'length':
                        logger.warning(f"LLM response was truncated due to max_tokens limit. Consider increasing max_tokens.")
                
                if content is None:
                    logger.warning(f"No content found in LLM response. Response structure: {type(response)}")
                    logger.warning(f"Choices: {response.choices if hasattr(response, 'choices') else 'No choices'}")
                    if response.choices and len(response.choices) > 0:
                        choice = response.choices[0]
                        logger.warning(f"Choice finish_reason: {getattr(choice, 'finish_reason', 'unknown')}")
                        logger.warning(f"Choice message: {getattr(choice, 'message', 'no message')}")
                
                return {
                    'content': content,
                    'usage': response.usage.dict() if response.usage else {},
                    'model': response.model,
                    'attempts': attempt + 1
                }
                
            except Exception as e:
                last_error = e
                error_message = str(e).lower()
                
                # Check if this is a retryable error
                is_retryable = any(error_type in error_message for error_type in self.retryable_errors)
                
                if not is_retryable or attempt == self.max_retries:
                    # Non-retryable error or max retries reached
                    if attempt == self.max_retries:
                        logger.error(f"Max retries ({self.max_retries}) reached for model {model}. Last error: {e}")
                    else:
                        logger.error(f"Non-retryable error for model {model}: {e}")
                    break
                
                # Calculate delay with exponential backoff and jitter
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                jitter = random.uniform(0, delay * 0.1)  # Add up to 10% jitter
                total_delay = delay + jitter
                
                logger.warning(f"Retryable error on attempt {attempt + 1}: {e}. "
                             f"Retrying in {total_delay:.2f} seconds...")
                
                time.sleep(total_delay)
        
        # All retries failed
        logger.error(f"All retry attempts failed for model {model}. Final error: {last_error}")
        return None
    
    def call_llm_json_with_retry(self, 
                                model: str, 
                                messages: List[Dict[str, str]], 
                                expected_keys: Optional[List[str]] = None,
                                **kwargs) -> Optional[Dict[str, Any]]:
        """
        Call LLM expecting JSON response with retry logic and validation.
        
        Args:
            model: The model to use
            messages: List of message dictionaries
            expected_keys: List of expected keys in the JSON response
            **kwargs: Additional parameters for the LLM call
            
        Returns:
            Parsed JSON response or None if failed
        """
        response = self.call_llm_with_retry(model, messages, **kwargs)
        
        if not response:
            return None
        
        content = response.get('content', '')
        
        # Try to parse JSON from the response
        parsed_json = self._extract_and_parse_json(content)
        
        if not parsed_json:
            content_preview = content[:200] if content else "None"
            logger.error(f"Failed to parse JSON from LLM response: {content_preview}...")
            return None
        
        # Validate expected keys if provided
        if expected_keys:
            missing_keys = [key for key in expected_keys if key not in parsed_json]
            if missing_keys:
                logger.warning(f"Missing expected keys in JSON response: {missing_keys}")
        
        # Add metadata from the original response
        parsed_json['_llm_metadata'] = {
            'model': response.get('model'),
            'attempts': response.get('attempts'),
            'usage': response.get('usage', {})
        }
        
        return parsed_json
    
    def _extract_and_parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Extract and parse JSON from LLM response content.
        Handles various formats including markdown code blocks.
        
        Args:
            content: The raw content from LLM response
            
        Returns:
            Parsed JSON dictionary or None if parsing failed
        """
        if not content:
            return None
        
        # Try to find JSON in the content
        json_candidates = []
        
        # Method 1: Look for JSON in code blocks
        import re
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        code_blocks = re.findall(code_block_pattern, content, re.DOTALL | re.IGNORECASE)
        json_candidates.extend(code_blocks)
        
        # Method 1b: More aggressive code block extraction for nested JSON
        code_block_pattern_nested = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
        code_blocks_nested = re.findall(code_block_pattern_nested, content, re.IGNORECASE)
        json_candidates.extend(code_blocks_nested)
        
        # Method 2: Look for JSON objects in the content
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        json_objects = re.findall(json_pattern, content, re.DOTALL)
        json_candidates.extend(json_objects)
        
        # Method 3: Try the entire content as JSON
        json_candidates.append(content.strip())
        
        # Try to parse each candidate
        for candidate in json_candidates:
            try:
                candidate = candidate.strip()
                if candidate.startswith('{') and candidate.endswith('}'):
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
            except json.JSONDecodeError:
                continue
        
        logger.error("Could not extract valid JSON from LLM response")
        return None
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """Get statistics about retry attempts."""
        # This could be expanded to track retry statistics
        return {
            'max_retries': self.max_retries,
            'base_delay': self.base_delay,
            'max_delay': self.max_delay
        }

# Global instance for easy access
enhanced_llm_caller = EnhancedLLMCaller()

def call_llm_with_exponential_backoff(model: str, 
                                     messages: List[Dict[str, str]], 
                                     **kwargs) -> Optional[Dict[str, Any]]:
    """
    Convenience function for calling LLM with exponential backoff.
    
    Args:
        model: The model to use
        messages: List of message dictionaries
        **kwargs: Additional parameters for the LLM call
        
    Returns:
        LLM response or None if failed
    """
    return enhanced_llm_caller.call_llm_with_retry(model, messages, **kwargs)

def call_llm_json_with_exponential_backoff(model: str, 
                                          messages: List[Dict[str, str]], 
                                          expected_keys: Optional[List[str]] = None,
                                          **kwargs) -> Optional[Dict[str, Any]]:
    """
    Convenience function for calling LLM expecting JSON with exponential backoff.
    
    Args:
        model: The model to use
        messages: List of message dictionaries
        expected_keys: List of expected keys in the JSON response
        **kwargs: Additional parameters for the LLM call
        
    Returns:
        Parsed JSON response or None if failed
    """
    return enhanced_llm_caller.call_llm_json_with_retry(model, messages, expected_keys, **kwargs)