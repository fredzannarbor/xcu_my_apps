#!/usr/bin/env python3
"""
Test script to verify configuration synchronization functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_configuration_synchronizer():
    """Test the ConfigurationSynchronizer class"""
    print("🧪 Testing Configuration Synchronizer")
    print("=" * 40)
    
    try:
        from codexes.modules.ui.config_synchronizer import ConfigurationSynchronizer
        
        # Create synchronizer instance
        sync = ConfigurationSynchronizer()
        
        # Test basic synchronization
        print("📋 Test 1: Basic synchronization")
        form_data = sync.sync_config_to_form("nimble_books", "xynapse_traces", "")
        
        expected_fields = ['publisher', 'imprint', 'tranche']
        for field in expected_fields:
            if field not in form_data:
                print(f"❌ Missing field: {field}")
                return False
        
        if form_data['publisher'] != 'nimble_books':
            print(f"❌ Expected publisher 'nimble_books', got '{form_data['publisher']}'")
            return False
            
        if form_data['imprint'] != 'xynapse_traces':
            print(f"❌ Expected imprint 'xynapse_traces', got '{form_data['imprint']}'")
            return False
        
        print("✅ Basic synchronization works")
        
        # Test sync status
        print("📋 Test 2: Sync status tracking")
        sync_status = sync.get_sync_status()
        
        if 'publisher' not in sync_status:
            print("❌ Publisher not in sync status")
            return False
            
        if sync_status['publisher'].source != 'configuration':
            print(f"❌ Expected publisher source 'configuration', got '{sync_status['publisher'].source}'")
            return False
        
        print("✅ Sync status tracking works")
        
        # Test user override
        print("📋 Test 3: User override tracking")
        sync.track_user_override('publisher', 'custom_publisher')
        
        override_status = sync.get_sync_status()
        if not override_status['publisher'].is_overridden:
            print("❌ User override not tracked")
            return False
        
        print("✅ User override tracking works")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing configuration synchronizer: {e}")
        return False

def test_configuration_aware_validator():
    """Test the ConfigurationAwareValidator class"""
    print("\n🧪 Testing Configuration-Aware Validator")
    print("=" * 45)
    
    try:
        from codexes.modules.ui.config_aware_validator import ConfigurationAwareValidator
        
        # Create validator instance
        validator = ConfigurationAwareValidator()
        
        # Test validation with empty form data but valid configuration
        print("📋 Test 1: Validation with configuration context")
        form_data = {
            'publisher': '',  # Empty in form
            'imprint': '',    # Empty in form
            'model': 'gemini/gemini-2.5-flash'
        }
        
        config_selection = {
            'publisher': 'nimble_books',    # Available in configuration
            'imprint': 'xynapse_traces',    # Available in configuration
            'tranche': ''
        }
        
        result = validator.validate_with_config_context(form_data, config_selection)
        
        # Should pass validation because configuration provides required values
        if not result.is_valid:
            # Check if errors are configuration-related
            config_related_errors = [
                error for error in result.errors 
                if error.field_name in ['publisher', 'imprint']
            ]
            
            if config_related_errors:
                print("❌ Validation failed for configuration-provided fields")
                for error in config_related_errors:
                    print(f"   - {error.field_name}: {error.error_message}")
                return False
        
        print("✅ Configuration-aware validation works")
        
        # Test validation with no configuration
        print("📋 Test 2: Validation without configuration")
        empty_config = {'publisher': '', 'imprint': '', 'tranche': ''}
        result_no_config = validator.validate_with_config_context(form_data, empty_config)
        
        # Should fail validation because no values provided
        if result_no_config.is_valid:
            print("❌ Validation should fail when no configuration provided")
            return False
        
        print("✅ Validation correctly fails without configuration")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing configuration-aware validator: {e}")
        return False

def test_book_pipeline_integration():
    """Test that Book Pipeline page integrates configuration synchronization"""
    print("\n🧪 Testing Book Pipeline Integration")
    print("=" * 38)
    
    # Check that the Book Pipeline page imports the synchronizer
    pipeline_file = Path("src/codexes/pages/10_Book_Pipeline.py")
    if not pipeline_file.exists():
        print("❌ Book Pipeline file not found")
        return False
    
    content = pipeline_file.read_text()
    
    checks = [
        ("Configuration synchronizer import", "config_synchronizer" in content),
        ("Sync data usage", "sync_config_to_form" in content),
        ("Configuration-aware validator", "ConfigurationAwareValidator" in content),
        ("Config context in validation", "config_selection" in content),
        ("Enhanced validation logic", "validate_with_config_context" in content)
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        status = "✅ PASS" if check_result else "❌ FAIL"
        print(f"{check_name:<35} {status}")
        if not check_result:
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("🚀 Configuration Synchronization Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration Synchronizer", test_configuration_synchronizer),
        ("Configuration-Aware Validator", test_configuration_aware_validator),
        ("Book Pipeline Integration", test_book_pipeline_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if not result:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Configuration synchronization is working.")
        print("\nThe application should now:")
        print("- Automatically populate publisher/imprint in core settings")
        print("- Pass validation when configuration is selected")
        print("- Show clear error messages with configuration context")
        return 0
    else:
        print("💥 SOME TESTS FAILED! Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())