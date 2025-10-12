"""
Tests for TokenEstimator class.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import tempfile
import os

from nimble_llm_caller.core.token_estimator import TokenEstimator


class TestTokenEstimator:
    """Test cases for TokenEstimator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.estimator = TokenEstimator()
    
    def test_init(self):
        """Test TokenEstimator initialization."""
        assert self.estimator._tiktoken_cache == {}
        assert self.estimator._anthropic_tokenizer is None
        assert self.estimator._google_tokenizer is None
    
    def test_detect_provider_from_name(self):
        """Test provider detection from model names."""
        # OpenAI models
        assert self.estimator._detect_provider_from_name("gpt-4")[0] == "openai"
        assert self.estimator._detect_provider_from_name("gpt-3.5-turbo")[0] == "openai"
        assert self.estimator._detect_provider_from_name("text-embedding-ada-002")[0] == "openai"
        
        # Anthropic models
        assert self.estimator._detect_provider_from_name("claude-3-sonnet")[0] == "anthropic"
        assert self.estimator._detect_provider_from_name("claude-2")[0] == "anthropic"
        
        # Google models
        assert self.estimator._detect_provider_from_name("gemini-pro")[0] == "google"
        assert self.estimator._detect_provider_from_name("gemini-1.5-pro")[0] == "google"
        
        # Cohere models
        assert self.estimator._detect_provider_from_name("command")[0] == "cohere"
        
        # Mistral models
        assert self.estimator._detect_provider_from_name("mistral-large")[0] == "mistral"
        
        # Unknown model defaults to OpenAI
        assert self.estimator._detect_provider_from_name("unknown-model")[0] == "openai"
    
    def test_detect_provider_and_model_with_prefix(self):
        """Test provider detection with provider prefix."""
        provider, model, config = self.estimator._detect_provider_and_model("openai/gpt-4")
        assert provider == "openai"
        assert model == "gpt-4"
        assert config["tokenizer_type"] == "tiktoken"
        
        provider, model, config = self.estimator._detect_provider_and_model("anthropic/claude-3-sonnet")
        assert provider == "anthropic"
        assert model == "claude-3-sonnet"
        assert config["tokenizer_type"] == "anthropic"
    
    def test_detect_provider_and_model_without_prefix(self):
        """Test provider detection without provider prefix."""
        provider, model, config = self.estimator._detect_provider_and_model("gpt-4o")
        assert provider == "openai"
        assert model == "gpt-4o"
        assert config["encoding"] == "o200k_base"
        
        provider, model, config = self.estimator._detect_provider_and_model("claude-3-haiku")
        assert provider == "anthropic"
        assert model == "claude-3-haiku"
        assert config["chars_per_token"] == 3.5
    
    @patch('tiktoken.get_encoding')
    def test_get_tiktoken_encoding(self, mock_get_encoding):
        """Test tiktoken encoding retrieval with caching."""
        mock_encoding = Mock()
        mock_get_encoding.return_value = mock_encoding
        
        # First call should fetch from tiktoken
        result1 = self.estimator._get_tiktoken_encoding("cl100k_base")
        assert result1 == mock_encoding
        mock_get_encoding.assert_called_once_with("cl100k_base")
        
        # Second call should use cache
        result2 = self.estimator._get_tiktoken_encoding("cl100k_base")
        assert result2 == mock_encoding
        assert mock_get_encoding.call_count == 1  # Still only called once
    
    @patch('tiktoken.get_encoding')
    def test_get_tiktoken_encoding_fallback(self, mock_get_encoding):
        """Test tiktoken encoding fallback on error."""
        mock_encoding = Mock()
        mock_get_encoding.side_effect = [Exception("Test error"), mock_encoding]
        
        result = self.estimator._get_tiktoken_encoding("invalid_encoding")
        assert result == mock_encoding
        assert mock_get_encoding.call_count == 2
        mock_get_encoding.assert_any_call("invalid_encoding")
        mock_get_encoding.assert_any_call("cl100k_base")
    
    @patch('tiktoken.get_encoding')
    def test_estimate_text_tokens_openai(self, mock_get_encoding):
        """Test text token estimation for OpenAI models."""
        mock_encoding = Mock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_get_encoding.return_value = mock_encoding
        
        tokens = self.estimator.estimate_text_tokens("Hello world", "gpt-4")
        assert tokens == 5
        mock_encoding.encode.assert_called_once_with("Hello world")
    
    def test_estimate_text_tokens_anthropic(self):
        """Test text token estimation for Anthropic models."""
        # Without actual Anthropic tokenizer, should use character estimation
        tokens = self.estimator.estimate_text_tokens("Hello world", "claude-3-sonnet")
        # "Hello world" = 11 characters, 3.5 chars per token = ~3.14 tokens, rounded to 3
        assert tokens == 3
    
    def test_estimate_text_tokens_google(self):
        """Test text token estimation for Google models."""
        # Without actual Google tokenizer, should use character estimation
        tokens = self.estimator.estimate_text_tokens("Hello world", "gemini-pro")
        # "Hello world" = 11 characters, 4.0 chars per token = 2.75 tokens, rounded to 2
        assert tokens == 2
    
    def test_estimate_text_tokens_empty(self):
        """Test token estimation for empty text."""
        tokens = self.estimator.estimate_text_tokens("", "gpt-4")
        assert tokens == 0
    
    def test_estimate_file_tokens_with_content(self):
        """Test file token estimation with provided content."""
        with patch.object(self.estimator, 'estimate_text_tokens', return_value=10) as mock_estimate:
            tokens = self.estimator.estimate_file_tokens("/fake/path", "gpt-4", "test content")
            assert tokens == 10
            mock_estimate.assert_called_once_with("test content", "gpt-4")
    
    def test_estimate_file_tokens_read_file(self):
        """Test file token estimation by reading file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test file content")
            temp_path = f.name
        
        try:
            with patch.object(self.estimator, 'estimate_text_tokens', return_value=15) as mock_estimate:
                tokens = self.estimator.estimate_file_tokens(temp_path, "gpt-4")
                assert tokens == 15
                mock_estimate.assert_called_once_with("test file content", "gpt-4")
        finally:
            os.unlink(temp_path)
    
    def test_estimate_file_tokens_read_error(self):
        """Test file token estimation with read error."""
        tokens = self.estimator.estimate_file_tokens("/nonexistent/file", "gpt-4")
        assert tokens == 0
    
    def test_estimate_image_tokens_openai(self):
        """Test image token estimation for OpenAI models."""
        with patch('builtins.__import__') as mock_import:
            mock_pil = Mock()
            mock_img = Mock()
            mock_img.size = (1024, 768)
            
            # Set up the context manager properly
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_img)
            mock_context.__exit__ = Mock(return_value=None)
            mock_pil.Image.open.return_value = mock_context
            
            def side_effect(name, *args, **kwargs):
                if name == 'PIL':
                    return mock_pil
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = side_effect
            
            tokens = self.estimator.estimate_image_tokens("/fake/image.jpg", "gpt-4o")
            # 1024x768 image: tiles_x = 2, tiles_y = 2, total = 85 + (2*2*170) = 765
            assert tokens == 765
    
    def test_estimate_image_tokens_anthropic(self):
        """Test image token estimation for Anthropic models."""
        with patch('builtins.__import__') as mock_import:
            mock_pil = Mock()
            mock_img = Mock()
            mock_img.size = (800, 600)
            
            # Set up the context manager properly
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_img)
            mock_context.__exit__ = Mock(return_value=None)
            mock_pil.Image.open.return_value = mock_context
            
            def side_effect(name, *args, **kwargs):
                if name == 'PIL':
                    return mock_pil
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = side_effect
            
            tokens = self.estimator.estimate_image_tokens("/fake/image.jpg", "claude-3-sonnet")
            # 800*600 = 480,000 pixels, < 1MP, so 480,000 * 0.002 = 960
            assert tokens == 960
    
    def test_estimate_image_tokens_google(self):
        """Test image token estimation for Google models."""
        with patch('builtins.__import__') as mock_import:
            mock_pil = Mock()
            mock_img = Mock()
            mock_img.size = (1200, 900)
            
            # Set up the context manager properly
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_img)
            mock_context.__exit__ = Mock(return_value=None)
            mock_pil.Image.open.return_value = mock_context
            
            def side_effect(name, *args, **kwargs):
                if name == 'PIL':
                    return mock_pil
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = side_effect
            
            tokens = self.estimator.estimate_image_tokens("/fake/image.jpg", "gemini-1.5-pro")
            # 1200*900 = 1,080,000 pixels, > 1MP, so 258 * 1.5 = 387
            assert tokens == 387
    
    def test_estimate_image_tokens_no_vision_support(self):
        """Test image token estimation for models without vision support."""
        tokens = self.estimator.estimate_image_tokens("/fake/image.jpg", "gpt-3.5-turbo")
        assert tokens == 0
    
    def test_estimate_image_tokens_pil_not_available(self):
        """Test image token estimation when PIL is not available."""
        with patch('builtins.__import__') as mock_import:
            def side_effect(name, *args, **kwargs):
                if name == 'PIL':
                    raise ImportError("PIL not available")
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = side_effect
            
            tokens = self.estimator.estimate_image_tokens("/fake/image.jpg", "gpt-4o")
            assert tokens == 1000  # Default for vision-capable models
    
    def test_estimate_request_tokens(self):
        """Test complete request token estimation."""
        with patch.object(self.estimator, 'estimate_text_tokens', side_effect=[10, 5, 3]) as mock_text:
            with patch.object(self.estimator, 'estimate_image_tokens', return_value=100) as mock_image:
                result = self.estimator.estimate_request_tokens(
                    "main text",
                    ["file1 content", "file2 content"],
                    ["/image1.jpg"],
                    "gpt-4o"
                )
                
                assert result == {
                    "text_tokens": 10,
                    "file_tokens": 8,  # 5 + 3
                    "image_tokens": 100,
                    "total_tokens": 118
                }
                
                assert mock_text.call_count == 3
                mock_image.assert_called_once_with("/image1.jpg", "gpt-4o")
    
    def test_get_model_info(self):
        """Test model information retrieval."""
        info = self.estimator.get_model_info("gpt-4o")
        
        assert info["model"] == "gpt-4o"
        assert info["clean_model"] == "gpt-4o"
        assert info["provider"] == "openai"
        assert info["tokenizer_type"] == "tiktoken"
        assert info["encoding"] == "o200k_base"
        assert info["supports_vision"] is True
        assert info["is_configured"] is True
    
    def test_get_model_info_unknown_model(self):
        """Test model information for unknown model."""
        info = self.estimator.get_model_info("unknown-model")
        
        assert info["model"] == "unknown-model"
        assert info["provider"] == "openai"  # Default
        assert info["is_configured"] is False
    
    def test_get_supported_providers(self):
        """Test getting supported providers."""
        providers = TokenEstimator.get_supported_providers()
        expected = ["openai", "anthropic", "google", "cohere", "mistral"]
        assert set(providers) == set(expected)
    
    def test_get_supported_models(self):
        """Test getting supported models by provider."""
        models = TokenEstimator.get_supported_models()
        
        assert "openai" in models
        assert "gpt-4" in models["openai"]
        assert "gpt-4o" in models["openai"]
        
        assert "anthropic" in models
        assert "claude-3-sonnet" in models["anthropic"]
        
        assert "google" in models
        assert "gemini-pro" in models["google"]
    
    def test_supports_vision(self):
        """Test vision support detection."""
        assert self.estimator.supports_vision("gpt-4o") is True
        assert self.estimator.supports_vision("gpt-3.5-turbo") is False
        assert self.estimator.supports_vision("claude-3-sonnet") is True
        assert self.estimator.supports_vision("gemini-1.5-pro") is True
        assert self.estimator.supports_vision("gemini-pro") is False
    
    def test_error_handling_in_estimate_text_tokens(self):
        """Test error handling in text token estimation."""
        with patch('tiktoken.get_encoding', side_effect=Exception("Encoding error")):
            tokens = self.estimator.estimate_text_tokens("test text", "gpt-4")
            # Should fall back to character-based estimation: 9 chars / 4 = 2.25 -> 2
            assert tokens == 2


class TestTokenEstimatorIntegration:
    """Integration tests for TokenEstimator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.estimator = TokenEstimator()
    
    def test_real_tiktoken_estimation(self):
        """Test with real tiktoken (if available)."""
        try:
            import tiktoken
            tokens = self.estimator.estimate_text_tokens("Hello, world!", "gpt-4")
            assert tokens > 0
            assert isinstance(tokens, int)
        except ImportError:
            pytest.skip("tiktoken not available")
    
    def test_provider_consistency(self):
        """Test that provider detection is consistent."""
        test_cases = [
            ("gpt-4", "openai"),
            ("openai/gpt-4", "openai"),
            ("claude-3-sonnet", "anthropic"),
            ("anthropic/claude-3-sonnet", "anthropic"),
            ("gemini-pro", "google"),
            ("google/gemini-pro", "google"),
        ]
        
        for model, expected_provider in test_cases:
            provider, _, _ = self.estimator._detect_provider_and_model(model)
            assert provider == expected_provider, f"Failed for model: {model}"