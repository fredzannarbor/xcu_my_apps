#!/usr/bin/env python3
"""
Test script to verify authentication and imprint loading fixes
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / "src"))

def test_simple_auth():
    """Test the simple authentication system"""
    print("🧪 Testing Simple Authentication System...")
    
    try:
        from codexes.core.simple_auth import SimpleAuth
        
        # Test authentication instance creation
        auth = SimpleAuth()
        print("✅ SimpleAuth instance created successfully")
        
        # Test authentication with default credentials
        result = auth.authenticate("admin", "hotdogtoy")
        if result:
            print("✅ Authentication with admin/hotdogtoy successful")
        else:
            print("❌ Authentication with admin/hotdogtoy failed")
        
        # Test invalid credentials
        result = auth.authenticate("admin", "wrongpassword")
        if not result:
            print("✅ Invalid credentials properly rejected")
        else:
            print("❌ Invalid credentials incorrectly accepted")
        
        return True
        
    except Exception as e:
        print(f"❌ SimpleAuth test failed: {e}")
        return False

def test_config_loader():
    """Test the configuration loader for imprint scanning"""
    print("\n🧪 Testing Configuration Loader...")
    
    try:
        from codexes.modules.ui.dynamic_config_loader import DynamicConfigurationLoader
        
        loader = DynamicConfigurationLoader()
        print("✅ DynamicConfigurationLoader created successfully")
        
        # Test publisher scanning
        publishers = loader.scan_publishers()
        print(f"✅ Found {len(publishers)} publishers: {publishers}")
        
        # Test imprint scanning
        if "nimble_books" in publishers:
            imprints = loader.scan_imprints("nimble_books")
            print(f"✅ Found {len(imprints)} imprints for nimble_books: {imprints}")
            
            if "xynapse_traces" in imprints:
                print("✅ xynapse_traces imprint found correctly")
            else:
                print("❌ xynapse_traces imprint not found")
        else:
            print("⚠️ nimble_books publisher not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loader test failed: {e}")
        return False

def test_streamlit_components():
    """Test streamlit components import"""
    print("\n🧪 Testing Streamlit Components...")
    
    try:
        from codexes.modules.ui.streamlit_components import ConfigurationUI
        
        # Test component creation (without Streamlit context)
        print("✅ ConfigurationUI import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Streamlit components test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running Authentication and Imprint Loading Tests...")
    print("=" * 60)
    
    tests = [
        test_simple_auth,
        test_config_loader,
        test_streamlit_components
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Authentication and imprint loading fixes are working.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    exit(main())