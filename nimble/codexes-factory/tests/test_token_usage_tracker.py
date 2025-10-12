"""
Tests for the TokenUsageTracker class.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.token_usage_tracker import (
    TokenUsageTracker, 
    UsageRecord, 
    ModelStats, 
    PromptStats
)


class TestUsageRecord:
    """Test the UsageRecord dataclass."""
    
    def test_usage_record_creation(self):
        """Test creating a usage record."""
        record = UsageRecord(
            model="gpt-4",
            prompt_name="test_prompt",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost=0.01,
            timestamp=datetime.now()
        )
        
        assert record.model == "gpt-4"
        assert record.prompt_name == "test_prompt"
        assert record.total_tokens == 150
        assert record.cost == 0.01
    
    def test_cost_per_token_calculation(self):
        """Test cost per token calculation."""
        record = UsageRecord(
            model="gpt-4",
            prompt_name="test_prompt",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost=0.15,
            timestamp=datetime.now()
        )
        
        assert record.cost_per_token == 0.001  # 0.15 / 150
    
    def test_cost_per_token_with_no_cost(self):
        """Test cost per token when cost is None."""
        record = UsageRecord(
            model="gpt-4",
            prompt_name="test_prompt",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost=None,
            timestamp=datetime.now()
        )
        
        assert record.cost_per_token is None


class TestModelStats:
    """Test the ModelStats dataclass."""
    
    def test_model_stats_creation(self):
        """Test creating model stats."""
        stats = ModelStats(model="gpt-4")
        assert stats.model == "gpt-4"
        assert stats.call_count == 0
        assert stats.total_cost is None
    
    def test_add_record_updates_stats(self):
        """Test that adding a record updates statistics."""
        stats = ModelStats(model="gpt-4")
        record = UsageRecord(
            model="gpt-4",
            prompt_name="test_prompt",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost=0.01,
            timestamp=datetime.now(),
            response_time=1.5
        )
        
        stats.add_record(record)
        
        assert stats.call_count == 1
        assert stats.total_input_tokens == 100
        assert stats.total_output_tokens == 50
        assert stats.total_tokens == 150
        assert stats.total_cost == 0.01
        assert stats.average_response_time == 1.5
    
    def test_add_multiple_records(self):
        """Test adding multiple records to model stats."""
        stats = ModelStats(model="gpt-4")
        
        record1 = UsageRecord(
            model="gpt-4", prompt_name="test1", input_tokens=100, output_tokens=50,
            total_tokens=150, cost=0.01, timestamp=datetime.now(), response_time=1.0
        )
        record2 = UsageRecord(
            model="gpt-4", prompt_name="test2", input_tokens=200, output_tokens=100,
            total_tokens=300, cost=0.02, timestamp=datetime.now(), response_time=2.0
        )
        
        stats.add_record(record1)
        stats.add_record(record2)
        
        assert stats.call_count == 2
        assert stats.total_tokens == 450
        assert stats.total_cost == 0.03
        assert stats.average_response_time == 1.5  # (1.0 + 2.0) / 2


class TestPromptStats:
    """Test the PromptStats dataclass."""
    
    def test_prompt_stats_creation(self):
        """Test creating prompt stats."""
        stats = PromptStats(prompt_name="test_prompt")
        assert stats.prompt_name == "test_prompt"
        assert stats.call_count == 0
        assert len(stats.models_used) == 0
    
    def test_add_record_tracks_models(self):
        """Test that adding records tracks which models were used."""
        stats = PromptStats(prompt_name="test_prompt")
        
        record1 = UsageRecord(
            model="gpt-4", prompt_name="test_prompt", input_tokens=100, output_tokens=50,
            total_tokens=150, cost=0.01, timestamp=datetime.now()
        )
        record2 = UsageRecord(
            model="gpt-3.5-turbo", prompt_name="test_prompt", input_tokens=200, output_tokens=100,
            total_tokens=300, cost=0.02, timestamp=datetime.now()
        )
        
        stats.add_record(record1)
        stats.add_record(record2)
        
        assert stats.call_count == 2
        assert stats.models_used["gpt-4"] == 1
        assert stats.models_used["gpt-3.5-turbo"] == 1


class TestTokenUsageTracker:
    """Test the TokenUsageTracker class."""
    
    def test_tracker_initialization(self):
        """Test tracker initialization."""
        tracker = TokenUsageTracker()
        assert len(tracker.records) == 0
        assert len(tracker.model_stats) == 0
        assert len(tracker.prompt_stats) == 0
        assert tracker.start_time is not None
    
    def test_extract_usage_from_response_with_usage_attribute(self):
        """Test extracting usage from response with usage attribute."""
        tracker = TokenUsageTracker()
        
        # Mock LiteLLM response object
        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150
        
        mock_response = Mock()
        mock_response.usage = mock_usage
        
        usage_data = tracker._extract_usage_from_response(mock_response)
        
        assert usage_data is not None
        assert usage_data['prompt_tokens'] == 100
        assert usage_data['completion_tokens'] == 50
        assert usage_data['total_tokens'] == 150
    
    def test_extract_usage_from_dict_response(self):
        """Test extracting usage from dictionary response."""
        tracker = TokenUsageTracker()
        
        mock_response = {
            'usage': {
                'prompt_tokens': 200,
                'completion_tokens': 100,
                'total_tokens': 300
            }
        }
        
        usage_data = tracker._extract_usage_from_response(mock_response)
        
        assert usage_data is not None
        assert usage_data['prompt_tokens'] == 200
        assert usage_data['completion_tokens'] == 100
        assert usage_data['total_tokens'] == 300
    
    def test_extract_usage_no_data(self):
        """Test extracting usage when no data is available."""
        tracker = TokenUsageTracker()
        
        mock_response = Mock()
        mock_response.usage = None
        
        usage_data = tracker._extract_usage_from_response(mock_response)
        assert usage_data is None
    
    @patch('litellm.completion_cost')
    def test_calculate_cost_success(self, mock_completion_cost):
        """Test successful cost calculation."""
        tracker = TokenUsageTracker()
        mock_completion_cost.return_value = 0.05
        
        mock_response = Mock()
        cost = tracker._calculate_cost(mock_response, "gpt-4")
        
        assert cost == 0.05
        mock_completion_cost.assert_called_once_with(completion_response=mock_response)
    
    @patch('litellm.completion_cost')
    def test_calculate_cost_failure(self, mock_completion_cost):
        """Test cost calculation failure."""
        tracker = TokenUsageTracker()
        mock_completion_cost.side_effect = Exception("Cost calculation failed")
        
        mock_response = Mock()
        cost = tracker._calculate_cost(mock_response, "gpt-4")
        
        assert cost is None
    
    @patch('litellm.completion_cost')
    def test_record_usage_success(self, mock_completion_cost):
        """Test successful usage recording."""
        tracker = TokenUsageTracker()
        mock_completion_cost.return_value = 0.05
        
        # Mock response with usage data
        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150
        
        mock_response = Mock()
        mock_response.usage = mock_usage
        
        tracker.record_usage("gpt-4", "test_prompt", mock_response, 1.5)
        
        assert len(tracker.records) == 1
        assert "gpt-4" in tracker.model_stats
        assert "test_prompt" in tracker.prompt_stats
        
        record = tracker.records[0]
        assert record.model == "gpt-4"
        assert record.prompt_name == "test_prompt"
        assert record.total_tokens == 150
        assert record.cost == 0.05
        assert record.response_time == 1.5
    
    def test_get_total_statistics(self):
        """Test getting total statistics."""
        tracker = TokenUsageTracker()
        
        # Add some mock records
        record1 = UsageRecord(
            model="gpt-4", prompt_name="test1", input_tokens=100, output_tokens=50,
            total_tokens=150, cost=0.01, timestamp=datetime.now()
        )
        record2 = UsageRecord(
            model="gpt-3.5-turbo", prompt_name="test2", input_tokens=200, output_tokens=100,
            total_tokens=300, cost=0.02, timestamp=datetime.now()
        )
        
        tracker.records = [record1, record2]
        tracker.model_stats = {
            "gpt-4": ModelStats("gpt-4"),
            "gpt-3.5-turbo": ModelStats("gpt-3.5-turbo")
        }
        tracker.prompt_stats = {
            "test1": PromptStats("test1"),
            "test2": PromptStats("test2")
        }
        
        stats = tracker.get_total_statistics()
        
        assert stats['total_calls'] == 2
        assert stats['total_input_tokens'] == 300
        assert stats['total_output_tokens'] == 150
        assert stats['total_tokens'] == 450
        assert stats['total_cost'] == 0.03
        assert len(stats['models_used']) == 2
        assert len(stats['prompts_used']) == 2
    
    def test_reset(self):
        """Test resetting the tracker."""
        tracker = TokenUsageTracker()
        
        # Add some data
        record = UsageRecord(
            model="gpt-4", prompt_name="test", input_tokens=100, output_tokens=50,
            total_tokens=150, cost=0.01, timestamp=datetime.now()
        )
        tracker.records = [record]
        tracker.model_stats = {"gpt-4": ModelStats("gpt-4")}
        tracker.prompt_stats = {"test": PromptStats("test")}
        
        # Reset
        tracker.reset()
        
        assert len(tracker.records) == 0
        assert len(tracker.model_stats) == 0
        assert len(tracker.prompt_stats) == 0
    
    def test_get_recent_records(self):
        """Test getting recent records."""
        tracker = TokenUsageTracker()
        
        # Add multiple records
        for i in range(15):
            record = UsageRecord(
                model="gpt-4", prompt_name=f"test{i}", input_tokens=100, output_tokens=50,
                total_tokens=150, cost=0.01, timestamp=datetime.now()
            )
            tracker.records.append(record)
        
        recent = tracker.get_recent_records(limit=5)
        assert len(recent) == 5
        assert recent[-1].prompt_name == "test14"  # Most recent
        
        # Test with fewer records than limit
        tracker.records = tracker.records[:3]
        recent = tracker.get_recent_records(limit=10)
        assert len(recent) == 3