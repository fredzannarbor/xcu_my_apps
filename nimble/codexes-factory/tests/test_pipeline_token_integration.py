"""
Integration test for token usage tracking in the pipeline.
This test verifies that the token tracking integration works correctly
with the actual pipeline imports and structure.
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from codexes.core.token_usage_tracker import TokenUsageTracker
from codexes.core.statistics_reporter import StatisticsReporter
from codexes.core import llm_caller


class TestPipelineTokenIntegration:
    """Test suite for pipeline token tracking integration."""
    
    def setup_method(self):
        """Set up each test method."""
        # Clear any existing tracker
        llm_caller.clear_token_tracker()
    
    def teardown_method(self):
        """Clean up after each test method."""
        # Clear tracker after each test
        llm_caller.clear_token_tracker()
    
    def test_token_tracker_initialization(self):
        """Test that token tracker can be initialized and set correctly."""
        tracker = TokenUsageTracker()
        llm_caller.set_token_tracker(tracker)
        
        retrieved_tracker = llm_caller.get_token_tracker()
        assert retrieved_tracker is tracker
        
        # Verify initial state
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 0
        assert stats['total_tokens'] == 0
    
    def test_token_usage_recording(self):
        """Test that token usage is recorded correctly."""
        tracker = TokenUsageTracker()
        llm_caller.set_token_tracker(tracker)
        
        # Mock a LiteLLM response
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        # Mock cost calculation
        with patch('litellm.completion_cost', return_value=0.001):
            tracker.record_usage(
                model="test-model",
                prompt_name="test-prompt",
                response=mock_response,
                response_time=1.5
            )
        
        # Verify recording
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 1
        assert stats['total_input_tokens'] == 100
        assert stats['total_output_tokens'] == 50
        assert stats['total_tokens'] == 150
        assert stats['total_cost'] == 0.001
        
        # Verify model breakdown
        model_breakdown = tracker.get_model_breakdown()
        assert 'test-model' in model_breakdown
        assert model_breakdown['test-model'].call_count == 1
        
        # Verify prompt breakdown
        prompt_breakdown = tracker.get_prompt_breakdown()
        assert 'test-prompt' in prompt_breakdown
        assert prompt_breakdown['test-prompt'].call_count == 1
    
    def test_statistics_reporter_integration(self):
        """Test that statistics reporter works with token tracker."""
        tracker = TokenUsageTracker()
        
        # Add some mock data
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 200
        mock_response.usage.completion_tokens = 100
        mock_response.usage.total_tokens = 300
        
        with patch('litellm.completion_cost', return_value=0.002):
            tracker.record_usage(
                model="gpt-4",
                prompt_name="quotes",
                response=mock_response,
                response_time=2.0
            )
        
        # Test reporter
        reporter = StatisticsReporter()
        
        # Test that report generation doesn't crash
        # We can't easily test the actual output without capturing logs,
        # but we can verify it doesn't raise exceptions
        reporter.report_pipeline_statistics(tracker)
        
        # Test summary generation
        summary = reporter.generate_summary_report(tracker)
        assert "Pipeline Statistics Summary" in summary
        assert "1 LLM calls" in summary
        assert "300 total tokens" in summary
    
    def test_concurrent_pipeline_handling(self):
        """Test that concurrent pipeline scenarios are handled correctly."""
        tracker1 = TokenUsageTracker()
        tracker2 = TokenUsageTracker()
        
        # Set first tracker
        llm_caller.set_token_tracker(tracker1)
        assert llm_caller.get_token_tracker() is tracker1
        
        # Set second tracker (should replace first)
        llm_caller.set_token_tracker(tracker2)
        assert llm_caller.get_token_tracker() is tracker2
        assert llm_caller.get_token_tracker() is not tracker1
        
        # Clear tracker
        llm_caller.clear_token_tracker()
        assert llm_caller.get_token_tracker() is None
    
    def test_tracker_reset_functionality(self):
        """Test that tracker reset works correctly."""
        tracker = TokenUsageTracker()
        
        # Add some data
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 25
        mock_response.usage.total_tokens = 75
        
        with patch('litellm.completion_cost', return_value=0.0005):
            tracker.record_usage(
                model="test-model",
                prompt_name="test-prompt",
                response=mock_response
            )
        
        # Verify data exists
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 1
        
        # Reset tracker
        tracker.reset()
        
        # Verify data is cleared
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 0
        assert stats['total_tokens'] == 0
        assert len(tracker.records) == 0
        assert len(tracker.model_stats) == 0
        assert len(tracker.prompt_stats) == 0
    
    def test_error_handling_in_usage_recording(self):
        """Test that errors in usage recording are handled gracefully."""
        tracker = TokenUsageTracker()
        
        # Test with invalid response object
        invalid_response = "not a response object"
        
        # This should not raise an exception
        tracker.record_usage(
            model="test-model",
            prompt_name="test-prompt",
            response=invalid_response
        )
        
        # Should still have no recorded usage
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 0
    
    def test_cost_calculation_fallback(self):
        """Test that cost calculation failures are handled gracefully."""
        tracker = TokenUsageTracker()
        
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        # Mock cost calculation to raise an exception
        with patch('litellm.completion_cost', side_effect=Exception("Cost calculation failed")):
            tracker.record_usage(
                model="test-model",
                prompt_name="test-prompt",
                response=mock_response
            )
        
        # Should still record usage without cost
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 1
        assert stats['total_tokens'] == 150
        assert stats['total_cost'] is None


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])