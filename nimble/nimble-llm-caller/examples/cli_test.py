#!/usr/bin/env python3
"""
Simple CLI tool to test nimble-llm-caller installation and basic functionality.
"""

import argparse
import sys
import os
from pathlib import Path

try:
    from nimble_llm_caller import LLMContentGenerator, ConfigManager
    from nimble_llm_caller.models.request import ResponseFormat
except ImportError as e:
    print(f"Error importing nimble-llm-caller: {e}")
    print("Make sure the package is installed: pip install nimble-llm-caller")
    sys.exit(1)


def test_installation():
    """Test that the package is properly installed."""
    print("Testing nimble-llm-caller installation...")
    
    try:
        # Test imports
        from nimble_llm_caller import (
            LLMCaller, LLMContentGenerator, PromptManager, 
            ConfigManager, LLMRequest, LLMResponse
        )
        print("✅ All imports successful")
        
        # Test basic initialization
        config_manager = ConfigManager()
        print(f"✅ ConfigManager initialized with {len(config_manager.list_available_models())} models")
        
        # Test prompt manager
        prompt_manager = PromptManager()
        print("✅ PromptManager initialized")
        
        print("🎉 Installation test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False


def test_configuration():
    """Test configuration management."""
    print("\nTesting configuration management...")
    
    try:
        config_manager = ConfigManager()
        
        # List available models
        models = config_manager.list_available_models()
        print(f"✅ Available models: {', '.join(models)}")
        
        # Test model validation
        for model in models[:2]:  # Test first 2 models
            validation = config_manager.validate_model(model)
            if validation["valid"]:
                print(f"✅ Model {model} configuration valid")
            else:
                print(f"⚠️  Model {model} configuration issues: {validation['issues']}")
        
        # Get config summary
        summary = config_manager.get_config_summary()
        print(f"✅ Configuration summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_prompt_management():
    """Test prompt management functionality."""
    print("\nTesting prompt management...")
    
    try:
        from nimble_llm_caller import PromptManager
        
        # Find sample prompts file
        sample_prompts_path = Path(__file__).parent / "sample_prompts.json"
        
        if not sample_prompts_path.exists():
            print("⚠️  Sample prompts file not found, skipping prompt tests")
            return True
        
        # Test prompt manager
        prompt_manager = PromptManager(str(sample_prompts_path))
        
        # List prompts
        prompt_keys = prompt_manager.list_prompt_keys()
        print(f"✅ Loaded {len(prompt_keys)} prompts: {', '.join(prompt_keys[:3])}...")
        
        # Test prompt preparation
        if prompt_keys:
            test_key = prompt_keys[0]
            prepared = prompt_manager.prepare_prompt(
                test_key, 
                {"text": "test", "content": "test", "topic": "test", "name": "test"}
            )
            
            if prepared:
                print(f"✅ Successfully prepared prompt: {test_key}")
            else:
                print(f"⚠️  Failed to prepare prompt: {test_key}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt management test failed: {e}")
        return False


def test_mock_llm_call():
    """Test LLM calling with mock (no actual API call)."""
    print("\nTesting mock LLM call...")
    
    try:
        from unittest.mock import patch, Mock
        
        # Find sample prompts file
        sample_prompts_path = Path(__file__).parent / "sample_prompts.json"
        
        if not sample_prompts_path.exists():
            print("⚠️  Sample prompts file not found, skipping LLM call test")
            return True
        
        # Mock the LiteLLM completion
        with patch('nimble_llm_caller.core.llm_caller.litellm.completion') as mock_completion:
            # Setup mock response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "This is a mock response for testing."
            mock_response.usage = Mock()
            mock_response.usage.dict.return_value = {"total_tokens": 25}
            mock_response.model = "gemini/gemini-2.5-flash"
            mock_completion.return_value = mock_response
            
            # Create generator
            generator = LLMContentGenerator(
                prompt_file_path=str(sample_prompts_path),
                default_model="gemini/gemini-2.5-flash"
            )
            
            # Make mock call
            response = generator.call_single(
                prompt_key="summarize_text",
                substitutions={"text": "This is test content to summarize."},
                response_format=ResponseFormat.TEXT
            )
            
            if response.is_success:
                print(f"✅ Mock LLM call successful: {response.content[:50]}...")
                print(f"✅ Execution time: {response.execution_time:.2f}s")
            else:
                print(f"❌ Mock LLM call failed: {response.error_message}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Mock LLM call test failed: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("🧪 Running nimble-llm-caller test suite...")
    print("=" * 50)
    
    tests = [
        test_installation,
        test_configuration,
        test_prompt_management,
        test_mock_llm_call
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! nimble-llm-caller is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Test nimble-llm-caller installation and functionality"
    )
    parser.add_argument(
        "--test", 
        choices=["all", "install", "config", "prompts", "mock"],
        default="all",
        help="Which test to run"
    )
    
    args = parser.parse_args()
    
    if args.test == "all":
        success = run_all_tests()
    elif args.test == "install":
        success = test_installation()
    elif args.test == "config":
        success = test_configuration()
    elif args.test == "prompts":
        success = test_prompt_management()
    elif args.test == "mock":
        success = test_mock_llm_call()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()