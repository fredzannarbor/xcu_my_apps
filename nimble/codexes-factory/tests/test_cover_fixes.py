#!/usr/bin/env python3
"""
Test script to verify cover fixes work correctly.
Tests both variable substitution and Korean text handling.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from codexes.modules.covers.cover_generator import substitute_template_variables, _escape_latex_preserve_korean

def test_variable_substitution():
    """Test that template variables are properly substituted."""
    
    print("Testing Variable Substitution...")
    print("=" * 50)
    
    # Test data similar to what's in the CSV
    test_data = {
        'title': 'Martian Self-Reliance: Isolation versus Earth Support',
        'author': 'AI Lab for Book-Lovers',
        'imprint': 'xynapse traces',
        'quotes_per_book': 90,
        'storefront_publishers_note_en': 'A profound exploration of independence and support systems'
    }
    
    test_cases = [
        {
            'input': 'Uncover the depths of {stream} with {title}.',
            'expected': 'Uncover the depths of Martian Self-Reliance: Isolation versus Earth Support with Martian Self-Reliance: Isolation versus Earth Support.',
            'description': 'Basic variable substitution'
        },
        {
            'input': 'This book contains {quotes_per_book} quotations by {author}.',
            'expected': 'This book contains 90 quotations by AI Lab for Book-Lovers.',
            'description': 'Multiple variable types'
        },
        {
            'input': 'Published by {imprint}, this explores {description}.',
            'expected': 'Published by xynapse traces, this explores A profound exploration of independence and support systems.',
            'description': 'Description fallback'
        },
        {
            'input': 'No variables here.',
            'expected': 'No variables here.',
            'description': 'No variables to substitute'
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Input:    {test_case['input']}")
        
        result = substitute_template_variables(test_case['input'], test_data)
        print(f"Output:   {result}")
        print(f"Expected: {test_case['expected']}")
        
        if result == test_case['expected']:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            all_passed = False
    
    return all_passed

def test_korean_text_preservation():
    """Test that Korean LaTeX commands are preserved during escaping."""
    
    print("\n\nTesting Korean Text Preservation...")
    print("=" * 50)
    
    test_cases = [
        {
            'input': '\\korean{필사}',
            'expected': '\\korean{필사}',
            'description': 'Simple Korean command'
        },
        {
            'input': 'This is \\korean{필사} text.',
            'expected': 'This is \\korean{필사} text.',
            'description': 'Korean command in English text'
        },
        {
            'input': 'Special & characters % need escaping but \\korean{필사} should not.',
            'expected': 'Special \\& characters \\% need escaping but \\korean{필사} should not.',
            'description': 'Mixed escaping and Korean preservation'
        },
        {
            'input': 'Multiple \\korean{필사} and \\korean{한글} commands.',
            'expected': 'Multiple \\korean{필사} and \\korean{한글} commands.',
            'description': 'Multiple Korean commands'
        },
        {
            'input': 'No Korean here, just & % # special chars.',
            'expected': 'No Korean here, just \\& \\% \\# special chars.',
            'description': 'Only escaping, no Korean'
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Input:    {test_case['input']}")
        
        result = _escape_latex_preserve_korean(test_case['input'])
        print(f"Output:   {result}")
        print(f"Expected: {test_case['expected']}")
        
        if result == test_case['expected']:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            all_passed = False
    
    return all_passed

def test_integration():
    """Test both fixes working together."""
    
    print("\n\nTesting Integration...")
    print("=" * 50)
    
    test_data = {
        'title': 'Korean Study Guide',
        'quotes_per_book': 50,
        'author': 'Language Expert'
    }
    
    # Simulate back cover text with both variables and Korean commands
    back_cover_text = "Discover {title} with {quotes_per_book} quotes. Features \\korean{필사} practice & meditation."
    
    print(f"Original: {back_cover_text}")
    
    # Step 1: Variable substitution
    step1 = substitute_template_variables(back_cover_text, test_data)
    print(f"After variable substitution: {step1}")
    
    # Step 2: Korean-aware escaping
    step2 = _escape_latex_preserve_korean(step1)
    print(f"After Korean-aware escaping: {step2}")
    
    expected = "Discover Korean Study Guide with 50 quotes. Features \\korean{필사} practice \\& meditation."
    
    if step2 == expected:
        print("✅ INTEGRATION TEST PASSED")
        return True
    else:
        print("❌ INTEGRATION TEST FAILED")
        print(f"Expected: {expected}")
        return False

if __name__ == "__main__":
    print("Cover Fixes Test Suite")
    print("=" * 60)
    
    # Run all tests
    var_test_passed = test_variable_substitution()
    korean_test_passed = test_korean_text_preservation()
    integration_test_passed = test_integration()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"Variable Substitution: {'✅ PASSED' if var_test_passed else '❌ FAILED'}")
    print(f"Korean Text Preservation: {'✅ PASSED' if korean_test_passed else '❌ FAILED'}")
    print(f"Integration Test: {'✅ PASSED' if integration_test_passed else '❌ FAILED'}")
    
    if var_test_passed and korean_test_passed and integration_test_passed:
        print("\n🎉 ALL TESTS PASSED! Cover fixes are working correctly.")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED! Please check the cover fix implementation.")
        sys.exit(1)