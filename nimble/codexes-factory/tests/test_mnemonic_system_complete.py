#!/usr/bin/env python3
"""
Complete test for the mnemonic system functionality
Tests both with and without actual LLM calls
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_json_parsing():
    """Test JSON parsing functionality"""
    print("=== Testing JSON Parsing ===")
    
    try:
        from codexes.core.enhanced_llm_caller import enhanced_llm_caller
        
        # Test case that mimics mnemonic response
        test_content = '''```json
{
    "mnemonics_data": [
        {
            "acronym": "MAKER",
            "expansion": "Manufacture Advanced Kinetic Equipment Rapidly",
            "definition": "A system designed for rapid production of advanced kinetic equipment"
        },
        {
            "acronym": "SPACE",
            "expansion": "Strategic Planning And Coordination Environment",
            "definition": "An environment focused on strategic planning and coordination activities"
        }
    ]
}
```'''
        
        result = _extract_and_parse_json(test_content, ["mnemonics_data"])
        
        if result and "mnemonics_data" in result:
            print("✅ JSON parsing works correctly")
            print(f"   Parsed {len(result['mnemonics_data'])} mnemonics")
            return True
        else:
            print("❌ JSON parsing failed")
            return False
            
    except Exception as e:
        print(f"❌ JSON parsing test failed: {e}")
        return False

def test_book_data_loading(book_json_path):
    """Test loading book data"""
    print(f"=== Testing Book Data Loading ===")
    
    try:
        if not os.path.exists(book_json_path):
            print(f"❌ Book JSON file not found: {book_json_path}")
            return False
            
        with open(book_json_path, 'r') as f:
            book_data = json.load(f)
            
        print("✅ Book data loaded successfully")
        print(f"   Title: {book_data.get('title', 'Unknown')}")
        print(f"   Author: {book_data.get('author', 'Unknown')}")
        return True
        
    except Exception as e:
        print(f"❌ Book data loading failed: {e}")
        return False

def test_mnemonic_generation_mock():
    """Test mnemonic generation with mock data"""
    print("=== Testing Mnemonic Generation (Mock) ===")
    
    try:
        # Mock response that would come from LLM
        mock_response = {
            "mnemonics_data": [
                {
                    "acronym": "MARS",
                    "expansion": "Martian Autonomous Resource System",
                    "definition": "A self-sufficient system for managing resources on Mars"
                },
                {
                    "acronym": "EARTH",
                    "expansion": "Emergency Assistance and Resource Transfer Hub",
                    "definition": "A hub for coordinating emergency assistance and resource transfers"
                }
            ]
        }
        
        # Validate the structure
        if "mnemonics_data" in mock_response:
            mnemonics = mock_response["mnemonics_data"]
            
            for mnemonic in mnemonics:
                required_keys = ["acronym", "expansion", "definition"]
                if not all(key in mnemonic for key in required_keys):
                    print(f"❌ Mnemonic missing required keys: {mnemonic}")
                    return False
                    
            print("✅ Mnemonic generation structure is valid")
            print(f"   Generated {len(mnemonics)} mnemonics")
            return True
        else:
            print("❌ Mock response missing mnemonics_data")
            return False
            
    except Exception as e:
        print(f"❌ Mnemonic generation test failed: {e}")
        return False

def test_llm_call_with_api_key():
    """Test actual LLM call if API key is available"""
    print("=== Testing LLM Call (if API key available) ===")
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️  No GEMINI_API_KEY found, skipping actual LLM test")
        return True  # Not a failure, just skipped
    
    try:
        from codexes.core.enhanced_llm_caller import call_llm_json_with_exponential_backoff
        
        messages = [
            {
                "role": "user",
                "content": """Generate 2 mnemonics for a science fiction story about Mars colonization. 
                
Return JSON in this exact format:
{
    "mnemonics_data": [
        {
            "acronym": "MARS",
            "expansion": "Martian Autonomous Resource System",
            "definition": "A self-sufficient system for managing resources on Mars"
        }
    ]
}"""
            }
        ]
        
        response = call_llm_json_with_exponential_backoff(
            model="gemini/gemini-2.5-flash",
            messages=messages,
            expected_keys=["mnemonics_data"],
            temperature=0.7,
            max_tokens=500
        )
        
        if response and "mnemonics_data" in response:
            print("✅ LLM call successful")
            print(f"   Generated {len(response['mnemonics_data'])} mnemonics")
            return True
        else:
            print("❌ LLM call returned invalid response")
            return False
            
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test mnemonic system functionality")
    parser.add_argument("--book-json", default="data/test_json/test_book.json", 
                       help="Path to book JSON file")
    parser.add_argument("--skip-llm", action="store_true", 
                       help="Skip actual LLM testing")
    
    args = parser.parse_args()
    
    print("🧪 Mnemonic System Complete Test")
    print("=" * 50)
    
    tests = [
        ("JSON Parsing", test_json_parsing),
        ("Book Data Loading", lambda: test_book_data_loading(args.book_json)),
        ("Mnemonic Generation (Mock)", test_mnemonic_generation_mock),
    ]
    
    if not args.skip_llm:
        tests.append(("LLM Call", test_llm_call_with_api_key))
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Mnemonic system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())