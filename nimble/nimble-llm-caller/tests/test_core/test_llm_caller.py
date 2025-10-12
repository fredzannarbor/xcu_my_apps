"""
Tests for the core LLM caller functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from nimble_llm_caller.core.llm_caller import LLMCaller
from nimble_llm_caller.models.request import LLMRequest, ResponseFormat
from nimble_llm_caller.models.response import LLMResponse, ResponseStatus
from nimble_llm_caller.utils.retry_strategy import RetryStrategy


class TestLLMCaller:
    """Test cases for LLMCaller class."""
    
    def test_initialization(self):
        """Test LLMCaller initialization."""
        caller = LLMCaller()
        
        assert caller.retry_strategy is not None
        assert caller.json_parser is not None
        assert caller.default_model_params == {}
        assert caller.stats["total_calls"] == 0
    
    def test_initialization_with_params(self):
        """Test LLMCaller initialization with custom parameters."""
        retry_strategy = RetryStrategy(max_retries=5)
        default_params = {"temperature": 0.5}
        
        caller = LLMCaller(
            retry_strategy=retry_strategy,
            default_model_params=default_params
        )
        
        assert caller.retry_strategy.max_retries == 5
        assert caller.default_model_params == default_params
    
    @patch('nimble_llm_caller.core.llm_caller.litellm.completion')
    def test_successful_call(self, mock_completion, sample_llm_request, mock_litellm_response):
        """Test successful LLM call."""
        mock_completion.return_value = mock_litellm_response
        
        caller = LLMCaller()
        response = caller.call(sample_llm_request)
        
        assert response.status == ResponseStatus.SUCCESS
        assert response.content == "Test response content"
        assert response.model == sample_llm_request.model
        assert response.prompt_key == sample_llm_request.prompt_key
        assert response.execution_time > 0
        assert caller.stats["successful_calls"] == 1
        assert caller.stats["total_calls"] == 1
    
    @patch('nimble_llm_caller.core.llm_caller.litellm.completion')
    def test_failed_call(self, mock_completion, sample_llm_request):
        """Test failed LLM call."""
        mock_completion.side_effect = Exception("API Error")
        
        caller = LLMCaller()
        response = caller.call(sample_llm_request)
        
        assert response.status == ResponseStatus.ERROR
        assert "API Error" in response.error_message
        assert response.content is None
        assert caller.stats["failed_calls"] == 1
        assert caller.stats["total_calls"] == 1
    
    def test_extract_messages_from_request(self, sample_llm_request):
        """Test message extraction from request."""
        caller = LLMCaller()
        
        # Test with messages in metadata
        sample_llm_request.metadata = {
            "messages": [{"role": "user", "content": "Test message"}]
        }
        
        messages = caller._extract_messages_from_request(sample_llm_request)
        assert len(messages) == 1
        assert messages[0]["content"] == "Test message"
        
        # Test fallback
        sample_llm_request.metadata = {"content": "Fallback content"}
        messages = caller._extract_messages_from_request(sample_llm_request)
        assert len(messages) == 1
        assert "Fallback content" in messages[0]["content"]
    
    def test_prepare_model_params(self, sample_llm_request):
        """Test model parameter preparation."""
        default_params = {"temperature": 0.5, "max_tokens": 1000}
        caller = LLMCaller(default_model_params=default_params)
        
        sample_llm_request.model_params = {"temperature": 0.8}
        
        params = caller._prepare_model_params(sample_llm_request)
        
        assert params["temperature"] == 0.8  # Request params override defaults
        assert params["max_tokens"] == 1000  # Default param preserved
        assert "model" not in params  # Model should be removed
    
    def test_prepare_model_params_json_format(self, sample_llm_request):
        """Test model parameter preparation for JSON format."""
        caller = LLMCaller()
        sample_llm_request.response_format = ResponseFormat.JSON
        
        params = caller._prepare_model_params(sample_llm_request)
        
        assert params["max_tokens"] >= 4096  # Should set minimum for JSON
    
    @patch('nimble_llm_caller.core.llm_caller.litellm.completion')
    def test_make_litellm_call(self, mock_completion, mock_litellm_response):
        """Test the actual LiteLLM call."""
        mock_completion.return_value = mock_litellm_response
        
        caller = LLMCaller()
        messages = [{"role": "user", "content": "Test"}]
        params = {"temperature": 0.7}
        
        result = caller._make_litellm_call("gpt-4o", messages, params)
        
        assert result["content"] == "Test response content"
        assert result["model"] == "gpt-4o"
        assert "usage" in result
        
        mock_completion.assert_called_once_with(
            model="gpt-4o",
            messages=messages,
            **params
        )
    
    @patch('nimble_llm_caller.core.llm_caller.litellm.completion')
    def test_make_litellm_call_no_content(self, mock_completion):
        """Test LiteLLM call with no content in response."""
        mock_response = Mock()
        mock_response.choices = []
        mock_response.usage = None
        mock_response.model = "gpt-4o"
        mock_completion.return_value = mock_response
        
        caller = LLMCaller()
        result = caller._make_litellm_call("gpt-4o", [], {})
        
        assert result["content"] == ""
        assert result["model"] == "gpt-4o"
    
    def test_parse_response_content_text(self):
        """Test parsing text response content."""
        caller = LLMCaller()
        
        content = "  This is a test response.  "
        result = caller._parse_response_content(content, ResponseFormat.TEXT)
        
        assert result == "This is a test response."
    
    def test_parse_response_content_json(self):
        """Test parsing JSON response content."""
        caller = LLMCaller()
        
        content = '{"key": "value"}'
        result = caller._parse_response_content(content, ResponseFormat.JSON)
        
        assert isinstance(result, dict)
        assert result["key"] == "value"
    
    def test_parse_response_content_empty(self):
        """Test parsing empty response content."""
        caller = LLMCaller()
        
        result = caller._parse_response_content("", ResponseFormat.TEXT)
        assert result is None
        
        result = caller._parse_response_content(None, ResponseFormat.TEXT)
        assert result is None
    
    def test_validate_response_success(self, sample_llm_response):
        """Test response validation for successful response."""
        caller = LLMCaller()
        
        validation = caller.validate_response(sample_llm_response)
        
        assert validation["valid"] is True
        assert len(validation["issues"]) == 0
    
    def test_validate_response_failure(self):
        """Test response validation for failed response."""
        caller = LLMCaller()
        
        failed_response = LLMResponse(
            prompt_key="test",
            model="gpt-4o",
            status=ResponseStatus.ERROR,
            error_message="Test error"
        )
        
        validation = caller.validate_response(failed_response)
        
        assert validation["valid"] is False
        assert len(validation["issues"]) > 0
    
    def test_validate_response_required_keys(self):
        """Test response validation with required keys."""
        caller = LLMCaller()
        
        response = LLMResponse(
            prompt_key="test",
            model="gpt-4o",
            status=ResponseStatus.SUCCESS,
            content="test",
            parsed_content={"title": "Test"}
        )
        
        # Should pass with existing key
        validation = caller.validate_response(response, required_keys=["title"])
        assert validation["valid"] is True
        
        # Should fail with missing key
        validation = caller.validate_response(response, required_keys=["missing_key"])
        assert validation["valid"] is False
        assert "Missing required keys" in validation["issues"][0]
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        caller = LLMCaller()
        
        # Initial stats
        stats = caller.get_statistics()
        assert stats["total_calls"] == 0
        assert stats["success_rate"] == 0.0
        
        # Update stats manually for testing
        caller.stats["total_calls"] = 10
        caller.stats["successful_calls"] = 8
        
        stats = caller.get_statistics()
        assert stats["total_calls"] == 10
        assert stats["successful_calls"] == 8
        assert stats["success_rate"] == 80.0
    
    def test_reset_statistics(self):
        """Test statistics reset."""
        caller = LLMCaller()
        
        # Set some stats
        caller.stats["total_calls"] = 5
        caller.stats["successful_calls"] = 3
        
        # Reset
        caller.reset_statistics()
        
        assert caller.stats["total_calls"] == 0
        assert caller.stats["successful_calls"] == 0
        assert caller.stats["failed_calls"] == 0
    
    @patch('nimble_llm_caller.core.llm_caller.litellm.completion')
    def test_call_with_retry_success_after_failure(self, mock_completion, sample_llm_request, mock_litellm_response):
        """Test successful call after initial failure."""
        # First call fails, second succeeds
        mock_completion.side_effect = [Exception("Temporary error"), mock_litellm_response]
        
        retry_strategy = RetryStrategy(max_retries=2, base_delay=0.1)
        caller = LLMCaller(retry_strategy=retry_strategy)
        
        response = caller.call(sample_llm_request)
        
        assert response.status == ResponseStatus.SUCCESS
        assert response.attempts == 2
        assert mock_completion.call_count == 2
    
    @patch('nimble_llm_caller.core.llm_caller.litellm.completion')
    def test_call_max_retries_exceeded(self, mock_completion, sample_llm_request):
        """Test call failure after max retries exceeded."""
        mock_completion.side_effect = Exception("Persistent error")
        
        retry_strategy = RetryStrategy(max_retries=2, base_delay=0.1)
        caller = LLMCaller(retry_strategy=retry_strategy)
        
        response = caller.call(sample_llm_request)
        
        assert response.status == ResponseStatus.ERROR
        assert "Persistent error" in response.error_message
        assert mock_completion.call_count == 3  # Initial + 2 retries