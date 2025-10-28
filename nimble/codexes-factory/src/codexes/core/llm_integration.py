"""
LLM Integration layer for codexes-factory using nimble-llm-caller.

This module provides backward compatibility with the existing LLM calling interface
while using the new nimble-llm-caller package under the hood.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from nimble_llm_caller import LLMContentGenerator, ConfigManager, PromptManager
from nimble_llm_caller.models.request import ResponseFormat
from nimble_llm_caller.models.response import ResponseStatus

logger = logging.getLogger(__name__)


class CodexesLLMIntegration:
    """Integration wrapper for nimble-llm-caller in codexes-factory."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the LLM integration.
        
        Args:
            config_path: Path to LLM configuration file
        """
        # Use default config path if not provided
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "..", 
                "config", 
                "llm_config.json"
            )
        
        # Initialize nimble-llm-caller components
        try:
            self.config_manager = ConfigManager(config_path)
            
            # Set up prompts file path
            prompts_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "prompts",
                "codexes_prompts.json"
            )
            
            self.content_generator = LLMContentGenerator(
                prompt_file_path=prompts_path if os.path.exists(prompts_path) else None,
                default_model=self._get_default_model(),
                output_dir=self.config_manager.output_config.output_directory
            )
            
            logger.info("CodexesLLMIntegration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CodexesLLMIntegration: {e}")
            # Fall back to basic configuration
            self.config_manager = ConfigManager()
            self.content_generator = LLMContentGenerator()
    
    def _get_default_model(self) -> str:
        """Get the default model from configuration."""
        # Always default to gemini/gemini-2.5-flash
        return "gemini/gemini-2.5-flash"

    def _detect_markdown_request(self, messages: List[Dict[str, str]]) -> bool:
        """
        Detect if the prompt is requesting markdown-formatted output.

        Args:
            messages: List of message dicts with role and content

        Returns:
            True if markdown output is likely requested
        """
        # Check for markdown indicators in prompt content
        markdown_indicators = [
            'markdown',
            '###',
            '##',
            '# ',
            'format your response',
            'format as markdown',
            'markdown-formatted',
            'with the following sections',
            'section heading'
        ]

        for message in messages:
            content = message.get('content', '').lower()
            if any(indicator in content for indicator in markdown_indicators):
                return True

        return False

    def _enhance_messages_for_markdown(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Add markdown formatting requirements to system message.

        Args:
            messages: Original list of messages

        Returns:
            Enhanced messages with markdown formatting requirements
        """
        MARKDOWN_FORMATTING_REQUIREMENTS = """

**CRITICAL MARKDOWN FORMATTING REQUIREMENTS:**
- Each heading (#, ##, ###) MUST be on its own line
- There MUST be a blank line (two newlines) after EVERY heading before body text begins
- Paragraphs MUST be separated by blank lines
- Do NOT merge headings and body text on the same line

Example correct format:
### Section Heading

First paragraph of body text here.

Second paragraph here.

Example INCORRECT format:
### Section Heading This is wrong because text immediately follows heading."""

        enhanced_messages = []
        system_message_found = False

        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')

            # Enhance the first system message, or add one if none exists
            if role == 'system' and not system_message_found:
                enhanced_content = content + MARKDOWN_FORMATTING_REQUIREMENTS
                enhanced_messages.append({'role': 'system', 'content': enhanced_content})
                system_message_found = True
            else:
                enhanced_messages.append(message)

        # If no system message found, add one at the beginning
        if not system_message_found:
            enhanced_messages.insert(0, {
                'role': 'system',
                'content': f"You are a helpful assistant.{MARKDOWN_FORMATTING_REQUIREMENTS}"
            })

        return enhanced_messages
    
    def call_model_with_prompt(
        self,
        model_name: str,
        prompt_config: Dict[str, Any],
        response_format_type: str = "text",
        max_retries: int = 3,
        initial_delay: int = 5,
        backoff_multiplier: float = 2.0,
        max_delay: int = 60,
        ensure_min_tokens: bool = True,
        min_tokens: int = 8192
    ) -> Dict[str, Any]:
        """
        Backward compatibility wrapper for single model calls.
        
        This maintains the exact same interface as the original function
        but uses nimble-llm-caller under the hood.
        """
        try:
            # Convert old format to new format
            messages = prompt_config.get("messages", [])
            model_params = prompt_config.get("params", {}).copy()

            # Detect and enhance markdown requests automatically
            if self._detect_markdown_request(messages):
                messages = self._enhance_messages_for_markdown(messages)
                logger.debug("Enhanced messages with markdown formatting requirements")

            # Handle ensure_min_tokens
            if ensure_min_tokens:
                current_max_tokens = model_params.get('max_tokens', 0)
                if current_max_tokens < min_tokens:
                    model_params['max_tokens'] = min_tokens
            
            # Determine response format
            response_format = ResponseFormat.JSON if response_format_type == "json_object" else ResponseFormat.TEXT

            # Log the format conversion for debugging
            logger.debug(f"Converting response_format_type '{response_format_type}' to {response_format}")

            # Create a temporary prompt key for this call
            temp_prompt_key = f"temp_prompt_{hash(str(messages))}"

            # Use content generator with direct message passing
            from nimble_llm_caller.models.request import LLMRequest

            request = LLMRequest(
                prompt_key=temp_prompt_key,
                model=model_name,
                response_format=response_format,
                model_params=model_params,
                metadata={"messages": messages}
            )

            logger.debug(f"Created LLMRequest with response_format: {request.response_format} (type: {type(request.response_format)})")
            
            response = self.content_generator.llm_caller.call(request)
            
            # Convert response back to old format
            if response.status == ResponseStatus.SUCCESS:
                return {
                    "parsed_content": response.parsed_content,
                    "raw_content": response.content
                }
            else:
                return {
                    "parsed_content": {"error": response.error_message or "Unknown error"},
                    "raw_content": response.error_message or "Unknown error"
                }
                
        except Exception as e:
            logger.error(f"Error in call_model_with_prompt: {e}")
            return {
                "parsed_content": {"error": f"Integration error: {str(e)}"},
                "raw_content": f"Integration error: {str(e)}"
            }
    
    def get_responses_from_multiple_models(
        self,
        prompt_configs: List[Dict[str, Any]],
        models: List[str],
        response_format_type: str = "text",
        per_model_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Backward compatibility wrapper for multiple model calls.
        
        This maintains the exact same interface as the original function
        but uses nimble-llm-caller batch processing under the hood.
        """
        try:
            all_responses: Dict[str, List[Dict[str, Any]]] = {}
            
            # Process each prompt configuration
            for i, config_wrapper in enumerate(prompt_configs):
                prompt_config = config_wrapper.get("prompt_config", {})
                prompt_key = config_wrapper.get("key", f"temp_prompt_{i}")

                # Determine which model to use
                model_to_use = prompt_config.get("params", {}).get("model")
                if not model_to_use:
                    model_to_use = models[0] if models else self._get_default_model()

                # Initialize response list for this model
                if model_to_use not in all_responses:
                    all_responses[model_to_use] = []

                # Merge per-model parameters if provided
                final_prompt_config = prompt_config.copy()
                if per_model_params and model_to_use in per_model_params:
                    final_prompt_config.setdefault("params", {}).update(
                        per_model_params[model_to_use]
                    )

                # Determine response format - use per-prompt override if available, else use global
                prompt_response_format = prompt_config.get("response_format", response_format_type)

                # Make the call using the single model function
                response_data = self.call_model_with_prompt(
                    model_name=model_to_use,
                    prompt_config=final_prompt_config,
                    response_format_type=prompt_response_format
                )
                
                # Add prompt key to response
                response_data['prompt_key'] = prompt_key
                
                # Add to responses
                all_responses[model_to_use].append(response_data)
            
            return all_responses
            
        except Exception as e:
            logger.error(f"Error in get_responses_from_multiple_models: {e}")
            # Return error response in expected format
            error_response = {
                "parsed_content": {"error": f"Integration error: {str(e)}"},
                "raw_content": f"Integration error: {str(e)}",
                "prompt_key": "error"
            }
            
            # Return error for the first model
            first_model = models[0] if models else "unknown"
            return {first_model: [error_response]}
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the current configuration."""
        validation_results = {
            "valid": True,
            "issues": [],
            "models_available": [],
            "models_with_issues": []
        }
        
        try:
            # Check available models
            available_models = self.config_manager.list_available_models()
            validation_results["models_available"] = available_models
            
            # Validate each model
            for model_name in available_models:
                model_validation = self.config_manager.validate_model(model_name)
                if not model_validation["valid"]:
                    validation_results["valid"] = False
                    validation_results["models_with_issues"].append({
                        "model": model_name,
                        "issues": model_validation["issues"]
                    })
                    validation_results["issues"].extend([
                        f"Model {model_name}: {issue}" 
                        for issue in model_validation["issues"]
                    ])
            
            # Check prompts file
            prompts_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "prompts", 
                "codexes_prompts.json"
            )
            
            if not os.path.exists(prompts_path):
                validation_results["issues"].append(
                    f"Prompts file not found: {prompts_path}"
                )
            
        except Exception as e:
            validation_results["valid"] = False
            validation_results["issues"].append(f"Configuration validation error: {e}")
        
        return validation_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from the LLM caller."""
        try:
            return self.content_generator.get_session_statistics()
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}
    
    def list_available_models(self) -> List[str]:
        """Get list of available models."""
        try:
            return self.config_manager.list_available_models()
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def call_llm(
        self,
        prompt: str,
        model: str = "gemini/gemini-2.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Simple LLM calling method for backward compatibility.
        
        Args:
            prompt: The prompt text to send to the LLM
            model: Model name (optional, uses default if not provided)
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters
            
        Returns:
            The LLM response as a string
        """
        try:
            # Use default model if not provided
            if model is None:
                model = self._get_default_model()
            
            # Create prompt config in the expected format
            prompt_config = {
                "messages": [{"role": "user", "content": prompt}],
                "params": {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
            }
            
            # Call the existing method
            response = self.call_model_with_prompt(
                model_name=model,
                prompt_config=prompt_config,
                response_format_type="text"
            )
            
            # Extract the text response
            if isinstance(response, dict):
                return response.get("raw_content", "") or response.get("parsed_content", "")
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Error in call_llm: {e}")
            return f"Error: {str(e)}"


# Backward compatibility alias
LLMCaller = CodexesLLMIntegration

# Global instance for backward compatibility
_global_integration = None


def get_llm_integration() -> CodexesLLMIntegration:
    """Get the global LLM integration instance."""
    global _global_integration
    if _global_integration is None:
        _global_integration = CodexesLLMIntegration()
    return _global_integration


# Backward compatibility functions that maintain the original API
def call_model_with_prompt(
    model_name: str,
    prompt_config: Dict[str, Any],
    response_format_type: str = "text",
    max_retries: int = 3,
    initial_delay: int = 5,
    backoff_multiplier: float = 2.0,
    max_delay: int = 60,
    ensure_min_tokens: bool = True,
    min_tokens: int = 8192
) -> Dict[str, Any]:
    """
    Backward compatibility function for single model calls.
    
    This function maintains the exact same signature as the original
    but uses the new nimble-llm-caller integration.
    """
    integration = get_llm_integration()
    return integration.call_model_with_prompt(
        model_name=model_name,
        prompt_config=prompt_config,
        response_format_type=response_format_type,
        max_retries=max_retries,
        initial_delay=initial_delay,
        backoff_multiplier=backoff_multiplier,
        max_delay=max_delay,
        ensure_min_tokens=ensure_min_tokens,
        min_tokens=min_tokens
    )


def get_responses_from_multiple_models(
    prompt_configs: List[Dict[str, Any]],
    models: List[str],
    response_format_type: str = "text",
    per_model_params: Optional[Dict[str, Any]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Backward compatibility function for multiple model calls.
    
    This function maintains the exact same signature as the original
    but uses the new nimble-llm-caller integration.
    """
    integration = get_llm_integration()
    return integration.get_responses_from_multiple_models(
        prompt_configs=prompt_configs,
        models=models,
        response_format_type=response_format_type,
        per_model_params=per_model_params
    )


def call_llm_simple(
    prompt: str,
    model: str = "gemini/gemini-2.0-flash-exp",
    max_tokens: int = 4096,
    temperature: float = 0.7
) -> str:
    """
    Simple helper function for one-off LLM calls with a text prompt.

    Args:
        prompt: Text prompt to send to the model
        model: Model name (default: gemini-2.0-flash-exp)
        max_tokens: Maximum tokens in response
        temperature: Temperature for generation

    Returns:
        Model response as text
    """
    prompt_config = {
        "messages": [{"role": "user", "content": prompt}],
        "params": {
            "max_tokens": max_tokens,
            "temperature": temperature
        }
    }

    try:
        result = call_model_with_prompt(
            model_name=model,
            prompt_config=prompt_config,
            response_format_type="text"
        )
        return result.get("content", "")
    except Exception as e:
        logger.error(f"call_llm_simple failed: {e}")
        raise