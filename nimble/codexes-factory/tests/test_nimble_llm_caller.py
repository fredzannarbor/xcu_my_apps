#!/usr/bin/env python3
"""
Test script to check nimble_llm_caller methods
"""

try:
    from nimble_llm_caller.core.enhanced_llm_caller import EnhancedLLMCaller
    from nimble_llm_caller.core.llm_caller import LLMCaller
    
    print("✅ Successfully imported nimble_llm_caller")
    
    # Check LLMCaller methods
    caller = LLMCaller()
    print(f"LLMCaller methods: {[m for m in dir(caller) if not m.startswith('_') and callable(getattr(caller, m))]}")
    
    # Check EnhancedLLMCaller methods
    enhanced_caller = EnhancedLLMCaller()
    print(f"EnhancedLLMCaller methods: {[m for m in dir(enhanced_caller) if not m.startswith('_') and callable(getattr(enhanced_caller, m))]}")
    
    # Test if we can call it
    try:
        # Check what the call method expects
        import inspect
        sig = inspect.signature(enhanced_caller.call)
        print(f"Enhanced call method signature: {sig}")
        
        sig = inspect.signature(caller.call)
        print(f"Base call method signature: {sig}")
        
    except Exception as e:
        print(f"Error checking signatures: {e}")
        
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()