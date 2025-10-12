"""
Unit tests for LLM models module.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.arxiv_writer.llm.models import LLMConfig, LLMResponse, LLMError


class TestLLMConfig:
    """Test cases for LLMConfig dataclass."""
    
    def test_default_initialization(self):
        """Test LLMConfig with default values."""
        config = LLMConfig()
        
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key is None
        assert config.base_url is None
        assert config.temperature == 0.7
        assert config.max_tokens is None
        assert config.timeout == 60
        assert config.retry_attempts == 3
        assert config.retry_delay == 1.0
    
    def test_custom_initialization(self):
        """Test LLMConfig with custom values."""
        config = LLMConfig(
            provider="anthropic",
            model="claude-3-opus",
            api_key="test-key",
            base_url="https://api.example.com",
            temperature=0.5,
            max_tokens=2000,
            timeout=120,
            retry_attempts=5,
            retry_delay=2.0
        )
        
        assert config.provider == "anthropic"
        assert config.model == "claude-3-opus"
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.example.com"
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
        assert config.timeout == 120
        assert config.retry_attempts == 5
        assert config.retry_delay == 2.0
    
    def test_partial_initialization(self):
        """Test LLMConfig with partial custom values."""
        config = LLMConfig(
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=1000
        )
        
        # Custom values
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.3
        assert config.max_tokens == 1000
        
        # Default values
        assert config.provider == "openai"
        assert config.api_key is None
        assert config.timeout == 60
        assert config.retry_attempts == 3
    
    def test_config_equality(self):
        """Test LLMConfig equality comparison."""
        config1 = LLMConfig(model="gpt-4", temperature=0.7)
        config2 = LLMConfig(model="gpt-4", temperature=0.7)
        config3 = LLMConfig(model="gpt-3.5-turbo", temperature=0.7)
        
        assert config1 == config2
        assert config1 != config3
    
    def test_config_repr(self):
        """Test LLMConfig string representation."""
        config = LLMConfig(model="test-model", temperature=0.5)
        repr_str = repr(config)
        
        assert "LLMConfig" in repr_str
        assert "test-model" in repr_str
        assert "0.5" in repr_str


class TestLLMResponse:
    """Test cases for LLMResponse dataclass."""
    
    def test_default_initialization(self):
        """Test LLMResponse with required fields only."""
        response = LLMResponse(
            content="Test response",
            model="gpt-4",
            provider="openai"
        )
        
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.tokens_used is None
        assert response.cost is None
        assert response.response_time == 0.0
        assert isinstance(response.timestamp, datetime)
        assert response.metadata == {}
    
    def test_full_initialization(self):
        """Test LLMResponse with all fields."""
        timestamp = datetime.now()
        metadata = {"request_id": "123", "version": "1.0"}
        
        response = LLMResponse(
            content="Full response",
            model="claude-3-opus",
            provider="anthropic",
            tokens_used=150,
            cost=0.05,
            response_time=2.5,
            timestamp=timestamp,
            metadata=metadata
        )
        
        assert response.content == "Full response"
        assert response.model == "claude-3-opus"
        assert response.provider == "anthropic"
        assert response.tokens_used == 150
        assert response.cost == 0.05
        assert response.response_time == 2.5
        assert response.timestamp == timestamp
        assert response.metadata == metadata
    
    def test_timestamp_auto_generation(self):
        """Test that timestamp is automatically generated."""
        before = datetime.now()
        response = LLMResponse(
            content="Test",
            model="gpt-4",
            provider="openai"
        )
        after = datetime.now()
        
        assert before <= response.timestamp <= after
    
    def test_metadata_default_factory(self):
        """Test that metadata uses default factory for empty dict."""
        response1 = LLMResponse(content="Test1", model="gpt-4", provider="openai")
        response2 = LLMResponse(content="Test2", model="gpt-4", provider="openai")
        
        # Should be separate dict instances
        response1.metadata["key1"] = "value1"
        response2.metadata["key2"] = "value2"
        
        assert "key1" in response1.metadata
        assert "key1" not in response2.metadata
        assert "key2" in response2.metadata
        assert "key2" not in response1.metadata
    
    def test_response_equality(self):
        """Test LLMResponse equality comparison."""
        timestamp = datetime.now()
        
        response1 = LLMResponse(
            content="Same content",
            model="gpt-4",
            provider="openai",
            timestamp=timestamp
        )
        response2 = LLMResponse(
            content="Same content",
            model="gpt-4",
            provider="openai",
            timestamp=timestamp
        )
        response3 = LLMResponse(
            content="Different content",
            model="gpt-4",
            provider="openai",
            timestamp=timestamp
        )
        
        assert response1 == response2
        assert response1 != response3
    
    def test_response_with_complex_metadata(self):
        """Test LLMResponse with complex metadata."""
        metadata = {
            "request_headers": {"Authorization": "Bearer token"},
            "response_headers": {"Content-Type": "application/json"},
            "processing_steps": [
                {"step": "tokenization", "duration": 0.1},
                {"step": "generation", "duration": 2.0},
                {"step": "post_processing", "duration": 0.2}
            ],
            "model_config": {
                "temperature": 0.7,
                "max_tokens": 1000,
                "top_p": 0.9
            }
        }
        
        response = LLMResponse(
            content="Complex response",
            model="gpt-4",
            provider="openai",
            metadata=metadata
        )
        
        assert response.metadata == metadata
        assert len(response.metadata["processing_steps"]) == 3
        assert response.metadata["model_config"]["temperature"] == 0.7
    
    def test_response_repr(self):
        """Test LLMResponse string representation."""
        response = LLMResponse(
            content="Test response",
            model="gpt-4",
            provider="openai",
            tokens_used=100
        )
        repr_str = repr(response)
        
        assert "LLMResponse" in repr_str
        assert "gpt-4" in repr_str
        assert "openai" in repr_str


class TestLLMError:
    """Test cases for LLMError exception."""
    
    def test_basic_error(self):
        """Test basic LLMError creation and usage."""
        error = LLMError("Test error message")
        
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_error_inheritance(self):
        """Test that LLMError inherits from Exception."""
        error = LLMError("Test error")
        
        assert isinstance(error, Exception)
        assert isinstance(error, LLMError)
    
    def test_error_raising(self):
        """Test raising and catching LLMError."""
        with pytest.raises(LLMError) as exc_info:
            raise LLMError("Custom error message")
        
        assert str(exc_info.value) == "Custom error message"
    
    def test_error_with_args(self):
        """Test LLMError with multiple arguments."""
        error = LLMError("Error", "Additional info", 123)
        
        assert error.args == ("Error", "Additional info", 123)
        assert str(error) == "('Error', 'Additional info', 123)"
    
    def test_error_chaining(self):
        """Test error chaining with LLMError."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise LLMError("LLM processing failed") from e
        except LLMError as llm_error:
            assert str(llm_error) == "LLM processing failed"
            assert isinstance(llm_error.__cause__, ValueError)
            assert str(llm_error.__cause__) == "Original error"


class TestLLMModelsIntegration:
    """Integration tests for LLM models."""
    
    def test_config_and_response_workflow(self):
        """Test typical workflow using config and response together."""
        # Create configuration
        config = LLMConfig(
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000,
            timeout=30
        )
        
        # Simulate creating a response based on config
        response = LLMResponse(
            content="Generated content based on config",
            model=config.model,
            provider=config.provider,
            tokens_used=config.max_tokens // 2,  # Simulate partial usage
            response_time=config.timeout / 2,    # Simulate response time
            metadata={
                "config_temperature": config.temperature,
                "config_max_tokens": config.max_tokens
            }
        )
        
        assert response.model == config.model
        assert response.provider == config.provider
        assert response.metadata["config_temperature"] == config.temperature
        assert response.metadata["config_max_tokens"] == config.max_tokens
    
    def test_error_handling_with_config(self):
        """Test error handling in context of configuration."""
        config = LLMConfig(model="invalid-model")
        
        try:
            # Simulate validation that might raise LLMError
            if not config.model.startswith(("gpt-", "claude-", "llama-")):
                raise LLMError(f"Unsupported model: {config.model}")
        except LLMError as e:
            assert "invalid-model" in str(e)
            assert "Unsupported model" in str(e)
    
    def test_response_serialization_compatibility(self):
        """Test that response data can be serialized (for logging/storage)."""
        response = LLMResponse(
            content="Serializable content",
            model="gpt-4",
            provider="openai",
            tokens_used=100,
            cost=0.02,
            response_time=1.5,
            metadata={"key": "value"}
        )
        
        # Convert to dict-like structure (simulating serialization)
        response_dict = {
            "content": response.content,
            "model": response.model,
            "provider": response.provider,
            "tokens_used": response.tokens_used,
            "cost": response.cost,
            "response_time": response.response_time,
            "timestamp": response.timestamp.isoformat(),
            "metadata": response.metadata
        }
        
        assert response_dict["content"] == response.content
        assert response_dict["model"] == response.model
        assert response_dict["tokens_used"] == response.tokens_used
        assert isinstance(response_dict["timestamp"], str)
    
    def test_config_validation_scenarios(self):
        """Test various configuration validation scenarios."""
        # Valid configurations
        valid_configs = [
            LLMConfig(),  # All defaults
            LLMConfig(model="gpt-3.5-turbo", temperature=0.0),  # Min temperature
            LLMConfig(model="gpt-4", temperature=2.0),  # Max temperature
            LLMConfig(max_tokens=1, timeout=1),  # Min values
            LLMConfig(max_tokens=100000, timeout=3600),  # Large values
        ]
        
        for config in valid_configs:
            assert isinstance(config.provider, str)
            assert isinstance(config.model, str)
            assert isinstance(config.temperature, (int, float))
            assert config.temperature >= 0
            assert config.retry_attempts >= 0
            assert config.timeout > 0
    
    def test_response_timing_accuracy(self):
        """Test response timing and timestamp accuracy."""
        import time
        
        start_time = time.time()
        response = LLMResponse(
            content="Timed response",
            model="gpt-4",
            provider="openai",
            response_time=1.23
        )
        end_time = time.time()
        
        # Timestamp should be between start and end
        timestamp_seconds = response.timestamp.timestamp()
        assert start_time <= timestamp_seconds <= end_time
        
        # Response time should be preserved
        assert response.response_time == 1.23