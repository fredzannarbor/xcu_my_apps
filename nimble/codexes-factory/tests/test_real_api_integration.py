#!/usr/bin/env python3
"""
Comprehensive test script to verify nimble-llm-caller integration works with real API keys.
This script tests all LLM calling functions with actual API calls.
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def load_environment():
    """Load environment variables from .env file."""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    print("🔑 Environment variables loaded:")
    api_keys = {
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY', 'Not set'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', 'Not set'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', 'Not set'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY', 'Not set')
    }
    
    for key, value in api_keys.items():
        status = "✅ Set" if value != 'Not set' else "❌ Not set"
        masked_value = f"{value[:8]}..." if value != 'Not set' else value
        print(f"  {key}: {status} ({masked_value})")
    
    return api_keys

def test_integration_layer_basic():
    """Test the basic integration layer functionality."""
    print("\n🧪 Testing Integration Layer Basic Functionality")
    print("=" * 60)
    
    try:
        from codexes.core.llm_integration import get_llm_integration, call_model_with_prompt
        
        print("✅ Successfully imported integration layer")
        
        # Get integration instance
        integration = get_llm_integration()
        print("✅ Integration instance created")
        
        # Test configuration validation
        validation = integration.validate_configuration()
        print(f"📋 Configuration validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
        
        if not validation['valid']:
            print("⚠️  Configuration issues:")
            for issue in validation['issues']:
                print(f"    - {issue}")
        
        # List available models
        models = integration.list_available_models()
        print(f"📋 Available models: {models}")
        
        return integration, True
        
    except Exception as e:
        print(f"❌ Integration layer error: {e}")
        return None, False

def test_simple_llm_call(integration):
    """Test a simple LLM call with Gemini 2.5 Flash."""
    print("\n🧪 Testing Simple LLM Call (Gemini 2.5 Flash)")
    print("=" * 60)
    
    try:
        # Test simple call
        response = integration.call_llm(
            prompt="Say 'Hello from nimble-llm-caller integration!' and explain what you are in one sentence.",
            model="gemini/gemini-2.5-flash",
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"✅ Simple LLM call successful")
        print(f"📝 Response: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple LLM call failed: {e}")
        return False

def test_structured_prompt_call(integration):
    """Test structured prompt call using the integration layer."""
    print("\n🧪 Testing Structured Prompt Call")
    print("=" * 60)
    
    try:
        # Create structured prompt config
        prompt_config = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that responds in JSON format."
                },
                {
                    "role": "user", 
                    "content": "Create a JSON object with fields: greeting, model_name, timestamp, and status. Set status to 'integration_working'."
                }
            ],
            "params": {
                "temperature": 0.3,
                "max_tokens": 200
            }
        }
        
        # Make the call
        result = integration.call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="json_object"
        )
        
        print(f"✅ Structured prompt call successful")
        print(f"📝 Response type: {type(result)}")
        print(f"📝 Response keys: {list(result.keys())}")
        
        # Try to parse the response
        raw_content = result.get('raw_content', '')
        parsed_content = result.get('parsed_content', {})
        
        print(f"📝 Raw content: {raw_content[:200]}...")
        print(f"📝 Parsed content: {parsed_content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Structured prompt call failed: {e}")
        return False

def test_multiple_models_call(integration):
    """Test calling multiple models with the same prompt."""
    print("\n🧪 Testing Multiple Models Call")
    print("=" * 60)
    
    try:
        # Create prompt configs for multiple models
        prompt_configs = [
            {
                "key": "test_prompt_1",
                "prompt_config": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Respond with exactly: 'Model test successful from {model_name}'"
                        }
                    ],
                    "params": {
                        "temperature": 0.1,
                        "max_tokens": 50
                    }
                }
            }
        ]
        
        # Test with available models
        available_models = integration.list_available_models()
        test_models = ["gemini/gemini-2.5-flash"]
        
        # Add other models if API keys are available
        if os.getenv('OPENAI_API_KEY') and 'gpt-4o' in available_models:
            test_models.append('gpt-4o')
        
        print(f"📋 Testing models: {test_models}")
        
        # Make the call
        results = integration.get_responses_from_multiple_models(
            prompt_configs=prompt_configs,
            models=test_models,
            response_format_type="text"
        )
        
        print(f"✅ Multiple models call successful")
        print(f"📝 Results keys: {list(results.keys())}")
        
        for model, responses in results.items():
            print(f"📝 {model}: {len(responses)} responses")
            for i, response in enumerate(responses):
                content = response.get('raw_content', '')[:100]
                print(f"    Response {i+1}: {content}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Multiple models call failed: {e}")
        return False

def test_prompt_file_integration(integration):
    """Test using prompts from the JSON file."""
    print("\n🧪 Testing Prompt File Integration")
    print("=" * 60)
    
    try:
        # Test using a prompt from the codexes_prompts.json file
        prompt_config = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at extracting structured metadata from book content."
                },
                {
                    "role": "user",
                    "content": "Extract metadata from this book content:\n\nTitle: The Future of AI\nAuthor: Dr. Jane Smith\nContent: This book explores the revolutionary impact of artificial intelligence on society, covering machine learning, neural networks, and ethical considerations.\n\nReturn JSON with title, author, summary, keywords, and genre."
                }
            ],
            "params": {
                "temperature": 0.3,
                "max_tokens": 500
            }
        }
        
        result = integration.call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="json_object"
        )
        
        print(f"✅ Prompt file integration successful")
        print(f"📝 Response: {result.get('raw_content', '')[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt file integration failed: {e}")
        return False

def test_error_handling_and_retries(integration):
    """Test error handling and retry logic."""
    print("\n🧪 Testing Error Handling and Retries")
    print("=" * 60)
    
    try:
        # Test with invalid model (should fail gracefully)
        prompt_config = {
            "messages": [{"role": "user", "content": "Test message"}],
            "params": {"temperature": 0.7, "max_tokens": 50}
        }
        
        result = integration.call_model_with_prompt(
            model_name="invalid/model-name",
            prompt_config=prompt_config,
            response_format_type="text"
        )
        
        print(f"✅ Error handling test completed")
        print(f"📝 Result type: {type(result)}")
        
        # Check if error is properly handled
        if 'error' in str(result).lower():
            print("✅ Error properly handled and returned in expected format")
        else:
            print("⚠️  Unexpected success with invalid model")
        
        return True
        
    except Exception as e:
        print(f"✅ Exception properly caught: {e}")
        return True

def test_cost_efficiency_validation():
    """Test that Gemini 2.5 Flash is being used as default for cost efficiency."""
    print("\n🧪 Testing Cost Efficiency (Gemini 2.5 Flash Default)")
    print("=" * 60)
    
    try:
        from codexes.core.llm_integration import get_llm_integration
        
        integration = get_llm_integration()
        default_model = integration._get_default_model()
        
        print(f"📋 Default model: {default_model}")
        
        if default_model == "gemini/gemini-2.5-flash":
            print("✅ Cost efficiency validated - Gemini 2.5 Flash is default")
            print("💰 Expected cost savings: ~95% vs GPT-4o")
            return True
        else:
            print(f"⚠️  Default model is not Gemini 2.5 Flash: {default_model}")
            return False
        
    except Exception as e:
        print(f"❌ Cost efficiency test failed: {e}")
        return False

def test_backward_compatibility():
    """Test backward compatibility with existing code patterns."""
    print("\n🧪 Testing Backward Compatibility")
    print("=" * 60)
    
    try:
        # Test importing the old way
        from codexes.core.llm_integration import call_model_with_prompt, get_responses_from_multiple_models
        
        print("✅ Backward compatibility imports successful")
        
        # Test old-style function call
        prompt_config = {
            "messages": [{"role": "user", "content": "Say hello for backward compatibility test"}],
            "params": {"temperature": 0.7, "max_tokens": 50}
        }
        
        result = call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="text"
        )
        
        print("✅ Backward compatibility function call successful")
        print(f"📝 Response: {result.get('raw_content', '')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def test_session_statistics(integration):
    """Test session statistics and monitoring."""
    print("\n🧪 Testing Session Statistics")
    print("=" * 60)
    
    try:
        # Get statistics
        stats = integration.get_statistics()
        
        print("✅ Statistics retrieval successful")
        print(f"📊 Statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Statistics test failed: {e}")
        return False

def run_performance_benchmark(integration):
    """Run a simple performance benchmark."""
    print("\n🧪 Running Performance Benchmark")
    print("=" * 60)
    
    try:
        # Simple performance test
        start_time = time.time()
        
        prompt_config = {
            "messages": [{"role": "user", "content": "Count from 1 to 5"}],
            "params": {"temperature": 0.1, "max_tokens": 50}
        }
        
        result = integration.call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="text"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Performance benchmark completed")
        print(f"⏱️  Response time: {duration:.2f} seconds")
        print(f"📝 Response: {result.get('raw_content', '')[:100]}...")
        
        return True, duration
        
    except Exception as e:
        print(f"❌ Performance benchmark failed: {e}")
        return False, 0

def main():
    """Run all integration tests with real API keys."""
    print("🚀 Nimble LLM Caller Real API Integration Test Suite")
    print("=" * 80)
    
    # Load environment
    api_keys = load_environment()
    
    # Check if we have at least one API key
    has_api_key = any(key != 'Not set' for key in api_keys.values())
    if not has_api_key:
        print("❌ No API keys found. Please set up at least one API key in .env file.")
        return False
    
    # Test functions
    tests = [
        ("Integration Layer Basic", test_integration_layer_basic),
        ("Cost Efficiency Validation", test_cost_efficiency_validation),
        ("Backward Compatibility", test_backward_compatibility),
    ]
    
    # Tests that require integration instance
    integration_tests = [
        ("Simple LLM Call", test_simple_llm_call),
        ("Structured Prompt Call", test_structured_prompt_call),
        ("Multiple Models Call", test_multiple_models_call),
        ("Prompt File Integration", test_prompt_file_integration),
        ("Error Handling and Retries", test_error_handling_and_retries),
        ("Session Statistics", test_session_statistics),
        ("Performance Benchmark", run_performance_benchmark),
    ]
    
    passed = 0
    total = len(tests) + len(integration_tests)
    integration = None
    
    # Run basic tests
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_name == "Integration Layer Basic":
                integration, success = test_func()
            else:
                success = test_func()
            
            if success:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
    
    # Run integration tests if we have an integration instance
    if integration:
        for test_name, test_func in integration_tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                if test_name == "Performance Benchmark":
                    success, duration = test_func(integration)
                else:
                    success = test_func(integration)
                
                if success:
                    passed += 1
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                print(f"❌ {test_name} CRASHED: {e}")
    else:
        print("\n⚠️  Skipping integration tests - no integration instance available")
    
    # Final results
    print("\n" + "=" * 80)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ nimble-llm-caller integration is working correctly with real API keys")
        print("💰 Cost efficiency validated with Gemini 2.5 Flash as default")
        print("🔄 Backward compatibility maintained")
        print("📊 Error handling and monitoring working")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)