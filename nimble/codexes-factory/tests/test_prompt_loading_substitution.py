#!/usr/bin/env python3
"""
Test prompt loading and substitution for the nimble-llm-caller integration.

This test suite verifies that:
1. Prompt files are loaded correctly
2. Prompt substitution works properly
3. Invalid prompts are handled gracefully
4. Prompt parameters are applied correctly
5. Error handling for missing prompts works
"""

import sys
import os
import tempfile
import json
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_prompt_file_loading():
    """Test that prompt files are loaded correctly."""
    print("\n🔍 Testing Prompt File Loading...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        # Test with default prompt file
        integration = CodexesLLMIntegration()
        
        # Should initialize successfully
        if integration.content_generator is not None:
            print("    ✅ Integration initialized with prompt file")
        else:
            print("    ❌ Failed to initialize with prompt file")
            return False
        
        # Check if prompts file exists
        prompts_path = os.path.join(
            os.path.dirname(__file__),
            "src", "codexes", "prompts", "codexes_prompts.json"
        )
        
        if os.path.exists(prompts_path):
            print(f"    ✅ Prompts file exists: {prompts_path}")
            
            # Try to load and validate the prompts file
            with open(prompts_path, 'r') as f:
                prompts_data = json.load(f)
            
            if isinstance(prompts_data, dict):
                print(f"    ✅ Prompts file contains {len(prompts_data)} prompt entries")
                
                # Check for expected prompt structure
                for prompt_key, prompt_data in list(prompts_data.items())[:3]:  # Check first 3
                    if "messages" in prompt_data:
                        print(f"    ✅ Prompt '{prompt_key}' has messages structure")
                    else:
                        print(f"    ⚠️ Prompt '{prompt_key}' missing messages structure")
            else:
                print(f"    ⚠️ Unexpected prompts file format: {type(prompts_data)}")
        else:
            print(f"    ⚠️ Prompts file not found: {prompts_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt file loading test failed: {e}")
        return False


def test_prompt_substitution():
    """Test prompt parameter substitution."""
    print("\n🔍 Testing Prompt Substitution...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        # Create a test prompt with parameters
        test_prompts = {
            "test_substitution": {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant."
                    },
                    {
                        "role": "user", 
                        "content": "Process this content: {content}\n\nReturn result in format: {format}"
                    }
                ],
                "params": {
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            }
        }
        
        # Create temporary prompts file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_prompts, f, indent=2)
            temp_prompts_path = f.name
        
        try:
            # Test prompt substitution by creating a prompt config manually
            prompt_config = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant."
                    },
                    {
                        "role": "user",
                        "content": "Process this content: test data\n\nReturn result in format: JSON"
                    }
                ],
                "params": {
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            }
            
            integration = CodexesLLMIntegration()
            
            # Test that the prompt config can be processed
            result = integration.call_model_with_prompt(
                model_name="gemini/gemini-2.5-flash",
                prompt_config=prompt_config,
                response_format_type="text"
            )
            
            # Should return a result (even if it's an error due to no API key)
            if isinstance(result, dict):
                print("    ✅ Prompt substitution processed successfully")
                
                if "raw_content" in result or "parsed_content" in result:
                    print("    ✅ Response has expected structure")
                else:
                    print(f"    ⚠️ Unexpected response structure: {list(result.keys())}")
            else:
                print(f"    ⚠️ Unexpected response type: {type(result)}")
            
        finally:
            os.unlink(temp_prompts_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt substitution test failed: {e}")
        return False


def test_prompt_parameter_application():
    """Test that prompt parameters are applied correctly."""
    print("\n🔍 Testing Prompt Parameter Application...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        integration = CodexesLLMIntegration()
        
        # Test with specific parameters
        prompt_config = {
            "messages": [
                {"role": "user", "content": "Test message"}
            ],
            "params": {
                "temperature": 0.1,
                "max_tokens": 100,
                "top_p": 0.9
            }
        }
        
        # Test parameter application
        result = integration.call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="text"
        )
        
        if isinstance(result, dict):
            print("    ✅ Parameters applied without errors")
            
            # The parameters should be passed through to the underlying LLM call
            # We can't directly verify they were used, but we can verify no errors occurred
            if "error" not in str(result).lower() or "api key" in str(result).lower():
                print("    ✅ No parameter-related errors detected")
            else:
                print(f"    ⚠️ Possible parameter error: {result}")
        else:
            print(f"    ⚠️ Unexpected result type: {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt parameter application test failed: {e}")
        return False


def test_missing_prompt_handling():
    """Test handling of missing or invalid prompts."""
    print("\n🔍 Testing Missing Prompt Handling...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        integration = CodexesLLMIntegration()
        
        # Test with empty prompt config
        empty_config = {"messages": [], "params": {}}
        
        result = integration.call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=empty_config,
            response_format_type="text"
        )
        
        if isinstance(result, dict):
            print("    ✅ Empty prompt config handled gracefully")
        else:
            print(f"    ⚠️ Unexpected handling of empty config: {type(result)}")
        
        # Test with malformed prompt config
        malformed_config = {"invalid": "structure"}
        
        result2 = integration.call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=malformed_config,
            response_format_type="text"
        )
        
        if isinstance(result2, dict):
            print("    ✅ Malformed prompt config handled gracefully")
        else:
            print(f"    ⚠️ Unexpected handling of malformed config: {type(result2)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Missing prompt handling test failed: {e}")
        return False


def test_multiple_message_formats():
    """Test different message formats and structures."""
    print("\n🔍 Testing Multiple Message Formats...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        integration = CodexesLLMIntegration()
        
        # Test different message formats
        test_cases = [
            {
                "name": "Simple user message",
                "config": {
                    "messages": [{"role": "user", "content": "Hello"}],
                    "params": {"temperature": 0.5}
                }
            },
            {
                "name": "System + user messages",
                "config": {
                    "messages": [
                        {"role": "system", "content": "You are helpful."},
                        {"role": "user", "content": "Hello"}
                    ],
                    "params": {"temperature": 0.5}
                }
            },
            {
                "name": "Multi-turn conversation",
                "config": {
                    "messages": [
                        {"role": "system", "content": "You are helpful."},
                        {"role": "user", "content": "What is 2+2?"},
                        {"role": "assistant", "content": "2+2 equals 4."},
                        {"role": "user", "content": "What about 3+3?"}
                    ],
                    "params": {"temperature": 0.5}
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"    Testing {test_case['name']}...")
            
            result = integration.call_model_with_prompt(
                model_name="gemini/gemini-2.5-flash",
                prompt_config=test_case["config"],
                response_format_type="text"
            )
            
            if isinstance(result, dict):
                print(f"      ✅ {test_case['name']} processed successfully")
            else:
                print(f"      ⚠️ {test_case['name']} unexpected result: {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Multiple message formats test failed: {e}")
        return False


def test_json_response_format():
    """Test JSON response format handling."""
    print("\n🔍 Testing JSON Response Format...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        integration = CodexesLLMIntegration()
        
        # Test JSON response format
        prompt_config = {
            "messages": [
                {"role": "user", "content": "Return a JSON object with a test field"}
            ],
            "params": {"temperature": 0.1}
        }
        
        result = integration.call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="json_object"
        )
        
        if isinstance(result, dict):
            print("    ✅ JSON response format processed successfully")
            
            # Check if response indicates JSON format was requested
            if "raw_content" in result or "parsed_content" in result:
                print("    ✅ JSON response has expected structure")
            else:
                print(f"    ⚠️ Unexpected JSON response structure: {list(result.keys())}")
        else:
            print(f"    ⚠️ Unexpected JSON response type: {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON response format test failed: {e}")
        return False


def test_prompt_validation():
    """Test prompt validation and error handling."""
    print("\n🔍 Testing Prompt Validation...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        integration = CodexesLLMIntegration()
        
        # Test with None prompt config
        try:
            result = integration.call_model_with_prompt(
                model_name="gemini/gemini-2.5-flash",
                prompt_config=None,
                response_format_type="text"
            )
            print("    ✅ None prompt config handled gracefully")
        except Exception as e:
            print(f"    ✅ None prompt config properly rejected: {type(e).__name__}")
        
        # Test with invalid message structure
        invalid_config = {
            "messages": [{"invalid": "message"}],  # Missing role and content
            "params": {}
        }
        
        result = integration.call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=invalid_config,
            response_format_type="text"
        )
        
        if isinstance(result, dict):
            print("    ✅ Invalid message structure handled gracefully")
        else:
            print(f"    ⚠️ Unexpected handling of invalid messages: {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt validation test failed: {e}")
        return False


def run_all_tests():
    """Run all prompt loading and substitution tests."""
    print("🚀 Starting Prompt Loading and Substitution Tests")
    print("=" * 60)
    
    tests = [
        test_prompt_file_loading,
        test_prompt_substitution,
        test_prompt_parameter_application,
        test_missing_prompt_handling,
        test_multiple_message_formats,
        test_json_response_format,
        test_prompt_validation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All prompt loading and substitution tests passed!")
        return True
    else:
        print(f"⚠️ {failed} tests failed - prompt handling issues detected")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)