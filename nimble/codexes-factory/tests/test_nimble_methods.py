#!/usr/bin/env python3
"""
Test script to check available methods in nimble_llm_caller
"""

try:
    from nimble_llm_caller.core.enhanced_llm_caller import EnhancedLLMCaller
    
    caller = EnhancedLLMCaller()
    
    # Check all methods
    methods = [m for m in dir(caller) if not m.startswith('_')]
    print("Available methods:")
    for method in methods:
        attr = getattr(caller, method)
        if callable(attr):
            print(f"  {method}")
    
    # Check if call_llm_with_retry exists
    print(f"\nHas call_llm_with_retry: {hasattr(caller, 'call_llm_with_retry')}")
    print(f"Has call_llm: {hasattr(caller, 'call_llm')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()