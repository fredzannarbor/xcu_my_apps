#!/usr/bin/env python3
"""
Complete test to verify both form structure and dropdown functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_form_structure():
    """Test that the Book Pipeline page doesn't have nested forms"""
    print("🧪 Testing Form Structure")
    print("=" * 30)
    
    # Read the Book Pipeline page
    pipeline_file = Path("src/codexes/pages/10_Book_Pipeline.py")
    if not pipeline_file.exists():
        print("❌ Book Pipeline file not found")
        return False
    
    content = pipeline_file.read_text()
    
    # Check that configuration selector is outside the form
    config_selector_line = None
    form_start_line = None
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'render_configuration_selector()' in line:
            config_selector_line = i
        if 'with st.form("pipeline_form"):' in line:
            form_start_line = i
    
    if config_selector_line is None:
        print("❌ Configuration selector not found")
        return False
    
    if form_start_line is None:
        print("❌ Pipeline form not found")
        return False
    
    if config_selector_line < form_start_line:
        print("✅ Configuration selector is OUTSIDE the form (correct)")
        print(f"   - Config selector at line {config_selector_line + 1}")
        print(f"   - Form starts at line {form_start_line + 1}")
        return True
    else:
        print("❌ Configuration selector is INSIDE the form (incorrect)")
        print(f"   - Config selector at line {config_selector_line + 1}")
        print(f"   - Form starts at line {form_start_line + 1}")
        return False

def test_dropdown_functionality():
    """Test that dropdown manager works correctly"""
    print("\n🧪 Testing Dropdown Functionality")
    print("=" * 35)
    
    try:
        from codexes.modules.ui.dropdown_manager import DropdownManager
        
        # Create dropdown manager
        manager = DropdownManager()
        
        # Test publisher -> imprint mapping
        publisher = "nimble_books"
        print(f"📋 Testing publisher: {publisher}")
        
        # Get publisher name
        publisher_name = manager._get_publisher_name(publisher)
        print(f"📝 Publisher name from config: {publisher_name}")
        
        if publisher_name != "Nimble Books LLC":
            print(f"❌ Expected 'Nimble Books LLC', got '{publisher_name}'")
            return False
        
        # Get imprints
        imprints = manager.get_imprints_for_publisher(publisher)
        print(f"🏢 Found imprints: {imprints}")
        
        if "xynapse_traces" not in imprints:
            print("❌ xynapse_traces not found in imprints")
            return False
        
        print("✅ Dropdown functionality works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing dropdown functionality: {e}")
        return False

def test_streamlit_components():
    """Test that Streamlit components import correctly"""
    print("\n🧪 Testing Streamlit Components")
    print("=" * 32)
    
    try:
        from codexes.modules.ui.streamlit_components import ConfigurationUI
        from codexes.modules.ui.dropdown_manager import DropdownManager
        from codexes.modules.ui.state_manager import StateManager
        
        print("✅ All UI components import successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error importing UI components: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Complete UI Fix Verification")
    print("=" * 50)
    
    tests = [
        ("Form Structure", test_form_structure),
        ("Dropdown Functionality", test_dropdown_functionality),
        ("Streamlit Components", test_streamlit_components)
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
        print("🎉 ALL TESTS PASSED! UI fixes are working correctly.")
        return 0
    else:
        print("💥 SOME TESTS FAILED! Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())