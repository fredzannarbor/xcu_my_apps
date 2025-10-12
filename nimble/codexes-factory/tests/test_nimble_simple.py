#!/usr/bin/env python3
"""
Simple test of nimble_llm_caller
"""

try:
    from nimble_llm_caller.core.enhanced_llm_caller import EnhancedLLMCaller
    from nimble_llm_caller.models.request import LLMRequest, ResponseFormat
    
    # Create caller
    caller = EnhancedLLMCaller()
    
    # Create simple request
    request = LLMRequest(
        prompt_key="test_prompt",
        model="gpt-4",
        response_format=ResponseFormat.TEXT,
        model_params={
            "temperature": 0.7,
            "max_tokens": 100
        },
        metadata={
            "content": "Say hello world"
        }
    )
    
    print("Making LLM call...")
    response = caller.call(request)
    
    print(f"Response status: {response.status}")
    print(f"Response is_success: {response.is_success}")
    print(f"Response content: {response.content}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()