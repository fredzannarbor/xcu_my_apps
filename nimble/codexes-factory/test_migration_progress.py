#!/usr/bin/env python3
"""
Test script to verify the migration progress and functionality.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_updated_modules():
    """Test that updated modules import correctly."""
    print("Testing updated module imports...")
    
    modules_to_test = [
        ("codexes.modules.builders.llm_get_book_data", "generate_back_cover_text"),
        ("codexes.pages.9_Imprint_Builder", None),  # Just test import
        ("codexes.modules.distribution.llm_field_completer", "LLMFieldCompleter"),
        ("codexes.modules.distribution.enhanced_llm_field_completer", "EnhancedLLMFieldCompleter"),
        ("codexes.modules.metadata.metadata_generator", "generate_metadata_from_pdf"),
    ]
    
    success_count = 0
    
    for module_name, function_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[function_name] if function_name else [])
            if function_name:
                getattr(module, function_name)
            print(f"✅ {module_name} imports successfully")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module_name} import failed: {e}")
        except AttributeError as e:
            print(f"❌ {module_name}.{function_name} not found: {e}")
        except Exception as e:
            print(f"⚠️  {module_name} import issue: {e}")
    
    print(f"\nModule import results: {success_count}/{len(modules_to_test)} successful")
    return success_count == len(modules_to_test)

def test_integration_functionality():
    """Test that the integration layer functions work correctly."""
    print("\nTesting integration layer functionality...")
    
    try:
        from codexes.core.llm_integration import (
            call_model_with_prompt,
            get_responses_from_multiple_models,
            get_llm_integration
        )
        
        # Test getting the integration instance
        integration = get_llm_integration()
        print("✅ Integration instance created successfully")
        
        # Test configuration validation
        validation = integration.validate_configuration()
        print(f"✅ Configuration validation: {len(validation['models_available'])} models available")
        
        # Test statistics
        stats = integration.get_statistics()
        print(f"✅ Statistics retrieved: {type(stats)}")
        
        # Test model listing
        models = integration.list_available_models()
        print(f"✅ Available models: {models}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration functionality test failed: {e}")
        return False

def test_backward_compatibility():
    """Test that the backward compatibility functions maintain the correct interface."""
    print("\nTesting backward compatibility...")
    
    try:
        from codexes.core.llm_integration import call_model_with_prompt, get_responses_from_multiple_models
        
        # Test call_model_with_prompt signature
        prompt_config = {
            "messages": [{"role": "user", "content": "Test message"}],
            "params": {"temperature": 0.7}
        }
        
        # This should not crash even without API keys (will return error response)
        result = call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="text"
        )
        
        # Check response format
        if isinstance(result, dict) and "parsed_content" in result and "raw_content" in result:
            print("✅ call_model_with_prompt maintains correct interface")
        else:
            print(f"❌ call_model_with_prompt interface changed: {type(result)}")
            return False
        
        # Test get_responses_from_multiple_models signature
        prompt_configs = [
            {
                "key": "test_prompt",
                "prompt_config": prompt_config
            }
        ]
        
        batch_result = get_responses_from_multiple_models(
            prompt_configs=prompt_configs,
            models=["gemini/gemini-2.5-flash"],
            response_format_type="text"
        )
        
        # Check response format
        if isinstance(batch_result, dict):
            print("✅ get_responses_from_multiple_models maintains correct interface")
        else:
            print(f"❌ get_responses_from_multiple_models interface changed: {type(batch_result)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def test_prompts_loading():
    """Test that prompts are loading correctly."""
    print("\nTesting prompts loading...")
    
    try:
        from codexes.core.llm_integration import get_llm_integration
        
        integration = get_llm_integration()
        
        # Check if prompts are loaded
        if hasattr(integration.content_generator, 'prompt_manager'):
            prompt_manager = integration.content_generator.prompt_manager
            prompt_keys = prompt_manager.list_prompt_keys()
            
            if prompt_keys:
                print(f"✅ Prompts loaded successfully: {len(prompt_keys)} prompts")
                print(f"   Sample prompts: {prompt_keys[:3]}")
                return True
            else:
                print("⚠️  No prompts loaded")
                return False
        else:
            print("⚠️  Prompt manager not accessible")
            return False
            
    except Exception as e:
        print(f"❌ Prompts loading test failed: {e}")
        return False

def main():
    """Run all migration tests."""
    print("🧪 Testing LLM Integration Migration Progress")
    print("=" * 50)
    
    tests = [
        test_updated_modules,
        test_integration_functionality,
        test_backward_compatibility,
        test_prompts_loading
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Migration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All migration tests passed! Integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)