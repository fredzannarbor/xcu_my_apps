# src/codexes/core/llm_caller.py

import logging
import json
import time
from typing import List, Dict, Any, Optional

import litellm
from litellm.exceptions import APIError, RateLimitError, ServiceUnavailableError, BadRequestError

# Configure LiteLLM
litellm.telemetry = False
litellm.set_verbose = False

logger = logging.getLogger(__name__)

try:
    from json_repair import repair_json
except ImportError:
    # Fallback if json_repair is not available
    def repair_json(json_str):
        return json_str
from .token_usage_tracker import TokenUsageTracker

# Global token usage tracker instance
_global_token_tracker: Optional[TokenUsageTracker] = None


def set_token_tracker(tracker: TokenUsageTracker) -> None:
    """
    Set the global token usage tracker.
    
    Args:
        tracker: TokenUsageTracker instance to use for tracking
    """
    global _global_token_tracker
    _global_token_tracker = tracker
    logger.debug("Global token tracker set")


def get_token_tracker() -> Optional[TokenUsageTracker]:
    """
    Get the current global token usage tracker.
    
    Returns:
        Current TokenUsageTracker instance or None if not set
    """
    return _global_token_tracker


def clear_token_tracker() -> None:
    """Clear the global token usage tracker."""
    global _global_token_tracker
    _global_token_tracker = None
    logger.debug("Global token tracker cleared")


def _is_retryable_api_error(error) -> bool:
    """
    Determine if an API error is retryable.
    
    Args:
        error: The API error to check
        
    Returns:
        True if the error should be retried
    """
    error_str = str(error).lower()
    retryable_patterns = [
        'timeout',
        'connection',
        'network',
        'temporary',
        'server error',
        'internal error',
        '502',
        '503',
        '504'
    ]
    return any(pattern in error_str for pattern in retryable_patterns)


def _is_retryable_exception(error) -> bool:
    """
    Determine if a general exception is retryable.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the exception should be retried
    """
    import socket
    import requests
    
    # Network-related exceptions that should be retried
    retryable_exceptions = (
        socket.timeout,
        socket.gaierror,
        ConnectionError,
        TimeoutError,
    )
    
    # Check if it's a requests exception
    if hasattr(requests, 'exceptions'):
        retryable_exceptions += (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
        )
    
    return isinstance(error, retryable_exceptions)


def _parse_llm_response(response_content: str, response_format_type: str) -> Any:
    """
    Parses the string response from an LLM into the desired format (e.g., JSON).
    This function is designed to be robust against common LLM output issues,
    like prepended/appended text or markdown code fences.
    """
    # Validate response content before parsing
    if response_content is None:
        logger.error("Response content is None - LLM returned no content")
        return None
    
    if not isinstance(response_content, str):
        logger.warning(f"Response content is not a string: {type(response_content)}")
        response_content = str(response_content) if response_content else ""
    
    if not response_content.strip():
        logger.error("Response content is empty or whitespace only")
        return ""
    
    logger.debug(f"Parsing response content: {len(response_content)} characters")
    
    if response_format_type == "json_object":
        return _parse_json_with_fallbacks(response_content)
    # If not expecting JSON, return the raw content.
    return response_content


def _parse_json_with_fallbacks(response_content: str) -> Dict[str, Any]:
    """
    Robust JSON parsing with multiple fallback strategies for LLM responses.
    """
    if not response_content or not response_content.strip():
        logger.error("Empty response content received")
        return {"error": "Empty response", "fallback_used": "empty_response"}
    
    # Strategy 1: Direct JSON parsing
    try:
        return json.loads(response_content)
    except (json.JSONDecodeError, ValueError):
        logger.debug("Direct JSON parsing failed, trying repair...")
    
    # Strategy 2: JSON repair
    try:
        repaired = repair_json(response_content)
        return json.loads(repaired)
    except (json.JSONDecodeError, ValueError):
        logger.debug("JSON repair failed, trying extraction...")
    
    # Strategy 3: Extract JSON from markdown or mixed content
    try:
        extracted_json = _extract_json_from_text(response_content)
        if extracted_json:
            return json.loads(extracted_json)
    except (json.JSONDecodeError, ValueError):
        logger.debug("JSON extraction failed, trying conversational parsing...")
    
    # Strategy 4: Parse conversational responses
    try:
        parsed = _parse_conversational_response(response_content)
        if parsed:
            return parsed
    except Exception:
        logger.debug("Conversational parsing failed, using final fallback...")
    
    # Final fallback: Return error with context
    logger.error(f"All JSON parsing strategies failed. Raw content: {response_content[:500]}...")
    return {
        "error": "JSON parsing failed after all strategies",
        "raw_content": response_content[:1000],  # Truncate for logging
        "fallback_used": "error_response"
    }


def _extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON from text that may contain markdown code blocks or other content.
    """
    import re
    
    # Remove markdown code blocks
    text = re.sub(r'```json\s*\n?', '', text)
    text = re.sub(r'```\s*\n?', '', text)
    
    # Find JSON-like content between braces
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    if matches:
        # Return the largest match (most likely to be complete JSON)
        return max(matches, key=len)
    
    return None


def _parse_conversational_response(response_content: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to parse useful information from conversational responses.
    This handles cases where the LLM returns explanatory text instead of JSON.
    """
    import re
    
    # Common patterns for different field types
    patterns = {
        'bibliography': r'(?:bibliography|sources?|references?):\s*(.+?)(?:\n\n|\Z)',
        'back_cover_text': r'(?:back cover|cover text):\s*(.+?)(?:\n\n|\Z)',
        'keywords': r'(?:keywords?|tags?):\s*(.+?)(?:\n\n|\Z)',
        'description': r'(?:description|summary):\s*(.+?)(?:\n\n|\Z)',
        'title': r'(?:title):\s*(.+?)(?:\n|\Z)',
        'author': r'(?:author):\s*(.+?)(?:\n|\Z)'
    }
    
    result = {}
    response_lower = response_content.lower()
    
    for field, pattern in patterns.items():
        match = re.search(pattern, response_lower, re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            # Clean up the extracted value
            value = re.sub(r'\s+', ' ', value)  # Normalize whitespace
            result[field] = value
    
    # If we found any fields, return them with a fallback indicator
    if result:
        result['fallback_used'] = 'conversational_parsing'
        logger.info(f"Extracted fields from conversational response: {list(result.keys())}")
        return result
    
    return None


def call_model_with_prompt(
        model_name: str,
        prompt_config: Dict[str, Any],
        response_format_type: str = "text",
        max_retries: int = 3,
        initial_delay: int = 5,
        backoff_multiplier: float = 2.0,
        max_delay: int = 60,
        ensure_min_tokens: bool = True,
        min_tokens: int = 8192,
        prompt_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calls a single model with a given prompt configuration, with retries.
    Returns a dictionary containing both parsed and raw content.
    
    Args:
        model_name: Name of the model to call
        prompt_config: Configuration containing messages and params
        response_format_type: Expected response format ("text" or "json_object")
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay before retrying
        backoff_multiplier: Multiplier for exponential backoff
        max_delay: Maximum delay between retries
        ensure_min_tokens: Whether to ensure minimum token count
        min_tokens: Minimum token count to ensure (default 8192)
        prompt_name: Optional name/identifier for the prompt (for logging and tracking)
    """
    messages = prompt_config.get("messages", [])
    model_params = prompt_config.get("params", {}).copy()
    model_params.pop('model', None)
    
    # Ensure minimum max_tokens if requested
    if ensure_min_tokens:
        current_max_tokens = model_params.get('max_tokens', 0)
        if current_max_tokens < min_tokens:
            model_params['max_tokens'] = min_tokens
            logger.debug(f"Increased max_tokens from {current_max_tokens} to {min_tokens}")
        else:
            logger.debug(f"Keeping existing max_tokens: {current_max_tokens}")
    
    # Handle OpenAI parameter compatibility for newer models
    if model_name.startswith('openai/'):
        # For newer OpenAI models, use max_completion_tokens instead of max_tokens
        if any(model_suffix in model_name.lower() for model_suffix in ['gpt-4o', 'gpt-5', 'o1']):
            if 'max_tokens' in model_params:
                max_tokens_value = model_params.pop('max_tokens')
                model_params['max_completion_tokens'] = max_tokens_value
                logger.info(f"Converted max_tokens to max_completion_tokens for newer OpenAI model: {model_name}")
            
            # Some newer models have restricted parameter support
            if 'gpt-5' in model_name.lower():
                # gpt-5-mini only supports temperature=1 (default)
                if 'temperature' in model_params and model_params['temperature'] != 1.0:
                    logger.warning(f"Removing temperature parameter for gpt-5 series (only supports default value of 1)")
                    model_params.pop('temperature', None)
                
                # Remove other potentially unsupported parameters
                unsupported_params = ['top_p', 'frequency_penalty', 'presence_penalty']
                for param in unsupported_params:
                    if param in model_params:
                        logger.warning(f"Removing {param} parameter for gpt-5 series(not supported)")
                        model_params.pop(param, None)
    
    # Format prompt name for logging
    prompt_display = f" [{prompt_name}]" if prompt_name else ""
    
    logger.info(f"Final model params being passed to {model_name}: {model_params}")
    logger.info(f"Message content length: {len(str(messages))} characters")
    
    # Log the full message content for inspection
    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        logger.info(f"Message {i+1} (role: {role}) - First 500 chars: {content[:500]}...")
        if "quotes_per_book" in content:
            # Find the quotes_per_book value in the content
            import re
            match = re.search(r'You MUST return at least (\d+) quotations', content)
            if match:
                quotes_count = match.group(1)
                logger.info(f"FOUND quotes_per_book value in prompt: {quotes_count}")

    for attempt in range(max_retries):
        try:
            logger.info(f"Querying {model_name}{prompt_display} (Attempt {attempt + 1}/{max_retries})...")
            logger.info(f"Final parameters being sent to LiteLLM: {model_params}")
            
            # Record start time for response time tracking
            start_time = time.time()
            
            response = litellm.completion(
                model=model_name,
                messages=messages,
                **model_params
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Detailed logging for debugging
            logger.debug(f"Raw LiteLLM response object type: {type(response)}")
            logger.debug(f"Response has choices: {hasattr(response, 'choices')}")
            if hasattr(response, 'choices') and response.choices:
                logger.debug(f"Number of choices: {len(response.choices)}")
                logger.debug(f"First choice type: {type(response.choices[0])}")
                logger.debug(f"First choice has message: {hasattr(response.choices[0], 'message')}")
                if hasattr(response.choices[0], 'message'):
                    message = response.choices[0].message
                    logger.debug(f"Message type: {type(message)}")
                    logger.debug(f"Message has content: {hasattr(message, 'content')}")
                    raw_content = message.content
                    logger.debug(f"Raw content type: {type(raw_content)}")
                    logger.debug(f"Raw content is None: {raw_content is None}")
                    if raw_content:
                        logger.debug(f"Raw content length: {len(str(raw_content))}")
                        logger.debug(f"Raw content preview: {str(raw_content)[:200]}...")
                    else:
                        logger.warning(f"Raw content is None or empty for {model_name}")
                else:
                    logger.error(f"Response choice has no message attribute for {model_name}")
                    raw_content = None
            else:
                logger.error(f"Response has no choices for {model_name}")
                raw_content = None
            
            parsed_content = _parse_llm_response(raw_content, response_format_type)
            
            # Additional validation for None responses
            if parsed_content is None and raw_content is None:
                logger.error(f"Both parsed and raw content are None for {model_name} - treating as API error")
                if attempt < max_retries - 1:
                    delay = min(initial_delay * (backoff_multiplier ** attempt), max_delay)
                    logger.warning(f"Retrying due to None response in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"❌ Final attempt failed with None response for {model_name}{prompt_display}")
                    return {"parsed_content": {"error": "None response after retries"}, "raw_content": "No content received"}
            
            # Record token usage if tracker is available
            if _global_token_tracker and prompt_name:
                try:
                    _global_token_tracker.record_usage(
                        model=model_name,
                        prompt_name=prompt_name,
                        response=response,
                        response_time=response_time
                    )
                except Exception as e:
                    logger.warning(f"Failed to record token usage for {model_name}{prompt_display}: {e}")
            
            # Use log_success to ensure success messages always appear
            from .logging_filters import log_success
            log_success(logger, f"✅ Successfully received response from {model_name}{prompt_display}.")
            return {"parsed_content": parsed_content, "raw_content": raw_content}

        except (RateLimitError, ServiceUnavailableError) as e:
            delay = min(initial_delay * (backoff_multiplier ** attempt), max_delay)
            logger.warning(f"Rate limit or service unavailable error for {model_name}{prompt_display}: {e}. Retrying in {delay}s...")
            time.sleep(delay)
        except (APIError, BadRequestError) as e:
            # Check if this is a retryable API error
            if _is_retryable_api_error(e) and attempt < max_retries - 1:
                delay = min(initial_delay * (backoff_multiplier ** attempt), max_delay)
                logger.warning(f"Retryable API error for {model_name}{prompt_display}: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                logger.error(f"❌ API or Bad Request Error for {model_name}{prompt_display}: {e}", exc_info=True)
                return {"parsed_content": {"error": "API/Bad Request Error"}, "raw_content": str(e)}
        except Exception as e:
            # Check if this is a retryable exception
            if _is_retryable_exception(e) and attempt < max_retries - 1:
                delay = min(initial_delay * (backoff_multiplier ** attempt), max_delay)
                logger.warning(f"Retryable error for {model_name}{prompt_display}: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                logger.critical(f"❌ An unexpected error occurred calling {model_name}{prompt_display}: {e}", exc_info=True)
                return {"parsed_content": {"error": "Unexpected Error"}, "raw_content": str(e)}

    logger.error(f"❌ Final failure after {max_retries} retries for model {model_name}{prompt_display}.")
    return {"parsed_content": {"error": "Final failure after retries"}, "raw_content": "Max retries exceeded."}


def get_responses_from_multiple_models(
        prompt_configs: List[Dict[str, Any]],
        models: List[str],
        response_format_type: str = "text",
        per_model_params: Optional[Dict[str, Any]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Orchestrates calls to LLMs for a list of prompts, allowing for prompt-specific model overrides.
    """
    default_model = models[0] if models else None
    all_responses: Dict[str, List[Dict[str, Any]]] = {}
    logger.info("arrived at get responses")
    for i, config_wrapper in enumerate(prompt_configs):
        prompt_config = config_wrapper.get("prompt_config", {})
        prompt_key = config_wrapper.get("key", f"unknown_prompt_{i}")
        logger.info(f"Processing Prompt (Key: '{prompt_key}')")
        
        # Check if this is the quotes prompt
        if prompt_key == "imprint_quotes_prompt":
            logger.info(f"FOUND imprint_quotes_prompt - Inspecting configuration")

        model_to_use = prompt_config.get("params", {}).get("model", default_model)

        if not model_to_use:
            logger.error(f"No model specified for prompt '{prompt_key}' and no default model available. Skipping.")
            continue

        if model_to_use not in all_responses:
            all_responses[model_to_use] = []

        final_prompt_config = prompt_config.copy()
        logger.info(f"Original prompt params for '{prompt_key}': {final_prompt_config.get('params', {})}")
        if per_model_params and model_to_use in per_model_params:
            logger.info(f"Updating with per_model_params for {model_to_use}: {per_model_params[model_to_use]}")
            final_prompt_config.setdefault("params", {}).update(per_model_params[model_to_use])
        logger.info(f"Final prompt params after update for '{prompt_key}': {final_prompt_config.get('params', {})}")
        
        # Special check for quotes prompt and max_tokens
        if prompt_key == "imprint_quotes_prompt":
            max_tokens = final_prompt_config.get("params", {}).get("max_tokens", 0)
            logger.info(f"QUOTES PROMPT max_tokens value: {max_tokens}")
            if max_tokens < 60000:
                logger.warning(f"WARNING: max_tokens for quotes prompt is less than 60000: {max_tokens}")
                # Force a higher value for testing
                # Use the appropriate parameter name based on model
                if any(model_suffix in model_to_use.lower() for model_suffix in ['gpt-4o', 'gpt-5', 'o1']):
                    final_prompt_config.setdefault("params", {})["max_completion_tokens"] = 65535
                    logger.info(f"Forced max_completion_tokens to 65535 for quotes prompt (newer OpenAI model)")
                else:
                    final_prompt_config.setdefault("params", {})["max_tokens"] = 65535
                    logger.info(f"Forced max_tokens to 65535 for quotes prompt")

        logger.info(f"Request {i + 1}/{len(prompt_configs)}: Querying {model_to_use}...")
        response_data = call_model_with_prompt(
            model_name=model_to_use,
            prompt_config=final_prompt_config,
            response_format_type=response_format_type,
            prompt_name=prompt_key
        )

        response_data['prompt_key'] = prompt_key

        parsed_content = response_data.get("parsed_content", {})
        if isinstance(parsed_content, dict) and "error" in parsed_content:
            logger.error(f"❌ [{prompt_key}] Failure from {model_to_use}: {parsed_content}")
            
            # Log fallback information if available
            if "fallback_used" in parsed_content:
                logger.info(f"[{prompt_key}] Fallback strategy used: {parsed_content['fallback_used']}")
        else:
            # Use log_success to ensure success messages always appear
            from .logging_filters import log_success
            log_success(logger, f"✅ [{prompt_key}] Success from {model_to_use}.")
            
            # Log if fallback was used even for successful responses
            if isinstance(parsed_content, dict) and "fallback_used" in parsed_content:
                logger.warning(f"⚠️ [{prompt_key}] Fallback used: {parsed_content['fallback_used']}")

        all_responses[model_to_use].append(response_data)

    return all_responses
