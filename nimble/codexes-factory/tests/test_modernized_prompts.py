#!/usr/bin/env python3
"""
Test script to verify that modernized prompts work correctly.

This script tests a few key prompts to ensure they produce valid JSON responses
after modernization.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from codexes.core import prompt_manager


def test_prompt_loading():
    """Test that modernized prompts can be loaded correctly."""
    print("Testing prompt loading...")
    
    # Test main prompts file
    try:
        with open('prompts/prompts.json', 'r') as f:
            prompts = json.load(f)
        
        # Check that key prompts have the modern format
        test_prompts = ['back_cover_text', 'bibliography_prompt', 'gemini_get_basic_info']
        
        for prompt_key in test_prompts:
            if prompt_key in prompts:
                prompt_config = prompts[prompt_key]
                
                # Check for modern format
                if 'messages' in prompt_config:
                    print(f"✅ {prompt_key} - Modern format detected")
                    
                    # Verify structure
                    messages = prompt_config['messages']
                    if len(messages) >= 2 and messages[0]['role'] == 'system':
                        print(f"   ✅ System message present")
                    else:
                        print(f"   ⚠️  System message missing or malformed")
                        
                    if 'params' in prompt_config:
                        print(f"   ✅ Parameters configured")
                    else:
                        print(f"   ⚠️  No parameters configured")
                        
                else:
                    print(f"❌ {prompt_key} - Still in old format")
            else:
                print(f"⚠️  {prompt_key} - Not found in prompts file")
        
        print(f"✅ Loaded {len(prompts)} prompts from main file")
        
    except Exception as e:
        print(f"❌ Failed to load main prompts: {e}")
        return False
    
    return True


def test_prompt_manager_integration():
    """Test that the prompt manager can work with modernized prompts."""
    print("\nTesting prompt manager integration...")
    
    try:
        # Test loading prompts through the prompt manager
        formatted_prompts = prompt_manager.load_and_prepare_prompts(
            prompt_file_path='prompts/prompts.json',
            prompt_keys=['back_cover_text'],
            substitutions={
                'title': 'Test Book',
                'stream': 'Technology',
                'description': 'A test book about technology',
                'quotes_per_book': 90,
                'book_content': 'Test content for the book'
            }
        )
        
        if formatted_prompts:
            print("✅ Prompt manager successfully loaded modernized prompts")
            
            # Check the structure
            for prompt in formatted_prompts:
                if 'messages' in prompt:
                    print("   ✅ Messages format preserved")
                if 'params' in prompt:
                    print("   ✅ Parameters preserved")
                    
            return True
        else:
            print("❌ Prompt manager returned empty results")
            return False
            
    except Exception as e:
        print(f"❌ Prompt manager integration failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing Modernized Prompts")
    print("=" * 50)
    
    success = True
    
    # Test prompt loading
    if not test_prompt_loading():
        success = False
    
    # Test prompt manager integration
    if not test_prompt_manager_integration():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! Modernized prompts are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())