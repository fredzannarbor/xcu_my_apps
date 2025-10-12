"""
Tests for the StatisticsReporter class.

This module tests the statistics reporting functionality including
report generation, formatting, and error handling.
"""

import pytest
import logging
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.statistics_reporter import StatisticsReporter
from codexes.core.token_usage_tracker import (
    TokenUsageTracker, UsageRecord, ModelStats, PromptStats
)


class TestStatisticsReporter:
    """Test cases for StatisticsReporter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = StatisticsReporter()
        self.tracker = TokenUsageTracker()
    
    def test_initialization(self):
        """Test StatisticsReporter initialization."""
        reporter = StatisticsReporter()
        assert hasattr(reporter, 'logger')
        assert isinstance(reporter.logger, logging.Logger)
    
    def test_report_pipeline_statistics_no_calls(self, caplog):
        """Test reporting when no LLM calls were made."""
        with caplog.at_level(logging.INFO):
            self.reporter.report_pipeline_statistics(self.tracker)
        
        assert "No LLM calls recorded" in caplog.text
    
    def test_report_pipeline_statistics_with_data(self, caplog):
        """Test comprehensive pipeline statistics reporting."""
        # Add some mock usage records
        self._add_mock_usage_records()
        
        with caplog.at_level(logging.INFO):
            self.reporter.report_pipeline_statistics(self.tracker)
        
        # Check that all sections are present
        assert "PIPELINE STATISTICS SUMMARY" in caplog.text
        assert "Overall Summary" in caplog.text
        assert "Model Breakdown" in caplog.text
        assert "Prompt Breakdown" in caplog.text
        assert "Cost Analysis" in caplog.text
    
    def test_overall_summary_logging(self, caplog):
        """Test overall summary section logging."""
        self._add_mock_usage_records()
        
        total_stats = self.tracker.get_total_statistics()
        
        with caplog.at_level(logging.INFO):
            self.reporter._log_overall_summary(total_stats)
        
        assert "Total LLM Calls:" in caplog.text
        assert "Total Tokens:" in caplog.text
        assert "Pipeline Duration:" in caplog.text
        assert "Processing Rate:" in caplog.text
    
    def test_model_breakdown_logging(self, caplog):
        """Test model breakdown section logging."""
        self._add_mock_usage_records()
        
        model_stats = self.tracker.get_model_breakdown()
        
        with caplog.at_level(logging.INFO):
            self.reporter._log_model_breakdown(model_stats)
        
        assert "Model Breakdown" in caplog.text
        assert "gpt-4" in caplog.text
        assert "gpt-3.5-turbo" in caplog.text
        assert "Calls:" in caplog.text
        assert "Tokens:" in caplog.text
    
    def test_prompt_breakdown_logging(self, caplog):
        """Test prompt breakdown section logging."""
        self._add_mock_usage_records()
        
        prompt_stats = self.tracker.get_prompt_breakdown()
        
        with caplog.at_level(logging.INFO):
            self.reporter._log_prompt_breakdown(prompt_stats)
        
        assert "Prompt Breakdown" in caplog.text
        assert "test_prompt_1" in caplog.text
        assert "test_prompt_2" in caplog.text
        assert "Models:" in caplog.text
    
    def test_cost_summary_with_cost_data(self, caplog):
        """Test cost summary when cost data is available."""
        self._add_mock_usage_records()
        
        total_stats = self.tracker.get_total_statistics()
        model_stats = self.tracker.get_model_breakdown()
        
        with caplog.at_level(logging.INFO):
            self.reporter._log_cost_summary(total_stats, model_stats)
        
        assert "Cost Analysis" in caplog.text
        assert "Total Cost:" in caplog.text
        assert "Cost per Token:" in caplog.text
        assert "Cost Data Coverage:" in caplog.text
    
    def test_cost_summary_without_cost_data(self, caplog):
        """Test cost summary when no cost data is available."""
        # Add records without cost data
        self._add_mock_usage_records(include_cost=False)
        
        total_stats = self.tracker.get_total_statistics()
        model_stats = self.tracker.get_model_breakdown()
        
        with caplog.at_level(logging.INFO):
            self.reporter._log_cost_summary(total_stats, model_stats)
        
        assert "Cost data not available" in caplog.text
        assert "This may be due to:" in caplog.text
    
    def test_format_cost_summary_with_cost(self):
        """Test cost summary formatting with cost data."""
        stats = {
            'total_calls': 5,
            'total_tokens': 1000,
            'total_cost': 0.05
        }
        
        result = self.reporter.format_cost_summary(stats)
        
        assert "5 calls" in result
        assert "1,000 tokens" in result
        assert "$0.0500" in result
    
    def test_format_cost_summary_without_cost(self):
        """Test cost summary formatting without cost data."""
        stats = {
            'total_calls': 3,
            'total_tokens': 500,
            'total_cost': None
        }
        
        result = self.reporter.format_cost_summary(stats)
        
        assert "3 calls" in result
        assert "500 tokens" in result
        assert "cost data unavailable" in result
    
    def test_log_model_breakdown_empty(self, caplog):
        """Test model breakdown logging with empty data."""
        with caplog.at_level(logging.INFO):
            self.reporter.log_model_breakdown({})
        
        assert "No model statistics available" in caplog.text
    
    def test_log_prompt_breakdown_empty(self, caplog):
        """Test prompt breakdown logging with empty data."""
        with caplog.at_level(logging.INFO):
            self.reporter.log_prompt_breakdown({})
        
        assert "No prompt statistics available" in caplog.text
    
    def test_generate_summary_report_with_data(self):
        """Test summary report generation with data."""
        self._add_mock_usage_records()
        
        result = self.reporter.generate_summary_report(self.tracker)
        
        assert "Pipeline Statistics Summary:" in result
        assert "LLM calls" in result
        assert "total tokens" in result
        assert "duration" in result
        assert "total cost" in result
    
    def test_generate_summary_report_no_data(self):
        """Test summary report generation with no data."""
        result = self.reporter.generate_summary_report(self.tracker)
        
        assert "No LLM calls recorded" in result
    
    def test_generate_summary_report_error_handling(self):
        """Test summary report generation error handling."""
        # Mock tracker to raise an exception
        mock_tracker = Mock()
        mock_tracker.get_total_statistics.side_effect = Exception("Test error")
        
        result = self.reporter.generate_summary_report(mock_tracker)
        
        assert "Error generating pipeline statistics summary" in result
    
    def test_report_pipeline_statistics_error_handling(self, caplog):
        """Test error handling in main report method."""
        # Mock tracker to raise an exception
        mock_tracker = Mock()
        mock_tracker.get_total_statistics.side_effect = Exception("Test error")
        
        with caplog.at_level(logging.ERROR):
            self.reporter.report_pipeline_statistics(mock_tracker)
        
        assert "Error generating pipeline statistics report" in caplog.text
    
    def test_sorting_by_token_usage(self, caplog):
        """Test that models and prompts are sorted by token usage."""
        # Add records with different token counts
        records = [
            UsageRecord(
                model="low-usage-model",
                prompt_name="low-usage-prompt",
                input_tokens=10,
                output_tokens=5,
                total_tokens=15,
                cost=0.001,
                timestamp=datetime.now()
            ),
            UsageRecord(
                model="high-usage-model",
                prompt_name="high-usage-prompt",
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                cost=0.01,
                timestamp=datetime.now()
            )
        ]
        
        for record in records:
            self.tracker.records.append(record)
            self.tracker._update_model_stats(record)
            self.tracker._update_prompt_stats(record)
        
        with caplog.at_level(logging.INFO):
            self.reporter.report_pipeline_statistics(self.tracker)
        
        # Check that high-usage items appear before low-usage items
        log_text = caplog.text
        high_model_pos = log_text.find("high-usage-model")
        low_model_pos = log_text.find("low-usage-model")
        high_prompt_pos = log_text.find("high-usage-prompt")
        low_prompt_pos = log_text.find("low-usage-prompt")
        
        assert high_model_pos < low_model_pos
        assert high_prompt_pos < low_prompt_pos
    
    def test_response_time_reporting(self, caplog):
        """Test that response times are included in reports when available."""
        record = UsageRecord(
            model="test-model",
            prompt_name="test-prompt",
            input_tokens=50,
            output_tokens=25,
            total_tokens=75,
            cost=0.005,
            timestamp=datetime.now(),
            response_time=2.5
        )
        
        self.tracker.records.append(record)
        self.tracker._update_model_stats(record)
        
        with caplog.at_level(logging.INFO):
            self.reporter.report_pipeline_statistics(self.tracker)
        
        assert "Avg Response Time: 2.50s" in caplog.text
    
    def test_models_used_in_prompt_breakdown(self, caplog):
        """Test that models used are shown in prompt breakdown."""
        # Add records with same prompt but different models
        records = [
            UsageRecord(
                model="gpt-4",
                prompt_name="shared-prompt",
                input_tokens=50,
                output_tokens=25,
                total_tokens=75,
                cost=0.005,
                timestamp=datetime.now()
            ),
            UsageRecord(
                model="gpt-3.5-turbo",
                prompt_name="shared-prompt",
                input_tokens=40,
                output_tokens=20,
                total_tokens=60,
                cost=0.003,
                timestamp=datetime.now()
            )
        ]
        
        for record in records:
            self.tracker.records.append(record)
            self.tracker._update_prompt_stats(record)
        
        with caplog.at_level(logging.INFO):
            self.reporter._log_prompt_breakdown(self.tracker.get_prompt_breakdown())
        
        assert "Models: gpt-4(1), gpt-3.5-turbo(1)" in caplog.text or \
               "Models: gpt-3.5-turbo(1), gpt-4(1)" in caplog.text
    
    def _add_mock_usage_records(self, include_cost=True):
        """Helper method to add mock usage records to the tracker."""
        records = [
            UsageRecord(
                model="gpt-4",
                prompt_name="test_prompt_1",
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                cost=0.01 if include_cost else None,
                timestamp=datetime.now(),
                response_time=1.5
            ),
            UsageRecord(
                model="gpt-3.5-turbo",
                prompt_name="test_prompt_2",
                input_tokens=80,
                output_tokens=40,
                total_tokens=120,
                cost=0.005 if include_cost else None,
                timestamp=datetime.now(),
                response_time=1.2
            ),
            UsageRecord(
                model="gpt-4",
                prompt_name="test_prompt_1",
                input_tokens=90,
                output_tokens=45,
                total_tokens=135,
                cost=0.009 if include_cost else None,
                timestamp=datetime.now(),
                response_time=1.8
            )
        ]
        
        for record in records:
            self.tracker.records.append(record)
            self.tracker._update_model_stats(record)
            self.tracker._update_prompt_stats(record)


class TestStatisticsReporterIntegration:
    """Integration tests for StatisticsReporter with real TokenUsageTracker."""
    
    def test_full_pipeline_simulation(self, caplog):
        """Test a full pipeline simulation with realistic data."""
        tracker = TokenUsageTracker()
        reporter = StatisticsReporter()
        
        # Simulate a realistic pipeline with multiple models and prompts
        pipeline_data = [
            ("gpt-4", "metadata_generation", 200, 100, 0.02),
            ("gpt-4", "metadata_generation", 180, 90, 0.018),
            ("gpt-3.5-turbo", "field_completion", 150, 75, 0.008),
            ("gpt-3.5-turbo", "field_completion", 160, 80, 0.009),
            ("gpt-4", "quality_check", 100, 50, 0.01),
        ]
        
        for model, prompt, input_tokens, output_tokens, cost in pipeline_data:
            record = UsageRecord(
                model=model,
                prompt_name=prompt,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost=cost,
                timestamp=datetime.now(),
                response_time=1.0 + (input_tokens / 100)  # Simulate response time
            )
            tracker.records.append(record)
            tracker._update_model_stats(record)
            tracker._update_prompt_stats(record)
        
        # Generate the report
        with caplog.at_level(logging.INFO):
            reporter.report_pipeline_statistics(tracker)
        
        # Verify comprehensive reporting
        log_text = caplog.text
        
        # Check overall summary
        assert "5 LLM calls" in log_text or "Total LLM Calls: 5" in log_text
        assert "1,185 tokens" in log_text or "Total Tokens: 1,185" in log_text
        
        # Check model breakdown
        assert "gpt-4" in log_text
        assert "gpt-3.5-turbo" in log_text
        
        # Check prompt breakdown
        assert "metadata_generation" in log_text
        assert "field_completion" in log_text
        assert "quality_check" in log_text
        
        # Check cost information
        assert "$0.0650" in log_text or "0.065" in log_text