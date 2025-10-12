#!/usr/bin/env python3
"""
Final comprehensive test for Streamlit application
"""
import sys
import subprocess
import time
import requests
from pathlib import Path

def test_streamlit_startup():
    """Test that Streamlit starts without errors"""
    print("🧪 Testing Streamlit startup...")
    
    try:
        # Start Streamlit in background
        process = subprocess.Popen(
            ["./start_streamlit.sh"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for startup
        time.sleep(10)
        
        # Test if server is responding
        try:
            response = requests.get("http://localhost:8502", timeout=5)
            if response.status_code == 200:
                print("✅ Streamlit server is running and responding")
                success = True
            else:
                print(f"❌ Server responded with status code: {response.status_code}")
                success = False
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to server: {e}")
            success = False
        
        # Stop the process
        process.terminate()
        process.wait(timeout=5)
        
        return success
        
    except Exception as e:
        print(f"❌ Error during startup test: {e}")
        return False

def test_ui_components():
    """Test UI component imports"""
    print("🧪 Testing UI component imports...")
    
    try:
        result = subprocess.run(
            ["uv", "run", "python", "test_ui_imports.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ All UI components import successfully")
            return True
        else:
            print(f"❌ UI component import failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing UI components: {e}")
        return False

def test_page_imports():
    """Test all Streamlit page imports"""
    print("🧪 Testing Streamlit page imports...")
    
    try:
        result = subprocess.run(
            ["uv", "run", "python", "test_streamlit_pages.py"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ All Streamlit pages import successfully")
            return True
        else:
            print(f"❌ Page import test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing page imports: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running comprehensive Streamlit tests...\n")
    
    tests = [
        ("UI Components", test_ui_components),
        ("Page Imports", test_page_imports),
        ("Streamlit Startup", test_streamlit_startup),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not success:
            all_passed = False
    
    print("="*50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Streamlit application is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())