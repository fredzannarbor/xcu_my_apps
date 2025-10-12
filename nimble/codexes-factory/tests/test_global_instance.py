#!/usr/bin/env python3
"""
Test script to check the global enhanced_llm_caller instance
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

try:
    from src.codexes.core.enhanced_llm_caller import enhanced_llm_caller
    print("✅ Successfully imported global enhanced_llm_caller")
    
    # Check methods
    print(f"Has call method: {hasattr(enhanced_llm_caller, 'call')}")
    print(f"Has call_llm method: {hasattr(enhanced_llm_caller, 'call_llm')}")
    
    # List all methods
    methods = [method for method in dir(enhanced_llm_caller) if not method.startswith('_')]
    print(f"Available methods: {methods}")
    
    # Try to call call_llm
    try:
        result = enhanced_llm_caller.call_llm("Test prompt")
        print(f"✅ call_llm worked: {result[:50]}...")
    except Exception as e:
        print(f"❌ call_llm failed: {e}")
        
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()