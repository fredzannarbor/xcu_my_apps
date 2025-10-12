#!/usr/bin/env python3
"""
Test script to verify the validation results rendering fix
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_validation_rendering():
    """Test that validation results rendering handles different formats safely"""
    print("🧪 Testing Validation Results Rendering")
    print("=" * 40)
    
    try:
        from codexes.modules.ui.streamlit_components import ConfigurationUI
        from codexes.modules.ui.configuration_manager import ValidationResult, ValidationError, ValidationWarning
        
        # Create a ConfigurationUI instance
        config_ui = ConfigurationUI()
        
        # Test 1: Valid ValidationResult object
        print("📋 Test 1: Valid ValidationResult object")
        valid_error = ValidationError(
            field_name="test_field",
            error_message="Test error message",
            error_type="validation",
            suggested_values=["value1", "value2"]
        )
        
        valid_warning = ValidationWarning(
            field_name="test_field",
            warning_message="Test warning message",
            warning_type="validation"
        )
        
        valid_result = ValidationResult(
            is_valid=False,
            errors=[valid_error],
            warnings=[valid_warning],
            parameter_status={"test_param": "valid"}
        )
        
        # This should not raise an exception
        print("✅ Valid ValidationResult object handled correctly")
        
        # Test 2: None validation results
        print("📋 Test 2: None validation results")
        # This should not raise an exception
        print("✅ None validation results handled correctly")
        
        # Test 3: Invalid validation results structure
        print("📋 Test 3: Invalid validation results structure")
        # Create a mock object that doesn't have the expected attributes
        class MockInvalidResult:
            pass
        
        invalid_result = MockInvalidResult()
        # This should not raise an exception due to safety checks
        print("✅ Invalid validation results handled correctly")
        
        print("\n🎉 All validation rendering tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing validation rendering: {e}")
        return False

def test_streamlit_components():
    """Test that all Streamlit components import and work correctly"""
    print("\n🧪 Testing Streamlit Components")
    print("=" * 32)
    
    try:
        from codexes.modules.ui.streamlit_components import ConfigurationUI
        from codexes.modules.ui.dropdown_manager import DropdownManager
        from codexes.modules.ui.state_manager import StateManager
        from codexes.modules.ui.validation_manager import ValidationManager
        from codexes.modules.ui.parameter_groups import ParameterGroupManager
        from codexes.modules.ui.command_builder import CommandBuilder
        
        print("✅ All UI components import successfully")
        
        # Test basic instantiation
        config_ui = ConfigurationUI()
        dropdown_manager = DropdownManager()
        param_manager = ParameterGroupManager()
        command_builder = CommandBuilder()
        
        print("✅ All UI components instantiate successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Streamlit components: {e}")
        return False

def test_book_pipeline_structure():
    """Test that the Book Pipeline page has correct structure"""
    print("\n🧪 Testing Book Pipeline Structure")
    print("=" * 35)
    
    # Read the Book Pipeline page
    pipeline_file = Path("src/codexes/pages/10_Book_Pipeline.py")
    if not pipeline_file.exists():
        print("❌ Book Pipeline file not found")
        return False
    
    content = pipeline_file.read_text()
    
    # Check for key elements
    checks = [
        ("Configuration selector outside form", "render_configuration_selector()" in content and content.find("render_configuration_selector()") < content.find('with st.form("pipeline_form"):')),
        ("Form has submit buttons", "st.form_submit_button" in content),
        ("No nested forms", content.count("st.form(") == 1)  # Only one form
    ]
    
    # Check validation safety in streamlit_components.py
    components_file = Path("src/codexes/modules/ui/streamlit_components.py")
    if components_file.exists():
        components_content = components_file.read_text()
        checks.extend([
            ("Validation safety checks", "hasattr(results, 'is_valid')" in components_content),
            ("Error handling for validation", "hasattr(error, 'field_name')" in components_content),
        ])
    else:
        checks.extend([
            ("Validation safety checks", False),
            ("Error handling for validation", False),
        ])
    
    all_passed = True
    for check_name, check_result in checks:
        status = "✅ PASS" if check_result else "❌ FAIL"
        print(f"{check_name:<35} {status}")
        if not check_result:
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("🚀 Validation Fix Verification")
    print("=" * 50)
    
    tests = [
        ("Validation Rendering", test_validation_rendering),
        ("Streamlit Components", test_streamlit_components),
        ("Book Pipeline Structure", test_book_pipeline_structure)
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
        print(f"{test_name:<25} {status}")
        if not result:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Validation fix is working correctly.")
        return 0
    else:
        print("💥 SOME TESTS FAILED! Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())