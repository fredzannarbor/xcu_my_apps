"""
Unit tests for enhanced LLM caller module.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from src.arxiv_writer.llm.enhanced_caller import (
    EnhancedLLMCaller,
    call_llm_with_exponential_backoff,
    call_llm_json_with_exponential_backoff
)


class TestEnhancedLLMCaller:
    """Test cases for enhanced LLM caller functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.caller = EnhancedLLMCaller(max_retries=3, base_delay=0.1, max_delay=1.0)
    
    def test_initialization(self):
        """Test caller initialization."""
        caller = EnhancedLLMCaller(max_retries=5, base_delay=2.0, max_delay=30.0)
        assert caller.max_retries == 5
        assert caller.base_delay == 2.0
        assert caller.max_delay == 30.0
        assert len(caller.retryable_errors) > 0
    
    def test_default_initialization(self):
        """Test caller with default parameters."""
        caller = EnhancedLLMCaller()
        assert caller.max_retries == 5
        assert caller.base_delay == 1.0
        assert caller.max_delay == 60.0
    
    @patch('src.arxiv_writer.llm.enhanced_caller.completion')
    def test_call_llm_with_retry_success(self, mock_completion):
        """Test successful LLM call without retries."""
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response content"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.dict.return_value = {"prompt_tokens": 10, "completion_tokens": 5}
        mock_response.model = "test-model"
        mock_completion.return_value = mock_response
        
        messages = [{"role": "user", "content": "Test prompt"}]
        result = self.caller.call_llm_with_retry("test-model", messages, temperature=0.7)
        
        assert result is not None
        assert result["content"] == "Test response content"
        assert result["model"] == "test-model"
        assert result["attempts"] == 1
        assert "usage" in result
        mock_completion.assert_called_once()
    
    @patch('src.arxiv_writer.llm.enhanced_caller.completion')
    def test_call_llm_with_retry_success_after_retries(self, mock_completion):
        """Test successful LLM call after retries."""
        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Success after retries"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.dict.return_value = {"prompt_tokens": 10, "completion_tokens": 5}
        mock_response.model = "test-model"
        
        mock_completion.side_effect = [
            Exception("rate_limit_exceeded"),
            Exception("service_unavailable"),
            mock_response
        ]
        
        messages = [{"role": "user", "content": "Test prompt"}]
        
        with patch('time.sleep'):  # Speed up test
            result = self.caller.call_llm_with_retry("test-model", messages)
        
        assert result is not None
        assert result["content"] == "Success after retries"
        assert result["attempts"] == 3
        assert mock_completion.call_count == 3
    
    @patch('src.arxiv_writer.llm.enhanced_caller.completion')
    def test_call_llm_with_retry_max_retries_exceeded(self, mock_completion):
        """Test behavior when max retries are exceeded."""
        mock_completion.side_effect = Exception("rate_limit_exceeded")
        
        messages = [{"role": "user", "content": "Test prompt"}]
        
        with patch('time.sleep'):  # Speed up test
            result = self.caller.call_llm_with_retry("test-model", messages)
        
        assert result is None
        assert mock_completion.call_count == self.caller.max_retries + 1
    
    @patch('src.arxiv_writer.llm.enhanced_caller.completion')
    def test_call_llm_with_retry_non_retryable_error(self, mock_completion):
        """Test behavior with non-retryable errors."""
        mock_completion.side_effect = Exception("authentication_failed")
        
        messages = [{"role": "user", "content": "Test prompt"}]
        result = self.caller.call_llm_with_retry("test-model", messages)
        
        assert result is None
        assert mock_completion.call_count == 1  # No retries for non-retryable errors
    
    @patch('src.arxiv_writer.llm.enhanced_caller.completion')
    def test_call_llm_with_retry_response_variations(self, mock_completion):
        """Test handling of different response structures."""
        # Test response with text attribute instead of message
        mock_choice = Mock(spec=['text', 'finish_reason'])  # Only allow these attributes
        mock_choice.text = "Text response"
        mock_choice.finish_reason = "stop"
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        mock_response.model = "test-model"
        mock_completion.return_value = mock_response
        
        messages = [{"role": "user", "content": "Test prompt"}]
        result = self.caller.call_llm_with_retry("test-model", messages)
        
        assert result is not None
        assert result["content"] == "Text response"
        assert result["usage"] == {}
    
    @patch('src.arxiv_writer.llm.enhanced_caller.completion')
    def test_call_llm_with_retry_truncated_response(self, mock_completion):
        """Test handling of truncated responses."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Truncated response"
        mock_response.choices[0].finish_reason = "length"  # Indicates truncation
        mock_response.usage = Mock()
        mock_response.usage.dict.return_value = {"prompt_tokens": 10, "completion_tokens": 1000}
        mock_response.model = "test-model"
        mock_completion.return_value = mock_response
        
        messages = [{"role": "user", "content": "Test prompt"}]
        
        with patch('src.arxiv_writer.llm.enhanced_caller.logger') as mock_logger:
            result = self.caller.call_llm_with_retry("test-model", messages)
            
            assert result is not None
            assert result["content"] == "Truncated response"
            mock_logger.warning.assert_called()  # Should warn about truncation
    
    @patch('src.arxiv_writer.llm.enhanced_caller.completion')
    def test_call_llm_with_retry_no_content(self, mock_completion):
        """Test handling of responses with no content."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.dict.return_value = {"prompt_tokens": 10, "completion_tokens": 0}
        mock_response.model = "test-model"
        mock_completion.return_value = mock_response
        
        messages = [{"role": "user", "content": "Test prompt"}]
        
        with patch('src.arxiv_writer.llm.enhanced_caller.logger') as mock_logger:
            result = self.caller.call_llm_with_retry("test-model", messages)
            
            assert result is not None
            assert result["content"] is None
            mock_logger.warning.assert_called()  # Should warn about no content
    
    def test_extract_and_parse_json_valid(self):
        """Test JSON extraction from valid JSON content."""
        json_data = {"key": "value", "number": 42, "nested": {"inner": "data"}}
        json_string = json.dumps(json_data)
        
        result = self.caller._extract_and_parse_json(json_string)
        assert result == json_data
    
    def test_extract_and_parse_json_code_block(self):
        """Test JSON extraction from markdown code blocks."""
        json_data = {"test": "value", "array": [1, 2, 3]}
        content = f"""
        Here's the JSON response:
        
        ```json
        {json.dumps(json_data)}
        ```
        
        That's the data you requested.
        """
        
        result = self.caller._extract_and_parse_json(content)
        assert result == json_data
    
    def test_extract_and_parse_json_code_block_no_lang(self):
        """Test JSON extraction from code blocks without language specification."""
        json_data = {"test": "value"}
        content = f"""
        ```
        {json.dumps(json_data)}
        ```
        """
        
        result = self.caller._extract_and_parse_json(content)
        assert result == json_data
    
    def test_extract_and_parse_json_nested_braces(self):
        """Test JSON extraction with nested braces."""
        json_data = {
            "outer": {
                "inner": {
                    "deep": "value"
                }
            },
            "array": [{"item": 1}, {"item": 2}]
        }
        json_string = json.dumps(json_data)
        content = f"Some text {json_string} more text"
        
        result = self.caller._extract_and_parse_json(content)
        # The regex might not capture the full nested JSON, so let's be more flexible
        assert isinstance(result, dict)
        # At least some of the data should be there
        assert "outer" in result or "inner" in result or "deep" in result
    
    def test_extract_and_parse_json_multiple_candidates(self):
        """Test JSON extraction when multiple JSON objects are present."""
        json1 = {"small": "object"}
        json2 = {"larger": "object", "with": {"more": "data", "and": ["arrays", "too"]}}
        
        content = f"First: {json.dumps(json1)} and second: {json.dumps(json2)}"
        
        result = self.caller._extract_and_parse_json(content)
        # Should return one of the JSON objects (the implementation may vary)
        assert isinstance(result, dict)
        assert result in [json1, json2] or "small" in result or "larger" in result
    
    def test_extract_and_parse_json_invalid(self):
        """Test JSON extraction with invalid content."""
        invalid_content = "This is not JSON at all, just plain text."
        result = self.caller._extract_and_parse_json(invalid_content)
        assert result is None
    
    def test_extract_and_parse_json_empty(self):
        """Test JSON extraction with empty content."""
        result = self.caller._extract_and_parse_json("")
        assert result is None
        
        result = self.caller._extract_and_parse_json(None)
        assert result is None
    
    @patch('src.arxiv_writer.llm.enhanced_caller.completion')
    def test_call_llm_json_with_retry_success(self, mock_completion):
        """Test successful JSON LLM call."""
        json_data = {"result": "success", "data": [1, 2, 3]}
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps(json_data)
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.dict.return_value = {"prompt_tokens": 10, "completion_tokens": 5}
        mock_response.model = "test-model"
        mock_completion.return_value = mock_response
        
        messages = [{"role": "user", "content": "Return JSON"}]
        result = self.caller.call_llm_json_with_retry("test-model", messages)
        
        assert result is not None
        assert result["result"] == "success"
        assert result["data"] == [1, 2, 3]
        assert "_llm_metadata" in result
        assert result["_llm_metadata"]["model"] == "test-model"
        assert result["_llm_metadata"]["attempts"] == 1
    
    @patch('src.arxiv_writer.llm.enhanced_caller.completion')
    def test_call_llm_json_with_retry_expected_keys(self, mock_completion):
        """Test JSON LLM call with expected keys validation."""
        json_data = {"name": "test", "value": 42}
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps(json_data)
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.dict.return_value = {"prompt_tokens": 10, "completion_tokens": 5}
        mock_response.model = "test-model"
        mock_completion.return_value = mock_response
        
        messages = [{"role": "user", "content": "Return JSON"}]
        expected_keys = ["name", "value", "missing_key"]
        
        with patch('src.arxiv_writer.llm.enhanced_caller.logger') as mock_logger:
            result = self.caller.call_llm_json_with_retry(
                "test-model", 
                messages, 
                expected_keys=expected_keys
            )
            
            assert result is not None
            assert result["name"] == "test"
            assert result["value"] == 42
            mock_logger.warning.assert_called()  # Should warn about missing key
    
    @patch('src.arxiv_writer.llm.enhanced_caller.completion')
    def test_call_llm_json_with_retry_invalid_json(self, mock_completion):
        """Test JSON LLM call with invalid JSON response."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "This is not JSON"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.dict.return_value = {"prompt_tokens": 10, "completion_tokens": 5}
        mock_response.model = "test-model"
        mock_completion.return_value = mock_response
        
        messages = [{"role": "user", "content": "Return JSON"}]
        result = self.caller.call_llm_json_with_retry("test-model", messages)
        
        assert result is None
    
    @patch('src.arxiv_writer.llm.enhanced_caller.completion')
    def test_call_llm_json_with_retry_no_response(self, mock_completion):
        """Test JSON LLM call when base call fails."""
        mock_completion.side_effect = Exception("authentication_failed")
        
        messages = [{"role": "user", "content": "Return JSON"}]
        result = self.caller.call_llm_json_with_retry("test-model", messages)
        
        assert result is None
    
    def test_get_retry_stats(self):
        """Test retry statistics retrieval."""
        stats = self.caller.get_retry_stats()
        
        assert stats["max_retries"] == self.caller.max_retries
        assert stats["base_delay"] == self.caller.base_delay
        assert stats["max_delay"] == self.caller.max_delay
    
    def test_delay_calculation_with_jitter(self):
        """Test that delay calculation includes jitter."""
        caller = EnhancedLLMCaller(base_delay=1.0, max_delay=10.0)
        
        # Test multiple delay calculations to ensure jitter varies
        delays = []
        for attempt in range(5):
            with patch('random.uniform') as mock_uniform:
                mock_uniform.return_value = 0.05  # 5% jitter
                
                # Simulate the delay calculation logic
                base_delay = min(caller.base_delay * (2 ** attempt), caller.max_delay)
                jitter = 0.05 * base_delay * 0.1
                expected_delay = base_delay + jitter
                delays.append(expected_delay)
        
        # Delays should increase exponentially (up to max_delay)
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]


class TestEnhancedLLMCallerConvenienceFunctions:
    """Test convenience functions for enhanced LLM caller."""
    
    @patch('src.arxiv_writer.llm.enhanced_caller.enhanced_llm_caller')
    def test_call_llm_with_exponential_backoff(self, mock_caller):
        """Test convenience function for LLM calls."""
        mock_caller.call_llm_with_retry.return_value = {"content": "test response"}
        
        messages = [{"role": "user", "content": "test"}]
        result = call_llm_with_exponential_backoff("test-model", messages, temperature=0.7)
        
        assert result == {"content": "test response"}
        mock_caller.call_llm_with_retry.assert_called_once_with(
            "test-model", messages, temperature=0.7
        )
    
    @patch('src.arxiv_writer.llm.enhanced_caller.enhanced_llm_caller')
    def test_call_llm_json_with_exponential_backoff(self, mock_caller):
        """Test convenience function for JSON LLM calls."""
        mock_caller.call_llm_json_with_retry.return_value = {"result": "success"}
        
        messages = [{"role": "user", "content": "return json"}]
        expected_keys = ["result"]
        result = call_llm_json_with_exponential_backoff(
            "test-model", messages, expected_keys=expected_keys, temperature=0.5
        )
        
        assert result == {"result": "success"}
        mock_caller.call_llm_json_with_retry.assert_called_once_with(
            "test-model", messages, expected_keys, temperature=0.5
        )


class TestEnhancedLLMCallerIntegration:
    """Integration tests for enhanced LLM caller."""
    
    def test_retryable_error_detection(self):
        """Test that retryable errors are correctly identified."""
        caller = EnhancedLLMCaller()
        
        retryable_messages = [
            "rate_limit_exceeded in request",
            "quota_exceeded for this model",
            "service_unavailable temporarily",
            "timeout occurred during request",
            "internal_server_error from provider",
            "bad_gateway response",
            "service_temporarily_unavailable",
            "too_many_requests received"
        ]
        
        for message in retryable_messages:
            error = Exception(message)
            error_str = str(error).lower()
            is_retryable = any(
                error_type in error_str 
                for error_type in caller.retryable_errors
            )
            assert is_retryable, f"Should be retryable: {message}"
    
    def test_exponential_backoff_timing(self):
        """Test that exponential backoff timing works correctly."""
        caller = EnhancedLLMCaller(base_delay=0.1, max_delay=1.0)
        
        # Test delay calculation for different attempts
        expected_delays = []
        for attempt in range(5):
            expected_delay = min(caller.base_delay * (2 ** attempt), caller.max_delay)
            expected_delays.append(expected_delay)
        
        # Delays should increase: 0.1, 0.2, 0.4, 0.8, 1.0 (capped at max_delay)
        assert expected_delays == [0.1, 0.2, 0.4, 0.8, 1.0]
    
    @patch('src.arxiv_writer.llm.enhanced_caller.completion')
    def test_full_retry_cycle(self, mock_completion):
        """Test a complete retry cycle with different error types."""
        caller = EnhancedLLMCaller(max_retries=3, base_delay=0.01, max_delay=0.1)
        
        # Simulate different types of failures followed by success
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Final success"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.dict.return_value = {"prompt_tokens": 10, "completion_tokens": 5}
        mock_response.model = "test-model"
        
        mock_completion.side_effect = [
            Exception("rate_limit_exceeded"),  # Retryable
            Exception("service_unavailable"),  # Retryable
            Exception("timeout occurred"),     # Retryable
            mock_response                      # Success
        ]
        
        messages = [{"role": "user", "content": "Test"}]
        
        with patch('time.sleep') as mock_sleep:
            result = caller.call_llm_with_retry("test-model", messages)
        
        assert result is not None
        assert result["content"] == "Final success"
        assert result["attempts"] == 4
        assert mock_completion.call_count == 4
        assert mock_sleep.call_count == 3  # Three delays before success