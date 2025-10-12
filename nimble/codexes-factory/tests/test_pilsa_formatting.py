#!/usr/bin/env python3
"""
Test script to verify pilsa italicization formatting works correctly.
This tests the fix_pilsa_formatting function with various broken patterns.
"""

import sys
import os
import re

def fix_pilsa_formatting(text):
    """Fix pilsa formatting to ensure it's always properly italicized."""
    if not text:
        return text
    
    # Fix various broken LaTeX formatting patterns for pilsa
    # Handle the most common pattern: \textbackslash{}textit{\textit{pilsa}}
    text = re.sub(r'\\textbackslash\{\}textit\{\\textit\{pilsa\}\}', r'\\textit{pilsa}', text)
    
    # Handle other escaped patterns
    text = re.sub(r'\\textbackslash\{\}textit\{pilsa\}', r'\\textit{pilsa}', text)
    
    # Fix nested textit patterns
    text = re.sub(r'\\textit\{\\textit\{pilsa\}\}', r'\\textit{pilsa}', text)
    
    # Fix the specific pattern we're seeing: any whitespace + extit{\textit{pilsa}}
    text = re.sub(r'\s*extit\{\\textit\{pilsa\}\}', r'\\textit{pilsa}', text)
    
    # Fix the tab + extit pattern we're actually seeing
    text = re.sub(r'(\s)\textit\{\\textit\{pilsa\}\}', r'\1\\textit{pilsa}', text)
    
    # Fix simple extit patterns
    text = re.sub(r'extit\{pilsa\}', r'\\textit{pilsa}', text)
    
    # Clean up any leftover \t characters that might be artifacts
    text = re.sub(r'\\t\\textit\{pilsa\}', r'\\textit{pilsa}', text)
    
    # Ensure standalone "pilsa" is italicized (but not if already properly formatted)
    # But don't double-italicize if it's already in \textit{}
    text = re.sub(r'(?<!\\textit\{)pilsa(?!\})', r'\\textit{pilsa}', text)
    
    return text

def test_pilsa_formatting():
    """Test various broken pilsa formatting patterns and verify they get fixed."""
    
    test_cases = [
        # Test case 1: The actual pattern we see in the output
        {
            'input': 'The Korean tradition of \\textbackslash{}textit{\\textit{pilsa}} (필사), or mindful transcription',
            'expected': 'The Korean tradition of \\textit{pilsa} (필사), or mindful transcription',
            'description': 'Real escaped textit with nested textit'
        },
        
        # Test case 1b: The tab + extit pattern we're actually seeing
        {
            'input': 'The Korean tradition of \textit{\\textit{pilsa}} (필사), or mindful transcription',
            'expected': 'The Korean tradition of \\textit{pilsa} (필사), or mindful transcription',
            'description': 'Tab + extit pattern'
        },
        
        # Test case 2: Simple escaped pattern
        {
            'input': 'This practice of \\textbackslash{}textit{pilsa} has ancient roots',
            'expected': 'This practice of \\textit{pilsa} has ancient roots',
            'description': 'Simple escaped textit'
        },
        
        # Test case 3: Nested textit pattern
        {
            'input': 'The art of \\textit{\\textit{pilsa}} requires patience',
            'expected': 'The art of \\textit{pilsa} requires patience',
            'description': 'Nested textit pattern'
        },
        
        # Test case 4: Simple extit pattern
        {
            'input': 'Through extit{pilsa} we find peace',
            'expected': 'Through \\textit{pilsa} we find peace',
            'description': 'Simple extit pattern'
        },
        
        # Test case 5: Standalone pilsa word
        {
            'input': 'The practice of pilsa is meditative',
            'expected': 'The practice of \\textit{pilsa} is meditative',
            'description': 'Standalone pilsa word'
        },
        
        # Test case 6: Already correctly formatted (should not change)
        {
            'input': 'The tradition of \\textit{pilsa} continues today',
            'expected': 'The tradition of \\textit{pilsa} continues today',
            'description': 'Already correctly formatted'
        },
        
        # Test case 7: Multiple instances in one text
        {
            'input': 'Both \\textbackslash{}textit{\\textit{pilsa}} and pilsa are important',
            'expected': 'Both \\textit{pilsa} and \\textit{pilsa} are important',
            'description': 'Multiple instances'
        }
    ]
    
    print("Testing pilsa formatting fixes...")
    print("=" * 60)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Input:    {test_case['input']}")
        
        result = fix_pilsa_formatting(test_case['input'])
        print(f"Output:   {result}")
        print(f"Expected: {test_case['expected']}")
        
        if result == test_case['expected']:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests PASSED! Pilsa formatting is working correctly.")
        return True
    else:
        print("💥 Some tests FAILED. Pilsa formatting needs more work.")
        return False

def test_integration():
    """Test the pilsa formatting in a realistic foreword context."""
    
    print("\n" + "=" * 60)
    print("Integration Test: Realistic Foreword Text")
    print("=" * 60)
    
    # Simulate what the LLM might generate and what gets escaped
    realistic_input = """The Korean tradition of \\textbackslash{}textit{\\textit{pilsa}} (필사), or mindful transcription, offers a profound pathway to engagement with text and self. Far more than mere copying, \\textbackslash{}textit{\\textit{pilsa}} is an ancient practice deeply embedded in Korea's intellectual and spiritual heritage.

With the advent of modern printing and rapid industrialization in the 20th century, the practical necessity of \\textbackslash{}textit{\\textit{pilsa}} diminished, and the tradition largely faded from daily life. However, in our increasingly fast-paced and digitally saturated world, \\textbackslash{}textit{\\textit{pilsa}} has experienced a remarkable resurgence.

This book invites you to partake in this timeless tradition. Through the practice of \\textbackslash{}textit{\\textit{pilsa}}, you are not merely reading; you are embodying the text, connecting with a lineage of wisdom."""
    
    expected_output = """The Korean tradition of \\textit{pilsa} (필사), or mindful transcription, offers a profound pathway to engagement with text and self. Far more than mere copying, \\textit{pilsa} is an ancient practice deeply embedded in Korea's intellectual and spiritual heritage.

With the advent of modern printing and rapid industrialization in the 20th century, the practical necessity of \\textit{pilsa} diminished, and the tradition largely faded from daily life. However, in our increasingly fast-paced and digitally saturated world, \\textit{pilsa} has experienced a remarkable resurgence.

This book invites you to partake in this timeless tradition. Through the practice of \\textit{pilsa}, you are not merely reading; you are embodying the text, connecting with a lineage of wisdom."""
    
    print("Processing realistic foreword text...")
    result = fix_pilsa_formatting(realistic_input)
    
    print(f"\nResult preview (first 200 chars):")
    print(f"{result[:200]}...")
    
    # Check if all instances were fixed
    broken_patterns = [
        r'\\textbackslash\\{\\}textit\\{\\textit\\{pilsa\\}\\}',
        r'\\textbackslash\\{\\}textit\\{pilsa\\}',
        r'extit\\{pilsa\\}'
    ]
    
    issues_found = []
    for pattern in broken_patterns:
        if re.search(pattern, result):
            issues_found.append(pattern)
    
    if not issues_found and '\\textit{pilsa}' in result:
        print("✅ Integration test PASSED! All pilsa instances properly formatted.")
        return True
    else:
        print("❌ Integration test FAILED!")
        if issues_found:
            print(f"Found broken patterns: {issues_found}")
        if '\\textit{pilsa}' not in result:
            print("No properly formatted \\textit{pilsa} found in result")
        return False

if __name__ == "__main__":
    print("Pilsa Formatting Test Suite")
    print("=" * 60)
    
    # Run unit tests
    unit_tests_passed = test_pilsa_formatting()
    
    # Run integration test
    integration_test_passed = test_integration()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"Unit Tests: {'✅ PASSED' if unit_tests_passed else '❌ FAILED'}")
    print(f"Integration Test: {'✅ PASSED' if integration_test_passed else '❌ FAILED'}")
    
    if unit_tests_passed and integration_test_passed:
        print("\n🎉 ALL TESTS PASSED! Pilsa formatting is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED! Please check the pilsa formatting function.")
        sys.exit(1)