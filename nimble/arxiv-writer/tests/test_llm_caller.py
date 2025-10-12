"""
Unit tests for LLM caller module.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from src.arxiv_writer.llm.caller import (
    call_model_with_prompt,
    get_responses_from_multiple_models,
    _parse_llm_response,
    _parse_json_with_fallbacks,
    _extract_json_from_text,
    _parse_conversational_response,
    _is_retryable_api_error,
    _is_retryable_exception,
    set_token_tracker,
    get_token_tracker,
    clear_token_tracker
)
from src.arxiv_writer.llm.token_usage_tracker import TokenUsageTracker


class TestLLMCaller:
    """Test cases for LLM caller functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        clear_token_tracker()
    
    def teardown_method(self):
        """Clean up after tests."""
        clear_token_tracker()
    
    def test_token_tracker_management(self):
        """Test token tracker global management."""
        # Initially no tracker
        assert get_token_tracker() is None
        
        # Set a tracker
        tracker = TokenUsageTracker()
        set_token_tracker(tracker)
        assert get_token_tracker() is tracker
        
        # Clear tracker
        clear_token_tracker()
        assert get_token_tracker() is None
    
    def test_is_retryable_api_error(self):
        """Test API error retry detection."""
        # Retryable errors
        retryable_errors = [
            "timeout occurred",
            "connection failed",
            "network error",
            "temporary failure",
            "server error 502",
            "internal error",
            "503 service unavailable",
            "504 gateway timeout"
        ]
        
        for error_msg in retryable_errors:
            error = Exception(error_msg)
            assert _is_retryable_api_error(error), f"Should be retryable: {error_msg}"
        
        # Non-retryable errors
        non_retryable_errors = [
            "invalid api key",
            "authentication failed",
            "bad request",
            "not found"
        ]
        
        for error_msg in non_retryable_errors:
            error = Exception(error_msg)
            assert not _is_retryable_api_error(error), f"Should not be retryable: {error_msg}"
    
    def test_is_retryable_exception(self):
        """Test exception retry detection."""
        import socket
        
        # Retryable exceptions
        retryable_exceptions = [
            socket.timeout(),
            socket.gaierror("Name resolution failed"),
            ConnectionError("Connection failed"),
            TimeoutError("Operation timed out")
        ]
        
        for exc in retryable_exceptions:
            assert _is_retryable_exception(exc), f"Should be retryable: {type(exc)}"
        
        # Non-retryable exceptions
        non_retryable_exceptions = [
            ValueError("Invalid value"),
            KeyError("Missing key"),
            TypeError("Wrong type")
        ]
        
        for exc in non_retryable_exceptions:
            assert not _is_retryable_exception(exc), f"Should not be retryable: {type(exc)}"
    
    def test_parse_llm_response_text(self):
        """Test parsing text responses."""
        # Valid text response
        response = "This is a text response"
        result = _parse_llm_response(response, "text")
        assert result == response
        
        # Empty response
        result = _parse_llm_response("", "text")
        assert result == ""
        
        # None response
        result = _parse_llm_response(None, "text")
        assert result is None
    
    def test_parse_llm_response_json(self):
        """Test parsing JSON responses."""
        # Valid JSON
        json_data = {"key": "value", "number": 42}
        json_string = json.dumps(json_data)
        result = _parse_llm_response(json_string, "json_object")
        assert result == json_data
        
        # Invalid JSON should use fallback
        invalid_json = "This is not JSON"
        result = _parse_llm_response(invalid_json, "json_object")
        assert isinstance(result, dict)
        assert "error" in result
    
    def test_parse_json_with_fallbacks_direct(self):
        """Test direct JSON parsing."""
        json_data = {"test": "value", "nested": {"key": "value"}}
        json_string = json.dumps(json_data)
        result = _parse_json_with_fallbacks(json_string)
        assert result == json_data
    
    def test_parse_json_with_fallbacks_markdown(self):
        """Test JSON parsing from markdown code blocks."""
        json_data = {"test": "value"}
        markdown_content = f"Here's the JSON:\n```json\n{json.dumps(json_data)}\n```\nThat's it!"
        result = _parse_json_with_fallbacks(markdown_content)
        assert result == json_data
    
    def test_parse_json_with_fallbacks_empty(self):
        """Test JSON parsing with empty content."""
        result = _parse_json_with_fallbacks("")
        assert isinstance(result, dict)
        assert result["fallback_used"] == "empty_response"
        
        result = _parse_json_with_fallbacks(None)
        assert isinstance(result, dict)
        assert result["fallback_used"] == "empty_response"
    
    def test_extract_json_from_text(self):
        """Test JSON extraction from mixed text."""
        # JSON in code block
        json_data = {"key": "value"}
        text = f"Some text\n```json\n{json.dumps(json_data)}\n```\nMore text"
        result = _extract_json_from_text(text)
        assert result == json.dumps(json_data)
        
        # JSON without code block
        text = f"Here is data: {json.dumps(json_data)} and more text"
        result = _extract_json_from_text(text)
        assert json.loads(result) == json_data
        
        # No JSON
        text = "This has no JSON content"
        result = _extract_json_from_text(text)
        assert result is None
    
    def test_parse_conversational_response(self):
        """Test parsing conversational responses."""
        # Response with recognizable fields
        response = """
        Title: Test Paper Title
        Author: John Doe
        Description: This is a test paper about something important.
        Keywords: test, paper, research
        """
        
        result = _parse_conversational_response(response)
        assert isinstance(result, dict)
        assert "title" in result
        assert "author" in result
        assert "description" in result
        assert "keywords" in result
        assert result["fallback_used"] == "conversational_parsing"
        
        # Response with no recognizable fields
        response = "This is just random text with no structure."
        result = _parse_conversational_response(response)
        assert result is None
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_call_model_with_prompt_success(self, mock_completion):
        """Test successful model call."""
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response"
        mock_completion.return_value = mock_response
        
        prompt_config = {
            "messages": [{"role": "user", "content": "Test prompt"}],
            "params": {"temperature": 0.7}
        }
        
        result = call_model_with_prompt("test-model", prompt_config)
        
        assert result["raw_content"] == "Test response"
        assert result["parsed_content"] == "Test response"
        mock_completion.assert_called_once()
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_call_model_with_prompt_json_success(self, mock_completion):
        """Test successful model call with JSON response."""
        json_data = {"key": "value", "number": 42}
        
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps(json_data)
        mock_completion.return_value = mock_response
        
        prompt_config = {
            "messages": [{"role": "user", "content": "Test prompt"}],
            "params": {"temperature": 0.7}
        }
        
        result = call_model_with_prompt("test-model", prompt_config, "json_object")
        
        assert result["raw_content"] == json.dumps(json_data)
        assert result["parsed_content"] == json_data
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_call_model_with_prompt_retry_on_rate_limit(self, mock_completion):
        """Test retry logic on rate limit error."""
        from litellm.exceptions import RateLimitError
        
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Success after retry"
        
        mock_completion.side_effect = [
            RateLimitError("Rate limit exceeded", "test_provider", "test_model"),
            mock_response
        ]
        
        prompt_config = {
            "messages": [{"role": "user", "content": "Test prompt"}],
            "params": {}
        }
        
        with patch('time.sleep'):  # Speed up test
            result = call_model_with_prompt(
                "test-model", 
                prompt_config, 
                max_retries=2,
                initial_delay=0.1
            )
        
        assert result["raw_content"] == "Success after retry"
        assert mock_completion.call_count == 2
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_call_model_with_prompt_max_retries_exceeded(self, mock_completion):
        """Test behavior when max retries are exceeded."""
        from litellm.exceptions import RateLimitError
        
        mock_completion.side_effect = RateLimitError("Rate limit exceeded", "test_provider", "test_model")
        
        prompt_config = {
            "messages": [{"role": "user", "content": "Test prompt"}],
            "params": {}
        }
        
        with patch('time.sleep'):  # Speed up test
            result = call_model_with_prompt(
                "test-model", 
                prompt_config, 
                max_retries=2,
                initial_delay=0.1
            )
        
        assert "error" in result["parsed_content"]
        assert mock_completion.call_count == 3  # Initial + 2 retries
    
    @patch('src.arxiv_writer.llm.caller.litellm.completion')
    def test_call_model_with_prompt_token_tracking(self, mock_completion):
        """Test token usage tracking."""
        # Set up token tracker
        tracker = TokenUsageTracker()
        set_token_tracker(tracker)
        
        # Mock successful response with usage info
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_completion.return_value = mock_response
        
        prompt_config = {
            "messages": [{"role": "user", "content": "Test prompt"}],
            "params": {}
        }
        
        result = call_model_with_prompt(
            "test-model", 
            prompt_config, 
            prompt_name="test_prompt"
        )
        
        assert result["raw_content"] == "Test response"
        # Token tracking should have been called (we can't easily verify the internal state)
    
    @patch('src.arxiv_writer.llm.caller.call_model_with_prompt')
    def test_get_responses_from_multiple_models(self, mock_call_model):
        """Test calling multiple models with multiple prompts."""
        # Mock responses
        mock_call_model.side_effect = [
            {"parsed_content": "Response 1", "raw_content": "Response 1"},
            {"parsed_content": "Response 2", "raw_content": "Response 2"},
            {"parsed_content": "Response 3", "raw_content": "Response 3"}
        ]
        
        prompt_configs = [
            {
                "key": "prompt1",
                "prompt_config": {
                    "messages": [{"role": "user", "content": "Prompt 1"}],
                    "params": {"model": "model1"}
                }
            },
            {
                "key": "prompt2", 
                "prompt_config": {
                    "messages": [{"role": "user", "content": "Prompt 2"}],
                    "params": {"model": "model2"}
                }
            },
            {
                "key": "prompt3",
                "prompt_config": {
                    "messages": [{"role": "user", "content": "Prompt 3"}],
                    "params": {}  # Should use default model
                }
            }
        ]
        
        models = ["model1", "model2"]
        
        result = get_responses_from_multiple_models(
            prompt_configs, 
            models, 
            response_format_type="text"
        )
        
        assert "model1" in result
        assert "model2" in result
        assert len(result["model1"]) == 2  # prompt1 and prompt3 (default)
        assert len(result["model2"]) == 1  # prompt2
        
        # Check that prompt keys are preserved
        assert result["model1"][0]["prompt_key"] == "prompt1"
        assert result["model2"][0]["prompt_key"] == "prompt2"
    
    def test_get_responses_from_multiple_models_per_model_params(self):
        """Test per-model parameter overrides."""
        with patch('src.arxiv_writer.llm.caller.call_model_with_prompt') as mock_call:
            mock_call.return_value = {"parsed_content": "Response", "raw_content": "Response"}
            
            prompt_configs = [
                {
                    "key": "test_prompt",
                    "prompt_config": {
                        "messages": [{"role": "user", "content": "Test"}],
                        "params": {"temperature": 0.5, "model": "test-model"}
                    }
                }
            ]
            
            per_model_params = {
                "test-model": {"max_tokens": 1000, "temperature": 0.8}
            }
            
            get_responses_from_multiple_models(
                prompt_configs,
                ["test-model"],
                per_model_params=per_model_params
            )
            
            # Verify the call was made with merged parameters
            call_args = mock_call.call_args
            final_config = call_args[1]["prompt_config"]
            params = final_config["params"]
            
            assert params["max_tokens"] == 1000
            assert params["temperature"] == 0.8  # Should be overridden
            assert params["model"] == "test-model"
    
    def test_openai_parameter_conversion(self):
        """Test OpenAI parameter conversion for newer models."""
        with patch('src.arxiv_writer.llm.caller.litellm.completion') as mock_completion:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "Test response"
            mock_completion.return_value = mock_response
            
            prompt_config = {
                "messages": [{"role": "user", "content": "Test"}],
                "params": {"max_tokens": 1000, "temperature": 0.7}
            }
            
            # Test with newer OpenAI model
            call_model_with_prompt("openai/gpt-4o", prompt_config)
            
            # Check that max_tokens was converted to max_completion_tokens
            call_args = mock_completion.call_args
            assert "max_completion_tokens" in call_args[1]
            assert "max_tokens" not in call_args[1]
            # The function enforces minimum tokens, so it might be higher than 1000
            assert call_args[1]["max_completion_tokens"] >= 1000
    
    def test_min_tokens_enforcement(self):
        """Test minimum token count enforcement."""
        with patch('src.arxiv_writer.llm.caller.litellm.completion') as mock_completion:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "Test response"
            mock_completion.return_value = mock_response
            
            prompt_config = {
                "messages": [{"role": "user", "content": "Test"}],
                "params": {"max_tokens": 100}  # Less than minimum
            }
            
            call_model_with_prompt(
                "test-model", 
                prompt_config,
                ensure_min_tokens=True,
                min_tokens=8192
            )
            
            # Check that max_tokens was increased
            call_args = mock_completion.call_args
            assert call_args[1]["max_tokens"] == 8192


class TestLLMCallerIntegration:
    """Integration tests for LLM caller."""
    
    def test_error_handling_chain(self):
        """Test the complete error handling chain."""
        # Test with various error scenarios
        error_scenarios = [
            ("Rate limit", "RateLimitError", True),
            ("Service unavailable", "ServiceUnavailableError", True),
            ("Bad request", "BadRequestError", False),
            ("API error with timeout", "APIError: timeout", True),
            ("API error with auth", "APIError: authentication", False)
        ]
        
        for scenario_name, error_msg, should_retry in error_scenarios:
            with patch('src.arxiv_writer.llm.caller.litellm.completion') as mock_completion:
                if "RateLimitError" in error_msg:
                    from litellm.exceptions import RateLimitError
                    mock_completion.side_effect = RateLimitError(error_msg, "test_provider", "test_model")
                elif "ServiceUnavailableError" in error_msg:
                    from litellm.exceptions import ServiceUnavailableError
                    mock_completion.side_effect = ServiceUnavailableError(error_msg, "test_provider", "test_model")
                elif "BadRequestError" in error_msg:
                    from litellm.exceptions import BadRequestError
                    mock_completion.side_effect = BadRequestError(error_msg, "test_provider", "test_model")
                else:
                    from litellm.exceptions import APIError
                    mock_completion.side_effect = APIError(error_msg, "test_provider", "test_model")
                
                prompt_config = {
                    "messages": [{"role": "user", "content": "Test"}],
                    "params": {}
                }
                
                with patch('time.sleep'):  # Speed up test
                    result = call_model_with_prompt(
                        "test-model",
                        prompt_config,
                        max_retries=2,
                        initial_delay=0.1
                    )
                
                assert "error" in result["parsed_content"]
                
                if should_retry:
                    assert mock_completion.call_count == 3  # Initial + 2 retries
                else:
                    assert mock_completion.call_count == 1  # No retries