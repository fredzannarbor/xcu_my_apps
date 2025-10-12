"""
Tests for LLM caller enhancements: prompt name logging and token tracking integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.llm_caller import (
    call_model_with_prompt,
    set_token_tracker,
    get_token_tracker,
    clear_token_tracker
)
from codexes.core.token_usage_tracker import TokenUsageTracker


class TestLLMCallerEnhancements:
    """Test the enhanced LLM caller functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear any existing tracker
        clear_token_tracker()
        
        # Create mock response
        self.mock_response = Mock()
        self.mock_response.choices = [Mock()]
        self.mock_response.choices[0].message = Mock()
        self.mock_response.choices[0].message.content = "Test response"
        
        # Mock usage data
        self.mock_usage = Mock()
        self.mock_usage.prompt_tokens = 10
        self.mock_usage.completion_tokens = 5
        self.mock_usage.total_tokens = 15
        self.mock_response.usage = self.mock_usage
    
    def teardown_method(self):
        """Clean up after tests."""
        clear_token_tracker()
    
    def test_token_tracker_management(self):
        """Test setting and getting token tracker."""
        # Initially no tracker
        assert get_token_tracker() is None
        
        # Set a tracker
        tracker = TokenUsageTracker()
        set_token_tracker(tracker)
        
        # Should return the same tracker
        assert get_token_tracker() is tracker
        
        # Clear tracker
        clear_token_tracker()
        assert get_token_tracker() is None
    
    @patch('codexes.core.llm_caller.litellm.completion')
    def test_prompt_name_in_logging(self, mock_completion, caplog):
        """Test that prompt names appear in log messages."""
        mock_completion.return_value = self.mock_response
        
        prompt_config = {
            "messages": [{"role": "user", "content": "test"}],
            "params": {"max_tokens": 50}
        }
        
        # Test with prompt name
        with caplog.at_level('INFO'):
            call_model_with_prompt(
                model_name="test-model",
                prompt_config=prompt_config,
                prompt_name="test_prompt",
                ensure_min_tokens=False
            )
        
        # Check that prompt name appears in logs
        log_messages = [record.message for record in caplog.records]
        
        # Should have prompt name in query message
        query_logs = [msg for msg in log_messages if "Querying" in msg]
        assert len(query_logs) > 0
        assert "[test_prompt]" in query_logs[0]
        
        # Should have prompt name in success message
        success_logs = [msg for msg in log_messages if "Successfully received response" in msg]
        assert len(success_logs) > 0
        assert "[test_prompt]" in success_logs[0]
    
    @patch('codexes.core.llm_caller.litellm.completion')
    def test_no_prompt_name_in_logging(self, mock_completion, caplog):
        """Test logging without prompt name."""
        mock_completion.return_value = self.mock_response
        
        prompt_config = {
            "messages": [{"role": "user", "content": "test"}],
            "params": {"max_tokens": 50}
        }
        
        # Test without prompt name
        with caplog.at_level('INFO'):
            call_model_with_prompt(
                model_name="test-model",
                prompt_config=prompt_config,
                ensure_min_tokens=False
            )
        
        # Check that no prompt name appears in logs
        log_messages = [record.message for record in caplog.records]
        
        # Should not have brackets in query message
        query_logs = [msg for msg in log_messages if "Querying" in msg]
        assert len(query_logs) > 0
        assert "[" not in query_logs[0]
        
        # Should not have brackets in success message
        success_logs = [msg for msg in log_messages if "Successfully received response" in msg]
        assert len(success_logs) > 0
        assert "[" not in success_logs[0]
    
    @patch('codexes.core.llm_caller.litellm.completion')
    def test_token_tracking_integration(self, mock_completion):
        """Test that token usage is tracked when tracker is set."""
        mock_completion.return_value = self.mock_response
        
        # Set up tracker
        tracker = TokenUsageTracker()
        set_token_tracker(tracker)
        
        prompt_config = {
            "messages": [{"role": "user", "content": "test"}],
            "params": {"max_tokens": 50}
        }
        
        # Make call with prompt name
        call_model_with_prompt(
            model_name="test-model",
            prompt_config=prompt_config,
            prompt_name="test_prompt",
            ensure_min_tokens=False
        )
        
        # Check that usage was recorded
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 1
        assert stats['total_tokens'] == 15
        assert 'test-model' in stats['models_used']
        assert 'test_prompt' in stats['prompts_used']
    
    @patch('codexes.core.llm_caller.litellm.completion')
    def test_no_tracking_without_prompt_name(self, mock_completion):
        """Test that usage is not tracked when no prompt name is provided."""
        mock_completion.return_value = self.mock_response
        
        # Set up tracker
        tracker = TokenUsageTracker()
        set_token_tracker(tracker)
        
        prompt_config = {
            "messages": [{"role": "user", "content": "test"}],
            "params": {"max_tokens": 50}
        }
        
        # Make call without prompt name
        call_model_with_prompt(
            model_name="test-model",
            prompt_config=prompt_config,
            ensure_min_tokens=False
        )
        
        # Check that no usage was recorded
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 0
        assert stats['total_tokens'] == 0
    
    @patch('codexes.core.llm_caller.litellm.completion')
    def test_tracking_error_handling(self, mock_completion, caplog):
        """Test that tracking errors don't break the LLM call."""
        mock_completion.return_value = self.mock_response
        
        # Set up tracker that will fail
        tracker = Mock()
        tracker.record_usage.side_effect = Exception("Tracking error")
        set_token_tracker(tracker)
        
        prompt_config = {
            "messages": [{"role": "user", "content": "test"}],
            "params": {"max_tokens": 50}
        }
        
        # Make call - should succeed despite tracking error
        with caplog.at_level('WARNING'):
            result = call_model_with_prompt(
                model_name="test-model",
                prompt_config=prompt_config,
                prompt_name="test_prompt",
                ensure_min_tokens=False
            )
        
        # Call should succeed
        assert result['parsed_content'] == "Test response"
        
        # Should have warning about tracking failure
        warning_logs = [record.message for record in caplog.records if record.levelname == 'WARNING']
        assert any("Failed to record token usage" in msg for msg in warning_logs)
    
    @patch('codexes.core.llm_caller.litellm.completion')
    def test_consistent_error_formatting(self, mock_completion, caplog):
        """Test that error messages use consistent formatting with prompt names."""
        from litellm.exceptions import BadRequestError
        
        # Mock an API error
        mock_completion.side_effect = BadRequestError(
            message="Test error",
            llm_provider="test-provider",
            model="test-model",
            response=Mock()
        )
        
        prompt_config = {
            "messages": [{"role": "user", "content": "test"}],
            "params": {"max_tokens": 50}
        }
        
        # Test with prompt name
        with caplog.at_level('ERROR'):
            result = call_model_with_prompt(
                model_name="test-model",
                prompt_config=prompt_config,
                prompt_name="test_prompt",
                ensure_min_tokens=False
            )
        
        # Should return error response
        assert "error" in result['parsed_content']
        
        # Should have error log with prompt name and emoji
        error_logs = [record.message for record in caplog.records if record.levelname == 'ERROR']
        assert len(error_logs) > 0
        assert "❌" in error_logs[0]
        assert "[test_prompt]" in error_logs[0]