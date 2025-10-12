#!/usr/bin/env python3
"""
Test script to verify interior fixes are working correctly.
"""

import sys
import re
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codexes.modules.prepress.partsofthebook_processor import PartsOfTheBookProcessor

def test_pilsa_formatting():
    """Test pilsa formatting fixes."""
    processor = PartsOfTheBookProcessor()
    
    test_cases = [
        ("This is about pilsa practice", "This is about \\textit{pilsa} practice"),
        ("The [\\textit{pilsa}] method", "The [\\textit{pilsa}] method"),
        ("Korean \\{korean{필사} text", "Korean \\korean{필사} text"),
        ("extit{pilsa} should be fixed", "\\textit{pilsa} should be fixed"),
        ("Already \\textit{pilsa} formatted", "Already \\textit{pilsa} formatted"),
    ]
    
    print("Testing pilsa formatting fixes:")
    for input_text, expected in test_cases:
        result = processor.fix_pilsa_formatting(input_text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_text}' -> '{result}'")
        if result != expected:
            print(f"    Expected: '{expected}'")

def test_korean_formatting():
    """Test Korean formatting fixes."""
    processor = PartsOfTheBookProcessor()
    
    test_cases = [
        ("\\{korean{필사}", "\\korean{필사}"),
        ("\\korean{필사}", "\\korean{필사}"),
        ("Text with \\korean{한글} here", "Text with \\korean{한글} here"),
    ]
    
    print("\nTesting Korean formatting fixes:")
    for input_text, expected in test_cases:
        result = processor.fix_korean_formatting(input_text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_text}' -> '{result}'")
        if result != expected:
            print(f"    Expected: '{expected}'")

def test_glossary_formatting():
    """Test glossary formatting."""
    processor = PartsOfTheBookProcessor()
    
    # Mock terms data
    terms = [
        {
            "korean": "필사",
            "english": "transcription",
            "definition": "The practice of copying text by hand"
        },
        {
            "korean": "서예",
            "english": "calligraphy", 
            "definition": "The art of beautiful handwriting"
        }
    ]
    
    result = processor._format_glossary_as_latex(terms)
    
    print("\nTesting glossary formatting:")
    print("✓ Generated glossary LaTeX")
    
    # Check for key elements
    checks = [
        ("\\textit{Pilsa} Terms" in result, "Title includes italicized pilsa"),
        ("\\begin{longtable}" in result, "Uses longtable for 3-column layout"),
        ("\\korean{필사}" in result, "Korean text properly formatted"),
        ("p{2.5cm} p{3.5cm} p{6.5cm}" in result, "3-column layout with proper widths"),
    ]
    
    for check, description in checks:
        status = "✓" if check else "✗"
        print(f"  {status} {description}")

def test_bibliography_formatting():
    """Test bibliography formatting."""
    processor = PartsOfTheBookProcessor()
    
    # Mock sources data
    sources = [
        {
            "author": "Test Author",
            "title": "Test Book about pilsa",
            "date_published": "2023",
            "isbn": "9781234567890"
        }
    ]
    
    book_data = {"title": "Test Book"}
    result = processor._format_bibliography_as_latex(sources, book_data)
    
    print("\nTesting bibliography formatting:")
    print("✓ Generated bibliography LaTeX")
    
    # Check for key elements
    checks = [
        ("\\setlength{\\hangindent}{0.15in}" in result, "Hanging indent set to 0.15in"),
        ("\\setlength{\\parskip}{3pt}" in result, "3pt spacing between entries"),
        ("NimbleBooks.com" in result, "QR code replaced with NimbleBooks.com"),
        ("\\textit{pilsa}" in result, "pilsa properly italicized"),
    ]
    
    for check, description in checks:
        status = "✓" if check else "✗"
        print(f"  {status} {description}")

if __name__ == "__main__":
    print("Running interior fixes tests...\n")
    test_pilsa_formatting()
    test_korean_formatting()
    test_glossary_formatting()
    test_bibliography_formatting()
    print("\nTests completed!")