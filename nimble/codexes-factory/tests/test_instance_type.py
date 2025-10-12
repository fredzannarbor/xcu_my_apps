#!/usr/bin/env python3
"""
Test script to check the type of the global enhanced_llm_caller instance
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

try:
    from src.codexes.core.enhanced_llm_caller import enhanced_llm_caller, EnhancedLLMCaller
    print(f"Global instance type: {type(enhanced_llm_caller)}")
    print(f"EnhancedLLMCaller class: {EnhancedLLMCaller}")
    print(f"Is instance of EnhancedLLMCaller: {isinstance(enhanced_llm_caller, EnhancedLLMCaller)}")
    
    # Create a new instance to compare
    new_instance = EnhancedLLMCaller()
    print(f"New instance type: {type(new_instance)}")
    print(f"New instance has call_llm: {hasattr(new_instance, 'call_llm')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()