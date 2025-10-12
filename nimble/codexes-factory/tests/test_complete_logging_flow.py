"""
Complete logging flow integration test.

This module tests the entire logging improvements system working together
with the actual LLM caller and pipeline components.
"""

import pytest
import logging
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.logging_config import LoggingConfigManager, setup_application_logging
from codexes.core.token_usage_tracker import TokenUsageTracker
from codexes.core.statistics_reporter import StatisticsReporter
from codexes.core import llm_caller


class TestCompleteLoggingFlow:
    """Test the complete logging flow from LLM call to statistics reporting."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear any existing tracker
        llm_caller.clear_token_tracker()
        
        # Create temporary directory for logs
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create logs directory
        Path('logs').mkdir(exist_ok=True)
        
        # Set up logging
        setup_application_logging()
    
    def teardown_method(self):
        """Clean up after tests."""
        # Clear tracker
        llm_caller.clear_token_tracker()
        
        # Return to original directory
        os.chdir(self.original_cwd)
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('codexes.core.llm_caller.litellm.completion')
    def test_end_to_end_logging_flow(self, mock_completion, caplog):
        """Test complete end-to-end logging flow."""
        # Set up mock LLM response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response from LLM"
        
        # Mock usage data
        mock_usage = Mock()
        mock_usage.prompt_tokens = 150
        mock_usage.completion_tokens = 75
        mock_usage.total_tokens = 225
        mock_response.usage = mock_usage
        
        mock_completion.return_value = mock_response
        
        # Set up token tracker
        tracker = TokenUsageTracker()
        llm_caller.set_token_tracker(tracker)
        
        # Mock cost calculation
        with patch('litellm.completion_cost', return_value=0.025):
            # Make LLM call with prompt name
            prompt_config = {
                "messages": [{"role": "user", "content": "Test prompt"}],
                "params": {"max_tokens": 100}
            }
            
            with caplog.at_level(logging.INFO):
                result = llm_caller.call_model_with_prompt(
                    model_name="gpt-4",
                    prompt_config=prompt_config,
                    prompt_name="end_to_end_test",
                    ensure_min_tokens=False
                )
            
            # Verify LLM call succeeded
            assert result['parsed_content'] == "Test response from LLM"
            
            # Check that prompt name appeared in logs
            log_messages = [record.message for record in caplog.records]
            query_logs = [msg for msg in log_messages if "Querying" in msg]
            success_logs = [msg for msg in log_messages if "Successfully received response" in msg]
            
            assert len(query_logs) > 0
            assert "[end_to_end_test]" in query_logs[0]
            assert len(success_logs) > 0
            assert "[end_to_end_test]" in success_logs[0]
            
            # Verify token usage was tracked
            stats = tracker.get_total_statistics()
            assert stats['total_calls'] == 1
            assert stats['total_tokens'] == 225
            assert stats['total_cost'] == 0.025
            assert 'gpt-4' in stats['models_used']
            assert 'end_to_end_test' in stats['prompts_used']
            
            # Generate statistics report
            reporter = StatisticsReporter()
            
            # Clear previous log records
            caplog.clear()
            
            with caplog.at_level(logging.INFO):
                reporter.report_pipeline_statistics(tracker)
            
            # Verify comprehensive report was generated
            report_text = caplog.text
            assert "PIPELINE STATISTICS SUMMARY" in report_text
            assert "1 LLM calls" in report_text or "Total LLM Calls: 1" in report_text
            assert "225 tokens" in report_text or "Total Tokens: 225" in report_text
            assert "$0.0250" in report_text or "0.025" in report_text
            assert "gpt-4" in report_text
            assert "end_to_end_test" in report_text
    
    @patch('codexes.core.llm_caller.litellm.completion')
    def test_multiple_llm_calls_with_different_prompts(self, mock_completion, caplog):
        """Test logging flow with multiple LLM calls using different prompts."""
        # Set up token tracker
        tracker = TokenUsageTracker()
        llm_caller.set_token_tracker(tracker)
        
        # Define test scenarios
        test_scenarios = [
            {
                "model": "gpt-4",
                "prompt_name": "metadata_generation",
                "response_content": "Generated metadata",
                "prompt_tokens": 200,
                "completion_tokens": 100,
                "cost": 0.03
            },
            {
                "model": "gpt-3.5-turbo",
                "prompt_name": "field_completion",
                "response_content": "Completed field data",
                "prompt_tokens": 150,
                "completion_tokens": 75,
                "cost": 0.008
            },
            {
                "model": "gpt-4",
                "prompt_name": "quality_check",
                "response_content": "Quality check passed",
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "cost": 0.015
            }
        ]
        
        # Execute each scenario
        for i, scenario in enumerate(test_scenarios):
            # Set up mock response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = scenario["response_content"]
            
            mock_usage = Mock()
            mock_usage.prompt_tokens = scenario["prompt_tokens"]
            mock_usage.completion_tokens = scenario["completion_tokens"]
            mock_usage.total_tokens = scenario["prompt_tokens"] + scenario["completion_tokens"]
            mock_response.usage = mock_usage
            
            mock_completion.return_value = mock_response
            
            # Mock cost calculation
            with patch('litellm.completion_cost', return_value=scenario["cost"]):
                prompt_config = {
                    "messages": [{"role": "user", "content": f"Test prompt {i}"}],
                    "params": {"max_tokens": 100}
                }
                
                result = llm_caller.call_model_with_prompt(
                    model_name=scenario["model"],
                    prompt_config=prompt_config,
                    prompt_name=scenario["prompt_name"],
                    ensure_min_tokens=False
                )
                
                assert result['parsed_content'] == scenario["response_content"]
        
        # Verify all usage was tracked correctly
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 3
        assert stats['total_input_tokens'] == 450  # 200 + 150 + 100
        assert stats['total_output_tokens'] == 225  # 100 + 75 + 50
        assert stats['total_tokens'] == 675  # 450 + 225
        assert abs(stats['total_cost'] - 0.053) < 0.001  # 0.03 + 0.008 + 0.015
        
        # Verify model breakdown
        model_breakdown = tracker.get_model_breakdown()
        assert len(model_breakdown) == 2
        assert model_breakdown['gpt-4'].call_count == 2
        assert model_breakdown['gpt-3.5-turbo'].call_count == 1
        
        # Verify prompt breakdown
        prompt_breakdown = tracker.get_prompt_breakdown()
        assert len(prompt_breakdown) == 3
        assert all(stats.call_count == 1 for stats in prompt_breakdown.values())
        
        # Generate comprehensive report
        reporter = StatisticsReporter()
        
        with caplog.at_level(logging.INFO):
            reporter.report_pipeline_statistics(tracker)
        
        report_text = caplog.text
        
        # Verify all models and prompts appear in report
        assert "gpt-4" in report_text
        assert "gpt-3.5-turbo" in report_text
        assert "metadata_generation" in report_text
        assert "field_completion" in report_text
        assert "quality_check" in report_text
        
        # Verify cost information
        assert "$0.0530" in report_text or "0.053" in report_text
    
    def test_litellm_noise_filtering_during_real_calls(self, caplog):
        """Test that LiteLLM noise is filtered during actual operation."""
        # Get LiteLLM logger
        litellm_logger = logging.getLogger('litellm')
        
        with caplog.at_level(logging.DEBUG):
            # Simulate various LiteLLM messages that should be filtered
            litellm_logger.info("Cost calculation for model gpt-4: $0.002")
            litellm_logger.info("Completion wrapper function called")
            litellm_logger.debug("LiteLLM utils processing request")
            litellm_logger.info("Making request to OpenAI API")
            
            # These should come through
            litellm_logger.error("Authentication failed with OpenAI")
            litellm_logger.warning("Rate limit exceeded, retrying")
            litellm_logger.info("Service unavailable - please retry")
        
        # Check that filtering worked correctly
        log_messages = [record.message for record in caplog.records]
        
        # Filtered messages should not appear
        filtered_patterns = [
            "Cost calculation",
            "Completion wrapper",
            "LiteLLM utils",
            "Making request to"
        ]
        
        for pattern in filtered_patterns:
            assert not any(pattern in msg for msg in log_messages), f"Pattern '{pattern}' should be filtered"
        
        # Important messages should appear
        important_patterns = [
            "Authentication failed",
            "Rate limit exceeded",
            "Service unavailable"
        ]
        
        for pattern in important_patterns:
            assert any(pattern in msg for msg in log_messages), f"Pattern '{pattern}' should not be filtered"
    
    @patch('codexes.core.llm_caller.litellm.completion')
    def test_error_handling_in_complete_flow(self, mock_completion, caplog):
        """Test error handling throughout the complete logging flow."""
        # Set up token tracker
        tracker = TokenUsageTracker()
        llm_caller.set_token_tracker(tracker)
        
        # Test 1: LLM call fails
        from litellm.exceptions import BadRequestError
        mock_completion.side_effect = BadRequestError(
            message="Invalid request",
            llm_provider="openai",
            model="gpt-4",
            response=Mock()
        )
        
        prompt_config = {
            "messages": [{"role": "user", "content": "Test prompt"}],
            "params": {"max_tokens": 100}
        }
        
        with caplog.at_level(logging.ERROR):
            result = llm_caller.call_model_with_prompt(
                model_name="gpt-4",
                prompt_config=prompt_config,
                prompt_name="error_test",
                ensure_min_tokens=False
            )
        
        # Should return error response
        assert "error" in result['parsed_content'].lower()
        
        # Should have error log with prompt name
        error_logs = [record.message for record in caplog.records if record.levelname == 'ERROR']
        assert len(error_logs) > 0
        assert any("❌" in msg and "[error_test]" in msg for msg in error_logs)
        
        # Test 2: Successful call but cost calculation fails
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Success after error"
        
        mock_usage = Mock()
        mock_usage.prompt_tokens = 50
        mock_usage.completion_tokens = 25
        mock_usage.total_tokens = 75
        mock_response.usage = mock_usage
        
        mock_completion.side_effect = None
        mock_completion.return_value = mock_response
        
        # Mock cost calculation to fail
        with patch('litellm.completion_cost', side_effect=Exception("Cost calc failed")):
            caplog.clear()
            
            with caplog.at_level(logging.WARNING):
                result = llm_caller.call_model_with_prompt(
                    model_name="gpt-4",
                    prompt_config=prompt_config,
                    prompt_name="cost_error_test",
                    ensure_min_tokens=False
                )
        
        # Call should succeed
        assert result['parsed_content'] == "Success after error"
        
        # Should have recorded usage without cost
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 1  # Only the successful call
        assert stats['total_tokens'] == 75
        assert stats['total_cost'] is None  # Cost calculation failed
        
        # Test 3: Statistics reporting with partial data
        reporter = StatisticsReporter()
        
        caplog.clear()
        with caplog.at_level(logging.INFO):
            reporter.report_pipeline_statistics(tracker)
        
        report_text = caplog.text
        
        # Should generate report despite missing cost data
        assert "PIPELINE STATISTICS SUMMARY" in report_text
        assert "Cost data not available" in report_text or "cost data unavailable" in report_text
    
    def test_performance_impact_of_logging_improvements(self):
        """Test that logging improvements don't significantly impact performance."""
        import time
        
        # Set up token tracker
        tracker = TokenUsageTracker()
        llm_caller.set_token_tracker(tracker)
        
        # Measure time for operations with logging improvements
        start_time = time.time()
        
        for i in range(100):
            # Simulate usage recording
            mock_response = Mock()
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.usage.total_tokens = 15
            
            with patch('litellm.completion_cost', return_value=0.001):
                tracker.record_usage(f"model-{i % 3}", f"prompt-{i % 5}", mock_response)
        
        # Generate statistics report
        reporter = StatisticsReporter()
        reporter.report_pipeline_statistics(tracker)
        
        total_time = time.time() - start_time
        
        # Should complete reasonably quickly (less than 1 second for 100 operations)
        assert total_time < 1.0, f"Logging operations took too long: {total_time:.2f}s"
        
        # Verify all operations completed correctly
        stats = tracker.get_total_statistics()
        assert stats['total_calls'] == 100
        assert stats['total_tokens'] == 1500  # 100 * 15
    
    def test_log_file_content_verification(self):
        """Test that log files contain expected content from the complete flow."""
        # Set up token tracker
        tracker = TokenUsageTracker()
        llm_caller.set_token_tracker(tracker)
        
        # Create some usage data
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        with patch('litellm.completion_cost', return_value=0.01):
            tracker.record_usage("gpt-4", "file_test_prompt", mock_response)
        
        # Generate statistics report
        reporter = StatisticsReporter()
        reporter.report_pipeline_statistics(tracker)
        
        # Force log flushing
        for handler in logging.getLogger().handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        
        # Check application log file
        app_log_path = Path('logs/application.log')
        assert app_log_path.exists()
        
        with open(app_log_path, 'r') as f:
            app_log_content = f.read()
            
            # Should contain statistics report
            assert "PIPELINE STATISTICS SUMMARY" in app_log_content
            assert "gpt-4" in app_log_content
            assert "file_test_prompt" in app_log_content
            assert "$0.0100" in app_log_content or "0.01" in app_log_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])