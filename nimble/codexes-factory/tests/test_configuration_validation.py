#!/usr/bin/env python3
"""
Test configuration loading and model selection for the nimble-llm-caller integration.

This test suite verifies that:
1. Configuration files are loaded correctly
2. Model validation works properly
3. Default model selection functions correctly
4. Invalid configurations are handled gracefully
5. Environment variable handling works
"""

import sys
import os
import tempfile
import json
import logging
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_default_configuration_loading():
    """Test that default configuration loads correctly."""
    print("\n🔍 Testing Default Configuration Loading...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        # Test with default configuration
        integration = CodexesLLMIntegration()
        
        # Should initialize successfully
        if integration.config_manager is not None:
            print("    ✅ Default configuration loaded successfully")
        else:
            print("    ❌ Failed to load default configuration")
            return False
        
        # Test getting default model
        default_model = integration._get_default_model()
        if default_model == "gemini/gemini-2.5-flash":
            print(f"    ✅ Default model is correct: {default_model}")
        else:
            print(f"    ⚠️ Unexpected default model: {default_model}")
        
        # Test listing available models
        available_models = integration.list_available_models()
        if isinstance(available_models, list):
            print(f"    ✅ Available models list returned: {len(available_models)} models")
            if len(available_models) > 0:
                print(f"    ✅ Models available: {available_models[:3]}...")  # Show first 3
            else:
                print("    ⚠️ No models available")
        else:
            print(f"    ⚠️ Unexpected available models type: {type(available_models)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Default configuration loading test failed: {e}")
        return False


def test_custom_configuration_loading():
    """Test loading custom configuration files."""
    print("\n🔍 Testing Custom Configuration Loading...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        # Create a temporary configuration file
        config_data = {
            "models": {
                "test-model": {
                    "provider": "openai",
                    "api_key_env": "TEST_API_KEY",
                    "default_params": {
                        "temperature": 0.5,
                        "max_tokens": 2000
                    }
                }
            },
            "output": {
                "default_format": "json",
                "save_raw_responses": True,
                "output_directory": "./test_output"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            config_path = f.name
        
        try:
            # Test loading custom configuration
            integration = CodexesLLMIntegration(config_path=config_path)
            
            if integration.config_manager is not None:
                print("    ✅ Custom configuration loaded successfully")
            else:
                print("    ❌ Failed to load custom configuration")
                return False
            
            # Test that custom models are available
            available_models = integration.list_available_models()
            if "test-model" in available_models:
                print("    ✅ Custom model found in available models")
            else:
                print(f"    ⚠️ Custom model not found. Available: {available_models}")
            
        finally:
            # Clean up temporary file
            os.unlink(config_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Custom configuration loading test failed: {e}")
        return False


def test_configuration_validation():
    """Test configuration validation functionality."""
    print("\n🔍 Testing Configuration Validation...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        integration = CodexesLLMIntegration()
        
        # Test configuration validation
        validation_results = integration.validate_configuration()
        
        if isinstance(validation_results, dict):
            print("    ✅ Configuration validation returned results")
            
            # Check expected keys
            expected_keys = ["valid", "issues", "models_available", "models_with_issues"]
            missing_keys = [key for key in expected_keys if key not in validation_results]
            
            if not missing_keys:
                print("    ✅ Validation results have all expected keys")
            else:
                print(f"    ⚠️ Missing validation keys: {missing_keys}")
            
            # Check if validation found any issues
            if validation_results.get("valid", False):
                print("    ✅ Configuration is valid")
            else:
                issues = validation_results.get("issues", [])
                print(f"    ⚠️ Configuration has issues: {len(issues)} issues found")
                for issue in issues[:3]:  # Show first 3 issues
                    print(f"        - {issue}")
            
            # Check models
            models_available = validation_results.get("models_available", [])
            print(f"    ℹ️ Models available: {len(models_available)}")
            
            models_with_issues = validation_results.get("models_with_issues", [])
            if models_with_issues:
                print(f"    ⚠️ Models with issues: {len(models_with_issues)}")
            else:
                print("    ✅ No models have validation issues")
        else:
            print(f"    ❌ Unexpected validation results type: {type(validation_results)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False


def test_invalid_configuration_handling():
    """Test handling of invalid configuration files."""
    print("\n🔍 Testing Invalid Configuration Handling...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        # Test with non-existent configuration file
        integration = CodexesLLMIntegration(config_path="/nonexistent/path.json")
        
        # Should still initialize with fallback
        if integration.config_manager is not None:
            print("    ✅ Gracefully handled non-existent config file")
        else:
            print("    ❌ Failed to handle non-existent config file")
            return False
        
        # Test with invalid JSON configuration
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json content")
            invalid_config_path = f.name
        
        try:
            integration2 = CodexesLLMIntegration(config_path=invalid_config_path)
            
            if integration2.config_manager is not None:
                print("    ✅ Gracefully handled invalid JSON config file")
            else:
                print("    ❌ Failed to handle invalid JSON config file")
                return False
                
        finally:
            os.unlink(invalid_config_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Invalid configuration handling test failed: {e}")
        return False


def test_model_selection():
    """Test model selection functionality."""
    print("\n🔍 Testing Model Selection...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        integration = CodexesLLMIntegration()
        
        # Test default model selection
        default_model = integration._get_default_model()
        if default_model:
            print(f"    ✅ Default model selected: {default_model}")
        else:
            print("    ❌ No default model selected")
            return False
        
        # Test that default model is Gemini 2.5 Flash (cost-effective)
        if "gemini" in default_model.lower() and "2.5" in default_model:
            print("    ✅ Default model is cost-effective Gemini 2.5 Flash")
        else:
            print(f"    ⚠️ Default model may not be cost-effective: {default_model}")
        
        # Test model availability check
        available_models = integration.list_available_models()
        if default_model in available_models:
            print("    ✅ Default model is available")
        else:
            print(f"    ⚠️ Default model not in available models list")
            print(f"        Available: {available_models[:5]}...")  # Show first 5
        
        return True
        
    except Exception as e:
        print(f"❌ Model selection test failed: {e}")
        return False


def test_environment_variable_handling():
    """Test environment variable handling for API keys."""
    print("\n🔍 Testing Environment Variable Handling...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        # Test with mock environment variables
        with patch.dict(os.environ, {
            'GOOGLE_API_KEY': 'test-google-key',
            'OPENAI_API_KEY': 'test-openai-key',
            'ANTHROPIC_API_KEY': 'test-anthropic-key'
        }):
            integration = CodexesLLMIntegration()
            
            # Should initialize successfully with API keys available
            if integration.config_manager is not None:
                print("    ✅ Integration initialized with environment variables")
            else:
                print("    ❌ Failed to initialize with environment variables")
                return False
            
            # Test configuration validation with API keys
            validation_results = integration.validate_configuration()
            
            # Should have fewer issues with API keys available
            issues = validation_results.get("issues", [])
            api_key_issues = [issue for issue in issues if "api" in issue.lower() or "key" in issue.lower()]
            
            if len(api_key_issues) == 0:
                print("    ✅ No API key issues with environment variables set")
            else:
                print(f"    ⚠️ Still have API key issues: {api_key_issues}")
        
        # Test without environment variables
        with patch.dict(os.environ, {}, clear=True):
            integration2 = CodexesLLMIntegration()
            
            if integration2.config_manager is not None:
                print("    ✅ Integration still works without environment variables")
            else:
                print("    ❌ Failed to initialize without environment variables")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Environment variable handling test failed: {e}")
        return False


def test_statistics_and_monitoring():
    """Test statistics and monitoring functionality."""
    print("\n🔍 Testing Statistics and Monitoring...")
    
    try:
        from codexes.core.llm_integration import CodexesLLMIntegration
        
        integration = CodexesLLMIntegration()
        
        # Test getting statistics
        stats = integration.get_statistics()
        
        if isinstance(stats, dict):
            print("    ✅ Statistics returned as dictionary")
            
            # Check for expected statistics keys
            if "error" not in stats:
                print("    ✅ No error in statistics")
            else:
                print(f"    ⚠️ Error in statistics: {stats['error']}")
        else:
            print(f"    ⚠️ Unexpected statistics type: {type(stats)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Statistics and monitoring test failed: {e}")
        return False


def run_all_tests():
    """Run all configuration validation tests."""
    print("🚀 Starting Configuration Validation Tests")
    print("=" * 60)
    
    tests = [
        test_default_configuration_loading,
        test_custom_configuration_loading,
        test_configuration_validation,
        test_invalid_configuration_handling,
        test_model_selection,
        test_environment_variable_handling,
        test_statistics_and_monitoring
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
        print("🎉 All configuration validation tests passed!")
        return True
    else:
        print(f"⚠️ {failed} tests failed - configuration issues detected")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)