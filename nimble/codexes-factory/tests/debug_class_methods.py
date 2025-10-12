#!/usr/bin/env python3
"""
Debug script to check the EnhancedLLMCaller class methods
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

try:
    from src.codexes.core.enhanced_llm_caller import EnhancedLLMCaller
    
    # Check class definition
    print("Class methods:")
    for name in dir(EnhancedLLMCaller):
        if not name.startswith('_'):
            attr = getattr(EnhancedLLMCaller, name)
            if callable(attr):
                print(f"  {name}: {type(attr)}")
    
    # Create instance and check methods
    instance = EnhancedLLMCaller()
    print("\nInstance methods:")
    for name in dir(instance):
        if not name.startswith('_'):
            attr = getattr(instance, name)
            if callable(attr):
                print(f"  {name}: {type(attr)}")
    
    # Check if call_llm is in the class
    print(f"\nClass has call_llm: {hasattr(EnhancedLLMCaller, 'call_llm')}")
    print(f"Instance has call_llm: {hasattr(instance, 'call_llm')}")
    
    # Try to get the method directly
    try:
        method = getattr(instance, 'call_llm')
        print(f"call_llm method: {method}")
    except AttributeError as e:
        print(f"AttributeError getting call_llm: {e}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()