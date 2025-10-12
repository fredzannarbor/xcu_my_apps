#!/usr/bin/env python3
"""
Validate that core dependencies can be imported.
This script helps ensure the dependency cleanup didn't break anything.
"""

import sys
from importlib import import_module

# Core dependencies that should be importable
CORE_DEPENDENCIES = [
    'click',
    'pandas', 
    'requests',
    'numpy',
    'gibberish',
    'nltk',
    'ftfy',
    'fitz',  # PyMuPDF
    'docx',  # python-docx
    'PIL',   # Pillow
]

# Optional dependencies (may not be installed)
OPTIONAL_DEPENDENCIES = {
    'web': ['streamlit'],
    'ai': ['openai', 'spacy'],
    'research': ['bibtexparser', 'isbnlib', 'pyzotero', 'openpyxl'],
    'image': ['html2image'],
    'payment': ['stripe'],
}

def test_import(module_name):
    """Test if a module can be imported."""
    try:
        import_module(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)

def main():
    """Main validation function."""
    print("Validating core dependencies...")
    
    failed_core = []
    for module in CORE_DEPENDENCIES:
        success, error = test_import(module)
        if success:
            print(f"✓ {module}")
        else:
            print(f"✗ {module}: {error}")
            failed_core.append(module)
    
    print(f"\nCore dependencies: {len(CORE_DEPENDENCIES) - len(failed_core)}/{len(CORE_DEPENDENCIES)} available")
    
    if failed_core:
        print(f"Missing core dependencies: {', '.join(failed_core)}")
        print("Install with: pip install trillions-of-people")
    
    # Test optional dependencies
    print("\nTesting optional dependencies...")
    for group, modules in OPTIONAL_DEPENDENCIES.items():
        available = 0
        for module in modules:
            success, _ = test_import(module)
            if success:
                available += 1
        
        print(f"{group}: {available}/{len(modules)} available")
        if available < len(modules):
            print(f"  Install with: pip install trillions-of-people[{group}]")
    
    return len(failed_core) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)