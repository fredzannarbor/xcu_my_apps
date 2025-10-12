"""
Tests for ContextAnalyzer class.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import os

from nimble_llm_caller.core.context_analyzer import ContextAnalyzer, ModelCapacity
from nimble_llm_caller.core.token_estimator import TokenEstimator
from nimble_llm_caller.models.request import LLMRequest, FileAttachment, ProcessedFile, ResponseFormat


class TestModelCapacity:
    """Test cases for ModelCapacity class."""
    
    def test_init(self):
        """Test ModelCapacity initialization."""
        capacity = ModelCapacity(
            model_name="gpt-4",
            max_context_tokens=8192,
            provider="openai",
            cost_multiplier=1.5,
            supports_vision=True,
            supported_file_types=["image", "text"]
        )
        
        assert capacity.model_name == "gpt-4"
        assert capacity.max_context_tokens == 8192
        assert capacity.provider == "openai"
        assert capacity.cost_multiplier == 1.5
        assert capacity.supports_vision is True
        assert capacity.supported_file_types == ["image", "text"]
    
    def test_init_defaults(self):
        """Test ModelCapacity initialization with defaults."""
        capacity = ModelCapacity("gpt-3.5-turbo", 4096, "openai")
        
        assert capacity.cost_multiplier == 1.0
        assert capacity.supports_vision is False
        assert capacity.supported_file_types == []


class TestContextAnalyzer:
    """Test cases for ContextAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_token_estimator = Mock(spec=TokenEstimator)
        self.analyzer = ContextAnalyzer(token_estimator=self.mock_token_estimator)
    
    def test_init(self):
        """Test ContextAnalyzer initialization."""
        analyzer = ContextAnalyzer()
        assert analyzer.token_estimator is not None
        assert isinstance(analyzer.model_capacities, dict)
        assert "gpt-4" in analyzer.model_capacities
        assert "claude-3-sonnet" in analyzer.model_capacities
    
    def test_init_with_custom_capacities(self):
        """Test initialization with custom capacities."""
        custom_capacity = ModelCapacity("custom-model", 16000, "custom", 2.0)
        custom_capacities = {"custom-model": custom_capacity}
        
        analyzer = ContextAnalyzer(custom_capacities=custom_capacities)
        assert "custom-model" in analyzer.model_capacities
        assert analyzer.model_capacities["custom-model"] == custom_capacity
    
    def test_get_model_capacity_direct_match(self):
        """Test getting model capacity with direct match."""
        capacity = self.analyzer.get_model_capacity("gpt-4")
        assert capacity is not None
        assert capacity.model_name == "gpt-4"
        assert capacity.max_context_tokens == 8192
        assert capacity.provider == "openai"
    
    def test_get_model_capacity_with_provider_prefix(self):
        """Test getting model capacity with provider prefix."""
        capacity = self.analyzer.get_model_capacity("openai/gpt-4")
        assert capacity is not None
        assert capacity.model_name == "gpt-4"
    
    def test_get_model_capacity_pattern_match(self):
        """Test getting model capacity with pattern matching."""
        # This should match gpt-4 pattern
        capacity = self.analyzer.get_model_capacity("gpt-4-custom-variant")
        assert capacity is not None
        assert capacity.provider == "openai"
    
    def test_get_model_capacity_unknown_model(self):
        """Test getting capacity for unknown model."""
        capacity = self.analyzer.get_model_capacity("unknown-model")
        assert capacity is None
    
    def test_extract_text_content(self):
        """Test text content extraction from request."""
        request = LLMRequest(
            prompt_key="test_prompt",
            model="gpt-4",
            substitutions={"name": "John", "age": 30},
            model_params={"temperature": 0.7}
        )
        
        content = self.analyzer._extract_text_content(request)
        assert "test_prompt" in content
        assert "John" in content
        assert "30" in content
        assert "temperature" in content
    
    def test_is_image_file(self):
        """Test image file detection."""
        assert self.analyzer._is_image_file(Path("test.jpg")) is True
        assert self.analyzer._is_image_file(Path("test.png")) is True
        assert self.analyzer._is_image_file(Path("test.gif")) is True
        assert self.analyzer._is_image_file(Path("test.txt")) is False
        assert self.analyzer._is_image_file(Path("test.pdf")) is False
        assert self.analyzer._is_image_file(Path("test.JPG")) is True  # Case insensitive
    
    def test_find_suitable_models(self):
        """Test finding suitable models for token requirements."""
        # Need 50000 tokens, current model is gpt-4 (8192 tokens)
        suitable = self.analyzer._find_suitable_models(50000, "gpt-4")
        
        # Should include models with >= 50000 tokens
        assert len(suitable) > 0
        
        # Check that all returned models have sufficient capacity
        for model_name in suitable:
            capacity = self.analyzer.get_model_capacity(model_name)
            assert capacity.max_context_tokens >= 50000
        
        # OpenAI models should be preferred (same provider as gpt-4)
        openai_models = [m for m in suitable if self.analyzer.get_model_capacity(m).provider == "openai"]
        if openai_models:
            assert suitable[0] in openai_models or len(openai_models) == 0
    
    def test_analyze_request_simple(self):
        """Test basic request analysis."""
        request = LLMRequest(
            prompt_key="test_prompt",
            model="gpt-4",
            substitutions={"content": "Hello world"}
        )
        
        # Mock token estimation
        self.mock_token_estimator.estimate_text_tokens.return_value = 100
        
        analysis = self.analyzer.analyze_request(request)
        
        assert analysis.total_tokens == 100
        assert analysis.text_tokens == 100
        assert analysis.file_tokens == 0
        assert analysis.model_capacity == 8192
        assert analysis.requires_upshift is False
        assert analysis.requires_chunking is False
        assert len(analysis.recommended_models) == 0
    
    def test_analyze_request_exceeds_capacity(self):
        """Test request analysis when context exceeds model capacity."""
        request = LLMRequest(
            prompt_key="large_prompt",
            model="gpt-4",
            substitutions={"content": "Very large content"}
        )
        
        # Mock token estimation to exceed gpt-4 capacity (8192)
        self.mock_token_estimator.estimate_text_tokens.return_value = 10000
        
        analysis = self.analyzer.analyze_request(request)
        
        assert analysis.total_tokens == 10000
        assert analysis.requires_upshift is True
        assert len(analysis.recommended_models) > 0
        
        # Recommended models should have sufficient capacity
        for model_name in analysis.recommended_models:
            capacity = self.analyzer.get_model_capacity(model_name)
            assert capacity.max_context_tokens >= 10000
    
    def test_analyze_request_with_file_attachments(self):
        """Test request analysis with file attachments."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("File content for testing")
            temp_file = f.name
        
        try:
            request = LLMRequest(
                prompt_key="test_prompt",
                model="gpt-4",
                file_attachments=[
                    FileAttachment(file_path=temp_file, content_type="text/plain")
                ]
            )
            
            # Mock token estimations
            self.mock_token_estimator.estimate_text_tokens.return_value = 50
            self.mock_token_estimator.estimate_file_tokens.return_value = 25
            
            analysis = self.analyzer.analyze_request(request)
            
            assert analysis.total_tokens == 75  # 50 + 25
            assert analysis.text_tokens == 50
            assert analysis.file_tokens == 25
            
        finally:
            os.unlink(temp_file)
    
    def test_analyze_request_with_image_attachment(self):
        """Test request analysis with image attachment."""
        request = LLMRequest(
            prompt_key="test_prompt",
            model="gpt-4o",  # Vision-capable model
            file_attachments=[
                FileAttachment(file_path="/fake/image.jpg", content_type="image/jpeg")
            ]
        )
        
        # Mock token estimations
        self.mock_token_estimator.estimate_text_tokens.return_value = 50
        self.mock_token_estimator.estimate_image_tokens.return_value = 200
        
        analysis = self.analyzer.analyze_request(request)
        
        assert analysis.total_tokens == 250  # 50 + 200
        assert analysis.text_tokens == 50
        assert analysis.file_tokens == 200
        
        # Verify image token estimation was called
        self.mock_token_estimator.estimate_image_tokens.assert_called_once()
    
    def test_analyze_request_image_with_non_vision_model(self):
        """Test request analysis with image but non-vision model."""
        request = LLMRequest(
            prompt_key="test_prompt",
            model="gpt-3.5-turbo",  # Non-vision model
            file_attachments=[
                FileAttachment(file_path="/fake/image.jpg", content_type="image/jpeg")
            ]
        )
        
        # Mock token estimations
        self.mock_token_estimator.estimate_text_tokens.return_value = 50
        
        analysis = self.analyzer.analyze_request(request)
        
        # Image should be skipped for non-vision model
        assert analysis.total_tokens == 50
        assert analysis.file_tokens == 0
        
        # Image token estimation should not be called
        self.mock_token_estimator.estimate_image_tokens.assert_not_called()
    
    def test_analyze_request_with_processed_files(self):
        """Test request analysis with processed files."""
        request = LLMRequest(
            prompt_key="test_prompt",
            model="gpt-4",
            processed_files=[
                ProcessedFile(
                    original_path="/fake/file.txt",
                    content="Processed file content",
                    content_type="text/plain",
                    token_count=30,
                    processing_method="text_extraction"
                )
            ]
        )
        
        # Mock token estimations
        self.mock_token_estimator.estimate_text_tokens.side_effect = [50, 30]  # prompt, then processed file
        
        analysis = self.analyzer.analyze_request(request)
        
        assert analysis.total_tokens == 80  # 50 + 30
        assert analysis.text_tokens == 50
        assert analysis.file_tokens == 30
    
    def test_analyze_request_requires_chunking(self):
        """Test request analysis when chunking is required."""
        request = LLMRequest(
            prompt_key="huge_prompt",
            model="gpt-4",
            substitutions={"content": "Extremely large content"}
        )
        
        # Mock token estimation to exceed all model capacities
        self.mock_token_estimator.estimate_text_tokens.return_value = 2000000  # 2M tokens
        
        analysis = self.analyzer.analyze_request(request)
        
        assert analysis.total_tokens == 2000000
        assert analysis.requires_upshift is False  # No model can handle this
        assert analysis.requires_chunking is True
        assert len(analysis.recommended_models) == 0
    
    def test_estimate_tokens_for_content(self):
        """Test token estimation for arbitrary content."""
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Text file content")
            text_file = f.name
        
        try:
            # Mock token estimations
            self.mock_token_estimator.estimate_text_tokens.return_value = 100
            self.mock_token_estimator.estimate_file_tokens.return_value = 50
            self.mock_token_estimator.estimate_image_tokens.return_value = 200
            
            result = self.analyzer.estimate_tokens_for_content(
                "Some text content",
                [text_file, "/fake/image.jpg"],
                "gpt-4o"
            )
            
            assert result["text_tokens"] == 100
            assert result["file_tokens"] == 50
            assert result["image_tokens"] == 200
            assert result["total_tokens"] == 350
            
        finally:
            os.unlink(text_file)
    
    def test_check_model_compatibility_compatible(self):
        """Test model compatibility check for compatible model."""
        result = self.analyzer.check_model_compatibility("gpt-4o", has_images=True)
        
        assert result["compatible"] is True
        assert result["reason"] == "Compatible"
        assert result["max_tokens"] == 128000
        assert result["supports_vision"] is True
        assert result["provider"] == "openai"
    
    def test_check_model_compatibility_no_vision(self):
        """Test model compatibility check for model without vision."""
        result = self.analyzer.check_model_compatibility("gpt-3.5-turbo", has_images=True)
        
        assert result["compatible"] is False
        assert result["reason"] == "Model does not support vision/images"
        assert result["supports_vision"] is False
    
    def test_check_model_compatibility_unknown_model(self):
        """Test model compatibility check for unknown model."""
        result = self.analyzer.check_model_compatibility("unknown-model")
        
        assert result["compatible"] is False
        assert result["reason"] == "Unknown model"
        assert result["max_tokens"] is None
    
    def test_add_custom_model_capacity(self):
        """Test adding custom model capacity."""
        custom_capacity = ModelCapacity("custom-model", 50000, "custom", 1.5)
        
        self.analyzer.add_custom_model_capacity("custom-model", custom_capacity)
        
        assert "custom-model" in self.analyzer.model_capacities
        assert self.analyzer.get_model_capacity("custom-model") == custom_capacity
    
    def test_get_all_model_capacities(self):
        """Test getting all model capacities."""
        capacities = self.analyzer.get_all_model_capacities()
        
        assert isinstance(capacities, dict)
        assert "gpt-4" in capacities
        assert "claude-3-sonnet" in capacities
        
        # Should be a copy, not the original
        capacities["test"] = "test"
        assert "test" not in self.analyzer.model_capacities
    
    def test_get_models_by_provider(self):
        """Test getting models by provider."""
        openai_models = self.analyzer.get_models_by_provider("openai")
        anthropic_models = self.analyzer.get_models_by_provider("anthropic")
        
        assert len(openai_models) > 0
        assert len(anthropic_models) > 0
        assert "gpt-4" in openai_models
        assert "claude-3-sonnet" in anthropic_models
        
        # Verify all returned models are from the correct provider
        for model in openai_models:
            capacity = self.analyzer.get_model_capacity(model)
            assert capacity.provider == "openai"
        
        for model in anthropic_models:
            capacity = self.analyzer.get_model_capacity(model)
            assert capacity.provider == "anthropic"


class TestContextAnalyzerIntegration:
    """Integration tests for ContextAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ContextAnalyzer()
    
    def test_real_analysis_workflow(self):
        """Test a realistic analysis workflow."""
        request = LLMRequest(
            prompt_key="summarize_document",
            model="gpt-3.5-turbo",
            substitutions={
                "document": "This is a sample document that needs to be summarized. " * 100,
                "style": "concise"
            }
        )
        
        analysis = self.analyzer.analyze_request(request)
        
        # Should have reasonable token counts
        assert analysis.total_tokens > 0
        assert analysis.text_tokens > 0
        assert analysis.model_capacity == 16385  # gpt-3.5-turbo capacity
        
        # Analysis should be consistent
        assert analysis.total_tokens == analysis.text_tokens + analysis.file_tokens
    
    def test_model_capacity_consistency(self):
        """Test that model capacities are consistent with token estimator."""
        models_to_test = ["gpt-4", "gpt-4o", "claude-3-sonnet", "gemini-1.5-pro"]
        
        for model in models_to_test:
            capacity = self.analyzer.get_model_capacity(model)
            if capacity:
                # Verify the model is known to the token estimator
                model_info = self.analyzer.token_estimator.get_model_info(model)
                assert model_info["provider"] == capacity.provider
                
                # Vision support should be consistent
                supports_vision = self.analyzer.token_estimator.supports_vision(model)
                assert supports_vision == capacity.supports_vision